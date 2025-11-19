# Registry Review MCP - File Upload Enhancement Specification

**Version:** 1.0
**Date:** 2025-11-17
**Author:** Claude (AI Assistant)
**Purpose:** Add file upload capabilities to the Registry Review MCP for seamless integration with web applications and chat interfaces like ElizaOS

---

## Executive Summary

This specification defines new MCP tools that accept file content directly (as base64-encoded data) instead of requiring files to exist on the filesystem. This enhancement makes the Registry Review MCP platform-agnostic and enables seamless integration with web applications, chat interfaces, and APIs where users upload files dynamically.

**Key Benefits:**
- Works with ElizaOS, Claude Desktop, web APIs, and any MCP client
- No filesystem coupling - files don't need to pre-exist on disk
- Backward compatible - existing filesystem-based tools remain unchanged
- Simpler integration - applications just need to base64-encode file content
- Automatic cleanup - temporary directories managed by the MCP

---

## Current Architecture (For Context)

### Existing Tools
The MCP currently provides these filesystem-based tools:

1. **`create_session`** - Requires `documents_path` pointing to a directory on disk
2. **`discover_documents`** - Scans files in the `documents_path` directory
3. **`extract_evidence`** - Reads markdown files from disk for evidence extraction

### Current Limitations
- Files must exist on the filesystem before session creation
- Requires users to manually organize files into a directory structure
- Not suitable for web applications where files are uploaded dynamically
- Tight coupling between MCP and local filesystem

---

## Proposed Enhancements

### Overview
Add three new tools that accept file content directly while maintaining full backward compatibility with existing tools.

### New Tools

#### 1. `create_session_from_uploads`

**Purpose:** Create a new registry review session from uploaded file content.

**Description:**
Accepts file content as base64-encoded strings, creates a temporary directory, writes the files to disk, and initializes a review session. This is ideal for web applications and APIs where files are uploaded by users.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string",
      "description": "Name of the project being reviewed",
      "required": true
    },
    "files": {
      "type": "array",
      "description": "Array of file objects to upload",
      "required": true,
      "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "filename": {
            "type": "string",
            "description": "Filename with extension (e.g., 'ProjectPlan.pdf')",
            "required": true
          },
          "content_base64": {
            "type": "string",
            "description": "File content encoded as base64 string",
            "required": true
          },
          "mime_type": {
            "type": "string",
            "description": "MIME type (e.g., 'application/pdf')",
            "default": "application/pdf"
          }
        },
        "required": ["filename", "content_base64"]
      }
    },
    "methodology": {
      "type": "string",
      "description": "Methodology identifier",
      "default": "soil-carbon-v1.2.2",
      "enum": ["soil-carbon-v1.2.2"]
    },
    "project_id": {
      "type": "string",
      "description": "Optional project ID if known (e.g., 'C06-4997')"
    },
    "proponent": {
      "type": "string",
      "description": "Optional name of project proponent"
    },
    "crediting_period": {
      "type": "string",
      "description": "Optional crediting period (e.g., '2022-2032')"
    }
  },
  "required": ["project_name", "files"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "Whether session creation succeeded"
    },
    "session_id": {
      "type": "string",
      "description": "Unique session identifier"
    },
    "temp_directory": {
      "type": "string",
      "description": "Absolute path to temporary directory containing files"
    },
    "files_saved": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of filenames successfully saved"
    },
    "documents_found": {
      "type": "integer",
      "description": "Number of documents discovered"
    },
    "documents_classified": {
      "type": "integer",
      "description": "Number of documents successfully classified"
    },
    "documents_by_type": {
      "type": "object",
      "description": "Documents grouped by classification type"
    },
    "next_steps": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Suggested next steps in the workflow"
    }
  }
}
```

**Behavior:**
1. Validate input parameters (project_name and files required)
2. Create temporary directory: `tempfile.mkdtemp(prefix=f"registry-{sanitized_project_name}-")`
3. For each file in `files` array:
   - Decode base64 content: `base64.b64decode(content_base64)`
   - Write to temp directory: `(temp_dir / filename).write_bytes(file_content)`
   - Track saved filenames
4. Call existing `create_session()` with `documents_path=str(temp_dir)`
5. Call existing `discover_documents()` with the new session_id
6. Return combined results
7. On error: Clean up temp directory with `shutil.rmtree(temp_dir, ignore_errors=True)`

**Error Handling:**
- Raise `ValueError` if `project_name` is empty
- Raise `ValueError` if `files` array is empty
- Raise `ValueError` if any file is missing `filename` or `content_base64`
- Raise `base64.binascii.Error` if base64 decoding fails
- Clean up temp directory on any error before re-raising

---

#### 2. `upload_additional_files`

**Purpose:** Add additional files to an existing session.

**Description:**
Accepts file content and adds it to an existing session's document directory, then re-runs document discovery. Useful for iterative document submission.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "session_id": {
      "type": "string",
      "description": "Existing session identifier",
      "required": true
    },
    "files": {
      "type": "array",
      "description": "Array of file objects to add",
      "required": true,
      "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "filename": {
            "type": "string",
            "description": "Filename with extension",
            "required": true
          },
          "content_base64": {
            "type": "string",
            "description": "File content encoded as base64",
            "required": true
          },
          "mime_type": {
            "type": "string",
            "description": "MIME type",
            "default": "application/pdf"
          }
        },
        "required": ["filename", "content_base64"]
      }
    }
  },
  "required": ["session_id", "files"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "session_id": {
      "type": "string"
    },
    "files_added": {
      "type": "array",
      "items": {"type": "string"},
      "description": "List of filenames added"
    },
    "documents_found": {
      "type": "integer",
      "description": "Total documents after adding new files"
    },
    "documents_classified": {
      "type": "integer"
    },
    "documents_by_type": {
      "type": "object"
    }
  }
}
```

**Behavior:**
1. Load existing session using `load_session(session_id)`
2. Get `documents_path` from session metadata
3. For each file in `files` array:
   - Check if file already exists: `if (documents_path / filename).exists(): raise ValueError`
   - Decode base64 content
   - Write to documents directory
   - Track added filenames
4. Call `discover_documents(session_id)` to re-scan directory
5. Return updated discovery results

**Error Handling:**
- Raise `ValueError` if session_id doesn't exist
- Raise `ValueError` if filename already exists in session directory
- Raise `ValueError` if files array is empty
- Clean up any partially written files on error

---

#### 3. `start_review_from_uploads`

**Purpose:** One-step tool to create session, upload files, discover documents, and optionally extract evidence.

**Description:**
Combines `create_session_from_uploads` + `discover_documents` + `extract_evidence` for the most streamlined user experience. This is the recommended tool for new integrations.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "project_name": {
      "type": "string",
      "required": true
    },
    "files": {
      "type": "array",
      "required": true,
      "minItems": 1,
      "items": {
        "type": "object",
        "properties": {
          "filename": {"type": "string", "required": true},
          "content_base64": {"type": "string", "required": true},
          "mime_type": {"type": "string", "default": "application/pdf"}
        }
      }
    },
    "methodology": {
      "type": "string",
      "default": "soil-carbon-v1.2.2"
    },
    "project_id": {
      "type": "string"
    },
    "proponent": {
      "type": "string"
    },
    "crediting_period": {
      "type": "string"
    },
    "auto_extract": {
      "type": "boolean",
      "description": "Automatically run evidence extraction (default: true)",
      "default": true
    }
  },
  "required": ["project_name", "files"]
}
```

**Output Schema:**
```json
{
  "type": "object",
  "properties": {
    "session_creation": {
      "type": "object",
      "description": "Results from create_session_from_uploads"
    },
    "evidence_extraction": {
      "type": "object",
      "description": "Results from extract_evidence (if auto_extract=true)"
    }
  }
}
```

**Behavior:**
1. Call `create_session_from_uploads()` with provided arguments
2. Extract `session_id` from results
3. If `auto_extract=true` and `documents_found > 0`:
   - Call `extract_evidence(session_id)`
   - Include results in response
4. Return combined results from both operations

**Error Handling:**
- Propagate errors from `create_session_from_uploads`
- If evidence extraction fails, still return session creation results with error details

---

## Implementation Details

### File Structure

**New files to create:**
```
src/registry_review_mcp/tools/
├── upload_tools.py          # New file - implements the 3 new tools
└── __init__.py              # Update to export new tools
```

**Files to modify:**
```
src/registry_review_mcp/
├── server.py                # Register new tools in list_tools() and call_tool()
└── README.md                # Document new tools and usage examples
```

### Code Organization

**upload_tools.py structure:**
```python
"""
File upload tools for registry review MCP.

Provides tools that accept file content directly (as base64) instead of
requiring files to exist on the filesystem. Enables seamless integration
with web applications and APIs.
"""

import base64
import tempfile
import shutil
from pathlib import Path
from typing import Any
import json

from mcp import types
from ..tools.session_tools import create_session, load_session
from ..tools.document_tools import discover_documents
from ..tools.evidence_tools import extract_evidence


async def create_session_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Implementation of create_session_from_uploads tool"""
    # ... implementation


async def upload_additional_files(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Implementation of upload_additional_files tool"""
    # ... implementation


async def start_review_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """Implementation of start_review_from_uploads tool"""
    # ... implementation
```

### Server Registration

**Modify server.py:**

```python
# In list_tools() - Add new tool definitions
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        # ... existing tools ...

        types.Tool(
            name="create_session_from_uploads",
            description=(
                "Create a new registry review session from uploaded file content. "
                "Accepts files as base64-encoded content instead of requiring "
                "filesystem paths. Ideal for web applications and APIs."
            ),
            inputSchema={
                # ... full schema from above ...
            }
        ),

        types.Tool(
            name="upload_additional_files",
            description=(
                "Add additional files to an existing session. Accepts file content "
                "and adds it to the session's document directory, then re-runs "
                "document discovery."
            ),
            inputSchema={
                # ... full schema from above ...
            }
        ),

        types.Tool(
            name="start_review_from_uploads",
            description=(
                "One-step tool to create a session, upload files, discover documents, "
                "and optionally extract evidence. The easiest way to start a review "
                "when you have uploaded files."
            ),
            inputSchema={
                # ... full schema from above ...
            }
        ),
    ]


