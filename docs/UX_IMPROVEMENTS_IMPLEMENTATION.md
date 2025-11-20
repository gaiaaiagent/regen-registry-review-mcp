# UX Improvements Implementation Plan

**Based on:** UX_ANALYSIS.md findings
**Priority:** High - Improves discoverability without breaking changes
**Effort:** ~5.5 hours
**Impact:** Significantly better first-use experience

---

## Changes Overview

### 1. Enhanced list_capabilities Prompt
**File:** `src/registry_review_mcp/server.py`
**Lines:** 337-428
**Effort:** 2 hours

### 2. Quick Reference Documentation
**File:** `README.md`
**Section:** New "Tool Selection Guide"
**Effort:** 1 hour

### 3. Integration Patterns
**File:** `README.md`
**Section:** Expanded "Usage" section
**Effort:** 2 hours

### 4. Remove list_example_projects
**Files:** `server.py`, `session_tools.py`
**Effort:** 30 minutes

---

## Implementation Details

### Change 1: Enhanced list_capabilities Prompt

**Current structure:**
```python
@mcp.prompt()
def list_capabilities() -> list[TextContent]:
    capabilities = f"""# Regen Registry Review MCP Server

**Version:** 2.0.0
**Purpose:** Automate carbon credit project registry review workflows

## Capabilities

### Tools Available

**Session Management:**
- `start_review` - Quick-start: Create session and discover documents in one step
- `create_session` - Create new review session
...
```

**New structure:**

