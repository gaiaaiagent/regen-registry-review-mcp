"""Tests for cost tracking functionality."""

import pytest
from pathlib import Path

from registry_review_mcp.config.settings import settings
from registry_review_mcp.utils.cost_tracker import CostTracker
from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    LandTenureExtractor,
    ProjectIDExtractor,
    set_cost_tracker,
)


pytestmark = [
    pytest.mark.expensive,
    pytest.mark.skipif(
        not settings.anthropic_api_key or not settings.llm_extraction_enabled,
        reason="LLM extraction not configured (set ANTHROPIC_API_KEY and enable LLM extraction)"
    )
]


class TestCostTracking:
    """Test cost tracking integration."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.expensive
    async def test_cost_tracker_records_api_calls(self):
        """Test that cost tracker records API calls from extractors."""
        import time

        # Create cost tracker
        tracker = CostTracker("test_cost_tracking", Path("/tmp/test_cost_tracking.json"))

        # Set global tracker for extractors
        set_cost_tracker(tracker)

        try:
            # Run a simple extraction with unique doc name to avoid cache
            markdown = "Project started on January 1, 2022"
            extractor = DateExtractor()
            # Clear cache for this extractor to ensure fresh API call
            extractor.cache.clear()

            # Use unique document name to avoid any potential caching
            unique_doc_name = f"test_doc_{int(time.time() * 1000000)}"
            results = await extractor.extract(markdown, [], unique_doc_name)

            # Check that cost was tracked
            summary = tracker.get_summary()

            print(f"\n=== Cost Tracking Test ===")
            print(f"API Calls: {summary.total_api_calls}")
            print(f"Input Tokens: {summary.total_input_tokens:,}")
            print(f"Output Tokens: {summary.total_output_tokens:,}")
            print(f"Total Cost: ${summary.total_cost_usd:.4f}")
            print(f"Duration: {summary.total_duration_seconds:.2f}s")

            assert summary.total_api_calls >= 1, "Should have tracked at least one API call"
            assert summary.total_input_tokens > 0, "Should have input tokens"
            assert summary.total_output_tokens > 0, "Should have output tokens"
            assert summary.total_cost_usd > 0, "Should have cost > 0"

        finally:
            # Clean up
            set_cost_tracker(None)
            if Path("/tmp/test_cost_tracking.json").exists():
                Path("/tmp/test_cost_tracking.json").unlink()

    @pytest.mark.asyncio
    async def test_cost_summary_breakdown_by_extractor(self):
        """Test cost summary breakdown by extractor type."""
        tracker = CostTracker("test_breakdown", Path("/tmp/test_breakdown.json"))
        set_cost_tracker(tracker)

        try:
            # Run multiple extractors
            markdown_dates = "Project started on January 1, 2022"
            markdown_tenure = "The land is owned by Nicholas Denman, area is 120.5 hectares"
            markdown_id = "Project ID: C06-4997"

            date_extractor = DateExtractor()
            tenure_extractor = LandTenureExtractor()
            id_extractor = ProjectIDExtractor()

            await date_extractor.extract(markdown_dates, [], "doc1")
            await tenure_extractor.extract(markdown_tenure, [], "doc2")
            await id_extractor.extract(markdown_id, [], "doc3")

            # Get summary
            summary = tracker.get_summary()

            print(f"\n=== Breakdown by Extractor ===")
            extractors = {}
            for call in summary.api_calls:
                if call.extractor not in extractors:
                    extractors[call.extractor] = []
                extractors[call.extractor].append(call)

            for extractor_name, calls in extractors.items():
                total_cost = sum(c.cost_usd for c in calls)
                total_tokens = sum(c.input_tokens + c.output_tokens for c in calls)
                print(f"  {extractor_name}: {len(calls)} calls, ${total_cost:.4f}, {total_tokens:,} tokens")

            # Should have tracked 3 different extractors
            assert len(extractors) == 3, f"Expected 3 extractors, got {len(extractors)}"
            assert "date" in extractors
            assert "tenure" in extractors
            assert "project_id" in extractors

        finally:
            set_cost_tracker(None)
            if Path("/tmp/test_breakdown.json").exists():
                Path("/tmp/test_breakdown.json").unlink()

    @pytest.mark.asyncio
    async def test_cost_tracker_print_summary(self):
        """Test that print_summary() works."""
        tracker = CostTracker("test_print", Path("/tmp/test_print.json"))
        set_cost_tracker(tracker)

        try:
            # Run extraction
            markdown = "Project ID: C06-4997"
            extractor = ProjectIDExtractor()
            await extractor.extract(markdown, [], "test_print_doc")

            # Print summary
            print("\n")
            tracker.print_summary()

            # Just verify it doesn't crash
            summary = tracker.get_summary()
            assert summary.total_api_calls > 0

        finally:
            set_cost_tracker(None)
            if Path("/tmp/test_print.json").exists():
                Path("/tmp/test_print.json").unlink()

    @pytest.mark.asyncio
    async def test_cache_hits_tracked_correctly(self):
        """Test that cache hits are tracked with cached=True flag."""
        import time

        tracker = CostTracker("test_cache_hits", Path("/tmp/test_cache_hits.json"))
        set_cost_tracker(tracker)

        try:
            # Use unique document name to avoid cache collisions
            doc_name = f"test_cache_{int(time.time() * 1000)}.pdf"
            markdown = "Project started on January 1, 2022"

            # First call - should make API call
            extractor = DateExtractor()
            extractor.cache.delete(f"{doc_name}_dates")  # Ensure clean slate
            results1 = await extractor.extract(markdown, [], doc_name)

            # Second call - should use cache
            results2 = await extractor.extract(markdown, [], doc_name)

            # Verify results are the same
            assert len(results1) == len(results2)

            # Check tracker recorded both calls
            summary = tracker.get_summary()
            assert summary.total_api_calls == 2  # One real call + one cache hit

            # Verify one call is cached
            calls = [call for call in tracker.api_calls if call.document_name == doc_name]
            assert len(calls) == 2
            assert sum(1 for call in calls if call.cached) == 1  # Exactly one cached call
            assert sum(1 for call in calls if not call.cached) == 1  # Exactly one real call

            # Cached call should have zero cost
            cached_call = [call for call in calls if call.cached][0]
            assert cached_call.cost_usd == 0.0
            assert cached_call.input_tokens == 0
            assert cached_call.output_tokens == 0

            print(f"\n=== Cache Hit Tracking Test ===")
            print(f"Total API calls: {summary.total_api_calls}")
            print(f"Cache hits: {sum(1 for call in calls if call.cached)}")
            print(f"Real API calls: {sum(1 for call in calls if not call.cached)}")
            print(f"Cached call cost: ${cached_call.cost_usd:.4f}")

        finally:
            set_cost_tracker(None)
            if Path("/tmp/test_cache_hits.json").exists():
                Path("/tmp/test_cache_hits.json").unlink()
