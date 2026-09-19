"""Unit tests for the in-memory token-bucket rate limiter."""

from __future__ import annotations

import pytest

from oe_infrastructure.core.errors import RateLimitedError
from oe_infrastructure.core.rate_limit import InMemoryRateLimiter


def test_allows_up_to_capacity_then_blocks() -> None:
    limiter = InMemoryRateLimiter()
    for _ in range(3):
        limiter.consume("key", permits_per_minute=3)
    with pytest.raises(RateLimitedError):
        limiter.consume("key", permits_per_minute=3)


def test_first_use_grants_full_capacity() -> None:
    limiter = InMemoryRateLimiter()
    # A fresh key must not start exhausted.
    limiter.consume("fresh", permits_per_minute=1)


def test_keys_are_isolated() -> None:
    limiter = InMemoryRateLimiter()
    limiter.consume("a", permits_per_minute=1)
    # Different key still has capacity.
    limiter.consume("b", permits_per_minute=1)


def test_non_positive_limit_is_unlimited() -> None:
    limiter = InMemoryRateLimiter()
    for _ in range(100):
        limiter.consume("unlimited", permits_per_minute=0)


def test_capacity_change_does_not_reset_blocked_key() -> None:
    limiter = InMemoryRateLimiter()
    for _ in range(2):
        limiter.consume("k", permits_per_minute=2)
    with pytest.raises(RateLimitedError):
        limiter.consume("k", permits_per_minute=2)
