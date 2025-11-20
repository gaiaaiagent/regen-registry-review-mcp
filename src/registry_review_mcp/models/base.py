"""Base models with common fields.

This module provides base Pydantic models that share common patterns:
- TimestampedModel: Automatic created_at/updated_at timestamps
- IdentifiedModel: Automatic UUID generation + timestamps
- VersionedModel: Version tracking for entities

Phase 4.3: Model Consolidation
Target: Eliminate repeated field definitions across models
Benefit: DRY principle, consistent timestamp handling, type safety
"""

import uuid
from datetime import datetime
from typing import Any, Annotated
from pydantic import BaseModel as PydanticBaseModel, Field, ConfigDict


class BaseModel(PydanticBaseModel):
    """Base model with common configuration.

    All models should inherit from this instead of pydantic.BaseModel directly.
    Provides consistent JSON encoding (datetime → ISO format).
    """

    model_config = ConfigDict(
        # Serialize datetime as ISO 8601 strings
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        # Allow arbitrary types (for flexibility)
        arbitrary_types_allowed=True,
        # Validate assignments after model creation
        validate_assignment=True
    )


class TimestampedModel(BaseModel):
    """Model with automatic timestamp tracking.

    Adds:
    - created_at: Set automatically on creation
    - updated_at: Set automatically on creation and updates

    Example:
        class Session(TimestampedModel):
            project_name: str
            # Inherits: created_at, updated_at
    """

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when entity was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when entity was last updated"
    )

    def touch(self) -> None:
        """Update the updated_at timestamp to now."""
        self.updated_at = datetime.now()


class IdentifiedModel(TimestampedModel):
    """Model with automatic ID generation and timestamps.

    Adds:
    - id: Auto-generated UUID
    - created_at: Set automatically on creation
    - updated_at: Set automatically on creation and updates

    Example:
        class Evidence(IdentifiedModel):
            requirement_id: str
            status: str
            # Inherits: id, created_at, updated_at
    """

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier (UUID)"
    )


class VersionedModel(IdentifiedModel):
    """Model with version tracking.

    Adds:
    - id: Auto-generated UUID
    - version: Version number (starts at 1)
    - created_at: Set automatically on creation
    - updated_at: Set automatically on creation and updates

    Example:
        class Document(VersionedModel):
            filename: str
            classification: str
            # Inherits: id, version, created_at, updated_at
    """

    version: int = Field(
        default=1,
        description="Version number (incremented on updates)",
        ge=1
    )

    def increment_version(self) -> None:
        """Increment version and update timestamp."""
        self.version += 1
        self.touch()


# Example usage for common patterns

class NamedEntity(IdentifiedModel):
    """Base for entities with names and descriptions.

    Adds:
    - name: Entity name
    - description: Optional description
    - Plus id, created_at, updated_at from IdentifiedModel

    Example:
        class Project(NamedEntity):
            location: str
            acreage: float
            # Inherits: id, name, description, created_at, updated_at
    """

    name: str = Field(description="Entity name")
    description: str | None = Field(default=None, description="Optional description")


class StatusTrackedModel(IdentifiedModel):
    """Base for entities with status tracking.

    Adds:
    - status: Current status
    - status_history: History of status changes
    - Plus id, created_at, updated_at from IdentifiedModel

    Example:
        class ReviewSession(StatusTrackedModel):
            project_name: str
            # Inherits: id, status, status_history, created_at, updated_at
    """

    status: str = Field(description="Current status")
    status_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="History of status changes"
    )

    def change_status(self, new_status: str, note: str | None = None) -> None:
        """Change status and record in history.

        Args:
            new_status: New status value
            note: Optional note about the change
        """
        old_status = self.status
        self.status = new_status
        self.status_history.append({
            "from": old_status,
            "to": new_status,
            "timestamp": datetime.now().isoformat(),
            "note": note
        })
        self.touch()


# Type aliases for common patterns
ModelID = str  # UUID string
Timestamp = datetime  # ISO 8601 datetime

# Annotated types for common field constraints
ConfidenceScore = Annotated[float, Field(ge=0.0, le=1.0, description="Confidence score between 0 and 1")]
