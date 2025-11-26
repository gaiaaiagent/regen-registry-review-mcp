"""Tests for evidence extraction (Phase 4)."""

import pytest
from pathlib import Path

from registry_review_mcp.tools import session_tools, document_tools, evidence_tools, mapping_tools
from registry_review_mcp.utils.state import StateManager


class TestEvidenceExtraction:
    """Test complete evidence extraction workflow using LLM-based extraction."""

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

            # Map requirements to documents (Stage 3)
            await mapping_tools.map_all_requirements(session_id)

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