```python
@mcp.prompt()
def list_capabilities() -> list[TextContent]:
    capabilities = f"""# Regen Registry Review MCP Server

**Version:** 2.0.0
**Purpose:** Automate carbon credit project registry review workflows

---

## Quick Reference

| I want to...                              | Use this                      | Type   |
|-------------------------------------------|-------------------------------|--------|
| 🚀 Start a new review (guided)            | `/initialize`                 | Prompt |
| 📄 Process documents                      | `/document-discovery`         | Prompt |
| 🔍 Extract evidence                       | `/evidence-extraction`        | Prompt |
| 📤 Upload files from API/web              | `start_review_from_uploads()` | Tool   |
| 📊 See all active reviews                 | `list_sessions()`            | Tool   |
| 🐛 Debug a single requirement             | `map_requirement()`          | Tool   |
| 📝 Extract text from specific PDF         | `extract_pdf_text()`         | Tool   |

---

## Integration Patterns

### 💬 Claude Desktop (Interactive Use)
**Best Practice:** Use prompts for guided workflow

```
/initialize Botany Farm, /path/to/documents
/document-discovery
/evidence-extraction
```

**Why:** Prompts provide context, guidance, and auto-selection

### 🔌 REST API / Web Application
**Best Practice:** Use tools directly

```python
# One-step upload + extraction
result = await start_review_from_uploads(
    project_name="Botany Farm",
    files=[
        {"filename": "plan.pdf", "content_base64": "..."},
        {"filename": "baseline.pdf", "content_base64": "..."}
    ],
    auto_extract=True
)
```

**Why:** Tools are designed for programmatic access

### 🧪 Testing / Debugging
**Best Practice:** Use individual tools

```python
session = await create_session("Test", "/path")
docs = await discover_documents(session["session_id"])
evidence = await map_requirement(session["session_id"], "REQ-007")
```

**Why:** Fine-grained control for investigation

---

## Tool Reference

### Session Management

#### Quick-Start ⭐ Recommended for New Users

**start_review**(project_name, documents_path, methodology="soil-carbon-v1.2.2")
```python
# Creates session + discovers documents in one step
result = await start_review(
    project_name="Botany Farm 2022-2023",
    documents_path="/absolute/path/to/documents"
)
# Returns: {{"session": {{...}}, "discovery": {{...}}}}
```

#### Manual Session Lifecycle

**create_session**(project_name, documents_path, methodology="soil-carbon-v1.2.2", ...)
```python
# Create a new review session
session = await create_session(
    project_name="Botany Farm",
    documents_path="/path/to/docs",
    project_id="C06-4997",        # optional
    proponent="Ecometric"         # optional
)
# Returns: {{"session_id": "session-abc123", ...}}
```

**load_session**(session_id)
```python
# Load existing session data
session = await load_session("session-abc123")
# Returns: {{project_metadata, workflow_progress, statistics, ...}}
```

**list_sessions**()
```python
# List all active review sessions
sessions = await list_sessions()
# Returns: [{{session_id, project_name, created_at, status, ...}}, ...]
```

**delete_session**(session_id)
```python
# Permanently delete a session
result = await delete_session("session-abc123")
# Returns: {{"status": "deleted", "message": "..."}}
```

---

### Upload Integration (API/Web Use)

**start_review_from_uploads** ⭐ Recommended for API Integration
```python
# One-step: upload files + create session + extract evidence
result = await start_review_from_uploads(
    project_name="Botany Farm",
    files=[
        {{"filename": "plan.pdf", "content_base64": "JVBERi0..."}},
        {{"filename": "baseline.pdf", "path": "/uploads/baseline.pdf"}}
    ],
    auto_extract=True,        # Run evidence extraction automatically
    deduplicate=True,         # Remove duplicate files
    force_new_session=False   # Use existing if found
)
```

**Accepts two file formats:**
1. Base64: `{{"filename": "...", "content_base64": "..."}}`
2. File path: `{{"filename": "...", "path": "/absolute/path"}}`

**create_session_from_uploads**(project_name, files, ...)
```python
# Upload files and create session (no auto-extraction)
result = await create_session_from_uploads(
    project_name="Botany Farm",
    files=[...],
    methodology="soil-carbon-v1.2.2"
)
```

**upload_additional_files**(session_id, files)
```python
# Add more files to existing session
result = await upload_additional_files(
    session_id="session-abc123",
    files=[{{"filename": "monitoring.pdf", "content_base64": "..."}}]
)
```

---

### Document Processing

**discover_documents**(session_id)
```python
# Scan directory and classify all documents
result = await discover_documents("session-abc123")
# Returns: {{
#   "documents_found": 7,
#   "classification_summary": {{
#     "project_plan": 1,
#     "baseline_report": 1,
#     ...
#   }},
#   "documents": [...]
# }}
```

**extract_pdf_text**(filepath, start_page=None, end_page=None, extract_tables=False)
```python
# Extract text from specific PDF file
result = await extract_pdf_text(
    filepath="/path/to/document.pdf",
    start_page=1,
    end_page=10,
    extract_tables=True
)
# Returns: {{"text": "...", "page_count": 10, ...}}
```

**extract_gis_metadata**(filepath)
```python
# Extract metadata from GIS shapefile or GeoJSON
result = await extract_gis_metadata("/path/to/project_area.shp")
# Returns: {{"crs": "EPSG:4326", "bounds": [...], "feature_count": 5}}
```

---

### Evidence Extraction & Analysis

**extract_evidence**(session_id)
```python
# Map ALL requirements to documents with evidence snippets
result = await extract_evidence("session-abc123")
# Returns: {{
#   "requirements_covered": 11,
#   "requirements_partial": 12,
#   "requirements_missing": 0,
#   "overall_coverage": 0.739,
#   "evidence": [...]
# }}
```

**map_requirement**(session_id, requirement_id)
```python
# Map SINGLE requirement (useful for debugging)
result = await map_requirement("session-abc123", "REQ-007")
# Returns: {{
#   "requirement_id": "REQ-007",
#   "status": "covered",
#   "confidence": 0.95,
#   "documents": [...],
#   "evidence_snippets": [...]
# }}
```

---

## Workflow Stages

The Registry Review process follows **7 sequential stages**:

```
┌─────────────────────┐
│ 1. Initialize       │  Create session + load checklist
└──────────┬──────────┘
           │ /initialize or start_review()
┌──────────▼──────────┐
│ 2. Discovery        │  Scan and classify documents
└──────────┬──────────┘
           │ /document-discovery or discover_documents()
┌──────────▼──────────┐
│ 3. Evidence         │  Map requirements to evidence
└──────────┬──────────┘
           │ /evidence-extraction or extract_evidence()
┌──────────▼──────────┐
│ 4. Validation       │  Verify consistency (dates, tenure, IDs)
└──────────┬──────────┘
           │ /cross-validation
┌──────────▼──────────┐
│ 5. Report           │  Generate structured report
└──────────┬──────────┘
           │ /report-generation
┌──────────▼──────────┐
│ 6. Human Review     │  Present flagged items for decision
└──────────┬──────────┘
           │ /human-review
┌──────────▼──────────┐
│ 7. Complete         │  Finalize and export report
└─────────────────────┘
           │ /complete
