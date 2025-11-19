# Registry Review MCP - File Upload Enhancement Specification
## ADDENDUM: Safety Features & Edge Case Handling

**Version:** 1.1 Addendum
**Date:** 2025-11-17
**Author:** Claude (AI Assistant)
**Purpose:** Additional safety features and edge case handling for the file upload tools
**Prerequisite:** Base specification (REGISTRY_MCP_UPLOAD_SPEC.md v1.0)

---

## Overview

This addendum specifies additional safety features and edge case handling to be added to the three upload tools defined in the base specification:
- `create_session_from_uploads`
- `upload_additional_files`
- `start_review_from_uploads`

These features can be implemented **after** the base functionality is working, as they are optional enhancements that improve the user experience but are not required for core functionality.

---

## Priority 1: Duplicate File Handling (HIGH PRIORITY)

### Problem Statement

Users may accidentally upload the same file multiple times within a single upload operation, leading to:
- Wasted storage space
- Duplicate entries in document discovery
- Confusion in evidence extraction (same evidence appearing multiple times)

### Solution: Automatic Deduplication

Add automatic deduplication at two levels:
1. **Filename-based**: Skip files with duplicate filenames
2. **Content-based**: Skip files with identical content (even if filenames differ)

### Implementation

#### New Helper Functions

Add to `src/registry_review_mcp/tools/upload_tools.py`:

```python
import hashlib
from typing import Any


async def deduplicate_by_filename(
    files: list[dict],
    existing_files: set[str] = None
) -> tuple[list[dict], list[str]]:
    """
    Remove duplicate filenames from upload.

    Args:
        files: List of file objects with filename and content_base64
        existing_files: Optional set of already-existing filenames to check against

    Returns:
        - Deduplicated files list
        - List of skipped duplicate filenames
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


async def deduplicate_by_content(
    files: list[dict]
) -> tuple[list[dict], dict]:
    """
    Remove duplicate file contents even if filenames differ.

    Uses SHA256 hash to detect identical content.

    Args:
        files: List of file objects with filename and content_base64

    Returns:
        - Deduplicated files list
        - Mapping of duplicate filename -> original filename
    """
    hash_to_file = {}  # hash -> (filename, file_obj)
    unique_files = []
    duplicates_map = {}  # duplicate_filename -> original_filename

    for file_obj in files:
        content_b64 = file_obj.get("content_base64", "")
        filename = file_obj.get("filename", "")

        # Calculate SHA256 hash
        content_bytes = base64.b64decode(content_b64)
        file_hash = hashlib.sha256(content_bytes).hexdigest()

        if file_hash in hash_to_file:
            # Duplicate content detected
            original_filename = hash_to_file[file_hash][0]
            duplicates_map[filename] = original_filename
        else:
            hash_to_file[file_hash] = (filename, file_obj)
            unique_files.append(file_obj)

    return unique_files, duplicates_map
```

#### Modified `create_session_from_uploads`

Add deduplication before file writing:

```python
async def create_session_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Create session with automatic deduplication"""

    project_name = arguments.get("project_name")
    files = arguments.get("files", [])
    deduplicate = arguments.get("deduplicate", True)  # NEW: default True

    # Validation...
    if not project_name:
        raise ValueError("project_name is required")
    if not files or len(files) == 0:
        raise ValueError("At least one file is required")

    # NEW: Automatic deduplication
    filename_duplicates = []
    content_duplicates = {}
    original_count = len(files)

    if deduplicate:
        # Remove filename duplicates first
        files, filename_duplicates = await deduplicate_by_filename(files)

        # Then remove content duplicates
        files, content_duplicates = await deduplicate_by_content(files)

    # Check if any files remain after deduplication
    if len(files) == 0:
        raise ValueError(
            f"All {original_count} files were duplicates. "
            f"Set deduplicate=false to upload anyway."
        )

    # Continue with temp directory creation and file writing...
    temp_dir = Path(tempfile.mkdtemp(prefix=f"registry-{project_name}-"))

    try:
        saved_files = []
        for file_obj in files:
            filename = file_obj.get("filename")
            content_b64 = file_obj.get("content_base64")

            if not filename or not content_b64:
                continue

            file_content = base64.b64decode(content_b64)
            file_path = temp_dir / filename
            file_path.write_bytes(file_content)
            saved_files.append(filename)

        # Create session...
        session = await create_session(
            project_name=project_name,
            documents_path=str(temp_dir),
            methodology=arguments.get("methodology", "soil-carbon-v1.2.2"),
            project_id=arguments.get("project_id"),
            proponent=arguments.get("proponent"),
            crediting_period=arguments.get("crediting_period")
        )

        # Discover documents...
        discovery = await discover_documents(session_id=session["session_id"])

        # NEW: Include deduplication info in response
        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "session_id": session["session_id"],
                    "temp_directory": str(temp_dir),
                    "files_saved": saved_files,
                    "files_uploaded": original_count,
                    "deduplication": {
                        "enabled": deduplicate,
                        "duplicate_filenames_skipped": filename_duplicates,
                        "duplicate_content_detected": content_duplicates,
                        "total_duplicates_removed": len(filename_duplicates) + len(content_duplicates)
                    },
                    "documents_found": discovery["documents_found"],
                    "documents_classified": discovery["documents_classified"],
                    "documents_by_type": discovery.get("documents_by_type", {}),
                    "next_steps": discovery.get("next_steps", [])
                }, indent=2)
            )
        ]

    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
```

