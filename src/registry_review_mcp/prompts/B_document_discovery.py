"""Document discovery workflow prompt."""

from mcp.types import TextContent

from ..tools import document_tools, session_tools
from ..utils.state import StateManager


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
    auto_selected = False

    # Case 1: Session ID provided explicitly
    if session_id:
        auto_selected = False

    # Case 2: Project details provided - create new session
    elif project_name and documents_path:
        try:
            result = await session_tools.create_session(
                project_name=project_name,
                documents_path=documents_path,
                methodology="soil-carbon-v1.2.2"
            )
            session_id = result["session_id"]
            auto_selected = False
        except Exception as e:
            error_message = f"""# ❌ Error Creating Session

Failed to create session: {str(e)}

Please check your inputs and try again.
"""
            return [TextContent(type="text", text=error_message)]

    # Case 3: No parameters - try to use most recent session
    else:
        sessions = await session_tools.list_sessions()

        if not sessions:
            # No sessions exist - provide usage help
            error_message = """# Registry Review Workflow - Document Discovery

No review sessions found. You can either:

## Option 1: Create Session & Discover (Recommended)

Provide project details directly to this prompt:

`/document-discovery Your Project Name, /absolute/path/to/documents`

**Example:**
`/document-discovery Botany Farm 2022-2023, /home/ygg/Workspace/RegenAI/regen-registry-review-mcp/examples/22-23`

This will:
1. ✅ Create a new session
2. ✅ Discover all documents
3. ✅ Classify files by type

All in one step!

## Option 2: Use Initialize First

Alternatively, create a session with `/initialize` first:

`/initialize Botany Farm 2022-2023, /path/to/documents`

Then run `/document-discovery` again.
"""
            return [TextContent(type="text", text=error_message)]

        # Use most recent session
        session_id = sessions[0]["session_id"]
        auto_selected = True

    # Validate session exists
    state_manager = StateManager(session_id)
    if not state_manager.exists():
        # List available sessions to help user
        sessions = await session_tools.list_sessions()
        session_list = "\n".join([f"  • {s['session_id']} - {s.get('project_name', 'Unknown')}"
                                   for s in sessions])

        error_message = f"""✗ Error: Session Not Found

Session ID: {session_id}

This session does not exist. Available sessions:

{session_list if sessions else "  (none)"}

Create a new session using the create_session tool.
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

        # Format errors if any occurred
        error_section = ""
        if results.get("error_count", 0) > 0:
            error_lines = []
            for error in results.get("errors", []):
                recovery = "\n".join([f"   - {step}" for step in error["recovery_steps"]])
                error_lines.append(
                    f"**File:** {error['filename']}\n"
                    f"**Error:** {error['message']}\n"
                    f"**Recovery Steps:**\n{recovery}"
                )

            error_section = f"""

## ⚠️ Processing Errors

{results['error_count']} file(s) could not be processed:

{chr(10).join([f"{i}. {err}" for i, err in enumerate(error_lines, 1)])}

---

These errors won't prevent the review from continuing, but you may want to resolve them to ensure complete coverage.

"""

        # Add auto-selection notice if applicable
        auto_notice = ""
        if auto_selected:
            auto_notice = f"\n*Note: Auto-selected most recent session*\n"

        response = f"""# Document Discovery Complete
{auto_notice}
**Project:** {project_name}
**Session:** {session_id}
**Documents Path:** {documents_path}

## Summary

Found **{results['documents_found']} document(s)**{f" ({results['error_count']} error(s))" if results.get('error_count', 0) > 0 else ""}

### Classification Breakdown
{summary_text}

## Discovered Documents

{doc_list}
{error_section}
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
