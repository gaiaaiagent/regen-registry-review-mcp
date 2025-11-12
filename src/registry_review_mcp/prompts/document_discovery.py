"""Document discovery workflow prompt."""

from mcp.types import TextContent

from ..tools import document_tools
from ..utils.state import StateManager


async def document_discovery_prompt(session_id: str) -> list[TextContent]:
    """Discover and classify all project documents.

    Args:
        session_id: Unique session identifier

    Returns:
        Formatted workflow guidance with results
    """
    # Validate session exists
    state_manager = StateManager(session_id)
    if not state_manager.exists():
        error_message = f"""✗ Error: Session Not Found

Session ID: {session_id}

The specified session does not exist. Create a new session first using the create_session tool.
"""
        return [TextContent(type="text", text=error_message)]

    # Load session data
    session_data = state_manager.read_json("session.json")
    project_name = session_data.get("project_metadata", {}).get("project_name", "Unknown")
    documents_path = session_data.get("project_metadata", {}).get("documents_path")

    # Run discovery
    try:
        results = await document_tools.discover_documents(session_id)

        # Format classification summary
        summary_lines = []
        for doc_type, count in sorted(results["classification_summary"].items()):
            summary_lines.append(f"  • {doc_type}: {count}")

        summary_text = "\n".join(summary_lines) if summary_lines else "  (none)"

        # Format document list
        doc_lines = []
        for idx, doc in enumerate(results["documents"], 1):
            confidence_icon = "✓" if doc["confidence"] >= 0.8 else "~"
            doc_lines.append(
                f"{idx}. {confidence_icon} {doc['filename']}\n"
                f"   Type: {doc['classification']} ({doc['confidence']:.0%} confidence)\n"
                f"   ID: {doc['document_id']}"
            )

        doc_list = "\n\n".join(doc_lines) if doc_lines else "(no documents found)"

        # Determine next steps
        if results["documents_found"] == 0:
            next_steps = """⚠ No documents found in the specified directory.

Please verify:
1. The documents_path is correct
2. The directory contains PDF, GIS, or image files
3. You have read permissions on the directory
"""
        else:
            next_steps = f"""Next Steps:

1. Review the document classification above
2. If any documents are misclassified, you can reclassify them manually
3. Proceed to evidence extraction:
   - Use the /evidence-extraction prompt to map requirements to documents
   - Or continue with the guided workflow

The system found {results['documents_found']} document(s) and is ready to extract evidence.
"""

        response = f"""# Document Discovery Complete

**Project:** {project_name}
**Session:** {session_id}
**Documents Path:** {documents_path}

## Summary

Found **{results['documents_found']} document(s)**

### Classification Breakdown
{summary_text}

## Discovered Documents

{doc_list}

---

{next_steps}
"""

        return [TextContent(type="text", text=response)]

    except Exception as e:
        error_message = f"""✗ Error During Document Discovery

Session: {session_id}
Error: {str(e)}

The document discovery process encountered an error. Please check:
1. The documents_path exists and is accessible
2. You have read permissions on the directory
3. The path contains valid document files

Try loading the session and verifying the documents_path setting.
"""
        return [TextContent(type="text", text=error_message)]
