# Regen Registry Review MCP Server Specification

**Version:** 1.0.0
**Date:** November 11, 2025
**Status:** Draft
**Authors:** Regen Network Team
**Target Protocol:** MCP 2025-06-18
**Python Version:** ≥3.10

---

## Executive Summary

The Regen Registry Review MCP Server automates the most tedious aspects of project registration review for carbon credit projects, enabling a single registry reviewer to process 100+ annual projects that would otherwise require dedicated full-time staff. This MCP server embodies the principle of **human-AI collaboration over replacement**: AI handles document organization, metadata extraction, consistency checking, and initial validation, while humans provide substantive analysis, judgment, and final approval.

**Core Value Proposition**: Transform a 6-8 hour manual document organization and checklist population task into a 30-minute guided workflow, freeing expert reviewers to focus on substantive compliance analysis rather than administrative drudgery.

**MVP Scope**: Single-project registration review for Soil Organic Carbon projects using local file system data, with architecture designed for future extension to credit issuance review, batch processing, and cloud storage connectors.

---

## Vision & Motivation

### The Problem: Manual Review at Breaking Point

Becca, the sole registry reviewer at Regen Network, faces an unsustainable workload. Ecometric alone submits 100+ projects annually, with batches sometimes containing 70 individual farm submissions. Each project requires meticulous review:

- Download project folders from multiple sources (Airtable, SharePoint, Google Drive)
- Manually organize and rename files following naming conventions
- Create registry review templates for each project
- Transcribe document names into checklist spreadsheets
- Copy filenames into requirement fields
- Cross-reference land ownership claims against registry documents
- Verify date alignments between imagery and soil sampling (must be within 4 months)
- Check completeness against 20+ methodology-specific requirements
- Add clarifying comments where necessary
- Conduct secondary review

The most time-consuming tasks—writing document names into checklists, copying them to requirement squares, cross-checking consistency—are precisely the tasks that AI excels at automating.

### The Opportunity: Systematic Automation

Analysis of completed reviews reveals that **50-70% of review time** involves systematizable tasks:
- Document discovery and classification
- Metadata extraction (dates, project IDs, names)
- Cross-document consistency validation
- Evidence location tracking
- Initial completeness checking

The remaining 30-50% requires genuine human expertise: interpreting complex legal documents, assessing risk, evaluating methodology deviations, and making final approval decisions.

### The Solution: Workflow Prompts as Recipes

This MCP server implements **workflow prompts** as the primary interface—not individual tool calls. Following the MCP primitives hierarchy (Prompts > Tools > Resources), we structure the review process as seven sequential workflow stages, each accessible via slash command:

```
/initialize          → Create review session, load checklist, index documents
/document-discovery  → Classify and organize submitted materials
/evidence-extraction → Map requirements to document sections
/cross-validation    → Check consistency across documents
/report-generation   → Populate checklist with findings
/human-review        → Present structured report for validation
/complete            → Finalize and export review
```

Each prompt orchestrates multiple underlying tools, provides progress reporting, and guides the reviewer to the next logical step. The visual language of collaboration: **AI writes in structured JSON/markdown, humans add judgment in comments**.

---

## System Architecture Overview

### Design Principles

1. **Local-First with Cloud-Ready Architecture**: MVP works entirely with local file systems, but data access patterns anticipate Google Drive and SharePoint connectors.

2. **Session-Based State Management**: All review state persists in JSON files under `/data/sessions/{session_id}/`, making state inspectable, debuggable, and recoverable.

3. **Modularity Through Small Tools**: Each tool performs one atomic operation (extract text, classify document, find date) enabling composition and testability.

4. **Prompts as Workflows**: Prompts are the primary user interface, composing tools into multi-step processes with progress reporting and guidance.

5. **Evidence Traceability**: Every finding includes source citations (document name, page number, section) enabling human verification.

6. **Fail-Explicit Design**: When confidence is low or evidence is ambiguous, the system escalates to human review rather than guessing.

### Technology Stack

- **MCP SDK**: Official Python SDK v1.21.0+ (`mcp[cli]`)
- **FastMCP**: Integrated framework from `mcp.server.fastmcp`
- **PDF Processing**: `pdfplumber` for text and table extraction
- **File Operations**: Python stdlib (`pathlib`, `json`, `shutil`)
- **Pattern Matching**: Basic regex for date extraction, filename parsing
- **Validation**: `pydantic` for data models

### Project Structure

```
regen-registry-review-mcp/
├── src/
│   └── registry_review_mcp/
│       ├── server.py              # Main MCP server instance
│       ├── tools/                 # Atomic tool implementations
│       │   ├── document_tools.py  # PDF extraction, classification
│       │   ├── evidence_tools.py  # Evidence extraction, mapping
│       │   ├── validation_tools.py # Cross-validation logic
│       │   └── session_tools.py   # Session management
│       ├── prompts/               # Workflow prompt definitions
│       │   ├── initialize.py
│       │   ├── document_discovery.py
│       │   ├── evidence_extraction.py
│       │   ├── cross_validation.py
│       │   ├── report_generation.py
│       │   └── human_review.py
│       ├── resources/             # Resource handlers
│       │   └── data_resources.py
│       └── models/                # Pydantic data models
│           └── schemas.py
├── data/
│   ├── checklists/                # Registry requirement templates
│   │   └── soil-carbon-v1.2.2.json
│   └── sessions/                  # Active review sessions
│       └── {session_id}/
│           ├── session.json       # Session metadata and state
│           ├── documents.json     # Document index and metadata
│           └── findings.json      # Extracted evidence and validations
├── examples/
│   ├── 22-23/                     # Botany Farm sample data
│   └── checklist.md               # Reference checklist template
├── tests/
│   ├── test_tools.py
│   ├── test_prompts.py
│   └── test_integration.py
├── pyproject.toml
└── README.md
```

---

## Resources

