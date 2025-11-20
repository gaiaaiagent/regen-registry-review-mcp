"""Helper utilities for MCP tools to eliminate duplication.

This module provides decorators that eliminate common boilerplate patterns
across tool implementations.

Key patterns eliminated:
- Try/except error handling (repeated 15+ times)
- Logger.info/error calls (repeated 30+ times)
"""

import logging
from functools import wraps
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def with_error_handling(tool_name: str):
    """Decorator to add consistent error handling and logging to tools.

    Before (per tool):
        try:
            logger.info(f"Starting operation")
            result = await do_something()
            logger.info(f"Operation complete")
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error(f"Operation failed: {e}", exc_info=True)
            return f"✗ Error: {str(e)}"

    After (per tool):
        @with_error_handling("operation_name")
        async def tool(**kwargs):
            result = await do_something()
            return json.dumps(result, indent=2)

    Reduction: ~8 lines → 2 lines per tool
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                logger.info(f"{tool_name}: Starting")
                result = await func(*args, **kwargs)
                logger.info(f"{tool_name}: Success")
                return result
            except Exception as e:
                logger.error(f"{tool_name}: Failed - {e}", exc_info=True)
                return format_error(e, tool_name)
        return wrapper
    return decorator


def format_error(error: Exception, context: str | None = None) -> str:
    """Format error response consistently.

    Args:
        error: Exception that occurred
        context: Optional context string (e.g., tool name)

    Returns:
        Formatted error string with type and message
    """
    error_type = type(error).__name__
    error_msg = str(error)

    if context:
        return f"✗ Error in {context}: [{error_type}] {error_msg}"
    return f"✗ Error: [{error_type}] {error_msg}"


def generate_validation_id(validation_type: str) -> str:
    """Generate unique validation ID with type prefix.

    Args:
        validation_type: Type of validation (date_alignment, land_tenure, project_id)

    Returns:
        Unique validation ID (e.g., "VAL-DATE-abc12345")
    """
    import uuid

    type_map = {
        "date_alignment": "DATE",
        "land_tenure": "TENURE",
        "project_id": "PID",
    }
    prefix = type_map.get(validation_type, "VAL")
    return f"VAL-{prefix}-{uuid.uuid4().hex[:8]}"
