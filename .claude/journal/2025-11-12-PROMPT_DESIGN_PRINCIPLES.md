# MCP Prompt Design Principles

**Document Purpose:** Systematic requirements for all MCP prompts to ensure consistency and excellent user experience.

---

## Core Principles

### 1. Auto-Selection is Mandatory

**Requirement:** All workflow prompts MUST auto-select the most recent session when no `session_id` is provided.

**Rationale:** Reduces friction and prevents user frustration. Most workflows operate on a single active session.

**Implementation Pattern:**

```python
async def your_workflow_prompt(session_id: str | None = None) -> list[TextContent]:
    """Your workflow description.

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.
    """
    # REQUIRED: Auto-selection logic
    auto_selected = False
    if not session_id:
        sessions = await session_tools.list_sessions()
        if not sessions:
            return [TextContent(type="text", text="""Help message for no sessions...""")]
        session_id = sessions[0]["session_id"]
        auto_selected = True
        print(f"Auto-selected most recent session: {session_id}")

    # ... rest of workflow ...

    # REQUIRED: Indicate auto-selection in response
    if auto_selected:
        report.append(f"*Note: Auto-selected most recent session*\n")
```

**Testing Pattern:**

```python
async def test_auto_selects_most_recent_session(self):
    """Test that calling without session_id auto-selects most recent session."""
    # Create a session
    session = await create_session(...)

    # Call prompt without session_id
    result = await your_prompt(session_id=None)

    # Verify it worked and indicated auto-selection
    assert "Auto-selected" in result[0].text or "*Note:" in result[0].text
```

**Acceptance Criteria:**
- ✅ Prompt accepts `session_id: str | None = None`
- ✅ When `None`, automatically uses most recent session
- ✅ Logs to stderr: `print(f"Auto-selected most recent session: {session_id}")`
- ✅ Indicates in response: `*Note: Auto-selected most recent session*`
- ✅ Test exists for auto-selection behavior

---

### 2. Fail Explicitly, Never Silently

**Requirement:** Prompts MUST provide helpful error messages when prerequisites are not met.

**Good Example:**
```
Evidence extraction has not been completed for session ABC.

Please run evidence extraction first:
```
/evidence-extraction
```

Then return here for validation.
```

**Bad Example:**
```
Error: evidence_extraction not completed
```

**Pattern:** Always explain what went wrong, what to do about it, and provide concrete next steps.

---

### 3. Guide the User Through the Workflow

**Requirement:** Every prompt response MUST end with clear next steps.

**Pattern:**
```markdown
## Next Steps

1. Review the validation results above
2. Run `/report-generation` to create the final report
3. Address any flagged items before making approval decision
```

**Acceptance Criteria:**
- ✅ Response includes "Next Steps" or equivalent section
- ✅ Next steps are concrete and actionable
- ✅ Next step is usually another prompt in the workflow

---

### 4. Check Prerequisites Explicitly

**Requirement:** Prompts that depend on previous workflow stages MUST check prerequisites and fail helpfully.

**Pattern:**
```python
# Check prerequisites
workflow = session.get("workflow_progress", {})
if workflow.get("evidence_extraction") != "completed":
    return [TextContent(
        type="text",
        text=f"""Evidence extraction has not been completed.

Please run evidence extraction first:
```
/evidence-extraction
```

Then return here for {current_stage_name}.
"""
    )]
```

**Acceptance Criteria:**
- ✅ Checks `workflow_progress` for required stages
- ✅ Returns helpful message if prerequisite missing
- ✅ Suggests the specific prompt to run

---

### 5. Update Workflow Progress

**Requirement:** Prompts MUST update `workflow_progress` upon successful completion.

**Pattern:**
```python
# Update workflow progress
workflow["cross_validation"] = "completed"
state_manager.update_json("session.json", {"workflow_progress": workflow})
```

**Acceptance Criteria:**
- ✅ Updates workflow progress on success
- ✅ Does NOT update on failure
- ✅ Uses status: "pending" | "in_progress" | "completed"

---

### 6. Provide Context in Every Response

**Requirement:** Responses MUST include session and project context.

**Pattern:**
```markdown
**Session:** session-abc123
**Project:** Botany Farm 2022-2023
```

**Rationale:** Users should always know what they're operating on.

---

### 7. Use Consistent Visual Language

**Requirement:** Use standardized icons and formatting for status indicators.

**Standard Icons:**
- ✅ Success, pass, covered
- ⚠️ Warning, partial, needs attention
- ❌ Fail, missing, error
- 🚩 Flagged for review
- 📊 Statistics, summary
- 📄 Document, file
- 💡 Tip, suggestion

**Example:**
```
✅ **Covered:** 11/23 (47.8%)
⚠️  **Partial:** 12/23 (52.2%)
❌ **Missing:** 0/23 (0.0%)
```

---

### 8. Provide Helpful Guidance When No Sessions Exist

**Requirement:** First-time users should get clear guidance on how to start.

**Pattern:**
```markdown
# Workflow Name

No review sessions found. To use this workflow, you need to:

1. **Create a session** with `/initialize` or `/document-discovery`
2. **Run prerequisite steps** (list them)
3. **Run this prompt again** to continue

**Quick Start:**
```
/document-discovery Your Project Name, /path/to/documents
/evidence-extraction
/current-workflow
```

The workflow will guide you through each step.
```

**Acceptance Criteria:**
- ✅ Explains what's missing
- ✅ Provides multiple options for getting started
- ✅ Includes concrete examples
- ✅ References other prompts by name

---

## Testing Requirements

### Auto-Selection Tests (REQUIRED for all workflow prompts)

```python
class TestYourWorkflowPrompt:
    """Tests for your workflow prompt."""

    async def test_auto_selects_most_recent_session(self):
        """REQUIRED: Test auto-selection behavior."""
        # Create a session
        session = await create_session(...)

        # Call without session_id
        result = await your_prompt(session_id=None)

        # Verify success and indication
        assert session["session_id"] in str(result)
        assert "Auto-selected" in result[0].text or "*Note:" in result[0].text

    async def test_no_session_provides_guidance(self):
        """REQUIRED: Test helpful guidance when no sessions exist."""
        # Call without any sessions
        result = await your_prompt(session_id=None)

        # Verify helpful guidance
        assert "No review sessions found" in result[0].text or similar
        assert "/initialize" in result[0].text or "/document-discovery" in result[0].text

    async def test_prerequisite_checking(self):
        """REQUIRED: Test prerequisite validation."""
        # Create session without completing prerequisite
        session = await create_session(...)

        # Call prompt
        result = await your_prompt(session_id=session["session_id"])

        # Verify helpful prerequisite message
        assert "not been completed" in result[0].text or similar
        assert suggests the prerequisite prompt
```

---

## Checklist for New Workflow Prompts

Use this checklist when creating new workflow prompts:

### Design Phase
- [ ] Defined clear purpose and prerequisites
- [ ] Identified previous and next workflow stages
- [ ] Designed helpful error messages
- [ ] Planned response structure with sections

### Implementation Phase
- [ ] Accepts `session_id: str | None = None`
- [ ] Implements auto-selection with indicator
- [ ] Checks prerequisites explicitly
- [ ] Updates workflow progress on success
- [ ] Includes session/project context in response
- [ ] Uses consistent visual language (icons)
- [ ] Provides clear next steps
- [ ] Handles "no sessions" case with guidance

### Testing Phase
- [ ] Test: Auto-selection works correctly
- [ ] Test: Auto-selection is indicated in response
- [ ] Test: No sessions provides helpful guidance
- [ ] Test: Prerequisite checking works
- [ ] Test: Workflow progress is updated
- [ ] Test: End-to-end with real data

### Documentation Phase
- [ ] Docstring explains auto-selection
- [ ] Examples show usage without session_id
- [ ] Registered in server.py with decorator
- [ ] Added to workflow documentation

---

## Example: Complete Prompt Implementation

