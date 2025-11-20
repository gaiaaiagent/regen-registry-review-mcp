"""Unified LLM-native analysis prompt.

This single prompt replaces:
- llm_extractors.py (48,500 chars)
- validation_tools.py (27,707 chars)
- evidence_tools.py (16,460 chars)
- Intelligence modules (28,080 chars)
- metadata_extractors.py (11,608 chars) [Phase 4.1]
- prior_review_detector.py (16,472 chars) [Phase 4.1]

Phase 1 Reduction: 120,747 chars → ~12,000 chars (108,747 chars saved)
Phase 4.1 Addition: +28,080 chars replaced → ~2,000 chars added
Phase 4.1 Net Gain: ~26,080 additional chars saved (93% reduction on new modules)
Total Reduction: 134,827 chars (91% overall reduction in extraction logic)
"""

import json
import logging
import re
from typing import Any
from pydantic import BaseModel, Field


# === Response Schema ===

class EvidenceSnippet(BaseModel):
    """Evidence snippet with citation."""
    text: str = Field(description="Evidence text (50-500 words, include sufficient context for verification)")
    page: int | None = Field(description="Page number (1-indexed)")
    section: str | None = Field(description="Section header")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score")


class MappedDocument(BaseModel):
    """Document mapped to requirement."""
    document_id: str
    document_name: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class RequirementEvidence(BaseModel):
    """Evidence for a single requirement."""
    requirement_id: str
    status: str = Field(description="covered | partial | missing")
    confidence: float = Field(ge=0.0, le=1.0)
    mapped_documents: list[MappedDocument]
    evidence_snippets: list[EvidenceSnippet]
    notes: str | None = None


class ExtractedField(BaseModel):
    """Structured field extraction with citation."""
    field_name: str
    field_value: str
    source_document: str
    page: int | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class ValidationCheck(BaseModel):
    """Cross-document validation result."""
    check_type: str = Field(description="date_alignment | land_tenure | project_id")
    status: str = Field(description="pass | warning | fail")
    message: str
    details: dict[str, Any] | None = None


class ProjectMetadata(BaseModel):
    """Extracted project metadata (replaces metadata_extractors.py)."""
    project_id: str | None = Field(description="Project ID (e.g., C06-4997, VCS1234)")
    proponent: str | None = Field(description="Project developer/proponent name")
    crediting_period_start: str | None = Field(description="Crediting period start date")
    crediting_period_end: str | None = Field(description="Crediting period end date")
    location: str | None = Field(description="Project location (state, county, coordinates)")
    acreage: float | None = Field(description="Project acreage/area")
    credit_class: str | None = Field(description="Credit class (e.g., Soil Carbon)")
    methodology_version: str | None = Field(description="Methodology version (e.g., v1.2.2)")
    vintage_year: int | None = Field(description="Vintage year for credits")
    confidence: float = Field(ge=0.0, le=1.0, description="Overall metadata confidence")


class PriorReviewStatus(BaseModel):
    """Prior review detection result (replaces prior_review_detector.py)."""
    has_prior_review: bool = Field(description="Whether prior review exists")
    review_id: str | None = Field(description="Prior review identifier")
    review_outcome: str | None = Field(description="approved | conditional | rejected | pending")
    reviewer_name: str | None = Field(description="Name of prior reviewer")
    review_date: str | None = Field(description="Date of prior review")
    conditions: list[str] = Field(default_factory=list, description="Conditions from prior review")
    notes: str | None = Field(description="Additional review notes")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence")


class UnifiedAnalysisResult(BaseModel):
    """Complete analysis result from single LLM call."""

    # Evidence extraction (replaces evidence_tools.py)
    requirements_evidence: list[RequirementEvidence]
    requirements_covered: int
    requirements_partial: int
    requirements_missing: int
    overall_coverage: float = Field(ge=0.0, le=1.0)

    # Field extraction (replaces llm_extractors.py)
    extracted_fields: list[ExtractedField]

    # Cross-validation (replaces validation_tools.py)
    validation_checks: list[ValidationCheck]

    # NEW: Project metadata extraction (replaces metadata_extractors.py)
    project_metadata: ProjectMetadata

    # NEW: Prior review detection (replaces prior_review_detector.py)
    prior_review_status: PriorReviewStatus | None = None

    # Quality assessment
    overall_assessment: str
    flagged_items: list[str]


# === Prompt Builder ===

