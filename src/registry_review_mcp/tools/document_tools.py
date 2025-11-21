"""Document processing tools for discovery, classification, and extraction."""

import base64
import hashlib
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from difflib import SequenceMatcher
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
from ..models.schemas import Document, DocumentMetadata, DocumentSource
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
from ..utils.state import StateManager, get_session_or_raise


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


async def detect_duplicates(
    project_name: str,
    file_hashes: set[str],
) -> dict[str, Any] | None:
    """Detect existing sessions with similar content.

    Universal duplicate detection that works for all source types:
    - Compares project names (80% fuzzy match)
    - Compares file content hashes (80% overlap)

    Args:
        project_name: Project name to compare against
        file_hashes: Set of SHA256 file hashes to compare

    Returns:
        Dict with session data and overlap info if duplicate found, None otherwise:
        {
            "session": {...},  # Session data
            "overlap_percent": 85.5,  # Percentage of file overlap
            "name_similarity": 0.92  # Project name similarity score
        }
    """
    if not file_hashes:
        return None

    # Search existing sessions
    sessions_dir = settings.sessions_dir
    if not sessions_dir.exists():
        return None

    for session_dir in sessions_dir.glob("session-*"):
        session_file = session_dir / "session.json"
        if not session_file.exists():
            continue

        try:
            state_manager = StateManager(session_dir.name)
            session_data = state_manager.read_json("session.json")
        except Exception:
            continue

        # Fuzzy match on project name (80% similarity)
        session_proj_name = session_data.get("project_metadata", {}).get("project_name", "")
        similarity = SequenceMatcher(None, project_name.lower(), session_proj_name.lower()).ratio()
        if similarity < 0.8:
            continue

        # Collect hashes from all document sources in this session
        session_hashes = set()
        document_sources = session_data.get("document_sources", [])

        for source in document_sources:
            source_type = source.get("source_type")
            metadata = source.get("metadata", {})

            if source_type == "upload":
                # For uploads, scan the temp directory
                directory = metadata.get("directory")
                if directory:
                    dir_path = Path(directory)
                    if dir_path.exists():
                        for file_path in dir_path.glob("*"):
                            if file_path.is_file():
                                try:
                                    session_hashes.add(compute_file_hash(file_path))
                                except Exception:
                                    continue

            elif source_type == "path":
                # For paths, scan the external directory
                path = metadata.get("path")
                if path:
                    path_obj = Path(path)
                    if path_obj.exists():
                        for file_path in path_obj.rglob("*"):
                            if file_path.is_file():
                                try:
                                    session_hashes.add(compute_file_hash(file_path))
                                except Exception:
                                    continue

        # Also check legacy documents_path for backward compatibility
        documents_path_str = session_data.get("project_metadata", {}).get("documents_path")
        if documents_path_str:
            documents_path = Path(documents_path_str)
            if documents_path.exists():
                for file_path in documents_path.rglob("*"):
                    if file_path.is_file():
                        try:
                            session_hashes.add(compute_file_hash(file_path))
                        except Exception:
                            continue

        # Check for significant overlap (>80% of files match)
        if len(file_hashes) == 0 or len(session_hashes) == 0:
            continue

        overlap = len(file_hashes & session_hashes) / len(file_hashes)

        if overlap > 0.8:
            return {
                "session": session_data,
                "overlap_percent": overlap * 100,
                "name_similarity": similarity,
            }

    return None


