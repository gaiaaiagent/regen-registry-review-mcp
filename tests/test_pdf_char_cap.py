"""Phase E — PDF char cap RED tests for ``_truncate_markdown_by_chars``.

The Phase D XLSX cap pattern (``MAX_CHARS_PER_SHEET`` / ``MAX_CHARS_PER_WORKBOOK``
in ``spreadsheet_extractor.py``) proved out the two-layer discipline:
a per-unit cap plus an aggregate cap, both annotated with a footer citing
original vs kept character counts so the LLM knows it is looking at a trim.

Phase E ports the same idea to PDFs (and any other doctype the evidence
pipeline hands to ``extract_evidence_with_llm``). CSSCP's Project Plan is
554K chars of markdown and the TELUS gateway times out well before that
payload can be processed; Burton and Rockscape sit at ~62K and should
pass through untouched. The cap is 80K chars — large enough to leave
both Burton and Rockscape Project Plans intact, small enough to shield
the gateway from a 554K payload, and keyed to the same "lazy disk, trim
prompt" philosophy Phase D established.

These are TDD RED tests — the helper ``_truncate_markdown_by_chars`` is
expected to raise ImportError before Phase E3 lands.
"""

from __future__ import annotations

import pytest


def _get_helper():
    """Import the helper lazily so ImportError drives RED until E3 lands."""
    from registry_review_mcp.tools.evidence_tools import _truncate_markdown_by_chars

    return _truncate_markdown_by_chars


class TestUnderCap:
    """Short PDFs should be returned untouched — no footer, no mutation."""

    def test_markdown_below_cap_untouched(self):
        helper = _get_helper()
        short_md = "# Small PDF\n\nJust a few paragraphs of content.\n" * 10
        out = helper(short_md, cap=80_000, source_name="small.pdf")
        assert out == short_md
        assert "Truncated by prompt budget" not in out

    def test_markdown_exactly_at_cap_untouched(self):
        helper = _get_helper()
        md = "x" * 80_000
        out = helper(md, cap=80_000, source_name="edge.pdf")
        assert out == md
        assert len(out) == 80_000
        assert "Truncated" not in out


class TestOverCap:
    """Large PDFs get trimmed + footer cites original and kept counts."""

    def test_markdown_above_cap_truncated_with_footer(self):
        helper = _get_helper()
        # 554K chars mirrors the CSSCP Project Plan real-world size.
        big_md = "## Section\n\n" + ("lorem ipsum dolor sit amet " * 500 + "\n\n") * 50
        assert len(big_md) > 80_000, "test setup must exceed cap"
        original_len = len(big_md)

        out = helper(big_md, cap=80_000, source_name="csscp-project-plan.pdf")

        # Header preserved — truncation cuts the tail, not the head.
        assert out.startswith("## Section")
        # Footer present with both original and kept counts.
        assert "Truncated by prompt budget" in out
        assert f"{original_len:,}" in out
        # Source name cited so downstream review can locate the full doc.
        assert "csscp-project-plan.pdf" in out
        # Total output respects cap + small footer overhead.
        # Footer is ~180 chars; allow 400 headroom.
        assert len(out) <= 80_000 + 400

    def test_truncation_prefers_paragraph_boundary(self):
        helper = _get_helper()
        # Content with clear paragraph boundaries well before cap.
        para = "This is a paragraph of prose about soil carbon.\n\n"
        prefix = para * 1_000  # ~50K chars, all clean boundaries
        tail = "X" * 40_000  # 40K chars of a single run — no boundaries in tail
        big_md = prefix + tail
        assert len(big_md) > 80_000

        out = helper(big_md, cap=80_000, source_name="prose.pdf")

        # We should trim at a paragraph boundary — body should not end mid-run-of-X.
        body_before_footer = out.split("*Truncated by prompt budget")[0].rstrip()
        assert not body_before_footer.endswith("X" * 50)

    def test_truncation_footer_cites_char_counts(self):
        helper = _get_helper()
        big_md = "A" * 200_000
        out = helper(big_md, cap=80_000, source_name="ones.pdf")

        # Footer should cite original (200_000) and kept (≤ 80_000) chars.
        assert "200,000" in out
        # The kept value should be ≤ cap.
        # Parse a plausible "kept first N" integer from the footer.
        import re as _re

        match = _re.search(r"kept first ([\d,]+)", out)
        assert match is not None, f"footer missing 'kept first N' clause: {out[-500:]}"
        kept = int(match.group(1).replace(",", ""))
        assert kept <= 80_000


class TestEdgeCases:
    """Defensive paths — empty string, exact-boundary, missing boundary in tail."""

    def test_empty_markdown_passthrough(self):
        helper = _get_helper()
        out = helper("", cap=80_000, source_name="empty.pdf")
        assert out == ""

    def test_markdown_one_over_cap_still_truncates(self):
        helper = _get_helper()
        md = "x" * 80_001
        out = helper(md, cap=80_000, source_name="off-by-one.pdf")
        assert "Truncated by prompt budget" in out

    def test_no_paragraph_boundary_falls_back_to_hard_cut(self):
        helper = _get_helper()
        # Single enormous run with no \n\n anywhere.
        big_md = "X" * 200_000
        out = helper(big_md, cap=80_000, source_name="run.pdf")

        assert "Truncated by prompt budget" in out
        body = out.split("*Truncated by prompt budget")[0].rstrip()
        # Fallback is hard cut at cap.
        assert len(body) <= 80_000


class TestDefaultCap:
    """Helper should expose a named default that callers can reference."""

    def test_module_exposes_default_cap_constant(self):
        from registry_review_mcp.tools import evidence_tools

        assert hasattr(evidence_tools, "MAX_CHARS_PER_DOCUMENT"), (
            "evidence_tools must expose MAX_CHARS_PER_DOCUMENT as the "
            "authoritative PDF cap so callers and PromptBudget stay in sync."
        )
        cap = evidence_tools.MAX_CHARS_PER_DOCUMENT
        # Must shield against CSSCP's 554K but preserve Burton (61,425) + Rockscape (62,199).
        # Upper bound sits at the TELUS Cloudflare edge-timeout ceiling (~200K chars).
        assert 62_500 < cap <= 200_000, (
            f"MAX_CHARS_PER_DOCUMENT={cap} must be above Burton/Rockscape Project "
            f"Plan natural size (~62K) and at/below observed gateway-timeout threshold (~200K)."
        )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
