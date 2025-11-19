"""Error formatting utilities.

Consolidates error message formatting found throughout the codebase,
providing consistent, user-friendly error messages with recovery guidance.
"""

from typing import Any


def format_error_with_recovery(
    error: Exception,
    context: str,
    recovery_steps: list[str],
    show_traceback: bool = False,
) -> str:
    """Format error message with recovery guidance.

    Args:
        error: The exception that occurred
        context: Context description (e.g., "PDF extraction", "LLM call")
        recovery_steps: List of steps user can take to recover
        show_traceback: Whether to include exception details

    Returns:
        Formatted error message with recovery steps
    """
    steps_text = "\n".join(f"{i+1}. {step}" for i, step in enumerate(recovery_steps))

    message = f"""
Error during {context}: {type(error).__name__}
{str(error) if show_traceback else ''}

Recovery steps:
{steps_text}
"""
    return message.strip()


def format_validation_error(
    field: str,
    value: Any,
    expected: str,
    suggestion: str | None = None,
) -> str:
    """Format validation error message.

    Args:
        field: Field name that failed validation
        value: Invalid value provided
        expected: Description of expected value
        suggestion: Optional suggestion for fixing

    Returns:
        Formatted validation error message
    """
    message = f"Invalid value for '{field}': {value}\nExpected: {expected}"
    if suggestion:
        message += f"\nSuggestion: {suggestion}"
    return message


def format_file_not_found_error(
    filepath: str,
    context: str,
    suggestions: list[str] | None = None,
) -> str:
    """Format file not found error with helpful suggestions.

    Args:
        filepath: Path to file that wasn't found
        context: What operation was being attempted
        suggestions: Optional list of suggestions

    Returns:
        Formatted error message
    """
    message = f"File not found during {context}: {filepath}"

    if suggestions:
        steps = "\n".join(f"  • {s}" for s in suggestions)
        message += f"\n\nSuggestions:\n{steps}"

    return message
