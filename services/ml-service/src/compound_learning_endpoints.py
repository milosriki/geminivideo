"""
Compound Learning Endpoints - Agent 50
FastAPI endpoints for the compound learning system

These endpoints should be integrated into main.py
"""

from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
from sqlalchemy import and_

logger = logging.getLogger(__name__)


class LearningCycleRequest(BaseModel):
    """Request model for triggering learning cycle"""
    account_id: Optional[str] = None


async def run_learning_cycle_endpoint(request: LearningCycleRequest):
    """
    Run a compound learning cycle immediately (Agent 50)

    Normally runs automatically at 3 AM daily, but can be triggered manually.

    Steps:
    1. Collect new performance data
    2. Extract patterns and insights
    3. Update knowledge base
    4. Retrain models if needed
    5. Update creative DNA formulas
    6. Calculate improvement metrics

    Args:
        request: Optional account_id to focus on

    Returns:
        Learning cycle results
    """
    try:
        logger.info("📚 Manually triggering compound learning cycle...")

        from src.compound_learner import compound_learner

        result = await compound_learner.learning_cycle(account_id=request.account_id)

        return {
            "success": True,
            "cycle_id": result.cycle_id,
            "status": result.status,
            "metrics": {
                "new_data_points": result.new_data_points,
                "new_patterns": result.new_patterns,
                "new_knowledge_nodes": result.new_knowledge_nodes,
                "models_retrained": result.models_retrained,
                "improvement_rate": round(result.improvement_rate * 100, 2),
                "cumulative_improvement": round(result.cumulative_improvement * 100, 2)
            },
            "duration_seconds": result.duration_seconds,
            "message": "Learning cycle completed successfully"
        }

    except Exception as e:
        logger.error(f"Error running learning cycle: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def get_improvement_trajectory_endpoint(account_id: str):
    """
    Get improvement trajectory with compound growth projections (Agent 50)

    Shows:
    - Current performance vs baseline
    - Daily improvement rate
    - Projected performance at 30, 90, 365 days
    - Historical improvement curve
    - On-track status for 10x improvement

    This is the KEY metric for demonstrating compound learning value.

    Args:
        account_id: Account ID to analyze

    Returns:
        Improvement trajectory with projections
    """
    try:
        logger.info(f"📈 Calculating improvement trajectory for account {account_id}...")

        from src.compound_learner import compound_learner

        trajectory = await compound_learner.get_improvement_trajectory(account_id)

        return {
            "success": True,
            "trajectory": trajectory
        }

    except Exception as e:
        logger.error(f"Error getting improvement trajectory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def get_compound_learning_dashboard_endpoint(account_id: Optional[str] = None):
    """
    Get compound learning dashboard (Agent 50)

    Complete view of:
    - Improvement trajectory and projections
    - Knowledge accumulation stats
    - Pattern discovery
    - Learning cycle history
    - Compound effect visualization

    Args:
        account_id: Optional account filter

    Returns:
        Complete dashboard data
    """
    try:
        logger.info("📊 Generating compound learning dashboard...")

        from src.compound_learner import compound_learner

        # Get stats
        db = compound_learner.SessionLocal()

        # Get recent learning cycles
        from src.compound_learner import LearningCycleLog
        recent_cycles = db.query(LearningCycleLog).order_by(
            LearningCycleLog.started_at.desc()
        ).limit(10).all()

        # Get knowledge stats
        from src.compound_learner import KnowledgeNode, LearningPattern
        total_knowledge_nodes = db.query(KnowledgeNode).count()
        total_patterns = db.query(LearningPattern).filter(
            LearningPattern.status == "active"
        ).count()

        # Get improvement snapshots
        from src.compound_learner import CompoundImprovementSnapshot
        snapshots_query = db.query(CompoundImprovementSnapshot)
        if account_id:
            snapshots_query = snapshots_query.filter(
                CompoundImprovementSnapshot.account_id == account_id
            )
        recent_snapshots = snapshots_query.order_by(
            CompoundImprovementSnapshot.date.desc()
        ).limit(30).all()

        db.close()

        # Calculate overall improvement
        if recent_snapshots and len(recent_snapshots) >= 2:
            latest = recent_snapshots[0]
            oldest = recent_snapshots[-1]
            if oldest.avg_roas > 0:
                overall_improvement = (latest.avg_roas - oldest.avg_roas) / oldest.avg_roas
            else:
                overall_improvement = 0
        else:
            overall_improvement = 0

        return {
            "success": True,
            "dashboard": {
                "overview": {
                    "total_knowledge_nodes": total_knowledge_nodes,
                    "total_active_patterns": total_patterns,
                    "total_learning_cycles": len(recent_cycles),
                    "overall_improvement": round(overall_improvement * 100, 2)
                },
                "recent_cycles": [
                    {
                        "cycle_id": cycle.cycle_id,
                        "started_at": cycle.started_at.isoformat() if cycle.started_at else None,
                        "status": cycle.status,
                        "new_data_points": cycle.new_data_points,
                        "new_patterns": cycle.new_patterns,
                        "improvement_rate": round(cycle.improvement_rate * 100, 2) if cycle.improvement_rate else 0,
                        "duration_seconds": cycle.duration_seconds
                    }
                    for cycle in recent_cycles
                ],
                "improvement_history": [
                    {
                        "date": snapshot.date,
                        "avg_roas": round(snapshot.avg_roas, 2),
                        "avg_ctr": round(snapshot.avg_ctr, 4),
                        "improvement_factor": round(snapshot.improvement_factor_roas, 2),
                        "total_revenue": round(snapshot.total_revenue, 2)
                    }
                    for snapshot in reversed(recent_snapshots)  # Chronological order
                ],
                "compound_effect": {
                    "description": "Expected improvement trajectory with compound learning",
                    "day_1": 1.0,
                    "day_30": 2.0,
                    "day_90": 5.0,
                    "day_365": 10.0,
                    "current_progress": round(1.0 + overall_improvement, 2)
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting compound learning dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def get_knowledge_graph_endpoint(limit: int = 50):
    """
    Get knowledge graph (Agent 50)

    Returns nodes and relationships for visualization.

    Args:
        limit: Maximum nodes to return

    Returns:
        Knowledge graph data
    """
    try:
        logger.info("🧠 Fetching knowledge graph...")

        from src.compound_learner import compound_learner, KnowledgeNode, KnowledgeRelationship

        db = compound_learner.SessionLocal()

        # Get top knowledge nodes by importance
        nodes = db.query(KnowledgeNode).order_by(
            KnowledgeNode.importance.desc()
        ).limit(limit).all()

        # Get relationships between these nodes
        node_ids = [n.node_id for n in nodes]
        relationships = db.query(KnowledgeRelationship).filter(
            and_(
                KnowledgeRelationship.from_node_id.in_(node_ids),
                KnowledgeRelationship.to_node_id.in_(node_ids)
            )
        ).all()

        db.close()

        return {
            "success": True,
            "graph": {
                "nodes": [
                    {
                        "id": node.node_id,
                        "type": node.node_type,
                        "name": node.name,
                        "description": node.description,
                        "confidence": round(node.confidence, 2),
                        "importance": round(node.importance, 2),
                        "knowledge": node.knowledge
                    }
                    for node in nodes
                ],
                "relationships": [
                    {
                        "from": rel.from_node_id,
                        "to": rel.to_node_id,
                        "type": rel.relationship_type,
                        "strength": round(rel.strength, 2)
                    }
                    for rel in relationships
                ],
                "stats": {
                    "total_nodes": len(nodes),
                    "total_relationships": len(relationships)
                }
            }
        }

    except Exception as e:
        logger.error(f"Error getting knowledge graph: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def get_learning_patterns_endpoint(
    pattern_type: Optional[str] = None,
    min_confidence: float = 0.5,
    limit: int = 50
):
    """
    Get discovered learning patterns (Agent 50)

    Returns patterns discovered through compound learning.

    Args:
        pattern_type: Filter by pattern type (hook, template, audience, etc.)
        min_confidence: Minimum confidence score
        limit: Maximum patterns to return

    Returns:
        List of learning patterns
    """
    try:
        logger.info("🔍 Fetching learning patterns...")

        from src.compound_learner import compound_learner, LearningPattern

        db = compound_learner.SessionLocal()

        query = db.query(LearningPattern).filter(
            and_(
                LearningPattern.status == "active",
                LearningPattern.confidence_score >= min_confidence
            )
        )

        if pattern_type:
            query = query.filter(LearningPattern.pattern_type == pattern_type)

        patterns = query.order_by(
            LearningPattern.avg_roas_lift.desc()
        ).limit(limit).all()

        db.close()

        return {
            "success": True,
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_type": p.pattern_type,
                    "pattern_name": p.pattern_name,
                    "description": p.pattern_description,
                    "avg_ctr_lift": round(p.avg_ctr_lift * 100, 2),
                    "avg_roas_lift": round(p.avg_roas_lift * 100, 2),
                    "avg_cvr_lift": round(p.avg_cvr_lift * 100, 2),
                    "sample_size": p.sample_size,
                    "confidence_score": round(p.confidence_score, 2),
                    "discovered_at": p.discovered_at.isoformat() if p.discovered_at else None,
                    "validation_count": p.validation_count
                }
                for p in patterns
            ],
            "count": len(patterns)
        }

    except Exception as e:
        logger.error(f"Error getting learning patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


async def get_scheduler_status_endpoint():
    """
    Get compound learning scheduler status (Agent 50)

    Returns:
        Scheduler status and stats
    """
    try:
        from src.compound_learning_scheduler import compound_learning_scheduler

        stats = compound_learning_scheduler.get_stats()

        return {
            "success": True,
            "scheduler": stats
        }

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
