# Registry Review MCP - State Machine Analysis

## System States

### Session States
- `NO_SESSION` - No session exists
- `INITIALIZED` - Session created, no documents discovered
- `DOCUMENTS_DISCOVERED` - Documents found and classified
- `EVIDENCE_EXTRACTED` - Requirements mapped to evidence
- `VALIDATED` - Cross-validation complete
- `REPORT_GENERATED` - Reports created
- `HUMAN_REVIEWED` - Flagged items reviewed (optional)
- `COMPLETED` - Review finalized

### Workflow Stage States
Each stage: `pending` → `in_progress` → `completed`

---

## State Transition Matrix

| Current State | Prompt Called | Expected Behavior | Current Behavior | Issues/Improvements |
|--------------|---------------|-------------------|------------------|---------------------|
| **NO_SESSION** | `/initialize` | ✅ Create session | ✅ Works | Perfect |
| NO_SESSION | `/document-discovery` | Create session inline | ✅ Works (can create) | Perfect |
| NO_SESSION | `/evidence-extraction` | Guide to create session | ✅ Error + guidance | Perfect |
| NO_SESSION | `/cross-validation` | Guide to create session | ✅ Error + guidance | Perfect |
| NO_SESSION | `/report-generation` | Guide to create session | ✅ Error + guidance | Perfect |
| NO_SESSION | `/human-review` | Guide to create session | ✅ Error + guidance | Perfect |
| NO_SESSION | `/complete` | Guide to create session | ✅ Error + guidance | Perfect |
| **INITIALIZED** | `/initialize` | Warn about existing session | ❌ Creates duplicate | **FIX NEEDED** |
| INITIALIZED | `/document-discovery` | ✅ Discover documents | ✅ Works | Perfect |
| INITIALIZED | `/evidence-extraction` | Require discovery first | ❓ Unknown | **CHECK NEEDED** |
| INITIALIZED | `/cross-validation` | Require evidence first | ❓ Unknown | **CHECK NEEDED** |
| INITIALIZED | `/report-generation` | Require evidence first | ✅ Checks | Good |
| INITIALIZED | `/human-review` | Require validation first | ✅ Checks | Good |
| INITIALIZED | `/complete` | Require report first | ✅ Checks | Good |
| **DOCUMENTS_DISCOVERED** | `/initialize` | Warn about existing session | ❌ Creates duplicate | **FIX NEEDED** |
| DOCUMENTS_DISCOVERED | `/document-discovery` | Re-run discovery | ✅ Works (idempotent) | Perfect |
| DOCUMENTS_DISCOVERED | `/evidence-extraction` | ✅ Extract evidence | ✅ Works | Perfect |
| DOCUMENTS_DISCOVERED | `/cross-validation` | Require evidence first | ❓ Unknown | **CHECK NEEDED** |
| DOCUMENTS_DISCOVERED | `/report-generation` | Require evidence first | ✅ Checks | Good |
| DOCUMENTS_DISCOVERED | `/human-review` | Require validation first | ✅ Checks | Good |
| DOCUMENTS_DISCOVERED | `/complete` | Require report first | ✅ Checks | Good |
| **EVIDENCE_EXTRACTED** | `/evidence-extraction` | Re-run extraction | ✅ Works (idempotent) | Perfect |
| EVIDENCE_EXTRACTED | `/cross-validation` | ✅ Validate | ✅ Works | Perfect |
| EVIDENCE_EXTRACTED | `/report-generation` | ✅ Generate report | ✅ Works (can skip validation) | **DESIGN QUESTION** |
| EVIDENCE_EXTRACTED | `/human-review` | Require validation first | ✅ Checks | Good |
| EVIDENCE_EXTRACTED | `/complete` | Require report first | ✅ Checks | Good |
| **VALIDATED** | `/cross-validation` | Re-run validation | ✅ Works (idempotent) | Perfect |
| VALIDATED | `/report-generation` | ✅ Generate report | ✅ Works | Perfect |
| VALIDATED | `/human-review` | ✅ Review flags | ✅ Works | Perfect |
| VALIDATED | `/complete` | Require report first | ✅ Checks | Good |
| **REPORT_GENERATED** | `/report-generation` | Re-generate report | ✅ Works (idempotent) | Perfect |
| REPORT_GENERATED | `/human-review` | Show flagged items | ✅ Works (optional) | Perfect |
| REPORT_GENERATED | `/complete` | ✅ Finalize | ✅ Works | Perfect |
| **COMPLETED** | Any prompt | Offer to start new session? | ❓ Unknown | **UX ENHANCEMENT** |

