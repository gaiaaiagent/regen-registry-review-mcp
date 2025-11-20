"""Test factories and builders for reducing test duplication.

This module provides reusable test data builders and factories to eliminate
duplication across test files. Following the Builder pattern for flexible,
readable test setup.
"""

import base64
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from unittest.mock import Mock, AsyncMock

from registry_review_mcp.tools import upload_tools, session_tools


# ============================================================================
# Data Builders - Fluent interface for test data
# ============================================================================

class FileBuilder:
    """Builder for creating test file objects with base64 content."""

    def __init__(self):
        self._filename = "test.pdf"
        self._content_base64 = None
        self._mime_type = None
        self._path = None

    def with_filename(self, filename: str) -> 'FileBuilder':
        """Set the filename."""
        self._filename = filename
        return self

    def with_pdf_content(self, content_suffix: str = "") -> 'FileBuilder':
        """Set PDF content with optional unique suffix."""
        pdf_base = (
            b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>"
            b"\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>"
            b"\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n"
            b"/Resources <</Font <</F1 <</Type /Font\n/Subtype /Type1\n"
            b"/BaseFont /Times-Roman>>>>\n>>/MediaBox [0 0 612 792]\n>>"
            b"\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n"
            b"0000000074 00000 n\n0000000120 00000 n\ntrailer\n<<\n/Size 4\n"
            b"/Root 1 0 R\n>>\nstartxref\n149\n%%EOF"
        )
        content = pdf_base + content_suffix.encode()
        self._content_base64 = base64.b64encode(content).decode('utf-8')
        self._mime_type = "application/pdf"
        return self

    def with_text_content(self, text: str = "Test content") -> 'FileBuilder':
        """Set text file content."""
        self._content_base64 = base64.b64encode(text.encode()).decode('utf-8')
        self._mime_type = "text/plain"
        return self

    def with_path(self, path: str) -> 'FileBuilder':
        """Set file path (for path-based uploads)."""
        self._path = path
        return self

    def build(self) -> Dict[str, Any]:
        """Build the file object."""
        file_obj = {"filename": self._filename}

        if self._content_base64:
            file_obj["content_base64"] = self._content_base64
        if self._mime_type:
            file_obj["mime_type"] = self._mime_type
        if self._path:
            file_obj["path"] = self._path

        return file_obj


class SessionBuilder:
    """Builder for creating test session objects."""

    def __init__(self):
        self._project_name = "Test Project"
        self._files: List[Dict] = []
        self._methodology = "soil-carbon-v1.2.2"
        self._project_id = None
        self._proponent = None
        self._crediting_period = None
        self._documents_path = None  # For path-based sessions

    def with_project_name(self, name: str) -> 'SessionBuilder':
        """Set project name."""
        self._project_name = name
        return self

    def with_documents_path(self, path: str) -> 'SessionBuilder':
        """Set documents path (for path-based sessions like Botany Farm)."""
        self._documents_path = path
        return self

    def with_file(self, file_builder: FileBuilder) -> 'SessionBuilder':
        """Add a file."""
        self._files.append(file_builder.build())
        return self

    def with_files(self, *file_builders: FileBuilder) -> 'SessionBuilder':
        """Add multiple files."""
        for fb in file_builders:
            self._files.append(fb.build())
        return self

    def with_methodology(self, methodology: str) -> 'SessionBuilder':
        """Set methodology."""
        self._methodology = methodology
        return self

    def with_metadata(self, project_id: str = None, proponent: str = None,
                      crediting_period: str = None) -> 'SessionBuilder':
        """Set project metadata."""
        self._project_id = project_id
        self._proponent = proponent
        self._crediting_period = crediting_period
        return self

    async def create(self) -> str:
        """Create the session and return session_id."""
        # Path-based session (like Botany Farm examples)
        if self._documents_path:
            result = await session_tools.create_session(
                project_name=self._project_name,
                documents_path=self._documents_path,
                methodology=self._methodology,
                project_id=self._project_id,
                proponent=self._proponent,
                crediting_period=self._crediting_period,
            )
            return result["session_id"]

        # Upload-based session
        result = await upload_tools.create_session_from_uploads(
            project_name=self._project_name,
            files=self._files,
            methodology=self._methodology,
            project_id=self._project_id,
            proponent=self._proponent,
            crediting_period=self._crediting_period,
        )
        return result["session_id"]

    def build_params(self) -> Dict[str, Any]:
        """Build parameters dict without creating session."""
        return {
            "project_name": self._project_name,
            "files": self._files,
            "methodology": self._methodology,
            "project_id": self._project_id,
            "proponent": self._proponent,
            "crediting_period": self._crediting_period,
        }


# ============================================================================
# Common Test Data - Pre-configured builders
# ============================================================================

def pdf_file(suffix: str = "", filename: str = "test.pdf") -> FileBuilder:
    """Quick factory for PDF file."""
    return FileBuilder().with_filename(filename).with_pdf_content(suffix)


def text_file(content: str = "Test content", filename: str = "test.txt") -> FileBuilder:
    """Quick factory for text file."""
    return FileBuilder().with_filename(filename).with_text_content(content)


def basic_session() -> SessionBuilder:
    """Quick factory for basic session."""
    return SessionBuilder().with_file(pdf_file())


