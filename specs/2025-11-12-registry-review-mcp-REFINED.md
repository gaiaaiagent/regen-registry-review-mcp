# Regen Registry Review MCP Server - Refined Specification

**Version:** 2.0.0
**Date:** November 12, 2025
**Status:** Implementation Ready
**Target:** Phase 2 (Nov 2025 - Jan 2026)

---

## Executive Summary

The **Registry Review MCP Server** is a standalone, self-contained Model Context Protocol server that automates registry review workflows for carbon credit project registration. It enables the Registry Agent (Becca archetype) to process project documentation 5-10x faster by automating document organization, evidence extraction, and compliance checking.

**Core Value Proposition:** Transform a 6-8 hour manual document review into a 60-90 minute guided workflow with complete audit trail and structured outputs.

**Design Principle:** This MCP is **completely independent** and functional on its own. It does not require KOI MCP or Regen Ledger MCP to operate, though it can optionally integrate with them for enhanced capabilities.

---

## Scope & Boundaries

### In Scope (MVP)

**Core Functionality:**
- ✅ Project registration review workflow (7 sequential stages)
- ✅ Document discovery and classification (PDF + GIS files)
- ✅ Evidence extraction and requirement mapping
- ✅ Cross-document validation (dates, land tenure, project IDs)
- ✅ Structured report generation (Markdown, JSON, PDF)
- ✅ Session-based state management with recovery
- ✅ Local file system operations
- ✅ Single project workflows

**Supported File Types:**
- ✅ PDF documents (text and tables)
- ✅ GIS shapefiles (.shp, .shx, .dbf, .geojson)
- ✅ Imagery files (.tif, .tiff) - metadata only

**Supported Methodology:**
- ✅ Soil Carbon v1.2.2 (with architecture for adding more)

**Success Metrics:**
- Process 1-2 real projects end-to-end
- 50-70% time reduction vs manual review
- 85%+ accuracy on requirement mapping
- <10% escalation rate to manual review

### Out of Scope (Future Phases)

**Deferred to Phase 3+:**
- ❌ Batch processing (70-farm aggregated projects)
- ❌ Credit issuance review workflows
- ❌ Google Drive / SharePoint connectors
- ❌ KOI Commons integration (optional enhancement)
- ❌ Regen Ledger integration (optional enhancement)
- ❌ Multi-methodology support beyond Soil Carbon

**Explicitly Not Included:**
- ❌ User interface (UI is separate - agent chat or custom app)
- ❌ Authentication/authorization (handled by consuming application)
- ❌ On-chain operations (handled by Ledger MCP if needed)
- ❌ Knowledge graph operations (handled by KOI MCP if needed)

---

## Architecture Overview

### Design Principles

1. **Standalone Completeness** - Works independently without external MCPs
2. **Optional Integration** - Can be enhanced with KOI/Ledger but doesn't require them
3. **Session-Based State** - All state persists in local JSON files
4. **Fail-Explicit** - Escalate to human review when uncertain, never guess
5. **Evidence Traceability** - Every finding cites source document, page, section
6. **Workflow-Oriented** - Prompts guide sequential stages, not isolated tools

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Registry Agent (Becca)                    │
│                  (AI Persona - External)                    │
└────────────────────────┬────────────────────────────────────┘
                         │ Uses MCP Protocol
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Registry Review MCP Server                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ PROMPTS (Workflow Orchestration)                     │  │
│  │ - /initialize                                        │  │
│  │ - /document-discovery                                │  │
│  │ - /evidence-extraction                               │  │
│  │ - /cross-validation                                  │  │
│  │ - /report-generation                                 │  │
│  │ - /human-review                                      │  │
│  │ - /complete                                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ TOOLS (Atomic Operations)                            │  │
│  │ Session: create, update, load                        │  │
│  │ Documents: discover, classify, extract_text          │  │
│  │ Evidence: map_requirements, extract_snippets         │  │
│  │ Validation: dates, land_tenure, completeness         │  │
│  │ Reports: generate, export                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ RESOURCES (Knowledge Base)                           │  │
│  │ - checklist://template/{methodology}                 │  │
│  │ - session://{session_id}                             │  │
│  │ - documents://{session_id}                           │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
                  ┌──────────────┐
                  │ Local Storage│
                  │              │
                  │ /data/       │
                  │ ├─checklists/│
                  │ ├─sessions/  │
                  │ └─cache/     │
                  └──────────────┘
