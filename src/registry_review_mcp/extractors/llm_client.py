"""
Multi-provider LLM client using LiteLLM.

Supports Anthropic, Google Gemini, and OpenAI with a unified interface.
"""

import asyncio
import logging
import os
import random
from typing import Any

import litellm
from litellm import acompletion
from litellm.exceptions import (
    RateLimitError,
    ServiceUnavailableError,
    APIConnectionError,
    Timeout,
)

from ..config.settings import settings

logger = logging.getLogger(__name__)

# Suppress LiteLLM's verbose logging
litellm.suppress_debug_info = True


class LLMClient:
    """Unified LLM client supporting multiple providers via LiteLLM."""

    def __init__(self):
        """Initialize LLM client with appropriate API keys based on provider."""
        self.provider = settings.llm_provider
        self.model = settings.get_active_llm_model()
        self._setup_api_keys()

    def _setup_api_keys(self):
        """Set up API keys for LiteLLM based on configured provider."""
        if self.provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
        elif self.provider == "gemini":
            os.environ["GEMINI_API_KEY"] = settings.google_api_key
        elif self.provider == "openai":
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key

    async def create_message(
        self,
        messages: list[dict],
        max_tokens: int = 4000,
        temperature: float = 0.0,
        system: str | None = None,
    ) -> dict[str, Any]:
        """Create a message/completion using the configured LLM provider.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0 = deterministic)
            system: Optional system prompt

        Returns:
            Response dict with 'content' (text) and 'usage' (token counts)
        """
        # Build the messages list
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        # Call LiteLLM
        response = await acompletion(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Extract content and usage
        content = response.choices[0].message.content
        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
        }

        return {
            "content": content,
            "usage": usage,
            "model": response.model,
        }

    async def create_message_with_retry(
        self,
        messages: list[dict],
        max_tokens: int = 4000,
        temperature: float = 0.0,
        system: str | None = None,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 32.0,
    ) -> dict[str, Any]:
        """Create a message with exponential backoff retry on transient errors.

        Args:
            messages: List of message dicts
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            system: Optional system prompt
            max_retries: Maximum retry attempts
            initial_delay: Initial delay between retries
            max_delay: Maximum delay between retries

        Returns:
            Response dict with 'content' and 'usage'
        """
        delay = initial_delay
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return await self.create_message(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                )

            except (RateLimitError, ServiceUnavailableError, APIConnectionError, Timeout) as e:
                last_exception = e
                error_type = type(e).__name__

                if attempt < max_retries:
                    jitter = delay * 0.25 * (2 * random.random() - 1)
                    sleep_time = min(delay + jitter, max_delay)

                    logger.warning(
                        f"LLM API call failed with {error_type} (attempt {attempt + 1}/{max_retries + 1}). "
                        f"Retrying in {sleep_time:.2f}s... Error: {str(e)}"
                    )

                    await asyncio.sleep(sleep_time)
                    delay = min(delay * 2, max_delay)
                else:
                    logger.error(
                        f"LLM API call failed after {max_retries + 1} attempts. "
                        f"Final error: {error_type}: {str(e)}"
                    )
                    raise

            except Exception as e:
                logger.error(f"LLM API call failed with non-retryable error: {type(e).__name__}: {str(e)}")
                raise

        if last_exception:
            raise last_exception


def get_llm_client() -> LLMClient:
    """Get an LLM client configured for the current provider.

    Returns:
        LLMClient instance
    """
    return LLMClient()
