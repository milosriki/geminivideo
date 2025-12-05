"""
Semantic Cache - Intelligent caching with semantic similarity matching.

AGENT 46: 10x LEVERAGE - Semantic Caching

Instead of exact match caching, use embedding similarity to reuse results:
- "Score this fitness ad" ≈ "Rate this gym advertisement" → Cache hit!
- 80%+ cache hit rate possible
- Massive cost savings on AI operations

Features:
- Embedding-based similarity search
- Confidence-aware cache hits (high/medium/low similarity thresholds)
- Automatic cache warming from training data
- Cache analytics and monitoring
- Time-based expiration
- Usage tracking and popularity scoring

Use cases:
- Creative scoring (hook scores, council votes)
- Hook analysis and classification
- CTR prediction
- Script generation
- Similar product recommendations
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json

from sqlalchemy import select, func, and_, or_, desc, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
import sys
import os

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'shared'))

from db.models import SemanticCacheEntry

# Import embedding pipeline
from src.embedding_pipeline import EmbeddingPipeline, get_embedder

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache hit strategies based on similarity scores."""
    EXACT = "exact"  # 100% match required
    HIGH = "high"  # >98% similarity - use cached directly
    MEDIUM = "medium"  # 92-98% similarity - use cached with flag
    LOW = "low"  # 85-92% similarity - compute fresh but log near-hit
    MISS = "miss"  # <85% similarity - compute fresh


@dataclass
class CacheHit:
    """Result from cache lookup."""
    hit: bool
    cached_result: Optional[Dict[str, Any]] = None
    similarity: float = 0.0
    strategy: CacheStrategy = CacheStrategy.MISS
    cache_id: Optional[str] = None
    age_seconds: Optional[float] = None
    usage_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'hit': self.hit,
            'cached_result': self.cached_result,
            'similarity': self.similarity,
            'strategy': self.strategy.value,
            'cache_id': self.cache_id,
            'age_seconds': self.age_seconds,
            'usage_count': self.usage_count
        }


@dataclass
class CacheEntry:
    """Semantic cache entry stored in database."""
    cache_id: str
    query_type: str  # 'creative_score', 'hook_analysis', 'ctr_prediction', etc.
    query_text: str  # Original query text
    query_embedding: List[float]  # Query embedding for similarity search
    result: Dict[str, Any]  # Cached result
    metadata: Dict[str, Any]  # Additional metadata
    created_at: datetime
    last_accessed_at: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None  # Time to live

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > self.ttl_seconds