SYSTEM_PROMPT = """You are an expert carbon credit registry reviewer analyzing project documentation against the Regen Network Soil Carbon Methodology v1.2.2.

Your task is to perform a comprehensive analysis in a single pass:

1. **Evidence Extraction**: For each requirement in the checklist:
   - Identify which documents contain relevant evidence
   - Extract specific text snippets with page citations
   - Determine coverage status (covered/partial/missing)
   - Calculate confidence scores based on evidence quality

2. **Structured Field Extraction**: Extract key project metadata:
   - Project start date
   - Crediting period (start and end dates)
   - Land tenure information (owner, rights, documentation)
   - Project ID

   For each field, provide the exact value found, source document, page number, and confidence.

3. **Cross-Document Validation**: Check consistency across documents:
   - Date alignment (same dates across all documents)
   - Land tenure consistency (same owner/rights everywhere)
   - Project ID consistency (same ID in all references)

   Report any discrepancies as warnings or failures.

4. **Project Metadata Extraction**: Extract comprehensive project metadata:
   - Project ID (format: C##-####, VCS####, GS####)
   - Proponent/developer name
   - Crediting period dates (start and end)
   - Project location (state, county, coordinates if available)
   - Project acreage/area
   - Credit class (e.g., Soil Carbon, Grassland)
   - Methodology version (e.g., v1.2.2)
   - Vintage year for credits

   Provide overall confidence score for extracted metadata. Use context and semantic understanding
   to extract values even if formatting varies - you're better at this than regex patterns.

5. **Prior Review Detection**: Check if documents include evidence of a prior registry review:
   - Look for "Registry Review", "Validation Report", "Verification Report" documents
   - Check for review outcomes (approved, conditional approval, rejected, pending)
   - Extract reviewer name and review date
   - Note any conditions or requirements from prior review
   - Extract any review ID or reference number

   Set has_prior_review=true only if clear evidence exists (2+ review indicators).

   **IMPORTANT**: ALWAYS populate prior_review_status - NEVER return null for this field.
   If no prior review found, return:
   {
     "has_prior_review": false,
     "review_id": null,
     "review_outcome": null,
     "reviewer_name": null,
     "review_date": null,
     "conditions": [],
     "notes": null,
     "confidence": 0.95
   }

6. **Quality Assessment**: Provide overall review assessment:
   - Strengths of the documentation
   - Gaps or weaknesses
   - Items that need human review
   - Recommendation (approve/request revisions/reject)

**Important Guidelines**:
- Only cite evidence that actually exists in the documents
- Use exact page numbers from page markers like `![](_page_3_Picture_0.jpeg)`
- Be conservative with confidence scores - only use >0.8 for clear evidence
- Flag any ambiguities or missing information
- Cross-reference information across documents to verify consistency
- Use semantic understanding for metadata - handle format variations naturally
- For prior review detection, require substantial evidence (not just similar keywords)

**CRITICAL OUTPUT FORMAT**:
- You MUST return valid JSON matching the exact schema provided in the prompt
- Use the EXACT field names specified (case-sensitive, required)
- DO NOT invent your own field names or structure
- DO NOT wrap JSON in markdown code blocks
- DO NOT add explanatory text before or after the JSON"""


def format_documents(documents: list[dict[str, Any]], markdown_contents: dict[str, str]) -> str:
    """Format documents for prompt."""
    sections = []

    for doc in documents:
        doc_id = doc["document_id"]
        filename = doc["filename"]
        classification = doc["classification"]
        markdown = markdown_contents.get(doc_id, "")

        # Truncate very long documents (keep first 50K chars)
        if len(markdown) > 50000:
            markdown = markdown[:50000] + "\n\n[... document truncated for length ...]"

        sections.append(f"""
## Document: {filename}
**ID**: {doc_id}
**Classification**: {classification}

{markdown}
""")

    return "\n---\n".join(sections)


def format_requirements(requirements: list[dict[str, Any]]) -> str:
    """Format requirements checklist for prompt."""
    sections = []

    for req in requirements:
        req_id = req["requirement_id"]
        category = req.get("category", "General")
        text = req.get("requirement_text", "")
        evidence = req.get("accepted_evidence", "")

        sections.append(f"""
### {req_id}: {category}
**Requirement**: {text}
**Accepted Evidence**: {evidence}
""")

    return "\n".join(sections)


