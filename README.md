# Registry Review MCP Server

**Version:** 2.0.0
**Status:** Phase 2 Complete (Document Processing)
**Next:** Phase 3 (Evidence Extraction)

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

\`\`\`bash
# Install dependencies
uv sync

# Run the MCP server (for Claude Desktop integration)
uv run python -m registry_review_mcp.server

# Or run tests
uv run pytest
\`\`\`

Once integrated with Claude Desktop, try:
\`\`\`
/document-discovery
\`\`\`

The prompt will guide you through creating a session if needed, then discover and classify all project documents automatically.

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
- **Quick-Start Workflow** - Single-command session creation + discovery
- **Auto-Selection** - Prompts automatically select most recent session
- **Helpful Guidance** - Clear error messages with actionable next steps

### 🚧 Phase 3-5: Planned

- Evidence extraction and requirement mapping (Phase 3)
- Cross-document validation (Phase 4)
- Report generation - Markdown, JSON, PDF (Phase 4)
- Human review workflow (Phase 5)

---

## Installation

### Prerequisites

- Python >=3.10
- [UV](https://github.com/astral-sh/uv) package manager

### Setup

\`\`\`bash
# Clone repository
cd regen-registry-review-mcp

# Install dependencies
uv sync

# Verify installation
uv run python -m registry_review_mcp.server
\`\`\`

---

## Configuration

### Claude Desktop Integration

Add to \`claude_desktop_config.json\`:

\`\`\`json
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
\`\`\`

Restart Claude Desktop to load the server.

---

## Usage

### Three Ways to Get Started

**1. Easiest: Use the Document Discovery Prompt**

Simply call the prompt without any parameters:
\`\`\`
/document-discovery
\`\`\`

The prompt will:
- Auto-select your most recent session, or
- Guide you to create a new session if none exists
- Discover and classify all documents
- Show detailed results with next steps

**2. Quick-Start Tool (Recommended for New Projects)**

Create a session and discover documents in one command:
\`\`\`
start_review(
    project_name="Botany Farm 2022-2023",
    documents_path="/absolute/path/to/examples/22-23",
    methodology="soil-carbon-v1.2.2"
)
\`\`\`

**3. Manual Workflow (Most Control)**

Step-by-step control over the process:
\`\`\`
# Step 1: Create a session
create_session(
    project_name="My Project",
    documents_path="/path/to/documents",
    methodology="soil-carbon-v1.2.2",
    project_id="C06-4997"
)

# Step 2: Discover documents
discover_documents(session_id="session-abc123")

# Step 3: Extract text from a specific PDF
extract_pdf_text(
    filepath="/path/to/document.pdf",
    start_page=1,
    end_page=10
)

# Step 4: Get GIS metadata
extract_gis_metadata(filepath="/path/to/boundary.shp")
\`\`\`

### Available Tools

**Session Management:**
- \`start_review\` - Quick-start: Create session and discover documents in one step
- \`create_session\` - Create new review session
- \`load_session\` - Load existing session
- \`list_sessions\` - List all sessions
- \`delete_session\` - Delete a session

**Document Processing:**
- \`discover_documents\` - Scan and classify project documents
- \`extract_pdf_text\` - Extract text from PDF files
- \`extract_gis_metadata\` - Extract GIS shapefile metadata

**Prompts:**
- \`/document-discovery\` - Run complete document discovery workflow

### Example Session

\`\`\`
# Start a new review (auto-creates session + discovers docs)
> start_review(
    project_name="Botany Farm",
    documents_path="/path/to/examples/22-23"
)

✓ Review Started Successfully

Session ID: session-abc123
Project: Botany Farm
Documents Found: 7

Classification Summary:
  - baseline_report: 1
  - monitoring_report: 1
  - project_plan: 1
  - registry_review: 2
  - ghg_emissions: 1
  - methodology_reference: 1

# Get detailed view with next steps
> /document-discovery

# Document Discovery Complete

**Project:** Botany Farm
**Session:** session-abc123

## Summary

Found **7 document(s)**

### Classification Breakdown
  • baseline_report: 1
  • ghg_emissions: 1
  • methodology_reference: 1
  • monitoring_report: 1
  • project_plan: 1
  • registry_review: 2

## Discovered Documents

1. ✓ 4997Botany22_Public_Project_Plan.pdf
   Type: project_plan (95% confidence)
   ID: DOC-334859c4

2. ✓ 4997Botany22_Soil_Organic_Carbon_Project_Public_Baseline_Report_2022.pdf
   Type: baseline_report (95% confidence)
   ID: DOC-b4e159f4

...

Next Steps:
1. Review the document classification above
2. Proceed to evidence extraction (Phase 3)
\`\`\`

---

## Development

### Running Tests

\`\`\`bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test suites
uv run pytest tests/test_infrastructure.py -v
uv run pytest tests/test_document_processing.py -v
uv run pytest tests/test_locking.py -v
uv run pytest tests/test_user_experience.py -v
\`\`\`

**Current Test Coverage:**
- 36 total tests
- Phase 1 (Infrastructure): 23 tests
- Phase 2 (Document Processing): 6 tests
- Locking Mechanism: 4 tests
- UX Improvements: 5 tests

### Code Quality

\`\`\`bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/
\`\`\`

---

## Project Structure

\`\`\`
regen-registry-review-mcp/
├── src/registry_review_mcp/   # Main package
│   ├── server.py               # MCP entry point
│   ├── config/                 # Configuration
│   ├── models/                 # Pydantic schemas
│   ├── tools/
│   │   ├── session_tools.py    # Session management
│   │   └── document_tools.py   # Document processing (NEW)
│   ├── prompts/
│   │   └── document_discovery.py  # Discovery workflow (NEW)
│   └── utils/
│       ├── state.py            # State management with locking
│       └── cache.py            # Caching utilities
├── data/
│   ├── checklists/             # Methodology requirements
│   ├── sessions/               # Active sessions (gitignored)
│   └── cache/                  # Cached data (gitignored)
├── tests/
│   ├── test_infrastructure.py  # Phase 1 tests
│   ├── test_document_processing.py  # Phase 2 tests (NEW)
│   ├── test_locking.py         # Locking mechanism tests (NEW)
│   └── test_user_experience.py # UX improvement tests (NEW)
├── examples/22-23/             # Botany Farm test data
├── docs/                       # Specifications
├── pyproject.toml
├── ROADMAP.md
└── README.md
\`\`\`

---

## The 7-Stage Workflow

1. ✅ **Initialize** - Create session and load checklist
2. ✅ **Document Discovery** - Scan and classify all documents
3. 🚧 **Evidence Extraction** - Map requirements to evidence
4. 📋 **Cross-Validation** - Verify consistency across documents
5. 📋 **Report Generation** - Generate structured review report
6. 📋 **Human Review** - Present flagged items for decision
7. 📋 **Complete** - Finalize and export report

---

## Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed implementation plan.

**Current Status:**
- ✅ Phase 1 (Foundation): Complete
- ✅ Phase 2 (Document Processing): Complete
- 🚧 Phase 3 (Evidence Extraction): Next
- 📋 Phase 4 (Validation & Reporting): Planned
- 📋 Phase 5 (Integration & Polish): Planned

**Recent Achievements:**
- Implemented document discovery with smart classification
- Added PDF text extraction with caching
- Built GIS metadata extraction
- Created quick-start workflow for better UX
- Fixed critical deadlock bug in locking mechanism
- Added comprehensive test coverage (36 tests)

---

## License

Copyright © 2025 Regen Network Development, Inc.

---

**Last Updated:** November 12, 2025
**Next Milestone:** Phase 3 - Evidence Extraction
