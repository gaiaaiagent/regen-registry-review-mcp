"""Report generation workflow prompt."""

from pathlib import Path
from mcp.types import TextContent

from ..tools import report_tools, session_tools
from ..utils.state import StateManager
from ..models.errors import SessionNotFoundError


async def report_generation_prompt(session_id: str | None = None) -> list[TextContent]:
    """
    Execute report generation workflow.

    This prompt orchestrates report generation:
    1. Loads session, evidence, and validation data
    2. Generates Markdown report
    3. Generates JSON report
    4. Saves both to session directory
    5. Presents summary and next steps

    Args:
        session_id: Optional session identifier. If not provided, uses most recent session.

    Returns:
        Formatted report summary with next steps
    """
    # Handle session selection
    auto_selected = False
    if not session_id:
        sessions = await session_tools.list_sessions()
        if not sessions:
            return [TextContent(
                type="text",
                text="""# Report Generation Workflow

No review sessions found. To generate a report, you need to:

1. **Create a session** with `/initialize` or `/document-discovery`
2. **Extract evidence** with `/evidence-extraction`
3. **(Optional) Run validation** with `/cross-validation`
4. **Run this prompt** to generate reports

**Quick Start:**
```
/document-discovery Your Project Name, /path/to/documents
/evidence-extraction
/cross-validation
/report-generation
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

Reports require evidence extraction to be completed first.

Please run:
```
/evidence-extraction
```

Then return here for report generation.
"""
        )]

    # Extract project info
    project_metadata = session.get('project_metadata', {})
    project_name = project_metadata.get('project_name', 'Unknown')

    print(f"\n{'='*80}")
    print(f"Report Generation for: {project_name}")
    print(f"Session: {session_id}")
    print(f"{'='*80}\n")

    # Generate reports
    print("Generating Markdown report...")
    md_result = await report_tools.generate_review_report(
        session_id=session_id,
        format="markdown"
    )

    print("Generating JSON report...")
    json_result = await report_tools.generate_review_report(
        session_id=session_id,
        format="json"
    )

    # Format results
    report = []
    report.append(f"\n{'='*80}")
    report.append("REPORT GENERATION COMPLETE")
    report.append(f"{'='*80}\n")

    # Add auto-selection notice if applicable
    if auto_selected:
        report.append(f"*Note: Auto-selected most recent session*\n")

    report.append(f"**Session:** {session_id}")
    report.append(f"**Project:** {project_name}")
    report.append("")

    # Generated reports section
    report.append("## Generated Reports")
    report.append("")

    md_path = Path(md_result["report_path"])
    json_path = Path(json_result["report_path"])

    report.append(f"📄 **Markdown Report:** `{md_path.name}`")
    report.append(f"   Path: {md_result['report_path']}")
    report.append("   - Complete checklist with findings")
    report.append("   - Evidence citations for each requirement")
    report.append("   - Cross-validation results")
    report.append("   - Items for human review")
    report.append("")

    report.append(f"📊 **JSON Report:** `{json_path.name}`")
    report.append(f"   Path: {json_result['report_path']}")
    report.append("   - Structured data for programmatic access")
    report.append("   - All evidence and validation details")
    report.append("   - Machine-readable format")
    report.append("")

    # Report summary
    summary = md_result["summary"]

    report.append("## Report Summary")
    report.append("")

    report.append("### Requirements Coverage")
    if summary["requirements_total"] > 0:
        report.append(f"  ✅ **Covered:** {summary['requirements_covered']}/{summary['requirements_total']} ({summary['requirements_covered']/summary['requirements_total']*100:.1f}%)")
        report.append(f"  ⚠️  **Partial:** {summary['requirements_partial']}/{summary['requirements_total']} ({summary['requirements_partial']/summary['requirements_total']*100:.1f}%)")
        report.append(f"  ❌ **Missing:** {summary['requirements_missing']}/{summary['requirements_total']} ({summary['requirements_missing']/summary['requirements_total']*100:.1f}%)")
        report.append(f"  **Overall Coverage:** {summary['overall_coverage']*100:.1f}%")
    else:
        report.append("  No requirements data available")

    report.append("")

    if summary.get("validations_total", 0) > 0:
        report.append("### Cross-Document Validation")
        report.append(f"  ✅ **Passed:** {summary['validations_passed']}/{summary['validations_total']}")
        report.append(f"  ⚠️  **Warnings:** {summary['validations_warning']}/{summary['validations_total']}")
        report.append(f"  ❌ **Failed:** {summary['validations_failed']}/{summary['validations_total']}")
        report.append("")

    report.append("### Review Statistics")
    report.append(f"  **Documents Reviewed:** {summary['documents_reviewed']}")
    report.append(f"  **Evidence Snippets:** {summary['total_evidence_snippets']}")
    report.append(f"  **Items for Human Review:** {summary['items_for_human_review']}")
    report.append("")

    # Next steps
    report.append(f"{'='*80}")
    report.append("NEXT STEPS")
    report.append(f"{'='*80}\n")

    if summary['items_for_human_review'] > 0:
        report.append(f"⚠️  **Action Required:** {summary['items_for_human_review']} item(s) need human review")
        report.append("")
        report.append("1. Open `report.md` to review detailed findings")
        report.append("2. Address flagged items:")
        report.append("   - Review partial requirements for sufficient evidence")
        report.append("   - Investigate any validation warnings or failures")
        report.append("   - Verify missing requirements are truly not applicable")
        report.append("3. Make final approval decision")
        report.append("")
    else:
        report.append("✅ **No items flagged for review**")
        report.append("")
        report.append("1. Open `report.md` to review the complete findings")
        report.append("2. Verify all requirements are properly documented")
        report.append("3. Make final approval decision")
        report.append("")

    report.append("**The review report is ready for final approval decision.**")
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"💡 **Tip:** Use `cat {md_path}` to view the Markdown report in your terminal")

    # Update workflow progress
    workflow["report_generation"] = "completed"
    state_manager = StateManager(session_id)
    state_manager.update_json("session.json", {"workflow_progress": workflow})

    return [TextContent(type="text", text="\n".join(report))]


__all__ = ["report_generation_prompt"]
