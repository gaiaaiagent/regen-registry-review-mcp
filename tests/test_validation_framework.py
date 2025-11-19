"""Tests for unified validation framework."""

import pytest
from pydantic import BaseModel

from registry_review_mcp.validation import (
    ValidationResult,
    ValidationRule,
    SchemaRule,
    CrossDocumentRule,
    BusinessRule,
    ValidatorChain,
)


class TestModel(BaseModel):
    """Test Pydantic model."""

    name: str
    age: int
    email: str | None = None


class TestValidationResult:
    """Test ValidationResult model."""

    def test_create_passed_result(self):
        result = ValidationResult(passed=True, message="Success")
        assert result.passed is True
        assert result.failed is False
        assert result.message == "Success"
        assert result.confidence == 1.0

    def test_create_failed_result(self):
        result = ValidationResult(
            passed=False, message="Failure", details={"error": "test"}, confidence=0.0
        )
        assert result.passed is False
        assert result.failed is True
        assert result.details["error"] == "test"


class TestSchemaRule:
    """Test SchemaRule validation."""

    def test_valid_data(self):
        rule = SchemaRule(TestModel)
        result = rule.validate({"name": "Alice", "age": 30})

        assert result.passed is True
        assert "Valid TestModel" in result.message
        assert result.details["validated_data"]["name"] == "Alice"

    def test_invalid_data_missing_field(self):
        rule = SchemaRule(TestModel)
        result = rule.validate({"name": "Alice"})  # Missing required 'age'

        assert result.passed is False
        assert "Schema validation failed" in result.message
        assert result.confidence == 0.0

    def test_invalid_data_wrong_type(self):
        rule = SchemaRule(TestModel)
        result = rule.validate({"name": "Alice", "age": "thirty"})  # Wrong type

        assert result.passed is False
        assert "Schema validation failed" in result.message


class TestCrossDocumentRule:
    """Test CrossDocumentRule validation."""

    def test_consistent_values(self):
        rule = CrossDocumentRule("project_id")
        data = {
            "documents": [
                {"project_id": "C06-4997"},
                {"project_id": "C06-4997"},
                {"project_id": "C06-4997"},
            ]
        }
        result = rule.validate(data)

        assert result.passed is True
        assert "consistent" in result.message.lower()
        assert result.details["value"] == "C06-4997"

    def test_inconsistent_values(self):
        rule = CrossDocumentRule("project_id")
        data = {
            "documents": [
                {"project_id": "C06-4997"},
                {"project_id": "C06-4998"},
                {"project_id": "C06-4997"},
            ]
        }
        result = rule.validate(data)

        assert result.passed is False
        assert "inconsistent" in result.message.lower()
        assert len(result.details["values"]) == 2

    def test_missing_field_not_allowed(self):
        rule = CrossDocumentRule("project_id", allow_missing=False)
        data = {"documents": [{"name": "doc1"}, {"name": "doc2"}]}
        result = rule.validate(data)

        assert result.passed is False
        assert "missing" in result.message.lower()

    def test_missing_field_allowed(self):
        rule = CrossDocumentRule("project_id", allow_missing=True)
        data = {"documents": [{"name": "doc1"}, {"name": "doc2"}]}
        result = rule.validate(data)

        assert result.passed is True
        assert "allowed" in result.message.lower()

    def test_inconsistency_allowed(self):
        rule = CrossDocumentRule("methodology", require_consistency=False)
        data = {
            "documents": [
                {"methodology": "v1.0"},
                {"methodology": "v1.1"},
            ]
        }
        result = rule.validate(data)

        assert result.passed is True
        assert result.confidence == 0.5  # Lower confidence for inconsistent values

    def test_no_documents(self):
        rule = CrossDocumentRule("project_id")
        data = {"documents": []}
        result = rule.validate(data)

        assert result.passed is False
        assert "No documents" in result.message


class TestBusinessRule:
    """Test BusinessRule validation."""

    def test_simple_predicate_pass(self):
        rule = BusinessRule(
            predicate=lambda x: x > 0,
            success_message="Value is positive",
            failure_message="Value must be positive",
            rule_name="positive_number",
        )
        result = rule.validate(5)

        assert result.passed is True
        assert result.message == "Value is positive"

    def test_simple_predicate_fail(self):
        rule = BusinessRule(
            predicate=lambda x: x > 0,
            success_message="Value is positive",
            failure_message="Value must be positive",
            rule_name="positive_number",
        )
        result = rule.validate(-5)

        assert result.passed is False
        assert result.message == "Value must be positive"

    def test_complex_predicate(self):
        def has_valid_project_id(data: dict) -> bool:
            project_id = data.get("project_id", "")
            return project_id.startswith("C") and len(project_id) > 3

        rule = BusinessRule(
            predicate=has_valid_project_id,
            success_message="Valid project ID format",
            failure_message="Invalid project ID format",
            rule_name="project_id_format",
        )

        assert rule.validate({"project_id": "C06-4997"}).passed is True
        assert rule.validate({"project_id": "XYZ"}).passed is False

    def test_predicate_exception(self):
        rule = BusinessRule(
            predicate=lambda x: x["missing_key"],  # Will raise KeyError
            success_message="Success",
            failure_message="Failure",
            rule_name="test_rule",
        )
        result = rule.validate({})

        assert result.passed is False
        assert "failed:" in result.message
        assert result.confidence == 0.0


