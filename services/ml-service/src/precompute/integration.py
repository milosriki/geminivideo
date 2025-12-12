"""
Integration Helpers for Query Logging

Agent 6: Precomputer Activator
Provides decorators and utilities to automatically log queries
for pattern analysis and precomputation optimization.
"""

import logging
import time
import functools
from typing import Callable, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def log_prediction_query(
    query_type: str,
    extract_metadata: Optional[Callable] = None
):
    """
    Decorator to automatically log prediction queries for pattern analysis.

    Usage:
        @log_prediction_query("ctr_prediction", extract_metadata=lambda kwargs: {...})
        def predict_ctr(ad_id: str, features: np.ndarray):
            ...

    Args:
        query_type: Type of query (ctr_prediction, budget_allocation, etc)
        extract_metadata: Optional function to extract metadata from kwargs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return _log_and_execute_sync(func, query_type, extract_metadata, *args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await _log_and_execute_async(func, query_type, extract_metadata, *args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _log_and_execute_sync(func, query_type, extract_metadata, *args, **kwargs):
    """Execute sync function and log query."""
    start_time = time.time()
    cache_hit = False

    try:
        # Check if result is from cache (if available in kwargs)
        cache_hit = kwargs.get('_from_cache', False)

        # Execute function
        result = func(*args, **kwargs)

        # Calculate compute time
        compute_time_ms = (time.time() - start_time) * 1000

        # Extract metadata
        metadata = {}
        if extract_metadata:
            try:
                metadata = extract_metadata(kwargs)
            except Exception as e:
                logger.debug(f"Failed to extract metadata: {e}")

        # Log query
        _log_query(
            query_type=query_type,
            metadata=metadata,
            compute_time_ms=compute_time_ms,
            cache_hit=cache_hit
        )

        return result

    except Exception as e:
        # Log failed query
        compute_time_ms = (time.time() - start_time) * 1000
        _log_query(
            query_type=query_type,
            metadata={},
            compute_time_ms=compute_time_ms,
            cache_hit=False
        )
        raise


async def _log_and_execute_async(func, query_type, extract_metadata, *args, **kwargs):
    """Execute async function and log query."""
    start_time = time.time()
    cache_hit = False

    try:
        # Check if result is from cache
        cache_hit = kwargs.get('_from_cache', False)

        # Execute function
        result = await func(*args, **kwargs)

        # Calculate compute time
        compute_time_ms = (time.time() - start_time) * 1000

        # Extract metadata
        metadata = {}
        if extract_metadata:
            try:
                metadata = extract_metadata(kwargs)
            except Exception as e:
                logger.debug(f"Failed to extract metadata: {e}")

        # Log query
        _log_query(
            query_type=query_type,
            metadata=metadata,
            compute_time_ms=compute_time_ms,
            cache_hit=cache_hit
        )

        return result

    except Exception as e:
        # Log failed query
        compute_time_ms = (time.time() - start_time) * 1000
        _log_query(
            query_type=query_type,
            metadata={},
            compute_time_ms=compute_time_ms,
            cache_hit=False
        )
        raise


def _log_query(
    query_type: str,
    metadata: dict,
    compute_time_ms: float,
    cache_hit: bool
):
    """
    Log query to query analyzer.

    Args:
        query_type: Type of query
        metadata: Query metadata (ad_id, campaign_id, etc)
        compute_time_ms: Compute time in milliseconds
        cache_hit: Whether this was a cache hit
    """
    try:
        from .query_analyzer import get_query_analyzer

        analyzer = get_query_analyzer()
        analyzer.log_query(
            query_type=query_type,
            ad_id=metadata.get('ad_id'),
            campaign_id=metadata.get('campaign_id'),
            tenant_id=metadata.get('tenant_id'),
            compute_time_ms=compute_time_ms,
            cache_hit=cache_hit
        )

    except Exception as e:
        # Don't fail the main request if logging fails
        logger.debug(f"Failed to log query: {e}")


# Import asyncio for async support
import asyncio


class QueryLogger:
    """
    Context manager for manual query logging.

    Usage:
        with QueryLogger("ctr_prediction", ad_id="123") as logger:
            prediction = model.predict(features)
            logger.mark_cached(True)  # If from cache
    """

    def __init__(
        self,
        query_type: str,
        ad_id: Optional[str] = None,
        campaign_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ):
        self.query_type = query_type
        self.ad_id = ad_id
        self.campaign_id = campaign_id
        self.tenant_id = tenant_id
        self.start_time = None
        self.cache_hit = False

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Calculate compute time
        compute_time_ms = (time.time() - self.start_time) * 1000

        # Log query
        _log_query(
            query_type=self.query_type,
            metadata={
                'ad_id': self.ad_id,
                'campaign_id': self.campaign_id,
                'tenant_id': self.tenant_id
            },
            compute_time_ms=compute_time_ms,
            cache_hit=self.cache_hit
        )

        return False  # Don't suppress exceptions

    def mark_cached(self, is_cached: bool = True):
        """Mark query as cached."""
        self.cache_hit = is_cached


def register_campaign_launch(
    campaign_id: str,
    tenant_id: str,
    launch_time: datetime,
    ad_count: int,
    estimated_queries: Optional[int] = None
):
    """
    Register a scheduled campaign launch for pre-warming.

    This should be called when a campaign is scheduled to launch.

    Args:
        campaign_id: Campaign ID
        tenant_id: Tenant ID
        launch_time: Scheduled launch time
        ad_count: Number of ads in campaign
        estimated_queries: Optional estimated query volume

    Example:
        # When user schedules a campaign
        register_campaign_launch(
            campaign_id="camp_123",
            tenant_id="tenant_456",
            launch_time=datetime(2025, 12, 15, 10, 0),
            ad_count=50
        )
    """
    try:
        from .query_analyzer import get_query_analyzer

        analyzer = get_query_analyzer()
        analyzer.register_campaign_launch(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            launch_time=launch_time,
            ad_count=ad_count,
            estimated_queries=estimated_queries or ad_count * 10
        )

        logger.info(f"Registered campaign launch: {campaign_id} at {launch_time}")

    except Exception as e:
        logger.error(f"Failed to register campaign launch: {e}")


def trigger_precomputation_for_campaign(campaign_id: str):
    """
    Manually trigger precomputation for a specific campaign.

    Useful when a campaign is about to launch and you want to ensure
    cache is warmed immediately.

    Args:
        campaign_id: Campaign ID to precompute

    Example:
        # Trigger warming before campaign launch
        trigger_precomputation_for_campaign("camp_123")
    """
    try:
        from .tasks import warm_cache_for_campaigns

        # Trigger async task
        result = warm_cache_for_campaigns.delay(campaign_ids=[campaign_id])

        logger.info(f"Triggered precomputation for campaign {campaign_id}: task {result.id}")

        return result.id

    except Exception as e:
        logger.error(f"Failed to trigger precomputation: {e}")
        return None
