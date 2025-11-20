"""Tests for cross-document validation tools."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from registry_review_mcp.tools import validation_tools
from registry_review_mcp.tools import session_tools, document_tools, evidence_tools
from registry_review_mcp.models.validation import (
    DateField,
    DateAlignmentValidation,
    LandTenureField,
    ProjectIDOccurrence,
)

# Import factory infrastructure
from tests.factories import SessionManager, path_based_session


@pytest.mark.usefixtures("cleanup_sessions")
class TestDateAlignmentValidation:
    """Test date alignment validation (4-month rule)."""

    async def test_dates_within_120_days_pass(self, tmp_path):
        """Test that dates within 120 days pass validation."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            # Test dates 66 days apart (from Botany Farm example)
            date1 = datetime(2022, 6, 15)
            date2 = datetime(2022, 8, 20)

        result = await validation_tools.validate_date_alignment(
            session_id=session_id,
            field1_name="imagery_date",
            field1_value=date1,
            field1_source="DOC-001, Page 5",
            field2_name="sampling_date",
            field2_value=date2,
            field2_source="DOC-002, Page 12",
            max_delta_days=120
        )

        assert result["status"] == "pass"
        assert result["delta_days"] == 66
        assert result["max_allowed_days"] == 120
        assert result["flagged_for_review"] is False
        assert "within acceptable range" in result["message"].lower()

    async def test_dates_exceeding_120_days_fail(self, tmp_path):
        """Test that dates exceeding 120 days fail validation."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            # Test dates 150 days apart
            date1 = datetime(2022, 1, 1)
            date2 = datetime(2022, 5, 31)

            result = await validation_tools.validate_date_alignment(
                session_id=session_id,
                field1_name="imagery_date",
                field1_value=date1,
                field1_source="DOC-001, Page 5",
                field2_name="sampling_date",
                field2_value=date2,
                field2_source="DOC-002, Page 12",
                max_delta_days=120
            )

            assert result["status"] == "fail"
            assert result["delta_days"] == 150
            assert result["flagged_for_review"] is True
            assert "exceeds maximum" in result["message"].lower()

    async def test_exact_boundary_120_days(self, tmp_path):
        """Test dates exactly at 120-day boundary."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            date1 = datetime(2022, 1, 1)
            date2 = date1 + timedelta(days=120)

            result = await validation_tools.validate_date_alignment(
                session_id=session_id,
                field1_name="imagery_date",
                field1_value=date1,
                field1_source="DOC-001, Page 5",
                field2_name="sampling_date",
                field2_value=date2,
                field2_source="DOC-002, Page 12",
                max_delta_days=120
            )

            assert result["status"] == "pass"
            assert result["delta_days"] == 120


