"""
Auto-Scaler REST API Endpoints
Part of Agent 47 - Auto-Scaling System

Provides API endpoints for:
- Evaluating campaigns
- Approving/rejecting actions
- Viewing scaling history
- Managing rules
- Dashboard data
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from auto_scaler import (
    BudgetAutoScaler,
    ScalingRule,
    ScalingAction as ScalingActionDB,
    ScalingStatus,
    CampaignPerformanceSnapshot,
    OptimalHourProfile,
    Base,
    DATABASE_URL
)
from time_optimizer import TimeBasedOptimizer

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/auto-scaler", tags=["auto-scaler"])


# ==================== PYDANTIC MODELS ====================

class ScalingRuleCreate(BaseModel):
    """Create/update scaling rule"""
    account_id: str
    campaign_id: Optional[str] = None
    rule_name: str
    enabled: bool = True

    # Thresholds
    roas_scale_up_aggressive: float = 4.0
    roas_scale_up: float = 3.0
    roas_scale_down: float = 1.5
    roas_pause: float = 1.0
    ctr_threshold: float = 0.03
    min_impressions: int = 1000

    # Multipliers
    multiplier_aggressive_up: float = 1.5
    multiplier_up: float = 1.2
    multiplier_down: float = 0.7

    # Limits
    max_daily_budget: Optional[float] = None
    min_daily_budget: float = 10.00
    max_daily_spend_limit: Optional[float] = None

    # Approval
    require_approval_threshold: float = 500.00
    auto_approve_up_to: float = 100.00

    # Time optimization
    enable_time_optimization: bool = True
    peak_hours_multiplier: float = 1.3


class ScalingRuleResponse(BaseModel):
    """Scaling rule response"""
    id: int
    account_id: str
    campaign_id: Optional[str]
    rule_name: str
    enabled: bool
    roas_scale_up_aggressive: float
    roas_scale_up: float
    roas_scale_down: float
    roas_pause: float
    ctr_threshold: float
    created_at: datetime
    updated_at: datetime


class ApprovalRequest(BaseModel):
    """Approve/reject scaling action"""
    action_id: int
    approved_by: str
    approved: bool = True
    rejection_reason: Optional[str] = None


class EvaluationRequest(BaseModel):
    """Request campaign evaluation"""
    campaign_id: str
    account_id: Optional[str] = None


class BulkEvaluationRequest(BaseModel):
    """Bulk evaluate campaigns"""
    campaign_ids: List[str]
    account_id: Optional[str] = None


# ==================== DATABASE DEPENDENCY ====================

def get_db():
    """Get database session"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== ENDPOINTS ====================