#### New Parameter

Add to input schema for `create_session_from_uploads` and `start_review_from_uploads`:

```json
{
  "deduplicate": {
    "type": "boolean",
    "description": "Automatically remove duplicate files (by filename and content hash). Default: true",
    "default": true
  }
}
```

#### Updated Response Schema

Add to output schema:

```json
{
  "deduplication": {
    "type": "object",
    "description": "Information about files that were deduplicated",
    "properties": {
      "enabled": {
        "type": "boolean",
        "description": "Whether deduplication was enabled"
      },
      "duplicate_filenames_skipped": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of filenames that were skipped as duplicates"
      },
      "duplicate_content_detected": {
        "type": "object",
        "description": "Map of duplicate filename to original filename for content duplicates"
      },
      "total_duplicates_removed": {
        "type": "integer",
        "description": "Total number of duplicate files removed"
      }
    }
  }
}
```

---

## Priority 2: Automatic Session Detection (MEDIUM PRIORITY)

### Problem Statement

Users may upload the same project files multiple times (e.g., lost session ID, browser refresh), creating duplicate sessions for the same project.

### Solution: Session Detection via File Hashes

Before creating a new session, check if an existing session has the same files based on content hashes.

### Implementation

#### New Helper Function

Add to `src/registry_review_mcp/tools/upload_tools.py`:

```python
async def detect_existing_session(
    files: list[dict],
    project_name: str
) -> dict | None:
    """
    Check if a session already exists for these files.

    Uses SHA256 hashes of file contents to detect matching sessions,
    even if filenames differ.

    Args:
        files: List of file objects with content_base64
        project_name: Project name to match

    Returns:
        Existing session data if found (>80% file overlap), None otherwise
    """
    import hashlib
    from difflib import SequenceMatcher

    # Calculate hash of file contents
    file_hashes = set()
    for file_obj in files:
        content = base64.b64decode(file_obj.get("content_base64", ""))
        file_hash = hashlib.sha256(content).hexdigest()
        file_hashes.add(file_hash)

    # Search existing sessions
    sessions_dir = settings.get_sessions_dir()

    for session_dir in sessions_dir.glob("session-*"):
        session_file = session_dir / "session.json"
        if not session_file.exists():
            continue

        session_data = json.loads(session_file.read_text())

        # Fuzzy match on project name (80% similarity)
        session_proj_name = session_data.get("project_metadata", {}).get("project_name", "")
        similarity = SequenceMatcher(None, project_name.lower(), session_proj_name.lower()).ratio()
        if similarity < 0.8:
            continue

        # Load document hashes
        docs_file = session_dir / "documents.json"
        if not docs_file.exists():
            continue

        docs_data = json.loads(docs_file.read_text())
        session_hashes = {doc.get("sha256") for doc in docs_data.get("documents", [])}

        # Check for significant overlap (>80% of files match)
        if len(file_hashes) == 0:
            continue
        overlap = len(file_hashes & session_hashes) / len(file_hashes)

        if overlap > 0.8:
            return session_data

    return None
```

#### Modified `create_session_from_uploads`

Add session detection before creating new session:

```python
async def create_session_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Create session with automatic session detection"""

    project_name = arguments.get("project_name")
    files = arguments.get("files", [])
    force_new = arguments.get("force_new_session", False)  # NEW

    # ... validation and deduplication ...

    # NEW: Check for existing session (unless force_new=true)
    if not force_new:
        existing = await detect_existing_session(files, project_name)
        if existing:
            return [
                types.TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "session_id": existing["session_id"],
                        "existing_session_detected": True,
                        "message": (
                            f"Found existing session for '{project_name}' with matching files. "
                            f"Returning existing session. To create a new session anyway, "
                            f"set force_new_session=true."
                        ),
                        "project_name": existing["project_metadata"]["project_name"],
                        "session_created": existing["created_at"],
                        "workflow_progress": existing.get("workflow_progress", {}),
                        "statistics": existing.get("statistics", {})
                    }, indent=2)
                )
            ]

    # Continue with normal session creation...
```

