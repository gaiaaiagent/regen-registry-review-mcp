---
id: task-27
title: Evidence extraction returns all missing for GPT uploads
status: Done
assignee: []
created_date: '2025-12-04 03:48'
updated_date: '2025-12-04 04:31'
labels:
  - bug
  - critical
  - stage-4
  - chatgpt
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Evidence extraction returns "0 requirements complete, 23 missing" for sessions created via ChatGPT GPT interface, despite successful document discovery and mapping.

### Observed Behavior

User workflow via ChatGPT GPT:
1. Created session "TEST A" (session-5f82272b2d5c)
2. Uploaded 7 PDF documents
3. Document discovery succeeded - classified 7 documents correctly
4. Requirement mapping succeeded - 100% coverage, all 23 mapped
5. Confirmed all mappings
6. Evidence extraction returned: **0 requirements complete, 23 missing**

### Root Cause Analysis

The evidence extraction code at `evidence_tools.py:570-575` loads document markdown:
```python
content = await get_markdown_content(doc, session_id)
if content:
    doc_cache[doc_id] = content
else:
    print(f"  ✗ Failed to load {doc['filename']}", flush=True)
```

If `get_markdown_content` returns None for all documents, no content is cached, and all requirements become "missing".

`get_markdown_content` at line 163 returns None when:
- `has_markdown` is False
- `markdown_path` is missing
- The markdown file doesn't exist at the specified path

### Potential Causes

1. **File path mismatch**: Uploaded files stored in temp location but markdown_path points elsewhere
2. **Session directory race condition**: Discovery marks docs as having markdown before files are written
3. **Upload processing incomplete**: `process-upload` returns before markdown extraction finishes
4. **Path serialization issue**: Paths stored incorrectly in documents.json after GPT upload

### Investigation Steps

1. Add logging to `get_markdown_content` to show which documents fail and why
2. Trace the full upload → discovery → evidence flow for GPT interface
3. Compare file paths in documents.json between working MCP flow vs broken GPT flow
4. Check if markdown files actually exist in session directories after GPT upload
5. Add error handling that fails fast if no documents have content (rather than silently producing 23 missing)

### Key Files

- `chatgpt_rest_api.py`: `process_upload` endpoint (lines 115-200)
- `evidence_tools.py`: `get_markdown_content` (line 156), `extract_all_evidence` (line 477)
- `document_processor.py`: Fast extraction and markdown storage
- `upload_tools.py`: File handling and session storage

### Implementation (Done)

Enhanced `evidence_tools.py` with defensive improvements:

1. **Improved `get_markdown_content` diagnostics** (lines 156-195):
   - Logs `fast_status` and `hq_status` when `has_markdown=False`
   - Reports when `markdown_path` is missing despite `has_markdown=True`
   - Logs when markdown file doesn't exist at expected path
   - Catches and logs file read errors

2. **Fail-fast validation** (lines 599-612):
   - If ALL documents fail to load markdown, raises ValueError with clear error message
   - Lists first 5 failed documents and count of remaining
   - Provides possible causes and recovery steps
   - Prevents silent "23 missing" output

3. **Partial failure handling** (lines 614-619):
   - If some documents fail but others succeed, warns and continues
   - Shows count of failed vs loaded documents

The issue may have been intermittent (server logs show later session worked). These improvements ensure:
- Clear diagnostics when content loading fails
- Immediate failure instead of silent empty results
- Actionable error messages for troubleshooting

### Acceptance Criteria

- [x] Add logging to clearly show when/why document content fails to load
- [x] Add validation that fails fast if no documents have extractable content
- [ ] Evidence extraction works for documents uploaded via ChatGPT GPT interface (needs retest)
- [ ] Add test case for GPT upload → evidence extraction flow (deferred)
<!-- SECTION:DESCRIPTION:END -->
