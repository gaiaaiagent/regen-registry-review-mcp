"""Report generation data models."""

from datetime import datetime
from pydantic import Field
from .base import BaseModel, ConfidenceScore


class ReportMetadata(BaseModel):
    """Metadata for a review report."""

    session_id: str
    project_name: str
    project_id: str | None = None
    methodology: str
    methodology_version: str | None = None
    generated_at: datetime
    generated_by: str = "Registry Review MCP"
    report_format: str  # "markdown", "json", "pdf"


class RequirementFinding(BaseModel):
    """Detailed finding for a single requirement in the report."""

    requirement_id: str
    requirement_text: str
    category: str
    status: str  # "covered", "partial", "missing", "flagged"
    confidence: ConfidenceScore
    documents_referenced: int
    snippets_found: int
    evidence_summary: str  # Brief summary of evidence found
    page_citations: list[str] = Field(default_factory=list)  # ["DOC-001, Page 8", ...]
    human_review_required: bool = False
    notes: str | None = None


class ValidationFinding(BaseModel):
    """Validation result for inclusion in report."""

    validation_type: str  # "date_alignment", "land_tenure", "project_id"
    status: str  # "pass", "fail", "warning"
    message: str
    details: str | None = None
    flagged_for_review: bool = False


class ReportSummary(BaseModel):
    """Summary statistics for the report."""

    requirements_total: int
    requirements_covered: int
    requirements_partial: int
    requirements_missing: int
    requirements_flagged: int
    overall_coverage: float = Field(..., ge=0.0, le=1.0)

    validations_total: int = 0
    validations_passed: int = 0
    validations_failed: int = 0
    validations_warning: int = 0

    documents_reviewed: int = 0
    total_evidence_snippets: int = 0
    items_for_human_review: int = 0


class ReviewReport(BaseModel):
    """Complete review report structure."""

    metadata: ReportMetadata
    summary: ReportSummary
    requirements: list[RequirementFinding]
    validations: list[ValidationFinding]
    items_for_review: list[str] = Field(default_factory=list)  # Human-readable items
    next_steps: list[str] = Field(default_factory=list)  # Recommended actions
    report_path: str | None = None  # Path to saved report file


__all__ = [
    "ReportMetadata",
    "RequirementFinding",
    "ValidationFinding",
    "ReportSummary",
    "ReviewReport",
]