```

**Stage Status Tracking:**

Each session tracks progress:
```json
{{
  "workflow_progress": {{
    "initialize": "completed",
    "document_discovery": "completed",
    "evidence_extraction": "in_progress",
    "cross_validation": "pending",
    "report_generation": "pending",
    "human_review": "pending",
    "complete": "pending"
  }}
}}
```

---

## Workflow Prompts

### Interactive Guided Workflow

Use these prompts in Claude Desktop for guided execution:

**A. /initialize** `project_name, documents_path`
- Creates new review session
- Loads methodology checklist
- Prepares workspace

**B. /document-discovery** `[session_id]`
- Scans project directory recursively
- Classifies documents by type
- Extracts metadata
- Auto-selects most recent session if no ID provided

**C. /evidence-extraction** `[session_id]`
- Maps all 23 requirements to documents
- Extracts evidence snippets with page citations
- Calculates coverage statistics
- Auto-selects most recent session if no ID provided

**D. /cross-validation** `[session_id]`
- Validates date alignment (120-day rule)
- Checks land tenure consistency
- Verifies project ID patterns
- Flags discrepancies for review

**E. /report-generation** `[session_id]`
- Generates Markdown report
- Generates JSON report
- Includes all evidence and citations
- Structured for human review

**F. /human-review** `[session_id]`
- Presents flagged validation items
- Guides decision-making
- Documents judgments
- Updates session state

**G. /complete** `[session_id]`
- Finalizes review
- Exports reports
- Archives session
- Generates summary statistics

---

## Supported Methodology

**Current:**
- Soil Carbon v1.2.2 (GHG Benefits in Managed Crop and Grassland Systems)
- 23 requirements across 6 categories

**Coming Soon:**
- Additional Regen Registry methodologies
- Custom checklist support

---

## File Types Supported

| Type       | Extensions                   | Capabilities                          |
|------------|------------------------------|---------------------------------------|
| PDF        | `.pdf`                       | Text extraction, table extraction     |
| GIS        | `.shp`, `.shx`, `.dbf`       | Metadata extraction (CRS, bounds)     |
| GeoJSON    | `.geojson`                   | Metadata extraction                   |
| Imagery    | `.tif`, `.tiff`              | Metadata only (no pixel processing)   |
| Markdown   | `.md`                        | Converted PDFs (via marker skill)     |

---

## Performance & Scaling

**Typical Performance (Botany Farm example - 7 documents):**
- Document discovery: ~1.5 seconds
- Evidence extraction: ~2.4 seconds (23 requirements)
- Cross-validation: <1 second
- Report generation: ~0.5 seconds

**Scaling Characteristics:**
- Documents: Linear scaling (O(n))
- Requirements: Linear scaling (O(m))
- Evidence extraction: O(n × m) with LLM caching reducing to ~O(n)

**Cost Optimization:**
- Prompt caching: 90% API cost reduction
- Session fixtures: 66% test cost reduction
- Parallel processing: Concurrent chunk analysis

**Limits:**
- Max documents per session: No hard limit (tested with 7-10)
- Max file size: Recommend <100MB per PDF
- API rate limiting: Configurable via REGISTRY_REVIEW_MAX_API_CALLS_PER_SESSION

---

## Error Handling

All tools and prompts return **structured, actionable error messages**:

**Example: Session not found**
```
❌ Session Not Found

Session ID: session-xyz123

This session does not exist.

Available sessions:

  • session-abc123 - Botany Farm 2022
  • session-def456 - Sample Project

Create a new session using /initialize.
```

**Example: File validation error**
```
✗ Error in create_session_from_uploads: [ValueError]
File 'ProjectPlan.pdf' at index 0 must have either 'content_base64' or 'path' field
```

**Example: No sessions exist**
```
No review sessions found. You can either:

## Option 1: Provide Project Details (Recommended)
/document-discovery Your Project Name, /absolute/path/to/documents

## Option 2: Use Initialize First
Create a session with /initialize first
```

---

## Status & Test Coverage

**Phase Completion:**
- ✅ Phase 1 (Foundation): Complete
- ✅ Phase 2 (Document Processing): Complete
- ✅ Phase 3 (Evidence Extraction): Complete
- ✅ Phase 4 (Validation & Reporting): Complete
- ✅ Phase 4.2 (LLM-Native Field Extraction): Complete
- 🚧 Phase 5 (Integration & Polish): In Progress

**Test Coverage:**
- 99 tests passing (100%)
- Real-world accuracy validation: 80%+ recall
- Cost tracking and monitoring: Active

**Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M UTC")}
"""

    return [TextContent(type="text", text=capabilities)]
```

---

### Change 2: Quick Reference in README

**Location:** README.md, after "Quick Start" section

**Content:**

