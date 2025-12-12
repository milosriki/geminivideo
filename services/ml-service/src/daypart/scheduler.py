"""
Day-Part Scheduler - Schedule Generation & API
Agent 8 - Day-Part Optimizer

Generates optimal ad schedules based on day-part analysis with
budget-aware allocation and provides REST API endpoints.

Features:
- Budget-aware schedule generation
- Multiple scheduling strategies (aggressive, balanced, conservative)
- Hour-by-hour and day-by-day scheduling
- Performance prediction for schedules
- RESTful API endpoints
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .models import DayPartSchedule, DayPartAnalysis
from .day_part_optimizer import DayPartOptimizer
from .time_analyzer import TimeAnalyzer

logger = logging.getLogger(__name__)

# API Router
router = APIRouter(prefix="/daypart", tags=["daypart"])


# Pydantic Models for API
class AnalyzeRequest(BaseModel):
    """Request model for day-part analysis."""
    campaign_id: str = Field(..., description="Campaign identifier")
    platform: str = Field(..., description="Platform (meta, tiktok, google)")
    niche: Optional[str] = Field(None, description="Niche identifier")
    lookback_days: int = Field(30, ge=7, le=90, description="Days of history to analyze")
    min_samples: int = Field(100, ge=10, description="Minimum samples required")


class ScheduleRequest(BaseModel):
    """Request model for schedule generation."""
    campaign_id: str = Field(..., description="Campaign identifier")
    platform: str = Field(..., description="Platform (meta, tiktok, google)")
    total_daily_budget: float = Field(..., gt=0, description="Total daily budget")
    schedule_type: str = Field("balanced", description="Strategy: aggressive, balanced, conservative")
    peak_multiplier: float = Field(1.5, ge=1.0, le=3.0, description="Budget multiplier for peak hours")
    valley_multiplier: float = Field(0.5, ge=0.1, le=1.0, description="Budget multiplier for valley hours")


class DayPartScheduler:
    """
    Generates optimal day-part schedules with budget allocation.

    Creates actionable schedules that concentrate budget on
    high-performing time windows.
    """

    def __init__(self, db_session: Session):
        """
        Initialize scheduler.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.optimizer = DayPartOptimizer(db_session)
        self.analyzer = TimeAnalyzer(db_session)
        logger.info("DayPartScheduler initialized")

    def generate_schedule(
        self,
        campaign_id: str,
        platform: str,
        total_daily_budget: float,
        schedule_type: str = "balanced",
        peak_multiplier: float = 1.5,
        valley_multiplier: float = 0.5,
        analysis_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate optimal schedule with budget allocation.

        Args:
            campaign_id: Campaign identifier
            platform: Platform name
            total_daily_budget: Total daily budget
            schedule_type: Strategy type
            peak_multiplier: Multiplier for peak hours
            valley_multiplier: Multiplier for valley hours
            analysis_id: Optional existing analysis ID

        Returns:
            Complete schedule with budget allocation
        """
        logger.info(f"Generating {schedule_type} schedule for campaign {campaign_id}")

        # Get or create analysis
        if analysis_id:
            analysis = self.db.query(DayPartAnalysis).filter_by(
                analysis_id=analysis_id
            ).first()

            if not analysis:
                raise ValueError(f"Analysis not found: {analysis_id}")
        else:
            # Perform new analysis
            analysis_result = self.optimizer.analyze_campaign(
                campaign_id=campaign_id,
                platform=platform
            )

            if 'error' in analysis_result:
                raise ValueError(f"Analysis failed: {analysis_result['error']}")

            analysis = self.db.query(DayPartAnalysis).filter_by(
                campaign_id=campaign_id,
                platform=platform
            ).order_by(DayPartAnalysis.created_at.desc()).first()

        # Adjust multipliers based on strategy
        if schedule_type == "aggressive":
            peak_multiplier = min(peak_multiplier * 1.3, 3.0)
            valley_multiplier = max(valley_multiplier * 0.7, 0.1)
        elif schedule_type == "conservative":
            peak_multiplier = min(peak_multiplier * 0.8, 2.0)
            valley_multiplier = max(valley_multiplier * 1.2, 0.5)

        # Generate hourly schedule
        hourly_schedule = self._generate_hourly_schedule(
            analysis,
            total_daily_budget,
            peak_multiplier,
            valley_multiplier
        )

        # Generate daily schedule
        daily_schedule = self._generate_daily_schedule(
            analysis,
            hourly_schedule
        )

        # Calculate budget allocation
        budget_allocation = self._calculate_budget_allocation(
            hourly_schedule,
            total_daily_budget
        )

        # Predict performance
        predicted_metrics = self._predict_schedule_performance(
            analysis,
            hourly_schedule
        )

        # Create schedule object
        schedule_id = f"sched_{campaign_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        schedule = DayPartSchedule(
            schedule_id=schedule_id,
            campaign_id=campaign_id,
            platform=platform,
            total_daily_budget=total_daily_budget,
            schedule_type=schedule_type,
            hourly_schedule=hourly_schedule,
            daily_schedule=daily_schedule,
            budget_allocation=budget_allocation,
            predicted_roas=predicted_metrics['predicted_roas'],
            predicted_conversions=predicted_metrics['predicted_conversions'],
            expected_lift=predicted_metrics['expected_lift'],
            confidence_score=predicted_metrics['confidence_score'],
            confidence_interval_lower=predicted_metrics['confidence_interval'][0],
            confidence_interval_upper=predicted_metrics['confidence_interval'][1],
            generation_metadata={
                'peak_multiplier': peak_multiplier,
                'valley_multiplier': valley_multiplier,
                'analysis_id': analysis.analysis_id if hasattr(analysis, 'analysis_id') else None
            }
        )

        self.db.add(schedule)
        self.db.commit()

        logger.info(f"Schedule generated: {schedule_id}")

        return {
            'schedule_id': schedule_id,
            'campaign_id': campaign_id,
            'platform': platform,
            'schedule_type': schedule_type,
            'total_daily_budget': total_daily_budget,
            'hourly_schedule': hourly_schedule,
            'daily_schedule': daily_schedule,
            'budget_allocation': budget_allocation,
            'predicted_metrics': predicted_metrics,
            'created_at': datetime.utcnow().isoformat()
        }

    def _generate_hourly_schedule(
        self,
        analysis: Any,
        total_daily_budget: float,
        peak_multiplier: float,
        valley_multiplier: float
    ) -> List[Dict[str, Any]]:
        """
        Generate hour-by-hour schedule with budget allocation.

        Args:
            analysis: DayPartAnalysis object
            total_daily_budget: Total budget to allocate
            peak_multiplier: Multiplier for peak hours
            valley_multiplier: Multiplier for valley hours

        Returns:
            List of hourly schedule entries
        """
        peak_hours = analysis.peak_windows or []
        valley_hours = analysis.valley_windows or []

        # Calculate total allocation units
        total_units = 0.0
        for hour in range(24):
            if hour in peak_hours:
                total_units += peak_multiplier
            elif hour in valley_hours:
                total_units += valley_multiplier
            else:
                total_units += 1.0

        # Budget per unit
        budget_per_unit = total_daily_budget / total_units

        # Generate schedule
        hourly_schedule = []
        for hour in range(24):
            if hour in peak_hours:
                multiplier = peak_multiplier
                status = "peak"
            elif hour in valley_hours:
                multiplier = valley_multiplier
                status = "valley"
            else:
                multiplier = 1.0
                status = "normal"

            allocated_budget = budget_per_unit * multiplier

            # Get expected performance from analysis
            hour_performance = {}
            if hasattr(analysis, 'overall_metrics'):
                hour_performance = analysis.overall_metrics.get('hour_performance', {}).get(str(hour), {})

            hourly_schedule.append({
                'hour': hour,
                'hour_label': f"{hour:02d}:00",
                'status': status,
                'allocated_budget': round(allocated_budget, 2),
                'multiplier': multiplier,
                'expected_roas': hour_performance.get('avg_roas', 0.0),
                'expected_ctr': hour_performance.get('avg_ctr', 0.0),
                'is_recommended': status == "peak"
            })

        return hourly_schedule

    def _generate_daily_schedule(
        self,
        analysis: Any,
        hourly_schedule: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate day-of-week schedule summary.

        Args:
            analysis: DayPartAnalysis object
            hourly_schedule: Generated hourly schedule

        Returns:
            List of daily schedule entries
        """
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        daily_schedule = []
        for day_idx, day_name in enumerate(day_names):
            # Get day performance from analysis if available
            day_performance = {}
            if hasattr(analysis, 'overall_metrics'):
                day_performance = analysis.overall_metrics.get('day_performance', {}).get(str(day_idx), {})

            # Calculate daily budget from hourly schedule
            daily_budget = sum(h['allocated_budget'] for h in hourly_schedule)

            daily_schedule.append({
                'day': day_idx,
                'day_name': day_name,
                'allocated_budget': round(daily_budget, 2),
                'expected_roas': day_performance.get('avg_roas', 0.0),
                'recommended_hours': [h['hour'] for h in hourly_schedule if h['is_recommended']]
            })

        return daily_schedule

    def _calculate_budget_allocation(
        self,
        hourly_schedule: List[Dict[str, Any]],
        total_daily_budget: float
    ) -> Dict[str, Any]:
        """
        Calculate budget allocation summary.

        Args:
            hourly_schedule: Generated hourly schedule
            total_daily_budget: Total budget

        Returns:
            Budget allocation summary
        """
        peak_budget = sum(
            h['allocated_budget']
            for h in hourly_schedule
            if h['status'] == 'peak'
        )

        valley_budget = sum(
            h['allocated_budget']
            for h in hourly_schedule
            if h['status'] == 'valley'
        )

        normal_budget = sum(
            h['allocated_budget']
            for h in hourly_schedule
            if h['status'] == 'normal'
        )

        return {
            'total_budget': total_daily_budget,
            'peak_hours_budget': round(peak_budget, 2),
            'valley_hours_budget': round(valley_budget, 2),
            'normal_hours_budget': round(normal_budget, 2),
            'peak_hours_percentage': round((peak_budget / total_daily_budget) * 100, 1),
            'valley_hours_percentage': round((valley_budget / total_daily_budget) * 100, 1),
            'normal_hours_percentage': round((normal_budget / total_daily_budget) * 100, 1)
        }

    def _predict_schedule_performance(
        self,
        analysis: Any,
        hourly_schedule: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Predict performance for the generated schedule.

        Args:
            analysis: DayPartAnalysis object
            hourly_schedule: Generated hourly schedule

        Returns:
            Predicted performance metrics
        """
        # Calculate weighted average ROAS
        total_budget = sum(h['allocated_budget'] for h in hourly_schedule)
        weighted_roas = sum(
            h['allocated_budget'] * h['expected_roas']
            for h in hourly_schedule
        ) / total_budget if total_budget > 0 else 0.0

        # Get baseline ROAS from analysis
        baseline_roas = 0.0
        if hasattr(analysis, 'overall_metrics'):
            baseline_roas = analysis.overall_metrics.get('baseline_roas', 0.0)

        # Calculate expected lift
        expected_lift = ((weighted_roas - baseline_roas) / baseline_roas * 100) if baseline_roas > 0 else 0.0

        # Predict conversions (simplified)
        predicted_conversions = int(total_budget * weighted_roas * 0.02)  # Rough estimate

        # Confidence based on analysis confidence
        confidence = analysis.analysis_confidence if hasattr(analysis, 'analysis_confidence') else 0.7

        # Confidence interval (simplified)
        ci_range = weighted_roas * 0.15  # ±15%
        confidence_interval = (
            max(0, weighted_roas - ci_range),
            weighted_roas + ci_range
        )

        return {
            'predicted_roas': round(weighted_roas, 2),
            'baseline_roas': round(baseline_roas, 2),
            'expected_lift': round(expected_lift, 1),
            'predicted_conversions': predicted_conversions,
            'confidence_score': round(confidence, 2),
            'confidence_interval': [round(ci, 2) for ci in confidence_interval]
        }

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a saved schedule.

        Args:
            schedule_id: Schedule identifier

        Returns:
            Schedule data or None
        """
        schedule = self.db.query(DayPartSchedule).filter_by(
            schedule_id=schedule_id
        ).first()

        if not schedule:
            return None

        return {
            'schedule_id': schedule.schedule_id,
            'campaign_id': schedule.campaign_id,
            'platform': schedule.platform,
            'schedule_type': schedule.schedule_type,
            'total_daily_budget': float(schedule.total_daily_budget),
            'hourly_schedule': schedule.hourly_schedule,
            'daily_schedule': schedule.daily_schedule,
            'budget_allocation': schedule.budget_allocation,
            'predicted_metrics': {
                'predicted_roas': float(schedule.predicted_roas),
                'predicted_conversions': schedule.predicted_conversions,
                'expected_lift': float(schedule.expected_lift),
                'confidence_score': float(schedule.confidence_score)
            },
            'is_active': schedule.is_active,
            'created_at': schedule.created_at.isoformat()
        }


# API Endpoints
def get_db():
    """Dependency to get database session."""
    # This would be properly implemented with actual DB connection
    # For now, it's a placeholder
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    import os

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
    )
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/analyze", summary="Analyze Campaign Day-Part Performance")
async def analyze_daypart(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze historical performance patterns for a campaign.

    Returns detected patterns, peak/valley hours, and actionable recommendations.
    """
    try:
        optimizer = DayPartOptimizer(db)
        result = optimizer.analyze_campaign(
            campaign_id=request.campaign_id,
            platform=request.platform,
            niche=request.niche,
            lookback_days=request.lookback_days,
            min_samples=request.min_samples
        )

        if 'error' in result:
            raise HTTPException(status_code=400, detail=result['error'])

        return result

    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommend/{campaign_id}", summary="Get Day-Part Recommendations")
async def get_recommendations(
    campaign_id: str,
    platform: str = Query(..., description="Platform (meta, tiktok, google)"),
    db: Session = Depends(get_db)
):
    """
    Get day-part recommendations for a campaign.

    Returns the most recent analysis and recommendations.
    """
    try:
        analysis = db.query(DayPartAnalysis).filter_by(
            campaign_id=campaign_id,
            platform=platform
        ).order_by(DayPartAnalysis.created_at.desc()).first()

        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for campaign {campaign_id}"
            )

        return {
            'campaign_id': campaign_id,
            'platform': platform,
            'analysis_id': analysis.analysis_id,
            'recommendations': analysis.recommendations,
            'peak_windows': analysis.peak_windows,
            'valley_windows': analysis.valley_windows,
            'confidence': analysis.analysis_confidence,
            'analyzed_at': analysis.created_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule", summary="Generate Optimal Schedule")
async def generate_schedule(
    request: ScheduleRequest,
    db: Session = Depends(get_db)
):
    """
    Generate optimal day-part schedule with budget allocation.

    Returns hour-by-hour schedule with budget distribution and performance predictions.
    """
    try:
        scheduler = DayPartScheduler(db)
        schedule = scheduler.generate_schedule(
            campaign_id=request.campaign_id,
            platform=request.platform,
            total_daily_budget=request.total_daily_budget,
            schedule_type=request.schedule_type,
            peak_multiplier=request.peak_multiplier,
            valley_multiplier=request.valley_multiplier
        )

        return schedule

    except Exception as e:
        logger.error(f"Schedule generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/{schedule_id}", summary="Get Schedule Details")
async def get_schedule_details(
    schedule_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve details for a specific schedule.
    """
    try:
        scheduler = DayPartScheduler(db)
        schedule = scheduler.get_schedule(schedule_id)

        if not schedule:
            raise HTTPException(
                status_code=404,
                detail=f"Schedule not found: {schedule_id}"
            )

        return schedule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schedule retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health Check")
async def health_check():
    """Health check endpoint for day-part service."""
    return {
        'service': 'daypart_optimizer',
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }
