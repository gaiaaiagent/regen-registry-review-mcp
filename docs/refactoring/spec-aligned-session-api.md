# Spec-Aligned Session API Design

**Status**: Implementation Plan
**Created**: 2025-11-20
**Goal**: Align codebase with 8-stage workflow specification

## Problem Statement

Current implementation violates spec's stage separation:
- `create_session()` takes documents_path (combines Stage 1 + 1b)
- `create_session_from_uploads()` combines creation + upload + discovery (Stages 1, 1b, 2)
- Duplicate detection only for uploads (inconsistent UX)
- 31 tests (1111 lines) for upload-specific functionality
- Tight coupling between session creation and document sources

## Spec-Aligned Architecture

### Stage 1: Initialize (Create Session Metadata Only)

```python
async def create_session(
    project_name: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
) -> dict:
    """Create new registry review session.

    Stage 1: Initialize
    - Creates session ID
    - Stores metadata only
    - NO document sources yet

    Returns:
        {
            "session_id": "session-20250120-143025",
            "project_name": "...",
            "methodology": "...",
            "status": "initialized",
            "created_at": "..."
        }
    """
```

### Stage 1b: Add Document Sources

```python
async def add_documents(
    session_id: str,
    source: dict,
    check_duplicates: bool = True,
) -> dict:
    """Add document sources to session.

    Stage 1b: Add sources before discovery
    Can be called multiple times to add different sources.

    Args:
        session_id: Existing session
        source: One of:
          - Upload: {"type": "upload", "files": [{filename, content_base64}, ...]}
          - Path: {"type": "path", "path": "/absolute/path"}
          - Link: {"type": "link", "url": "https://..."} [future]
        check_duplicates: Detect existing sessions with similar content

    Returns:
        {
            "session_id": "...",
            "source_type": "upload|path|link",
            "files_added": 5,
            "duplicate_warning": {...} | None,
            "message": "..."
        }

    Raises:
        DuplicateSessionWarning: If check_duplicates=True and match found
    """
```

### Stage 2: Document Discovery (Enhanced)

```python
async def discover_documents(session_id: str) -> dict:
    """Discover and classify documents from ALL sources.

    Stage 2: Document Discovery
    Scans all sources added via add_documents().

    Internal logic:
    - Reads session's document_sources list
    - For each source:
      - upload: Scan session directory
      - path: Scan external directory
      - link: Fetch from external source [future]
    - Classify all documents
    - Generate inventory

    Returns:
        {
            "session_id": "...",
            "documents_found": 7,
            "sources_scanned": [
                {"type": "upload", "files": 3},
                {"type": "path", "files": 4}
            ],
            "classification_summary": {...},
            "documents": [...]
        }
    """
```

## Data Model Changes

### Session Schema (Enhanced)

```python
class Session(BaseModel):
    session_id: str
    project_metadata: ProjectMetadata
    document_sources: list[DocumentSource] = []  # NEW: Track all sources
    workflow_progress: WorkflowProgress
    statistics: SessionStatistics
    created_at: datetime
    updated_at: datetime
    status: str

class DocumentSource(BaseModel):
    """Tracks a single document source."""
    source_type: Literal["upload", "path", "link"]
    added_at: datetime
    metadata: dict  # Type-specific metadata

    # Example metadata by type:
    # upload: {"temp_directory": "/tmp/...", "file_count": 3}
    # path: {"path": "/absolute/path", "file_count": 4}
    # link: {"url": "https://...", "access_mode": "mirror|reference"}
```

## Universal Duplicate Detection

### Algorithm (Works for All Source Types)

```python
async def detect_duplicates(
    project_name: str,
    file_hashes: set[str],  # SHA256 hashes
) -> dict | None:
    """Detect existing sessions with similar content.

    Works consistently regardless of source type:
    - Computes hashes from uploaded files
    - Computes hashes from path directory
    - Computes hashes from linked sources [future]

    Matching criteria:
    1. Project name 80% similar (fuzzy match)
    2. File content 80% overlap (hash comparison)

    Returns existing session metadata if found, None otherwise.
    """
```

