"""Integration tests for land tenure and project ID extraction with real API calls."""

import pytest
import time
from pathlib import Path

from registry_review_mcp.config.settings import settings
from registry_review_mcp.extractors.llm_extractors import (
    LandTenureExtractor,
    ProjectIDExtractor,
)

# Import factory infrastructure
from tests.factories import (
    unique_doc_name,
    create_llm_mock_response,
    create_llm_client_mock,
)


pytestmark = [
    pytest.mark.expensive,
    pytest.mark.skipif(
        not settings.anthropic_api_key or not settings.llm_extraction_enabled,
        reason="LLM extraction not configured (set ANTHROPIC_API_KEY and enable LLM extraction)"
    )
]


class TestRealAPILandTenureExtraction:
    """Test land tenure extraction with real Anthropic API calls."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.expensive
    async def test_extract_owner_name_and_area(self):
        """Test extracting owner name and area from text."""
        markdown = """
        # Land Ownership Information

        ## Property Details

        The project is located on land owned by Nicholas Denman. The total property
        area is 120.5 hectares, with the project utilizing the full extent of the
        property under a freehold ownership arrangement.

        The land title certificate confirms Nicholas Denman as the registered owner
        of the property since 2018.
        """

        extractor = LandTenureExtractor()
        results = await extractor.extract(markdown, [], "test_land_ownership.pdf")

        print(f"\n=== Extracted {len(results)} tenure fields ===")
        for field in results:
            print(f"  {field.field_type}: {field.value} (confidence: {field.confidence})")
            print(f"    Reasoning: {field.reasoning}")

        # Verify we got results
        assert len(results) > 0, "Should extract at least one tenure field"

        # Check for owner name
        owner_fields = [f for f in results if f.field_type == "owner_name"]
        assert len(owner_fields) > 0, "Should find owner name"

        # Verify the name (should normalize to full form)
        owner_name = owner_fields[0].value
        assert "Nicholas" in owner_name or "Denman" in owner_name

        # Check for area
        area_fields = [f for f in results if f.field_type == "area_hectares"]
        if area_fields:
            assert area_fields[0].value == 120.5 or area_fields[0].value == "120.5"

    @pytest.mark.asyncio
    async def test_name_variation_handling(self):
        """Test that name variations are normalized."""
        markdown = """
        # Property Information

        ## Owner Details

        The land is owned by Nick Denman, who has held this property since 2018.

        ## Land Title

        Registered Owner: N. Denman
        Property Size: 120.5 ha
        """

        extractor = LandTenureExtractor()
        results = await extractor.extract(markdown, [], "test_name_variation.pdf")

        print(f"\n=== Name Variation Handling ===")
        for field in results:
            print(f"  {field.field_type}: {field.value}")
            print(f"    Raw: {field.raw_text}")

        # Should extract owner name
        owner_fields = [f for f in results if f.field_type == "owner_name"]
        assert len(owner_fields) > 0, "Should extract owner name despite variations"

        # Should NOT extract "maps dating" (common false positive)
        for field in results:
            if field.field_type == "owner_name":
                assert "maps" not in field.value.lower(), "Should not extract 'maps dating' as owner name"
                assert "dating" not in field.value.lower(), "Should not extract 'maps dating' as owner name"

    @pytest.mark.asyncio
    async def test_tenure_type_extraction(self):
        """Test extracting different tenure types."""
        markdown = """
        # Land Tenure

        The project area is held under freehold ownership by the landowner.
        An additional 50 hectares are held under a 99-year lease arrangement.

        Total project area: 170.5 hectares
        - Freehold: 120.5 ha
        - Leased: 50 ha
        """

        extractor = LandTenureExtractor()
        results = await extractor.extract(markdown, [], "test_tenure_types.pdf")

        print(f"\n=== Tenure Types ===")
        for field in results:
            print(f"  {field.field_type}: {field.value}")

        # Should extract tenure types
        tenure_types = [f for f in results if f.field_type == "tenure_type"]
        assert len(tenure_types) > 0, "Should extract tenure type information"

    @pytest.mark.asyncio
    async def test_area_unit_conversion(self):
        """Test that areas in different units are converted to hectares."""
        markdown = """
        # Property Size

        The property comprises 298 acres (approximately 120.5 hectares).
        """

        extractor = LandTenureExtractor()
        results = await extractor.extract(markdown, [], "test_area_conversion.pdf")

        print(f"\n=== Area Conversion ===")
        for field in results:
            if field.field_type == "area_hectares":
                print(f"  Extracted: {field.value} hectares")
                print(f"  From: {field.raw_text}")

        # Should extract area in hectares
        area_fields = [f for f in results if f.field_type == "area_hectares"]
        # LLM should convert or at least extract the hectare value
        assert len(area_fields) > 0, "Should extract area information"


class TestRealAPIProjectIDExtraction:
    """Test project ID extraction with real Anthropic API calls."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.expensive
    async def test_extract_regen_network_id(self):
        """Test extracting Regen Network project ID."""
        markdown = """
        # Project Information

        **Project ID:** C06-4997

        ## Project Overview

        This soil carbon project (C06-4997) is located in New South Wales, Australia.
        The project was registered with Regen Network in 2022.

        For more information about C06-4997, please visit the Regen Registry.
        """

        extractor = ProjectIDExtractor()
        results = await extractor.extract(markdown, [], "test_project_id.pdf")

        print(f"\n=== Extracted {len(results)} project IDs ===")
        for field in results:
            print(f"  ID: {field.value} (confidence: {field.confidence})")
            print(f"    Source: {field.source}")
            print(f"    Reasoning: {field.reasoning}")

        # Verify we got results
        assert len(results) > 0, "Should extract at least one project ID"

        # Check that we found C06-4997
        project_ids = [f.value for f in results]
        assert "C06-4997" in project_ids, "Should find C06-4997"

        # Results should be deduplicated (only one instance of each unique ID)
        c06_occurrences = [f for f in results if f.value == "C06-4997"]
        assert len(c06_occurrences) == 1, "Should return deduplicated results (one instance per unique ID)"

        # Verify the confidence is high (should keep highest confidence from multiple occurrences)
        assert c06_occurrences[0].confidence >= 0.7, "Deduplicated result should have high confidence"

    @pytest.mark.asyncio
    async def test_filter_out_requirement_ids(self):
        """Test that requirement IDs are not confused with project IDs."""
        markdown = """
        # Compliance Check

        Project ID: C06-4997

        ## Requirements

        - REQ-007: Project start date must be documented
        - REQ-018: Baseline imagery date required
        - DOC-001: Project plan submitted

        Version: v1.2.2
        Date: 2022-01-01
        """

        extractor = ProjectIDExtractor()
        results = await extractor.extract(markdown, [], "test_filter_ids.pdf")

        print(f"\n=== Filtering Non-Project IDs ===")
        for field in results:
            print(f"  {field.value}")

        # Should extract C06-4997
        project_ids = [f.value for f in results]
        assert "C06-4997" in project_ids, "Should find actual project ID"

        # Should NOT extract requirement IDs, document IDs, versions, or dates
        assert "REQ-007" not in project_ids, "Should not extract requirement IDs"
        assert "REQ-018" not in project_ids, "Should not extract requirement IDs"
        assert "DOC-001" not in project_ids, "Should not extract document IDs"
        assert "v1.2.2" not in project_ids, "Should not extract version numbers"
        assert "2022-01-01" not in project_ids, "Should not extract dates"

    @pytest.mark.asyncio
    async def test_multiple_registry_ids(self):
        """Test extracting IDs from different registries."""
        markdown = """
        # Cross-Registry Reference

        This project is registered with:
        - Regen Network: C06-4997
        - Verra (VCS): VCS-1234
        - Gold Standard: GS-5678

        Each registry maintains independent records for this project.
        """

        extractor = ProjectIDExtractor()
        results = await extractor.extract(markdown, [], "test_multiple_registries.pdf")

        print(f"\n=== Multiple Registry IDs ===")
        for field in results:
            print(f"  {field.value} - {field.reasoning[:80]}...")

        # Should extract multiple different IDs
        project_ids = [f.value for f in results]

        # Should find at least 2-3 different IDs (depending on LLM extraction)
        unique_ids = set(project_ids)
        assert len(unique_ids) >= 2, "Should extract multiple unique project IDs"

    @pytest.mark.asyncio
    async def test_consistency_detection(self):
        """Test detecting consistent vs inconsistent project IDs."""
        markdown = """
        # Document 1: Project Plan
        Project ID: C06-4997

        # Document 2: Baseline Report
        Project ID: C06-4997

        # Document 3: Monitoring Report
        Project ID: C06-4997
        """

        extractor = ProjectIDExtractor()
        results = await extractor.extract(markdown, [], "test_consistency.pdf")

        print(f"\n=== Consistency Check ===")
        print(f"Total results (deduplicated): {len(results)}")
        unique_ids = set(f.value for f in results)
        print(f"Unique IDs: {unique_ids}")

        # With deduplication, should get exactly one result
        assert len(results) == 1, "Should return one deduplicated result"
        assert len(unique_ids) == 1, "Should find only one unique project ID (consistent)"
        assert "C06-4997" in unique_ids, "Should be C06-4997"

        # The deduplicated result should have high confidence (kept best from multiple occurrences)
        assert results[0].confidence >= 0.7, "Deduplicated result should have high confidence"


