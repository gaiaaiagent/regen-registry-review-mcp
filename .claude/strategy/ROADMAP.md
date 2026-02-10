# Development Roadmap

Last updated: 2026-02-09

This roadmap sequences work into phases based on urgency and dependency. Each phase has clear acceptance criteria. Phases may overlap where work is independent.

## Phase 0: Orientation and Production Verification — DONE

**Goal:** Establish ground truth about what's deployed and working.

- [x] SSH to production server, verify running version against `main`
- [x] Confirm whether task-12 (Jan 26) changes are deployed — YES, `0513c8b` is live
- [x] Run health check: hit `/sessions` endpoint, verify response — 7 active sessions, API healthy
- [x] Check service status and recent logs — PM2 (not systemd), online 11 days, last restart Jan 27
- [x] Document any drift between dev and production in `runbooks/deploy.md` — Updated for PM2
- [x] Run fast test suite locally: 241 passed, 56 deselected, 12.84s. 23 Pydantic deprecation warnings (json_encoders).

**Acceptance:** Complete. STATUS.md updated, runbooks corrected for PM2, test suite green. Phase 0 done on 2026-02-07.

## Phase 1: Carbon Egg Registration Readiness — DONE

**Goal:** The system can process Carbon Egg's registration documents end-to-end without errors and produce a clean, professional report.

### 1a. Fix Mapping Bug — DONE (Feb 7)

- [x] Reproduce Becca's mapping error with available test data
- [x] Diagnose: naming convention split — classifier uses underscores (`land_tenure`), mapper used hyphens (`land-tenure`)
- [x] Fix: normalized all mapper labels to underscores (commit `467695e`)
- [x] Added 5 regression tests in `TestMappingConventionConsistency`
- [x] Verify with Botany Farm test project — all tests pass

Sources: review-agent-readiness.md item 2.1, Becca's Slack screenshots

### 1b. Spreadsheet Ingestion — DONE (Feb 7)

- [x] Add `openpyxl>=3.1.0` dependency
- [x] Add `SPREADSHEET_EXTENSIONS` and `is_spreadsheet_file()` to `utils/patterns.py`
- [x] Create `extractors/spreadsheet_extractor.py` (.xlsx/.xls/.csv/.tsv to markdown tables)
- [x] Integrate with document discovery (Stage B) — spreadsheet extensions in `supported_extensions`
- [x] Classification: filename patterns take priority, generic `spreadsheet_data` as fallback
- [x] Integrate into `document_processor.py` fast extraction path (spreadsheets skip HQ dual-track)
- [x] Add `spreadsheet_data` to relevant mapping categories (land tenure, monitoring, emissions, project details)
- [x] 7 new tests: discovery, xlsx extraction, csv extraction, classification (domain + generic), mapper coverage, pattern helper

Sources: Jan 20 standup, Jan 27 standup, data-types-for-registry-protocols.md

### 1c. Report Output Quality — DONE (Feb 7)

- [x] Remove duplicate "Value:" label from Submitted Material column (markdown and DOCX)
- [x] Remove emojis from generated report content (summary stats, section headers, requirement headings, validation summaries)
- [x] Replace emoji status indicators with text labels (PASS/WARNING/FAIL, [Review] flag)
- [x] Remove dead code (`_get_docx_submitted_material`, `_get_docx_comments`) that still had old patterns
- [x] 5 new tests: no-emojis-in-report, no-value-label, section-headers, validation-flagged, checklist-row-approved
- [x] Full test suite: 246 passed, 56 deselected
- [x] PDF download — implemented in Phase 3a (fpdf2, `format_pdf_report`, REST download endpoint).
- [ ] Verify tables render cleanly in web app export — needs manual check after deployment

Sources: review-agent-readiness.md items 2.3 and 3.1-3.2, Feb 3 standup

### 1d. Multi-Project Support + Dead Code Cleanup — DONE (Feb 7)

- [x] Document the farm vs. meta-project distinction as auxiliary knowledge (`data/knowledge/carbon-egg-multi-project.md`)
- [x] Add `scope` field to checklist JSON: "farm" for REQ-002/003/004/009, "meta" for the other 19
- [x] Create centralized `load_checklist(methodology, scope)` utility (`utils/checklist.py`)
- [x] Wire `scope` through session creation (schemas, session_tools, server.py MCP tool, REST API)
- [x] Replace all 5 manual `json.load` checklist patterns with `load_checklist()`
- [x] Fix hardcoded methodology bug in `evidence_tools.py` and `analyze_llm.py`
- [x] Remove `use_llm_native_extraction` feature flag (always True, dead conditional)
- [x] Clean unused imports/params in `report_tools.py` and `E_cross_validation.py`
- [x] Mark `llm_extractors.py` and `validation_tools.py` deprecated (retain for test deps)
- [x] 11 new tests: scope filtering (5), session creation with scope (4), requirement coverage (2)
- [x] Full test suite: 257 passed, 56 deselected

