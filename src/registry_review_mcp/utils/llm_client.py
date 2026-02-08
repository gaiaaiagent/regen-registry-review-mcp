"""Centralized Anthropic client creation and API error handling.

Provides pre-flight validation, human-readable error classification, and
a factory function so every call site gets consistent behavior. Fatal errors
(no credits, bad key) are surfaced immediately rather than silently swallowed.
"""

import logging
from dataclasses import dataclass

from anthropic import AsyncAnthropic

from ..config.settings import settings
from ..models.errors import ConfigurationError

logger = logging.getLogger(__name__)


class LLMBillingError(ConfigurationError):
    """API call failed due to billing — insufficient credits or expired plan."""

    pass


class LLMAuthenticationError(ConfigurationError):
    """API call failed due to an invalid or revoked API key."""

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
