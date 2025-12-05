"""
REST API for Smart Model Routing

Provides HTTP endpoints for:
- Routing tasks to optimal models
- Viewing analytics and dashboard
- Managing A/B tests
- Exporting reports

Usage:
    from titan_core.routing.api import router as routing_api
    app.include_router(routing_api, prefix="/api/v1/routing")
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import logging

from .model_router import router
from .analytics import analytics
from .ab_testing import ab_test_manager
from .dashboard import router_dashboard
from .integration import smart_council, smart_executor

logger = logging.getLogger(__name__)

# Create API router
routing_router = APIRouter(tags=["routing"])


# ============================================================================
# Request/Response Models
# ============================================================================

class TaskRequest(BaseModel):
    """Request to route a task"""
    text: str = Field(..., description="Input text to process")
    task_type: str = Field("general", description="Type of task (score, creative, analysis, etc.)")
    prompt_template: Optional[str] = Field(None, description="Optional prompt template")
    complexity_hint: Optional[str] = Field(None, description="Optional complexity hint (simple/medium/complex)")
    user_id: Optional[str] = Field(None, description="Optional user ID for A/B testing")
    response_format: Optional[Dict] = Field(None, description="Optional JSON schema for structured output")


class ScriptEvaluationRequest(BaseModel):
    """Request to evaluate a script"""
    script: str = Field(..., description="Script content to evaluate")
    niche: str = Field("fitness", description="Business niche (fitness, e-commerce, etc.)")
    user_id: Optional[str] = Field(None, description="Optional user ID for A/B testing")


class TaskResponse(BaseModel):
    """Response from routing a task"""
    result: Any = Field(..., description="Task result")
    model_used: str = Field(..., description="Model that processed the task")
    complexity: str = Field(..., description="Detected task complexity")
    cost: float = Field(..., description="Cost in USD")
    confidence: float = Field(..., description="Confidence score (0-1)")
    escalated: bool = Field(..., description="Whether task was escalated")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: str = Field(..., description="ISO timestamp")


# ============================================================================
# Routing Endpoints
# ============================================================================

@routing_router.post("/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Execute a task with smart model routing

    The router will:
    1. Classify task complexity
    2. Select optimal model
    3. Execute task
    4. Escalate to better model if confidence is low
    5. Track analytics

    Returns detailed result with routing metadata.
    """
    try:
        # Build task
        task = {
            "text": request.text,
            "type": request.task_type
        }

        if request.complexity_hint:
            task["complexity_override"] = request.complexity_hint

        # Execute with smart routing
        result = await smart_executor.execute(
            text=request.text,
            task_type=request.task_type,
            prompt_template=request.prompt_template,
            response_format=request.response_format
        )

        return TaskResponse(**result)

    except Exception as e:
        logger.error(f"Task execution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.post("/evaluate-script")
async def evaluate_script(request: ScriptEvaluationRequest):
    """
    Evaluate an ad script with smart routing

    Uses the Council of Titans evaluation with intelligent
    model selection for optimal cost/quality.

    Returns:
    - verdict (APPROVED/NEEDS_REVISION)
    - final_score (0-100)
    - feedback
    - routing metadata (model used, cost, etc.)
    """
    try:
        result = await smart_council.evaluate_script(
            script_content=request.script,
            niche=request.niche,
            user_id=request.user_id
        )

        return result

    except Exception as e:
        logger.error(f"Script evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Analytics & Dashboard Endpoints
# ============================================================================

@routing_router.get("/dashboard")
async def get_dashboard():
    """
    Get comprehensive routing dashboard

    Returns:
    - Overview metrics (total requests, costs, savings)
    - Cost analysis by model and complexity
    - Model performance metrics
    - Quality metrics and confidence scores
    - A/B test results
    - Insights and alerts
    """
    try:
        dashboard = router_dashboard.get_dashboard()
        return dashboard

    except Exception as e:
        logger.error(f"Dashboard fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.get("/analytics/summary")
async def get_analytics_summary():
    """
    Get analytics summary

    Returns high-level metrics:
    - Total requests and costs
    - Cost savings vs. baseline
    - Model distribution
    - Complexity distribution
    - Actionable insights
    """
    try:
        summary = analytics.get_summary()
        return summary

    except Exception as e:
        logger.error(f"Analytics fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.get("/analytics/cost-breakdown")
async def get_cost_breakdown():
    """
    Get detailed cost breakdown

    Returns cost analysis by:
    - Model
    - Complexity level
    """
    try:
        breakdown = analytics.get_cost_breakdown()
        return breakdown

    except Exception as e:
        logger.error(f"Cost breakdown fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.get("/analytics/time-series")
async def get_time_series(
    hours: int = Query(24, description="Number of hours to look back", ge=1, le=168)
):
    """
    Get time series data for the last N hours

    Returns list of data points with:
    - timestamp
    - cost
    - confidence
    - model
    """
    try:
        time_series = analytics.get_time_series(hours=hours)
        return {"time_series": time_series}

    except Exception as e:
        logger.error(f"Time series fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Statistics Endpoints
# ============================================================================

@routing_router.get("/stats")
async def get_router_stats():
    """
    Get current router statistics

    Returns:
    - Total requests
    - Requests by complexity
    - Requests by model
    - Total cost
    - Average confidence
    - Escalation rate
    - Cost savings percentage
    """
    try:
        stats = router.get_stats()
        return stats

    except Exception as e:
        logger.error(f"Stats fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.get("/stats/cost-summary")
async def get_cost_summary():
    """
    Get quick cost summary

    Returns:
    - Total cost
    - Baseline cost (if always using premium)
    - Savings amount and percentage
    """
    try:
        summary = router_dashboard.get_cost_summary()
        return summary

    except Exception as e:
        logger.error(f"Cost summary fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.get("/stats/performance-summary")
async def get_performance_summary():
    """
    Get quick performance summary

    Returns:
    - Total requests
    - Average confidence
    - Escalation rate
    - System status
    """
    try:
        summary = router_dashboard.get_performance_summary()
        return summary

    except Exception as e:
        logger.error(f"Performance summary fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# A/B Testing Endpoints
# ============================================================================

@routing_router.get("/ab-test/results")
async def get_ab_test_results():
    """
    Get A/B test results

    Returns:
    - Test status (enabled/disabled)
    - Traffic split configuration
    - Results by strategy
    - Winner determination
    - Recommendations
    """
    try:
        results = ab_test_manager.get_results()
        return results

    except Exception as e:
        logger.error(f"A/B test results fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.get("/ab-test/learned-preferences")
async def get_learned_preferences():
    """
    Get learned task type preferences

    For adaptive strategy, shows which models perform
    best for different task types.
    """
    try:
        preferences = ab_test_manager.get_learned_preferences()
        return {"preferences": preferences}

    except Exception as e:
        logger.error(f"Learned preferences fetch failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Export Endpoints
# ============================================================================

@routing_router.post("/export/analytics")
async def export_analytics(
    output_path: str = Query("/tmp/routing_analytics_export.json", description="Output file path")
):
    """
    Export complete analytics report to JSON file

    Includes:
    - Summary metrics
    - Cost breakdown
    - Time series data
    - Raw metrics
    """
    try:
        analytics.export_report(output_path)
        return {
            "status": "success",
            "message": f"Analytics exported to {output_path}"
        }

    except Exception as e:
        logger.error(f"Analytics export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.post("/export/dashboard")
async def export_dashboard(
    output_path: str = Query("/tmp/routing_dashboard_export.json", description="Output file path")
):
    """
    Export complete dashboard data to JSON file
    """
    try:
        router_dashboard.export_dashboard(output_path)
        return {
            "status": "success",
            "message": f"Dashboard exported to {output_path}"
        }

    except Exception as e:
        logger.error(f"Dashboard export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Management Endpoints
# ============================================================================

@routing_router.post("/reset")
async def reset_all_stats():
    """
    Reset all statistics and analytics

    WARNING: This will clear all tracked data.
    Use only for testing.
    """
    try:
        router.reset_stats()
        analytics.reset()
        ab_test_manager.reset()

        return {
            "status": "success",
            "message": "All routing statistics reset"
        }

    except Exception as e:
        logger.error(f"Reset failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@routing_router.get("/health")
async def health_check():
    """
    Health check endpoint

    Returns system status and basic metrics
    """
    try:
        stats = router.get_stats()

        return {
            "status": "healthy",
            "router": {
                "available": True,
                "total_requests": stats["total_requests"],
                "avg_confidence": stats["avg_confidence"]
            },
            "analytics": {
                "available": True,
                "storage_path": analytics.storage_path
            },
            "ab_testing": {
                "enabled": ab_test_manager.enabled
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Export router
router = routing_router
