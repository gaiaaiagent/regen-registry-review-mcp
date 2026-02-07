# Phase 1: Carbon Egg Registration Readiness

Status: Not Started
Created: 2026-02-07
Target: Before next team check-in (Feb 11)

## Objective

The system can process Carbon Egg's registration documents end-to-end without errors and produce a clean, professional report. Becca can run a review and get output she'd confidently show to a partner.

## Prerequisites

Before starting implementation work:

1. **Verify production state** — SSH to the GAIA server and confirm what commit is deployed. Document any drift between dev and production. This determines whether task-12 fixes are live.

2. **Run the fast test suite** — `pytest` should show 229+ passing with expensive tests deselected. If anything is broken, fix it before adding new work.

3. **Reproduce the mapping bug** — Use the Botany Farm example or request specific files from Becca that trigger the error. The bug is described in review-agent-readiness.md item 2.1 with a screenshot. It may be related to document naming confusion at the mapping step.

## Work Items

### 1a. Fix Mapping Bug

**Problem:** System confuses document names during the mapping stage (Stage C). Different from the earlier cross-validation bug that was fixed. Becca has a screenshot.

**Investigation approach:**
- Check `tools/mapping_tools.py` for how document names are resolved
- Check `prompts/C_requirement_mapping.py` for how documents are presented to the LLM
- Look at `services/document_processor.py` for document classification logic
- Run the Botany Farm example through stages A-C and inspect the mapping output

**Files likely involved:**
- `src/registry_review_mcp/tools/mapping_tools.py`
- `src/registry_review_mcp/prompts/C_requirement_mapping.py`
- `src/registry_review_mcp/services/document_processor.py`

**Test:** Add a regression test to `tests/test_document_processing.py` or create a new `tests/test_mapping_bug.py`.

### 1b. Spreadsheet Ingestion

**Problem:** System only processes PDFs. Carbon Egg has land tenure records in .xlsx and .csv files.

**Implementation approach:**
- Add spreadsheet reading capability to `services/document_processor.py`
- Use `openpyxl` (for .xlsx) or the existing pandas/csv stdlib for parsing
- Integrate with document discovery (Stage B) so spreadsheets appear in the document inventory
- Extract tabular data into a text representation suitable for evidence mapping
- Handle multi-sheet workbooks (each sheet may represent a different farm)

**Files to modify:**
- `src/registry_review_mcp/services/document_processor.py` — add spreadsheet detection and extraction
- `src/registry_review_mcp/prompts/B_document_discovery.py` — update if needed for spreadsheet classification
- `pyproject.toml` — add dependency if needed (check if openpyxl is already available)

**Test:** Create `tests/test_spreadsheet_ingestion.py` with sample .xlsx and .csv files.

### 1c. Report Output Quality

**Problem:** Reports look like ChatGPT output. Specific issues: duplicate "value" field, emojis in content, chat-style formatting, PDF download broken.

**Implementation approach:**

*Duplicate value field:*
- Locate where "value" appears before "Primary Documentation" in report output
- Check `tools/report_tools.py` — the `_format_submitted_material()` and related functions
- Remove or merge the redundant field

*Emoji removal:*
- Check `prompts/F_report_generation.py` for emoji usage in prompts
- Strip emojis from generated content in `tools/report_tools.py`

*Professional formatting:*
- Ensure tables use consistent column widths
- Use registry-style language (not conversational AI language)
- Check that the DOCX template (`examples/checklist.docx`) produces clean output

*PDF download:*
- Check `chatgpt_rest_api.py` — the `/sessions/{id}/report/download` endpoint
- Verify the file path resolution and content-type headers
- PDF export was listed as "post-MVP" in the spec, but working download of existing formats is critical

**Files to modify:**
- `src/registry_review_mcp/tools/report_tools.py`
- `src/registry_review_mcp/prompts/F_report_generation.py`
- `chatgpt_rest_api.py` (download endpoints)

**Test:** Visual inspection of output. Update `tests/test_report_generation.py` to verify no emojis and no duplicate fields.

### 1d. Multi-Project Support

**Problem:** Carbon Egg has 100+ farms plus a meta-project. System needs to handle this scale and structure.

**Implementation approach:**

This is primarily a workflow and knowledge problem, not a code problem. The system already handles individual projects. What's needed:

- **Auxiliary knowledge document:** Create a markdown file explaining the farm vs meta-project distinction that can be loaded as context. Include: what's the same across every project, what's repeated, what's unique, how the meta-project relates to the whole.
- **Checklist variants:** Work with Becca to determine if the per-farm checklist is a subset of the full checklist or a different structure entirely. If different, create a new JSON checklist in `data/checklists/`.
- **Batch processing guidance:** Document the recommended workflow for processing 100+ farms — likely a script or instruction set that creates sessions in sequence.

**Files to create/modify:**
- `data/checklists/` — new checklist file(s) if needed
- Documentation for the batch processing workflow

**Dependencies:** Needs input from Becca on checklist differentiation (see review-agent-readiness.md item 2.2: "Becca needs to think through and update checklist").

## Acceptance Criteria

- [ ] Fast test suite passes (`pytest` — 229+ passing)
- [ ] Botany Farm example processes without mapping errors
- [ ] A .xlsx file can be uploaded and appears in document discovery
- [ ] Report output has no duplicate "value" field
- [ ] Report output has no emojis
- [ ] Report tables render as structured data, not chat prose
- [ ] Markdown and DOCX downloads work from the web app
- [ ] Changes deployed to production and verified

## Notes

- Do not run expensive tests unless specifically investigating LLM extraction quality
- Commit frequently with clear messages — Darren may need to sync changes for the web app
- Update STATUS.md and this plan file as work progresses
- If Carbon Egg test data becomes available, prioritize testing with real data over the Botany Farm example
