# Regen Registry Review MCP Server

Automated carbon credit project registration review through an eight-stage workflow.

## Workflow Prompts

| Stage | Prompt | Description |
|-------|--------|-------------|
| A | `A-initialize` | Create session with project name and documents path |
| B | `B-document-discovery` | Discover and classify all project documents |
| C | `C-requirement-mapping` | Map documents to checklist requirements |
| D | `D-evidence-extraction` | Extract evidence snippets with citations |
| E | `E-cross-validation` | Validate consistency across documents |
| F | `F-report-generation` | Generate review reports (Markdown + JSON) |
| G | `G-human-review` | Review flagged items for human judgment |
| H | `H-completion` | Finalize and archive the review |

**Utility Prompts:**
- `list_capabilities` - Show this capabilities list
- `list-sessions` - List all active review sessions
- `list-projects` - List example projects for testing

## Tools

### Session Management

| Tool | Description |
|------|-------------|
| `create_session` | Create new review session with project metadata |
| `load_session` | Load existing session by ID |
| `list_sessions` | List all review sessions |
| `delete_session` | Delete session and all data |
| `start_review` | Quick-start: create session + discover documents |
| `list_example_projects` | List available test projects |
| `add_documents` | Add document sources to existing session |
| `update_session_state` | Update session status and workflow progress |

### File Upload

| Tool | Description |
|------|-------------|
| `create_session_from_uploads` | Create session from uploaded files (base64 or path) |
| `upload_additional_files` | Add files to existing session |
| `start_review_from_uploads` | Full workflow: upload, discover, extract |

### Document Processing

| Tool | Description |
|------|-------------|
| `discover_documents` | Scan and classify project documents |
| `extract_pdf_text` | Extract text content from PDF files |
| `extract_gis_metadata` | Extract metadata from shapefiles/GeoJSON |

### Requirement Mapping

| Tool | Description |
|------|-------------|
| `map_all_requirements` | Semantic mapping of all requirements to documents |
| `confirm_mapping` | Confirm or set document mappings for a requirement |
| `remove_mapping` | Remove a document from a requirement mapping |
| `get_mapping_status` | Get mapping status and statistics |

### Evidence Extraction

| Tool | Description |
|------|-------------|
| `extract_evidence` | Extract evidence for all requirements |
| `map_requirement` | Map single requirement and extract evidence |

## Supported Methodologies

- **Soil Carbon v1.2.2** - Soil Organic Carbon Estimation in Regenerative Cropping and Managed Grassland Ecosystems (23 requirements)

## Configuration

The server reads configuration from environment variables. See `.env.example` for all options:

- `REGISTRY_REVIEW_ANTHROPIC_API_KEY` - Required for LLM extraction
- `REGISTRY_REVIEW_LLM_EXTRACTION_ENABLED` - Enable/disable LLM features
- `REGISTRY_REVIEW_LOG_LEVEL` - Logging verbosity (INFO, DEBUG, etc.)
