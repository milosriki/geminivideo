"""
Celery Tasks for ML Precomputation

Agent 6: Precomputer Activator
Scheduled tasks for zero-latency predictions:
- precompute_daily_predictions: Runs at 2am daily
- warm_cache_for_campaigns: Runs before campaign launches
- analyze_query_patterns: Runs hourly
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


def get_or_create_event_loop():
    """
    Get or create event loop for async tasks.

    Celery workers may not have an event loop, so we create one if needed.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop is closed")
        return loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def run_async_task(coro):
    """
    Run async coroutine in Celery worker context.

    Args:
        coro: Async coroutine to run

    Returns:
        Coroutine result
    """
    loop = get_or_create_event_loop()

    if loop.is_running():
        # If loop is already running, use run_until_complete in a thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    else:
        return loop.run_until_complete(coro)


# Import celery app (will be imported from parent)
try:
    from ..celery_app import celery_app
except ImportError:
    # Fallback for testing
    from celery import Celery
    celery_app = Celery('ml-service-precompute')


@celery_app.task(name='precompute_daily_predictions', bind=True)
def precompute_daily_predictions(self, limit: int = 1000, force: bool = False) -> Dict[str, Any]:
    """
    Pre-calculate predictions for top 1000 ads by query frequency.

    Scheduled to run at 2am daily during off-peak hours.

    Args:
        limit: Maximum number of ads to precompute (default 1000)
        force: Force recompute even if cached

    Returns:
        Dictionary with job results
    """
    logger.info(f"🚀 Starting daily predictions precomputation (limit={limit})")

    try:
        # Import precomputer
        from .precomputer import get_ml_precomputer

        precomputer = get_ml_precomputer()

        # Run async precomputation
        async def _run():
            return await precomputer.precompute_daily_predictions(limit=limit, force=force)

        result = run_async_task(_run())

        # Convert dataclass to dict
        result_dict = {
            "job_id": result.job_id,
            "job_type": result.job_type,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "items_processed": result.items_processed,
            "items_cached": result.items_cached,
            "errors": result.errors,
            "avg_compute_time_ms": result.avg_compute_time_ms,
            "status": result.status,
            "error_message": result.error_message
        }

        logger.info(
            f"✅ Daily predictions completed: {result.items_processed} ads, "
            f"{result.errors} errors, status: {result.status}"
        )

        return result_dict

    except Exception as e:
        logger.error(f"❌ Daily predictions failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='warm_cache_for_campaigns', bind=True)
def warm_cache_for_campaigns(
    self,
    campaign_ids: Optional[List[str]] = None,
    hours_ahead: int = 24
) -> Dict[str, Any]:
    """
    Warm cache for upcoming campaign launches.

    Scheduled to run before campaign launch times.

    Args:
        campaign_ids: Optional list of specific campaign IDs to warm
        hours_ahead: Look ahead this many hours for scheduled launches

    Returns:
        Dictionary with job results
    """
    logger.info(f"🚀 Warming cache for campaigns (hours_ahead={hours_ahead})")

    try:
        # Import precomputer
        from .precomputer import get_ml_precomputer

        precomputer = get_ml_precomputer()

        # Run async precomputation
        async def _run():
            return await precomputer.warm_cache_for_campaigns(
                campaign_ids=campaign_ids,
                hours_ahead=hours_ahead
            )

        result = run_async_task(_run())

        # Convert dataclass to dict
        result_dict = {
            "job_id": result.job_id,
            "job_type": result.job_type,
            "started_at": result.started_at.isoformat(),
            "completed_at": result.completed_at.isoformat() if result.completed_at else None,
            "items_processed": result.items_processed,
            "items_cached": result.items_cached,
            "errors": result.errors,
            "status": result.status,
            "error_message": result.error_message
        }

        logger.info(
            f"✅ Campaign warming completed: {result.items_processed} campaigns, "
            f"{result.errors} errors, status: {result.status}"
        )

        return result_dict

    except Exception as e:
        logger.error(f"❌ Campaign warming failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='analyze_query_patterns', bind=True)
def analyze_query_patterns(self) -> Dict[str, Any]:
    """
    Analyze query patterns to optimize precomputation strategy.

    Scheduled to run hourly.

    Returns:
        Dictionary with analysis results
    """
    logger.info("🔍 Analyzing query patterns")

    try:
        # Import precomputer
        from .precomputer import get_ml_precomputer

        precomputer = get_ml_precomputer()

        # Run async analysis
        async def _run():
            return await precomputer.analyze_query_patterns()

        results = run_async_task(_run())

        logger.info(
            f"✅ Pattern analysis completed: "
            f"{results.get('statistics', {}).get('patterns_tracked', 0)} patterns tracked"
        )

        return results

    except Exception as e:
        logger.error(f"❌ Pattern analysis failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='precompute_top_campaigns', bind=True)
def precompute_top_campaigns(self, limit: int = 100) -> Dict[str, Any]:
    """
    Pre-calculate budget allocations for top campaigns by query frequency.

    This is an on-demand task that can be triggered manually or scheduled.

    Args:
        limit: Maximum number of campaigns to precompute

    Returns:
        Dictionary with job results
    """
    logger.info(f"🚀 Precomputing top {limit} campaigns")

    try:
        from .query_analyzer import get_query_analyzer

        query_analyzer = get_query_analyzer()

        # Get top campaigns
        top_campaigns = query_analyzer.get_top_campaigns_for_precomputation(limit=limit)

        if not top_campaigns:
            logger.info("No campaigns found for precomputation")
            return {
                "status": "completed",
                "campaigns_processed": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        # Warm cache for these campaigns
        campaign_ids = [c["campaign_id"] for c in top_campaigns]

        # Trigger campaign warming
        result = warm_cache_for_campaigns.delay(campaign_ids=campaign_ids)

        return {
            "status": "triggered",
            "campaigns_queued": len(campaign_ids),
            "celery_task_id": result.id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Campaign precomputation failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='precompute_scheduled_campaigns', bind=True)
def precompute_scheduled_campaigns(self, hours_ahead: int = 4) -> Dict[str, Any]:
    """
    Pre-warm cache for campaigns launching in the next N hours.

    This runs every 2 hours to ensure cache is warm before launches.

    Args:
        hours_ahead: Look ahead this many hours

    Returns:
        Dictionary with job results
    """
    logger.info(f"🚀 Pre-warming scheduled campaigns (next {hours_ahead} hours)")

    try:
        from .query_analyzer import get_query_analyzer

        query_analyzer = get_query_analyzer()

        # Get upcoming launches
        upcoming = query_analyzer.get_upcoming_launches(
            hours_ahead=hours_ahead,
            hours_warmup=0  # Start warming now
        )

        if not upcoming:
            logger.info("No upcoming campaign launches")
            return {
                "status": "completed",
                "campaigns_found": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        logger.info(f"Found {len(upcoming)} campaigns launching soon")

        # Warm each campaign
        campaign_ids = [launch.campaign_id for launch in upcoming]

        # Trigger warming
        result = warm_cache_for_campaigns.delay(campaign_ids=campaign_ids)

        return {
            "status": "triggered",
            "campaigns_found": len(upcoming),
            "campaign_ids": campaign_ids,
            "celery_task_id": result.id,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Scheduled campaign warming failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='cleanup_old_query_logs', bind=True)
def cleanup_old_query_logs(self, days_to_keep: int = 7) -> Dict[str, Any]:
    """
    Clean up old query logs to keep Redis storage manageable.

    Scheduled to run daily at 3am.

    Args:
        days_to_keep: Keep logs from last N days

    Returns:
        Dictionary with cleanup results
    """
    logger.info(f"🧹 Cleaning up query logs older than {days_to_keep} days")

    try:
        from .query_analyzer import get_query_analyzer
        from datetime import timedelta

        query_analyzer = get_query_analyzer()

        # Calculate cutoff timestamp
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        cutoff_score = cutoff.timestamp()

        # Remove old entries from query log
        removed = query_analyzer.redis.zremrangebyscore(
            query_analyzer.QUERY_LOG_KEY,
            "-inf",
            cutoff_score
        )

        logger.info(f"✅ Cleaned up {removed} old query log entries")

        return {
            "status": "completed",
            "entries_removed": removed,
            "cutoff_date": cutoff.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ Query log cleanup failed: {e}", exc_info=True)
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