Sources: review-agent-readiness.md item 2.2, Feb 3 standup (Darren's recommendation)

### 1e. Classification Fixes — DONE (Feb 7)

Discovered during first real test run against Greens Lodge (19 files):
- [x] Add UK Land Registry patterns to `LAND_TENURE_PATTERNS` ("Official Copy (Register)", "Land Registry", LT title numbers)
- [x] Create `LAND_COVER_PATTERNS` for geographic/boundary documents
- [x] Add classification check for `land_cover_map` in `document_tools.py`
- [x] Add `land_cover_map` and `spreadsheet_data` to ecosystem type mapping
- [x] 4 new tests for classification and mapping coverage
- [x] Greens Lodge classification: 5/19 (26%) to 19/19 (100%)

### 1f. LLM Error Handling — DONE (Feb 7)

Discovered when evidence extraction hit $0 API credit balance:
- [x] Create `utils/llm_client.py` — centralized `get_anthropic_client()`, `classify_api_error()`
- [x] `LLMBillingError` and `LLMAuthenticationError` custom exceptions
- [x] Fatal errors (billing, auth) propagate immediately instead of being silently swallowed
- [x] Actionable guidance in error messages (console URLs, explanations)
- [x] REST API returns HTTP 402 for billing/auth errors
- [x] Mark `test_full_report_workflow` as `@pytest.mark.expensive` (was previously false-passing)
- [x] 8 new tests for error classification and key validation

### 1g. Claude CLI Backend — DONE (Feb 7, commit `8ac8fe9`)

**Goal:** Route LLM calls through Max plan via `claude -p` subprocess, eliminating the need for API credits.

- [x] Add `call_llm()` to `utils/llm_client.py` with auto-detecting dual backend (API + CLI)
- [x] Add `_call_via_api()` wrapping AsyncAnthropic with prompt caching
- [x] Add `_call_via_cli()` using `asyncio.create_subprocess_exec` with `claude -p`
- [x] Add `_resolve_backend()` with auto/api/cli logic and `_check_cli_available()` with caching
- [x] Add `classify_cli_error()` mapping CLI failures to same `APIErrorInfo` categories
- [x] Add `llm_backend` setting (auto/api/cli) to `config/settings.py`
- [x] Convert `llm_synthesis.py` — removed pre-flight client check, uses `call_llm()`
- [x] Convert `evidence_tools.py` — removed `client` param threading, simplified `save_to_cache()`
- [x] Convert `unified_analysis.py` — removed `anthropic_client` param, fixed hardcoded model bug
- [x] Convert `analyze_llm.py` — removed client creation and threading
- [x] 18 new tests for backend selection, CLI flag construction, error classification
- [x] Full test suite: 288 passed, 57 deselected
- [x] Install Claude Code v2.1.37 on GAIA production server (native install)
- [x] Deploy and configure: auto backend prefers CLI, falls back to API
- [x] Fix CLI flags: removed `--max-tokens`, added `--tools ""` for pure LLM mode
- [x] End-to-end verification: Greens Lodge review via CLI backend (Feb 9). 19/19 docs, 4/4 reqs covered, 122 evidence snippets, report generated. Cross-validation has pre-existing Pydantic model bug (not blocking).

### 1h. Polish for Acceptance — DONE (Feb 9)

- [x] Unified REST API error handling: `_llm_error_response()` helper applied to `/evidence`, `/validate`, `/report`
- [x] Auth errors return 401, billing errors return 402 (was returning 402 for both)
- [x] 4 new `call_llm()` happy-path tests (routing, default model, log-once)
- [x] 3 new REST API error response tests (auth→401, billing→402)
- [x] Full test suite: 295 passed, 57 deselected

**Overall Phase 1 Acceptance:** Carbon Egg's test documents process cleanly. Report is professional. No mapping errors. Spreadsheets are handled. LLM pipeline runs without API credit costs. Becca can run a review and get a result she'd show to a partner.

**Progress:** Phase 1 complete. All sub-phases (1a-1h) deployed. End-to-end Greens Lodge review verified via CLI backend on production (Feb 9).

## Phase 2: Operational Foundations

**Goal:** The system is trustworthy enough that failures are caught before users see them, deployments are predictable, and the next person who touches this codebase doesn't have to reverse-engineer the infrastructure.

**Why this comes before demos:** Phase 1 deployment revealed that a demo could fail for purely operational reasons — wrong nginx route, missing access logs, silent field-dropping in request models. A demo that fails because of infrastructure is worse than no demo at all. This phase ensures the floor is solid before we invite people to stand on it.

### 2a. Diagnose PM2 Instability — DONE (Feb 9)

- [x] Decompress and analyze rotated PM2 logs — found root cause in `pm2-error.log.3.gz` (95K, Jan 15)
- [x] Check system journal for OOM kills — none found
- [x] Check PM2 config — `max_memory_restart: 1GB`, `restart_delay: 5000`, no backoff, no `kill_timeout`
- [x] Document findings in `runbooks/deploy.md`
- [x] Create `ecosystem.config.cjs` with `kill_timeout`, `listen_timeout`, `exp_backoff_restart_delay`

**Root cause:** 8,703 of 8,749 restarts came from a single port-bind storm on Jan 14. The process crashed at 05:21 UTC, but port 8003 wasn't released before PM2 restarted it. Each restart failed with `[Errno 98] address already in use` and PM2 retried every ~6.5 seconds for 16 hours until the port freed at 22:01 UTC. The remaining ~46 restarts are accumulated manual deploys. No OOM kills, no memory leak. Current memory usage is ~340MB against a 1GB ceiling.

**Fix:** `ecosystem.config.cjs` adds `kill_timeout: 10000` (10s for socket release), `listen_timeout: 15000` (wait for bind), and `exp_backoff_restart_delay: 100` (exponential backoff caps at ~15min). Needs to be applied on next deploy via `pm2 delete && pm2 start ecosystem.config.cjs && pm2 save`.

### 2b. Health Check — DONE (Feb 9)

- [x] Add `GET /health` endpoint returning status, version, session count, sessions_dir_exists
- [x] Fix hardcoded `"1.0.0"` version → `"2.0.0"` in FastAPI app and root endpoint
- [x] 3 tests in `TestHealthEndpoint` + 1 in `TestRootEndpoint`
- [ ] `scripts/smoke-test.sh` — deferred (manual `curl /health` suffices for now; documented in deploy runbook)

### 2c. REST API Integration Tests — DONE (Feb 9)

- [x] Created `tests/test_rest_integration.py` using Starlette `TestClient` (no new dependency)
- [x] `TestHealthEndpoint` (3 tests): status 200, version match, session count type
- [x] `TestRequestModelHardening` (3 tests): unknown fields → 422 on session, override, determination
- [x] `TestRequestIdMiddleware` (3 tests): header presence, echo, timing
- [x] `TestRootEndpoint` (1 test): version consistency
- [x] Full suite: 310 passed, 57 deselected, 2.3s

### 2d. Request Model Hardening — DONE (Feb 9)

- [x] Added `ConfigDict(extra="forbid")` to all 13 request models
- [x] `SessionResponse` (response model) left as-is — only inputs are hardened
- [x] 3 tests verify 422 on unknown fields (session creation, override, determination)
- [ ] Verify web app and Custom GPT don't send extra fields — coordinate with Darren on next deploy

### 2e. Architecture Documentation — DONE (Feb 9)

Two systems (our API on port 8003, Darren's web app on port 8200) serve different nginx paths but share session state. This relationship was undocumented. During Phase 1 closure we lost 10 minutes to a ghost session that existed in the web app layer but not in ours.

- [x] Create `docs/architecture.md` with correct nginx routing diagram, dual-interface pattern, session state, deployment topology, configuration reference
- [x] Document shared session state (both systems read/write shawn's data dir)
- [x] Document deployment topology: 7 PM2 processes, ports, nginx routing, user context
- [x] Deployment procedure documented in `docs/architecture.md` (no separate runbook needed — procedure is 6 commands)
- [x] Fix incorrect nginx diagram in `.claude/strategy/indexes/infrastructure.md` (was showing `/api/registry` → 8003; actually routes to 8200)

**Acceptance:** A new developer can read `docs/architecture.md` and deploy a change to production without SSH archaeology.

### 2f. Observability — DONE (Feb 9)

- [x] Request ID middleware: every response carries `X-Request-ID` (auto-generated UUID or echoed from client) and `X-Response-Time-Ms`
- [x] 3 tests for middleware behavior
- [x] `ecosystem.config.cjs` adds `log_date_format` for timestamped PM2 logs
- [x] Verified FastAPI access logging works — uvicorn default access log shows method, path, status on every request
- [x] `pm2-logrotate` installed and configured: 50MB max, 14 files retained, compress, daily rotation at midnight
- [x] Uptime monitoring: cron job every 5 minutes pings `/health`, logs failures to `logs/health-failures.log`
- [x] `last_request_at` added to health endpoint (ISO timestamp, null before first request). 1 new test.

### Phase 2 Overall Acceptance

1. ~~`scripts/smoke-test.sh` passes after every deployment~~ — deferred; `curl /health` documented in `docs/architecture.md`
2. **DONE** — `pytest` includes REST integration tests (311 tests, 2.3s)
3. **DONE** — Unknown request fields return 422, not silent success
4. **DONE** — `GET /health` returns API version, session count, and `last_request_at`
5. **DONE** — `docs/architecture.md` exists with correct nginx routing, deployment procedure, topology
6. **DONE** — PM2 restart count explained (port-bind storm, Jan 14), fix in `ecosystem.config.cjs`
7. **DONE** — Request ID headers on every response, pm2-logrotate (50MB/14-day/compress), cron health check every 5min

**Progress:** Phase 2 complete. All sub-phases (2a-2f) done. Code changes need deployment; server-side config (logrotate, cron) already applied.

## Phase 3: Demo Readiness and BizDev Support

**Goal:** The system works reliably across all test data, produces professional deliverables in every output format, and withstands Becca's direct testing with partner projects. The web app is impressive enough that partners focus on usefulness, not rough edges.

**Why this matters now:** Becca is the first person outside the development team who will test this system with real client projects. She will try every output format, every workflow path, and every edge case — not because she's looking for bugs, but because that's what a thorough reviewer does. Phase 3 ensures the system passes this scrutiny before it reaches external partners.

### 3a. PDF Export — DONE (Feb 9)

- [x] Add `fpdf2>=2.7.0` dependency (pure Python, no system libraries)
- [x] Implement `format_pdf_report()` in `report_tools.py` — renders ReviewReport as professional PDF
- [x] Wire PDF format through `generate_review_report()` and `export_review()`
- [x] Remove `NotImplementedError` from `export_review()` — PDF now flows through normally
- [x] Add REST download endpoint `GET /sessions/{session_id}/report/download-pdf`
- [x] Add download URL in report generation response for `format=pdf`
- [x] 5 new tests: valid PDF output, content verification (project name, requirement IDs), Unicode sanitization, integration test
- [x] 1 new REST endpoint test: PDF download returns 404 without prior generation
- [x] Full test suite: 317 passed, 57 deselected

### 3a-bis. OpenAI Fallback Backend — DONE (Feb 9)

- [x] Add `openai>=1.0.0` dependency
- [x] Implement `_call_via_openai()` in `llm_client.py` — transparent fallback when Anthropic unavailable
- [x] Add `openai_api_key` and `openai_model` to Settings (env vars, defaults to `gpt-4o-mini`)
- [x] Wire into `_resolve_backend()`: auto mode tries cli → api → openai
- [x] Error classification for OpenAI API errors (auth, billing, rate limit)
- [x] Settings immutability: `__setattr__`/`__delattr__` prevent post-init mutation
- [x] 10 new tests: backend selection, OpenAI routing, error classification, settings freeze
- [x] Full suite: 327 passed, 57 deselected

### 3b. Multi-Project E2E Verification

Currently at n=1 confidence (Greens Lodge only). Need n=3 before demos.

- [ ] **Botany Farm** (7 PDFs) — Run full workflow: discover, classify, map, extract evidence, validate, generate report. Verify all 7 documents classified correctly, requirements mapped, evidence extracted with citations.
- [ ] **Fonthill Farms** (5 files including spreadsheet) — Same full workflow. Key test: spreadsheet ingestion (yields data), land cover map classification. This exercises the 1b and 1e changes on a different project.
- [ ] **Greens Lodge** (19 files) — Already verified via CLI backend (Feb 9). Re-run after Phase 2 deployment to confirm behavior is identical on production.
- [ ] Verify all three produce professional reports in markdown, DOCX, and PDF formats
- [ ] Document any classification gaps or evidence quality issues discovered during testing

### 3c. API Integration Testing — DONE (Feb 9)

Every REST endpoint that the web app or Custom GPT calls needs to work correctly. Becca won't use the CLI — she'll use the web app.

- [x] **Session lifecycle** (5 tests): Create, create with documents_path, list, get by ID, delete
- [x] **Document discovery** (2 tests): Discover finds all 7 Botany Farm PDFs, classifies all with non-empty classification
- [x] **Error paths** (4 tests): Nonexistent session → 404 on GET/discover/map, empty body → 422
- [x] **Human review workflow** (7 tests): Set/clear override, add annotation, set/clear determination, audit log entries, aggregated review-status
- [x] **Report generation** (3 tests): Markdown format, JSON format, download returns file or 404
- [x] **Bug fix:** `SessionNotFoundError` now inherits `FileNotFoundError` — all REST endpoints return 404 (not 500) for missing sessions
- [x] Full suite: 348 passed, 57 deselected (21 new integration tests)

Remaining coverage for E2E (3b): evidence extraction, cross-validation, all 5 report formats. These require LLM calls and will be exercised during E2E testing on the server.

### 3d. Cross-Validation Quality

The cross-validation endpoint works (no longer 500s), but the quality of results needs verification. Partial coordinator output is tolerated but should be distinguishable from complete results.

- [ ] Verify land tenure validation produces meaningful results for Greens Lodge (13 land registry PDFs)
- [ ] Verify date alignment validation catches real inconsistencies (or correctly passes when dates are consistent)
- [ ] Verify project ID validation works across multiple document versions (Greens Lodge has 3 project plan versions)
- [ ] Document any cases where validation returns partial results and whether they're actionable

### 3e. Demo Preparation

- [ ] Ensure demo flow works in <3 minutes (start review to see results)
- [ ] Prepare demo framing: "This is a registry agent, not an AI assistant"
- [ ] Privacy and data isolation talking points documented
- [ ] Verify web app handles concurrent sessions without data leakage
- [ ] Stage bypass capability: start at evidence extraction when documents are already mapped

Sources: updated-registry-spec.md, review-agent-readiness.md Demo-Ready checklist

### Phase 3 Overall Acceptance

1. All three registration test projects (Botany Farm, Fonthill Farms, Greens Lodge) produce complete reviews without errors
2. All 5 output formats generate and download correctly
3. All REST API endpoints return expected responses (no 500s on any standard workflow)
4. Cross-validation produces structured, actionable results
5. A non-technical person (Dave, Gregory) can watch a demo and understand the value proposition
6. Becca can run a review through the web app end-to-end and get results she'd show to a partner

**Progress:** 3a (PDF export), 3a-bis (OpenAI fallback), and 3c (integration tests) complete. 3b (E2E), 3d (quality), 3e (demo prep) pending deployment.

## Phase 4: Integration and Sustained Use

**Goal:** The system is reliable for sustained use, not just demos.

- [ ] Google Drive ingestion bot integration (Darren's work, needs testing)
- [ ] Third-party Drive access testing (can clients add the bot to their own Drive?)
- [ ] Airtable API integration for structured data (Samu exploring with Carbon Egg)
- [ ] CarbonEg-specific requirements pre-loaded in checklist
- [ ] Session data backup strategy (periodic snapshot of sessions directory to offsite storage)
- [ ] Evaluate file-based storage vs. lightweight database (SQLite) for Phase 5+ scale

**Acceptance:** The system can be pointed at a new project's Drive folder and produce a review without manual intervention beyond clicking "Start Review."

## Phase 5: Issuance Review Agent

**Goal:** Extend from registration review to credit issuance review.

Scoped in updated-registry-spec.md. Builds on the same architecture with expanded evidence validation:
- Monitoring report completeness
- Sampling method checks (stratification, depth, count, GNSS accuracy)
- Lab verification (SOC%, accreditation)
- Temporal alignment (sampling dates vs imagery dates, +/-4 months)
- Buffer pool, leakage, and additionality evidence
- Issuance-specific checklist and report format

This is substantial new work. Detailed plan to be created when Phase 4 integration work is stable.

## Phase 6: Scale and Ecosystem

**Goal:** Support multiple protocols, registries, and project types.

- Protocol-specific checklists generated from program guides
- Multi-registry support
- Verifier-specific views (GIS-el's suggestion)
- Geospatial file processing (.shp, .tif, .gdb, etc.)
- Naming convention agent/sub-agent
- Ledger-aligned outputs (on-chain anchoring)
- Registry-as-a-service positioning

This phase represents the long-term product vision described in regen-marketplace-regen-registry.md and the Jan 20 standup. Detailed planning deferred.
