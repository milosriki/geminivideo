"""
Auto-Promotion API Endpoints
Agent 44 - FastAPI endpoints for automatic A/B test winner promotion

These endpoints should be integrated into main.py
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime

from src.auto_promoter import auto_promoter, PromotionStatus
from src.auto_promotion_scheduler import get_scheduler

logger = logging.getLogger(__name__)


class AutoPromotionCheckRequest(BaseModel):
    """Request model for auto-promotion check"""
    experiment_id: str
    force_promotion: bool = False


# ====================
# ENDPOINT FUNCTIONS
# ====================

async def check_experiment_for_promotion(request: AutoPromotionCheckRequest):
    """
    Check if an A/B test experiment is ready for auto-promotion.

    Agent 44 - Auto-Promotion System

    Args:
        experiment_id: A/B test experiment ID
        force_promotion: Force promotion even if below confidence threshold

    Returns:
        Promotion result with status and details
    """
    try:
        if not auto_promoter:
            raise HTTPException(status_code=503, detail="Auto-promoter not initialized")

        result = await auto_promoter.check_and_promote(
            experiment_id=request.experiment_id,
            force_promotion=request.force_promotion
        )

        return result.to_dict()

    except Exception as e:
        logger.error(f"Error checking experiment for promotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def check_all_experiments_for_promotion():
    """
    Check all active A/B test experiments for auto-promotion.

    Agent 44 - Auto-Promotion System

    This endpoint checks all active experiments and promotes winners
    when statistically significant. Normally called by scheduler.

    Returns:
        List of promotion results
    """
    try:
        if not auto_promoter:
            raise HTTPException(status_code=503, detail="Auto-promoter not initialized")

        results = await auto_promoter.check_all_active_experiments()

        # Convert results to dicts
        results_dict = [r.to_dict() for r in results]

        # Count by status
        promoted_count = sum(1 for r in results if r.status == PromotionStatus.PROMOTED)
        continue_count = sum(1 for r in results if r.status == PromotionStatus.CONTINUE_TESTING)

        return {
            "total_checked": len(results),
            "promoted": promoted_count,
            "continue_testing": continue_count,
            "results": results_dict,
            "checked_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking all experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_promotion_history(days_back: int = 30, limit: int = 100):
    """
    Get history of auto-promoted experiments.

    Agent 44 - Auto-Promotion System

    Args:
        days_back: Number of days to look back (default 30)
        limit: Maximum number of results (default 100)

    Returns:
        List of promoted experiments with metrics
    """
    try:
        if not auto_promoter:
            raise HTTPException(status_code=503, detail="Auto-promoter not initialized")

        history = await auto_promoter.get_promotion_history(
            days_back=days_back,
            limit=limit
        )

        return {
            "history": history,
            "count": len(history),
            "days_back": days_back
        }

    except Exception as e:
        logger.error(f"Error getting promotion history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_compound_improvement_report():
    """
    Get cumulative improvement report from auto-promotions.

    Agent 44 - Auto-Promotion System

    Shows compound learning effect - how each test makes the next one better.
    This is the 10x leverage of auto-promotion!

    Returns:
        Compound improvement metrics and trends
    """
    try:
        if not auto_promoter:
            raise HTTPException(status_code=503, detail="Auto-promoter not initialized")

        report = await auto_promoter.get_cumulative_improvement_report()

        return report

    except Exception as e:
        logger.error(f"Error generating compound report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_scheduler_status():
    """
    Get auto-promotion scheduler status.

    Agent 44 - Auto-Promotion System

    Returns:
        Scheduler status and next run times
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            return {
                "status": "not_initialized",
                "message": "Auto-promotion scheduler not initialized"
            }

        return scheduler.get_status()

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def trigger_scheduler_now():
    """
    Manually trigger auto-promotion check now.

    Agent 44 - Auto-Promotion System

    Useful for testing or forcing an immediate check instead of
    waiting for the next scheduled run.

    Returns:
        Trigger confirmation
    """
    try:
        scheduler = get_scheduler()

        if not scheduler:
            raise HTTPException(
                status_code=503,
                detail="Auto-promotion scheduler not initialized"
            )

        result = await scheduler.force_check_now()

        return result

    except Exception as e:
        logger.error(f"Error triggering scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_auto_promotion_dashboard():
    """
    Get comprehensive auto-promotion dashboard data.

    Agent 44 - Auto-Promotion System

    Returns:
        Dashboard data with promotions, insights, and trends
    """
    try:
        if not auto_promoter:
            raise HTTPException(status_code=503, detail="Auto-promoter not initialized")

        # Get recent promotions
        history = await auto_promoter.get_promotion_history(days_back=7, limit=10)

        # Get compound improvement
        compound_report = await auto_promoter.get_cumulative_improvement_report()

        # Get scheduler status
        scheduler = get_scheduler()
        scheduler_status = scheduler.get_status() if scheduler else {"status": "not_running"}

        # Calculate summary stats
        recent_promotions = len(history)
        avg_confidence = sum(h['confidence'] for h in history) / recent_promotions if recent_promotions > 0 else 0

        improvements = []
        for h in history:
            winner_ctr = h['winner_metrics'].get('ctr', 0)
            loser_ctr = h['loser_metrics'].get('ctr', 0)
            if loser_ctr > 0:
                improvement = (winner_ctr - loser_ctr) / loser_ctr * 100
                improvements.append(improvement)

        avg_improvement = sum(improvements) / len(improvements) if improvements else 0

        return {
            "summary": {
                "recent_promotions_7d": recent_promotions,
                "avg_confidence": avg_confidence,
                "avg_improvement_pct": avg_improvement,
                "total_experiments": compound_report.get('total_experiments', 0),
                "compound_improvement_pct": compound_report.get('compound_improvement_pct', 0)
            },
            "recent_winners": history,
            "compound_learning": compound_report,
            "scheduler": scheduler_status,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error generating dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ====================
# ROUTE REGISTRATION
# ====================

def register_auto_promotion_routes(app):
    """
    Register auto-promotion routes with FastAPI app.

    Usage in main.py:
        from src.auto_promotion_endpoints import register_auto_promotion_routes
        register_auto_promotion_routes(app)
    """

    @app.post("/api/ab/auto-promote/check", tags=["Auto-Promotion"])
    async def _check_experiment(request: AutoPromotionCheckRequest):
        return await check_experiment_for_promotion(request)

    @app.post("/api/ab/auto-promote/check-all", tags=["Auto-Promotion"])
    async def _check_all_experiments():
        return await check_all_experiments_for_promotion()

    @app.get("/api/ab/auto-promote/history", tags=["Auto-Promotion"])
    async def _get_history(days_back: int = 30, limit: int = 100):
        return await get_promotion_history(days_back, limit)

    @app.get("/api/ab/auto-promote/compound-report", tags=["Auto-Promotion"])
    async def _get_compound_report():
        return await get_compound_improvement_report()

    @app.get("/api/ab/auto-promote/scheduler/status", tags=["Auto-Promotion"])
    async def _get_scheduler_status():
        return await get_scheduler_status()

    @app.post("/api/ab/auto-promote/scheduler/trigger", tags=["Auto-Promotion"])
    async def _trigger_scheduler():
        return await trigger_scheduler_now()

    @app.get("/api/ab/auto-promote/dashboard", tags=["Auto-Promotion"])
    async def _get_dashboard():
        return await get_auto_promotion_dashboard()

    logger.info("✓ Auto-promotion routes registered")
