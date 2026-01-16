"""Coordinator for three-layer validation architecture.

Orchestrates:
- Layer 1: Structural checks (always runs)
- Layer 2: Cross-document checks (when 2+ documents)
- Layer 3: LLM synthesis (when configured)
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

from .structural import (
    run_structural_checks,
    extract_all_fields_from_evidence,
    StructuralValidationResult,
)
from .cross_document import (
    run_cross_document_checks,
    CrossDocumentValidationResult,
)
from .llm_synthesis import (
    run_llm_synthesis,
    LLMSynthesisResult,
)
from ..tools.validation_tools import extract_structured_fields_from_evidence

logger = logging.getLogger(__name__)


@dataclass
class ValidationSummary:
    """Summary statistics across all validation layers."""
    total_checks: int = 0
    passed: int = 0
    warnings: int = 0
    failed: int = 0
    flagged_for_review: int = 0
    pass_rate: float = 0.0

    # Layer breakdown
    structural_checks: int = 0
    cross_document_checks: int = 0
    llm_synthesis_available: bool = False


@dataclass
class ValidationResult:
    """Complete validation results from all three layers."""
    session_id: str
    validated_at: datetime

    # Layer results
    structural: StructuralValidationResult
    cross_document: CrossDocumentValidationResult
    llm_synthesis: LLMSynthesisResult

    # Summary
    summary: ValidationSummary

    # Fact sheet data for UI (extracted from evidence)
    fact_sheets: dict[str, Any] = field(default_factory=dict)

    # Backward compatibility with old validation.json format
    date_alignments: list[dict] = field(default_factory=list)
    land_tenure: list[dict] = field(default_factory=list)
    project_ids: list[dict] = field(default_factory=list)
    contradictions: list[dict] = field(default_factory=list)
    sanity_checks: list[dict] = field(default_factory=list)
    all_passed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "validated_at": self.validated_at.isoformat(),

            # New three-layer structure
            "structural": {
                "checks": [asdict(c) for c in self.structural.checks],
                "total_checks": self.structural.total_checks,
                "passed": self.structural.passed,
                "warnings": self.structural.warnings,
                "failed": self.structural.failed,
            },
            "cross_document": {
                "checks": [asdict(c) for c in self.cross_document.checks],
                "documents_analyzed": self.cross_document.documents_analyzed,
                "sufficient_data": self.cross_document.sufficient_data,
                "total_checks": self.cross_document.total_checks,
                "passed": self.cross_document.passed,
                "warnings": self.cross_document.warnings,
                "failed": self.cross_document.failed,
            },
            "llm_synthesis": {
                "available": self.llm_synthesis.available,
                "coherence_score": self.llm_synthesis.coherence_score,
                "compliance_status": self.llm_synthesis.compliance_status,
                "flags_for_review": self.llm_synthesis.flags_for_review,
                "reasoning": self.llm_synthesis.reasoning,
                "error": self.llm_synthesis.error,
            },

            # Summary
            "summary": asdict(self.summary),

            # Fact sheet data for UI
            "fact_sheets": self.fact_sheets,

            # Backward compatibility
            "date_alignments": self.date_alignments,
            "land_tenure": self.land_tenure,
            "project_ids": self.project_ids,
            "contradictions": self.contradictions,
            "sanity_checks": self.sanity_checks,
            "all_passed": self.all_passed,
        }


def _build_summary(
    structural: StructuralValidationResult,
    cross_doc: CrossDocumentValidationResult,
    llm_synthesis: LLMSynthesisResult
) -> ValidationSummary:
    """Build summary statistics from all layers."""

    total_checks = structural.total_checks + cross_doc.total_checks
    passed = structural.passed + cross_doc.passed
    warnings = structural.warnings + cross_doc.warnings
    failed = structural.failed + cross_doc.failed

    flagged = (
        structural.flagged_count +
        sum(1 for c in cross_doc.checks if c.flagged_for_review) +
        llm_synthesis.flagged_count
    )

    pass_rate = passed / total_checks if total_checks > 0 else 0.0

    return ValidationSummary(
        total_checks=total_checks,
        passed=passed,
        warnings=warnings,
        failed=failed,
        flagged_for_review=flagged,
        pass_rate=pass_rate,
        structural_checks=structural.total_checks,
        cross_document_checks=cross_doc.total_checks,
        llm_synthesis_available=llm_synthesis.available,
    )


def _build_fact_sheets(
    evidence_data: dict,
    structural: StructuralValidationResult,
    cross_doc: CrossDocumentValidationResult
) -> dict[str, Any]:
    """Build fact sheet data for the UI from extracted evidence.

    Returns formatted data for the fact sheet tables:
    - date_alignment: Documents with their start/end dates
    - land_tenure: Documents with ownership info
    - project_id: Documents with project IDs
    - quantification: Documents with GHG metrics
    """
    # Extract structured fields from evidence
    extracted = extract_structured_fields_from_evidence(evidence_data)

    # Compute overall status for each category based on checks
    def compute_status(check_type: str) -> str:
        relevant_checks = [c for c in cross_doc.checks if c.check_type == check_type]
        if not relevant_checks:
            # Check structural checks for this field type
            structural_checks = [c for c in structural.checks if check_type in c.field_name.lower()]
            if not structural_checks:
                return "pass"
            if any(c.status == "fail" for c in structural_checks):
                return "error"
            if any(c.status == "warning" for c in structural_checks):
                return "warning"
            return "pass"
        if any(c.status == "fail" for c in relevant_checks):
            return "error"
        if any(c.status == "warning" for c in relevant_checks):
            return "warning"
        return "pass"

    def extract_issues(check_type: str) -> list[dict]:
        issues = []
        for c in cross_doc.checks:
            if c.check_type == check_type and c.status in ("warning", "fail"):
                issues.append({
                    "requirement_id": c.field_name,
                    "message": c.message,
                    "severity": "error" if c.status == "fail" else "warning",
                })
        for c in structural.checks:
            if check_type in c.field_name.lower() and c.status in ("warning", "fail"):
                issues.append({
                    "requirement_id": c.field_name,
                    "message": c.message,
                    "severity": "error" if c.status == "fail" else "warning",
                })
        return issues

    # Transform dates into date_alignment rows
    date_rows = []
    for d in extracted.get("dates", []):
        # Group dates by document for date alignment display
        date_rows.append({
            "document": d.get("document_name", "Unknown"),
            "document_id": d.get("document_id"),
            "page_number": d.get("page"),
            "document_type": d.get("date_type", "date").replace("_", " ").title(),
            "start_date": d.get("date_value") if "start" in d.get("date_type", "") else None,
            "end_date": d.get("date_value") if "end" in d.get("date_type", "") else None,
        })

    # Transform tenure into land_tenure rows
    tenure_rows = []
    for t in extracted.get("tenure", []):
        tenure_rows.append({
            "document": t.get("document_name", "Unknown"),
            "document_id": t.get("document_id"),
            "page_number": t.get("page"),
            "owner_name": t.get("owner_name"),
            "area_hectares": t.get("area_hectares"),
            "tenure_type": t.get("tenure_type"),
            "expiry_date": t.get("expiry_date"),
        })

    # Transform project_ids into project_id rows
    project_id_rows = []
    for p in extracted.get("project_ids", []):
        project_id_rows.append({
            "document": p.get("document_name", "Unknown"),
            "document_id": p.get("document_id"),
            "page_number": p.get("page"),
            "document_type": "Project Document",
            "project_id": p.get("project_id"),
        })

    # Build quantification rows from structured checks
    quantification_rows = []
    for c in structural.checks:
        if c.field_name in ("area_hectares", "crediting_period_years", "carbon_stock"):
            quantification_rows.append({
                "document": c.source or "Multiple",
                "metric": c.field_name.replace("_", " ").title(),
                "value": c.value if isinstance(c.value, (int, float)) else None,
                "unit": "ha" if "hectares" in c.field_name else "years" if "years" in c.field_name else "tCO2e",
            })

    return {
        "date_alignment": {
            "status": compute_status("date_alignment"),
            "rows": date_rows,
            "issues": extract_issues("date_alignment"),
        },
        "land_tenure": {
            "status": compute_status("name_consistency"),
            "rows": tenure_rows,
            "issues": extract_issues("name_consistency"),
        },
        "project_id": {
            "status": compute_status("id_consistency"),
            "rows": project_id_rows,
            "issues": extract_issues("id_consistency"),
        },
        "quantification": {
            "status": compute_status("range"),
            "rows": quantification_rows,
            "issues": extract_issues("range"),
        },
    }


def _build_backward_compat(
    structural: StructuralValidationResult,
    cross_doc: CrossDocumentValidationResult
) -> dict[str, list[dict]]:
    """Build backward-compatible structures for old API consumers."""

    # Convert structural checks to sanity_checks format
    sanity_checks = [
        {
            "validation_id": c.check_id,
            "validation_type": f"sanity_check_{c.check_type}",
            "field_name": c.field_name,
            "status": c.status,
            "message": c.message,
            "flagged_for_review": c.flagged_for_review,
        }
        for c in structural.checks
    ]

    # Convert cross-document date checks to date_alignments format
    date_alignments = [
        {
            "validation_id": c.check_id,
            "validation_type": "date_alignment",
            "status": c.status,
            "message": c.message,
            "flagged_for_review": c.flagged_for_review,
        }
        for c in cross_doc.checks
        if c.check_type == "date_alignment"
    ]

    # Convert cross-document name checks to land_tenure format
    land_tenure = [
        {
            "validation_id": c.check_id,
            "validation_type": "land_tenure",
            "status": c.status,
            "message": c.message,
            "owner_name_match": c.status == "pass",
            "owner_name_similarity": c.similarity or 1.0,
            "flagged_for_review": c.flagged_for_review,
        }
        for c in cross_doc.checks
        if c.check_type == "name_consistency" and "owner" in c.field_name
    ]

    # Convert cross-document ID checks to project_ids format
    project_ids = [
        {
            "validation_id": c.check_id,
            "validation_type": "project_id",
            "status": c.status,
            "message": c.message,
            "flagged_for_review": c.flagged_for_review,
        }
        for c in cross_doc.checks
        if c.check_type == "id_consistency"
    ]

    return {
        "sanity_checks": sanity_checks,
        "date_alignments": date_alignments,
        "land_tenure": land_tenure,
        "project_ids": project_ids,
        "contradictions": [],
    }


async def validate_session(session_id: str) -> ValidationResult:
    """Run all three validation layers for a session.

    Args:
        session_id: Session identifier

    Returns:
        ValidationResult with results from all layers
    """
    from ..utils.state import StateManager

    logger.info(f"Starting three-layer validation for session {session_id}")

    state_manager = StateManager(session_id)

    # Load evidence data
    evidence_path = state_manager.session_dir / "evidence.json"
    if not evidence_path.exists():
        logger.warning(f"No evidence.json found for session {session_id}")
        # Return empty result
        return ValidationResult(
            session_id=session_id,
            validated_at=datetime.now(timezone.utc),
            structural=StructuralValidationResult(),
            cross_document=CrossDocumentValidationResult(),
            llm_synthesis=LLMSynthesisResult(available=False, error="No evidence data"),
            summary=ValidationSummary(),
            all_passed=False,
        )

    evidence_data = state_manager.read_json("evidence.json")

    # Load session data for methodology name
    session_data = state_manager.read_json("session.json")
    methodology_name = session_data.get("methodology_name", "Soil Organic Carbon")

    # Extract all fields for LLM synthesis
    all_fields = extract_all_fields_from_evidence(evidence_data)
    logger.info(f"Extracted {len(all_fields)} structured fields for validation")

    # Layer 1: Structural checks (always runs)
    logger.info("Running Layer 1: Structural validation")
    structural_results = run_structural_checks(evidence_data)

    # Layer 2: Cross-document checks (runs if 2+ documents)
    logger.info("Running Layer 2: Cross-document validation")
    cross_doc_results = run_cross_document_checks(evidence_data)

    # Layer 3: LLM synthesis (runs if configured)
    logger.info("Running Layer 3: LLM synthesis")
    llm_results = await run_llm_synthesis(
        evidence_data=evidence_data,
        all_fields=all_fields,
        structural_results=structural_results,
        cross_doc_results=cross_doc_results,
        methodology_name=methodology_name,
    )

    # Build summary
    summary = _build_summary(structural_results, cross_doc_results, llm_results)

    # Build fact sheet data for UI
    fact_sheets = _build_fact_sheets(evidence_data, structural_results, cross_doc_results)

    # Build backward-compatible structures
    compat = _build_backward_compat(structural_results, cross_doc_results)

    # Determine all_passed (no failures, no flags requiring review)
    all_passed = (
        summary.failed == 0 and
        summary.flagged_for_review == 0
    )

    # Build result
    result = ValidationResult(
        session_id=session_id,
        validated_at=datetime.now(timezone.utc),
        structural=structural_results,
        cross_document=cross_doc_results,
        llm_synthesis=llm_results,
        summary=summary,
        fact_sheets=fact_sheets,
        sanity_checks=compat["sanity_checks"],
        date_alignments=compat["date_alignments"],
        land_tenure=compat["land_tenure"],
        project_ids=compat["project_ids"],
        contradictions=compat["contradictions"],
        all_passed=all_passed,
    )

    # Save validation results
    state_manager.write_json("validation.json", result.to_dict())

    # Update workflow progress to mark validation as completed
    state_manager.update_json("session.json", {
        "workflow_progress.cross_validation": "completed"
    })

    logger.info(
        f"Validation complete for {session_id}: "
        f"{summary.total_checks} checks, {summary.passed} passed, "
        f"{summary.warnings} warnings, {summary.failed} failed, "
        f"{summary.flagged_for_review} flagged for review"
    )

    return result
