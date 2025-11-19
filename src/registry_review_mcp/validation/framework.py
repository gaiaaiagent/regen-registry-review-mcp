"""Unified validation framework consolidating all validation patterns."""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ValidationResult(BaseModel):
    """Standard validation result used throughout the system."""

    passed: bool
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @property
    def failed(self) -> bool:
        """Check if validation failed."""
        return not self.passed


class ValidationRule(ABC, Generic[T]):
    """Base class for all validation rules."""

    @abstractmethod
    def validate(self, data: T) -> ValidationResult:
        """Run validation and return result."""
        pass


class SchemaRule(ValidationRule[dict]):
    """Validate data against Pydantic schema."""

    def __init__(self, schema: type[BaseModel], strict: bool = True):
        self.schema = schema
        self.strict = strict

    def validate(self, data: dict) -> ValidationResult:
        """Validate dictionary matches Pydantic schema."""
        try:
            instance = self.schema(**data)
            return ValidationResult(
                passed=True,
                message=f"Valid {self.schema.__name__}",
                details={"validated_data": instance.model_dump()},
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Schema validation failed: {type(e).__name__}",
                details={"error": str(e), "schema": self.schema.__name__},
                confidence=0.0,
            )


class CrossDocumentRule(ValidationRule[dict]):
    """Validate consistency of a field across multiple documents."""

    def __init__(
        self, field_name: str, require_consistency: bool = True, allow_missing: bool = False
    ):
        self.field_name = field_name
        self.require_consistency = require_consistency
        self.allow_missing = allow_missing

    def validate(self, data: dict) -> ValidationResult:
        """Check if field values are consistent across documents."""
        documents = data.get("documents", [])
        if not documents:
            return ValidationResult(
                passed=False,
                message="No documents provided for cross-document validation",
                confidence=0.0,
            )

        # Extract field values from all documents
        values = []
        for doc in documents:
            value = doc.get(self.field_name)
            if value is not None:
                values.append(value)

        if not values:
            if self.allow_missing:
                return ValidationResult(
                    passed=True,
                    message=f"{self.field_name} missing from all documents (allowed)",
                    details={"field": self.field_name, "documents_checked": len(documents)},
                )
            else:
                return ValidationResult(
                    passed=False,
                    message=f"{self.field_name} missing from all documents",
                    details={"field": self.field_name, "documents_checked": len(documents)},
                    confidence=0.0,
                )

        # Check consistency
        unique_values = set(str(v) for v in values)  # Convert to strings for comparison

        if len(unique_values) == 1:
            return ValidationResult(
                passed=True,
                message=f"{self.field_name} is consistent across {len(documents)} documents",
                details={
                    "field": self.field_name,
                    "value": values[0],
                    "documents_checked": len(documents),
                },
            )
        elif not self.require_consistency:
            return ValidationResult(
                passed=True,
                message=f"{self.field_name} has {len(unique_values)} different values (allowed)",
                details={
                    "field": self.field_name,
                    "values": list(unique_values),
                    "documents_checked": len(documents),
                },
                confidence=0.5,
            )
        else:
            return ValidationResult(
                passed=False,
                message=f"{self.field_name} has inconsistent values across documents",
                details={
                    "field": self.field_name,
                    "values": list(unique_values),
                    "documents_checked": len(documents),
                },
                confidence=0.0,
            )


class BusinessRule(ValidationRule[Any]):
    """Validate custom business logic using a predicate function."""

    def __init__(
        self,
        predicate: callable,
        success_message: str,
        failure_message: str,
        rule_name: str | None = None,
    ):
        self.predicate = predicate
        self.success_message = success_message
        self.failure_message = failure_message
        self.rule_name = rule_name or predicate.__name__

    def validate(self, data: Any) -> ValidationResult:
        """Run custom validation predicate."""
        try:
            passed = self.predicate(data)
            return ValidationResult(
                passed=bool(passed),
                message=self.success_message if passed else self.failure_message,
                details={"rule": self.rule_name},
            )
        except Exception as e:
            return ValidationResult(
                passed=False,
                message=f"Business rule '{self.rule_name}' failed: {e}",
                details={"rule": self.rule_name, "error": str(e)},
                confidence=0.0,
            )


class ValidatorChain:
    """Chain multiple validation rules together."""

    def __init__(self, rules: list[ValidationRule], stop_on_failure: bool = False):
        self.rules = rules
        self.stop_on_failure = stop_on_failure

    def validate(self, data: Any) -> list[ValidationResult]:
        """Run all rules and return results."""
        results = []
        for rule in self.rules:
            result = rule.validate(data)
            results.append(result)

            if self.stop_on_failure and result.failed:
                break

        return results

    def validate_all_pass(self, data: Any) -> tuple[bool, list[ValidationResult]]:
        """Check if all validations pass."""
        results = self.validate(data)
        all_passed = all(r.passed for r in results)
        return all_passed, results

    def validate_summary(self, data: Any) -> ValidationResult:
        """Run all rules and return summary result."""
        results = self.validate(data)

        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        all_passed = passed_count == total_count

        return ValidationResult(
            passed=all_passed,
            message=f"{passed_count}/{total_count} validation rules passed",
            details={
                "total_rules": total_count,
                "passed": passed_count,
                "failed": total_count - passed_count,
                "results": [r.model_dump() for r in results],
            },
            confidence=passed_count / total_count if total_count > 0 else 0.0,
        )