Resources provide read-only access to structured data used throughout the review process. They are the "knowledge base" that tools and prompts query.

### Resource 1: Checklist Template

**URI Pattern**: `checklist://template/{methodology_id}`

**Purpose**: Provides the structured requirements checklist for a specific credit protocol methodology.

**Implementation**: Reads from `/data/checklists/{methodology_id}.json`

**Data Model**:
```json
{
  "methodology_id": "soil-carbon-v1.2.2",
  "methodology_name": "Soil Organic Carbon Estimation in Regenerative Cropping and Managed Grassland Ecosystems",
  "version": "1.2.2",
  "protocol": "GHG Benefits in Managed Crop and Grassland Systems",
  "program_guide_version": "1.1",
  "requirements": [
    {
      "requirement_id": "REQ-001",
      "category": "General",
      "requirement_text": "Projects shall apply the latest version of the applicable credit class and methodology",
      "source": "Program Guide, Section 8.1.3",
      "accepted_evidence": "Project plan, methodology and credit class version are up to date.",
      "mandatory": true,
      "validation_type": "document_presence"
    },
    {
      "requirement_id": "REQ-002",
      "category": "Land Tenure",
      "requirement_text": "Provide evidence of legal land tenure and control over the project area for the crediting period",
      "source": "Program Guide, Section 8.2; Credit Class, Section 3.4, 3.5",
      "accepted_evidence": "Deeds, lease agreements, land use agreements, or legal attestations confirming long-term control and ownership",
      "mandatory": true,
      "validation_type": "cross_document"
    }
  ]
}
```

**Access Pattern**:
```python
# In tools/prompts
checklist = await fetch_resource("checklist://template/soil-carbon-v1.2.2")
requirements = checklist["requirements"]
```

**Rationale**: Storing checklists as JSON resources enables:
- Version control of requirement changes
- Easy addition of new methodologies
- Machine-readable validation logic
- Human-readable structure (can be generated from markdown via `/extract-checklist` prompt)

---

### Resource 2: Session State

**URI Pattern**: `session://{session_id}`

**Purpose**: Provides current state of an active review session.

**Implementation**: Reads from `/data/sessions/{session_id}/session.json`

**Data Model**:
```json
{
  "session_id": "REV-20231115-001",
  "created_at": "2023-11-15T10:30:00Z",
  "updated_at": "2023-11-15T11:45:00Z",
  "status": "evidence_extraction",
  "project_metadata": {
    "project_name": "Botany Farm Regenerative Agriculture",
    "project_id": "C06-4997",
    "crediting_period": "2022-2032",
    "submission_date": "2023-11-10",
    "methodology": "soil-carbon-v1.2.2",
    "proponent": "Ecometric",
    "documents_path": "/absolute/path/to/examples/22-23"
  },
  "workflow_progress": {
    "initialize": "completed",
    "document_discovery": "completed",
    "evidence_extraction": "in_progress",
    "cross_validation": "pending",
    "report_generation": "pending",
    "human_review": "pending",
    "complete": "pending"
  },
  "statistics": {
    "documents_found": 7,
    "requirements_total": 20,
    "requirements_mapped": 12,
    "requirements_pending": 8,
    "validations_passed": 8,
    "validations_failed": 2,
    "validations_pending": 10
  }
}
```

**Access Pattern**:
```python
session = await fetch_resource("session://REV-20231115-001")
if session["workflow_progress"]["document_discovery"] != "completed":
    raise ValueError("Must complete document discovery first")
```

**Rationale**: Explicit session state enables:
- Progress tracking across multi-step workflows
- Recovery from interruptions
- Parallel review of multiple projects
- Audit trail of review activities

---

### Resource 3: Document Index

**URI Pattern**: `documents://{session_id}`

**Purpose**: Provides index of all discovered documents with classifications and metadata.

**Implementation**: Reads from `/data/sessions/{session_id}/documents.json`

**Data Model**:
```json
{
  "session_id": "REV-20231115-001",
  "documents": [
    {
      "document_id": "DOC-001",
      "filename": "4997Botany22 Public Project Plan.pdf",
      "filepath": "/absolute/path/to/examples/22-23/4997Botany22 Public Project Plan.pdf",
      "file_size_bytes": 2458392,
      "classification": "project_plan",
      "confidence": 0.95,
      "classification_method": "filename_pattern",
      "metadata": {
        "page_count": 45,
        "creation_date": "2022-08-15",
        "modification_date": "2022-09-01",
        "has_tables": true,
        "has_maps": false
      },
      "extracted_fields": {
        "project_name": "Botany Farm",
        "project_id": "C06-4997",
        "project_start_date": "2022-01-01",
        "crediting_period": "2022-2032"
      },
      "indexed_at": "2023-11-15T10:35:00Z"
    },
    {
      "document_id": "DOC-002",
      "filename": "4997Botany22 Soil Organic Carbon Project Public Baseline Report 2022.pdf",
      "filepath": "/absolute/path/to/examples/22-23/4997Botany22 Soil Organic Carbon Project Public Baseline Report 2022.pdf",
      "file_size_bytes": 1895432,
      "classification": "baseline_report",
      "confidence": 0.98,
      "classification_method": "filename_pattern",
      "metadata": {
        "page_count": 32,
        "creation_date": "2022-10-20",
        "has_tables": true
      },
      "indexed_at": "2023-11-15T10:35:01Z"
    }
  ]
}
```

**Rationale**: Centralized document index enables:
- Fast lookup without re-scanning files
- Classification caching
- Metadata enrichment over time
- Evidence mapping to specific documents

---

## Tools

Tools are atomic operations that perform single, well-defined tasks. They are composed by prompts into multi-step workflows.

### Tool 1: `create_session`

**Purpose**: Initialize a new review session with project metadata.

**Signature**:
```python
async def create_session(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: Optional[str] = None,
    proponent: Optional[str] = None
) -> dict
```