class TestValidatorChain:
    """Test ValidatorChain functionality."""

    def test_all_rules_pass(self):
        rules = [
            BusinessRule(lambda x: x > 0, "Positive", "Not positive"),
            BusinessRule(lambda x: x < 100, "Less than 100", "Too large"),
            BusinessRule(lambda x: x % 2 == 0, "Even", "Not even"),
        ]
        chain = ValidatorChain(rules)

        all_passed, results = chain.validate_all_pass(10)

        assert all_passed is True
        assert len(results) == 3
        assert all(r.passed for r in results)

    def test_some_rules_fail(self):
        rules = [
            BusinessRule(lambda x: x > 0, "Positive", "Not positive"),
            BusinessRule(lambda x: x < 100, "Less than 100", "Too large"),
            BusinessRule(lambda x: x % 2 == 0, "Even", "Not even"),
        ]
        chain = ValidatorChain(rules)

        all_passed, results = chain.validate_all_pass(5)  # Odd number

        assert all_passed is False
        assert len(results) == 3
        assert sum(1 for r in results if r.passed) == 2

    def test_stop_on_failure(self):
        rules = [
            BusinessRule(lambda x: x > 0, "Positive", "Not positive"),
            BusinessRule(lambda x: x < 100, "Less than 100", "Too large"),
            BusinessRule(lambda x: x % 2 == 0, "Even", "Not even"),
        ]
        chain = ValidatorChain(rules, stop_on_failure=True)

        results = chain.validate(-5)  # Fails first rule

        assert len(results) == 1  # Should stop after first failure
        assert results[0].passed is False

    def test_validate_summary(self):
        rules = [
            BusinessRule(lambda x: x > 0, "Positive", "Not positive"),
            BusinessRule(lambda x: x < 100, "Less than 100", "Too large"),
            BusinessRule(lambda x: x % 2 == 0, "Even", "Not even"),
        ]
        chain = ValidatorChain(rules)

        summary = chain.validate_summary(10)

        assert summary.passed is True
        assert "3/3" in summary.message
        assert summary.details["passed"] == 3
        assert summary.confidence == 1.0

    def test_validate_summary_partial_pass(self):
        rules = [
            BusinessRule(lambda x: x > 0, "Positive", "Not positive"),
            BusinessRule(lambda x: x < 100, "Less than 100", "Too large"),
            BusinessRule(lambda x: x % 2 == 0, "Even", "Not even"),
        ]
        chain = ValidatorChain(rules)

        summary = chain.validate_summary(5)  # 2/3 pass

        assert summary.passed is False
        assert "2/3" in summary.message
        assert summary.details["passed"] == 2
        assert summary.details["failed"] == 1
        assert summary.confidence == pytest.approx(2 / 3)


class TestIntegratedValidation:
    """Test combined validation scenarios."""

    def test_schema_and_business_rules(self):
        """Test combining schema validation with business rules."""
        schema_rule = SchemaRule(TestModel)
        age_rule = BusinessRule(
            lambda data: data.get("age", 0) >= 18,
            "Age is valid (18+)",
            "Must be 18 or older",
            "minimum_age",
        )

        chain = ValidatorChain([schema_rule, age_rule])

        # Valid schema and business rule
        data = {"name": "Alice", "age": 25}
        all_passed, results = chain.validate_all_pass(data)
        assert all_passed is True

        # Valid schema but failed business rule
        data = {"name": "Bob", "age": 15}
        all_passed, results = chain.validate_all_pass(data)
        assert all_passed is False
        assert results[0].passed is True  # Schema valid
        assert results[1].passed is False  # Age invalid

    def test_cross_document_and_schema(self):
        """Test cross-document validation combined with schema checks."""
        # Rule: All documents must have consistent project_id
        consistency_rule = CrossDocumentRule("project_id")

        data = {
            "documents": [
                {"project_id": "C06-4997", "name": "Plan"},
                {"project_id": "C06-4997", "name": "Report"},
                {"project_id": "C06-4997", "name": "Baseline"},
            ]
        }

        result = consistency_rule.validate(data)
        assert result.passed is True
        assert result.details["value"] == "C06-4997"
