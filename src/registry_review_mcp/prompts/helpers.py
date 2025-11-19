"""Helper utilities for prompt formatting and workflow management.

This module consolidates common patterns across workflow prompts to reduce
duplication and improve maintainability.
"""

from mcp.types import TextContent

from ..tools import session_tools
from ..utils.state import StateManager


def text_content(message: str) -> list[TextContent]:
    """Wrap a message string in TextContent format.

    Args:
        message: Markdown-formatted message string

    Returns:
        List containing single TextContent object
    """
    return [TextContent(type="text", text=message)]


def format_error(title: str, details: str, suggestion: str | None = None) -> list[TextContent]:
    """Format a standardized error message.

    Args:
        title: Error title (without emoji)
        details: Error details
        suggestion: Optional suggestion for resolving the error

    Returns:
        Formatted error message
    """
    message = f"""# ❌ {title}

{details}"""

    if suggestion:
        message += f"\n\n{suggestion}"

    return text_content(message)


def format_success(title: str, data: dict[str, str], next_steps: str | None = None) -> list[TextContent]:
    """Format a standardized success message.

    Args:
        title: Success title (without emoji)
        data: Key-value pairs to display
        next_steps: Optional next steps guidance

    Returns:
        Formatted success message
    """
    lines = [f"# ✅ {title}", ""]

    for key, value in data.items():
        lines.append(f"**{key}:** {value}")

    if next_steps:
        lines.extend(["", "---", "", next_steps])

    return text_content("\n".join(lines))


def format_session_list(sessions: list[dict], empty_message: str | None = None) -> str:
    """Format a list of sessions for display.

    Args:
        sessions: List of session dictionaries
        empty_message: Optional message to show when list is empty

    Returns:
        Formatted session list string
    """
    if not sessions:
        return empty_message or "  (none)"

    return "\n".join([
        f"  • {s['session_id']} - {s.get('project_name', 'Unknown')}"
        for s in sessions
    ])


async def get_or_select_session(
    session_id: str | None,
    project_name: str | None,
    documents_path: str | None,
    workflow_name: str
) -> tuple[str | None, bool, list[TextContent] | None]:
    """Get session ID or auto-select most recent, with error handling.

    This consolidates the common pattern of:
    1. Using provided session_id
    2. Creating new session from project details
    3. Auto-selecting most recent session
    4. Returning appropriate error messages

    Args:
        session_id: Optional explicit session ID
        project_name: Optional project name (for new session)
        documents_path: Optional documents path (for new session)
        workflow_name: Name of workflow (for error messages)

    Returns:
        Tuple of (session_id, auto_selected, error_response)
        - If successful: (session_id, bool, None)
        - If error: (None, False, error_response)
    """
    auto_selected = False

    # Case 1: Session ID provided explicitly
    if session_id:
        return session_id, False, None

    # Case 2: Project details provided - create new session
    if project_name and documents_path:
        try:
            result = await session_tools.create_session(
                project_name=project_name,
                documents_path=documents_path,
                methodology="soil-carbon-v1.2.2"
            )
            return result["session_id"], False, None
        except Exception as e:
            return None, False, format_error(
                "Error Creating Session",
                f"Failed to create session: {str(e)}",
                "Please check your inputs and try again."
            )

    # Case 3: No parameters - try to use most recent session
    sessions = await session_tools.list_sessions()

    if not sessions:
        # No sessions exist - provide usage help
        usage_message = f"""# Registry Review Workflow - {workflow_name}

No review sessions found. You can either:

## Option 1: Provide Project Details (Recommended)

`/{workflow_name.lower().replace(' ', '-')} Your Project Name, /absolute/path/to/documents`

**Example:**
`/{workflow_name.lower().replace(' ', '-')} Botany Farm 2022-2023, /home/ygg/Workspace/RegenAI/regen-registry-review-mcp/examples/22-23`

This will create a new session and run the workflow in one step!

## Option 2: Use Initialize First

Create a session with `/initialize` first:

`/initialize Botany Farm 2022-2023, /path/to/documents`

Then run this workflow again.
"""
        return None, False, text_content(usage_message)

    # Use most recent session
    return sessions[0]["session_id"], True, None


def validate_session_exists(session_id: str, workflow_name: str) -> list[TextContent] | None:
    """Validate that a session exists and return error if not.

    Args:
        session_id: Session ID to validate
        workflow_name: Name of workflow (for error messages)

    Returns:
        Error response if session doesn't exist, None if valid
    """
    state_manager = StateManager(session_id)
    if not state_manager.exists():
        # Session doesn't exist - show available sessions
        import asyncio
        sessions = asyncio.run(session_tools.list_sessions())
        session_list = format_session_list(sessions)

        return format_error(
            "Session Not Found",
            f"Session ID: {session_id}\n\nThis session does not exist.",
            f"Available sessions:\n\n{session_list}\n\nCreate a new session using /initialize."
        )

    return None


def format_workflow_header(
    stage: str,
    session_id: str,
    project_name: str,
    auto_selected: bool = False
) -> str:
    """Format standard workflow stage header.

    Args:
        stage: Workflow stage name (e.g., "Document Discovery")
        session_id: Session ID
        project_name: Project name
        auto_selected: Whether session was auto-selected

    Returns:
        Formatted header string
    """
    lines = [f"# Registry Review - {stage}", ""]

    if auto_selected:
        lines.append("ℹ️  **Auto-selected most recent session**")
        lines.append("")

    lines.append(f"**Session ID:** `{session_id}`")
    lines.append(f"**Project:** {project_name}")
    lines.append("")
    lines.append("---")
    lines.append("")

    return "\n".join(lines)


def format_next_steps_section(steps: list[str], title: str = "Next Steps") -> str:
    """Format a next steps section.

    Args:
        steps: List of step descriptions
        title: Section title

    Returns:
        Formatted next steps string
    """
    lines = ["", "---", "", f"## {title}", ""]
    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")

    return "\n".join(lines)
