---
id: task-23
title: Evidence extraction returns all missing despite successful mapping
status: Resolved
assignee: []
created_date: '2025-12-04 03:20'
labels:
  - bug
  - critical
  - evidence-extraction
dependencies: []
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GPT agent successfully:
1. Created session "TEST A" (session-5f82272b2d5c)
2. Uploaded 7 Botany Farm documents
3. Discovered all 7 documents with correct classifications
4. Mapped all 23 requirements (100% coverage, high confidence)
5. Confirmed all mappings

But evidence extraction returned **ALL 23 requirements as "missing"**.

## Symptoms

- Mapping works (documents linked to requirements)
- Evidence extraction runs without error
- All requirements show status: "missing"
- No evidence snippets extracted from any document

## Potential Causes

1. **LLM extraction disabled** - `llm_extraction_enabled` might be False
2. **Document markdown not available** - `has_markdown` might be False after fast extraction
3. **Server not restarted** - Recent .env changes (Haiku model) not picked up
4. **XDG path mismatch** - Session created but documents stored elsewhere
5. **API errors suppressed** - LLM calls failing silently

## Investigation Steps

1. Check if session exists in XDG path
2. Check if documents have `has_markdown: true`
3. Check server logs for API errors
4. Verify `llm_extraction_enabled` setting
5. Test evidence extraction manually

## ROOT CAUSE IDENTIFIED

**Two issues combined:**

1. **Fast extraction failed** - All 7 documents have `fast_status: "failed"` with error:
   ```
   "PyMuPDF4LLM not installed. Install with: uv pip install pymupdf4llm"
   ```
   This is a **false error** - pymupdf4llm IS installed. The server instance that ran at 18:56 had some transient import issue. After server restart, extraction works.

2. **Path mismatch** - Session was created in OLD path (`data/sessions/`) but new server uses XDG path (`~/.local/share/registry-review-mcp/sessions/`). The XDG migration is working correctly - this is expected isolation.

## Fix Applied

1. ✅ Server restarted (PID 547828)
2. ✅ Fast extraction verified working
3. ✅ XDG paths active
4. **User action**: Create fresh session in GPT (old session is orphaned)

## Session Details

- Session ID: session-5f82272b2d5c
- Project: TEST A
- Documents: 7 (Botany Farm)
- Requirements: 23 (all mapped, all missing evidence)
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root cause identified (fast extraction transient failure + XDG path migration)
- [x] #2 Evidence extraction returns actual evidence for mapped documents (verified with new sessions)
- [ ] #3 Add better error logging if LLM calls fail (deferred - not critical)
<!-- AC:END -->

## Related Tasks

- task-25: GPT/Eliza session visibility mismatch (same root cause)
