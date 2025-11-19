"""Helper utilities for MCP tools to eliminate duplication.

This module provides decorators and formatters that eliminate common boilerplate
patterns across tool implementations.

Key patterns eliminated:
- Try/except error handling (repeated 15+ times)
- Logger.info/error calls (repeated 30+ times)
- Response string formatting (custom in each tool)
- Error message formatting (inconsistent across tools)
"""

import logging
import json
from functools import wraps
from typing import Callable, TypeVar, Any
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


def with_error_handling(tool_name: str):
    """Decorator to add consistent error handling and logging to tools.

    Before (per tool):
        try:
            logger.info(f"Starting operation")
            result = await do_something()
            logger.info(f"Operation complete")
            return format_success(result)
        except Exception as e:
            logger.error(f"Operation failed: {e}", exc_info=True)
            return f"✗ Error: {str(e)}"

    After (per tool):
        @with_error_handling("operation_name")
        async def tool(**kwargs):
            result = await do_something()
            return format_success(result)

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


def format_success(
    message: str,
    data: dict[str, Any] | None = None,
    next_step: str | None = None
) -> str:
    """Format successful tool response consistently.

    Args:
        message: Success message
        data: Optional data dictionary to include
        next_step: Optional next step instructions

    Returns:
        Formatted string with success indicator, message, data, and next steps
    """
    lines = [f"✓ {message}", ""]

    if data:
        for key, value in data.items():
            # Format key as title case with spaces
            formatted_key = key.replace("_", " ").title()
            lines.append(f"{formatted_key}: {value}")
        lines.append("")

    if next_step:
        lines.append("Next Step:")
        lines.append(f"  {next_step}")

    return "\n".join(lines)


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


def format_list(items: list[dict[str, Any]], title: str | None = None) -> str:
    """Format a list of items consistently.

    Args:
        items: List of dictionaries to format
        title: Optional title for the list

    Returns:
        Formatted string with each item as a numbered entry
    """
    lines = []

    if title:
        lines.append(f"✓ {title}")
        lines.append("")

    if not items:
        lines.append("(No items found)")
        return "\n".join(lines)

    for i, item in enumerate(items, 1):
        lines.append(f"{i}. {item.get('name', item.get('id', 'Unknown'))}")
        for key, value in item.items():
            if key not in ('name', 'id'):
                formatted_key = key.replace("_", " ").title()
                lines.append(f"   {formatted_key}: {value}")
        lines.append("")

    return "\n".join(lines)


def format_sessions_list(sessions: list[dict[str, Any]]) -> str:
    """Format list of sessions with full details.

    Specialized formatter for list_sessions tool.
    """
    if not sessions:
        return "No sessions found.\n\nCreate a new session with /initialize or the create_session tool."

    lines = [f"✓ Found {len(sessions)} session(s)", "", "=" * 80, ""]

    for idx, session in enumerate(sessions, 1):
        lines.append(f"{idx}. Session ID: {session.get('session_id', 'Unknown')}")
        lines.append(f"   Project Name: {session.get('project_name', 'Unknown')}")
        lines.append(f"   Status: {session.get('status', 'unknown')}")
        lines.append(f"   Created At: {session.get('created_at', 'Unknown')}")
        lines.append(f"   Methodology: {session.get('methodology', 'Unknown')}")
        lines.append("")

        # Project metadata
        project_meta = session.get('project_metadata', {})
        if project_meta:
            lines.append("   Project Metadata:")
            for key, value in project_meta.items():
                if value:
                    lines.append(f"    - {key}: {value}")
            lines.append("")

        # Workflow progress
        workflow = session.get('workflow_progress', {})
        if workflow:
            lines.append("   Workflow Progress:")
            for stage, status in workflow.items():
                lines.append(f"    - {stage}: {status}")
            lines.append("")

        # Statistics
        stats = session.get('statistics', {})
        if stats:
            lines.append("   Statistics:")
            for key, value in stats.items():
                lines.append(f"    - {key}: {value}")

        lines.append("")
        lines.append("-" * 80)
        lines.append("")

    lines.append("Use /document-discovery (or any workflow prompt) to continue with the most recent session.")

    return "\n".join(lines)


def format_session_created(result: dict[str, Any]) -> str:
    """Format session creation response.

    Specialized formatter for create_session and related tools.
    """
    return format_success(
        "Session Created Successfully",
        data={
            "session_id": result['session_id'],
            "project": result['project_name'],
            "methodology": result['methodology'],
            "documents_path": result['documents_path'],
            "created": result['created_at'],
        },
        next_step=f"Run document discovery with session_id: {result['session_id']}"
    )


def format_session_loaded(session_data: dict[str, Any]) -> str:
    """Format session load response.

    Specialized formatter for load_session tool.
    """
    lines = ["✓ Session Loaded", ""]

    # Basic info
    lines.append(f"Session ID: {session_data.get('session_id')}")
    lines.append(f"Project: {session_data.get('project_metadata', {}).get('project_name')}")
    lines.append(f"Status: {session_data.get('status')}")
    lines.append("")

    # Workflow progress
    progress = session_data.get("workflow_progress", {})
    if progress:
        lines.append("Workflow Progress:")
        for stage, status in progress.items():
            lines.append(f"  - {stage}: {status}")
        lines.append("")

    # Statistics
    stats = session_data.get("statistics", {})
    if stats:
        lines.append("Statistics:")
        for key, value in stats.items():
            formatted_key = key.replace("_", " ").title()
            lines.append(f"  - {formatted_key}: {value}")

    return "\n".join(lines)


def format_documents_discovered(result: dict[str, Any]) -> str:
    """Format document discovery response.

    Specialized formatter for discover_documents tool.
    """
    lines = ["✓ Documents Discovered", ""]

    summary = result.get('summary', {})
    lines.append(f"Total Documents: {summary.get('total_documents', 0)}")
    lines.append(f"Total Pages: {summary.get('total_pages', 0)}")
    lines.append("")

    by_type = summary.get('by_type', {})
    if by_type:
        lines.append("Documents by Type:")
        for doc_type, count in by_type.items():
            lines.append(f"  - {doc_type}: {count}")
        lines.append("")

    if result.get('documents'):
        lines.append("Discovered Documents:")
        for doc in result['documents']:
            lines.append(f"  • {doc.get('filename')}")
            lines.append(f"    Classification: {doc.get('classification')}")
            lines.append(f"    Confidence: {doc.get('confidence', 0):.0%}")
        lines.append("")

    lines.append("Next Step:")
    lines.append("  Run evidence extraction to analyze document contents")

    return "\n".join(lines)


def format_evidence_extracted(result: dict[str, Any]) -> str:
    """Format evidence extraction response.

    Specialized formatter for extract_evidence tool.
    """
    lines = ["✓ Evidence Extraction Complete", ""]

    summary = result.get('summary', {})
    lines.append(f"Requirements Analyzed: {summary.get('total_requirements', 0)}")
    lines.append(f"Covered: {summary.get('covered', 0)}")
    lines.append(f"Partial: {summary.get('partial', 0)}")
    lines.append(f"Missing: {summary.get('missing', 0)}")
    lines.append(f"Overall Coverage: {summary.get('coverage_percentage', 0):.0%}")
    lines.append("")

    if result.get('flagged_requirements'):
        lines.append("⚠️  Flagged Requirements:")
        for req in result['flagged_requirements'][:5]:  # Show first 5
            lines.append(f"  - {req.get('requirement_id')}: {req.get('status')}")
        lines.append("")

    lines.append("Next Step:")
    lines.append("  Review flagged requirements or proceed to cross-validation")

    return "\n".join(lines)


class ResponseBuilder:
    """Builder pattern for constructing formatted responses.

    Provides a fluent interface for building complex responses step-by-step.

    Example:
        return (
            ResponseBuilder()
            .success("Operation Complete")
            .add_data("session_id", session_id)
            .add_data("status", "ready")
            .add_section("Statistics", stats)
            .add_next_step("Run the next command")
            .build()
        )
    """

    def __init__(self):
        self.lines: list[str] = []
        self._has_content = False

    def success(self, message: str) -> 'ResponseBuilder':
        """Add success message."""
        self.lines.append(f"✓ {message}")
        self.lines.append("")
        self._has_content = True
        return self

    def error(self, message: str) -> 'ResponseBuilder':
        """Add error message."""
        self.lines.append(f"✗ {message}")
        self.lines.append("")
        self._has_content = True
        return self

    def add_data(self, key: str, value: Any) -> 'ResponseBuilder':
        """Add a key-value data pair."""
        formatted_key = key.replace("_", " ").title()
        self.lines.append(f"{formatted_key}: {value}")
        return self

    def add_section(self, title: str, data: dict[str, Any]) -> 'ResponseBuilder':
        """Add a titled section with key-value pairs."""
        if not self._has_content:
            self.lines.append("")
        self.lines.append(f"{title}:")
        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()
            self.lines.append(f"  - {formatted_key}: {value}")
        self.lines.append("")
        return self

    def add_list(self, title: str, items: list[str]) -> 'ResponseBuilder':
        """Add a titled list of items."""
        if not self._has_content:
            self.lines.append("")
        self.lines.append(f"{title}:")
        for item in items:
            self.lines.append(f"  • {item}")
        self.lines.append("")
        return self

    def add_next_step(self, step: str) -> 'ResponseBuilder':
        """Add next step instructions."""
        if not self._has_content:
            self.lines.append("")
        self.lines.append("Next Step:")
        self.lines.append(f"  {step}")
        return self

    def build(self) -> str:
        """Build and return the formatted response."""
        return "\n".join(self.lines)
