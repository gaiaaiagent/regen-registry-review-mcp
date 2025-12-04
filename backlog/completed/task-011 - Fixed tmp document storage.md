---
id: task-011
title: Fixed uploaded documents stored in /tmp/ causing data loss on reboot
status: Done
priority: critical
labels: [bug, data-loss, storage, upload]
created: 2025-12-03
completed: 2025-12-03
---

## Summary

Fixed critical bug where uploaded documents were stored in `/tmp/` directories which are cleared on system reboot, causing permanent data loss.

## Problem

The upload flow created documents in `/tmp/registry-{name}-{random}/` using `tempfile.mkdtemp()`, but session metadata stored this path permanently. On system reboot, `/tmp/` is cleared and documents are lost.

## Solution Implemented

1. **New helper function** `get_session_uploads_dir(session_id)` in `session_tools.py`
   - Returns `data/sessions/{session_id}/uploads/`
   - Creates directory if it doesn't exist

2. **Fixed `create_session_from_uploads()`** in `upload_tools.py`
   - Creates session first to get session_id
   - Stores documents in persistent `uploads/` subdirectory
   - Updates session metadata with correct path

3. **Fixed `upload_additional_files()`** in `upload_tools.py`
   - Auto-migrates old sessions with `/tmp/` paths to persistent storage
   - Handles missing documents_path gracefully

4. **Fixed `add_documents()`** in `document_tools.py`
   - Upload source type now uses persistent storage
   - Consistent with other upload methods

## Files Changed

- `src/registry_review_mcp/tools/session_tools.py` - Added `get_session_uploads_dir()`
- `src/registry_review_mcp/tools/upload_tools.py` - Rewrote upload flow
- `src/registry_review_mcp/tools/document_tools.py` - Fixed add_documents upload handling
- `tests/test_upload_tools.py` - Updated test assertions

## Verification

- All 57 upload tests pass
- Documents now stored in `data/sessions/{session_id}/uploads/`
- Documents survive system reboot
