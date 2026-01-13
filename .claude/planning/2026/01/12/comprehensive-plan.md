# Comprehensive Planning Document: Registry Review MCP Improvements

**Date:** 2026-01-12
**Context:** Addressing cross-validation bug, Becca's feedback, and systemic improvements

---

## Executive Summary

Three primary issues require attention:

1. **Cross-validation produces false positives** — extracting garbage text ("The Project", "2023") instead of actual owner names and project IDs
2. **No document modification workflow** — cannot delete, replace, or re-upload documents without nuking the entire session
3. **Missing on-chain output format** — system produces human-readable reports but not blockchain-compatible checklists

Root cause analysis reveals these share a common architectural theme: **the system was designed for forward-only workflows** with no provisions for data correction, mutation, or external system integration.

---

## Issue #1: Cross-Validation Bug

### Symptoms

From the failed validation transcript:
```
Land Tenure Consistency: ❌ Failed
  Owner names inconsistent: "The Project" vs "as appended to this document"

Project ID Format: ❌ Failed
  Found ID "2023" — does not match required format C##-###
```

### Root Cause

**Two-phase extraction architecture creates contamination opportunities:**

```
Phase 1 (Stage D): Evidence snippet extraction
  Document → LLM → EvidenceSnippet (unstructured text quotes)
  ✅ Works well - finds relevant passages

Phase 2 (Stage E): Structured field extraction from snippets
  EvidenceSnippet.text → Regex/LLM → ExtractedField (owner_name, project_id)
  ❌ FAILS - extracts from mixed context, filenames, irrelevant text
```

**Specific code problems:**

| Location | Problem | Effect |
|----------|---------|--------|
| `validation_tools.py:477-478` | Regex `r'([A-Z][a-z]+\s+[A-Z][a-z]+).*(?:owner\|steward)'` too broad | Matches "The Project" as owner name |
| `validation_tools.py:366` | Regex `r'\b(\d{4})\b'` matches any 4-digit number | Extracts years like "2023" as project IDs |
| `validation_tools.py:377` | Filter `int(project_id) < 9000` doesn't exclude years | 2023 < 9000 passes filter |
| `llm_extractors.py:1001-1061` | ProjectIDExtractor filters exist but aren't used in validation fallback | Regex path bypasses LLM quality controls |

### The Deeper Problem

The evidence model stores **unstructured text snippets without field boundaries**:

```python
# Current: stores text blob
EvidenceSnippet(
    text="The farm owned by Nicholas Denman as per document 4997Botany22...",
    confidence=0.92
)

# What validation needs: structured fields with provenance
ExtractedField(
    field_type="owner_name",
    value="Nicholas Denman",
    source_char_offset=(15, 31),  # exact location in snippet
    confidence=0.95
)
```

Without field boundaries, validation tools must re-extract via regex from mixed text, causing contamination.

### Recommended Fix Strategy

**Option A: Fix extraction at source (preferred)**
- Modify `extract_evidence_with_llm()` to extract structured fields during Stage D
- Store `extracted_fields: dict[str, ExtractedField]` on each EvidenceSnippet
- Validation reads pre-extracted fields instead of re-parsing

**Option B: Improve regex fallback**
- Add negative lookahead to exclude years: `r'\b(?!20[0-2]\d\b)(\d{4})\b'`
- Require "owner:" or "landowner:" prefix for name extraction
- Add filename detection: skip extraction if text matches `\d{4}[A-Za-z]+\d{2}` pattern

**Option C: Always use LLM extractors**
- Remove regex fallback path entirely
- Route all field extraction through `llm_extractors.py` which has better filtering
- Cost: ~$0.02 per requirement × 23 requirements = ~$0.50 per session

### Files Requiring Modification

```
src/registry_review_mcp/tools/validation_tools.py
  - extract_land_tenure_from_evidence() lines 453-513
  - extract_project_ids_from_evidence() lines 353-385
  - extract_dates_from_evidence() lines 388-450

src/registry_review_mcp/models/evidence.py
  - Add extracted_fields to EvidenceSnippet model

src/registry_review_mcp/tools/evidence_tools.py
  - Modify extract_evidence_with_llm() to populate extracted_fields
```

### Testing Strategy

