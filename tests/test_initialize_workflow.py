"""Test suite for initialize workflow and session state management.

This test file catches critical bugs found during development:
1. Initialize workflow not marking stage as "completed"
2. Checklist requirements not loaded into statistics
3. StateManager.update_json() not handling nested dot notation
4. Session state inconsistencies between creation and initialization
"""

import json
import re
import pytest
from pathlib import Path

from registry_review_mcp.tools import session_tools
from registry_review_mcp.prompts import A_initialize
from registry_review_mcp.utils.state import StateManager
from registry_review_mcp.config.settings import settings


# Test Helpers

def extract_session_id(result_text: str) -> str:
    """Extract session ID from initialize prompt result text.

    Args:
        result_text: Result text from initialize_prompt() containing session ID

    Returns:
        Session ID string (e.g., 'session-abc123')

    Raises:
        AssertionError: If session ID not found in expected format
    """
    match = re.search(r'`(session-[a-f0-9]+)`', result_text)
    assert match, "Session ID not found in result text"
    return match.group(1)


def get_expected_requirements_count() -> int:
    """Get expected requirements count from soil-carbon-v1.2.2 checklist.

    Returns:
        Number of requirements in the checklist
    """
    checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)
    return len(checklist_data["requirements"])


class StateManagerCleanup:
    """Context manager for StateManager cleanup in tests."""

    def __init__(self, session_id: str):
        self.state_manager = StateManager(session_id)

    def __enter__(self):
        return self.state_manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        import shutil
        if self.state_manager.session_dir.exists():
            shutil.rmtree(self.state_manager.session_dir)


class TestInitializeWorkflow:
    """Test the initialize workflow prompt and session creation."""

    @pytest.mark.asyncio
    async def test_initialize_creates_session_with_requirements(self, tmp_path):
        """Test that initialize prompt creates session with requirements_total set.

        This test catches the bug where initialize_prompt() creates a session
        but doesn't load the checklist requirements count into statistics.
        """
        result = await A_initialize.initialize_prompt("Test Project", str(tmp_path))
        session_id = extract_session_id(result[0].text)
        session_data = await session_tools.load_session(session_id)
        expected_count = get_expected_requirements_count()

        # BUG CHECK 1: requirements_total should NOT be 0
        assert session_data["statistics"]["requirements_total"] > 0, \
            "Initialize workflow must load checklist requirements count"

        # BUG CHECK 2: requirements_total should match checklist
        assert session_data["statistics"]["requirements_total"] == expected_count, \
            f"requirements_total should be {expected_count}, got {session_data['statistics']['requirements_total']}"

    @pytest.mark.asyncio
    async def test_initialize_marks_stage_completed(self, tmp_path):
        """Test that initialize prompt marks the 'initialize' stage as completed.

        This test catches the bug where the initialize stage remains 'pending'
        after successful session creation.
        """
        result = await A_initialize.initialize_prompt("Test Project", str(tmp_path))
        session_id = extract_session_id(result[0].text)
        session_data = await session_tools.load_session(session_id)

        # BUG CHECK: initialize workflow stage should be 'completed'
        assert session_data["workflow_progress"]["initialize"] == "completed", \
            "Initialize workflow must mark 'initialize' stage as 'completed'"

    @pytest.mark.asyncio
    async def test_initialize_shows_correct_requirements_count(self, tmp_path):
        """Test that initialize success message shows the actual requirements count.

        This test verifies the message uses the dynamic count, not a hardcoded value.
        """
        result = await A_initialize.initialize_prompt("Test Project", str(tmp_path))
        expected_count = get_expected_requirements_count()

        # BUG CHECK: Message should contain actual count (not hardcoded "23")
        assert f"({expected_count} requirements)" in result[0].text, \
            f"Success message should show '({expected_count} requirements)'"


