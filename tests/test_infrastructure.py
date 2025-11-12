"""Infrastructure tests for Registry Review MCP.

Tests for configuration, state management, and basic session operations.
"""

import pytest
import json
from pathlib import Path

from registry_review_mcp.config.settings import Settings
from registry_review_mcp.models.schemas import Session, ProjectMetadata
from registry_review_mcp.models.errors import SessionNotFoundError, SessionLockError
from registry_review_mcp.utils.state import StateManager
from registry_review_mcp.utils.cache import Cache
from registry_review_mcp.tools import session_tools


class TestSettings:
    """Test configuration management."""

    def test_settings_initialization(self, test_settings):
        """Test that settings initialize correctly."""
        assert test_settings.log_level == "INFO"
        assert test_settings.data_dir.exists()
        assert test_settings.checklists_dir.exists()
        assert test_settings.sessions_dir.exists()
        assert test_settings.cache_dir.exists()

    def test_get_checklist_path(self, test_settings):
        """Test checklist path generation."""
        path = test_settings.get_checklist_path("soil-carbon-v1.2.2")
        assert path.name == "soil-carbon-v1.2.2.json"
        assert path.parent == test_settings.checklists_dir

    def test_get_session_path(self, test_settings):
        """Test session path generation."""
        path = test_settings.get_session_path("test-session-123")
        assert path.name == "test-session-123"
        assert path.parent == test_settings.sessions_dir


class TestStateManager:
    """Test atomic state management."""

    def test_state_manager_initialization(self, test_settings):
        """Test state manager initialization."""
        manager = StateManager("test-session")
        assert manager.session_id == "test-session"
        assert "test-session" in str(manager.session_dir)

    def test_write_and_read_json(self, test_settings):
        """Test writing and reading JSON files."""
        manager = StateManager("test-session")

        test_data = {"key": "value", "number": 42}
        manager.write_json("test.json", test_data)

        read_data = manager.read_json("test.json")
        assert read_data == test_data

    def test_read_nonexistent_file(self, test_settings):
        """Test reading nonexistent file raises error."""
        manager = StateManager("test-session")

        with pytest.raises(SessionNotFoundError):
            manager.read_json("nonexistent.json")

    def test_update_json(self, test_settings):
        """Test atomic JSON updates."""
        manager = StateManager("test-session")

        # Create initial data
        initial_data = {"count": 0, "status": "pending"}
        manager.write_json("test.json", initial_data)

        # Update
        updated_data = manager.update_json("test.json", {"count": 1})

        assert updated_data["count"] == 1
        assert updated_data["status"] == "pending"  # Preserved

    def test_exists(self, test_settings):
        """Test checking file existence."""
        manager = StateManager("test-session-exists")

        # Ensure clean state (cleanup fixture may not have run yet)
        if manager.exists():
            import shutil
            shutil.rmtree(manager.session_dir, ignore_errors=True)

        assert not manager.exists()  # Session doesn't exist yet

        manager.write_json("test.json", {})
        assert manager.exists()  # Session exists now
        assert manager.exists("test.json")  # File exists
        assert not manager.exists("other.json")  # Other file doesn't exist


class TestCache:
    """Test caching utilities."""

    def test_cache_set_and_get(self, test_settings):
        """Test setting and getting cached values."""
        cache = Cache("test")

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_cache_get_nonexistent(self, test_settings):
        """Test getting nonexistent key returns default."""
        cache = Cache("test")

        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"

    def test_cache_exists(self, test_settings):
        """Test checking if key exists."""
        cache = Cache("test-exists")

        # Ensure clean state
        cache.delete("key1")

        assert not cache.exists("key1")

        cache.set("key1", "value1")
        assert cache.exists("key1")

    def test_cache_delete(self, test_settings):
        """Test deleting cached values."""
        cache = Cache("test")

        cache.set("key1", "value1")
        assert cache.exists("key1")

        cache.delete("key1")
        assert not cache.exists("key1")

    def test_cache_clear(self, test_settings):
        """Test clearing all cache entries."""
        cache = Cache("test")

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        count = cache.clear()
        assert count == 3
        assert not cache.exists("key1")
        assert not cache.exists("key2")
        assert not cache.exists("key3")


class TestSessionTools:
    """Test session management tools."""

    @pytest.mark.asyncio
    async def test_create_session(self, test_settings, example_documents_path):
        """Test creating a new session."""
        result = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )

        assert "session_id" in result
        assert result["project_name"] == "Test Project"
        assert "created_at" in result

        # Verify session files were created
        manager = StateManager(result["session_id"])
        assert manager.exists("session.json")
        assert manager.exists("documents.json")
        assert manager.exists("findings.json")

    @pytest.mark.asyncio
    async def test_load_session(self, test_settings, example_documents_path):
        """Test loading an existing session."""
        # Create session
        create_result = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(example_documents_path),
        )
        session_id = create_result["session_id"]

        # Load session
        loaded = await session_tools.load_session(session_id)

        assert loaded["session_id"] == session_id
        assert loaded["project_metadata"]["project_name"] == "Test Project"

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, test_settings):
        """Test loading nonexistent session raises error."""
        with pytest.raises(SessionNotFoundError):
            await session_tools.load_session("nonexistent-session")

    @pytest.mark.asyncio
    async def test_update_session_state(self, test_settings, example_documents_path):
        """Test updating session state."""
        # Create session
        create_result = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(example_documents_path),
        )
        session_id = create_result["session_id"]

        # Update state
        updated = await session_tools.update_session_state(
            session_id,
            {"status": "in_progress"},
        )

        assert updated["status"] == "in_progress"
        assert "updated_at" in updated

    @pytest.mark.asyncio
    async def test_list_sessions(self, test_settings, example_documents_path):
        """Test listing all sessions."""
        # Create multiple sessions
        await session_tools.create_session(
            project_name="Project 1",
            documents_path=str(example_documents_path),
        )
        await session_tools.create_session(
            project_name="Project 2",
            documents_path=str(example_documents_path),
        )

        # List sessions
        sessions = await session_tools.list_sessions()

        assert len(sessions) >= 2
        assert all("session_id" in s for s in sessions)
        assert all("project_name" in s for s in sessions)

    @pytest.mark.asyncio
    async def test_delete_session(self, test_settings, example_documents_path):
        """Test deleting a session."""
        # Create session
        create_result = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(example_documents_path),
        )
        session_id = create_result["session_id"]

        # Verify it exists
        manager = StateManager(session_id)
        assert manager.exists()

        # Delete session
        result = await session_tools.delete_session(session_id)

        assert result["status"] == "deleted"
        assert not manager.exists()


class TestChecklist:
    """Test checklist loading."""

    def test_checklist_exists(self):
        """Test that soil carbon checklist exists."""
        checklist_path = Path(__file__).parent.parent / "data" / "checklists" / "soil-carbon-v1.2.2.json"
        assert checklist_path.exists()

    def test_checklist_structure(self):
        """Test checklist has correct structure."""
        checklist_path = Path(__file__).parent.parent / "data" / "checklists" / "soil-carbon-v1.2.2.json"

        with open(checklist_path, "r") as f:
            checklist = json.load(f)

        # Verify top-level fields
        assert "methodology_id" in checklist
        assert "requirements" in checklist
        assert checklist["methodology_id"] == "soil-carbon-v1.2.2"

        # Verify requirements structure
        assert len(checklist["requirements"]) >= 20
        req = checklist["requirements"][0]
        assert "requirement_id" in req
        assert "category" in req
        assert "requirement_text" in req
        assert "source" in req
        assert "accepted_evidence" in req
        assert "mandatory" in req
        assert "validation_type" in req