```

### Optional Integration Points

The MCP exposes clean interfaces for optional integration with other systems:

```
[Optional] KOI MCP Integration:
- Query methodology documentation during requirement mapping
- Search historical reviews for similar projects
- Fetch best practices and common patterns

[Optional] Ledger MCP Integration:
- Resolve IRIs from submitted documents
- Validate project IDs against on-chain data
- Fetch existing project metadata

[Optional] Custom Storage:
- Replace local JSON with database backend
- Integrate with SharePoint/Google Drive
- Add cloud storage connectors
```

**Implementation:** Extensions use standard MCP resource/tool patterns. The core MCP never directly calls other MCPs - the consuming agent orchestrates multi-MCP workflows.

---

## Features & Capabilities

### 1. Session Management

**Purpose:** Create and manage isolated review sessions with recoverable state.

**Capabilities:**
- Create session with project metadata
- Load/update session state atomically
- Track workflow progress (7 stages)
- Recover from interruptions
- Session history and audit trail

**Key Tools:**
- `create_session(project_name, documents_path, methodology, ...)`
- `load_session(session_id)`
- `update_session_state(session_id, updates)`

**State Storage:**
```
/data/sessions/{session_id}/
  ├── session.json          # Metadata and progress
  ├── documents.json        # Document index
  ├── findings.json         # Evidence and validations
  ├── report.md            # Generated report
  └── .lock                # Atomic update lock
```

---

### 2. Document Discovery & Classification

**Purpose:** Scan project folders, identify file types, extract metadata.

**Capabilities:**
- Recursive directory scanning
- Multi-format support (PDF, GIS, imagery)
- Filename-based classification (fast path)
- Content-based classification (fallback)
- Metadata extraction (dates, page counts, file sizes)
- Document index generation

**Supported Classifications:**
```python
DOCUMENT_TYPES = {
    "project_plan",
    "baseline_report",
    "monitoring_report",
    "ghg_emissions",
    "land_tenure",
    "gis_shapefile",
    "land_cover_map",
    "methodology_reference",
    "registry_review",
    "attestation",
    "unknown"
}
```

**Key Tools:**
- `discover_documents(session_id)` - Scan and index all files
- `classify_document(document_id, session_id)` - Determine type
- `extract_pdf_text(filepath, page_range, extract_tables)` - PDF parsing
- `extract_gis_metadata(filepath)` - GIS file parsing

**Output Example:**
```json
{
  "documents_found": 7,
  "classification_summary": {
    "project_plan": 1,
    "baseline_report": 1,
    "gis_shapefile": 2,
    "unknown": 0
  },
  "documents": [
    {
      "document_id": "DOC-001",
      "filename": "4997Botany22 Public Project Plan.pdf",
      "classification": "project_plan",
      "confidence": 0.95,
      "metadata": {
        "page_count": 45,
        "file_size_bytes": 2458392,
        "creation_date": "2022-08-15"
      }
    }
  ]
}
```

---

### 3. Requirement Mapping & Evidence Extraction

**Purpose:** Map checklist requirements to document evidence with citations.

**Capabilities:**
- Load methodology-specific checklists
- Keyword-based requirement mapping
- Multi-document evidence aggregation
- Snippet extraction with page/section references
- Confidence scoring
- Gap identification

**Workflow:**
1. Load checklist (20+ requirements for Soil Carbon v1.2.2)
2. For each requirement:
   - Extract keywords from requirement text and accepted evidence
   - Search all documents for keyword matches
   - Rank documents by relevance score
   - Extract evidence snippets with ±100 word context
   - Record page numbers and section headers
3. Flag requirements with low confidence or no evidence

**Key Tools:**
- `map_requirement_to_documents(session_id, requirement_id)` - Find relevant docs
- `extract_evidence(session_id, requirement_id, document_id)` - Extract snippets
- `extract_structured_fields(document_id, field_schema)` - Parse specific fields

**Output Example:**
```json
{
  "requirement_id": "REQ-002",
  "requirement_text": "Provide evidence of legal land tenure...",
  "mapped_documents": [
    {
      "document_id": "DOC-001",
      "document_name": "Project Plan",
      "relevance_score": 0.92
    }
  ],
  "evidence_snippets": [
    {
      "text": "The project proponent holds a 20-year lease agreement...",
      "document_id": "DOC-001",
      "page": 8,
      "section": "3.2 Land Tenure",
      "confidence": 0.88
    }
  ],
  "status": "covered",
  "confidence": 0.85
}
```

---

### 4. Cross-Document Validation

**Purpose:** Verify consistency and correctness across multiple documents.

**Capabilities:**
- Date alignment validation (imagery vs sampling within 4 months)
- Land tenure consistency (owner names, areas, tenure types)
- Project ID propagation across documents
- Crediting period validation
- Temporal logic checks

**Validation Types:**
```python
VALIDATION_TYPES = {
    "date_alignment": {
        "max_delta_days": 120,
        "field_pairs": [
            ("imagery_date", "sampling_date"),
            ("baseline_date", "project_start_date")
        ]
    },
    "land_tenure": {
        "fields": ["owner_name", "area_hectares", "tenure_type"],
        "fuzzy_match": True,  # Allow surname-only matches
        "threshold": 0.8
    },
    "project_id": {
        "pattern": r"^C\d{2}-\d+$",
        "min_occurrences": 3  # Should appear in at least 3 docs
    }
}
```

**Key Tools:**
- `validate_date_alignment(session_id, date1_field, date2_field, max_delta)`
- `validate_land_tenure(session_id)` - Cross-check ownership claims
- `validate_project_id_consistency(session_id)` - Check ID propagation

**Output Example:**
```json
{
  "validation_type": "date_alignment",
  "date1": {
    "field": "imagery_date",
    "value": "2022-06-15",
    "source": "DOC-002, Page 5"
  },
  "date2": {
    "field": "sampling_date",
    "value": "2022-08-20",
    "source": "DOC-002, Page 12"
  },
  "delta_days": 66,
  "max_allowed": 120,
  "status": "pass",
  "message": "Dates within acceptable range"
}
```

---

### 5. Structured Report Generation

**Purpose:** Produce human-readable and machine-readable review reports.

**Capabilities:**
- Multi-format output (Markdown, JSON, PDF)
- Checklist population with findings
- Evidence citations for each requirement
- Summary statistics
- Flagged items requiring human review
- Version tracking

**Report Structure:**
```markdown
# Registry Agent Review

