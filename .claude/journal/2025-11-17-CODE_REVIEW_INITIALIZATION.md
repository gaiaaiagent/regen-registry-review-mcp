# Code Review: Session Initialization Functionality

**Date:** 2025-11-14
**Reviewer:** Claude Code
**Scope:** Session initialization flow across `create_session()`, `A_initialize.initialize_prompt()`, and `start_review()`

## Executive Summary

The session initialization code exhibits significant **duplication**, **inconsistency**, and **architectural confusion** across three different entry points. The codebase violates the DRY (Don't Repeat Yourself) principle and creates maintenance hazards through inconsistent handling of critical operations.

### Critical Issues Found

1. **Workflow stage completion inconsistency** - `initialize` stage marked complete in different places with different logic
2. **Requirements counting duplication** - Checklist loading repeated in 3 locations with identical code
3. **Duplicate session creation logic** - Multiple paths create sessions without centralized validation
4. **Missing workflow stage updates** - `start_review()` bypasses workflow tracking entirely
5. **Architectural confusion** - Unclear separation between tools, prompts, and convenience functions

---

## 1. Code Duplication Analysis

### 1.1 Requirements Total Loading (3x Duplication)

**Location 1:** `session_tools.py:create_session()` (Lines 70-76)
```python
# Load checklist requirements count
checklist_path = settings.get_checklist_path(methodology)
requirements_count = 0
if checklist_path.exists():
    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)
    requirements_count = len(checklist_data.get("requirements", []))
```

**Location 2:** `A_initialize.py:initialize_prompt()` (Lines 156-164)
```python
result = await session_tools.create_session(
    project_name=project_name,
    documents_path=documents_path,
    methodology="soil-carbon-v1.2.2"
)

session_id = result["session_id"]
requirements_count = result.get("requirements_total", 0)
```
*Note: This relies on Location 1 having already computed it*

**Location 3:** `server.py:start_review()` (Lines 327-332)
```python
session_result = await session_tools.create_session(
    project_name=project_name,
    documents_path=documents_path,
    methodology=methodology,
    project_id=project_id,
)
```
*Note: Also relies on Location 1*

**Analysis:**
While the actual JSON loading only happens in `create_session()`, the *result handling* and requirements count extraction is duplicated. More critically, all three locations independently decide whether to load the checklist, creating a brittle dependency chain.

**Impact:** If checklist loading logic changes (e.g., validation, caching, different file format), all three locations need updates.

---

### 1.2 Duplicate Session Creation Workflows

Three distinct entry points create sessions:

| Entry Point | File | Purpose | Workflow Stage Handling |
|------------|------|---------|------------------------|
| `create_session()` | `session_tools.py:27` | Base tool - creates session | **None** - Does not mark `initialize` complete |
| `initialize_prompt()` | `A_initialize.py:11` | User-facing prompt | **Marks `initialize` complete** (Line 169) |
| `start_review()` | `server.py:303` | Quick-start convenience | **None** - Skips workflow tracking entirely |

**Critical Problem:** The same session can be created with different workflow states depending on the entry point used.

**Example Scenario:**
```python
# User path 1: Using prompt
/initialize Botany Farm, /path/to/docs
# Result: session with workflow_progress.initialize = "completed"

# User path 2: Using tool directly
create_session("Botany Farm", "/path/to/docs")
# Result: session with workflow_progress.initialize = "pending"

# User path 3: Using quick-start
start_review("Botany Farm", "/path/to/docs")
# Result: session with workflow_progress.initialize = "pending"
# But documents_discovery = "completed" (implicitly)
```

This creates **state machine inconsistency** - sessions in identical states have different workflow progress markers.

---

## 2. Requirements Total Inconsistencies

### 2.1 Current Behavior

| Function | Sets `requirements_total`? | How? |
|----------|---------------------------|------|
| `create_session()` | ✅ Yes | Loads checklist JSON, counts requirements, sets `SessionStatistics(requirements_total=count)` |
| `initialize_prompt()` | ❌ No | Reads from `create_session()` result but doesn't update session |
| `start_review()` | ❌ No | Reads from `create_session()` result but doesn't use it |

### 2.2 Data Flow

```
create_session()
  ↓
  Loads checklist JSON
  ↓
  Counts: len(checklist_data["requirements"])
  ↓
  Creates Session(statistics=SessionStatistics(requirements_total=N))
  ↓
  Saves to session.json

initialize_prompt()
  ↓
  Calls create_session()
  ↓
  Extracts result["requirements_total"]
  ↓
  Displays in message (but doesn't validate or update)
  ↓
  Manually updates session.json to mark initialize="completed"

start_review()
  ↓
  Calls create_session()
  ↓
  Ignores requirements_total entirely
  ↓
  Never marks initialize stage
```

### 2.3 Problems Identified

**Problem 1: Redundant Extraction**
`initialize_prompt()` extracts `requirements_total` from the result just to display it, but the value is already persisted in `session.json`. This creates unnecessary coupling.

**Problem 2: No Validation**
If the checklist file is corrupted or missing requirements, `create_session()` silently sets `requirements_total=0`. No downstream code validates this.

**Problem 3: Race Condition Risk**
If checklist file is updated between session creation and document discovery, the count becomes stale. No refresh mechanism exists.

---

## 3. Workflow Stage Completion Logic

### 3.1 Initialize Stage Handling

**Expected behavior:** The `initialize` workflow stage should be marked `"completed"` when session creation finishes successfully.

**Actual behavior:**

| Entry Point | Marks Initialize Complete? | Location |
|------------|---------------------------|----------|
| `create_session()` | ❌ No | Sets all stages to `"pending"` via `WorkflowProgress()` default |
| `initialize_prompt()` | ✅ Yes | Lines 166-170 - manually updates session.json |
| `start_review()` | ❌ No | Never touches workflow progress |

**Code from `A_initialize.py` (Lines 166-170):**
```python
# Mark initialize stage as completed
state_manager = StateManager(session_id)
session_data = state_manager.read_json("session.json")
session_data["workflow_progress"]["initialize"] = "completed"
state_manager.write_json("session.json", session_data)
```

### 3.2 Architectural Issues

**Issue 1: Leaky Abstraction**
The prompt layer (`A_initialize.py`) reaches into session internals to manually update workflow progress. This violates separation of concerns - the tool layer (`session_tools.py`) should own state transitions.

**Issue 2: Race Condition**
The workflow update is **non-atomic** with session creation:
1. `create_session()` writes session.json (initialize="pending")
2. `initialize_prompt()` reads session.json
3. `initialize_prompt()` modifies dict
4. `initialize_prompt()` writes session.json

If another process accesses the session between steps 1-4, it sees incomplete state.

**Issue 3: Inconsistent State Management**
Compare to other workflow stages:
- `document_discovery` - Updated by `document_tools.discover_documents()` (correct)
- `evidence_extraction` - Updated by `evidence_tools.extract_all_evidence()` (correct)
- `initialize` - Updated by prompt, not tool (incorrect)

**Expected pattern:**
```python
# Tools update their own workflow stages
async def create_session(...) -> dict:
    session = Session(...)
    state_manager.write_json("session.json", session.model_dump())

    # Tool marks its own stage complete
    await update_session_state(
        session_id,
        {"workflow_progress.initialize": "completed"}
    )
    return {...}
```

---

## 4. Start Review Tool Analysis

### 4.1 Current Implementation

**File:** `server.py` (Lines 303-369)

```python
async def start_review(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
) -> str:
    """Quick-start: Create session and discover documents in one step."""

    # Create session
    session_result = await session_tools.create_session(...)
    session_id = session_result["session_id"]

    # Discover documents
    discovery_result = await document_tools.discover_documents(session_id)

    # Return formatted summary
    return f"""✓ Review Started Successfully
    ...
    """
```

### 4.2 Problems

**Problem 1: Incomplete Workflow Tracking**
The tool completes two workflow stages (`initialize` and `document_discovery`) but only `discover_documents()` updates the workflow. The result:
- `initialize` = `"pending"` ❌ (should be `"completed"`)
- `document_discovery` = `"completed"` ✅

**Problem 2: No Duplicate Session Detection**
Unlike `initialize_prompt()` (Lines 67-153), `start_review()` has zero duplicate detection logic. It will happily create multiple sessions for the same `documents_path`.

**Comparison:**

| Feature | `initialize_prompt()` | `start_review()` |
|---------|----------------------|------------------|
| Duplicate detection by path | ✅ Yes (Lines 67-90) | ❌ No |
| Duplicate session warning | ✅ Yes (Lines 92-153) | ❌ No |
| Workflow stage marking | ✅ Yes (initialize) | ⚠️ Partial (only document_discovery) |
| User guidance on conflicts | ✅ Yes | ❌ No |

**Problem 3: Architectural Redundancy**
`start_review()` is meant to be a convenience function, but it duplicates the logic of:
1. `create_session()` - Session creation
2. `discover_documents()` - Document discovery

The only value it adds is formatting the combined output. This is insufficient justification for a separate tool.

---

## 5. Duplicate Session Detection

### 5.1 Detection Logic in `initialize_prompt()`

**Lines 64-90:**
```python
# Normalize documents path for comparison
normalized_path = str(Path(documents_path).absolute())

# Check for duplicate sessions by documents_path only
duplicates = []
if settings.sessions_dir.exists():
    for session_dir in settings.sessions_dir.iterdir():
        if session_dir.is_dir() and (session_dir / "session.json").exists():
            try:
                state_manager = StateManager(session_dir.name)
                session_data = state_manager.read_json("session.json")
                session_project = session_data.get("project_metadata", {})
                session_path = str(Path(session_project.get("documents_path", "")).absolute())

                # Match by documents_path only - one directory = one session
                if session_path == normalized_path:
                    duplicates.append({...})
            except Exception:
                continue
```

### 5.2 Problems

**Problem 1: Wrong Layer**
Duplicate detection belongs in the **tool layer** (`session_tools.py`), not the **prompt layer** (`A_initialize.py`). The tool should enforce business rules.

**Problem 2: Performance**
Every initialization scans **all sessions** on disk. For large deployments (100+ sessions), this becomes a performance bottleneck.

**Better approach:**
```python
# In session_tools.py
def find_session_by_path(documents_path: str) -> str | None:
    """Find existing session for a documents path.

    Uses path index for O(1) lookup instead of O(n) scan.
    """
    # Use a simple path -> session_id mapping file
    pass
```

**Problem 3: Code Duplication with list_sessions()**
Compare the duplicate detection loop (Lines 70-89) to `list_sessions()` (Lines 165-200 in `session_tools.py`):

```python
# Both iterate sessions identically
for session_dir in settings.sessions_dir.iterdir():
    if session_dir.is_dir() and (session_dir / "session.json").exists():
        state_manager = StateManager(session_dir.name)
        session_data = state_manager.read_json("session.json")
        # ...
```

This iteration pattern should be extracted to a utility function.

---

## 6. Architectural Inconsistencies

### 6.1 Layering Violations

**Expected Architecture:**
```
User Interface Layer (Prompts)
    ↓ Calls
Business Logic Layer (Tools)
    ↓ Uses
Data Access Layer (StateManager)
```

**Actual Architecture:**
```
Prompts (A_initialize.py)
    ↓ Calls tools AND manipulates state directly
Tools (session_tools.py)
    ↓ Incomplete state management
StateManager
```

**Violation Example:** `A_initialize.py` (Lines 166-170)
```python
# Prompt directly manipulates session state
state_manager = StateManager(session_id)
session_data = state_manager.read_json("session.json")
session_data["workflow_progress"]["initialize"] = "completed"
state_manager.write_json("session.json", session_data)
```

This should be:
```python
# Prompt calls tool
await session_tools.complete_initialization(session_id)
```

### 6.2 Responsibility Confusion

| Responsibility | Current Owner | Should Be |
|---------------|--------------|-----------|
| Session creation | `create_session()` | ✅ Correct |
| Checklist loading | `create_session()` | ✅ Correct |
| Workflow stage updates | Mixed (prompts + tools) | ❌ Should be tools only |
| Duplicate detection | `initialize_prompt()` | ❌ Should be `create_session()` |
| User messaging | Tools (return strings) | ⚠️ Should be prompts only |

**Example of messaging confusion:**

`create_session()` returns:
```python
return {
    "session_id": session_id,
    "message": f"Session created successfully for project: {project_name}",
    # ^ This is presentation logic, shouldn't be in tool layer
}
```

Tools should return structured data. Prompts should format messages.

---

## 7. Missing Error Handling

### 7.1 Checklist Loading Failures

**Current code** (`session_tools.py:70-76`):
```python
checklist_path = settings.get_checklist_path(methodology)
requirements_count = 0
if checklist_path.exists():
    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)
    requirements_count = len(checklist_data.get("requirements", []))
```

**Problems:**
- No exception handling for JSON parsing errors
- No validation that `requirements` key exists
- No validation that requirements are well-formed
- Silently defaults to 0 if file missing (should this be an error?)

**Better approach:**
```python
checklist_path = settings.get_checklist_path(methodology)
if not checklist_path.exists():
    raise ValueError(f"Checklist not found for methodology: {methodology}")

try:
    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid checklist JSON: {e}")

requirements = checklist_data.get("requirements", [])
if not requirements:
    raise ValueError(f"Checklist has no requirements: {methodology}")

requirements_count = len(requirements)
```

### 7.2 Path Validation Inconsistency

**In `ProjectMetadata` (schemas.py:29-38):**
```python
@field_validator("documents_path")
@classmethod
def validate_path_exists(cls, value: str) -> str:
    path = Path(value)
    if not path.exists():
        raise ValueError(f"Path does not exist: {value}")
    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {value}")
    return str(path.absolute())
```

**In `initialize_prompt()` (Lines 210-223):**
```python
except FileNotFoundError:
    message = f"""# ❌ Error: Document Path Not Found

    The path you provided does not exist:
    `{documents_path}`
    ...
    """
```

**Problem:** Path validation happens twice:
1. First in Pydantic model (raises `ValueError`)
2. Then prompt catches `FileNotFoundError` (which never happens because Pydantic validates first)

The error handling in `initialize_prompt()` is dead code.

---

## 8. Recommended Refactoring Approach

### 8.1 Principle: Single Responsibility

Each function should have **one reason to change**.

### 8.2 Proposed Architecture

```python
# === session_tools.py ===

async def create_session(...) -> dict:
    """Creates session with complete initialization.

    - Validates inputs
    - Checks for duplicates
    - Loads checklist
    - Creates session directory
    - Marks initialize workflow stage complete
    """
    # 1. Check for existing session
    existing = find_session_by_path(documents_path)
    if existing:
        raise SessionAlreadyExistsError(existing_session_id=existing)

    # 2. Load and validate checklist
    requirements_count = load_checklist_requirements(methodology)

    # 3. Create session
    session = Session(
        session_id=generate_session_id(),
        status="initialized",
        statistics=SessionStatistics(requirements_total=requirements_count),
        workflow_progress=WorkflowProgress(initialize="completed"),  # ← Mark complete
        ...
    )

    # 4. Persist
    state_manager = StateManager(session.session_id)
    state_manager.write_json("session.json", session.model_dump(mode="json"))

    return session.model_dump(mode="json")


def find_session_by_path(documents_path: str) -> str | None:
    """Find existing session for a documents path."""
    # Extract from initialize_prompt()
    pass


def load_checklist_requirements(methodology: str) -> int:
    """Load checklist and return requirement count with validation."""
    # Extract from create_session()
    pass


# === A_initialize.py ===

async def initialize_prompt(...) -> list[TextContent]:
    """User-facing session initialization with helpful guidance."""

    try:
        # Let tool handle business logic
        result = await session_tools.create_session(...)

        # Prompt only formats output
        message = format_success_message(result)

    except session_tools.SessionAlreadyExistsError as e:
        # Format friendly duplicate warning
        message = format_duplicate_warning(e.existing_session)

    except ValueError as e:
        # Format validation errors
        message = format_error_message(str(e))

    return [TextContent(type="text", text=message)]


# === server.py ===

# REMOVE start_review() entirely - it's redundant
# Users can call:
#   1. create_session() + discover_documents() (explicit)
#   2. /initialize + /document-discovery (guided)
```

### 8.3 Workflow Stage Ownership

**Principle:** Each tool marks its own workflow stage complete.

```python
# session_tools.py
async def create_session(...) -> dict:
    ...
    workflow_progress=WorkflowProgress(initialize="completed")
    ...

# document_tools.py
async def discover_documents(...) -> dict:
    ...
    await update_session_state(session_id, {
        "workflow_progress.document_discovery": "completed"
    })
    ...

# evidence_tools.py
async def extract_all_evidence(...) -> dict:
    ...
    await update_session_state(session_id, {
        "workflow_progress.evidence_extraction": "completed"
    })
    ...
```

---

## 9. Specific Changes Needed

### 9.1 High Priority (Correctness)

**Change 1: Move duplicate detection to create_session()**
```python
# File: src/registry_review_mcp/tools/session_tools.py

async def create_session(...) -> dict:
    # Add at start (before creating session)
    existing = find_session_by_path(documents_path)
    if existing:
        raise SessionAlreadyExistsError(
            f"Session already exists for path: {documents_path}",
            details={"existing_session_id": existing}
        )

    # Continue with creation...
```

**Change 2: Mark initialize stage in create_session()**
```python
# File: src/registry_review_mcp/tools/session_tools.py

# Replace line 85:
workflow_progress=WorkflowProgress(),

# With:
workflow_progress=WorkflowProgress(initialize="completed"),
```

**Change 3: Remove workflow update from initialize_prompt()**
```python
# File: src/registry_review_mcp/prompts/A_initialize.py

# DELETE lines 166-170:
# Mark initialize stage as completed
state_manager = StateManager(session_id)
session_data = state_manager.read_json("session.json")
session_data["workflow_progress"]["initialize"] = "completed"
state_manager.write_json("session.json", session_data)
```

**Change 4: Handle duplicate in initialize_prompt()**
```python
# File: src/registry_review_mcp/prompts/A_initialize.py

try:
    result = await session_tools.create_session(...)
except session_tools.SessionAlreadyExistsError as e:
    # Format the duplicate warning we already have
    existing = await session_tools.load_session(e.existing_session_id)
    message = format_duplicate_warning(existing)
    return [TextContent(type="text", text=message)]
```

### 9.2 Medium Priority (Maintainability)

**Change 5: Extract checklist loading**
```python
# File: src/registry_review_mcp/tools/session_tools.py

def load_checklist_requirements(methodology: str) -> int:
    """Load checklist and return validated requirement count.

    Raises:
        ValueError: If checklist missing or invalid
    """
    checklist_path = settings.get_checklist_path(methodology)

    if not checklist_path.exists():
        raise ValueError(f"Checklist not found: {methodology}")

    try:
        with open(checklist_path, "r") as f:
            checklist_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid checklist JSON: {e}")

    requirements = checklist_data.get("requirements", [])
    if not requirements:
        raise ValueError(f"Checklist has no requirements: {methodology}")

    return len(requirements)
```

**Change 6: Extract session iteration helper**
```python
# File: src/registry_review_mcp/utils/helpers.py (new file)

def iter_sessions() -> Iterator[tuple[str, dict]]:
    """Iterate all sessions with error handling.

    Yields:
        (session_id, session_data) tuples
    """
    if not settings.sessions_dir.exists():
        return

    for session_dir in settings.sessions_dir.iterdir():
        if session_dir.is_dir() and (session_dir / "session.json").exists():
            try:
                state_manager = StateManager(session_dir.name)
                session_data = state_manager.read_json("session.json")
                yield session_dir.name, session_data
            except Exception:
                continue  # Skip corrupted sessions
```

Then use in both `find_session_by_path()` and `list_sessions()`.

**Change 7: Remove start_review() or fix it**

Option A - Remove it:
```python
# Delete server.py:303-369
# Update documentation to recommend:
#   create_session() + discover_documents()
#   or /initialize + /document-discovery
```

Option B - Fix it:
```python
async def start_review(...) -> str:
    """Quick-start with proper workflow tracking."""
    try:
        # This will handle duplicates and mark initialize complete
        session_result = await session_tools.create_session(...)
    except session_tools.SessionAlreadyExistsError as e:
        return f"✗ Session already exists: {e.existing_session_id}\n\n" + \
               "Use /initialize for guided resolution."

    # Document discovery already marks its stage
    discovery_result = await document_tools.discover_documents(session_id)

    # Return combined summary
    return format_quickstart_summary(session_result, discovery_result)
```

### 9.3 Low Priority (Polish)

**Change 8: Separate data from presentation**
```python
# Tools return structured data only
async def create_session(...) -> dict:
    return {
        "session_id": session_id,
        "project_name": project_name,
        "created_at": now.isoformat(),
        "requirements_total": requirements_count,
        # Remove: "message": "..." (presentation logic)
    }
```

**Change 9: Add type hints for error handling**
```python
# File: src/registry_review_mcp/models/errors.py

class SessionAlreadyExistsError(RegistryReviewError):
    """Raised when trying to create duplicate session."""

    def __init__(self, message: str, *, existing_session_id: str):
        super().__init__(message, details={"existing_session_id": existing_session_id})
        self.existing_session_id = existing_session_id
```

---

## 10. Testing Recommendations

### 10.1 Test Cases Needed

**Test: Duplicate session detection**
```python
async def test_create_session_duplicate_path():
    """Creating session with existing path should raise error."""
    await create_session("Project A", "/path/to/docs")

    with pytest.raises(SessionAlreadyExistsError) as exc:
        await create_session("Project B", "/path/to/docs")  # Different name, same path

    assert exc.value.existing_session_id is not None
```

**Test: Initialize workflow stage**
```python
async def test_create_session_marks_initialize_complete():
    """Session creation should mark initialize stage complete."""
    result = await create_session("Test", "/path")

    session = await load_session(result["session_id"])
    assert session["workflow_progress"]["initialize"] == "completed"
```

**Test: Checklist validation**
```python
async def test_create_session_invalid_checklist():
    """Invalid methodology should raise clear error."""
    with pytest.raises(ValueError, match="Checklist not found"):
        await create_session("Test", "/path", methodology="invalid-v9.9.9")
```

**Test: Idempotency**
```python
async def test_start_review_vs_manual_workflow():
    """Quick-start and manual workflow should produce identical sessions."""

    # Path 1: Quick-start
    session1 = await start_review("Project", "/path1")

    # Path 2: Manual
    session2 = await create_session("Project", "/path2")
    await discover_documents(session2["session_id"])

    # Both should have same workflow progress
    s1_data = await load_session(session1["session_id"])
    s2_data = await load_session(session2["session_id"])

    assert s1_data["workflow_progress"] == s2_data["workflow_progress"]
```

---

## 11. Migration Path

### Phase 1: Non-Breaking Changes (Week 1)
1. Add `SessionAlreadyExistsError` to errors.py
2. Add `load_checklist_requirements()` helper
3. Add `find_session_by_path()` helper
4. Add tests for new helpers

### Phase 2: Fix create_session() (Week 1)
1. Update `create_session()` to mark initialize complete
2. Update `create_session()` to check duplicates
3. Update existing tests
4. Add new test coverage

### Phase 3: Update Prompts (Week 2)
1. Remove workflow update from `initialize_prompt()`
2. Add duplicate error handling
3. Test prompt flows

### Phase 4: Fix or Remove start_review() (Week 2)
1. Decide: remove or fix?
2. If fixing: add duplicate handling
3. Update documentation
4. Update integration tests

### Phase 5: Cleanup (Week 3)
1. Remove dead error handling code
2. Extract session iteration helper
3. Separate presentation from data
4. Performance profiling for large session counts

---

## 12. Risk Assessment

### High Risk Changes
- **Duplicate detection in create_session()** - Could break existing workflows that rely on creating multiple sessions for same path
  - *Mitigation:* Add flag `allow_duplicate=False` for backward compatibility

- **Workflow stage in create_session()** - Changes session schema
  - *Mitigation:* Version the session schema, add migration script

### Medium Risk Changes
- **Remove start_review()** - Breaks API contract
  - *Mitigation:* Deprecate for 2 versions before removing

- **Checklist validation** - Could break sessions with missing checklists
  - *Mitigation:* Add validation warnings in Phase 1, errors in Phase 2

### Low Risk Changes
- Helper functions - Pure additions
- Test coverage - No production impact
- Documentation updates - No code impact

---

## 13. Conclusion

The session initialization code requires significant refactoring to address:

1. **Code duplication** - Extract checklist loading, session iteration
2. **Inconsistent state management** - Tools must own their workflow stages
3. **Layering violations** - Prompts should not manipulate state directly
4. **Missing validation** - Checklist loading needs error handling
5. **Duplicate session handling** - Must be in tool layer, not prompt layer

The recommended approach prioritizes **correctness first** (fixing workflow stages, duplicate detection), then **maintainability** (extracting helpers, removing duplication), and finally **polish** (presentation separation, performance).

Estimated effort: **2-3 weeks** for complete refactoring with full test coverage and migration.

**Priority order:**
1. Fix workflow stage marking (High - Correctness)
2. Add duplicate detection to tools (High - Correctness)
3. Remove prompt state manipulation (High - Architecture)
4. Extract helpers (Medium - Maintainability)
5. Fix/remove start_review() (Medium - API clarity)
6. Presentation cleanup (Low - Polish)
