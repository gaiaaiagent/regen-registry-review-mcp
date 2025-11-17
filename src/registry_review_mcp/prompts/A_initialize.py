"""Initialize workflow - Stage 1 of registry review."""

from pathlib import Path
from mcp.types import TextContent

from ..config.settings import settings
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
        message = """# Registry Review Workflow - Initialize Session

## Usage

`/initialize Project Name, /absolute/path/to/documents`

**Important:** 🔒 One directory = one session. If a session exists for this path, you'll be prompted to resume it.

## Examples

**For the Botany Farm example:**
```
/initialize Botany Farm 2022-2023, /home/ygg/Workspace/RegenAI/regen-registry-review-mcp/examples/22-23
```

**Different name, same directory?** The existing session will be detected:
```
/initialize Botany 22, /home/ygg/.../examples/22-23
→ Will find existing "Botany Farm 2022-2023" session
```

## What This Does

1. ✅ Checks if a session exists for this directory
2. ✅ Creates new session (or prompts you to resume existing)
3. ✅ Loads checklist template (23 requirements)
4. ✅ Validates document path

## Need Help?

- **See available examples:** `list_example_projects`
- **See your sessions:** `list_sessions`
- **Continue existing session:** Just run `/document-discovery`
"""
        return [TextContent(type="text", text=message)]

    # Normalize documents path for comparison
    normalized_path = str(Path(documents_path).absolute())

    # Check for duplicate sessions by documents_path only (one directory = one session)
    duplicates = []
    if settings.sessions_dir.exists():
        for session_dir in settings.sessions_dir.iterdir():
            if session_dir.is_dir() and (session_dir / "session.json").exists():
                try:
                    state_manager = StateManager(session_dir.name)
                    session_data = state_manager.read_json("session.json")
                    session_project = session_data.get("project_metadata", {})
                    session_path = str(Path(session_project.get("documents_path", "")).absolute())

                    # Match by documents_path only - one directory = one session
                    if session_path == normalized_path:
                        duplicates.append({
                            "session_id": session_data.get("session_id"),
                            "project_name": session_project.get("project_name"),
                            "created_at": session_data.get("created_at"),
                            "status": session_data.get("status"),
                            "workflow_progress": session_data.get("workflow_progress", {})
                        })
                except Exception:
                    # Skip corrupted sessions
                    continue

    # If duplicates found, show warning and options
    if duplicates:
        duplicate = duplicates[0]  # Show most recent

        # Check if user provided a different name
        name_changed = duplicate['project_name'] != project_name
        name_note = ""
        if name_changed:
            name_note = f"""
**Note:** You provided the name "{project_name}" but this directory already has an active session named "{duplicate['project_name']}".

🔒 **One Directory = One Session:** Each documents directory can only have one active session to avoid confusion.
"""

        # Get workflow progress
        workflow = duplicate.get('workflow_progress', {})
        completed = [stage for stage, status in workflow.items() if status == 'completed']
        progress_summary = f"{len(completed)}/7 stages completed" if completed else "Not started"

        message = f"""# ⚠️ Session Already Exists for This Directory

{name_note}
**Existing Session:** `{duplicate['session_id']}`
**Project Name:** {duplicate['project_name']}
**Documents Path:** {documents_path}
**Created:** {duplicate.get('created_at', 'Unknown')}
**Progress:** {progress_summary}
**Status:** {duplicate.get('status', 'active')}

---

## What To Do Next

### ✅ Continue Existing Session (Recommended)

Simply run the next workflow stage (auto-selects this session):

`/document-discovery`

Or specify the session explicitly:

`/document-discovery {duplicate['session_id']}`

### 📊 Check Session Status

View full session details:

`load_session {duplicate['session_id']}`

### 🗑️ Start Fresh

Delete the existing session and create a new one:

```
delete_session {duplicate['session_id']}
/initialize {project_name}, {documents_path}
```

---

**Tip:** Use `list_sessions` to see all your active sessions and their progress!
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
        requirements_count = result.get("requirements_total", 0)

        # Note: initialize stage is already marked "completed" by create_session()

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
- ✅ Loaded checklist template ({requirements_count} requirements)
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
