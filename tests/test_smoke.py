"""Smoke tests: Ultra-fast critical path validation.

These tests verify that core functionality works without any failures.
Target runtime: < 1 second total.

Usage:
    pytest -m smoke -v          # Run smoke tests only
    ptw -- -m smoke             # Watch mode
    make smoke                  # Via Makefile
"""

import pytest
from pathlib import Path

from registry_review_mcp.config.settings import Settings
from registry_review_mcp.utils.state import StateManager
from registry_review_mcp.utils.cache import Cache
from registry_review_mcp.extractors.verification import (
    verify_citation,
    verify_extracted_field,
)


@pytest.mark.smoke
class TestCoreInfrastructure:
    """Essential infrastructure tests that must always pass."""

    def test_settings_initialize(self, test_settings):
        """Settings load and directories exist."""
        assert test_settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert test_settings.data_dir.exists()
        assert test_settings.checklists_dir.exists()
        assert test_settings.sessions_dir.exists()

    def test_state_manager_write_read(self, test_settings):
        """State manager can persist data."""
        manager = StateManager("smoke-test-state")
        test_data = {"status": "ok", "count": 42}

        manager.write_json("smoke.json", test_data)
        read_data = manager.read_json("smoke.json")

        assert read_data == test_data

    def test_cache_store_retrieve(self, test_settings):
        """Cache can store and retrieve values."""
        cache = Cache("smoke-test-cache")

        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        assert cache.exists("test_key")


@pytest.mark.smoke
class TestCriticalValidation:
    """Core validation logic that protects data integrity."""

    def test_citation_verification_exact_match(self):
        """Citation verification detects exact matches."""
        raw_text = "Project Start Date: 01/01/2022"
        source = "The project began on January 1, 2022. Project Start Date: 01/01/2022 is when we commenced."

        is_verified, score, snippet = verify_citation(raw_text, source, "project_start_date")

        assert is_verified is True
        assert score >= 95.0

    def test_citation_verification_hallucination_detection(self):
        """Citation verification catches hallucinations."""
        raw_text = "Project ended on December 31, 2023"
        source = "Project started in January 2022"

        is_verified, score, snippet = verify_citation(raw_text, source, "project_end_date")

        assert is_verified is False
        assert score < 50.0

    def test_extracted_field_confidence_penalty(self):
        """Unverified fields get confidence penalty."""
        field = {
            "value": "2022-01-01",
            "field_type": "project_start_date",
            "confidence": 0.95,
            "raw_text": "January 1, 2022",
        }
        source_text = "The project began in March 2022"  # Different!

        verified_field = verify_extracted_field(field, source_text)

        # Confidence should be reduced
        assert verified_field["confidence"] < 0.95
        assert verified_field["verification_status"] == "failed"


@pytest.mark.smoke
@pytest.mark.asyncio
class TestSessionManagement:
    """Critical session operations."""

    async def test_create_and_load_session(self, test_settings, tmp_path, cleanup_sessions):
        """Sessions can be created and loaded."""
        from registry_review_mcp.tools import session_tools

        # Create minimal session
        result = await session_tools.create_session(
            project_name="Smoke Test Project",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2",
        )

        session_id = result["session_id"]
        assert session_id is not None

        # Load session back
        loaded = await session_tools.load_session(session_id)
        assert loaded["session_id"] == session_id
        assert loaded["project_metadata"]["project_name"] == "Smoke Test Project"


@pytest.mark.smoke
class TestDataIntegrity:
    """Essential data structures and validation."""

    def test_checklist_structure(self):
        """Soil carbon checklist is valid."""
        checklist_path = (
            Path(__file__).parent.parent
            / "data"
            / "checklists"
            / "soil-carbon-v1.2.2.json"
        )

        assert checklist_path.exists(), "Checklist file missing"

        import json
        with open(checklist_path) as f:
            checklist = json.load(f)

        assert "methodology_id" in checklist
        assert "requirements" in checklist
        assert len(checklist["requirements"]) >= 20

        # Verify requirement structure
        req = checklist["requirements"][0]
        assert "requirement_id" in req
        assert "category" in req
        assert "requirement_text" in req

    def test_state_manager_atomic_update(self, test_settings):
        """State updates are atomic."""
        manager = StateManager("smoke-atomic")

        initial = {"counter": 0, "status": "pending"}
        manager.write_json("atomic.json", initial)

        updated = manager.update_json("atomic.json", {"counter": 1})

        assert updated["counter"] == 1
        assert updated["status"] == "pending"  # Other fields preserved


@pytest.mark.smoke
class TestErrorHandling:
    """Critical error conditions are handled correctly."""

    def test_nonexistent_session_raises(self, test_settings):
        """Loading nonexistent session raises proper error."""
        from registry_review_mcp.models.errors import SessionNotFoundError

        manager = StateManager("nonexistent-session-12345")

        with pytest.raises(SessionNotFoundError):
            manager.read_json("nonexistent.json")

    def test_cache_nonexistent_key(self, test_settings):
        """Cache returns default for missing keys."""
        cache = Cache("smoke-missing")

        assert cache.get("nonexistent") is None
        assert cache.get("nonexistent", "default") == "default"
        assert not cache.exists("nonexistent")


# Summary fixture to track smoke test health
@pytest.fixture(scope="module", autouse=True)
def smoke_test_summary(request):
    """Track smoke test execution time."""
    import time
    start = time.time()

    yield

    duration = time.time() - start
    print(f"\n\n{'='*80}")
    print(f"SMOKE TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Duration: {duration:.3f}s")
    print(f"Target: < 1.0s")
    print(f"Status: {'✓ PASS' if duration < 1.0 else '✗ SLOW'}")
    print(f"{'='*80}\n")
