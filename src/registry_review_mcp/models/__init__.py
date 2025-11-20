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
    TimestampedModel,
    IdentifiedModel,
    VersionedModel,
    NamedEntity,
    StatusTrackedModel,
    ModelID,
    Timestamp,
    ConfidenceScore,
)

# Session & Document models (Workflow Stages 1-2)
from .schemas import (
    Session,
    ProjectMetadata,
    WorkflowProgress,
    SessionStatistics,
    Document,
    DocumentMetadata,
    Checklist,
    Requirement,
    RequirementMapping,
    MappingCollection,
)

# Evidence extraction models (Stage 3)
from .evidence import (
    EvidenceSnippet,
    MappedDocument,
    RequirementEvidence,
    EvidenceExtractionResult,
    StructuredField,
)

# Cross-validation models (Stage 4)
from .validation import (
    DateField,
    DateAlignmentValidation,
    LandTenureField,
    LandTenureValidation,
    ProjectIDOccurrence,
    ProjectIDValidation,
    ContradictionCheck,
    ValidationSummary,
    ValidationResult,
)

# Report generation models (Stage 5)
from .report import (
    ReportMetadata,
    RequirementFinding,
    ValidationFinding,
    ReportSummary,
    ReviewReport,
)

# Tool responses (all stages)
from .responses import ToolResponse

# Errors (all stages)
from .errors import (
    RegistryReviewError,
    SessionError,
    SessionNotFoundError,
    SessionLockError,
    DocumentError,
    DocumentNotFoundError,
    DocumentExtractionError,
    DocumentClassificationError,
    RequirementError,
    RequirementNotFoundError,
    EvidenceExtractionError,
    ValidationError,
    DateAlignmentError,
    LandTenureValidationError,
    ConfigurationError,
    ChecklistLoadError,
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