---

## Critical Issues Identified

### 1. Duplicate Session Creation (HIGH PRIORITY)

**Problem:** User can run `/initialize` multiple times, creating duplicate sessions.

**Current Behavior:**
```
Session 1: session-abc123 (Botany Farm)
Run /initialize again...
Session 2: session-def456 (Botany Farm) ← Duplicate!
```

**Expected Behavior:**
- Detect if a session with the same `project_name` + `documents_path` exists
- Offer to resume existing session or create new one
- Warn about potential duplicate

**Fix:**
```python
# In initialize.py
existing_sessions = [s for s in state_manager.list_sessions()
                     if s['project_name'] == project_name
                     and s['documents_path'] == documents_path]

if existing_sessions:
    return """# ⚠️ Session Already Exists

Found existing session for this project:

**Session ID:** {existing_sessions[0]['session_id']}
**Created:** {existing_sessions[0]['created_at']}
**Status:** {existing_sessions[0]['status']}

## Options

1. **Resume existing session:**
   Use any prompt without specifying session_id (auto-selects most recent)

2. **Create new session anyway:**
   Use `create_session` tool directly with `force=True`

3. **Delete old session first:**
   `delete_session {existing_sessions[0]['session_id']}`
"""
```

### 2. Missing Precondition Checks

**Problem:** Some prompts may not check all prerequisites.

**Fix Needed:** Audit all prompts for:
- `/evidence-extraction` - Must check `document_discovery == "completed"`
- `/cross-validation` - Must check `evidence_extraction == "completed"`

### 3. Completed Session Behavior

**Problem:** After `/complete`, what happens if user runs prompts again?

**Options:**
1. **Reopenable** - Allow re-running any stage, mark as "in_progress" again
2. **Locked** - Require explicit "reopen" action
3. **Read-only** - Only allow viewing, not modification

**Recommendation:** Reopenable with warning

```python
if session["status"] == "completed":
    return """# ⚠️ Session Already Completed

This session was completed on {completed_at}.

## Options

1. **View results:**
   - `/report-generation` - View reports
   - `/human-review` - View flagged items
   - `/complete` - View completion summary

2. **Reopen for changes:**
   Continue with this prompt to reopen and {action}

   ⚠️ This will mark the session as "in_progress" again.

3. **Start fresh:**
   Create a new session with `/initialize`
"""
```

---

## UX Enhancement Opportunities

### 1. Progress Indicator

Show workflow progress in every prompt:

```
## Workflow Progress

✅ 1. Initialize
✅ 2. Document Discovery (7 documents)
✅ 3. Evidence Extraction (21/23 requirements)
🔄 4. Cross-Validation ← YOU ARE HERE
⏸️ 5. Report Generation
⏸️ 6. Human Review
⏸️ 7. Complete
```

### 2. Smart Next Steps

Instead of always showing `/next-prompt`, analyze state and suggest:

```python
def suggest_next_steps(session):
    progress = session['workflow_progress']

    if progress['document_discovery'] == 'completed' and progress['evidence_extraction'] == 'pending':
        return "`/evidence-extraction` - Map requirements to discovered documents"

    if progress['evidence_extraction'] == 'completed' and progress['cross_validation'] == 'pending':
        return "`/cross-validation` - Validate consistency across documents (optional but recommended)"

    if progress['evidence_extraction'] == 'completed' and progress['report_generation'] == 'pending':
        return "`/report-generation` - Generate review reports"

    # ... etc
```

