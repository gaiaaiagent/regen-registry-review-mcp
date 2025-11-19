"""Base class for MCP tools with unified patterns.

This module provides a base class that eliminates boilerplate and ensures
consistent error handling, validation, and response formatting across all tools.

Before (per tool): ~60 lines of boilerplate
After (per tool): ~12 lines of pure business logic
Reduction: ~80% per tool
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any
from pydantic import BaseModel, ValidationError
import json
import logging

logger = logging.getLogger(__name__)

TArgs = TypeVar('TArgs', bound=BaseModel)
TResult = TypeVar('TResult')


class MCPTool(ABC, Generic[TArgs, TResult]):
    """Base class for all MCP tools with automatic error handling and validation.

    Subclasses must implement:
    - name: Tool name for MCP registration
    - description: Tool description
    - args_class: Pydantic model for argument validation
    - execute(): Core business logic

    Example:
        class CreateSessionTool(MCPTool[CreateSessionArgs, dict]):
            name = "create_session"
            description = "Create new review session"
            args_class = CreateSessionArgs

            async def execute(self, args: CreateSessionArgs) -> dict:
                session = await Session.create(args.project_name)
                return session.to_dict()
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name for MCP registration."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for MCP."""
        pass

    @property
    @abstractmethod
    def args_class(self) -> type[TArgs]:
        """Pydantic model class for argument validation."""
        pass

    @abstractmethod
    async def execute(self, args: TArgs) -> TResult:
        """Core business logic. Override in subclass."""
        pass

    def format_success(self, result: TResult, message: str = "Success") -> str:
        """Format successful response as JSON string.

        Override for custom formatting if needed.
        """
        return json.dumps({
            "status": "success",
            "message": message,
            "data": result
        }, indent=2)

    def format_error(self, error: Exception) -> str:
        """Format error response as JSON string.

        Override for custom error formatting if needed.
        """
        error_data = {
            "status": "error",
            "error_type": type(error).__name__,
            "message": str(error)
        }

        # Add validation details for Pydantic errors
        if isinstance(error, ValidationError):
            error_data["validation_errors"] = error.errors()

        return json.dumps(error_data, indent=2)

    async def __call__(self, **kwargs) -> str:
        """Entry point called by MCP server.

        Handles:
        1. Argument validation (Pydantic)
        2. Core execution (via execute())
        3. Response formatting
        4. Error handling
        """
        try:
            # Validate arguments
            args = self.args_class(**kwargs)

            # Log execution
            logger.debug(f"Executing {self.name} with args: {args}")

            # Execute core logic
            result = await self.execute(args)

            # Format and return success
            return self.format_success(result)

        except ValidationError as e:
            logger.error(f"{self.name} validation error: {e}")
            return self.format_error(e)

        except Exception as e:
            logger.error(f"{self.name} execution error: {e}", exc_info=True)
            return self.format_error(e)


def register_tools(mcp_server, *tools: MCPTool):
    """Register multiple tools with MCP server.

    Args:
        mcp_server: MCP server instance
        *tools: MCPTool instances to register

    Example:
        register_tools(
            mcp,
            CreateSessionTool(),
            ListSessionsTool(),
            ExtractEvidenceTool()
        )
    """
    for tool in tools:
        # Register tool with MCP server
        mcp_server.tool(name=tool.name, description=tool.description)(tool)
        logger.info(f"Registered MCP tool: {tool.name}")
