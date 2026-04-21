# Changelog

All notable changes to the Registry Review MCP Server are documented here.

## [2.2.0] - 2026-04-21

OCR fallback is now **enabled by default**. Image-heavy registry PDFs
(Ecometric Soil Carbon monitoring reports, InDesign-derived submissions,
scan-based inputs) recover text automatically when Tesseract is installed on
the host; text-native PDFs continue on the fast path with zero new work.

### Changed
- **OCR fallback default flipped from `False` to `True`.** Set
  `REGISTRY_REVIEW_OCR_ENABLED=false` to opt out. Hosts without Tesseract
  degrade gracefully — the `is_tesseract_available()` probe returns `False`,
  a one-time warning is logged, and the fast extractor continues on the
  native PyMuPDF4LLM output unchanged.

### Added
- **Benchmark fixtures** — `tests/fixtures/README.md` and
  `tests/fixtures/fixtures.toml` declare the env-var contract
  (`RRM_FIXTURE_BURTON_LATIMER`, `RRM_FIXTURE_BOTANY_FARM`), per-OS Tesseract
  install recipes, and the v2.2.0 Burton Latimer baseline (90.9%
  sparse-page rescue, +11.3% character recovery across 36 PDFs).
- **Default-flip regression test** — `tests/test_ocr_fallback.py` asserts
  `Settings().ocr_enabled is True` so any future accidental revert surfaces
  in CI.

### Notes
- Install Tesseract: `pacman -S tesseract tesseract-data-eng` (Arch /
  CachyOS), `apt install tesseract-ocr tesseract-ocr-eng` (Debian /
  Ubuntu), `dnf install tesseract tesseract-langpack-eng` (Fedora), or
  `brew install tesseract` (macOS).
- Multi-language OCR (e.g. CSSCP Czech-Slovak submissions): install the
  extra language pack and set `REGISTRY_REVIEW_OCR_LANGUAGE=eng+ces`.

## [Unreleased] — feat/ocr-fallback (Issue #4)

OCR fallback pipeline prototype for image-heavy registry documents. Opt-in
via `REGISTRY_REVIEW_OCR_ENABLED=true`; disabled by default so existing
deployments are unaffected.

### Added
- **`extractors/ocr.py`** — new module with `is_tesseract_available()`
  (memoized probe via PyMuPDF's `get_tessdata`, graceful degradation when
  Tesseract is missing), `ocr_page()` (per-page OCR with auto / blocks /
  full modes), `page_needs_ocr()` (density-plus-image-blocks heuristic),
  and a deterministic cache keyed on `(filepath, mtime, page, mode,
  language, dpi)`.
- **`fast_extract_pdf` integration** — after the PyMuPDF4LLM pass, any
  page whose extracted text drops below the density threshold AND whose
  underlying PDF page contains at least one image block is OCRed, with
  recovered text spliced into the chunk under an
  `<!-- OCR-recovered page N -->` marker so downstream consumers can
  distinguish native from recovered content. The extractor return value
  now includes an `ocr` sub-dictionary (`mode`, `pages_recovered`,
  `language`, `dpi`) regardless of whether OCR ran, giving callers a
  stable schema to inspect.
- **Settings** — `ocr_enabled`, `ocr_density_threshold`, `ocr_language`,
  `ocr_dpi`, all with conservative defaults (`False`, 50 chars, `eng`,
  150dpi).
- **`tests/test_ocr_fallback.py`** — 18 tests covering probe memoization,
  graceful degradation when Tesseract is absent, one-time warning
  behavior, the density-plus-images heuristic, cache-key determinism and
  mtime invalidation, and the stable `ocr` schema on the fast extractor
  result.
- **Install helper** — `~/.claude/local/scripts/install-tesseract-for-ra-agent.sh`
  for operators on Arch / CachyOS, with Debian / Fedora / macOS hints in
  the script header.

### Not yet
- No accuracy / benchmark test against the Rockscape fixture — Tesseract
  is not installed on the development machine yet, so the next step is
  running the helper script and executing a marked-expensive fixture
  suite.
- No automatic enablement. Once the fixture run confirms precision and
  recall are acceptable, flip the default to `True` and add a
  configuration note.

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