### 3. Idempotency Warnings

When re-running a completed stage:

```
⚠️ **Note:** This stage was already completed on 2025-11-13 12:30.

Re-running will overwrite previous results.

Continue? (Results will be regenerated with current data)
```

### 4. Dependency Visualization

Show what's blocking progress:

```
## Cannot Proceed

❌ Human Review requires:
   ✅ Evidence extraction (completed)
   ❌ Cross-validation (not run)

**Next step:** Run `/cross-validation` first
```

### 5. Session Health Check

Add a `/status` or `/health-check` prompt:

```markdown
# Session Health Check

**Project:** Botany Farm 2022-2023
**Session:** session-abc123
**Status:** in_progress

## Workflow Status

✅ Initialize - Completed
✅ Document Discovery - 7 documents found
✅ Evidence Extraction - 21/23 requirements covered (91%)
⚠️ Cross-Validation - 3 items flagged for review
⏸️ Report Generation - Not started
⏸️ Human Review - Waiting for report
⏸️ Complete - Waiting for human review

## Issues Detected

⚠️ 2 requirements missing evidence:
   - REQ-015: Baseline soil carbon measurements
   - REQ-018: Additionality demonstration

⚠️ 3 validation items need review:
   - Date alignment warning
   - Land tenure name variation
   - Project ID format inconsistency

## Recommended Next Steps

1. Review missing requirements - check if evidence is in documents
2. Run `/cross-validation` to complete validation
3. Review flagged items with `/human-review`
4. Generate final report with `/report-generation`
```

---

## State Transition Rules (Formal)

### Valid Transitions

```
NO_SESSION
  ├─→ INITIALIZED (/initialize, /document-discovery)
  └─→ error (all other prompts)

INITIALIZED
  ├─→ DOCUMENTS_DISCOVERED (/document-discovery)
  ├─→ INITIALIZED (re-run /initialize with warning)
  └─→ error (evidence/validation/report/review/complete)

DOCUMENTS_DISCOVERED
  ├─→ EVIDENCE_EXTRACTED (/evidence-extraction)
  ├─→ DOCUMENTS_DISCOVERED (re-run /document-discovery)
  └─→ error (validation/report without evidence)

EVIDENCE_EXTRACTED
  ├─→ VALIDATED (/cross-validation) [optional]
  ├─→ REPORT_GENERATED (/report-generation) [can skip validation]
  └─→ EVIDENCE_EXTRACTED (re-run /evidence-extraction)

VALIDATED
  ├─→ REPORT_GENERATED (/report-generation)
  ├─→ HUMAN_REVIEWED (/human-review) [if flags exist]
  └─→ VALIDATED (re-run /cross-validation)

REPORT_GENERATED
  ├─→ HUMAN_REVIEWED (/human-review) [optional]
  ├─→ COMPLETED (/complete)
  └─→ REPORT_GENERATED (re-run /report-generation)

HUMAN_REVIEWED
  ├─→ COMPLETED (/complete)
  └─→ REPORT_GENERATED (re-generate with notes)

COMPLETED
  ├─→ any state (reopenable with warning)
  └─→ COMPLETED (view-only operations)
```

### Linearization Options

**Option A: Strict Linear (Current)**
```
Initialize → Discovery → Evidence → Validation → Report → Review → Complete
```
- Pros: Simple, predictable
- Cons: Inflexible, validation optional but feels required

**Option B: Flexible with Required Core**
```
Required: Initialize → Discovery → Evidence → Report → Complete
Optional: Validation (before Report)
Optional: Human Review (after Report, before Complete)
```
- Pros: Clear requirements, flexibility for power users
- Cons: More complex state management

