"""Redis client for caching with TTL support."""

import redis
import json
import os
from typing import Any, Optional

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD,
    decode_responses=True
)

def get_redis_client() -> redis.Redis:
    """Get Redis client instance."""
    return redis_client

def set_cache(key: str, value: Any, ttl: int = 3600) -> bool:
    """
    Set cache value with TTL.

    Args:
        key: Cache key
        value: Value to cache (will be JSON serialized)
        ttl: Time to live in seconds (default 1 hour)

    Returns:
        Success status
    """
    try:
        serialized = json.dumps(value)
        redis_client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        print(f"Redis cache set failed: {e}")
        return False

def get_cache(key: str) -> Optional[Any]:
    """
    Get cached value.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        print(f"Redis cache get failed: {e}")
        return None

def delete_cache(key: str) -> bool:
    """
    Delete cached value.

    Args:
        key: Cache key

    Returns:
        Success status
    """
    try:
        redis_client.delete(key)
        return True
    except Exception as e:
        print(f"Redis cache delete failed: {e}")
        return False

def cache_exists(key: str) -> bool:
    """
    Check if cache key exists.

    Args:
        key: Cache key

    Returns:
        True if exists
    """
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        print(f"Redis cache exists check failed: {e}")
        return False
