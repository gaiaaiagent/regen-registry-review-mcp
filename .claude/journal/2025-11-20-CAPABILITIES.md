# Regen Registry Review MCP Server

**Version:** 2.0.0
**Purpose:** Automate carbon credit project registry review workflows

## Capabilities

### Tools Available

**Session Management:**
- `start_review` - Quick-start: Create session and discover documents in one step
- `create_session` - Create new review session
- `load_session` - Load existing session
- `update_session_state` - Update session progress
- `list_sessions` - List all sessions
- `delete_session` - Delete a session

**Document Processing (Phase 2):**
- `discover_documents` - Scan and classify project documents
- `extract_pdf_text` - Extract text from PDF files
- `extract_gis_metadata` - Extract GIS shapefile metadata

**Requirement Mapping (Phase 3):**
- `map_all_requirements` - Map all requirements to documents using semantic matching
- `confirm_mapping` - Confirm or manually set document mappings for a requirement
- `remove_mapping` - Remove a document from a requirement mapping
- `get_mapping_status` - Get current mapping status and statistics

**Evidence Extraction (Phase 4):**
- `extract_evidence` - Extract evidence from mapped documents (requires Stage 3 complete)
- `map_requirement` - Map a single requirement to documents with evidence snippets

**Validation & Reporting (Phase 5):**
- `cross_validation` - Validate dates, land tenure, and project IDs across documents
- `generate_report` - Create comprehensive Markdown and JSON reports

### Workflows (8 Sequential Stages)

1. **Initialize** (`/A-initialize`) - Create session and load checklist
2. **Document Discovery** (`/B-document-discovery`) - Scan and classify all documents
3. **Requirement Mapping** (`/C-requirement-mapping`) - Map documents to checklist requirements
4. **Evidence Extraction** (`/D-evidence-extraction`) - Extract evidence from mapped documents
5. **Cross-Validation** (`/E-cross-validation`) - Verify consistency across documents
6. **Report Generation** (`/F-report-generation`) - Generate structured review report
7. **Human Review** (`/G-human-review`) - Present flagged items for decision
8. **Completion** (`/H-completion`) - Finalize and export report

### Supported Methodology

- Soil Carbon v1.2.2 (GHG Benefits in Managed Crop and Grassland Systems)
- Additional methodologies: Coming in Phase 3+

### File Types Supported

- PDF documents (text and tables)
- GIS shapefiles (.shp, .shx, .dbf, .geojson)
- Imagery files (.tif, .tiff) - metadata only

## Getting Started

**Quick Start (Recommended):**
```
start_review(
    project_name="Botany Farm",
    documents_path="/absolute/path/to/documents",
    methodology="soil-carbon-v1.2.2"
)
```
This creates a session and discovers all documents in one step.

**Or use the prompts directly:**
```
/B-document-discovery
/C-requirement-mapping
/D-evidence-extraction
```
These will auto-select your most recent session, or guide you to create one if none exists.

**Manual workflow:**
1. Create a session with `create_session`
2. Discover documents with `discover_documents` or `/B-document-discovery` prompt
3. Map requirements with `map_all_requirements` or `/C-requirement-mapping` prompt
4. Extract evidence with `extract_evidence` or `/D-evidence-extraction` prompt

## Status

- **Phase 1 (Foundation):** ✅ Complete (Session management, infrastructure)
- **Phase 2 (Document Processing):** ✅ Complete (Document discovery, classification, PDF/GIS extraction)
- **Phase 3 (Requirement Mapping):** ✅ Complete (Semantic document-to-requirement mapping, human confirmation)
- **Phase 4 (Evidence Extraction):** ✅ Complete (Extract evidence from mapped documents, coverage analysis)
- **Phase 5 (Validation & Reporting):** ✅ Complete (Cross-validation, report generation, LLM-native extraction)
- **Phase 6 (Integration & Polish):** 🚧 In Progress (All 8 prompts complete, testing in progress)

**Test Coverage:** 120/120 tests passing (100%)
**LLM Extraction:** 80%+ recall with caching and cost tracking
