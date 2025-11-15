"""Initialize workflow - Stage 1 of registry review."""

from pathlib import Path
from mcp.types import TextContent

from ..config.settings import settings
from ..tools import session_tools
from ..utils.state import StateManager


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

    # Normalize documents path for comparison
    normalized_path = str(Path(documents_path).absolute())

    # Check for duplicate sessions by scanning sessions directory
    duplicates = []
    if settings.sessions_dir.exists():
        for session_dir in settings.sessions_dir.iterdir():
            if session_dir.is_dir() and (session_dir / "session.json").exists():
                try:
                    state_manager = StateManager(session_dir.name)
                    session_data = state_manager.read_json("session.json")
                    session_project = session_data.get("project_metadata", {})
                    session_path = str(Path(session_project.get("documents_path", "")).absolute())

                    if (session_project.get("project_name") == project_name and
                        session_path == normalized_path):
                        duplicates.append({
                            "session_id": session_data.get("session_id"),
                            "created_at": session_data.get("created_at"),
                            "status": session_data.get("status")
                        })
                except Exception:
                    # Skip corrupted sessions
                    continue

    # If duplicates found, show warning and options
    if duplicates:
        duplicate = duplicates[0]  # Show most recent
        message = f"""# ⚠️ Existing Session Found

A session already exists for this project:

**Session ID:** `{duplicate['session_id']}`
**Project:** {project_name}
**Documents:** {documents_path}
**Created:** {duplicate.get('created_at', 'Unknown')}
**Status:** {duplicate.get('status', 'Unknown')}

---

## Options

### 1. Resume Existing Session (Recommended)

Continue working on the existing session:

Simply run the next workflow stage (the system auto-selects most recent session):

`/document-discovery`

Or specify the session explicitly:

`/document-discovery {duplicate['session_id']}`

### 2. View Session Status

Check the current state of the session:

`load_session {duplicate['session_id']}`

### 3. Delete and Start Fresh

If you want to start over, first delete the old session:

`delete_session {duplicate['session_id']}`

Then run `/initialize` again.

### 4. Create Duplicate Anyway (Not Recommended)

If you really need multiple sessions for the same project, use the tool directly:

`create_session {project_name}, {documents_path}, soil-carbon-v1.2.2, force=true`

⚠️ Warning: Having multiple sessions for the same project can lead to confusion about which is the active review.

---

**Tip:** Most users want to resume the existing session. Just run `/document-discovery` to continue where you left off!
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

        # Mark initialize stage as completed
        state_manager = StateManager(session_id)
        session_data = state_manager.read_json("session.json")
        session_data["workflow_progress"]["initialize"] = "completed"
        state_manager.write_json("session.json", session_data)

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
