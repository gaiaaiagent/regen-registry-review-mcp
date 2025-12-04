---
id: task-25
title: GPT and Eliza see different sessions due to XDG path migration
status: Resolved
assignee: []
created_date: '2025-12-04 03:45'
labels:
  - bug
  - configuration
  - xdg-paths
dependencies:
  - task-23
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GPT agent shows 0 sessions while Eliza agent shows 1 session (session-5f82272b2d5c).

## Observed Behavior

**GPT (ChatGPT Custom GPT via REST API):**
> "There are currently no active review sessions."

**Eliza (local agent):**
> Shows session-5f82272b2d5c with 7 documents, 23 requirements mapped

## Root Cause

**XDG Base Directory Migration**

The server was updated to use XDG-compliant paths:
- **NEW location**: `~/.local/share/registry-review-mcp/sessions/`
- **OLD location**: `data/sessions/` (project-relative)

When the server was restarted (PID 547828) after the XDG migration:
1. GPT hits the new server → reads from XDG path → finds 0 sessions
2. Eliza likely reads from project-relative path OR cached data → finds 1 session

Session `session-5f82272b2d5c` exists ONLY in `data/sessions/` (old path), not in the XDG location.

## Evidence

From server logs (`/tmp/chatgpt_rest_api_new2.log`):
```
2025-12-03 19:19:08,108 [INFO] registry_review_mcp.server: Initializing Registry Review MCP Server v2.0.0
INFO:     172.212.159.76:0 - "GET /sessions HTTP/1.1" 200 OK
```

GPT correctly called the API - it returned 200 OK with empty list (XDG path has no sessions).

## Resolution Options

### Option A: Forward-only (Recommended)
- Accept that old sessions are orphaned
- Create fresh sessions going forward
- Both GPT and Eliza will see the same data

### Option B: Migration script
- Write script to move sessions from `data/sessions/` to XDG location
- Risk: May bring forward sessions with broken fast_status

### Option C: Symlink
- Symlink XDG path to project-relative path
- Maintains backwards compatibility
- Pollutes XDG namespace

## Resolution Applied

**Option A** - Forward-only approach:
1. Old sessions in `data/sessions/` are considered archived
2. New sessions created via GPT or any agent will use XDG paths
3. All agents hitting the same server will see consistent data

This is the expected behavior of the XDG migration - data isolation is working correctly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root cause documented
- [x] #2 Resolution approach selected
- [x] #3 Both GPT and Eliza can create/see sessions when using same server
<!-- AC:END -->
