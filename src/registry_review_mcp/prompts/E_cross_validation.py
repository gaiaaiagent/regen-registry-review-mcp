"""Cross-validation workflow - Stage 5 of registry review."""

from mcp.types import TextContent

from ..config.settings import settings
from ..tools import validation_tools, session_tools
from ..utils.state import StateManager
from ..models.errors import SessionNotFoundError
from .helpers import (
    text_content,
    format_error,
    format_workflow_header,
    format_next_steps_section,
)


async def cross_validation_prompt(session_id: str | None = None) -> list[TextContent]:
    """Execute cross-document validation workflow.

    This prompt orchestrates all validation checks:
    1. Loads session and evidence data
    2. Extracts fields for validation (dates, land tenure, project IDs)
    3. Runs validation checks
    4. Calculates summary statistics
    5. Saves validation results
    6. Presents formatted results with next steps

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.

    Returns:
        Formatted validation results with next steps
    """
    # Handle session selection
    auto_selected = False
    if not session_id:
        sessions = await session_tools.list_sessions()
        if not sessions:
            return text_content("""# Cross-Validation Workflow

No review sessions found. To run cross-validation, you need to:

1. **Create a session** with `/initialize` or `/document-discovery`
2. **Extract evidence** with `/evidence-extraction`
3. **Run this prompt again** for validation

**Quick Start:**
```
/document-discovery Your Project Name, /path/to/documents
/evidence-extraction
/cross-validation
```

The workflow will guide you through each step.
""")
        session_id = sessions[0]["session_id"]
        auto_selected = True

    # Verify session exists
    try:
        session = await session_tools.load_session(session_id)
    except SessionNotFoundError:
        sessions = await session_tools.list_sessions()
        session_list = "\n".join([f"- {s['session_id']} ({s['project_name']})" for s in sessions])
        return format_error(
            "Session Not Found",
            f"Session '{session_id}' not found.\n\nAvailable sessions:\n{session_list}",
            "Use one of the above session IDs or create a new session."
        )

    # Check prerequisites
    workflow = session.get("workflow_progress", {})
    if workflow.get("evidence_extraction") != "completed":
        return text_content(f"""Evidence extraction has not been completed for session {session_id}.

Please run evidence extraction first:
```
/evidence-extraction
```

Then return here for cross-validation.
""")

    # Extract project info
    project_metadata = session.get('project_metadata', {})
    project_name = project_metadata.get('project_name', 'Unknown')

    # Load evidence data and run validation
    state_manager = StateManager(session_id)

    if settings.use_llm_native_extraction:
        from ..tools import analyze_llm
        validation_results = await analyze_llm.cross_validate_llm(session_id)
    else:
        validation_results = await validation_tools.cross_validate(session_id)

    summary = validation_results["summary"]

    # Build header
    header = format_workflow_header("Cross-Validation", session_id, project_name, auto_selected)

    # Build validation summary
    content = ["## ✅ Cross-Validation Complete\n"]

    content.append("**Validation Summary:**")
    content.append(f"- Total Checks: {summary['total_validations']}")

    if summary['total_validations'] > 0:
        total = summary['total_validations']
        passed = summary.get('passed', summary.get('validations_passed', 0))
        warnings = summary.get('warnings', summary.get('validations_warning', 0))
        failed = summary.get('failed', summary.get('validations_failed', 0))
        content.append(f"- ✅ Passed: {passed} ({passed/total*100:.1f}%)")
        content.append(f"- ⚠️  Warnings: {warnings} ({warnings/total*100:.1f}%)")
        content.append(f"- ❌ Failed: {failed} ({failed/total*100:.1f}%)")
    else:
        content.append("- No validation checks performed yet.")
        content.append("- (Validation checks will be added as features are implemented)")

    content.append("")

    # Detailed checks
    if validation_results.get("date_alignments"):
        content.append("### Date Alignment Checks")
        for val in validation_results["date_alignments"]:
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(val["status"], "❓")
            content.append(f"{status_icon} {val['message']}")
        content.append("")

    if validation_results.get("land_tenure"):
        content.append("### Land Tenure Checks")
        for val in validation_results["land_tenure"]:
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(val["status"], "❓")
            flag_icon = " 🚩" if val.get("flagged_for_review") else ""
            content.append(f"{status_icon}{flag_icon} {val['message']}")
            if val.get("discrepancies"):
                for disc in val["discrepancies"]:
                    content.append(f"  - {disc}")
        content.append("")

    if validation_results.get("project_ids"):
        content.append("### Project ID Checks")
        for val in validation_results["project_ids"]:
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(val["status"], "❓")
            content.append(f"{status_icon} {val['message']}")
        content.append("")

    # Flagged items
    flagged_items = []
    for val_list in [
        validation_results.get("date_alignments", []),
        validation_results.get("land_tenure", []),
        validation_results.get("project_ids", [])
    ]:
        for val in val_list:
            if val.get("flagged_for_review"):
                flagged_items.append(val.get("message", "Unknown issue"))

    if flagged_items:
        content.append("### Items Flagged for Review")
        for idx, item in enumerate(flagged_items, 1):
            content.append(f"{idx}. {item}")
        content.append("")

    content.append("📄 Validation results saved to: validation.json")
    content.append("📊 Session updated with validation statistics")

    # Next steps
    next_steps = format_next_steps_section([
        "Review the validation results above",
        "Generate the review report: `/report-generation`",
        "This will create Markdown and JSON reports with all findings"
    ], "Next Step: Report Generation")

    # Update workflow progress and statistics
    workflow["cross_validation"] = "completed"
    stats = session.get("statistics", {})
    stats["validations_passed"] = summary.get("passed", summary.get("validations_passed", 0))
    stats["validations_failed"] = summary.get("failed", summary.get("validations_failed", 0))

    state_manager.update_json("session.json", {
        "workflow_progress": workflow,
        "statistics": stats
    })

    message = header + "\n".join(content) + next_steps
    return text_content(message)


__all__ = ["cross_validation_prompt"]
