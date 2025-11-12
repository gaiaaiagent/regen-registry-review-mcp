"""Document processing tools for discovery, classification, and extraction."""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pdfplumber
import fiona

from ..config.settings import settings
from ..models.errors import (
    DocumentError,
    DocumentExtractionError,
    SessionNotFoundError,
)
from ..models.schemas import Document, DocumentMetadata
from ..utils.cache import pdf_cache, gis_cache
from ..utils.patterns import (
    PROJECT_PLAN_PATTERNS,
    BASELINE_PATTERNS,
    MONITORING_PATTERNS,
    GHG_PATTERNS,
    LAND_TENURE_PATTERNS,
    REGISTRY_REVIEW_PATTERNS,
    METHODOLOGY_PATTERNS,
    is_pdf_file,
    is_gis_file,
    is_image_file,
    match_any,
)
from ..utils.state import StateManager


def generate_document_id(filepath: str) -> str:
    """Generate a unique document ID from filepath.

    Args:
        filepath: Path to document

    Returns:
        Unique document ID (DOC-xxxxx)
    """
    # Use hash of filepath for consistency
    hash_obj = hashlib.md5(filepath.encode())
    short_hash = hash_obj.hexdigest()[:8]
    return f"DOC-{short_hash}"


async def discover_documents(session_id: str) -> dict[str, Any]:
    """Discover and index all documents in the session's project directory.

    Args:
        session_id: Unique session identifier

    Returns:
        Dictionary with discovery results and document index

    Raises:
        SessionNotFoundError: If session doesn't exist
    """
    # Load session
    state_manager = StateManager(session_id)
    if not state_manager.exists():
        raise SessionNotFoundError(
            f"Session not found: {session_id}",
            details={"session_id": session_id},
        )

    session_data = state_manager.read_json("session.json")
    documents_path = Path(session_data["project_metadata"]["documents_path"])

    # Discover files
    discovered_files = []
    classification_summary = {}

    # Supported extensions
    supported_extensions = {".pdf", ".shp", ".geojson", ".tif", ".tiff"}

    # Recursive scan
    for file_path in documents_path.rglob("*"):
        if not file_path.is_file():
            continue

        # Check if supported file type
        if file_path.suffix.lower() not in supported_extensions:
            continue

        # Skip hidden files and cache directories
        if any(part.startswith(".") for part in file_path.parts):
            continue

        discovered_files.append(file_path)

    # Process each file
    documents = []
    for file_path in discovered_files:
        try:
            # Generate document ID
            doc_id = generate_document_id(str(file_path))

            # Classify document
            classification, confidence, method = await classify_document_by_filename(
                str(file_path)
            )

            # Extract metadata
            metadata = await extract_document_metadata(file_path)

            # Create document record
            document = Document(
                document_id=doc_id,
                filename=file_path.name,
                filepath=str(file_path),
                classification=classification,
                confidence=confidence,
                classification_method=method,
                metadata=metadata,
                indexed_at=datetime.now(timezone.utc),
            )

            documents.append(document.model_dump(mode="json"))

            # Update classification summary
            classification_summary[classification] = (
                classification_summary.get(classification, 0) + 1
            )

        except Exception as e:
            # Log but continue processing other files
            print(f"Warning: Failed to process {file_path}: {e}", flush=True)
            continue

    # Save document index
    documents_data = {
        "documents": documents,
        "total_count": len(documents),
        "classification_summary": classification_summary,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
    }
    state_manager.write_json("documents.json", documents_data)

    # Update session statistics
    state_manager.update_json(
        "session.json",
        {
            "statistics": {
                **session_data.get("statistics", {}),
                "documents_found": len(documents),
            },
            "workflow_progress": {
                **session_data.get("workflow_progress", {}),
                "document_discovery": "completed",
            },
        },
    )

    return {
        "session_id": session_id,
        "documents_found": len(documents),
        "classification_summary": classification_summary,
        "documents": documents,
    }


async def classify_document_by_filename(filepath: str) -> tuple[str, float, str]:
    """Classify document based on filename patterns.

    Args:
        filepath: Path to document

    Returns:
        Tuple of (classification, confidence, method)
    """
    filename = Path(filepath).name.lower()

    # Check patterns in order of specificity
    if match_any(filename, PROJECT_PLAN_PATTERNS):
        return ("project_plan", 0.95, "filename")

    if match_any(filename, BASELINE_PATTERNS):
        return ("baseline_report", 0.95, "filename")

    if match_any(filename, MONITORING_PATTERNS):
        return ("monitoring_report", 0.90, "filename")

    if match_any(filename, GHG_PATTERNS):
        return ("ghg_emissions", 0.90, "filename")

    if match_any(filename, LAND_TENURE_PATTERNS):
        return ("land_tenure", 0.85, "filename")

    if match_any(filename, REGISTRY_REVIEW_PATTERNS):
        return ("registry_review", 0.95, "filename")

    if match_any(filename, METHODOLOGY_PATTERNS):
        return ("methodology_reference", 0.90, "filename")

    # File type based classification
    if is_gis_file(filename):
        return ("gis_shapefile", 0.80, "file_type")

    if is_image_file(filename):
        return ("land_cover_map", 0.70, "file_type")

    # Default
    return ("unknown", 0.50, "default")