**Parameters**:
- `project_name`: Human-readable project name
- `documents_path`: Absolute path to folder containing project documents
- `methodology`: Methodology ID for checklist template selection
- `project_id`: Optional project ID (extracted if not provided)
- `proponent`: Optional proponent name

**Returns**:
```json
{
  "session_id": "REV-20231115-001",
  "status": "initialized",
  "project_metadata": { ... },
  "session_path": "/data/sessions/REV-20231115-001"
}
```

**Implementation Notes**:
- Generates unique session ID using timestamp + counter
- Creates session directory structure
- Validates documents_path exists and is readable
- Loads checklist template for specified methodology
- Initializes empty document index and findings store

**Error Handling**:
- Raises `ValueError` if documents_path does not exist
- Raises `ValueError` if methodology template not found
- Returns structured error if unable to create session directory

---

### Tool 2: `discover_documents`

**Purpose**: Scan document folder and index all files with basic classification.

**Signature**:
```python
async def discover_documents(
    session_id: str,
    ctx: Context
) -> dict
```

**Parameters**:
- `session_id`: Active session identifier
- `ctx`: MCP context for progress reporting

**Returns**:
```json
{
  "documents_found": 7,
  "documents": [
    {
      "document_id": "DOC-001",
      "filename": "4997Botany22 Public Project Plan.pdf",
      "classification": "project_plan",
      "confidence": 0.95
    }
  ],
  "classification_summary": {
    "project_plan": 1,
    "baseline_report": 1,
    "monitoring_report": 1,
    "ghg_emissions": 1,
    "methodology_reference": 1,
    "registry_review": 2,
    "unknown": 0
  }
}
```

**Implementation**:
1. Read session to get documents_path
2. Recursively scan directory for PDF files
3. For each file:
   - Extract basic metadata (size, dates, page count)
   - Attempt filename-based classification using patterns
   - Generate unique document_id
   - Store in document index
4. Report progress via `ctx.report_progress(current, total)`
5. Update session statistics

**Classification Logic**:
```python
FILENAME_PATTERNS = {
    "project_plan": r"project.?plan",
    "baseline_report": r"baseline.?report",
    "monitoring_report": r"monitoring.?report",
    "ghg_emissions": r"ghg.?emissions",
    "land_tenure": r"(deed|lease|land.?tenure)",
    "registry_review": r"registry.?agent.?review"
}
```

**Error Handling**:
- Skips non-PDF files with warning
- Logs files that fail classification as "unknown"
- Continues on individual file errors, reports at end

---

### Tool 3: `extract_pdf_text`

**Purpose**: Extract text content from PDF with optional page range.

**Signature**:
```python
async def extract_pdf_text(
    filepath: str,
    page_range: Optional[tuple[int, int]] = None,
    extract_tables: bool = False
) -> dict
```

**Parameters**:
- `filepath`: Absolute path to PDF file
- `page_range`: Optional (start_page, end_page) tuple (1-indexed)
- `extract_tables`: Whether to extract tables as structured data

**Returns**:
```json
{
  "text": "Full text content...",
  "page_count": 45,
  "pages_extracted": 45,
  "tables": [
    {
      "page": 12,
      "data": [[...], [...]]
    }
  ],
  "extraction_warnings": []
}
```

**Implementation**:
- Uses `pdfplumber` for text extraction
- Handles malformed PDFs gracefully
- Returns empty text on failure with warning
- Caches extracted text in document metadata

**Error Handling**:
- Returns `{"error": "message", "text": ""}` on failure
- Logs extraction warnings but doesn't fail

---

### Tool 4: `classify_document`

**Purpose**: Classify document type using filename and content analysis.

**Signature**:
```python
async def classify_document(
    document_id: str,
    session_id: str,
    force_content_analysis: bool = False
) -> dict
```

**Parameters**:
- `document_id`: Document to classify
- `session_id`: Session context
- `force_content_analysis`: Skip filename heuristic, analyze content

**Returns**:
```json
{
  "document_id": "DOC-001",
  "classification": "project_plan",
  "confidence": 0.95,
  "method": "filename_pattern",
  "alternative_classifications": [
    {"type": "baseline_report", "confidence": 0.3}
  ]
}
```

**Implementation**:
1. Try filename pattern matching first (fast)
2. If confidence < 0.7 or force_content_analysis:
   - Extract first 2 pages of text
   - Look for document type indicators in content
   - Check for specific sections/headers
3. Return classification with confidence score

**Content Indicators**:
```python
CONTENT_PATTERNS = {
    "project_plan": [
        r"project.?plan",
        r"project.?proponent",
        r"crediting.?period",
        r"section 8\."  # Program Guide references
    ],
    "baseline_report": [
        r"baseline",
        r"soil.?organic.?carbon",
        r"sampling.?protocol"
    ]
}
```

---

### Tool 5: `extract_project_metadata`

**Purpose**: Extract key project fields from project plan document.

**Signature**:
```python
async def extract_project_metadata(
    session_id: str,
    ctx: Context
) -> dict
```

**Parameters**:
- `session_id`: Session identifier
- `ctx`: Context for progress updates

**Returns**:
```json
{
  "project_name": "Botany Farm Regenerative Agriculture",
  "project_id": "C06-4997",
  "project_start_date": "2022-01-01",
  "crediting_period": "2022-2032",
  "crediting_period_duration": "10 years",
  "proponent": "Ecometric",
  "ecosystem_type": "Managed Grassland",
  "extraction_confidence": 0.85,
  "extracted_from": "DOC-001",
  "extraction_method": "pattern_matching"
}
```

**Implementation**:
1. Identify project_plan document from index
2. Extract full text
3. Use regex patterns to find key fields:
   - Project ID: `C\d{2}-\d+`
   - Dates: `\d{4}-\d{2}-\d{2}` or `\d{1,2}/\d{1,2}/\d{4}`
   - Crediting period: Look for "crediting period" heading
