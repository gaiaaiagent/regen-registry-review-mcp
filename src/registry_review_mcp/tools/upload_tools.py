"""File upload tools for registry review.

Provides tools that accept file content directly (as base64) instead of
requiring files to exist on the filesystem. Enables seamless integration
with web applications, chat interfaces, and APIs.
"""

import base64
import hashlib
import tempfile
import shutil
import re
import json
import os
from pathlib import Path
from typing import Any
from difflib import SequenceMatcher

from . import session_tools, document_tools, evidence_tools
from ..models.errors import SessionNotFoundError
from ..config.settings import settings


def _sanitize_project_name(project_name: str) -> str:
    """Sanitize project name for use in directory names.
    """
    # Replace spaces and special chars with hyphens
    sanitized = re.sub(r'[^\w\s-]', '', project_name)
    sanitized = re.sub(r'[-\s]+', '-', sanitized)
    return sanitized.lower().strip('-')


def _resolve_file_path(path_str: str) -> Path:
    """Resolve file path, handling ElizaOS upload URL paths.
    """
    path = Path(path_str)

    # If already absolute and exists, use as-is
    if path.is_absolute() and path.exists():
        return path

    # Check for ElizaOS media URL pattern
    if str(path).startswith('/media/uploads/'):
        # Try to find ElizaOS installation
        possible_roots = [
            Path.cwd(),  # Current working directory
            Path.cwd().parent,  # Parent directory
            Path.home() / 'Workspace/RegenAI/eliza',  # Common dev location
        ]

        # Also check ELIZA_ROOT environment variable
        if 'ELIZA_ROOT' in os.environ:
            possible_roots.insert(0, Path(os.environ['ELIZA_ROOT']))

        # Convert /media/uploads/... to .eliza/data/uploads/...
        relative_part = str(path).replace('/media/', '')

        for root in possible_roots:
            # Try standard ElizaOS data directory structure
            candidate = root / 'packages/cli/.eliza/data' / relative_part

            if candidate.exists():
                return candidate

        # Also try without packages/cli prefix (for different ElizaOS setups)
        for root in possible_roots:
            candidate = root / '.eliza/data' / relative_part

            if candidate.exists():
                return candidate

    # If path is relative, try resolving from current directory
    if not path.is_absolute():
        candidate = Path.cwd() / path
        if candidate.exists():
            return candidate

    # Return original path (will fail validation if doesn't exist)
    return path


def process_file_input(file_obj: dict[str, Any], index: int) -> dict[str, str]:
    """Process file input from either base64 content or file path.
    """
    if not isinstance(file_obj, dict):
        raise ValueError(f"File at index {index} must be a dictionary")

    # Extract filename (may be in 'filename' or 'name' field for compatibility)
    filename = file_obj.get("filename") or file_obj.get("name")

    # If no filename provided but path exists, extract filename from path
    if not filename and "path" in file_obj:
        filename = Path(file_obj["path"]).name

    if not filename:
        raise ValueError(
            f"File at index {index} is missing 'filename' or 'name' field "
            f"and no path to extract filename from"
        )

    # Check if base64 content is provided
    if "content_base64" in file_obj and file_obj["content_base64"]:
        # Validate base64 is not empty
        if not file_obj["content_base64"].strip():
            raise ValueError(f"File '{filename}' has empty content_base64")

        return {
            "filename": filename,
            "content_base64": file_obj["content_base64"],
        }

    # Check if file path is provided
    if "path" in file_obj and file_obj["path"]:
        file_path_str = file_obj["path"]

        # Resolve path (handles ElizaOS URL paths like /media/uploads/...)
        file_path = _resolve_file_path(file_path_str)

        # Security validation: resolved path must be absolute
        if not file_path.is_absolute():
            raise ValueError(
                f"File '{filename}' resolved to relative path '{file_path}'. "
                "Only absolute paths are allowed for security reasons."
            )

        # Security validation: path must exist and be a file
        if not file_path.exists():
            raise ValueError(
                f"File '{filename}' path does not exist: {file_path}\n"
                f"Original path: {file_path_str}"
            )

        if not file_path.is_file():
            raise ValueError(
                f"File '{filename}' path is not a file: {file_path}\n"
                f"Original path: {file_path_str}"
            )

        # Security validation: prevent directory traversal
        try:
            file_path.resolve(strict=True)
        except Exception as e:
            raise ValueError(
                f"File '{filename}' path resolution failed (possible directory traversal): {file_path_str}"
            ) from e

        # Read file and encode to base64
        try:
            file_content = file_path.read_bytes()
            content_base64 = base64.b64encode(file_content).decode("utf-8")
        except Exception as e:
            raise ValueError(
                f"Failed to read file '{filename}' from path '{file_path_str}': {str(e)}"
            ) from e

        return {
            "filename": filename,
            "content_base64": content_base64,
        }

    # Neither content_base64 nor path provided
    raise ValueError(
        f"File '{filename}' at index {index} must have either 'content_base64' or 'path' field"
    )


