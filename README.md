# Registry Review MCP Server

**Version:** 2.0.0
**Status:** Phase 4 Complete (Cross-Validation & Report Generation)
**Next:** Phase 5 (Integration & Polish)

Automated registry review workflows for carbon credit project registration using the Model Context Protocol (MCP).

---

## Overview

The Registry Review MCP Server automates the manual document review process for carbon credit project registration. It transforms a 6-8 hour manual review into a 60-90 minute guided workflow with complete audit trail and structured outputs.

**Core Value Proposition:** Enable Registry Agents (like Becca) to process project documentation 5-10x faster by automating:
- Document discovery and classification
- Evidence extraction and requirement mapping
- Cross-document validation
- Compliance checking and report generation

---

## Quick Start

```bash
# Install dependencies
uv sync

# Run the MCP server (for Claude Desktop integration)
uv run python -m registry_review_mcp.server

# Or run tests
uv run pytest
```

Once integrated with Claude Desktop, try the complete workflow:

```
/initialize Botany Farm 2022-2023, /absolute/path/to/examples/22-23
/document-discovery
/evidence-extraction
/cross-validation
/report-generation
```

The prompts guide you through the entire review process automatically!

---

## Features

### ✅ Phase 1: Foundation (Complete)

- **Session Management** - Create, load, update, and delete review sessions
- **Atomic State Persistence** - Thread-safe file operations with locking
- **Configuration Management** - Environment-based settings with validation
- **Error Hierarchy** - Comprehensive error types for graceful handling
- **Caching Infrastructure** - TTL-based caching for expensive operations
- **Checklist System** - Soil Carbon v1.2.2 methodology with 23 requirements

### ✅ Phase 2: Document Processing (Complete)

- **Document Discovery** - Recursively scan project directories for documents
- **Smart Classification** - Auto-classify documents by type (project plan, baseline report, monitoring report, etc.)
- **PDF Text Extraction** - Extract text and tables from PDF documents with caching
- **GIS Metadata** - Extract metadata from shapefiles and GeoJSON files
- **Markdown Integration** - Read markdown conversions from marker skill
- **Quick-Start Workflow** - Single-command session creation + discovery
- **Auto-Selection** - Prompts automatically select most recent session
- **Helpful Guidance** - Clear error messages with actionable next steps

### ✅ Phase 3: Evidence Extraction (Complete)

- **Requirement Mapping** - Automatically map all 23 checklist requirements to documents
- **Evidence Extraction** - Extract text snippets with ±100 words of context
- **Page Citations** - Include page numbers from PDF markers for precise references
- **Section References** - Add markdown section headers for navigation
- **Keyword-Based Search** - Smart keyword extraction with phrase detection and stop-word filtering
- **Relevance Scoring** - Documents scored 0.0-1.0 based on keyword coverage and density
- **Status Classification** - Automatic covered/partial/missing/flagged classification
- **Coverage Analysis** - Overall statistics with confidence scores (85-90% accuracy on test data)
- **Structured Field Extraction** - Extract specific data fields (dates, IDs) using regex patterns

### ✅ Phase 4: Validation & Reporting (Complete)

- **Cross-Document Validation** - Date alignment (120-day rule), land tenure (fuzzy matching), project ID consistency
- **Validation Results** - Status indicators (pass/warning/fail) with flagged items for review
- **Report Generation** - Markdown and JSON formats with complete findings and evidence
- **Structured Output** - Machine-readable reports with all evidence, validations, and citations
- **Summary Statistics** - Requirements coverage, validation results, items for human review

### 📋 Phase 5: Planned

- Human review workflow and approval decision support
- Export to additional formats (PDF, CSV)
- Advanced contradiction detection
- Integration with external registry systems

---

## Installation

### Prerequisites

