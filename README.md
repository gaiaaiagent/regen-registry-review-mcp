# Registry Review MCP Server

MCP server and web application that automates carbon credit project registration reviews through an eight-stage workflow.

## Overview

The Registry Review system transforms a 6-8 hour manual document review into a 60-90 minute guided workflow where AI handles document organization, data extraction, and consistency checking while humans provide expertise, judgment, and final approval.

**Core Capabilities:**
- Document discovery and intelligent classification
- Requirement mapping with semantic matching
- Evidence extraction with PDF bounding box coordinates for click-to-highlight
- Cross-document validation (dates, land tenure, project IDs)
- Structured report generation (Markdown + JSON)
- Web-based review workspace with side-by-side document viewing

## Live Deployment

The application is deployed at: **https://registry.regen.gaiaai.xyz/**

## Quick Start

### Web Application (Recommended)

```bash
# Install dependencies
uv sync
cd web_app && npm install && cd ..

# Start backend API (port 8003)
python chatgpt_rest_api.py

# In another terminal, start frontend (port 5173)
cd web_app && npm run dev
```

Then open http://localhost:5173 in your browser.

### MCP Server Only (Claude Desktop)

```bash
# Install dependencies
uv sync

# Run the MCP server
uv run python -m registry_review_mcp.server

# Run tests (expensive tests excluded by default)
uv run pytest
```

## Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "registry-review": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/regen-registry-review-mcp",
        "run", "python", "-m", "registry_review_mcp.server"
      ]
    }
  }
}
```

## The Eight-Stage Workflow

Each stage produces artifacts for human verification before proceeding. The workflow follows a collaboration model where AI handles tedious document processing while humans provide expertise and final judgment.

### Stage A: Initialize

Create a review session with project metadata and load the checklist template.

```
/A-initialize Botany Farm 2022-2023, /path/to/documents
```

**Output:** Session ID, project metadata, loaded checklist (23 requirements for Soil Carbon v1.2.2)

### Stage B: Document Discovery

Scan the documents directory, extract file metadata, and classify each document by type.

```
/B-document-discovery
```

**Agent Actions:**
- Recursively scan for PDFs, shapefiles, GeoJSON, spreadsheets
- Classify documents (project plan, baseline report, monitoring report, land tenure, etc.)
- Generate document inventory with confidence scores

**Human Actions:** Review classifications, mark documents as in-scope/ignored/pinned

**Output:** Document inventory with normalized names, types, and source references

### Stage C: Requirement Mapping

Connect discovered documents to specific checklist requirements using semantic matching.

```
/C-requirement-mapping
```

**Agent Actions:**
- Parse checklist into structured requirements with expected evidence types
- Analyze documents and suggest requirement → document mappings
- Flag requirements with no plausible matches

**Human Actions:** Confirm/reject suggested mappings, manually add missing mappings

**Output:** Mapping matrix linking each requirement to 0+ documents with confidence scores

### Stage D: Evidence Extraction

Extract key data points and text snippets from mapped documents.

```
/D-evidence-extraction
```

**Agent Actions:**
- Parse document content (PDF text, tables, metadata)
- Extract 0-3 evidence snippets per requirement with page citations
- Extract structured data: dates, locations, ownership info, numerical values

**Human Actions:** Review snippets, delete irrelevant ones, add manual notes

**Output:** Evidence database with snippets, citations, and structured data points

### Stage E: Cross-Validation

Verify consistency, completeness, and compliance across all extracted evidence.

```
/E-cross-validation
```

**Validation Checks:**
- **Date Alignment:** Sampling dates within ±120 days of imagery dates
- **Land Tenure:** Owner names consistent across documents (fuzzy matching)
- **Project ID:** Consistent project identifiers across all documents
- **Completeness:** Each requirement has mapped documents with sufficient evidence

**Output:** Validation results with pass/warning/fail flags and coverage statistics

### Stage F: Report Generation

Produce structured, auditable Registry Review Report.

```
/F-report-generation
```

**Output Formats:**
- **Markdown:** Human-readable report with executive summary, per-requirement findings, citations
- **JSON:** Machine-readable for audit trails and downstream systems

**Report Contents:** Project metadata, coverage statistics, requirement findings with evidence snippets, validation results, items requiring human review

### Stage G: Human Review

Expert validation, annotation, and revision handling.

```
/G-human-review
```

**Human Actions:**
- Review flagged items requiring judgment
- Override agent assessments where expert knowledge differs
- Request revisions from proponent if gaps identified
- Make final determination: Approve / Conditional / Reject / On Hold

**Output:** Finalized report with human annotations and approval decision

### Stage H: Completion

Finalize and archive the review.

```
/H-completion
```

**Agent Actions:**
- Lock finalized report
- Generate archive package with audit trail
- Prepare data for on-chain registration (if approved)

**Output:** Locked report, complete audit trail, archived session

### Quick Example

```
/A-initialize Botany Farm 2022-2023, /home/user/projects/botany-farm
/B-document-discovery
/C-requirement-mapping
/D-evidence-extraction
/E-cross-validation
/F-report-generation
```

Each stage auto-selects the most recent session, so you can run them in sequence without specifying session IDs.

## Web Application

The `web_app/` directory contains a React-based review workspace that provides:

- **Three-panel layout:** PDF viewer, checklist, and AI chat side-by-side
- **Click-to-highlight:** Evidence snippets link to exact PDF locations with bounding boxes
- **Drag-and-drop:** Link manual evidence from scratchpad to requirements
- **AI assistance:** Chat panel for questions, automation, and explanations
- **Verification workflow:** DocuSign-style verify/reject for each evidence snippet

See [docs/web_app/README.md](docs/web_app/README.md) for detailed frontend documentation.

### Running Locally

```bash
# Terminal 1: Backend API
python chatgpt_rest_api.py

