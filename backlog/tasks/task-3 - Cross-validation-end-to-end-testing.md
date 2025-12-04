---
id: task-3
title: Cross-validation end-to-end testing
status: Done
assignee: []
created_date: '2025-12-04 01:50'
updated_date: '2025-12-04 02:15'
labels:
  - testing
  - stage-5
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Verify Stage 5 cross-validation works with real data. Test date alignment (sampling vs imagery dates within 120 days), land tenure consistency, project ID validation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Run cross_validate on real session with evidence data
- [x] #2 Date alignment check validates sampling vs imagery dates
- [x] #3 Land tenure check validates owner name consistency
- [x] #4 Project ID check validates C06-4997 pattern
<!-- AC:END -->
