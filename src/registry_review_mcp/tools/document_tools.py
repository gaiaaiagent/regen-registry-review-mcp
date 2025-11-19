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


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of file content for deduplication.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_document_id(content_hash: str) -> str:
    """Generate a unique document ID from content hash.
    """
    # Use first 8 chars of content hash for document ID
    short_hash = content_hash[:8]
    return f"DOC-{short_hash}"


async def discover_documents(session_id: str) -> dict[str, Any]:
    """Discover and index all documents in the session's project directory.
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

    # Recursive scan with progress
    print(f"🔍 Scanning directory: {documents_path}", flush=True)

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

    file_count = len(discovered_files)
    print(f"📄 Found {file_count} supported files to process", flush=True)

    # Process each file with progress updates
    documents = []
    errors = []
    seen_hashes = {}  # Track content hashes for deduplication
    duplicates_skipped = 0

    for i, file_path in enumerate(discovered_files, 1):
        # Show progress every 3 files or on last file
        if i % 3 == 0 or i == file_count:
            percentage = (i / file_count * 100)
            print(f"  ⏳ Processing {i}/{file_count} ({percentage:.0f}%): {file_path.name}", flush=True)

        try:
            # Extract metadata (includes content hash computation)
            metadata = await extract_document_metadata(file_path)

            # Check for duplicate content
            content_hash = metadata.content_hash
            if content_hash in seen_hashes:
                # Skip duplicate - already processed this file content
                original_path = seen_hashes[content_hash]
                duplicates_skipped += 1
                print(f"  ⏭️  Skipping duplicate: {file_path.name} (same as {Path(original_path).name})", flush=True)
                continue

            # Track this hash
            seen_hashes[content_hash] = str(file_path)

            # Generate document ID from content hash
            doc_id = generate_document_id(content_hash)

            # Classify document
            classification, confidence, method = await classify_document_by_filename(
                str(file_path)
            )

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

            # NEW: Convert PDF to markdown for better extraction quality
            if is_pdf_file(file_path.name):
                try:
                    print(f"  🔄 Converting {file_path.name} to markdown...", flush=True)
                    from ..extractors.marker_extractor import convert_pdf_to_markdown
                    from ..intelligence import get_metadata_extractor, get_prior_review_detector

                    # Convert PDF to markdown
                    markdown_result = await convert_pdf_to_markdown(str(file_path))

                    # Store markdown alongside PDF
                    markdown_path = file_path.with_suffix('.md')
                    markdown_path.write_text(markdown_result["markdown"], encoding="utf-8")

                    # Extract intelligent metadata from markdown
                    metadata_extractor = get_metadata_extractor()
                    intelligent_metadata = metadata_extractor.extract_all_metadata(
                        text=markdown_result["markdown"],
                        filename=file_path.name
                    )

                    # Detect and analyze if this is a prior review
                    prior_review_detector = get_prior_review_detector()
                    prior_review_analysis = prior_review_detector.analyze_document(
                        text=markdown_result["markdown"],
                        filename=file_path.name
                    )

                    # Add markdown reference and intelligent metadata to document
                    doc_dict = document.model_dump(mode="json")
                    doc_dict["markdown_path"] = str(markdown_path)
                    doc_dict["has_markdown"] = True
                    doc_dict["markdown_char_count"] = len(markdown_result["markdown"])
                    doc_dict["intelligent_metadata"] = intelligent_metadata
                    doc_dict["prior_review_analysis"] = prior_review_analysis
                    documents.append(doc_dict)

                    print(f"  ✅ Markdown saved: {markdown_path.name} ({len(markdown_result['markdown']):,} chars)", flush=True)

                except Exception as e:
                    # If markdown conversion fails, still add document without markdown
                    print(f"  ⚠️  Markdown conversion failed for {file_path.name}: {str(e)}", flush=True)
                    doc_dict = document.model_dump(mode="json")
                    doc_dict["markdown_path"] = None
                    doc_dict["has_markdown"] = False
                    doc_dict["markdown_error"] = str(e)
                    documents.append(doc_dict)
            else:
                # Non-PDF files don't need markdown conversion
                documents.append(document.model_dump(mode="json"))

            # Update classification summary
            classification_summary[classification] = (
                classification_summary.get(classification, 0) + 1
            )

        except PermissionError as e:
            error_msg = f"Cannot read {file_path.name}: Permission denied"
            print(f"⚠️  {error_msg}", flush=True)
            errors.append({
                "filepath": str(file_path),
                "filename": file_path.name,
                "error_type": "permission_denied",
                "message": error_msg,
                "recovery_steps": [
                    f"Check file permissions: chmod 644 {file_path}",
                    f"Ensure you have read access to the file",
                    "Contact system administrator if needed"
                ]
            })
        except Exception as e:
            error_type = type(e).__name__
            error_msg = f"Failed to process {file_path.name}: {str(e)}"
            print(f"⚠️  {error_msg}", flush=True)

            # Provide specific recovery guidance based on error type
            recovery_steps = []
            if "PDF" in str(e) or "pdf" in str(e).lower():
                recovery_steps = [
                    "The PDF file may be corrupted or encrypted",
                    f"Try opening {file_path.name} in a PDF viewer to verify it's valid",
                    "Consider re-downloading or re-scanning the document"
                ]
            elif "shapefile" in str(e).lower() or ".shp" in str(file_path):
                recovery_steps = [
                    "Shapefile may be missing required components (.shp, .shx, .dbf)",
                    f"Verify all shapefile components are present in {file_path.parent}",
                    "Try re-exporting the shapefile from GIS software"
                ]
            else:
                recovery_steps = [
                    f"Verify the file is not corrupted: {file_path.name}",
                    "Check file format is supported (.pdf, .shp, .geojson, .tif)",
                    "Try re-processing the file or contact support"
                ]

            errors.append({
                "filepath": str(file_path),
                "filename": file_path.name,
                "error_type": error_type,
                "message": error_msg,
                "recovery_steps": recovery_steps
            })

    # Show completion with error summary
    print(f"✅ Discovery complete: {len(documents)} unique documents classified", flush=True)
    if duplicates_skipped > 0:
        print(f"  ⏭️  Skipped {duplicates_skipped} duplicate file(s)", flush=True)
    if errors:
        print(f"⚠️  {len(errors)} file(s) could not be processed (see errors below)", flush=True)

    # Save document index with errors
    documents_data = {
        "documents": documents,
        "total_count": len(documents),
        "duplicates_skipped": duplicates_skipped,
        "classification_summary": classification_summary,
        "errors": errors,
        "error_count": len(errors),
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
                "duplicates_skipped": duplicates_skipped,
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
        "duplicates_skipped": duplicates_skipped,
        "classification_summary": classification_summary,
        "documents": documents,
    }


async def classify_document_by_filename(filepath: str) -> tuple[str, float, str]:
    """Classify document based on filename patterns.
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
    """
    stat = file_path.stat()

    # Compute content hash for deduplication
    content_hash = compute_file_hash(file_path)

    metadata = DocumentMetadata(
        file_size_bytes=stat.st_size,
        creation_date=datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc),
        modification_date=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        content_hash=content_hash,
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
    """Extract text content from a PDF file using marker for high-quality conversion.
    """
    # Import marker extractor
    from ..extractors.marker_extractor import (
        convert_pdf_to_markdown,
        extract_tables_from_markdown,
    )

    # Use marker for conversion
    result = await convert_pdf_to_markdown(filepath, page_range)

    # Extract tables from markdown if requested
    tables = None
    if extract_tables:
        tables = extract_tables_from_markdown(result["markdown"])

    # Format result with backward compatibility
    return {
        "filepath": filepath,
        "markdown": result["markdown"],  # NEW: Full markdown
        "full_text": result["markdown"],  # Backward compat (same as markdown)
        "tables": tables,
        "images": result["images"],
        "page_count": result["page_count"],
        "extracted_at": result["extracted_at"],
        "extraction_method": "marker",
        "metadata": result.get("metadata", {}),
    }


async def extract_gis_metadata(filepath: str) -> dict[str, Any]:
    """Extract metadata from a GIS shapefile.
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
    """
    state_manager = StateManager(session_id)
    if not state_manager.exists("documents.json"):
        return None

    documents_data = state_manager.read_json("documents.json")
    for doc in documents_data.get("documents", []):
        if doc["document_id"] == document_id:
            return doc

    return None