class TestFuzzyNameDeduplication:
    """Test fuzzy matching for owner name variations."""

    @pytest.mark.asyncio
    async def test_fuzzy_name_deduplication(self):
        """Test that similar owner names are deduplicated correctly."""
        # Mock response with name variations
        json_content = '''[
    {
        "value": "Nicholas Denman",
        "field_type": "owner_name",
        "source": "Page 1",
        "confidence": 0.85,
        "reasoning": "Found in header"
    },
    {
        "value": "Nick Denman",
        "field_type": "owner_name",
        "source": "Page 3",
        "confidence": 0.95,
        "reasoning": "Found in signature"
    },
    {
        "value": "N. Denman",
        "field_type": "owner_name",
        "source": "Page 5",
        "confidence": 0.80,
        "reasoning": "Found in footer"
    },
    {
        "value": "Sarah Johnson",
        "field_type": "owner_name",
        "source": "Page 2",
        "confidence": 0.90,
        "reasoning": "Different person"
    },
    {
        "value": 120.5,
        "field_type": "area_hectares",
        "source": "Page 1",
        "confidence": 0.95,
        "reasoning": "Property area"
    },
    {
        "value": 120.5,
        "field_type": "area_hectares",
        "source": "Page 4",
        "confidence": 0.85,
        "reasoning": "Duplicate area"
    }
]'''
        response = create_llm_mock_response(json_content)
        client = create_llm_client_mock(response)

        extractor = LandTenureExtractor(client)
        results = await extractor.extract("test content", [], unique_doc_name("fuzzy_dedup"))

        # Verify fuzzy deduplication worked
        owner_names = [f.value for f in results if f.field_type == "owner_name"]

        # Should deduplicate Nicholas/Nick/N. Denman to 1 entry (highest confidence)
        # Should keep Sarah Johnson separate
        assert len(owner_names) == 2, f"Expected 2 unique owners, got {len(owner_names)}: {owner_names}"

        # Should keep "Nick Denman" (highest confidence: 0.95)
        assert "Nick Denman" in owner_names, "Should keep highest confidence name variant"
        assert "Sarah Johnson" in owner_names, "Should keep distinct name"

        # Area should be deduplicated exactly (not fuzzy)
        areas = [f for f in results if f.field_type == "area_hectares"]
        assert len(areas) == 1, f"Expected 1 area after exact dedup, got {len(areas)}"
        assert areas[0].confidence == 0.95, "Should keep highest confidence area"


