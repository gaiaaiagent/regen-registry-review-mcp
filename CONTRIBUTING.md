# Contributing to Registry Review MCP

Thank you for contributing to the Registry Review MCP! This document provides guidelines to maintain code quality, consistency, and the elegant architecture we've established.

## Philosophy: Elegance Through Subtraction

Our development philosophy follows these principles:

1. **Minimize code while maximizing capability** - The best code is no code. Remove before adding.
2. **Semantic organization** - File structure should mirror system architecture.
3. **LLM-first extraction** - Prefer intelligent extraction over manual regex patterns.
4. **Type-safe, validated data** - Pydantic models everywhere, no raw dicts.
5. **Test-driven confidence** - Every change must maintain 100% test coverage.

> "Perfection is achieved not when there is nothing left to add, but when there is nothing left to take away." – Antoine de Saint-Exupéry

## Code Organization

### Model Organization

Models are organized by workflow stage for semantic clarity:

- **`models/base.py`** - Base classes and common patterns (BaseModel, TimestampedModel, ConfidenceScore, etc.)
- **`models/schemas.py`** - Session/Project/Document/Checklist (Workflow Stages 1-2)
- **`models/evidence.py`** - Evidence extraction models (Stage 3)
- **`models/validation.py`** - Cross-validation models (Stage 4)
- **`models/report.py`** - Report generation models (Stage 5)
- **`models/responses.py`** - MCP tool response format (all stages)
- **`models/errors.py`** - Exception hierarchy (all stages)

**Rules:**
1. Models belong in the file matching their workflow stage
2. **NEVER duplicate model definitions across files** (CI will fail if you do)
3. Import from canonical location: `from ..models.evidence import EvidenceSnippet`
4. Use the centralized `models/__init__.py` for convenience imports

**Adding New Models:**
```python
# ✅ Good: Import from canonical location
from ..models.evidence import EvidenceSnippet, RequirementEvidence

# ✅ Also good: Convenience import
from ..models import EvidenceSnippet, RequirementEvidence

# ❌ Bad: Duplicate model definition
class EvidenceSnippet(BaseModel):  # Already exists in models/evidence.py!
    ...
```

**Model Placement Guide:**
- Session/project setup → `schemas.py`
- Document processing → `schemas.py`
- Evidence extraction → `evidence.py`
- Validation logic → `validation.py`
- Reports/findings → `report.py`
- Tool responses → `responses.py`
- Errors/exceptions → `errors.py`

### Prompt Organization

Prompts use shared helpers to avoid duplication:

- **`prompts/helpers.py`** - Common formatting and session management utilities
- **`prompts/A_initialize.py`** through **`prompts/G_complete.py`** - Stage-specific logic only

**Adding New Prompts:**
```python
from .helpers import (
    get_or_select_session,
    validate_session_exists,
    format_workflow_header,
    format_next_steps_section,
)

async def my_new_prompt(session_id: str | None = None) -> list[TextContent]:
    """My new workflow stage."""
    # Use helpers for common patterns
    session_id, auto_selected, error = await get_or_select_session(
        session_id, None, None, "My Stage"
    )
    if error:
        return error

    # Stage-specific logic here
    ...
```

### Tool Organization

Tools should leverage LLM-native extraction:

**LLM-First Philosophy:**
```python
# ✅ Preferred: LLM extraction → validation
async def validate_dates(session_id: str):
    # Use LLM-extracted structured fields
    fields = await extract_fields_with_llm(session_id, evidence_data)
    # Validate the extracted data
    return validate_date_alignment(fields)

# ❌ Avoid: Manual regex → LLM fallback
async def validate_dates(session_id: str):
    try:
        dates = extract_with_regex(evidence_data)  # Manual, brittle
    except:
        dates = await extract_with_llm(evidence_data)  # Why not use this first?
    return validate_date_alignment(dates)
```

**Why LLM-First:**
- **98.5% faster:** 1 unified LLM call vs. 70 manual operations
- **More accurate:** LLM understands context and variations
- **More maintainable:** No regex pattern maintenance
- **Self-documenting:** Prompts describe requirements in natural language

## Development Workflow

### 1. Before You Start

```bash
# Ensure you're on latest main
git pull origin main

# Create feature branch
git branch feature/your-feature-name

# Install dependencies
uv pip install -e ".[dev]"

# Run duplicate model check
python scripts/check_duplicate_models.py
```

### 2. Making Changes

**Code Style:**
- Use type hints everywhere: `def foo(x: str) -> int:`
- Prefer Pydantic models over dicts
- Use `async`/`await` for I/O operations
- Keep functions under 50 lines
- Document with docstrings (Google style)

**Testing:**
```bash
# Run tests as you develop
pytest tests/ -xvs

# Check specific test file
pytest tests/test_validation.py -v

# Run with coverage
pytest --cov=src/registry_review_mcp tests/
```

