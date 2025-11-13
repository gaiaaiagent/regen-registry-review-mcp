"""Tests for LLM-powered field extraction (Phase 4.2)."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from registry_review_mcp.config.settings import settings
from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    ExtractedField,
    extract_doc_id,
    extract_doc_name,
    extract_page,
    group_fields_by_document,
)


class TestDateExtractor:
    """Test date extraction with LLM."""

    @pytest.mark.asyncio
    async def test_extract_simple_date(self):
        """Test extraction of a simple date."""
        import time

        # Use unique document name to avoid cache
        doc_name = f"test_{int(time.time() * 1000000)}.pdf"

        # Create mock response
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "Section 1.8",
        "confidence": 0.95,
        "reasoning": "Explicitly labeled as Project Start Date",
        "raw_text": "Project Start Date: 01/01/2022"
    }
]
```'''
            )
        ]

        # Create mock client
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        # Extract
        extractor = DateExtractor(mock_client)
        results = await extractor.extract(
            markdown_content="Project Start Date: 01/01/2022",
            images=[],
            document_name=doc_name,
        )

        # Verify
        assert len(results) == 1
        assert results[0].value == "2022-01-01"
        assert results[0].field_type == "project_start_date"
        assert results[0].confidence == 0.95
        assert mock_client.messages.create.called


class TestHelperFunctions:
    """Test helper functions for data transformation."""

    def test_extract_doc_id(self):
        """Test document ID extraction from source strings."""
        assert extract_doc_id("DOC-001, Page 5") == "DOC-001"
        assert extract_doc_id("REQ-002") == "REQ-002"
        assert extract_doc_id("Project Plan, Section 1.8") is None

    def test_extract_doc_name(self):
        """Test document name extraction from source strings."""
        assert extract_doc_name("Project Plan, Section 1.8, Page 4") == "Project Plan"
        assert extract_doc_name("DOC-001, Page 5") == "DOC-001"

    def test_extract_page(self):
        """Test page number extraction from source strings."""
        assert extract_page("Project Plan, Page 4") == 4
        assert extract_page("Section 1.8") is None

    def test_group_fields_by_document(self):
        """Test grouping of tenure fields by document."""
        fields = [
            ExtractedField(
                value="Nick Denman",
                field_type="owner_name",
                source="Project Plan, Page 8",
                confidence=0.9,
                reasoning="Found in section 1.7",
            ),
            ExtractedField(
                value=120.5,
                field_type="area_hectares",
                source="Project Plan, Page 8",
                confidence=0.95,
                reasoning="Stated as gross project area",
            ),
        ]

        grouped = group_fields_by_document(fields)

        assert len(grouped) == 1
        assert grouped[0]["owner_name"] == "Nick Denman"
        assert grouped[0]["area_hectares"] == 120.5
        assert grouped[0]["document_name"] == "Project Plan"
        assert grouped[0]["page"] == 8


class TestChunking:
    """Test content chunking logic."""

    def test_chunk_content_no_chunking_needed(self):
        """Test that short content is not chunked."""
        extractor = DateExtractor()
        content = "A" * 5000  # Well below default limit
        chunks = extractor._chunk_content(content)

        assert len(chunks) == 1
        assert chunks[0] == content

    def test_chunk_content_basic_chunking(self):
        """Test basic chunking of long content."""
        extractor = DateExtractor()

        # Create content that requires chunking
        # Default: max_input_chars=100000, chunk_size=80000, overlap=2000
        content = "A" * 150000

        chunks = extractor._chunk_content(content)

        # With boundary-aware chunking, should create 2-3 chunks
        assert 2 <= len(chunks) <= 3, f"Expected 2-3 chunks, got {len(chunks)}"

        # All chunks should have reasonable sizes (not tiny)
        for i, chunk in enumerate(chunks):
            assert len(chunk) >= 1000, f"Chunk {i} too small: {len(chunk)} chars"

        # Verify chunks cover all content (accounting for overlap)
        assert chunks[0][0] == content[0], "First chunk should start at beginning"
        assert chunks[-1][-1] == content[-1], "Last chunk should end at end"

    def test_chunk_content_boundary_conditions(self):
        """Test chunking at exact boundaries."""
        extractor = DateExtractor()

        # Test exact multiple of (chunk_size - overlap)
        # chunk_size=80000, overlap=2000, step=78000
        content = "B" * 156000

        chunks = extractor._chunk_content(content)

        # With boundary-aware chunking, should create 2-3 chunks
        assert 2 <= len(chunks) <= 3, f"Expected 2-3 chunks, got {len(chunks)}"

        # All chunks should have reasonable sizes
        for i, chunk in enumerate(chunks):
            assert len(chunk) >= 1000, f"Chunk {i} too small: {len(chunk)} chars"

        # Verify coverage
        assert chunks[0][0] == content[0], "First chunk should start at beginning"
        assert chunks[-1][-1] == content[-1], "Last chunk should end at end"

    def test_chunk_content_preserves_all_content(self):
        """Test that no content is lost during chunking."""
        extractor = DateExtractor()

        # Use identifiable content
        content = "".join(f"{i:010d}" for i in range(20000))  # 200,000 chars total

        chunks = extractor._chunk_content(content)

        # Should create 3 chunks (200000 > 100000, needs chunking)
        assert len(chunks) >= 2

        # Verify we can reconstruct the beginning and end
        assert chunks[0].startswith("0000000000")
        assert chunks[-1].endswith(f"{19999:010d}")

        # Verify total unique content equals original length
        # (This is tricky with overlap, but we can verify key positions)
        # First chunk starts at 0
        # Last chunk should extend to end
        assert chunks[-1][-10:] == content[-10:]

    def test_chunk_overlap_validation(self):
        """Test that invalid overlap raises error."""
        extractor = DateExtractor()

        # Temporarily modify settings to create invalid overlap
        original_chunk_size = settings.llm_chunk_size
        original_overlap = settings.llm_chunk_overlap

        try:
            settings.llm_chunk_size = 1000
            settings.llm_chunk_overlap = 1500  # Invalid: overlap >= chunk_size

            with pytest.raises(ValueError, match="Chunk overlap .* must be less than chunk size"):
                extractor._chunk_content("A" * 200000)
        finally:
            settings.llm_chunk_size = original_chunk_size
            settings.llm_chunk_overlap = original_overlap

    def test_chunk_overlap_equal_to_size(self):
        """Test that overlap equal to chunk size raises error."""
        extractor = DateExtractor()

        original_chunk_size = settings.llm_chunk_size
        original_overlap = settings.llm_chunk_overlap

        try:
            settings.llm_chunk_size = 1000
            settings.llm_chunk_overlap = 1000  # Invalid: creates infinite loop

            with pytest.raises(ValueError, match="Chunk overlap .* must be less than chunk size"):
                extractor._chunk_content("A" * 200000)
        finally:
            settings.llm_chunk_size = original_chunk_size
            settings.llm_chunk_overlap = original_overlap


class TestBoundaryAwareChunking:
    """Test intelligent boundary-aware chunking."""

    def test_boundary_aware_splits_at_paragraph(self):
        """Test that chunking prefers paragraph boundaries."""
        from registry_review_mcp.extractors.llm_extractors import DateExtractor
        from registry_review_mcp.config.settings import settings

        extractor = DateExtractor()

        # Temporarily reduce chunk size for faster testing
        original_chunk_size = settings.llm_chunk_size
        original_max_chars = settings.llm_max_input_chars
        original_overlap = settings.llm_chunk_overlap
        try:
            settings.llm_chunk_size = 1000
            settings.llm_max_input_chars = 1500
            settings.llm_chunk_overlap = 100

            # Create content with clear paragraph boundaries
            paragraph = "This is a test paragraph with some content.\n\n"
            content = paragraph * 40  # ~1,800 chars

            chunks = extractor._chunk_content(content)

            # Should create chunks
            assert len(chunks) >= 2, "Should split long content into chunks"

            # Verify chunks don't split mid-paragraph
            for i, chunk in enumerate(chunks[:-1]):  # Check all but last chunk
                # If split at paragraph boundary, should end with double newline
                # or at least not end mid-word
                assert chunk[-1] in '\n ' or i == len(chunks) - 1, f"Chunk {i} should end at natural boundary"
        finally:
            settings.llm_chunk_size = original_chunk_size
            settings.llm_max_input_chars = original_max_chars
            settings.llm_chunk_overlap = original_overlap

    def test_boundary_aware_splits_at_sentence(self):
        """Test that chunking falls back to sentence boundaries."""
        from registry_review_mcp.extractors.llm_extractors import DateExtractor
        from registry_review_mcp.config.settings import settings

        extractor = DateExtractor()

        # Temporarily reduce chunk size for faster testing
        original_chunk_size = settings.llm_chunk_size
        original_max_chars = settings.llm_max_input_chars
        original_overlap = settings.llm_chunk_overlap
        try:
            settings.llm_chunk_size = 800
            settings.llm_max_input_chars = 1200
            settings.llm_chunk_overlap = 80

            # Create content with sentences but no paragraph breaks
            sentence = "This is sentence number X with some details. "
            # Build content that will require splitting
            sentences = [sentence.replace("X", str(i)) for i in range(30)]
            content = "".join(sentences)  # ~1,350 chars

            chunks = extractor._chunk_content(content)

            # Should create multiple chunks
            assert len(chunks) >= 2

            # Verify chunks end at sentence boundaries (or natural breaks)
            for chunk in chunks[:-1]:  # All but last
                # Should end with sentence punctuation + space, or newline
                last_chars = chunk[-3:] if len(chunk) >= 3 else chunk
                has_sentence_end = any(p in last_chars for p in ['. ', '! ', '? ', '\n'])
                has_word_boundary = chunk[-1] == ' '
                assert has_sentence_end or has_word_boundary, "Should end at natural boundary"
        finally:
            settings.llm_chunk_size = original_chunk_size
            settings.llm_max_input_chars = original_max_chars
            settings.llm_chunk_overlap = original_overlap

    def test_boundary_aware_fallback_to_char(self):
        """Test that chunking falls back gracefully when no boundaries found."""
        from registry_review_mcp.extractors.llm_extractors import DateExtractor
        from registry_review_mcp.config.settings import settings

        extractor = DateExtractor()

        # Temporarily reduce chunk size for faster testing
        original_chunk_size = settings.llm_chunk_size
        original_max_chars = settings.llm_max_input_chars
        original_overlap = settings.llm_chunk_overlap
        try:
            settings.llm_chunk_size = 800
            settings.llm_max_input_chars = 1200
            settings.llm_chunk_overlap = 80

            # Create content with no natural boundaries (one giant "word")
            content = "A" * 1500

            chunks = extractor._chunk_content(content)

            # Should still create chunks (fallback to character-based)
            assert len(chunks) >= 2
            assert all(len(chunk) > 0 for chunk in chunks)
        finally:
            settings.llm_chunk_size = original_chunk_size
            settings.llm_max_input_chars = original_max_chars
            settings.llm_chunk_overlap = original_overlap


class TestCaching:
    """Test caching behavior."""

    @pytest.mark.asyncio
    async def test_date_extraction_uses_cache(self, tmp_path):
        """Test that date extraction caches results."""
        import time

        # Use unique document name to avoid cache collisions
        doc_name = f"test_{int(time.time() * 1000)}.pdf"

        # Mock response
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='[{"value": "2022-01-01", "field_type": "project_start_date", "source": "test", "confidence": 0.9, "reasoning": "test"}]'
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)

        # Clear cache for this document
        extractor.cache.delete(f"{doc_name}_dates")

        # First call
        results1 = await extractor.extract("test content", [], doc_name)
        assert len(results1) == 1
        assert mock_client.messages.create.call_count == 1

        # Second call - should use cache
        results2 = await extractor.extract("test content", [], doc_name)
        assert len(results2) == 1
        assert results1[0].value == results2[0].value
        # API should still only be called once
        assert mock_client.messages.create.call_count == 1