4. Validate extracted fields (date formats, ID patterns)
5. Update session metadata

**Pattern Examples**:
```python
PATTERNS = {
    "project_id": r"(?:Project ID|Project Number)[\s:]+([A-Z]\d{2}-\d+)",
    "start_date": r"(?:Project Start Date|Start Date)[\s:]+(\d{4}-\d{2}-\d{2})",
    "crediting_period": r"Crediting Period[\s:]+(\d{4})-(\d{4})"
}
```

---

### Tool 6: `map_requirement_to_documents`

**Purpose**: Find documents that contain evidence for a specific requirement.

**Signature**:
```python
async def map_requirement_to_documents(
    session_id: str,
    requirement_id: str,
    ctx: Context
) -> dict
```

**Parameters**:
- `session_id`: Session identifier
- `requirement_id`: Requirement from checklist (e.g., "REQ-002")
- `ctx`: Context for logging

**Returns**:
```json
{
  "requirement_id": "REQ-002",
  "requirement_text": "Provide evidence of legal land tenure...",
  "mapped_documents": [
    {
      "document_id": "DOC-001",
      "document_name": "4997Botany22 Public Project Plan.pdf",
      "relevance_score": 0.9,
      "evidence_found": true,
      "evidence_location": "Section 3.2, Pages 8-10"
    }
  ],
  "mapping_method": "keyword_search",
  "confidence": 0.85
}
```

**Implementation**:
1. Load requirement details from checklist
2. Extract keywords from requirement and accepted_evidence
3. For each document in index:
   - Search for keywords in document text
   - Calculate relevance score
   - Identify specific sections/pages
4. Rank documents by relevance
5. Store mapping in findings

**Keyword Extraction**:
```python
# For REQ-002 (Land Tenure)
keywords = ["land tenure", "deed", "lease", "ownership",
            "land use agreement", "legal control"]
```

---

### Tool 7: `extract_evidence`

**Purpose**: Extract specific evidence snippets from a document for a requirement.

**Signature**:
```python
async def extract_evidence(
    session_id: str,
    requirement_id: str,
    document_id: str,
    max_snippets: int = 3
) -> dict
```

**Parameters**:
- `session_id`: Session identifier
- `requirement_id`: Target requirement
- `document_id`: Document to extract from
- `max_snippets`: Maximum evidence snippets to return

**Returns**:
```json
{
  "requirement_id": "REQ-002",
  "document_id": "DOC-001",
  "evidence_snippets": [
    {
      "snippet_id": "EVID-001",
      "text": "The project proponent holds a 20-year lease agreement with the landowner, valid from 2022-01-01 to 2042-01-01, covering the entire 500-hectare project area.",
      "page": 8,
      "section": "3.2 Land Tenure",
      "confidence": 0.92,
      "extraction_method": "context_window"
    }
  ],
  "extraction_summary": "Found 1 high-confidence evidence snippet"
}
```

**Implementation**:
1. Load requirement keywords
2. Extract document text
3. Find keyword matches
4. Extract surrounding context (±100 words)
5. Score snippets by relevance
6. Return top N snippets with locations
7. Store in findings

---

### Tool 8: `validate_date_alignment`

**Purpose**: Check if two dates are within specified delta (e.g., imagery vs sampling within 4 months).

**Signature**:
```python
async def validate_date_alignment(
    session_id: str,
    date1_field: str,
    date2_field: str,
    max_delta_days: int = 120,
    ctx: Context
) -> dict
```

**Parameters**:
- `session_id`: Session identifier
- `date1_field`: First date field name
- `date2_field`: Second date field name
- `max_delta_days`: Maximum allowed difference in days
- `ctx`: Context for logging

**Returns**:
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
  "max_delta_days": 120,
  "status": "pass",
  "message": "Dates are within acceptable range (66 days < 120 days)"
}
```

**Implementation**:
1. Extract both dates from findings or documents
2. Parse dates (handle multiple formats)
3. Calculate difference in days
4. Compare to threshold
5. Return validation result with sources

---

### Tool 9: `validate_land_tenure`

**Purpose**: Cross-reference land ownership claims in project plan against registry documents.

**Signature**:
```python
async def validate_land_tenure(
    session_id: str,
    ctx: Context
) -> dict
```

**Returns**:
```json
{
  "validation_type": "land_tenure_consistency",
  "status": "pass",
  "project_plan_claim": {
    "owner_name": "John Smith",
    "area_hectares": 500,
    "tenure_type": "lease",
    "source": "DOC-001, Section 3.2"
  },
  "registry_documentation": {
    "owner_name": "John Smith",
    "area_hectares": 500,
    "document_type": "lease_agreement",
    "source": "DOC-003"
  },
  "consistency_checks": [
    {"field": "owner_name", "status": "match"},
    {"field": "area", "status": "match"},
    {"field": "tenure_type", "status": "match"}
  ],
  "message": "Land tenure claims are consistent across documents"
}
```

**Implementation**:
1. Extract ownership info from project plan
2. Find land tenure documents (deeds, leases)
3. Extract ownership info from those documents
4. Compare key fields (names, areas, dates)
5. Flag mismatches for human review

---

### Tool 10: `generate_review_report`

**Purpose**: Generate final checklist report with all findings.

**Signature**:
```python
async def generate_review_report(
    session_id: str,
    format: str = "markdown",
    include_evidence: bool = True
) -> dict
```

**Parameters**:
- `session_id`: Session identifier
- `format`: Output format ("markdown", "json", "html")
- `include_evidence`: Include evidence snippets in report

**Returns**:
```json
{
  "report_path": "/data/sessions/REV-20231115-001/report.md",
  "format": "markdown",
  "generated_at": "2023-11-15T12:00:00Z",
  "summary": {
    "total_requirements": 20,
    "approved": 15,
    "not_approved": 3,
    "pending_review": 2
  }
}
```

**Implementation**:
1. Load session, checklist, findings
2. For each requirement:
   - Populate "Submitted Material" with mapped documents
   - Set "Approved" status based on validations
   - Add "Comments" with AI findings and confidence
3. Generate report in requested format
4. Save to session directory
5. Return path

**Report Format** (Markdown):
```markdown
# Registry Agent Review

