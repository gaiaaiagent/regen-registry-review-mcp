# Changelog

All notable changes to the Registry Review MCP Server are documented here.

## [2.1.0] - 2026-04-21

Packaging and distribution fixes so `uvx registry-review-mcp` resolves bundled
resources correctly without hand-patching cache environments.

### Fixed
- **[#2]** Checklists are now bundled inside the installed package at
  `registry_review_mcp/data/checklists/`. Previously `data/checklists/` sat at
  the repository root, so `_get_project_root()` resolved into site-packages
  (never the repository) after a PyPI install and every new uvx archive
  environment required manual population of its `lib/python3.13/data/checklists/`
  directory before `start_review` would succeed.
- Default `checklists_dir` now derives from a new `_get_bundled_data_dir()`
  helper that walks from `config/settings.py` to the package root rather than
  the repository root. Tests updated to use the same helper so they exercise
  the bundled path instead of the legacy repo-root location.
- Explicit `[tool.hatch.build.targets.wheel]` configuration so hatchling ships
  `src/registry_review_mcp` as the wheel's only package and non-Python resources
  under the package tree ride along automatically.

### Verified
- `uv build` produces `registry_review_mcp-2.1.0-py3-none-any.whl` containing
  `registry_review_mcp/data/checklists/soil-carbon-v1.2.2.json`.
- Full fast test suite green (`pytest`: 367 passed, 57 expensive deselected).

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
