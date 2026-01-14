"""Per-extraction verification models for human review."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import Field
from .base import BaseModel


class VerificationStatus(str, Enum):
    """Status of human verification on an evidence snippet."""

    UNVERIFIED = "unverified"      # Not yet reviewed
    VERIFIED = "verified"           # Human confirms valid evidence
    REJECTED = "rejected"           # Human confirms NOT valid evidence
    PARTIAL = "partial"             # Useful but incomplete
    NEEDS_CONTEXT = "needs_context" # Valid but missing context


class SnippetVerification(BaseModel):
    """Human verification record for a single EvidenceSnippet."""

    snippet_id: str = Field(..., description="References EvidenceSnippet.snippet_id")
    requirement_id: str = Field(..., description="Requirement this snippet relates to")

    # Verification
    status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        description="Human verification status"
    )
    verified_by: Optional[str] = Field(None, description="Reviewer identifier")
    verified_at: Optional[str] = Field(None, description="ISO timestamp of verification")

    # Notes
    reviewer_notes: Optional[str] = Field(None, description="Reviewer's explanation")

    # Audit trail
    previous_status: Optional[str] = Field(None, description="Previous status for history")


class RequirementVerificationSummary(BaseModel):
    """Summary of verification status for all snippets in a requirement."""

    requirement_id: str
    total_snippets: int = Field(0, description="Total evidence snippets")
    verified_count: int = Field(0, description="Snippets marked verified")
    rejected_count: int = Field(0, description="Snippets marked rejected")
    pending_count: int = Field(0, description="Snippets not yet reviewed")

    # Computed
    verification_progress: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Fraction of snippets reviewed"
    )


class SessionVerifications(BaseModel):
    """All verifications for a session, stored in verifications.json."""

    session_id: str
    verifications: dict[str, list[SnippetVerification]] = Field(
        default_factory=dict,
        description="Verifications by requirement_id"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