- Python >=3.10
- [UV](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone repository
cd regen-registry-review-mcp

# Install dependencies
uv sync

# Verify installation
uv run python -m registry_review_mcp.server
```

---

## Configuration

### Claude Desktop Integration

Add to `claude_desktop_config.json`:

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
      ],
      "env": {
        "REGISTRY_REVIEW_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

Restart Claude Desktop to load the server.

---

## Usage

### The Complete Workflow (3 Simple Prompts)

**Stage 1: Initialize**
```
/initialize Botany Farm 2022-2023, /absolute/path/to/examples/22-23
```
Creates a new review session with project metadata.

**Stage 2: Document Discovery**
```
/document-discovery
```
Discovers and classifies all documents (auto-selects your session).

**Stage 3: Evidence Extraction**
```
/evidence-extraction
```
Maps all requirements to evidence with page citations (auto-selects your session).

That's it! Three prompts, fully automated, highly informative results.

### Alternative: Provide Details to Any Stage

Each prompt can accept project details directly:

```
/document-discovery Botany Farm 2022-2023, /path/to/documents
```

This creates a session and discovers documents in one step!

### Available Tools

**Session Management:**
- `start_review` - Quick-start: Create session and discover documents in one step
- `create_session` - Create new review session
- `load_session` - Load existing session
- `list_sessions` - List all sessions
- `delete_session` - Delete a session

**Document Processing:**
- `discover_documents` - Scan and classify project documents
- `extract_pdf_text` - Extract text from PDF files
- `extract_gis_metadata` - Extract GIS shapefile metadata

**Evidence Extraction:**
- `extract_evidence` - Map all requirements to documents and extract evidence
- `map_requirement` - Map a single requirement to documents with evidence snippets

**Validation:**
- `cross_validate` - Run all cross-document validation checks
- `validate_date_alignment` - Verify dates are within 120-day rule
- `validate_land_tenure` - Check land tenure consistency with fuzzy name matching
- `validate_project_id` - Verify project ID patterns and consistency

**Report Generation:**
- `generate_review_report` - Generate complete review report in Markdown or JSON
- `export_review` - Export report to custom location

**Prompts (Workflow Stages):**
- `/initialize` - Stage 1: Create session and load checklist
- `/document-discovery` - Stage 2: Discover and classify documents
- `/evidence-extraction` - Stage 3: Extract evidence for all requirements
- `/cross-validation` - Stage 4: Run cross-document validation checks
- `/report-generation` - Stage 5: Generate complete review reports

### Example Session

```
# Stage 1: Initialize a new review
> /initialize Botany Farm 2022-2023, /home/user/projects/botany-farm

✅ Registry Review Session Initialized

Session ID: session-6b38c7e86bae
Project: Botany Farm 2022-2023
Methodology: Soil Carbon v1.2.2
Created: 2025-11-12T23:33:41Z

Next Step: Run /document-discovery

# Stage 2: Discover documents
> /document-discovery

✓ Document Discovery Complete

Session: session-6b38c7e86bae
Project: Botany Farm 2022-2023
Found 7 document(s)

Classification Summary:
  • baseline_report: 1
  • ghg_emissions: 1
  • methodology_reference: 1
  • monitoring_report: 1
  • project_plan: 1
  • registry_review: 2

Discovered Documents:
1. ✓ 4997Botany22_Public_Project_Plan.pdf
   Type: project_plan (95% confidence)
   ID: DOC-334859c4

2. ✓ 4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf
   Type: baseline_report (95% confidence)
   ID: DOC-b4e159f4

... (5 more documents)

Next Steps: Run /evidence-extraction

# Stage 3: Extract evidence
> /evidence-extraction

================================================================================
EVIDENCE EXTRACTION RESULTS
================================================================================

📊 Coverage Summary:
  Total Requirements: 23
  ✅ Covered:  11 (47.8%)
  ⚠️  Partial:  12 (52.2%)
  ❌ Missing:   0 (0.0%)
  Overall Coverage: 73.9%

✅ COVERED REQUIREMENTS (11):
  REQ-002: Provide evidence of legal land tenure and control...
    Confidence: 1.00
    Documents: 5, Snippets: 15

  REQ-003: No conversion from natural ecosystems...
    Confidence: 1.00
    Documents: 5, Snippets: 15

... (9 more covered requirements)

⚠️  PARTIAL REQUIREMENTS (12):
  REQ-001: Projects shall apply the latest version...
    Confidence: 0.39
    Documents: 5, Snippets: 15

... (11 more partial requirements)

================================================================================
NEXT STEPS
================================================================================

📄 Results saved to: evidence.json
📊 Session updated with coverage statistics

View detailed evidence for a specific requirement:
map_requirement("session-6b38c7e86bae", "REQ-007")
```

---

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test suites
uv run pytest tests/test_infrastructure.py -v
uv run pytest tests/test_document_processing.py -v
uv run pytest tests/test_evidence_extraction.py -v
uv run pytest tests/test_locking.py -v
uv run pytest tests/test_user_experience.py -v
```

**Current Test Coverage:**
- 61 total tests (100% passing)
- Phase 1 (Infrastructure): 23 tests
- Phase 2 (Document Processing): 6 tests
- Phase 3 (Evidence Extraction): 6 tests
- Phase 4 (Validation & Reporting): 19 tests
- Locking Mechanism: 4 tests
- UX Improvements: 3 tests

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/
```

---

## Project Structure

```
regen-registry-review-mcp/
├── src/registry_review_mcp/   # Main package
│   ├── server.py               # MCP entry point
│   ├── config/                 # Configuration
│   ├── models/
│   │   ├── session.py          # Session models
│   │   ├── evidence.py         # Evidence models
│   │   ├── validation.py       # Validation models (Phase 4)
│   │   ├── report.py           # Report models (Phase 4)
│   │   └── errors.py           # Error types
│   ├── tools/
│   │   ├── session_tools.py    # Session management
│   │   ├── document_tools.py   # Document processing
│   │   ├── evidence_tools.py   # Evidence extraction
│   │   ├── validation_tools.py # Cross-document validation (Phase 4)
│   │   └── report_tools.py     # Report generation (Phase 4)
│   ├── prompts/
│   │   ├── initialize.py       # Stage 1: Initialize
│   │   ├── document_discovery.py  # Stage 2: Discovery
│   │   ├── evidence_extraction.py # Stage 3: Extraction
│   │   ├── cross_validation.py    # Stage 4: Validation (Phase 4)
│   │   └── report_generation.py   # Stage 5: Reporting (Phase 4)
│   └── utils/
│       ├── state.py            # State management with locking
│       └── cache.py            # Caching utilities
├── data/
│   ├── checklists/             # Methodology requirements
│   ├── sessions/               # Active sessions (gitignored)
│   └── cache/                  # Cached data (gitignored)
├── tests/
│   ├── test_infrastructure.py  # Phase 1 tests
│   ├── test_document_processing.py  # Phase 2 tests
│   ├── test_evidence_extraction.py  # Phase 3 tests
│   ├── test_validation.py      # Phase 4 validation tests
│   ├── test_report_generation.py  # Phase 4 reporting tests
│   ├── test_locking.py         # Locking mechanism tests
│   └── test_user_experience.py # UX improvement tests
├── examples/22-23/             # Botany Farm test data
│   └── */                      # Markdown versions from marker
├── docs/
│   ├── PHASE_2_COMPLETION.md   # Phase 2 summary
│   ├── PHASE_3_COMPLETION.md   # Phase 3 summary
│   ├── PHASE_4_COMPLETION.md   # Phase 4 summary (NEW)
│   └── PROMPT_DESIGN_PRINCIPLES.md  # MCP prompt design standards (NEW)
├── pyproject.toml
├── ROADMAP.md
└── README.md
```

---

## The 7-Stage Workflow

1. ✅ **Initialize** - Create session and load checklist
2. ✅ **Document Discovery** - Scan and classify all documents
3. ✅ **Evidence Extraction** - Map requirements to evidence with page citations
4. ✅ **Cross-Validation** - Verify consistency across documents (dates, land tenure, project IDs)
5. ✅ **Report Generation** - Generate structured review report (Markdown + JSON)
6. 📋 **Human Review** - Present flagged items for decision (Phase 5)
7. 📋 **Complete** - Finalize and export report (Phase 5)

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed implementation plan.

**Current Status:**
- ✅ Phase 1 (Foundation): Complete
- ✅ Phase 2 (Document Processing): Complete
- ✅ Phase 3 (Evidence Extraction): Complete
- ✅ Phase 4 (Validation & Reporting): Complete
- 📋 Phase 5 (Integration & Polish): Next

**Phase 4 Achievements:**
- Implemented cross-document validation with three key checks:
  - Date alignment validation (120-day rule with customizable threshold)
  - Land tenure validation (fuzzy name matching with surname boost)
  - Project ID validation (pattern matching and consistency checks)
- Built comprehensive report generation in multiple formats:
  - Markdown reports with complete findings and evidence
  - JSON reports for programmatic access and integration
- Added validation status indicators (pass/warning/fail) with flagged items
- Implemented auto-selection with visible user feedback for all workflow prompts
- Created systematic prompt design principles document to ensure consistency
- Complete test coverage (61/61 tests passing - 100%)

**Performance Metrics:**
- Full evidence extraction: ~2.4 seconds for 23 requirements
- Cross-validation: <1 second for all checks
- Report generation: ~0.5 seconds for both Markdown and JSON
- Coverage on Botany Farm: 73.9% (11 covered, 12 partial, 0 missing)
- Test execution: ~10 seconds for full suite (61 tests)

---

## License

Copyright © 2025 Regen Network Development, Inc.

---

**Last Updated:** November 12, 2025
**Next Milestone:** Phase 5 - Integration, Human Review Workflow & Polish
