"""Centralized LLM client with API and CLI backends.

Provides a unified `call_llm()` entry point that routes to either the Anthropic
API (via SDK) or the Claude CLI (`claude -p` subprocess). Backend selection is
automatic based on what's available, or can be forced via settings.

Also provides pre-flight validation, human-readable error classification, and
a factory function so every call site gets consistent behavior. Fatal errors
(no credits, bad key) are surfaced immediately rather than silently swallowed.
"""

import asyncio
import json
import logging
import shutil
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from ..config.settings import settings
from ..models.errors import ConfigurationError

logger = logging.getLogger(__name__)

# Cached result of CLI availability check
_cli_available: bool | None = None


class LLMBillingError(ConfigurationError):
    """API call failed due to billing — insufficient credits or expired plan."""

    pass


class LLMAuthenticationError(ConfigurationError):
    """API call failed due to an invalid or revoked API key."""

    pass


class LLMBackendError(ConfigurationError):
    """CLI backend subprocess failed."""

    pass


@dataclass
class APIErrorInfo:
    """Classified API error with actionable guidance."""

    category: str  # "billing", "auth", "rate_limit", "server", "request", "network"
    message: str  # Human-readable explanation
    is_fatal: bool  # Should the caller stop all work (True) or retry/skip (False)
    guidance: str  # What the user should do to fix it


def classify_api_error(error: Exception) -> APIErrorInfo:
    """Turn an Anthropic SDK exception into actionable guidance.

    Examines the exception type and message to determine what went wrong and
    whether the caller should abort (fatal) or retry/skip (transient).
    """
    from anthropic import (
        APIConnectionError,
        APIStatusError,
        AuthenticationError,
        BadRequestError,
        RateLimitError,
    )

    error_str = str(error).lower()

    if isinstance(error, AuthenticationError):
        return APIErrorInfo(
            category="auth",
            message=f"Invalid API key: {error}",
            is_fatal=True,
            guidance=(
                "Your ANTHROPIC_API_KEY is invalid or revoked. "
                "Generate a new key at https://console.anthropic.com/settings/keys"
            ),
        )

    if isinstance(error, BadRequestError):
        if "credit balance" in error_str or "billing" in error_str:
            return APIErrorInfo(
                category="billing",
                message=f"Insufficient API credits: {error}",
                is_fatal=True,
                guidance=(
                    "Your Anthropic API credit balance is too low. "
                    "Add credits at https://console.anthropic.com/settings/billing — "
                    "note: API credits are separate from Max/Pro subscriptions."
                ),
            )
        return APIErrorInfo(
            category="request",
            message=f"Bad request: {error}",
            is_fatal=False,
            guidance="The API rejected the request. This may be a bug — check the logs.",
        )

    if isinstance(error, RateLimitError):
        return APIErrorInfo(
            category="rate_limit",
            message=f"Rate limited: {error}",
            is_fatal=False,
            guidance="Too many concurrent requests. The system will retry automatically.",
        )

    if isinstance(error, APIConnectionError):
        return APIErrorInfo(
            category="network",
            message=f"Cannot reach Anthropic API: {error}",
            is_fatal=False,
            guidance="Check your internet connection and try again.",
        )

    if isinstance(error, APIStatusError):
        return APIErrorInfo(
            category="server",
            message=f"Anthropic API error (HTTP {error.status_code}): {error}",
            is_fatal=False,
            guidance="Anthropic is experiencing issues. Try again in a few minutes.",
        )

    return APIErrorInfo(
        category="unknown",
        message=f"Unexpected error: {error}",
        is_fatal=False,
        guidance="An unexpected error occurred. Check the logs for details.",
    )


def classify_cli_error(stderr: str, returncode: int) -> APIErrorInfo:
    """Map CLI subprocess failures to the same APIErrorInfo categories."""
    stderr_lower = stderr.lower()

    if "rate limit" in stderr_lower:
        return APIErrorInfo(
            category="rate_limit",
            message=f"CLI rate limited: {stderr.strip()}",
            is_fatal=False,
            guidance="Too many concurrent requests. Try again shortly.",
        )

    if "authentication" in stderr_lower or "not logged in" in stderr_lower:
        return APIErrorInfo(
            category="auth",
            message=f"CLI authentication failed: {stderr.strip()}",
            is_fatal=True,
            guidance="Run `claude login` to authenticate the CLI.",
        )

    if "usage limit" in stderr_lower or "billing" in stderr_lower:
        return APIErrorInfo(
            category="billing",
            message=f"CLI usage limit reached: {stderr.strip()}",
            is_fatal=True,
            guidance="Your Claude plan usage limit has been reached.",
        )

    if returncode == -15 or "timeout" in stderr_lower:
        return APIErrorInfo(
            category="network",
            message=f"CLI timed out (exit {returncode}): {stderr.strip()}",
            is_fatal=False,
            guidance="The request timed out. Try again or reduce prompt size.",
        )

    return APIErrorInfo(
        category="unknown",
        message=f"CLI failed (exit {returncode}): {stderr.strip()}",
        is_fatal=False,
        guidance="Check `claude` CLI installation and authentication.",
    )


