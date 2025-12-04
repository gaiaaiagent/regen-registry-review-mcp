"""Tests for user experience improvements."""

import pytest

from registry_review_mcp.prompts.B_document_discovery import document_discovery_prompt
from registry_review_mcp.tools import session_tools
from registry_review_mcp.server import start_review


class TestDocumentDiscoveryUX:
    """Test document discovery prompt user experience."""

    @pytest.mark.asyncio
    async def test_no_session_provides_guidance(self, test_settings):
        """Test that calling without session_id when no sessions exist provides helpful guidance."""
        # Use test_settings fixture which already provides isolated temp directory
        # The cleanup_sessions fixture handles isolation - no manual cleanup needed

        # Call without session_id when no sessions exist
        result = await document_discovery_prompt(session_id=None)

        # Should provide helpful guidance
        assert len(result) == 1
        text = result[0].text
        # The message should contain guidance for starting a new session
        assert "Registry Review" in text
        # Should mention either Option(s) for how to proceed or /initialize
        has_options = "Option" in text or "option" in text
        has_initialize = "initialize" in text.lower()
        assert has_options or has_initialize, f"Expected guidance with options or initialize, got: {text[:200]}..."

    @pytest.mark.asyncio
    async def test_auto_selects_most_recent_session(self, test_settings, example_documents_path):
        """Test that calling without session_id auto-selects most recent session."""
        # Create a session
        session = await session_tools.create_session(
            project_name="Auto-Select Test",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        try:
            # Call without session_id - should auto-select
            result = await document_discovery_prompt(session_id=None)

            # Should have auto-selected and run discovery
            assert len(result) == 1
            text = result[0].text
            assert "Discovery Complete" in text  # More flexible - matches actual message
            assert "Auto-selected most recent session" in text
            assert session_id in text

        finally:
            await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_invalid_session_lists_available(self, test_settings, example_documents_path):
        """Test that invalid session_id shows list of available sessions."""
        # Create a session
        session = await session_tools.create_session(
            project_name="List Test",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        try:
            # Try with invalid session_id
            result = await document_discovery_prompt(session_id="invalid-session-id")

            # Should list available sessions
            assert len(result) == 1
            text = result[0].text
            assert "Session Not Found" in text
            assert "Available sessions:" in text
            assert session_id in text  # Should show the real session

        finally:
            await session_tools.delete_session(session_id)


class TestQuickStart:
    """Test the start_review quick-start tool."""

    @pytest.mark.asyncio
    async def test_start_review_end_to_end(self, test_settings, example_documents_path):
        """Test that start_review creates session and discovers documents."""
        result = await start_review(
            project_name="Quick Start Test",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )

        # Parse JSON result
        import json
        data = json.loads(result)
        assert "session" in data, "Should include session data"
        assert "discovery" in data, "Should include discovery data"

        session_id = data["session"]["session_id"]
        assert session_id.startswith("session-"), "Should have valid session ID"

        try:
            # Verify session contains expected information
            assert data["session"]["project_name"] == "Quick Start Test"
            assert data["discovery"]["documents_found"] >= 0

            # Verify session was created
            session_data = await session_tools.load_session(session_id)
            assert session_data["project_metadata"]["project_name"] == "Quick Start Test"
            assert session_data["workflow_progress"]["document_discovery"] == "completed"

        finally:
            # Cleanup
            await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_start_review_with_invalid_path(self, test_settings):
        """Test that start_review handles invalid paths gracefully."""
        result = await start_review(
            project_name="Invalid Path Test",
            documents_path="/nonexistent/path/to/documents",
            methodology="soil-carbon-v1.2.2",
        )

        # Should create session successfully even with invalid path
        # Discovery will find 0 documents (documents_path is optional now)
        import json
        data = json.loads(result)
        assert "session" in data
        assert "discovery" in data
        assert data["session"]["project_name"] == "Invalid Path Test"
        assert data["discovery"]["documents_found"] == 0
