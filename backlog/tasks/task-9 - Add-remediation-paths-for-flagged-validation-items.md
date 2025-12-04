---
id: task-9
title: Add remediation paths for flagged validation items
status: Done
assignee: []
created_date: '2025-12-04 01:59'
updated_date: '2025-12-04 02:16'
labels:
  - enhancement
  - stage-5
  - ux
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Flagged validation items now include remediation paths with:

- **Action statement**: Brief description of what needs to be done
- **Step-by-step guidance**: Numbered steps for resolution
- **Documents to check**: Specific document types to consult
- **Registry guidance**: Reference to relevant Program Guide section

Implemented for all three validation types:
- **Date alignment**: Steps for verifying date consistency, format interpretation
- **Land tenure**: Steps for resolving owner name mismatches, area discrepancies
- **Project ID**: Steps for correcting ID inconsistencies, format validation

Markdown reports now render remediation paths as blockquotes under flagged items, providing immediate actionable guidance for human reviewers.

Implementation:
- Added RemediationPath model to report.py
- Added REMEDIATION_TEMPLATES with guidance for each validation type/status
- Added get_remediation_path() helper function
- Updated ValidationFinding to include optional remediation field
- Added format_remediation_markdown() for report rendering
- Integrated into format_validation_summary_markdown()

All 246 tests pass.
<!-- SECTION:DESCRIPTION:END -->
