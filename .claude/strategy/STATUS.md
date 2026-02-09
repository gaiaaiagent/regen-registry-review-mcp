# Project Status

Last updated: 2026-02-09

## Production State

The Registry Review MCP runs on the GAIA server (`202.61.196.119`) managed by **PM2** (not systemd) on port 8003, proxied through nginx at `https://regen.gaiaai.xyz/api/registry`. A Custom GPT and Darren's web app (`https://regen.gaiaai.xyz/registry-review/`) both consume this REST API. The MCP server is also available for direct Claude Desktop/Code integration via stdio.

**Deployed version:** `2a52f2b` (Phase 1 complete + bug fixes, Feb 9). All phases 1a-1h deployed. CLI backend active, auto-preferring CLI over API.

**Production health:** Verified healthy on Feb 9. Greens Lodge E2E: 19 docs discovered, 4/4 farm reqs covered, 122 evidence snippets, validation returns structured results (no 500), report generated. API responds on port 8003. PM2 shows `registry-review-api` online.

**Important:** The nginx proxy at `regen.gaiaai.xyz/api/registry` routes to port 8200 (Darren's web app), NOT directly to port 8003. Direct API access is via `regen.gaiaai.xyz/registry` (requires auth_basic) or `localhost:8003` on the server.

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
- Auto backend prefers CLI (zero cost), falls back to API
- Cross-validation endpoint returns structured results (Pydantic model tolerates partial coordinator output)
- REST session creation accepts `documents_path` for path-based ingestion without manual setup
- 310 tests passing (fast suite), 57 deselected
- Health endpoint (`GET /health`) for PM2 liveness
- Request ID tracing (`X-Request-ID`, `X-Response-Time-Ms` on every response)
- Request model hardening (`extra="forbid"` on all 13 request models) (expensive)

## What's Broken or Missing

### Blocking for Carbon Egg (registration imminent)

1. ~~**Mapping bug**~~ — Fixed (Feb 7, commit `467695e`).
2. ~~**Spreadsheet ingestion**~~ — Implemented (Feb 7).
3. ~~**Meta-project architecture**~~ — Implemented (Feb 7, scope filtering).
4. ~~**CarbonEg-specific requirements**~~ — Addressed via scope filtering.
5. ~~**API credits exhausted**~~ — Resolved. CLI backend deployed (`a56f16a`). Auto mode prefers CLI (Max plan, zero cost), falls back to API. Claude Code v2.1.37 installed on GAIA.

### Blocking for demos and BizDev

6. ~~**Report formatting**~~ — Fixed (Feb 7).
7. **PDF download** — Not implemented (raises `NotImplementedError`). Requires a rendering library (e.g., weasyprint). Deferred — markdown and DOCX downloads work correctly.
8. ~~**Duplicate value field**~~ — Fixed (Feb 7).
9. ~~**Supplementary evidence quality**~~ — Verified (Feb 9). Greens Lodge REQ-002 pulled evidence from 17 documents with section/page citations.

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

### Also committed and deployed (Feb 7, later)

- **LLM error handling (1f)** — Centralized error classification, fatal errors propagate with actionable guidance. 8 new tests.
- **Claude CLI backend (1g)** — Unified `call_llm()` with dual backend. Auto prefers CLI (Max plan). Fixed hardcoded model bug. 20 new tests. Deployed as `a56f16a`.
- **CLI flag fix** — Removed non-existent `--max-tokens`, added `--tools ""` for pure LLM mode. Verified against claude v2.1.37.

### Deployed (Feb 9, commit `2a52f2b`)

- **Phase 1h polish** — Unified REST error handling (`_llm_error_response()`), auth→401/billing→402. 7 new tests.
- **documents_path passthrough** — `CreateSessionRequest` now accepts and forwards `documents_path` to `create_session()`. Removes need to manually set path after session creation.
- **Cross-validation Pydantic fix** — `LandTenureValidation.fields`, `area_consistent`, and `tenure_type_consistent` now have safe defaults. `/validate` no longer 500s when the coordinator doesn't produce field-level results.
- **310 tests passing** (fast suite), 57 deselected (expensive).

## Key Dates and Context

- Carbon Egg registration: described as "this month" on Feb 3
- ETHDenver/Boulder hackathon: starting around Feb 7 (Shawn, Darren, Eve attending)
- Next team check-in target: Wednesday Feb 11
- BizDev calls potentially starting as early as first week of Feb
- Last code change: Feb 9 (Phase 2 operational foundations)
- PM2 restart mystery: diagnosed Feb 9 — port-bind storm on Jan 14, fix in `ecosystem.config.cjs`

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

Phase 1 complete. Phase 2 code-level work (2a-2d, 2f partial) complete. Remaining Phase 2 items are operational (2e architecture docs, 2f log rotation + uptime monitoring) and deployment (apply `ecosystem.config.cjs` via `pm2 delete && pm2 start ecosystem.config.cjs && pm2 save`).

Next priority is deploying Phase 2 changes to production and coordinating with Darren on request model hardening (verify web app doesn't send extra fields that would now return 422).

After that: Phase 3 (Demo Readiness). Carbon Egg registration is "this month." Team check-in target: Wednesday Feb 11.