```markdown
## Tool Selection Guide

### When to Use What

| Scenario                                  | Recommended Approach          | Why                                    |
|-------------------------------------------|-------------------------------|----------------------------------------|
| **First time using the system**           | `/initialize` → `/document-discovery` → `/evidence-extraction` | Guided prompts with explanations       |
| **Building an API integration**           | `start_review_from_uploads()` | One-step upload + extraction           |
| **Analyzing uploaded files**              | `create_session_from_uploads()` then `extract_evidence()` | Two-step control                       |
| **Debugging a specific requirement**      | `map_requirement(session_id, "REQ-007")` | Detailed single-requirement analysis   |
| **Checking session status**               | `load_session(session_id)` or `list_sessions()` | Quick status check                     |
| **Extracting text from one PDF**          | `extract_pdf_text(filepath)` | File-level extraction                  |
| **Re-running discovery after adding files** | `discover_documents(session_id)` | Updates document index                 |

### Tools vs Prompts

**Use Prompts when:**
- Working interactively in Claude Desktop
- Learning the system
- Want guided workflow with explanations
- Need auto-session selection

**Use Tools when:**
- Building API integrations
- Scripting automation
- Need programmatic control
- Working with uploaded files (base64/path)

### Most Common Workflows

**Interactive (Claude Desktop):**
```
/initialize Botany Farm, /path/to/documents
/document-discovery
/evidence-extraction
```

**API Integration (ElizaOS, web apps):**
```python
result = await start_review_from_uploads(
    project_name="Botany Farm",
    files=[...],
    auto_extract=True
)
```

**Manual Control (debugging, testing):**
```python
session = await create_session("Test", "/path")
docs = await discover_documents(session["session_id"])
evidence = await extract_evidence(session["session_id"])
```
```

---

### Change 3: Integration Patterns Section

**Location:** README.md, new section after "Usage"

**Content:**

```markdown
## Integration Patterns

### Claude Desktop

The MCP server is designed for seamless integration with Claude Desktop.

**Configuration:**
```json
{
  "mcpServers": {
    "registry-review": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/regen-registry-review-mcp",
        "run",
        "python",
        "-m",
        "registry_review_mcp.server"
      ]
    }
  }
}
```

**Usage:**
- Use prompts (`/initialize`, `/document-discovery`) for guided workflow
- Auto-session selection: Prompts automatically use most recent session
- Inline session creation: Provide project details to any prompt

---

### ElizaOS Integration

Registry Review integrates with ElizaOS character agents for conversational registry reviews.

**Example: Character Agent with Registry Review**
```typescript
// character.json
{
  "name": "Becca the Registry Agent",
  "clients": ["twitter", "telegram"],
  "modelProvider": "anthropic",
  "settings": {
    "mcpServers": {
      "registry-review": {
        "command": "uv",
        "args": [
          "--directory",
          "/workspace/regen-registry-review-mcp",
          "run",
          "python",
          "-m",
          "registry_review_mcp.server"
        ]
      }
    }
  }
}
```

**Handling File Uploads:**
```typescript
// ElizaOS action handler
async function handleRegistryReview(runtime: IAgentRuntime, message: Memory) {
  // Get uploaded files from ElizaOS
  const files = message.content.attachments.map(att => ({
    name: att.name,
    path: att.url  // ElizaOS provides URL like /media/uploads/...
  }));

  // Call Registry Review MCP
  const result = await runtime.mcpClient.callTool("registry-review", {
    tool: "start_review_from_uploads",
    arguments: {
      project_name: "Uploaded Project",
      files: files,
      auto_extract: true
    }
  });

  return result;
}
```

**Why path format works:**
- Registry Review automatically resolves ElizaOS upload paths
- Searches common ElizaOS installation locations
- Respects `ELIZA_ROOT` environment variable

---

### REST API Wrapper

For non-MCP environments, wrap the MCP server in a REST API.

**Example: FastAPI wrapper**
```python
from fastapi import FastAPI, UploadFile, File
from registry_review_mcp.tools import upload_tools, evidence_tools
import base64

app = FastAPI()

@app.post("/api/v1/reviews")
async def create_review(
    project_name: str,
    files: list[UploadFile] = File(...)
):
    # Convert uploaded files to base64
    file_dicts = []
    for file in files:
        content = await file.read()
        file_dicts.append({
            "filename": file.filename,
            "content_base64": base64.b64encode(content).decode()
        })

    # Call Registry Review
    result = await upload_tools.start_review_from_uploads(
        project_name=project_name,
        files=file_dicts,
        auto_extract=True
    )

    return result

@app.get("/api/v1/reviews/{session_id}/evidence")
async def get_evidence(session_id: str):
    result = await evidence_tools.extract_all_evidence(session_id)
    return result
```

---

### Python SDK Usage

Direct Python integration without MCP protocol.

```python
from registry_review_mcp.tools import (
    session_tools,
    document_tools,
    evidence_tools
)

# Create session
session = await session_tools.create_session(
    project_name="Botany Farm",
    documents_path="/path/to/documents"
)

