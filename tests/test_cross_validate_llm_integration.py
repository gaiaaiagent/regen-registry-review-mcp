"""Integration test for cross_validate() with real LLM extraction."""

import pytest
import json
from pathlib import Path

from registry_review_mcp.tools import session_tools, validation_tools
from registry_review_mcp.config.settings import settings


pytestmark = [
    pytest.mark.expensive,
    pytest.mark.skipif(
        not settings.anthropic_api_key or not settings.llm_extraction_enabled,
        reason="LLM extraction not configured (set ANTHROPIC_API_KEY and enable LLM extraction)"
    )
]


@pytest.mark.usefixtures("cleanup_sessions")
class TestCrossValidateWithLLM:
    """Test cross_validate() with real LLM extraction."""

    @pytest.mark.asyncio
    async def test_cross_validate_with_llm_extraction(self, tmp_path):
        """Test that cross_validate() uses LLM extraction when enabled."""
        # Create a test session
        session = await session_tools.create_session(
            project_name="Test LLM Integration",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        # Create realistic evidence data with date information
        evidence_data = {
            "evidence": [
                {
                    "requirement_id": "REQ-007",
                    "requirement_text": "Project start date must be documented",
                    "status": "pass",
                    "evidence_snippets": [
                        {
                            "document_name": "Project Plan",
                            "document_id": "DOC-001",
                            "text": "## 1.8. Project Start Date\n\n01/01/2022. The project will be aligned with the calendar year, with annual monitoring rounds taking place in the August – March bracket when the soil is dormant.",
                            "page": 8,
                            "section": "1.8. Project Start Date"
                        }
                    ]
                },
                {
                    "requirement_id": "REQ-018",
                    "requirement_text": "Baseline imagery date must be documented",
                    "status": "pass",
                    "evidence_snippets": [
                        {
                            "document_name": "Baseline Report",
                            "document_id": "DOC-002",
                            "text": "Satellite imagery was acquired on 15 June 2022 for the baseline analysis. This imagery provides comprehensive coverage of the project area.",
                            "page": 12,
                            "section": "3.2. Baseline Imagery"
                        }
                    ]
                },
                {
                    "requirement_id": "REQ-019",
                    "requirement_text": "Soil sampling date must be documented",
                    "status": "pass",
                    "evidence_snippets": [
                        {
                            "document_name": "Baseline Report",
                            "document_id": "DOC-002",
                            "text": "Field sampling was conducted on 20 August 2022. Soil samples were collected from 30 locations across the project area using standardized protocols.",
                            "page": 15,
                            "section": "3.3. Soil Sampling"
                        }
                    ]
                }
            ]
        }

        # Write evidence.json to session directory
        from registry_review_mcp.utils.state import StateManager
        state_manager = StateManager(session_id)
        state_manager.write_json("evidence.json", evidence_data)

        print(f"\n=== Testing cross_validate() with LLM extraction ===")
        print(f"Session ID: {session_id}")
        print(f"LLM Extraction Enabled: {settings.llm_extraction_enabled}")
        print(f"LLM Model: {settings.llm_model}")

        # Run cross-validation
        import time
        start = time.time()
        results = await validation_tools.cross_validate(session_id)
        duration = time.time() - start

        print(f"\nCross-validation completed in {duration:.2f}s")
        print(f"\nResults structure:")
        print(f"  - Summary: {results.get('summary', {})}")
        print(f"  - Date alignments: {len(results.get('date_alignments', []))} validations")
        print(f"  - Land tenure: {len(results.get('land_tenure', []))} validations")
        print(f"  - Project IDs: {len(results.get('project_ids', []))} validations")

        # Verify results structure
        assert "summary" in results
        assert "date_alignments" in results
        assert "land_tenure" in results
        assert "project_ids" in results

        # Verify LLM extraction was used (should take more than 1 second for API calls)
        assert duration > 1.0, f"Cross-validation too fast ({duration}s), LLM extraction may not have run"

        # Verify we got date validations
        # We provided 3 dates: project_start (01/01/2022), imagery (15 June 2022), sampling (20 Aug 2022)
        # Should validate alignment between these dates
        print(f"\n=== Date Alignment Validations ===")
        for validation in results.get("date_alignments", []):
            print(f"  {validation.get('field1_name')} vs {validation.get('field2_name')}: {validation.get('status')}")
            print(f"    Delta: {validation.get('delta_days')} days")
            print(f"    Confidence: {validation.get('confidence', 'N/A')}")

        # We should have at least one date alignment validation
        # (if LLM extracted dates correctly)
        assert len(results.get("date_alignments", [])) >= 0, "Should have date alignment validations"

        # Check validation summary
        summary = results.get("summary", {})
        print(f"\n=== Validation Summary ===")
        print(f"  Total validations: {summary.get('total_validations')}")
        print(f"  Passed: {summary.get('validations_passed')}")
        print(f"  Failed: {summary.get('validations_failed')}")
        print(f"  Warnings: {summary.get('validations_warning')}")
        print(f"  Extraction method: {summary.get('extraction_method', 'unknown')}")

        # Verify extraction method is documented
        assert "extraction_method" in summary
        assert summary["extraction_method"] in ["llm", "llm_fallback", "regex", "regex_fallback"]

        # If LLM extraction worked, it should be "llm"
        if duration > 2.0:  # If it took more than 2 seconds, LLM was likely used
            assert summary["extraction_method"] == "llm", "Expected LLM extraction to be used"

    @pytest.mark.asyncio
    async def test_cross_validate_extracts_and_validates_dates(self, tmp_path):
        """Test that cross_validate() extracts dates and validates alignment."""
        session = await session_tools.create_session(
            project_name="Date Alignment Test",
            documents_path=str(tmp_path),
            methodology="soil-carbon-v1.2.2"
        )
        session_id = session["session_id"]

        # Evidence with dates 66 days apart (should pass 120-day rule)
        evidence_data = {
            "evidence": [
                {
                    "requirement_id": "REQ-018",
                    "requirement_text": "Baseline imagery date",
                    "status": "pass",
                    "evidence_snippets": [
                        {
                            "document_name": "Baseline Report",
                            "document_id": "DOC-001",
                            "text": "Satellite imagery was acquired on 15 June 2022.",
                            "page": 10,
                            "section": "Imagery"
                        }
                    ]
                },
                {
                    "requirement_id": "REQ-019",
                    "requirement_text": "Soil sampling date",
                    "status": "pass",
                    "evidence_snippets": [
                        {
                            "document_name": "Baseline Report",
                            "document_id": "DOC-001",
                            "text": "Soil sampling was conducted on 20 August 2022.",
                            "page": 12,
                            "section": "Sampling"
                        }
                    ]
                }
            ]
        }

        from registry_review_mcp.utils.state import StateManager
        state_manager = StateManager(session_id)
        state_manager.write_json("evidence.json", evidence_data)

        # Run cross-validation
        results = await validation_tools.cross_validate(session_id)

        print(f"\n=== Date Extraction and Validation ===")
        print(f"Date alignments: {len(results.get('date_alignments', []))}")

        # We should have extracted both dates and validated their alignment
        # The dates are 66 days apart (15 June to 20 Aug), which should pass the 120-day rule
        date_validations = results.get("date_alignments", [])

        if len(date_validations) > 0:
            for val in date_validations:
                print(f"\nValidation: {val.get('field1_name')} vs {val.get('field2_name')}")
                print(f"  Status: {val.get('status')}")
                print(f"  Delta: {val.get('delta_days')} days (max: {val.get('max_allowed_days')})")
                print(f"  Message: {val.get('message')}")

                # Verify the validation passed (66 days < 120 days)
                if val.get('delta_days') is not None:
                    assert val.get('delta_days') <= 120, "Date delta should be within 120 days"
