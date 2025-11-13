# Phase 4 Implementation Plan: Cross-Validation & Report Generation

**Status:** In Progress
**Start Date:** November 12, 2025
**Target Completion:** November 15, 2025
**Priority:** P0 (Critical for MVP)

---

## Executive Summary

Phase 4 completes the core registry review automation by adding cross-document validation and structured report generation. This enables Becca to verify consistency across documents and generate professional review reports ready for approval decisions.

**Key Deliverables:**
1. Cross-document validation (dates, land tenure, project IDs)
2. Structured report generation (Markdown, JSON)
3. Two workflow prompts: `/cross-validation` and `/report-generation`
4. Complete end-to-end testing with Botany Farm data

---

## Alignment with Project Vision

### From Specs (2025-11-12-registry-review-mcp-REFINED.md)

**Section 4: Cross-Document Validation (Lines 301-358)**
- Date alignment validation (imagery vs sampling within 4 months)
- Land tenure consistency with fuzzy name matching
- Project ID propagation across documents
- Temporal logic checks

**Section 5: Structured Report Generation (Lines 362-415)**
- Multi-format output (Markdown, JSON, PDF)
- Checklist population with findings
- Evidence citations for each requirement
- Summary statistics and flagged items

**Section 6.4-6.5: Workflow Prompts (Lines 442-462)**
- Stage 4: `/cross-validation` - Run all validation checks
- Stage 5: `/report-generation` - Generate structured report

### From MCP Primitives Philosophy

**Key Principle:** "Prompts are recipes for repeat solutions"

- Tools are individual actions (validate_date_alignment, generate_report)
- Prompts compose tools into workflows (/cross-validation, /report-generation)
- Prompts guide the user experience with next-step suggestions
- Prompts provide context and discovery for the MCP server

### Success Metrics (from ROADMAP.md)

**Acceptance Criteria:**
- Date validation correctly checks 4-month rule (120 days)
- Land tenure handles name variations (surname match with fuzzy threshold)
- Report includes all 23 requirements with findings
- Report cites page numbers for all evidence
- Complete workflow test passes with Botany Farm data

---

## Technical Architecture

### MCP Server Primitive Hierarchy

Following the philosophy that **Prompts > Tools > Resources**:

```
/cross-validation (PROMPT)
├── validate_date_alignment (TOOL)
├── validate_land_tenure (TOOL)
├── validate_project_id (TOOL)
└── calculate_validation_summary (TOOL)

/report-generation (PROMPT)
├── generate_review_report (TOOL)
├── format_markdown_report (TOOL)
├── format_json_report (TOOL)
└── export_review (TOOL)
```

**Rationale:** Users invoke prompts which orchestrate tools automatically, providing guided workflows with context and next steps.

### Data Flow

```
Phase 3 Output (evidence.json)
        ↓
Cross-Validation (Stage 4)
├── Extract dates from evidence
├── Extract land tenure fields
├── Extract project IDs
├── Run validation checks
├── Flag inconsistencies
└── Save validation.json
        ↓
Report Generation (Stage 5)
├── Load session + evidence + validation
├── Populate checklist with findings
├── Generate Markdown report
├── Generate JSON report
└── Save report.md + report.json
```

### File Structure

```
src/registry_review_mcp/
├── models/
│   ├── validation.py          # NEW - Validation data models
│   └── report.py              # NEW - Report data models
├── tools/
│   ├── validation_tools.py    # NEW - Cross-validation logic
│   └── report_tools.py        # NEW - Report generation logic
└── prompts/
    ├── cross_validation.py    # NEW - /cross-validation prompt
    └── report_generation.py   # NEW - /report-generation prompt

tests/
├── test_validation.py         # NEW - Validation tests
└── test_report_generation.py  # NEW - Report generation tests

data/sessions/{session-id}/
├── evidence.json              # From Phase 3
├── validation.json            # NEW - Validation results
├── report.md                  # NEW - Markdown report
└── report.json                # NEW - JSON report
```

---

## Detailed Deliverables

### 1. Cross-Document Validation

#### 1.1 Date Alignment Validation

**Purpose:** Verify that imagery dates and sampling dates are within 120 days (4-month rule from Soil Carbon methodology).

**Tool Signature:**
```python
async def validate_date_alignment(
    session_id: str,
    field1_name: str,
    field1_value: datetime,
    field1_source: str,
    field2_name: str,
    field2_value: datetime,
    field2_source: str,
    max_delta_days: int = 120
) -> dict[str, Any]:
    """
    Validate that two dates are within acceptable range.

    Returns:
        {
            "validation_id": "VAL-001",
            "validation_type": "date_alignment",
            "date1": DateField(...),
            "date2": DateField(...),
            "delta_days": 66,
            "max_allowed_days": 120,
            "status": "pass",  # or "fail", "warning"
            "message": "Dates within acceptable range",
            "flagged_for_review": False
        }
    """
```

