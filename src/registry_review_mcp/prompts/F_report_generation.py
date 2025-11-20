"""Report generation workflow - Stage 6 of registry review."""

from pathlib import Path
from mcp.types import TextContent

from ..tools import report_tools, session_tools
from ..utils.state import StateManager
from ..models.errors import SessionNotFoundError
from .helpers import (
    text_content,
    format_error,
    format_workflow_header,
    format_next_steps_section,
)


async def report_generation_prompt(session_id: str | None = None) -> list[TextContent]:
    """Execute report generation workflow.

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
            return text_content("""# Report Generation Workflow

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

Reports require evidence extraction to be completed first.

Please run:
```
/evidence-extraction
```

Then return here for report generation.
""")

    # Extract project info
    project_metadata = session.get('project_metadata', {})
    project_name = project_metadata.get('project_name', 'Unknown')

    # Generate reports
    md_result = await report_tools.generate_review_report(
        session_id=session_id,
        format="markdown"
    )

    json_result = await report_tools.generate_review_report(
        session_id=session_id,
        format="json"
    )

    summary = md_result["summary"]
    md_path = Path(md_result["report_path"])
    json_path = Path(json_result["report_path"])

    # Build header
    header = format_workflow_header("Report Generation", session_id, project_name, auto_selected)

    # Build content
    content = [
        "## ✅ Report Generation Complete\n",
        "### Generated Reports\n",
        f"📄 **Markdown Report:** `{md_path.name}`",
        f"   Path: {md_result['report_path']}",
        "   - Complete checklist with findings",
        "   - Evidence citations for each requirement",
        "   - Cross-validation results",
        "   - Items for human review\n",
        f"📊 **JSON Report:** `{json_path.name}`",
        f"   Path: {json_result['report_path']}",
        "   - Structured data for programmatic access",
        "   - All evidence and validation details",
        "   - Machine-readable format\n",
        "### Requirements Coverage\n"
    ]

    if summary["requirements_total"] > 0:
        total = summary['requirements_total']
        content.extend([
            f"- ✅ Covered: {summary['requirements_covered']}/{total} ({summary['requirements_covered']/total*100:.1f}%)",
            f"- ⚠️  Partial: {summary['requirements_partial']}/{total} ({summary['requirements_partial']/total*100:.1f}%)",
            f"- ❌ Missing: {summary['requirements_missing']}/{total} ({summary['requirements_missing']/total*100:.1f}%)",
            f"- **Overall Coverage:** {summary['overall_coverage']*100:.1f}%\n"
        ])
    else:
        content.append("No requirements data available\n")

    if summary.get("validations_total", 0) > 0:
        content.extend([
            "### Cross-Document Validation\n",
            f"- ✅ Passed: {summary['validations_passed']}/{summary['validations_total']}",
            f"- ⚠️  Warnings: {summary['validations_warning']}/{summary['validations_total']}",
            f"- ❌ Failed: {summary['validations_failed']}/{summary['validations_total']}\n"
        ])

    content.extend([
        "### Review Statistics\n",
        f"- **Documents Reviewed:** {summary['documents_reviewed']}",
        f"- **Evidence Snippets:** {summary['total_evidence_snippets']}",
        f"- **Items for Human Review:** {summary['items_for_human_review']}\n"
    ])

    # Next steps
    if summary['items_for_human_review'] > 0:
        next_steps_list = [
            f"⚠️  {summary['items_for_human_review']} items need human review",
            f"Open `{md_path}` to review detailed findings",
            "Address flagged items before making final approval decision"
        ]
    else:
        next_steps_list = [
            "✅ No items flagged for review",
            f"Open `{md_path}` to review the complete findings",
            "Make final approval decision"
        ]

    next_steps = format_next_steps_section(next_steps_list, "Next Steps")

    # Update workflow progress
    workflow["report_generation"] = "completed"
    state_manager = StateManager(session_id)
    state_manager.update_json("session.json", {"workflow_progress": workflow})

    message = header + "\n".join(content) + next_steps + f"\n\n💡 **Tip:** Use `cat {md_path}` to view the Markdown report in your terminal"
    return text_content(message)


__all__ = ["report_generation_prompt"]
