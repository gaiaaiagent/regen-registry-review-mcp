# Codebase Map

Last updated: 2026-02-07

## Repository

- **Location:** `/home/ygg/Workspace/regenai/regenai-forum-content/resources/regen-registry-review-mcp`
- **Remote:** `git@github.com:gaiaaiagent/regen-registry-review-mcp.git`
- **Branch:** `main`
- **Python:** 3.13 (via UV)
- **Version:** 2.0.0 (pyproject.toml)
- **Production code:** ~15,600 lines across 55 Python files in `src/`
- **Test code:** ~3,000 lines across 30 test files

## Source Structure

```
src/registry_review_mcp/
  server.py                      MCP server entry point (FastMCP). Registers all tools and prompts.
  config/settings.py             Pydantic Settings. All config via REGISTRY_REVIEW_* env vars.
```

### Models (data structures)

```
  models/
    base.py                      BaseModel extensions
    schemas.py                   Core data schemas (sessions, documents, requirements)
    evidence.py                  Evidence extraction models
    report.py                    Report generation models
    validation.py                Validation result models
    responses.py                 MCP tool response schemas
    errors.py                    Custom error types
```

### Prompts (8-stage workflow instructions)

Each file contains the system prompt that guides the LLM through that workflow stage.

```
  prompts/
    A_initialize.py              Stage 1: Create session, load checklist
    B_document_discovery.py      Stage 2: Scan and classify documents
    C_requirement_mapping.py     Stage 3: Semantic matching to requirements
    D_evidence_extraction.py     Stage 4: Extract snippets with citations
    E_cross_validation.py        Stage 5: Date/tenure/project ID consistency
    F_report_generation.py       Stage 6: Generate markdown + JSON reports
    G_human_review.py            Stage 7: Human expert review and override
    H_completion.py              Stage 8: Finalize and archive
    unified_analysis.py          Unified extraction schema for LLM calls
    helpers.py                   Prompt formatting utilities
```

### Tools (MCP tool implementations)

Each tool module exposes async functions that become MCP tools or REST API endpoints.

```
  tools/
    base.py                      Tool base classes and shared logic
    session_tools.py             Session lifecycle: create, load, list, delete
    document_tools.py            Document discovery, classification, extraction
    mapping_tools.py             Requirement mapping with semantic matching
    evidence_tools.py            Evidence extraction orchestration
    validation_tools.py          Cross-document validation coordinator
    report_tools.py              Report generation (markdown, JSON, DOCX)
    upload_tools.py              File upload handling (base64 + signed URLs)
    human_review_tools.py        Override assessments, annotations, determinations
    analyze_llm.py               LLM call analysis and debugging
```

### Services (business logic)

```
  services/
    document_processor.py        Document scanning, classification, PDF conversion
    background_jobs.py           Async job orchestration for long-running tasks
```

### Extractors (PDF and data extraction)

```
  extractors/
    fast_extractor.py            PyMuPDF fast text extraction (default)
    marker_extractor.py          Marker PDF extraction (high-quality fallback, 8GB+ RAM)
    llm_extractors.py            LLM-powered field extraction (dates, land tenure, project IDs)
    verification.py              Extraction quality verification
```

### Validation (cross-document checks)

```
  validation/
    structural.py                Format and structure validation
    cross_document.py            Multi-document consistency checks
    llm_synthesis.py             LLM-based synthesis validation
    coordinator.py               Validation orchestration
```

### Utilities

```
  utils/
    state.py                     StateManager: atomic JSON read/write with file locking
    cache.py                     Extraction and LLM response caching with compression
    cost_tracker.py              API cost tracking per session
    patterns.py                  Regex patterns for document classification
    tool_helpers.py              Error handling decorators for tool functions
    safe_delete.py               Protected file deletion with audit trail
```

## REST API Wrapper

`chatgpt_rest_api.py` (1,607 lines) — FastAPI server that wraps MCP tools as REST endpoints. Runs on port 8003. Serves the Custom GPT and web app. See `indexes/api-surface.md` for endpoint reference.

## Test Structure

```
tests/
  conftest.py                    Pytest config, environment isolation, fixtures
  factories.py                   Test data factories
  botany_farm_ground_truth.json  Reference data for accuracy tests
  plugins/cost_control.py        Cost limiting plugin for expensive tests
  test_smoke.py                  Critical path validation
  test_infrastructure.py         Server initialization
  test_initialize_workflow.py    Stage 1 tests
  test_document_processing.py    Stage 2 tests
  test_evidence_extraction.py    Stage 4 tests
  test_validation.py             Stage 5 tests
  test_report_generation.py      Stage 6 tests
  test_integration_full_workflow.py  End-to-end 8-stage test
  test_botany_farm_accuracy.py   Ground truth accuracy (marked: accuracy)
  test_llm_extraction.py         LLM field extraction (marked: expensive)
  ...and 17 more test files
```

## Data

```
data/
  checklists/
    soil-carbon-v1.2.2.json      23 requirements for Soil Organic Carbon methodology
  sessions/                      Runtime session data (gitignored)
  cache/                         PDF extraction cache (gitignored)
```

## Key Files at Root

```
chatgpt_rest_api.py              REST API server (FastAPI + Uvicorn)
install-systemd-service.sh       Production service installer
pyproject.toml                   Dependencies and project metadata
pytest.ini                       Test configuration (expensive tests excluded by default)
.env                             Environment variables (gitignored content, checked-in template)
.mcp.json                        MCP server configs for Claude Code
verify_workflow.py               Phase 1.1 workflow verification script
```
