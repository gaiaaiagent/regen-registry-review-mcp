# Changelog

All notable changes to the Registry Review MCP Server are documented here.

## [2.0.0] - 2025-11-26

Eight-stage workflow implementation for automated carbon credit project registration reviews.

### Added
- **Eight-stage workflow** (A-H prompts) for guided review process
- **Session management** - Create, load, list, delete review sessions
- **Document discovery** - Recursive scanning with intelligent classification
- **Requirement mapping** - Semantic matching to 23 checklist requirements
- **Evidence extraction** - Text snippets with page citations
- **Cross-validation** - Date alignment, land tenure, project ID consistency
- **Report generation** - Markdown and JSON output formats
- **File upload tools** - Base64 and path-based upload support
- **LLM-powered extraction** - Optional Anthropic API integration for field extraction
- **PDF text extraction** - PyMuPDF fast extraction with marker fallback
- **GIS metadata extraction** - Shapefile and GeoJSON support

### Configuration
- Environment-based settings via `.env`
- Configurable LLM model, chunking, and cost management
- Test markers for expensive/integration/accuracy tests

## [0.1.0] - 2025-11-12

Initial prototype with foundation infrastructure.

### Added
- MCP server scaffolding with FastMCP
- Basic session state management
- Soil Carbon v1.2.2 checklist (23 requirements)
- Error handling infrastructure
