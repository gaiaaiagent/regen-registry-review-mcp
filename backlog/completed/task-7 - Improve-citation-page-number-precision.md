---
id: task-7
title: Improve citation page number precision
status: Done
assignee: []
created_date: '2025-12-04 01:59'
completed_date: '2025-12-04 02:11'
labels:
  - enhancement
  - stage-4
  - accuracy
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Evidence citations sometimes lack precise page numbers. Improve extraction to capture exact page/section references for each evidence snippet.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Summary

Added comprehensive page number validation and fallback extraction to improve citation precision:

### New Functions in `evidence_tools.py`

1. **`extract_page_from_markers(content, evidence_text)`**: Extracts page number from nearby page markers in markdown. Supports multiple marker formats:
   - Marker library images: `![](_page_5_Picture_0.jpeg)`
   - Markdown headers: `## Page 5`
   - Separators: `--- Page 5 ---`
   - Bracket notation: `[Page 5]`

2. **`validate_page_number(page, page_count, content, evidence_text)`**: Validates LLM-extracted page numbers against document metadata and falls back to marker extraction when:
   - LLM returns None for page
   - LLM hallucinated a page beyond document length
   - Page number is invalid (< 1)

3. **`format_citation(document_name, page, section)`**: Formats human-readable citations like "Document.pdf, Section: 2.1, p. 5"

### LLM Prompt Improvements

Enhanced the evidence extraction prompt with:
- Clear documentation of page marker formats
- Instructions to find nearest preceding marker
- Document length context for validation
- Explicit instruction to use `null` when page unknown

### Integration

- Wired validation into `extract_evidence_with_llm()` function
- Passes `page_count` from document metadata for validation
- Logs when pages are corrected or extracted via fallback

### Tests

Added 26 new tests in `test_citation_precision.py` covering:
- Page extraction from all marker formats
- Validation of valid/invalid page numbers
- Fallback extraction scenarios
- Citation formatting
- End-to-end integration tests

All 246 tests pass.
