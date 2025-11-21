"""Session management tools for creating, loading, and updating review sessions."""

import uuid
from datetime import datetime, timezone
from typing import Any

from ..config.settings import settings
from ..models.errors import SessionNotFoundError
from ..models.schemas import (
    ProjectMetadata,
    Session,
    SessionStatistics,
    WorkflowProgress,
)
from ..utils.state import StateManager, get_session_or_raise


def generate_session_id() -> str:
    """Generate a unique session ID.
    """
    return f"session-{uuid.uuid4().hex[:12]}"


async def create_session(
    project_name: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
    submission_date: datetime | None = None,
    documents_path: str | None = None,  # Deprecated: Use add_documents() instead
) -> dict[str, Any]:
    """Create a new registry review session.

    Stage 1: Initialize session with metadata only.
    No document sources are added yet - use add_documents() for that.

    Args:
        project_name: Name of the project being reviewed
        methodology: Methodology identifier (default: soil-carbon-v1.2.2)
        project_id: Optional project ID (e.g., C06-4997)
        proponent: Optional project proponent name
        crediting_period: Optional crediting period
        submission_date: Optional submission date
        documents_path: DEPRECATED - Use add_documents() instead

    Returns:
        Session creation result with session_id and metadata
    """
    import json

    # Validate inputs via Pydantic
    project_metadata = ProjectMetadata(
        project_name=project_name,
        project_id=project_id,
        crediting_period=crediting_period,
        submission_date=submission_date,
        methodology=methodology,
        proponent=proponent,
        documents_path=documents_path,  # Backward compatibility
    )

    # Generate session
    session_id = generate_session_id()
    now = datetime.now(timezone.utc)

    # Load checklist requirements count
    checklist_path = settings.get_checklist_path(methodology)
    requirements_count = 0
    if checklist_path.exists():
        with open(checklist_path, "r") as f:
            checklist_data = json.load(f)
        requirements_count = len(checklist_data.get("requirements", []))

    # Create session with empty document_sources list
    session = Session(
        session_id=session_id,
        created_at=now,
        updated_at=now,
        status="initialized",
        project_metadata=project_metadata,
        document_sources=[],  # Start with no sources
        workflow_progress=WorkflowProgress(initialize="completed"),
        statistics=SessionStatistics(requirements_total=requirements_count),
    )

    # Persist to disk
    state_manager = StateManager(session_id)
    state_manager.write_json("session.json", session.model_dump(mode="json"))

    # Initialize empty structures
    state_manager.write_json("documents.json", {"documents": []})
    state_manager.write_json("findings.json", {"findings": []})

    return {
        "session_id": session_id,
        "project_name": project_name,
        "created_at": now.isoformat(),
        "methodology": methodology,
        "requirements_total": requirements_count,
        "message": f"Session created successfully for project: {project_name}",
    }


async def load_session(session_id: str) -> dict[str, Any]:
    """Load an existing session.
    """
    state_manager = get_session_or_raise(session_id)
    session_data = state_manager.read_json("session.json")
    return session_data


async def update_session_state(
    session_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Update session state with partial changes.
    """
    state_manager = get_session_or_raise(session_id)

    # Add updated timestamp
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Atomic update
    session_data = state_manager.update_json("session.json", updates)

    return session_data


async def list_sessions() -> list[dict[str, Any]]:
    """List all available sessions.
    """
    sessions = []

    for session_dir in settings.sessions_dir.iterdir():
        if session_dir.is_dir() and (session_dir / "session.json").exists():
            try:
                state_manager = StateManager(session_dir.name)
                session_data = state_manager.read_json("session.json")

                sessions.append(
                    {
                        "session_id": session_data.get("session_id"),
                        "project_name": session_data.get("project_metadata", {}).get(
                            "project_name"
                        ),
                        "created_at": session_data.get("created_at"),
                        "updated_at": session_data.get("updated_at"),
                        "status": session_data.get("status"),
                        "methodology": session_data.get("project_metadata", {}).get("methodology"),
                        "workflow_progress": session_data.get("workflow_progress", {}),
                        "statistics": session_data.get("statistics", {}),
                        "project_metadata": session_data.get("project_metadata", {}),
                    }
                )
            except Exception:
                # Skip corrupted sessions
                continue

    # Sort by creation date (newest first)
    sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return sessions


async def delete_session(session_id: str) -> dict[str, Any]:
    """Delete a session and all its data.
    """
    import shutil

    state_manager = get_session_or_raise(session_id)

    # Remove entire session directory
    shutil.rmtree(state_manager.session_dir)

    return {
        "session_id": session_id,
        "status": "deleted",
        "message": f"Session {session_id} has been deleted",
    }


async def list_example_projects() -> dict[str, Any]:
    """List example projects available in the examples directory.
    """
    from pathlib import Path

    # Get examples directory relative to settings
    examples_dir = settings.data_dir.parent / "examples"

    if not examples_dir.exists():
        return {
            "projects_found": 0,
            "projects": [],
            "message": "No examples directory found",
        }

    projects = []
    for item in sorted(examples_dir.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            # Count files in the directory
            file_count = sum(1 for f in item.rglob('*') if f.is_file())
            projects.append({
                "name": item.name,
                "path": str(item.absolute()),
                "file_count": file_count,
            })

    return {
        "projects_found": len(projects),
        "projects": projects,
        "message": f"Found {len(projects)} example project(s)" if projects else "No example projects found",
    }
