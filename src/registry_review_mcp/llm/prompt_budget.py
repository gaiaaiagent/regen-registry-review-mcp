"""Prompt-budget accounting for the LLM extractor layer.

Phase D capped spreadsheet markdown at the extractor boundary
(``MAX_CHARS_PER_SHEET`` / ``MAX_CHARS_PER_WORKBOOK``). Phase E ports the
same two-layer discipline to PDFs via ``evidence_tools.MAX_CHARS_PER_DOCUMENT``
and now lifts both into a single abstraction so any new doctype
(shapefile, DOCX, email archive, GeoTIFF sidecar, ...) inherits the
same budget discipline automatically.

Design principles:

1. **Disk stays canonical.** The budget trims at prompt-assembly time;
   on-disk markdown retains full fidelity so reviewers can audit what
   was cut.

2. **Paragraph-boundary preferred.** We delegate to
   :func:`evidence_tools._truncate_markdown_by_chars` so the trim
   behavior and footer annotation stay identical between the helper
   and the budget object. One truth, two entry points.

3. **Gateway-first.** The default ``max_total_chars`` sits below the
   ~150K char threshold where TELUS Cloudflare gateway 504s were
   observed during Phase D.

4. **Defense in depth.** Extractor-layer caps remain as defensive
   defaults. PromptBudget is the primary gate; extractors defend
   against callers that skip the budget (offline debugging, unit
   tests, direct extractor invocation).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptBudget:
    """Budget for a single LLM prompt payload.

    All caps are measured in characters. We use chars rather than tokens
    because the constraint we are defending against — the Cloudflare
    edge-timeout — is char/byte-rate bound at the gateway layer, and
    char counting is O(1) without a tokenizer dependency.

    Attributes:
        max_document_chars: Cap on the extracted document markdown.
            Defaults to ``evidence_tools.MAX_CHARS_PER_DOCUMENT`` so
            the budget and the standalone helper stay in sync.
        max_instructions_chars: Cap on the extractor instructions
            (structured-field guidance, evidence prompt, etc.).
        max_schema_chars: Cap on the JSON schema / output-format block.
        max_total_chars: Hard ceiling on the assembled prompt. Sits
            below the TELUS Cloudflare gateway timeout threshold.
    """

    max_document_chars: int = 80_000
    max_instructions_chars: int = 8_000
    max_schema_chars: int = 2_000
    max_total_chars: int = 100_000

    def __post_init__(self) -> None:
        # Import lazily to avoid a module-import cycle: evidence_tools
        # exposes the historical constant, but the budget is authoritative.
        from ..tools import evidence_tools

        # If the caller explicitly set a custom cap, respect it. Otherwise
        # default to the module constant so a single knob changes both.
        if self.max_document_chars == 80_000:
            self.max_document_chars = evidence_tools.MAX_CHARS_PER_DOCUMENT

    def trim_document(self, content: str, source_name: str) -> str:
        """Return ``content`` trimmed to ``max_document_chars``.

        Delegates to :func:`evidence_tools._truncate_markdown_by_chars`
        so the footer format, paragraph-boundary preference, and
        hard-cut fallback stay consistent across the repository.
        """
        from ..tools.evidence_tools import _truncate_markdown_by_chars

        return _truncate_markdown_by_chars(
            content, cap=self.max_document_chars, source_name=source_name
        )

    def fits(self, total_len: int) -> bool:
        """True when ``total_len`` chars fit inside ``max_total_chars``."""
        return total_len <= self.max_total_chars


def default_budget() -> PromptBudget:
    """Factory returning a fresh ``PromptBudget`` at the repo defaults.

    Prefer this over sharing a module-level instance when you want to
    mutate the budget per-call (e.g. tighter caps during stress tests).
    """
    return PromptBudget()


# Module-level reference for callers that want a shared instance. Because
# ``PromptBudget`` is a dataclass with immutable semantics in practice
# (nobody mutates caps mid-run), sharing an instance is safe.
DEFAULT_BUDGET = default_budget()