## Project Metadata
- Project Name: Botany Farm
- Project ID: C06-4997
- Methodology: Soil Carbon v1.2.2
- Reviewed: 2025-11-12

## Summary
- Total Requirements: 20
- Covered: 15 (75%)
- Partially Covered: 3 (15%)
- Missing: 2 (10%)

## Requirements Review

### REQ-001: Latest Methodology Version
**Status:** ✓ Covered
**Evidence:** Project Plan states "Soil Organic Carbon Estimation v1.2.2" (Page 3, Section 1.2)
**Confidence:** High (0.95)

### REQ-002: Land Tenure
**Status:** ⚠ Partially Covered
**Evidence:**
- Lease agreement found (20-year term, covers crediting period)
- Owner name discrepancy: "Nick Denman" in Project Plan vs "Nicholas Denman" in deed
**Confidence:** Medium (0.72)
**Human Review Required:** Confirm name variation acceptable

[... continue for all 20 requirements ...]

## Items Requiring Human Review
1. REQ-002: Name variation in land tenure documents
2. REQ-013: No yield data found for leakage calculation
```

**Key Tools:**
- `generate_review_report(session_id, format, include_evidence)`
- `export_review(session_id, output_format, output_path)`

---

### 6. Workflow Orchestration via Prompts

**Purpose:** Guide users through sequential review stages with context and suggestions.

**The 7 Workflow Stages:**

#### Stage 1: `/initialize`
- Create session
- Load checklist template
- Validate document path
- Output: Session ID, next step suggestion

#### Stage 2: `/document-discovery`
- Scan folder recursively
- Classify all files
- Extract metadata
- Output: Document index, classification summary, next step

#### Stage 3: `/evidence-extraction`
- Map all requirements to documents
- Extract evidence snippets
- Calculate coverage
- Output: Requirement findings, gaps identified, next step

#### Stage 4: `/cross-validation`
- Run all validation checks
- Flag inconsistencies
- Output: Validation results, warnings, next step

#### Stage 5: `/report-generation`
- Populate checklist with findings
- Generate structured report
- Output: Report path, summary stats, next step

#### Stage 6: `/human-review`
- Present flagged items
- Provide context for each
- Suggest actions
- Output: Review guidance, next step

#### Stage 7: `/complete`
- Finalize session
- Export final report
- Archive session data
- Output: Completion summary, file paths

**Prompt Design Pattern:**

Each prompt:
1. Checks prerequisites (previous stage completed)
2. Orchestrates multiple tools in sequence
3. Reports progress via `ctx.report_progress()`
4. Logs actions via `ctx.info()`, `ctx.warning()`, `ctx.error()`
5. Returns structured results
6. Suggests next step

**Example Prompt Implementation:**
```python
@mcp.prompt()
async def document_discovery(session_id: str) -> list[base.Message]:
    """Discover and classify all project documents"""

    # Validate session exists
    session = await load_session(session_id)

    # Run discovery
    results = await discover_documents(session_id, ctx)

    # Format response
    summary = f"""
✓ Document Discovery Complete

Found {results['documents_found']} documents:
{format_classification_summary(results)}

Next step: Run /evidence-extraction to map requirements
    """

    return [
        base.UserMessage(f"Discover documents for {session_id}"),
        base.AssistantMessage(summary)
    ]
