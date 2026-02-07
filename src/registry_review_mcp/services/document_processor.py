"""Document processing service with dual-track extraction.

Orchestrates fast (PyMuPDF4LLM) and high-quality (Marker) PDF extraction.
This service is interface-agnostic and can be used by both MCP and REST API.

Architecture:
    Upload → Fast Extraction (2-3 sec) → Immediately usable
                      ↓
              Queue HQ Conversion → Background (5-15 min)
                      ↓
              HQ Available → Upgrade quality
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import psutil

from ..config.settings import settings
from ..utils.state import StateManager, get_session_or_raise

logger = logging.getLogger(__name__)

# Marker model requires ~8GB RAM. Guard threshold includes buffer.
MARKER_MIN_RAM_GB = 10  # Need 8GB for model + 2GB buffer


def check_memory_available(min_gb: float = MARKER_MIN_RAM_GB) -> tuple[bool, float]:
    """Check if sufficient RAM is available for HQ conversion.

    Args:
        min_gb: Minimum required RAM in GB

    Returns:
        Tuple of (is_available, available_gb)
    """
    available_gb = psutil.virtual_memory().available / (1024 ** 3)
    return available_gb >= min_gb, round(available_gb, 1)


@dataclass
class DocumentStatus:
    """Status of a single document's extraction."""
    document_id: str
    filename: str
    fast_status: str  # "pending" | "complete" | "failed"
    hq_status: str  # "pending" | "queued" | "converting" | "complete" | "failed"
    hq_progress: int  # 0-100
    preferred_quality: str  # "fast" | "hq"
    has_content: bool


@dataclass
class ConversionStatus:
    """Overall conversion status for a session."""
    session_id: str
    total_documents: int
    pdfs_total: int
    fast_complete: int
    hq_complete: int
    hq_converting: int
    hq_queued: int
    overall_progress: float
    estimated_completion: str | None
    documents: list[DocumentStatus]
    message: str


