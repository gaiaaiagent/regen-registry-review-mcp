# Development Roadmap

Last updated: 2026-02-07

This roadmap sequences work into phases based on urgency and dependency. Each phase has clear acceptance criteria. Phases may overlap where work is independent.

## Phase 0: Orientation and Production Verification

**Goal:** Establish ground truth about what's deployed and working.

- [ ] SSH to production server, verify running version against `main`
- [ ] Confirm whether task-12 (Jan 26) changes are deployed
- [ ] Run health check: hit `/sessions` endpoint, verify response
- [ ] Check systemd service status and recent logs
- [ ] Document any drift between dev and production in `runbooks/deploy.md`
- [ ] Run fast test suite locally: `pytest` (should see 229+ passing, expensive deselected)

**Acceptance:** STATUS.md updated with verified production state. Any drift documented and remediation plan in place.

## Phase 1: Carbon Egg Registration Readiness

**Goal:** The system can process Carbon Egg's registration documents end-to-end without errors and produce a clean, professional report.

### 1a. Fix Mapping Bug

- [ ] Reproduce Becca's mapping error with available test data
- [ ] Diagnose: is this a document naming issue, a mapping logic issue, or a cross-validation variant?
- [ ] Fix and add regression test
- [ ] Verify with Botany Farm test project (existing tests pass)

Sources: review-agent-readiness.md item 2.1, Becca's Slack screenshots

### 1b. Spreadsheet Ingestion

- [ ] Add .xlsx and .csv support to document processor (`services/document_processor.py`)
- [ ] Integrate with document discovery stage (Stage B)
- [ ] Handle tabular data extraction for evidence mapping
- [ ] Test with sample land tenure spreadsheet data
- [ ] Add unit tests for spreadsheet processing

Sources: Jan 20 standup, Jan 27 standup, data-types-for-registry-protocols.md

### 1c. Report Output Quality

- [ ] Remove duplicate "value" field from output table
- [ ] Remove emojis from generated report content
- [ ] Containerize report sections (structured tables, not chat-style prose)
- [ ] Verify tables render cleanly when exported from the web app
- [ ] Fix PDF download (currently broken in web app)
- [ ] Test DOCX download with the cleaned-up formatting

Sources: review-agent-readiness.md items 2.3 and 3.1-3.2, Feb 3 standup

### 1d. Multi-Project Support (Carbon Egg Architecture)

- [ ] Document the farm vs. meta-project distinction as auxiliary knowledge
- [ ] Create per-farm checklist variant (shorter, focused on individual farm requirements)
- [ ] Create meta-project checklist variant (aggregated project-level requirements)
- [ ] Test processing multiple independent farm projects in sequence
- [ ] Verify project isolation (one farm's data doesn't leak into another's review)

Sources: review-agent-readiness.md item 2.2, Feb 3 standup (Darren's recommendation)

**Acceptance:** Carbon Egg's test documents (when available) process cleanly. Report is professional. No mapping errors. Spreadsheets are handled. Becca can run a review and get a result she'd show to a partner.

## Phase 2: Demo Readiness and BizDev Support

**Goal:** The web app is impressive enough that partners focus on usefulness, not rough edges. The team has demo materials and talking points.

- [ ] Prepare demo framing: "This is a registry agent, not an AI assistant"
- [ ] Ensure demo flow works in <3 minutes (start review → see results)
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
- [ ] Improved error handling for edge cases (large documents, malformed PDFs, network failures)
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
