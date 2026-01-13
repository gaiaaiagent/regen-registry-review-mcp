# Implementation Design: Type-Aware Evidence Extraction

**Date:** 2026-01-12
**Status:** In Progress
**Approach:** Pragmatic Balance

---

## Executive Summary

This document describes the architecture design and implementation approach for fixing the cross-validation bug and adding type-aware evidence extraction to the Registry Review MCP.

**The Core Problem:** Evidence extraction ignores `validation_type` from the checklist, producing only text snippets. Validation then re-extracts structured fields using buggy regex that matches years ("2023") as project IDs and "The Project" as owner names.

**The Solution:** Type-aware extraction that produces structured fields during evidence extraction, eliminating the need for re-extraction during validation.

---

## Architecture Decision: Pragmatic Balance

After evaluating three approaches (Minimal Changes, Clean Architecture, Pragmatic Balance), we chose **Pragmatic Balance** because it:

1. **Fixes the bug properly** (not a band-aid)
2. **Keeps the codebase simple** (no over-abstraction)
3. **Maintains backward compatibility** (existing evidence.json files still work)
4. **Reuses existing infrastructure** (LLM extractors, caching, etc.)

### Why Not the Other Approaches?

| Approach | Rejected Because |
|----------|------------------|
| **Minimal Changes** | Hardcodes requirement ID → extractor mapping. Less flexible. |
| **Clean Architecture** | Strategy Pattern adds unnecessary abstraction for this use case. |

---

## Data Model Changes

### 1. EvidenceSnippet (models/evidence.py)

**New Field Added:**
```python
structured_fields: dict[str, Any] | None = Field(
    None,
    description="Structured fields extracted for cross-validation (owner_name, project_id, dates, etc.)"
)
```

**Purpose:** Store structured data extracted by the LLM alongside the evidence text. For example:
```json
{
  "text": "The farm is owned by Nicholas Denman...",
  "confidence": 0.95,
  "structured_fields": {
    "owner_name": "Nicholas Denman",
    "area_hectares": 100.5,
    "tenure_type": "ownership"
  }
}
```

### 2. RequirementEvidence (models/evidence.py)

**New Field Added:**
```python
validation_type: str = Field(
    "document_presence",
    description="Validation type from checklist: document_presence, cross_document, structured_field, manual"
)
```

**Purpose:** Preserve the validation type from the checklist so validation knows how to process each requirement.

### Backward Compatibility

Both new fields have default values:
- `structured_fields` defaults to `None`
- `validation_type` defaults to `"document_presence"`

This means existing evidence.json files will still deserialize correctly.

---

## Evidence Extraction Changes

### Type-Aware Prompt Builder

**New Function:** `build_type_aware_prompt()`

**Location:** `evidence_tools.py`

**Behavior:**
Based on `validation_type`, builds a prompt that instructs the LLM to extract specific structured fields:

| validation_type | Structured Fields Extracted |
|-----------------|---------------------------|
| `cross_document` (REQ-002) | `owner_name`, `area_hectares`, `tenure_type` |
| `structured_field` (REQ-007) | `project_start_date` |
| `structured_field` (REQ-010) | `crediting_period_years`, `crediting_period_start`, `crediting_period_end` |
| `structured_field` (REQ-012) | `leakage_percentage` |
| `structured_field` (REQ-013) | `permanence_period_years` |
| `structured_field` (REQ-018) | `buffer_pool_percentage` |
| `document_presence` | None (just text snippets) |
| `manual` | None (just text snippets for human review) |

**Key Prompt Improvements:**
- Explicit instructions to extract actual names, not generic text like "The Project"
- Date format specification (YYYY-MM-DD)
- Unit conversion guidance (acres → hectares)

### Updated extract_evidence_with_llm()

**Changes:**
1. New parameter: `validation_type: str = "document_presence"`
2. Uses `build_type_aware_prompt()` instead of hardcoded prompt
3. Parses `structured_fields` from LLM response
4. Cache key includes validation_type suffix for differentiation

### Updated extract_requirement_evidence()

**Changes:**
1. Passes `validation_type` from checklist requirement to extraction function
2. Includes `validation_type` in `RequirementEvidence` result

---

## Validation Changes

### Removal of Regex Fallback

**Deleted Functions:**
- `extract_project_ids_from_evidence()` (lines 353-386) - buggy regex
- `extract_dates_from_evidence()` (lines 388-451) - regex fallback
- `extract_land_tenure_from_evidence()` (lines 453-514) - regex fallback