# In call_tool() - Add handlers for new tools
@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:

    # ... existing tool handlers ...

    # New upload-based tools
    elif name == "create_session_from_uploads":
        from .tools.upload_tools import create_session_from_uploads
        return await create_session_from_uploads(arguments)

    elif name == "upload_additional_files":
        from .tools.upload_tools import upload_additional_files
        return await upload_additional_files(arguments)

    elif name == "start_review_from_uploads":
        from .tools.upload_tools import start_review_from_uploads
        return await start_review_from_uploads(arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")
```

---

## Testing Requirements

### Unit Tests

Create `tests/test_upload_tools.py`:

```python
import pytest
import base64
from pathlib import Path

from registry_review_mcp.tools.upload_tools import (
    create_session_from_uploads,
    upload_additional_files,
    start_review_from_uploads
)


@pytest.fixture
def sample_pdf_base64():
    """Create a small test PDF encoded as base64"""
    # Minimal PDF content
    pdf_content = b"%PDF-1.4\n%%EOF"
    return base64.b64encode(pdf_content).decode('utf-8')


async def test_create_session_from_uploads_success(sample_pdf_base64):
    """Test successful session creation from uploads"""
    result = await create_session_from_uploads({
        "project_name": "Test Project",
        "files": [
            {
                "filename": "test.pdf",
                "content_base64": sample_pdf_base64,
                "mime_type": "application/pdf"
            }
        ],
        "methodology": "soil-carbon-v1.2.2"
    })

    data = json.loads(result[0].text)
    assert data["success"] is True
    assert "session_id" in data
    assert data["files_saved"] == ["test.pdf"]

    # Verify temp directory was created
    assert Path(data["temp_directory"]).exists()


async def test_create_session_from_uploads_missing_project_name():
    """Test error when project_name is missing"""
    with pytest.raises(ValueError, match="project_name is required"):
        await create_session_from_uploads({
            "files": []
        })


async def test_create_session_from_uploads_no_files():
    """Test error when files array is empty"""
    with pytest.raises(ValueError, match="At least one file is required"):
        await create_session_from_uploads({
            "project_name": "Test",
            "files": []
        })


async def test_upload_additional_files_success(sample_pdf_base64):
    """Test adding files to existing session"""
    # First create a session
    session_result = await create_session_from_uploads({
        "project_name": "Test Project",
        "files": [
            {
                "filename": "file1.pdf",
                "content_base64": sample_pdf_base64
            }
        ]
    })

    session_data = json.loads(session_result[0].text)
    session_id = session_data["session_id"]

    # Add another file
    result = await upload_additional_files({
        "session_id": session_id,
        "files": [
            {
                "filename": "file2.pdf",
                "content_base64": sample_pdf_base64
            }
        ]
    })

    data = json.loads(result[0].text)
    assert data["success"] is True
    assert data["files_added"] == ["file2.pdf"]
    assert data["documents_found"] == 2


async def test_upload_additional_files_duplicate_filename(sample_pdf_base64):
    """Test error when uploading file with duplicate filename"""
    # Create session with file1.pdf
    session_result = await create_session_from_uploads({
        "project_name": "Test Project",
        "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
    })

    session_id = json.loads(session_result[0].text)["session_id"]

    # Try to add another file1.pdf
    with pytest.raises(ValueError, match="File already exists"):
        await upload_additional_files({
            "session_id": session_id,
            "files": [{"filename": "file1.pdf", "content_base64": sample_pdf_base64}]
        })


async def test_start_review_from_uploads_full_workflow(sample_pdf_base64):
    """Test complete review workflow with auto-extraction"""
    result = await start_review_from_uploads({
        "project_name": "Full Test",
        "files": [
            {"filename": "ProjectPlan.pdf", "content_base64": sample_pdf_base64},
            {"filename": "BaselineReport.pdf", "content_base64": sample_pdf_base64}
        ],
        "auto_extract": True
    })

    data = json.loads(result[0].text)
    assert "session_creation" in data
    assert "evidence_extraction" in data
    assert data["session_creation"]["files_saved"] == ["ProjectPlan.pdf", "BaselineReport.pdf"]
```

### Integration Tests

Create `tests/integration/test_upload_workflow.py`:

```python
"""Integration test for complete upload workflow with real files"""

import pytest
import base64
from pathlib import Path


@pytest.mark.integration
async def test_complete_upload_review_workflow():
    """
    Test complete workflow:
    1. Upload files
    2. Create session
    3. Discover documents
    4. Extract evidence
    5. Verify results
    """
    # Use actual test PDF from examples
    test_pdf = Path("examples/22-23/4997Botany22_Public_Project_Plan.pdf")

    with open(test_pdf, 'rb') as f:
        pdf_content = f.read()
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

    # Start review
    result = await start_review_from_uploads({
        "project_name": "Integration Test Project",
        "files": [
            {
                "filename": "ProjectPlan.pdf",
                "content_base64": pdf_base64,
                "mime_type": "application/pdf"
            }
        ],
        "methodology": "soil-carbon-v1.2.2",
        "auto_extract": True
    })

    data = json.loads(result[0].text)

    # Verify session creation
    assert data["session_creation"]["success"] is True
    assert data["session_creation"]["documents_found"] >= 1

    # Verify evidence extraction
    assert "evidence_extraction" in data
    evidence = data["evidence_extraction"]
    assert "coverage_statistics" in evidence
    assert evidence["coverage_statistics"]["requirements_total"] == 23
```

---

## Advanced Features & Safety Mechanisms

### Automatic Session Detection

**Problem:** User uploads the same project files multiple times, potentially creating duplicate sessions.

**Solution:** Implement content-based session detection using file hashes.

#### Implementation:

```python
async def detect_existing_session(
    files: list[dict],
    project_name: str
) -> dict | None:
    """
    Check if a session already exists for these files.

    Uses SHA256 hashes of file contents to detect duplicates,
    even if filenames differ.

    Returns existing session data if found, None otherwise.
    """
    import hashlib

    # Calculate hash of file contents
    file_hashes = set()
    for file_obj in files:
        content = base64.b64decode(file_obj["content_base64"])
        file_hash = hashlib.sha256(content).hexdigest()
        file_hashes.add(file_hash)

    # Search existing sessions for matching file hashes
    sessions_dir = settings.get_sessions_dir()

    for session_dir in sessions_dir.glob("session-*"):
        session_file = session_dir / "session.json"
        if not session_file.exists():
            continue

        session_data = json.loads(session_file.read_text())

        # Check if project name matches (fuzzy)
        if not fuzzy_match(session_data.get("project_name", ""), project_name):
            continue

        # Load document metadata
        docs_file = session_dir / "documents.json"
        if not docs_file.exists():
            continue

        docs_data = json.loads(docs_file.read_text())
        session_hashes = {doc.get("sha256") for doc in docs_data.get("documents", [])}

        # Check if significant overlap (>80% of files match)
        overlap = len(file_hashes & session_hashes) / len(file_hashes)
        if overlap > 0.8:
            return session_data

    return None


def fuzzy_match(str1: str, str2: str, threshold: float = 0.8) -> bool:
    """Simple fuzzy string matching"""
    from difflib import SequenceMatcher
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() > threshold
```

#### Updated `create_session_from_uploads` behavior:

```python
async def create_session_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    project_name = arguments.get("project_name")
    files = arguments.get("files", [])
    force_new = arguments.get("force_new_session", False)

    # Check for existing session (unless force_new=true)
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
                        "session_created": existing["created_at"],
                        "documents_found": existing["statistics"]["documents_found"]
                    }, indent=2)
                )
            ]

    # Continue with normal session creation...