class DocumentProcessor:
    """Orchestrates dual-track PDF extraction for a session.

    Fast track (PyMuPDF4LLM):
        - Runs immediately after upload
        - ~2-3 seconds per document
        - 75-90% quality
        - Result stored in document record

    High-quality track (Marker):
        - Queued after fast extraction
        - ~5-15 minutes per document
        - 100% quality
        - Runs in background, replaces fast when ready

    IMPORTANT: This class does NOT cache StateManager. Each method gets a fresh
    StateManager to ensure context is valid in background tasks. This prevents
    the session context bug where self.state captured at init becomes stale.
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        # Validate session exists at init time
        get_session_or_raise(session_id)

    async def run_fast_extraction(self, document_ids: list[str] | None = None) -> dict[str, Any]:
        """Run fast extraction on documents.

        Processes PDFs (via PyMuPDF4LLM) and spreadsheets (via openpyxl/csv).
        Spreadsheets are already structured data so they only need one
        extraction pass — no HQ conversion is applicable.

        Args:
            document_ids: Specific documents to process. If None, process all extractable files.

        Returns:
            Summary of extraction results
        """
        from ..extractors.fast_extractor import fast_extract_pdf
        from ..extractors.spreadsheet_extractor import extract_spreadsheet
        from ..utils.patterns import SPREADSHEET_EXTENSIONS

        # Get fresh state for this operation
        state = get_session_or_raise(self.session_id)
        docs_data = state.read_json("documents.json")
        documents = docs_data.get("documents", [])

        # Filter to specified documents or all extractable files (PDFs + spreadsheets)
        extractable_suffixes = {".pdf"} | SPREADSHEET_EXTENSIONS
        to_process = []
        for doc in documents:
            if document_ids and doc["document_id"] not in document_ids:
                continue
            suffix = Path(doc["filepath"]).suffix.lower()
            if suffix not in extractable_suffixes:
                continue
            if doc.get("fast_status") == "complete":
                continue
            to_process.append(doc)

        if not to_process:
            return {
                "session_id": self.session_id,
                "processed": 0,
                "message": "No documents need fast extraction",
            }

        logger.info(f"Running fast extraction on {len(to_process)} documents")
        print(f"⚡ Fast extracting {len(to_process)} document(s)...", flush=True)

        results = {"successful": 0, "failed": 0, "documents": []}

        for i, doc in enumerate(to_process, 1):
            doc_id = doc["document_id"]
            filepath = doc["filepath"]
            filename = Path(filepath).name
            suffix = Path(filepath).suffix.lower()

            print(f"  [{i}/{len(to_process)}] {filename}...", flush=True, end=" ")

            try:
                if suffix in SPREADSHEET_EXTENSIONS:
                    result = await extract_spreadsheet(filepath)
                else:
                    result = await fast_extract_pdf(filepath)

                # Save markdown alongside the source file
                src_path = Path(filepath)
                fast_md_path = src_path.with_suffix(".fast.md")
                fast_md_path.write_text(result["markdown"], encoding="utf-8")

                # Update document record
                doc["fast_status"] = "complete"
                doc["fast_markdown_path"] = str(fast_md_path)
                doc["fast_extracted_at"] = datetime.now(timezone.utc).isoformat()
                doc["fast_page_count"] = result["page_count"]
                doc["fast_char_count"] = result["total_chars"]

                # Set as active markdown
                if not doc.get("hq_status") == "complete":
                    doc["has_markdown"] = True
                    doc["markdown_path"] = str(fast_md_path)
                    doc["active_quality"] = "fast"

                # Spreadsheets don't need HQ conversion — they're already structured
                if suffix in SPREADSHEET_EXTENSIONS:
                    doc["hq_status"] = "not_applicable"
                elif "hq_status" not in doc:
                    doc["hq_status"] = "pending"

                results["successful"] += 1
                results["documents"].append({
                    "document_id": doc_id,
                    "filename": filename,
                    "chars": result["total_chars"],
                    "pages": result["page_count"],
                })
                print(f"✓ ({result['total_chars']:,} chars)", flush=True)

            except Exception as e:
                doc["fast_status"] = "failed"
                doc["fast_error"] = str(e)
                results["failed"] += 1
                logger.error(f"Fast extraction failed for {filename}: {e}")
                print(f"✗ {e}", flush=True)

        # Save updated documents
        docs_data["documents"] = documents
        state.write_json("documents.json", docs_data)

        print(f"\n✅ Fast extraction complete: {results['successful']} successful, {results['failed']} failed", flush=True)

        return {
            "session_id": self.session_id,
            "processed": len(to_process),
            **results,
        }

    async def queue_hq_conversion(
        self,
        document_ids: list[str] | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Queue high-quality conversion for documents.

        Args:
            document_ids: Specific documents to convert. If None, convert all PDFs.
            force: Skip memory check (use with caution - may freeze system)

        Returns:
            Job information with memory_warning if insufficient RAM
        """
        from .background_jobs import get_job_manager

        # Memory guard: Check available RAM before loading 8GB model
        if not force:
            has_memory, available_gb = check_memory_available()
            if not has_memory:
                logger.warning(
                    f"Insufficient RAM for HQ conversion: {available_gb}GB available, "
                    f"{MARKER_MIN_RAM_GB}GB required"
                )
                return {
                    "session_id": self.session_id,
                    "queued": 0,
                    "memory_warning": {
                        "available_gb": available_gb,
                        "required_gb": MARKER_MIN_RAM_GB,
                        "message": (
                            f"HQ conversion requires ~{MARKER_MIN_RAM_GB}GB RAM but only "
                            f"{available_gb}GB available. Close other applications or use "
                            f"force=True to override (may freeze system)."
                        ),
                    },
                    "message": f"Insufficient RAM ({available_gb}GB available, {MARKER_MIN_RAM_GB}GB required)",
                }

        # Get fresh state for this operation
        state = get_session_or_raise(self.session_id)
        docs_data = state.read_json("documents.json")
        documents = docs_data.get("documents", [])

        # Find documents needing HQ conversion
        to_convert = []
        for doc in documents:
            if document_ids and doc["document_id"] not in document_ids:
                continue
            if not doc["filepath"].lower().endswith(".pdf"):
                continue
            if doc.get("hq_status") in ("complete", "converting", "queued"):
                continue
            to_convert.append(doc)

        if not to_convert:
            return {
                "session_id": self.session_id,
                "queued": 0,
                "message": "No documents need HQ conversion",
            }

        # Mark as queued
        doc_ids = [doc["document_id"] for doc in to_convert]
        for doc in to_convert:
            doc["hq_status"] = "queued"

        docs_data["documents"] = documents
        state.write_json("documents.json", docs_data)

        # Create background job
        job_manager = get_job_manager()
        job_id = job_manager.create_job(self.session_id, doc_ids)

        # Start job with converter function
        await job_manager.start_job(job_id, self._convert_document_hq)

        logger.info(f"Queued HQ conversion job {job_id} for {len(to_convert)} documents")

        return {
            "session_id": self.session_id,
            "job_id": job_id,
            "queued": len(to_convert),
            "documents": [{"document_id": d["document_id"], "filename": d["filename"]} for d in to_convert],
            "message": f"HQ conversion started for {len(to_convert)} documents",
        }

    async def _convert_document_hq(self, doc_id: str, on_progress: callable) -> dict:
        """Convert a single document with Marker (high-quality).

        This is called by the job manager for each document.

        IMPORTANT: Gets fresh StateManager each time to avoid stale context bug.
        Background tasks may run long after the DocumentProcessor was created.
        """
        from ..extractors.marker_extractor import convert_pdf_to_markdown

        # Get FRESH state - critical for background tasks
        state = get_session_or_raise(self.session_id)
        docs_data = state.read_json("documents.json")
        documents = docs_data.get("documents", [])
        doc = next((d for d in documents if d["document_id"] == doc_id), None)

        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        filepath = doc["filepath"]
        filename = Path(filepath).name

        # Update status to converting
        doc["hq_status"] = "converting"
        state.write_json("documents.json", docs_data)

        logger.info(f"Converting {filename} with Marker...")

        try:
            # Run marker conversion
            result = await convert_pdf_to_markdown(filepath)

            # Save HQ markdown
            pdf_path = Path(filepath)
            hq_md_path = pdf_path.with_suffix(".hq.md")
            hq_md_path.write_text(result["markdown"], encoding="utf-8")

            # Reload fresh state and update document record
            state = get_session_or_raise(self.session_id)
            docs_data = state.read_json("documents.json")
            documents = docs_data.get("documents", [])
            doc = next((d for d in documents if d["document_id"] == doc_id), None)

            doc["hq_status"] = "complete"
            doc["hq_markdown_path"] = str(hq_md_path)
            doc["hq_extracted_at"] = datetime.now(timezone.utc).isoformat()
            doc["hq_page_count"] = result["page_count"]

            # Upgrade to HQ as active
            doc["has_markdown"] = True
            doc["markdown_path"] = str(hq_md_path)
            doc["active_quality"] = "hq"

            state.write_json("documents.json", docs_data)

            logger.info(f"HQ conversion complete for {filename}")
            return {"success": True, "document_id": doc_id}

        except Exception as e:
            # Reload fresh state and mark as failed
            state = get_session_or_raise(self.session_id)
            docs_data = state.read_json("documents.json")
            documents = docs_data.get("documents", [])
            doc = next((d for d in documents if d["document_id"] == doc_id), None)
            doc["hq_status"] = "failed"
            doc["hq_error"] = str(e)
            state.write_json("documents.json", docs_data)

            logger.error(f"HQ conversion failed for {filename}: {e}")
            raise

    def get_document_text(
        self,
        doc_id: str,
        quality: str = "best",
    ) -> tuple[str, str] | None:
        """Get document text at requested quality.

        Args:
            doc_id: Document ID
            quality: "fast", "hq", or "best" (default)

        Returns:
            Tuple of (text, quality_used) or None if not available
        """
        # Get fresh state
        state = get_session_or_raise(self.session_id)
        docs_data = state.read_json("documents.json")
        doc = next(
            (d for d in docs_data.get("documents", []) if d["document_id"] == doc_id),
            None
        )

        if not doc:
            return None

        # Get best available
        if quality == "best":
            if doc.get("hq_status") == "complete" and doc.get("hq_markdown_path"):
                md_path = Path(doc["hq_markdown_path"])
                if md_path.exists():
                    return md_path.read_text(encoding="utf-8"), "hq"

            if doc.get("fast_status") == "complete" and doc.get("fast_markdown_path"):
                md_path = Path(doc["fast_markdown_path"])
                if md_path.exists():
                    return md_path.read_text(encoding="utf-8"), "fast"

        # Get specific quality
        elif quality == "hq":
            if doc.get("hq_status") == "complete" and doc.get("hq_markdown_path"):
                md_path = Path(doc["hq_markdown_path"])
                if md_path.exists():
                    return md_path.read_text(encoding="utf-8"), "hq"

        elif quality == "fast":
            if doc.get("fast_status") == "complete" and doc.get("fast_markdown_path"):
                md_path = Path(doc["fast_markdown_path"])
                if md_path.exists():
                    return md_path.read_text(encoding="utf-8"), "fast"

        return None


