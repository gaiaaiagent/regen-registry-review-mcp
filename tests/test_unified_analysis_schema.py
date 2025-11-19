"""Tests for unified analysis schema generation and validation.

This module tests that the LLM-native unified analysis prompt properly embeds
the Pydantic schema, ensuring the LLM returns JSON with correct field names.
"""

import json
import pytest

from registry_review_mcp.prompts.unified_analysis import (
    build_unified_analysis_prompt,
    UnifiedAnalysisResult,
)


class TestSchemaGeneration:
    """Test that Pydantic schema is properly generated and embedded."""

    def test_pydantic_schema_generation(self):
        """Test that UnifiedAnalysisResult generates valid JSON schema."""
        schema = UnifiedAnalysisResult.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "required" in schema

        # Verify all required fields are in schema
        required_fields = {
            "requirements_evidence",
            "requirements_covered",
            "requirements_partial",
            "requirements_missing",
            "overall_coverage",
            "extracted_fields",
            "validation_checks",
            "project_metadata",  # Phase 4.1: Added metadata extraction
            "overall_assessment",
            "flagged_items",
        }

        assert set(schema["required"]) == required_fields
        assert all(field in schema["properties"] for field in required_fields)

    def test_schema_is_json_serializable(self):
        """Test that the schema can be serialized to JSON."""
        schema = UnifiedAnalysisResult.model_json_schema()
        schema_json = json.dumps(schema, indent=2)

        assert isinstance(schema_json, str)
        assert len(schema_json) > 0

        # Verify it can be parsed back
        parsed = json.loads(schema_json)
        assert isinstance(parsed, dict)


class TestPromptGeneration:
    """Test that prompts properly embed the schema."""

    def test_schema_embedded_in_prompt(self):
        """Test that the Pydantic schema is embedded in the generated prompt."""
        # Create minimal test data
        documents = [
            {
                "document_id": "DOC-test",
                "filename": "test.pdf",
                "classification": "Project Plan",
            }
        ]

        markdown_contents = {"DOC-test": "# Test Document\n\nTest content."}

        requirements = [
            {
                "requirement_id": "REQ-001",
                "category": "General",
                "requirement_text": "Test requirement",
                "accepted_evidence": "Test evidence",
            }
        ]

        # Build prompt
        prompt = build_unified_analysis_prompt(
            documents, markdown_contents, requirements
        )

        # Verify schema-related content is in prompt
        assert "CRITICAL: RESPONSE FORMAT" in prompt
        assert "requirements_evidence" in prompt
        assert "extracted_fields" in prompt
        assert "validation_checks" in prompt
        assert '"type": "object"' in prompt  # JSON schema structure

    def test_prompt_warns_against_incorrect_fields(self):
        """Test that prompt explicitly warns against incorrect field names."""
        documents = [
            {
                "document_id": "DOC-test",
                "filename": "test.pdf",
                "classification": "Project Plan",
            }
        ]

        markdown_contents = {"DOC-test": "Test content"}

        requirements = [
            {
                "requirement_id": "REQ-001",
                "category": "General",
                "requirement_text": "Test",
                "accepted_evidence": "Test",
            }
        ]

        prompt = build_unified_analysis_prompt(
            documents, markdown_contents, requirements
        )

        # Verify warnings about common mistakes
        assert "requirement_analysis" in prompt.lower()  # Warning NOT to use this
        assert "structured_data" in prompt.lower()  # Warning NOT to use this
        assert (
            "cross_document_validation" in prompt.lower()
        )  # Warning NOT to use this

    def test_prompt_includes_example_structure(self):
        """Test that prompt includes an example response structure."""
        documents = [{"document_id": "DOC-test", "filename": "test.pdf", "classification": "Project Plan"}]
        markdown_contents = {"DOC-test": "Test"}
        requirements = [
            {
                "requirement_id": "REQ-001",
                "category": "General",
                "requirement_text": "Test",
                "accepted_evidence": "Test",
            }
        ]

        prompt = build_unified_analysis_prompt(
            documents, markdown_contents, requirements
        )

        # Verify example structure is present
        assert "Example Response Structure" in prompt
        assert "REQ-001" in prompt  # Example requirement ID
        assert "project_start_date" in prompt  # Example field


class TestModelValidation:
    """Test Pydantic model validation with various inputs."""

    def test_model_accepts_correct_schema(self):
        """Test that model accepts data with correct field names."""
        data = {
            "requirements_evidence": [],
            "requirements_covered": 0,
            "requirements_partial": 0,
            "requirements_missing": 0,
            "overall_coverage": 0.0,
            "extracted_fields": [],
            "validation_checks": [],
            "project_metadata": {  # Phase 4.1: Added metadata extraction
                "project_id": "C06-4997",
                "proponent": "Test Proponent",
                "crediting_period_start": "2022-01-01",
                "crediting_period_end": "2032-12-31",
                "location": "Test Location",
                "acreage": 1000.0,
                "credit_class": "Soil Carbon",
                "methodology_version": "v1.2.2",
                "vintage_year": 2023,
                "confidence": 0.9
            },
            "overall_assessment": "Test assessment",
            "flagged_items": [],
        }

        result = UnifiedAnalysisResult(**data)
        assert result.requirements_covered == 0
        assert result.overall_coverage == 0.0
        assert result.project_metadata.project_id == "C06-4997"

    def test_model_rejects_incorrect_field_names(self):
        """Test that model rejects data with incorrect field names."""
        # Old incorrect field names that LLM might use
        incorrect_data = {
            "requirement_analysis": [],  # Should be requirements_evidence
            "structured_data": {},  # Should be extracted_fields
            "cross_document_validation": {},  # Should be validation_checks
            "overall_assessment": "Test",
        }

        with pytest.raises(Exception):  # Should raise validation error
            UnifiedAnalysisResult(**incorrect_data)

    def test_model_validates_field_types(self):
        """Test that model validates field types correctly."""
        data = {
            "requirements_evidence": [],
            "requirements_covered": 5,  # Must be int
            "requirements_partial": 3,  # Must be int
            "requirements_missing": 2,  # Must be int
            "overall_coverage": 0.5,  # Must be float between 0-1
            "extracted_fields": [],
            "validation_checks": [],
            "project_metadata": {  # Phase 4.1: Added metadata extraction
                "project_id": "TEST-001",
                "proponent": None,
                "crediting_period_start": None,
                "crediting_period_end": None,
                "location": None,
                "acreage": None,
                "credit_class": None,
                "methodology_version": None,
                "vintage_year": None,
                "confidence": 0.5
            },
            "overall_assessment": "Test",
            "flagged_items": [],
        }

        result = UnifiedAnalysisResult(**data)
        assert result.requirements_covered == 5
        assert result.overall_coverage == 0.5

        # Test invalid coverage (must be 0-1)
        invalid_data = data.copy()
        invalid_data["overall_coverage"] = 1.5  # Out of range

        with pytest.raises(Exception):  # Should raise validation error
            UnifiedAnalysisResult(**invalid_data)