```bash
# Existing ground truth test
pytest tests/test_evidence_extraction.py -k "botany" -v

# Add new test: verify extracted fields don't contain filenames
# Add new test: verify owner names are actual names not fragments
# Add new test: verify project IDs match registry patterns
```

---

## Issue #2: Document Modification/Deletion Workflow

### Current State

| Operation | Supported | Workaround |
|-----------|-----------|------------|
| Add documents | ✅ Yes | `upload_additional_files()` |
| Delete single document | ❌ No | Delete entire session |
| Replace document content | ❌ No | Delete session, re-upload all |
| Rename document | ❌ No | Delete session, re-upload |
| Update classification | ❌ No | Manual JSON edit |

### Why This Matters

Becca asked: "How does modifying / deleting / re-uploading documents work?"

Answer: **It doesn't.** The system assumes documents are immutable after discovery. Any correction requires starting over.

### Cascade Effects (Currently Unhandled)

When a document changes, dependent data becomes stale:

```
documents.json ←── Document deleted/modified
       ↓
mappings.json ←── Contains document_id references → ORPHANED
       ↓
findings.json ←── Evidence snippets reference document_id → ORPHANED
       ↓
validations.json ←── Based on stale evidence → INVALID
```

### Recommended Implementation

**Phase 1: Granular Document Deletion**

```python
# New tool: delete_document()
async def delete_document(session_id: str, document_id: str) -> dict:
    """
    Delete a single document and cascade-clean dependent data.

    1. Remove from documents.json
    2. Remove from all mappings in mappings.json
    3. Remove evidence snippets referencing this document
    4. Mark validation results as stale
    5. Update session statistics
    """
```

**Phase 2: Document Replacement**

```python
# New tool: replace_document()
async def replace_document(
    session_id: str,
    document_id: str,
    new_file: dict  # {filename, content_base64}
) -> dict:
    """
    Replace document content, preserving mappings where possible.

    1. Compute new content hash
    2. If hash unchanged, no-op
    3. If hash changed:
       - Update document record with new hash/metadata
       - Mark all evidence from this doc as "stale" (don't delete)
       - Flag validation results as outdated
       - Return list of affected requirements for re-extraction
    """
```

**Phase 3: Stale Data Indicators**

```python
# Add to EvidenceSnippet model
class EvidenceSnippet(BaseModel):
    # ... existing fields ...
    is_stale: bool = False
    stale_reason: str | None = None  # "source_document_modified"
```

**Phase 4: Validation Refresh**

```python
# New tool: refresh_validation()
async def refresh_validation(session_id: str) -> dict:
    """
    Re-run cross-validation on current evidence.
    Call after document changes to update validation results.
    """
```

### Files Requiring Modification

```
src/registry_review_mcp/tools/document_tools.py
  - Add delete_document()
  - Add replace_document()
  - Add validate_document_references()

src/registry_review_mcp/tools/evidence_tools.py
  - Add mark_evidence_stale()
  - Add delete_evidence_for_document()

src/registry_review_mcp/models/evidence.py
  - Add is_stale, stale_reason fields

src/registry_review_mcp/tools/validation_tools.py
  - Add invalidate_validation_results()
  - Add refresh_validation()
```

### Testing Strategy

```python
# New test scenarios needed:
def test_delete_document_cascades_to_mappings(): ...
def test_delete_document_cascades_to_evidence(): ...
def test_replace_document_marks_evidence_stale(): ...
def test_stale_evidence_excluded_from_validation(): ...
def test_refresh_validation_after_document_change(): ...
```

---

## Issue #3: On-Chain Checklist Output

### Current Output Formats

**Markdown Report:** Human-readable with emoji status indicators
**JSON Report:** Machine-parseable with full evidence and validation details

Neither is suitable for blockchain upload.

### What On-Chain Requires

From Regen Ledger integration context:

1. **Document IRIs** — Evidence must reference IPFS/on-chain document identifiers, not local filenames
2. **Approval Decision** — Explicit Approved/Conditional/Rejected status with timestamp
3. **Reviewer Identity** — Who made the decision (for audit trail)
4. **Cryptographic Integrity** — Hash chain linking to document proofs
5. **Canonical Schema** — Must match Regen Ledger's expected data structure

### Current JSON Structure vs On-Chain Needs

