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
- [ ] PDF download — not implemented (raises `NotImplementedError`); requires a rendering library. Deferred.
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

### 2a. Diagnose PM2 Instability

PM2 shows 8,749 restarts. Log rotation preserves 7 rotated files (back to Dec 13), but the current log only has ~600 lines covering the most recent session. We don't know whether the restarts are crashes, OOM kills, or accumulated manual restarts over 2+ months.

- [ ] Decompress and analyze rotated PM2 logs (`pm2-error.log.1` through `pm2-error.log.7.gz`) for crash patterns
- [ ] Check system journal for OOM kills: `journalctl -k | grep -i 'oom\|killed'`
- [ ] Check PM2 ecosystem config for `max_memory_restart`, `min_uptime`, or other auto-restart triggers
- [ ] Monitor process memory over a 24-hour period: `pm2 monit` or log `pm2 jlist` periodically
- [ ] Document findings — if restarts are benign (accumulated from deploys), note it; if there's a memory leak, fix it

**Acceptance:** We can explain why the restart count is 8,749 and either fix the underlying issue or document that it's expected.

### 2b. Health Check and Smoke Test

No health endpoint exists. No deployment verification script exists. The `runbooks/` directory referenced in Phase 0 doesn't exist. Every deployment is a manual curl adventure.

- [ ] Add `GET /health` endpoint to `chatgpt_rest_api.py` returning: API version (from `pyproject.toml`), uptime, session count, git commit hash, last request timestamp
- [ ] Create `scripts/smoke-test.sh` that exercises the 6-stage pipeline against a small fixture (Botany Farm, fastest test data): create session → discover → map → verify non-zero mappings → verify no 500s on validate
- [ ] Wire smoke test into deployment: the deployment script runs it automatically after `pm2 restart` and rolls back on failure
- [ ] Add a test for the `/health` endpoint in the integration test suite (see 2c)

**Acceptance:** `scripts/smoke-test.sh` runs in <30 seconds, exits 0 when the API is healthy, exits 1 with a clear error message when something is wrong. Deployments refuse to finish without a green smoke test.

### 2c. REST API Integration Tests

We have 300 unit tests but zero tests that exercise the actual FastAPI endpoints. Both bugs fixed today (documents_path silently dropped, validation 500) would have been caught by integration tests.

- [ ] Add `httpx` (or use FastAPI's `TestClient`) as a test dependency
- [ ] Create `tests/test_rest_integration.py` with a `TestClient` fixture that uses a temp `sessions_dir`
- [ ] Test `POST /sessions` round-trip: send `documents_path`, read back session, verify it's stored
- [ ] Test `POST /sessions/{id}/discover` with a real test-data directory
- [ ] Test `POST /sessions/{id}/validate` returns 200 (not 500) with partial coordinator output
- [ ] Test `GET /health` returns expected structure
- [ ] Test that unknown fields in request body are rejected (see 2d)

**Acceptance:** Integration tests cover every REST endpoint's happy path. Running `pytest` still completes in <10 seconds (these tests don't call LLMs). Test count increases by ~10-15.

### 2d. Request Model Hardening

Pydantic's default `extra` config is `"ignore"` — callers can send fields that the model doesn't declare, and they're silently discarded. This is how `documents_path` went unnoticed for weeks. The REST request models should reject unknown fields so that mismatches between callers and the API surface immediately.

- [ ] Add `model_config = ConfigDict(extra='forbid')` to all REST request models in `chatgpt_rest_api.py`: `CreateSessionRequest`, `DiscoverRequest`, `MapRequest`, `EvidenceRequest`, `UploadFileRequest`, and any others
- [ ] Verify that existing callers (web app, Custom GPT) don't send extra fields that would now be rejected — if they do, add the fields to the model or coordinate with Darren
- [ ] Add a test that sends an unknown field to `POST /sessions` and verifies a 422 response

**Acceptance:** Sending `{"project_name": "Test", "bogus_field": true}` to `POST /sessions` returns 422 Unprocessable Entity, not 200 with the field silently dropped.

### 2e. Architecture Documentation

Two systems (our API on port 8003, Darren's web app on port 8200) serve different nginx paths but share session state. This relationship is undocumented. During Phase 1 closure we lost 10 minutes to a ghost session that existed in the web app layer but not in ours.

- [ ] Create `docs/architecture.md` with a clear diagram: nginx → `/registry` (auth_basic, port 8003, our API) vs. `/api/registry` (port 8200, web app) vs. `/registry-review/` (web app frontend)
- [ ] Document which sessions belong to which system (shawn's data dir vs. darren's)
- [ ] Document the deployment topology: PM2 processes, ports, nginx routing, user contexts
- [ ] Create `runbooks/deploy.md` with the actual deployment steps (currently just in our heads and MEMORY.md)
- [ ] Document how to verify a deployment is healthy (reference `scripts/smoke-test.sh`)

**Acceptance:** A new developer can read `docs/architecture.md` and `runbooks/deploy.md` and deploy a change to production without SSH archaeology.

### 2f. Observability

The PM2 out log showed no access logs from our test requests. FastAPI logs `INFO:` access lines but they may not be flushing reliably, or log rotation truncated them. When something goes wrong in production, we need to be able to see what happened.

- [ ] Verify FastAPI access logging works after PM2 restart (may need `--log-level info` in uvicorn config or explicit `logging.basicConfig`)
- [ ] Add structured logging with request IDs: each request gets a UUID, logged at start and end, so we can trace a request through the system
- [ ] Configure `pm2-logrotate` explicitly: retain 14 days, compress after 1 day, max size 50MB per file
- [ ] Set up basic uptime monitoring: a free service (UptimeRobot, Healthchecks.io, or a cron job) that hits `GET /health` every 5 minutes and alerts on failure
- [ ] Add a `last_request_at` timestamp to the health endpoint so we can see if the API is receiving traffic

**Acceptance:** After a deployment, `pm2 logs registry-review-api --lines 10` shows access logs for the smoke test. If the API goes down at 3am, someone gets a notification.

### Phase 2 Overall Acceptance

All of the following are true:

1. `scripts/smoke-test.sh` passes after every deployment
2. `pytest` includes REST integration tests (310+ tests, <10 seconds)
3. Unknown request fields return 422, not silent success
4. `GET /health` returns API version, uptime, and session count
5. `docs/architecture.md` and `runbooks/deploy.md` exist and are accurate
6. PM2 restart count is explained (and fixed if it's a real problem)
7. Access logs are visible in PM2 logs after every request

## Phase 3: Demo Readiness and BizDev Support

**Goal:** The web app is impressive enough that partners focus on usefulness, not rough edges. The team has demo materials and talking points.

- [ ] Prepare demo framing: "This is a registry agent, not an AI assistant"
- [ ] Ensure demo flow works in <3 minutes (start review to see results)
- [ ] Privacy and data isolation talking points documented
- [ ] Test with Fonthill Farms and Greens Lodge projects (Becca shared these for Ecometric protocol)
- [ ] Stage bypass capability: start at evidence extraction when documents are already mapped
- [ ] Verify web app handles concurrent sessions without data leakage

Sources: updated-registry-spec.md, review-agent-readiness.md Demo-Ready checklist

**Acceptance:** A non-technical person (Dave, Gregory) can watch a demo and understand the value proposition. The web app doesn't crash, stall, or produce embarrassing output.

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
