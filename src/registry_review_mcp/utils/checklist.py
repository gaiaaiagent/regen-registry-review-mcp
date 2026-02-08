"""Centralized checklist loading with optional scope filtering.

Replaces the repeated json.load() pattern scattered across evidence_tools,
analyze_llm, mapping_tools, session_tools, and C_requirement_mapping.
"""

import json

from ..config.settings import settings


def load_checklist(methodology: str, scope: str | None = None) -> dict:
    """Load a methodology checklist, optionally filtering requirements by scope.

    Args:
        methodology: Methodology identifier (e.g., "soil-carbon-v1.2.2")
        scope: Optional filter -- "farm" for per-farm requirements,
               "meta" for meta-project requirements, or None for all.

    Returns:
        Full checklist dict with filtered requirements list.

    Raises:
        FileNotFoundError: If the checklist file does not exist.
    """
    checklist_path = settings.get_checklist_path(methodology)
    if not checklist_path.exists():
        raise FileNotFoundError(f"Checklist not found: {checklist_path}")

    with open(checklist_path, "r") as f:
        checklist_data = json.load(f)

    if scope is not None:
        checklist_data["requirements"] = [
            req for req in checklist_data.get("requirements", [])
            if req.get("scope") == scope
        ]

    return checklist_data
