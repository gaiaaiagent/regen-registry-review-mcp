# Systemic Architectural Audit: Mapping → Extraction → Validation

**Date:** 2026-01-12
**Purpose:** Deep analysis of the three core phases and a specification for how they should work together

---

## Executive Summary

The current implementation has a fundamental architectural flaw: **the three phases are disconnected and work against each other** instead of forming a coherent pipeline.

| Phase | Current | Should Be |
|-------|---------|-----------|
| **Mapping** | Category keyword matching | Semantic LLM-based document relevance |
| **Extraction** | Generic text snippets for all requirements | Type-aware extraction based on `validation_type` |
| **Validation** | Re-extracts structured fields from snippets | Validates pre-extracted structured data |

The root cause: **Evidence extraction ignores `validation_type`** and produces only text blobs. Validation then has to re-extract structured fields from those blobs, losing context and introducing errors.

---

## Part 1: Understanding the Domain

### What Is This System For?

A reviewer needs to verify that a carbon credit project meets 23 methodology requirements. For each requirement, they need:

1. **Evidence** that the requirement is satisfied
2. **Confidence** that the evidence is valid
3. **Cross-checks** that evidence is consistent across documents

### The Checklist Is the Contract

The checklist (`data/checklists/soil-carbon-v1.2.2.json`) defines each requirement with:

```json
{
  "requirement_id": "REQ-007",
  "category": "Project Start Date",
  "requirement_text": "Project must stipulate the Project Start Date...",
  "source": "Program Guide, Section 8.6",
  "accepted_evidence": "Explicit mention of the name, start date, and duration",
  "mandatory": true,
  "validation_type": "structured_field"  // <-- THIS IS THE KEY
}
```

**The `validation_type` tells us exactly what kind of evidence is needed:**

| validation_type | What It Means | Example Requirements |
|-----------------|---------------|---------------------|
| `document_presence` | Just need to find evidence exists | REQ-003 (land not converted), REQ-005 (project boundary) |
| `cross_document` | Need consistent values across docs | REQ-002 (land tenure consistent) |
| `structured_field` | Need specific typed values | REQ-007 (project start date), REQ-010 (crediting period) |
| `manual` | Requires human judgment | REQ-016 (project plan deviations) |

**This should drive the entire extraction strategy.**

---

## Part 2: Current Architecture Analysis

### Phase 1: Requirements Mapping (`mapping_tools.py`)

**Current Implementation:**
```python
def _infer_document_types(category: str, accepted_evidence: str) -> list[str]:
    # Hardcoded category → document type mapping
    type_mapping = {
        "land tenure": ["land-tenure", "legal-document", "project-plan"],
        "baseline": ["baseline-report", "project-plan"],
        ...
    }
    # Returns list of document classifications to look for
```

**Problems:**
1. **No semantic understanding** — Pure string matching on category names
2. **Doesn't use LLM** — Misses nuanced relevance
3. **Hardcoded mappings** — Can't adapt to documents with non-standard names
4. **Ignores `validation_type`** — Treats all requirements the same
5. **Confidence is arbitrary** — 0.85 for single match, 0.75 for multiple

**Result:** Mapping works okay for well-structured projects but fails when:
- Documents are named unusually
- Multiple documents contain overlapping information
- A document contains evidence for requirements in different categories

### Phase 2: Evidence Extraction (`evidence_tools.py`)

**Current Implementation:**
```python
async def extract_evidence_with_llm(client, requirement, document_content, ...):
    prompt = f"""Extract ALL passages that provide evidence for this requirement...

    Return JSON array:
    [
      {{
        "text": "The farm is owned by John Smith...",
        "page": 5,
        "confidence": 0.95,
        "reasoning": "Provides owner name..."
      }}
    ]
    """
    # Returns: list[EvidenceSnippet]
```

**Problems:**
1. **One-size-fits-all extraction** — Same prompt for all requirements regardless of `validation_type`
2. **Only extracts text snippets** — No structured fields (dates, names, IDs)
3. **Doesn't prepare for validation** — cross_document requirements get the same treatment as document_presence
4. **Field boundaries are lost** — Snippet contains "John Smith" but no way to know that's the owner_name field

