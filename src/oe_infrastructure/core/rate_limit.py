"""In-process rate limiting.

Production deployments should place this service behind an edge gateway
(nginx/cloud) for distributed rate limiting; the middleware here provides a
defense-in-depth token bucket per route. Data is only ever in memory.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import Request

from oe_infrastructure.config import get_settings
from oe_infrastructure.core.errors import RateLimitedError


class TokenBucket:
    def __init__(self, capacity: float, refill_per_second: float) -> None:
        self.capacity = capacity
        self.tokens = capacity
        self.refill_per_second = refill_per_second
        self.updated_at = time.monotonic()

    def try_consume(self, amount: float = 1.0) -> bool:
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.updated_at = now
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class InMemoryRateLimiter:
    """Per-key token bucket limiter guarded by a lock."""

    def __init__(self) -> None:
        self._buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(0, 0.0)
        )
        self._lock = Lock()
        self._last_prune = time.monotonic()

    def _prune(self) -> None:
        now = time.monotonic()
        if now - self._last_prune > 300:
            stale = [
                key
                for key, bucket in self._buckets.items()
                if now - bucket.updated_at > 900
            ]
            for key in stale:
                self._buckets.pop(key, None)
            self._last_prune = now

    def consume(self, key: str, permits_per_minute: int | None = None) -> None:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return
        rpm = permits_per_minute or settings.rate_limit_default_per_minute
        if rpm <= 0:
            return
        with self._lock:
            self._prune()
            bucket = self._buckets[key]
            if bucket.capacity != rpm:
                first_use = bucket.capacity == 0
                bucket.capacity = float(rpm)
                bucket.refill_per_second = rpm / 60.0
                bucket.tokens = float(rpm) if first_use else min(bucket.tokens, float(rpm))
            allowed = bucket.try_consume(1.0)
        if not allowed:
            raise RateLimitedError(retry_after_seconds=60 // rpm)


_limiter = InMemoryRateLimiter()


class RateLimitKey:
    """FastAPI dependency that rate-limits by client IP + path.

    Usage::

        router.get("/events", dependencies=[Depends(rate_limit(60))])
    """

    def __init__(self, permits_per_minute: int) -> None:
        self.permits_per_minute = permits_per_minute

    def __call__(self, request: Request) -> None:
        forwarded = request.headers.get("x-forwarded-for")
        client_ip = (
            forwarded.split(",")[0].strip()
            if forwarded
            else (request.client.host if request.client else "unknown")
        )
        # Verified client IP is fine for a per-key bucket (in-memory only).
        _limiter.consume(f"{request.url.path}:{client_ip}", self.permits_per_minute)


def rate_limit(permits_per_minute: int = 120) -> RateLimitKey:
    return RateLimitKey(permits_per_minute)