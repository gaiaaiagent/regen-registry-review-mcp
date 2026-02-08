"""Tests for report generation tools."""

import pytest
from datetime import datetime
from pathlib import Path

from registry_review_mcp.tools import report_tools, session_tools, document_tools, evidence_tools, mapping_tools
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

    @pytest.mark.expensive
    async def test_markdown_report_includes_citations(self, tmp_path):
        """Test that Markdown report includes page citations (requires LLM extraction)."""
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
        await mapping_tools.map_all_requirements(session_id)
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
        assert "Covered" in formatted_text
        assert "0.95" in formatted_text or "95" in formatted_text
        assert "✅" not in formatted_text

    async def test_format_validation_summary(self, tmp_path):
        """Test formatting of validation summary uses text labels, not emojis."""
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
        formatted_text = "\n".join(formatted)

        # Should use text labels
        assert "**PASS:**" in formatted_text
        assert "**WARNING:**" in formatted_text
        assert "**FAIL:**" in formatted_text

        # Should NOT contain emojis
        assert "✅" not in formatted_text
        assert "⚠️" not in formatted_text
        assert "❌" not in formatted_text
        assert "🚩" not in formatted_text

    async def test_format_validation_summary_flagged(self, tmp_path):
        """Test that flagged validations use [Review] label instead of emoji."""
        validations = {
            "date_alignments": [
                {"status": "fail", "message": "Date mismatch", "flagged_for_review": True}
            ],
        }

        formatted = report_tools.format_validation_summary_markdown(validations)
        formatted_text = "\n".join(formatted)

        assert "[Review]" in formatted_text
        assert "🚩" not in formatted_text


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

    @pytest.mark.expensive
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

        # Mapping
        await mapping_tools.map_all_requirements(session_id)

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


