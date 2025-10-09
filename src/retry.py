"""
Retry utilities using tenacity for HTTP and Twitter API calls.
"""
from __future__ import annotations

from typing import Callable, Type

from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
    before_sleep_log,
)
import logging

# Tweepy dependency removed - using pure requests implementation


logger = logging.getLogger("crybb.retry")


def _rate_limit_handler(retry_state):
    # Hook to log retry attempts uniformly
    attempt = retry_state.attempt_number
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        "retrying_operation",
        extra={
            "module": "retry",
            "attempt": attempt,
            "exception": repr(exc),
        },
    )


def _build_wait_strategy():
    return wait_exponential(multiplier=0.5, min=0.5, max=8)


def retry_http(func: Callable):
    """Retry decorator for HTTP calls (e.g., requests)."""
    return retry(
        wait=_build_wait_strategy(),
        stop=stop_after_attempt(5),
        reraise=True,
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )(func)


def retry_api(func: Callable):
    """Retry decorator for Twitter API calls with rate limit handling."""

    def _should_retry_exception(exc: BaseException) -> bool:
        # Generic network / server errors
        return True

    return retry(
        wait=_build_wait_strategy(),
        stop=stop_after_attempt(5),
        reraise=True,
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )(func)


def maybe_sleep_for_rate_limit(e: BaseException) -> None:
    """Sleep to respect rate limits when TooManyRequests is encountered."""
    import time

    # Check for HTTP 429 status code or similar rate limit indicators
    if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
        if e.response.status_code == 429:
            retry_after = e.response.headers.get('Retry-After', 60)
            sleep_seconds = int(retry_after) if retry_after else 60
            logger.warning(
                "rate_limited_sleep",
                extra={"module": "retry", "sleep_seconds": sleep_seconds},
            )
            time.sleep(sleep_seconds)


