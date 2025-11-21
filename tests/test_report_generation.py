"""Tests for report generation tools."""

import pytest
from datetime import datetime
from pathlib import Path

from registry_review_mcp.tools import report_tools, session_tools, document_tools, evidence_tools
from registry_review_mcp.models.report import (
    ReportMetadata,
    RequirementFinding,
    ValidationFinding,
    ReportSummary,
)


@pytest.mark.usefixtures("cleanup_sessions")
class TestMarkdownReportGeneration:
    """Test Markdown report generation."""

    async def test_generate_markdown_report_structure(self, tmp_path):
        """Test that Markdown report has correct structure."""
        # Create session with mock data
        session = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        # Generate report (will use placeholder data)
        result = await report_tools.generate_review_report(
            session_id=session_id,
            format="markdown"
        )

        assert result["format"] == "markdown"
        assert "report_path" in result
        assert result["session_id"] == session_id

        # Verify file was created
        report_path = Path(result["report_path"])
        assert report_path.exists()
        assert report_path.suffix == ".md"

        # Read and check content structure
        content = report_path.read_text()
        assert "# Registry Agent Review" in content or "Registry Review" in content
        assert "Project Metadata" in content or "Project:" in content
        assert "Summary" in content

    async def test_markdown_report_includes_requirements(self, tmp_path):
        """Test that Markdown report includes requirement findings."""
        session = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        result = await report_tools.generate_review_report(
            session_id=session_id,
            format="markdown"
        )

        content = Path(result["report_path"]).read_text()

        # Should have requirements section
        assert "Requirements" in content or "REQ-" in content

    async def test_markdown_report_includes_citations(self, tmp_path):
        """Test that Markdown report includes page citations."""
        example_path = Path(__file__).parent.parent / "examples" / "22-23"

        if not example_path.exists():
            pytest.skip("Botany Farm example data not available")

        session = await session_tools.create_session(
            project_name="Botany Farm",
            documents_path=str(example_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        # Discover documents and extract evidence
        await document_tools.discover_documents(session_id)
        await evidence_tools.extract_all_evidence(session_id)

        # Generate report
        result = await report_tools.generate_review_report(
            session_id=session_id,
            format="markdown"
        )

        content = Path(result["report_path"]).read_text()

        # Should have page citations (format: "Page X" or "DOC-XXX, Page X")
        assert "Page" in content or "page" in content


@pytest.mark.usefixtures("cleanup_sessions")
class TestJSONReportGeneration:
    """Test JSON report generation."""

    async def test_generate_json_report_structure(self, tmp_path):
        """Test that JSON report has correct structure."""
        session = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        result = await report_tools.generate_review_report(
            session_id=session_id,
            format="json"
        )

        assert result["format"] == "json"
        assert "report_path" in result

        # Verify file was created
        report_path = Path(result["report_path"])
        assert report_path.exists()
        assert report_path.suffix == ".json"

        # Read and validate JSON structure
        import json
        with open(report_path) as f:
            report_data = json.load(f)

        assert "metadata" in report_data
        assert "summary" in report_data
        assert "requirements" in report_data
        assert isinstance(report_data["requirements"], list)

    async def test_json_report_is_valid_json(self, tmp_path):
        """Test that generated JSON is valid and parseable."""
        session = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        result = await report_tools.generate_review_report(
            session_id=session_id,
            format="json"
        )

        # This should not raise an exception
        import json
        with open(result["report_path"]) as f:
            report_data = json.load(f)

        # Basic validation
        assert report_data["metadata"]["session_id"] == session_id
        assert "project_name" in report_data["metadata"]


@pytest.mark.usefixtures("cleanup_sessions")
class TestReportFormatting:
    """Test report formatting and content."""

    async def test_format_requirement_finding(self, tmp_path):
        """Test formatting of individual requirement findings."""
        # Test the helper function for formatting requirement findings
        finding = {
            "requirement_id": "REQ-001",
            "requirement_text": "Test requirement text",
            "status": "covered",
            "confidence": 0.95,
            "mapped_documents": [{"document_id": "DOC-001"}],
            "evidence_snippets": [
                {
                    "text": "Test evidence",
                    "page": 5,
                    "section": "1.1 Introduction"
                }
            ]
        }

        formatted = report_tools.format_requirement_markdown(finding)

        # format_requirement_markdown returns a list of strings
        formatted_text = "\n".join(formatted)

        assert "REQ-001" in formatted_text
        assert "covered" in formatted_text.lower() or "✅" in formatted_text
        assert "0.95" in formatted_text or "95" in formatted_text

    async def test_format_validation_summary(self, tmp_path):
        """Test formatting of validation summary."""
        validations = {
            "date_alignments": [
                {"status": "pass", "message": "Test pass"}
            ],
            "land_tenure": [
                {"status": "warning", "message": "Test warning"}
            ],
            "project_ids": [
                {"status": "fail", "message": "Test fail"}
            ]
        }

        formatted = report_tools.format_validation_summary_markdown(validations)

        # format_validation_summary_markdown returns a list of strings
        formatted_text = "\n".join(formatted)

        assert "pass" in formatted_text.lower() or "✅" in formatted_text
        assert "warning" in formatted_text.lower() or "⚠" in formatted_text
        assert "fail" in formatted_text.lower() or "❌" in formatted_text


@pytest.mark.usefixtures("cleanup_sessions")
class TestReportExport:
    """Test report export functionality."""

    async def test_export_both_formats(self, tmp_path):
        """Test exporting report in both Markdown and JSON."""
        session = await session_tools.create_session(
            project_name="Test Project",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        # Generate both formats
        md_result = await report_tools.generate_review_report(
            session_id=session_id,
            format="markdown"
        )

        json_result = await report_tools.generate_review_report(
            session_id=session_id,
            format="json"
        )

        # Both should exist
        assert Path(md_result["report_path"]).exists()
        assert Path(json_result["report_path"]).exists()

        # Should be different files
        assert md_result["report_path"] != json_result["report_path"]


class TestCompleteWorkflow:
    """Test complete report generation workflow."""

    async def test_full_report_workflow(self, tmp_path):
        """Test complete workflow from session to report."""
        example_path = Path(__file__).parent.parent / "examples" / "22-23"

        if not example_path.exists():
            pytest.skip("Botany Farm example data not available")

        # Initialize
        session = await session_tools.create_session(
            project_name="Botany Farm",
            documents_path=str(example_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        # Discovery
        docs = await document_tools.discover_documents(session_id)
        assert docs["documents_found"] > 0

        # Extraction
        evidence = await evidence_tools.extract_all_evidence(session_id)
        assert evidence["requirements_total"] == 23

        # Report Generation
        report = await report_tools.generate_review_report(
            session_id=session_id,
            format="markdown"
        )

        assert Path(report["report_path"]).exists()

        content = Path(report["report_path"]).read_text()
        assert "Botany Farm" in content
        assert len(content) > 1000  # Should be substantial
