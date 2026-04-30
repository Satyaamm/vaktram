"""Retry + circuit-breaker primitives for outbound integrations.

Wrap any async call that hits an external dependency (Groq, OpenAI, Stripe,
Google Calendar, the bot service) with `with_retry` to get exponential
backoff with jitter, and `breaker` to short-circuit when the dependency is
clearly down so we don't keep paying timeouts.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import random
import time
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)


class CircuitOpenError(RuntimeError):
    pass


class CircuitBreaker:
    """Simple half-open circuit breaker keyed by dependency name."""

    def __init__(self, name: str, failure_threshold: int = 5, recovery_seconds: float = 30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._failures = 0
        self._opened_at: float | None = None

    def _state(self) -> str:
        if self._opened_at is None:
            return "closed"
        if time.monotonic() - self._opened_at >= self.recovery_seconds:
            return "half_open"
        return "open"

    def before_call(self) -> None:
        s = self._state()
        if s == "open":
            raise CircuitOpenError(f"circuit '{self.name}' is open")
        # half_open: allow one trial through

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= self.failure_threshold:
            self._opened_at = time.monotonic()
            logger.warning("circuit '%s' opened after %d failures", self.name, self._failures)


_breakers: dict[str, CircuitBreaker] = {}


def breaker(name: str, **kwargs) -> CircuitBreaker:
    if name not in _breakers:
        _breakers[name] = CircuitBreaker(name, **kwargs)
    return _breakers[name]


def with_retry(
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    breaker_name: str | None = None,
    retry_on: tuple[type[BaseException], ...] = (Exception,),
):
    """Decorator: retry an async fn with exponential backoff + jitter."""

    def deco(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> T:
            cb = breaker(breaker_name) if breaker_name else None
            last_exc: BaseException | None = None
            for attempt in range(1, attempts + 1):
                if cb:
                    cb.before_call()
                try:
                    result = await fn(*args, **kwargs)
                    if cb:
                        cb.record_success()
                    return result
                except retry_on as exc:
                    last_exc = exc
                    if cb:
                        cb.record_failure()
                    if attempt == attempts:
                        break
                    delay = min(max_delay, base_delay * 2 ** (attempt - 1))
                    delay *= 0.5 + random.random()  # jitter
                    logger.info(
                        "%s failed (attempt %d/%d): %s — retrying in %.2fs",
                        fn.__name__, attempt, attempts, exc, delay,
                    )
                    await asyncio.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapper

    return deco