def get_anthropic_client() -> AsyncAnthropic:
    """Create an Anthropic client after validating the API key exists.

    Raises ConfigurationError immediately if no key is configured, before
    any expensive document loading or processing begins.
    """
    if not settings.anthropic_api_key:
        raise LLMAuthenticationError(
            "No Anthropic API key configured. "
            "Set ANTHROPIC_API_KEY in your environment or .env file. "
            "Get a key at https://console.anthropic.com/settings/keys",
            details={"env_var": "ANTHROPIC_API_KEY"},
        )
    return AsyncAnthropic(api_key=settings.anthropic_api_key)


async def _check_cli_available() -> bool:
    """Check whether the `claude` CLI is installed and reachable.

    Caches the result after the first check.
    """
    global _cli_available
    if _cli_available is not None:
        return _cli_available

    if not shutil.which("claude"):
        _cli_available = False
        return False

    try:
        proc = await asyncio.create_subprocess_exec(
            "claude", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.wait(), timeout=10)
        _cli_available = proc.returncode == 0
    except Exception:
        _cli_available = False

    return _cli_available


async def _resolve_backend() -> str:
    """Determine which backend to use based on settings.

    Returns "api" or "cli".

    Raises ConfigurationError if no backend is available.
    """
    backend = settings.llm_backend

    if backend == "api":
        if not settings.anthropic_api_key:
            raise ConfigurationError(
                "llm_backend='api' but no ANTHROPIC_API_KEY is set.",
                details={"setting": "llm_backend"},
            )
        return "api"

    if backend == "cli":
        if not await _check_cli_available():
            raise ConfigurationError(
                "llm_backend='cli' but `claude` CLI is not installed or not authenticated.",
                details={"setting": "llm_backend"},
            )
        return "cli"

    # auto: try API first, then CLI
    if settings.anthropic_api_key:
        return "api"
    if await _check_cli_available():
        return "cli"

    raise ConfigurationError(
        "No LLM backend available. Either set ANTHROPIC_API_KEY for the API backend, "
        "or install and authenticate the Claude CLI (`claude login`) for the CLI backend.",
        details={"setting": "llm_backend"},
    )


# Track whether we've logged the backend selection
_backend_logged = False


async def call_llm(
    prompt: str,
    system: str | None = None,
    model: str | None = None,
    max_tokens: int = 4000,
) -> str:
    """Unified LLM entry point. Returns raw response text.

    Resolves the backend (API or CLI) and dispatches accordingly.
    All three call sites in the codebase should use this instead of
    constructing client.messages.create() calls directly.

    Args:
        prompt: The user prompt to send.
        system: Optional system prompt.
        model: Model identifier. Defaults to settings.get_active_llm_model().
        max_tokens: Maximum tokens in response.

    Returns:
        The LLM's response text.

    Raises:
        LLMBackendError: If the CLI subprocess fails.
        ConfigurationError: If no backend is available.
        anthropic.APIError: If the API call fails (propagated for classify_api_error).
    """
    global _backend_logged
    backend = await _resolve_backend()
    model = model or settings.get_active_llm_model()

    if not _backend_logged:
        logger.info(f"LLM backend: {backend} (model: {model})")
        _backend_logged = True

    if backend == "api":
        return await _call_via_api(prompt, system, model, max_tokens)
    return await _call_via_cli(prompt, system, model, max_tokens)


async def _call_via_api(
    prompt: str,
    system: str | None,
    model: str,
    max_tokens: int,
) -> str:
    """Call LLM via the Anthropic Python SDK."""
    client = get_anthropic_client()

    kwargs: dict = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
            }
        ],
    }

    if system:
        kwargs["system"] = [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    response = await client.messages.create(**kwargs)
    return response.content[0].text


async def _call_via_cli(
    prompt: str,
    system: str | None,
    model: str,
    max_tokens: int,  # noqa: ARG001 — kept for interface parity with _call_via_api
) -> str:
    """Call LLM via the Claude CLI subprocess.

    Spawns `claude -p` with structured JSON output. The prompt is piped
    via stdin to avoid shell escaping issues. The CLI does not support
    max_tokens — response length is managed by the CLI internally.
    """
    cmd = [
        "claude",
        "-p",
        "--output-format", "json",
        "--model", model,
        "--tools", "",
        "--no-session-persistence",
    ]

    if system:
        cmd.extend(["--system-prompt", system])

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await asyncio.wait_for(
        proc.communicate(input=prompt.encode("utf-8")),
        timeout=300,
    )

    returncode = proc.returncode or 0
    if returncode != 0:
        error_info = classify_cli_error(stderr.decode("utf-8", errors="replace"), returncode)
        raise LLMBackendError(
            error_info.message,
            details={"category": error_info.category, "is_fatal": error_info.is_fatal},
        )

    # Parse JSON response
    try:
        response_data = json.loads(stdout.decode("utf-8"))
    except json.JSONDecodeError as e:
        # stdout might be plain text if --output-format wasn't honored
        raw = stdout.decode("utf-8", errors="replace")
        if raw.strip():
            return raw.strip()
        raise LLMBackendError(
            f"Failed to parse CLI JSON response: {e}",
            details={"stdout_preview": raw[:500]},
        )

    # Check for error in structured response
    if response_data.get("is_error"):
        error_text = response_data.get("result", "Unknown CLI error")
        error_info = classify_cli_error(error_text, 0)
        raise LLMBackendError(
            error_info.message,
            details={"category": error_info.category, "is_fatal": error_info.is_fatal},
        )

    return response_data.get("result", "")
