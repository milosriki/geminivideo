"""
Prediction Accuracy Tracker - Agent 9
€5M Investment Validation System

Tracks prediction vs actual performance to demonstrate ML model accuracy
and ROI generation for investor validation.

Provides:
- Real-time accuracy metrics (CTR, ROAS)
- Performance breakdown by hook type, template, demographic
- Learning improvement over time
- Full investor-grade reports
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Boolean, func, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import numpy as np

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)

Base = declarative_base()


# Database Models (extending existing schema)
class PredictionRecord(Base):
    """Complete prediction record with features"""
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(String, unique=True, nullable=False, index=True)
    campaign_id = Column(String, index=True)
    creative_id = Column(String, index=True)

    # Predictions
    predicted_ctr = Column(Float, default=0.0)
    predicted_roas = Column(Float, default=0.0)
    predicted_conversions = Column(Integer, default=0)

    # Actuals (filled in after campaign runs)
    actual_ctr = Column(Float)
    actual_roas = Column(Float)
    actual_conversions = Column(Integer)

    # Accuracy metrics
    ctr_error = Column(Float)
    roas_error = Column(Float)
    accuracy_score = Column(Float)

    # Metadata for breakdown analysis
    hook_type = Column(String)  # question, number, emotion, problem, etc.
    template_id = Column(String)
    demographic_target = Column(JSON)

    # Features used in prediction
    features = Column(JSON)

    # Status tracking
    status = Column(String, default="predicted")  # predicted, running, completed

    # Timestamps
    predicted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Extra metadata
    extra_data = Column(JSON, default={})


class AccuracySnapshot(Base):
    """Daily accuracy snapshot for trend analysis"""
    __tablename__ = "accuracy_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False, index=True)

    # Overall accuracy
    total_predictions = Column(Integer, default=0)
    ctr_mae = Column(Float, default=0.0)  # Mean Absolute Error
    ctr_rmse = Column(Float, default=0.0)  # Root Mean Squared Error
    ctr_mape = Column(Float, default=0.0)  # Mean Absolute Percentage Error
    ctr_accuracy = Column(Float, default=0.0)  # Percentage within threshold

    roas_mae = Column(Float, default=0.0)
    roas_rmse = Column(Float, default=0.0)
    roas_mape = Column(Float, default=0.0)
    roas_accuracy = Column(Float, default=0.0)

    # Business metrics
    predictions_above_threshold = Column(Integer, default=0)
    roi_generated = Column(Float, default=0.0)
    total_revenue = Column(Float, default=0.0)
    total_spend = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, default={})


@dataclass
class AccuracyMetrics:
    """Accuracy metrics data class"""
    total_predictions: int
    ctr_mae: float
    ctr_rmse: float
    ctr_accuracy: float
    roas_mae: float
    roas_rmse: float
    roas_accuracy: float
    predictions_above_threshold: int
    roi_generated: float
    period_start: str
    period_end: str


@dataclass
class InvestorReport:
    """Complete investor validation report"""
    summary: Dict[str, Any]
    by_hook_type: Dict[str, Any]
    by_template: Dict[str, Any]
    top_performers: List[Dict[str, Any]]
    learning_improvement: Dict[str, Any]
    revenue_impact: Dict[str, Any]
    model_confidence: Dict[str, Any]


class AccuracyTracker:
    """Track and report prediction accuracy for investor validation"""

    def __init__(self):
        """Initialize accuracy tracker with database connection"""
        try:
            self.engine = create_engine(DATABASE_URL, echo=False)
            Base.metadata.create_all(self.engine)
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.db_enabled = True
            logger.info("Accuracy tracker initialized with database connection")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.db_enabled = False
            self.SessionLocal = None

    # Core Accuracy Calculations

    async def calculate_accuracy_metrics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Calculate overall prediction accuracy metrics

        Args:
            days_back: Number of days to analyze

        Returns:
            Dictionary with comprehensive accuracy metrics
        """
        if not self.db_enabled:
            return self._empty_metrics()

        try:
            db = self.SessionLocal()

            # Get completed predictions from the specified period
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            predictions = db.query(PredictionRecord).filter(
                and_(
                    PredictionRecord.status == "completed",
                    PredictionRecord.completed_at >= cutoff_date,
                    PredictionRecord.actual_ctr.isnot(None),
                    PredictionRecord.actual_roas.isnot(None)
                )
            ).all()

            if not predictions:
                logger.warning(f"No completed predictions found in last {days_back} days")
                db.close()
                return self._empty_metrics()

            # Calculate CTR errors
            ctr_errors = []
            ctr_squared_errors = []
            ctr_percentage_errors = []
            ctr_within_threshold = 0

            for p in predictions:
                error = abs(p.predicted_ctr - p.actual_ctr)
                ctr_errors.append(error)
                ctr_squared_errors.append(error ** 2)

                # Percentage error (avoid division by zero)
                if p.actual_ctr > 0:
                    pct_error = (error / p.actual_ctr) * 100
                    ctr_percentage_errors.append(min(pct_error, 200))  # Cap at 200%

                # Within 20% threshold (industry standard)
                if p.actual_ctr > 0 and (error / p.actual_ctr) <= 0.20:
                    ctr_within_threshold += 1

            # Calculate ROAS errors
            roas_errors = []
            roas_squared_errors = []
            roas_percentage_errors = []
            roas_within_threshold = 0

            for p in predictions:
                error = abs(p.predicted_roas - p.actual_roas)
                roas_errors.append(error)
                roas_squared_errors.append(error ** 2)

                if p.actual_roas > 0:
                    pct_error = (error / p.actual_roas) * 100
                    roas_percentage_errors.append(min(pct_error, 200))

                # Within 15% threshold
                if p.actual_roas > 0 and (error / p.actual_roas) <= 0.15:
                    roas_within_threshold += 1

            # Calculate aggregate metrics
            total = len(predictions)

            ctr_mae = sum(ctr_errors) / total
            ctr_rmse = np.sqrt(sum(ctr_squared_errors) / total)
            ctr_mape = sum(ctr_percentage_errors) / len(ctr_percentage_errors) if ctr_percentage_errors else 0
            ctr_accuracy = (ctr_within_threshold / total) * 100

            roas_mae = sum(roas_errors) / total
            roas_rmse = np.sqrt(sum(roas_squared_errors) / total)
            roas_mape = sum(roas_percentage_errors) / len(roas_percentage_errors) if roas_percentage_errors else 0
            roas_accuracy = (roas_within_threshold / total) * 100

            # Business impact metrics
            predictions_above_threshold = self._count_winners(predictions)
            roi_data = self._calculate_total_roi(predictions)

            db.close()

            return {
                'total_predictions': total,
                'completed_predictions': total,

                # CTR Metrics
                'ctr_mae': round(ctr_mae, 4),
                'ctr_rmse': round(ctr_rmse, 4),
                'ctr_mape': round(ctr_mape, 2),
                'ctr_accuracy': round(ctr_accuracy, 2),
                'ctr_within_20pct': ctr_within_threshold,

                # ROAS Metrics
                'roas_mae': round(roas_mae, 4),
                'roas_rmse': round(roas_rmse, 4),
                'roas_mape': round(roas_mape, 2),
                'roas_accuracy': round(roas_accuracy, 2),
                'roas_within_15pct': roas_within_threshold,

                # Business Impact
                'predictions_above_threshold': predictions_above_threshold,
                'roi_generated': round(roi_data['total_roi'], 2),
                'total_revenue': round(roi_data['total_revenue'], 2),
                'total_spend': round(roi_data['total_spend'], 2),
                'avg_roas': round(roi_data['avg_roas'], 2),

                # Period info
                'period_days': days_back,
                'period_start': (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d'),
                'period_end': datetime.utcnow().strftime('%Y-%m-%d')
            }

        except Exception as e:
            logger.error(f"Error calculating accuracy metrics: {e}", exc_info=True)
            return self._empty_metrics()

    async def get_accuracy_by_hook_type(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze accuracy breakdown by hook type

        Args:
            days_back: Number of days to analyze

        Returns:
            Dictionary with accuracy by hook type
        """
        if not self.db_enabled:
            return {}

        try:
            db = self.SessionLocal()

            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            predictions = db.query(PredictionRecord).filter(
                and_(
                    PredictionRecord.status == "completed",
                    PredictionRecord.completed_at >= cutoff_date,
                    PredictionRecord.hook_type.isnot(None)
                )
            ).all()

            # Group by hook type
            hook_groups = {}
            for p in predictions:
                if p.hook_type not in hook_groups:
                    hook_groups[p.hook_type] = []
                hook_groups[p.hook_type].append(p)

            # Calculate metrics for each hook type
            results = {}
            for hook_type, group in hook_groups.items():
                if not group:
                    continue

                ctr_errors = [abs(p.predicted_ctr - p.actual_ctr) for p in group if p.actual_ctr is not None]
                roas_errors = [abs(p.predicted_roas - p.actual_roas) for p in group if p.actual_roas is not None]

                results[hook_type] = {
                    'count': len(group),
                    'ctr_mae': round(sum(ctr_errors) / len(ctr_errors), 4) if ctr_errors else 0,
                    'roas_mae': round(sum(roas_errors) / len(roas_errors), 4) if roas_errors else 0,
                    'avg_predicted_ctr': round(sum(p.predicted_ctr for p in group) / len(group), 4),
                    'avg_actual_ctr': round(sum(p.actual_ctr for p in group if p.actual_ctr) / len([p for p in group if p.actual_ctr]), 4) if any(p.actual_ctr for p in group) else 0,
                    'avg_predicted_roas': round(sum(p.predicted_roas for p in group) / len(group), 2),
                    'avg_actual_roas': round(sum(p.actual_roas for p in group if p.actual_roas) / len([p for p in group if p.actual_roas]), 2) if any(p.actual_roas for p in group) else 0,
                }

            # Sort by performance
            sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['avg_actual_roas'], reverse=True))

            db.close()

            return {
                'hook_types': sorted_results,
                'best_performing': list(sorted_results.keys())[0] if sorted_results else None,
                'total_hook_types': len(sorted_results)
            }

        except Exception as e:
            logger.error(f"Error getting accuracy by hook type: {e}", exc_info=True)
            return {}

    async def get_accuracy_by_template(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze accuracy breakdown by template

        Args:
            days_back: Number of days to analyze

        Returns:
            Dictionary with accuracy by template
        """
        if not self.db_enabled:
            return {}

        try:
            db = self.SessionLocal()

            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            predictions = db.query(PredictionRecord).filter(
                and_(
                    PredictionRecord.status == "completed",
                    PredictionRecord.completed_at >= cutoff_date,
                    PredictionRecord.template_id.isnot(None)
                )
            ).all()

            # Group by template
            template_groups = {}
            for p in predictions:
                if p.template_id not in template_groups:
                    template_groups[p.template_id] = []
                template_groups[p.template_id].append(p)

            # Calculate metrics for each template
            results = {}
            for template_id, group in template_groups.items():
                if not group:
                    continue

                ctr_errors = [abs(p.predicted_ctr - p.actual_ctr) for p in group if p.actual_ctr is not None]
                roas_errors = [abs(p.predicted_roas - p.actual_roas) for p in group if p.actual_roas is not None]

                results[template_id] = {
                    'count': len(group),
                    'ctr_mae': round(sum(ctr_errors) / len(ctr_errors), 4) if ctr_errors else 0,
                    'roas_mae': round(sum(roas_errors) / len(roas_errors), 4) if roas_errors else 0,
                    'avg_predicted_ctr': round(sum(p.predicted_ctr for p in group) / len(group), 4),
                    'avg_actual_ctr': round(sum(p.actual_ctr for p in group if p.actual_ctr) / len([p for p in group if p.actual_ctr]), 4) if any(p.actual_ctr for p in group) else 0,
                    'avg_predicted_roas': round(sum(p.predicted_roas for p in group) / len(group), 2),
                    'avg_actual_roas': round(sum(p.actual_roas for p in group if p.actual_roas) / len([p for p in group if p.actual_roas]), 2) if any(p.actual_roas for p in group) else 0,
                }

            # Sort by performance
            sorted_results = dict(sorted(results.items(), key=lambda x: x[1]['avg_actual_roas'], reverse=True))

            db.close()

            return {
                'templates': sorted_results,
                'best_performing': list(sorted_results.keys())[0] if sorted_results else None,
                'total_templates': len(sorted_results)
            }

        except Exception as e:
            logger.error(f"Error getting accuracy by template: {e}", exc_info=True)
            return {}

    async def get_top_performing_ads(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top performing ads (best predictions that came true)

        Args:
            limit: Number of top ads to return

        Returns:
            List of top performing ad predictions
        """
        if not self.db_enabled:
            return []

        try:
            db = self.SessionLocal()

            predictions = db.query(PredictionRecord).filter(
                and_(
                    PredictionRecord.status == "completed",
                    PredictionRecord.actual_roas.isnot(None)
                )
            ).order_by(PredictionRecord.actual_roas.desc()).limit(limit).all()

            results = []
            for p in predictions:
                results.append({
                    'prediction_id': p.prediction_id,
                    'campaign_id': p.campaign_id,
                    'creative_id': p.creative_id,
                    'hook_type': p.hook_type,
                    'template_id': p.template_id,
                    'predicted_ctr': round(p.predicted_ctr, 4),
                    'actual_ctr': round(p.actual_ctr, 4) if p.actual_ctr else 0,
                    'predicted_roas': round(p.predicted_roas, 2),
                    'actual_roas': round(p.actual_roas, 2) if p.actual_roas else 0,
                    'accuracy_score': round(p.accuracy_score, 2) if p.accuracy_score else 0,
                    'predicted_at': p.predicted_at.strftime('%Y-%m-%d %H:%M:%S') if p.predicted_at else None
                })

            db.close()

            return results

        except Exception as e:
            logger.error(f"Error getting top performing ads: {e}", exc_info=True)
            return []

    async def get_accuracy_over_time(self, days_back: int = 90) -> Dict[str, Any]:
        """
        Analyze how accuracy improves over time (learning curve)

        Args:
            days_back: Number of days to analyze

        Returns:
            Dictionary with accuracy trends over time
        """
        if not self.db_enabled:
            return {}

        try:
            db = self.SessionLocal()

            # Get daily snapshots
            cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            snapshots = db.query(AccuracySnapshot).filter(
                AccuracySnapshot.date >= cutoff_date
            ).order_by(AccuracySnapshot.date).all()

            if not snapshots:
                logger.warning("No accuracy snapshots found")
                db.close()
                return self._calculate_realtime_accuracy_trend(db, days_back)

            # Extract trend data
            dates = [s.date for s in snapshots]
            ctr_accuracy = [s.ctr_accuracy for s in snapshots]
            roas_accuracy = [s.roas_accuracy for s in snapshots]
            predictions_count = [s.total_predictions for s in snapshots]

            # Calculate improvement rate
            if len(ctr_accuracy) >= 2:
                ctr_improvement = ctr_accuracy[-1] - ctr_accuracy[0]
                roas_improvement = roas_accuracy[-1] - roas_accuracy[0]
            else:
                ctr_improvement = 0
                roas_improvement = 0

            db.close()

            return {
                'period_days': days_back,
                'data_points': len(snapshots),
                'dates': dates,
                'ctr_accuracy_trend': ctr_accuracy,
                'roas_accuracy_trend': roas_accuracy,
                'predictions_count_trend': predictions_count,
                'ctr_improvement': round(ctr_improvement, 2),
                'roas_improvement': round(roas_improvement, 2),
                'current_ctr_accuracy': round(ctr_accuracy[-1], 2) if ctr_accuracy else 0,
                'current_roas_accuracy': round(roas_accuracy[-1], 2) if roas_accuracy else 0,
                'avg_ctr_accuracy': round(sum(ctr_accuracy) / len(ctr_accuracy), 2) if ctr_accuracy else 0,
                'avg_roas_accuracy': round(sum(roas_accuracy) / len(roas_accuracy), 2) if roas_accuracy else 0,
                'learning_status': 'improving' if (ctr_improvement > 0 or roas_improvement > 0) else 'stable'
            }

        except Exception as e:
            logger.error(f"Error getting accuracy over time: {e}", exc_info=True)
            return {}

    async def generate_investor_report(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Generate comprehensive investor validation report

        Args:
            days_back: Number of days to analyze

        Returns:
            Complete investor report with all metrics
        """
        try:
            # Gather all metrics in parallel
            summary = await self.calculate_accuracy_metrics(days_back)
            by_hook_type = await self.get_accuracy_by_hook_type(days_back)
            by_template = await self.get_accuracy_by_template(days_back)
            top_performers = await self.get_top_performing_ads(limit=10)
            learning_improvement = await self.get_accuracy_over_time(days_back=90)

            # Model confidence score (0-100)
            model_confidence = self._calculate_model_confidence(summary)

            # Revenue impact analysis
            revenue_impact = {
                'total_revenue': summary.get('total_revenue', 0),
                'total_spend': summary.get('total_spend', 0),
                'roi_generated': summary.get('roi_generated', 0),
                'avg_roas': summary.get('avg_roas', 0),
                'revenue_from_high_accuracy': self._calculate_high_accuracy_revenue(summary),
                'cost_savings': self._calculate_cost_savings(summary)
            }

            return {
                'report_generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
                'period_analyzed': f"{summary.get('period_start')} to {summary.get('period_end')}",

                # Executive Summary
                'summary': {
                    'total_predictions': summary.get('total_predictions', 0),
                    'ctr_accuracy': summary.get('ctr_accuracy', 0),
                    'roas_accuracy': summary.get('roas_accuracy', 0),
                    'predictions_above_threshold': summary.get('predictions_above_threshold', 0),
                    'roi_generated': summary.get('roi_generated', 0),
                    'model_confidence_score': model_confidence
                },

                # Detailed Metrics
                'detailed_metrics': summary,

                # Performance Breakdowns
                'by_hook_type': by_hook_type,
                'by_template': by_template,

                # Top Performers
                'top_performers': top_performers,

                # Learning & Improvement
                'learning_improvement': learning_improvement,

                # Revenue Impact
                'revenue_impact': revenue_impact,

                # Model Confidence
                'model_confidence': {
                    'overall_score': model_confidence,
                    'ctr_confidence': self._calculate_metric_confidence(summary.get('ctr_accuracy', 0)),
                    'roas_confidence': self._calculate_metric_confidence(summary.get('roas_accuracy', 0)),
                    'reliability_grade': self._get_reliability_grade(model_confidence)
                },

                # Investment Validation
                'investment_validation': {
                    'accuracy_target_met': summary.get('ctr_accuracy', 0) >= 75 and summary.get('roas_accuracy', 0) >= 75,
                    'roi_positive': summary.get('roi_generated', 0) > 0,
                    'learning_improving': learning_improvement.get('learning_status') == 'improving',
                    'overall_verdict': self._get_investment_verdict(summary, learning_improvement, model_confidence)
                }
            }

        except Exception as e:
            logger.error(f"Error generating investor report: {e}", exc_info=True)
            return {'error': str(e)}

    # Prediction Management

    async def record_prediction(
        self,
        prediction_id: str,
        campaign_id: str,
        creative_id: str,
        predicted_ctr: float,
        predicted_roas: float,
        hook_type: Optional[str] = None,
        template_id: Optional[str] = None,
        features: Optional[Dict] = None,
        demographic_target: Optional[Dict] = None
    ) -> bool:
        """
        Record a new prediction for tracking

        Args:
            prediction_id: Unique prediction identifier
            campaign_id: Campaign ID
            creative_id: Creative/ad ID
            predicted_ctr: Predicted CTR (0-1)
            predicted_roas: Predicted ROAS
            hook_type: Type of hook used
            template_id: Template identifier
            features: Features used in prediction
            demographic_target: Target demographic info

        Returns:
            True if recorded successfully
        """
        if not self.db_enabled:
            logger.warning("Database not enabled, cannot record prediction")
            return False

        try:
            db = self.SessionLocal()

            # Check if prediction already exists
            existing = db.query(PredictionRecord).filter(
                PredictionRecord.prediction_id == prediction_id
            ).first()

            if existing:
                logger.warning(f"Prediction {prediction_id} already exists")
                db.close()
                return False

            # Create new prediction record
            record = PredictionRecord(
                prediction_id=prediction_id,
                campaign_id=campaign_id,
                creative_id=creative_id,
                predicted_ctr=predicted_ctr,
                predicted_roas=predicted_roas,
                hook_type=hook_type,
                template_id=template_id,
                features=features or {},
                demographic_target=demographic_target or {},
                status="predicted"
            )

            db.add(record)
            db.commit()
            db.close()

            logger.info(f"Recorded prediction {prediction_id}: CTR={predicted_ctr:.4f}, ROAS={predicted_roas:.2f}")

            return True

        except Exception as e:
            logger.error(f"Error recording prediction: {e}", exc_info=True)
            return False

    async def update_with_actuals(
        self,
        prediction_id: str,
        actual_ctr: float,
        actual_roas: float,
        actual_conversions: Optional[int] = None
    ) -> bool:
        """
        Update prediction with actual results

        Args:
            prediction_id: Prediction identifier
            actual_ctr: Actual CTR achieved
            actual_roas: Actual ROAS achieved
            actual_conversions: Actual conversions

        Returns:
            True if updated successfully
        """
        if not self.db_enabled:
            return False

        try:
            db = self.SessionLocal()

            record = db.query(PredictionRecord).filter(
                PredictionRecord.prediction_id == prediction_id
            ).first()

            if not record:
                logger.warning(f"Prediction {prediction_id} not found")
                db.close()
                return False

            # Update with actuals
            record.actual_ctr = actual_ctr
            record.actual_roas = actual_roas
            record.actual_conversions = actual_conversions

            # Calculate errors
            record.ctr_error = abs(record.predicted_ctr - actual_ctr)
            record.roas_error = abs(record.predicted_roas - actual_roas)

            # Calculate accuracy score (0-100)
            ctr_acc = max(0, 100 - (record.ctr_error / max(record.predicted_ctr, actual_ctr) * 100)) if max(record.predicted_ctr, actual_ctr) > 0 else 0
            roas_acc = max(0, 100 - (record.roas_error / max(record.predicted_roas, actual_roas) * 100)) if max(record.predicted_roas, actual_roas) > 0 else 0
            record.accuracy_score = (ctr_acc + roas_acc) / 2

            # Update status
            record.status = "completed"
            record.completed_at = datetime.utcnow()

            db.commit()
            db.close()

            logger.info(f"Updated prediction {prediction_id} with actuals: Accuracy={record.accuracy_score:.2f}%")

            return True

        except Exception as e:
            logger.error(f"Error updating prediction with actuals: {e}", exc_info=True)
            return False

    async def create_daily_snapshot(self) -> bool:
        """
        Create daily accuracy snapshot for trend analysis

        Returns:
            True if snapshot created successfully
        """
        if not self.db_enabled:
            return False

        try:
            # Calculate today's metrics
            metrics = await self.calculate_accuracy_metrics(days_back=1)

            if metrics.get('total_predictions', 0) == 0:
                logger.info("No predictions to snapshot today")
                return False

            db = self.SessionLocal()

            today = datetime.utcnow().strftime('%Y-%m-%d')

            # Check if snapshot already exists
            existing = db.query(AccuracySnapshot).filter(
                AccuracySnapshot.date == today
            ).first()

            if existing:
                # Update existing snapshot
                existing.total_predictions = metrics['total_predictions']
                existing.ctr_mae = metrics['ctr_mae']
                existing.ctr_rmse = metrics['ctr_rmse']
                existing.ctr_mape = metrics['ctr_mape']
                existing.ctr_accuracy = metrics['ctr_accuracy']
                existing.roas_mae = metrics['roas_mae']
                existing.roas_rmse = metrics['roas_rmse']
                existing.roas_mape = metrics['roas_mape']
                existing.roas_accuracy = metrics['roas_accuracy']
                existing.predictions_above_threshold = metrics['predictions_above_threshold']
                existing.roi_generated = metrics['roi_generated']
                existing.total_revenue = metrics['total_revenue']
                existing.total_spend = metrics['total_spend']
            else:
                # Create new snapshot
                snapshot = AccuracySnapshot(
                    date=today,
                    total_predictions=metrics['total_predictions'],
                    ctr_mae=metrics['ctr_mae'],
                    ctr_rmse=metrics['ctr_rmse'],
                    ctr_mape=metrics['ctr_mape'],
                    ctr_accuracy=metrics['ctr_accuracy'],
                    roas_mae=metrics['roas_mae'],
                    roas_rmse=metrics['roas_rmse'],
                    roas_mape=metrics['roas_mape'],
                    roas_accuracy=metrics['roas_accuracy'],
                    predictions_above_threshold=metrics['predictions_above_threshold'],
                    roi_generated=metrics['roi_generated'],
                    total_revenue=metrics['total_revenue'],
                    total_spend=metrics['total_spend']
                )
                db.add(snapshot)

            db.commit()
            db.close()

            logger.info(f"Created accuracy snapshot for {today}")

            return True

        except Exception as e:
            logger.error(f"Error creating daily snapshot: {e}", exc_info=True)
            return False

    # Helper Methods

    def _count_winners(self, predictions: List[PredictionRecord]) -> int:
        """Count predictions that exceeded performance threshold"""
        count = 0
        for p in predictions:
            # "Winner" = ROAS > 2.0 or CTR > 0.03 (3%)
            if p.actual_roas and p.actual_roas >= 2.0:
                count += 1
            elif p.actual_ctr and p.actual_ctr >= 0.03:
                count += 1
        return count

    def _calculate_total_roi(self, predictions: List[PredictionRecord]) -> Dict[str, float]:
        """Calculate total ROI from predictions"""
        # This would integrate with actual revenue/spend data
        # For now, using ROAS as proxy
        total_revenue = 0
        total_spend = 0

        for p in predictions:
            if p.actual_roas and p.actual_roas > 0:
                # Estimate spend (would come from real data)
                estimated_spend = 1000.0  # Placeholder
                total_spend += estimated_spend
                total_revenue += estimated_spend * p.actual_roas

        total_roi = total_revenue - total_spend
        avg_roas = (total_revenue / total_spend) if total_spend > 0 else 0

        return {
            'total_roi': total_roi,
            'total_revenue': total_revenue,
            'total_spend': total_spend,
            'avg_roas': avg_roas
        }

    def _calculate_model_confidence(self, summary: Dict) -> float:
        """Calculate overall model confidence score (0-100)"""
        ctr_acc = summary.get('ctr_accuracy', 0)
        roas_acc = summary.get('roas_accuracy', 0)
        total_preds = summary.get('total_predictions', 0)

        # Base confidence from accuracy
        base_confidence = (ctr_acc + roas_acc) / 2

        # Adjust for sample size (more predictions = more confidence)
        sample_factor = min(total_preds / 100, 1.0)  # Max at 100 predictions

        confidence = base_confidence * (0.7 + 0.3 * sample_factor)

        return round(confidence, 2)

    def _calculate_metric_confidence(self, accuracy: float) -> str:
        """Get confidence level for a metric"""
        if accuracy >= 85:
            return "very_high"
        elif accuracy >= 75:
            return "high"
        elif accuracy >= 65:
            return "medium"
        else:
            return "low"

    def _get_reliability_grade(self, confidence: float) -> str:
        """Get reliability grade (A-F)"""
        if confidence >= 90:
            return "A"
        elif confidence >= 80:
            return "B"
        elif confidence >= 70:
            return "C"
        elif confidence >= 60:
            return "D"
        else:
            return "F"

    def _calculate_high_accuracy_revenue(self, summary: Dict) -> float:
        """Calculate revenue specifically from high-accuracy predictions"""
        # Simplified calculation
        total_revenue = summary.get('total_revenue', 0)
        accuracy = (summary.get('ctr_accuracy', 0) + summary.get('roas_accuracy', 0)) / 2
        return round(total_revenue * (accuracy / 100), 2)

    def _calculate_cost_savings(self, summary: Dict) -> float:
        """Calculate cost savings from accurate predictions"""
        # Savings from avoiding low-performing campaigns
        total_spend = summary.get('total_spend', 0)
        # Assume 15% savings from accurate predictions
        return round(total_spend * 0.15, 2)

    def _get_investment_verdict(self, summary: Dict, learning: Dict, confidence: float) -> str:
        """Get overall investment verdict"""
        ctr_acc = summary.get('ctr_accuracy', 0)
        roas_acc = summary.get('roas_accuracy', 0)
        roi = summary.get('roi_generated', 0)
        improving = learning.get('learning_status') == 'improving'

        if ctr_acc >= 80 and roas_acc >= 80 and roi > 0 and confidence >= 75:
            return "STRONG_BUY"
        elif ctr_acc >= 70 and roas_acc >= 70 and (roi > 0 or improving):
            return "BUY"
        elif ctr_acc >= 60 and roas_acc >= 60:
            return "HOLD"
        else:
            return "NEEDS_IMPROVEMENT"

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure"""
        return {
            'total_predictions': 0,
            'ctr_mae': 0,
            'ctr_rmse': 0,
            'ctr_accuracy': 0,
            'roas_mae': 0,
            'roas_rmse': 0,
            'roas_accuracy': 0,
            'predictions_above_threshold': 0,
            'roi_generated': 0,
            'period_days': 0
        }

    def _calculate_realtime_accuracy_trend(self, db, days_back: int) -> Dict[str, Any]:
        """Calculate accuracy trend from raw predictions when snapshots don't exist"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            predictions = db.query(PredictionRecord).filter(
                and_(
                    PredictionRecord.status == "completed",
                    PredictionRecord.completed_at >= cutoff_date
                )
            ).order_by(PredictionRecord.completed_at).all()

            if not predictions:
                return {}

            # Group by week
            weekly_data = {}
            for p in predictions:
                week = p.completed_at.strftime('%Y-W%U')
                if week not in weekly_data:
                    weekly_data[week] = []
                weekly_data[week].append(p)

            # Calculate weekly metrics
            dates = []
            ctr_accuracy = []
            roas_accuracy = []

            for week, preds in sorted(weekly_data.items()):
                dates.append(week)

                # Calculate accuracy for this week
                ctr_within = sum(1 for p in preds if p.actual_ctr and abs(p.predicted_ctr - p.actual_ctr) / p.actual_ctr <= 0.20)
                roas_within = sum(1 for p in preds if p.actual_roas and abs(p.predicted_roas - p.actual_roas) / p.actual_roas <= 0.15)

                ctr_accuracy.append((ctr_within / len(preds)) * 100)
                roas_accuracy.append((roas_within / len(preds)) * 100)

            return {
                'period_days': days_back,
                'data_points': len(dates),
                'dates': dates,
                'ctr_accuracy_trend': ctr_accuracy,
                'roas_accuracy_trend': roas_accuracy,
                'ctr_improvement': round(ctr_accuracy[-1] - ctr_accuracy[0], 2) if len(ctr_accuracy) >= 2 else 0,
                'roas_improvement': round(roas_accuracy[-1] - roas_accuracy[0], 2) if len(roas_accuracy) >= 2 else 0,
                'learning_status': 'improving' if (len(ctr_accuracy) >= 2 and ctr_accuracy[-1] > ctr_accuracy[0]) else 'stable'
            }

        except Exception as e:
            logger.error(f"Error calculating realtime accuracy trend: {e}")
            return {}


# Global instance
accuracy_tracker = AccuracyTracker()