### User Experience

```python
# Upload-based
add_documents(session_id, {
    "type": "upload",
    "files": [...]
})
# ⚠️ Warning: "Found existing session 'Botany Farm 2023' with 95% matching files"
#    User can: [Continue Anyway] [Use Existing] [Cancel]

# Path-based (NOW CONSISTENT!)
add_documents(session_id, {
    "type": "path",
    "path": "/docs/botany-farm"
})
# ⚠️ Warning: "Found existing session 'Botany Farm 2023' with 88% matching files"
#    User can: [Continue Anyway] [Use Existing] [Cancel]
```

## Migration Strategy

### Phase 1: Additive Implementation (No Breaking Changes)

**New Functions:**
- `session_tools.create_session()` - Simplified (no documents_path)
- `document_tools.add_documents()` - Universal source handler
- `document_tools.detect_duplicates()` - Universal detection
- `document_tools.discover_documents()` - Enhanced (multi-source)

**Keep Existing (Mark Deprecated):**
- `session_tools.create_session()` with documents_path - Add deprecation warning
- `upload_tools.create_session_from_uploads()` - Redirect to new API
- `upload_tools.start_review_from_uploads()` - Redirect to new API

### Phase 2: Update Tests

**New Tests:**
- `tests/test_session_api.py` - New simplified API
- `tests/test_document_sources.py` - Multi-source handling
- `tests/test_duplicate_detection.py` - Universal detection

**Update Existing:**
- Keep `tests/test_upload_tools.py` (mark as legacy)
- Ensure backward compatibility

### Phase 3: Update MCP Server

**New Tools:**
```python
@mcp.tool()
async def create_session(project_name, methodology, ...) -> str:
    """Stage 1: Create session (metadata only)"""

@mcp.tool()
async def add_documents(session_id, source, check_duplicates=True) -> str:
    """Stage 1b: Add document sources"""
```

**Deprecate (Keep Functional):**
```python
@mcp.tool()
@deprecated("Use create_session() + add_documents() instead")
async def create_session_from_uploads(...) -> str:
    """Legacy: Redirects to new API"""
```

## Implementation Checklist

- [ ] Update `session_tools.create_session()` - Remove documents_path
- [ ] Create `document_tools.add_documents()`
- [ ] Create `document_tools.detect_duplicates()` (universal)
- [ ] Update `document_tools.discover_documents()` (multi-source)
- [ ] Update Session model (add document_sources field)
- [ ] Create DocumentSource model
- [ ] Update StateManager (handle document_sources)
- [ ] Add deprecation warnings to old functions
- [ ] Update MCP server tools
- [ ] Create new test files
- [ ] Update existing tests for backward compat
- [ ] Run full test suite
- [ ] Update documentation

## Success Criteria

✅ **Spec Alignment:**
- Stage 1: Create session (metadata only) ✓
- Stage 1b: Add sources (separate step) ✓
- Stage 2: Discovery (scans all sources) ✓

✅ **Consistency:**
- Duplicate detection works same for all source types ✓
- User warnings consistent regardless of input method ✓

✅ **Quality:**
- All existing tests pass (backward compat) ✓
- New tests cover new API (100% coverage) ✓
- Codebase smaller (remove redundant upload logic) ✓

✅ **Maintainability:**
- Clear stage separation ✓
- Single responsibility per function ✓
- Extensible for future source types (Drive, SharePoint) ✓

## File Size Reduction Estimate

**Current:**
- `upload_tools.py`: ~600 lines (deduplication, detection, temp dirs)
- `test_upload_tools.py`: 1111 lines
- Total: ~1700 lines

**After Refactoring:**
- `document_tools.add_documents()`: ~150 lines (universal handler)
- `document_tools.detect_duplicates()`: ~100 lines (universal detection)
- `test_document_sources.py`: ~400 lines (covers all source types)
- `test_duplicate_detection.py`: ~200 lines (universal detection tests)
- Total: ~850 lines

**Savings: ~850 lines (~50% reduction)** while adding universal detection!
