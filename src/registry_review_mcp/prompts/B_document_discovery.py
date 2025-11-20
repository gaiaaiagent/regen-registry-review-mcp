"""Document discovery workflow prompt."""

from mcp.types import TextContent

from ..tools import document_tools
from ..utils.state import StateManager
from .helpers import (
    text_content,
    format_error,
    format_workflow_header,
    format_next_steps_section,
    get_or_select_session,
    validate_session_exists,
)


async def document_discovery_prompt(
    project_name: str | None = None,
    documents_path: str | None = None,
    session_id: str | None = None
) -> list[TextContent]:
    """Discover and classify all project documents.

    Can either use an existing session or create a new one.

    Args:
        project_name: Project name (creates new session if provided with documents_path)
        documents_path: Path to documents (creates new session if provided with project_name)
        session_id: Optional existing session ID (overrides project_name/documents_path)

    Returns:
        Formatted workflow guidance with results
    """
    # Get or select session
    session_id, auto_selected, error = await get_or_select_session(
        session_id, project_name, documents_path, "Document Discovery"
    )

    if error:
        return error

    # Validate session exists
    error = await validate_session_exists(session_id, "Document Discovery")
    if error:
        return error

    # Load session data
    state_manager = StateManager(session_id)
    session_data = state_manager.read_json("session.json")
    project_name = session_data.get("project_metadata", {}).get("project_name", "Unknown")

    # Run discovery
    try:
        results = await document_tools.discover_documents(session_id)

        # Format classification summary
        classification_lines = []
        for doc_type, count in sorted(results["classification_summary"].items()):
            classification_lines.append(f"  - **{doc_type.replace('_', ' ').title()}:** {count} document(s)")

        classification_text = "\n".join(classification_lines) if classification_lines else "  (No documents found)"

        # Build message
        header = format_workflow_header("Document Discovery", session_id, project_name, auto_selected)

        content = f"""## ✅ Discovery Complete

Found and classified **{results['documents_found']} document(s)**:

{classification_text}

All documents have been:
- ✅ Scanned and indexed
- ✅ Classified by type
- ✅ Metadata extracted
- ✅ Saved to document index
"""

        next_steps = format_next_steps_section([
            "Review the document classifications above",
            "Run evidence extraction: `/evidence-extraction`",
            "Or view session status: `load_session {session_id}`"
        ], "Next Step: Evidence Extraction")

        message = header + content + next_steps

        return text_content(message)

    except Exception as e:
        return format_error(
            "Document Discovery Failed",
            f"An error occurred during document discovery: {str(e)}",
            "Please check the session and try again, or contact support if the issue persists."
        )
