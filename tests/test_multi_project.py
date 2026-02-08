"""Tests for multi-project scope support and centralized checklist loading."""

import pytest

from registry_review_mcp.utils.checklist import load_checklist

METHODOLOGY = "soil-carbon-v1.2.2"

FARM_REQ_IDS = {"REQ-002", "REQ-003", "REQ-004", "REQ-009"}


class TestLoadChecklist:
    """Tests for the centralized checklist loader."""

    def test_load_checklist_no_scope(self):
        """Loading with no scope returns all 23 requirements."""
        data = load_checklist(METHODOLOGY)
        requirements = data["requirements"]
        assert len(requirements) == 23

    def test_load_checklist_farm_scope(self):
        """Loading with scope='farm' returns exactly 4 per-farm requirements."""
        data = load_checklist(METHODOLOGY, scope="farm")
        requirements = data["requirements"]
        assert len(requirements) == 4
        req_ids = {r["requirement_id"] for r in requirements}
        assert req_ids == FARM_REQ_IDS

    def test_load_checklist_meta_scope(self):
        """Loading with scope='meta' returns exactly 19 meta-project requirements."""
        data = load_checklist(METHODOLOGY, scope="meta")
        requirements = data["requirements"]
        assert len(requirements) == 19
        req_ids = {r["requirement_id"] for r in requirements}
        assert req_ids & FARM_REQ_IDS == set()

    def test_load_checklist_preserves_metadata(self):
        """Scope filtering preserves top-level checklist metadata."""
        data = load_checklist(METHODOLOGY, scope="farm")
        assert data["methodology_id"] == METHODOLOGY
        assert data["version"] == "1.2.2"
        assert "protocol" in data

    def test_load_checklist_farm_plus_meta_equals_all(self):
        """Farm + meta requirements together equal the full set."""
        farm = load_checklist(METHODOLOGY, scope="farm")
        meta = load_checklist(METHODOLOGY, scope="meta")
        full = load_checklist(METHODOLOGY)
        farm_ids = {r["requirement_id"] for r in farm["requirements"]}
        meta_ids = {r["requirement_id"] for r in meta["requirements"]}
        full_ids = {r["requirement_id"] for r in full["requirements"]}
        assert farm_ids | meta_ids == full_ids
        assert farm_ids & meta_ids == set()

    def test_load_checklist_missing_methodology(self):
        """Loading a nonexistent methodology raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_checklist("nonexistent-methodology-v99")

    def test_every_requirement_has_scope(self):
        """Every requirement in the checklist has an explicit scope field."""
        data = load_checklist(METHODOLOGY)
        for req in data["requirements"]:
            assert "scope" in req, f"{req['requirement_id']} missing scope field"
            assert req["scope"] in ("farm", "meta"), (
                f"{req['requirement_id']} has invalid scope: {req['scope']}"
            )


class TestSessionCreationWithScope:
    """Tests for session creation with scope parameter."""

    @pytest.mark.asyncio
    async def test_session_creation_with_farm_scope(self):
        """Creating a session with scope='farm' sets requirements_total to 4."""
        from registry_review_mcp.tools.session_tools import create_session

        result = await create_session(
            project_name="Test Farm Session",
            scope="farm",
        )
        assert result["requirements_total"] == 4

    @pytest.mark.asyncio
    async def test_session_creation_with_meta_scope(self):
        """Creating a session with scope='meta' sets requirements_total to 19."""
        from registry_review_mcp.tools.session_tools import create_session

        result = await create_session(
            project_name="Test Meta Session",
            scope="meta",
        )
        assert result["requirements_total"] == 19

    @pytest.mark.asyncio
    async def test_session_creation_no_scope(self):
        """Creating a session without scope sets requirements_total to 23."""
        from registry_review_mcp.tools.session_tools import create_session

        result = await create_session(
            project_name="Test Full Session",
        )
        assert result["requirements_total"] == 23

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """Two sessions with different scopes have independent state."""
        from registry_review_mcp.tools.session_tools import create_session

        farm = await create_session(project_name="Farm A", scope="farm")
        meta = await create_session(project_name="Meta Project", scope="meta")

        assert farm["session_id"] != meta["session_id"]
        assert farm["requirements_total"] == 4
        assert meta["requirements_total"] == 19