| Current Field | On-Chain Equivalent | Gap |
|---------------|---------------------|-----|
| `metadata.project_id` | `project_id` | ✅ Compatible |
| `metadata.methodology` | `checklist_id` | ✅ Compatible |
| `requirements[].status` | `assessment.status` | ✅ Compatible |
| `requirements[].page_citations` | `proofs[].document_iri` | ❌ Need IRI, not filename |
| (missing) | `approval_decision` | ❌ Not captured |
| (missing) | `reviewer_id` | ❌ Not captured |
| (missing) | `document_hash` | ❌ Not computed |
| (missing) | `ledger_anchor_date` | ❌ Not tracked |

### Recommended Implementation

**New Model: OnChainReview**

```python
# src/registry_review_mcp/models/onchain.py

class DocumentProof(BaseModel):
    requirement_id: str
    document_iri: str  # "ipfs://Qm..." or on-chain anchor
    document_hash: str  # SHA256 for integrity verification
    excerpt: str  # Evidence text
    location: dict  # {page, section}
    confidence: float

class ApprovalDecision(BaseModel):
    decision: Literal["approved", "conditional", "rejected", "on_hold"]
    decision_reason: str
    reviewer_id: str
    reviewed_at: datetime
    approved_for_credit_issuance: bool
    special_conditions: list[str] = []

class OnChainReview(BaseModel):
    # Project identification
    project_id: str
    project_name: str

    # Checklist reference
    checklist_id: str  # "soil-carbon-v1.2.2"
    checklist_version: str

    # Assessment results
    requirements_assessment: list[RequirementAssessment]
    validation_results: list[ValidationResult]

    # Decision
    approval_decision: ApprovalDecision

    # Provenance
    document_proofs: list[DocumentProof]
    audit_timestamp: datetime
    audit_chain_hash: str | None  # Links to previous audit entry

    # On-chain status
    ledger_anchor_date: datetime | None
    ledger_transaction_id: str | None
```

**New Tool: generate_onchain_report()**

```python
# src/registry_review_mcp/tools/report_tools.py

async def generate_onchain_report(
    session_id: str,
    approval_decision: str,  # "approved" | "conditional" | "rejected"
    decision_reason: str,
    reviewer_id: str,
    document_iris: dict[str, str] | None = None  # {document_id: iri}
) -> dict:
    """
    Generate blockchain-compatible checklist output.

    Requires human review stage (G) to be complete.
    Document IRIs can be provided if documents were uploaded to IPFS.
    """
```

**Integration with Stage H (Completion)**

Update `H_completion.py` to:
1. Require approval decision before completion
2. Generate on-chain report as final artifact
3. Optionally call Regen Ledger MCP to anchor

### Files Requiring Creation/Modification

```
src/registry_review_mcp/models/onchain.py  # NEW
  - DocumentProof, ApprovalDecision, OnChainReview models

src/registry_review_mcp/tools/report_tools.py
  - Add generate_onchain_report()
  - Add format_onchain_json()

src/registry_review_mcp/tools/human_review_tools.py
  - Add capture_approval_decision()
  - Ensure reviewer_id is captured

src/registry_review_mcp/prompts/H_completion.py
  - Update to generate on-chain output
  - Add Regen Ledger integration point

tests/test_onchain_output.py  # NEW
  - Schema validation tests
  - IRI serialization tests
```

### Testing Strategy

```python
def test_onchain_report_has_required_fields(): ...
def test_onchain_report_validates_project_id_format(): ...
def test_document_proofs_include_hashes(): ...
def test_approval_decision_is_captured(): ...
def test_onchain_json_is_valid_schema(): ...
```

---

## Auxiliary Improvements Identified

### A. State Management Improvements

**Issue:** Session state scattered across multiple JSON files with no atomic transactions.

**Current:**
```
session.json      ← session metadata
documents.json    ← document inventory
mappings.json     ← requirement mappings
findings.json     ← extracted evidence
validations.json  ← validation results
```

**Recommendation:** Consider SQLite for atomic transactions and referential integrity.

```python
# Alternative: Single-file state with versioning
session_state = {
    "version": 3,
    "metadata": {...},
    "documents": [...],
    "mappings": [...],
    "evidence": [...],
    "validations": [...]
}
```

### B. Confidence Score Calibration

