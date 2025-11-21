# Critical Bugs Discovered - November 14, 2025

## Priority: P0 (CRITICAL - Data Loss)

### Bug #1: Test Fixture Destroys Real User Sessions

**File:** `tests/conftest.py:270-291`
**Severity:** **CRITICAL - Silent Data Loss**
**Status:** ✅ FIXED

#### The Problem

The `cleanup_sessions()` fixture has catastrophic design flaws:

```python
@pytest.fixture(autouse=True)  # ← Runs for EVERY test automatically
def cleanup_sessions():
    # Cleanup before test
    if sessions_dir.exists():
        for session_file in sessions_dir.glob("session-*"):  # ← Matches ALL sessions
            if session_file.is_dir():
                shutil.rmtree(session_file, ignore_errors=True)  # ← Silent deletion
```

**Critical Issues:**

1. **`autouse=True`** - Runs automatically for EVERY pytest execution
2. **Real data directory** - Operates on `/data/sessions/` not a temp directory
3. **Overly broad glob** - `"session-*"` matches ALL user sessions, not just test sessions
4. **Silent deletion** - `ignore_errors=True` suppresses any warnings
5. **Runs twice** - Before AND after each test (maximum destruction)

#### Impact

- **All manual testing sessions destroyed** when running pytest
- **Demo sessions disappear** immediately
- **Production data loss risk** if deployed with tests enabled
- **Violates "Fail Explicit" principle** - silent, catastrophic failure
- **Makes real-world usage impossible** alongside testing

#### Real-World Evidence

Test run at 11:17-11:18 destroyed session `session-e445ed059b6a` which was created for workflow demonstration:

```bash
# Session created successfully at 11:16
$ list_sessions
✓ Found 1 session(s)
1. **Botany Farm 2022-2023** (session-e445ed059b6a)

# Pytest runs at 11:17-11:18...

# Session GONE
$ list_sessions
No sessions found.

$ ls data/sessions/
# Only test-* sessions remain
test-lock-basic/  test-lock-concurrent/  test-session/
test-session-exists/  test-update-bug/  test-write-alone/
```

#### The Fix

✅ **APPLIED:** Changed glob pattern from `"session-*"` to `"test-*"`

```python
@pytest.fixture(autouse=True)
def cleanup_sessions():
    """Clean up TEST sessions only before and after each test.

    CRITICAL: Only removes test-* sessions to avoid destroying real user sessions.
    This prevents test pollution while preserving manual testing data.
    """
    # Cleanup ONLY test-* sessions
    if sessions_dir.exists():
        for session_file in sessions_dir.glob("test-*"):  # ← Now safe
            if session_file.is_dir():
                shutil.rmtree(session_file, ignore_errors=True)
```

**Alternative Improvements (Future):**
1. Use isolated temp directories per test
2. Remove `autouse=True`, require explicit fixture usage
3. Add confirmation prompt for data cleanup
4. Log deletions to stderr for visibility

#### Testing Required

- [ ] Verify pytest no longer destroys `session-*` directories
- [ ] Confirm `test-*` sessions are still cleaned up
- [ ] Run full test suite to ensure no breakage
- [ ] Create real session before/after test run to verify preservation

---

## Priority: P0 (CRITICAL - Silent Failure)

### Bug #2: `start_review` Tool Reports Success Despite Failure

**Status:** 🔍 UNDER INVESTIGATION

#### The Problem

The `start_review` MCP tool reports success but session is never created:

```
Called: start_review("Botany Farm 2022-2023", "./examples/22-23/")
Response: ✓ Review Started Successfully
          Session ID: session-90f3e915fc3c
          Document Discovery Complete: Found 7 document(s)

Reality: Session does not exist
```

**Verification:**
- `list_sessions` → "No sessions found"
- Filesystem check → No directory `session-90f3e915fc3c/`
- MCP tool responds with success message and valid session ID

#### Possible Causes

