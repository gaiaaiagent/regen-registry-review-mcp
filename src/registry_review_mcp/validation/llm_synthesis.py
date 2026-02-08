"""Layer 3: LLM synthesis - holistic coherence assessment via single LLM call.

This layer provides an intelligent sanity check by reviewing all extracted
fields, evidence snippets, and rule-based check results in context.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

from .structural import StructuralValidationResult
from .cross_document import CrossDocumentValidationResult

logger = logging.getLogger(__name__)


@dataclass
class LLMSynthesisResult:
    """Result of LLM synthesis analysis."""
    available: bool = False  # False if LLM not configured
    coherence_score: float | None = None  # 0.0-1.0
    compliance_status: str | None = None  # "compliant", "partial", "non_compliant"
    flags_for_review: list[str] = field(default_factory=list)
    reasoning: str | None = None
    error: str | None = None

    @property
    def flagged_count(self) -> int:
        return len(self.flags_for_review)


def _build_synthesis_prompt(
    all_fields: dict[str, Any],
    evidence_snippets: list[dict],
    structural_results: StructuralValidationResult,
    cross_doc_results: CrossDocumentValidationResult,
    methodology_name: str = "Soil Organic Carbon"
) -> str:
    """Build the synthesis prompt with full context."""

    # Format fields for readability
    fields_summary = json.dumps(all_fields, indent=2, default=str)

    # Format snippets (truncated)
    snippets_summary = []
    for i, snippet in enumerate(evidence_snippets[:10]):  # Limit to 10
        snippets_summary.append({
            "requirement": snippet.get("requirement_id", "unknown"),
            "document": snippet.get("document_name", "unknown")[:40],
            "text": snippet.get("text", "")[:150] + "...",
            "confidence": snippet.get("confidence", 0)
        })

    # Format structural check results
    structural_issues = [
        {"field": c.field_name, "status": c.status, "message": c.message}
        for c in structural_results.checks
        if c.status != "pass"
    ]

    # Format cross-document check results
    cross_doc_issues = [
        {"field": c.field_name, "status": c.status, "message": c.message}
        for c in cross_doc_results.checks
        if c.status != "pass"
    ]

    prompt = f"""You are reviewing extracted evidence from a carbon credit project registration.

## Methodology
{methodology_name}

## Extracted Structured Fields
```json
{fields_summary}
```

## Sample Evidence Snippets ({len(evidence_snippets)} total, showing 10)
```json
{json.dumps(snippets_summary, indent=2)}
```

## Rule-Based Check Issues ({len(structural_issues)} structural, {len(cross_doc_issues)} cross-document)

### Structural Issues:
{json.dumps(structural_issues, indent=2) if structural_issues else "None"}

### Cross-Document Issues:
{json.dumps(cross_doc_issues, indent=2) if cross_doc_issues else "None"}

## Your Task

Review the extracted data holistically and provide:

1. **Coherence Assessment**: Does the data tell a consistent story? Are there contradictions?
2. **Completeness Check**: Are key fields present for methodology compliance?
3. **Reasonableness Review**: Do values make sense in context?
4. **Flags for Human Review**: Specific issues that need human attention.

## Response Format

Respond with JSON only:
```json
{{
  "coherence_score": 0.85,
  "compliance_status": "partial",
  "flags_for_review": [
    "Owner name needs verification against title deed",
    "Project start date should align with baseline sampling"
  ],
  "reasoning": "Brief explanation of your assessment"
}}
```

Where:
- coherence_score: 0.0 (incoherent) to 1.0 (fully coherent)
- compliance_status: "compliant", "partial", or "non_compliant"
- flags_for_review: List of specific actionable items for human reviewer
- reasoning: 2-3 sentences explaining your assessment

Focus on substantive issues. Don't flag minor formatting concerns.
"""
    return prompt


def _parse_llm_response(response_text: str) -> dict[str, Any]:
    """Parse the LLM JSON response."""

    # Try to extract JSON from response
    json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)

    if json_match:
        return json.loads(json_match.group(1))

    # Try to parse entire response as JSON
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to find any JSON object in response
    brace_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response: {response_text[:200]}")


def _collect_evidence_snippets(evidence_data: dict) -> list[dict]:
    """Collect all evidence snippets with their metadata."""
    snippets = []

    for req in evidence_data.get("evidence", []):
        req_id = req.get("requirement_id", "unknown")
        for snippet in req.get("evidence_snippets", []):
            snippets.append({
                "requirement_id": req_id,
                "document_name": snippet.get("document_name", "unknown"),
                "text": snippet.get("text", ""),
                "confidence": snippet.get("confidence", 0),
                "structured_fields": snippet.get("structured_fields")
            })

    return snippets


async def run_llm_synthesis(
    evidence_data: dict,
    all_fields: dict[str, Any],
    structural_results: StructuralValidationResult,
    cross_doc_results: CrossDocumentValidationResult,
    methodology_name: str = "Soil Organic Carbon"
) -> LLMSynthesisResult:
    """Run LLM synthesis for holistic coherence assessment.

    Makes ONE LLM call with full context to provide intelligent sanity check.

    Args:
        evidence_data: Full evidence.json data
        all_fields: Merged structured fields from all snippets
        structural_results: Results from Layer 1 checks
        cross_doc_results: Results from Layer 2 checks
        methodology_name: Name of methodology for context

    Returns:
        LLMSynthesisResult with coherence assessment
    """
    from ..config.settings import settings
    from ..utils.llm_client import call_llm, classify_api_error

    try:
        # Collect evidence snippets
        snippets = _collect_evidence_snippets(evidence_data)

        # Build prompt
        prompt = _build_synthesis_prompt(
            all_fields=all_fields,
            evidence_snippets=snippets,
            structural_results=structural_results,
            cross_doc_results=cross_doc_results,
            methodology_name=methodology_name
        )

        logger.info("Running LLM synthesis for coherence assessment")

        response_text = await call_llm(
            prompt=prompt,
            model=settings.get_active_llm_model(),
            max_tokens=1500,
        )

        # Parse response
        parsed = _parse_llm_response(response_text)

        result = LLMSynthesisResult(
            available=True,
            coherence_score=parsed.get("coherence_score"),
            compliance_status=parsed.get("compliance_status"),
            flags_for_review=parsed.get("flags_for_review", []),
            reasoning=parsed.get("reasoning")
        )

        logger.info(
            f"LLM synthesis complete: coherence={result.coherence_score}, "
            f"compliance={result.compliance_status}, flags={len(result.flags_for_review)}"
        )

        return result

    except Exception as e:
        error_info = classify_api_error(e)
        logger.error(f"LLM synthesis failed ({error_info.category}): {error_info.message}")
        return LLMSynthesisResult(
            available=False,
            error=f"{error_info.message} — {error_info.guidance}"
        )
