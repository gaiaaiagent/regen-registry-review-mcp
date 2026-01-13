# Cross-Validation Architecture Redesign

**Date**: January 12, 2026
**Status**: Implementation In Progress

## Problem Statement

Cross-validation (Stage E) returns "0 automated validations" because:

1. **Field Name Mismatch**: LLM extracts arbitrary names (`project_identifier`) but code expects exact names (`project_id`)
2. **Single Document Trap**: All structured fields come from ONE document, but cross-validation requires 2+ documents
3. **No Sanity Checks**: System only does cross-document comparison, nothing for single-document cases

## User Requirements (from interactive clarification)

| Decision | Choice |
|----------|--------|
| Sanity checks | Rule-based checks FIRST, then ONE LLM synthesis call |
| LLM context | Full: fields + snippets + methodology requirements |
| Failure mode | Flag for human review (not hard fail) |
| Field names | Strict enforcement in Stage D prompts |

## Chosen Architecture: Three-Layer Validation

```
┌─────────────────────────────────────────────────────────────┐
│         Stage E: Validation (NEW DESIGN)                     │
│                                                               │
│  Layer 1: Structural Validation (Rule-Based) - ALWAYS RUNS   │
│  ├─ Required field presence checks                           │
│  ├─ Format validation (dates, IDs, percentages)              │
│  ├─ Range checks (dates reasonable, % in 0-100)              │
│  └─ Internal consistency (period_end > period_start)         │
│                                                               │
│  Layer 2: Cross-Document Validation - CONDITIONAL            │
│  ├─ Only runs if 2+ documents with same field                │
│  ├─ Date alignment (project_start vs baseline)               │
│  ├─ Tenure consistency (owner names, areas)                  │
│  └─ ID consistency (same project_id everywhere)              │
│                                                               │
│  Layer 3: LLM Synthesis - SINGLE CALL                        │
│  ├─ Full context: all fields + snippets + checklist          │
│  ├─ Holistic coherence check                                 │
│  ├─ Methodology-specific requirements                        │
│  └─ Flag suspicious patterns for human review                │
└─────────────────────────────────────────────────────────────┘
```

## Module Structure

```
src/registry_review_mcp/validation/
├── __init__.py          # Public API
├── structural.py        # Layer 1: Rule-based checks
├── cross_document.py    # Layer 2: Multi-document comparison
├── llm_synthesis.py     # Layer 3: Single LLM coherence check
└── coordinator.py       # Orchestrates all layers
```

## Implementation Plan

### File 1: structural.py (~200 lines)

**Purpose**: Rule-based checks that work with ANY number of documents

**Key Functions**:
```python
def check_required_fields(fields: dict, required: list[str]) -> list[CheckResult]
def check_field_formats(fields: dict) -> list[CheckResult]
def check_field_ranges(fields: dict) -> list[CheckResult]
def check_internal_consistency(fields: dict) -> list[CheckResult]
def run_structural_checks(evidence_data: dict) -> StructuralValidationResult
```

**Checks to implement**:
- Required fields: `owner_name`, `project_start_date`, `project_id`
- Format validation: dates parse as ISO, project_id matches `C##-####` pattern
- Range checks: dates not in future, percentages 0-100, areas positive
- Consistency: `crediting_period_end > crediting_period_start`
- Generic name detection: flag "The Project", "The Farm" as owner names

### File 2: cross_document.py (~150 lines)

**Purpose**: Compare values across documents (when 2+ available)

**Key Functions**:
```python
def check_date_alignment(dates: list[dict]) -> list[CheckResult]
def check_tenure_consistency(tenure_fields: list[dict]) -> list[CheckResult]
def check_project_id_consistency(project_ids: list[dict]) -> list[CheckResult]
def run_cross_document_checks(evidence_data: dict) -> CrossDocumentValidationResult
```

**Logic**:
- Group fields by document
- Only run checks if 2+ documents have the same field type
- Return empty list (not failure) if insufficient documents

### File 3: llm_synthesis.py (~100 lines)

**Purpose**: Single LLM call for holistic assessment

**Key Functions**:
```python
async def run_llm_synthesis(
    all_fields: dict,
    evidence_snippets: list[dict],
    methodology_requirements: list[dict],
    structural_results: StructuralValidationResult,
    cross_doc_results: CrossDocumentValidationResult
) -> LLMSynthesisResult
```

**Prompt Design**:
- Include all extracted fields with sources
- Include relevant evidence snippets (truncated)
- Include methodology requirements from checklist
- Include structural/cross-doc check results as context
- Ask for: coherence score, compliance status, flags for human review

### File 4: coordinator.py (~150 lines)

**Purpose**: Orchestrate all layers

**Key Functions**:
```python
async def validate_session(session_id: str) -> ValidationResult
```

**Flow**:
1. Load evidence.json
2. Extract all structured fields
3. Run Layer 1: Structural checks (always)
4. Run Layer 2: Cross-document checks (conditional)
5. Run Layer 3: LLM synthesis (if enabled)
6. Aggregate results into ValidationResult
7. Save validation.json

### Additional Changes

**evidence_tools.py** (modify ~30 lines):
- Strengthen `_build_structured_guidance()` to enforce exact field names
- Add JSON examples with canonical names
- Add "DO NOT use synonyms" instruction