def build_unified_analysis_prompt(
    documents: list[dict[str, Any]],
    markdown_contents: dict[str, str],
    requirements: list[dict[str, Any]]
) -> str:
    """Build complete analysis prompt.

    Args:
        documents: List of document metadata dicts
        markdown_contents: Dict mapping document_id -> markdown text
        requirements: List of requirement dicts from checklist

    Returns:
        Complete prompt for LLM analysis
    """
    doc_count = len(documents)
    req_count = len(requirements)
    total_chars = sum(len(md) for md in markdown_contents.values())

    # Generate explicit JSON schema for the LLM to follow
    schema = UnifiedAnalysisResult.model_json_schema()
    schema_json = json.dumps(schema, indent=2)

    return f"""# Registry Review Analysis Task

You are analyzing **{doc_count} documents** ({total_chars:,} characters) against **{req_count} requirements** from the Soil Carbon Methodology v1.2.2.

---

# Project Documents

{format_documents(documents, markdown_contents)}

---

# Requirements Checklist

{format_requirements(requirements)}

---

# Your Analysis Task

Perform a complete registry review analysis by:

1. **Evidence Extraction** ({req_count} requirements)
   - For each requirement above, find evidence in the documents
   - Extract text snippets with page numbers and sections
   - Mark status as covered/partial/missing
   - Provide confidence scores

2. **Structured Field Extraction**
   - Project start date (e.g., "1/17/2022")
   - Crediting period start (e.g., "1/17/2022")
   - Crediting period end (e.g., "12/31/2032")
   - Land tenure owner (full name)
   - Land tenure rights (owned/leased/other)
   - Land tenure documentation (deed/lease/agreement)
   - Project ID (e.g., "C06-4997")

3. **Cross-Document Validation**
   - Verify dates are consistent across all documents
   - Verify land tenure information matches everywhere
   - Verify project ID is consistent
   - Flag any discrepancies

4. **Project Metadata Extraction** (NEW - replaces regex patterns)
   Extract comprehensive project metadata using semantic understanding:
   - **project_id**: Project identifier (C06-4997, VCS1234, GS1234, etc.)
   - **proponent**: Project developer/proponent full name
   - **crediting_period_start**: Start date of crediting period
   - **crediting_period_end**: End date of crediting period
   - **location**: Project location (state, county, coordinates)
   - **acreage**: Project acreage or area
   - **credit_class**: Credit class name (Soil Carbon, Grassland, etc.)
   - **methodology_version**: Methodology version (v1.2.2, etc.)
   - **vintage_year**: Vintage year for credits
   - **confidence**: Overall confidence in metadata extraction (0.0-1.0)

   Use context to find these values even with format variations. Return null for missing fields.

5. **Prior Review Detection** (NEW - replaces pattern matching)
   Detect if a prior registry review exists:
   - **has_prior_review**: true if clear evidence of prior review (2+ indicators), false otherwise
   - **review_id**: Prior review identifier if found (null if none)
   - **review_outcome**: "approved" | "conditional" | "rejected" | "pending" (null if none)
   - **reviewer_name**: Name of prior reviewer (null if none)
   - **review_date**: Date of prior review (null if none)
   - **conditions**: List of conditions from prior review (empty list [] if none)
   - **notes**: Additional notes about prior review (null if none)
   - **confidence**: Detection confidence (0.0-1.0, use ~0.95 for clear negative)

   Look for documents titled "Registry Review", "Validation Report", "Verification Report"
   or sections discussing prior review findings. Require substantial evidence.

   **CRITICAL**: ALWAYS populate prior_review_status object - NEVER return null for the entire field.
   If no review detected, set has_prior_review=false with confidence ~0.95.

6. **Overall Assessment**
   - Summarize documentation quality
   - List any gaps or missing information
   - Recommend approval/revisions/rejection

---

# CRITICAL: RESPONSE FORMAT

You MUST return your analysis as JSON matching this EXACT schema.

**USE THESE EXACT FIELD NAMES** (case-sensitive, not suggestions):

```json
{schema_json}
```

**IMPORTANT NOTES**:
1. Field names are EXACT and REQUIRED (not suggestions or alternatives)
2. Use "requirements_evidence" NOT "requirement_analysis"
3. Use "extracted_fields" NOT "structured_data"
4. Use "validation_checks" NOT "cross_document_validation"
5. Return ONLY valid JSON (no markdown wrapper, no explanatory text)

**Example Response Structure**:
```json
{{
  "requirements_evidence": [
    {{
      "requirement_id": "REQ-001",
      "status": "covered",
      "confidence": 0.95,
      "mapped_documents": [
        {{
          "document_id": "DOC-abc123",
          "document_name": "ProjectPlan.pdf",
          "relevance_score": 0.95
        }}
      ],
      "evidence_snippets": [
        {{
          "text": "Evidence text from document...",
          "page": 5,
          "section": "Section Title",
          "confidence": 0.95
        }}
      ],
      "notes": "Analysis notes"
    }}
  ],
  "requirements_covered": 15,
  "requirements_partial": 5,
  "requirements_missing": 3,
  "overall_coverage": 0.87,
  "extracted_fields": [
    {{
      "field_name": "project_start_date",
      "field_value": "1/17/2022",
      "source_document": "DOC-abc123",
      "page": 5,
      "confidence": 0.95
    }}
  ],
  "validation_checks": [
    {{
      "check_type": "date_alignment",
      "status": "pass",
      "message": "All dates consistent across documents",
      "details": {{"verified_documents": ["DOC-1", "DOC-2"]}}
    }}
  ],
  "project_metadata": {{
    "project_id": "C06-4997",
    "proponent": "Botany Bay Farm LLC",
    "crediting_period_start": "1/17/2022",
    "crediting_period_end": "12/31/2032",
    "location": "McLean County, North Dakota",
    "acreage": 1247.5,
    "credit_class": "Soil Carbon",
    "methodology_version": "v1.2.2",
    "vintage_year": 2023,
    "confidence": 0.92
  }},
  "prior_review_status": {{
    "has_prior_review": false,
    "review_id": null,
    "review_outcome": null,
    "reviewer_name": null,
    "review_date": null,
    "conditions": [],
    "notes": null,
    "confidence": 0.95
  }},
  "overall_assessment": "Project documentation is comprehensive and well-organized...",
  "flagged_items": ["Missing land tenure deed", "Date discrepancy in monitoring report"]
}}
```

**Note**: If prior review IS detected, populate prior_review_status like:
```json
  "prior_review_status": {{
    "has_prior_review": true,
    "review_id": "REV-2023-001",
    "review_outcome": "conditional",
    "reviewer_name": "Sarah Johnson",
    "review_date": "03/15/2023",
    "conditions": ["Update soil sampling protocol", "Provide additional baseline data"],
    "notes": "Project approved with minor conditions",
    "confidence": 0.88
  }}
```

**Critical**: Only cite evidence that exists. Use actual page numbers from page markers. Be honest about missing information."""