**What Should Happen:**
- For `structured_field`: Extract the actual typed value (date, percentage)
- For `cross_document`: Extract comparable values from each document
- For `document_presence`: Extract evidence snippet (current behavior)

### Phase 3: Cross-Validation (`validation_tools.py`)

**Current Implementation:**
```python
async def cross_validate(session_id: str):
    # Load evidence.json (text snippets)
    evidence_data = state_manager.read_json("evidence.json")

    # Try LLM extraction from snippets
    if settings.llm_extraction_enabled:
        raw_fields = await extract_fields_with_llm(session_id, evidence_data)
    else:
        # Regex fallback
        project_ids = extract_project_ids_from_evidence(evidence_data)  # BROKEN
        tenure_fields = extract_land_tenure_from_evidence(evidence_data)  # BROKEN
```

**Problems:**
1. **Re-extracts from snippets** — Wastes tokens and loses context
2. **Regex fallback is garbage** — Matches years as project IDs, "The Project" as owner names
3. **Hardcoded requirement IDs** — Only checks REQ-002, REQ-007, etc.
4. **Works on snippets, not documents** — Lost context leads to false positives

**The Critical Bug:**
```python
# validation_tools.py line 366
id_pattern = re.compile(r'\b(\d{4})\b|C\d{2}-(\d{4})')
# Matches any 4-digit number including years like 2023!

# validation_tools.py line 477
owner_patterns = [
    r'([A-Z][a-z]+\s+[A-Z][a-z]+).*(?:owner|steward)',
]
# Matches "The Project" because it's two capitalized words before "owner"
```

### The LLM Extractors (`llm_extractors.py`)

**Current Implementation:**

Three well-designed extractors exist:
- `DateExtractor` — Extracts 8 date types with context
- `LandTenureExtractor` — Extracts owner names with fuzzy matching
- `ProjectIDExtractor` — Extracts IDs with false positive filtering

**Problems:**
1. **Called too late** — Only used in validation, not evidence extraction
2. **Extracts from snippets** — By validation time, we only have snippets, not full documents
3. **Not integrated with main flow** — Duplicated extraction logic

**What's Good:**
- Prompts are well-designed with clear instructions
- Has filtering for false positives (years, filenames)
- Uses fuzzy matching for name variations
- Includes prompt caching for efficiency

---

## Part 3: The Ideal Architecture

### Core Principle: Type-Aware Extraction

The `validation_type` should drive everything:

```
┌─────────────────────────────────────────────────────────────────┐
│                  CHECKLIST REQUIREMENT                          │
│  validation_type: document_presence | cross_document |          │
│                   structured_field | manual                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 1: SEMANTIC MAPPING                      │
│                                                                 │
│  Input: requirement + all documents                             │
│  Process: LLM determines which documents are relevant           │
│  Output: RequirementMapping {                                   │
│    requirement_id,                                              │
│    validation_type,           // Preserved from checklist       │
│    mapped_documents: [{                                         │
│      document_id,                                               │
│      relevance_score,                                           │
│      relevance_reasoning      // Why this doc is relevant       │
│    }]                                                           │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 2: TYPE-AWARE EXTRACTION                 │
│                                                                 │
│  For each (requirement, mapped_documents):                      │
│                                                                 │
│  SWITCH on validation_type:                                     │
│                                                                 │
│  ┌─ document_presence ─────────────────────────────────────┐    │
│  │  → Extract evidence snippet proving requirement met     │    │
│  │  → Output: PresenceEvidence {                           │    │
│  │      snippet: "The property was...",                    │    │
│  │      source: {document_id, page, section},              │    │
│  │      confidence: 0.95                                   │    │
│  │    }                                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ structured_field ──────────────────────────────────────┐    │
│  │  → Extract the specific typed value                     │    │
│  │  → Output: StructuredEvidence {                         │    │
│  │      field_type: "project_start_date",                  │    │
│  │      value: "2022-01-15",           // Typed!           │    │
│  │      raw_text: "Project Start: January 15, 2022",       │    │
│  │      source: {document_id, page, section},              │    │
│  │      confidence: 0.95                                   │    │
│  │    }                                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ cross_document ────────────────────────────────────────┐    │
│  │  → Extract comparable values from EACH mapped document  │    │
│  │  → Output: CrossDocumentEvidence {                      │    │
│  │      field_type: "owner_name",                          │    │
│  │      values: [                                          │    │
│  │        {document_id: "DOC-001", value: "Nicholas Denman",│    │
│  │         source: {page: 1}, confidence: 1.0},            │    │
│  │        {document_id: "DOC-002", value: "Nick Denman",   │    │
│  │         source: {page: 3}, confidence: 0.9}             │    │
│  │      ]                                                  │    │
│  │    }                                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─ manual ────────────────────────────────────────────────┐    │
│  │  → Extract relevant context for human review            │    │
│  │  → Output: HumanReviewEvidence {                        │    │
│  │      context_snippets: [...],                           │    │
│  │      review_question: "Does this deviation meet...?"    │    │
│  │    }                                                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 3: VALIDATION                            │
│                                                                 │
│  For cross_document requirements:                               │
│    → Compare extracted values (already typed!)                  │
│    → Apply fuzzy matching for names                             │
│    → Apply date tolerance (±120 days)                           │
│    → Output: ValidationResult(pass/fail/warning)                │
│                                                                 │
│  For structured_field requirements:                             │
│    → Validate extracted value against schema                    │
│    → Check date format, ID pattern, numeric ranges              │
│    → Output: ValidationResult(pass/fail/warning)                │
│                                                                 │
│  For document_presence requirements:                            │
│    → Verify evidence exists with sufficient confidence          │
│    → Output: ValidationResult(pass/fail based on confidence)    │
│                                                                 │
│  NO RE-EXTRACTION NEEDED — structured data already available    │
└─────────────────────────────────────────────────────────────────┘
```