#### New Parameter

Add to input schema:

```json
{
  "force_new_session": {
    "type": "boolean",
    "description": "Force creation of new session even if existing session with same files is detected. Default: false",
    "default": false
  }
}
```

#### Updated Response Schema

Add to output schema:

```json
{
  "existing_session_detected": {
    "type": "boolean",
    "description": "Whether an existing session was found and returned"
  }
}
```

---

## Priority 3: Session Resume Tool (LOW PRIORITY)

### Problem Statement

If a user loses their session ID or the workflow is interrupted, they should be able to resume from where they left off.

### Solution: Resume Tool

Add a new tool `resume_session_from_uploads` that:
1. Attempts to find existing session by files + project name
2. Returns session status and suggests next step
3. Falls back to creating new session if none found

### Implementation

#### New Tool

Add to `src/registry_review_mcp/tools/upload_tools.py`:

```python
async def resume_session_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Resume an existing session or create new one if not found.

    Attempts to detect existing session for the project. If found,
    returns session details and workflow progress. If not found,
    creates new session.

    This is a convenience tool that combines session detection with
    automatic fallback to session creation.
    """
    project_name = arguments.get("project_name")
    files = arguments.get("files", [])

    # Try to find existing session
    existing = await detect_existing_session(files, project_name)

    if existing:
        session_id = existing["session_id"]
        workflow_progress = existing.get("workflow_progress", {})

        # Determine next step
        next_stage = determine_next_workflow_stage(workflow_progress)

        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "session_id": session_id,
                    "resumed": True,
                    "project_name": existing["project_metadata"]["project_name"],
                    "workflow_progress": workflow_progress,
                    "next_stage": next_stage,
                    "message": f"Resumed existing session. Next step: {next_stage}",
                    "statistics": existing.get("statistics", {})
                }, indent=2)
            )
        ]
    else:
        # No existing session found, create new one
        return await create_session_from_uploads(arguments)


def determine_next_workflow_stage(workflow_progress: dict) -> str:
    """
    Determine what workflow stage should be executed next.

    Args:
        workflow_progress: Dict with stage names as keys and status as values

    Returns:
        Name of next stage to execute
    """
    workflow_stages = [
        "initialize",
        "document_discovery",
        "evidence_extraction",
        "cross_validation",
        "report_generation",
        "human_review",
        "complete"
    ]

    for stage in workflow_stages:
        status = workflow_progress.get(stage, "pending")
        if status in ["pending", "in_progress"]:
            return stage

    return "complete"
```

#### Tool Registration

Add to `server.py` in `list_tools()`:

```python
types.Tool(
    name="resume_session_from_uploads",
    description=(
        "Resume an existing registry review session or create new one if not found. "
        "Attempts to detect existing session for the project by matching uploaded files. "
        "If found, returns session status and suggests next workflow step. "
        "If not found, automatically creates a new session. "
        "This is useful when user loses session ID or needs to continue after interruption."
    ),
    inputSchema={
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "Name of the project being reviewed",
                "required": True
            },
            "files": {
                "type": "array",
                "description": "Project document files (same format as create_session_from_uploads)",
                "required": True,
                "items": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "content_base64": {"type": "string"},
                        "mime_type": {"type": "string"}
                    }
                }
            },
            "methodology": {
                "type": "string",
                "default": "soil-carbon-v1.2.2"
            }
        },
        "required": ["project_name", "files"]
    }
)
```

Add handler in `call_tool()`:

```python
elif name == "resume_session_from_uploads":
    from .tools.upload_tools import resume_session_from_uploads
    return await resume_session_from_uploads(arguments)
```

---

## Testing Additions

### Test Deduplication

Add to `tests/test_upload_tools.py`:

```python
async def test_deduplicate_by_filename():
    """Test filename deduplication"""
    files = [
        {"filename": "file1.pdf", "content_base64": "AAAA"},
        {"filename": "file2.pdf", "content_base64": "BBBB"},
        {"filename": "file1.pdf", "content_base64": "CCCC"},  # Duplicate filename
    ]

    unique, duplicates = await deduplicate_by_filename(files)

    assert len(unique) == 2
    assert len(duplicates) == 1
    assert duplicates[0] == "file1.pdf"


async def test_deduplicate_by_content(sample_pdf_base64):
    """Test content-based deduplication"""
    files = [
        {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
        {"filename": "file2.pdf", "content_base64": sample_pdf_base64},  # Same content
        {"filename": "file3.pdf", "content_base64": "different"},
    ]

    unique, duplicates_map = await deduplicate_by_content(files)

    assert len(unique) == 2
    assert "file2.pdf" in duplicates_map
    assert duplicates_map["file2.pdf"] == "file1.pdf"


async def test_create_session_with_duplicates(sample_pdf_base64):
    """Test that duplicates are automatically removed"""
    result = await create_session_from_uploads({
        "project_name": "Test",
        "files": [
            {"filename": "file1.pdf", "content_base64": sample_pdf_base64},
            {"filename": "file1.pdf", "content_base64": sample_pdf_base64},  # Dup
        ],
        "deduplicate": True
    })

    data = json.loads(result[0].text)
    assert data["files_uploaded"] == 2
    assert len(data["files_saved"]) == 1
    assert data["deduplication"]["total_duplicates_removed"] == 1
```

### Test Session Detection

Add to `tests/test_upload_tools.py`:

```python
async def test_detect_existing_session(sample_pdf_base64):
    """Test automatic session detection"""
    # Create initial session
    result1 = await create_session_from_uploads({
        "project_name": "Test Project",
        "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
    })
    session1_id = json.loads(result1[0].text)["session_id"]

    # Try to create again with same files
    result2 = await create_session_from_uploads({
        "project_name": "Test Project",  # Same name
        "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}],  # Same file
        "force_new_session": False
    })

    data2 = json.loads(result2[0].text)
    assert data2["existing_session_detected"] is True
    assert data2["session_id"] == session1_id


async def test_force_new_session(sample_pdf_base64):
    """Test force_new_session parameter"""
    # Create initial session
    await create_session_from_uploads({
        "project_name": "Test",
        "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
    })

    # Force create new session with same files
    result = await create_session_from_uploads({
        "project_name": "Test",
        "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}],
        "force_new_session": True  # Override detection
    })

    data = json.loads(result[0].text)
    assert "existing_session_detected" not in data or data["existing_session_detected"] is False
```

### Test Resume

Add to `tests/test_upload_tools.py`:

```python
async def test_resume_existing_session(sample_pdf_base64):
    """Test resuming an existing session"""
    # Create and progress a session
    create_result = await create_session_from_uploads({
        "project_name": "Resume Test",
        "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
    })
    original_session_id = json.loads(create_result[0].text)["session_id"]

    # Simulate losing session ID, then resume
    resume_result = await resume_session_from_uploads({
        "project_name": "Resume Test",
        "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
    })

    data = json.loads(resume_result[0].text)
    assert data["resumed"] is True
    assert data["session_id"] == original_session_id
    assert "next_stage" in data


async def test_resume_creates_new_if_not_found(sample_pdf_base64):
    """Test resume creates new session if no existing found"""
    result = await resume_session_from_uploads({
        "project_name": "Brand New Project",
        "files": [{"filename": "new.pdf", "content_base64": sample_pdf_base64}]
    })

    data = json.loads(result[0].text)
    assert "resumed" not in data or data["resumed"] is False
    assert data["success"] is True
    assert "session_id" in data
```

---

## Implementation Priority

### Phase 1 (HIGH): Duplicate File Handling
- Implement `deduplicate_by_filename()`
- Implement `deduplicate_by_content()`
- Add `deduplicate` parameter to upload tools
- Add deduplication info to responses
- Write tests

**Rationale:** This prevents immediate user frustration from accidentally uploading duplicates.

### Phase 2 (MEDIUM): Session Detection
- Implement `detect_existing_session()`
- Add `force_new_session` parameter
- Modify `create_session_from_uploads()` to check for existing sessions
- Write tests

**Rationale:** This prevents duplicate sessions but is less critical than duplicate files.

### Phase 3 (LOW): Resume Tool
- Implement `resume_session_from_uploads()`
- Implement `determine_next_workflow_stage()`
- Register new tool
- Write tests

**Rationale:** This is a convenience feature that can be added last.

---

## Backward Compatibility

All new features are **fully backward compatible**:
- New parameters have sensible defaults
- Existing tool behavior unchanged when new parameters not provided
- Response schema extended (not changed)
- No breaking changes to existing tools

---

## Summary

This addendum specifies three safety features:
1. **Duplicate file handling** - Automatic deduplication by filename and content
2. **Session detection** - Prevent creating duplicate sessions
3. **Session resume** - Continue interrupted workflows

All features are optional enhancements that can be implemented incrementally without breaking existing functionality.