@pytest.mark.usefixtures("cleanup_sessions")
class TestLandTenureValidation:
    """Test land tenure cross-document validation."""

    async def test_exact_name_match_passes(self, tmp_path):
        """Test that exact owner name matches pass validation."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            fields = [
                {
                    "owner_name": "Nick Denman",
                    "area_hectares": 120.5,
                    "tenure_type": "lease",
                    "source": "DOC-001, Page 8",
                    "document_id": "DOC-001",
                    "confidence": 0.95
                },
                {
                    "owner_name": "Nick Denman",
                    "area_hectares": 120.5,
                    "tenure_type": "lease",
                    "source": "DOC-002, Page 3",
                    "document_id": "DOC-002",
                    "confidence": 0.92
                }
            ]

            result = await validation_tools.validate_land_tenure(
                session_id=session_id,
                fields=fields
            )

            assert result["status"] == "pass"
            assert result["owner_name_match"] is True
            assert result["owner_name_similarity"] >= 0.95
            assert result["area_consistent"] is True
            assert result["tenure_type_consistent"] is True
            assert result["flagged_for_review"] is False

    async def test_surname_only_match_with_fuzzy(self, tmp_path):
        """Test that surname-only matches pass with fuzzy matching."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            fields = [
                {
                    "owner_name": "Nick Denman",
                    "area_hectares": 120.5,
                    "tenure_type": "lease",
                    "source": "DOC-001, Page 8",
                    "document_id": "DOC-001",
                    "confidence": 0.95
                },
                {
                    "owner_name": "Nicholas Denman",
                    "area_hectares": 120.5,
                    "tenure_type": "lease",
                    "source": "DOC-002, Page 3",
                    "document_id": "DOC-002",
                    "confidence": 0.92
                }
            ]

            result = await validation_tools.validate_land_tenure(
                session_id=session_id,
                fields=fields,
                fuzzy_match_threshold=0.8
            )

            assert result["status"] in ["pass", "warning"]
            assert result["owner_name_similarity"] >= 0.8
            assert "variation" in result["message"].lower() or "similar" in result["message"].lower()

    async def test_different_names_fail(self, tmp_path):
        """Test that completely different names fail validation."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            fields = [
                {
                    "owner_name": "Nick Denman",
                    "area_hectares": 120.5,
                    "tenure_type": "lease",
                    "source": "DOC-001, Page 8",
                    "document_id": "DOC-001",
                    "confidence": 0.95
                },
                {
                    "owner_name": "John Smith",
                    "area_hectares": 120.5,
                    "tenure_type": "lease",
                    "source": "DOC-002, Page 3",
                    "document_id": "DOC-002",
                    "confidence": 0.92
                }
            ]

            result = await validation_tools.validate_land_tenure(
                session_id=session_id,
                fields=fields
            )

            assert result["status"] == "fail"
            assert result["owner_name_match"] is False
            assert result["flagged_for_review"] is True
            assert "mismatch" in result["message"].lower() or "different" in result["message"].lower()


@pytest.mark.usefixtures("cleanup_sessions")
class TestProjectIDValidation:
    """Test project ID consistency validation."""

    async def test_correct_pattern_and_consistency(self, tmp_path):
        """Test that correct project ID pattern passes validation."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Botany Farm"))

            occurrences = [
                {
                    "project_id": "C06-4997",
                    "document_id": "DOC-001",
                    "document_name": "Project Plan",
                    "page": 1,
                    "section": "1.1 Project Information"
                },
                {
                    "project_id": "C06-4997",
                    "document_id": "DOC-002",
                    "document_name": "Baseline Report",
                    "page": 3,
                    "section": "2.1 Project Overview"
                },
                {
                    "project_id": "C06-4997",
                    "document_id": "DOC-003",
                    "document_name": "Monitoring Report",
                    "page": 1,
                    "section": None
                }
            ]

            result = await validation_tools.validate_project_id(
                session_id=session_id,
                occurrences=occurrences,
                total_documents=5,
                expected_pattern=r"^C\d{2}-\d+$",
                min_occurrences=3
            )

            assert result["status"] == "pass"
            assert result["primary_id"] == "C06-4997"
            assert result["total_occurrences"] >= 3
            assert result["flagged_for_review"] is False

    async def test_inconsistent_project_ids(self, tmp_path):
        """Test that inconsistent project IDs fail validation."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            occurrences = [
                {
                    "project_id": "C06-4997",
                    "document_id": "DOC-001",
                    "document_name": "Project Plan",
                    "page": 1,
                    "section": None
                },
                {
                    "project_id": "C06-5000",
                    "document_id": "DOC-002",
                    "document_name": "Baseline Report",
                    "page": 3,
                    "section": None
                }
            ]

            result = await validation_tools.validate_project_id(
                session_id=session_id,
                occurrences=occurrences,
                total_documents=5,
                expected_pattern=r"^C\d{2}-\d+$"
            )

            assert result["status"] in ["fail", "warning"]
            assert result["flagged_for_review"] is True
            assert "multiple" in result["message"].lower() or "inconsistent" in result["message"].lower()


@pytest.mark.usefixtures("cleanup_sessions")
class TestCrossValidationWorkflow:
    """Test complete cross-validation workflow."""

    async def test_full_cross_validation(self, tmp_path):
        """Test complete cross-validation workflow with all checks."""
        # This would use the actual Botany Farm example data
        # For now, test the basic workflow structure

        # Create session with documents
        example_path = Path(__file__).parent.parent / "examples" / "22-23"

        if not example_path.exists():
            pytest.skip("Botany Farm example data not available")

        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Botany Farm 2022-2023"))

            # Discover documents
            await document_tools.discover_documents(session_id)

            # Run full cross-validation
            results = await validation_tools.cross_validate(session_id)

            assert "summary" in results
            assert results["summary"]["total_validations"] >= 0
            assert "date_alignments" in results
            assert "land_tenure" in results
            assert "project_ids" in results


@pytest.mark.usefixtures("cleanup_sessions")
class TestValidationSummary:
    """Test validation summary calculation."""

    async def test_calculate_validation_summary(self, tmp_path):
        """Test that validation summary calculates correctly."""
        async with SessionManager() as manager:
            session_id = await manager.create(path_based_session(str(tmp_path), "Test Project"))

            # Mock validation results
            validations = {
                "date_alignments": [
                    {"status": "pass"},
                    {"status": "pass"},
                    {"status": "fail"}
                ],
                "land_tenure": [
                    {"status": "pass"}
                ],
                "project_ids": [
                    {"status": "warning"}
                ]
            }

            summary = validation_tools.calculate_validation_summary(validations)

            assert summary["total_validations"] == 5
            assert summary["validations_passed"] == 3
            assert summary["validations_failed"] == 1
            assert summary["validations_warning"] == 1
            assert summary["pass_rate"] == 3 / 5  # 60%
