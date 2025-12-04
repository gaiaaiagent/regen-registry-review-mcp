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

    def test_chunk_overlap_validation(self, monkeypatch):
        """Test that invalid overlap raises error."""
        # Create extractor with patched settings that have invalid overlap
        from registry_review_mcp.config.settings import Settings
        from registry_review_mcp.extractors import llm_extractors as llm_module

        # Create new settings with invalid configuration
        # llm_chunk_size must be >= 10000 per Settings validation
        new_settings = Settings(
            llm_chunk_size=10000,
            llm_chunk_overlap=15000  # Invalid: overlap >= chunk_size
        )
        monkeypatch.setattr(llm_module, "settings", new_settings)

        extractor = DateExtractor()

        with pytest.raises(ValueError, match="Chunk overlap .* must be less than chunk size"):
            extractor._chunk_content("A" * 200000)

    def test_chunk_overlap_equal_to_size(self, monkeypatch):
        """Test that overlap equal to chunk size raises error."""
        from registry_review_mcp.config.settings import Settings
        from registry_review_mcp.extractors import llm_extractors as llm_module

        # Create new settings with invalid configuration
        # llm_chunk_size must be >= 10000 per Settings validation
        new_settings = Settings(
            llm_chunk_size=10000,
            llm_chunk_overlap=10000  # Invalid: creates infinite loop
        )
        monkeypatch.setattr(llm_module, "settings", new_settings)

        extractor = DateExtractor()

        with pytest.raises(ValueError, match="Chunk overlap .* must be less than chunk size"):
            extractor._chunk_content("A" * 200000)


class TestBoundaryAwareChunking:
    """Test intelligent boundary-aware chunking."""

    def test_boundary_aware_splits_at_paragraph(self, monkeypatch):
        """Test that chunking prefers paragraph boundaries."""
        from registry_review_mcp.extractors.llm_extractors import DateExtractor
        from registry_review_mcp.config.settings import Settings
        from registry_review_mcp.extractors import llm_extractors as llm_module

        # Create new settings with valid chunk sizes (must be >= 10000)
        new_settings = Settings(
            llm_chunk_size=15000,
            llm_max_input_chars=20000,
            llm_chunk_overlap=1000
        )
        monkeypatch.setattr(llm_module, "settings", new_settings)

        extractor = DateExtractor()

        # Create content with clear paragraph boundaries
        paragraph = "This is a test paragraph with some content.\n\n"
        content = paragraph * 500  # ~22,000 chars - enough to require chunking

        chunks = extractor._chunk_content(content)

        # Should create chunks
        assert len(chunks) >= 2, "Should split long content into chunks"

        # Verify chunks don't split mid-paragraph
        for i, chunk in enumerate(chunks[:-1]):  # Check all but last chunk
            # If split at paragraph boundary, should end with double newline
            # or at least not end mid-word
            assert chunk[-1] in '\n ' or i == len(chunks) - 1, f"Chunk {i} should end at natural boundary"

    def test_boundary_aware_splits_at_sentence(self, monkeypatch):
        """Test that chunking falls back to sentence boundaries."""
        from registry_review_mcp.extractors.llm_extractors import DateExtractor
        from registry_review_mcp.config.settings import Settings
        from registry_review_mcp.extractors import llm_extractors as llm_module

        # Create new settings with valid chunk sizes (must be >= 10000)
        new_settings = Settings(
            llm_chunk_size=12000,
            llm_max_input_chars=18000,
            llm_chunk_overlap=1000
        )
        monkeypatch.setattr(llm_module, "settings", new_settings)

        extractor = DateExtractor()

        # Create content with sentences but no paragraph breaks
        sentence = "This is sentence number X with some details. "
        # Build content that will require splitting (need > 18000 chars)
        sentences = [sentence.replace("X", str(i)) for i in range(500)]
        content = "".join(sentences)  # ~22,500 chars

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

    def test_boundary_aware_fallback_to_char(self, monkeypatch):
        """Test that chunking falls back gracefully when no boundaries found."""
        from registry_review_mcp.extractors.llm_extractors import DateExtractor
        from registry_review_mcp.config.settings import Settings
        from registry_review_mcp.extractors import llm_extractors as llm_module

        # Create new settings with valid chunk sizes (must be >= 10000)
        new_settings = Settings(
            llm_chunk_size=12000,
            llm_max_input_chars=18000,
            llm_chunk_overlap=1000
        )
        monkeypatch.setattr(llm_module, "settings", new_settings)

        extractor = DateExtractor()

        # Create content with no natural boundaries (one giant "word")
        content = "A" * 25000

        chunks = extractor._chunk_content(content)

        # Should still create chunks (fallback to character-based)
        assert len(chunks) >= 2
        assert all(len(chunk) > 0 for chunk in chunks)