def multi_file_session() -> SessionBuilder:
    """Quick factory for session with multiple files."""
    return SessionBuilder().with_files(
        pdf_file("_1", "file1.pdf"),
        pdf_file("_2", "file2.pdf"),
        text_file("Content", "file3.txt")
    )


def path_based_session(documents_path: str, project_name: str = "Test Path Session") -> SessionBuilder:
    """Quick factory for path-based session (like Botany Farm examples)."""
    return SessionBuilder() \
        .with_project_name(project_name) \
        .with_documents_path(documents_path)


# ============================================================================
# Test Utilities
# ============================================================================

class SessionManager:
    """Context manager for automatic session cleanup."""

    def __init__(self):
        self.sessions: List[str] = []

    async def create(self, builder: SessionBuilder) -> str:
        """Create session and track for cleanup."""
        session_id = await builder.create()
        self.sessions.append(session_id)
        return session_id

    async def cleanup(self):
        """Clean up all tracked sessions."""
        for session_id in self.sessions:
            try:
                await session_tools.delete_session(session_id)
            except Exception:
                pass
        self.sessions.clear()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with cleanup."""
        await self.cleanup()


# ============================================================================
# Assertion Helpers
# ============================================================================

class SessionAssertions:
    """Common assertions for session validation."""

    @staticmethod
    def assert_valid_session_id(session_id: str):
        """Assert session ID has correct format."""
        assert session_id.startswith("session-")
        assert len(session_id) > 10

    @staticmethod
    def assert_session_result(result: Dict, expected_files: int = 1):
        """Assert session creation result is valid."""
        assert result["success"] is True
        assert "session_id" in result
        SessionAssertions.assert_valid_session_id(result["session_id"])
        assert len(result["files_saved"]) == expected_files
        assert "temp_directory" in result

    @staticmethod
    def assert_temp_directory_exists(result: Dict):
        """Assert temp directory was created and contains files."""
        temp_dir = Path(result["temp_directory"])
        assert temp_dir.exists()
        for filename in result["files_saved"]:
            assert (temp_dir / filename).exists()

    @staticmethod
    async def assert_workflow_stage_completed(session_id: str, stage: str):
        """Assert specific workflow stage is completed."""
        session = await session_tools.load_session(session_id)
        assert session["workflow_progress"].get(stage) == "completed", \
            f"Expected stage '{stage}' to be completed, got: {session['workflow_progress'].get(stage)}"

    @staticmethod
    async def assert_session_status(session_id: str, expected_status: str):
        """Assert session has expected status."""
        session = await session_tools.load_session(session_id)
        assert session["status"] == expected_status, \
            f"Expected status '{expected_status}', got: {session['status']}'"


# ============================================================================
# LLM Mock Helpers - For testing LLM extractors
# ============================================================================

def unique_doc_name(test_name: str) -> str:
    """Generate unique document name for testing to avoid cache collisions."""
    return f"{test_name}_{int(time.time() * 1000000)}.pdf"


def create_llm_mock_response(json_content: str, use_code_fence: bool = True) -> Mock:
    """Create a mock LLM response with JSON content.

    Args:
        json_content: The JSON string to return
        use_code_fence: Whether to wrap in markdown code fence

    Returns:
        Mock response object
    """
    if use_code_fence:
        text = f"```json\n{json_content}\n```"
    else:
        text = json_content

    mock_response = Mock()
    mock_response.content = [Mock(text=text)]
    return mock_response


def create_llm_client_mock(response: Mock) -> AsyncMock:
    """Create a mock LLM client that returns the given response.

    Args:
        response: Mock response from create_llm_mock_response()

    Returns:
        AsyncMock client
    """
    mock_client = AsyncMock()
    mock_client.messages.create.return_value = response
    return mock_client


def mock_date_extraction(value: str, confidence: float = 0.95,
                         field_type: str = "project_start_date") -> str:
    """Create JSON for a valid date extraction response."""
    return f'''[{{
        "value": "{value}",
        "field_type": "{field_type}",
        "source": "test document",
        "confidence": {confidence},
        "reasoning": "Test extraction"
    }}]'''


def mock_tenure_extraction(value: str, confidence: float = 0.95) -> str:
    """Create JSON for a valid land tenure extraction response."""
    return f'''[{{
        "value": "{value}",
        "field_type": "land_tenure",
        "source": "test document",
        "confidence": {confidence},
        "reasoning": "Test extraction"
    }}]'''


def mock_project_id_extraction(value: str, confidence: float = 0.95) -> str:
    """Create JSON for a valid project ID extraction response."""
    return f'''[{{
        "value": "{value}",
        "field_type": "project_id",
        "source": "test document",
        "confidence": {confidence},
        "reasoning": "Test extraction"
    }}]'''


# ============================================================================
# Example Usage Patterns (for documentation)
# ============================================================================

"""
# Basic usage:
async with SessionManager() as manager:
    session_id = await manager.create(basic_session())
    # ... test code ...
    # auto-cleanup on exit

# Custom session:
session = await SessionBuilder() \\
    .with_project_name("Custom Project") \\
    .with_file(pdf_file("_unique")) \\
    .with_metadata(project_id="C06-001") \\
    .create()

# Multiple files:
session = await multi_file_session().create()

# Assertions:
result = await upload_tools.create_session_from_uploads(...)
SessionAssertions.assert_session_result(result, expected_files=3)
SessionAssertions.assert_temp_directory_exists(result)
"""