**validation_tools.py** (add ~10 lines):
- Add backward-compatible wrapper that calls new coordinator
- Deprecation notice on old `cross_validate()` function

**models/validation.py** (add ~80 lines):
- New dataclasses: `CheckResult`, `StructuralValidationResult`, `CrossDocumentValidationResult`, `LLMSynthesisResult`
- Updated `ValidationResult` to include all three layers

## Data Models

```python
@dataclass
class CheckResult:
    check_id: str
    check_type: str  # "required", "format", "range", "consistency", "cross_doc"
    field_name: str
    status: str  # "pass", "warning", "fail"
    message: str
    source: str | None = None  # Document name
    flagged_for_review: bool = False

@dataclass
class StructuralValidationResult:
    checks: list[CheckResult]
    total_checks: int
    passed: int
    warnings: int
    failed: int

@dataclass
class CrossDocumentValidationResult:
    checks: list[CheckResult]
    documents_compared: int
    sufficient_data: bool  # False if <2 documents

@dataclass
class LLMSynthesisResult:
    available: bool  # False if LLM not configured
    coherence_score: float | None  # 0.0-1.0
    compliance_status: str | None  # "compliant", "partial", "non_compliant"
    flags_for_review: list[str]
    reasoning: str | None

@dataclass
class ValidationResult:
    session_id: str
    validated_at: datetime
    structural: StructuralValidationResult
    cross_document: CrossDocumentValidationResult
    llm_synthesis: LLMSynthesisResult
    summary: ValidationSummary
    # Backward compat (deprecated)
    date_alignments: list[dict] = field(default_factory=list)
    land_tenure: list[dict] = field(default_factory=list)
    project_ids: list[dict] = field(default_factory=list)
```

## Canonical Field Names (enforce in Stage D)

```python
CANONICAL_FIELDS = {
    # Land Tenure
    "owner_name": "Full name of landowner (NOT 'The Project')",
    "area_hectares": "Total area in hectares (numeric)",
    "tenure_type": "One of: ownership, lease, easement",

    # Project Identity
    "project_id": "Project identifier (format: C##-#### or similar)",
    "project_name": "Full project name",

    # Dates
    "project_start_date": "YYYY-MM-DD format",
    "crediting_period_start": "YYYY-MM-DD format",
    "crediting_period_end": "YYYY-MM-DD format",
    "baseline_date": "YYYY-MM-DD format",

    # Periods
    "crediting_period_years": "Integer, typically 10",
    "permanence_period_years": "Integer, typically 10",

    # Percentages
    "buffer_pool_percentage": "Numeric, typically ~20",
    "leakage_percentage": "Numeric threshold",
}
```

## Test Strategy

**Unit Tests** (`tests/test_validation_layers.py`):
- Test each structural check independently
- Test cross-document checks with mock data
- Test LLM synthesis prompt construction
- Test coordinator flow

**Integration Tests**:
- Run full workflow with single document → verify structural checks fire
- Run with multiple documents → verify cross-document checks fire
- Verify backward compatibility with old validation.json format

**Regression Tests**:
- "The Project" as owner_name → flagged
- "2023" as project_id → flagged
- Future dates → flagged

## Success Criteria

1. Single-document sessions get `total_validations > 0`
2. No false positives on valid data (Nick Denman, 2022-01-01)
3. Catches known bad patterns (The Project, 2023)
4. LLM synthesis provides useful flags for human review
5. All existing tests pass
6. GPT shows meaningful validation results

## Estimated Effort

| Component | Lines | Time |
|-----------|-------|------|
| structural.py | ~200 | 45 min |
| cross_document.py | ~150 | 30 min |
| llm_synthesis.py | ~100 | 30 min |
| coordinator.py | ~150 | 30 min |
| evidence_tools.py updates | ~30 | 15 min |
| models/validation.py updates | ~80 | 15 min |
| validation_tools.py wrapper | ~10 | 5 min |
| Tests | ~300 | 60 min |
| **Total** | **~1020** | **~4 hours** |

## Context from Codebase Exploration

### Key Files Analyzed

1. **evidence_tools.py**:
   - `STRUCTURED_FIELD_CONFIGS` at lines 36-79
   - `_build_structured_guidance()` at lines 91-108
   - LLM extraction at lines 350-474

2. **validation_tools.py**:
   - `extract_structured_fields_from_evidence()` at lines 357-459
   - `cross_validate()` at lines 462-743
   - Field routing uses `TENURE_FIELDS`, `DATE_FIELDS`

3. **soil-carbon-v1.2.2.json**:
   - 23 requirements
   - 16 `document_presence`, 6 `structured_field`, 1 `cross_document`, 1 `manual`

### Evidence Analysis (Current Session)

From `session-60eb2a27be78`:
- 131 total evidence snippets
- Only 20 have `structured_fields` (15%)
- All structured fields from same document (`4997Botany22_Public_Project_Plan.pdf`)
- Field name examples extracted: `project_identifier` (not `project_id`), `permanence_period_years`, `owner_name`

### Root Cause Confirmed

The LLM extracted `project_identifier` but validation code looks for `project_id`. Field names are not enforced, causing silent routing failures.
