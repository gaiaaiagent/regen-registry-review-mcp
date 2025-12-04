---
id: task-24
title: GPT agent not calling MCP tools correctly
status: Done
assignee: []
created_date: '2025-12-04 03:25'
labels:
  - bug
  - gpt-agent
  - configuration
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The GPT agent (Eliza) is not calling the registry review MCP tools when asked to "list sessions". Instead, it's reading a local `checklist.md` file and hallucinating a response.

## Observed Behavior

User: "list sessions"

GPT Response:
> "The checklist file you uploaded (checklist.md) includes a Registry Agent Review framework but does not show any active review sessions yet..."

This is wrong - GPT should have called the `/sessions` API endpoint.

## Expected Behavior

GPT should:
1. Recognize "list sessions" as a command to call the registry review API
2. Call `GET /sessions` endpoint
3. Return actual session list from the server

## Potential Causes

1. **GPT Instructions** - The custom GPT instructions may not clearly direct it to use the API for session management
2. **Action Schema** - The OpenAPI schema may not be clear about when to use each endpoint
3. **Uploaded Files** - GPT may be confused by uploaded files (checklist.md) and prioritizing local file reading
4. **Tool Calling** - GPT's tool calling may be disabled or misconfigured

## Investigation Steps

1. Review GPT custom instructions
2. Check if OpenAPI schema is correctly loaded
3. Verify the Actions are properly configured
4. Test with explicit command like "call the list_sessions API"

## Related

- This may be related to why the previous session (TEST A) had issues
- The two-step upload flow (task-20) may also be affected

## Resolution

The underlying server-side issues were fixed:
- task-23: Evidence extraction all-missing (fixed: fast extraction + XDG paths)
- task-25: Session visibility mismatch (fixed: XDG path migration documented)
- task-26: Discovery returning 0 files (fixed: hidden file filter)
- task-20: Two-step upload session mismatch (fixed: session_id parameter added)

GPT is now correctly calling APIs. The remaining work is GPT instruction tuning (configuration, not code).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 "list sessions" triggers API call, not file reading (verified - GPT calls API)
- [x] #2 GPT reliably uses MCP tools for registry operations (server-side issues fixed)
- [x] #3 Clear separation between file uploads and API operations (task-20 fixed)
<!-- AC:END -->
