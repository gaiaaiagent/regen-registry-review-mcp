"""Error hierarchy for Registry Review MCP.

All errors inherit from RegistryReviewError for consistent handling.
"""


class RegistryReviewError(Exception):
    """Base exception for all registry review errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class SessionError(RegistryReviewError):
    """Errors related to session management."""

    pass


class SessionNotFoundError(SessionError, FileNotFoundError):
    """Session does not exist.

    Inherits FileNotFoundError so REST handlers' ``except FileNotFoundError``
    clauses catch it without per-endpoint changes.
    """

    pass


class SessionLockError(SessionError):
    """Failed to acquire session lock for atomic updates."""

    pass


class DocumentError(RegistryReviewError):
    """Errors related to document processing."""

    pass


class DocumentNotFoundError(DocumentError):
    """Document does not exist."""

    pass


class DocumentExtractionError(DocumentError):
    """Failed to extract content from document."""

    pass


class DocumentClassificationError(DocumentError):
    """Failed to classify document type."""

    pass


class RequirementError(RegistryReviewError):
    """Errors related to requirement processing."""

    pass


class RequirementNotFoundError(RequirementError):
    """Requirement does not exist in checklist."""

    pass


class EvidenceExtractionError(RequirementError):
    """Failed to extract evidence for requirement."""

    pass


class ValidationError(RegistryReviewError):
    """Errors related to cross-document validation."""

    pass


class DateAlignmentError(ValidationError):
    """Date validation failed."""

    pass


class LandTenureValidationError(ValidationError):
    """Land tenure validation failed."""

    pass


class ConfigurationError(RegistryReviewError):
    """Configuration or settings errors."""

    pass


class ChecklistLoadError(ConfigurationError):
    """Failed to load or parse checklist."""

    pass