```

#### New parameter for all upload tools:

```json
{
  "force_new_session": {
    "type": "boolean",
    "description": "Force creation of new session even if existing session with same files is detected",
    "default": false
  }
}
```

---

### Duplicate File Handling

**Problem:** User accidentally uploads the same file twice in a single session.

**Solution:** Implement file deduplication at multiple levels.

#### Level 1: Filename Deduplication

```python
async def deduplicate_by_filename(
    files: list[dict],
    existing_files: set[str] = None
) -> tuple[list[dict], list[str]]:
    """
    Remove duplicate filenames from upload.

    Returns:
        - Deduplicated files list
        - List of skipped duplicate filenames
    """
    seen_names = existing_files or set()
    unique_files = []
    duplicates = []

    for file_obj in files:
        filename = file_obj["filename"]

        if filename in seen_names:
            duplicates.append(filename)
        else:
            seen_names.add(filename)
            unique_files.append(file_obj)

    return unique_files, duplicates
```

#### Level 2: Content-Based Deduplication

```python
async def deduplicate_by_content(
    files: list[dict]
) -> tuple[list[dict], dict]:
    """
    Remove duplicate file contents even if filenames differ.

    Returns:
        - Deduplicated files list
        - Mapping of duplicate filename -> original filename
    """
    import hashlib

    hash_to_file = {}  # hash -> first filename seen
    unique_files = []
    duplicates_map = {}  # duplicate_filename -> original_filename

    for file_obj in files:
        content = base64.b64decode(file_obj["content_base64"])
        file_hash = hashlib.sha256(content).hexdigest()
        filename = file_obj["filename"]

        if file_hash in hash_to_file:
            # Same content, different filename
            original = hash_to_file[file_hash]
            duplicates_map[filename] = original
        else:
            hash_to_file[file_hash] = filename
            unique_files.append(file_obj)

    return unique_files, duplicates_map
```

#### Updated upload behavior with deduplication:

```python
async def create_session_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    # ... validation ...

    files = arguments.get("files", [])
    deduplicate = arguments.get("deduplicate", True)

    filename_duplicates = []
    content_duplicates = {}

    if deduplicate:
        # Remove filename duplicates
        files, filename_duplicates = await deduplicate_by_filename(files)

        # Remove content duplicates
        files, content_duplicates = await deduplicate_by_content(files)

    # ... continue with session creation ...

    # Include deduplication info in response
    return [
        types.TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "session_id": session_id,
                "files_saved": saved_files,
                "deduplication": {
                    "duplicate_filenames_skipped": filename_duplicates,
                    "duplicate_content_detected": content_duplicates,
                    "total_duplicates_removed": len(filename_duplicates) + len(content_duplicates)
                },
                # ... rest of response ...
            }, indent=2)
        )
    ]
