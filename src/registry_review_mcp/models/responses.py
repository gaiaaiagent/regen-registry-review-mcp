"""Standard MCP tool response models.

This module provides consistent response formatting for all MCP tools,
replacing scattered response patterns throughout the codebase.

Phase 4.3: Tool Response Formatting
Target: Consolidate 15 MCP tools with inconsistent responses
Benefit: Type-safe, predictable API responses
"""

from typing import Any, Literal
from datetime import datetime
from .base import BaseModel
from pydantic import Field


class ToolResponse(BaseModel):
    """Standard MCP tool response format.

    All MCP tools should return responses using this consistent structure:
    - status: success | error | partial
    - message: Human-readable description
    - data: Tool-specific result data
    - metadata: Optional context (timestamps, IDs, etc.)

    Examples:
        Success response:
            ToolResponse.success(
                message="Discovered 5 documents",
                data={"documents": [...]},
                session_id="abc123"
            )

        Error response:
            ToolResponse.error(
                message="Session not found",
                error_details={"session_id": "abc123"},
                suggestion="Use list_sessions to see available sessions"
            )
    """

    status: Literal["success", "error", "partial"] = Field(
        description="Operation status"
    )
    message: str = Field(
        description="Human-readable message describing the result"
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific result data"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (timestamps, IDs, counts, etc.)"
    )

    @classmethod
    def success(
        cls,
        message: str,
        data: dict[str, Any] | None = None,
        **metadata: Any
    ) -> "ToolResponse":
        """Create a success response.

        Args:
            message: Success message
            data: Tool-specific result data
            **metadata: Optional metadata fields

        Returns:
            ToolResponse with status="success"
        """
        return cls(
            status="success",
            message=message,
            data=data or {},
            metadata=metadata
        )

    @classmethod
    def error(
        cls,
        message: str,
        error_details: dict[str, Any] | None = None,
        **metadata: Any
    ) -> "ToolResponse":
        """Create an error response.

        Args:
            message: Error message
            error_details: Error details and context
            **metadata: Optional metadata fields

        Returns:
            ToolResponse with status="error"
        """
        return cls(
            status="error",
            message=message,
            data=error_details or {},
            metadata=metadata
        )

    @classmethod
    def partial(
        cls,
        message: str,
        data: dict[str, Any] | None = None,
        **metadata: Any
    ) -> "ToolResponse":
        """Create a partial success response.

        Use this when an operation partially succeeded but had some failures.

        Args:
            message: Partial success message
            data: Tool-specific result data
            **metadata: Optional metadata fields

        Returns:
            ToolResponse with status="partial"
        """
        return cls(
            status="partial",
            message=message,
            data=data or {},
            metadata=metadata
        )

    def to_json(self) -> str:
        """Serialize to JSON string.

        Returns:
            Pretty-printed JSON string
        """
        return self.model_dump_json(indent=2)

    def with_timestamp(self) -> "ToolResponse":
        """Add timestamp to metadata.

        Returns:
            Self (for chaining)
        """
        self.metadata["timestamp"] = datetime.now().isoformat()
        return self

    def with_session_id(self, session_id: str) -> "ToolResponse":
        """Add session_id to metadata.

        Args:
            session_id: Session identifier

        Returns:
            Self (for chaining)
        """
        self.metadata["session_id"] = session_id
        return self

    def with_count(self, count: int, label: str = "count") -> "ToolResponse":
        """Add count to metadata.

        Args:
            count: Count value
            label: Label for the count (default: "count")

        Returns:
            Self (for chaining)
        """
        self.metadata[label] = count
        return self
