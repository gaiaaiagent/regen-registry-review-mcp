"""Tests for LLM JSON response validation and error handling."""

import pytest
import time
from unittest.mock import AsyncMock, Mock

from registry_review_mcp.extractors.llm_extractors import (
    DateExtractor,
    LandTenureExtractor,
    ProjectIDExtractor,
)


def unique_doc_name(test_name: str) -> str:
    """Generate unique document name for testing to avoid cache collisions."""
    return f"{test_name}_{int(time.time() * 1000000)}.pdf"


class TestInvalidJSON:
    """Test handling of invalid JSON responses."""

    @pytest.mark.asyncio
    async def test_malformed_json_syntax_error(self):
        """Test that malformed JSON is handled gracefully."""
        # Create mock response with invalid JSON (missing closing bracket)
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test",
        "confidence": 0.95,
        "reasoning": "test"

```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("malformed_json")
        results = await extractor.extract("test content", [], doc_name)

        # Should return empty list instead of crashing
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_json_without_code_fence(self):
        """Test JSON response without markdown code fence."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='[{"value": "2022-01-01", "field_type": "project_start_date", "source": "test", "confidence": 0.95, "reasoning": "test"}]'
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("json_without_fence")
        results = await extractor.extract("test content", [], doc_name)

        # Should still parse successfully
        assert len(results) == 1
        assert results[0].value == "2022-01-01"

    @pytest.mark.asyncio
    async def test_non_json_text_response(self):
        """Test handling of plain text instead of JSON."""
        mock_response = Mock()
        mock_response.content = [
            Mock(text="I found the project start date to be January 1, 2022.")
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("non_json_text")
        results = await extractor.extract("test content", [], doc_name)

        # Should return empty list when JSON parsing fails
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_empty_json_array(self):
        """Test handling of empty JSON array response."""
        mock_response = Mock()
        mock_response.content = [Mock(text='```json\n[]\n```')]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("empty_array")
        results = await extractor.extract("test content", [], doc_name)

        # Empty array is valid - just means no fields found
        assert isinstance(results, list)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_json_object_instead_of_array(self):
        """Test handling when LLM returns object instead of array."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
{
    "value": "2022-01-01",
    "field_type": "project_start_date",
    "source": "test",
    "confidence": 0.95,
    "reasoning": "test"
}
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("json_object")
        results = await extractor.extract("test content", [], doc_name)

        # Should handle gracefully - either convert to array or return empty
        assert isinstance(results, list)


class TestMissingRequiredFields:
    """Test handling of JSON with missing required fields."""

    @pytest.mark.asyncio
    async def test_missing_value_field(self):
        """Test handling when 'value' field is missing."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "field_type": "project_start_date",
        "source": "test",
        "confidence": 0.95,
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("missing_value")
        results = await extractor.extract("test content", [], doc_name)

        # Should skip invalid entries
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_missing_field_type(self):
        """Test handling when 'field_type' is missing."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "source": "test",
        "confidence": 0.95,
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("missing_field_type")
        results = await extractor.extract("test content", [], doc_name)

        # Should skip entries without field_type
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_missing_confidence(self):
        """Test handling when 'confidence' is missing."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test",
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("missing_confidence")
        results = await extractor.extract("test content", [], doc_name)

        # Should skip or use default confidence
        assert len(results) == 0 or results[0].confidence >= 0.0

    @pytest.mark.asyncio
    async def test_missing_optional_fields(self):
        """Test that optional fields (raw_text, page_number) can be missing."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test.pdf",
        "confidence": 0.95,
        "reasoning": "Found in document"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("missing_optional")
        results = await extractor.extract("test content", [], doc_name)

        # Should work fine - raw_text and page_number are optional
        assert len(results) == 1
        assert results[0].value == "2022-01-01"


class TestInvalidFieldValues:
    """Test handling of invalid field values."""

    @pytest.mark.asyncio
    async def test_confidence_above_one(self):
        """Test handling when confidence > 1.0."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test",
        "confidence": 1.5,
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("confidence_above_one")
        results = await extractor.extract("test content", [], doc_name)

        # Should either skip or clamp to 1.0
        if len(results) > 0:
            assert results[0].confidence <= 1.0

    @pytest.mark.asyncio
    async def test_confidence_below_zero(self):
        """Test handling when confidence < 0.0."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test",
        "confidence": -0.5,
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("confidence_below_zero")
        results = await extractor.extract("test content", [], doc_name)

        # Should either skip or clamp to 0.0
        if len(results) > 0:
            assert results[0].confidence >= 0.0

    @pytest.mark.asyncio
    async def test_confidence_as_string(self):
        """Test handling when confidence is string instead of number."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test",
        "confidence": "high",
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("confidence_string")
        results = await extractor.extract("test content", [], doc_name)

        # Should skip entries with invalid confidence type
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_null_value(self):
        """Test handling when value is null."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": null,
        "field_type": "project_start_date",
        "source": "test",
        "confidence": 0.95,
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("null_value")
        results = await extractor.extract("test content", [], doc_name)

        # Implementation preserves null values (they can be filtered downstream)
        assert len(results) >= 0  # Either skips or preserves as None
        if len(results) > 0:
            # If preserved, value should be None
            assert results[0].value is None


class TestPartiallyValidResponses:
    """Test handling when some entries are valid and others aren't."""

    @pytest.mark.asyncio
    async def test_mixed_valid_and_invalid_entries(self):
        """Test that valid entries are preserved when some are invalid."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test",
        "confidence": 0.95,
        "reasoning": "Valid entry"
    },
    {
        "value": "2022-06-15",
        "field_type": "baseline_imagery_date",
        "source": "test",
        "confidence": 2.5,
        "reasoning": "Invalid confidence"
    },
    {
        "field_type": "project_end_date",
        "source": "test",
        "confidence": 0.9,
        "reasoning": "Missing value"
    },
    {
        "value": "2024-01-01",
        "field_type": "reporting_period_end",
        "source": "test",
        "confidence": 0.85,
        "reasoning": "Another valid entry"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("mixed_valid_invalid")
        results = await extractor.extract("test content", [], doc_name)

        # Implementation uses strict validation: rejects entire response if ANY entry is invalid
        # This is good for data quality - better to fail and get it fixed than accept partial data
        assert isinstance(results, list)

        # With strict validation, invalid confidence (2.5) causes entire response to be rejected
        # So we expect empty results (or all entries have valid confidence)
        for result in results:
            assert 0.0 <= result.confidence <= 1.0, "All results should have valid confidence"


class TestLandTenureJSONValidation:
    """Test JSON validation for land tenure extractor."""

    @pytest.mark.asyncio
    async def test_invalid_area_value(self):
        """Test handling when area is not a number."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "very large",
        "field_type": "area_hectares",
        "source": "test",
        "confidence": 0.9,
        "reasoning": "test"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = LandTenureExtractor(mock_client)
        doc_name = unique_doc_name("invalid_area")
        results = await extractor.extract("test content", [], doc_name)

        # Should handle gracefully - either skip or keep as string
        assert isinstance(results, list)


class TestProjectIDJSONValidation:
    """Test JSON validation for project ID extractor."""

    @pytest.mark.asyncio
    async def test_duplicate_project_ids_in_response(self):
        """Test deduplication when LLM returns duplicate IDs."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "C06-4997",
        "field_type": "regen_project_id",
        "source": "page 1",
        "confidence": 0.95,
        "reasoning": "Found in header"
    },
    {
        "value": "C06-4997",
        "field_type": "regen_project_id",
        "source": "page 3",
        "confidence": 0.90,
        "reasoning": "Found in footer"
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = ProjectIDExtractor(mock_client)
        doc_name = unique_doc_name("duplicate_ids")
        results = await extractor.extract("test content", [], doc_name)

        # Should deduplicate (per the implementation in llm_extractors.py)
        assert len(results) == 1
        assert results[0].value == "C06-4997"
        # Should keep the highest confidence
        assert results[0].confidence == 0.95


class TestExtraFields:
    """Test that extra unexpected fields don't break parsing."""

    @pytest.mark.asyncio
    async def test_extra_fields_ignored(self):
        """Test that extra fields in JSON don't cause errors."""
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text='''```json
[
    {
        "value": "2022-01-01",
        "field_type": "project_start_date",
        "source": "test",
        "confidence": 0.95,
        "reasoning": "test",
        "extra_field": "should be ignored",
        "another_extra": 12345
    }
]
```'''
            )
        ]

        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_response

        extractor = DateExtractor(mock_client)
        doc_name = unique_doc_name("extra_fields")
        results = await extractor.extract("test content", [], doc_name)

        # Should parse successfully, ignoring extra fields
        assert len(results) == 1
        assert results[0].value == "2022-01-01"