def get_conversion_status(session_id: str) -> ConversionStatus:
    """Get comprehensive conversion status for a session.

    Returns status suitable for user display, including ETAs and progress.
    """
    state = get_session_or_raise(session_id)

    try:
        docs_data = state.read_json("documents.json")
    except Exception:
        return ConversionStatus(
            session_id=session_id,
            total_documents=0,
            pdfs_total=0,
            fast_complete=0,
            hq_complete=0,
            hq_converting=0,
            hq_queued=0,
            overall_progress=0.0,
            estimated_completion=None,
            documents=[],
            message="No documents discovered yet",
        )

    documents = docs_data.get("documents", [])

    # Filter to PDFs only for conversion status
    pdfs = [d for d in documents if d["filepath"].lower().endswith(".pdf")]

    # Count statuses
    fast_complete = sum(1 for d in pdfs if d.get("fast_status") == "complete")
    hq_complete = sum(1 for d in pdfs if d.get("hq_status") == "complete")
    hq_converting = sum(1 for d in pdfs if d.get("hq_status") == "converting")
    hq_queued = sum(1 for d in pdfs if d.get("hq_status") == "queued")

    # Calculate overall progress
    if pdfs:
        # Fast progress: 30%, HQ progress: 70%
        fast_progress = (fast_complete / len(pdfs)) * 0.3
        hq_progress = (hq_complete / len(pdfs)) * 0.7
        overall = fast_progress + hq_progress
    else:
        overall = 1.0

    # Estimate completion time
    eta = None
    if hq_converting > 0 or hq_queued > 0:
        remaining = hq_queued + hq_converting
        # Rough estimate: 5 minutes per document
        eta_minutes = remaining * 5
        if eta_minutes < 60:
            eta = f"{eta_minutes} minute{'s' if eta_minutes != 1 else ''}"
        else:
            hours = eta_minutes // 60
            mins = eta_minutes % 60
            eta = f"{hours}h {mins}m"

    # Build per-document status
    doc_statuses = []
    for doc in pdfs:
        doc_statuses.append(DocumentStatus(
            document_id=doc["document_id"],
            filename=doc["filename"],
            fast_status=doc.get("fast_status", "pending"),
            hq_status=doc.get("hq_status", "pending"),
            hq_progress=100 if doc.get("hq_status") == "complete" else 0,
            preferred_quality=doc.get("active_quality", "none"),
            has_content=bool(doc.get("has_markdown")),
        ))

    # Generate message
    if hq_complete == len(pdfs) and len(pdfs) > 0:
        message = f"All {len(pdfs)} documents fully processed (high-quality)"
    elif fast_complete == len(pdfs) and len(pdfs) > 0:
        if hq_converting > 0:
            message = f"Fast analysis ready. High-quality processing: {hq_complete}/{len(pdfs)} complete"
        elif hq_queued > 0:
            message = f"Fast analysis ready. {hq_queued} documents queued for high-quality conversion"
        else:
            message = f"Fast analysis complete for all {len(pdfs)} documents. High-quality conversion available."
    elif fast_complete > 0:
        message = f"Fast: {fast_complete}/{len(pdfs)} ready. HQ: {hq_complete}/{len(pdfs)} complete"
    else:
        message = "No documents processed yet"

    return ConversionStatus(
        session_id=session_id,
        total_documents=len(documents),
        pdfs_total=len(pdfs),
        fast_complete=fast_complete,
        hq_complete=hq_complete,
        hq_converting=hq_converting,
        hq_queued=hq_queued,
        overall_progress=round(overall, 2),
        estimated_completion=eta,
        documents=doc_statuses,
        message=message,
    )