@router.post("/evaluate")
async def evaluate_campaign(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate a single campaign and determine scaling action.

    Returns action details (executed if no approval needed).
    """
    try:
        scaler = BudgetAutoScaler(db_session=db)
        result = await scaler.evaluate_and_scale(
            campaign_id=request.campaign_id,
            account_id=request.account_id
        )

        return result

    except Exception as e:
        logger.error(f"Error evaluating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate-bulk")
async def evaluate_campaigns_bulk(
    request: BulkEvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate multiple campaigns in bulk.

    Returns summary of all actions.
    """
    try:
        scaler = BudgetAutoScaler(db_session=db)

        results = []
        for campaign_id in request.campaign_ids:
            try:
                result = await scaler.evaluate_and_scale(
                    campaign_id=campaign_id,
                    account_id=request.account_id
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating campaign {campaign_id}: {e}")
                results.append({
                    "campaign_id": campaign_id,
                    "success": False,
                    "error": str(e)
                })

        summary = {
            "total": len(results),
            "successful": sum(1 for r in results if r.get("success")),
            "failed": sum(1 for r in results if not r.get("success")),
            "executed": sum(1 for r in results if r.get("executed")),
            "pending_approval": sum(1 for r in results if r.get("requires_approval")),
            "results": results
        }

        return summary

    except Exception as e:
        logger.error(f"Error in bulk evaluation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approve")
async def approve_action(
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    """
    Approve or reject a pending scaling action.

    If approved, the action will be executed.
    """
    try:
        scaler = BudgetAutoScaler(db_session=db)

        if request.approved:
            # Approve
            success = scaler.approve_scaling_action(
                action_id=request.action_id,
                approved_by=request.approved_by
            )

            if not success:
                raise HTTPException(status_code=404, detail="Action not found")

            # Execute the approved action
            execution_result = await scaler.execute_scaling_action(request.action_id)

            return {
                "success": True,
                "action_id": request.action_id,
                "status": "approved_and_executed",
                "execution": execution_result
            }
        else:
            # Reject
            success = scaler.reject_scaling_action(
                action_id=request.action_id,
                reason=request.rejection_reason or "Rejected by user"
            )

            if not success:
                raise HTTPException(status_code=404, detail="Action not found")

            return {
                "success": True,
                "action_id": request.action_id,
                "status": "rejected"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/pending")
async def get_pending_actions(
    account_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get all pending scaling actions awaiting approval.
    """
    try:
        query = db.query(ScalingActionDB).filter(
            ScalingActionDB.status == ScalingStatus.PENDING.value
        )

        if account_id:
            query = query.filter(ScalingActionDB.account_id == account_id)

        actions = query.order_by(ScalingActionDB.created_at.desc()).limit(limit).all()

        return {
            "count": len(actions),
            "actions": [
                {
                    "id": a.id,
                    "campaign_id": a.campaign_id,
                    "action_type": a.action_type,
                    "budget_before": float(a.budget_before),
                    "budget_after": float(a.budget_after),
                    "budget_change_pct": a.budget_change_pct,
                    "roas": a.roas,
                    "ctr": a.ctr,
                    "reasoning": a.reasoning,
                    "created_at": a.created_at.isoformat()
                }
                for a in actions
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching pending actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actions/history")
async def get_action_history(
    campaign_id: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get scaling action history.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = db.query(ScalingActionDB).filter(
            ScalingActionDB.created_at >= cutoff_date
        )

        if campaign_id:
            query = query.filter(ScalingActionDB.campaign_id == campaign_id)

        if account_id:
            query = query.filter(ScalingActionDB.account_id == account_id)

        actions = query.order_by(ScalingActionDB.created_at.desc()).limit(limit).all()

        return {
            "count": len(actions),
            "period_days": days,
            "actions": [
                {
                    "id": a.id,
                    "campaign_id": a.campaign_id,
                    "action_type": a.action_type,
                    "status": a.status,
                    "budget_before": float(a.budget_before),
                    "budget_after": float(a.budget_after),
                    "budget_change_pct": a.budget_change_pct,
                    "roas": a.roas,
                    "ctr": a.ctr,
                    "reasoning": a.reasoning,
                    "created_at": a.created_at.isoformat(),
                    "executed_at": a.executed_at.isoformat() if a.executed_at else None,
                    "approved_by": a.approved_by
                }
                for a in actions
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching action history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard_data(
    account_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview data.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query actions
        query = db.query(ScalingActionDB).filter(
            ScalingActionDB.created_at >= cutoff_date
        )

        if account_id:
            query = query.filter(ScalingActionDB.account_id == account_id)

        actions = query.all()

        # Calculate statistics
        total_actions = len(actions)
        executed = sum(1 for a in actions if a.status == ScalingStatus.EXECUTED.value)
        pending = sum(1 for a in actions if a.status == ScalingStatus.PENDING.value)
        rejected = sum(1 for a in actions if a.status == ScalingStatus.REJECTED.value)

        # Action type breakdown
        action_types = {}
        for action in actions:
            action_types[action.action_type] = action_types.get(action.action_type, 0) + 1

        # Total budget changes
        total_budget_increase = sum(
            float(a.budget_after - a.budget_before)
            for a in actions
            if a.status == ScalingStatus.EXECUTED.value and a.budget_after > a.budget_before
        )

        total_budget_decrease = sum(
            float(a.budget_before - a.budget_after)
            for a in actions
            if a.status == ScalingStatus.EXECUTED.value and a.budget_after < a.budget_before
        )

        # Performance impact (estimated)
        total_revenue_tracked = sum(float(a.revenue_24h) for a in actions if a.status == ScalingStatus.EXECUTED.value)
        avg_roas = sum(a.roas for a in actions) / len(actions) if actions else 0

        # Recent actions
        recent_actions = sorted(actions, key=lambda a: a.created_at, reverse=True)[:10]

        return {
            "period_days": days,
            "summary": {
                "total_actions": total_actions,
                "executed": executed,
                "pending": pending,
                "rejected": rejected,
                "execution_rate": (executed / total_actions * 100) if total_actions > 0 else 0
            },
            "action_breakdown": action_types,
            "budget_impact": {
                "total_increase": round(total_budget_increase, 2),
                "total_decrease": round(total_budget_decrease, 2),
                "net_change": round(total_budget_increase - total_budget_decrease, 2)
            },
            "performance": {
                "avg_roas": round(avg_roas, 2),
                "total_revenue_tracked": round(total_revenue_tracked, 2)
            },
            "recent_actions": [
                {
                    "id": a.id,
                    "campaign_id": a.campaign_id,
                    "action_type": a.action_type,
                    "status": a.status,
                    "budget_change_pct": round(a.budget_change_pct, 1),
                    "roas": round(a.roas, 2),
                    "created_at": a.created_at.isoformat()
                }
                for a in recent_actions
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RULES MANAGEMENT ====================

@router.post("/rules")
async def create_rule(
    rule: ScalingRuleCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new scaling rule.
    """
    try:
        db_rule = ScalingRule(**rule.dict())
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)

        return {
            "success": True,
            "rule_id": db_rule.id,
            "message": "Rule created successfully"
        }

    except Exception as e:
        logger.error(f"Error creating rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules")
async def get_rules(
    account_id: Optional[str] = Query(None),
    campaign_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get scaling rules.
    """
    try:
        query = db.query(ScalingRule)

        if account_id:
            query = query.filter(ScalingRule.account_id == account_id)

        if campaign_id:
            query = query.filter(ScalingRule.campaign_id == campaign_id)

        rules = query.all()

        return {
            "count": len(rules),
            "rules": [
                {
                    "id": r.id,
                    "account_id": r.account_id,
                    "campaign_id": r.campaign_id,
                    "rule_name": r.rule_name,
                    "enabled": r.enabled,
                    "roas_scale_up_aggressive": r.roas_scale_up_aggressive,
                    "roas_scale_up": r.roas_scale_up,
                    "roas_scale_down": r.roas_scale_down,
                    "roas_pause": r.roas_pause,
                    "max_daily_budget": float(r.max_daily_budget) if r.max_daily_budget else None,
                    "created_at": r.created_at.isoformat()
                }
                for r in rules
            ]
        }

    except Exception as e:
        logger.error(f"Error fetching rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_rule(
    rule_id: int,
    rule: ScalingRuleCreate,
    db: Session = Depends(get_db)
):
    """
    Update an existing scaling rule.
    """
    try:
        db_rule = db.query(ScalingRule).filter_by(id=rule_id).first()

        if not db_rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        # Update fields
        for key, value in rule.dict().items():
            setattr(db_rule, key, value)

        db_rule.updated_at = datetime.utcnow()
        db.commit()

        return {
            "success": True,
            "rule_id": rule_id,
            "message": "Rule updated successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a scaling rule.
    """
    try:
        db_rule = db.query(ScalingRule).filter_by(id=rule_id).first()

        if not db_rule:
            raise HTTPException(status_code=404, detail="Rule not found")

        db.delete(db_rule)
        db.commit()

        return {
            "success": True,
            "message": "Rule deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TIME OPTIMIZATION ====================

@router.post("/time-optimization/learn")
async def learn_optimal_hours(
    campaign_id: Optional[str] = Query(None),
    min_samples: int = Query(24),
    db: Session = Depends(get_db)
):
    """
    Learn optimal hours for campaign(s).
    """
    try:
        optimizer = TimeBasedOptimizer(db_session=db)

        if campaign_id:
            # Single campaign
            profile = optimizer.learn_optimal_hours(campaign_id, min_samples)

            if not profile:
                return {
                    "success": False,
                    "message": "Insufficient data to learn patterns"
                }

            return {
                "success": True,
                "campaign_id": campaign_id,
                "peak_hours": profile.peak_hours,
                "valley_hours": profile.valley_hours,
                "confidence": profile.confidence_score
            }
        else:
            # Bulk learn all campaigns
            result = optimizer.bulk_learn_campaigns(min_samples=min_samples)
            return result

    except Exception as e:
        logger.error(f"Error learning optimal hours: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-optimization/report/{campaign_id}")
async def get_time_report(
    campaign_id: str,
    db: Session = Depends(get_db)
):
    """
    Get time-based performance report for campaign.
    """
    try:
        optimizer = TimeBasedOptimizer(db_session=db)
        report = optimizer.get_campaign_time_report(campaign_id)

        if not report:
            raise HTTPException(status_code=404, detail="No time profile found for campaign")

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching time report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/time-optimization/schedule/{campaign_id}")
async def get_budget_schedule(
    campaign_id: str,
    base_daily_budget: float = Query(..., gt=0),
    peak_multiplier: float = Query(1.3, gt=1.0, le=2.0),
    db: Session = Depends(get_db)
):
    """
    Get recommended hourly budget schedule.
    """
    try:
        optimizer = TimeBasedOptimizer(db_session=db)
        schedule = optimizer.recommend_budget_schedule(
            campaign_id=campaign_id,
            base_daily_budget=base_daily_budget,
            peak_multiplier=peak_multiplier
        )

        return {
            "campaign_id": campaign_id,
            "base_daily_budget": base_daily_budget,
            "peak_multiplier": peak_multiplier,
            "schedule": schedule
        }

    except Exception as e:
        logger.error(f"Error generating budget schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Export router
__all__ = ["router"]
