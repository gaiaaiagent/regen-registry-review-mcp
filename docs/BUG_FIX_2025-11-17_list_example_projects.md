# Bug Fix: list_example_projects Missing Import

**Date:** 2025-11-17
**Issue:** Runtime error when calling `list_example_projects` MCP tool
**Status:** ✅ Fixed and tested

---

## Problem

When testing the MCP server with a live Eliza agent, the `list_example_projects` tool failed with:

```
NameError: name 'Path' is not defined
```

This occurred at `server.py:270` when the function tried to use `Path(__file__)` without importing it.

---

## Root Cause Analysis

### Why This Wasn't Caught by Tests

**The bug exposed an architectural inconsistency:**

1. **Design Pattern:** The codebase follows a clear pattern:
   - **Business logic** lives in `tools/` modules (testable)
   - **MCP wrappers** in `server.py` are thin formatters (minimal logic)

2. **The violation:** `list_example_projects` in `server.py` contained its own implementation logic instead of delegating to a tool function.

3. **Test coverage:** Tests properly focused on the business logic layer (`session_tools`, `document_tools`, etc.) but `list_example_projects` had no corresponding function in `tools/` to test.

4. **Result:** Untested code path with a simple import error.

---

## Solution

### Refactoring to Maintain Design Consistency

**Step 1: Move Business Logic to `session_tools.py`**

Added `list_example_projects()` function to `src/registry_review_mcp/tools/session_tools.py`:

```python
async def list_example_projects() -> dict[str, Any]:
    """List example projects available in the examples directory.

    Returns:
        Dictionary with list of example projects and their metadata
    """
    from pathlib import Path

    # Get examples directory relative to settings
    examples_dir = settings.data_dir.parent / "examples"

    if not examples_dir.exists():
        return {
            "projects_found": 0,
            "projects": [],
            "message": "No examples directory found",
        }

    projects = []
    for item in sorted(examples_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            file_count = sum(1 for f in item.rglob('*') if f.is_file())
            projects.append({
                "name": item.name,
                "path": str(item.absolute()),
                "file_count": file_count,
            })

    return {
        "projects_found": len(projects),
        "projects": projects,
        "message": f"Found {len(projects)} example project(s)" if projects else "No example projects found",
    }
```

**Step 2: Update MCP Wrapper in `server.py`**

Changed `server.py` to be a thin wrapper (consistent with other tools):

```python
@mcp.tool()
async def list_example_projects() -> str:
    """List example projects available in the examples directory for testing/demo purposes"""
    try:
        logger.info("Listing example projects")

        result = await session_tools.list_example_projects()

        if result["projects_found"] == 0:
            return f"✗ {result['message']}"

        # Format projects for display
        project_list = []
        for project in result["projects"]:
            project_list.append(
                f"• **{project['name']}**\n"
                f"  Path: {project['path']}\n"
                f"  Files: {project['file_count']}"
            )

        return (
            f"✓ {result['message']}\n\n"
            + "\n\n".join(project_list)
            + "\n\n---\n\n"
            "To initialize an example project:\n"
            "/initialize Project Name, /path/from/above"
        )

    except Exception as e:
        logger.error(f"Failed to list example projects: {e}", exc_info=True)
        return f"✗ Error: {str(e)}"
```

**Step 3: Add Comprehensive Tests**

Added 2 tests to `tests/test_infrastructure.py`:

1. **`test_list_example_projects`** - Verifies the function returns correct structure and data
2. **`test_list_example_projects_no_examples`** - Tests edge case when examples directory doesn't exist

---

## Test Results

**Before Fix:**
- 99 tests passing
- `list_example_projects` untested (runtime error on first use)

**After Fix:**
- ✅ 101 tests passing
- Full coverage of `list_example_projects` business logic
- Edge cases tested

```bash
tests/test_infrastructure.py::TestSessionTools::test_list_example_projects PASSED
tests/test_infrastructure.py::TestSessionTools::test_list_example_projects_no_examples PASSED
```

---

## Architecture Improvements

### Pattern Consistency Restored

| Component | Responsibility | Testability |
|-----------|---------------|-------------|
| `tools/session_tools.py` | Business logic: find and parse example projects | ✅ Directly testable |
| `server.py` | MCP wrapper: format results for display | ✅ Minimal logic, calls tested tool |

### Benefits

1. **Separation of Concerns:** Business logic separate from presentation
2. **Testability:** All logic paths covered by unit tests
3. **Reusability:** Tool function can be used by other components
4. **Maintainability:** Consistent patterns across codebase
5. **Error Prevention:** Future additions follow established pattern

---

## Lessons Learned

### Why Design Patterns Matter

This bug demonstrates why architectural consistency is critical:

1. **Patterns create expectations** - When tests focus on `tools/`, putting logic in `server.py` creates a blind spot
2. **Violations compound** - One inconsistency makes future violations more likely
3. **Immediate fixes vs. proper fixes** - Adding the import would work, but refactoring to maintain patterns prevents similar issues

### Testing Strategy Validation

The existing test strategy was **correct** - it focused on business logic. The bug revealed that new code violated the architecture, not that tests were insufficient.

---

## Files Modified

- ✅ `src/registry_review_mcp/tools/session_tools.py` - Added `list_example_projects()`
- ✅ `src/registry_review_mcp/server.py` - Refactored to thin wrapper
- ✅ `tests/test_infrastructure.py` - Added 2 comprehensive tests

---

## Verification

To verify the fix:

```bash
# Run new tests
uv run pytest tests/test_infrastructure.py -v -k "list_example"

# Run full test suite
uv run pytest

# Test with live MCP server
uv run python -m registry_review_mcp.server
```

All tests pass ✅ (101/101)