**Why:** These functions used brittle regex patterns that:
- Matched years (2023, 2024) as project IDs
- Matched generic text ("The Project") as owner names
- Provided false confidence in bad data

### New Helper: extract_structured_fields_from_evidence()

**Purpose:** Extract pre-extracted structured fields from evidence snippets.

**Behavior:**
```python
def extract_structured_fields_from_evidence(evidence_data: dict) -> dict[str, list]:
    """Extract structured fields from evidence snippets (pre-extracted during Stage 4)."""
    dates = []
    tenure_fields = []
    project_ids = []

    for req in evidence_data.get("evidence", []):
        for snippet in req.get("evidence_snippets", []):
            if fields := snippet.get("structured_fields"):
                # Route to appropriate validation category
                # ... (see implementation)

    return {"dates": dates, "tenure": tenure_fields, "project_ids": project_ids}
```

### Updated cross_validate()

**Changes:**
1. First tries to use pre-extracted structured fields from evidence.json
2. If no structured fields found (old evidence.json), falls back to LLM extraction
3. Removes regex fallback entirely - fails explicitly if LLM unavailable

**New Flow:**
```
Load evidence.json
  ↓
Try extract_structured_fields_from_evidence()
  ↓
If sufficient fields found:
  → Use pre-extracted fields (fast path)
Else:
  → Use LLM extraction (extract_fields_with_llm)
  → No regex fallback
  ↓
Run validation checks
```

---

## File Manifest

### Modified Files

| File | Changes | Lines |
|------|---------|-------|
| `models/evidence.py` | Add `structured_fields` to EvidenceSnippet, `validation_type` to RequirementEvidence | +8 |
| `tools/evidence_tools.py` | Add `build_type_aware_prompt()`, update `extract_evidence_with_llm()` | +100 |
| `tools/validation_tools.py` | Delete regex functions, add `extract_structured_fields_from_evidence()`, update `cross_validate()` | -150, +50 |

### No New Files Created

We're modifying existing files, not creating new abstractions.

---

## Data Flow

### Stage 4: Evidence Extraction (Type-Aware)

```
FOR each requirement in checklist:
  validation_type = requirement["validation_type"]

  FOR each mapped document:
    prompt = build_type_aware_prompt(requirement, content, validation_type)

    LLM Response:
    {
      "text": "The farm is owned by Nicholas Denman...",
      "confidence": 0.95,
      "structured_fields": {
        "owner_name": "Nicholas Denman",
        "area_hectares": 100.5
      }
    }

    → EvidenceSnippet with structured_fields populated

  → RequirementEvidence with validation_type preserved

Save to evidence.json
```

### Stage 5: Cross-Validation (No Re-extraction)

```
Load evidence.json

FOR each requirement_evidence:
  IF structured_fields in any snippet:
    → Extract directly (no LLM, no regex)
  ELSE:
    → Use LLM extraction (fallback for old data)

Run validation checks:
  - compare_owner_names() with fuzzy matching
  - compare_project_ids() with pattern validation
  - compare_dates() with tolerance

Save to validation.json
```

---

## Key Design Decisions

### 1. Store Structured Fields on Snippets (Not Separate)

**Decision:** Add `structured_fields` to `EvidenceSnippet` rather than creating a separate model.

**Rationale:**
- Keeps evidence and its structured interpretation together
- Maintains provenance (which snippet produced which fields)
- Simple to serialize/deserialize
- Backward compatible

### 2. Use Type-Aware Prompts (Not Separate Extractors)

**Decision:** Build validation-type-specific prompts rather than calling different extractor classes.

**Rationale:**
- Single LLM call per document (not multiple extractor passes)
- Prompt engineering is more flexible than code changes
- Reuses existing caching infrastructure
- Easier to tune and iterate

### 3. Remove Regex Entirely (Not Improve It)

**Decision:** Delete regex extraction functions rather than fixing the patterns.

**Rationale:**
- Regex is inherently brittle for natural language
- Better to fail explicitly than silently produce bad data
- LLM extraction is more reliable and maintainable
- Removes maintenance burden

### 4. Fallback to LLM (Not Regex)

**Decision:** If pre-extracted fields don't exist, fall back to LLM extraction.

**Rationale:**
- Handles old evidence.json files gracefully
- LLM is reliable; regex is not
- Cost is acceptable (~$0.50 per session)
- Better UX than requiring re-extraction

---

## Testing Strategy

