# Development Roadmap

Last updated: 2026-02-07 (evening)

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

## Phase 1: Carbon Egg Registration Readiness — IN PROGRESS

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

### 1f. LLM Error Handling — DONE (Feb 7, uncommitted)

Discovered when evidence extraction hit $0 API credit balance:
- [x] Create `utils/llm_client.py` — centralized `get_anthropic_client()`, `classify_api_error()`
- [x] `LLMBillingError` and `LLMAuthenticationError` custom exceptions
- [x] Fatal errors (billing, auth) propagate immediately instead of being silently swallowed
- [x] Actionable guidance in error messages (console URLs, explanations)
- [x] REST API returns HTTP 402 for billing/auth errors
- [x] Mark `test_full_report_workflow` as `@pytest.mark.expensive` (was previously false-passing)
- [x] 8 new tests for error classification and key validation
- [x] Full test suite: 268 passed, 57 deselected

### 1g. Claude CLI Backend — SPEC'D (Feb 7)

**Goal:** Route LLM calls through Max plan via `claude -p` subprocess, eliminating the need for API credits.

Full spec: `.claude/strategy/plans/claude-cli-backend.md`

- [ ] Add `call_llm()` to `utils/llm_client.py` with auto-detecting dual backend (API + CLI)
- [ ] Add `_call_via_cli()` using `asyncio.create_subprocess_exec` with `claude -p`
- [ ] Add `llm_backend` setting (auto/api/cli) to `config/settings.py`
- [ ] Update `evidence_tools.py` to use `call_llm()` instead of direct `AsyncAnthropic`
- [ ] Update `llm_synthesis.py` to use `call_llm()`
- [ ] Update `analyze_llm.py` / `unified_analysis.py` to use `call_llm()`
- [ ] Add tests for backend selection, CLI invocation, error classification
- [ ] Manual verification with Max plan on dev machine
- [ ] Install Claude Code on GAIA production server
- [ ] Deploy and verify end-to-end

**Acceptance:** Evidence extraction runs successfully using Max plan (CLI backend) with no API credit charges. The system auto-detects the best backend. Test suite passes. Greens Lodge and Fonthill Farms produce complete reviews.

**Overall Phase 1 Acceptance:** Carbon Egg's test documents process cleanly. Report is professional. No mapping errors. Spreadsheets are handled. LLM pipeline runs without API credit costs. Becca can run a review and get a result she'd show to a partner.

**Progress:** 1a through 1f complete. 1g spec'd, implementation next.

## Phase 2: Demo Readiness and BizDev Support

**Goal:** The web app is impressive enough that partners focus on usefulness, not rough edges. The team has demo materials and talking points.

- [ ] Prepare demo framing: "This is a registry agent, not an AI assistant"
- [ ] Ensure demo flow works in <3 minutes (start review to see results)
- [ ] Privacy and data isolation talking points documented
- [ ] Test with Fonthill Farms and Greens Lodge projects (Becca shared these for Ecometric protocol)
- [ ] Stage bypass capability: start at evidence extraction when documents are already mapped
- [ ] Verify web app handles concurrent sessions without data leakage

Sources: updated-registry-spec.md, review-agent-readiness.md Demo-Ready checklist

**Acceptance:** A non-technical person (Dave, Gregory) can watch a demo and understand the value proposition. The web app doesn't crash, stall, or produce embarrassing output.

## Phase 3: Infrastructure Hardening

**Goal:** The system is reliable for sustained use, not just demos.

- [ ] Google Drive ingestion bot integration (Darren's work, needs testing)
- [ ] Third-party Drive access testing (can clients add the bot to their own Drive?)
- [ ] Airtable API integration for structured data (Samu exploring with Carbon Egg)
- [ ] CarbonEg-specific requirements pre-loaded in checklist
- [ ] Production monitoring: alerts when service goes down, log rotation
- [ ] Deploy procedure documented and tested (runbooks/deploy.md)

**Acceptance:** The system can be pointed at a new project's Drive folder and produce a review without manual intervention beyond clicking "Start Review."

## Phase 4: Issuance Review Agent

**Goal:** Extend from registration review to credit issuance review.

Scoped in updated-registry-spec.md. Builds on the same architecture with expanded evidence validation:
- Monitoring report completeness
- Sampling method checks (stratification, depth, count, GNSS accuracy)
- Lab verification (SOC%, accreditation)
- Temporal alignment (sampling dates vs imagery dates, +/-4 months)
- Buffer pool, leakage, and additionality evidence
- Issuance-specific checklist and report format

This is substantial new work. Detailed plan to be created when Phase 1 is complete.

## Phase 5: Scale and Ecosystem

**Goal:** Support multiple protocols, registries, and project types.

- Protocol-specific checklists generated from program guides
- Multi-registry support
- Verifier-specific views (GIS-el's suggestion)
- Geospatial file processing (.shp, .tif, .gdb, etc.)
- Naming convention agent/sub-agent
- Ledger-aligned outputs (on-chain anchoring)
- Registry-as-a-service positioning

This phase represents the long-term product vision described in regen-marketplace-regen-registry.md and the Jan 20 standup. Detailed planning deferred.
