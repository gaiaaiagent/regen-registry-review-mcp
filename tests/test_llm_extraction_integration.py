"""Integration tests for LLM extraction with real API calls."""

import pytest
from pathlib import Path

from registry_review_mcp.config.settings import settings
from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    extract_fields_with_llm,
)


pytestmark = pytest.mark.skipif(
    not settings.anthropic_api_key or not settings.llm_extraction_enabled,
    reason="LLM extraction not configured (set ANTHROPIC_API_KEY and enable LLM extraction)"
)


class TestRealAPIDateExtraction:
    """Test date extraction with real Anthropic API calls."""

    @pytest.mark.asyncio
    async def test_extract_simple_project_start_date(self):
        """Test extracting a simple project start date."""
        markdown = """
        # Project Information

        ## 1.8. Project Start Date

        01/01/2022. The project will be aligned with the calendar year, with annual
        monitoring rounds taking place in the August  March bracket when the soil is
        dormant.
        """

        extractor = DateExtractor()
        results = await extractor.extract(markdown, [], "test_project_plan.pdf")

        print(f"\n=== Extracted {len(results)} dates ===")
        for field in results:
            print(f"  {field.field_type}: {field.value} (confidence: {field.confidence})")
            print(f"    Reasoning: {field.reasoning}")

        # Verify we got results
        assert len(results) > 0, "Should extract at least one date"

        # Check for project start date
        project_start_dates = [f for f in results if f.field_type == "project_start_date"]
        assert len(project_start_dates) > 0, "Should find project start date"

        # Verify the date value
        assert "2022-01-01" in project_start_dates[0].value

        # Verify confidence is reasonable
        assert project_start_dates[0].confidence >= 0.7

    @pytest.mark.asyncio
    async def test_extract_multiple_date_types(self):
        """Test extracting multiple date types from complex text."""
        markdown = """
        # Project Timeline

        Project Start Date: January 1, 2022

        Baseline assessment was conducted on March 15, 2022.

        Satellite imagery was acquired on June 20, 2022 for the baseline analysis.

        Field sampling occurred from August 15-20, 2022.

        The monitoring report was completed on December 31, 2022.
        """

        extractor = DateExtractor()
        results = await extractor.extract(markdown, [], "test_timeline.pdf")

        print(f"\n=== Extracted {len(results)} dates ===")
        for field in results:
            print(f"  {field.field_type}: {field.value} (confidence: {field.confidence})")

        # Should extract multiple dates
        assert len(results) >= 3, "Should extract at least 3 different dates"

        # Check for different date types
        date_types = {f.field_type for f in results}
        assert "project_start_date" in date_types
        assert "baseline_date" in date_types or "sampling_date" in date_types

    @pytest.mark.asyncio
    async def test_date_format_flexibility(self):
        """Test that various date formats are recognized."""
        markdown = """
        Project Timeline:

        Project started: January 15, 2022

        Baseline conducted: 03/20/2022

        Field work: August 10-15, 2022

        Report submitted: 2022-12-31
        """

        extractor = DateExtractor()
        results = await extractor.extract(markdown, [], "test_formats.pdf")

        print(f"\n=== Extracted {len(results)} dates from various formats ===")
        for field in results:
            print(f"  {field.value} from: '{field.raw_text}' (type: {field.field_type})")

        # Should recognize multiple formats
        assert len(results) >= 3, "Should extract dates in multiple formats"

        # Verify different date formats were parsed
        values = [f.value for f in results]
        assert any("2022-01-15" in str(v) for v in values)
        assert any("2022-03-20" in str(v) or "03" in str(v) for v in values)

    @pytest.mark.asyncio
    async def test_date_disambiguation(self):
        """Test that dates are correctly classified by context."""
        markdown = """
        Project Dates:

        The project started on 01/01/2022.

        Imagery was acquired on 06/15/2022 for baseline analysis.

        Soil sampling was conducted on 08/20/2022.
        """

        extractor = DateExtractor()
        results = await extractor.extract(markdown, [], "test_disambiguation.pdf")

        print(f"\n=== Date Classification ===")
        for field in results:
            print(f"  {field.field_type}: {field.value}")
            print(f"    Context: {field.raw_text}")

        # Check that dates are classified differently
        date_types = {f.field_type for f in results}
        assert len(date_types) >= 2, "Should classify dates into different types"

        # Verify specific classifications
        imagery_dates = [f for f in results if "imagery" in f.field_type]
        sampling_dates = [f for f in results if "sampling" in f.field_type]

        # At least one should be correctly classified
        assert len(imagery_dates) > 0 or len(sampling_dates) > 0


class TestCachingWithRealAPI:
    """Test that caching works with real API calls."""

    @pytest.mark.asyncio
    async def test_caching_prevents_duplicate_api_calls(self):
        """Test that second call uses cache instead of API."""
        import time

        markdown = "Project started on 01/01/2022"
        doc_name = f"cache_test_{int(time.time())}.pdf"

        extractor = DateExtractor()

        # First call - hits API
        start1 = time.time()
        results1 = await extractor.extract(markdown, [], doc_name)
        duration1 = time.time() - start1

        print(f"\nFirst call (API): {duration1:.2f}s, extracted {len(results1)} dates")

        # Second call - should use cache
        start2 = time.time()
        results2 = await extractor.extract(markdown, [], doc_name)
        duration2 = time.time() - start2

        print(f"Second call (cache): {duration2:.2f}s, extracted {len(results2)} dates")

        # Verify results are identical
        assert len(results1) == len(results2)
        assert results1[0].value == results2[0].value

        # Second call should be much faster (< 100ms for cache hit)
        assert duration2 < 0.1, f"Cache hit should be fast, got {duration2}s"


class TestEndToEndExtraction:
    """Test end-to-end extraction with evidence data format."""

    @pytest.mark.asyncio
    async def test_extract_from_evidence_structure(self):
        """Test extraction from evidence.json format."""
        # Simulate evidence data structure
        evidence_data = {
            "evidence": [
                {
                    "requirement_id": "REQ-007",
                    "requirement_text": "Project start date",
                    "evidence_snippets": [
                        {
                            "document_name": "Project Plan",
                            "text": "Project Start Date: 01/01/2022. The project will be aligned with the calendar year.",
                            "page": 4,
                        }
                    ],
                }
            ]
        }

        session_id = "test_session"
        results = await extract_fields_with_llm(session_id, evidence_data)

        print(f"\n=== End-to-End Extraction ===")
        print(f"Dates extracted: {len(results.get('dates', []))}")
        for field in results.get('dates', []):
            print(f"  {field.field_type}: {field.value} (confidence: {field.confidence})")

        # Should extract dates
        assert len(results.get('dates', [])) > 0, "Should extract dates from evidence"

        # Should have high confidence
        dates = results.get('dates', [])
        if dates:
            assert dates[0].confidence >= 0.7, "Should have reasonable confidence"
