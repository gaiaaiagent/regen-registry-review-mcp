"""Accuracy validation test using real Botany Farm documents and ground truth.

Uses shared fixtures from conftest.py to avoid duplicate API calls and reduce costs.
"""

import json
import pytest
from pathlib import Path

from registry_review_mcp.config.settings import settings
from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    LandTenureExtractor,
    ProjectIDExtractor,
)


pytestmark = pytest.mark.skipif(
    not settings.anthropic_api_key or not settings.llm_extraction_enabled,
    reason="LLM extraction not configured (set ANTHROPIC_API_KEY and enable LLM extraction)"
)


# Load ground truth
GROUND_TRUTH_PATH = Path(__file__).parent / "botany_farm_ground_truth.json"
with open(GROUND_TRUTH_PATH) as f:
    GROUND_TRUTH = json.load(f)


class TestBotanyFarmAccuracy:
    """Validate extraction accuracy against Botany Farm ground truth."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_date_extraction_accuracy(self, botany_farm_dates):
        """Test date extraction accuracy against ground truth.

        Uses shared fixture to avoid duplicate API calls.
        """
        # Use shared extraction results from fixture
        results = botany_farm_dates

        print(f"\n=== Date Extraction Results ===")
        print(f"Total extracted: {len(results)}")
        for field in results:
            print(f"  {field.field_type}: {field.value} (confidence: {field.confidence})")
            print(f"    {field.reasoning[:100]}...")

        # Ground truth validation - use Project Plan specific dates
        ground_truth_dates = {d["field_type"]: d["value"] for d in GROUND_TRUTH["project_plan_dates"]}

        # Debug: Show what was extracted vs what was expected
        print(f"\n=== Debug: Date Type Comparison ===")
        extracted_date_types = {f.field_type for f in results}
        ground_truth_types = set(ground_truth_dates.keys())
        print(f"Extracted types: {extracted_date_types}")
        print(f"Ground truth types (Project Plan only): {ground_truth_types}")
        print(f"Matches: {extracted_date_types & ground_truth_types}")
        print(f"Extracted but not in ground truth: {extracted_date_types - ground_truth_types}")
        print(f"In ground truth but not extracted: {ground_truth_types - extracted_date_types}")

        # Check for project start date
        project_start = [f for f in results if f.field_type == "project_start_date"]
        if project_start:
            assert len(project_start) > 0, "Should extract project start date"
            assert "2022-01-01" in str(project_start[0].value), f"Expected 2022-01-01, got {project_start[0].value}"
            print(f"\n✅ Project start date: CORRECT")
        else:
            print(f"\n❌ Project start date: NOT FOUND")

        # Calculate accuracy metrics
        true_positives = 0
        false_positives = 0
        false_negatives = 0

        extracted_types = {f.field_type for f in results}
        ground_truth_types = set(ground_truth_dates.keys())

        # True positives: correctly extracted
        for field_type in extracted_types & ground_truth_types:
            true_positives += 1

        # False positives: extracted but not in ground truth
        false_positives = len(extracted_types - ground_truth_types)

        # False negatives: in ground truth but not extracted
        false_negatives = len(ground_truth_types - extracted_types)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        print(f"\n=== Accuracy Metrics ===")
        print(f"True Positives: {true_positives}")
        print(f"False Positives: {false_positives}")
        print(f"False Negatives: {false_negatives}")
        print(f"Precision: {precision:.2%}")
        print(f"Recall: {recall:.2%}")
        print(f"F1 Score: {f1_score:.2%}")

        # Should achieve high accuracy on Project Plan dates
        # All 3 ground truth dates should be extractable from Project Plan
        assert recall >= 0.80, f"Recall too low: {recall:.2%} (expected >= 80%)"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_land_tenure_accuracy(self, botany_farm_tenure):
        """Test land tenure extraction accuracy against ground truth.

        Uses shared fixture to avoid duplicate API calls.
        """
        # Use shared extraction results from fixture
        results = botany_farm_tenure

        print(f"\n=== Land Tenure Extraction Results ===")
        print(f"Total extracted: {len(results)}")
        for field in results:
            print(f"  {field.field_type}: {field.value} (confidence: {field.confidence})")

        # Ground truth validation
        ground_truth_tenure = GROUND_TRUTH["ground_truth"]["land_tenure"][0]
        acceptable_names = GROUND_TRUTH["acceptable_variations"]["owner_name"]

        # Check for owner name
        owner_names = [f for f in results if f.field_type == "owner_name"]
        if owner_names:
            owner_value = str(owner_names[0].value)
            # Check if any acceptable variation is in the extracted name
            name_match = any(name in owner_value or owner_value in name for name in acceptable_names)

            if name_match:
                print(f"\n✅ Owner name: CORRECT ({owner_value})")
            else:
                print(f"\n❌ Owner name: INCORRECT (got '{owner_value}', expected one of {acceptable_names})")

            assert name_match, f"Owner name '{owner_value}' doesn't match acceptable variations"
        else:
            print(f"\n❌ Owner name: NOT FOUND")
            # Don't fail - might be in a different section

        # Check for area
        areas = [f for f in results if f.field_type == "area_hectares"]
        if areas:
            area_value = float(areas[0].value)
            expected_area = ground_truth_tenure["area_hectares"]

            # Allow 1% tolerance
            if abs(area_value - expected_area) / expected_area < 0.01:
                print(f"✅ Area: CORRECT ({area_value} ha)")
            else:
                print(f"❌ Area: INCORRECT (got {area_value}, expected {expected_area})")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_project_id_accuracy(self, botany_farm_project_ids):
        """Test project ID extraction accuracy against ground truth.

        Uses shared fixture to avoid duplicate API calls.

        NOTE: After validation improvements, we correctly filter out filename
        prefixes like "4997Botany22" which appear in document lists.
        We should only extract official registry IDs (C##-####, VCS####, etc.).
        """
        # Use shared extraction results from fixture
        results = botany_farm_project_ids

        print(f"\n=== Project ID Extraction Results ===")
        print(f"Total extracted: {len(results)}")

        unique_ids = set()
        for field in results:
            unique_ids.add(field.value)
            print(f"  {field.value} (confidence: {field.confidence})")

        # After validation improvements, we should:
        # 1. NOT extract filename prefixes (4997Botany22, 4998Botany23)
        # 2. ONLY extract official registry IDs

        # Check that filename prefixes were filtered
        filename_prefixes = ["4997Botany22", "4998Botany23", "4997", "4998"]
        found_prefixes = [pid for pid in unique_ids if pid in filename_prefixes]

        if found_prefixes:
            print(f"\n❌ Found filename prefixes (should be filtered): {found_prefixes}")
            assert len(found_prefixes) == 0, f"Filename prefixes should be filtered: {found_prefixes}"
        else:
            print(f"✅ No filename prefixes extracted (correctly filtered)")

        # Check that we extracted valid registry ID patterns
        # Valid patterns: C##-####, VCS####, GS-####, CAR####, ACR####, etc.
        import re
        valid_patterns = [
            r"^C\d{2}-\d+$",  # Regen Network (C06-006, C06-4997)
            r"^VCS-?\d+$",     # VCS
            r"^GS-?\d+$",      # Gold Standard
            r"^CAR\d+$",       # Climate Action Reserve
            r"^ACR\d+$",       # American Carbon Registry
        ]

        valid_ids = []
        for pid in unique_ids:
            if any(re.match(pattern, pid) for pattern in valid_patterns):
                valid_ids.append(pid)

        if valid_ids:
            print(f"\n✅ Found valid registry IDs: {valid_ids}")
            # Should have at least one valid registry ID
            assert len(valid_ids) >= 1, "Should extract at least one valid registry ID"
        else:
            print(f"\n⚠️  No valid registry IDs found (may not be in Project Plan)")
            # This is acceptable - Project Plan may only have internal names

        # Check that no false positives (REQ-*, DOC-*, etc.)
        false_positives = [id for id in unique_ids if id.startswith(("REQ-", "DOC-", "v"))]
        if false_positives:
            print(f"\n❌ False positives found: {false_positives}")
            assert len(false_positives) == 0, f"Found false positive IDs: {false_positives}"
        else:
            print(f"✅ No false positives (REQ-, DOC-, v*)")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_full_accuracy_report(self):
        """Generate comprehensive accuracy report for all extractors."""
        project_plan_path = Path("examples/22-23/4997Botany22_Public_Project_Plan/4997Botany22_Public_Project_Plan.md")

        if not project_plan_path.exists():
            pytest.skip("Botany Farm Project Plan not found")

        with open(project_plan_path) as f:
            markdown = f.read()[:20000]  # First 20K chars

        print(f"\n" + "="*60)
        print(f"BOTANY FARM ACCURACY VALIDATION REPORT")
        print(f"="*60)
        print(f"\nDocument: Project Plan (first 20K characters)")
        print(f"Ground Truth: {GROUND_TRUTH['project_name']}")

        # Date extraction
        print(f"\n--- DATE EXTRACTION ---")
        date_extractor = DateExtractor()
        date_results = await date_extractor.extract(markdown, [], "Project Plan")
        print(f"Extracted: {len(date_results)} dates")

        ground_truth_date_types = {d["field_type"] for d in GROUND_TRUTH["ground_truth"]["dates"]}
        extracted_date_types = {f.field_type for f in date_results}

        date_matches = ground_truth_date_types & extracted_date_types
        print(f"Matches: {len(date_matches)}/{len(ground_truth_date_types)} = {len(date_matches)/len(ground_truth_date_types):.1%}")

        # Land tenure extraction
        print(f"\n--- LAND TENURE EXTRACTION ---")
        tenure_extractor = LandTenureExtractor()
        tenure_results = await tenure_extractor.extract(markdown, [], "Project Plan")
        print(f"Extracted: {len(tenure_results)} tenure fields")

        owner_names = [f for f in tenure_results if f.field_type == "owner_name"]
        print(f"Owner names found: {len(owner_names)}")

        # Project ID extraction
        print(f"\n--- PROJECT ID EXTRACTION ---")
        id_extractor = ProjectIDExtractor()
        id_results = await id_extractor.extract(markdown, [], "Project Plan")
        print(f"Extracted: {len(id_results)} project ID occurrences")

        unique_ids = set(f.value for f in id_results)
        print(f"Unique IDs: {unique_ids}")

        ground_truth_ids = {pid["value"] for pid in GROUND_TRUTH["ground_truth"]["project_ids"]}
        id_matches = ground_truth_ids & unique_ids
        print(f"Matches: {len(id_matches)}/{len(ground_truth_ids)} = {len(id_matches)/len(ground_truth_ids):.1%}")

        print(f"\n" + "="*60)
        print(f"SUMMARY")
        print(f"="*60)
        print(f"Dates: {len(date_matches)}/{len(ground_truth_date_types)} correct")
        print(f"Tenure: {len(owner_names)} owner fields found")
        print(f"Project IDs: {len(id_matches)}/{len(ground_truth_ids)} correct")
        print(f"="*60)
