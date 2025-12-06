"""
Prediction Accuracy Tracker

Tracks prediction accuracy over time to:
1. Know when models are right/wrong
2. Detect model drift
3. Trigger retraining when accuracy drops
4. Build confidence in predictions

Without this: Blind predictions, no feedback
With this: Self-improving predictions
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import numpy as np
from enum import Enum

logger = logging.getLogger(__name__)

class MetricType(Enum):
    CTR = "ctr"
    CVR = "cvr"
    CPA = "cpa"
    ROAS = "roas"
    CONVERSIONS = "conversions"

@dataclass
class PredictionRecord:
    """A single prediction with its actual outcome"""
    prediction_id: str
    model_type: str
    model_version: str

    # Predictions
    predicted_value: float
    confidence: float

    # Actuals (filled in later)
    actual_value: Optional[float] = None

    # Metadata
    campaign_id: str = ""
    creative_id: str = ""
    metric_type: MetricType = MetricType.ROAS

    # Timestamps
    predicted_at: datetime = field(default_factory=datetime.now)
    actual_recorded_at: Optional[datetime] = None

    # Calculated
    error: Optional[float] = None
    error_percent: Optional[float] = None
    is_accurate: Optional[bool] = None  # Within acceptable range

@dataclass
class AccuracyReport:
    """Accuracy report for a model over a time period"""
    model_type: str
    model_version: str
    period_start: datetime
    period_end: datetime

    # Counts
    total_predictions: int
    predictions_with_actuals: int
    accurate_predictions: int

    # Accuracy metrics
    accuracy_rate: float  # % of predictions within acceptable range
    mean_absolute_error: float
    mean_absolute_percentage_error: float
    root_mean_squared_error: float

    # Trend
    accuracy_trend: str  # 'improving', 'stable', 'declining'

    # Recommendation
    needs_retraining: bool
    confidence_adjustment: float  # How much to adjust confidence

class PredictionAccuracyTracker:
    """
    Tracks prediction accuracy to ensure model reliability.

    Key features:
    - Store predictions with actual outcomes
    - Calculate accuracy metrics
    - Detect model drift
    - Recommend retraining
    - Adjust confidence based on history
    """

    # Accuracy thresholds
    ACCEPTABLE_ERROR_PERCENT = {
        MetricType.CTR: 0.25,    # 25% error acceptable
        MetricType.CVR: 0.30,    # 30% error acceptable
        MetricType.CPA: 0.35,    # 35% error acceptable
        MetricType.ROAS: 0.30,   # 30% error acceptable
        MetricType.CONVERSIONS: 0.40  # 40% error acceptable
    }

    # Retraining thresholds
    RETRAIN_ACCURACY_THRESHOLD = 0.6  # Retrain if accuracy below 60%
    MIN_SAMPLES_FOR_REPORT = 20

    def __init__(self):
        self.predictions: Dict[str, PredictionRecord] = {}
        self.accuracy_history: List[AccuracyReport] = []

    def record_prediction(self,
                          prediction_id: str,
                          model_type: str,
                          model_version: str,
                          predicted_value: float,
                          confidence: float,
                          metric_type: MetricType,
                          campaign_id: str = "",
                          creative_id: str = "") -> PredictionRecord:
        """Record a new prediction"""
        record = PredictionRecord(
            prediction_id=prediction_id,
            model_type=model_type,
            model_version=model_version,
            predicted_value=predicted_value,
            confidence=confidence,
            metric_type=metric_type,
            campaign_id=campaign_id,
            creative_id=creative_id,
            predicted_at=datetime.now()
        )

        self.predictions[prediction_id] = record
        logger.info(f"Recorded prediction {prediction_id}: {predicted_value}")

        return record

    def record_actual(self, prediction_id: str, actual_value: float) -> Optional[PredictionRecord]:
        """Record actual outcome for a prediction"""
        if prediction_id not in self.predictions:
            logger.warning(f"Prediction {prediction_id} not found")
            return None

        record = self.predictions[prediction_id]
        record.actual_value = actual_value
        record.actual_recorded_at = datetime.now()

        # Calculate error
        if record.predicted_value != 0:
            record.error = abs(actual_value - record.predicted_value)
            record.error_percent = record.error / abs(record.predicted_value)
        else:
            record.error = abs(actual_value)
            record.error_percent = 1.0 if actual_value != 0 else 0.0

        # Check if accurate
        threshold = self.ACCEPTABLE_ERROR_PERCENT.get(record.metric_type, 0.30)
        record.is_accurate = record.error_percent <= threshold

        logger.info(f"Recorded actual for {prediction_id}: {actual_value} (error: {record.error_percent:.2%})")

        return record

    def get_accuracy_report(self,
                            model_type: str = None,
                            model_version: str = None,
                            days: int = 7) -> AccuracyReport:
        """Generate accuracy report for a model"""
        cutoff = datetime.now() - timedelta(days=days)

        # Filter predictions
        records = [
            r for r in self.predictions.values()
            if r.predicted_at >= cutoff
            and r.actual_value is not None
            and (model_type is None or r.model_type == model_type)
            and (model_version is None or r.model_version == model_version)
        ]

        if len(records) < self.MIN_SAMPLES_FOR_REPORT:
            return AccuracyReport(
                model_type=model_type or "all",
                model_version=model_version or "all",
                period_start=cutoff,
                period_end=datetime.now(),
                total_predictions=len(records),
                predictions_with_actuals=len(records),
                accurate_predictions=0,
                accuracy_rate=0,
                mean_absolute_error=0,
                mean_absolute_percentage_error=0,
                root_mean_squared_error=0,
                accuracy_trend="unknown",
                needs_retraining=False,
                confidence_adjustment=0
            )

        # Calculate metrics
        errors = [r.error for r in records if r.error is not None]
        error_percents = [r.error_percent for r in records if r.error_percent is not None]
        accurate_count = sum(1 for r in records if r.is_accurate)

        mae = np.mean(errors) if errors else 0
        mape = np.mean(error_percents) if error_percents else 0
        rmse = np.sqrt(np.mean([e**2 for e in errors])) if errors else 0
        accuracy_rate = accurate_count / len(records) if records else 0

        # Determine trend
        accuracy_trend = self._calculate_trend(model_type, accuracy_rate)

        # Check if retraining needed
        needs_retraining = accuracy_rate < self.RETRAIN_ACCURACY_THRESHOLD

        # Calculate confidence adjustment
        confidence_adjustment = self._calculate_confidence_adjustment(accuracy_rate)

        report = AccuracyReport(
            model_type=model_type or "all",
            model_version=model_version or "all",
            period_start=cutoff,
            period_end=datetime.now(),
            total_predictions=len([r for r in self.predictions.values() if r.predicted_at >= cutoff]),
            predictions_with_actuals=len(records),
            accurate_predictions=accurate_count,
            accuracy_rate=accuracy_rate,
            mean_absolute_error=mae,
            mean_absolute_percentage_error=mape,
            root_mean_squared_error=rmse,
            accuracy_trend=accuracy_trend,
            needs_retraining=needs_retraining,
            confidence_adjustment=confidence_adjustment
        )

        self.accuracy_history.append(report)

        return report

    def _calculate_trend(self, model_type: str, current_accuracy: float) -> str:
        """Calculate accuracy trend"""
        relevant_history = [
            r for r in self.accuracy_history[-5:]
            if r.model_type == model_type
        ]

        if len(relevant_history) < 2:
            return "stable"

        avg_historical = np.mean([r.accuracy_rate for r in relevant_history])

        if current_accuracy > avg_historical * 1.1:
            return "improving"
        elif current_accuracy < avg_historical * 0.9:
            return "declining"
        return "stable"

    def _calculate_confidence_adjustment(self, accuracy_rate: float) -> float:
        """Calculate how much to adjust model confidence"""
        # If accuracy is high, boost confidence
        # If accuracy is low, reduce confidence
        if accuracy_rate >= 0.8:
            return 0.1  # Boost 10%
        elif accuracy_rate >= 0.7:
            return 0.0  # No change
        elif accuracy_rate >= 0.6:
            return -0.1  # Reduce 10%
        else:
            return -0.2  # Reduce 20%

    def get_prediction_history(self, campaign_id: str = None,
                               limit: int = 100) -> List[Dict]:
        """Get prediction history with outcomes"""
        records = list(self.predictions.values())

        if campaign_id:
            records = [r for r in records if r.campaign_id == campaign_id]

        # Sort by prediction time
        records.sort(key=lambda r: r.predicted_at, reverse=True)

        return [
            {
                'prediction_id': r.prediction_id,
                'model_type': r.model_type,
                'predicted': r.predicted_value,
                'actual': r.actual_value,
                'error_percent': r.error_percent,
                'is_accurate': r.is_accurate,
                'predicted_at': r.predicted_at.isoformat()
            }
            for r in records[:limit]
        ]

    def should_retrain(self, model_type: str) -> Tuple[bool, str]:
        """Check if model should be retrained"""
        report = self.get_accuracy_report(model_type=model_type)

        if report.predictions_with_actuals < self.MIN_SAMPLES_FOR_REPORT:
            return False, "Not enough data for assessment"

        if report.needs_retraining:
            return True, f"Accuracy {report.accuracy_rate:.1%} below threshold {self.RETRAIN_ACCURACY_THRESHOLD:.1%}"

        if report.accuracy_trend == "declining":
            return True, "Accuracy trend is declining"

        return False, "Model accuracy is acceptable"

    def get_dashboard_metrics(self) -> Dict:
        """Get metrics for monitoring dashboard"""
        total_predictions = len(self.predictions)
        with_actuals = len([p for p in self.predictions.values() if p.actual_value is not None])
        accurate = len([p for p in self.predictions.values() if p.is_accurate])

        return {
            'total_predictions': total_predictions,
            'predictions_with_outcomes': with_actuals,
            'overall_accuracy': accurate / with_actuals if with_actuals > 0 else 0,
            'pending_outcomes': total_predictions - with_actuals,
            'models_tracked': len(set(p.model_type for p in self.predictions.values())),
            'latest_reports': [
                {
                    'model': r.model_type,
                    'accuracy': r.accuracy_rate,
                    'trend': r.accuracy_trend
                }
                for r in self.accuracy_history[-5:]
            ]
        }
