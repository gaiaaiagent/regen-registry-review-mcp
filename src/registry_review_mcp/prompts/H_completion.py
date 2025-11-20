"""Completion workflow - Stage 8 of registry review."""

from mcp.types import TextContent

from ..utils.state import StateManager
from .helpers import (
    text_content,
    format_workflow_header,
    format_next_steps_section,
)


async def complete_prompt(session_id: str | None = None) -> list[TextContent]:
    """Complete the registry review workflow and finalize the session (Stage 7).

    This prompt marks the review as complete, provides a final summary,
    and guides the user on next steps (export, archive, share report).

    Args:
        session_id: Session ID (optional - will auto-select most recent)

    Returns:
        Completion summary with final report location and next steps
    """
    # Auto-select session if not provided
    auto_selected = False
    if not session_id:
        state_manager = StateManager(None)
        sessions = state_manager.list_sessions()

        if not sessions:
            return text_content("""# Registry Review Workflow - Stage 7: Complete

No active sessions found.

## Next Step

Create a session first:

`/initialize Your Project Name, /path/to/documents`

Then proceed through the workflow stages.""")

        session_id = sessions[0]["session_id"]
        auto_selected = True

    # Load session
    manager = StateManager(session_id)

    if not manager.exists("session.json"):
        sessions_list = "\n".join(f"- `{s['session_id']}`: {s['project_name']}" for s in StateManager(None).list_sessions())
        return text_content(f"""# ❌ Error: Session Not Found

Session `{session_id}` does not exist.

## Available Sessions

{sessions_list}

## Next Step

Use an existing session ID or create a new one:

`/initialize Your Project Name, /path/to/documents`""")

    session = manager.read_json("session.json")
    project_name = session.get("project_name", "Unknown Project")
    project_metadata = session.get("project_metadata", {})

    # Check if report has been generated
    if not manager.exists("report.md") and not manager.exists("report.json"):
        header = format_workflow_header("Complete Review", session_id, project_name, auto_selected)
        message = header + """## ⚠️ Report Not Generated

You need to generate the report before completing the review.

## Next Step

Run Stage 5 first:

`/report-generation`

This will create Markdown and JSON reports with all findings."""
        return text_content(message)

    # Load statistics
    statistics = session.get("statistics", {})
    workflow_progress = session.get("workflow_progress", {})

    # Check if validation was run
    validation_summary = None
    has_flagged_items = False
    if manager.exists("validation.json"):
        validation_data = manager.read_json("validation.json")
        validation_summary = validation_data.get("summary", {})

        # Check for flagged items
        date_flags = sum(1 for v in validation_data.get("date_alignments", []) if v.get("flagged_for_review"))
        tenure_flags = sum(1 for v in validation_data.get("land_tenure", []) if v.get("flagged_for_review"))
        id_flags = sum(1 for v in validation_data.get("project_ids", []) if v.get("flagged_for_review"))
        contra_flags = sum(1 for v in validation_data.get("contradictions", []) if v.get("flagged_for_review"))
        total_flagged = date_flags + tenure_flags + id_flags + contra_flags
        has_flagged_items = total_flagged > 0

    # Get report paths
    session_dir = manager.session_dir
    report_md_path = session_dir / "report.md"
    report_json_path = session_dir / "report.json"

    # Mark session as completed
    session["status"] = "completed"
    session["workflow_progress"]["complete"] = "completed"
    manager.write_json("session.json", session)

    # Extract statistics
    requirements_total = statistics.get("requirements_total", 0)
    requirements_covered = statistics.get("requirements_covered", 0)
    requirements_partial = statistics.get("requirements_partial", 0)
    requirements_missing = statistics.get("requirements_missing", 0)
    documents_found = statistics.get("documents_found", 0)
    workflow_stages_completed = sum(1 for status in workflow_progress.values() if status == "completed")

    coverage_pct = (requirements_covered / requirements_total * 100) if requirements_total > 0 else 0

    # Determine overall assessment
    if coverage_pct >= 90 and requirements_missing == 0 and not has_flagged_items:
        assessment = "✅ **READY FOR APPROVAL**"
        assessment_detail = "All requirements are covered with strong evidence and no validation issues."
    elif coverage_pct >= 80 and requirements_missing <= 2:
        assessment = "⚠️ **CONDITIONAL APPROVAL RECOMMENDED**"
        assessment_detail = "Most requirements are covered, but some minor gaps or flags require clarification."
    else:
        assessment = "❌ **REQUIRES MAJOR REVISIONS**"
        assessment_detail = "Significant gaps in evidence or validation issues must be addressed."

    # Build header
    header = format_workflow_header("Complete Review", session_id, project_name, auto_selected)

    # Build content sections
    content = [
        f"**Status:** Complete",
        f"**Created:** {session.get('created_at', 'Unknown')}",
        f"**Completed:** {session.get('updated_at', 'Unknown')}\n",
        f"## Assessment\n",
        assessment,
        f"{assessment_detail}\n",
        f"## Review Summary\n",
        f"### Workflow Progress\n",
        f"Completed {workflow_stages_completed}/7 stages of the review workflow.\n",
        f"### Evidence Coverage\n",
        f"- **Total Requirements:** {requirements_total}",
        f"- **Covered:** {requirements_covered} ({coverage_pct:.1f}%)",
        f"- **Partial:** {requirements_partial}",
        f"- **Missing:** {requirements_missing}",
        f"- **Documents Processed:** {documents_found}\n"
    ]

    # Add validation section if available
    if validation_summary:
        total_validations = validation_summary.get("total_validations", 0)
        validations_passed = validation_summary.get("validations_passed", 0)
        validations_failed = validation_summary.get("validations_failed", 0)
        validations_warning = validation_summary.get("validations_warning", 0)
        pass_rate = (validations_passed / total_validations * 100) if total_validations > 0 else 0

        content.extend([
            "### Cross-Validation Results\n",
            f"- **Total Validations:** {total_validations}",
            f"- **Passed:** {validations_passed} ({pass_rate:.0f}%)",
            f"- **Failed:** {validations_failed}",
            f"- **Warnings:** {validations_warning}",
            f"- **Items Flagged for Review:** {total_flagged}\n"
        ])
    else:
        content.append("### Cross-Validation Results\n*Note: Cross-validation was not run for this review.*\n")

    # Reports section
    content.extend([
        "## Generated Reports\n",
        f"- **Markdown Report:** `{report_md_path}`",
        f"- **JSON Report:** `{report_json_path}`\n",
        "Reports include complete evidence citations, validation results, coverage analysis, and recommendations.\n",
        "## Project Metadata\n",
        f"- **Project Name:** {project_name}",
        f"- **Project ID:** {project_metadata.get('project_id', 'Not specified')}",
        f"- **Methodology:** {project_metadata.get('methodology', 'Unknown')}",
        f"- **Proponent:** {project_metadata.get('proponent', 'Not specified')}",
        f"- **Crediting Period:** {project_metadata.get('crediting_period', 'Not specified')}"
    ])

    # Next steps
    next_steps_list = [
        f"Review the reports: `cat {report_md_path}`",
        f"{'Address ' + str(total_flagged) + ' flagged items (use `/human-review`)' if has_flagged_items else 'No items flagged'}",
        "Share reports with project proponent or submit to registry",
        f"Archive session when done: `delete_session {session_id}` (Warning: permanent deletion)"
    ]

    next_steps = format_next_steps_section(next_steps_list, "Next Steps")

    message = header + "\n".join(content) + next_steps + "\n\n**Thank you for using Regen Registry Review MCP!**\n\nThis completes the automated review workflow."

    return text_content(message)