**Issue:** LLM extraction marks low-quality extractions as 0.8-1.0 confidence.

**Recommendation:** Post-hoc calibration based on validation outcomes:
- If extracted field fails validation → reduce confidence retroactively
- Track historical accuracy to calibrate future extractions

### C. Error Recovery & Retry

**Issue:** If extraction fails mid-workflow, no way to resume from checkpoint.

**Recommendation:** Add workflow checkpointing:
```python
# Save checkpoint after each requirement
checkpoint = {
    "stage": "evidence_extraction",
    "completed_requirements": ["REQ-001", "REQ-002"],
    "in_progress": "REQ-003",
    "last_error": None
}
```

### D. Cost Tracking Visibility

**Issue:** Cost tracking exists but isn't surfaced to users.

**Location:** `src/registry_review_mcp/utils/cost_tracker.py`

**Recommendation:** Add `get_session_costs()` tool to show:
- Total API spend for session
- Breakdown by stage (discovery, extraction, validation)
- Estimated remaining cost to completion

### E. Documentation Gaps

**Missing documentation:**
- How to handle document upload errors
- What happens when extraction confidence is low
- How to interpret validation failures
- Recovery procedures for corrupted sessions

**Recommendation:** Add `docs/USER_GUIDE.md` with workflow troubleshooting.

### F. Test Data Isolation

**Issue:** Tests may accidentally modify production data if paths misconfigured.

**Current mitigation:** XDG Base Directory spec separates data.

**Recommendation:** Add test fixture that:
1. Creates isolated temp directory
2. Sets `REGISTRY_REVIEW_DATA_DIR` to temp
3. Cleans up after test

---

## Implementation Priority

### Phase 1: Fix Cross-Validation Bug (Urgent)

1. Add year exclusion to project ID regex
2. Add "owner:" prefix requirement for name extraction
3. Add filename detection to skip contaminated text
4. Add tests for ground truth validation

**Estimated scope:** 2-3 focused sessions

### Phase 2: Document Management (High Priority)

1. Implement `delete_document()` with cascade
2. Add `is_stale` flag to evidence model
3. Add `refresh_validation()` tool
4. Update prompts to explain document management

**Estimated scope:** 3-4 focused sessions

### Phase 3: On-Chain Output (Medium Priority)

1. Create OnChainReview model
2. Implement `generate_onchain_report()`
3. Add approval decision capture to Stage G
4. Integration tests with mock Regen Ledger

**Estimated scope:** 2-3 focused sessions

### Phase 4: Auxiliary Improvements (Low Priority)

1. Cost tracking visibility
2. Documentation
3. Error recovery
4. Confidence calibration

**Estimated scope:** 1-2 sessions each

---

## Key Concepts & Reminders

### Architectural Invariants

1. **Forward-only workflow assumption** — Currently no backward data propagation
2. **Content-hash document IDs** — Changing content changes the ID
3. **Two-phase extraction** — Snippets first, structured fields second
4. **Regex fallback exists** — LLM extraction has regex backup that bypasses quality controls

### Testing Protocol

```bash
# Always run fast tests (default)
pytest

# Never run expensive tests without explicit instruction
# pytest -m expensive  ← DON'T DO THIS

# Ground truth validation
pytest tests/test_evidence_extraction.py -k "botany"
```

### Data Locations

```
Production data: ~/.local/share/registry-review-mcp/
Cache: ~/.cache/registry-review-mcp/
Test fixtures: ./examples/22-23/
Checklists: ./data/checklists/
```

### Key Files for Each Issue

**Cross-validation bug:**
- `tools/validation_tools.py` (lines 353-513)
- `extractors/llm_extractors.py` (lines 1001-1061)
- `models/evidence.py`

**Document management:**
- `tools/document_tools.py`
- `tools/upload_tools.py`
- `tools/evidence_tools.py`

**On-chain output:**
- `tools/report_tools.py`
- `models/report.py`
- `prompts/H_completion.py`

---

## Next Steps

Ready to address Issue #1 (Cross-Validation Bug) first. The recommended approach:

1. Read the validation_tools.py extraction functions
2. Identify the specific regex patterns causing false positives
3. Add negative patterns for year exclusion and filename detection
4. Write tests using Botany Farm ground truth data
5. Verify cross-validation passes on known-good session

Shall we proceed?
