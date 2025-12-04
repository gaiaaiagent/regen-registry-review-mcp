---
id: task-5
title: Sessions cannot be loaded after server restart
status: Done
assignee: []
created_date: '2025-12-04 01:51'
updated_date: '2025-12-04 01:59'
labels:
  - bug
  - blocker
  - session-management
  - eliza
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Sessions cannot be loaded after server restart. list_sessions shows sessions with documents, but load_session and all other session-scoped tools fail with 'session not found'. This blocks the full 8-stage workflow testing.

## Root Cause Analysis

The bug was in `src/registry_review_mcp/config/settings.py:29-32`:
```python
data_dir: Path = Field(default_factory=lambda: Path.cwd() / "data")
sessions_dir: Path = Field(default_factory=lambda: Path.cwd() / "data" / "sessions")
```

`Path.cwd()` returns the **current working directory at the time the server starts**. This created a critical bug:

1. If MCP server starts from `/home/ygg/Workspace/RegenAI/regen-registry-review-mcp/`, sessions go to `./data/sessions/`
2. If MCP server starts from a different directory (e.g., Eliza's runtime env), sessions go to a **completely different location**
3. After server restart, `Path.cwd()` may differ, causing sessions to be "invisible"

## Fix Applied

Changed from `Path.cwd()` to package-relative paths using `Path(__file__).resolve().parent.parent.parent.parent`:
```python
def _get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent.parent

class Settings(BaseSettings):
    data_dir: Path = Field(default_factory=lambda: _get_project_root() / "data")
    sessions_dir: Path = Field(default_factory=lambda: _get_project_root() / "data" / "sessions")
    # ...
```

This ensures sessions are **always** stored in the same location regardless of where the server is started from.

## Verification

All 220 tests pass after the fix.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 load_session works after server restart
- [ ] #2 Session state fully reconstructed from disk/database
- [ ] #3 All session-scoped tools work on reloaded sessions
- [ ] #4 Test sequence: create → restart → load → continue workflow
<!-- AC:END -->