```

---

## Data Models

### Session Schema

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class ProjectMetadata(BaseModel):
    project_name: str = Field(min_length=1, max_length=200)
    project_id: str | None = Field(None, pattern=r"^C\d{2}-\d+$")
    crediting_period: str | None = None
    submission_date: datetime | None = None
    methodology: str = "soil-carbon-v1.2.2"
    proponent: str | None = None
    documents_path: str

    @field_validator('documents_path')
    @classmethod
    def validate_path_exists(cls, value: str) -> str:
        from pathlib import Path
        path = Path(value)
        if not path.exists():
            raise ValueError(f"Path does not exist: {value}")
        return str(path.absolute())

class WorkflowProgress(BaseModel):
    initialize: Literal["pending", "in_progress", "completed"] = "pending"
    document_discovery: Literal["pending", "in_progress", "completed"] = "pending"
    evidence_extraction: Literal["pending", "in_progress", "completed"] = "pending"
    cross_validation: Literal["pending", "in_progress", "completed"] = "pending"
    report_generation: Literal["pending", "in_progress", "completed"] = "pending"
    human_review: Literal["pending", "in_progress", "completed"] = "pending"
    complete: Literal["pending", "in_progress", "completed"] = "pending"

class SessionStatistics(BaseModel):
    documents_found: int = 0
    requirements_total: int = 0
    requirements_covered: int = 0
    requirements_partial: int = 0
    requirements_missing: int = 0
    validations_passed: int = 0
    validations_failed: int = 0

class Session(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    project_metadata: ProjectMetadata
    workflow_progress: WorkflowProgress
    statistics: SessionStatistics
```

### Checklist Schema

```python
class Requirement(BaseModel):
    requirement_id: str = Field(pattern=r"^REQ-\d{3}$")
    category: str
    requirement_text: str
    source: str  # "Program Guide, Section X.Y"
    accepted_evidence: str
    mandatory: bool = True
    validation_type: Literal[
        "document_presence",
        "cross_document",
        "date_alignment",
        "structured_field",
        "manual"
    ]

class Checklist(BaseModel):
    methodology_id: str
    methodology_name: str
    version: str
    protocol: str
    program_guide_version: str
    requirements: list[Requirement]
```

### Document Schema

```python
class DocumentMetadata(BaseModel):
    page_count: int | None = None
    creation_date: datetime | None = None
    modification_date: datetime | None = None
    file_size_bytes: int
    has_tables: bool = False

class Document(BaseModel):
    document_id: str
    filename: str
    filepath: str
    classification: str
    confidence: float = Field(ge=0.0, le=1.0)
    classification_method: str
    metadata: DocumentMetadata
    indexed_at: datetime
```

### Finding Schema

