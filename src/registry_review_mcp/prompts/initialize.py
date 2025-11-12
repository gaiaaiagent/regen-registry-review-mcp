"""Initialize workflow - Stage 1 of registry review."""

from mcp.types import TextContent

from ..tools import session_tools


async def initialize_prompt(
    project_name: str | None = None,
    documents_path: str | None = None
) -> list[TextContent]:
    """Initialize a new registry review session (Stage 1).

    This prompt creates a new review session and prepares it for document discovery.

    Args:
        project_name: Name of the project being reviewed
        documents_path: Absolute path to directory containing project documents

    Returns:
        Session creation results with next step guidance
    """
    # Validate inputs
    if not project_name or not documents_path:
        message = """# Registry Review Workflow - Stage 1: Initialize

Welcome! Let's start a new registry review.

## Usage

Provide your project details:

`/initialize Your Project Name, /absolute/path/to/documents`

## Example

For the Botany Farm example project:

`/initialize Botany Farm 2022-2023, /home/ygg/Workspace/RegenAI/regen-registry-review-mcp/examples/22-23`

## What This Does

This prompt will:
1. ✅ Create a new review session
2. ✅ Load the checklist template
3. ✅ Validate the document path
4. ✅ Set up session state

Then you can proceed to Stage 2: `/document-discovery`
"""
        return [TextContent(type="text", text=message)]

    # Create session
    try:
        result = await session_tools.create_session(
            project_name=project_name,
            documents_path=documents_path,
            methodology="soil-carbon-v1.2.2"
        )

        session_id = result["session_id"]

        # Format success message
        message = f"""# ✅ Registry Review Session Initialized

**Session ID:** `{session_id}`
**Project:** {project_name}
**Documents:** {documents_path}
**Methodology:** Soil Carbon v1.2.2
**Created:** {result['created_at']}

---

## Session Created Successfully

Your review session is ready. The system has:
- ✅ Created session state directory
- ✅ Loaded checklist template (23 requirements)
- ✅ Validated document path
- ✅ Initialized workflow tracking

---

## Next Step: Document Discovery

Run Stage 2 to discover and classify all documents:

`/document-discovery`

This will automatically:
- Scan all files in your project directory
- Classify documents by type (Project Plan, Baseline Report, etc.)
- Extract metadata
- Generate document index

The prompt will auto-select your session - no need to provide the session ID!
"""

        return [TextContent(type="text", text=message)]

    except FileNotFoundError:
        message = f"""# ❌ Error: Document Path Not Found

The path you provided does not exist:
`{documents_path}`

Please check:
- The path is correct
- The path is absolute (not relative)
- You have permission to access the directory

Try again with a valid path.
"""
        return [TextContent(type="text", text=message)]

    except Exception as e:
        message = f"""# ❌ Error Creating Session

An error occurred: {str(e)}

Please check your inputs and try again.
"""
        return [TextContent(type="text", text=message)]