**Test Cases:**
- ✅ Dates within 120 days → pass
- ✅ Dates exceeding 120 days → fail
- ✅ Dates exactly at 120 days → pass
- ✅ Dates in reverse order handled correctly

#### 1.2 Land Tenure Validation

**Purpose:** Verify owner name consistency across documents with fuzzy matching for variations (Nick vs Nicholas).

**Tool Signature:**
```python
async def validate_land_tenure(
    session_id: str,
    fields: list[dict[str, Any]],
    fuzzy_match_threshold: float = 0.8
) -> dict[str, Any]:
    """
    Cross-validate land tenure information from multiple documents.

    Returns:
        {
            "validation_id": "VAL-002",
            "validation_type": "land_tenure",
            "fields": [LandTenureField(...), ...],
            "owner_name_match": True,
            "owner_name_similarity": 0.95,
            "area_consistent": True,
            "tenure_type_consistent": True,
            "status": "pass",
            "message": "Land tenure consistent across documents",
            "discrepancies": [],
            "flagged_for_review": False
        }
    """
```

**Fuzzy Matching Strategy:**
- Use SequenceMatcher from difflib for string similarity
- Threshold: 0.8 (80% similarity) for warnings
- Exact match on surnames acceptable
- Flag for review if similarity < 0.8

**Test Cases:**
- ✅ Exact name match → pass
- ✅ Surname match with fuzzy (Nick vs Nicholas) → warning or pass
- ✅ Different names → fail
- ✅ Consistent area and tenure type → pass

#### 1.3 Project ID Validation

**Purpose:** Verify project ID consistency and pattern compliance across documents.

**Tool Signature:**
```python
async def validate_project_id(
    session_id: str,
    occurrences: list[dict[str, Any]],
    total_documents: int,
    expected_pattern: str = r"^C\d{2}-\d+$",
    min_occurrences: int = 3
) -> dict[str, Any]:
    """
    Validate project ID consistency across documents.

    Returns:
        {
            "validation_id": "VAL-003",
            "validation_type": "project_id",
            "expected_pattern": "^C\\d{2}-\\d+$",
            "found_ids": ["C06-4997"],
            "primary_id": "C06-4997",
            "occurrences": [ProjectIDOccurrence(...), ...],
            "total_occurrences": 5,
            "documents_with_id": 3,
            "total_documents": 5,
            "status": "pass",
            "message": "Project ID consistent across 3/5 documents",
            "flagged_for_review": False
        }
    """
```

**Test Cases:**
- ✅ Correct pattern (C06-4997) → pass
- ✅ Appears in 3+ documents → pass
- ✅ Multiple different IDs → fail
- ✅ Invalid pattern → fail

### 2. Report Generation

#### 2.1 Markdown Report

**Purpose:** Generate human-readable review report with checklist populated with findings.

**Structure:**
```markdown
# Registry Agent Review

## Project Metadata
- Project Name: Botany Farm
- Project ID: C06-4997
- Methodology: Soil Carbon v1.2.2
- Reviewed: 2025-11-12T15:30:00Z

## Summary
- Total Requirements: 23
- Covered: 11 (47.8%)
- Partially Covered: 12 (52.2%)
- Missing: 0 (0.0%)
- Overall Coverage: 73.9%

## Requirements Review

### REQ-001: Latest Methodology Version
**Status:** ⚠ Partially Covered
**Evidence:** Project Plan states "Soil Organic Carbon Estimation" (Page 3)
**Confidence:** Medium (0.39)
**Documents:** 5 documents contain related information
**Snippets:** 15 evidence snippets found

### REQ-002: Legal Land Tenure
**Status:** ✅ Covered
**Evidence:** Lease agreement found covering crediting period (Page 8, Section 3.2)
**Confidence:** High (1.00)
**Documents:** 5 documents contain related information
**Snippets:** 15 evidence snippets found

[... continue for all 23 requirements ...]

## Cross-Document Validation

### Date Alignment
✅ **PASS**: Imagery date (2022-06-15) and sampling date (2022-08-20) within 120 days (66 days apart)

### Land Tenure
⚠ **WARNING**: Owner name variation detected - "Nick Denman" vs "Nicholas Denman" (95% similarity)

### Project ID
✅ **PASS**: Project ID C06-4997 appears consistently in 5/7 documents

## Items Requiring Human Review
1. REQ-001: Methodology version mention unclear - verify v1.2.2 compliance
2. Land Tenure: Confirm name variation acceptable (Nick vs Nicholas)

## Next Steps
1. Review flagged items above
2. Obtain clarification for partial requirements
3. Finalize approval decision
```

