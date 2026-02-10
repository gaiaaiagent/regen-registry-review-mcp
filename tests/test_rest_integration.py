"""REST API integration tests.

Default-run tests (smoke): health, model hardening, request ID middleware.
Integration tests: session lifecycle, discovery, error paths, human review, reports.
All tests are fast (no LLM calls) and run in the default pytest suite.
"""
from datetime import datetime
from pathlib import Path

from starlette.testclient import TestClient

from chatgpt_rest_api import app

client = TestClient(app)

# Minimal payload for session creation (reused across test classes)
_SESSION_PAYLOAD = {"project_name": "Test", "methodology": "soil-carbon-v1.2.2"}

# Absolute path to botany-farm test data (7 PDFs, simplest case)
_BOTANY_FARM_PATH = str(
    (Path(__file__).parent.parent / "examples" / "test-data" / "registration" / "botany-farm").resolve()
)


def _create_session(**overrides) -> dict:
    """Create a session and return the JSON response. Raises on non-200."""
    payload = {**_SESSION_PAYLOAD, **overrides}
    r = client.post("/sessions", json=payload)
    assert r.status_code == 200, f"Session creation failed: {r.text}"
    return r.json()


class TestHealthEndpoint:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "session_count" in data
        assert "sessions_dir_exists" in data

    def test_health_version_matches_app(self):
        r = client.get("/health")
        assert r.json()["version"] == "2.0.0"

    def test_health_session_count_is_integer(self):
        r = client.get("/health")
        assert isinstance(r.json()["session_count"], int)

    def test_health_last_request_at(self):
        # First request populates _last_request_at via middleware
        client.get("/health")
        r = client.get("/health")
        data = r.json()
        assert data["last_request_at"] is not None
        # Verify it's a valid ISO timestamp ending with Z
        ts = data["last_request_at"]
        assert ts.endswith("Z")
        datetime.fromisoformat(ts.replace("Z", "+00:00"))


class TestRequestModelHardening:
    def test_create_session_rejects_unknown_fields(self):
        r = client.post("/sessions", json={
            "project_name": "Test",
            "unknown_field": "should_fail",
        })
        assert r.status_code == 422

    def test_override_rejects_unknown_fields(self):
        r = client.post("/sessions/fake-id/override", json={
            "requirement_id": "REQ-001",
            "override_status": "approved",
            "unknown_field": "should_fail",
        })
        assert r.status_code == 422

    def test_set_determination_rejects_unknown_fields(self):
        r = client.post("/sessions/fake-id/determination", json={
            "determination": "approve",
            "notes": "looks good",
            "bogus": "nope",
        })
        assert r.status_code == 422


class TestRequestIdMiddleware:
    def test_response_includes_request_id(self):
        r = client.get("/health")
        assert "x-request-id" in r.headers

    def test_client_request_id_echoed(self):
        r = client.get("/health", headers={"X-Request-ID": "trace-123"})
        assert r.headers["x-request-id"] == "trace-123"

    def test_response_includes_timing(self):
        r = client.get("/health")
        assert "x-response-time-ms" in r.headers
        # Should be a parseable number
        float(r.headers["x-response-time-ms"])


class TestPDFDownloadEndpoint:
    def test_pdf_download_returns_404_without_generation(self):
        """PDF download for nonexistent session returns 404."""
        r = client.get("/sessions/nonexistent-id/report/download-pdf")
        assert r.status_code == 404


class TestRootEndpoint:
    def test_root_version_matches_app(self):
        r = client.get("/")
        assert r.json()["version"] == "2.0.0"


# ============================================================================
# Phase 3c: Integration Tests
# ============================================================================


class TestSessionLifecycle:
    """Session CRUD via REST endpoints. Each test is self-contained."""

    def test_create_session(self):
        data = _create_session()
        assert data["session_id"]
        assert data["project_name"] == "Test"

    def test_create_session_with_documents_path(self):
        data = _create_session(documents_path=_BOTANY_FARM_PATH)
        assert data["session_id"]
        # Verify path stored — load session and check metadata
        r = client.get(f"/sessions/{data['session_id']}")
        assert r.status_code == 200
        session = r.json()
        assert session["project_metadata"]["documents_path"] == _BOTANY_FARM_PATH

    def test_list_sessions_includes_created(self):
        data = _create_session()
        r = client.get("/sessions")
        assert r.status_code == 200
        ids = [s["session_id"] for s in r.json()["sessions"]]
        assert data["session_id"] in ids

    def test_get_session_by_id(self):
        data = _create_session()
        r = client.get(f"/sessions/{data['session_id']}")
        assert r.status_code == 200
        session = r.json()
        assert session["session_id"] == data["session_id"]
        assert session["project_metadata"]["project_name"] == "Test"

    def test_delete_session(self):
        data = _create_session()
        sid = data["session_id"]
        r = client.delete(f"/sessions/{sid}")
        assert r.status_code == 200
        # Session should no longer appear in list
        r = client.get("/sessions")
        ids = [s["session_id"] for s in r.json()["sessions"]]
        assert sid not in ids


class TestDocumentDiscovery:
    """Discovery with real Botany Farm test data (7 PDFs, no LLM calls)."""

    def test_discover_finds_all_documents(self):
        data = _create_session(documents_path=_BOTANY_FARM_PATH)
        r = client.post(f"/sessions/{data['session_id']}/discover")
        assert r.status_code == 200
        assert r.json()["documents_found"] == 7

    def test_discover_classifies_documents(self):
        data = _create_session(documents_path=_BOTANY_FARM_PATH)
        r = client.post(f"/sessions/{data['session_id']}/discover")
        assert r.status_code == 200
        docs = r.json().get("documents", [])
        assert len(docs) == 7
        for doc in docs:
            assert doc.get("classification"), f"Missing classification for {doc.get('filename')}"