## Project Registration

| Project Name | Botany Farm Regenerative Agriculture |
| Project ID | C06-4997 |
| Crediting Period | 2022-2032 |
...

## Registry Agent Review Checklist

| Category | Requirement | Submitted Material | Approved | Comments |
|----------|-------------|-------------------|----------|----------|
| General | Projects shall apply the latest version... | **Primary**: 4997Botany22 Public Project Plan.pdf (Section 1.2) | ✓ | Verified methodology v1.2.2 on page 3 |
| Land Tenure | Provide evidence of legal land tenure... | **Primary**: 4997Botany22 Public Project Plan.pdf (Section 3.2) **Supplementary**: Land_Lease_Agreement.pdf | ✓ | Lease agreement confirmed, 20-year term covers crediting period |
```

---

### Tool 11: `update_session_state`

**Purpose**: Update session workflow progress and statistics.

**Signature**:
```python
async def update_session_state(
    session_id: str,
    workflow_stage: Optional[str] = None,
    statistics_update: Optional[dict] = None
) -> dict
```

**Parameters**:
- `session_id`: Session identifier
- `workflow_stage`: Stage to mark as completed
- `statistics_update`: Statistics fields to update

**Returns**:
```json
{
  "session_id": "REV-20231115-001",
  "updated_at": "2023-11-15T11:00:00Z",
  "current_status": "evidence_extraction"
}
```

**Implementation**:
- Atomically updates session.json
- Validates workflow stage transitions
- Updates timestamps
- Recalculates statistics if needed

---

### Tool 12: `export_review`

**Purpose**: Export finalized review in various formats for external use.

**Signature**:
```python
async def export_review(
    session_id: str,
    output_format: str = "pdf",
    output_path: Optional[str] = None
) -> dict
```

**Parameters**:
- `session_id`: Session to export
- `output_format`: "pdf", "markdown", "json", "excel"
- `output_path`: Optional custom output location

**Returns**:
```json
{
  "export_path": "/exports/REV-20231115-001.pdf",
  "format": "pdf",
  "exported_at": "2023-11-15T14:00:00Z",
  "file_size_bytes": 158392
}
```

---

## Prompts

Prompts are workflow orchestrators that compose multiple tools into guided, multi-step processes. They are the primary user interface to the MCP server.

### Prompt 1: `/initialize`

**Purpose**: Create a new review session and prepare for document processing.

**User Experience**:
```
Reviewer: /initialize
Agent: I'll help you initialize a new registry review session.

First, I need some information:
- Project name (or press Enter to extract from documents)
- Path to project documents folder
- Methodology (default: soil-carbon-v1.2.2)

Reviewer: Botany Farm
          /absolute/path/to/examples/22-23
          [Enter]

Agent: Creating review session...
       ✓ Session ID: REV-20231115-001
       ✓ Loaded checklist: Soil Carbon v1.2.2 (20 requirements)
       ✓ Validated document path
       ✓ Session initialized

Next step: Run /document-discovery to index all submitted documents.
```

**Workflow**:
1. Collect project metadata from user (or offer to extract)
2. Call `create_session()` tool
3. Verify checklist template exists
4. Initialize session directory structure
5. Report session ID and status
6. Suggest next step

**Returns**:
```python
@mcp.prompt()
def initialize(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2"
) -> list[base.Message]:
    return [
        base.UserMessage(f"Create review session for {project_name}"),
        base.AssistantMessage(
            f"I'll initialize a registry review session:\n"
            f"- Project: {project_name}\n"
            f"- Documents: {documents_path}\n"
            f"- Methodology: {methodology}"
        )
    ]
```

**Tool Composition**:
- `create_session()`
- `load_checklist_template()` (via resource)
- `update_session_state()`

---

### Prompt 2: `/document-discovery`

**Purpose**: Scan, classify, and index all documents in the project folder.

**User Experience**:
```
Reviewer: /document-discovery REV-20231115-001

Agent: Discovering and classifying documents...
       [Progress: 3/7 files processed]

       ✓ Discovery complete

       Found 7 documents:
       - Project Plan (1): 4997Botany22 Public Project Plan.pdf
       - Baseline Report (1): 4997Botany22...Baseline Report 2022.pdf
       - Monitoring Report (1): 4998Botany23...Monitoring Report 2023.pdf
       - GHG Emissions (1): 4998Botany23_GHG_Emissions_30_Sep_2023.pdf
       - Methodology (1): Methodology of the Farm Carbon Calculator.pdf
       - Registry Review (2): Botany Farm...[completed reviews]

       All documents classified with high confidence (avg: 0.93)

       Next step: Run /evidence-extraction to map requirements to documents.
```

**Workflow**:
1. Load session
2. Call `discover_documents()` with progress reporting
3. For each document:
   - Extract basic metadata
   - Classify using `classify_document()`
   - Store in document index
4. Display classification summary
5. Suggest next step

**Tool Composition**:
- `discover_documents()`
- `classify_document()` (per document)
- `extract_pdf_text()` (for classification)
- `update_session_state()`

---

### Prompt 3: `/evidence-extraction`

**Purpose**: Map each requirement to relevant documents and extract evidence snippets.

**User Experience**:
```
Reviewer: /evidence-extraction REV-20231115-001

Agent: Extracting evidence for 20 requirements...
       [Progress: 8/20 requirements processed]

       ✓ Evidence extraction complete

       Summary:
       - 18 requirements mapped to documents
       - 2 requirements have no clear evidence (flagged for review)
       - 156 evidence snippets extracted
       - Average confidence: 0.87

       Flagged requirements:
       - REQ-013 (GHG Accounting - Leakage): No yield data found
       - REQ-018 (Safeguards - Public Comment): No consultation records found

       Next step: Run /cross-validation to check consistency.
