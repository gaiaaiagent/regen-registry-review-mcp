"""Requirement mapping workflow - Stage 3 of registry review."""

from mcp.types import TextContent

from ..tools import mapping_tools
from ..utils.state import StateManager
from .helpers import (
    text_content,
    format_error,
    format_workflow_header,
    format_next_steps_section,
    get_or_select_session,
    validate_session_exists,
)


async def requirement_mapping_prompt(
    session_id: str | None = None
) -> list[TextContent]:
    """Map discovered documents to checklist requirements (Stage 3).

    This prompt loads the checklist, analyzes documents, and suggests
    which documents satisfy which requirements.

    Args:
        session_id: Optional existing session ID (auto-selects latest if not provided)

    Returns:
        Formatted mapping results with human review interface
    """
    # Get or select session
    session_id, auto_selected, error = await get_or_select_session(
        session_id, None, None, "Requirement Mapping"
    )

    if error:
        return error

    # Validate session exists
    error = await validate_session_exists(session_id, "Requirement Mapping")
    if error:
        return error

    # Load session data
    state_manager = StateManager(session_id)
    session_data = state_manager.read_json("session.json")
    project_name = session_data.get("project_metadata", {}).get("project_name", "Unknown")
    methodology = session_data.get("project_metadata", {}).get("methodology", "soil-carbon-v1.2.2")

    # Check that document discovery was completed
    workflow_progress = session_data.get("workflow_progress", {})
    if workflow_progress.get("document_discovery") != "completed":
        return format_error(
            "Document Discovery Not Complete",
            "You must complete Stage 2 (Document Discovery) before mapping requirements.",
            "Run `/B-document-discovery` first to discover and classify all project documents."
        )

    # Run requirement mapping
    try:
        results = await mapping_tools.map_all_requirements(session_id)

        # Format confidence breakdown
        status = await mapping_tools.get_mapping_status(session_id)
        confidence_breakdown = status.get("confidence_breakdown", {})

        confidence_text = f"""**Confidence Breakdown:**
  - 🟢 **High confidence** (>75%): {confidence_breakdown.get('high', 0)} mappings
  - 🟡 **Medium confidence** (50-75%): {confidence_breakdown.get('medium', 0)} mappings
  - 🟠 **Low confidence** (<50%): {confidence_breakdown.get('low', 0)} mappings
"""

        # Load documents for summary
        documents_data = state_manager.read_json("documents.json")
        documents = documents_data.get("documents", documents_data)
        doc_count = len(documents)

        # Build message
        header = format_workflow_header("Requirement Mapping", session_id, project_name, auto_selected)

        coverage_rate = results.get("coverage_rate", 0.0)
        coverage_pct = int(coverage_rate * 100)

        content = f"""## ✅ Mapping Complete

Successfully mapped **{results['mapped_count']}/{results['total_requirements']} requirements** ({coverage_pct}% coverage)

### Summary
- **Total Requirements:** {results['total_requirements']}
- **Mapped:** {results['mapped_count']} requirements have suggested documents
- **Unmapped:** {results['unmapped_count']} requirements need attention
- **Documents Analyzed:** {doc_count}
- **Methodology:** {methodology}

{confidence_text}

### What Happened

The agent analyzed all {doc_count} discovered documents and matched them to checklist requirements based on:
- Document classification (e.g., project plan, land tenure, monitoring report)
- Requirement categories (e.g., Land Tenure, Baseline, GIS Data)
- Evidence type expectations

Each mapping includes a confidence score indicating how well the documents match the requirement.

---

## Next Steps

### ✅ Review Suggested Mappings (Recommended)

Check the mapping details:

```
load_session {session_id}
```

Look at the `mappings` array in the JSON output to see which documents are mapped to which requirements.

### ⚠️ Fix Unmapped Requirements ({results['unmapped_count']} need attention)

If requirements are unmapped, you can:

1. **Manually map a requirement to documents:**
```
confirm_mapping {session_id} REQ-XXX ["doc-id-1", "doc-id-2"]
```

2. **Request additional documents from proponent**

3. **Proceed anyway** if requirements are non-mandatory

### 🎯 Proceed to Evidence Extraction

Once satisfied with mappings, extract evidence from mapped documents:

```
/D-evidence-extraction
```

This will pull specific data points and snippets from the documents you've mapped.

---

## Tools Available

**View mapping status:**
```
get_mapping_status {session_id}
```

**Confirm a mapping:**
```
confirm_mapping {session_id} REQ-007 ["doc-land-tenure", "doc-project-plan"]
```

**Remove incorrect mapping:**
```
remove_mapping {session_id} REQ-007 "doc-wrong-document"
```
"""

        next_steps = format_next_steps_section([
            "Review mappings: `load_session {session_id}`",
            "Fix unmapped requirements (if needed)",
            "Run evidence extraction: `/D-evidence-extraction`",
        ], "Next Step: Evidence Extraction")

        message = header + content + next_steps

        return text_content(message)

    except FileNotFoundError as e:
        return format_error(
            "Checklist Not Found",
            f"Could not load checklist for methodology: {methodology}",
            f"Error details: {str(e)}\n\nPlease ensure the checklist file exists in the checklists directory."
        )

    except ValueError as e:
        error_msg = str(e)
        if "No documents discovered" in error_msg:
            return format_error(
                "No Documents Found",
                "Cannot map requirements without documents.",
                "Run Stage 2 first: `/B-document-discovery`"
            )
        else:
            return format_error(
                "Mapping Failed",
                error_msg,
                "Please check the session state and try again."
            )

    except Exception as e:
        return format_error(
            "Requirement Mapping Failed",
            f"An error occurred during requirement mapping: {str(e)}",
            "Please check the session and try again, or contact support if the issue persists."
        )
