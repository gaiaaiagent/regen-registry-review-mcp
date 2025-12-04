---
id: task-28
title: Session status field not synchronized with workflow_progress
status: Done
assignee: []
created_date: '2025-12-04 04:50'
labels:
  - bug
  - architecture
  - data-model
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The session `status` field shows "initialized" even after multiple workflow stages have completed. This creates confusing UI where the status says "Initialized" but checkmarks show stages 1-3 complete.

## Root Cause

Two parallel status tracking mechanisms exist but are NOT synchronized:

| Mechanism | Set At | Updated During Workflow? | Used for Decisions? |
|-----------|--------|--------------------------|---------------------|
| `status` string | Session creation | NO (except Stage 8) | Never |
| `workflow_progress` dict | Each stage | YES | Always |

### Code Evidence

**Session creation** (`session_tools.py:98`):
```python
status="initialized",  # Set once, never updated
workflow_progress=WorkflowProgress(initialize="completed"),
```

**Stage 2-7 updates** (e.g., `mapping_tools.py:145`):
```python
state_manager.update_json("session.json", {
    "workflow_progress.requirement_mapping": "completed",
    # NOTE: "status" field NOT updated
})
```

**Only Stage 8** updates status (`H_completion.py:149`):
```python
session["status"] = "completed"
```

## Impact

- GPT agent shows "Status: Initialized" with 3 green checkmarks
- Confusing UX for users
- Spec (2025-11-20) expected status to reflect current stage

## Design Decision

The implementation chose `workflow_progress` (granular, type-safe) over single `status` field, but forgot to deprecate or synchronize the status field.

## Proposed Fix: Option A (Derive Status)

Add helper function to derive status from workflow_progress:

```python
def get_derived_status(workflow_progress: dict) -> str:
    """Derive human-readable status from workflow progress."""
    stages = [
        ("completion", "Completed"),
        ("human_review", "In Human Review"),
        ("report_generation", "Report Generated"),
        ("cross_validation", "Validated"),
        ("evidence_extraction", "Evidence Extracted"),
        ("requirement_mapping", "Requirements Mapped"),
        ("document_discovery", "Documents Discovered"),
        ("initialize", "Initialized"),
    ]

    for stage_key, status_label in stages:
        if workflow_progress.get(stage_key) == "completed":
            return status_label

    return "Initialized"
```

Use this in REST API response instead of raw `status` field.

## Alternative Fixes

**Option B**: Update status at each stage completion (6 files to modify)
**Option C**: Remove status field entirely (breaking change)
**Option D**: Document current behavior (doesn't fix UX)

## Resolution

**Implemented Option A**: Added `get_derived_status()` and `apply_derived_status()` helper functions in `chatgpt_rest_api.py:39-72`. The REST API endpoints `/sessions` and `/sessions/{session_id}` now derive status from `workflow_progress` before returning responses.

**Example**: Session with `workflow_progress.evidence_extraction: completed` now returns `"status": "Evidence Extracted"` instead of `"initialized"`.

## Related Issues

- Report generation (`report_tools.py`) doesn't update session state at all
- Human review doesn't update `workflow_progress.human_review`
- `updated_at` timestamp not maintained after creation
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Session status reflects actual workflow progress (derived from workflow_progress)
- [x] #2 GPT agent shows consistent status with checkmarks (status now matches progress)
- [x] #3 Status values match spec: "Initialized", "Documents Discovered", "Requirements Mapped", etc.
<!-- AC:END -->