async def add_documents(
    session_id: str,
    source: dict[str, Any],
    check_duplicates: bool = True,
) -> dict[str, Any]:
    """Add document sources to session.

    Stage 1b: Add sources before discovery.
    Can be called multiple times to add different sources.

    Args:
        session_id: Existing session ID
        source: Source specification (one of):
            - Upload: {"type": "upload", "files": [{filename, content_base64}, ...]}
            - Path: {"type": "path", "path": "/absolute/path"}
            - Link: {"type": "link", "url": "https://..."} [future]
        check_duplicates: Detect existing sessions with similar content

    Returns:
        Result dict with files_added, duplicate_warning, etc.

    Raises:
        ValueError: If source type invalid or files missing
        SessionNotFoundError: If session doesn't exist
    """
    # Load session
    state_manager = get_session_or_raise(session_id)
    session_data = state_manager.read_json("session.json")

    source_type = source.get("type")
    if not source_type:
        raise ValueError("Source must have 'type' field")

    if source_type not in ["upload", "path", "link"]:
        raise ValueError(f"Invalid source type: {source_type}. Must be 'upload', 'path', or 'link'")

    # Initialize result
    result = {
        "session_id": session_id,
        "source_type": source_type,
        "files_added": 0,
        "duplicate_warning": None,
    }

    # Process based on source type
    if source_type == "upload":
        files = source.get("files", [])
        if not files:
            raise ValueError("Upload source must have 'files' list")

        # Import helper from upload_tools
        from . import upload_tools

        # Normalize files (supports both base64 and path format)
        normalized_files = []
        for idx, file in enumerate(files):
            normalized_file = upload_tools.process_file_input(file, idx)
            normalized_files.append(normalized_file)

        # Compute hashes for duplicate detection
        file_hashes = set()
        for file_obj in normalized_files:
            try:
                content = base64.b64decode(file_obj.get("content_base64", ""))
                file_hash = hashlib.sha256(content).hexdigest()
                file_hashes.add(file_hash)
            except Exception:
                continue

        # Check for duplicates if enabled
        if check_duplicates and file_hashes:
            project_name = session_data.get("project_metadata", {}).get("project_name", "")
            existing = await detect_duplicates(project_name, file_hashes)
            if existing:
                existing_session = existing["session"]
                overlap_pct = existing["overlap_percent"]
                name_similarity_pct = existing["name_similarity"] * 100
                result["duplicate_warning"] = {
                    "existing_session_id": existing_session["session_id"],
                    "project_name": existing_session["project_metadata"]["project_name"],
                    "created_at": existing_session.get("created_at"),
                    "file_overlap_percent": overlap_pct,
                    "name_similarity_percent": name_similarity_pct,
                    "message": (
                        f"Found existing session '{existing_session['project_metadata']['project_name']}' "
                        f"with {overlap_pct:.1f}% file overlap and {name_similarity_pct:.1f}% name similarity"
                    ),
                }

        # Create temp directory for uploads
        from . import upload_tools
        sanitized_name = upload_tools._sanitize_project_name(
            session_data["project_metadata"]["project_name"]
        )
        temp_dir = Path(tempfile.mkdtemp(prefix=f"registry-{sanitized_name}-"))

        # Write files to temp directory
        files_saved = []
        try:
            for file in normalized_files:
                filename = file["filename"]
                content_base64 = file["content_base64"]

                # Decode and write
                file_content = base64.b64decode(content_base64)
                file_path = temp_dir / filename
                file_path.write_bytes(file_content)
                files_saved.append(filename)

            # Add source to session
            doc_source = DocumentSource(
                source_type="upload",
                added_at=datetime.now(timezone.utc),
                metadata={
                    "directory": str(temp_dir),
                    "file_count": len(files_saved),
                    "files": files_saved,
                },
            )

            # Update session with new source
            document_sources = session_data.get("document_sources", [])
            document_sources.append(doc_source.model_dump(mode="json"))

            state_manager.update_json("session.json", {"document_sources": document_sources})

            result["files_added"] = len(files_saved)
            result["message"] = f"Added {len(files_saved)} files via upload"

        except Exception as e:
            # Cleanup on error
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    elif source_type == "path":
        path_str = source.get("path")
        if not path_str:
            raise ValueError("Path source must have 'path' field")

        # Validate path
        path = Path(path_str)
        if not path.exists():
            raise ValueError(f"Path does not exist: {path_str}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {path_str}")

        path = path.absolute()

        # Compute hashes for duplicate detection
        file_hashes = set()
        file_count = 0
        for file_path in path.rglob("*"):
            if file_path.is_file():
                try:
                    file_hashes.add(compute_file_hash(file_path))
                    file_count += 1
                except Exception:
                    continue

        # Check for duplicates if enabled
        if check_duplicates and file_hashes:
            project_name = session_data.get("project_metadata", {}).get("project_name", "")
            existing = await detect_duplicates(project_name, file_hashes)
            if existing:
                existing_session = existing["session"]
                overlap_pct = existing["overlap_percent"]
                name_similarity_pct = existing["name_similarity"] * 100
                result["duplicate_warning"] = {
                    "existing_session_id": existing_session["session_id"],
                    "project_name": existing_session["project_metadata"]["project_name"],
                    "created_at": existing_session.get("created_at"),
                    "file_overlap_percent": overlap_pct,
                    "name_similarity_percent": name_similarity_pct,
                    "message": (
                        f"Found existing session '{existing_session['project_metadata']['project_name']}' "
                        f"with {overlap_pct:.1f}% file overlap and {name_similarity_pct:.1f}% name similarity"
                    ),
                }

        # Add source to session
        doc_source = DocumentSource(
            source_type="path",
            added_at=datetime.now(timezone.utc),
            metadata={
                "path": str(path),
                "file_count": file_count,
            },
        )

        # Update session with new source
        document_sources = session_data.get("document_sources", [])
        document_sources.append(doc_source.model_dump(mode="json"))

        state_manager.update_json("session.json", {"document_sources": document_sources})

        result["files_added"] = file_count
        result["message"] = f"Added path source with {file_count} files"

    elif source_type == "link":
        raise ValueError("Link source type not yet implemented")

    return result