```python
class EvidenceSnippet(BaseModel):
    snippet_id: str
    text: str = Field(max_length=500)  # ~2-3 sentences
    document_id: str
    page: int | None = None
    section: str | None = None
    confidence: float
    extraction_method: str

class RequirementFinding(BaseModel):
    requirement_id: str
    mapped_documents: list[str]  # document_ids
    evidence_snippets: list[EvidenceSnippet]
    status: Literal["covered", "partial", "missing", "needs_review"]
    confidence: float
    ai_comments: str | None = None
    human_comments: str | None = None
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goal:** Working MCP server with basic infrastructure

**Deliverables:**
1. ✅ Project setup with `uv`
2. ✅ Server entry point (`server.py`) with FastMCP initialization
3. ✅ Logging infrastructure (stderr for MCP, file for debugging)
4. ✅ Configuration management (`settings.py`)
5. ✅ Error hierarchy (`errors.py`)
6. ✅ State management with atomic updates (`state.py`)
7. ✅ Example checklist JSON from `examples/checklist.md`

**Acceptance Criteria:**
- Server starts with `uv run python src/registry_review_mcp/server.py`
- Appears in MCP Inspector
- Basic `/list-capabilities` prompt works
- Can create and load session successfully
- All infrastructure tests pass

**Code to Deliver:**

```python
# src/registry_review_mcp/server.py
import sys
import logging
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.session import ServerSession
from .config import settings
from .tools import session_tools, document_tools

# Setup logging (CRITICAL: stderr only for MCP)
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create MCP server
mcp = FastMCP("Regen Registry Review")

# Register session tools
@mcp.tool()
async def create_session(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    ctx: Context[ServerSession, None] = None
) -> dict:
    """Create new registry review session"""
    logger.info(f"Creating session: {project_name}")
    return await session_tools.create_session(
        project_name, documents_path, methodology,
        project_id, proponent, ctx
    )

# Register prompts
from .prompts import list_capabilities

@mcp.prompt()
def list_capabilities_prompt() -> list:
    """List all MCP server capabilities"""
    return list_capabilities.generate()

if __name__ == "__main__":
    logger.info("Starting Regen Registry Review MCP Server")
    mcp.run()
```

---

### Phase 2: Document Processing (Week 2)

**Goal:** Document discovery, classification, and text extraction

**Deliverables:**
1. ✅ `discover_documents()` tool with progress reporting
2. ✅ `classify_document()` with filename + content analysis
3. ✅ `extract_pdf_text()` with caching
4. ✅ `extract_gis_metadata()` basic implementation
5. ✅ Document index generation
6. ✅ `/document-discovery` prompt

**Acceptance Criteria:**
- Process all 7 files in `/examples/22-23/`
- Correctly classify project plan, baseline report, etc.
- Extract text from PDFs with 95%+ accuracy
- Cache extracted text (verify with timing tests)
- Generate complete document index JSON

**Test Case:**
```python
async def test_document_discovery():
    session = await create_session(
        "Botany Farm",
        "/path/to/examples/22-23",
        "soil-carbon-v1.2.2"
    )

    results = await discover_documents(session["session_id"])

    assert results["documents_found"] == 7
    assert results["classification_summary"]["project_plan"] == 1
    assert results["classification_summary"]["baseline_report"] == 1
    assert results["classification_summary"]["gis_shapefile"] >= 1
```

---

### Phase 3: Evidence Extraction (Week 3)

**Goal:** Requirement mapping and evidence snippet extraction

**Deliverables:**
1. ✅ `map_requirement_to_documents()` with keyword search
2. ✅ `extract_evidence()` with snippet extraction
3. ✅ `extract_structured_fields()` for specific data
4. ✅ Requirement coverage calculation
5. ✅ `/evidence-extraction` prompt

**Acceptance Criteria:**
- Map 18+ of 20 requirements successfully
- Extract evidence snippets with page numbers
- Calculate coverage status (covered/partial/missing)
- Flag 2-3 requirements for human review
- Confidence scores >0.8 for clear evidence

**Test Case:**
```python
async def test_evidence_extraction():
    # Assume session with discovered documents
    results = await evidence_extraction(session_id)

    assert results["requirements_total"] == 20
    assert results["requirements_covered"] >= 15
    assert results["requirements_partial"] <= 5
    assert results["requirements_missing"] <= 2

    # Check specific requirement
    req_002 = get_finding(results, "REQ-002")  # Land Tenure
    assert req_002["status"] in ["covered", "partial"]
    assert len(req_002["evidence_snippets"]) >= 1
    assert req_002["evidence_snippets"][0]["page"] is not None
