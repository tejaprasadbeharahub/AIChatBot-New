"""Reusable reliability primitives for MCP tools and external APIs."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from app.services.mcp.errors import MCPRateLimitError

T = TypeVar("T")


@dataclass
class RetryPolicy:
    max_attempts: int
    initial_delay_seconds: float
    max_delay_seconds: float
    timeout_seconds: float


def _compute_backoff(attempt: int, policy: RetryPolicy, retry_after: float | None) -> float:
    if retry_after is not None and retry_after >= 0:
        return min(retry_after, policy.max_delay_seconds)
    return min(policy.max_delay_seconds, policy.initial_delay_seconds * (2 ** (attempt - 1)))


async def retry_async(
    operation_name: str,
    operation: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    is_retryable_error: Callable[[Exception], bool],
    logger: logging.Logger,
) -> T:
    """Run an async operation with timeout + exponential backoff retries."""
    attempts = max(1, policy.max_attempts)
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(operation(), timeout=policy.timeout_seconds)
            return result
        except Exception as exc:
            last_error = exc
            retryable = is_retryable_error(exc)
            elapsed_ms = int((time.perf_counter() - started) * 1000)

            if not retryable or attempt >= attempts:
                logger.error(
                    "mcp_retry_exhausted",
                    extra={
                        "operation": operation_name,
                        "attempt": attempt,
                        "max_attempts": attempts,
                        "retryable": retryable,
                        "elapsed_ms": elapsed_ms,
                        "error": str(exc),
                    },
                )
                raise

            retry_after = exc.retry_after_seconds if isinstance(exc, MCPRateLimitError) else None
            delay = _compute_backoff(attempt, policy, retry_after)
            logger.warning(
                "mcp_retry_attempt",
                extra={
                    "operation": operation_name,
                    "attempt": attempt,
                    "max_attempts": attempts,
                    "delay_seconds": delay,
                    "elapsed_ms": elapsed_ms,
                    "error": str(exc),
                },
            )
            await asyncio.sleep(delay)

    assert last_error is not None
    raise last_error


class AsyncRateLimiter:
    """Simple min-interval asynchronous rate limiter."""

    def __init__(self, min_interval_seconds: float) -> None:
        self.min_interval_seconds = max(0.0, min_interval_seconds)
        self._lock = asyncio.Lock()
        self._last_ts = 0.0

    async def acquire(self) -> None:
        if self.min_interval_seconds <= 0:
            return

        async with self._lock:
            now = time.monotonic()
            wait = self.min_interval_seconds - (now - self._last_ts)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_ts = time.monotonic()


class AsyncSingleFlight:
    """De-duplicate concurrent async calls with the same key."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._inflight: dict[str, asyncio.Future[Any]] = {}

    async def do(self, key: str, factory: Callable[[], Awaitable[T]]) -> T:
        existing: asyncio.Future[Any] | None = None
        async with self._lock:
            existing = self._inflight.get(key)
            if existing is None:
                loop = asyncio.get_running_loop()
                fut: asyncio.Future[Any] = loop.create_future()
                self._inflight[key] = fut

        # Awaiting an existing call must happen outside the lock to avoid deadlocks.
        if existing is not None:
            return await existing

        fut = self._inflight[key]

        try:
            result = await factory()
            fut.set_result(result)
            return result
        except Exception as exc:
            fut.set_exception(exc)
            raise
        finally:
            async with self._lock:
                self._inflight.pop(key, None)