async def discover_documents(session_id: str) -> dict[str, Any]:
    """Discover and index all documents from ALL session sources.

    Stage 2: Document Discovery
    Scans all sources added via add_documents() plus legacy documents_path.
    """
    # Load session
    state_manager = get_session_or_raise(session_id)
    session_data = state_manager.read_json("session.json")

    # Collect all paths to scan
    paths_to_scan = []
    sources_scanned = []

    # Scan new document_sources
    document_sources = session_data.get("document_sources", [])
    for source in document_sources:
        source_type = source.get("source_type")
        metadata = source.get("metadata", {})

        if source_type == "upload":
            directory = metadata.get("directory")
            if directory:
                dir_path = Path(directory)
                if dir_path.exists():
                    paths_to_scan.append(dir_path)
                    sources_scanned.append({
                        "type": "upload",
                        "path": str(dir_path),
                    })

        elif source_type == "path":
            path = metadata.get("path")
            if path:
                path_obj = Path(path)
                if path_obj.exists():
                    paths_to_scan.append(path_obj)
                    sources_scanned.append({
                        "type": "path",
                        "path": str(path_obj),
                    })

    # Also check legacy documents_path for backward compatibility
    documents_path_str = session_data.get("project_metadata", {}).get("documents_path")
    if documents_path_str:
        documents_path = Path(documents_path_str)
        if documents_path.exists():
            paths_to_scan.append(documents_path)
            sources_scanned.append({
                "type": "legacy_path",
                "path": str(documents_path),
            })

    if not paths_to_scan:
        return {
            "session_id": session_id,
            "documents_found": 0,
            "sources_scanned": [],
            "classification_summary": {},
            "documents": [],
            "message": "No document sources found. Use add_documents() to add sources.",
        }

    # Discover files from all sources
    discovered_files = []
    classification_summary = {}

    # Supported extensions
    supported_extensions = {".pdf", ".shp", ".geojson", ".tif", ".tiff"}

    # Recursive scan with progress
    print(f"🔍 Scanning {len(paths_to_scan)} source(s)", flush=True)

    for scan_path in paths_to_scan:
        for file_path in scan_path.rglob("*"):
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

            # Document discovery: Just catalog metadata, don't extract content
            # Markdown conversion happens lazily during evidence extraction (Stage 5)
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
        "sources_scanned": sources_scanned,
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