```

---

### Phase 4: Validation & Reporting (Week 4)

**Goal:** Cross-validation and report generation

**Deliverables:**
1. ✅ `validate_date_alignment()` implementation
2. ✅ `validate_land_tenure()` with fuzzy matching
3. ✅ `generate_review_report()` in Markdown/JSON
4. ✅ `export_review()` to PDF
5. ✅ `/cross-validation` and `/report-generation` prompts

**Acceptance Criteria:**
- Date validation correctly checks 4-month rule
- Land tenure handles name variations (surname match)
- Report includes all 20 requirements with findings
- Report cites page numbers for all evidence
- PDF export works and is readable

**Test Case:**
```python
async def test_full_workflow():
    """End-to-end test against Botany Farm example"""

    # Initialize
    session = await create_session(
        "Botany Farm",
        "/path/to/examples/22-23"
    )
    sid = session["session_id"]

    # Discovery
    docs = await discover_documents(sid)
    assert docs["documents_found"] == 7

    # Extraction
    evidence = await evidence_extraction(sid)
    assert evidence["requirements_covered"] >= 15

    # Validation
    validation = await cross_validation(sid)
    assert validation["validations_passed"] >= 3

    # Report
    report = await generate_review_report(sid)
    assert Path(report["report_path"]).exists()

    content = Path(report["report_path"]).read_text()
    assert "Botany Farm" in content
    assert "C06-4997" in content
    assert "REQ-002" in content  # All requirements present
```

---

### Phase 5: Integration & Polish (Week 5)

**Goal:** Complete workflow, testing, documentation

**Deliverables:**
1. ✅ `/initialize`, `/human-review`, `/complete` prompts
2. ✅ Comprehensive error handling
3. ✅ Integration test suite
4. ✅ Developer documentation
5. ✅ Example workflows
6. ✅ Performance optimization (caching, parallel processing)

**Acceptance Criteria:**
- All 7 prompts work end-to-end
- Error messages are clear and actionable
- Integration tests pass on CI/CD
- README with setup and usage instructions
- Process Botany Farm example in <2 minutes (warm cache)

---

## Technical Specifications

### Dependencies

```toml
[project]
name = "registry-review-mcp"
version = "2.0.0"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.21.0",
    "pdfplumber>=0.11.0",
    "pydantic>=2.11.0",
    "python-dateutil>=2.8.0",
    "fiona>=1.9.0",          # GIS file reading
    "structlog>=24.0.0",     # Structured logging
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
]