def deduplicate_by_filename(
    files: list[dict[str, str]],
    existing_files: set[str] | None = None,
) -> tuple[list[dict[str, str]], list[str]]:
    """Remove duplicate filenames from upload.
    """
    seen_names = existing_files or set()
    unique_files = []
    duplicates = []

    for file_obj in files:
        filename = file_obj.get("filename", "")

        if filename in seen_names:
            duplicates.append(filename)
        else:
            seen_names.add(filename)
            unique_files.append(file_obj)

    return unique_files, duplicates


def deduplicate_by_content(
    files: list[dict[str, str]],
) -> tuple[list[dict[str, str]], dict[str, str]]:
    """Remove duplicate file contents even if filenames differ.
    """
    hash_to_file: dict[str, tuple[str, dict[str, str]]] = {}  # hash -> (filename, file_obj)
    unique_files = []
    duplicates_map = {}  # duplicate_filename -> original_filename

    for file_obj in files:
        content_b64 = file_obj.get("content_base64", "")
        filename = file_obj.get("filename", "")

        # Calculate SHA256 hash
        try:
            content_bytes = base64.b64decode(content_b64)
            file_hash = hashlib.sha256(content_bytes).hexdigest()
        except Exception:
            # If we can't decode, treat as unique
            unique_files.append(file_obj)
            continue

        if file_hash in hash_to_file:
            # Duplicate content detected
            original_filename = hash_to_file[file_hash][0]
            duplicates_map[filename] = original_filename
        else:
            hash_to_file[file_hash] = (filename, file_obj)
            unique_files.append(file_obj)

    return unique_files, duplicates_map


async def detect_existing_session(
    files: list[dict[str, str]],
    project_name: str,
) -> dict[str, Any] | None:
    """Check if a session already exists for these files.

    Uses universal duplicate detection that works across all source types.
    """
    # Calculate hash of file contents
    file_hashes = set()
    for file_obj in files:
        try:
            content = base64.b64decode(file_obj.get("content_base64", ""))
            file_hash = hashlib.sha256(content).hexdigest()
            file_hashes.add(file_hash)
        except Exception:
            # Skip files that can't be decoded
            continue

    if not file_hashes:
        return None

    # Use universal duplicate detection from document_tools
    duplicate_result = await document_tools.detect_duplicates(project_name, file_hashes)

    if duplicate_result:
        # Return session data (unwrap from detect_duplicates response)
        return duplicate_result["session"]

    return None


async def create_session_from_uploads(
    project_name: str,
    files: list[dict[str, str]],
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
    deduplicate: bool = True,
    force_new_session: bool = False,
) -> dict[str, Any]:
    """Create a new registry review session from uploaded file content.
    """
    # Validate inputs
    if not project_name or not project_name.strip():
        raise ValueError("project_name is required and cannot be empty")

    if not files or len(files) == 0:
        raise ValueError("At least one file is required")

    # Process and normalize file inputs (supports both base64 and path formats)
    normalized_files = []
    for idx, file in enumerate(files):
        normalized_file = process_file_input(file, idx)
        normalized_files.append(normalized_file)

    # Use normalized files for the rest of the function
    files = normalized_files

    # Check for existing session (unless force_new_session=True)
    if not force_new_session:
        existing = await detect_existing_session(files, project_name)
        if existing:
            # Return existing session info
            return {
                "success": True,
                "session_id": existing["session_id"],
                "existing_session_detected": True,
                "project_name": existing["project_metadata"]["project_name"],
                "session_created": existing.get("created_at", "Unknown"),
                "workflow_progress": existing.get("workflow_progress", {}),
                "statistics": existing.get("statistics", {}),
                "message": (
                    f"Found existing session for '{project_name}' with matching files. "
                    f"Returning existing session. To create a new session anyway, "
                    f"set force_new_session=True."
                ),
            }

    # Track deduplication for response
    original_file_count = len(files)
    filename_duplicates: list[str] = []
    content_duplicates: dict[str, str] = {}

    # Apply deduplication if enabled
    if deduplicate:
        # Remove filename duplicates first
        files, filename_duplicates = deduplicate_by_filename(files)

        # Then remove content duplicates
        files, content_duplicates = deduplicate_by_content(files)

        # Check if any files remain after deduplication
        if len(files) == 0:
            total_dupes = len(filename_duplicates) + len(content_duplicates)
            raise ValueError(
                f"All {original_file_count} files were duplicates. "
                f"Set deduplicate=False to upload anyway."
            )

    # Create temporary directory
    sanitized_name = _sanitize_project_name(project_name)
    temp_dir = None

    try:
        temp_dir = Path(tempfile.mkdtemp(prefix=f"registry-{sanitized_name}-"))

        # Write files to temp directory
        files_saved = []
        for file in files:
            filename = file["filename"]
            content_base64 = file["content_base64"]

            # Decode base64 content
            try:
                file_content = base64.b64decode(content_base64)
            except Exception as e:
                raise ValueError(
                    f"Failed to decode base64 content for '{filename}': {str(e)}"
                ) from e

            # Write to temp directory
            file_path = temp_dir / filename
            file_path.write_bytes(file_content)
            files_saved.append(filename)

        # Create session using the temp directory
        session_result = await session_tools.create_session(
            project_name=project_name,
            documents_path=str(temp_dir),
            methodology=methodology,
            project_id=project_id,
            proponent=proponent,
            crediting_period=crediting_period,
        )

        session_id = session_result["session_id"]

        # Discover documents
        discovery_result = await document_tools.discover_documents(session_id)

        # Return combined results with deduplication info
        return {
            "success": True,
            "session_id": session_id,
            "temp_directory": str(temp_dir),
            "files_uploaded": original_file_count,
            "files_saved": files_saved,
            "deduplication": {
                "enabled": deduplicate,
                "duplicate_filenames_skipped": filename_duplicates,
                "duplicate_content_detected": content_duplicates,
                "total_duplicates_removed": len(filename_duplicates) + len(content_duplicates),
            },
            "documents_found": discovery_result["documents_found"],
            "documents_classified": discovery_result["documents_found"],
            "documents_by_type": discovery_result["classification_summary"],
            "next_steps": [
                f"Run extract_evidence('{session_id}') to map requirements to documents",
                "Or use /evidence-extraction prompt for guided workflow",
            ],
        }

    except Exception as e:
        # Clean up temp directory on error
        if temp_dir and temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise


async def upload_additional_files(
    session_id: str,
    files: list[dict[str, str]],
) -> dict[str, Any]:
    """Add additional files to an existing session.
    """
    # Validate inputs
    if not files or len(files) == 0:
        raise ValueError("At least one file is required")

    # Process and normalize file inputs (supports both base64 and path formats)
    normalized_files = []
    for idx, file in enumerate(files):
        normalized_file = process_file_input(file, idx)
        normalized_files.append(normalized_file)

    # Use normalized files for the rest of the function
    files = normalized_files

    # Load session to get documents path
    session_data = await session_tools.load_session(session_id)
    documents_path = Path(session_data["project_metadata"]["documents_path"])

    if not documents_path.exists():
        raise ValueError(
            f"Documents directory not found: {documents_path}. "
            "The session may have been created with a temporary directory that no longer exists."
        )

    # Write files to session directory
    files_added = []
    written_files = []  # Track for cleanup on error

    try:
        for file in files:
            filename = file["filename"]
            content_base64 = file["content_base64"]

            file_path = documents_path / filename

            # Check if file already exists
            if file_path.exists():
                raise ValueError(
                    f"File already exists in session directory: {filename}. "
                    "Please use a different filename or delete the existing file first."
                )

            # Decode base64 content
            try:
                file_content = base64.b64decode(content_base64)
            except Exception as e:
                raise ValueError(
                    f"Failed to decode base64 content for '{filename}': {str(e)}"
                ) from e

            # Write file
            file_path.write_bytes(file_content)
            written_files.append(file_path)
            files_added.append(filename)

        # Re-run document discovery
        discovery_result = await document_tools.discover_documents(session_id)

        return {
            "success": True,
            "session_id": session_id,
            "files_added": files_added,
            "documents_found": discovery_result["documents_found"],
            "documents_classified": discovery_result["documents_found"],
            "documents_by_type": discovery_result["classification_summary"],
        }

    except Exception as e:
        # Clean up partially written files on error
        for file_path in written_files:
            if file_path.exists():
                file_path.unlink()
        raise


async def start_review_from_uploads(
    project_name: str,
    files: list[dict[str, str]],
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
    auto_extract: bool = True,
    deduplicate: bool = True,
    force_new_session: bool = False,
) -> dict[str, Any]:
    """One-step tool to create session, upload files, and optionally extract evidence.
    """
    # Create session from uploads
    session_result = await create_session_from_uploads(
        project_name=project_name,
        files=files,
        methodology=methodology,
        project_id=project_id,
        proponent=proponent,
        crediting_period=crediting_period,
        deduplicate=deduplicate,
        force_new_session=force_new_session,
    )

    session_id = session_result["session_id"]
    response = {"session_creation": session_result}

    # Optionally extract evidence
    if auto_extract and session_result["documents_found"] > 0:
        try:
            evidence_result = await evidence_tools.extract_all_evidence(session_id)
            response["evidence_extraction"] = evidence_result
        except Exception as e:
            # Include error but don't fail the whole operation
            response["evidence_extraction"] = {
                "success": False,
                "error": str(e),
                "message": "Session created successfully but evidence extraction failed. You can run extract_evidence manually.",
            }

    return response
