# Phase 1: Carbon Egg Registration Readiness

Status: In Progress (1a, 1b complete — 1c, 1d remain)
Created: 2026-02-07
Updated: 2026-02-07
Target: Before next team check-in (Feb 11)

## Objective

The system can process Carbon Egg's registration documents end-to-end without errors and produce a clean, professional report. Becca can run a review and get output she'd confidently show to a partner.

## Prerequisites

Before starting implementation work:

1. **Verify production state** — SSH to the GAIA server and confirm what commit is deployed. Document any drift between dev and production. This determines whether task-12 fixes are live.

2. **Run the fast test suite** — `pytest` should show 229+ passing with expensive tests deselected. If anything is broken, fix it before adding new work.

3. **Reproduce the mapping bug** — Use the Botany Farm example or request specific files from Becca that trigger the error. The bug is described in review-agent-readiness.md item 2.1 with a screenshot. It may be related to document naming confusion at the mapping step.

## Work Items

### 1a. Fix Mapping Bug — DONE

**Problem:** System confuses document names during the mapping stage (Stage C).

**Root cause:** Naming convention split. The classifier (`classify_document_by_filename`) produces underscore labels (`land_tenure`, `ghg_emissions`, `gis_shapefile`), but the mapper (`_infer_document_types`) was looking for hyphenated labels (`land-tenure`). Three document types silently fell through to the project plan fallback.

**Fix:** Normalized all mapper labels to underscores (commit `467695e`). Added 5 regression tests in `TestMappingConventionConsistency` that verify: all classifier labels appear in mapper output, no hyphenated labels exist anywhere in mapper, and specific document types map to their correct requirements.

### 1b. Spreadsheet Ingestion — DONE

**Problem:** System only processes PDFs. Carbon Egg has land tenure records in .xlsx and .csv files.

**Implementation (7 files modified/created):**
- `pyproject.toml` — added `openpyxl>=3.1.0`
- `utils/patterns.py` — added `SPREADSHEET_EXTENSIONS`, `is_spreadsheet_file()`
- `extractors/spreadsheet_extractor.py` — new file, converts .xlsx/.xls/.csv/.tsv → markdown tables with `--- Sheet "name" (N of M) ---` markers
- `tools/document_tools.py` — spreadsheet extensions in discovery, classification branch (pattern-first, then generic `spreadsheet_data`), metadata extraction (sheet count)
- `services/document_processor.py` — `run_fast_extraction()` handles spreadsheets alongside PDFs; `hq_status = "not_applicable"` for spreadsheets
- `tools/mapping_tools.py` — `spreadsheet_data` added to land tenure, monitoring, emissions, project details, ownership categories
- `tests/conftest.py` + `test_document_processing.py` — 3 fixtures + 7 tests

**Design decisions:** Filename patterns take priority over file type (so `land_tenure_records.xlsx` classifies as `land_tenure`, not `spreadsheet_data`). Sheet markers mirror PDF page markers for uniform citation extraction. 10,000-row cap per sheet. No HQ dual-track (spreadsheets are already structured). `page_count = sheet_count` for compatibility.

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

- [x] Fast test suite passes (`pytest` — 241 passing)
- [x] Botany Farm example processes without mapping errors
- [x] A .xlsx file can be uploaded and appears in document discovery
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
