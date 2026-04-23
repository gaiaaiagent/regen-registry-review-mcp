"""Models package - domain-organized data structures.

This module provides comprehensive exports for all model classes, enabling both:
- Convenient imports: `from models import Session, Document`
- Explicit imports: `from models.schemas import Session` (when location matters)

Model Organization:
- base.py: Base classes and common patterns
- schemas.py: Session/Document/Checklist (Workflow Stages 1-2)
- evidence.py: Evidence extraction models (Stage 3)
- validation.py: Cross-validation models (Stage 4)
- report.py: Report generation models (Stage 5)
- responses.py: MCP tool response format
- errors.py: Exception hierarchy
"""

# Base models and types
from .base import (
    BaseModel,
    ConfidenceScore,
    IdentifiedModel,
    ModelID,
    NamedEntity,
    StatusTrackedModel,
    Timestamp,
    TimestampedModel,
    VersionedModel,
)

# Errors (all stages)
from .errors import (
    ChecklistLoadError,
    ConfigurationError,
    DateAlignmentError,
    DocumentClassificationError,
    DocumentError,
    DocumentExtractionError,
    DocumentNotFoundError,
    EvidenceExtractionError,
    LandTenureValidationError,
    RegistryReviewError,
    RequirementError,
    RequirementNotFoundError,
    SessionError,
    SessionLockError,
    SessionNotFoundError,
    ValidationError,
)

# Evidence extraction models (Stage 3)
from .evidence import (
    EvidenceExtractionResult,
    EvidenceSnippet,
    MappedDocument,
    RequirementEvidence,
    StructuredField,
)

# Report generation models (Stage 5)
from .report import (
    ReportMetadata,
    ReportSummary,
    RequirementFinding,
    ReviewReport,
    ValidationFinding,
)

# Tool responses (all stages)
from .responses import ToolResponse

# Session & Document models (Workflow Stages 1-2)
from .schemas import (
    Checklist,
    Document,
    DocumentMetadata,
    MappingCollection,
    ProjectMetadata,
    Requirement,
    RequirementMapping,
    Session,
    SessionStatistics,
    WorkflowProgress,
)

# Cross-validation models (Stage 4)
from .validation import (
    ContradictionCheck,
    DateAlignmentValidation,
    DateField,
    LandTenureField,
    LandTenureValidation,
    ProjectIDOccurrence,
    ProjectIDValidation,
    ValidationResult,
    ValidationSummary,
)

__all__ = [
    # Base models and types
    "BaseModel",
    "TimestampedModel",
    "IdentifiedModel",
    "VersionedModel",
    "NamedEntity",
    "StatusTrackedModel",
    "ModelID",
    "Timestamp",
    "ConfidenceScore",
    # Session & Document (Stages 1-2)
    "Session",
    "ProjectMetadata",
    "WorkflowProgress",
    "SessionStatistics",
    "Document",
    "DocumentMetadata",
    "Checklist",
    "Requirement",
    "RequirementMapping",
    "MappingCollection",
    # Evidence (Stage 3)
    "EvidenceSnippet",
    "MappedDocument",
    "RequirementEvidence",
    "EvidenceExtractionResult",
    "StructuredField",
    # Validation (Stage 4)
    "DateField",
    "DateAlignmentValidation",
    "LandTenureField",
    "LandTenureValidation",
    "ProjectIDOccurrence",
    "ProjectIDValidation",
    "ContradictionCheck",
    "ValidationSummary",
    "ValidationResult",
    # Report (Stage 5)
    "ReportMetadata",
    "RequirementFinding",
    "ValidationFinding",
    "ReportSummary",
    "ReviewReport",
    # Tool responses
    "ToolResponse",
    # Errors
    "RegistryReviewError",
    "SessionError",
    "SessionNotFoundError",
    "SessionLockError",
    "DocumentError",
    "DocumentNotFoundError",
    "DocumentExtractionError",
    "DocumentClassificationError",
    "RequirementError",
    "RequirementNotFoundError",
    "EvidenceExtractionError",
    "ValidationError",
    "DateAlignmentError",
    "LandTenureValidationError",
    "ConfigurationError",
    "ChecklistLoadError",
]
