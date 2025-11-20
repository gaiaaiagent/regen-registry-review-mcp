"""Report generation tools."""

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from ..models.report import (
    ReportMetadata,
    RequirementFinding,
    ValidationFinding,
    ReportSummary,
    ReviewReport,
)
from ..utils.state import StateManager, get_session_or_raise


async def generate_review_report(
    session_id: str,
    format: str = "markdown",
    include_evidence_snippets: bool = True,
    include_validation_details: bool = True
) -> dict[str, Any]:
    """
    Generate complete review report.

    Args:
        session_id: Session identifier
        format: Output format ("markdown" or "json")
        include_evidence_snippets: Include full evidence snippets
        include_validation_details: Include validation details

    Returns:
        Report generation result with path to saved report
    """
    state_manager = StateManager(session_id)

    # Load session data
    session_data = state_manager.read_json("session.json")
    project_metadata = session_data.get("project_metadata", {})

    # Load evidence data if available
    evidence_path = state_manager.session_dir / "evidence.json"
    if evidence_path.exists():
        evidence_data = state_manager.read_json("evidence.json")
    else:
        evidence_data = {
            "requirements_total": 0,
            "requirements_covered": 0,
            "requirements_partial": 0,
            "requirements_missing": 0,
            "overall_coverage": 0.0,
            "evidence": []
        }

    # Load validation data if available
    validation_path = state_manager.session_dir / "validation.json"
    if validation_path.exists():
        validation_data = state_manager.read_json("validation.json")
    else:
        validation_data = {
            "summary": {
                "total_validations": 0,
                "validations_passed": 0,
                "validations_failed": 0,
                "validations_warning": 0
            },
            "date_alignments": [],
            "land_tenure": [],
            "project_ids": []
        }

    # Load documents data if available
    documents_path = state_manager.session_dir / "documents.json"
    if documents_path.exists():
        documents_data = state_manager.read_json("documents.json")
        documents_count = documents_data.get("documents_found", 0)
    else:
        documents_count = 0

    # Build report metadata
    metadata = ReportMetadata(
        session_id=session_id,
        project_name=project_metadata.get("project_name", "Unknown"),
        project_id=project_metadata.get("project_id"),
        methodology=project_metadata.get("methodology", "Unknown"),
        generated_at=datetime.now(UTC),
        report_format=format
    )

    # Build requirement findings
    requirements = []
    total_snippets = 0
    items_for_review = []

    for req in evidence_data.get("evidence", []):
        snippets_found = len(req.get("evidence_snippets", []))
        total_snippets += snippets_found

        # Extract page citations
        page_citations = []
        for snippet in req.get("evidence_snippets", []):
            doc_name = snippet.get("document_name", "Unknown")
            page = snippet.get("page")
            if page:
                page_citations.append(f"{doc_name}, Page {page}")

        # Build evidence summary
        docs_count = len(req.get("mapped_documents", []))
        confidence = req.get("confidence", 0.0)
        status = req.get("status", "missing")

        if confidence >= 0.8:
            evidence_summary = f"Strong evidence found across {docs_count} document(s)"
        elif confidence >= 0.5:
            evidence_summary = f"Partial evidence found in {docs_count} document(s)"
        else:
            evidence_summary = f"Limited or no evidence found"

        # Flag for human review if needed
        human_review_required = status in ["partial", "missing", "flagged"] or confidence < 0.8

        if human_review_required:
            items_for_review.append(
                f"{req['requirement_id']}: {req['requirement_text'][:80]}... "
                f"(Status: {status}, Confidence: {confidence:.2f})"
            )

        finding = RequirementFinding(
            requirement_id=req["requirement_id"],
            requirement_text=req["requirement_text"],
            category=req.get("category", "Unknown"),
            status=status,
            confidence=confidence,
            documents_referenced=docs_count,
            snippets_found=snippets_found,
            evidence_summary=evidence_summary,
            page_citations=page_citations[:5],  # Limit to first 5
            human_review_required=human_review_required,
            notes=req.get("notes")
        )
        requirements.append(finding)

    # Build validation findings
    validations = []

    for date_val in validation_data.get("date_alignments", []):
        validations.append(ValidationFinding(
            validation_type="date_alignment",
            status=date_val["status"],
            message=date_val["message"],
            flagged_for_review=date_val.get("flagged_for_review", False)
        ))

    for tenure_val in validation_data.get("land_tenure", []):
        validations.append(ValidationFinding(
            validation_type="land_tenure",
            status=tenure_val["status"],
            message=tenure_val["message"],
            details=", ".join(tenure_val.get("discrepancies", [])),
            flagged_for_review=tenure_val.get("flagged_for_review", False)
        ))

    for pid_val in validation_data.get("project_ids", []):
        validations.append(ValidationFinding(
            validation_type="project_id",
            status=pid_val["status"],
            message=pid_val["message"],
            flagged_for_review=pid_val.get("flagged_for_review", False)
        ))

    # Build summary
    val_summary = validation_data.get("summary", {})
    summary = ReportSummary(
        requirements_total=evidence_data.get("requirements_total", 0),
        requirements_covered=evidence_data.get("requirements_covered", 0),
        requirements_partial=evidence_data.get("requirements_partial", 0),
        requirements_missing=evidence_data.get("requirements_missing", 0),
        requirements_flagged=evidence_data.get("requirements_flagged", 0),
        overall_coverage=evidence_data.get("overall_coverage", 0.0),
        validations_total=val_summary.get("total_validations", 0),
        validations_passed=val_summary.get("validations_passed", 0),
        validations_failed=val_summary.get("validations_failed", 0),
        validations_warning=val_summary.get("validations_warning", 0),
        documents_reviewed=documents_count,
        total_evidence_snippets=total_snippets,
        items_for_human_review=len(items_for_review)
    )

    # Build complete report
    report = ReviewReport(
        metadata=metadata,
        summary=summary,
        requirements=requirements,
        validations=validations,
        items_for_review=items_for_review,
        next_steps=[
            "Review items flagged for human review",
            "Verify partial requirements have sufficient evidence",
            "Address any validation warnings or failures",
            "Make final approval decision"
        ]
    )

    # Generate output based on format
    if format == "markdown":
        report_content = format_markdown_report(report)
        report_path = state_manager.session_dir / "report.md"
        report_path.write_text(report_content, encoding="utf-8")
    elif format == "json":
        report_path = state_manager.session_dir / "report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)
    else:
        raise ValueError(f"Unsupported format: {format}")

    report.report_path = str(report_path)

    return {
        "session_id": session_id,
        "format": format,
        "report_path": str(report_path),
        "generated_at": metadata.generated_at.isoformat(),
        "summary": summary.model_dump()
    }


