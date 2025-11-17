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
        # Ensure no sessions exist
        from src.registry_review_mcp.config.settings import settings
        import shutil

        sessions_dir = settings.sessions_dir
        if sessions_dir.exists():
            # Clean ALL sessions to guarantee no-session state
            shutil.rmtree(sessions_dir, ignore_errors=True)
            sessions_dir.mkdir(parents=True, exist_ok=True)

        # Call without session_id when no sessions exist
        result = await document_discovery_prompt(session_id=None)

        # Should provide helpful guidance
        assert len(result) == 1
        text = result[0].text
        assert "Registry Review" in text or "No sessions found" in text
        assert ("Option" in text or "initialize" in text.lower())  # Multiple options or guidance provided
        assert "/document-discovery" in text or "/initialize" in text

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
            assert "Document Discovery Complete" in text
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

        # Extract session_id from result
        import re
        match = re.search(r"Session ID: (session-[a-f0-9]+)", result)
        assert match, "Should include session ID in result"
        session_id = match.group(1)

        try:
            # Verify result contains expected information
            assert "Review Started Successfully" in result
            assert "Document Discovery Complete" in result
            assert "Found" in result and "document(s)" in result
            assert "Classification Summary:" in result

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

        # Should create session but fail gracefully on discovery
        # (The session is still created even if documents_path is invalid)
        assert "Session ID:" in result or "Error" in result