[tool.uv]
exclude-newer = "2025-11-12T00:00:00Z"
```

### Directory Structure

```
regen-registry-review-mcp/
├── src/
│   └── registry_review_mcp/
│       ├── __init__.py
│       ├── server.py                # MCP server entry point
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py          # Configuration management
│       ├── models/
│       │   ├── __init__.py
│       │   ├── schemas.py           # Pydantic models
│       │   └── errors.py            # Error hierarchy
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── session_tools.py     # Session CRUD
│       │   ├── document_tools.py    # Discovery, classification
│       │   ├── evidence_tools.py    # Mapping, extraction
│       │   └── validation_tools.py  # Cross-validation
│       ├── prompts/
│       │   ├── __init__.py
│       │   ├── list_capabilities.py
│       │   ├── initialize.py
│       │   ├── document_discovery.py
│       │   ├── evidence_extraction.py
│       │   ├── cross_validation.py
│       │   ├── report_generation.py
│       │   ├── human_review.py
│       │   └── complete.py
│       ├── resources/
│       │   ├── __init__.py
│       │   └── data_resources.py    # Checklist, session resources
│       └── utils/
│           ├── __init__.py
│           ├── cache.py             # PDF text caching
│           ├── state.py             # Atomic state management
│           └── patterns.py          # Regex patterns
├── data/
│   ├── checklists/
│   │   └── soil-carbon-v1.2.2.json  # Requirement templates
│   ├── sessions/                    # Active sessions (gitignored)
│   └── cache/                       # Cached extractions (gitignored)
├── examples/
│   ├── 22-23/                       # Botany Farm test data
│   └── checklist.md                 # Reference checklist
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_session_tools.py
│   ├── test_document_tools.py
│   ├── test_evidence_tools.py
│   ├── test_validation_tools.py
│   └── test_integration.py          # End-to-end tests
├── pyproject.toml
├── README.md
└── .gitignore
```

### Performance Targets

**With Warm Cache (After First Run):**
- Session creation: <1 second
- Document discovery (7 files): <5 seconds
- Evidence extraction (20 requirements): 30-60 seconds
- Cross-validation: <5 seconds
- Report generation: <3 seconds
- **Total workflow: 45-90 seconds**

**With Cold Cache (First Run):**
- Document discovery: 10-15 seconds (PDF extraction)
- Evidence extraction: 60-90 seconds
- **Total workflow: 90-120 seconds**

**Optimization Strategies:**
1. Cache all PDF text extractions
2. Parallelize document classification (up to 5 concurrent)
3. Lazy-load checklist templates
4. Incremental session saves
5. Pre-compile regex patterns

---

## Testing Strategy

### Unit Tests

**Session Tools:**
- `test_create_session()` - Creates valid session with all fields
- `test_load_session()` - Loads existing session correctly
- `test_atomic_update()` - Concurrent updates don't corrupt state

**Document Tools:**
- `test_discover_documents()` - Finds all files recursively
- `test_classify_pdf()` - Correctly classifies document types
- `test_extract_pdf_text()` - Extracts text accurately
- `test_extract_gis_metadata()` - Parses shapefile metadata

**Evidence Tools:**
- `test_map_requirement()` - Maps requirements to relevant docs
- `test_extract_evidence()` - Extracts snippets with citations
- `test_structured_fields()` - Parses specific field values

**Validation Tools:**
- `test_date_alignment()` - Validates date ranges correctly
- `test_land_tenure()` - Handles name variations
- `test_project_id()` - Checks ID consistency

### Integration Tests

**End-to-End Workflow:**
```python
@pytest.mark.asyncio
async def test_botany_farm_workflow():
    """Complete workflow against real example data"""

    example_path = Path(__file__).parent.parent / "examples" / "22-23"

    # 1. Initialize
    session = await create_session(
        project_name="Botany Farm",
        documents_path=str(example_path),
        methodology="soil-carbon-v1.2.2"
    )
    session_id = session["session_id"]

    # 2. Document Discovery
    discovery = await discover_documents(session_id)
    assert discovery["documents_found"] == 7
    assert "project_plan" in discovery["classification_summary"]

    # 3. Evidence Extraction
    extraction = await evidence_extraction(session_id)
    assert extraction["requirements_covered"] >= 15
    assert extraction["requirements_total"] == 20

    # 4. Cross-Validation
    validation = await cross_validation(session_id)
    assert validation["validations_passed"] >= 3

    # 5. Report Generation
    report = await generate_review_report(
        session_id=session_id,
        format="markdown"
    )
    assert Path(report["report_path"]).exists()

    # 6. Verify Report Content
    content = Path(report["report_path"]).read_text()
    assert "Botany Farm" in content
    assert "C06-4997" in content
    assert "REQ-002" in content  # Land Tenure requirement

    # 7. Export PDF
    pdf_export = await export_review(
        session_id=session_id,
        output_format="pdf"
    )
    assert Path(pdf_export["export_path"]).exists()
    assert Path(pdf_export["export_path"]).stat().st_size > 10000  # >10KB
```

### Manual Testing

**MCP Inspector:**
```bash
# Install inspector
npm install -g @modelcontextprotocol/inspector

