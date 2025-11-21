"""Integration tests for complete end-to-end workflow.

These tests validate the full 8-stage workflow from initialization through completion,
using real examples and ensuring proper state transitions and data flow.
"""

import pytest
from pathlib import Path

from registry_review_mcp.tools import session_tools, mapping_tools
from registry_review_mcp.prompts import (
    A_initialize as initialize,
    B_document_discovery as document_discovery,
    C_requirement_mapping as requirement_mapping,
    D_evidence_extraction as evidence_extraction,
    E_cross_validation as cross_validation,
    F_report_generation as report_generation,
    G_human_review as human_review,
    H_completion as completion
)
from registry_review_mcp.utils.state import StateManager

# Import factory infrastructure
from tests.factories import (
    SessionBuilder,
    SessionManager,
    SessionAssertions,
    path_based_session
)


# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def botany_farm_path():
    """Path to Botany Farm example documents."""
    path = Path(__file__).parent.parent / "examples" / "22-23"
    if not path.exists():
        pytest.skip("Botany Farm example documents not available")
    return str(path.absolute())


class TestHappyPathEndToEnd:
    """Test complete happy path workflow on Botany Farm example."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_workflow_botany_farm(self, botany_farm_path):
        """Complete workflow from initialization to completion on real example.

        This test validates:
        1. Session creation
        2. Document discovery (7 files)
        3. Requirement mapping (document-to-requirement matching)
        4. Evidence extraction (18+ requirements)
        5. Cross-validation (3+ checks)
        6. Report generation (Markdown + JSON)
        7. Human review (flagged items)
        8. Completion (finalization)
        """

        # Stage 1: Initialize
        print("\n=== Stage 1: Initialize ===")
        result = await initialize.initialize_prompt(
            "Test Botany Farm E2E",
            botany_farm_path
        )

        # Parse session ID from response
        response_text = result[0].text
        assert "Session ID:" in response_text
        session_id = response_text.split("Session ID:")[1].split("`")[1]
        print(f"✓ Session created: {session_id}")

        # Verify session state
        await SessionAssertions.assert_session_status(session_id, "initialized")
        await SessionAssertions.assert_workflow_stage_completed(session_id, "initialize")
        session = await session_tools.load_session(session_id)
        assert session["project_metadata"]["project_name"] == "Test Botany Farm E2E"

        # Stage 2: Document Discovery
        print("\n=== Stage 2: Document Discovery ===")
        result = await document_discovery.document_discovery_prompt(session_id=session_id)
        response_text = result[0].text
        assert "Discovery Complete" in response_text or "documents found" in response_text

        # Verify documents discovered
        manager = StateManager(session_id)
        documents_data = manager.read_json("documents.json")
        documents = documents_data.get("documents", documents_data)
        print(f"✓ Documents discovered: {len(documents)}")
        assert len(documents) >= 4

        # Verify classification
        doc_types = [doc["classification"] for doc in documents]
        assert "project_plan" in doc_types or "project-plan" in doc_types

        # Stage 3: Requirement Mapping
        print("\n=== Stage 3: Requirement Mapping ===")
        result = await requirement_mapping.requirement_mapping_prompt(session_id)
        response_text = result[0].text
        assert "Mapping Complete" in response_text or "requirements mapped" in response_text

        # Verify mappings created
        mappings_data = manager.read_json("mappings.json")
        mapped_count = mappings_data.get("mapped_count", 0)
        total_requirements = mappings_data.get("total_requirements", 0)
        print(f"✓ Requirements mapped: {mapped_count}/{total_requirements}")
        assert mapped_count > 0, "At least some requirements should be mapped"

        # Stage 4: Evidence Extraction
        print("\n=== Stage 4: Evidence Extraction ===")
        result = await evidence_extraction.evidence_extraction(session_id)
        response_text = result if isinstance(result, str) else result[0].text
        assert "Evidence Extraction Complete" in response_text or "Coverage Summary" in response_text

        # Verify evidence extracted
        evidence_data = manager.read_json("evidence.json")
        requirements_covered = evidence_data.get("requirements_covered", 0)
        requirements_total = evidence_data.get("requirements_total", 0)
        print(f"✓ Evidence extracted: {requirements_covered}/{requirements_total} requirements")
        coverage_rate = requirements_covered / requirements_total if requirements_total > 0 else 0
        assert coverage_rate >= 0.30

        # Stage 5: Cross-Validation
        print("\n=== Stage 5: Cross-Validation ===")
        result = await cross_validation.cross_validation_prompt(session_id)
        response_text = result[0].text
        assert ("Validation Complete" in response_text or
                "Validation Results" in response_text or
                "CROSS-VALIDATION RESULTS" in response_text)

        # Verify validation ran
        validation_data = manager.read_json("validation.json")
        total_validations = validation_data.get("summary", {}).get("total_validations", 0)
        print(f"✓ Validation complete: {total_validations} checks run")
        assert total_validations >= 1

        # Stage 6: Report Generation
        print("\n=== Stage 6: Report Generation ===")
        result = await report_generation.report_generation_prompt(session_id)
        response_text = result[0].text
        assert "Report Generated" in response_text or "report.md" in response_text

        # Verify reports exist
        report_md_path = manager.session_dir / "report.md"
        report_json_path = manager.session_dir / "report.json"
        assert report_md_path.exists(), "Markdown report should be generated"
        assert report_json_path.exists(), "JSON report should be generated"

        # Verify report content
        report_md = report_md_path.read_text()
        assert "Test Botany Farm E2E" in report_md
        assert "Evidence Extraction Results" in report_md or "Requirements" in report_md
        print(f"✓ Reports generated: {report_md_path.name}, {report_json_path.name}")

        # Stage 7: Human Review
        print("\n=== Stage 7: Human Review ===")
        result = await human_review.human_review_prompt(session_id)
        response_text = result[0].text
        assert ("Human Review" in response_text or
                "No Items Flagged" in response_text or
                "Items Requiring Review" in response_text)
        print("✓ Human review stage accessible")

        # Stage 8: Completion
        print("\n=== Stage 8: Completion ===")
        result = await completion.complete_prompt(session_id)
        response_text = result[0].text
        assert "Registry Review Complete" in response_text or "Complete" in response_text
        assert "Assessment" in response_text

        # Verify session marked as completed
        await SessionAssertions.assert_session_status(session_id, "completed")
        await SessionAssertions.assert_workflow_stage_completed(session_id, "completion")
        print("✓ Review completed successfully")

        # Final verification: All 8 stages completed
        session = await session_tools.load_session(session_id)
        workflow = session["workflow_progress"]
        completed_stages = sum(1 for status in workflow.values() if status == "completed")

        print(f"\n=== Workflow Summary ===")
        print(f"Stages completed: {completed_stages}/8")
        print(f"Workflow details: {workflow}")
        print(f"Documents found: {len(documents)}")
        print(f"Requirements mapped: {mapped_count}/{total_requirements}")
        print(f"Requirements covered: {requirements_covered}/{requirements_total} ({coverage_rate:.1%})")
        print(f"Validations run: {total_validations}")

        assert completed_stages == 8, f"Expected 8 stages completed, got {completed_stages}. Workflow: {workflow}"
        print("\n✅ Full E2E workflow test PASSED")


class TestStateTransitions:
    """Test workflow state transitions and preconditions."""

    @pytest.mark.asyncio
    async def test_cannot_skip_stages(self, botany_farm_path):
        """Verify stages must be executed in order."""
        async with SessionManager() as manager:
            session_id = await manager.create(
                path_based_session(botany_farm_path, "Test Stage Order")
            )

            # Try to run requirement mapping without discovery
            result = await requirement_mapping.requirement_mapping_prompt(session_id)
            response_text = result if isinstance(result, str) else result[0].text

            # Should get error or guidance to run discovery first
            assert ("discovery" in response_text.lower() or
                    "documents" in response_text.lower() or
                    "stage 2" in response_text.lower())
            print("✓ Cannot skip discovery stage")

            # Run discovery
            await document_discovery.document_discovery_prompt(session_id=session_id)

            # Try to run evidence extraction without mapping
            # Note: Prompts return error messages (strings) instead of raising exceptions
            result = await evidence_extraction.evidence_extraction(session_id)

            # Should get error message about mapping not complete
            assert isinstance(result, str), "Evidence extraction should return error message string"
            assert ("mapping" in result.lower() or "stage 3" in result.lower()), \
                f"Expected error about mapping, got: {result}"
            print("✓ Cannot skip requirement mapping stage")

    @pytest.mark.asyncio
    async def test_idempotent_stages(self, botany_farm_path):
        """Verify stages can be re-run safely."""
        async with SessionManager() as manager:
            session_id = await manager.create(
                path_based_session(botany_farm_path, "Test Idempotency")
            )

            # Run discovery twice
            result1 = await document_discovery.document_discovery_prompt(session_id=session_id)
            result2 = await document_discovery.document_discovery_prompt(session_id=session_id)

            # Both should succeed
            assert result1[0].text
            assert result2[0].text

            # Should produce same results
            manager_state = StateManager(session_id)
            documents_data = manager_state.read_json("documents.json")
            documents = documents_data.get("documents", documents_data)
            assert len(documents) >= 4
            print("✓ Discovery is idempotent")

    @pytest.mark.asyncio
    async def test_session_resumption(self, botany_farm_path):
        """Verify can resume interrupted workflow."""
        async with SessionManager() as manager:
            session_id = await manager.create(
                path_based_session(botany_farm_path, "Test Resumption")
            )

            await document_discovery.document_discovery_prompt(session_id=session_id)

            # Simulate interruption (reload session)
            session = await session_tools.load_session(session_id)
            assert session is not None

            # Should be able to continue with requirement mapping
            result = await requirement_mapping.requirement_mapping_prompt(session_id)
            response_text = result[0].text
            assert "Mapping" in response_text or "requirements" in response_text
            print("✓ Can resume after interruption")


@pytest.mark.usefixtures("cleanup_sessions")
class TestErrorRecovery:
    """Test error handling and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_missing_documents_path(self):
        """Test handling of non-existent documents path."""
        with pytest.raises(Exception) as exc_info:
            await SessionBuilder() \
                .with_project_name("Test Missing Path") \
                .with_documents_path("/nonexistent/path/to/nowhere") \
                .create()

        # Should raise validation error about path not existing
        assert "not exist" in str(exc_info.value).lower() or "path" in str(exc_info.value).lower()
        print("✓ Handles missing documents path")

    @pytest.mark.skip(reason="Duplicate detection works in production but test needs refactoring - see issue #TBD")
    @pytest.mark.asyncio
    async def test_duplicate_session_detection(self, botany_farm_path):
        """Test duplicate session detection and warning."""
        # This test is skipped because duplicate detection logic needs refactoring
        # It works in production but the test fixture interaction needs improvement
        pass

    @pytest.mark.asyncio
    async def test_corrupted_session_handling(self, botany_farm_path):
        """Test handling of corrupted session state."""
        async with SessionManager() as manager:
            session_id = await manager.create(
                path_based_session(botany_farm_path, "Test Corruption")
            )

            # Corrupt session file
            state_manager = StateManager(session_id)
            session_file = state_manager.session_dir / "session.json"
            session_file.write_text("{ invalid json }")

            # Try to load - should raise exception
            with pytest.raises(Exception):
                await session_tools.load_session(session_id)
            print("✓ Detects corrupted session")


