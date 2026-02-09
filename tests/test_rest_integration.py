"""REST API integration tests.

Default-run tests (smoke): health, model hardening, request ID middleware.
Integration-marked tests: full workflow (excluded by default via pytest.ini).
"""
from starlette.testclient import TestClient

from chatgpt_rest_api import app

client = TestClient(app)


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


class TestRootEndpoint:
    def test_root_version_matches_app(self):
        r = client.get("/")
        assert r.json()["version"] == "2.0.0"