```

**Workflow**:
1. Load session and checklist
2. For each requirement:
   - Call `map_requirement_to_documents()`
   - For each mapped document:
     - Call `extract_evidence()`
   - Store findings
3. Flag requirements with low confidence or no evidence
4. Update statistics
5. Suggest next step

**Tool Composition**:
- `map_requirement_to_documents()` (per requirement)
- `extract_evidence()` (per document-requirement pair)
- `extract_project_metadata()` (if not done)
- `update_session_state()`

---

### Prompt 4: `/cross-validation`

**Purpose**: Run consistency checks across documents and validate critical fields.

**User Experience**:
```
Reviewer: /cross-validation REV-20231115-001

Agent: Running cross-document validations...

       ✓ Date alignment check
         - Imagery date: 2022-06-15
         - Sampling date: 2022-08-20
         - Delta: 66 days (< 120 days threshold)
         - Status: PASS

       ✓ Land tenure consistency
         - Project Plan owner: John Smith, 500 ha
         - Lease agreement: John Smith, 500 ha
         - Status: MATCH

       ✓ Project ID consistency
         - Found C06-4997 in 5/7 documents
         - Status: PASS

       ⚠ Warning: Crediting period end date
         - Project Plan: 2032-12-31
         - Baseline Report: 2032-01-01
         - Delta: 364 days
         - Status: FLAGGED (human review needed)

       Validation summary: 3 passed, 1 flagged

       Next step: Run /report-generation to create draft review.
```

**Workflow**:
1. Load session and findings
2. Run validation checks:
   - `validate_date_alignment()` for critical dates
   - `validate_land_tenure()` for ownership
   - Custom checks for project ID, dates, areas
3. Store validation results
4. Display summary with pass/fail/flagged
5. Suggest next step

**Tool Composition**:
- `validate_date_alignment()`
- `validate_land_tenure()`
- `update_session_state()`

---

### Prompt 5: `/report-generation`

**Purpose**: Generate complete checklist report with all findings.

**User Experience**:
```
Reviewer: /report-generation REV-20231115-001

Agent: Generating registry review report...

       ✓ Report generated

       Summary:
       - Total requirements: 20
       - Approved: 15 (evidence found, validations passed)
       - Not Approved: 3 (missing evidence or failed validation)
       - Pending Review: 2 (low confidence, needs human judgment)

       Report saved to:
       /data/sessions/REV-20231115-001/report.md

       Not Approved requirements:
       - REQ-013 (Leakage): No yield data found
       - REQ-018 (Public Comment): No consultation records
       - REQ-020 (Crediting Period): Date mismatch between documents

       Next step: Run /human-review to examine flagged items.
```

**Workflow**:
1. Load all session data
2. Call `generate_review_report()`
3. Populate checklist with:
   - Document mappings
   - Evidence snippets
   - Approval status
   - AI-generated comments
4. Save report
5. Display summary
6. Suggest next step

**Tool Composition**:
- `generate_review_report()`
- `update_session_state()`

---

### Prompt 6: `/human-review`

**Purpose**: Present structured review for human validation and editing.

**User Experience**:
```
Reviewer: /human-review REV-20231115-001

Agent: Here's your review report for human validation:

       Report location: /data/sessions/REV-20231115-001/report.md

       Items requiring your attention:

       1. REQ-013 (Leakage - Yield Reduction)
          Status: Not Approved
          Reason: No yield data found in submitted documents
          Action needed: Request historical yield data from proponent OR
                        confirm this requirement can be deferred to monitoring

       2. REQ-018 (Public Comment)
          Status: Not Approved
          Reason: No public consultation records found
          Action needed: Verify if consultation was required for this project type

       3. REQ-020 (Crediting Period)
          Status: Pending Review
          Reason: Date inconsistency (364 days difference)
          Confidence: Low (possible typo)
          Action needed: Confirm correct end date with proponent

       You can:
       - Edit the report directly in /data/sessions/.../report.md
       - Add your analysis and comments
       - Change approval status based on your judgment
       - Request clarifications from proponent

       When ready: Run /complete to finalize the review.
```

**Workflow**:
1. Load session and report
2. Identify items needing human attention:
   - Not Approved requirements
   - Low-confidence findings
   - Failed validations
3. Display each with context and suggested actions
4. Provide report location for editing
5. Explain next steps

**Tool Composition**:
- No tools (informational prompt)
- Reads session state and report

---

### Prompt 7: `/complete`

**Purpose**: Finalize review and export in required formats.

**User Experience**:
```
Reviewer: /complete REV-20231115-001

Agent: Finalizing review session...

       ✓ Session marked as complete
       ✓ Final report generated
       ✓ Exported to PDF: /exports/Botany_Farm_Review_20231115.pdf

       Review Summary:
       - Session ID: REV-20231115-001
       - Project: Botany Farm (C06-4997)
       - Completed: 2023-11-15 14:30:00
       - Documents processed: 7
       - Requirements reviewed: 20
       - Approved: 17
       - Not Approved: 3
       - Time saved: ~5.5 hours (estimated)

       Outputs:
       - Session archive: /data/sessions/REV-20231115-001/
       - Final report (Markdown): .../report.md
       - Exported PDF: /exports/Botany_Farm_Review_20231115.pdf
       - Findings JSON: .../findings.json

       Session complete! 🎉
```

**Workflow**:
1. Validate session is ready (human review done)
2. Mark session as complete
3. Call `export_review()` for final formats
4. Generate summary statistics
5. Archive session data
6. Display completion message

**Tool Composition**:
- `export_review()`
- `update_session_state()`

---

### Meta Prompt: `/extract-checklist`

**Purpose**: Help convert completed registry review PDFs into reusable JSON checklist templates.

**User Experience**:
```
Reviewer: /extract-checklist /path/to/completed-review.pdf

