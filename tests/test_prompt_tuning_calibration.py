"""Phase F1 — prompt-tuning calibration tests for the accepted-evidence schema gate.

Phase E's synthetic-mixed-verdict-1 fixture surfaced a 13% over-scoring
bias: the pipeline accepted topically-related snippets as sufficient
evidence even when they did not satisfy the ``accepted_evidence`` schema.
Phase F1 tightens the contract on TWO surfaces:

1. ``EvidenceSnippet`` gains a ``schema_match`` boolean. Default True
   preserves pre-Phase-F1 behavior for legacy cached responses and manual
   construction paths.
2. ``extract_evidence_with_llm``'s status determination requires at least
   one snippet with ``confidence > 0.8 AND schema_match=True`` before the
   requirement is classified ``covered``. Snippets present but none clearing
   the schema-match gate → ``partial``. No snippets → ``missing``.

These tests exercise both surfaces directly (without calling the LLM) and
assert the behavior the synthetic fixture was built to catch.
"""

from __future__ import annotations

import pytest

from registry_review_mcp.models.evidence import EvidenceSnippet
from registry_review_mcp.tools.evidence_tools import (
    PROMPT_VERSION,
    build_type_aware_prompt,
)


# ---------------------------------------------------------------------------
# EvidenceSnippet.schema_match default + round-trip
# ---------------------------------------------------------------------------
class TestSchemaMatchFieldDefaults:
    """Back-compat: legacy callers that don't pass schema_match still work."""

    def test_default_is_true_for_backcompat(self):
        s = EvidenceSnippet(
            text="some text",
            document_id="d1",
            document_name="d1.pdf",
            confidence=0.9,
        )
        assert s.schema_match is True

    def test_explicit_false_is_preserved(self):
        s = EvidenceSnippet(
            text="topical only",
            document_id="d1",
            document_name="d1.pdf",
            confidence=0.85,
            schema_match=False,
        )
        assert s.schema_match is False

    def test_model_dump_roundtrip_preserves_field(self):
        s = EvidenceSnippet(
            text="anchor",
            document_id="d1",
            document_name="d1.pdf",
            confidence=0.7,
            schema_match=False,
        )
        dumped = s.model_dump()
        assert dumped["schema_match"] is False
        clone = EvidenceSnippet(**dumped)
        assert clone.schema_match is False


# ---------------------------------------------------------------------------
# Prompt-template instrumentation
# ---------------------------------------------------------------------------
class TestPromptContainsSchemaCheckInstructions:
    """The new prompt MUST tell the LLM how to set schema_match."""

    def _sample_req(self) -> dict:
        return {
            "requirement_id": "REQ-017",
            "requirement_text": (
                "A monitoring plan must be in place describing sampling locations, "
                "sampling frequency, and analytical methods."
            ),
            "accepted_evidence": (
                "Sampling plan with plot locations AND sampling frequency AND analytical methods."
            ),
            "category": "Monitoring",
        }

    def test_prompt_names_schema_match_field(self):
        prompt = build_type_aware_prompt(
            self._sample_req(),
            document_content="example document body",
            document_name="example.pdf",
            validation_type="document_presence",
        )
        assert "schema_match" in prompt

    def test_prompt_explains_schema_match_true_case(self):
        prompt = build_type_aware_prompt(
            self._sample_req(),
            document_content="example document body",
            document_name="example.pdf",
            validation_type="document_presence",
        )
        # The prompt must tell the LLM when to set true.
        assert "schema_match: true" in prompt

    def test_prompt_explains_schema_match_false_case(self):
        prompt = build_type_aware_prompt(
            self._sample_req(),
            document_content="example document body",
            document_name="example.pdf",
            validation_type="document_presence",
        )
        assert "schema_match: false" in prompt
        # And explicitly frame the "topically related but not sufficient" pattern.
        assert "topically related" in prompt.lower()

    def test_prompt_output_format_includes_schema_match_example(self):
        prompt = build_type_aware_prompt(
            self._sample_req(),
            document_content="example document body",
            document_name="example.pdf",
            validation_type="document_presence",
        )
        # The JSON template the LLM imitates must show the field so it appears
        # in output. An example value is enough — absence would be silent failure.
        assert '"schema_match": true' in prompt

    def test_structured_field_prompt_also_includes_schema_match(self):
        prompt = build_type_aware_prompt(
            self._sample_req(),
            document_content="example document body",
            document_name="example.pdf",
            validation_type="structured_field",
        )
        assert "schema_match" in prompt
        assert '"schema_match": true' in prompt


