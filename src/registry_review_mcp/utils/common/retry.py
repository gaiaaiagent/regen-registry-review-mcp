"""Retry utilities with exponential backoff.

Consolidates retry logic found in:
- marker_extractor.py (PDF extraction)
- llm_extractors.py (LLM calls)
- document_tools.py (document processing)
"""

import asyncio
import logging
from typing import TypeVar, Callable, Any
from functools import wraps

T = TypeVar("T")

logger = logging.getLogger(__name__)


async def retry_with_backoff(
    func: Callable[..., T],
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    """Retry async function with exponential backoff.

    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        backoff_factor: Multiplier for delay between attempts
        initial_delay: Initial delay in seconds
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Result from successful function call

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts:
                logger.warning(
                    f"Attempt {attempt}/{max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_attempts} attempts failed")

    raise last_exception


def with_retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Decorator for automatic retry with exponential backoff.

    Usage:
        @with_retry(max_attempts=3, backoff_factor=2.0)
        async def my_function():
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            return await retry_with_backoff(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                backoff_factor=backoff_factor,
                initial_delay=initial_delay,
                exceptions=exceptions,
            )

        return wrapper

    return decorator
