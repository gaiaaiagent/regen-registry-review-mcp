# Project Status

Last updated: 2026-02-07 (evening)

## Production State

The Registry Review MCP runs on the GAIA server (`202.61.196.119`) managed by **PM2** (not systemd) on port 8003, proxied through nginx at `https://regen.gaiaai.xyz/api/registry`. A Custom GPT and Darren's web app (`https://regen.gaiaai.xyz/registry-review/`) both consume this REST API. The MCP server is also available for direct Claude Desktop/Code integration via stdio.

**Deployed version:** `6433b13` (Phase 1a-1e + test data, Feb 7). Phase 1f-1g committed locally (`8ac8fe9`) but not yet deployed.

**Production health:** Verified healthy on Feb 7. API responds on port 8003. PM2 shows `registry-review-api` online (PID 2351086), restart count 8744. Dependencies synced — `openpyxl` installed for spreadsheet support.

**Other services on this server:** koi-api, koi-mcp-knowledge, regen-koi-mcp, regen-network-api, regenai-agents, koi-event-bridge. All managed via PM2 under the `shawn` user.

## What Works

The 8-stage workflow (Initialize through Completion) is functional for PDF-based registration reviews. The system processes the Botany Farm test project end-to-end: document discovery, requirement mapping against the soil-carbon-v1.2.2 checklist (23 requirements), evidence extraction with page/section citations, cross-document validation, and report generation in markdown and DOCX formats. The web app provides a professional UI with one-click review, side-by-side PDF viewing, and evidence highlighting.

Specifically verified:
- Per-farm land tenure validation
- Citations with document name, section number, and page reference (task-12)
- Value vs Evidence distinction in output (task-12)
- Supplementary evidence from multiple documents (task-12)
- Evidence text in Comments column beneath confidence scores (task-12)
- Sentence-boundary truncation (task-12)
- Project ID prefixed in document references (task-12)
- Confidence scores always visible in report comments
- Human review flagged only where needed
- Session persistence and recovery
- File upload via signed URLs and path-based ingestion
- Spreadsheet ingestion (.xlsx, .xls, .csv, .tsv)
- Multi-project scope filtering (farm/meta/all)
- Centralized checklist loading via `load_checklist()`
- UK Land Registry document classification ("Official Copy (Register) - LT*.pdf")
- Land cover map classification
- Centralized LLM error handling with actionable guidance
- Dual LLM backend: API (SDK) and CLI (`claude -p` subprocess via Max plan)
- Auto-detecting backend resolution (API key present → API, otherwise → CLI)
- 286 tests passing (fast suite), 57 deselected (expensive)

## What's Broken or Missing

### Blocking for Carbon Egg (registration imminent)

1. ~~**Mapping bug**~~ — Fixed (Feb 7, commit `467695e`).
2. ~~**Spreadsheet ingestion**~~ — Implemented (Feb 7).
3. ~~**Meta-project architecture**~~ — Implemented (Feb 7, scope filtering).
4. ~~**CarbonEg-specific requirements**~~ — Addressed via scope filtering.
5. ~~**API credits exhausted**~~ — Resolved. Claude CLI backend implemented (commit `8ac8fe9`). LLM calls now auto-route through Max plan via `claude -p` when no API key is set. Needs deployment to production (install Claude Code on GAIA, authenticate).

### Blocking for demos and BizDev

6. ~~**Report formatting**~~ — Fixed (Feb 7).
7. **PDF download** — Not implemented (raises `NotImplementedError`). Requires a rendering library (e.g., weasyprint). Deferred — markdown and DOCX downloads work correctly.
8. ~~**Duplicate value field**~~ — Fixed (Feb 7).
9. **Supplementary evidence quality** — Unclear how well the system pulls supplementary evidence beyond primary documentation. Needs testing once LLM backend is restored.

### Needed but not blocking