class TestCachingForNewExtractors:
    """Test caching behavior for land tenure and project ID extractors."""

    async def _verify_caching(self, extractor, markdown: str, test_name: str, result_type: str):
        """Helper to verify caching behavior for any extractor."""
        doc_name = unique_doc_name(test_name)

        # First call - hits API
        start1 = time.time()
        results1 = await extractor.extract(markdown, [], doc_name)
        duration1 = time.time() - start1
        print(f"\nFirst call (API): {duration1:.2f}s, extracted {len(results1)} {result_type}")

        # Second call - should use cache
        start2 = time.time()
        results2 = await extractor.extract(markdown, [], doc_name)
        duration2 = time.time() - start2
        print(f"Second call (cache): {duration2:.2f}s, extracted {len(results2)} {result_type}")

        # Verify results are identical
        assert len(results1) == len(results2)
        if results1:
            assert results1[0].value == results2[0].value

        # Second call should be much faster (< 500ms for cache hit)
        assert duration2 < 0.5, f"Cache hit should be fast, got {duration2}s"

    @pytest.mark.asyncio
    async def test_land_tenure_caching(self):
        """Test that land tenure extraction uses cache on second call."""
        markdown = "The property is owned by Nicholas Denman, total area 120.5 hectares."
        await self._verify_caching(LandTenureExtractor(), markdown, "cache_tenure", "fields")

    @pytest.mark.asyncio
    async def test_project_id_caching(self):
        """Test that project ID extraction uses cache on second call."""
        markdown = "Project ID: C06-4997"
        await self._verify_caching(ProjectIDExtractor(), markdown, "cache_id", "IDs")