**Option C: DAG with Dependencies**
```
Initialize → Discovery → Evidence ─┬→ Report → Complete
                                    └→ Validation → Report

Human Review can run after Report if validation was run
```
- Pros: Maximum flexibility
- Cons: Complex to implement, harder to explain

**Recommendation:** Option B with clear messaging

---

## Implementation Plan

### Phase 1: Critical Fixes (P0)
1. ✅ Add duplicate session detection to `/initialize`
2. ✅ Add precondition checks to all prompts
3. ✅ Add completed session handling

### Phase 2: UX Enhancements (P1)
1. ✅ Add progress indicator to all prompts
2. ✅ Smart next step suggestions
3. ✅ Idempotency warnings
4. ✅ Add `/status` health check prompt

### Phase 3: Polish (P2)
1. Session resumption after completion
2. Partial rollback (e.g., re-run evidence without losing validation)
3. Session comparison (diff between two reviews)
4. Session templates (save common configurations)

---

## Testing Matrix

| State | Prompt | Expected Result | Test Status |
|-------|--------|----------------|-------------|
| NO_SESSION | /initialize | Create session | ✅ Tested |
| NO_SESSION | /evidence-extraction | Error + guide | ⏳ Need test |
| INITIALIZED | /initialize | Duplicate warning | ❌ No test |
| INITIALIZED | /evidence-extraction | Error + guide | ⏳ Need test |
| DOCUMENTS_DISCOVERED | /complete | Error + guide | ⏳ Need test |
| EVIDENCE_EXTRACTED | /report-generation | Generate report | ✅ Tested |
| VALIDATED | /complete | Error + guide | ⏳ Need test |
| REPORT_GENERATED | /complete | Finalize | ⏳ Need test |
| COMPLETED | /evidence-extraction | Reopen warning | ❌ No test |

---

## Edge Cases

### 1. Documents Change During Review

**Scenario:** User runs discovery, then adds/removes documents, then runs discovery again.

**Current Behavior:** Overwrites `documents.json`

**Issues:**
- Evidence mappings may reference deleted documents
- New documents not included in evidence

**Solution:** Detect changes and warn:
```
⚠️ Documents have changed since last discovery!

Added: 2 files
Removed: 1 file
Modified: 0 files

Re-running evidence extraction is recommended to include new documents.
```

### 2. Concurrent Sessions

**Scenario:** User creates two sessions for different projects, switches between them.

**Current Behavior:** Auto-selection picks most recent (by timestamp)

**Issues:**
- User may accidentally work on wrong session
- No clear indication which session is active

**Solution:**
- Show session selection at top of every prompt
- Add "pin active session" feature
- Warn if switching sessions mid-workflow

### 3. Session Corruption

**Scenario:** State file becomes corrupted or invalid.

**Current Behavior:** JSON parse error, crashes prompt

**Solution:**
- Validate session schema on load
- Offer to repair or create backup
- Never delete corrupted sessions, mark as "corrupted"

### 4. Long-Running Workflows

**Scenario:** User starts review, comes back days later.

**Current Behavior:** Session works but may feel "stale"

**Issues:**
- Documents may have changed
- User forgets where they left off

**Solution:**
- Show "last activity" timestamp
- Offer to refresh/re-validate if >24 hours old
- Session expiration policy (configurable)

---

## Recommendations Summary

### High Priority (Do Now)
1. ✅ Add duplicate session detection
2. ✅ Add comprehensive precondition checks
3. ✅ Add progress indicators to all prompts
4. ✅ Handle completed session reopening

### Medium Priority (Next Sprint)
1. Add `/status` health check prompt
2. Smart next-step suggestions
3. Idempotency warnings
4. Session change detection

### Low Priority (Future)
1. Session templates
2. Session comparison
3. Partial rollback
4. Advanced session management (pin, archive, tag)

---

**Analysis Date:** 2025-11-13
**Analyst:** Development Team
**Status:** Draft - Ready for Review