# === LLM Call Function ===

async def analyze_with_llm(
    documents: list[dict[str, Any]],
    markdown_contents: dict[str, str],
    requirements: list[dict[str, Any]],
    anthropic_client: Any
) -> UnifiedAnalysisResult:
    """Perform unified analysis with single LLM call.

    This replaces:
    - Multiple calls in llm_extractors.py (3 extractors × N chunks)
    - Multiple calls in evidence_tools.py (N requirements)
    - Multiple calls in validation_tools.py (3-5 validation checks)

    Total current calls: ~100+
    New approach: 1 call (with prompt caching for 90% cost reduction)

    Args:
        documents: Document metadata
        markdown_contents: Full markdown for each document
        requirements: Requirements checklist
        anthropic_client: Anthropic API client

    Returns:
        Complete analysis result

    Raises:
        DocumentExtractionError: If LLM call fails
    """
    from ..models.errors import DocumentExtractionError

    # Build prompt with embedded schema
    prompt = build_unified_analysis_prompt(documents, markdown_contents, requirements)

    # The schema is now embedded in the prompt, no need for additional instruction
    logger = logging.getLogger(__name__)

    try:
        # Single LLM call - Note: Claude currently doesn't support tool_choice for structured output
        # so we rely on prompt engineering to get JSON
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=16000,
            temperature=0,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}  # Cache system prompt
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                            "cache_control": {"type": "ephemeral"}  # Cache documents
                        }
                    ]
                }
            ]
        )

        # Extract JSON from response
        result_text = response.content[0].text

        # Log first 1000 chars for debugging
        logger.debug(f"LLM response (first 1000 chars): {result_text[:1000]}")

        # Try to extract JSON if wrapped in markdown code block
        if result_text.strip().startswith("```"):
            # Extract content between ```json and ```
            json_match = re.search(r'```(?:json)?\s*\n(.*?)\n```', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(1)
            else:
                # Try without language specifier
                result_text = result_text.strip().removeprefix("```").removesuffix("```").strip()

        # Parse and validate with Pydantic
        result_data = json.loads(result_text)
        result = UnifiedAnalysisResult(**result_data)

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response. First 2000 chars:\n{result_text[:2000]}")
        raise DocumentExtractionError(
            f"Failed to parse LLM response as JSON: {str(e)}",
            details={"response_preview": result_text[:1000]}
        )
    except Exception as e:
        raise DocumentExtractionError(
            f"LLM analysis failed: {str(e)}",
            details={"error_type": type(e).__name__}
        )
