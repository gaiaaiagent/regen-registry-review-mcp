"""Pydantic schemas for Registry Review MCP.

All data models with validation for session, document, requirement, and finding structures.
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Session Models
# ============================================================================


class ProjectMetadata(BaseModel):
    """Metadata about the project being reviewed."""

    project_name: str = Field(min_length=1, max_length=200)
    project_id: str | None = Field(None, pattern=r"^C\d{2}-\d+$")
    crediting_period: str | None = None
    submission_date: datetime | None = None
    methodology: str = "soil-carbon-v1.2.2"
    proponent: str | None = None
    documents_path: str

    @field_validator("documents_path")
    @classmethod
    def validate_path_exists(cls, value: str) -> str:
        """Validate that the documents path exists."""
        path = Path(value)
        if not path.exists():
            raise ValueError(f"Path does not exist: {value}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {value}")
        return str(path.absolute())


class WorkflowProgress(BaseModel):
    """Tracks progress through the 7-stage workflow."""

    initialize: Literal["pending", "in_progress", "completed"] = "pending"
    document_discovery: Literal["pending", "in_progress", "completed"] = "pending"
    evidence_extraction: Literal["pending", "in_progress", "completed"] = "pending"
    cross_validation: Literal["pending", "in_progress", "completed"] = "pending"
    report_generation: Literal["pending", "in_progress", "completed"] = "pending"
    human_review: Literal["pending", "in_progress", "completed"] = "pending"
    complete: Literal["pending", "in_progress", "completed"] = "pending"


class SessionStatistics(BaseModel):
    """Aggregated statistics for the review session."""

    documents_found: int = 0
    requirements_total: int = 0
    requirements_covered: int = 0
    requirements_partial: int = 0
    requirements_missing: int = 0
    validations_passed: int = 0
    validations_failed: int = 0


class Session(BaseModel):
    """Complete session state."""

    session_id: str
    created_at: datetime
    updated_at: datetime
    status: str
    project_metadata: ProjectMetadata
    workflow_progress: WorkflowProgress
    statistics: SessionStatistics


# ============================================================================
# Checklist Models
# ============================================================================


class Requirement(BaseModel):
    """A single requirement from the checklist."""

    requirement_id: str = Field(pattern=r"^REQ-\d{3}$")
    category: str
    requirement_text: str
    source: str  # "Program Guide, Section X.Y"
    accepted_evidence: str
    mandatory: bool = True
    validation_type: Literal[
        "document_presence",
        "cross_document",
        "date_alignment",
        "structured_field",
        "manual",
    ]


class Checklist(BaseModel):
    """Complete checklist for a methodology."""

    methodology_id: str
    methodology_name: str
    version: str
    protocol: str
    program_guide_version: str
    requirements: list[Requirement]


# ============================================================================
# Document Models
# ============================================================================


class DocumentMetadata(BaseModel):
    """Metadata extracted from a document."""

    page_count: int | None = None
    creation_date: datetime | None = None
    modification_date: datetime | None = None
    file_size_bytes: int
    has_tables: bool = False
    content_hash: str | None = None  # SHA256 hash for deduplication


class Document(BaseModel):
    """A discovered and classified document."""

    document_id: str
    filename: str
    filepath: str
    classification: str
    confidence: float = Field(ge=0.0, le=1.0)
    classification_method: str  # "filename", "content", "manual"
    metadata: DocumentMetadata
    indexed_at: datetime


# ============================================================================
# Evidence & Finding Models
# ============================================================================


class EvidenceSnippet(BaseModel):
    """A snippet of text extracted as evidence."""

    snippet_id: str
    text: str = Field(max_length=500)  # ~2-3 sentences
    document_id: str
    page: int | None = None
    section: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    extraction_method: str  # "keyword", "semantic", "structured"


class RequirementFinding(BaseModel):
    """Evidence and assessment for a single requirement."""

    requirement_id: str
    mapped_documents: list[str]  # document_ids
    evidence_snippets: list[EvidenceSnippet]
    status: Literal["covered", "partial", "missing", "needs_review"]
    confidence: float = Field(ge=0.0, le=1.0)
    ai_comments: str | None = None
    human_comments: str | None = None


# ============================================================================
# Validation Models
# ============================================================================


class DateValidation(BaseModel):
    """Result of date alignment validation."""

    validation_type: Literal["date_alignment"] = "date_alignment"
    date1_field: str
    date1_value: str
    date1_source: str  # "DOC-001, Page 5"
    date2_field: str
    date2_value: str
    date2_source: str
    delta_days: int
    max_allowed: int
    status: Literal["pass", "fail", "warning"]
    message: str


class LandTenureValidation(BaseModel):
    """Result of land tenure validation."""

    validation_type: Literal["land_tenure"] = "land_tenure"
    field: str  # "owner_name", "area_hectares", etc.
    values_found: list[dict]  # [{"value": "Nick Denman", "source": "DOC-001"}]
    status: Literal["pass", "fail", "warning"]
    message: str
    fuzzy_match_threshold: float = 0.8


class ProjectIDValidation(BaseModel):
    """Result of project ID consistency validation."""

    validation_type: Literal["project_id"] = "project_id"
    project_id: str
    occurrences: list[dict]  # [{"document_id": "DOC-001", "page": 3}]
    min_required: int = 3
    status: Literal["pass", "fail", "warning"]
    message: str


# ============================================================================
# Report Models
# ============================================================================


class ReportMetadata(BaseModel):
    """Metadata for a generated report."""

    report_id: str
    session_id: str
    generated_at: datetime
    format: Literal["markdown", "json", "pdf"]
    report_path: str


class ReviewSummary(BaseModel):
    """High-level summary of review findings."""

    project_name: str
    project_id: str | None
    methodology: str
    reviewed_at: datetime
    total_requirements: int
    covered: int
    partial: int
    missing: int
    needs_human_review: list[str]  # requirement_ids
    overall_status: Literal["approved", "needs_revision", "not_approved"]
