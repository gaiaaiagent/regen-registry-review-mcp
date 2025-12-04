---
id: task-29
title: Recurring session data loss - audit and prevention
status: Open
assignee: []
created_date: '2025-12-04 06:40'
labels:
  - bug
  - critical
  - data-safety
  - recurring
dependencies: []
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Production session data has been lost AGAIN despite safeguards implemented in task-21, task-30, and task-32. This is the third occurrence of this issue.

## Incident Timeline (2025-12-04)

```
21:12 - API server started (PID 730456), session-d7f74793b886 existed
21:12 - pytest run #1 (243 passed, used /tmp isolation)
21:46 - pytest run #2 (243 passed)
22:22 - Last API call on session-d7f74793b886 (validate endpoint, 200 OK)
22:28 - XDG sessions directory modified (timestamp shows change)
22:34+ - GET /sessions returns empty list - ALL SESSIONS GONE
```

## Evidence

1. **Server logs show NO DELETE calls** - grep found no DELETE HTTP requests
2. **XDG directory empty** - `~/.local/share/registry-review-mcp/sessions/` contains nothing
3. **Legacy directory untouched** - `data/sessions/` still has session-b30def7be221
4. **Pytest isolation verified** - conftest.py correctly sets XDG_DATA_HOME to /tmp

## Gaps in Existing Safeguards

### Gap 1: `safe_rmtree` Not Used Everywhere

`session_tools.py:217` uses `shutil.rmtree()` directly:
```python
# Line 217 - BYPASSES safe_delete guard!
shutil.rmtree(session_dir)
```

Should use:
```python
from registry_review_mcp.utils.safe_delete import safe_rmtree
safe_rmtree(session_dir, force=True)  # force=True for intentional deletes
```

### Gap 2: No Deletion Audit Trail

When sessions ARE deleted (intentionally or not), there's no log entry. We can't trace what happened.

### Gap 3: Incomplete Acceptance Criteria

Both task-5 and task-21 are marked "Done" but their acceptance criteria checkboxes are NOT checked:
- task-5: "load_session works after server restart" - NOT VERIFIED
- task-21: "Running pytest while server is active does NOT delete production sessions" - NOT VERIFIED

### Gap 4: No File System Monitoring

No mechanism to detect unexpected file deletions in real-time.

## Root Cause Hypotheses

1. **Stale process with old settings** - A Python process imported settings before XDG migration
2. **pytest race condition** - Despite isolation, some edge case leaked through
3. **Manual/external deletion** - OS cleanup, user action, or GPT-requested delete
4. **Import side-effect** - Some module initialization triggers unexpected behavior

## Proposed Fixes

### Immediate (task-29a)
1. Add deletion audit logging to `session_tools.delete_session()`
2. Replace `shutil.rmtree` with `safe_rmtree` in session_tools.py
3. Add file system watcher for sessions directory (development mode)

### Short-term (task-29b)
1. Add `--audit` flag to API server that logs ALL file operations
2. Create session backup before any destructive operation
3. Add soft-delete (move to trash) before hard delete

### Long-term (task-29c)
1. Move session storage to SQLite/database with transaction logs
2. Add session recovery mechanism from backups
3. Implement proper audit trail with actor attribution

## Investigation Commands

```bash
# Check for any process that might have deleted files
sudo ausearch -f ~/.local/share/registry-review-mcp/sessions/ -ts today

# Monitor sessions directory for changes
inotifywait -m -r ~/.local/share/registry-review-mcp/sessions/

# Find all rmtree/unlink calls in codebase
grep -rn "shutil.rmtree\|\.unlink(" src/

# Check for zombie processes with settings imported
pgrep -af "python.*registry"
```

## Related Issues

- task-5: Sessions cannot be loaded after server restart (REGRESSED?)
- task-21: Fix pytest production data isolation (INSUFFICIENT?)
- task-27: Cross-validation fails session-not-found after server restart
- task-30: Production path deletion guard (NOT ENFORCED EVERYWHERE)
- task-32: Test isolation audit and hardening
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 All `shutil.rmtree` calls in src/ replaced with `safe_rmtree`
- [ ] #2 Deletion audit log created (who/what/when/where)
- [ ] #3 Session backup created before any delete operation
- [ ] #4 File system monitoring active in development mode
- [ ] #5 Root cause identified and documented
- [ ] #6 No session data loss for 7 consecutive days of active use
<!-- AC:END -->
