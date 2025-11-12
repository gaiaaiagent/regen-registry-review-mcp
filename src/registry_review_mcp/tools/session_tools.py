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
from ..utils.state import StateManager


def generate_session_id() -> str:
    """Generate a unique session ID.

    Returns:
        UUID-based session identifier
    """
    return f"session-{uuid.uuid4().hex[:12]}"


async def create_session(
    project_name: str,
    documents_path: str,
    methodology: str = "soil-carbon-v1.2.2",
    project_id: str | None = None,
    proponent: str | None = None,
    crediting_period: str | None = None,
    submission_date: datetime | None = None,
) -> dict[str, Any]:
    """Create a new registry review session.

    Args:
        project_name: Name of the project being reviewed
        documents_path: Absolute path to directory containing project documents
        methodology: Methodology identifier (default: soil-carbon-v1.2.2)
        project_id: Project ID if known (e.g., C06-4997)
        proponent: Name of project proponent
        crediting_period: Crediting period description
        submission_date: Date of submission

    Returns:
        Dictionary with session_id and creation metadata

    Raises:
        ValueError: If documents_path does not exist or is invalid
    """
    # Validate inputs via Pydantic
    project_metadata = ProjectMetadata(
        project_name=project_name,
        project_id=project_id,
        crediting_period=crediting_period,
        submission_date=submission_date,
        methodology=methodology,
        proponent=proponent,
        documents_path=documents_path,
    )

    # Generate session
    session_id = generate_session_id()
    now = datetime.now(timezone.utc)

    session = Session(
        session_id=session_id,
        created_at=now,
        updated_at=now,
        status="initialized",
        project_metadata=project_metadata,
        workflow_progress=WorkflowProgress(),
        statistics=SessionStatistics(),
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
        "documents_path": project_metadata.documents_path,
        "methodology": methodology,
        "message": f"Session created successfully for project: {project_name}",
    }


async def load_session(session_id: str) -> dict[str, Any]:
    """Load an existing session.

    Args:
        session_id: Unique session identifier

    Returns:
        Complete session data

    Raises:
        SessionNotFoundError: If session does not exist
    """
    state_manager = StateManager(session_id)

    if not state_manager.exists():
        raise SessionNotFoundError(
            f"Session not found: {session_id}",
            details={"session_id": session_id},
        )

    session_data = state_manager.read_json("session.json")
    return session_data


async def update_session_state(
    session_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    """Update session state with partial changes.

    Args:
        session_id: Unique session identifier
        updates: Dictionary of fields to update (supports nested updates)

    Returns:
        Updated session data

    Raises:
        SessionNotFoundError: If session does not exist
    """
    state_manager = StateManager(session_id)

    if not state_manager.exists():
        raise SessionNotFoundError(
            f"Session not found: {session_id}",
            details={"session_id": session_id},
        )

    # Add updated timestamp
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Atomic update
    session_data = state_manager.update_json("session.json", updates)

    return session_data


async def list_sessions() -> list[dict[str, Any]]:
    """List all available sessions.

    Returns:
        List of session summaries with metadata
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
                        "status": session_data.get("status"),
                        "methodology": session_data.get("project_metadata", {}).get("methodology"),
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

    Args:
        session_id: Unique session identifier

    Returns:
        Confirmation message

    Raises:
        SessionNotFoundError: If session does not exist
    """
    import shutil

    state_manager = StateManager(session_id)

    if not state_manager.exists():
        raise SessionNotFoundError(
            f"Session not found: {session_id}",
            details={"session_id": session_id},
        )

    # Remove entire session directory
    shutil.rmtree(state_manager.session_dir)

    return {
        "session_id": session_id,
        "status": "deleted",
        "message": f"Session {session_id} has been deleted",
    }