class TestStateManagerNestedUpdates:
    """Test StateManager nested update functionality."""

    def test_update_json_nested_dot_notation(self, tmp_path):
        """Test that update_json handles nested updates with dot notation.

        This test catches the bug where StateManager.update_json() creates
        top-level keys like "workflow_progress.initialize" instead of updating
        the nested structure data["workflow_progress"]["initialize"].
        """
        with StateManagerCleanup("test-nested-update") as state_manager:
            # Write initial data
            initial_data = {
                "status": "initialized",
                "workflow_progress": {
                    "initialize": "pending",
                    "document_discovery": "pending"
                },
                "statistics": {"requirements_total": 0}
            }
            state_manager.write_json("test.json", initial_data)

            # Update with dot notation
            updates = {
                "workflow_progress.initialize": "completed",
                "statistics.requirements_total": 23
            }
            result = state_manager.update_json("test.json", updates)

            # BUG CHECK 1: Should NOT create top-level keys
            assert "workflow_progress.initialize" not in result, \
                "update_json must NOT create top-level keys with dots"
            assert "statistics.requirements_total" not in result, \
                "update_json must NOT create top-level keys with dots"

            # BUG CHECK 2: Should update nested structure
            assert result["workflow_progress"]["initialize"] == "completed", \
                "update_json must update nested workflow_progress.initialize"
            assert result["statistics"]["requirements_total"] == 23, \
                "update_json must update nested statistics.requirements_total"

            # BUG CHECK 3: Should preserve other nested values
            assert result["workflow_progress"]["document_discovery"] == "pending", \
                "update_json must preserve untouched nested values"

    def test_update_json_mixed_updates(self, tmp_path):
        """Test update_json with both top-level and nested updates."""
        with StateManagerCleanup("test-mixed-update") as state_manager:
            initial_data = {
                "status": "initialized",
                "workflow_progress": {"initialize": "pending"},
                "count": 0
            }
            state_manager.write_json("test.json", initial_data)

            # Mix of top-level and nested updates
            updates = {
                "status": "active",
                "workflow_progress.initialize": "completed",
                "count": 42
            }
            result = state_manager.update_json("test.json", updates)

            # Verify all updates applied correctly
            assert result["status"] == "active"
            assert result["workflow_progress"]["initialize"] == "completed"
            assert result["count"] == 42

    def test_update_json_creates_missing_nested_structure(self, tmp_path):
        """Test that update_json creates missing nested structures."""
        with StateManagerCleanup("test-create-nested") as state_manager:
            initial_data = {"status": "initialized"}
            state_manager.write_json("test.json", initial_data)

            # Update non-existent nested path
            updates = {
                "workflow_progress.initialize": "completed",
                "statistics.requirements_total": 23
            }
            result = state_manager.update_json("test.json", updates)

            # Verify nested structures were created
            assert "workflow_progress" in result
            assert result["workflow_progress"]["initialize"] == "completed"
            assert "statistics" in result
            assert result["statistics"]["requirements_total"] == 23


class TestSessionConsistency:
    """Test session state consistency across workflows."""

    @pytest.mark.asyncio
    async def test_new_session_has_all_workflow_stages(self, tmp_path):
        """Test that new sessions have all 7 workflow stages defined."""
        result = await A_initialize.initialize_prompt("Test Project", str(tmp_path))
        session_id = extract_session_id(result[0].text)
        session_data = await session_tools.load_session(session_id)

        # Verify all 7 stages exist
        expected_stages = [
            "initialize",
            "document_discovery",
            "evidence_extraction",
            "cross_validation",
            "report_generation",
            "human_review",
            "completion"  # Fixed: was "complete", should be "completion"
        ]

        for stage in expected_stages:
            assert stage in session_data["workflow_progress"], \
                f"Session must define workflow stage '{stage}'"

    @pytest.mark.asyncio
    async def test_initialize_stage_completed_after_creation(self, tmp_path):
        """Test that initialize stage is completed immediately after session creation."""
        result = await A_initialize.initialize_prompt("Test Project", str(tmp_path))
        session_id = extract_session_id(result[0].text)

        # Read session file directly to verify state
        state_manager = StateManager(session_id)
        session_data = state_manager.read_json("session.json")

        # BUG CHECK: initialize must be completed
        assert session_data["workflow_progress"]["initialize"] == "completed", \
            "Initialize stage must be 'completed' immediately after session creation"

    @pytest.mark.asyncio
    async def test_all_statistics_initialized(self, tmp_path):
        """Test that all statistics fields are initialized properly."""
        result = await A_initialize.initialize_prompt("Test Project", str(tmp_path))
        session_id = extract_session_id(result[0].text)
        session_data = await session_tools.load_session(session_id)
        stats = session_data["statistics"]

        # Verify all required statistics fields exist
        required_fields = [
            "documents_found",
            "requirements_total",
            "requirements_covered",
            "requirements_partial",
            "requirements_missing",
            "validations_passed",
            "validations_failed"
        ]

        for field in required_fields:
            assert field in stats, f"Statistics must include field '{field}'"

        # BUG CHECK: requirements_total must be set to actual count, not 0
        assert stats["requirements_total"] > 0, \
            "requirements_total must be loaded from checklist during initialization"