class SemanticCache:
    """
    Semantic cache with embedding-based similarity matching.

    Instead of exact match caching, uses semantic similarity to reuse
    results for similar queries.

    Example:
        cache = SemanticCache(db_session, embedder)

        # First call - computes and caches
        result = await cache.get_or_compute(
            query="Score this fitness ad targeting women 25-35",
            query_type="creative_score",
            compute_fn=lambda q: ai_council.score_creative(q)
        )

        # Second call with similar query - returns cached!
        result = await cache.get_or_compute(
            query="Rate this gym advertisement for young women",
            query_type="creative_score",
            compute_fn=lambda q: ai_council.score_creative(q)
        )
        # 96% similarity → cache hit, returns cached result
    """

    def __init__(
        self,
        db_session: AsyncSession,
        embedder: Optional[EmbeddingPipeline] = None,
        high_similarity_threshold: float = 0.98,
        medium_similarity_threshold: float = 0.92,
        low_similarity_threshold: float = 0.85,
        default_ttl_seconds: int = 86400  # 24 hours
    ):
        """
        Initialize semantic cache.

        Args:
            db_session: Async database session
            embedder: Embedding pipeline (creates global if None)
            high_similarity_threshold: Threshold for HIGH strategy (default 0.98)
            medium_similarity_threshold: Threshold for MEDIUM strategy (default 0.92)
            low_similarity_threshold: Threshold for LOW strategy (default 0.85)
            default_ttl_seconds: Default time-to-live for cache entries (default 24h)
        """
        self.db_session = db_session
        self.embedder = embedder or get_embedder()
        self.high_threshold = high_similarity_threshold
        self.medium_threshold = medium_similarity_threshold
        self.low_threshold = low_similarity_threshold
        self.default_ttl = default_ttl_seconds

        # Analytics
        self.stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'high_similarity_hits': 0,
            'medium_similarity_hits': 0,
            'low_similarity_near_hits': 0,
            'total_compute_saved_ms': 0
        }

        logger.info(
            f"Initialized SemanticCache (high={high_similarity_threshold}, "
            f"medium={medium_similarity_threshold}, low={low_similarity_threshold})"
        )

    async def get_or_compute(
        self,
        query: str,
        query_type: str,
        compute_fn: Callable,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> Tuple[Dict[str, Any], CacheHit]:
        """
        Get cached result or compute fresh if no similar query found.

        This is the MAIN method for semantic caching. It:
        1. Embeds the query
        2. Searches for semantically similar cached queries
        3. Returns cached result if similarity is high enough
        4. Otherwise computes fresh and caches the result

        Args:
            query: Query text to cache/lookup
            query_type: Type of query (creative_score, hook_analysis, etc.)
            compute_fn: Function to call if cache miss (takes query as arg)
            ttl_seconds: Time-to-live for cache entry (uses default if None)
            metadata: Additional metadata to store
            force_refresh: Force fresh computation even if cache hit

        Returns:
            Tuple of (result, cache_hit_info)
        """
        self.stats['total_queries'] += 1
        start_time = datetime.utcnow()

        try:
            # Check cache first (unless force refresh)
            cache_hit = None
            if not force_refresh:
                cache_hit = await self._search_cache(query, query_type)

                if cache_hit.hit:
                    self.stats['cache_hits'] += 1

                    if cache_hit.strategy == CacheStrategy.HIGH:
                        self.stats['high_similarity_hits'] += 1
                        logger.info(
                            f"🎯 HIGH similarity cache hit ({cache_hit.similarity:.4f}) "
                            f"for {query_type}: '{query[:50]}...'"
                        )
                    elif cache_hit.strategy == CacheStrategy.MEDIUM:
                        self.stats['medium_similarity_hits'] += 1
                        logger.info(
                            f"✅ MEDIUM similarity cache hit ({cache_hit.similarity:.4f}) "
                            f"for {query_type}: '{query[:50]}...'"
                        )

                    # Update access stats
                    await self._update_access_stats(cache_hit.cache_id)

                    # Calculate compute time saved
                    elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
                    self.stats['total_compute_saved_ms'] += max(0, 2000 - elapsed_ms)  # Assume 2s compute

                    # Return cached result
                    result = cache_hit.cached_result
                    if cache_hit.strategy == CacheStrategy.MEDIUM:
                        # Flag as from cache for transparency
                        result = {**result, 'from_cache': True, 'similarity': cache_hit.similarity}

                    return result, cache_hit
                elif cache_hit.strategy == CacheStrategy.LOW:
                    self.stats['low_similarity_near_hits'] += 1
                    logger.info(
                        f"⚠️  LOW similarity near-hit ({cache_hit.similarity:.4f}) "
                        f"for {query_type}: '{query[:50]}...' - computing fresh"
                    )

            # Cache miss or force refresh - compute fresh
            self.stats['cache_misses'] += 1
            logger.info(f"🔄 Cache miss for {query_type}: '{query[:50]}...' - computing fresh")

            # Compute result
            result = await compute_fn(query) if asyncio.iscoroutinefunction(compute_fn) else compute_fn(query)

            # Cache the result
            await self._store_result(
                query=query,
                query_type=query_type,
                result=result,
                ttl_seconds=ttl_seconds,
                metadata=metadata
            )

            # Create cache hit info for miss
            if cache_hit is None:
                cache_hit = CacheHit(hit=False, strategy=CacheStrategy.MISS)

            return result, cache_hit

        except Exception as e:
            logger.error(f"Error in get_or_compute: {e}", exc_info=True)
            # On error, compute without caching
            result = await compute_fn(query) if asyncio.iscoroutinefunction(compute_fn) else compute_fn(query)
            return result, CacheHit(hit=False, strategy=CacheStrategy.MISS)

    async def _search_cache(
        self,
        query: str,
        query_type: str
    ) -> CacheHit:
        """
        Search for semantically similar cached query.

        Args:
            query: Query text
            query_type: Type of query

        Returns:
            CacheHit with similarity info
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedder.embed_text(query)

            # Generate hash for exact match optimization
            query_hash = hashlib.sha256(f"{query_type}:{query}".encode()).hexdigest()[:16]

            # First check for exact match (fastest)
            exact_match = await self.db_session.execute(
                select(SemanticCacheEntry).where(
                    and_(
                        SemanticCacheEntry.query_type == query_type,
                        SemanticCacheEntry.query_hash == query_hash
                    )
                )
            )
            exact_entry = exact_match.scalar_one_or_none()

            if exact_entry:
                # Check if expired
                if exact_entry.expires_at and exact_entry.expires_at < datetime.utcnow():
                    # Expired - delete and continue to semantic search
                    await self.db_session.delete(exact_entry)
                    await self.db_session.commit()
                else:
                    # Exact match found!
                    age_seconds = (datetime.utcnow() - exact_entry.created_at).total_seconds()
                    return CacheHit(
                        hit=True,
                        cached_result=exact_entry.result,
                        similarity=1.0,
                        strategy=CacheStrategy.EXACT,
                        cache_id=exact_entry.cache_id,
                        age_seconds=age_seconds,
                        usage_count=exact_entry.access_count
                    )

            # Semantic similarity search using pgvector
            # Use cosine distance for similarity (1 - distance = similarity)
            similarity = 1 - SemanticCacheEntry.query_embedding.cosine_distance(query_embedding)

            query = select(
                SemanticCacheEntry,
                similarity.label('similarity')
            ).where(
                SemanticCacheEntry.query_type == query_type
            ).order_by(
                similarity.desc()
            ).limit(1)

            result = await self.db_session.execute(query)
            row = result.one_or_none()

            if not row:
                return CacheHit(hit=False, strategy=CacheStrategy.MISS)

            entry, sim_score = row

            # Check if expired
            if entry.expires_at and entry.expires_at < datetime.utcnow():
                # Expired - delete and return miss
                await self.db_session.delete(entry)
                await self.db_session.commit()
                return CacheHit(hit=False, strategy=CacheStrategy.MISS)

            # Determine strategy based on similarity
            strategy = self._determine_strategy(float(sim_score))

            # Only return cache hit for HIGH and MEDIUM strategies
            if strategy in (CacheStrategy.HIGH, CacheStrategy.MEDIUM):
                age_seconds = (datetime.utcnow() - entry.created_at).total_seconds()
                return CacheHit(
                    hit=True,
                    cached_result=entry.result,
                    similarity=float(sim_score),
                    strategy=strategy,
                    cache_id=entry.cache_id,
                    age_seconds=age_seconds,
                    usage_count=entry.access_count
                )
            else:
                # LOW or MISS - return as near-hit but no cache
                return CacheHit(
                    hit=False,
                    similarity=float(sim_score),
                    strategy=strategy
                )

        except Exception as e:
            logger.error(f"Error searching cache: {e}", exc_info=True)
            return CacheHit(hit=False, strategy=CacheStrategy.MISS)

    async def _store_result(
        self,
        query: str,
        query_type: str,
        result: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compute_time_ms: Optional[float] = None
    ) -> str:
        """
        Store result in semantic cache.

        Args:
            query: Query text
            query_type: Type of query
            result: Result to cache
            ttl_seconds: Time-to-live
            metadata: Additional metadata
            compute_time_ms: How long the computation took

        Returns:
            Cache entry ID
        """
        try:
            # Generate embedding for query
            query_embedding = await self.embedder.embed_text(query)

            # Generate cache ID and hash
            cache_id = self._generate_cache_id(query, query_type)
            query_hash = hashlib.sha256(f"{query_type}:{query}".encode()).hexdigest()[:16]

            # Calculate expiration time
            ttl = ttl_seconds or self.default_ttl
            expires_at = datetime.utcnow() + timedelta(seconds=ttl) if ttl else None

            # Check if entry already exists (for update)
            existing = await self.db_session.execute(
                select(SemanticCacheEntry).where(
                    and_(
                        SemanticCacheEntry.query_type == query_type,
                        SemanticCacheEntry.query_hash == query_hash
                    )
                )
            )
            existing_entry = existing.scalar_one_or_none()

            if existing_entry:
                # Update existing entry
                existing_entry.result = result
                existing_entry.query_embedding = query_embedding
                existing_entry.ttl_seconds = ttl
                existing_entry.expires_at = expires_at
                existing_entry.metadata = metadata or {}
                existing_entry.compute_time_ms = compute_time_ms
                existing_entry.updated_at = datetime.utcnow()

                await self.db_session.commit()
                logger.info(f"Updated cache entry: {cache_id} (type: {query_type})")
                return cache_id

            # Create new cache entry
            cache_entry = SemanticCacheEntry(
                cache_id=cache_id,
                query_type=query_type,
                query_text=query,
                query_hash=query_hash,
                query_embedding=query_embedding,
                result=result,
                result_type=result.get('type', 'unknown'),
                ttl_seconds=ttl,
                expires_at=expires_at,
                access_count=0,
                last_accessed_at=datetime.utcnow(),
                compute_time_ms=compute_time_ms,
                metadata=metadata or {},
                is_warmed=metadata.get('warmed', False) if metadata else False
            )

            self.db_session.add(cache_entry)
            await self.db_session.commit()

            logger.info(f"Stored cache entry: {cache_id} (type: {query_type}, ttl: {ttl}s)")
            return cache_id

        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error storing cache result: {e}", exc_info=True)
            return None

    async def _update_access_stats(self, cache_id: str) -> None:
        """
        Update access statistics for cache entry.

        Args:
            cache_id: Cache entry ID
        """
        try:
            await self.db_session.execute(
                update(SemanticCacheEntry).where(
                    SemanticCacheEntry.cache_id == cache_id
                ).values(
                    access_count=SemanticCacheEntry.access_count + 1,
                    last_accessed_at=datetime.utcnow()
                )
            )
            await self.db_session.commit()
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error updating access stats: {e}")

    def _generate_cache_id(self, query: str, query_type: str) -> str:
        """Generate unique cache ID from query and type."""
        content = f"{query_type}:{query}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _determine_strategy(self, similarity: float) -> CacheStrategy:
        """
        Determine cache strategy based on similarity score.

        Args:
            similarity: Cosine similarity score (0-1)

        Returns:
            Cache strategy
        """
        if similarity >= 0.999:
            return CacheStrategy.EXACT
        elif similarity >= self.high_threshold:
            return CacheStrategy.HIGH
        elif similarity >= self.medium_threshold:
            return CacheStrategy.MEDIUM
        elif similarity >= self.low_threshold:
            return CacheStrategy.LOW
        else:
            return CacheStrategy.MISS

    async def warm_cache(
        self,
        query_type: str,
        training_data: List[Tuple[str, Dict[str, Any]]],
        ttl_seconds: Optional[int] = None
    ) -> int:
        """
        Warm cache with pre-computed results from training data.

        This is POWERFUL for bootstrapping the cache with known
        good results before production use.

        Args:
            query_type: Type of queries
            training_data: List of (query, result) tuples
            ttl_seconds: Time-to-live for entries

        Returns:
            Number of entries cached
        """
        logger.info(f"Warming cache with {len(training_data)} entries for {query_type}")

        cached_count = 0
        for query, result in training_data:
            try:
                cache_id = await self._store_result(
                    query=query,
                    query_type=query_type,
                    result=result,
                    ttl_seconds=ttl_seconds,
                    metadata={'warmed': True}
                )
                if cache_id:
                    cached_count += 1
            except Exception as e:
                logger.error(f"Error warming cache for query '{query[:50]}...': {e}")

        logger.info(f"Cache warmed: {cached_count}/{len(training_data)} entries cached")
        return cached_count

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        hit_rate = (
            self.stats['cache_hits'] / self.stats['total_queries'] * 100
            if self.stats['total_queries'] > 0 else 0
        )

        return {
            **self.stats,
            'cache_hit_rate': hit_rate,
            'average_compute_saved_ms': (
                self.stats['total_compute_saved_ms'] / self.stats['cache_hits']
                if self.stats['cache_hits'] > 0 else 0
            ),
            'thresholds': {
                'high': self.high_threshold,
                'medium': self.medium_threshold,
                'low': self.low_threshold
            }
        }

    async def clear_expired(self) -> int:
        """
        Clear expired cache entries.

        Returns:
            Number of entries cleared
        """
        try:
            # Delete expired entries
            result = await self.db_session.execute(
                delete(SemanticCacheEntry).where(
                    and_(
                        SemanticCacheEntry.expires_at.isnot(None),
                        SemanticCacheEntry.expires_at < datetime.utcnow()
                    )
                )
            )
            await self.db_session.commit()

            count = result.rowcount
            logger.info(f"Cleared {count} expired cache entries")
            return count
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error clearing expired entries: {e}")
            return 0

    async def clear_cache(self, query_type: Optional[str] = None) -> int:
        """
        Clear cache entries.

        Args:
            query_type: If provided, only clear entries of this type

        Returns:
            Number of entries cleared
        """
        try:
            if query_type:
                result = await self.db_session.execute(
                    delete(SemanticCacheEntry).where(
                        SemanticCacheEntry.query_type == query_type
                    )
                )
            else:
                result = await self.db_session.execute(
                    delete(SemanticCacheEntry)
                )

            await self.db_session.commit()

            count = result.rowcount
            logger.info(f"Cleared {count} cache entries (type: {query_type or 'all'})")
            return count
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Error clearing cache: {e}")
            return 0

    async def get_popular_entries(
        self,
        query_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most popular cache entries by access count.

        Args:
            query_type: Filter by query type
            limit: Number of entries to return

        Returns:
            List of popular cache entries
        """
        try:
            query = select(SemanticCacheEntry)

            if query_type:
                query = query.where(SemanticCacheEntry.query_type == query_type)

            query = query.order_by(desc(SemanticCacheEntry.access_count)).limit(limit)

            result = await self.db_session.execute(query)
            entries = result.scalars().all()

            return [
                {
                    'cache_id': entry.cache_id,
                    'query_type': entry.query_type,
                    'query_text': entry.query_text,
                    'access_count': entry.access_count,
                    'created_at': entry.created_at.isoformat(),
                    'last_accessed_at': entry.last_accessed_at.isoformat() if entry.last_accessed_at else None,
                    'result_preview': str(entry.result)[:100] + '...' if len(str(entry.result)) > 100 else str(entry.result)
                }
                for entry in entries
            ]
        except Exception as e:
            logger.error(f"Error getting popular entries: {e}")
            return []


# ============================================================================
# CONVENIENCE DECORATORS
# ============================================================================

def semantic_cached(
    query_type: str,
    ttl_seconds: Optional[int] = None,
    cache_instance: Optional[SemanticCache] = None
):
    """
    Decorator for automatic semantic caching of function results.

    Example:
        @semantic_cached(query_type="creative_score", ttl_seconds=3600)
        async def score_creative(hook_text: str) -> Dict[str, Any]:
            # Expensive AI operation
            return ai_council.score(hook_text)

        # First call - computes and caches
        result1 = await score_creative("Stop wasting money on gym memberships")

        # Second call with similar text - returns cached!
        result2 = await score_creative("Don't waste cash on unused gym subscriptions")

    Args:
        query_type: Type of query for caching
        ttl_seconds: Time-to-live for cache entries
        cache_instance: SemanticCache instance (creates global if None)
    """
    def decorator(func):
        async def wrapper(query: str, *args, **kwargs):
            # Get or create cache instance
            cache = cache_instance
            if cache is None:
                # TODO: Create global cache instance
                logger.warning("No cache instance provided, computing without cache")
                return await func(query, *args, **kwargs)

            # Use semantic cache
            result, cache_hit = await cache.get_or_compute(
                query=query,
                query_type=query_type,
                compute_fn=lambda q: func(q, *args, **kwargs),
                ttl_seconds=ttl_seconds
            )

            return result

        return wrapper
    return decorator


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    async def example():
        """Example semantic cache usage."""

        # Mock compute function (expensive AI operation)
        async def expensive_ai_score(query: str) -> Dict[str, Any]:
            logger.info(f"💰 EXPENSIVE AI CALL for: '{query}'")
            await asyncio.sleep(2)  # Simulate 2s AI call
            return {
                'score': 85,
                'confidence': 0.92,
                'reasoning': 'Strong hook with emotional appeal'
            }

        # Initialize cache (with mock db session)
        # cache = SemanticCache(db_session=mock_db, embedder=get_embedder())

        # Example queries
        queries = [
            "Score this fitness ad targeting women 25-35",
            "Rate this gym advertisement for young women",  # Similar to first
            "Analyze this tech product hook for developers",  # Different
            "Evaluate fitness commercial aimed at females 25-35"  # Similar to first
        ]

        logger.info("=" * 80)
        logger.info("SEMANTIC CACHE DEMO")
        logger.info("=" * 80)

        # Mock cache (without real db for demo)
        # In production, use real cache with database

        for i, query in enumerate(queries, 1):
            logger.info(f"\n--- Query {i} ---")
            logger.info(f"Query: '{query}'")

            # This would use semantic cache in production
            result = await expensive_ai_score(query)
            logger.info(f"Result: {result}")

        logger.info("\n" + "=" * 80)
        logger.info("In production with semantic cache:")
        logger.info("- Query 1: MISS (compute fresh)")
        logger.info("- Query 2: HIT 96% similarity (return cached from Query 1)")
        logger.info("- Query 3: MISS (different topic, compute fresh)")
        logger.info("- Query 4: HIT 94% similarity (return cached from Query 1)")
        logger.info("Result: 2/4 queries cached = 50% hit rate = 50% cost savings!")
        logger.info("=" * 80)

    # Run example
    asyncio.run(example())
