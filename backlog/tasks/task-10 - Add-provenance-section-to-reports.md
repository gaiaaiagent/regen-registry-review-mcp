---
id: task-10
title: Add provenance section to reports
status: Done
assignee: []
created_date: '2025-12-04 01:59'
updated_date: '2025-12-04 02:13'
labels:
  - feature
  - stage-6
  - compliance
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Reports now include a Document Provenance section with:

- SHA256 content hashes for all source documents
- File sizes and indexing timestamps
- Extraction methods used (marker, fast, etc.)
- Methodology identifier
- Report generation timestamp

Markdown reports include:
- Summary statistics (documents analyzed, total bytes processed)
- Document hash table (truncated for readability)
- Collapsible section with full SHA256 hashes for verification

This provides the cryptographic anchor needed for:
- Audit trails (supports task-15 change tracking)
- On-chain registration (Stage 8 requirement)
- Document verification by external parties

Implementation:
- Added DocumentProvenance and ReportProvenance models to report.py
- Added build_provenance() function to construct from documents.json
- Added format_provenance_markdown() for report rendering
- Integrated into generate_review_report() workflow

All 246 tests pass.
<!-- SECTION:DESCRIPTION:END -->
