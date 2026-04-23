"""Phase F6 — standalone HTML reviewer preview.

Reads a ``review.json`` dossier produced by the pipeline, renders it through
``templates/review-preview.html.j2`` as a self-contained HTML file with:

- Headline coverage stats (covered / partial / missing / overall %).
- One row per requirement, expandable to show evidence snippets with page +
  section + confidence + schema-match tags.
- Override dropdown per requirement (covered / partial / missing / flagged).
- Free-text comment per requirement for the audit trail.
- Export button that downloads ``overrides.json`` with the reviewer's deltas.

No server. No network. No build step. One file in, one file out.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------
def _templates_dir() -> Path:
    """Locate the packaged ``templates/`` directory.

    Lives inside the reviewer package so pip-installed copies of the wheel
    carry the template alongside the Python code. Layout:

        src/registry_review_mcp/reviewer/preview.py     <- this file
        src/registry_review_mcp/reviewer/templates/*.j2 <- target

    Phase F6 originally placed the template at the repo root, but that
    location is outside the build's ``src/`` layout and would have been
    absent from the published wheel.
    """
    return Path(__file__).resolve().parent / "templates"


# ---------------------------------------------------------------------------
# Review → template context
# ---------------------------------------------------------------------------
@dataclass
class ReviewContext:
    fixture_name: str
    model_name: str
    methodology_name: str
    run_date: str
    n_requirements: int
    covered_count: int
    partial_count: int
    missing_count: int
    coverage_pct: int
    requirements: list[dict[str, Any]]


def _coerce_review(review: dict[str, Any]) -> ReviewContext:
    """Normalize a ``review.json`` dict into the shape the template expects.

    Fields are pulled defensively because the ``review.json`` schema has
    evolved across phases A–E. Missing fields default to safe placeholders so
    the template always renders, even on partial dossiers.
    """
    requirements = review.get("requirements", []) or []

    covered = sum(1 for r in requirements if r.get("status") == "covered")
    partial = sum(1 for r in requirements if r.get("status") == "partial")
    missing = sum(1 for r in requirements if r.get("status") in ("missing", "flagged", None))
    n = len(requirements)
    coverage_pct = int(round(100 * covered / n)) if n else 0

    # The Phase E/F review format keeps snippets inside each requirement as
    # ``evidence_snippets``. Older dossiers may flatten snippets into a top
    # level list with ``requirement_id`` back-refs; we don't touch those —
    # the template's ``req.evidence_snippets`` loop tolerates an empty list.
    return ReviewContext(
        fixture_name=review.get("fixture_name") or review.get("project_name") or review.get("session_id", "review"),
        model_name=review.get("model") or review.get("telemetry", {}).get("model", {}).get("name", "unknown"),
        methodology_name=review.get("methodology", "Ecometric Soil Carbon v1.2.2"),
        run_date=review.get("run_date") or review.get("extracted_at") or datetime.now(timezone.utc).isoformat(),
        n_requirements=n,
        covered_count=covered,
        partial_count=partial,
        missing_count=missing,
        coverage_pct=coverage_pct,
        requirements=requirements,
    )


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_review_preview(review: dict[str, Any]) -> str:
    """Render a ``review.json`` dict as HTML. Returns the rendered string."""
    # Import jinja2 lazily so non-reviewer code paths don't pay its import cost.
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    env = Environment(
        loader=FileSystemLoader(_templates_dir()),
        autoescape=select_autoescape(enabled_extensions=("html", "j2", "html.j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Register ``none`` checks for Jinja2 — the default ``is not none`` works
    # via ``Undefined`` which matches our dataclass pattern.
    tmpl = env.get_template("review-preview.html.j2")
    ctx = _coerce_review(review)
    return tmpl.render(**ctx.__dict__)


def write_review_preview(review_json_path: Path, out_path: Path | None = None) -> Path:
    """Read ``review_json_path``, render to HTML, write to ``out_path``.

    If ``out_path`` is None, writes alongside the review JSON with suffix
    ``-preview.html``. Returns the final output path.
    """
    review = json.loads(Path(review_json_path).read_text())
    html = render_review_preview(review)
    if out_path is None:
        out_path = Path(review_json_path).with_name(Path(review_json_path).stem + "-preview.html")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# CLI — ``uv run python -m registry_review_mcp.reviewer.preview <review.json>``
# ---------------------------------------------------------------------------
def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("review_json", type=Path, help="Path to review.json dossier")
    ap.add_argument(
        "-o",
        "--out",
        type=Path,
        default=None,
        help="Output HTML path (default: <review>-preview.html)",
    )
    args = ap.parse_args()

    out = write_review_preview(args.review_json, args.out)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
