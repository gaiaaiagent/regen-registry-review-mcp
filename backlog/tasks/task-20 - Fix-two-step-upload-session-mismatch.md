---
id: task-20
title: Fix two-step upload session mismatch
status: Done
assignee: []
created_date: '2025-12-04 02:45'
labels:
  - bug
  - blocker
  - chatgpt-integration
  - session-management
dependencies: []
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The ChatGPT REST API has a flow mismatch bug where the two-step upload process creates a NEW session instead of adding files to an existing session. This causes sessions to appear empty and subsequent operations to fail.

## Problem Analysis

The GPT mixes two separate flows:

1. **Flow A (session-first)**: `POST /sessions` → upload files → discover
2. **Flow B (upload-first)**: `POST /generate-upload-url` → user uploads → `POST /process-upload` (creates session internally)

When GPT uses both flows together:
1. `POST /sessions` creates `session-A`
2. `POST /generate-upload-url` creates in-memory upload slot
3. User uploads files (stored in memory, NOT attached to session-A)
4. `POST /process-upload` calls `start_review_from_uploads()` which creates `session-B`
5. GPT calls `/sessions/session-A/map` → fails because session-A has no documents

The documents are in session-B, but GPT references session-A.

## Root Cause

`chatgpt_rest_api.py` line 1055-1060:
```python
result = await upload_tools.start_review_from_uploads(
    project_name=session["project_name"],
    files=[...],
    auto_extract=False,
)
```

`/process-upload` always creates a new session via `start_review_from_uploads()`. It has no way to add files to an existing session.

## Proposed Solution

Modify the two-step upload flow to support adding files to existing sessions:

1. Add optional `session_id` parameter to `/generate-upload-url`
2. If `session_id` is provided, `/process-upload` should add files to that session using `upload_additional_files()` instead of creating a new one
3. If no `session_id`, create new session (current behavior)
4. Update GPT instructions to pass session_id when using both flows
5. Consider: should `/sessions` be removed entirely, forcing all file uploads through the two-step flow?

## Files to Modify

- `chatgpt_rest_api.py`: Add session_id to upload flow
- GPT system prompt: Update instructions to use single flow

## Agent Synchronization

The MCP tools (`session_tools`, `upload_tools`) need to expose consistent semantics for both:
- Claude Code (MCP protocol)
- ChatGPT (REST API wrapper)

Both agents should follow the same session lifecycle:
1. Create session (optionally with documents path)
2. Add documents (via path OR upload)
3. Discover → Map → Extract → Validate → Report
<!-- SECTION:DESCRIPTION:END -->

## Implementation

**Changes to `chatgpt_rest_api.py`:**

1. Added `session_id: str | None` to `GenerateUploadUrlRequest`
2. Store `session_id` in `pending_uploads` dictionary
3. In `/process-upload`:
   - If `session_id` exists: call `upload_additional_files()` + `discover_documents()`
   - If no `session_id`: call `start_review_from_uploads()` (original behavior)
4. Updated response to include `mode: "add_to_existing"` or `mode: "create_new"`

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Two-step upload with existing session adds files to that session
- [x] #2 Two-step upload without session_id creates new session (backward compatible)
- [ ] #3 GPT can complete full workflow: create session → upload files → map → extract (needs testing)
- [x] #4 Session persistence works across server restarts (verified with task-5 fix)
- [x] #5 MCP tools and REST API have consistent session semantics
<!-- AC:END -->
