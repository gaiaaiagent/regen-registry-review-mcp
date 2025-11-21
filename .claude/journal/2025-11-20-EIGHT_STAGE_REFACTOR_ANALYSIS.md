# Eight-Stage Workflow Refactoring Analysis

**Date:** November 20, 2025
**Purpose:** Analyze codebase changes required to refactor from 7-stage to 8-stage workflow
**Canonical Reference:** [Registry Review Workflow: Eight-Stage Process](specs/2025-11-20-registry-review-workflow-stages.md)

---

## Current State: 7-Stage Implementation

The codebase currently implements a **7-stage workflow** that conflates requirement mapping with evidence extraction:

### Current Stages (Implicit)
1. **Initialize** (A_initialize.py) - Session creation
2. **Document Discovery** (B_document_discovery.py) - Find and classify files
3. **Evidence Extraction** (C_evidence_extraction.py) - **[CONFLATED: includes requirement mapping + extraction]**
4. **Cross-Validation** (D_cross_validation.py) - Consistency checks
5. **Report Generation** (E_report_generation.py) - Structured output
6. **Human Review** (F_human_review.py) - Expert review
7. **Complete** (G_complete.py) - Finalization

### The Problem

**Stage 3 (Evidence Extraction)** currently tries to do two fundamentally different things:
1. Map documents to checklist requirements (which files satisfy which requirements?)
2. Extract evidence snippets from those mapped documents (what data exists in the files?)

This creates confusion because:
- The tool `map_requirement(session_id, requirement_id)` exists but isn't integrated into the workflow
- Evidence extraction can't know which documents to extract from without prior mapping
- The workflow progress model doesn't track requirement mapping completion
- Tests validate "evidence extraction" without validating the mapping step

---

## Target State: 8-Stage Workflow

### New Explicit Stages
1. **Initialize** - Session creation
2. **Document Discovery** - Find and classify files
3. **Requirement Mapping** - ✨ NEW: Map documents to checklist requirements
4. **Evidence Extraction** - Extract data from mapped documents
5. **Cross-Validation** - Consistency checks
6. **Report Generation** - Structured output
7. **Human Review** - Expert review
8. **Completion** - Finalization

---

## Changes Required

### 1. Data Model Changes

#### `src/registry_review_mcp/models/schemas.py`

**Current (Line 43-52):**
```python
class WorkflowProgress(BaseModel):
    """Tracks progress through the 7-stage workflow."""

    initialize: Literal["pending", "in_progress", "completed"] = "pending"
    document_discovery: Literal["pending", "in_progress", "completed"] = "pending"
    evidence_extraction: Literal["pending", "in_progress", "completed"] = "pending"
    cross_validation: Literal["pending", "in_progress", "completed"] = "pending"
    report_generation: Literal["pending", "in_progress", "completed"] = "pending"
    human_review: Literal["pending", "in_progress", "completed"] = "pending"
    complete: Literal["pending", "in_progress", "completed"] = "pending"
```

**Required Change:**
```python
class WorkflowProgress(BaseModel):
    """Tracks progress through the 8-stage workflow."""

    initialize: Literal["pending", "in_progress", "completed"] = "pending"
    document_discovery: Literal["pending", "in_progress", "completed"] = "pending"
    requirement_mapping: Literal["pending", "in_progress", "completed"] = "pending"  # NEW
    evidence_extraction: Literal["pending", "in_progress", "completed"] = "pending"
    cross_validation: Literal["pending", "in_progress", "completed"] = "pending"
    report_generation: Literal["pending", "in_progress", "completed"] = "pending"
    human_review: Literal["pending", "in_progress", "completed"] = "pending"
    completion: Literal["pending", "in_progress", "completed"] = "pending"  # RENAMED from "complete"
```

**Impact:**
- ⚠️ BREAKING CHANGE for existing sessions (backward compatibility issue)
- Need migration strategy for sessions created under 7-stage model
- All tests that check `workflow_progress` will need updates

