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


def format_review_started(session_result: dict[str, Any], discovery_result: dict[str, Any]) -> str:
    """Format start_review response combining session creation and document discovery.

    Specialized formatter for start_review tool.
    """
    summary_lines = []
    for doc_type, count in sorted(discovery_result["classification_summary"].items()):
        summary_lines.append(f"  - {doc_type}: {count}")

    summary = "\n".join(summary_lines) if summary_lines else "  (none found)"

    return (
        ResponseBuilder()
        .success("Review Started Successfully")
        .add_data("session_id", session_result["session_id"])
        .add_data("project", session_result["project_name"])
        .add_data("methodology", session_result["methodology"])
        .add_data("documents_path", session_result["documents_path"])
        .add_data("created", session_result["created_at"])
        .add_section("Document Discovery Complete", {
            "documents_found": discovery_result["documents_found"]
        })
        .build()
        + f"\n\nClassification Summary:\n{summary}\n\n"
        + "Next Steps:\n"
        + "  - Review the document classifications\n"
        + "  - Use the /document-discovery prompt for detailed results\n"
        + "  - Or proceed to evidence extraction (Phase 3)"
    )


def format_upload_result(result: dict[str, Any]) -> str:
    """Format file upload response with session and discovery details.

    Specialized formatter for create_session_from_uploads and start_review_from_uploads.
    """
    builder = ResponseBuilder().success(result.get("message", "Files Uploaded Successfully"))

    # Session details
    if "session_id" in result:
        builder.add_data("session_id", result["session_id"])
    if "project_name" in result:
        builder.add_data("project", result["project_name"])

    # File statistics
    if "files_received" in result:
        builder.add_section("Files", {
            "received": result["files_received"],
            "saved": result.get("files_saved", result["files_received"]),
        })

    # Document discovery (if present)
    if "documents_found" in result:
        builder.add_section("Document Discovery", {
            "documents_found": result["documents_found"],
        })

        # Classification summary
        if "classification_summary" in result:
            summary_lines = []
            for doc_type, count in sorted(result["classification_summary"].items()):
                summary_lines.append(f"  - {doc_type}: {count}")
            if summary_lines:
                builder.lines.append("Classification Summary:")
                builder.lines.extend(summary_lines)
                builder.lines.append("")

    # Next steps
    if result.get("documents_found"):
        builder.add_next_step("Run evidence extraction to analyze document contents")
    elif "session_id" in result:
        builder.add_next_step(f"Run document discovery with session_id: {result['session_id']}")

    return builder.build()


def format_pdf_extraction(result: dict[str, Any]) -> str:
    """Format PDF text extraction response.

    Specialized formatter for extract_pdf_text tool.
    """
    lines = ["✓ PDF Text Extracted", ""]

    lines.append(f"Filepath: {result.get('filepath', 'Unknown')}")
    lines.append(f"Page Count: {result.get('page_count', 0)}")
    lines.append(f"Extraction Method: {result.get('extraction_method', 'marker')}")
    lines.append(f"Character Count: {len(result.get('markdown', ''))}")
    lines.append("")

    if result.get('tables'):
        lines.append(f"Tables Found: {len(result['tables'])}")
        lines.append("")

    if result.get('images'):
        lines.append(f"Images Found: {len(result['images'])}")
        lines.append("")

    # Show full content
    content = result.get('markdown', result.get('full_text', ''))
    if content:
        lines.append("Full Content:")
        lines.append(content)

    return "\n".join(lines)


def format_gis_metadata(result: dict[str, Any]) -> str:
    """Format GIS metadata extraction response.

    Specialized formatter for extract_gis_metadata tool.
    """
    return (
        ResponseBuilder()
        .success("GIS Metadata Extracted")
        .add_data("filepath", result.get("filepath", "Unknown"))
        .add_data("driver", result.get("driver", "Unknown"))
        .add_data("crs", result.get("crs", "Unknown"))
        .add_data("feature_count", result.get("feature_count", 0))
        .add_data("geometry_type", result.get("geometry_type", "Unknown"))
        .add_section("Bounds", {
            "bounds": str(result.get("bounds", "Unknown"))
        })
        .build()
    )


def format_requirement_mapping(result: dict[str, Any]) -> str:
    """Format requirement mapping response with full evidence details.

    Specialized formatter for map_requirement tool.
    """
    status_emoji = {
        "covered": "✅",
        "partial": "⚠️",
        "missing": "❌",
        "flagged": "🚩"
    }

    emoji = status_emoji.get(result['status'], "❓")

    lines = ["✓ Requirement Mapping Complete", ""]
    lines.append(f"{emoji} {result['requirement_id']}: {result['requirement_text']}")
    lines.append("")
    lines.append(f"Status: {result['status'].upper()}")
    lines.append(f"Confidence: {result['confidence']:.2f}")
    lines.append(f"Category: {result['category']}")
    lines.append("")
    lines.append(f"Mapped Documents ({len(result['mapped_documents'])}):")

    for doc in result['mapped_documents']:
        lines.append(f"  - {doc['document_name']} (relevance: {doc['relevance_score']:.2f})")

    lines.append("")
    lines.append(f"Evidence Snippets ({len(result['evidence_snippets'])}):")

    for idx, snippet in enumerate(result['evidence_snippets'], 1):
        page_info = f" (page {snippet['page']})" if snippet.get('page') else ""
        section_info = f" - {snippet['section']}" if snippet.get('section') else ""
        lines.append(f"\n{idx}. {snippet['document_name']}{page_info}{section_info}")
        lines.append(f"   {snippet['text']}")  # Full text, no truncation
        lines.append(f"   Confidence: {snippet['confidence']:.2f}")

    return "\n".join(lines)