# Run server with inspector
npx @modelcontextprotocol/inspector uv --directory $PWD run python src/registry_review_mcp/server.py
```

**Claude Code Integration:**
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
        "src/registry_review_mcp/server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

---

## Extension Points

### Optional Enhancements (Post-MVP)

**1. KOI MCP Integration**

When KOI MCP is available, enhance requirement mapping:

```python
# In evidence_tools.py
async def map_requirement_to_documents(
    session_id: str,
    requirement_id: str,
    ctx: Context
) -> dict:
    requirement = load_requirement(session_id, requirement_id)

    # Standard keyword search (always works)
    keywords = extract_keywords(requirement)
    local_matches = search_documents(keywords)

    # Optional: Query KOI for additional context
    try:
        koi_context = await query_koi_if_available(
            f"methodology requirements for {requirement['source']}"
        )
        if koi_context:
            enhanced_keywords = extract_keywords_from_koi(koi_context)
            keywords.extend(enhanced_keywords)
    except MCPNotAvailable:
        # KOI not available, proceed with local keywords only
        pass

    return map_documents(keywords, local_matches)

async def query_koi_if_available(query: str) -> dict | None:
    """Attempt to query KOI MCP if available"""
    # This would be orchestrated by the Registry Agent
    # Not a direct MCP-to-MCP call
    return None  # Stub for now
```

**2. Regen Ledger Integration**

Add on-chain validation:

```python
async def validate_project_metadata(
    session_id: str,
    ctx: Context
) -> dict:
    session = load_session(session_id)
    project_id = session["project_metadata"]["project_id"]

    # Extract from documents (always works)
    extracted_metadata = extract_project_fields(session_id)

    # Optional: Validate against on-chain data
    try:
        ledger_metadata = await query_ledger_if_available(project_id)
        if ledger_metadata:
            # Compare extracted vs on-chain
            return cross_validate(extracted_metadata, ledger_metadata)
    except MCPNotAvailable:
        pass

    return {"status": "extracted_only", "data": extracted_metadata}
```

**3. Batch Processing**

Add batch session type:

```python
@mcp.tool()
async def create_batch_session(
    batch_name: str,
    projects: list[dict],  # [{name, path}, ...]
    methodology: str = "soil-carbon-v1.2.2",
    ctx: Context[ServerSession, None] = None
) -> dict:
    """Create batch session for multiple projects"""

    batch_session_id = generate_batch_id()
    individual_sessions = []

    for project in projects:
        session = await create_session(
            project_name=project["name"],
            documents_path=project["path"],
            methodology=methodology,
            ctx=ctx
        )
        individual_sessions.append(session["session_id"])

    # Store batch metadata
    save_batch_session({
        "batch_id": batch_session_id,
        "batch_name": batch_name,
        "sessions": individual_sessions,
        "created_at": datetime.utcnow()
    })

    return {
        "batch_id": batch_session_id,
        "projects_count": len(projects),
        "session_ids": individual_sessions
    }
```

---

## Success Criteria

### MVP Success Metrics

**Functional:**
- ✅ Process 1-2 real projects end-to-end without errors
- ✅ Generate reports that reviewers can use directly
- ✅ Map 85%+ of requirements automatically
- ✅ Flag <10% of requirements for manual investigation

**Performance:**
- ✅ Complete workflow in <2 minutes (warm cache)
- ✅ Document discovery in <10 seconds
- ✅ Evidence extraction in <90 seconds

**Quality:**
- ✅ 95%+ accuracy on document classification
- ✅ 90%+ accuracy on evidence location (page numbers correct)
- ✅ 85%+ confidence on high-confidence findings

**User Feedback:**
- ✅ Registry reviewers report time saved
- ✅ Registry reviewers report clearer structure
- ✅ Output quality acceptable for human validation

---

## Conclusion

This refined specification defines a **standalone, complete MCP server** for registry review automation. It is:

- ✅ **Self-contained** - Works independently without KOI or Ledger MCP
- ✅ **Well-scoped** - Focuses on single-project registration review
- ✅ **Implementation-ready** - 5-week plan with concrete deliverables
- ✅ **Testable** - Clear acceptance criteria and test cases
- ✅ **Extensible** - Clean integration points for future enhancements

**Next Steps:**
1. Review and approve specification
2. Create `data/checklists/soil-carbon-v1.2.2.json` from `examples/checklist.md`
3. Begin Phase 1 implementation (Week 1: Foundation)
4. Weekly check-ins on Tuesday stand-up

---

**Document Version:** 2.0.0
**Last Updated:** November 12, 2025
**Status:** Ready for Implementation
**Timeline:** Phase 2 (Nov 2025 - Jan 2026)