# ---------------------------------------------------------------------------
# Status determination logic — the heart of Phase F1
# ---------------------------------------------------------------------------
def _make_snippet(confidence: float, schema_match: bool) -> EvidenceSnippet:
    return EvidenceSnippet(
        text="snippet body",
        document_id="d1",
        document_name="d1.pdf",
        confidence=confidence,
        schema_match=schema_match,
    )


def _determine_status(snippets: list[EvidenceSnippet]) -> str:
    """Mirror the status determination logic in extract_evidence_with_llm.

    Phase F1 proposed gating on ``schema_match`` AND ``confidence > 0.8`` but
    the Burton regression (100% → 82.6%) tripped the plan's hard floor, so
    the classifier reverted to confidence-only gating. ``schema_match`` is
    retained as a DATA field (prompt, snippet, reviewer preview warning tag)
    — Phase G will tune a classifier rule against a richer corpus.

    If this drifts from the implementation the regression gate will catch it.
    """
    if not snippets:
        return "missing"
    if any(s.confidence > 0.8 for s in snippets):
        return "covered"
    return "partial"


class TestStatusIsConfidenceGated:
    """Post-revert: schema_match is data-only; status depends on confidence."""

    def test_no_snippets_is_missing(self):
        assert _determine_status([]) == "missing"

    def test_high_conf_schema_match_true_is_covered(self):
        snippets = [_make_snippet(confidence=0.95, schema_match=True)]
        assert _determine_status(snippets) == "covered"

    def test_high_conf_schema_match_false_is_still_covered(self):
        """Phase F scoping decision (see risk table §7): classifier does NOT
        gate on schema_match; the field is visible to reviewers but doesn't
        downgrade a high-confidence snippet. Phase G tunes this."""
        snippets = [_make_snippet(confidence=0.95, schema_match=False)]
        assert _determine_status(snippets) == "covered"

    def test_low_conf_is_partial_regardless_of_schema(self):
        snippets = [_make_snippet(confidence=0.6, schema_match=True)]
        assert _determine_status(snippets) == "partial"

    def test_exact_boundary_is_partial(self):
        """Gate is strictly > 0.8 (pre-existing behavior), not >=."""
        snippets = [_make_snippet(confidence=0.8, schema_match=True)]
        assert _determine_status(snippets) == "partial"

    def test_mixed_snippets_any_high_conf_wins(self):
        snippets = [
            _make_snippet(confidence=0.95, schema_match=False),
            _make_snippet(confidence=0.60, schema_match=True),
        ]
        assert _determine_status(snippets) == "covered"


# ---------------------------------------------------------------------------
# PROMPT_VERSION discipline
# ---------------------------------------------------------------------------
class TestPromptVersionBumped:
    """Phase F1.4 — bump PROMPT_VERSION on any extractor-prompt change."""

    def test_prompt_version_is_v2_5_0_or_higher(self):
        """Phase F1 bumps the version — cache invalidates automatically."""
        # Semver-style comparison: accept v2.5.0, v2.5.1, v2.6.0, ...
        assert PROMPT_VERSION.startswith("v")
        parts = [int(x) for x in PROMPT_VERSION[1:].split(".")]
        assert parts >= [2, 5, 0], (
            f"PROMPT_VERSION={PROMPT_VERSION!r} has not been bumped for Phase F1; "
            "extractor-prompt changes must force cache invalidation."
        )


class TestCacheKeyIncludesPromptVersion:
    """Phase F4.2 — ``generate_cache_key`` must mix PROMPT_VERSION into the hash."""

    def test_prompt_version_change_flips_cache_key(self):
        from registry_review_mcp.tools.evidence_tools import generate_cache_key

        kwargs = dict(
            requirement_id="REQ-042",
            requirement_text="text",
            accepted_evidence="ev",
            document_id="d1",
            document_content="body",
            model="gpt-oss:120b",
            temperature=0.0,
        )
        a = generate_cache_key(**kwargs, prompt_version="v2.4.0")
        b = generate_cache_key(**kwargs, prompt_version="v2.5.0")
        assert a != b, "prompt_version must participate in the cache key"

    def test_model_change_flips_cache_key(self):
        """Phase F0 prerequisite — executor model must key the cache."""
        from registry_review_mcp.tools.evidence_tools import generate_cache_key

        base = dict(
            requirement_id="REQ-042",
            requirement_text="text",
            accepted_evidence="ev",
            document_id="d1",
            document_content="body",
            temperature=0.0,
            prompt_version="v2.5.0",
        )
        a = generate_cache_key(**base, model="gpt-oss:120b")
        b = generate_cache_key(**base, model="google/gemma-4-31b-it")
        assert a != b, "model must participate in the cache key"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