# Terminal 2: Frontend dev server
cd web_app && npm run dev
```

### Production Deployment

The application is deployed to `registry.regen.gaiaai.xyz` via:
- **Backend:** systemd service (`registry-review-api.service`) running FastAPI on port 8003
- **Frontend:** Built static files served by nginx
- **Proxy:** nginx routes `/api/` to the backend

See server management commands in the deployment section.

## Available Tools

**Session Management:**
- `create_session` - Create new review session
- `load_session` / `list_sessions` / `delete_session` - Session lifecycle
- `start_review` - Quick-start: create session + discover documents
- `list_example_projects` - List available test projects

**File Upload:**
- `create_session_from_uploads` - Create session from uploaded files
- `upload_additional_files` - Add files to existing session
- `start_review_from_uploads` - Full workflow from uploads

**Document Processing:**
- `discover_documents` - Scan and classify project documents
- `add_documents` - Add document sources to session
- `extract_pdf_text` - Extract text from PDFs
- `extract_gis_metadata` - Extract GIS shapefile metadata

**Requirement Mapping:**
- `map_all_requirements` - Semantic mapping to documents
- `confirm_mapping` / `remove_mapping` - Manual mapping adjustments
- `get_mapping_status` - View mapping statistics

**Evidence & Validation:**
- `extract_evidence` - Extract evidence for all requirements
- `map_requirement` - Map and extract for single requirement

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Required for LLM-powered extraction
REGISTRY_REVIEW_ANTHROPIC_API_KEY=sk-ant-api03-...
REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED=true

# Optional
REGISTRY_REVIEW_LLM_MODEL=claude-sonnet-4-5-20250929
REGISTRY_REVIEW_LOG_LEVEL=INFO
```

See `.env.example` for all configuration options including chunking, image processing, cost management, and validation settings.

## Project Structure

```
regen-registry-review-mcp/
├── src/registry_review_mcp/
│   ├── server.py           # MCP entry point
│   ├── config/             # Settings management
│   ├── extractors/         # PDF, LLM extraction, coordinate resolution
│   ├── models/             # Pydantic models (evidence, verification)
│   ├── prompts/            # A-H workflow prompts
│   ├── services/           # Document processing
│   ├── tools/              # MCP tool implementations
│   └── utils/              # State, cache, helpers
├── web_app/                # React frontend
│   ├── src/
│   │   ├── components/     # UI components (workspace/, ui/)
│   │   ├── contexts/       # React contexts (Auth, Workspace)
│   │   ├── hooks/          # Custom hooks (useWorkspace, useVerification)
│   │   ├── pages/          # Route pages (Dashboard, SessionWorkspace)
│   │   └── lib/            # API client, utilities
│   └── dist/               # Production build output
├── chatgpt_rest_api.py     # FastAPI backend (45+ endpoints)
├── data/
│   ├── checklists/         # Methodology requirements (JSON)
│   ├── sessions/           # Active sessions (gitignored)
│   └── cache/              # Cached extractions (gitignored)
├── tests/                  # Test suite
├── docs/
│   ├── web_app/            # Web application documentation
│   └── specs/              # Workflow specifications
└── examples/               # Test data (Botany Farm)
```

## Development

```bash
# Run tests (fast tests only - expensive tests excluded)
uv run pytest

# Format and lint
uv run black src/ tests/
uv run ruff check src/ tests/
```

**Test Markers:**
- `smoke` - Critical path tests (<1s)
- `expensive` - Tests with API costs (excluded by default)
- `marker` - PDF extraction tests (slow, 8GB+ RAM)
- `accuracy` - Ground truth validation tests

See `pytest.ini` for marker configuration.

## Requirements

- Python >= 3.10
- Node.js >= 18 (for web app)
- [uv](https://github.com/astral-sh/uv) package manager
- 4GB RAM minimum (8GB recommended for large PDFs)

## Production Deployment

The application is deployed at **https://registry.regen.gaiaai.xyz/** on server `202.61.196.119`.

### Server Management

```bash
# SSH to server
ssh darren@202.61.196.119

# Check backend status
sudo systemctl status registry-review-api

# View backend logs
journalctl -u registry-review-api -f

# Restart backend
sudo systemctl restart registry-review-api

# Check nginx logs
docker logs nginx --tail 50
```

### Redeploying

```bash
# From local machine
rsync -avz --exclude='.venv' --exclude='node_modules' --exclude='examples' \
  . darren@202.61.196.119:/opt/projects/registry-review/

# On server: rebuild and restart
ssh darren@202.61.196.119
cd /opt/projects/registry-review
uv sync
cd web_app && npm install && npm run build
sudo systemctl restart registry-review-api
```

### Architecture

- **Backend:** FastAPI (`chatgpt_rest_api.py`) running via systemd on port 8003
- **Frontend:** React/Vite static files in `/opt/projects/registry-review/web_app/dist/`
- **Proxy:** nginx (Docker) routes `registry.regen.gaiaai.xyz` to backend and serves frontend
- **SSL:** Let's Encrypt wildcard certificate for `*.regen.gaiaai.xyz`

## License

Copyright 2025 Regen Network Development, Inc.
