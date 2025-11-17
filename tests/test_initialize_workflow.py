"""Test suite for initialize workflow and session state management.

This test file catches critical bugs found during development:
1. Initialize workflow not marking stage as "completed"
2. Checklist requirements not loaded into statistics
3. StateManager.update_json() not handling nested dot notation
4. Session state inconsistencies between creation and initialization
"""

import json
import pytest
from pathlib import Path

from registry_review_mcp.tools import session_tools
from registry_review_mcp.prompts import A_initialize
from registry_review_mcp.utils.state import StateManager
from registry_review_mcp.config.settings import settings


class TestInitializeWorkflow:
    """Test the initialize workflow prompt and session creation."""

    @pytest.mark.asyncio
    async def test_initialize_creates_session_with_requirements(self, tmp_path):
        """Test that initialize prompt creates session with requirements_total set.

        This test catches the bug where initialize_prompt() creates a session
        but doesn't load the checklist requirements count into statistics.
        """
        # Setup
        project_name = "Test Project"
        documents_path = str(tmp_path)

        # Execute initialize
        result = await A_initialize.initialize_prompt(project_name, documents_path)

        # Extract session ID from result text
        result_text = result[0].text
        assert "Session ID" in result_text

        # Parse session ID (format: **Session ID:** `session-xxxx`)
        import re
        match = re.search(r'`(session-[a-f0-9]+)`', result_text)
        assert match, "Session ID not found in result"
        session_id = match.group(1)

        # Load session and verify requirements_total is set
        session_data = await session_tools.load_session(session_id)

        # BUG CHECK 1: requirements_total should NOT be 0
        assert session_data["statistics"]["requirements_total"] > 0, \
            "Initialize workflow must load checklist requirements count"

        # BUG CHECK 2: requirements_total should match checklist
        checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
        with open(checklist_path, "r") as f:
            checklist_data = json.load(f)
        expected_count = len(checklist_data["requirements"])

        assert session_data["statistics"]["requirements_total"] == expected_count, \
            f"requirements_total should be {expected_count}, got {session_data['statistics']['requirements_total']}"

    @pytest.mark.asyncio
    async def test_initialize_marks_stage_completed(self, tmp_path):
        """Test that initialize prompt marks the 'initialize' stage as completed.

        This test catches the bug where the initialize stage remains 'pending'
        after successful session creation.
        """
        # Setup
        project_name = "Test Project"
        documents_path = str(tmp_path)

        # Execute initialize
        result = await A_initialize.initialize_prompt(project_name, documents_path)

        # Extract session ID
        import re
        match = re.search(r'`(session-[a-f0-9]+)`', result[0].text)
        session_id = match.group(1)

        # Load session and verify initialize stage is completed
        session_data = await session_tools.load_session(session_id)

        # BUG CHECK: initialize workflow stage should be 'completed'
        assert session_data["workflow_progress"]["initialize"] == "completed", \
            "Initialize workflow must mark 'initialize' stage as 'completed'"

    @pytest.mark.asyncio
    async def test_initialize_shows_correct_requirements_count(self, tmp_path):
        """Test that initialize success message shows the actual requirements count.

        This test verifies the message uses the dynamic count, not a hardcoded value.
        """
        # Setup
        project_name = "Test Project"
        documents_path = str(tmp_path)

        # Execute initialize
        result = await A_initialize.initialize_prompt(project_name, documents_path)
        result_text = result[0].text

        # Load expected count from checklist
        checklist_path = settings.get_checklist_path("soil-carbon-v1.2.2")
        with open(checklist_path, "r") as f:
            checklist_data = json.load(f)
        expected_count = len(checklist_data["requirements"])

        # BUG CHECK: Message should contain actual count (not hardcoded "23")
        assert f"({expected_count} requirements)" in result_text, \
            f"Success message should show '({expected_count} requirements)'"


class TestStateManagerNestedUpdates:
    """Test StateManager nested update functionality."""

    def test_update_json_nested_dot_notation(self, tmp_path):
        """Test that update_json handles nested updates with dot notation.

        This test catches the bug where StateManager.update_json() creates
        top-level keys like "workflow_progress.initialize" instead of updating
        the nested structure data["workflow_progress"]["initialize"].
        """
        # Create a test session
        session_id = "test-nested-update"
        state_manager = StateManager(session_id)

        # Write initial data
        initial_data = {
            "status": "initialized",
            "workflow_progress": {
                "initialize": "pending",
                "document_discovery": "pending"
            },
            "statistics": {
                "requirements_total": 0
            }
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

        # Cleanup
        import shutil
        if state_manager.session_dir.exists():
            shutil.rmtree(state_manager.session_dir)

    def test_update_json_mixed_updates(self, tmp_path):
        """Test update_json with both top-level and nested updates."""
        session_id = "test-mixed-update"
        state_manager = StateManager(session_id)

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

        # Cleanup
        import shutil
        if state_manager.session_dir.exists():
            shutil.rmtree(state_manager.session_dir)

    def test_update_json_creates_missing_nested_structure(self, tmp_path):
        """Test that update_json creates missing nested structures."""
        session_id = "test-create-nested"
        state_manager = StateManager(session_id)

        initial_data = {
            "status": "initialized"
        }
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

        # Cleanup
        import shutil
        if state_manager.session_dir.exists():
            shutil.rmtree(state_manager.session_dir)


class TestSessionConsistency:
    """Test session state consistency across workflows."""

    @pytest.mark.asyncio
    async def test_new_session_has_all_workflow_stages(self, tmp_path):
        """Test that new sessions have all 7 workflow stages defined."""
        project_name = "Test Project"
        documents_path = str(tmp_path)

        result = await A_initialize.initialize_prompt(project_name, documents_path)

        import re
        match = re.search(r'`(session-[a-f0-9]+)`', result[0].text)
        session_id = match.group(1)

        session_data = await session_tools.load_session(session_id)

        # Verify all 7 stages exist
        expected_stages = [
            "initialize",
            "document_discovery",
            "evidence_extraction",
            "cross_validation",
            "report_generation",
            "human_review",
            "complete"
        ]

        for stage in expected_stages:
            assert stage in session_data["workflow_progress"], \
                f"Session must define workflow stage '{stage}'"

    @pytest.mark.asyncio
    async def test_initialize_stage_completed_after_creation(self, tmp_path):
        """Test that initialize stage is completed immediately after session creation."""
        project_name = "Test Project"
        documents_path = str(tmp_path)

        result = await A_initialize.initialize_prompt(project_name, documents_path)

        import re
        match = re.search(r'`(session-[a-f0-9]+)`', result[0].text)
        session_id = match.group(1)

        # Read session file directly to verify state
        state_manager = StateManager(session_id)
        session_data = state_manager.read_json("session.json")

        # BUG CHECK: initialize must be completed
        assert session_data["workflow_progress"]["initialize"] == "completed", \
            "Initialize stage must be 'completed' immediately after session creation"

    @pytest.mark.asyncio
    async def test_all_statistics_initialized(self, tmp_path):
        """Test that all statistics fields are initialized properly."""
        project_name = "Test Project"
        documents_path = str(tmp_path)

        result = await A_initialize.initialize_prompt(project_name, documents_path)

        import re
        match = re.search(r'`(session-[a-f0-9]+)`', result[0].text)
        session_id = match.group(1)

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