### Unified Evidence Model

```python
# models/evidence.py (redesigned)

class EvidenceBase(BaseModel):
    """Base class for all evidence types."""
    requirement_id: str
    status: Literal["found", "partial", "not_found"]
    confidence: ConfidenceScore
    extraction_method: str  # "semantic", "structured", "manual"


class PresenceEvidence(EvidenceBase):
    """Evidence for document_presence requirements."""
    snippet: str
    source: EvidenceSource  # {document_id, page, section}


class StructuredEvidence(EvidenceBase):
    """Evidence for structured_field requirements."""
    field_type: str  # "project_start_date", "crediting_period", "buffer_pool_percentage"
    value: Any  # The typed value (date, int, float, str)
    raw_text: str  # Original text it was extracted from
    source: EvidenceSource


class DocumentValue(BaseModel):
    """A single value extracted from one document (for cross-document comparison)."""
    document_id: str
    document_name: str
    value: Any
    raw_text: str
    source: EvidenceSource
    confidence: ConfidenceScore


class CrossDocumentEvidence(EvidenceBase):
    """Evidence for cross_document requirements."""
    field_type: str  # "owner_name", "project_id", "area_hectares"
    values: list[DocumentValue]  # One per document, ready for comparison

    @property
    def is_consistent(self) -> bool:
        """Quick check if all values match."""
        unique_values = set(v.value for v in self.values)
        return len(unique_values) == 1


class HumanReviewEvidence(EvidenceBase):
    """Evidence for manual requirements."""
    context_snippets: list[EvidenceSnippet]
    review_question: str
    suggested_answer: str | None = None


# Union type for polymorphic handling
Evidence = PresenceEvidence | StructuredEvidence | CrossDocumentEvidence | HumanReviewEvidence


class RequirementEvidence(BaseModel):
    """Complete evidence record for a requirement."""
    requirement_id: str
    validation_type: str  # Preserved from checklist
    evidence: Evidence  # Polymorphic based on validation_type
    extracted_at: datetime
```

### Type-Aware Extraction Implementation

