"""Tests for document processing (Phase 2)."""

import pytest
from pathlib import Path

from registry_review_mcp.tools import session_tools, document_tools
from registry_review_mcp.utils.state import StateManager


@pytest.mark.usefixtures("cleanup_examples_sessions")
class TestDocumentDiscovery:
    """Test document discovery functionality."""

    @pytest.mark.asyncio
    async def test_discover_documents_botany_farm(self, example_documents_path):
        """Test document discovery with real Botany Farm data."""
        # Create session
        session = await session_tools.create_session(
            project_name="Botany Farm Test",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        # Run discovery
        results = await document_tools.discover_documents(session_id)

        # Verify results
        assert results["documents_found"] > 0, "Should find documents in examples/22-23"
        assert "classification_summary" in results
        assert "documents" in results

        # Check that at least some PDFs were found
        assert results["documents_found"] >= 5, "Should find at least 5 PDFs"

        # Verify classification summary has expected types
        summary = results["classification_summary"]
        assert "project_plan" in summary or "baseline_report" in summary, \
            "Should classify at least one project plan or baseline report"

        # Verify document structure
        first_doc = results["documents"][0]
        assert "document_id" in first_doc
        assert "filename" in first_doc
        assert "classification" in first_doc
        assert "confidence" in first_doc
        assert first_doc["document_id"].startswith("DOC-")

        # Cleanup
        await session_tools.delete_session(session_id)

    @pytest.mark.asyncio
    async def test_document_classification_patterns(self):
        """Test that classification patterns work correctly."""
        # Test project plan
        classification, confidence, method = await document_tools.classify_document_by_filename(
            "/path/to/4997Botany22_Public_Project_Plan.pdf"
        )
        assert classification == "project_plan"
        assert confidence >= 0.9
        assert method == "filename"

        # Test baseline report
        classification, confidence, method = await document_tools.classify_document_by_filename(
            "/path/to/Baseline_Report_2022.pdf"
        )
        assert classification == "baseline_report"
        assert confidence >= 0.9

        # Test monitoring report
        classification, confidence, method = await document_tools.classify_document_by_filename(
            "/path/to/Monitoring_Report_2023.pdf"
        )
        assert classification == "monitoring_report"
        assert confidence >= 0.8

        # Test GHG emissions
        classification, confidence, method = await document_tools.classify_document_by_filename(
            "/path/to/GHG_Emissions_Report.pdf"
        )
        assert classification == "ghg_emissions"
        assert confidence >= 0.8

        # Test unknown
        classification, confidence, method = await document_tools.classify_document_by_filename(
            "/path/to/random_file.pdf"
        )
        assert classification == "unknown"
        assert confidence <= 0.6


@pytest.mark.usefixtures("cleanup_examples_sessions")
class TestPDFExtraction:
    """Test PDF text extraction."""

    @pytest.mark.marker
    @pytest.mark.asyncio
    async def test_extract_pdf_text_basic(self, example_documents_path):
        """Test basic PDF text extraction."""
        # Find a PDF in the example data
        pdf_files = list(example_documents_path.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in example data")

        pdf_path = str(pdf_files[0])

        # Extract text
        results = await document_tools.extract_pdf_text(pdf_path)

        # Verify results
        assert results["filepath"] == pdf_path
        assert results["page_count"] > 0
        assert len(results["full_text"]) > 0
        assert len(results["pages"]) > 0

        # Verify page structure
        first_page = results["pages"][0]
        assert "page_number" in first_page
        assert "text" in first_page
        assert first_page["page_number"] == 1

    @pytest.mark.marker
    @pytest.mark.asyncio
    async def test_extract_pdf_text_with_page_range(self, example_documents_path):
        """Test PDF extraction with specific page range."""
        pdf_files = list(example_documents_path.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in example data")

        pdf_path = str(pdf_files[0])

        # Extract pages 1-2
        results = await document_tools.extract_pdf_text(pdf_path, page_range=(1, 2))

        # Verify only 2 pages extracted
        assert len(results["pages"]) == 2
        assert results["pages"][0]["page_number"] == 1
        assert results["pages"][1]["page_number"] == 2

    @pytest.mark.marker
    @pytest.mark.asyncio
    async def test_extract_pdf_text_caching(self, example_documents_path):
        """Test that PDF extraction results are cached."""
        pdf_files = list(example_documents_path.glob("*.pdf"))
        if not pdf_files:
            pytest.skip("No PDF files found in example data")

        pdf_path = str(pdf_files[0])

        # First extraction
        results1 = await document_tools.extract_pdf_text(pdf_path)

        # Second extraction (should be from cache)
        results2 = await document_tools.extract_pdf_text(pdf_path)

        # Should be identical
        assert results1["full_text"] == results2["full_text"]
        assert results1["page_count"] == results2["page_count"]


@pytest.mark.usefixtures("cleanup_examples_sessions")
class TestEndToEnd:
    """End-to-end workflow tests."""

    @pytest.mark.marker
    @pytest.mark.asyncio
    async def test_full_discovery_workflow(self, example_documents_path):
        """Test complete discovery workflow from session to results."""
        # Step 1: Create session
        session = await session_tools.create_session(
            project_name="E2E Test Project",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
            project_id="C06-9999",
        )
        session_id = session["session_id"]

        try:
            # Step 2: Discover documents
            discovery = await document_tools.discover_documents(session_id)

            assert discovery["documents_found"] > 0
            assert len(discovery["documents"]) == discovery["documents_found"]

            # Step 3: Verify session state updated
            updated_session = await session_tools.load_session(session_id)
            assert updated_session["statistics"]["documents_found"] == discovery["documents_found"]
            assert updated_session["workflow_progress"]["document_discovery"] == "completed"

            # Step 4: Verify documents.json was created
            state_manager = StateManager(session_id)
            docs_data = state_manager.read_json("documents.json")
            assert docs_data["total_count"] == discovery["documents_found"]
            assert len(docs_data["documents"]) == discovery["documents_found"]

            # Step 5: Extract text from first PDF
            pdf_docs = [d for d in discovery["documents"] if d["filename"].endswith(".pdf")]
            if pdf_docs:
                first_pdf = pdf_docs[0]
                text_results = await document_tools.extract_pdf_text(first_pdf["filepath"])
                assert text_results["page_count"] > 0
                assert len(text_results["full_text"]) > 100  # Should have substantial text

        finally:
            # Cleanup
            await session_tools.delete_session(session_id)
