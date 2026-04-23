"""Reviewer UX — Phase F6 option A.

Renders a ``review.json`` dossier as a self-contained HTML file a human
reviewer can open locally, inspect snippet-by-snippet, override verdicts
with comments, and export as ``overrides.json`` for the feedback loop
into Phase G tuning.

The reviewer surface is deliberately offline-first: no server, no API
calls, single HTML file. Option B (Rolls-embedded React) will graft onto
this data contract when Marie + Alexander are available.
"""

from .preview import render_review_preview, write_review_preview

__all__ = ["render_review_preview", "write_review_preview"]
