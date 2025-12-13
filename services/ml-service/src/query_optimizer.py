"""
Query Optimizer - Agent 12 Performance Optimization

Provides optimized database queries for winner detection and processing.
Includes connection pooling, query caching, and performance analytics.

Created: 2025-12-13
"""

import os
import logging
import hashlib
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from functools import lru_cache
from dataclasses import dataclass

from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.orm import sessionmaker, Session

# Configure logging
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

@dataclass
class QueryOptimizerConfig:
    """Configuration for query optimizer."""
    # Connection pool settings
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 1800  # 30 minutes

    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    max_cache_size: int = 1000

    # Query settings
    query_timeout_seconds: int = 30
    slow_query_threshold_ms: int = 100

    # Batch settings
    batch_size: int = 100
    max_concurrent_queries: int = 5


# Default configuration
DEFAULT_CONFIG = QueryOptimizerConfig()


# ============================================================================
# Query Cache
# ============================================================================

class QueryCache:
    """In-memory query result cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def _generate_key(self, query: str, params: Optional[Dict] = None) -> str:
        """Generate a cache key from query and parameters."""
        key_data = query + json.dumps(params or {}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Get cached result if available and not expired."""
        key = self._generate_key(query, params)
        if key in self.cache:
            result, expires_at = self.cache[key]
            if time.time() < expires_at:
                self.hits += 1
                logger.debug(f"Cache HIT for query: {query[:50]}...")
                return result
            else:
                # Expired, remove from cache
                del self.cache[key]

        self.misses += 1
        logger.debug(f"Cache MISS for query: {query[:50]}...")
        return None

    def set(
        self,
        query: str,
        result: Any,
        params: Optional[Dict] = None,
        ttl: Optional[int] = None
    ) -> None:
        """Cache a query result."""
        # Evict oldest entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_expired()
            if len(self.cache) >= self.max_size:
                # Remove oldest 10% of entries
                entries_to_remove = int(self.max_size * 0.1)
                for key in list(self.cache.keys())[:entries_to_remove]:
                    del self.cache[key]

        key = self._generate_key(query, params)
        expires_at = time.time() + (ttl or self.default_ttl)
        self.cache[key] = (result, expires_at)

    def _evict_expired(self) -> int:
        """Remove all expired entries."""
        now = time.time()
        expired_keys = [
            key for key, (_, expires_at) in self.cache.items()
            if now >= expires_at
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)

    def invalidate(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries matching pattern or all if None."""
        if pattern is None:
            count = len(self.cache)
            self.cache.clear()
            return count

        # Pattern-based invalidation (simple prefix match)
        keys_to_remove = [
            key for key in self.cache.keys()
            if pattern in key
        ]
        for key in keys_to_remove:
            del self.cache[key]
        return len(keys_to_remove)

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_seconds": self.default_ttl
        }


# ============================================================================
# Query Performance Tracker
# ============================================================================

class QueryPerformanceTracker:
    """Tracks query performance metrics."""

    def __init__(self, slow_threshold_ms: int = 100):
        self.slow_threshold_ms = slow_threshold_ms
        self.queries: List[Dict[str, Any]] = []
        self.max_history = 1000

    def record(
        self,
        query: str,
        duration_ms: float,
        rows_affected: int = 0,
        cached: bool = False
    ) -> None:
        """Record query execution metrics."""
        entry = {
            "query": query[:200],  # Truncate for storage
            "duration_ms": round(duration_ms, 2),
            "rows_affected": rows_affected,
            "cached": cached,
            "is_slow": duration_ms > self.slow_threshold_ms,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.queries.append(entry)

        # Keep history bounded
        if len(self.queries) > self.max_history:
            self.queries = self.queries[-self.max_history:]

        if entry["is_slow"]:
            logger.warning(
                f"Slow query detected ({duration_ms:.2f}ms): {query[:100]}..."
            )

    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slowest queries."""
        slow = [q for q in self.queries if q["is_slow"]]
        return sorted(slow, key=lambda x: x["duration_ms"], reverse=True)[:limit]

    def stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.queries:
            return {"total_queries": 0}

        durations = [q["duration_ms"] for q in self.queries]
        slow_count = sum(1 for q in self.queries if q["is_slow"])
        cached_count = sum(1 for q in self.queries if q["cached"])

        return {
            "total_queries": len(self.queries),
            "avg_duration_ms": round(sum(durations) / len(durations), 2),
            "max_duration_ms": round(max(durations), 2),
            "min_duration_ms": round(min(durations), 2),
            "slow_query_count": slow_count,
            "slow_query_threshold_ms": self.slow_threshold_ms,
            "cache_hit_count": cached_count,
            "cache_hit_rate": round(cached_count / len(self.queries) * 100, 2)
        }


# ============================================================================
# Optimized Query Builder
# ============================================================================

class OptimizedQueryBuilder:
    """Builds optimized SQL queries for winner detection."""

    # Pre-defined optimized queries
    WINNER_DETECTION_QUERY = """
        SELECT
            a.id as ad_id,
            a.video_id,
            a.campaign_id,
            a.actual_ctr as ctr,
            a.actual_roas as roas,
            a.impressions,
            a.spend,
            a.conversions,
            a.revenue,
            a.creative_dna,
            a.created_at
        FROM ads a
        WHERE a.status = 'published'
          AND a.impressions >= :min_impressions
          AND a.actual_ctr >= :min_ctr
          AND a.actual_roas >= :min_roas
          AND a.created_at >= :since_date
        ORDER BY a.actual_roas DESC, a.actual_ctr DESC
        LIMIT :limit
    """

    WINNER_COUNT_QUERY = """
        SELECT COUNT(*) as count
        FROM ads
        WHERE status = 'published'
          AND impressions >= :min_impressions
          AND actual_ctr >= :min_ctr
          AND actual_roas >= :min_roas
          AND created_at >= :since_date
    """

    TOP_PERFORMERS_QUERY = """
        SELECT
            a.id as ad_id,
            a.campaign_id,
            a.actual_ctr as ctr,
            a.actual_roas as roas,
            a.spend,
            a.revenue,
            (a.revenue - a.spend) as profit,
            a.creative_dna
        FROM ads a
        WHERE a.status = 'published'
          AND a.impressions >= 1000
          AND a.created_at >= NOW() - INTERVAL ':days days'
        ORDER BY (a.revenue - a.spend) DESC
        LIMIT :limit
    """

    BUDGET_REALLOCATION_CANDIDATES = """
        WITH winner_ads AS (
            SELECT id, campaign_id, actual_roas, spend
            FROM ads
            WHERE status = 'published'
              AND actual_ctr >= :min_ctr
              AND actual_roas >= :min_roas
              AND impressions >= :min_impressions
        ),
        underperformer_ads AS (
            SELECT id, campaign_id, actual_roas, spend
            FROM ads
            WHERE status = 'published'
              AND impressions >= :min_impressions
              AND actual_roas < :underperformer_roas_threshold
        )
        SELECT
            'winner' as ad_type,
            w.id as ad_id,
            w.campaign_id,
            w.actual_roas,
            w.spend
        FROM winner_ads w
        UNION ALL
        SELECT
            'underperformer' as ad_type,
            u.id as ad_id,
            u.campaign_id,
            u.actual_roas,
            u.spend
        FROM underperformer_ads u
        ORDER BY ad_type, actual_roas DESC
    """

    CREATIVE_DNA_PATTERNS = """
        SELECT
            creative_dna->>'hook_type' as hook_type,
            creative_dna->>'cta_type' as cta_type,
            COUNT(*) as count,
            AVG(actual_ctr) as avg_ctr,
            AVG(actual_roas) as avg_roas
        FROM ads
        WHERE status = 'published'
          AND actual_ctr >= :min_ctr
          AND actual_roas >= :min_roas
          AND impressions >= :min_impressions
        GROUP BY
            creative_dna->>'hook_type',
            creative_dna->>'cta_type'
        ORDER BY avg_roas DESC, count DESC
        LIMIT :limit
    """

    @classmethod
    def get_winner_detection_query(cls) -> str:
        """Get optimized winner detection query."""
        return cls.WINNER_DETECTION_QUERY

    @classmethod
    def get_budget_reallocation_query(cls) -> str:
        """Get budget reallocation candidates query."""
        return cls.BUDGET_REALLOCATION_CANDIDATES


# ============================================================================
# Query Optimizer
# ============================================================================

class QueryOptimizer:
    """
    High-performance query optimizer with caching and connection pooling.

    Features:
    - Connection pooling with SQLAlchemy
    - Query result caching with TTL
    - Slow query detection and logging
    - Batch query execution
    - Performance metrics
    """

    def __init__(
        self,
        database_url: Optional[str] = None,
        config: Optional[QueryOptimizerConfig] = None
    ):
        """
        Initialize query optimizer.

        Args:
            database_url: Database connection URL
            config: Optimizer configuration
        """
        self.config = config or DEFAULT_CONFIG
        self.database_url = database_url or os.getenv("DATABASE_URL")

        # Initialize components
        self.cache = QueryCache(
            max_size=self.config.max_cache_size,
            default_ttl=self.config.cache_ttl_seconds
        )
        self.performance_tracker = QueryPerformanceTracker(
            slow_threshold_ms=self.config.slow_query_threshold_ms
        )

        # Initialize connection pool
        self._engine: Optional[Engine] = None
        self._session_factory = None

        if self.database_url:
            self._init_engine()

    def _init_engine(self) -> None:
        """Initialize SQLAlchemy engine with connection pool."""
        if not self.database_url:
            logger.warning("No database URL configured")
            return

        pool_class = QueuePool

        # Use StaticPool for SQLite
        if "sqlite" in self.database_url.lower():
            pool_class = StaticPool

        self._engine = create_engine(
            self.database_url,
            poolclass=pool_class,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,  # Verify connections before use
            echo=False
        )

        self._session_factory = sessionmaker(bind=self._engine)

        # Add query timing events
        @event.listens_for(self._engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault("query_start_time", []).append(time.time())

        @event.listens_for(self._engine, "after_cursor_execute")
        def after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            start_time = conn.info.get("query_start_time", []).pop()
            duration_ms = (time.time() - start_time) * 1000
            self.performance_tracker.record(
                query=statement,
                duration_ms=duration_ms,
                rows_affected=cursor.rowcount
            )

        logger.info("✅ Query optimizer initialized with connection pool")

    def get_session(self) -> Session:
        """Get a database session from the pool."""
        if not self._session_factory:
            raise RuntimeError("Database not configured")
        return self._session_factory()

    def execute(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query with optional caching.

        Args:
            query: SQL query string
            params: Query parameters
            use_cache: Whether to use cache
            cache_ttl: Cache TTL in seconds

        Returns:
            List of result dictionaries
        """
        # Check cache first
        if use_cache and self.config.cache_enabled:
            cached_result = self.cache.get(query, params)
            if cached_result is not None:
                self.performance_tracker.record(
                    query=query,
                    duration_ms=0.1,
                    cached=True
                )
                return cached_result

        # Execute query
        start_time = time.time()

        session = self.get_session()
        try:
            result = session.execute(text(query), params or {})
            rows = [dict(row._mapping) for row in result.fetchall()]

            # Cache result
            if use_cache and self.config.cache_enabled:
                self.cache.set(query, rows, params, cache_ttl)

            return rows

        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
        finally:
            session.close()

    def execute_batch(
        self,
        queries: List[Tuple[str, Dict[str, Any]]],
        use_cache: bool = True
    ) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries efficiently.

        Args:
            queries: List of (query, params) tuples
            use_cache: Whether to use cache

        Returns:
            List of result lists
        """
        results = []
        for query, params in queries:
            result = self.execute(query, params, use_cache)
            results.append(result)
        return results

    def detect_winners(
        self,
        min_ctr: float = 0.03,
        min_roas: float = 2.0,
        min_impressions: int = 1000,
        days_back: int = 7,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Detect winner ads using optimized query.

        Args:
            min_ctr: Minimum CTR threshold
            min_roas: Minimum ROAS threshold
            min_impressions: Minimum impressions
            days_back: Days to look back
            limit: Maximum results

        Returns:
            List of winner ads
        """
        query = OptimizedQueryBuilder.get_winner_detection_query()
        params = {
            "min_ctr": min_ctr,
            "min_roas": min_roas,
            "min_impressions": min_impressions,
            "since_date": datetime.utcnow() - timedelta(days=days_back),
            "limit": limit
        }

        return self.execute(query, params, use_cache=True, cache_ttl=60)

    def get_budget_reallocation_candidates(
        self,
        min_ctr: float = 0.03,
        min_roas: float = 2.0,
        min_impressions: int = 1000,
        underperformer_roas_threshold: float = 1.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get candidates for budget reallocation.

        Returns:
            Dictionary with 'winners' and 'underperformers' lists
        """
        query = OptimizedQueryBuilder.get_budget_reallocation_query()
        params = {
            "min_ctr": min_ctr,
            "min_roas": min_roas,
            "min_impressions": min_impressions,
            "underperformer_roas_threshold": underperformer_roas_threshold
        }

        results = self.execute(query, params, use_cache=True, cache_ttl=120)

        return {
            "winners": [r for r in results if r.get("ad_type") == "winner"],
            "underperformers": [
                r for r in results if r.get("ad_type") == "underperformer"
            ]
        }

    def invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cache entries."""
        return self.cache.invalidate(pattern)

    def stats(self) -> Dict[str, Any]:
        """Get optimizer statistics."""
        pool_stats = {}
        if self._engine and hasattr(self._engine.pool, "status"):
            pool = self._engine.pool
            pool_stats = {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow()
            }

        return {
            "cache": self.cache.stats(),
            "performance": self.performance_tracker.stats(),
            "connection_pool": pool_stats,
            "config": {
                "pool_size": self.config.pool_size,
                "cache_enabled": self.config.cache_enabled,
                "cache_ttl_seconds": self.config.cache_ttl_seconds
            }
        }

    def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get slow queries for analysis."""
        return self.performance_tracker.get_slow_queries(limit)

    def health_check(self) -> Dict[str, Any]:
        """Check database connectivity."""
        try:
            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            return {"status": "healthy", "database": "connected"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# ============================================================================
# Global Instance
# ============================================================================

# Singleton instance
_query_optimizer: Optional[QueryOptimizer] = None


def get_query_optimizer(
    database_url: Optional[str] = None,
    config: Optional[QueryOptimizerConfig] = None
) -> QueryOptimizer:
    """Get or create the global query optimizer instance."""
    global _query_optimizer

    if _query_optimizer is None:
        _query_optimizer = QueryOptimizer(database_url, config)

    return _query_optimizer


# ============================================================================
# Usage Example
# ============================================================================

if __name__ == "__main__":
    # Example usage
    optimizer = get_query_optimizer()

    # Check health
    health = optimizer.health_check()
    print(f"Health: {health}")

    # Get stats
    stats = optimizer.stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
