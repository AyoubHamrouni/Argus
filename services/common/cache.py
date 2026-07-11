"""Redis-based caching for frequently accessed data."""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def init_redis(url: str = "redis://redis:6379/0") -> redis.Redis:
    """Initialize Redis connection pool."""
    global _redis_pool, _redis_client
    try:
        _redis_pool = redis.ConnectionPool.from_url(
            url, max_connections=20, decode_responses=True
        )
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        await _redis_client.ping()
        logger.info("Redis connected successfully")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable, caching disabled: {e}")
        _redis_client = None
        return None


async def close_redis():
    """Close Redis connection."""
    global _redis_client, _redis_pool
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
    if _redis_pool:
        await _redis_pool.disconnect()
        _redis_pool = None


def get_redis() -> Optional[redis.Redis]:
    """Get the current Redis client."""
    return _redis_client


def make_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a deterministic cache key from prefix and arguments."""
    key_parts = [prefix]
    for arg in args:
        key_parts.append(str(arg))
    for k, v in sorted(kwargs.items()):
        key_parts.append(f"{k}={v}")
    raw = ":".join(key_parts)
    if len(raw) > 128:
        return f"{prefix}:{hashlib.md5(raw.encode()).hexdigest()}"
    return raw


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache."""
    client = get_redis()
    if not client:
        return None
    try:
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.debug(f"Cache get failed for {key}: {e}")
        return None


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set a value in cache with TTL in seconds."""
    client = get_redis()
    if not client:
        return False
    try:
        serialized = json.dumps(value, default=str)
        await client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.debug(f"Cache set failed for {key}: {e}")
        return False


async def cache_delete(pattern: str) -> int:
    """Delete keys matching a pattern."""
    client = get_redis()
    if not client:
        return 0
    try:
        keys = []
        async for key in client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception as e:
        logger.debug(f"Cache delete failed for {pattern}: {e}")
        return 0


def cached(prefix: str, ttl: int = 300, key_builder: Optional[Callable] = None):
    """Decorator for caching async function results.

    Usage:
        @cached("rag:retrieve", ttl=600)
        async def retrieve(query: str, collection: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = make_cache_key(prefix, *args, **kwargs)

            # Try cache first
            cached_value = await cache_get(cache_key)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = await func(*args, **kwargs)
            if result is not None:
                await cache_set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