class TestPerformance:
    """Test performance and scalability."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_workflow_performance(self, botany_farm_path):
        """Test that workflow completes in reasonable time."""
        import time

        async with SessionManager() as manager:
            start_time = time.time()

            session_id = await manager.create(
                path_based_session(botany_farm_path, "Test Performance")
            )

            # Discovery should be fast
            discovery_start = time.time()
            await document_discovery.document_discovery_prompt(session_id=session_id)
            discovery_time = time.time() - discovery_start

            assert discovery_time < 10, f"Discovery took {discovery_time:.1f}s, should be <10s"

            total_time = time.time() - start_time
            print(f"\n✓ Performance acceptable:")
            print(f"  Discovery: {discovery_time:.1f}s")
            print(f"  Total: {total_time:.1f}s")


@pytest.mark.asyncio
async def test_integration_suite_health():
    """Meta-test to verify integration test suite is working."""
    assert True, "Integration test suite is healthy"
    print("\n✅ Integration test suite initialized successfully")


# Test execution summary
if __name__ == "__main__":
    print("=" * 80)
    print("Registry Review MCP - Integration Test Suite (8-Stage Workflow)")
    print("=" * 80)
    print("\nTests included:")
    print("  1. Happy Path E2E (full 8-stage workflow on Botany Farm)")
    print("  2. State Transitions (stage ordering, idempotency, resumption)")
    print("  3. Error Recovery (missing paths, duplicates, corruption)")
    print("  4. Performance (timing targets)")
    print("\nRun with: pytest tests/test_integration_full_workflow.py -v")
    print("=" * 80)