```python
# evidence_tools.py (redesigned)

async def extract_evidence_for_requirement(
    requirement: dict,
    mapped_documents: list[dict],
    doc_cache: dict[str, str],  # document_id -> markdown content
) -> RequirementEvidence:
    """Extract evidence based on requirement's validation_type."""

    validation_type = requirement.get("validation_type", "document_presence")

    if validation_type == "document_presence":
        return await extract_presence_evidence(requirement, mapped_documents, doc_cache)

    elif validation_type == "structured_field":
        return await extract_structured_evidence(requirement, mapped_documents, doc_cache)

    elif validation_type == "cross_document":
        return await extract_cross_document_evidence(requirement, mapped_documents, doc_cache)

    elif validation_type == "manual":
        return await extract_human_review_evidence(requirement, mapped_documents, doc_cache)

    else:
        raise ValueError(f"Unknown validation_type: {validation_type}")


async def extract_structured_evidence(
    requirement: dict,
    mapped_documents: list[dict],
    doc_cache: dict[str, str],
) -> RequirementEvidence:
    """Extract a specific typed field value."""

    # Determine what field to extract based on requirement
    field_type = infer_field_type(requirement)
    # e.g., REQ-007 → "project_start_date"
    # e.g., REQ-010 → "crediting_period_years"
    # e.g., REQ-012 → "leakage_percentage"

    # Use specialized extractor
    if field_type.endswith("_date"):
        extractor = DateExtractor()
    elif field_type in ["owner_name", "area_hectares", "tenure_type"]:
        extractor = LandTenureExtractor()
    elif field_type == "project_id":
        extractor = ProjectIDExtractor()
    else:
        extractor = GenericFieldExtractor(field_type)

    # Extract from best document
    best_result = None
    for doc in mapped_documents:
        content = doc_cache.get(doc["document_id"])
        if not content:
            continue

        fields = await extractor.extract(content, [], doc["document_name"])

        # Find field matching our target type
        for field in fields:
            if field.field_type == field_type:
                if best_result is None or field.confidence > best_result.confidence:
                    best_result = field

    if best_result:
        return RequirementEvidence(
            requirement_id=requirement["requirement_id"],
            validation_type="structured_field",
            evidence=StructuredEvidence(
                requirement_id=requirement["requirement_id"],
                status="found",
                confidence=best_result.confidence,
                extraction_method="structured",
                field_type=field_type,
                value=best_result.value,
                raw_text=best_result.raw_text,
                source=EvidenceSource(
                    document_id=doc["document_id"],
                    page=extract_page(best_result.source),
                    section=extract_section(best_result.source),
                )
            ),
            extracted_at=datetime.now()
        )
    else:
        return RequirementEvidence(
            requirement_id=requirement["requirement_id"],
            validation_type="structured_field",
            evidence=StructuredEvidence(
                requirement_id=requirement["requirement_id"],
                status="not_found",
                confidence=0.0,
                extraction_method="structured",
                field_type=field_type,
                value=None,
                raw_text="",
                source=None
            ),
            extracted_at=datetime.now()
        )


async def extract_cross_document_evidence(
    requirement: dict,
    mapped_documents: list[dict],
    doc_cache: dict[str, str],
) -> RequirementEvidence:
    """Extract comparable values from ALL mapped documents."""

    field_type = infer_field_type(requirement)
    # e.g., REQ-002 → "owner_name" (land tenure)

    extractor = get_extractor_for_field(field_type)

    # Extract from EVERY mapped document
    values = []
    for doc in mapped_documents:
        content = doc_cache.get(doc["document_id"])
        if not content:
            continue

        fields = await extractor.extract(content, [], doc["document_name"])

        for field in fields:
            if field.field_type == field_type:
                values.append(DocumentValue(
                    document_id=doc["document_id"],
                    document_name=doc["document_name"],
                    value=field.value,
                    raw_text=field.raw_text or "",
                    source=EvidenceSource(
                        document_id=doc["document_id"],
                        page=extract_page(field.source),
                        section=extract_section(field.source),
                    ),
                    confidence=field.confidence
                ))

    # Determine status based on what we found
    if len(values) >= 2:
        status = "found"
    elif len(values) == 1:
        status = "partial"  # Need multiple docs for cross-validation
    else:
        status = "not_found"

    return RequirementEvidence(
        requirement_id=requirement["requirement_id"],
        validation_type="cross_document",
        evidence=CrossDocumentEvidence(
            requirement_id=requirement["requirement_id"],
            status=status,
            confidence=max((v.confidence for v in values), default=0.0),
            extraction_method="cross_document",
            field_type=field_type,
            values=values
        ),
        extracted_at=datetime.now()
    )
```