---

#### New Data Models Needed

**Add to `src/registry_review_mcp/models/schemas.py`:**

```python
class RequirementMapping(BaseModel):
    """Mapping between a requirement and supporting documents."""

    requirement_id: str = Field(pattern=r"^REQ-\d{3}$")
    mapped_documents: list[str] = []  # List of document_ids
    mapping_status: Literal["suggested", "confirmed", "unmapped", "manual"] = "suggested"
    confidence: ConfidenceScore | None = None
    suggested_by: Literal["agent", "manual"] = "agent"
    confirmed_by: str | None = None  # User who confirmed
    confirmed_at: datetime | None = None


class RequirementMappingCollection(BaseModel):
    """Collection of all requirement mappings for a session."""

    session_id: str
    mappings: list[RequirementMapping]
    total_requirements: int
    mapped_count: int
    unmapped_count: int
    confirmed_count: int
    created_at: datetime
    updated_at: datetime
```

**Storage:** New file `mappings.json` in session directory

---

### 2. Prompt Changes

#### Create New File: `src/registry_review_mcp/prompts/C_requirement_mapping.py`

**Purpose:** New Stage 3 prompt for requirement mapping

**Functionality:**
- Load checklist template for session methodology
- Load discovered documents from Stage 2
- For each requirement:
  - Suggest document matches using semantic similarity
  - Provide confidence scores
  - Mark as unmapped if no plausible matches
- Output mapping matrix for human review
- Update workflow_progress.requirement_mapping = "completed"

**File Structure:**
```python
"""Requirement mapping workflow - Stage 3 of registry review."""

from mcp.types import TextContent
from ..tools import mapping_tools  # NEW module needed
from ..utils.state import StateManager
from .helpers import (
    text_content,
    format_error,
    format_workflow_header,
    format_next_steps_section,
    get_or_select_session,
    validate_session_exists,
)


async def requirement_mapping_prompt(
    session_id: str | None = None
) -> list[TextContent]:
    """Map discovered documents to checklist requirements (Stage 3).

    This prompt loads the checklist, analyzes documents, and suggests
    which documents satisfy which requirements.

    Args:
        session_id: Optional existing session ID (auto-selects latest if not provided)

    Returns:
        Formatted mapping results with human review interface
    """
    # Implementation here
```

#### Rename Current File: `C_evidence_extraction.py` → `D_evidence_extraction.py`

**Current Stage 3 becomes Stage 4**

**Required Changes in File:**
- Update docstring: "Stage 3" → "Stage 4"
- Load `mappings.json` to know which documents to extract from
- Only extract evidence from **confirmed** mappings
- Update workflow_progress field: `evidence_extraction` (now Stage 4)
- Update next step guidance to point to Stage 5 (cross-validation)

#### Rename Subsequent Files:
- `D_cross_validation.py` → `E_cross_validation.py` (Stage 4 → Stage 5)
- `E_report_generation.py` → `F_report_generation.py` (Stage 5 → Stage 6)
- `F_human_review.py` → `G_human_review.py` (Stage 6 → Stage 7)
- `G_complete.py` → `H_completion.py` (Stage 7 → Stage 8)

**Naming Convention Note:** Consider renaming `G_complete.py` → `H_completion.py` to match canonical spec terminology

---

### 3. Tool Changes

#### Create New Module: `src/registry_review_mcp/tools/mapping_tools.py`

**Purpose:** Business logic for requirement mapping

**Functions Needed:**

```python
async def map_all_requirements(session_id: str) -> dict[str, Any]:
    """Map all requirements to documents using semantic matching.

    Returns:
        {
            "session_id": str,
            "mappings": [...],
            "total_requirements": int,
            "mapped_count": int,
            "unmapped_count": int,
            "confidence_summary": {...}
        }
    """

async def confirm_mapping(
    session_id: str,
    requirement_id: str,
    document_ids: list[str],
    confirmed_by: str = "user"
) -> dict[str, Any]:
    """Confirm or manually set mapping for a requirement."""

async def remove_mapping(
    session_id: str,
    requirement_id: str,
    document_id: str
) -> dict[str, Any]:
    """Remove an incorrect suggested mapping."""

async def get_mapping_status(session_id: str) -> dict[str, Any]:
    """Get current mapping status and statistics."""
```

