"""Evidence extraction data models."""

from datetime import datetime
from typing import Any

from pydantic import Field
from .base import BaseModel, ConfidenceScore


class EvidenceSnippet(BaseModel):
    """A snippet of text that serves as evidence for a requirement."""

    text: str = Field(..., description="The extracted text snippet", max_length=5000)
    document_id: str = Field(..., description="ID of the source document")
    document_name: str = Field(..., description="Name of the source document")
    page: int | None = Field(None, description="Page number (1-indexed)")
    section: str | None = Field(None, description="Section header")
    confidence: ConfidenceScore
    keywords_matched: list[str] = Field(
        default_factory=list, description="Keywords that matched in this snippet"
    )
    snippet_id: str | None = Field(None, description="Unique snippet identifier")
    extraction_method: str | None = Field(None, description="Method: keyword, semantic, or structured")
    structured_fields: dict[str, Any] | None = Field(
        None,
        description="Structured fields extracted for cross-validation (owner_name, project_id, dates, etc.)"
    )


class MappedDocument(BaseModel):
    """A document mapped to a requirement."""

    document_id: str = Field(..., description="ID of the document")
    document_name: str = Field(..., description="Name of the document")
    filepath: str = Field(..., description="Path to the document")
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0, description="Relevance score"
    )
    keywords_found: list[str] = Field(
        default_factory=list, description="Keywords found in this document"
    )


class RequirementEvidence(BaseModel):
    """Evidence collected for a single requirement."""

    requirement_id: str = Field(..., description="Requirement ID (e.g., REQ-002)")
    requirement_text: str = Field(..., description="The requirement text")
    category: str = Field(..., description="Requirement category")
    validation_type: str = Field(
        "document_presence",
        description="Validation type from checklist: document_presence, cross_document, structured_field, manual"
    )
    status: str = Field(
        ..., description="Status: covered, partial, missing, or flagged"
    )
    confidence: ConfidenceScore
    mapped_documents: list[MappedDocument] = Field(
        default_factory=list, description="Documents containing evidence"
    )
    evidence_snippets: list[EvidenceSnippet] = Field(
        default_factory=list, description="Extracted evidence snippets"
    )
    notes: str | None = Field(None, description="Additional notes or flags")
    extracted_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When evidence was extracted",
    )


class EvidenceExtractionResult(BaseModel):
    """Complete evidence extraction results for a session."""

    session_id: str = Field(..., description="Session identifier")
    requirements_total: int = Field(..., description="Total requirements")
    requirements_covered: int = Field(..., description="Requirements with clear evidence")
    requirements_partial: int = Field(
        ..., description="Requirements with partial evidence"
    )
    requirements_missing: int = Field(
        ..., description="Requirements with no evidence"
    )
    requirements_flagged: int = Field(
        ..., description="Requirements flagged for human review"
    )
    overall_coverage: float = Field(
        ..., ge=0.0, le=1.0, description="Overall coverage percentage"
    )
    evidence: list[RequirementEvidence] = Field(
        default_factory=list, description="Evidence for each requirement"
    )
    extracted_at: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="When extraction was performed",
    )


class StructuredField(BaseModel):
    """A structured field extracted from documents."""

    field_name: str = Field(..., description="Name of the field")
    field_value: Any = Field(..., description="Extracted value")
    source_document: str = Field(..., description="Source document ID")
    page: int | None = Field(None, description="Page number")
    confidence: ConfidenceScore
    extraction_method: str = Field(..., description="Method used to extract (regex, table, etc.)")
