"""Cross-validation workflow prompt."""

from mcp.types import TextContent

from ..config.settings import settings
from ..tools import validation_tools, session_tools
from ..utils.state import StateManager
from ..models.errors import SessionNotFoundError


async def cross_validation_prompt(session_id: str | None = None) -> list[TextContent]:
    """
    Execute cross-document validation workflow.

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
            return [TextContent(
                type="text",
                text="""# Cross-Validation Workflow

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
"""
            )]
        # Use most recent session
        session_id = sessions[0]["session_id"]
        auto_selected = True
        print(f"Auto-selected most recent session: {session_id}")

    # Verify session exists
    try:
        session = await session_tools.load_session(session_id)
    except SessionNotFoundError:
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

    # Check prerequisites
    workflow = session.get("workflow_progress", {})
    if workflow.get("evidence_extraction") != "completed":
        return [TextContent(
            type="text",
            text=f"""Evidence extraction has not been completed for session {session_id}.

Please run evidence extraction first:
```
/evidence-extraction
```

Then return here for cross-validation.
"""
        )]

    # Extract project info
    project_metadata = session.get('project_metadata', {})
    project_name = project_metadata.get('project_name', 'Unknown')

    print(f"\n{'='*80}")
    print(f"Cross-Document Validation for: {project_name}")
    print(f"Session: {session_id}")
    print(f"{'='*80}\n")

    # Load evidence data
    state_manager = StateManager(session_id)
    evidence_data = state_manager.read_json("evidence.json")

    # Run cross-validation (use LLM-native if enabled)
    if settings.use_llm_native_extraction:
        print("🤖 Using LLM-native unified validation...")
        from ..tools import analyze_llm
        validation_results = await analyze_llm.cross_validate_llm(session_id)
    else:
        print("Running cross-document validation checks...")
        validation_results = await validation_tools.cross_validate(session_id)

    # TODO: In future, extract actual validation fields from evidence
    # For now, validation checks return placeholder data

    # Format results
    report = []
    report.append(f"\n{'='*80}")
    report.append("CROSS-VALIDATION RESULTS")
    report.append(f"{'='*80}\n")

    # Add auto-selection notice if applicable
    if auto_selected:
        report.append(f"*Note: Auto-selected most recent session*\n")

    summary = validation_results["summary"]

    report.append("📊 Validation Summary:")
    report.append(f"  Total Checks: {summary['total_validations']}")

    if summary['total_validations'] > 0:
        report.append(f"  ✅ Passed: {summary['validations_passed']} ({summary['validations_passed']/summary['total_validations']*100:.1f}%)")
        report.append(f"  ⚠️  Warnings: {summary['validations_warning']} ({summary['validations_warning']/summary['total_validations']*100:.1f}%)")
        report.append(f"  ❌ Failed: {summary['validations_failed']} ({summary['validations_failed']/summary['total_validations']*100:.1f}%)")
    else:
        report.append("  No validation checks performed yet.")
        report.append("  (Validation checks will be added as features are implemented)")

    report.append("")

    # Date alignment checks
    if validation_results.get("date_alignments"):
        report.append("## Date Alignment Checks")
        for val in validation_results["date_alignments"]:
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(val["status"], "❓")
            report.append(f"{status_icon} {val['message']}")
        report.append("")

    # Land tenure checks
    if validation_results.get("land_tenure"):
        report.append("## Land Tenure Checks")
        for val in validation_results["land_tenure"]:
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(val["status"], "❓")
            flag_icon = " 🚩" if val.get("flagged_for_review") else ""
            report.append(f"{status_icon}{flag_icon} {val['message']}")
            if val.get("discrepancies"):
                for disc in val["discrepancies"]:
                    report.append(f"  - {disc}")
        report.append("")

    # Project ID checks
    if validation_results.get("project_ids"):
        report.append("## Project ID Checks")
        for val in validation_results["project_ids"]:
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(val["status"], "❓")
            report.append(f"{status_icon} {val['message']}")
        report.append("")

    # Items flagged for review
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
        report.append("## Items Flagged for Review")
        for idx, item in enumerate(flagged_items, 1):
            report.append(f"{idx}. {item}")
        report.append("")

    # Next steps
    report.append(f"{'='*80}")
    report.append("NEXT STEPS")
    report.append(f"{'='*80}\n")

    report.append("📄 Validation results saved to: validation.json")
    report.append("📊 Session updated with validation statistics")
    report.append("")
    report.append("**Next:** Generate the review report with `/report-generation`")
    report.append("")
    report.append("This will create:")
    report.append("  • Markdown report with all findings")
    report.append("  • JSON report for programmatic access")
    report.append("  • Summary statistics and items for human review")

    # Update workflow progress and statistics
    workflow["cross_validation"] = "completed"

    # Update statistics with validation results
    stats = session.get("statistics", {})
    stats["validations_passed"] = summary["validations_passed"]
    stats["validations_failed"] = summary["validations_failed"]

    state_manager.update_json("session.json", {
        "workflow_progress": workflow,
        "statistics": stats
    })

    return [TextContent(type="text", text="\n".join(report))]


__all__ = ["cross_validation_prompt"]