#### Update Existing: `src/registry_review_mcp/tools/evidence_tools.py`

**Current Function:**
```python
async def extract_all_evidence(session_id: str) -> dict[str, Any]:
    """Extract evidence for all requirements from discovered documents."""
```

**Required Changes:**
- Load `mappings.json` first
- Only process requirements with `mapping_status == "confirmed"`
- For each confirmed mapping, extract evidence from specified documents only
- Skip unmapped requirements (don't attempt blind extraction)
- Update statistics to distinguish "mapped but no evidence" vs "unmapped"

**Current Function:**
```python
async def map_requirement(session_id: str, requirement_id: str) -> dict[str, Any]:
    """Map a single requirement to documents and extract evidence."""
```

**Action:**
- ⚠️ This function appears to do both mapping AND extraction
- Should be **split** or **moved** to `mapping_tools.py`
- Evidence extraction should be separate operation after mapping confirmed

---

### 4. Server Registration Changes

#### `src/registry_review_mcp/server.py`

**Add New Prompt (Line ~369-425):**
```python
@mcp.prompt(name="C-requirement-mapping")
async def requirement_mapping(project: str = "") -> list[TextContent]:
    """Map documents to checklist requirements - provide session ID (optional, auto-selects latest)"""
    session_id = project if project else None
    return await C_requirement_mapping.requirement_mapping_prompt(session_id)
```

**Rename Existing Prompts:**
```python
# OLD: @mcp.prompt(name="C-evidence-extraction")
@mcp.prompt(name="D-evidence-extraction")  # Now Stage 4
async def evidence_extraction(project: str = "") -> list[TextContent]:
    """Extract evidence from mapped documents - provide session ID (optional, auto-selects latest)"""
    session_id = project if project else None
    result = await D_evidence_extraction.evidence_extraction(session_id)
    return [TextContent(type="text", text=result)]

# OLD: @mcp.prompt(name="D-cross-validation")
@mcp.prompt(name="E-cross-validation")  # Now Stage 5
async def cross_validation(project: str = "") -> list[TextContent]:
    """Validate consistency across documents - provide session ID (optional)"""
    session_id = project if project else None
    return await E_cross_validation.cross_validation_prompt(session_id)

# ... continue renaming D→E, E→F, F→G, G→H
```

**Add New Tools:**
```python
@mcp.tool()
@with_error_handling("map_all_requirements")
async def map_all_requirements(session_id: str) -> str:
    """Map all requirements to documents using semantic matching."""
    from .tools import mapping_tools
    results = await mapping_tools.map_all_requirements(session_id)
    return json.dumps(results, indent=2)

@mcp.tool()
@with_error_handling("confirm_mapping")
async def confirm_mapping(
    session_id: str,
    requirement_id: str,
    document_ids: list[str]
) -> str:
    """Confirm or manually set document mappings for a requirement."""
    from .tools import mapping_tools
    result = await mapping_tools.confirm_mapping(session_id, requirement_id, document_ids)
    return json.dumps(result, indent=2)
```

**Import Updates:**
```python
# OLD:
from .prompts import A_initialize, B_document_discovery, C_evidence_extraction, D_cross_validation, E_report_generation, F_human_review, G_complete

# NEW:
from .prompts import (
    A_initialize,
    B_document_discovery,
    C_requirement_mapping,  # NEW
    D_evidence_extraction,  # RENAMED
    E_cross_validation,     # RENAMED
    F_report_generation,    # RENAMED
    G_human_review,         # RENAMED
    H_completion            # RENAMED
)
```

---

### 5. Test Updates

#### `tests/test_integration_full_workflow.py`

**Current Test (Line 3-4):**
```python
"""Integration tests for complete end-to-end workflow.

These tests validate the full 7-stage workflow from initialization through completion,
using real examples and ensuring proper state transitions and data flow.
"""
```

**Required Changes:**

1. **Update docstring:** "7-stage workflow" → "8-stage workflow"

2. **Add Stage 3 test between Document Discovery and Evidence Extraction:**

```python
# Stage 2: Document Discovery
print("\n=== Stage 2: Document Discovery ===")
result = await document_discovery.document_discovery_prompt(session_id=session_id)
# ... existing assertions ...

# NEW: Stage 3: Requirement Mapping
print("\n=== Stage 3: Requirement Mapping ===")
result = await requirement_mapping.requirement_mapping_prompt(session_id)
response_text = result[0].text
assert "Mapping Complete" in response_text or "requirements mapped" in response_text

# Verify mappings created
mappings_data = manager.read_json("mappings.json")
total_requirements = mappings_data.get("total_requirements", 0)
mapped_count = mappings_data.get("mapped_count", 0)
print(f"✓ Requirements mapped: {mapped_count}/{total_requirements}")
assert mapped_count >= 10  # At least 10 requirements should find plausible documents

# Verify mapping data structure
assert "mappings" in mappings_data
mappings = mappings_data["mappings"]
assert len(mappings) > 0
first_mapping = mappings[0]
assert "requirement_id" in first_mapping
assert "mapped_documents" in first_mapping
assert "mapping_status" in first_mapping

# Stage 4: Evidence Extraction (was Stage 3)
print("\n=== Stage 4: Evidence Extraction ===")
# ... existing evidence extraction test ...
```

3. **Renumber remaining stages in print statements:**
```python
print("\n=== Stage 5: Cross-Validation ===")  # was Stage 4
print("\n=== Stage 6: Report Generation ===")  # was Stage 5
print("\n=== Stage 7: Human Review ===")      # was Stage 6
print("\n=== Stage 8: Completion ===")        # was Stage 7
```

4. **Update workflow progress assertions:**
```python
# After Stage 3
await SessionAssertions.assert_workflow_stage_completed(session_id, "requirement_mapping")

# After Stage 4 (evidence extraction)
await SessionAssertions.assert_workflow_stage_completed(session_id, "evidence_extraction")
# ... etc
```

#### `tests/factories.py`

**Update SessionBuilder:**
```python
class SessionBuilder:
    """Factory for building test sessions with flexible configuration."""

    @staticmethod
    async def with_workflow_stage(
        session_id: str,
        stage: Literal[
            "initialize",
            "document_discovery",
            "requirement_mapping",  # NEW
            "evidence_extraction",
            "cross_validation",
            "report_generation",
            "human_review",
            "completion"  # RENAMED from "complete"
        ],
        status: Literal["pending", "in_progress", "completed"] = "completed"
    ):
        """Set a specific workflow stage status."""
        # Implementation
```

#### Other Test Files Requiring Updates

**Search Results Show These Files Reference Workflow:**
- `tests/test_initialize_workflow.py` - Update stage references
- `tests/test_document_processing.py` - Update workflow progress checks
- `tests/test_evidence_extraction.py` - Add mapping prerequisite
- `tests/test_validation.py` - Update stage sequence
- `tests/test_user_experience.py` - Update UX expectations for 8 stages

---

### 6. Documentation Updates

#### User-Facing Documentation

**`README.md`** - Update workflow description:
```markdown
## Workflow Stages

The Registry Review workflow consists of 8 stages:

1. **Initialize** - Create review session
2. **Document Discovery** - Find and classify files
3. **Requirement Mapping** - Map documents to checklist requirements
4. **Evidence Extraction** - Extract data from mapped documents
5. **Cross-Validation** - Check consistency across documents
6. **Report Generation** - Generate structured review report
7. **Human Review** - Expert validation and annotations
8. **Completion** - Finalize and archive
```

**`CAPABILITIES.md`** - Update prompt list:
```markdown
### Workflow Prompts (8-Stage Process)

1. `/A-initialize` - Initialize new review session
2. `/B-document-discovery` - Discover and classify documents
3. `/C-requirement-mapping` - Map documents to requirements (NEW)
4. `/D-evidence-extraction` - Extract evidence from documents
5. `/E-cross-validation` - Validate consistency
6. `/F-report-generation` - Generate review report
7. `/G-human-review` - Human review and annotations
8. `/H-completion` - Complete and finalize review
```

#### Internal Documentation

Files mentioning "7-stage" or "seven-stage":
- `docs/UX_ANALYSIS_INDEX.md`
- `docs/UX_VISUAL_GUIDE.md`
- `docs/UX_ANALYSIS_SUMMARY.md`
- `docs/UX_ANALYSIS.md`
- `docs/CODE_QUALITY_REVIEW.md`
- `docs/P0_SPRINT_SUMMARY.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/specs/UX/00_EXECUTIVE_SUMMARY.md`
- `docs/specs/UX/07_completion_stage_analysis.md`

**Action:** Global find/replace "7-stage" → "8-stage" and "seven-stage" → "eight-stage"

**Exception:** Don't update historical transcripts or archived documents

---

### 7. State Migration Strategy

#### Problem: Existing Sessions

Sessions created under the 7-stage model will have:
```json
{
  "workflow_progress": {
    "initialize": "completed",
    "document_discovery": "completed",
    "evidence_extraction": "pending",
    "cross_validation": "pending",
    "report_generation": "pending",
    "human_review": "pending",
    "complete": "pending"
  }
}
```

They're missing:
- `requirement_mapping` field
- Renamed `completion` field (was `complete`)

#### Solution: Automatic Migration

**Add to `src/registry_review_mcp/utils/state.py`:**

```python
def migrate_workflow_progress(workflow_progress: dict) -> dict:
    """Migrate workflow_progress from 7-stage to 8-stage model.

    Handles:
    - Missing 'requirement_mapping' field
    - Renamed 'complete' → 'completion'
    - Inserts requirement_mapping between discovery and extraction
    """
    # If already 8-stage, return as-is
    if "requirement_mapping" in workflow_progress and "completion" in workflow_progress:
        return workflow_progress

    # Build new 8-stage structure
    migrated = {
        "initialize": workflow_progress.get("initialize", "pending"),
        "document_discovery": workflow_progress.get("document_discovery", "pending"),
        "requirement_mapping": "pending",  # New field, default to pending
        "evidence_extraction": workflow_progress.get("evidence_extraction", "pending"),
        "cross_validation": workflow_progress.get("cross_validation", "pending"),
        "report_generation": workflow_progress.get("report_generation", "pending"),
        "human_review": workflow_progress.get("human_review", "pending"),
        "completion": workflow_progress.get("complete", "pending"),  # Renamed field
    }

    # Smart inference: If evidence_extraction is completed, assume requirement_mapping was done
    if migrated["evidence_extraction"] in ["in_progress", "completed"]:
        migrated["requirement_mapping"] = "completed"

    return migrated


class StateManager:
    """Manages session state persistence."""

    def read_json(self, filename: str) -> dict:
        """Read JSON file from session directory with automatic migration."""
        path = self.session_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        with open(path, "r") as f:
            data = json.load(f)

        # Auto-migrate workflow_progress if reading session.json
        if filename == "session.json" and "workflow_progress" in data:
            data["workflow_progress"] = migrate_workflow_progress(data["workflow_progress"])

        return data
```

**Impact:**
- ✅ Backward compatible - old sessions still load
- ✅ Automatic - no manual intervention required
- ✅ Safe - preserves existing data
- ⚠️ Write-back needed - should save migrated version

---

## Summary of Changes

### Files to Create (New)
1. `src/registry_review_mcp/prompts/C_requirement_mapping.py` - New Stage 3 prompt
2. `src/registry_review_mcp/tools/mapping_tools.py` - Requirement mapping business logic
3. `docs/EIGHT_STAGE_REFACTOR_ANALYSIS.md` - This document

### Files to Rename
1. `src/registry_review_mcp/prompts/C_evidence_extraction.py` → `D_evidence_extraction.py`
2. `src/registry_review_mcp/prompts/D_cross_validation.py` → `E_cross_validation.py`
3. `src/registry_review_mcp/prompts/E_report_generation.py` → `F_report_generation.py`
4. `src/registry_review_mcp/prompts/F_human_review.py` → `G_human_review.py`
5. `src/registry_review_mcp/prompts/G_complete.py` → `H_completion.py`

### Files to Modify (Major Changes)
1. `src/registry_review_mcp/models/schemas.py` - Add `requirement_mapping` field, new models
2. `src/registry_review_mcp/server.py` - Add new prompt, rename existing, new tools
3. `src/registry_review_mcp/tools/evidence_tools.py` - Use mappings, don't blindly extract
4. `src/registry_review_mcp/utils/state.py` - Add migration logic
5. `tests/test_integration_full_workflow.py` - Add Stage 3 test, renumber stages

### Files to Modify (Minor Updates)
1. All renamed prompt files (D-H) - Update stage numbers in docstrings
2. `tests/factories.py` - Update SessionBuilder stage enum
3. `README.md` - Update workflow description
4. `CAPABILITIES.md` - Update prompt list
5. Test files: `test_initialize_workflow.py`, `test_evidence_extraction.py`, etc.

### Global Search/Replace Operations
1. Find: `"7-stage"` Replace: `"8-stage"` (excluding archived docs)
2. Find: `"seven-stage"` Replace: `"eight-stage"` (excluding archived docs)
3. Find: `workflow_progress.complete` Replace: `workflow_progress.completion`

---

## Risk Assessment

### High Risk
- **Data Model Changes** - Breaking change to `WorkflowProgress` schema
  - Mitigation: Automatic migration in `StateManager.read_json()`

- **File Renaming** - Import paths break if not updated atomically
  - Mitigation: Use refactoring tools, comprehensive test suite

### Medium Risk
- **Evidence Extraction Logic** - Depends on mappings now, can't work standalone
  - Mitigation: Clear error messages if mappings missing

- **Test Coverage Gaps** - New Stage 3 needs comprehensive tests
  - Mitigation: Write tests for mapping before implementing

### Low Risk
- **Documentation** - Outdated docs confuse users
  - Mitigation: Find/replace is safe, affects user-facing docs only

---

## Implementation Strategy

### Phase 1: Foundation (No Breaking Changes)
1. Add `requirement_mapping` field to `WorkflowProgress` with default `"pending"`
2. Create migration logic in `StateManager`
3. Add new data models (`RequirementMapping`, etc.)
4. Create `mapping_tools.py` module with business logic
5. Write comprehensive tests for mapping logic

**Checkpoint:** Tests pass, existing sessions still work

### Phase 2: New Prompt (Additive)
1. Create `C_requirement_mapping.py` prompt
2. Register prompt in `server.py` as `C-requirement-mapping`
3. Test manually that Stage 3 works in isolation
4. Add integration test for full 8-stage workflow

**Checkpoint:** 8-stage workflow functional, 7-stage still works

### Phase 3: File Renaming (Breaking)
1. Rename prompt files C→D, D→E, E→F, F→G, G→H
2. Update imports in `server.py`
3. Update prompt registrations in `server.py`
4. Update all test imports
5. Run full test suite

**Checkpoint:** All tests pass with renamed files

### Phase 4: Evidence Extraction Refactor
1. Update `evidence_tools.py` to load and use `mappings.json`
2. Move or deprecate `map_requirement()` function
3. Update error messages to guide users through correct sequence
4. Test that extraction fails gracefully without mappings

**Checkpoint:** Evidence extraction requires mapping

### Phase 5: Documentation
1. Global search/replace "7-stage" → "8-stage"
2. Update `README.md`, `CAPABILITIES.md`
3. Update UX documentation files
4. Add migration notes to `CHANGELOG.md`

**Checkpoint:** Docs consistent with implementation

---

## Testing Checklist

- [ ] WorkflowProgress migration works (7→8 stage model)
- [ ] New sessions create with 8-stage workflow_progress
- [ ] Old sessions load and auto-migrate
- [ ] Stage 3 (requirement mapping) prompt works standalone
- [ ] Evidence extraction fails if mappings missing (with clear error)
- [ ] Evidence extraction succeeds with valid mappings
- [ ] Full 8-stage workflow passes end-to-end test
- [ ] All renamed imports resolve correctly
- [ ] All prompt registrations work (@mcp.prompt names)
- [ ] SessionBuilder factory supports all 8 stages
- [ ] Progress tracking shows all 8 stages correctly
- [ ] Backward compatibility: 7-stage sessions still usable

---

## Estimated Effort

### Development Time
- **Phase 1 (Foundation):** 4-6 hours
- **Phase 2 (New Prompt):** 3-4 hours
- **Phase 3 (File Renaming):** 2-3 hours
- **Phase 4 (Evidence Refactor):** 3-4 hours
- **Phase 5 (Documentation):** 2-3 hours

**Total Estimate:** 14-20 hours development + testing

### Lines of Code Impacted
- **New Code:** ~500 lines (mapping_tools.py, C_requirement_mapping.py, tests)
- **Modified Code:** ~300 lines (schemas, evidence_tools, server, state)
- **Renamed Files:** ~1000 lines (no logic changes, just file moves)
- **Documentation:** ~50 files touched (mostly find/replace)

**Total Impact:** ~1850 lines

---

## Questions to Resolve

1. **Naming Convention:** Should we rename `complete` → `completion` to match canonical spec?
   - **Recommendation:** Yes, for consistency

2. **Backward Compatibility:** How long do we support 7-stage sessions?
   - **Recommendation:** Auto-migrate indefinitely (negligible cost)

3. **UI Display:** How do we show requirement mapping status to users?
   - **Recommendation:** Matrix view (rows=requirements, cols=documents) in prompt output

4. **Mapping Confidence:** What threshold triggers "unmapped" flag?
   - **Recommendation:** <0.5 confidence = unmapped, 0.5-0.75 = partial, >0.75 = suggested

5. **Manual Mapping:** Should users be able to map via UI or only via tools?
   - **Recommendation:** Both - prompt shows suggestions, tools allow manual override

---

## Success Criteria

The refactoring is complete when:

✅ All 8 stages are represented in `WorkflowProgress` model
✅ Stage 3 (requirement mapping) has dedicated prompt and tools
✅ Evidence extraction depends on mappings (not standalone)
✅ Full integration test passes with 8 stages
✅ Old 7-stage sessions auto-migrate without errors
✅ Documentation consistently references 8-stage workflow
✅ All tests pass (existing + new)
✅ No regressions in existing functionality

---

## Next Actions

**Immediate:**
1. Review this analysis with team
2. Confirm naming conventions (`completion` vs `complete`)
3. Decide on migration strategy (auto-migrate vs manual)

**Before Coding:**
1. Write tests for mapping logic (TDD approach)
2. Define mapping confidence scoring algorithm
3. Design mapping matrix UI/UX

**Implementation Order:**
1. Start with Phase 1 (Foundation) - safest, non-breaking
2. Validate migration works on real sessions
3. Proceed through phases sequentially
4. Run full test suite after each phase

---

**Document Status:** Draft for Review
**Next Review Date:** TBD
**Owner:** Development Team
