"""Regression tests for critical bug fix: Silent failure in error handling decorator.

Bug: The @with_error_handling decorator was catching exceptions and returning
error strings instead of re-raising them. This violated the MCP protocol contract
and caused failures to appear as successes to MCP clients.

Fix: Decorator now re-raises exceptions while still logging them.

Incident: Session creation for "Test B" (session-6543bffc727a) reported success
but the session directory was never created, causing silent failure.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from registry_review_mcp.tools import session_tools
from registry_review_mcp.models.errors import SessionNotFoundError


class TestErrorPropagation:
    """Verify that errors propagate correctly through the decorator."""

    @pytest.mark.asyncio
    async def test_session_creation_failure_raises_exception(self, tmp_path):
        """REGRESSION: Verify session creation failures raise exceptions, not return error strings.

        This test ensures that when session creation fails (e.g., permission error,
        disk full, etc.), an exception is raised rather than returning an error string.

        The bug would have caused this test to fail because it would have returned
        a string like "✗ Error in create_session: [PermissionError] ..." instead
        of raising the exception.
        """
        # Simulate filesystem error by using a non-writable path
        with patch('registry_review_mcp.tools.session_tools.StateManager') as mock_manager:
            # Make write_json raise a permission error
            mock_instance = Mock()
            mock_instance.write_json.side_effect = PermissionError("Permission denied")
            mock_manager.return_value = mock_instance

            # Should raise PermissionError, not return error string
            with pytest.raises(PermissionError, match="Permission denied"):
                await session_tools.create_session(project_name="Test Project")

    @pytest.mark.asyncio
    async def test_session_load_failure_raises_exception(self):
        """Verify that loading non-existent session raises SessionNotFoundError."""
        # Should raise SessionNotFoundError, not return error string
        with pytest.raises(SessionNotFoundError, match="Session not found"):
            await session_tools.load_session("nonexistent-session-id")

    @pytest.mark.asyncio
    async def test_successful_operation_returns_result(self, tmp_path, monkeypatch):
        """Verify that successful operations return results normally."""
        # Set up temp sessions directory via environment and new Settings instance
        from registry_review_mcp.config.settings import Settings
        from registry_review_mcp.tools import session_tools as st_module
        from registry_review_mcp.utils import state as state_module

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        # Create a new settings instance with the temp directory
        new_settings = Settings(sessions_dir=sessions_dir)

        # Patch settings in both modules that use it
        monkeypatch.setattr(st_module, "settings", new_settings)
        monkeypatch.setattr(state_module, "settings", new_settings)

        result = await session_tools.create_session(
            project_name="Test Project",
            methodology="soil-carbon-v1.2.2"
        )

        # Should return dict result, not error string
        assert isinstance(result, dict)
        assert result["project_name"] == "Test Project"
        assert "session_id" in result
        assert result["message"].startswith("Session created successfully")

        # Verify no error prefix
        assert not str(result).startswith("✗ Error")

    @pytest.mark.asyncio
    async def test_error_logged_before_raising(self, tmp_path):
        """Verify that errors are logged with full context before being re-raised.

        Note: This test verifies the exception is raised correctly.
        The logging happens in the MCP server decorator layer, which is tested
        separately through integration tests.
        """
        with patch('registry_review_mcp.tools.session_tools.StateManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.write_json.side_effect = IOError("Disk full")
            mock_manager.return_value = mock_instance

            # The important part: exception should be raised, not swallowed
            with pytest.raises(IOError, match="Disk full"):
                await session_tools.create_session(project_name="Test")


class TestMCPProtocolCompliance:
    """Verify MCP protocol contract: tools return results OR raise exceptions."""

    @pytest.mark.asyncio
    async def test_tool_never_returns_error_string(self, tmp_path):
        """Verify tools never return error strings like '✗ Error: ...'

        This is the core MCP protocol compliance test. Tools must either:
        1. Return a valid result (dict, string, etc.), OR
        2. Raise an exception

        They must NEVER return error strings that could be misinterpreted as success.
        """
        # Test various failure scenarios
        test_cases = [
            ("Permission denied", PermissionError("Permission denied")),
            ("Disk full", IOError("Disk full")),
            ("Invalid path", ValueError("Invalid path")),
            ("Lock timeout", TimeoutError("Could not acquire lock")),
        ]

        for error_msg, exception in test_cases:
            with patch('registry_review_mcp.tools.session_tools.StateManager') as mock_manager:
                mock_instance = Mock()
                mock_instance.write_json.side_effect = exception
                mock_manager.return_value = mock_instance

                # Should raise the exception
                with pytest.raises(type(exception)):
                    result = await session_tools.create_session(project_name="Test")

                    # If we get here, the tool returned instead of raising
                    # Check if it's an error string (the bug)
                    if isinstance(result, str) and result.startswith("✗ Error"):
                        pytest.fail(
                            f"Tool returned error string instead of raising exception: {result}"
                        )


class TestIncidentRecreation:
    """Recreate the exact incident that triggered this bug fix."""

    @pytest.mark.asyncio
    async def test_session_6543bffc727a_incident(self, tmp_path):
        """Recreate the 'Test B' session creation failure incident.

        Incident timeline:
        - 11:01 AM: User creates session "Test B"
        - create_session fails (likely I/O error)
        - Decorator catches exception, returns error string
        - ElizaOS receives string, interprets as success
        - ElizaOS tells user: "Session created successfully"
        - ElizaOS stores session_id: session-6543bffc727a
        - Later: User uploads fail (session doesn't exist)

        With the fix:
        - create_session fails
        - Decorator logs error and re-raises exception
        - ElizaOS receives exception
        - ElizaOS tells user: "Error creating session: [details]"
        - User knows something went wrong
        """
        # Simulate the exact failure scenario
        with patch('registry_review_mcp.tools.session_tools.StateManager') as mock_manager:
            # Simulate I/O error during session creation
            mock_instance = Mock()
            mock_instance.write_json.side_effect = OSError("No space left on device")
            mock_manager.return_value = mock_instance

            # With the bug: would return "✗ Error in create_session: ..."
            # With the fix: raises OSError
            with pytest.raises(OSError, match="No space left on device"):
                result = await session_tools.create_session(
                    project_name="Test B",
                    methodology="soil-carbon-v1.2.2"
                )

                # If we reach here, the bug is back
                if isinstance(result, str) and "Error" in result:
                    pytest.fail(
                        "CRITICAL: Bug regression detected! Tool returned error string "
                        f"instead of raising exception: {result}"
                    )