Agent: I'll help extract the checklist structure from this completed review.

       Analyzing document structure...

       ✓ Found checklist table on pages 3-8
       ✓ Identified 20 requirements across 14 categories

       Extracted structure:
       - General (1 requirement)
       - Land Tenure (1 requirement)
       - Project Area (2 requirements)
       - Project Boundary (1 requirement)
       ...

       Would you like me to:
       1. Generate JSON template
       2. Show extracted requirements for review
       3. Save to /data/checklists/

Reviewer: 1

Agent: Generated checklist template:

       {
         "methodology_id": "soil-carbon-v1.2.2",
         "requirements": [
           {
             "requirement_id": "REQ-001",
             "category": "General",
             "requirement_text": "Projects shall apply...",
             "source": "Program Guide, Section 8.1.3",
             ...
           }
         ]
       }

       Saved to: /data/checklists/soil-carbon-v1.2.2.json

       You can now use this checklist with:
       /initialize --methodology soil-carbon-v1.2.2
```

**Workflow**:
1. Load PDF
2. Identify checklist table
3. Parse table structure
4. Extract requirements
5. Generate JSON
6. Save to checklists directory

**Rationale**: Bootstrapping - enables creating new checklist templates from existing completed reviews, reducing manual data entry.

---

## Testing & Validation

### Integration Test: Botany Farm Example

**Test Case**: Run full workflow against `/examples/22-23/`

**Expected Behavior**:

1. **Initialize**:
   - Creates session successfully
   - Loads soil-carbon-v1.2.2 checklist (20 requirements)
   - Validates document path exists

2. **Document Discovery**:
   - Finds 7 PDF files
   - Classifies correctly:
     - 1 project plan
     - 1 baseline report
     - 1 monitoring report
     - 1 GHG emissions
     - 1 methodology reference
     - 2 registry reviews
   - Average classification confidence >0.85

3. **Evidence Extraction**:
   - Maps 18+ requirements to documents
   - Extracts project ID: C06-4997
   - Extracts project name: Botany Farm
   - Extracts dates correctly
   - Flags 2-3 requirements with missing evidence

4. **Cross-Validation**:
   - Date alignment check passes
   - Land tenure consistency (if docs present)
   - Project ID found in multiple documents

5. **Report Generation**:
   - Generates markdown report
   - Populates checklist table
   - Includes evidence citations
   - Marks approval status

6. **Export**:
   - Creates PDF successfully
   - File size >100KB
   - Contains all sections

**Success Criteria**:
- Zero crashes
- 15+ requirements successfully mapped
- Report generates in <30 seconds
- Human can complete review in <1 hour (vs 6-8 hours manual)

---

### Unit Tests

**Test Coverage**:

1. **Tool Tests**:
   - `test_create_session()` - validates session creation
   - `test_discover_documents()` - mocked file system
   - `test_classify_document()` - known document types
   - `test_extract_evidence()` - sample PDFs
   - `test_validate_date_alignment()` - edge cases
   - `test_generate_report()` - output format validation

2. **Prompt Tests**:
   - `test_initialize_prompt()` - message generation
   - `test_document_discovery_prompt()` - workflow composition
   - `test_evidence_extraction_prompt()` - progress reporting

3. **Resource Tests**:
   - `test_checklist_resource()` - JSON loading
   - `test_session_resource()` - state persistence

**Test Data**:
- Sample PDFs in `/tests/fixtures/`
- Mock session JSON files
- Reference checklist templates

---

## Implementation Notes

### Development Workflow

1. **Local Testing**:
```bash
# Install dependencies
uv sync

# Run MCP server locally
uv run python src/registry_review_mcp/server.py

# Test with MCP Inspector
npx @modelcontextprotocol/inspector uv run python src/registry_review_mcp/server.py
```

2. **Claude Code Integration**:
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
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

3. **Running Tests**:
```bash
# Unit tests
uv run pytest tests/

# Integration test with example data
uv run pytest tests/test_integration.py --example-data=examples/22-23
```

---

### Error Handling Philosophy

**Fail Explicit, Not Silent**:
- When extraction fails, return empty with warning
- When confidence is low (<0.7), escalate to human
- When validation fails, flag for review (don't auto-reject)

**Progressive Degradation**:
- Filename classification → Content classification → Manual classification
- Pattern matching → LLM extraction (future)
- Fast heuristics → Slow analysis (only when needed)

**Human-in-the-Loop**:
- AI suggests, human confirms
- Low confidence = mandatory review
- Failed validations = review, not rejection

---

### Performance Targets

**MVP Goals**:
- Session creation: <2 seconds
- Document discovery (7 files): <10 seconds
- Evidence extraction (20 requirements): <60 seconds
- Report generation: <5 seconds
- Total workflow: <2 minutes machine time

**Optimization Opportunities**:
- Cache extracted text
- Parallel document processing
- Incremental saves (resume on crash)
- Pre-compiled patterns

---

### Security Considerations

**File Access**:
- Validate all file paths (prevent directory traversal)
- Restrict to configured document roots
- No deletion operations (read-only on source documents)

**Data Privacy**:
- Session data contains project details
- Store sessions in protected directory
- No external API calls (all local processing)

**Input Validation**:
- Sanitize file paths
- Validate date formats
- Escape special characters in reports

---

## Future Extensions

### Phase 2: Cloud Connectors

**Google Drive Integration**:
- OAuth 2.0 authentication
- Read-only access to shared folders
- Automatic document sync

**SharePoint Integration**:
- Microsoft Graph API
- Ecometric folder access
- Batch project support

**Implementation**:
- Abstract `DocumentSource` interface
- Pluggable connectors
- Same tool signatures, different backends

---

### Phase 3: Batch Processing

**Aggregated Projects**:
- Process 70-farm batches in parallel
- Master batch review document
- Per-farm findings
- Bulk approval workflow

**Architecture**:
- `create_batch_session()`
- Parallel `discover_documents()` per farm
- Aggregated `generate_batch_report()`

---

### Phase 4: Credit Issuance Review

**Extended Workflow**:
- Monitoring report validation
- Carbon calculation verification
- Sampling data checks
- AI model output validation

**New Requirements**:
- More complex validations
- Calculation audits
- Temporal data analysis

---

### Phase 5: Advanced Extraction

**ML-Based Extraction**:
- Fine-tuned models for document classification
- Table structure recognition
- Form field extraction
- Geospatial data parsing

**Integration Points**:
- Replace pattern matching with ML inference
- Same tool interfaces
- Confidence scoring
- Fallback to heuristics

---

## Appendix A: Data Models

### Session Model

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class ProjectMetadata(BaseModel):
    project_name: str
    project_id: Optional[str] = None
    crediting_period: Optional[str] = None
    submission_date: Optional[datetime] = None
    methodology: str = "soil-carbon-v1.2.2"
    proponent: Optional[str] = None
    documents_path: str

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
    requirements_mapped: int = 0
    requirements_pending: int = 0
    validations_passed: int = 0
    validations_failed: int = 0
    validations_pending: int = 0

class Session(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    project_metadata: ProjectMetadata
    workflow_progress: WorkflowProgress
    statistics: SessionStatistics
```

