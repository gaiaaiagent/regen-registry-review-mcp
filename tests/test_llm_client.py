"""Tests for centralized LLM client utilities and API error classification."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from registry_review_mcp.utils.llm_client import (
    APIErrorInfo,
    LLMAuthenticationError,
    LLMBillingError,
    classify_api_error,
    classify_openai_error,
    get_anthropic_client,
    _resolve_backend,
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


class TestClassifyOpenAIError:
    """Verify that OpenAI SDK exceptions are classified with actionable guidance."""

    def test_auth_error_is_fatal(self):
        from openai import AuthenticationError
        error = AuthenticationError(
            message="Incorrect API key provided",
            response=MagicMock(status_code=401, headers={}),
            body={"error": {"message": "Incorrect API key provided"}},
        )
        info = classify_openai_error(error)
        assert info.category == "auth"
        assert info.is_fatal is True
        assert "OPENAI_API_KEY" in info.guidance

    def test_rate_limit_billing_is_fatal(self):
        from openai import RateLimitError
        error = RateLimitError(
            message="You exceeded your current quota, insufficient_quota",
            response=MagicMock(status_code=429, headers={}),
            body={"error": {"message": "insufficient_quota"}},
        )
        info = classify_openai_error(error)
        assert info.category == "billing"
        assert info.is_fatal is True

    def test_rate_limit_is_transient(self):
        from openai import RateLimitError
        error = RateLimitError(
            message="Rate limit exceeded",
            response=MagicMock(status_code=429, headers={}),
            body={"error": {"message": "Rate limit exceeded"}},
        )
        info = classify_openai_error(error)
        assert info.category == "rate_limit"
        assert info.is_fatal is False

    def test_connection_error_is_transient(self):
        from openai import APIConnectionError
        error = APIConnectionError(request=MagicMock())
        info = classify_openai_error(error)
        assert info.category == "network"
        assert info.is_fatal is False

    def test_unknown_error_is_not_fatal(self):
        info = classify_openai_error(RuntimeError("something broke"))
        assert info.category == "unknown"
        assert info.is_fatal is False


class TestResolveBackendOpenAI:
    """Verify _resolve_backend handles the OpenAI backend and auto fallback chain."""

    async def test_forced_openai_with_key(self):
        with patch("registry_review_mcp.utils.llm_client.settings") as mock_settings:
            mock_settings.llm_backend = "openai"
            mock_settings.openai_api_key = "sk-test-openai-key"
            result = await _resolve_backend()
            assert result == "openai"

    async def test_forced_openai_without_key_raises(self):
        with patch("registry_review_mcp.utils.llm_client.settings") as mock_settings:
            mock_settings.llm_backend = "openai"
            mock_settings.openai_api_key = ""
            from registry_review_mcp.models.errors import ConfigurationError
            with pytest.raises(ConfigurationError, match="OPENAI_API_KEY"):
                await _resolve_backend()

    async def test_auto_falls_through_to_openai(self):
        with patch("registry_review_mcp.utils.llm_client.settings") as mock_settings, \
             patch("registry_review_mcp.utils.llm_client._check_cli_available", return_value=False):
            mock_settings.llm_backend = "auto"
            mock_settings.anthropic_api_key = ""
            mock_settings.openai_api_key = "sk-test-openai-key"
            result = await _resolve_backend()
            assert result == "openai"

    async def test_auto_prefers_api_over_openai(self):
        with patch("registry_review_mcp.utils.llm_client.settings") as mock_settings, \
             patch("registry_review_mcp.utils.llm_client._check_cli_available", return_value=False):
            mock_settings.llm_backend = "auto"
            mock_settings.anthropic_api_key = "sk-ant-key"
            mock_settings.openai_api_key = "sk-test-openai-key"
            result = await _resolve_backend()
            assert result == "api"


class TestCallViaOpenAI:
    """Verify the OpenAI backend correctly maps prompts to the chat completions API."""

    async def test_call_maps_prompt_correctly(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test response"

        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        with patch("registry_review_mcp.utils.llm_client.settings") as mock_settings, \
             patch("openai.AsyncOpenAI", return_value=mock_client):
            mock_settings.openai_api_key = "sk-test"
            mock_settings.get_active_openai_model.return_value = "gpt-4o"

            from registry_review_mcp.utils.llm_client import _call_via_openai
            result = await _call_via_openai("What is 2+2?", "You are a calculator.", 100)

            assert result == "test response"
            mock_client.chat.completions.create.assert_called_once()
            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert call_kwargs["model"] == "gpt-4o"
            assert call_kwargs["temperature"] == 0
            assert call_kwargs["max_tokens"] == 100
            assert len(call_kwargs["messages"]) == 2
            assert call_kwargs["messages"][0]["role"] == "system"
            assert call_kwargs["messages"][1]["role"] == "user"
