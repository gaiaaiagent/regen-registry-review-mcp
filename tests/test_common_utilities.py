"""Tests for common shared utilities."""

import pytest
import asyncio

from registry_review_mcp.utils.common import (
    retry_with_backoff,
    with_retry,
    format_error_with_recovery,
    format_validation_error,
    format_file_not_found_error,
    DocumentClassifier,
    DocumentType,
)


class TestRetryWithBackoff:
    """Test retry utilities."""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Test function succeeds on first attempt."""
        call_count = 0

        async def succeeds_immediately():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await retry_with_backoff(succeeds_immediately, max_attempts=3)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_succeeds_after_retries(self):
        """Test function succeeds after some failures."""
        call_count = 0

        async def succeeds_on_third_attempt():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Not yet")
            return "success"

        result = await retry_with_backoff(
            succeeds_on_third_attempt, max_attempts=3, initial_delay=0.01
        )
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_fails_after_max_attempts(self):
        """Test function fails after exhausting retries."""

        async def always_fails():
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await retry_with_backoff(always_fails, max_attempts=3, initial_delay=0.01)

    @pytest.mark.asyncio
    async def test_backoff_timing(self):
        """Test exponential backoff timing."""
        call_times = []

        async def track_timing():
            call_times.append(asyncio.get_event_loop().time())
            if len(call_times) < 3:
                raise ValueError("Not yet")
            return "success"

        await retry_with_backoff(
            track_timing,
            max_attempts=3,
            initial_delay=0.1,
            backoff_factor=2.0,
        )

        # Check delays increased exponentially
        assert len(call_times) == 3
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        # Second delay should be roughly 2x first delay
        assert delay2 > delay1
        assert delay2 / delay1 > 1.5  # Allow some timing variance

    @pytest.mark.asyncio
    async def test_specific_exceptions(self):
        """Test catching only specific exceptions."""

        async def raises_type_error():
            raise TypeError("Type error")

        # Should not catch TypeError when only catching ValueError
        with pytest.raises(TypeError):
            await retry_with_backoff(
                raises_type_error,
                max_attempts=3,
                exceptions=(ValueError,),
                initial_delay=0.01,
            )

    @pytest.mark.asyncio
    async def test_with_retry_decorator(self):
        """Test retry decorator."""
        call_count = 0

        @with_retry(max_attempts=3, initial_delay=0.01)
        async def decorated_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Not yet")
            return "decorated success"

        result = await decorated_function()
        assert result == "decorated success"
        assert call_count == 2


class TestErrorFormatting:
    """Test error formatting utilities."""

    def test_format_error_with_recovery(self):
        """Test error formatting with recovery steps."""
        error = ValueError("Something went wrong")
        context = "PDF extraction"
        steps = [
            "Check file is valid PDF",
            "Verify marker service is running",
            "Try re-uploading file",
        ]

        message = format_error_with_recovery(error, context, steps)

        assert "Error during PDF extraction" in message
        assert "ValueError" in message
        assert "1. Check file is valid PDF" in message
        assert "2. Verify marker service is running" in message
        assert "3. Try re-uploading file" in message

    def test_format_validation_error(self):
        """Test validation error formatting."""
        message = format_validation_error(
            field="project_id",
            value="XYZ",
            expected="ID starting with 'C' followed by digits",
            suggestion="Use format like 'C06-4997'",
        )

        assert "Invalid value for 'project_id'" in message
        assert "XYZ" in message
        assert "Expected: ID starting with 'C'" in message
        assert "Suggestion: Use format like 'C06-4997'" in message

    def test_format_file_not_found_error(self):
        """Test file not found error formatting."""
        message = format_file_not_found_error(
            filepath="/path/to/missing/file.pdf",
            context="document loading",
            suggestions=[
                "Check file path is correct",
                "Verify file exists in session directory",
            ],
        )

        assert "File not found during document loading" in message
        assert "/path/to/missing/file.pdf" in message
        assert "Check file path is correct" in message
        assert "Verify file exists in session directory" in message


class TestDocumentClassifier:
    """Test document classification."""

    def test_project_plan_classification(self):
        """Test project plan detection."""
        assert (
            DocumentClassifier.classify("ProjectPlan.pdf") == DocumentType.PROJECT_PLAN
        )
        assert DocumentClassifier.classify("project_plan_v2.pdf") == DocumentType.PROJECT_PLAN
        assert DocumentClassifier.classify("PP_Final.pdf") == DocumentType.PROJECT_PLAN

    def test_monitoring_report_classification(self):
        """Test monitoring report detection."""
        assert (
            DocumentClassifier.classify("MonitoringReport2023.pdf")
            == DocumentType.MONITORING_REPORT
        )
        assert DocumentClassifier.classify("MR_2023.pdf") == DocumentType.MONITORING_REPORT
        assert (
            DocumentClassifier.classify("monitoring-report.pdf")
            == DocumentType.MONITORING_REPORT
        )

    def test_baseline_classification(self):
        """Test baseline document detection."""
        assert DocumentClassifier.classify("Baseline.pdf") == DocumentType.BASELINE
        assert DocumentClassifier.classify("baseline_report.pdf") == DocumentType.BASELINE
        assert DocumentClassifier.classify("BL_Final.pdf") == DocumentType.BASELINE

    def test_verification_report_classification(self):
        """Test verification report detection."""
        assert (
            DocumentClassifier.classify("VerificationReport.pdf")
            == DocumentType.VERIFICATION_REPORT
        )
        assert DocumentClassifier.classify("VR_2023.pdf") == DocumentType.VERIFICATION_REPORT

    def test_agent_review_classification(self):
        """Test agent review detection."""
        assert (
            DocumentClassifier.classify("RegistryAgentReview.pdf")
            == DocumentType.AGENT_REVIEW
        )
        assert DocumentClassifier.classify("agent_review.pdf") == DocumentType.AGENT_REVIEW

    def test_gis_data_classification(self):
        """Test GIS data detection."""
        assert DocumentClassifier.classify("boundary.shp") == DocumentType.GIS_DATA
        assert DocumentClassifier.classify("project_area.geojson") == DocumentType.GIS_DATA
        assert DocumentClassifier.classify("spatial_data.kml") == DocumentType.GIS_DATA

    def test_supporting_classification(self):
        """Test supporting document detection."""
        assert (
            DocumentClassifier.classify("Appendix_A.pdf") == DocumentType.SUPPORTING
        )
        assert DocumentClassifier.classify("supporting_docs.pdf") == DocumentType.SUPPORTING

    def test_unknown_classification(self):
        """Test unknown document classification."""
        assert DocumentClassifier.classify("random_file.pdf") == DocumentType.UNKNOWN
        assert DocumentClassifier.classify("data.csv") == DocumentType.UNKNOWN

    def test_case_insensitive_classification(self):
        """Test classification is case-insensitive."""
        assert (
            DocumentClassifier.classify("PROJECTPLAN.PDF") == DocumentType.PROJECT_PLAN
        )
        assert (
            DocumentClassifier.classify("MonitoringReport.PDF")
            == DocumentType.MONITORING_REPORT
        )

    def test_is_primary_document(self):
        """Test primary document identification."""
        assert DocumentClassifier.is_primary_document(DocumentType.PROJECT_PLAN) is True
        assert (
            DocumentClassifier.is_primary_document(DocumentType.MONITORING_REPORT)
            is True
        )
        assert DocumentClassifier.is_primary_document(DocumentType.BASELINE) is True
        assert (
            DocumentClassifier.is_primary_document(DocumentType.VERIFICATION_REPORT)
            is True
        )
        assert DocumentClassifier.is_primary_document(DocumentType.AGENT_REVIEW) is False
        assert DocumentClassifier.is_primary_document(DocumentType.SUPPORTING) is False
        assert DocumentClassifier.is_primary_document(DocumentType.UNKNOWN) is False

    def test_get_display_name(self):
        """Test display name generation."""
        assert DocumentClassifier.get_display_name(DocumentType.PROJECT_PLAN) == "Project Plan"
        assert (
            DocumentClassifier.get_display_name(DocumentType.MONITORING_REPORT)
            == "Monitoring Report"
        )
        assert DocumentClassifier.get_display_name(DocumentType.GIS_DATA) == "GIS/Spatial Data"

    def test_get_expected_count(self):
        """Test expected count ranges."""
        # Project plan: exactly 1
        min_pp, max_pp = DocumentClassifier.get_expected_count(DocumentType.PROJECT_PLAN)
        assert min_pp == 1 and max_pp == 1

        # Monitoring report: 1 or more
        min_mr, max_mr = DocumentClassifier.get_expected_count(
            DocumentType.MONITORING_REPORT
        )
        assert min_mr == 1 and max_mr == 10

        # Baseline: 0 or 1
        min_bl, max_bl = DocumentClassifier.get_expected_count(DocumentType.BASELINE)
        assert min_bl == 0 and max_bl == 1

        # Supporting: any number
        min_sup, max_sup = DocumentClassifier.get_expected_count(DocumentType.SUPPORTING)
        assert min_sup == 0 and max_sup > 0

    def test_content_based_classification(self):
        """Test classification using document content."""
        content = "This is a Project Plan for carbon credit project..."
        result = DocumentClassifier.classify("document.pdf", content=content)
        assert result == DocumentType.PROJECT_PLAN

        content2 = "Monitoring Report for the period 2023-2024..."
        result2 = DocumentClassifier.classify("doc.pdf", content=content2)
        assert result2 == DocumentType.MONITORING_REPORT
