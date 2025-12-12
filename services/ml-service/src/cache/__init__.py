"""
Cache module for ML service with semantic caching support.

Provides:
- SemanticCacheManager: High-level cache manager with Redis backend
- get_cache_manager(): Get global cache manager instance
"""

from .semantic_cache_manager import SemanticCacheManager, get_cache_manager

__all__ = ['SemanticCacheManager', 'get_cache_manager']