def format_markdown_report(report: ReviewReport) -> str:
    """
    Format review report as Markdown.

    Args:
        report: ReviewReport object

    Returns:
        Markdown-formatted report string
    """
    lines = []

    # Header
    lines.append("# Registry Agent Review")
    lines.append("")

    # Metadata
    lines.append("## Project Metadata")
    lines.append(f"- **Project Name:** {report.metadata.project_name}")
    if report.metadata.project_id:
        lines.append(f"- **Project ID:** {report.metadata.project_id}")
    lines.append(f"- **Methodology:** {report.metadata.methodology}")
    lines.append(f"- **Review Date:** {report.metadata.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("### Requirements Coverage")
    lines.append(f"- **Total Requirements:** {report.summary.requirements_total}")
    lines.append(f"- ✅ **Covered:** {report.summary.requirements_covered} ({report.summary.requirements_covered/report.summary.requirements_total*100:.1f}%)" if report.summary.requirements_total > 0 else "- ✅ **Covered:** 0 (0.0%)")
    lines.append(f"- ⚠️  **Partial:** {report.summary.requirements_partial} ({report.summary.requirements_partial/report.summary.requirements_total*100:.1f}%)" if report.summary.requirements_total > 0 else "- ⚠️  **Partial:** 0 (0.0%)")
    lines.append(f"- ❌ **Missing:** {report.summary.requirements_missing} ({report.summary.requirements_missing/report.summary.requirements_total*100:.1f}%)" if report.summary.requirements_total > 0 else "- ❌ **Missing:** 0 (0.0%)")
    lines.append(f"- **Overall Coverage:** {report.summary.overall_coverage*100:.1f}%")
    lines.append("")

    if report.summary.validations_total > 0:
        lines.append("### Cross-Document Validation")
        lines.append(f"- **Total Checks:** {report.summary.validations_total}")
        lines.append(f"- ✅ **Passed:** {report.summary.validations_passed}")
        lines.append(f"- ⚠️  **Warnings:** {report.summary.validations_warning}")
        lines.append(f"- ❌ **Failed:** {report.summary.validations_failed}")
        lines.append("")

    lines.append(f"### Review Statistics")
    lines.append(f"- **Documents Reviewed:** {report.summary.documents_reviewed}")
    lines.append(f"- **Evidence Snippets Extracted:** {report.summary.total_evidence_snippets}")
    lines.append(f"- **Items Requiring Human Review:** {report.summary.items_for_human_review}")
    lines.append("")

    # Requirements by status
    covered = [r for r in report.requirements if r.status == "covered"]
    partial = [r for r in report.requirements if r.status == "partial"]
    missing = [r for r in report.requirements if r.status == "missing"]
    flagged = [r for r in report.requirements if r.status == "flagged"]

    if covered:
        lines.append("## ✅ Covered Requirements")
        lines.append("")
        for req in covered:
            lines.extend(format_requirement_markdown(req))
            lines.append("")

    if partial:
        lines.append("## ⚠️  Partially Covered Requirements")
        lines.append("")
        for req in partial:
            lines.extend(format_requirement_markdown(req))
            lines.append("")

    if missing:
        lines.append("## ❌ Missing Requirements")
        lines.append("")
        for req in missing:
            lines.extend(format_requirement_markdown(req))
            lines.append("")

    if flagged:
        lines.append("## 🚩 Flagged Requirements")
        lines.append("")
        for req in flagged:
            lines.extend(format_requirement_markdown(req))
            lines.append("")

    # Validation Results
    if report.validations:
        lines.append("## Cross-Document Validation Results")
        lines.append("")
        lines.extend(format_validation_summary_markdown({
            "date_alignments": [v for v in report.validations if v.validation_type == "date_alignment"],
            "land_tenure": [v for v in report.validations if v.validation_type == "land_tenure"],
            "project_ids": [v for v in report.validations if v.validation_type == "project_id"]
        }))
        lines.append("")

    # Items for Review
    if report.items_for_review:
        lines.append("## Items Requiring Human Review")
        lines.append("")
        for idx, item in enumerate(report.items_for_review, 1):
            lines.append(f"{idx}. {item}")
        lines.append("")

    # Next Steps
    lines.append("## Next Steps")
    lines.append("")
    for idx, step in enumerate(report.next_steps, 1):
        lines.append(f"{idx}. {step}")
    lines.append("")

    return "\n".join(lines)


def format_requirement_markdown(req: dict | RequirementFinding) -> list[str]:
    """
    Format a single requirement finding as Markdown.

    Args:
        req: Requirement finding (dict or RequirementFinding object)

    Returns:
        List of markdown lines
    """
    lines = []

    # Handle both dict and RequirementFinding
    if isinstance(req, dict):
        req_id = req["requirement_id"]
        req_text = req["requirement_text"]
        status = req["status"]
        confidence = req["confidence"]
        docs_ref = req.get("documents_referenced", len(req.get("mapped_documents", [])))
        snippets = req.get("snippets_found", len(req.get("evidence_snippets", [])))
        evidence_summary = req.get("evidence_summary", "")
        page_citations = req.get("page_citations", [])
    else:
        req_id = req.requirement_id
        req_text = req.requirement_text
        status = req.status
        confidence = req.confidence
        docs_ref = req.documents_referenced
        snippets = req.snippets_found
        evidence_summary = req.evidence_summary
        page_citations = req.page_citations

    # Status icon
    status_icon = {
        "covered": "✅",
        "partial": "⚠️",
        "missing": "❌",
        "flagged": "🚩"
    }.get(status, "❓")

    lines.append(f"### {status_icon} {req_id}: {req_text[:80]}{'...' if len(req_text) > 80 else ''}")
    lines.append(f"**Status:** {status.title()}")
    lines.append(f"**Confidence:** {confidence:.2f} ({confidence*100:.0f}%)")
    lines.append(f"**Evidence:** {snippets} snippet(s) from {docs_ref} document(s)")

    if evidence_summary:
        lines.append(f"**Summary:** {evidence_summary}")

    if page_citations:
        lines.append(f"**Citations:** {', '.join(page_citations[:3])}")
        if len(page_citations) > 3:
            lines.append(f"  (and {len(page_citations) - 3} more)")

    return lines


def format_validation_summary_markdown(validations: dict) -> list[str]:
    """
    Format validation summary as Markdown.

    Args:
        validations: Dictionary of validation results by type

    Returns:
        List of markdown lines
    """
    lines = []

    for val_type, val_list in validations.items():
        if not val_list:
            continue

        type_name = val_type.replace("_", " ").title()
        lines.append(f"### {type_name}")
        lines.append("")

        for val in val_list:
            # Handle both dict and ValidationFinding
            if isinstance(val, dict):
                status = val["status"]
                message = val["message"]
                flagged = val.get("flagged_for_review", False)
            else:
                status = val.status
                message = val.message
                flagged = val.flagged_for_review

            status_icon = {
                "pass": "✅",
                "warning": "⚠️",
                "fail": "❌"
            }.get(status, "❓")

            flag_icon = " 🚩" if flagged else ""
            lines.append(f"{status_icon}{flag_icon} {message}")

        lines.append("")

    return lines


async def export_review(
    session_id: str,
    output_format: str,
    output_path: str | None = None
) -> dict[str, Any]:
    """
    Export review report to specified format.

    Args:
        session_id: Session identifier
        output_format: Output format ("markdown", "json", "pdf")
        output_path: Optional custom output path

    Returns:
        Export result with path to exported file
    """
    if output_format == "pdf":
        raise NotImplementedError("PDF export not yet implemented")

    # Generate report
    result = await generate_review_report(session_id, format=output_format)

    # Copy to custom output path if specified
    if output_path:
        source_path = Path(result["report_path"])
        dest_path = Path(output_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(source_path.read_bytes())
        result["export_path"] = str(dest_path)

    return result


__all__ = [
    "generate_review_report",
    "format_markdown_report",
    "format_requirement_markdown",
    "format_validation_summary_markdown",
    "export_review",
]