async def extract_document_metadata(file_path: Path) -> DocumentMetadata:
    """Extract metadata from a document file.

    Args:
        file_path: Path to document

    Returns:
        DocumentMetadata object
    """
    stat = file_path.stat()

    metadata = DocumentMetadata(
        file_size_bytes=stat.st_size,
        creation_date=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
        modification_date=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
    )

    # PDF-specific metadata
    if is_pdf_file(file_path.name):
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata.page_count = len(pdf.pages)
                # Quick check for tables in first few pages
                metadata.has_tables = any(
                    len(page.extract_tables()) > 0
                    for page in pdf.pages[:min(3, len(pdf.pages))]
                )
        except Exception:
            # If PDF extraction fails, just use basic metadata
            pass

    return metadata


async def extract_pdf_text(
    filepath: str,
    page_range: tuple[int, int] | None = None,
    extract_tables: bool = False,
) -> dict[str, Any]:
    """Extract text content from a PDF file with caching.

    Args:
        filepath: Path to PDF file
        page_range: Optional tuple of (start_page, end_page) (1-indexed)
        extract_tables: Whether to extract tables

    Returns:
        Dictionary with extracted text, pages, and metadata

    Raises:
        DocumentExtractionError: If extraction fails
    """
    # Check cache
    cache_key = f"{filepath}:{page_range}:{extract_tables}"
    cached = pdf_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        file_path = Path(filepath)
        if not file_path.exists():
            raise DocumentExtractionError(
                f"PDF file not found: {filepath}",
                details={"filepath": filepath},
            )

        result = {
            "filepath": filepath,
            "pages": [],
            "full_text": "",
            "tables": [] if extract_tables else None,
            "page_count": 0,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        with pdfplumber.open(file_path) as pdf:
            result["page_count"] = len(pdf.pages)

            # Determine page range
            start_page = (page_range[0] - 1) if page_range else 0
            end_page = page_range[1] if page_range else len(pdf.pages)
            end_page = min(end_page, len(pdf.pages))

            # Extract from each page
            for page_num in range(start_page, end_page):
                page = pdf.pages[page_num]
                text = page.extract_text() or ""

                page_data = {
                    "page_number": page_num + 1,  # 1-indexed
                    "text": text,
                    "char_count": len(text),
                }

                # Extract tables if requested
                if extract_tables:
                    tables = page.extract_tables()
                    if tables:
                        page_data["tables"] = tables
                        result["tables"].extend(
                            {
                                "page": page_num + 1,
                                "table_data": table,
                            }
                            for table in tables
                        )

                result["pages"].append(page_data)
                result["full_text"] += f"\n\n--- Page {page_num + 1} ---\n\n{text}"

        # Cache the result
        pdf_cache.set(cache_key, result)

        return result

    except Exception as e:
        raise DocumentExtractionError(
            f"Failed to extract PDF text: {str(e)}",
            details={"filepath": filepath, "error": str(e)},
        )


async def extract_gis_metadata(filepath: str) -> dict[str, Any]:
    """Extract metadata from a GIS shapefile.

    Args:
        filepath: Path to shapefile (.shp) or GeoJSON

    Returns:
        Dictionary with GIS metadata

    Raises:
        DocumentExtractionError: If extraction fails
    """
    # Check cache
    cache_key = filepath
    cached = gis_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        file_path = Path(filepath)
        if not file_path.exists():
            raise DocumentExtractionError(
                f"GIS file not found: {filepath}",
                details={"filepath": filepath},
            )

        result = {
            "filepath": filepath,
            "driver": None,
            "crs": None,
            "bounds": None,
            "feature_count": 0,
            "geometry_type": None,
            "schema": None,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        with fiona.open(file_path) as src:
            result["driver"] = src.driver
            result["crs"] = str(src.crs) if src.crs else None
            result["bounds"] = list(src.bounds) if src.bounds else None
            result["feature_count"] = len(src)
            result["schema"] = dict(src.schema) if src.schema else None

            # Get geometry type from first feature
            if len(src) > 0:
                first_feature = next(iter(src))
                result["geometry_type"] = first_feature.get("geometry", {}).get("type")

        # Cache the result
        gis_cache.set(cache_key, result)

        return result

    except Exception as e:
        raise DocumentExtractionError(
            f"Failed to extract GIS metadata: {str(e)}",
            details={"filepath": filepath, "error": str(e)},
        )


async def get_document_by_id(session_id: str, document_id: str) -> dict[str, Any] | None:
    """Get a specific document from the session.

    Args:
        session_id: Unique session identifier
        document_id: Document identifier

    Returns:
        Document data or None if not found
    """
    state_manager = StateManager(session_id)
    if not state_manager.exists("documents.json"):
        return None

    documents_data = state_manager.read_json("documents.json")
    for doc in documents_data.get("documents", []):
        if doc["document_id"] == document_id:
            return doc

    return None