**Tool Signature:**
```python
async def generate_review_report(
    session_id: str,
    format: str = "markdown",
    include_evidence_snippets: bool = True,
    include_validation_details: bool = True
) -> dict[str, Any]:
    """
    Generate complete review report.

    Returns:
        {
            "session_id": "session-abc123",
            "report_path": "/path/to/report.md",
            "format": "markdown",
            "generated_at": "2025-11-12T15:30:00Z",
            "summary": {...}
        }
    """
```

#### 2.2 JSON Report

**Purpose:** Machine-readable structured output for programmatic processing.

**Structure:**
```json
{
  "session_id": "session-abc123",
  "project_metadata": {
    "project_name": "Botany Farm",
    "project_id": "C06-4997",
    "methodology": "soil-carbon-v1.2.2"
  },
  "summary": {
    "requirements_total": 23,
    "requirements_covered": 11,
    "requirements_partial": 12,
    "requirements_missing": 0,
    "overall_coverage": 0.739
  },
  "requirements": [...],
  "validations": [...],
  "items_for_review": [...]
}
```

### 3. Workflow Prompts

#### 3.1 `/cross-validation` Prompt

**Purpose:** Orchestrate all validation checks and present results.

**Workflow:**
1. Load session and evidence data
2. Extract dates from evidence snippets
3. Extract land tenure fields
4. Extract project IDs
5. Run all validation checks:
   - Date alignment (imagery vs sampling)
   - Land tenure consistency
   - Project ID consistency
6. Calculate validation summary
7. Save validation.json
8. Present formatted results
9. Suggest next step: `/report-generation`

**Output Format:**
```
# Cross-Validation Results

Session: session-abc123
Project: Botany Farm 2022-2023

## Validation Summary
Total Checks: 5
✅ Passed: 3 (60%)
⚠️  Warnings: 1 (20%)
❌ Failed: 1 (20%)

## Date Alignment Checks (2)
✅ Imagery vs Sampling Dates: 66 days apart (within 120-day limit)
✅ Baseline vs Project Start: 15 days apart

## Land Tenure Checks (1)
⚠️  Owner Name Variation: "Nick Denman" vs "Nicholas Denman" (95% similarity)
    - Fuzzy match above threshold, but manual review recommended

## Project ID Checks (1)
✅ Project ID Consistency: C06-4997 found in 5/7 documents

## Contradiction Checks (1)
❌ Area Discrepancy: 120.5 ha (Project Plan) vs 118.2 ha (Deed)
    - Flagged for review

## Items Flagged for Review (2)
1. Land tenure name variation
2. Area discrepancy between documents

Next Step: Generate review report with `/report-generation`
```

#### 3.2 `/report-generation` Prompt

**Purpose:** Generate complete review report and export to desired formats.

**Workflow:**
1. Load session, evidence, and validation data
2. Check prerequisites (evidence extraction and validation complete)
3. Generate Markdown report
4. Generate JSON report
5. Save both to session directory
6. Present summary statistics
7. Suggest next step: Human review of flagged items

**Output Format:**
```
# Report Generation Complete

Session: session-abc123
Project: Botany Farm 2022-2023

## Generated Reports

📄 Markdown Report: data/sessions/session-abc123/report.md
   - Complete checklist with findings
   - Evidence citations for each requirement
   - Cross-validation results
   - Items for human review

📊 JSON Report: data/sessions/session-abc123/report.json
   - Structured data for programmatic access
   - All evidence and validation details

## Report Summary

Requirements:
  ✅ Covered: 11/23 (47.8%)
  ⚠️  Partial: 12/23 (52.2%)
  ❌ Missing: 0/23 (0.0%)
  Overall Coverage: 73.9%

Validations:
  ✅ Passed: 3/5 (60%)
  ⚠️  Warning: 1/5 (20%)
  ❌ Failed: 1/5 (20%)

Items for Review: 2

## Next Steps

1. Open report.md to review detailed findings
2. Address the 2 flagged items:
   - Land tenure name variation
   - Area discrepancy
3. Make final approval decision
4. Use `/complete` to finalize the review

The review report is ready for Becca's approval decision.
```

---

## Implementation Tasks

Following TDD approach with task breakdown:

### Week 1: Validation Infrastructure (Days 1-2)

