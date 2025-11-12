"""Tests for evidence extraction (Phase 3)."""

import pytest
from pathlib import Path

from registry_review_mcp.tools import session_tools, document_tools, evidence_tools
from registry_review_mcp.utils.state import StateManager


class TestKeywordExtraction:
    """Test keyword extraction from requirements."""

    def test_extract_keywords_from_requirement():
        """Test extracting search keywords from requirement text."""
        requirement = {
            "requirement_id": "REQ-002",
            "requirement_text": "Provide evidence of legal land tenure and control over the project area",
            "accepted_evidence": "Deeds, lease agreements, land use agreements, legal attestations"
        }

        keywords = evidence_tools.extract_keywords(requirement)

        # Should extract important terms
        assert "land tenure" in keywords or "tenure" in keywords
        assert "lease" in keywords or "agreement" in keywords
        # Should not include common words
        assert "the" not in keywords
        assert "of" not in keywords


class TestDocumentRelevance:
    """Test document relevance scoring."""

    @pytest.mark.asyncio
    async def test_calculate_relevance_score(self, example_documents_path):
        """Test relevance scoring based on keyword matches."""
        # Create a test session
        session = await session_tools.create_session(
            project_name="Test Relevance",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        try:
            # Discover documents
            await document_tools.discover_documents(session_id)

            # Test relevance for land tenure requirement
            keywords = ["land", "tenure", "lease", "agreement", "ownership"]

            # Get markdown content for Project Plan
            state_manager = StateManager(session_id)
            docs_data = state_manager.read_json("documents.json")

            project_plan = next(
                (d for d in docs_data["documents"] if "Project_Plan" in d["filename"]),
                None
            )

            if project_plan:
                score = await evidence_tools.calculate_relevance_score(
                    project_plan,
                    keywords,
                    session_id
                )

                # Project plan should have decent relevance for land tenure
                assert 0.0 <= score <= 1.0
                assert score > 0.1  # Should find some matches

        finally:
            await session_tools.delete_session(session_id)


class TestEvidenceSnippetExtraction:
    """Test evidence snippet extraction."""

    @pytest.mark.asyncio
    async def test_extract_snippets_from_markdown(self, example_documents_path):
        """Test extracting text snippets with context."""
        session = await session_tools.create_session(
            project_name="Test Snippets",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        try:
            await document_tools.discover_documents(session_id)

            keywords = ["project", "start", "date"]
            state_manager = StateManager(session_id)
            docs_data = state_manager.read_json("documents.json")

            project_plan = next(
                (d for d in docs_data["documents"] if "Project_Plan" in d["filename"]),
                None
            )

            if project_plan:
                snippets = await evidence_tools.extract_evidence_snippets(
                    project_plan,
                    keywords,
                    session_id,
                    max_snippets=5
                )

                assert len(snippets) > 0
                assert all(hasattr(s, 'text') for s in snippets)
                assert all(hasattr(s, 'page') for s in snippets)
                assert all(hasattr(s, 'confidence') for s in snippets)

        finally:
            await session_tools.delete_session(session_id)


class TestRequirementMapping:
    """Test full requirement mapping workflow."""

    @pytest.mark.asyncio
    async def test_map_single_requirement(self, example_documents_path):
        """Test mapping a single requirement to documents."""
        session = await session_tools.create_session(
            project_name="Test Mapping",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        try:
            await document_tools.discover_documents(session_id)

            # Map REQ-007 (Project Start Date)
            result = await evidence_tools.map_requirement(
                session_id=session_id,
                requirement_id="REQ-007"
            )

            assert result["requirement_id"] == "REQ-007"
            assert result["status"] in ["covered", "partial", "missing", "flagged"]
            assert 0.0 <= result["confidence"] <= 1.0
            assert "mapped_documents" in result
            assert "evidence_snippets" in result

        finally:
            await session_tools.delete_session(session_id)


class TestEvidenceExtraction:
    """Test complete evidence extraction workflow."""

    @pytest.mark.asyncio
    async def test_extract_all_evidence(self, example_documents_path):
        """Test extracting evidence for all requirements."""
        session = await session_tools.create_session(
            project_name="Botany Farm Evidence Test",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        try:
            # Discover documents first
            await document_tools.discover_documents(session_id)

            # Extract all evidence
            results = await evidence_tools.extract_all_evidence(session_id)

            # Verify structure
            assert results["session_id"] == session_id
            assert results["requirements_total"] == 23
            assert results["requirements_covered"] + results["requirements_partial"] + results["requirements_missing"] == 23

            # Should map most requirements successfully
            assert results["requirements_covered"] + results["requirements_partial"] >= 15

            # Check individual evidence
            assert len(results["evidence"]) == 23

            # Verify specific requirement
            req_007 = next((e for e in results["evidence"] if e["requirement_id"] == "REQ-007"), None)
            assert req_007 is not None
            assert req_007["status"] in ["covered", "partial", "missing"]

            # Verify evidence.json was saved
            state_manager = StateManager(session_id)
            assert state_manager.exists("evidence.json")

        finally:
            await session_tools.delete_session(session_id)


class TestStructuredFieldExtraction:
    """Test extraction of specific structured fields."""

    @pytest.mark.asyncio
    async def test_extract_project_start_date(self, example_documents_path):
        """Test extracting project start date."""
        session = await session_tools.create_session(
            project_name="Test Structured Fields",
            documents_path=str(example_documents_path),
            methodology="soil-carbon-v1.2.2",
        )
        session_id = session["session_id"]

        try:
            await document_tools.discover_documents(session_id)

            # Extract project start date
            result = await evidence_tools.extract_structured_field(
                session_id=session_id,
                field_name="project_start_date",
                field_patterns=[
                    r"Project Start Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                    r"Start Date[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"
                ]
            )

            assert result is not None
            assert "field_value" in result
            assert "source_document" in result
            assert "confidence" in result

        finally:
            await session_tools.delete_session(session_id)
