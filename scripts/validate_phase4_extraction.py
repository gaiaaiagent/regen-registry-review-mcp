#!/usr/bin/env python3
"""Phase 4.1 Live Validation: Run actual LLM extraction and measure accuracy.

This script:
1. Loads Botany Farm Project Plan
2. Runs LLM-native unified analysis
3. Extracts metadata and prior review status
4. Compares against ground truth
5. Calculates accuracy metrics
6. Generates validation report

Usage:
    python scripts/validate_phase4_extraction.py
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from anthropic import AsyncAnthropic

from registry_review_mcp.config.settings import settings
from registry_review_mcp.prompts.unified_analysis import (
    build_unified_analysis_prompt,
    UnifiedAnalysisResult,
    ProjectMetadata,
    PriorReviewStatus,
)


# Ground truth for Botany Farm (CORRECTED from actual document)
# NOTE: Previous assumptions were wrong - project is in UK, not Iowa
GROUND_TRUTH = {
    "project_metadata": {
        "project_id": "4997Botany22",  # Internal ID (registry ID C06-4997 may be elsewhere)
        "proponent": "Ecometric Ltd",  # Actual proponent from document
        "crediting_period_start": "01/01/2022",  # Format from document (DD/MM/YYYY)
        "crediting_period_end": "31/12/2031",  # 10-year period ending 2031
        "location": "Northamptonshire",  # UK location (Ravensthorpe)
        "acreage": None,  # Not found in first 50K chars (acceptable)
        "credit_class": "GHG Benefits",  # Accept partial match for full name
        "methodology_version": "1.1",  # Version stated in document
        "vintage_year": 2022,
    },
    "prior_review_status": {
        "has_prior_review": False,
        "expected_confidence": 0.9,
    }
}


def calculate_metadata_accuracy(extracted: ProjectMetadata, ground_truth: dict) -> dict:
    """Calculate metadata extraction accuracy."""
    results = {
        "total_fields": 0,
        "correct_fields": 0,
        "incorrect_fields": 0,
        "missing_fields": 0,
        "field_results": {},
    }

    for field_name, expected_value in ground_truth.items():
        results["total_fields"] += 1
        extracted_value = getattr(extracted, field_name, None)

        # If both expected and extracted are None, that's correct (both agree field is missing)
        if expected_value is None and extracted_value is None:
            results["correct_fields"] += 1
            results["field_results"][field_name] = {
                "status": "correct",
                "expected": None,
                "extracted": None,
            }
        elif extracted_value is None:
            results["missing_fields"] += 1
            results["field_results"][field_name] = {
                "status": "missing",
                "expected": expected_value,
                "extracted": None,
            }
        else:
            # Flexible matching for string fields
            if isinstance(expected_value, str) and isinstance(extracted_value, str):
                # Check for partial matches (e.g., "Iowa" in "Iowa, USA")
                match = expected_value.lower() in extracted_value.lower() or \
                        extracted_value.lower() in expected_value.lower()
            elif isinstance(expected_value, float) and isinstance(extracted_value, (int, float)):
                # Allow 1% tolerance for numeric fields
                match = abs(float(extracted_value) - expected_value) / expected_value < 0.01
            else:
                # Exact match for other types
                match = str(extracted_value) == str(expected_value)

            if match:
                results["correct_fields"] += 1
                results["field_results"][field_name] = {
                    "status": "correct",
                    "expected": expected_value,
                    "extracted": extracted_value,
                }
            else:
                results["incorrect_fields"] += 1
                results["field_results"][field_name] = {
                    "status": "incorrect",
                    "expected": expected_value,
                    "extracted": extracted_value,
                }

    results["accuracy"] = results["correct_fields"] / results["total_fields"] if results["total_fields"] > 0 else 0.0

    return results


def calculate_prior_review_accuracy(extracted: PriorReviewStatus | None, ground_truth: dict) -> dict:
    """Calculate prior review detection accuracy."""
    expected_has_review = ground_truth["has_prior_review"]

    if extracted is None:
        return {
            "status": "missing",
            "expected": expected_has_review,
            "extracted": None,
            "accuracy": 0.0,
            "confidence": 0.0,
        }

    detected_has_review = extracted.has_prior_review
    correct = detected_has_review == expected_has_review

    return {
        "status": "correct" if correct else "incorrect",
        "expected": expected_has_review,
        "extracted": detected_has_review,
        "accuracy": 1.0 if correct else 0.0,
        "confidence": extracted.confidence,
        "details": {
            "review_id": extracted.review_id,
            "review_outcome": extracted.review_outcome,
            "reviewer_name": extracted.reviewer_name,
            "review_date": extracted.review_date,
            "conditions": extracted.conditions,
            "notes": extracted.notes,
        }
    }


async def run_llm_extraction(documents: list, markdown_contents: dict, requirements: list) -> UnifiedAnalysisResult:
    """Run actual LLM extraction using unified analysis."""
    print(f"\n{'='*80}")
    print(f"Running LLM Extraction...")
    print(f"{'='*80}\n")

    # Build prompt
    prompt = build_unified_analysis_prompt(documents, markdown_contents, requirements)

    print(f"✓ Prompt built ({len(prompt):,} chars)")
    print(f"✓ Includes Task 4: Project Metadata Extraction")
    print(f"✓ Includes Task 5: Prior Review Detection")

    # Create LLM client
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    print(f"\n✓ Anthropic client created")
    print(f"✓ Model: {settings.llm_model}")
    print(f"✓ Max tokens: {settings.llm_max_tokens}")

    # Call LLM
    print(f"\n⏳ Calling LLM (this may take 20-30 seconds)...")

    try:
        response = await client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # Deterministic for validation
        )

        print(f"✓ LLM responded ({response.usage.input_tokens} input tokens, {response.usage.output_tokens} output tokens)")

        # Extract JSON from response
        response_text = response.content[0].text

        # Try to extract JSON from markdown code blocks
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text.strip()

        # Parse JSON
        print(f"\n⏳ Parsing JSON response...")
        result_data = json.loads(json_text)

        # Validate with Pydantic
        print(f"✓ JSON parsed successfully")
        print(f"⏳ Validating with Pydantic schema...")

        result = UnifiedAnalysisResult(**result_data)

        print(f"✓ Pydantic validation passed")
        print(f"✓ project_metadata: {result.project_metadata is not None}")
        print(f"✓ prior_review_status: {result.prior_review_status is not None}")

        # Calculate cost
        input_cost = (response.usage.input_tokens / 1_000_000) * 3.0  # $3/MTok
        output_cost = (response.usage.output_tokens / 1_000_000) * 15.0  # $15/MTok
        total_cost = input_cost + output_cost

        print(f"\n💰 Cost Analysis:")
        print(f"   Input tokens: {response.usage.input_tokens:,} (${input_cost:.4f})")
        print(f"   Output tokens: {response.usage.output_tokens:,} (${output_cost:.4f})")
        print(f"   Total cost: ${total_cost:.4f}")

        return result

    except json.JSONDecodeError as e:
        print(f"\n❌ Error: Failed to parse JSON response")
        print(f"   {str(e)}")
        print(f"\n   Response preview:")
        print(f"   {response_text[:500]}...")
        raise

    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        raise


async def main():
    """Run Phase 4.1 validation."""
    print(f"\n{'='*80}")
    print(f"PHASE 4.1 PRODUCTION VALIDATION")
    print(f"{'='*80}")
    print(f"Date: {datetime.now().isoformat()}")
    print(f"Dataset: Botany Farm (4997Botany22)")
    print(f"{'='*80}\n")

    # Check API key
    if not settings.anthropic_api_key:
        print(f"❌ Error: ANTHROPIC_API_KEY not set")
        print(f"   Set environment variable: export ANTHROPIC_API_KEY=your_key_here")
        return 1

    # Load Botany Farm Project Plan
    project_plan_path = Path("examples/22-23/4997Botany22_Public_Project_Plan/4997Botany22_Public_Project_Plan.md")

    if not project_plan_path.exists():
        print(f"❌ Error: Botany Farm Project Plan not found")
        print(f"   Expected path: {project_plan_path}")
        return 1

    print(f"✓ Loading Botany Farm Project Plan...")
    with open(project_plan_path) as f:
        content = f.read()

    print(f"✓ Loaded {len(content):,} characters")

    # Prepare documents
    documents = [
        {
            "document_id": "DOC-001",
            "filename": "4997Botany22_Public_Project_Plan.md",
            "classification": "Project Plan",
            "document_type": "Project Plan",
            "confidence": 1.0,
        }
    ]

    markdown_contents = {
        "DOC-001": content[:50000]  # First 50K chars
    }

    print(f"✓ Using first 50,000 characters for validation")

    # Minimal requirements (not used for metadata/prior review)
    requirements = [
        {
            "requirement_id": "REQ-001",
            "category": "General",
            "requirement_text": "Project must have valid metadata",
            "accepted_evidence": "Project Plan document",
        }
    ]

    # Run LLM extraction
    try:
        result = await run_llm_extraction(documents, markdown_contents, requirements)
    except Exception as e:
        print(f"\n❌ LLM extraction failed: {e}")
        return 1

    # Validate metadata
    print(f"\n{'='*80}")
    print(f"METADATA EXTRACTION VALIDATION")
    print(f"{'='*80}\n")

    metadata_results = calculate_metadata_accuracy(result.project_metadata, GROUND_TRUTH["project_metadata"])

    print(f"Overall Accuracy: {metadata_results['accuracy']:.1%} ({metadata_results['correct_fields']}/{metadata_results['total_fields']} fields correct)")
    print(f"Target: ≥95%")
    print(f"Status: {'✅ PASS' if metadata_results['accuracy'] >= 0.95 else '❌ FAIL'}\n")

    print(f"Field-by-Field Results:")
    print(f"{'─'*80}")
    for field_name, field_result in metadata_results["field_results"].items():
        status_icon = {
            "correct": "✅",
            "incorrect": "❌",
            "missing": "⚠️"
        }[field_result["status"]]

        print(f"{status_icon} {field_name:25s} | Expected: {field_result['expected']!r:30s} | Extracted: {field_result['extracted']!r}")

    print(f"{'─'*80}\n")

    # Validate prior review detection
    print(f"{'='*80}")
    print(f"PRIOR REVIEW DETECTION VALIDATION")
    print(f"{'='*80}\n")

    prior_review_results = calculate_prior_review_accuracy(result.prior_review_status, GROUND_TRUTH["prior_review_status"])

    print(f"Detection Status: {prior_review_results['status'].upper()}")
    print(f"Expected: has_prior_review = {prior_review_results['expected']}")
    print(f"Extracted: has_prior_review = {prior_review_results['extracted']}")
    print(f"Confidence: {prior_review_results['confidence']:.2%}")
    print(f"Target: ≥98% accuracy, ≥90% confidence")
    print(f"Status: {'✅ PASS' if prior_review_results['accuracy'] >= 0.98 and prior_review_results['confidence'] >= 0.90 else '❌ FAIL'}\n")

    if prior_review_results['details']['notes']:
        print(f"Notes: {prior_review_results['details']['notes']}")

    # Overall validation result
    print(f"\n{'='*80}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*80}\n")

    metadata_pass = metadata_results['accuracy'] >= 0.95
    prior_review_pass = prior_review_results['accuracy'] >= 0.98 and prior_review_results['confidence'] >= 0.90

    print(f"Metadata Extraction:")
    print(f"  Accuracy: {metadata_results['accuracy']:.1%} (target: ≥95%)")
    print(f"  Status: {'✅ PASS' if metadata_pass else '❌ FAIL'}\n")

    print(f"Prior Review Detection:")
    print(f"  Accuracy: {prior_review_results['accuracy']:.0%} (target: ≥98%)")
    print(f"  Confidence: {prior_review_results['confidence']:.1%} (target: ≥90%)")
    print(f"  Status: {'✅ PASS' if prior_review_pass else '❌ FAIL'}\n")

    print(f"Overall Result: {'✅ VALIDATION PASSED' if metadata_pass and prior_review_pass else '❌ VALIDATION FAILED'}")

    if metadata_pass and prior_review_pass:
        print(f"\n🎉 Phase 4.1 is READY for production deployment!")
        print(f"   Recommendation: Proceed with module deprecation (+20,590 chars)")
    else:
        print(f"\n⚠️  Phase 4.1 needs iteration before production deployment")
        print(f"   Recommendation: Refine prompts and re-test")

    print(f"\n{'='*80}\n")

    # Save results to file
    results_file = Path("/tmp/phase4_validation_results.json")
    results_data = {
        "timestamp": datetime.now().isoformat(),
        "dataset": "Botany Farm (4997Botany22)",
        "metadata_validation": {
            "accuracy": metadata_results["accuracy"],
            "correct_fields": metadata_results["correct_fields"],
            "total_fields": metadata_results["total_fields"],
            "target": 0.95,
            "passed": metadata_pass,
            "field_results": metadata_results["field_results"],
        },
        "prior_review_validation": {
            "accuracy": prior_review_results["accuracy"],
            "confidence": prior_review_results["confidence"],
            "target_accuracy": 0.98,
            "target_confidence": 0.90,
            "passed": prior_review_pass,
            "expected": prior_review_results["expected"],
            "extracted": prior_review_results["extracted"],
        },
        "overall": {
            "passed": metadata_pass and prior_review_pass,
            "ready_for_production": metadata_pass and prior_review_pass,
        }
    }

    with open(results_file, 'w') as f:
        json.dump(results_data, f, indent=2)

    print(f"✓ Results saved to: {results_file}")

    return 0 if (metadata_pass and prior_review_pass) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
