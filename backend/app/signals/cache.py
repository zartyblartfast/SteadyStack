"""Redis-backed caching layer for signal data.

Provides a simple async get/set interface with TTL support.
Falls back gracefully if Redis is unavailable — returns None on get,
silently skips on set. The collector handles cache misses by fetching live.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the shared Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


async def cache_get(key: str) -> Any | None:
    """Retrieve a cached value by key.

    Returns:
        The deserialized value, or None if not found or Redis is unavailable.
    """
    try:
        client = await get_redis()
        raw = await client.get(f"ss:{key}")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("Cache read failed for key=%s", key, exc_info=True)
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    """Store a value in cache with a TTL.

    Silently skips if Redis is unavailable — caching is an optimization, not a requirement.
    """
    try:
        client = await get_redis()
        await client.set(f"ss:{key}", json.dumps(value), ex=ttl_seconds)
    except Exception:
        logger.warning("Cache write failed for key=%s", key, exc_info=True)


async def cache_age(key: str) -> float | None:
    """Get the age of a cached value in seconds using its TTL.

    Returns:
        Approximate age in seconds, or None if the key doesn't exist.
    """
    try:
        client = await get_redis()
        ttl = await client.ttl(f"ss:{key}")
        if ttl is None or ttl < 0:
            return None
        # We don't store the original TTL, so we can't compute exact age.
        # This returns the *remaining* TTL, which the collector can use
        # to estimate staleness relative to the configured TTL.
        return float(ttl)
    except Exception:
        logger.warning("Cache TTL check failed for key=%s", key, exc_info=True)
        return None
