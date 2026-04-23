"""Phase F6 — reviewer preview renderer tests.

The template lives outside the source tree (``templates/review-preview.html.j2``
at the repo root). These tests exercise the loader + template wiring with
synthetic review dossiers so the rendering contract stays stable.
"""

from __future__ import annotations

import json

import pytest

from registry_review_mcp.reviewer.preview import (
    render_review_preview,
    write_review_preview,
)


@pytest.fixture
def sample_review() -> dict:
    return {
        "fixture_name": "test-fixture",
        "model": "gpt-oss:120b",
        "methodology": "Ecometric Soil Carbon v1.2.2",
        "run_date": "2026-04-22",
        "requirements": [
            {
                "requirement_id": "REQ-001",
                "requirement_text": "Project start date documented.",
                "accepted_evidence": "Date in Project Plan",
                "category": "Eligibility",
                "status": "covered",
                "confidence": 0.95,
                "evidence_snippets": [
                    {
                        "text": "Project started on 2023-01-15.",
                        "document_name": "project-plan.pdf",
                        "page": 3,
                        "section": "1. Overview",
                        "confidence": 0.95,
                        "schema_match": True,
                    }
                ],
            },
            {
                "requirement_id": "REQ-017",
                "requirement_text": "Monitoring plan is in place.",
                "accepted_evidence": "Sampling plan with plot locations",
                "category": "Monitoring",
                "status": "partial",
                "confidence": 0.75,
                "evidence_snippets": [
                    {
                        "text": "A monitoring program will be implemented.",
                        "document_name": "project-plan.pdf",
                        "page": 12,
                        "section": "5. Monitoring",
                        "confidence": 0.85,
                        "schema_match": False,
                    }
                ],
            },
            {
                "requirement_id": "REQ-099",
                "requirement_text": "Impossible requirement.",
                "accepted_evidence": "Nothing.",
                "category": "Test",
                "status": "missing",
                "confidence": 0.0,
                "evidence_snippets": [],
            },
        ],
    }


class TestRenderBasics:
    def test_renders_without_error(self, sample_review):
        html = render_review_preview(sample_review)
        assert isinstance(html, str)
        assert html.startswith("<!doctype html>")

    def test_fixture_name_in_output(self, sample_review):
        html = render_review_preview(sample_review)
        assert "test-fixture" in html

    def test_model_name_in_output(self, sample_review):
        html = render_review_preview(sample_review)
        assert "gpt-oss:120b" in html

    def test_counts_correct(self, sample_review):
        html = render_review_preview(sample_review)
        # 1 covered, 1 partial, 1 missing, 33% coverage
        # Coverage rendered as "33%" in template; counts appear as standalone integers.
        assert "covered" in html
        assert "partial" in html
        assert "missing" in html
        assert "33%" in html


class TestSnippetRendering:
    def test_schema_match_false_renders_warning_tag(self, sample_review):
        html = render_review_preview(sample_review)
        # REQ-017 has schema_match: False — the template shows a warning tag.
        assert "schema_match: false" in html
        assert "no-schema" in html

    def test_schema_match_true_no_warning(self, sample_review):
        html = render_review_preview(sample_review)
        # REQ-001 has schema_match: True — no warning tag for that snippet.
        # Just confirm schema_match phrase appears only once (only the False case).
        assert html.count("schema_match: false") == 1

    def test_missing_requirement_has_no_snippets_placeholder(self, sample_review):
        html = render_review_preview(sample_review)
        # REQ-099 has no snippets — template falls back to the italic placeholder.
        assert "No evidence snippets extracted" in html


class TestOverrideUX:
    def test_each_req_has_override_dropdown(self, sample_review):
        html = render_review_preview(sample_review)
        for req in sample_review["requirements"]:
            rid = req["requirement_id"]
            assert f'data-req-id="{rid}"' in html

    def test_export_button_present(self, sample_review):
        html = render_review_preview(sample_review)
        assert "Export overrides.json" in html
        assert "exportOverrides()" in html


class TestFileIO:
    def test_write_creates_file(self, sample_review, tmp_path):
        review_path = tmp_path / "review.json"
        review_path.write_text(json.dumps(sample_review))
        out = write_review_preview(review_path)
        assert out.exists()
        assert out.read_text().startswith("<!doctype html>")

    def test_write_respects_custom_out_path(self, sample_review, tmp_path):
        review_path = tmp_path / "review.json"
        review_path.write_text(json.dumps(sample_review))
        custom_out = tmp_path / "sub" / "preview.html"
        out = write_review_preview(review_path, custom_out)
        assert out == custom_out
        assert out.exists()


class TestDefensiveCoercion:
    """Older dossiers may omit fields — the renderer must not crash."""

    def test_empty_review_renders(self):
        html = render_review_preview({})
        assert html.startswith("<!doctype html>")

    def test_missing_model_falls_back(self):
        html = render_review_preview({"fixture_name": "x", "requirements": []})
        assert "unknown" in html  # default model placeholder


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
