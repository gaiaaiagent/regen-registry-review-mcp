---
id: task-30
title: Production path deletion guard
status: Completed
assignee: []
created_date: '2025-12-04 04:25'
updated_date: '2025-12-04'
completed_date: '2025-12-04'
labels:
  - security
  - high
  - defense-in-depth
dependencies: []
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement a safe deletion utility that refuses to delete production paths. This is a defense-in-depth measure - even if all other protections fail, this guard prevents catastrophic data loss.

### Problem

Any code can call `shutil.rmtree()` on any path. There's no verification that the path is safe to delete.

### Solution

Create a `safe_rmtree()` function that verifies paths before deletion using an allowlist approach.

### Implementation

Created `src/registry_review_mcp/utils/safe_delete.py`:

```python
SAFE_PATH_PREFIXES = ("/tmp/", "/var/tmp/")

class UnsafeDeleteError(Exception):
    """Raised when attempting to delete a path outside safe locations."""
    pass

def is_safe_to_delete(path: Path) -> bool:
    """Check if a path is safe to delete (allowlist approach)."""
    path = path.resolve()
    path_str = str(path)
    for prefix in SAFE_PATH_PREFIXES:
        if path_str.startswith(prefix):
            return True
    return False

def safe_rmtree(path: Path, force: bool = False) -> None:
    """Delete a directory tree, but refuse if not in safe location."""
    path = Path(path).resolve()
    if not force and not is_safe_to_delete(path):
        raise UnsafeDeleteError(
            f"REFUSED: Cannot delete '{path}' - not in safe location (/tmp/). "
            f"If this is intentional, use force=True."
        )
    if path.exists():
        shutil.rmtree(path)

def safe_unlink(path: Path, force: bool = False) -> None:
    """Delete a file, but refuse if not in safe location."""
    path = Path(path).resolve()
    if not force and not is_safe_to_delete(path):
        raise UnsafeDeleteError(
            f"REFUSED: Cannot delete '{path}' - not in safe location (/tmp/)."
        )
    if path.exists():
        path.unlink()
```

### Usage in Tests

Updated `tests/conftest.py` to use `safe_rmtree()` in all cleanup operations:

```python
from registry_review_mcp.utils.safe_delete import safe_rmtree

@pytest.fixture(autouse=True, scope="function")
def cleanup_sessions(tmp_path_factory, worker_id):
    def cleanup_test_sessions():
        if settings.sessions_dir.exists():
            safe_rmtree(settings.sessions_dir)
            settings.sessions_dir.mkdir(exist_ok=True)
    cleanup_test_sessions()
    try:
        yield
    finally:
        cleanup_test_sessions()
```

### Files Created/Modified

- `src/registry_review_mcp/utils/safe_delete.py` - New file with safe deletion utilities
- `tests/conftest.py` - Uses safe_rmtree for all cleanup operations

### Acceptance Criteria

- [x] `safe_rmtree()` refuses to delete paths not under `/tmp/` or `/var/tmp/`
- [x] `safe_rmtree()` allows deletion of `/tmp/` paths
- [x] All test cleanup code uses `safe_rmtree()`
- [x] Production paths survive even if isolation fails
- [x] Clear error message explains why deletion was refused
<!-- SECTION:DESCRIPTION:END -->
