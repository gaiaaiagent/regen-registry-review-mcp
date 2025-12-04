---
id: task-27
title: Cross-validation fails session-not-found after server restart
status: Open
assignee: []
created_date: '2025-12-04 03:55'
updated_date: '2025-12-04 03:55'
labels:
  - bug
  - critical
  - session-management
  - chatgpt
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Cross-validation fails with 500 error "session not found" after server restart, despite the session completing discovery, mapping, and evidence extraction successfully in the same GPT conversation.

### Observed Behavior

GPT workflow via ChatGPT:
1. Listed sessions - showed "TEST B session-1e0e3c168240"
2. Requested mapping - succeeded with 23/23 mapped at 100% coverage
3. Requested evidence extraction - succeeded with 23/23 complete
4. User exported matrix to CSV and PDF - worked
5. Requested cross-validation - **Failed with 500 error**

Server logs showed:
```
POST /sessions/session-1e0e3c168240/validate HTTP/1.1" 500 Internal Server Error
```

### Root Cause Analysis

**Dual path problem:** The codebase has two different session storage locations:

1. **XDG path** (current): `~/.local/share/registry-review-mcp/sessions/`
   - Used after settings.py was updated to XDG standard
   - Currently **empty**

2. **Project path** (legacy): `./data/sessions/`
   - Used by older server instances
   - Contains `session-5f82272b2d5c` (TEST A) with full data

**Missing session:** `session-1e0e3c168240` (TEST B) exists in **neither location**.

The session was visible to `list_sessions` during the GPT conversation, which means:
- Either the session was stored in memory only
- Or the session was deleted during server restart
- Or the session was stored in a third location (temp directory?)

### Timeline Analysis

1. User creates TEST B session via GPT
2. Discovery, mapping, evidence extraction all work
3. Claude restarts REST API server at 19:49 (for code update)
4. New server uses XDG paths, can't see old sessions
5. Cross-validation fails - session-1e0e3c168240 not found

### Key Evidence

```bash
# XDG sessions directory (current config)
$ ls ~/.local/share/registry-review-mcp/sessions/
(empty)

# Project sessions directory (legacy)
$ ls ./data/sessions/
session-5f82272b2d5c  # TEST A exists here

# TEST B session-1e0e3c168240 exists nowhere
$ find / -name "*1e0e3c168240*"
(no results)
```

### Key Files

- `src/registry_review_mcp/config/settings.py:77` - sessions_dir uses XDG path
- `src/registry_review_mcp/utils/state.py:26` - StateManager uses settings.sessions_dir
- `chatgpt_rest_api.py:379-398` - cross_validate endpoint

### Fix Options

1. **Migrate legacy sessions**: Add startup logic to migrate sessions from `./data/sessions/` to XDG location
2. **Fall-through lookup**: Check both XDG and legacy paths when loading sessions
3. **Environment variable**: Allow REGISTRY_REVIEW_SESSIONS_DIR to override path
4. **Session backup**: Persist session state more aggressively with backups

### Related Tasks

- task-5: Sessions cannot be loaded after server restart (marked Done but not fully fixed)
- task-16: Evidence extraction returns all missing for GPT uploads

### Acceptance Criteria

- [ ] Sessions created before server restart are accessible after restart
- [ ] Sessions persist to disk immediately (not just in memory)
- [ ] Cross-validation works for sessions created via ChatGPT GPT interface
- [ ] Legacy sessions in `./data/sessions/` are migrated or accessible
<!-- SECTION:DESCRIPTION:END -->