class TestErrorPaths:
    """HTTP error codes for missing/invalid resources."""

    def test_get_nonexistent_session_404(self):
        r = client.get("/sessions/no-such-id")
        assert r.status_code == 404

    def test_discover_nonexistent_session_404(self):
        r = client.post("/sessions/no-such-id/discover")
        assert r.status_code == 404

    def test_map_nonexistent_session_404(self):
        r = client.post("/sessions/no-such-id/map")
        assert r.status_code == 404

    def test_create_session_empty_body_422(self):
        r = client.post("/sessions", json={})
        assert r.status_code == 422


class TestHumanReviewWorkflow:
    """Override, annotation, determination, and audit — no LLM calls."""

    def test_set_override(self):
        data = _create_session()
        sid = data["session_id"]
        r = client.post(f"/sessions/{sid}/override", json={
            "requirement_id": "REQ-001",
            "override_status": "approved",
            "notes": "Verified manually",
        })
        assert r.status_code == 200
        # Per-requirement review-status returns singular "override" dict
        r = client.get(f"/sessions/{sid}/review-status", params={"requirement_id": "REQ-001"})
        assert r.status_code == 200
        override = r.json().get("override")
        assert override is not None
        assert override["status"] == "approved"

    def test_clear_override(self):
        data = _create_session()
        sid = data["session_id"]
        client.post(f"/sessions/{sid}/override", json={
            "requirement_id": "REQ-001",
            "override_status": "rejected",
        })
        r = client.delete(f"/sessions/{sid}/override/REQ-001")
        assert r.status_code == 200

    def test_add_annotation(self):
        data = _create_session()
        sid = data["session_id"]
        r = client.post(f"/sessions/{sid}/annotation", json={
            "requirement_id": "REQ-001",
            "note": "Need clarification on sampling dates",
            "annotation_type": "question",
        })
        assert r.status_code == 200
        # Per-requirement review-status returns "annotations" as a list
        r = client.get(f"/sessions/{sid}/review-status", params={"requirement_id": "REQ-001"})
        assert r.status_code == 200
        annotations = r.json().get("annotations", [])
        assert len(annotations) >= 1

    def test_set_determination(self):
        data = _create_session()
        sid = data["session_id"]
        r = client.post(f"/sessions/{sid}/determination", json={
            "determination": "approve",
            "notes": "All requirements met",
        })
        assert r.status_code == 200
        # Verify via GET
        r = client.get(f"/sessions/{sid}/determination")
        assert r.status_code == 200
        det = r.json()
        assert det.get("determination") == "approve"

    def test_clear_determination(self):
        data = _create_session()
        sid = data["session_id"]
        client.post(f"/sessions/{sid}/determination", json={
            "determination": "reject",
            "notes": "Missing documents",
        })
        r = client.delete(f"/sessions/{sid}/determination")
        assert r.status_code == 200
        # Verify cleared
        r = client.get(f"/sessions/{sid}/determination")
        assert r.status_code == 200
        det = r.json()
        assert det.get("determination") is None or det.get("status") == "no_determination"

    def test_audit_log_records_actions(self):
        data = _create_session()
        sid = data["session_id"]
        # Perform two actions to generate audit entries
        client.post(f"/sessions/{sid}/override", json={
            "requirement_id": "REQ-001",
            "override_status": "approved",
        })
        client.post(f"/sessions/{sid}/annotation", json={
            "requirement_id": "REQ-002",
            "note": "Looks good",
        })
        r = client.get(f"/sessions/{sid}/audit-log")
        assert r.status_code == 200
        events = r.json().get("events", [])
        assert len(events) >= 2

    def test_review_status_aggregates(self):
        data = _create_session()
        sid = data["session_id"]
        client.post(f"/sessions/{sid}/override", json={
            "requirement_id": "REQ-001",
            "override_status": "conditional",
            "notes": "Pending field visit",
        })
        client.post(f"/sessions/{sid}/annotation", json={
            "requirement_id": "REQ-001",
            "note": "Schedule site visit",
            "annotation_type": "note",
        })
        r = client.get(f"/sessions/{sid}/review-status")
        assert r.status_code == 200
        status = r.json()
        assert "overrides" in status
        assert "annotations" in status


class TestReportDownloads:
    """Report format endpoints on minimal sessions (no evidence)."""

    def test_report_markdown_format(self):
        data = _create_session()
        sid = data["session_id"]
        r = client.post(f"/sessions/{sid}/report", params={"format": "markdown"})
        assert r.status_code == 200
        body = r.json()
        assert "report" in body or "report_path" in body

    def test_report_json_format(self):
        data = _create_session()
        sid = data["session_id"]
        r = client.post(f"/sessions/{sid}/report", params={"format": "json"})
        assert r.status_code == 200
        body = r.json()
        # JSON format returns a structured object
        assert isinstance(body, dict)

    def test_checklist_download_returns_file_or_404(self):
        """After report generation, checklist download returns content or 404 if not generated."""
        data = _create_session()
        sid = data["session_id"]
        # Generate markdown report first
        client.post(f"/sessions/{sid}/report", params={"format": "markdown"})
        r = client.get(f"/sessions/{sid}/report/download")
        # Either the file exists (200 with markdown content-type) or not yet written (404)
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            assert "markdown" in r.headers.get("content-type", "") or "text" in r.headers.get("content-type", "")