### Unit Tests
- Test `build_type_aware_prompt()` produces correct prompts for each validation_type
- Test `structured_fields` parsing from LLM responses
- Test `extract_structured_fields_from_evidence()` extracts fields correctly

### Integration Tests
- Test full pipeline: extraction → evidence.json → validation
- Test with REQ-002 (land tenure) - should extract owner_name per document
- Test with REQ-007 (project start date) - should extract date

### Regression Tests
- Verify years (2023, 2024) are NOT extracted as project IDs
- Verify "The Project" is NOT extracted as owner_name
- Verify old evidence.json files still work (backward compat)

### Test Command
```bash
# Fast tests only (no expensive API calls)
pytest

# Specific evidence extraction tests
pytest tests/test_evidence_extraction.py -v
```

---

## Implementation Progress

### Completed
- [x] Add `structured_fields` to EvidenceSnippet model
- [x] Add `validation_type` to RequirementEvidence model
- [x] Add `build_type_aware_prompt()` function
- [x] Update `extract_evidence_with_llm()` to accept validation_type
- [x] Update `extract_evidence_with_llm()` to parse structured_fields
- [x] Update call site in `extract_requirement_evidence()` to pass validation_type
- [x] Update `RequirementEvidence` creation to include validation_type
- [x] Remove regex fallback from validation_tools.py (deleted 3 buggy functions)
- [x] Add `extract_structured_fields_from_evidence()` helper
- [x] Update `cross_validate()` to use pre-extracted fields first, LLM fallback second
- [x] Syntax verification passed for all modified files

### Quality Review Fixes (2026-01-12)
- [x] Fix 1: Replace `print(..., file=sys.stderr)` with `logger` pattern
- [x] Fix 2: Correct routing logic (changed `or` to field-based routing)
- [x] Fix 3: Add field merging conflict detection with logging
- [x] Fix 4: Add proper Args/Returns docstrings to `build_type_aware_prompt()`
- [x] Fix 5: Replace hardcoded REQ IDs with field-name-based routing
- [x] Fix 6: Make `build_type_aware_prompt()` config-driven via STRUCTURED_FIELD_CONFIGS
- [x] Fix 7: Add backward compatibility warning for old evidence.json files

### Pending
- [ ] Integration testing with real session data (requires expensive test run)

---

## Risk Assessment

### Low Risk
- Model changes (new optional fields, backward compatible)
- Prompt changes (can iterate without code changes)

### Medium Risk
- Removing regex fallback (must verify LLM extraction works for all cases)
- Cache invalidation (old cache entries won't have structured_fields)

### Mitigations
- Test thoroughly with real session data
- Keep LLM fallback in validation for old evidence.json files
- Cache key includes validation_type suffix to differentiate entries

---

## Success Criteria

1. **Bug Fixed:** Cross-validation no longer produces false positives
2. **Type-Aware Extraction:** Evidence extraction dispatches based on validation_type
3. **Structured Fields:** Pre-extracted fields available in evidence.json
4. **No Regression:** Old sessions still validate correctly
5. **Tests Pass:** `pytest` completes successfully

---

## Appendix: Validation Type Reference

| REQ | Category | validation_type | Structured Fields |
|-----|----------|-----------------|-------------------|
| REQ-001 | General | document_presence | None |
| REQ-002 | Land Tenure | **cross_document** | owner_name, area_hectares, tenure_type |
| REQ-003 | Project Area | document_presence | None |
| REQ-004 | Project Area | document_presence | None |
| REQ-005 | Project Boundary | document_presence | None |
| REQ-006 | Project Ownership | document_presence | None |
| REQ-007 | Project Start Date | **structured_field** | project_start_date |
| REQ-008 | Ecosystem Type | document_presence | None |
| REQ-009 | Ecosystem Type | document_presence | None |
| REQ-010 | Crediting Period | **structured_field** | crediting_period_years, start, end |
| REQ-011 | GHG Accounting | document_presence | None |
| REQ-012 | GHG Accounting | **structured_field** | leakage_percentage |
| REQ-013 | GHG Accounting | **structured_field** | permanence_period_years |
| REQ-014 | Regulatory Compliance | document_presence | None |
| REQ-015 | Registration | document_presence | None |
| REQ-016 | Project Plan Deviations | **manual** | None (human review) |
| REQ-017 | Monitoring Plan | document_presence | None |
| REQ-018 | Risk Management | **structured_field** | buffer_pool_percentage |
| REQ-019-023 | Safeguards | document_presence | None |
