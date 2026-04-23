"""LLM-layer infrastructure: prompt-budget accounting and throttle discipline.

Phase E introduced this package to hold the shared gates that every
extractor path passes through before the prompt reaches ``call_llm``:

- :mod:`prompt_budget`: cap document markdown at a safe edge-timeout
  budget with a boundary-aware, footer-annotated trim.
- :mod:`throttle` (Phase E5): limit aggregate concurrency + interval
  between LLM calls to keep the TELUS Cloudflare gateway happy.

Extractor-layer caps (``spreadsheet_extractor.MAX_CHARS_PER_SHEET`` etc.)
remain as defensive defaults for offline debugging. The shared gates in
this package are the primary discipline.
"""

from .prompt_budget import DEFAULT_BUDGET, PromptBudget, default_budget

__all__ = ["DEFAULT_BUDGET", "PromptBudget", "default_budget"]
