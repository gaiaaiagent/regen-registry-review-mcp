---
id: task-32
title: Test isolation audit and hardening
status: Completed
assignee: []
created_date: '2025-12-04 04:25'
updated_date: '2025-12-04'
completed_date: '2025-12-04'
labels:
  - security
  - high
  - testing
dependencies:
  - task-28
  - task-30
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Comprehensive audit of all test code to identify and fix isolation vulnerabilities. Remove all patterns that could affect production data.

### Problem

The data loss incident revealed that our test isolation was behavioral, not structural. We needed to audit all tests and remove dangerous patterns.

### Audit Results

**Patterns Fixed:**

1. **Direct settings modification** - 7 tests were modifying the now-immutable Settings object
   - Fixed by creating new Settings instances via monkeypatch

2. **Invalid Settings configurations** - 5 tests were using chunk sizes below validation minimum (10000)
   - Fixed by using valid values (10000-15000) and larger test content

3. **Parallel test pollution** - 1 test was seeing sessions from other workers
   - Fixed by updating `cleanup_sessions` fixture to clean `settings.sessions_dir` directly

4. **Assertion fragility** - 1 test had overly specific assertions
   - Fixed by using more flexible assertions

### Files Audited and Fixed

- `tests/conftest.py` - Environment-level isolation + safe_rmtree usage
- `tests/test_infrastructure.py` - Fixed Settings immutability issues
- `tests/test_error_propagation.py` - Fixed Settings immutability issues
- `tests/test_llm_extraction.py` - Fixed 5 tests with invalid chunk size configurations
- `tests/test_user_experience.py` - Fixed assertion and cleanup

### Test Results

All 243 tests pass with the new security architecture:
- Environment-level isolation (XDG_DATA_HOME in /tmp)
- Immutable Settings (TypeError on modification attempt)
- Safe deletion (UnsafeDeleteError on production paths)
- Import path enforcement (lint rule)

### Acceptance Criteria

- [x] No `shutil.rmtree()` without safety check in test code
- [x] No `from src.` imports in test code
- [x] No direct settings modification in test code
- [x] All test file operations use safe paths
- [x] Audit documented with findings and fixes
<!-- SECTION:DESCRIPTION:END -->
