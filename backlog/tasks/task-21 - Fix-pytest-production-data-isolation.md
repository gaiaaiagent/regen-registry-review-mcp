---
id: task-21
title: Fix pytest production data isolation
status: Done
assignee: []
created_date: '2025-12-04 02:55'
labels:
  - bug
  - critical
  - testing
  - data-safety
dependencies: []
priority: critical
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The pytest test suite deleted production session data while a server was running. This is a critical data safety bug.

## Evidence

- **18:33-34**: GPT created session-3bcc63138eb5, uploaded 7 files, ran mapping successfully
- **18:40:02**: pytest-30 started (pytest ran)
- **18:40:04**: Production sessions directory was recreated (all sessions deleted)
- **Result**: session-3bcc63138eb5 and all its data was lost

## Root Cause Analysis

The `cleanup_sessions` fixture in `tests/conftest.py` (lines 293-346) is supposed to:
1. Save original `settings.sessions_dir`
2. Switch to temp directory
3. Run test
4. Restore original `settings.sessions_dir`

However, somehow the production sessions directory was affected. Possible causes:
1. Race condition between pytest and running server sharing the same `settings` singleton
2. Import ordering issue where settings gets modified before fixture saves original
3. Some test or fixture not respecting the isolation
4. The `_ensure_directories()` method being called at wrong time

## Impact

- **Critical**: Production data can be deleted by running tests
- **Silent failure**: No warnings or errors when this happens
- **Trust erosion**: Users cannot rely on session persistence

## Proposed Solutions

### Option A: Environment Variable Lock
Add an environment variable check that prevents pytest from running if server is active:
```python
if os.environ.get("REGISTRY_REVIEW_SERVER_RUNNING"):
    pytest.skip("Cannot run tests while server is running")
```

### Option B: Separate Settings Instances
Use completely separate settings instances for tests vs production:
```python
# In conftest.py
test_settings = TestSettings()  # Separate class, not singleton modification
```

### Option C: File Lock
Use a lock file to prevent concurrent access:
```python
# Server creates data/.server.lock
# Pytest checks for lock and refuses to run
```

### Option D: Read-Only Production Path
Make production path immutable once loaded:
```python
@property
def sessions_dir(self):
    return self._sessions_dir

# No setter - tests must use their own settings instance
```

## Recommended Fix

Implement Option B + Option C:
1. Tests should NEVER modify the production settings singleton
2. Server should create a lock file when running
3. Pytest should check for lock and fail fast with clear error
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Running pytest while server is active does NOT delete production sessions
- [ ] #2 Tests continue to pass in isolation
- [ ] #3 Clear error message if test/server conflict detected
- [ ] #4 Document the isolation mechanism
<!-- AC:END -->