1. **Path validation failure** - Relative path `./examples/22-23/` rejected by Pydantic validator
2. **Exception swallowed** - Try/catch block returning success despite error
3. **MCP response buffering** - Success message sent before actual creation
4. **Race condition** - Session created then immediately destroyed (see Bug #1)

#### Code Analysis

The `start_review` tool (server.py:273-339):
```python
@mcp.tool()
async def start_review(...) -> str:
    try:
        session_result = await session_tools.create_session(...)
        session_id = session_result["session_id"]
        logger.info(f"Session created: {session_id}")

        discovery_result = await document_tools.discover_documents(session_id)

        return f"""✓ Review Started Successfully
Session ID: {session_id}
...
```
    except Exception as e:
        logger.error(f"Failed to start review: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"
```

**Path validation** in ProjectMetadata (schemas.py:29-38):
```python
@field_validator("documents_path")
@classmethod
def validate_path_exists(cls, value: str) -> str:
    path = Path(value)
    if not path.exists():
        raise ValueError(f"Path does not exist: {value}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {value}")
    return str(path.absolute())  # ← Converts to absolute
```

**Hypothesis:**
Most likely cause is Bug #1 (cleanup fixture). The session WAS created successfully, but pytest ran immediately after and destroyed it.

#### Testing Plan

Now that Bug #1 is fixed:
1. Call `start_review` with absolute path
2. Call `start_review` with relative path
3. Verify session persists
4. Check logs for exceptions

If issue persists, investigate:
- MCP server response timing
- Async execution order
- Transaction rollback scenarios

---

## Priority: P1 (Missing Functionality)

### Bug #3: Validation and Report Tools Not Exposed as MCP Tools

**Files:** `src/registry_review_mcp/server.py`
**Severity:** MEDIUM - Incomplete API
**Status:** 📋 DOCUMENTED

#### The Problem

Cross-validation and report generation functions exist in tool modules but are NOT exposed as MCP tools:

**Tools Exist:**
- `validation_tools.py` - Contains validation logic
- `report_tools.py` - Contains report generation

**MCP Server:**
- ❌ No `@mcp.tool()` decorator for `cross_validate()`
- ❌ No `@mcp.tool()` decorator for `generate_report()`
- ✅ Prompts exist: `/cross-validation`, `/report-generation`

**Impact:**
- Users can only access via prompts (workflow-driven)
- Cannot call validation/reporting directly as tools
- Breaks composability and automation use cases
- Inconsistent with other phases (discovery, extraction both have tools + prompts)

#### Example

Documentation (README.md:649-651) claims:
```markdown
**Validation & Reporting (Phase 4):**
- `cross_validation` - Validate dates, land tenure, and project IDs across documents
- `generate_report` - Create comprehensive Markdown and JSON reports
```

But these tools don't exist in MCP interface. Only prompts work.

#### The Fix

Add MCP tool decorators in `server.py`:

```python
@mcp.tool()
async def cross_validate(session_id: str) -> str:
    """Run all cross-document validation checks."""
    result = await validation_tools.cross_validate(session_id)
    return format_validation_result(result)

@mcp.tool()
async def generate_report(
    session_id: str,
    format: str = "markdown"
) -> str:
    """Generate complete review report."""
    result = await report_tools.generate_review_report(
        session_id, format=format
    )
    return format_report_result(result)
```

---

## Summary

| Bug | Severity | Status | Impact |
|-----|----------|--------|--------|
| #1: Test cleanup destroys real sessions | **CRITICAL** | ✅ FIXED | Data loss, unusable |
| #2: start_review silent failure | **CRITICAL** | 🔍 Investigation | Silent failure, trust loss |
| #3: Missing MCP tools for validation/reporting | MEDIUM | 📋 Documented | Incomplete API |

### Recommendations

**Immediate (Today):**
1. ✅ Deploy Bug #1 fix
2. Test Bug #2 with fix in place
3. Document Bug #3 for Phase 5 sprint

**Short-term (This Week):**
1. Add missing MCP tools (Bug #3)
2. Comprehensive integration testing
3. Review all autouse fixtures for safety

**Long-term (Phase 5):**
1. Isolated test environments (no shared data directories)
2. Test data factories instead of cleanup fixtures
3. Pre-commit hooks to prevent autouse fixture bugs
4. Monitoring/alerting for silent failures

---

**Report Date:** November 14, 2025
**Discovered By:** Claude Code (ultrathink deep investigation)
**Validated:** Real-world session destruction, code analysis
**Priority:** All bugs block production readiness