```

#### New parameters:

```json
{
  "deduplicate": {
    "type": "boolean",
    "description": "Automatically remove duplicate files (by filename and content)",
    "default": true
  },
  "on_duplicate": {
    "type": "string",
    "enum": ["skip", "error", "rename"],
    "description": "How to handle duplicate files: skip (default), raise error, or rename",
    "default": "skip"
  }
}
```

---

### Session Resume & Recovery

**Problem:** User starts a review, session crashes or times out, wants to resume.

**Solution:** Add session resume capabilities.

#### New tool: `resume_session_from_uploads`

```python
async def resume_session_from_uploads(
    arguments: dict[str, Any]
) -> list[types.TextContent]:
    """
    Resume an existing session or create new one if not found.

    Attempts to detect existing session for the project. If found,
    returns session details and allows continuing from last workflow stage.
    If not found, creates new session.
    """
    project_name = arguments.get("project_name")
    files = arguments.get("files", [])

    # Try to find existing session
    existing = await detect_existing_session(files, project_name)

    if existing:
        session_id = existing["session_id"]
        workflow_stage = existing["workflow_progress"]

        # Determine next step based on workflow progress
        next_step = determine_next_step(workflow_stage)

        return [
            types.TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "session_id": session_id,
                    "resumed": True,
                    "workflow_progress": workflow_stage,
                    "next_step": next_step,
                    "message": f"Resumed existing session. Last step: {next_step['last_completed']}"
                }, indent=2)
            )
        ]
    else:
        # No existing session, create new one
        return await create_session_from_uploads(arguments)


def determine_next_step(workflow_progress: dict) -> dict:
    """Determine what workflow step to execute next"""
    stages = [
        "initialize",
        "document_discovery",
        "evidence_extraction",
        "cross_validation",
        "report_generation"
    ]

    for stage in stages:
        status = workflow_progress.get(stage, "pending")
        if status in ["pending", "in_progress"]:
            return {
                "next_stage": stage,
                "last_completed": stages[stages.index(stage) - 1] if stage != "initialize" else None
            }

    return {
        "next_stage": "complete",
        "last_completed": "report_generation"
    }
```

---

### Comprehensive Error Messages

All tools should return detailed, actionable error information:

```python
# Example error response format
{
  "success": false,
  "error": {
    "code": "DUPLICATE_FILES_DETECTED",
    "message": "3 duplicate files detected in upload",
    "details": {
      "duplicates": [
        {
          "filename": "ProjectPlan.pdf",
          "reason": "content_duplicate",
          "matches": "ProjectPlan_v2.pdf"
        }
      ]
    },
    "suggestion": "Set deduplicate=true to automatically skip duplicates, or on_duplicate='rename' to keep all files",
    "recoverable": true
  }
}
```

---

## Usage Examples

### Example 1: ElizaOS Integration

```typescript
// ElizaOS action handler
const pdfAttachments = message.content.attachments.filter(
  att => att.title?.endsWith('.pdf')
);

// Fetch and encode files
const files = [];
for (const att of pdfAttachments) {
  const response = await fetch(getLocalServerUrl(att.url));
  const buffer = Buffer.from(await response.arrayBuffer());
  files.push({
    filename: att.title,
    content_base64: buffer.toString('base64'),
    mime_type: 'application/pdf'
  });
}

// Call MCP tool
const result = await runtime.callMCPTool('registry-review', 'start_review_from_uploads', {
  project_name: "Botany Farm 2022",
  files: files,
  methodology: 'soil-carbon-v1.2.2',
  auto_extract: true
});
```

### Example 2: Python API Integration

```python
import base64
from pathlib import Path

# Read uploaded files
files = []
for uploaded_file in request.files.getlist('documents'):
    content = uploaded_file.read()
    files.append({
        'filename': uploaded_file.filename,
        'content_base64': base64.b64encode(content).decode('utf-8'),
        'mime_type': uploaded_file.content_type
    })

# Call MCP tool
result = await mcp_client.call_tool('start_review_from_uploads', {
    'project_name': request.form['project_name'],
    'files': files,
    'methodology': 'soil-carbon-v1.2.2',
    'auto_extract': True
})
```

### Example 3: Claude Desktop

```
User: I want to review these project documents for registry compliance.
[Uploads 7 PDF files]