class TestBeccaFeedbackItems:
    """Tests for Becca's feedback items (task-12).

    Issue 1: Section numbers in citations
    Issue 2: Value vs Evidence distinction
    Issue 3: Supplementary evidence support
    Issue 4: Evidence text in Comments column
    Issue 5: Sentence-boundary truncation
    Issue 6: Project ID in document references
    """

    def test_format_citation_with_section_and_page(self):
        """Issue 1: Citations should include section numbers."""
        from registry_review_mcp.tools.report_tools import _format_citation

        # Both section and page
        result = _format_citation("Project Plan.pdf", "3.2", 17)
        assert result == "Project Plan.pdf (Section 3.2, p.17)"

        # Only section
        result = _format_citation("Project Plan.pdf", "3.2", None)
        assert result == "Project Plan.pdf (Section 3.2)"

        # Only page
        result = _format_citation("Project Plan.pdf", None, 17)
        assert result == "Project Plan.pdf (p.17)"

        # Neither - just doc name
        result = _format_citation("Project Plan.pdf", None, None)
        assert result == "Project Plan.pdf"

    def test_extract_value_from_structured_fields(self):
        """Issue 2: Value should come from extracted_value or structured_fields."""
        from registry_review_mcp.tools.report_tools import _extract_value

        # Test with explicit value field
        snippet = {
            "text": "Some long evidence text that would normally be truncated.",
            "structured_fields": {"value": "Nicholas Denman"}
        }
        result = _extract_value(snippet)
        assert result == "Nicholas Denman"

        # Test with extracted_value field
        snippet = {
            "text": "Some long evidence text.",
            "structured_fields": {},
            "extracted_value": "10 years"
        }
        result = _extract_value(snippet)
        assert result == "10 years"

        # Test with owner_name field
        snippet = {
            "text": "Some text.",
            "structured_fields": {"owner_name": "John Smith"}
        }
        result = _extract_value(snippet)
        assert result == "John Smith"

        # Fallback to first sentence when no structured data
        snippet = {
            "text": "The crediting period is 10 years. This is additional detail.",
            "structured_fields": {}
        }
        result = _extract_value(snippet)
        assert result == "The crediting period is 10 years."

    def test_format_submitted_material_with_supplementary(self):
        """Issue 3: Supplementary evidence should be included."""
        from registry_review_mcp.tools.report_tools import _format_submitted_material

        snippets = [
            {"document_name": "Project Plan.pdf", "page": 5, "section": "1.1",
             "text": "Primary evidence.", "structured_fields": {"value": "Primary value"}},
            {"document_name": "Supporting Doc.pdf", "page": 10, "section": "2.3",
             "text": "Second evidence."},
            {"document_name": "Third Doc.pdf", "page": 15, "section": None,
             "text": "Third evidence."},
        ]

        submitted, evidence = _format_submitted_material(snippets, project_id="C06-123")

        # Check primary documentation
        assert "**Primary Documentation:**" in submitted
        assert "[C06-123]" in submitted
        assert "Section 1.1" in submitted

        # Check supplementary evidence
        assert "**Supplementary:**" in submitted
        assert "Supporting Doc.pdf" in submitted
        assert "Third Doc.pdf" in submitted

        # Check value extracted (no **Value:** label, just the text)
        assert "Primary value" in submitted
        assert "**Value:**" not in submitted

    def test_format_submitted_material_returns_evidence_separately(self):
        """Issue 4: Evidence text should be separate for Comments column."""
        from registry_review_mcp.tools.report_tools import _format_submitted_material

        snippets = [
            {"document_name": "Doc.pdf", "page": 1, "section": None,
             "text": "This is the evidence text.", "structured_fields": {}}
        ]

        submitted, evidence = _format_submitted_material(snippets)

        # Evidence should NOT be in submitted material
        assert "**Evidence:**" not in submitted

        # Evidence should be returned separately
        assert evidence == "This is the evidence text."

    def test_truncate_at_sentence_boundary(self):
        """Issue 5: Truncation should respect sentence boundaries."""
        from registry_review_mcp.tools.report_tools import _truncate_at_sentence

        # Should truncate at sentence end
        text = "First sentence. Second sentence. Third sentence is much longer."
        result = _truncate_at_sentence(text, max_length=35)
        assert result == "First sentence. Second sentence."

        # Should not truncate mid-sentence
        assert "Third" not in result
        assert not result.endswith("...")

        # Short text should not be truncated
        short = "Short text."
        assert _truncate_at_sentence(short, max_length=100) == short

    def test_project_id_in_document_references(self):
        """Issue 6: Project ID should be included in document references."""
        from registry_review_mcp.tools.report_tools import _format_submitted_material

        snippets = [
            {"document_name": "Project Plan.pdf", "page": 1, "section": None,
             "text": "Evidence.", "structured_fields": {}}
        ]

        # With project ID
        submitted, _ = _format_submitted_material(snippets, project_id="C06-456")
        assert "[C06-456] Project Plan.pdf" in submitted

        # Without project ID
        submitted, _ = _format_submitted_material(snippets, project_id=None)
        assert "[" not in submitted  # No brackets
        assert "Project Plan.pdf" in submitted

    def test_no_evidence_returns_placeholder(self):
        """Test empty snippets case."""
        from registry_review_mcp.tools.report_tools import _format_submitted_material

        submitted, evidence = _format_submitted_material([])
        assert submitted == "_No evidence found_"
        assert evidence == ""