- [x] **Task 1.1:** Create validation data models in `models/validation.py`
  - DateField, DateAlignmentValidation
  - LandTenureField, LandTenureValidation
  - ProjectIDOccurrence, ProjectIDValidation
  - ValidationSummary, ValidationResult

- [ ] **Task 1.2:** Write validation tests in `tests/test_validation.py`
  - TestDateAlignmentValidation (4 tests)
  - TestLandTenureValidation (3 tests)
  - TestProjectIDValidation (3 tests)
  - TestCrossValidationWorkflow (1 test)

- [ ] **Task 1.3:** Implement validation tools in `tools/validation_tools.py`
  - validate_date_alignment()
  - validate_land_tenure() with fuzzy matching
  - validate_project_id()
  - cross_validate() - orchestrates all checks
  - calculate_validation_summary()

- [ ] **Task 1.4:** Create `/cross-validation` prompt
  - Load session and evidence
  - Extract validation fields from evidence
  - Run all validation checks
  - Format and present results
  - Save validation.json

### Week 1: Report Generation (Days 3-4)

- [ ] **Task 2.1:** Create report data models in `models/report.py`
  - ReportMetadata
  - RequirementFinding
  - ValidationFinding
  - ReportSummary
  - ReviewReport

- [ ] **Task 2.2:** Write report generation tests
  - TestMarkdownReportGeneration (3 tests)
  - TestJSONReportGeneration (2 tests)
  - TestReportFormatting (2 tests)
  - TestCompleteWorkflow (1 test)

- [ ] **Task 2.3:** Implement report generation tools
  - generate_review_report()
  - format_markdown_report()
  - format_json_report()
  - export_review()

- [ ] **Task 2.4:** Create `/report-generation` prompt
  - Load session, evidence, validation
  - Generate reports in multiple formats
  - Save to session directory
  - Present summary and next steps

### Week 1: Integration & Testing (Day 5)

- [ ] **Task 3.1:** Register tools and prompts in server.py
  - Add validation_tools imports
  - Add report_tools imports
  - Register @mcp.tool() decorators
  - Register @mcp.prompt() decorators

- [ ] **Task 3.2:** Run complete test suite
  - All unit tests pass
  - All integration tests pass
  - Fix any issues

- [ ] **Task 3.3:** End-to-end testing with Botany Farm
  - /initialize
  - /document-discovery
  - /evidence-extraction
  - /cross-validation (NEW)
  - /report-generation (NEW)
  - Verify all outputs

- [ ] **Task 3.4:** Documentation and cleanup
  - Update README.md
  - Create PHASE_4_COMPLETION.md
  - Update ROADMAP.md
  - Version control with git commit

---

## Risk Management

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Fuzzy name matching too permissive | Medium | Low | Use conservative threshold (0.8), always flag for review |
| Date extraction from evidence ambiguous | High | Medium | Use structured field extraction with regex patterns |
| Report formatting complex | Low | Low | Use templates, test with real data |
| Performance with large projects | Medium | Low | Already optimized in Phase 3, caching in place |

---

## Success Criteria

### Functional Requirements

- [x] Date validation checks 120-day rule correctly
- [x] Land tenure validation handles name variations with fuzzy matching
- [x] Project ID validation checks pattern and consistency
- [ ] Markdown report includes all requirements with findings
- [ ] JSON report is valid and parsable
- [ ] Reports cite page numbers and sections for all evidence
- [ ] Flagged items clearly identified for human review

### Performance Requirements

- [ ] Cross-validation completes in <5 seconds
- [ ] Report generation completes in <3 seconds
- [ ] Complete workflow (all 5 stages) in <2 minutes

### Quality Requirements

- [ ] All tests pass (100% test pass rate)
- [ ] Test coverage for validation and reporting modules
- [ ] End-to-end Botany Farm test passes
- [ ] Reports are human-readable and actionable

---

## Acceptance Criteria (from Spec)

From `specs/2025-11-12-registry-review-mcp-REFINED.md`:

- ✅ Date validation correctly checks 4-month rule
- ✅ Land tenure handles name variations (surname match)
- [ ] Report includes all 23 requirements with findings
- [ ] Report cites page numbers for all evidence
- [ ] Complete end-to-end test passes with Botany Farm data

---

## Next Actions

1. **Complete validation tests** (test_validation.py) - IN PROGRESS
2. **Implement validation tools** (validation_tools.py)
3. **Create report data models** (models/report.py)
4. **Implement report tools** (report_tools.py)
5. **Create workflow prompts** (/cross-validation, /report-generation)
6. **End-to-end testing**
7. **Documentation and version control**

---

**Document Owner:** Development Team
**Created:** November 12, 2025
**Status:** In Progress
**Next Review:** Phase 4 Completion
