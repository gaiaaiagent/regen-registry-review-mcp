---
id: task-34
title: Evidence matrix and validation reliability overhaul
status: Done
assignee: []
created_date: '2025-12-04'
updated_date: '2025-12-04'
labels:
  - reliability
  - ux
  - data-quality
  - high
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Investigation revealed critical gaps between what the system displays and what it actually validates. ChatGPT is inventing data when asked to show matrices because the API doesn't provide complete, structured responses.

### Root Cause Analysis

#### Issue 1: Cross-Validation Runs Zero Checks

From `validation.json` for a "completed" session:
```json
{
    "total_validations": 0,
    "validations_passed": 0,
    "pass_rate": 0.0,
    "extraction_method": "llm"
}
```

The system says "all good" but ran **zero actual validations**. This happens because:

1. `cross_validate()` attempts LLM extraction for dates, tenure, project IDs
2. LLM extraction returns insufficient or empty data
3. Without extractable fields, no validation checks run
4. "pass_rate: 0.0" is interpreted as "no failures" rather than "nothing checked"

**Impact**: Users think their documents passed validation when nothing was actually checked.

#### Issue 2: ChatGPT Invents Matrix Data

When user asked "Can you show me a matrix", ChatGPT fabricated:
- A table with 23 requirements categorized as "Auto-Validated" vs "Manual Review Needed"
- 5 "safeguard" requirements marked as needing manual review
- Citations that don't match actual evidence.json data

**Root cause**: The API returns raw data without a structured matrix view. ChatGPT fills the gap with hallucinated content based on its training data.

#### Issue 3: Evidence Data Exists But Isn't Displayed

The `evidence.json` DOES contain proper citations:
```json
{
  "text": "Credit Class Name: GHG Benefits...",
  "document_id": "DOC-f35bd7ab",
  "document_name": "4997Botany22 Public Project Plan.pdf",
  "page": 3,
  "section": "1.3. Credit Class and Methodology",
  "confidence": 0.95
}
```

But no endpoint returns this as a **standardized evidence matrix** with columns:
- Requirement ID
- Source Document
- Page Number
- Evidence Text
- Confidence Score
- Validation Status

#### Issue 4: No Requirement Classification

Requirements aren't classified by validation type:
- **Auto-validatable**: dates, project IDs, tenure (cross-document consistency checks)
- **Human-judgment**: safeguards, stakeholder consultation, risk assessment

Without this classification, the system can't report which requirements were machine-checked vs which need human review.

### Proposed Solutions

#### Solution 1: Create Evidence Matrix Endpoint

Add `/sessions/{session_id}/evidence-matrix` that returns:

```json
{
  "session_id": "session-xxx",
  "matrix": [
    {
      "requirement_id": "REQ-001",
      "category": "General",
      "description": "Latest methodology version applied",
      "evidence": [
        {
          "source_document": "4997Botany22 Public Project Plan.pdf",
          "page": 3,
          "text": "Methodology Version: 1.1",
          "confidence": 0.95
        }
      ],
      "validation_type": "auto",
      "validation_status": "passed",
      "human_review_required": false
    }
  ],
  "summary": {
    "total_requirements": 23,
    "auto_validated": 18,
    "pending_human_review": 5,
    "coverage": 1.0
  }
}
```

This gives ChatGPT structured data it can display directly without inventing content.

#### Solution 2: Add Requirement Classification to Checklist

Extend checklist schema:
```json
{
  "requirement_id": "REQ-019",
  "category": "Safeguards",
  "validation_type": "human_judgment",
  "auto_validatable": false,
  "cross_validate_fields": []
}
```

vs:
```json
{
  "requirement_id": "REQ-002",
  "category": "Land Tenure",
  "validation_type": "auto",
  "auto_validatable": true,
  "cross_validate_fields": ["owner_name", "area_hectares", "tenure_type"]
}
```

#### Solution 3: Fix Cross-Validation Empty Results

When `total_validations: 0`, the system should:
1. Report which requirements COULD NOT be auto-validated
2. Explain WHY (missing structured data)
3. Route those to human review queue

Change validation summary from:
```
"Pass rate: 100% (no flags)"
```

To:
```
"Checked: 5/23 requirements (auto-validatable)
 Passed: 5/5 (100%)
 Pending human review: 18/23 (qualitative requirements)"
```

#### Solution 4: Standardize Data Matrix Responses

All matrix/table endpoints should include these columns:
1. **Identifier** (requirement_id, document_id)
2. **Description** (brief text)
3. **Source** (document name)
4. **Page** (page number)
5. **Status** (passed/failed/pending)
6. **Confidence** (0.0-1.0)

This prevents ChatGPT from inventing its own column structure.

### Workflow Improvements

**Current workflow has redundancy and gaps**:

1. Evidence Extraction → extracts text with page/document citations ✓
2. Cross-Validation → attempts to extract SAME fields again, fails silently ✗
3. Report Generation → uses evidence.json data ✓
4. Human Review → has no structured view of what needs review ✗

**Proposed streamlined workflow**:

1. Evidence Extraction → extracts text AND structured fields (dates, IDs, tenure)
2. Cross-Validation → uses pre-extracted structured fields, reports what couldn't be checked
3. Evidence Matrix → shows all requirements with citations and validation status
4. Human Review → shows only requirements requiring judgment, with evidence summary

### Acceptance Criteria

- [x] `/evidence-matrix` endpoint returns structured matrix with standard columns
- [x] Requirements checklist includes `validation_type` classification
- [x] Cross-validation reports what it DID check vs what it COULDN'T check
- [x] Zero-validation cases are clearly flagged (not silent "success")
- [x] All matrix views include: source document, page, description, status
- [x] ChatGPT displays actual API data, not invented content (GPT instructions updated)

### Implementation Notes (2025-12-04)

1. **API Enhancement**: Added `extracted_value` and `section` fields to `/evidence-matrix` endpoint
2. **GPT Instructions**: Created `docs/specs/2025-12-03-gpt4.md` with:
   - Explicit endpoint routing: "evidence matrix" → `/evidence-matrix`
   - 8-column matrix format specification
   - "NEVER omit ANY columns" rule
   - API field-to-column mapping
3. **Commit**: `77c2152` - Add extracted_value to evidence-matrix API and update GPT instructions
<!-- SECTION:DESCRIPTION:END -->