```python
"""Example workflow prompt following all principles."""

from mcp.types import TextContent
from ..tools import session_tools, your_tools
from ..utils.state import StateManager
from ..models.errors import SessionNotFoundError


async def example_workflow_prompt(session_id: str | None = None) -> list[TextContent]:
    """Execute example workflow (Stage X).

    This prompt does X, Y, and Z. It requires stage N to be completed first.

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.

    Returns:
        Formatted workflow results with next steps

    Examples:
        /example-workflow (uses most recent session)
        /example-workflow session-abc123
    """
    # PRINCIPLE 1: Auto-selection
    auto_selected = False
    if not session_id:
        sessions = await session_tools.list_sessions()
        if not sessions:
            # PRINCIPLE 8: Helpful guidance when no sessions
            return [TextContent(
                type="text",
                text="""# Example Workflow

No review sessions found. To use this workflow, you need to:

1. **Create a session** with `/initialize` or `/document-discovery`
2. **Complete prerequisite** with `/prerequisite-workflow`
3. **Run this prompt again** to continue

**Quick Start:**
```
/document-discovery Your Project Name, /path/to/documents
/prerequisite-workflow
/example-workflow
```

The workflow will guide you through each step.
"""
            )]
        session_id = sessions[0]["session_id"]
        auto_selected = True
        print(f"Auto-selected most recent session: {session_id}")

    # Verify session exists
    try:
        session = await session_tools.load_session(session_id)
    except SessionNotFoundError:
        # PRINCIPLE 2: Fail explicitly
        sessions = await session_tools.list_sessions()
        session_list = "\n".join([f"- {s['session_id']} ({s['project_name']})" for s in sessions])
        return [TextContent(
            type="text",
            text=f"""Session '{session_id}' not found.

Available sessions:
{session_list}

Use one of the above session IDs or create a new session.
"""
        )]

    # PRINCIPLE 4: Check prerequisites
    workflow = session.get("workflow_progress", {})
    if workflow.get("prerequisite_stage") != "completed":
        return [TextContent(
            type="text",
            text=f"""Prerequisite stage has not been completed for session {session_id}.

Please run the prerequisite first:
```
/prerequisite-workflow
```

Then return here for this workflow.
"""
        )]

    # Extract project info - PRINCIPLE 6: Provide context
    project_metadata = session.get('project_metadata', {})
    project_name = project_metadata.get('project_name', 'Unknown')

    # Do the work...
    results = await your_tools.do_work(session_id)

    # PRINCIPLE 7: Use consistent visual language
    report = []
    report.append(f"\n{'='*80}")
    report.append("EXAMPLE WORKFLOW RESULTS")
    report.append(f"{'='*80}\n")

    # PRINCIPLE 1: Indicate auto-selection
    if auto_selected:
        report.append(f"*Note: Auto-selected most recent session*\n")

    # PRINCIPLE 6: Provide context
    report.append(f"**Session:** {session_id}")
    report.append(f"**Project:** {project_name}")
    report.append("")

    # Format results with icons
    report.append("## Summary")
    report.append(f"✅ **Success items:** {results['success_count']}")
    report.append(f"⚠️  **Warnings:** {results['warning_count']}")
    report.append(f"❌ **Failures:** {results['failure_count']}")
    report.append("")

    # PRINCIPLE 3: Guide the user through the workflow
    report.append(f"{'='*80}")
    report.append("NEXT STEPS")
    report.append(f"{'='*80}\n")
    report.append("1. Review the results above")
    report.append("2. Run `/next-workflow` to continue")
    report.append("3. Address any warnings or failures")
    report.append("")

    # PRINCIPLE 5: Update workflow progress
    workflow["example_stage"] = "completed"
    state_manager = StateManager(session_id)
    state_manager.update_json("session.json", {"workflow_progress": workflow})

    return [TextContent(type="text", text="\n".join(report))]
```

---

## Enforcement

### Code Review Checklist
When reviewing PRs with new prompts, verify:
1. Auto-selection is implemented with indication
2. Helpful error messages for all failure modes
3. Next steps are clear and actionable
4. Tests cover auto-selection and edge cases
5. Docstring mentions auto-selection behavior

### Automated Testing
- All workflow prompts must have auto-selection tests
- CI fails if auto-selection tests are missing
- Test coverage reports include prompt testing

### Documentation
- All prompts documented with examples showing auto-selection
- README shows workflows without explicit session IDs
- User guides emphasize "just run the prompt" workflow

---

**Version:** 1.0
**Last Updated:** November 12, 2025
**Status:** Active - Required for all new development