---

### Document Model

```python
class DocumentMetadata(BaseModel):
    page_count: Optional[int] = None
    creation_date: Optional[datetime] = None
    modification_date: Optional[datetime] = None
    has_tables: bool = False
    has_maps: bool = False
    file_size_bytes: int

class ExtractedFields(BaseModel):
    project_name: Optional[str] = None
    project_id: Optional[str] = None
    project_start_date: Optional[str] = None
    crediting_period: Optional[str] = None

class Document(BaseModel):
    document_id: str
    filename: str
    filepath: str
    file_size_bytes: int
    classification: str
    confidence: float = Field(ge=0.0, le=1.0)
    classification_method: str
    metadata: DocumentMetadata
    extracted_fields: Optional[ExtractedFields] = None
    indexed_at: datetime
```

---

### Requirement Model

```python
class Requirement(BaseModel):
    requirement_id: str
    category: str
    requirement_text: str
    source: str  # Program Guide section
    accepted_evidence: str
    mandatory: bool = True
    validation_type: Literal[
        "document_presence",
        "cross_document",
        "date_alignment",
        "calculation",
        "manual"
    ]
```

---

### Finding Model

```python
class EvidenceSnippet(BaseModel):
    snippet_id: str
    text: str
    page: int
    section: Optional[str] = None
    confidence: float
    extraction_method: str

class RequirementFinding(BaseModel):
    requirement_id: str
    mapped_documents: list[str]  # document_ids
    evidence_snippets: list[EvidenceSnippet]
    approval_status: Literal["approved", "not_approved", "pending_review"]
    ai_comments: Optional[str] = None
    human_comments: Optional[str] = None
    confidence: float
```

---

## Appendix B: Checklist JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["methodology_id", "version", "requirements"],
  "properties": {
    "methodology_id": {
      "type": "string",
      "description": "Unique identifier for this methodology"
    },
    "methodology_name": {
      "type": "string"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$"
    },
    "protocol": {
      "type": "string"
    },
    "program_guide_version": {
      "type": "string"
    },
    "requirements": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "requirement_id",
          "category",
          "requirement_text",
          "source",
          "accepted_evidence"
        ],
        "properties": {
          "requirement_id": {
            "type": "string",
            "pattern": "^REQ-\\d{3}$"
          },
          "category": {
            "type": "string"
          },
          "requirement_text": {
            "type": "string"
          },
          "source": {
            "type": "string"
          },
          "accepted_evidence": {
            "type": "string"
          },
          "mandatory": {
            "type": "boolean",
            "default": true
          },
          "validation_type": {
            "type": "string",
            "enum": [
              "document_presence",
              "cross_document",
              "date_alignment",
              "calculation",
              "manual"
            ]
          }
        }
      }
    }
  }
}
```

---

## Appendix C: MCP Server Configuration

### pyproject.toml

```toml
[project]
name = "registry-review-mcp"
version = "1.0.0"
description = "MCP server for Regen Registry project review automation"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.21.0",
    "pdfplumber>=0.11.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

### Claude Code Configuration

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
        "LOG_LEVEL": "INFO",
        "DATA_DIR": "/absolute/path/to/regen-registry-review-mcp/data"
      }
    }
  }
}
```

---

## Conclusion

This specification defines a minimal yet complete MCP server for automating registry review workflows. By focusing on the most time-consuming, systematizable tasks—document organization, metadata extraction, and consistency checking—the server enables a single reviewer to handle 100+ annual projects while maintaining high-quality, auditable compliance reviews.

The architecture prioritizes:
- **Testability** through small, composable tools
- **Debuggability** through explicit session state
- **Extensibility** through abstract interfaces
- **Usability** through guided workflow prompts
- **Reliability** through fail-explicit design

The MVP targets single-project registration review using local files, with clear extension points for batch processing, cloud connectors, and credit issuance review.

**Success Metric**: Transform a 6-8 hour manual task into a 30-minute guided workflow with higher consistency and complete traceability.

---

**Next Steps**:
1. Review and approve specification
2. Create `/data/checklists/soil-carbon-v1.2.2.json` from example checklist
3. Implement core tools (`create_session`, `discover_documents`, `extract_pdf_text`)
4. Implement `/initialize` and `/document-discovery` prompts
5. Test against `/examples/22-23/` data
6. Iterate based on real-world usage with Becca

---

*Document Version: 1.0.0*
*Last Updated: November 11, 2025*
*Status: Ready for Review*
