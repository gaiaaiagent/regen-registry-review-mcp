"""Tests for centralized LLM client utilities and API error classification."""

import pytest
from unittest.mock import patch

from registry_review_mcp.utils.llm_client import (
    APIErrorInfo,
    LLMAuthenticationError,
    LLMBillingError,
    classify_api_error,
    get_anthropic_client,
)


class TestClassifyApiError:
    """Verify that Anthropic SDK exceptions are classified with actionable guidance."""

    def test_authentication_error_is_fatal(self):
        from anthropic import AuthenticationError
        import httpx

        error = AuthenticationError(
            message="Invalid API key",
            response=httpx.Response(status_code=401, request=httpx.Request("POST", "https://api.anthropic.com")),
            body={"error": {"type": "authentication_error", "message": "Invalid API key"}},
        )
        info = classify_api_error(error)
        assert info.category == "auth"
        assert info.is_fatal is True
        assert "console.anthropic.com" in info.guidance

    def test_credit_balance_error_is_fatal(self):
        from anthropic import BadRequestError
        import httpx

        error = BadRequestError(
            message="Your credit balance is too low",
            response=httpx.Response(status_code=400, request=httpx.Request("POST", "https://api.anthropic.com")),
            body={"error": {"type": "invalid_request_error", "message": "Your credit balance is too low"}},
        )
        info = classify_api_error(error)
        assert info.category == "billing"
        assert info.is_fatal is True
        assert "separate from Max" in info.guidance

    def test_rate_limit_is_transient(self):
        from anthropic import RateLimitError
        import httpx

        error = RateLimitError(
            message="Rate limit exceeded",
            response=httpx.Response(status_code=429, request=httpx.Request("POST", "https://api.anthropic.com")),
            body={"error": {"type": "rate_limit_error", "message": "Rate limit exceeded"}},
        )
        info = classify_api_error(error)
        assert info.category == "rate_limit"
        assert info.is_fatal is False

    def test_connection_error_is_transient(self):
        from anthropic import APIConnectionError

        error = APIConnectionError(request=None)
        info = classify_api_error(error)
        assert info.category == "network"
        assert info.is_fatal is False

    def test_generic_bad_request_is_not_fatal(self):
        from anthropic import BadRequestError
        import httpx

        error = BadRequestError(
            message="max_tokens must be positive",
            response=httpx.Response(status_code=400, request=httpx.Request("POST", "https://api.anthropic.com")),
            body={"error": {"type": "invalid_request_error", "message": "max_tokens must be positive"}},
        )
        info = classify_api_error(error)
        assert info.category == "request"
        assert info.is_fatal is False

    def test_unknown_error_is_not_fatal(self):
        info = classify_api_error(RuntimeError("something broke"))
        assert info.category == "unknown"
        assert info.is_fatal is False


class TestGetAnthropicClient:
    """Verify pre-flight API key validation."""

    def test_raises_when_no_key(self):
        with patch("registry_review_mcp.utils.llm_client.settings") as mock_settings:
            mock_settings.anthropic_api_key = ""
            with pytest.raises(LLMAuthenticationError, match="ANTHROPIC_API_KEY"):
                get_anthropic_client()

    def test_returns_client_when_key_present(self):
        with patch("registry_review_mcp.utils.llm_client.settings") as mock_settings:
            mock_settings.anthropic_api_key = "sk-ant-test-key"
            client = get_anthropic_client()
            assert client is not None