### Simplified Validation

```python
# validation_tools.py (redesigned)

async def cross_validate(session_id: str) -> ValidationResult:
    """Validate extracted evidence — NO RE-EXTRACTION."""

    evidence_data = state_manager.read_json("evidence.json")

    validation_results = []

    for req_evidence in evidence_data["evidence"]:
        validation_type = req_evidence["validation_type"]
        evidence = req_evidence["evidence"]

        if validation_type == "cross_document":
            # Evidence already has values from each document
            result = validate_cross_document(
                requirement_id=req_evidence["requirement_id"],
                field_type=evidence["field_type"],
                values=evidence["values"]  # Already extracted!
            )
            validation_results.append(result)

        elif validation_type == "structured_field":
            # Validate the extracted value against schema
            result = validate_structured_field(
                requirement_id=req_evidence["requirement_id"],
                field_type=evidence["field_type"],
                value=evidence["value"]  # Already extracted!
            )
            validation_results.append(result)

        # document_presence and manual don't need cross-validation

    return ValidationResult(
        session_id=session_id,
        validations=validation_results,
        summary=calculate_summary(validation_results)
    )


def validate_cross_document(
    requirement_id: str,
    field_type: str,
    values: list[DocumentValue]
) -> CrossValidationResult:
    """Compare values across documents."""

    if len(values) < 2:
        return CrossValidationResult(
            requirement_id=requirement_id,
            status="warning",
            message=f"Only {len(values)} document(s) contain {field_type}"
        )

    # Use field-specific comparison
    if field_type == "owner_name":
        return compare_owner_names(values)
    elif field_type == "project_id":
        return compare_project_ids(values)
    elif field_type == "area_hectares":
        return compare_areas(values, tolerance=0.05)  # 5% tolerance
    elif field_type.endswith("_date"):
        return compare_dates(values, max_delta_days=120)
    else:
        return compare_exact(values)


def compare_owner_names(values: list[DocumentValue]) -> CrossValidationResult:
    """Compare owner names with fuzzy matching."""

    names = [v.value for v in values]

    # Check all pairs for similarity
    min_similarity = 1.0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            sim = fuzz.token_set_ratio(names[i].lower(), names[j].lower()) / 100.0
            min_similarity = min(min_similarity, sim)

    if min_similarity >= 0.80:
        return CrossValidationResult(
            status="pass",
            message=f"Owner names consistent ({min_similarity:.0%} similarity)"
        )
    elif min_similarity >= 0.60:
        return CrossValidationResult(
            status="warning",
            message=f"Owner names similar but not identical ({min_similarity:.0%})"
        )
    else:
        return CrossValidationResult(
            status="fail",
            message=f"Owner names differ: {', '.join(names)}"
        )
```

---

## Part 4: Migration Path

### Step 1: Fix Immediate Bugs (Quick Win)

Before redesigning, fix the regex fallback that's causing false positives:

```python
# validation_tools.py - line 366
# BEFORE: r'\b(\d{4})\b|C\d{2}-(\d{4})'
# AFTER: Only match known patterns, exclude years
id_pattern = re.compile(r'C\d{2}-\d+|VCS-?\d+|GS-?\d+')

# validation_tools.py - line 477
# BEFORE: r'([A-Z][a-z]+\s+[A-Z][a-z]+).*(?:owner|steward)'
# AFTER: Require explicit prefix
owner_patterns = [
    r'(?:landowner|owner|steward)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
]
```

### Step 2: Add validation_type to Evidence Model

Update `models/evidence.py` to preserve validation_type:

```python
class RequirementEvidence(BaseModel):
    requirement_id: str
    validation_type: str  # NEW: preserve from checklist
    # ... rest unchanged
```

### Step 3: Type-Aware Extraction in evidence_tools.py

Modify `extract_evidence_with_llm` to handle different types:

```python
async def extract_evidence_with_llm(client, requirement, document_content, ...):
    validation_type = requirement.get("validation_type", "document_presence")

    if validation_type == "structured_field":
        # Use specialized extractor to get typed value
        return await extract_structured_field_evidence(...)

    elif validation_type == "cross_document":
        # Extract value for later comparison
        return await extract_cross_document_value(...)

    else:
        # Default: extract text snippet
        return await extract_presence_evidence(...)
```

### Step 4: Simplify Validation

Once extraction produces typed data, validation becomes trivial:

```python
async def cross_validate(session_id: str):
    evidence_data = load_evidence()

    for req_evidence in evidence_data["evidence"]:
        if req_evidence["validation_type"] == "cross_document":
            # Values already extracted — just compare them
            compare_values(req_evidence["values"])
```

---

## Part 5: Key Insights

### Why the Current Architecture Fails

1. **Extraction is blind to intent** — Doesn't know what validation needs
2. **Double extraction is wasteful** — Extracts snippets, then re-extracts fields
3. **Context is lost** — Validation works on snippets, not full documents
4. **Regex is a trap** — Used as fallback but matches garbage

### Why Type-Aware Extraction Solves This

1. **Extract once, validate without re-extraction** — Structured data ready for comparison
2. **Right tool for the job** — Different extraction strategy for each validation_type
3. **Preserves context** — Extract from full documents, store typed values
4. **No regex fallback needed** — LLM handles all extraction

### The `validation_type` Field Is Everything

The checklist already tells us exactly what each requirement needs:

| REQ | validation_type | What to Extract | What to Validate |
|-----|-----------------|-----------------|------------------|
| REQ-002 | cross_document | owner_name from each doc | Names match across docs |
| REQ-007 | structured_field | project_start_date | Date is valid format |
| REQ-003 | document_presence | Evidence snippet | Snippet exists with confidence |
| REQ-016 | manual | Context for review | Human decides |

**The system should read `validation_type` and act accordingly.**

---

## Part 6: Specification Summary

### Phase 1: Semantic Mapping

**Input:** Requirement + all documents
**Process:** LLM determines relevance (not keyword matching)
**Output:** RequirementMapping with relevance_reasoning

**Key Change:** Use LLM instead of category keywords

### Phase 2: Type-Aware Extraction

**Input:** Requirement + mapped documents
**Process:** Extract based on validation_type
**Output:**
- document_presence → PresenceEvidence (snippet)
- structured_field → StructuredEvidence (typed value)
- cross_document → CrossDocumentEvidence (value per document)
- manual → HumanReviewEvidence (context + question)

**Key Change:** Different extraction for different validation_type

### Phase 3: Validation

**Input:** Extracted evidence (already typed)
**Process:** Compare/validate without re-extraction
**Output:** ValidationResult

**Key Change:** No re-extraction — use typed data from Phase 2

---

## Appendix: Requirement → Field Type Mapping

Based on the checklist, here's what each requirement needs:

| REQ | Category | validation_type | Field to Extract |
|-----|----------|-----------------|------------------|
| REQ-001 | General | document_presence | methodology_version |
| REQ-002 | Land Tenure | cross_document | owner_name, area_hectares |
| REQ-003 | Project Area | document_presence | land_conversion_proof |
| REQ-004 | Project Area | document_presence | gis_boundary |
| REQ-005 | Project Boundary | document_presence | ghg_boundary_description |
| REQ-006 | Project Ownership | document_presence | credit_ownership_structure |
| REQ-007 | Project Start Date | structured_field | project_start_date |
| REQ-008 | Ecosystem Type | document_presence | ecosystem_classification |
| REQ-009 | Ecosystem Type | document_presence | land_use_history |
| REQ-010 | Crediting Period | structured_field | crediting_period_years |
| REQ-011 | GHG Accounting | document_presence | additionality_proof |
| REQ-012 | GHG Accounting | structured_field | leakage_percentage |
| REQ-013 | GHG Accounting | structured_field | permanence_period_years |
| REQ-014 | Regulatory Compliance | document_presence | compliance_attestation |
| REQ-015 | Registration | document_presence | other_registry_disclosure |
| REQ-016 | Project Plan Deviations | manual | deviation_justification |
| REQ-017 | Monitoring Plan | document_presence | monitoring_plan |
| REQ-018 | Risk Management | structured_field | buffer_pool_percentage |
| REQ-019 | Safeguards | document_presence | safeguard_activities |
| REQ-020 | Safeguards | document_presence | no_net_harm_assessment |
| REQ-021 | Safeguards | document_presence | stakeholder_consultation |
| REQ-022 | Safeguards | document_presence | environmental_impact |
| REQ-023 | Safeguards | document_presence | public_comment_process |

