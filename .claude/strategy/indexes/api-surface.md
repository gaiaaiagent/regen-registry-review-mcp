# API Surface Reference

Last updated: 2026-02-07

## REST API (chatgpt_rest_api.py)

Base URL: `https://regen.gaiaai.xyz/api/registry`
Local: `http://localhost:8003`
Docs: `http://localhost:8003/docs` (Swagger UI)

### Session Management

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/sessions` | List all sessions |
| POST | `/sessions` | Create new session |
| GET | `/sessions/{id}` | Get session details |
| DELETE | `/sessions/{id}` | Delete session |
| POST | `/sessions/{id}/upload` | Upload file to session |

### Workflow Stages

| Method | Path | Stage | Description |
|--------|------|-------|-------------|
| POST | `/sessions/{id}/discover` | B | Discover and classify documents |
| GET | `/sessions/{id}/conversion-status` | B | PDF conversion progress |
| POST | `/sessions/{id}/map` | C | Map all requirements |
| GET | `/sessions/{id}/mapping-status` | C | Mapping progress |
| GET | `/sessions/{id}/mapping-matrix` | C | Visual mapping matrix |
| POST | `/sessions/{id}/confirm-all-mappings` | C | Confirm all mappings |
| POST | `/sessions/{id}/evidence` | D | Extract evidence |
| GET | `/sessions/{id}/evidence-matrix` | D | Evidence matrix view |
| POST | `/sessions/{id}/validate` | E | Cross-validate evidence |
| POST | `/sessions/{id}/report` | F | Generate report |
| GET | `/sessions/{id}/report/download` | F | Download markdown report |
| GET | `/sessions/{id}/checklist/download` | F | Download checklist markdown |
| GET | `/sessions/{id}/checklist/download-docx` | F | Download DOCX checklist |

### Human Review (Stage G)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/sessions/{id}/review-status` | Review status |
| POST | `/sessions/{id}/override` | Set requirement override |
| DELETE | `/sessions/{id}/override/{req_id}` | Clear override |
| POST | `/sessions/{id}/annotation` | Add annotation |
| GET | `/sessions/{id}/determination` | Get final determination |
| POST | `/sessions/{id}/determination` | Set final determination |
| DELETE | `/sessions/{id}/determination` | Clear determination |
| GET | `/sessions/{id}/revisions` | Get revision requests |
| POST | `/sessions/{id}/revisions` | Request revision |
| GET | `/sessions/{id}/revisions/summary` | Revision summary |
| POST | `/sessions/{id}/revisions/{req_id}/resolve` | Resolve revision |
| GET | `/sessions/{id}/audit-log` | Audit log |

### File Upload and Examples

| Method | Path | Description |
|--------|------|-------------|
| GET | `/examples` | List example projects |
| POST | `/start-example-review` | Start review from example |
| POST | `/start-review-with-files` | Create session + discover from uploads |
| POST | `/generate-upload-url` | Generate signed URL for upload |
| GET | `/upload/{id}?token={t}` | Download file via signed URL |
| POST | `/upload/{id}?token={t}` | Upload file via signed URL |
| POST | `/process-upload/{id}` | Process uploaded files |
| GET | `/upload-status/{id}` | Check upload status |

## MCP Server Tools

The MCP server (`server.py`) exposes the same capabilities as async tools for direct Claude integration. The 8 workflow prompts are:

| Prompt | Name | Purpose |
|--------|------|---------|
| A | `/A-initialize` | Create session, load checklist |
| B | `/B-document-discovery` | Scan and classify documents |
| C | `/C-requirement-mapping` | Semantic matching to requirements |
| D | `/D-evidence-extraction` | Extract snippets with citations |
| E | `/E-cross-validation` | Date/tenure/project ID validation |
| F | `/F-report-generation` | Generate markdown + JSON reports |
| G | `/G-human-review` | Human expert review and override |
| H | `/H-completion` | Finalize and archive |

Individual tools are registered from each tool module (session_tools, document_tools, mapping_tools, evidence_tools, validation_tools, report_tools, human_review_tools, upload_tools). The MCP server uses stdio transport. See `.mcp.json` for Claude Code configuration.
