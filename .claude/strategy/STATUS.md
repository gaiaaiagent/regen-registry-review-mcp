# Project Status

Last updated: 2026-02-10

## Production State

The Registry Review MCP runs on the GAIA server (`202.61.196.119`) managed by **PM2** (not systemd) on port 8003, proxied through nginx at `https://regen.gaiaai.xyz/api/registry`. A Custom GPT and Darren's web app (`https://regen.gaiaai.xyz/registry-review/`) both consume this REST API. The MCP server is also available for direct Claude Desktop/Code integration via stdio.

**Deployed version:** `944155d` (Phase 1-3 complete, Feb 10). All phases deployed and E2E verified on 3 projects. 347 tests pass locally.

**Production health:** Verified healthy on Feb 10. PM2 stable: 0 unstable restarts. CLI backend active (zero API cost). Health endpoint responds with version, session count, last_request_at.

**Important:** The nginx proxy at `regen.gaiaai.xyz/api/registry` routes to port 8200 (Darren's web app), NOT directly to port 8003. Direct API access is via `regen.gaiaai.xyz/registry` (requires auth_basic) or `localhost:8003` on the server.

**Other services on this server:** koi-api, koi-mcp-knowledge, regen-koi-mcp, regen-network-api, regenai-agents, koi-event-bridge. All managed via PM2 under the `shawn` user.

## E2E Test Results (Feb 10)

All 3 test projects run end-to-end on production (real LLM calls via CLI backend):

| Project | Files | Covered | Coverage | Snippets | Validation | Report |
|---|---|---|---|---|---|---|
| Botany Farm | 7 PDFs | 23/23 | 100% | 125 | 14/16 passed (87%) | 12.7KB md, 8.3KB pdf |
| Fonthill Farms | 5 files | 22/23 | 96% | 202 | 20/23 passed (87%) | 13.4KB md, 8.6KB pdf |
| Greens Lodge | 19 files | 22/23 | 96% | 371 | 20/23 passed (87%) | 14.4KB md, 9.1KB pdf |

Key observations:
- Greens Lodge REQ-002 (land tenure) pulled 68 snippets from 17 documents — excellent cross-document evidence
- Greens Lodge REQ-017 (monitoring plan) correctly flagged as missing — expected for registration-only projects
- Fonthill's 23MB title plan PDF extracted successfully with 2GB memory limit
- All reports generate clean markdown and PDF with section/page citations

## What Works

The full workflow (Initialize through Report) is production-verified for PDF-based registration reviews across 3 projects with varying complexity (7-19 files, single-farm to multi-document).

Specifically verified:
- Per-farm land tenure validation
- Citations with document name, section number, and page reference
- Supplementary evidence from multiple documents (68 snippets across 17 docs)
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
- Triple LLM backend: CLI → API → OpenAI (auto-resolved, cheapest first)
- Cross-validation with three-layer architecture (structural + cross-doc + LLM synthesis)
- REST session creation accepts `documents_path` for path-based ingestion
- PDF report generation via fpdf2 (professional layout, multi-page, automatic wrapping)
- SessionNotFoundError returns 404 (not 500) across all REST endpoints
- 347 tests passing (fast suite), 57 deselected
- Health endpoint (`GET /health`) with `last_request_at` for staleness detection
- Request ID tracing (`X-Request-ID`, `X-Response-Time-Ms` on every response)
- Request model hardening (`extra="forbid"` on all 13 request models)
- pm2-logrotate configured (50MB max, 14-day retention, compressed, daily rotation)
- Cron health check every 5 minutes
- Architecture documented in `docs/architecture.md`

## What's Broken or Missing

### All blocking items resolved

1-9. All previously blocking items (mapping bug, spreadsheet ingestion, report formatting, CLI backend, PDF download, etc.) are fixed and deployed.

### Needed but not blocking

10. **Google Drive ingestion bot** — Darren built an email-based bot that can be added to Drive folders. Not yet integrated with the review workflow.
11. **Airtable integration** — Carbon Egg maintains land tenure data in spreadsheets, team considering Airtable migration.
12. **Bypass workflow stages** — Ability to skip document discovery and requirement mapping, starting directly at evidence extraction.
13. **Issuance Review Agent** — Scoped by Becca but not implemented. Post-registration priority.
14. **Geospatial processing** — Stub exists. Long-term.
15. **Large PDF memory handling** — 23MB image-heavy PDFs (title plans) spike memory to ~1.5GB during PyMuPDF extraction. Current fix: 2GB memory limit. Proper fix: size-based extraction strategy or streaming.
16. **LLM call deduplication** — Validation synthesis has no application-level cache (evidence extraction does). Low priority given the single LLM call per session.

## Recent Changes (Feb 10)

### Deployed (commit `944155d`)

- **CLI flag fix** — Claude Code v2.0.1 removed `--tools` and `--no-session-persistence` flags. Every CLI LLM call was failing. Removed obsolete flags.
- **PM2 memory limit** — Increased from 1GB to 2GB for large PDF extraction (23MB Fonthill title plan).
- **Validation model defaults** — `DateAlignmentValidation`, `ProjectIDValidation`, `ContradictionCheck` now tolerate partial cross-document results (same pattern as earlier `LandTenureValidation` fix).

### Previously deployed (commits `69f68b3` through `a5a756b`)

- **OpenAI fallback backend** — Auto-detected, transparent retry when Anthropic unavailable.
- **PDF export via fpdf2** — Professional layout, multi-page, automatic wrapping.
- **Integration tests** — 21 new tests covering session lifecycle, discovery, error paths, human review, reports.
- **404 error fix** — `SessionNotFoundError` inherits `FileNotFoundError` for clean 404 handling.
- **Phase 2 operational foundations** — Health endpoint, model hardening, request tracing, PM2 fix, architecture docs.

## Key Dates and Context

- Carbon Egg registration: described as "this month" on Feb 3
- ETHDenver/Boulder hackathon: starting around Feb 7 (Shawn, Darren, Eve attending)
- **Demo ready:** Feb 10 — all 3 E2E projects verified on production
- Next team check-in target: Wednesday Feb 11
- BizDev calls potentially starting as early as first week of Feb
- Claude Code CLI on GAIA: v2.0.1 (rebranded from claude v2.1.37)

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

All phases through 3e complete. System is demo-ready.

Next priorities:
1. **Wednesday check-in** (Feb 11) — Present E2E results, discuss Carbon Egg timeline
2. **Coordinate with Darren** — Verify web app doesn't send extra fields (request model hardening → 422)
3. **Issuance review agent** — Becca's next priority after registration reviews are solid
4. **Architecture redesign** — Four-layer concurrent model (see `.claude/strategy/architecture/first-principles-redesign.md`)
