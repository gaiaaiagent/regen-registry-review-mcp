"""Tests for the CLI backend and backend resolution in llm_client."""

import json

import pytest
from unittest.mock import AsyncMock, patch

from registry_review_mcp.models.errors import ConfigurationError
from registry_review_mcp.utils.llm_client import (
    LLMBackendError,
    _resolve_backend,
    _call_via_cli,
    classify_cli_error,
)
import registry_review_mcp.utils.llm_client as llm_client_module


@pytest.fixture(autouse=True)
def reset_cli_cache():
    """Reset the module-level CLI availability cache between tests."""
    llm_client_module._cli_available = None
    llm_client_module._backend_logged = False
    yield
    llm_client_module._cli_available = None
    llm_client_module._backend_logged = False


class TestResolveBackend:
    """Verify backend resolution logic based on settings and availability."""

    async def test_api_when_key_set(self):
        with patch.object(llm_client_module, "settings") as mock_settings:
            mock_settings.llm_backend = "auto"
            mock_settings.anthropic_api_key = "sk-ant-test"
            assert await _resolve_backend() == "api"

    async def test_cli_when_no_key(self):
        with (
            patch.object(llm_client_module, "settings") as mock_settings,
            patch("shutil.which", return_value="/usr/bin/claude"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_settings.llm_backend = "auto"
            mock_settings.anthropic_api_key = ""
            proc = AsyncMock()
            proc.returncode = 0
            proc.wait = AsyncMock(return_value=0)
            mock_exec.return_value = proc
            assert await _resolve_backend() == "cli"

    async def test_raises_when_nothing_available(self):
        with (
            patch.object(llm_client_module, "settings") as mock_settings,
            patch("shutil.which", return_value=None),
        ):
            mock_settings.llm_backend = "auto"
            mock_settings.anthropic_api_key = ""
            with pytest.raises(ConfigurationError, match="No LLM backend available"):
                await _resolve_backend()

    async def test_explicit_api_with_key(self):
        with patch.object(llm_client_module, "settings") as mock_settings:
            mock_settings.llm_backend = "api"
            mock_settings.anthropic_api_key = "sk-ant-test"
            assert await _resolve_backend() == "api"

    async def test_explicit_cli_with_cli(self):
        with (
            patch.object(llm_client_module, "settings") as mock_settings,
            patch("shutil.which", return_value="/usr/bin/claude"),
            patch("asyncio.create_subprocess_exec") as mock_exec,
        ):
            mock_settings.llm_backend = "cli"
            proc = AsyncMock()
            proc.returncode = 0
            proc.wait = AsyncMock(return_value=0)
            mock_exec.return_value = proc
            assert await _resolve_backend() == "cli"

    async def test_explicit_api_no_key_raises(self):
        with patch.object(llm_client_module, "settings") as mock_settings:
            mock_settings.llm_backend = "api"
            mock_settings.anthropic_api_key = ""
            with pytest.raises(ConfigurationError, match="ANTHROPIC_API_KEY"):
                await _resolve_backend()


class TestCliInvocation:
    """Verify CLI subprocess flag construction and stdin handling."""

    async def test_cli_passes_model(self):
        response = {"result": "hello", "is_error": False}
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = AsyncMock()
            proc.communicate = AsyncMock(
                return_value=(json.dumps(response).encode(), b"")
            )
            proc.returncode = 0
            mock_exec.return_value = proc

            await _call_via_cli("test prompt", None, "claude-haiku-4-5-20251001", 4000)

            cmd_args = mock_exec.call_args[0]
            assert "--model" in cmd_args
            model_idx = cmd_args.index("--model")
            assert cmd_args[model_idx + 1] == "claude-haiku-4-5-20251001"

    async def test_cli_passes_system_prompt(self):
        response = {"result": "hello", "is_error": False}
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = AsyncMock()
            proc.communicate = AsyncMock(
                return_value=(json.dumps(response).encode(), b"")
            )
            proc.returncode = 0
            mock_exec.return_value = proc

            await _call_via_cli("test prompt", "You are helpful", "claude-haiku-4-5-20251001", 4000)

            cmd_args = mock_exec.call_args[0]
            assert "--system-prompt" in cmd_args
            sp_idx = cmd_args.index("--system-prompt")
            assert cmd_args[sp_idx + 1] == "You are helpful"

    async def test_cli_omits_system_prompt_when_none(self):
        response = {"result": "hello", "is_error": False}
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = AsyncMock()
            proc.communicate = AsyncMock(
                return_value=(json.dumps(response).encode(), b"")
            )
            proc.returncode = 0
            mock_exec.return_value = proc

            await _call_via_cli("test prompt", None, "claude-haiku-4-5-20251001", 4000)

            cmd_args = mock_exec.call_args[0]
            assert "--system-prompt" not in cmd_args

    async def test_cli_sends_prompt_via_stdin(self):
        response = {"result": "hello", "is_error": False}
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = AsyncMock()
            proc.communicate = AsyncMock(
                return_value=(json.dumps(response).encode(), b"")
            )
            proc.returncode = 0
            mock_exec.return_value = proc

            await _call_via_cli("my prompt text", None, "claude-haiku-4-5-20251001", 4000)

            proc.communicate.assert_called_once_with(input=b"my prompt text")

    async def test_cli_uses_json_output_format(self):
        response = {"result": "hello", "is_error": False}
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = AsyncMock()
            proc.communicate = AsyncMock(
                return_value=(json.dumps(response).encode(), b"")
            )
            proc.returncode = 0
            mock_exec.return_value = proc

            await _call_via_cli("test", None, "claude-haiku-4-5-20251001", 4000)

            cmd_args = mock_exec.call_args[0]
            assert "--output-format" in cmd_args
            fmt_idx = cmd_args.index("--output-format")
            assert cmd_args[fmt_idx + 1] == "json"

    async def test_cli_raises_on_is_error(self):
        response = {"result": "authentication failed", "is_error": True}
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = AsyncMock()
            proc.communicate = AsyncMock(
                return_value=(json.dumps(response).encode(), b"")
            )
            proc.returncode = 0
            mock_exec.return_value = proc

            with pytest.raises(LLMBackendError):
                await _call_via_cli("test", None, "claude-haiku-4-5-20251001", 4000)

    async def test_cli_raises_on_nonzero_exit(self):
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            proc = AsyncMock()
            proc.communicate = AsyncMock(return_value=(b"", b"CLI crashed"))
            proc.returncode = 1
            mock_exec.return_value = proc

            with pytest.raises(LLMBackendError, match="CLI failed"):
                await _call_via_cli("test", None, "claude-haiku-4-5-20251001", 4000)


class TestClassifyCliError:
    """Verify CLI error classification maps to the same APIErrorInfo categories."""

    def test_rate_limit_is_transient(self):
        info = classify_cli_error("Error: rate limit exceeded", 1)
        assert info.category == "rate_limit"
        assert info.is_fatal is False

    def test_auth_is_fatal(self):
        info = classify_cli_error("Error: authentication failed", 1)
        assert info.category == "auth"
        assert info.is_fatal is True

    def test_billing_is_fatal(self):
        info = classify_cli_error("Error: usage limit reached for billing period", 1)
        assert info.category == "billing"
        assert info.is_fatal is True

    def test_timeout_is_transient(self):
        info = classify_cli_error("Request timeout", -15)
        assert info.category == "network"
        assert info.is_fatal is False

    def test_unknown_error(self):
        info = classify_cli_error("Something unexpected", 42)
        assert info.category == "unknown"
        assert info.is_fatal is False