class TestReportOutputQuality:
    """Tests for report output quality (Phase 1c).

    Ensures reports are professional — no emojis, no confusing labels.
    """

    def test_no_emojis_in_markdown_report(self):
        """Verify no emoji Unicode characters appear in markdown report output."""
        from registry_review_mcp.models.report import ReviewReport, ReportMetadata, ReportSummary, RequirementFinding

        report = ReviewReport(
            metadata=ReportMetadata(
                session_id="test-session",
                project_name="Test Project",
                methodology="soil-carbon-v1.2.2",
                generated_at=datetime.now(),
                report_format="markdown",
            ),
            summary=ReportSummary(
                requirements_total=3,
                requirements_covered=1,
                requirements_partial=1,
                requirements_missing=1,
                requirements_flagged=0,
                overall_coverage=0.33,
                validations_total=2,
                validations_passed=1,
                validations_failed=1,
                validations_warning=0,
                documents_reviewed=2,
                total_evidence_snippets=5,
                items_for_human_review=2,
            ),
            requirements=[
                RequirementFinding(
                    requirement_id="REQ-001", requirement_text="Test covered",
                    category="General", status="covered", confidence=0.95,
                    documents_referenced=1, snippets_found=2,
                    evidence_summary="Strong evidence", page_citations=[],
                    human_review_required=False,
                ),
                RequirementFinding(
                    requirement_id="REQ-002", requirement_text="Test partial",
                    category="General", status="partial", confidence=0.6,
                    documents_referenced=1, snippets_found=1,
                    evidence_summary="Partial evidence", page_citations=[],
                    human_review_required=True,
                ),
                RequirementFinding(
                    requirement_id="REQ-003", requirement_text="Test missing",
                    category="General", status="missing", confidence=0.0,
                    documents_referenced=0, snippets_found=0,
                    evidence_summary="No evidence", page_citations=[],
                    human_review_required=True,
                ),
            ],
            validations=[],
            items_for_review=["REQ-002: Test partial..."],
            next_steps=["Review flagged items"],
        )

        content = report_tools.format_markdown_report(report)

        # These specific emojis must not appear anywhere in report output
        forbidden_emojis = ["✅", "❌", "⚠️", "🚩", "❓"]
        for emoji in forbidden_emojis:
            assert emoji not in content, f"Found forbidden emoji {emoji!r} in report output"

    def test_submitted_material_no_value_label(self):
        """Verify _format_submitted_material() does not prefix with **Value:**."""
        from registry_review_mcp.tools.report_tools import _format_submitted_material

        snippets = [
            {"document_name": "Doc.pdf", "page": 5, "section": "2.1",
             "text": "The project covers 500 hectares.",
             "structured_fields": {"value": "500 hectares"}}
        ]

        submitted, _ = _format_submitted_material(snippets)

        assert "**Value:**" not in submitted
        assert "500 hectares" in submitted

    def test_section_headers_no_emojis(self):
        """Verify section headers use plain text, not emoji prefixes."""
        from registry_review_mcp.models.report import ReviewReport, ReportMetadata, ReportSummary, RequirementFinding

        report = ReviewReport(
            metadata=ReportMetadata(
                session_id="test", project_name="Test",
                methodology="test", generated_at=datetime.now(),
                report_format="markdown",
            ),
            summary=ReportSummary(
                requirements_total=1, requirements_covered=1,
                requirements_partial=0, requirements_missing=0,
                requirements_flagged=0, overall_coverage=1.0,
                validations_total=0, validations_passed=0,
                validations_failed=0, validations_warning=0,
                documents_reviewed=1, total_evidence_snippets=1,
                items_for_human_review=0,
            ),
            requirements=[
                RequirementFinding(
                    requirement_id="REQ-001", requirement_text="Test",
                    category="General", status="covered", confidence=0.95,
                    documents_referenced=1, snippets_found=1,
                    evidence_summary="Found", page_citations=[],
                    human_review_required=False,
                ),
            ],
            validations=[], items_for_review=[], next_steps=[],
        )

        content = report_tools.format_markdown_report(report)

        assert "## Covered Requirements" in content
        assert "## ✅" not in content

    def test_checklist_row_approved_no_emoji(self):
        """Verify _format_checklist_row uses plain ⚠ (not ⚠️ emoji) in Approved column."""
        from registry_review_mcp.tools.report_tools import _format_checklist_row

        # Partial status triggers the warning symbol
        req = RequirementFinding(
            requirement_id="REQ-001", requirement_text="Test partial requirement",
            category="General", status="partial", confidence=0.6,
            documents_referenced=1, snippets_found=1,
            evidence_summary="Partial evidence", page_citations=[],
            human_review_required=True,
        )
        row = _format_checklist_row(req, {})

        # Should use plain Unicode ⚠ (U+26A0), not emoji ⚠️ (U+26A0 + U+FE0F)
        assert "⚠" in row
        assert "⚠️" not in row
        assert "✅" not in row
        assert "❌" not in row
