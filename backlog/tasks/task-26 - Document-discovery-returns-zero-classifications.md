---
id: task-26
title: Document discovery returns zero classifications after successful upload
status: Resolved
assignee: []
created_date: '2025-12-04 04:00'
labels:
  - bug
  - critical
  - document-discovery
dependencies: []
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
GPT agent successfully:
1. Created session "TEST B" (session-55bd0419af27 → session-1e0e3c168240)
2. Generated upload URL
3. User uploaded 7 Botany Farm documents
4. Upload confirmed with all 7 files listed

But document discovery returned **zero classifications**.

## Observed Behavior

GPT Response after running discovery:
> "It looks like the system scanned your uploaded files but couldn't classify them automatically — likely because the discovery engine couldn't extract metadata from the PDFs yet."

The 7 documents uploaded:
1. Methodology of the Farm Carbon Calculator - April 2024.pdf
2. 4998Botany23_GHG_Emissions_30_Sep_2023.pdf
3. 4998Botany23 Soil Organic Carbon Project Public Monitoring Report 2023.pdf
4. 4997Botany22 Public Project Plan.pdf
5. Botany Farm Project Registration Registry Agent Review.pdf
6. Botany Farm Credit Issuance Registry Agent Review 2023 Monitoring.pdf
7. 4997Botany22 Soil Organic Carbon Project Public Baseline Report 2022.pdf

## Expected Behavior

Document discovery should:
1. Extract text from each PDF (fast extraction)
2. Classify each document by type (Project Plan, Monitoring Report, etc.)
3. Return classification results with confidence scores

## Potential Causes

1. **Fast extraction not triggered on upload** - PDFs uploaded but markdown not extracted
2. **PDF text extraction failing silently** - pymupdf4llm errors suppressed
3. **Document classifier receiving empty content** - No text to analyze
4. **Path issues** - Documents stored but not found by discovery
5. **Session ID mismatch** - Note: Two session IDs mentioned (55bd0419af27 and 1e0e3c168240)

## Session ID Discrepancy

Interesting: GPT shows two different session IDs:
- Session created: `session-55bd0419af27`
- Upload confirmed: `session-1e0e3c168240`

This could indicate:
- Session was recreated during upload flow
- OR upload created a new session
- OR display bug in GPT

## Investigation Steps

1. Check server logs for discovery errors
2. Verify documents exist in session directory
3. Check if fast extraction ran on upload
4. Check document classifier logic
5. Test discovery manually via curl
6. Investigate session ID discrepancy

## ROOT CAUSE IDENTIFIED

**Hidden file filter was blocking XDG paths**

In `document_tools.py:493-495`:
```python
# Old code - blocked all XDG paths
if any(part.startswith(".") for part in file_path.parts):
    continue
```

The XDG path `/home/ygg/.local/share/registry-review-mcp/...` contains `.local` which triggered the "hidden files" filter, blocking ALL documents.

## Fix Applied

Changed to only check the filename, not the full path:
```python
# Fixed code - only checks filename
if file_path.name.startswith("."):
    continue
```

This correctly skips hidden files like `.DS_Store` while allowing files in XDG directories like `.local`.

## Verification

After fix, discovery correctly finds all 7 documents:
- documents_found: 7
- classifications: registry_review (2), project_plan (1), baseline_report (1), methodology_reference (1), monitoring_report (1), ghg_emissions (1)
- fast_status: "complete" for all documents
- has_markdown: true for all documents
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Root cause identified (hidden file filter blocked XDG paths)
- [x] #2 Document discovery correctly classifies uploaded PDFs (7/7 classified)
- [x] #3 Fast extraction runs automatically on document upload (all documents have has_markdown: true)
- [ ] #4 Session ID remains consistent throughout workflow (separate issue - GPT UI behavior)
<!-- AC:END -->
