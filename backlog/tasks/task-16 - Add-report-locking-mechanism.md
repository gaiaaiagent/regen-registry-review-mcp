---
id: task-16
title: Add report locking mechanism
status: To Do
assignee: []
created_date: '2025-12-04 02:00'
labels:
  - feature
  - stage-8
dependencies:
  - task-2
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Lock finalized reports to prevent edits without creating a new version. Add is_locked flag to session, prevent modifications after completion, require unlock to make changes (which creates new version).
<!-- SECTION:DESCRIPTION:END -->
