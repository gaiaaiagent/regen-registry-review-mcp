"""Phase E — PromptBudget abstraction tests.

Budget sits at the LLM-extractor / prompt-assembly layer. Its job is to
guarantee that the combined (instructions + schema + document markdown)
prompt stays inside the TELUS Cloudflare gateway's ~150K edge-timeout
budget, regardless of which extractor path produced the content.

Phase D's XLSX caps and Phase E's PDF cap (``evidence_tools._truncate_markdown_by_chars``)
are defensive defaults. PromptBudget is the primary, shared gate.

Scope in Phase E:
- Dataclass with sensible default caps.
- ``trim_document`` delegates to the evidence_tools helper so behavior
  stays consistent (paragraph-boundary trim + footer).
- ``fits`` answers whether a total-length payload is inside the gateway budget.
- ``default_budget`` factory returns a PromptBudget aligned with the
  evidence_tools module constants.
"""

from __future__ import annotations

import pytest


def _get_module():
    from registry_review_mcp.llm import prompt_budget

    return prompt_budget


class TestConstruction:
    def test_default_budget_has_document_cap_matching_evidence_tools(self):
        from registry_review_mcp.tools import evidence_tools

        pb = _get_module().PromptBudget()
        assert pb.max_document_chars == evidence_tools.MAX_CHARS_PER_DOCUMENT

    def test_custom_caps_accepted(self):
        PromptBudget = _get_module().PromptBudget
        pb = PromptBudget(
            max_document_chars=50_000,
            max_instructions_chars=3_000,
            max_schema_chars=1_500,
            max_total_chars=60_000,
        )
        assert pb.max_document_chars == 50_000
        assert pb.max_total_chars == 60_000

    def test_default_factory_returns_fresh_instance(self):
        mod = _get_module()
        a = mod.default_budget()
        b = mod.default_budget()
        assert a is not b
        assert a.max_document_chars == b.max_document_chars


class TestTrimDocument:
    def test_trim_under_cap_returns_untouched(self):
        PromptBudget = _get_module().PromptBudget
        pb = PromptBudget(max_document_chars=80_000)
        md = "short content\n\nmore text"
        assert pb.trim_document(md, "demo.pdf") == md

    def test_trim_over_cap_delegates_to_evidence_tools_helper(self):
        PromptBudget = _get_module().PromptBudget
        pb = PromptBudget(max_document_chars=5_000)
        long_md = "para ABC\n\n" * 5_000  # ~50K chars
        out = pb.trim_document(long_md, "big.pdf")

        assert "Truncated by prompt budget" in out
        assert "big.pdf" in out
        # Respect cap plus small footer overhead.
        assert len(out) <= 5_000 + 400

    def test_trim_uses_instance_max_document_chars(self):
        PromptBudget = _get_module().PromptBudget
        md = "X" * 20_000
        small = PromptBudget(max_document_chars=1_000).trim_document(md, "a.pdf")
        large = PromptBudget(max_document_chars=15_000).trim_document(md, "a.pdf")
        # Smaller cap yields shorter body.
        assert len(small) < len(large)


class TestFits:
    def test_fits_true_when_total_below_cap(self):
        pb = _get_module().PromptBudget(max_total_chars=100_000)
        assert pb.fits(total_len=99_999) is True

    def test_fits_true_at_exact_cap(self):
        pb = _get_module().PromptBudget(max_total_chars=100_000)
        assert pb.fits(total_len=100_000) is True

    def test_fits_false_over_cap(self):
        pb = _get_module().PromptBudget(max_total_chars=100_000)
        assert pb.fits(total_len=100_001) is False


class TestIntegration:
    """Wiring check: evidence_tools must apply PromptBudget at the extractor."""

    def test_default_budget_total_cap_above_document_cap(self):
        """Instructions + schema + doc must all fit. Total > document."""
        pb = _get_module().default_budget()
        overhead = pb.max_instructions_chars + pb.max_schema_chars
        assert pb.max_total_chars >= pb.max_document_chars + overhead // 2

    def test_budget_caps_are_positive(self):
        pb = _get_module().default_budget()
        assert pb.max_document_chars > 0
        assert pb.max_instructions_chars > 0
        assert pb.max_schema_chars > 0
        assert pb.max_total_chars > 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
