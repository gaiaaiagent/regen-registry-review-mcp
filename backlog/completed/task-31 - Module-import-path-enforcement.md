---
id: task-31
title: Module import path enforcement
status: Completed
assignee: []
created_date: '2025-12-04 04:25'
updated_date: '2025-12-04'
completed_date: '2025-12-04'
labels:
  - security
  - medium
  - code-quality
dependencies: []
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Prevent the dual-singleton problem by enforcing consistent import paths. The bug that deleted production data was caused by importing from `src.registry_review_mcp.config.settings` instead of `registry_review_mcp.config.settings`.

### Problem

Python treats these as different modules:
- `from src.registry_review_mcp.config.settings import settings`
- `from registry_review_mcp.config.settings import settings`

Each creates a separate singleton. If code modifies one, the other is unaffected. This is extremely dangerous for configuration objects.

### Solution

Added a Ruff lint rule to ban `src.` imports.

### Implementation

Added to `pyproject.toml`:

```toml
[tool.ruff.lint]
select = ["E", "F", "I"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
"src.registry_review_mcp".msg = "Import from 'registry_review_mcp', not 'src.registry_review_mcp'. The 'src.' prefix creates a separate module singleton."
```

### Files Modified

- `pyproject.toml` - Added lint rule for import path enforcement

### Acceptance Criteria

- [x] Lint fails on `from src.registry_review_mcp` imports
- [x] All tests use consistent import path
- [x] Documentation explains correct import path (in error message)
<!-- SECTION:DESCRIPTION:END -->