This mapping should be added to the checklist JSON or inferred from the requirement category and text.

---

The Core Problem

The three phases are disconnected and work against each other:

CURRENT FLOW (BROKEN):

Stage C: Mapping
→ Uses category keywords (no LLM)
→ Output: "REQ-002 might be in land-tenure docs"

Stage D: Evidence Extraction
→ Same generic prompt for ALL requirements
→ Output: text snippets (no typed values)
→ IGNORES validation_type entirely

Stage E: Validation
→ Receives only text snippets
→ Must RE-EXTRACT structured fields from snippets
→ Regex fallback matches garbage ("2023" as project ID)

The root cause: Evidence extraction doesn't know what validation needs, so it produces generic text blobs. Validation then has to re-parse those blobs, losing context and introducing errors.

---
The Key Insight: validation_type

The checklist already tells us exactly what each requirement needs:

{
"requirement_id": "REQ-007",
"validation_type": "structured_field",  // ← THIS IS THE KEY
"accepted_evidence": "Explicit mention of project start date"
}
┌───────────────────┬───────────────────────┬─────────────────────────────────┐
│  validation_type  │        Meaning        │             Example             │
├───────────────────┼───────────────────────┼─────────────────────────────────┤
│ document_presence │ Find evidence snippet │ REQ-003: "land not converted"   │
├───────────────────┼───────────────────────┼─────────────────────────────────┤
│ structured_field  │ Extract typed value   │ REQ-007: extract actual date    │
├───────────────────┼───────────────────────┼─────────────────────────────────┤
│ cross_document    │ Compare across docs   │ REQ-002: owner names consistent │
├───────────────────┼───────────────────────┼─────────────────────────────────┤
│ manual            │ Human judgment needed │ REQ-016: deviations             │
└───────────────────┴───────────────────────┴─────────────────────────────────┘
The system completely ignores this. Every requirement gets the same generic extraction.

---
The Ideal Architecture

SHOULD BE:

Stage C: Semantic Mapping
→ LLM determines document relevance
→ Preserves validation_type from checklist

Stage D: Type-Aware Extraction
→ SWITCH on validation_type:
    document_presence → extract snippet
    structured_field  → extract typed value (date, %)
    cross_document    → extract value from EACH document
    manual           → extract context for human

Stage E: Validation
→ NO RE-EXTRACTION
→ For cross_document: compare pre-extracted values
→ For structured_field: validate format/range

---
Why This Matters

Current: Extraction produces EvidenceSnippet(text="The farm is owned by Nicholas Denman...")

Then validation: Tries to regex-extract owner name from that string, matches "The Project" instead

With type-aware extraction: Evidence already contains CrossDocumentEvidence(values=[{doc: "DOC-001", value: "Nicholas Denman"}, ...])

Validation just compares: "Nicholas Denman" vs "Nick Denman" → 85% similarity → PASS

---
The Good News

The LLM extractors in llm_extractors.py are well-designed. They:
- Have detailed prompts for dates, tenure, project IDs
- Include filtering for false positives
- Use fuzzy matching for name variations

They're just called too late — in validation instead of extraction.

---
Recommended Path

Immediate (Fix the Bug)

1. Fix regex patterns in validation_tools.py to stop matching years/garbage
2. This unblocks users but doesn't fix the architecture

Short-term (Type-Aware Extraction)

1. Add validation_type to evidence model
2. Modify extract_evidence_with_llm to dispatch based on type
3. Call the specialized extractors during Stage D, not Stage E

Medium-term (Full Redesign)

1. Make mapping semantic (LLM-based)
2. Implement polymorphic evidence types
3. Simplify validation to just compare/check (no re-extraction)

---
The detailed specification is in .claude/planning/2026/01/12/architecture-audit.md. Want me to proceed with implementing the fix, or would you like to discuss the architecture further?
