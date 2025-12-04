---
id: task-29
title: Immutable settings after initialization
status: Completed
assignee: []
created_date: '2025-12-04 04:25'
updated_date: '2025-12-04'
completed_date: '2025-12-04'
labels:
  - security
  - high
  - architecture
dependencies:
  - task-28
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Make the Settings class immutable after initialization. This prevents runtime modification of paths, eliminating an entire class of bugs where code accidentally modifies settings.

### Problem

The current Settings class allows runtime modification:
```python
settings.sessions_dir = some_path  # This works, and shouldn't
```

This enables the fixture-based isolation pattern that failed. It also creates a general hazard: any code, anywhere, can modify settings and affect all other code.

### Solution

Freeze settings after `__init__` completes. Any attempt to modify raises an error.

### Implementation

Added to `src/registry_review_mcp/config/settings.py`:

```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self._ensure_directories()
    object.__setattr__(self, '_frozen', True)

def __setattr__(self, name: str, value) -> None:
    if getattr(self, '_frozen', False) and name != '_frozen':
        raise TypeError(
            f"Settings are immutable. Cannot modify '{name}' after initialization. "
            f"Use environment variables to configure settings."
        )
    super().__setattr__(name, value)

def __delattr__(self, name: str) -> None:
    if getattr(self, '_frozen', False):
        raise TypeError("Settings are immutable. Cannot delete attributes.")
    super().__delattr__(name)
```

### Migration Path

1. Updated conftest.py to use environment variables instead of attribute assignment
2. Fixed all tests that were modifying settings to use new Settings instances via monkeypatch
3. All configuration now happens via environment or constructor

### Files Modified

- `src/registry_review_mcp/config/settings.py` - Added immutability via `__setattr__` and `__delattr__` overrides
- `tests/test_infrastructure.py` - Fixed `test_list_example_projects_no_examples` to use new Settings instance
- `tests/test_error_propagation.py` - Fixed `test_successful_operation_returns_result` to use monkeypatch
- `tests/test_llm_extraction.py` - Fixed 5 chunking tests to use valid Settings configurations

### Acceptance Criteria

- [x] Settings cannot be modified after `__init__`
- [x] Attempting modification raises `TypeError`
- [x] All tests pass using environment-based configuration (243 tests)
- [x] No production code relies on settings modification
<!-- SECTION:DESCRIPTION:END -->
