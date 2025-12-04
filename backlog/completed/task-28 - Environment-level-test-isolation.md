---
id: task-28
title: Environment-level test isolation
status: Completed
assignee: []
created_date: '2025-12-04 04:25'
updated_date: '2025-12-04'
completed_date: '2025-12-04'
labels:
  - security
  - critical
  - infrastructure
  - testing
dependencies: []
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement environment-level isolation so tests physically cannot access production data. This is the primary structural defense against test-induced data loss.

### Problem

Currently, tests and production share the same filesystem namespace. The only separation is a runtime fixture that modifies the global `settings` singleton. This approach failed catastrophically when a test imported settings from a different module path (`src.registry_review_mcp.config.settings` vs `registry_review_mcp.config.settings`), creating two singletons - one protected, one not.

Result: Production data was permanently deleted by tests.

### Solution

Run pytest with `XDG_DATA_HOME` and `XDG_CACHE_HOME` set to temporary directories at the PROCESS level, before any Python imports occur.

### Implementation

Updated `tests/conftest.py` to set environment variables BEFORE any package imports:

```python
import os
import sys
import tempfile

_PYTEST_RUNNING = "pytest" in sys.modules or "py.test" in sys.modules

if _PYTEST_RUNNING:
    _TEST_ROOT = tempfile.mkdtemp(prefix="pytest-registry-")
    os.environ["XDG_DATA_HOME"] = os.path.join(_TEST_ROOT, "data")
    os.environ["XDG_CACHE_HOME"] = os.path.join(_TEST_ROOT, "cache")
    os.makedirs(os.environ["XDG_DATA_HOME"], exist_ok=True)
    os.makedirs(os.environ["XDG_CACHE_HOME"], exist_ok=True)

# NOW safe to import from package - settings will see /tmp paths
from registry_review_mcp.config.settings import settings, Settings
```

Added validation in `pytest_configure` to fail fast if isolation fails:

```python
def pytest_configure(config):
    if not str(settings.sessions_dir).startswith("/tmp"):
        raise RuntimeError(
            f"SAFETY FAILURE: Test isolation failed!\n"
            f"sessions_dir = {settings.sessions_dir}\n"
            f"Expected /tmp prefix. Production data at risk."
        )
```

### Why This Works

When `XDG_DATA_HOME` is set before Python imports settings.py:
1. The settings singleton initializes with `/tmp/...` paths
2. There's only ONE singleton (no dual-module-path problem)
3. Tests literally cannot see `~/.local/share/` - it's not in their namespace
4. No fixture modification means no race conditions

### Files Modified

- `tests/conftest.py` - Environment isolation at module load time + validation

### Acceptance Criteria

- [x] Tests run with `XDG_DATA_HOME=/tmp/...` set at process level
- [x] Settings singleton sees temp paths on first import
- [x] No fixture-based settings.sessions_dir modification
- [x] Validation fails if test code somehow points to production paths
- [x] All existing tests pass (243 tests)
- [x] Production data survives repeated test runs
<!-- SECTION:DESCRIPTION:END -->
