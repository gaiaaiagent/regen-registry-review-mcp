"""Human review workflow - Stage 7 of registry review."""

from mcp.types import TextContent

from ..models.validation import ValidationResult
from ..utils.state import StateManager
from .helpers import (
    text_content,
    format_workflow_header,
    format_next_steps_section,
)


async def human_review_prompt(session_id: str | None = None) -> list[TextContent]:
    """Review flagged validation items requiring human judgment (Stage 5).

    This prompt presents items that have been flagged for human review during
    cross-validation. It provides context, evidence, and guides the reviewer
    through making decisions on each flagged item.

    Args:
        session_id: Session ID (optional - will auto-select most recent)

    Returns:
        List of flagged items with context for human review
    """
    # Auto-select session if not provided
    auto_selected = False
    if not session_id:
        state_manager = StateManager(None)
        sessions = state_manager.list_sessions()

        if not sessions:
            return text_content("""# Registry Review Workflow - Stage 5: Human Review

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

    # Check if cross-validation has been run
    if not manager.exists("validation.json"):
        header = format_workflow_header("Human Review", session_id, project_name, auto_selected)
        message = header + """## ⚠️ Cross-Validation Not Run

You need to run cross-validation before human review.

## Next Step

Run Stage 4 first:

`/cross-validation`

This will validate dates, land tenure, and project IDs across documents."""
        return text_content(message)

    # Load validation results
    validation_data = manager.read_json("validation.json")
    validation = ValidationResult(**validation_data)

    # Collect all flagged items
    flagged_items = []

    # Date alignment flags
    for val in validation.date_alignments:
        if val.flagged_for_review:
            flagged_items.append({
                "type": "Date Alignment",
                "status": val.status,
                "message": val.message,
                "details": f"""**Date 1:** {val.date1.field_name} = {val.date1.value.strftime('%Y-%m-%d')}
  - Source: {val.date1.source}
  - Confidence: {val.date1.confidence:.0%}

**Date 2:** {val.date2.field_name} = {val.date2.value.strftime('%Y-%m-%d')}
  - Source: {val.date2.source}
  - Confidence: {val.date2.confidence:.0%}

**Time Difference:** {val.delta_days} days (max allowed: {val.max_allowed_days} days)"""
            })

    # Land tenure flags
    for val in validation.land_tenure:
        if val.flagged_for_review:
            fields_text = "\n".join(
                f"  - **{field.owner_name}** ({field.tenure_type or 'unknown tenure'})\n"
                f"    - Area: {field.area_hectares:.2f} ha\n"
                f"    - Source: {field.source}\n"
                f"    - Confidence: {field.confidence:.0%}"
                for field in val.fields
            )

            discrepancies_text = (
                "\n\n**Discrepancies:**\n"
                + "\n".join(f"  - {d}" for d in val.discrepancies)
                if val.discrepancies
                else ""
            )

            flagged_items.append({
                "type": "Land Tenure",
                "status": val.status,
                "message": val.message,
                "details": f"""**Fields Found:**
{fields_text}

**Name Similarity:** {val.owner_name_similarity:.0%}
**Area Consistent:** {'✅ Yes' if val.area_consistent else '❌ No'}
**Tenure Type Consistent:** {'✅ Yes' if val.tenure_type_consistent else '❌ No'}{discrepancies_text}"""
            })

    # Project ID flags
    for val in validation.project_ids:
        if val.flagged_for_review:
            occurrences_text = "\n".join(
                f"  - {occ.project_id} in {occ.document_name}"
                + (f" (Page {occ.page})" if occ.page else "")
                for occ in val.occurrences[:10]
            )

            if len(val.occurrences) > 10:
                occurrences_text += f"\n  - ... and {len(val.occurrences) - 10} more"

            flagged_items.append({
                "type": "Project ID",
                "status": val.status,
                "message": val.message,
                "details": f"""**Expected Pattern:** `{val.expected_pattern}`
**Found IDs:** {', '.join(val.found_ids) if val.found_ids else 'None'}
**Primary ID:** {val.primary_id or 'Not identified'}
**Total Occurrences:** {val.total_occurrences} across {val.documents_with_id}/{val.total_documents} documents

**Sample Occurrences:**
{occurrences_text}"""
            })

    # Contradiction flags
    for val in validation.contradictions:
        if val.flagged_for_review:
            flagged_items.append({
                "type": "Contradiction",
                "status": "warning",
                "message": val.message,
                "details": f"""**Field:** {val.field_name}
**Severity:** {val.severity.upper()}

**Value 1:** {val.value1}
  - Source: {val.source1}

**Value 2:** {val.value2}
  - Source: {val.source2}"""
            })

    # Generate human review report
    if not flagged_items:
        header = format_workflow_header("Human Review", session_id, project_name, auto_selected)
        content = f"""## ✅ No Items Flagged for Review

**Validation Summary:**

All validation checks passed without requiring human review!

- **Total Validations:** {validation.summary.total_validations}
- **Passed:** {validation.summary.validations_passed} ({validation.summary.pass_rate:.0%})
- **Failed:** {validation.summary.validations_failed}
- **Warnings:** {validation.summary.validations_warning}
- **Items Flagged:** 0"""

        next_steps = format_next_steps_section([
            "All validation checks have passed",
            "Generate the final review report: `/report-generation`",
            "This will create a comprehensive report of all findings, evidence, and validations"
        ], "Next Step: Generate Report")

        message = header + content + next_steps
    else:
        # Format flagged items
        items_text = ""
        for i, item in enumerate(flagged_items, 1):
            status_icon = {"pass": "✅", "warning": "⚠️", "fail": "❌"}.get(
                item["status"], "❓"
            )

            items_text += f"""
---

### {i}. {item['type']} - {status_icon} {item['status'].upper()}

**Issue:** {item['message']}

{item['details']}

**Action Required:**
- Review the evidence above
- Verify the information in the source documents
- Make a determination:
  - ✅ **Accept as-is** - Information is correct despite the flag
  - ⚠️ **Request clarification** - Need more information from project proponent
  - ❌ **Reject/Requires correction** - Information is incorrect or insufficient

"""

        header = format_workflow_header("Human Review", session_id, project_name, auto_selected)

        content = f"""## 🔍 Human Review Required

**{len(flagged_items)} item(s)** have been flagged for human review during cross-validation.

These items require your expert judgment to determine whether they represent actual issues or are acceptable within the project context.

### Validation Summary

- **Total Validations:** {validation.summary.total_validations}
- **Passed:** {validation.summary.validations_passed}
- **Failed:** {validation.summary.validations_failed}
- **Warnings:** {validation.summary.validations_warning}
- **Flagged for Review:** {len(flagged_items)}

### Items Requiring Review

{items_text}"""

        next_steps = format_next_steps_section([
            "Document your decisions - Note any actions needed (clarifications, corrections)",
            "Update session notes if needed (use `update_session` tool)",
            "Generate the final report: `/report-generation`"
        ], "Next Steps")

        message = header + content + next_steps + """\n
**Note:** This human review stage ensures expert judgment on ambiguous or inconsistent information before making a final registration decision."""

    # Mark human_review stage as completed
    session = manager.read_json("session.json")
    session["workflow_progress"]["human_review"] = "completed"
    manager.write_json("session.json", session)

    return text_content(message)