### 3. Validation Checks

Before committing, run:

```bash
# 1. Check for duplicate models (critical!)
python scripts/check_duplicate_models.py

# 2. Run full test suite
pytest tests/

# 3. Type checking (if mypy configured)
mypy src/

# 4. Linting (if ruff configured)
ruff check src/
```

### 4. Committing Changes

```python
# Stage your changes
git add src/path/to/changed/files

# Commit with clear message
git commit -m "Add: Feature description

- Bullet point explaining what changed
- Why it changed
- Any breaking changes or migrations needed
"

# Push to your branch
git push origin feature/your-feature-name
```

**Commit Message Format:**
- `Add: ` - New feature or capability
- `Fix: ` - Bug fix
- `Refactor: ` - Code improvement without functionality change
- `Docs: ` - Documentation only
- `Test: ` - Test additions or fixes
- `Chore: ` - Maintenance (dependencies, tooling, etc.)

## Common Tasks

### Adding a New Workflow Stage

1. Create prompt file: `prompts/H_new_stage.py`
2. Use helpers from `prompts/helpers.py`
3. Add tool functions in appropriate `tools/*_tools.py`
4. Create models in appropriate `models/*.py`
5. Add tests in `tests/test_new_stage.py`
6. Update `server.py` to expose the prompt
7. Run full test suite

### Adding a New Validation Check

1. Add validation model to `models/validation.py`
2. Implement validation logic in `tools/validation_tools.py`
3. Use LLM extraction, not manual regex
4. Add tests in `tests/test_validation.py`
5. Update cross_validation prompt if needed

### Adding a New Document Type

1. Add classification pattern to `utils/patterns.py`
2. Update document classifier logic
3. Add handling in `tools/document_tools.py`
4. Add tests with example documents
5. Update documentation

## Architecture Guidelines

### Data Flow

```
1. Session Creation (A_initialize)
   ↓
2. Document Discovery (B_document_discovery)
   ↓ (Documents indexed)
3. Evidence Extraction (C_evidence_extraction)
   ↓ (Requirements mapped)
4. Cross-Validation (D_cross_validation)
   ↓ (Consistency checked)
5. Report Generation (E_report_generation)
   ↓ (Report created)
6. Human Review (F_human_review)
   ↓ (Flags resolved)
7. Complete (G_complete)
   ✓ (Final report)
```

### State Management

- **Session state** stored in `data/sessions/{session_id}/`
- Files: `session.json`, `documents.json`, `evidence.json`, `validation.json`, `report.json`
- Use `StateManager` for all file I/O
- Atomic writes with file locking
- JSON serialization via Pydantic

### Error Handling

```python
from ..models.errors import SessionNotFoundError, DocumentError

# Raise specific errors
if not session_exists(session_id):
    raise SessionNotFoundError(
        f"Session not found: {session_id}",
        details={"session_id": session_id}
    )

# Use @with_error_handling decorator for MCP tools
from ..utils.tool_helpers import with_error_handling

@mcp.tool()
@with_error_handling("my_tool")
async def my_tool(session_id: str) -> str:
    # Error handling automatically applied
    ...
```

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── factories.py             # Test data builders
├── test_session_tools.py    # Unit tests per tool module
├── test_evidence_extraction.py
├── test_validation.py
├── test_integration_*.py    # Integration tests
└── test_*_workflow.py       # End-to-end workflow tests
```

### Writing Tests

```python
import pytest
from tests.factories import SessionBuilder

@pytest.mark.asyncio
async def test_my_feature():
    """Test description following Google docstring style."""
    # Arrange: Set up test data
    session = SessionBuilder().with_project("Test Project").build()

    # Act: Execute the feature
    result = await my_feature(session.session_id)

    # Assert: Verify expectations
    assert result["status"] == "success"
    assert len(result["data"]) > 0
```

### Test Coverage Requirements

- **100% coverage** for all new code
- Integration tests for workflow stages
- Edge cases and error conditions
- Performance tests for LLM calls (mocked)

## Getting Help

- **Documentation:** See `REFACTORING_ROADMAP.md` for architecture decisions
- **Capabilities:** See `CAPABILITIES.md` for MCP server features
- **Issues:** Check existing issues or create new ones
- **Questions:** Ask in pull request comments

## Code Review Checklist

Before requesting review, ensure:

- [ ] No duplicate model definitions (`python scripts/check_duplicate_models.py`)
- [ ] All tests passing (`pytest tests/`)
- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] No manual regex extraction (use LLM-first approach)
- [ ] Models organized by workflow stage
- [ ] Pydantic models for all data structures
- [ ] Error handling with specific exception types
- [ ] No secrets or credentials in code
- [ ] Updated relevant documentation

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

**Remember:** We're building an elegant, maintainable system. When in doubt, favor simplicity, clarity, and subtraction over addition.
