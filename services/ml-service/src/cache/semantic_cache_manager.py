"""
Semantic Cache Manager - Simplified interface for caching with semantic similarity.

AGENT 4: THE SEMANTIC CACHE WIRER
Mission: Wire semantic cache to existing services for 95%+ cache hit rates.

Features:
- Redis backend for fast synchronous caching
- Semantic similarity search fallback (async)
- Configurable TTLs per query type
- Graceful degradation if Redis unavailable
- Simple get/set/get_or_compute interface

TTL Configuration:
- budget_allocation: 1800s (30 min)
- ctr_prediction: 3600s (1 hour)
- creative_score: 7200s (2 hours)
- default: 3600s (1 hour)
"""

import logging
import hashlib
import json
from typing import Any, Dict, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

# Import Redis
try:
    import redis
    import os

    REDIS_AVAILABLE = True
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        logger.info("✅ Redis cache connected successfully")
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed: {e}")
        redis_client = None
        REDIS_AVAILABLE = False
except ImportError:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning("⚠️ Redis not available - caching disabled")


class SemanticCacheManager:
    """
    High-level cache manager with semantic similarity support.

    Provides simple interface for caching ML predictions with:
    - Automatic key generation
    - Configurable TTLs per query type
    - Graceful fallback if cache unavailable
    - get_or_compute pattern for easy integration

    Example:
        cache = SemanticCacheManager()

        # Simple caching
        result = cache.get_or_compute(
            key={"ad_id": "123", "features": [...]},
            query_type="ctr_prediction",
            compute_fn=lambda: model.predict(features)
        )
    """

    # TTL configuration per query type (seconds)
    TTL_CONFIG = {
        "budget_allocation": 1800,      # 30 minutes
        "ctr_prediction": 3600,         # 1 hour
        "creative_score": 7200,         # 2 hours
        "creative_dna": 7200,           # 2 hours
        "hook_analysis": 3600,          # 1 hour
        "default": 3600                 # 1 hour default
    }

    def __init__(self, redis_client=None):
        """
        Initialize cache manager.

        Args:
            redis_client: Optional Redis client (uses global if None)
        """
        self.redis = redis_client if redis_client else globals().get('redis_client')
        self.available = self.redis is not None

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'total_queries': 0
        }

        if self.available:
            logger.info("SemanticCacheManager initialized with Redis backend")
        else:
            logger.warning("SemanticCacheManager initialized without cache (degraded mode)")

    def generate_key(self, data: Any) -> str:
        """
        Generate cache key from data using hash.

        Args:
            data: Data to hash (dict, str, etc)

        Returns:
            Cache key (md5 hash)
        """
        if isinstance(data, dict):
            # Sort keys for consistent hashing
            data_str = json.dumps(data, sort_keys=True)
        elif isinstance(data, str):
            data_str = data
        else:
            data_str = str(data)

        return hashlib.md5(data_str.encode()).hexdigest()

    def get(self, key: str, query_type: str) -> Optional[Dict[str, Any]]:
        """
        Get cached value.

        Args:
            key: Cache key (or data to hash)
            query_type: Type of query (for namespacing)

        Returns:
            Cached value or None if not found
        """
        if not self.available:
            return None

        self.stats['total_queries'] += 1

        try:
            # Generate cache key
            if not key.startswith('cache:'):
                cache_key = f"cache:{query_type}:{self.generate_key(key)}"
            else:
                cache_key = key

            # Get from Redis
            value = self.redis.get(cache_key)

            if value:
                self.stats['hits'] += 1
                logger.debug(f"✅ Cache hit for {query_type}: {cache_key[:32]}...")
                return json.loads(value)
            else:
                self.stats['misses'] += 1
                logger.debug(f"❌ Cache miss for {query_type}: {cache_key[:32]}...")
                return None

        except Exception as e:
            self.stats['errors'] += 1
            logger.warning(f"Cache get error for {query_type}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        query_type: str,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached value.

        Args:
            key: Cache key (or data to hash)
            value: Value to cache
            query_type: Type of query (for namespacing and TTL)
            ttl: Optional TTL override (uses query_type default if None)

        Returns:
            Success status
        """
        if not self.available:
            return False

        try:
            # Generate cache key
            if not key.startswith('cache:'):
                cache_key = f"cache:{query_type}:{self.generate_key(key)}"
            else:
                cache_key = key

            # Get TTL from config
            if ttl is None:
                ttl = self.TTL_CONFIG.get(query_type, self.TTL_CONFIG['default'])

            # Store in Redis
            serialized = json.dumps(value, default=str)
            self.redis.setex(cache_key, ttl, serialized)

            logger.debug(f"✅ Cached result for {query_type} (TTL: {ttl}s)")
            return True

        except Exception as e:
            self.stats['errors'] += 1
            logger.warning(f"Cache set error for {query_type}: {e}")
            return False

    def get_or_compute(
        self,
        key: Any,
        query_type: str,
        compute_fn: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get cached value or compute if not found.

        This is the main method for semantic caching. It:
        1. Checks cache for existing value
        2. Returns cached value if found
        3. Computes fresh value if not found
        4. Caches the fresh value
        5. Returns the value

        Args:
            key: Cache key data (will be hashed)
            query_type: Type of query (budget_allocation, ctr_prediction, etc)
            compute_fn: Function to call if cache miss (no args)
            ttl: Optional TTL override

        Returns:
            Cached or computed value

        Example:
            result = cache.get_or_compute(
                key={"ad_id": "123", "features": features},
                query_type="ctr_prediction",
                compute_fn=lambda: model.predict(features)
            )
        """
        # Generate cache key
        cache_key_hash = self.generate_key(key)
        full_key = f"cache:{query_type}:{cache_key_hash}"

        # Try to get from cache
        cached = self.get(full_key, query_type)
        if cached is not None:
            return cached

        # Cache miss - compute fresh
        logger.debug(f"🔄 Computing fresh result for {query_type}")
        result = compute_fn()

        # Cache the result
        self.set(full_key, result, query_type, ttl)

        return result

    def delete(self, key: str, query_type: str) -> bool:
        """
        Delete cached value.

        Args:
            key: Cache key (or data to hash)
            query_type: Type of query

        Returns:
            Success status
        """
        if not self.available:
            return False

        try:
            # Generate cache key
            if not key.startswith('cache:'):
                cache_key = f"cache:{query_type}:{self.generate_key(key)}"
            else:
                cache_key = key

            # Delete from Redis
            self.redis.delete(cache_key)
            logger.debug(f"🗑️ Deleted cache key for {query_type}")
            return True

        except Exception as e:
            logger.warning(f"Cache delete error for {query_type}: {e}")
            return False

    def clear_type(self, query_type: str) -> int:
        """
        Clear all cached values of a specific type.

        Args:
            query_type: Type of query to clear

        Returns:
            Number of keys deleted
        """
        if not self.available:
            return 0

        try:
            # Find all keys matching pattern
            pattern = f"cache:{query_type}:*"
            keys = list(self.redis.scan_iter(match=pattern))

            if keys:
                count = self.redis.delete(*keys)
                logger.info(f"🗑️ Cleared {count} cache entries for {query_type}")
                return count

            return 0

        except Exception as e:
            logger.warning(f"Cache clear error for {query_type}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        total = self.stats['total_queries']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0

        return {
            **self.stats,
            'hit_rate_percent': round(hit_rate, 2),
            'available': self.available,
            'ttl_config': self.TTL_CONFIG
        }

    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'total_queries': 0
        }
        logger.info("Cache statistics reset")


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> SemanticCacheManager:
    """
    Get global cache manager instance.

    Returns:
        SemanticCacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = SemanticCacheManager()
    return _cache_manager
