"""
Actuals Fetcher FastAPI Endpoints - Agent 8
Investment-grade API endpoints for Meta Ads actuals fetching

Import and register these endpoints in main.py:
    from src.actuals_endpoints import register_actuals_endpoints
    register_actuals_endpoints(app)
"""

import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.actuals_fetcher import actuals_fetcher
from src.actuals_scheduler import actuals_scheduler

logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class ActualsFetchRequest(BaseModel):
    """Request model for fetching actuals"""
    ad_id: str
    video_id: str
    days_back: int = 7


# ==================== Endpoint Registration ====================

def register_actuals_endpoints(app: FastAPI):
    """
    Register actuals fetcher endpoints with FastAPI app.
    Call this from main.py startup.
    """

    @app.post("/api/ml/actuals/fetch/{ad_id}")
    async def fetch_ad_actuals_endpoint(ad_id: str, video_id: str, days_back: int = 7):
        """
        Fetch actual performance data for a specific ad from Meta API (Agent 8)

        This endpoint fetches real CTR, ROAS, conversions, and spend data
        from Meta Ads API for €5M investment validation.
        """
        try:
            logger.info(f"Manual actuals fetch requested for ad {ad_id}")

            actuals = await actuals_fetcher.fetch_ad_actuals(
                ad_id=ad_id,
                video_id=video_id,
                days_back=days_back
            )

            if not actuals:
                raise HTTPException(
                    status_code=404,
                    detail=f"Could not fetch actuals for ad {ad_id}. Check Meta API credentials and ad ID."
                )

            # Save to database
            saved = actuals_fetcher.save_actuals_to_db(actuals)

            return {
                "status": "success",
                "ad_id": actuals.ad_id,
                "video_id": actuals.video_id,
                "actuals": {
                    "impressions": actuals.impressions,
                    "clicks": actuals.clicks,
                    "ctr": actuals.actual_ctr,
                    "spend": actuals.spend,
                    "conversions": actuals.conversions,
                    "roas": actuals.actual_roas,
                    "revenue": actuals.revenue,
                    "reach": actuals.reach,
                    "cpm": actuals.cpm,
                    "cpc": actuals.cpc
                },
                "saved_to_db": saved,
                "fetched_at": actuals.fetched_at.isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching actuals: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/ml/actuals/sync")
    async def sync_all_actuals_endpoint(
        min_age_hours: int = 24,
        max_age_days: int = 30
    ):
        """
        Sync actuals for all pending predictions (Agent 8)

        This is the main endpoint that the hourly cron job calls.
        It fetches actual performance for all videos with Meta ads
        and updates the database.

        Args:
            min_age_hours: Only fetch ads older than this (default: 24h)
            max_age_days: Don't fetch ads older than this (default: 30 days)
        """
        try:
            logger.info("Manual sync requested for all pending actuals")

            summary = await actuals_fetcher.sync_actuals_for_pending_predictions(
                min_age_hours=min_age_hours,
                max_age_days=max_age_days
            )

            return {
                "status": "success",
                "summary": {
                    "total_ads": summary.total_ads,
                    "successful": summary.successful,
                    "failed": summary.failed,
                    "rate_limited": summary.rate_limited,
                    "no_data": summary.no_data,
                    "total_spend": summary.total_spend,
                    "total_conversions": summary.total_conversions,
                    "total_revenue": summary.total_revenue,
                    "duration_seconds": summary.duration_seconds,
                    "timestamp": summary.timestamp.isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Error syncing actuals: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/ml/actuals/scheduler-status")
    async def get_actuals_scheduler_status():
        """
        Get actuals scheduler status (Agent 8)

        Returns information about the automated hourly sync:
        - Is it running?
        - When was last run?
        - Statistics from last run
        """
        try:
            status = actuals_scheduler.get_status()
            return {
                "status": "healthy" if status['is_running'] else "stopped",
                "scheduler": status
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/ml/actuals/stats")
    async def get_actuals_fetcher_stats():
        """
        Get actuals fetcher statistics (Agent 8)

        Returns cumulative statistics:
        - Total fetches
        - Success rate
        - Total spend tracked
        - Total conversions tracked
        """
        try:
            stats = actuals_fetcher.get_stats()
            return {
                "status": "success",
                "stats": stats
            }
        except Exception as e:
            logger.error(f"Error getting actuals stats: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    logger.info("✅ Actuals fetcher endpoints registered")


def start_actuals_scheduler():
    """
    Start the actuals scheduler.
    Call this from main.py startup event.
    """
    try:
        actuals_scheduler.start()
        logger.info("✅ Actuals scheduler started (runs hourly) - Investment Grade Data Validation")
        return True
    except Exception as e:
        logger.warning(f"Failed to start actuals scheduler: {e}")
        return False