session_id = session["session_id"]

# Discover documents
docs = await document_tools.discover_documents(session_id)
print(f"Found {docs['documents_found']} documents")

# Extract evidence
evidence = await evidence_tools.extract_all_evidence(session_id)
print(f"Coverage: {evidence['overall_coverage']:.1%}")

# Load session for status
session_data = await session_tools.load_session(session_id)
print(f"Workflow progress: {session_data['workflow_progress']}")
```

---

### Batch Processing (Multiple Projects)

Process multiple projects in parallel.

```python
import asyncio
from registry_review_mcp.tools import session_tools, document_tools, evidence_tools

async def process_project(project_name: str, docs_path: str):
    # Create session
    session = await session_tools.create_session(
        project_name=project_name,
        documents_path=docs_path
    )

    session_id = session["session_id"]

    # Run workflow
    await document_tools.discover_documents(session_id)
    evidence = await evidence_tools.extract_all_evidence(session_id)

    return {
        "session_id": session_id,
        "project_name": project_name,
        "coverage": evidence["overall_coverage"]
    }

# Process batch of projects
projects = [
    ("Botany Farm 22-23", "/data/botany-22-23"),
    ("Cedar Valley 23-24", "/data/cedar-23-24"),
    ("Maple Ridge 21-22", "/data/maple-21-22"),
]

results = await asyncio.gather(*[
    process_project(name, path) for name, path in projects
])

for result in results:
    print(f"{result['project_name']}: {result['coverage']:.1%} coverage")
```
```

---

### Change 4: Remove list_example_projects

**Files to modify:**

1. **src/registry_review_mcp/server.py**
   - Remove lines 98-103 (tool definition)
   - Remove prompt wrapper (if exists)

2. **src/registry_review_mcp/tools/session_tools.py**
   - Remove function `list_example_projects()` (lines 168-199)

3. **README.md**
   - Add examples directory documentation:

```markdown
## Example Data

The `examples/` directory contains sample project data for testing:

**examples/22-23/** - Botany Farm 2022-2023
- 7 documents (project plan, baseline report, monitoring reports)
- Real-world test case for methodology validation
- Used in test suite for accuracy validation

**Usage:**
```bash
/initialize Botany Farm Test, /absolute/path/to/examples/22-23
```

Or programmatically:
```python
session = await create_session(
    project_name="Botany Farm Test",
    documents_path="/path/to/examples/22-23"
)
```
```

---

## Testing Plan

### Test Changes

1. **Test that list_capabilities returns new format:**
```python
def test_list_capabilities_has_quick_reference():
    result = list_capabilities()
    text = result[0].text
    assert "Quick Reference" in text
    assert "Integration Patterns" in text
    assert "Tool Reference" in text
```

2. **Test that list_example_projects is removed:**
```python
def test_list_example_projects_removed():
    from registry_review_mcp import server
    assert not hasattr(server, 'list_example_projects')
```

3. **Verify all existing tests still pass:**
```bash
uv run pytest -v
# Expected: 98 tests passing (down from 99)
```

---

## Rollout Plan

### Phase 1: Documentation (Low Risk)
1. Update list_capabilities prompt
2. Add quick reference to README
3. Add integration patterns to README
4. Test in Claude Desktop

### Phase 2: Code Changes (Low Risk)
1. Remove list_example_projects tool
2. Add examples documentation to README
3. Run test suite
4. Verify tool count: 14 tools

### Phase 3: Validation
1. Test full workflow in Claude Desktop
2. Verify documentation accuracy
3. Get user feedback
4. Iterate based on feedback

---

## Success Metrics

**Before:**
- 15 tools
- 10 prompts
- ~100 lines of capabilities documentation
- No integration examples

**After:**
- 14 tools (-1 testing tool)
- 10 prompts (unchanged)
- ~300 lines of enhanced capabilities documentation
- 5 integration patterns documented
- Quick reference table for task-based discovery
- Tool signatures with examples

**Expected Impact:**
- 50% faster tool discovery (task → tool mapping)
- Clearer integration guidance (Claude Desktop vs API vs SDK)
- Reduced trial-and-error for new users
- Better documentation for external integrations

---

## Timeline

**Total Effort:** ~5.5 hours

| Task                              | Time   | Priority |
|-----------------------------------|--------|----------|
| Enhanced list_capabilities        | 2h     | High     |
| Quick reference in README         | 1h     | High     |
| Integration patterns in README    | 2h     | High     |
| Remove list_example_projects      | 30min  | Medium   |
| Testing and validation            | (included) | -    |

**Recommended Execution:** Complete all in single session to maintain consistency.