10. **Google Drive ingestion bot** — Darren built an email-based bot that can be added to Drive folders. Not yet integrated with the review workflow.
11. **Airtable integration** — Carbon Egg maintains land tenure data in spreadsheets, team considering Airtable migration.
12. **Bypass workflow stages** — Ability to skip document discovery and requirement mapping, starting directly at evidence extraction.
13. **Issuance Review Agent** — Scoped by Becca but not implemented. Post-registration priority.
14. **Geospatial processing** — Stub exists. Long-term.

## Recent Changes (Feb 7)

### Committed and deployed

- **Phase 1a-1d** — Mapping bug, spreadsheet ingestion, report formatting, multi-project scope. All deployed as commit `a7c7a5f`.
- **UK Land Registry classification** — 3 new patterns for `land_tenure` (Official Copy, Land Registry, LT title numbers), new `land_cover_map` type with 4 patterns. Greens Lodge went from 26% to 100% classification. Deployed as commit `6433b13`.
- **Test data** — Becca's 415-file archive organized into `examples/test-data/` with clean directory structure. GIS files gitignored (192MB).

### Committed locally (not yet deployed)

- **LLM error handling (1f)** — Centralized `get_anthropic_client()`, `classify_api_error()`, `LLMBillingError`, `LLMAuthenticationError`. Fatal errors propagate with actionable guidance. REST API returns HTTP 402 for billing errors. 8 new tests.
- **Claude CLI backend (1g)** — Unified `call_llm()` entry point with dual backend (API SDK + CLI subprocess). Auto-detects available backend. All three LLM call sites converted. Fixed hardcoded model bug in `unified_analysis.py`. 18 new tests. Commit `8ac8fe9`.

## Key Dates and Context

- Carbon Egg registration: described as "this month" on Feb 3
- ETHDenver/Boulder hackathon: starting around Feb 7 (Shawn, Darren, Eve attending)
- Next team check-in target: Wednesday Feb 11
- BizDev calls potentially starting as early as first week of Feb
- Last code change: Feb 7

## Test Data Available

Becca's test data extracted to `examples/test-data/` with clean directory structure:
- `registration/botany-farm/` — 7 PDFs (project plan, baseline, GHG, monitoring, methodology, reviews)
- `registration/fonthill-farms/` — 5 files (project plans, title plan, yields spreadsheet, land cover)
- `registration/greens-lodge/` — 19 files (3 project plan versions, 13 land registry PDFs, yields spreadsheet, land cover)
- `issuance/kerr/` — Baseline + Monitoring Round 1 (SOC reports, AI network data, sampling, yields)
- `issuance/lowick/` — Baseline + Monitoring Round 1 (same structure as Kerr)
- `issuance/neesham/` — Baseline + Monitoring Round 1 (same structure)
- GIS raster files (.tif, .shp, etc.) present on disk but gitignored (192MB)

## Immediate Next Actions

1. ~~Verify production deployment state~~ — Done (Feb 7)
2. ~~Fix mapping bug~~ — Done (Feb 7, commit `467695e`)
3. ~~Add spreadsheet ingestion~~ — Done (Feb 7)
4. ~~Clean up report formatting~~ — Done (Feb 7, Phase 1c)
5. ~~Multi-project scope support~~ — Done (Feb 7, Phase 1d)
6. ~~Deploy Phase 1 to production~~ — Done (Feb 7, commit `a7c7a5f`)
7. ~~Extract and organize test data~~ — Done (Feb 7)
8. ~~Fix UK Land Registry classification~~ — Done (Feb 7, commit `6433b13`)
9. ~~Centralize LLM error handling~~ — Done (Feb 7, commit `b669d9c`)
10. ~~Implement Claude CLI backend~~ — Done (Feb 7, commit `8ac8fe9`)
11. **Deploy 1f+1g to production** — Install Claude Code on GAIA, authenticate, push + restart
12. Run registration review on Greens Lodge with CLI backend
13. Verify supplementary evidence quality across documents
