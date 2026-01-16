"""Validation result data models."""

from datetime import datetime
from pydantic import Field
from .base import BaseModel, ConfidenceScore


class DateField(BaseModel):
    """A date field extracted from a document."""

    field_name: str
    value: datetime
    source: str  # "DOC-123, Page 5"
    document_id: str
    confidence: ConfidenceScore


class DateAlignmentValidation(BaseModel):
    """Result of date alignment validation between two fields."""

    validation_id: str
    validation_type: str = "date_alignment"
    date1: DateField
    date2: DateField
    delta_days: int
    max_allowed_days: int
    status: str  # "pass", "fail", "warning"
    message: str
    flagged_for_review: bool = False


class LandTenureField(BaseModel):
    """Land tenure information extracted from a document."""

    owner_name: str
    area_hectares: float | None = None
    tenure_type: str | None = None  # "lease", "ownership", "easement"
    source: str  # "DOC-123, Page 8"
    document_id: str
    confidence: ConfidenceScore


class LandTenureValidation(BaseModel):
    """Result of cross-document land tenure validation."""

    validation_id: str
    validation_type: str = "land_tenure"
    fields: list[LandTenureField]
    owner_name_match: bool
    owner_name_similarity: float = Field(..., ge=0.0, le=1.0)
    area_consistent: bool
    tenure_type_consistent: bool
    status: str  # "pass", "fail", "warning"
    message: str
    discrepancies: list[str] = Field(default_factory=list)
    flagged_for_review: bool = False


class ProjectIDOccurrence(BaseModel):
    """Single occurrence of a project ID in a document."""

    project_id: str
    document_id: str
    document_name: str
    page: int | None = None
    section: str | None = None


class ProjectIDValidation(BaseModel):
    """Result of project ID consistency validation."""

    validation_id: str
    validation_type: str = "project_id"
    expected_pattern: str  # r"^C\d{2}-\d+$"
    found_ids: list[str]
    primary_id: str | None = None
    occurrences: list[ProjectIDOccurrence]
    total_occurrences: int
    documents_with_id: int
    total_documents: int
    status: str  # "pass", "fail", "warning"
    message: str
    flagged_for_review: bool = False


class ContradictionCheck(BaseModel):
    """Result of checking for contradictions between two pieces of information."""

    validation_id: str
    validation_type: str = "contradiction"
    field_name: str
    value1: str
    source1: str
    value2: str
    source2: str
    is_contradiction: bool
    severity: str  # "high", "medium", "low"
    message: str
    flagged_for_review: bool = False


class ValidationSummary(BaseModel):
    """Summary statistics for validation results."""

    total_validations: int
    validations_passed: int
    validations_failed: int
    validations_warning: int
    items_flagged: int
    pass_rate: float = Field(..., ge=0.0, le=1.0)
    extraction_method: str = "regex"  # "llm", "regex", "llm_fallback", "regex_fallback"

    # Three-layer architecture counts (optional for backward compat)
    structural_checks: int | None = None
    cross_document_checks: int | None = None
    llm_synthesis_available: bool | None = None


class SanityCheck(BaseModel):
    """Result of a single-document sanity check (Layer 1)."""

    validation_id: str
    validation_type: str
    field_name: str
    status: str  # "pass", "warning", "fail"
    message: str
    flagged_for_review: bool = False


class ValidationResult(BaseModel):
    """Complete validation results for a session."""

    session_id: str
    validated_at: datetime
    date_alignments: list[DateAlignmentValidation] = Field(default_factory=list)
    land_tenure: list[LandTenureValidation] = Field(default_factory=list)
    project_ids: list[ProjectIDValidation] = Field(default_factory=list)
    contradictions: list[ContradictionCheck] = Field(default_factory=list)
    summary: ValidationSummary
    all_passed: bool

    # Three-layer architecture results (optional for backward compat)
    sanity_checks: list[SanityCheck] = Field(default_factory=list)
    structural: dict | None = None  # Full Layer 1 results
    cross_document: dict | None = None  # Full Layer 2 results
    llm_synthesis: dict | None = None  # Full Layer 3 results

    # Fact sheet data for UI display
    fact_sheets: dict | None = None


__all__ = [
    "DateField",
    "DateAlignmentValidation",
    "LandTenureField",
    "LandTenureValidation",
    "ProjectIDOccurrence",
    "ProjectIDValidation",
    "ContradictionCheck",
    "SanityCheck",
    "ValidationSummary",
    "ValidationResult",
]
