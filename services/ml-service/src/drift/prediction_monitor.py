"""
Prediction Monitor - Track prediction distributions and calibration
===================================================================

Monitors:
    - Prediction distribution over time
    - Predicted vs actual outcomes (when feedback available)
    - Calibration drift (confidence vs accuracy mismatch)
    - Model freshness indicators

Features:
    - Real-time prediction tracking
    - Calibration curve analysis
    - Prediction drift detection
    - Expected Calibration Error (ECE)

Author: Agent 10
Created: 2025-12-12
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)


@dataclass
class PredictionSnapshot:
    """Snapshot of prediction statistics"""
    model_name: str
    mean_prediction: float
    std_prediction: float
    min_prediction: float
    max_prediction: float
    sample_count: int
    timestamp: datetime

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class CalibrationResult:
    """Calibration analysis result"""
    model_name: str
    is_calibrated: bool
    expected_calibration_error: float  # ECE
    calibration_bins: List[Dict[str, float]]
    drift_detected: bool
    severity: str  # 'none', 'warning', 'critical'
    recommendation: str


@dataclass
class PredictionDriftReport:
    """Prediction drift report"""
    model_name: str
    is_drifting: bool
    drift_magnitude: float
    baseline_mean: float
    current_mean: float
    baseline_std: float
    current_std: float
    prediction_shift: float  # In standard deviations
    recommendation: str


class PredictionMonitor:
    """
    Monitor model predictions and detect drift/calibration issues.

    Tracks prediction distributions and compares predicted vs actual
    outcomes to detect model degradation.
    """

    def __init__(
        self,
        window_size: int = 1000,
        calibration_bins: int = 10,
        ece_warning_threshold: float = 0.05,  # 5% ECE
        ece_critical_threshold: float = 0.10,  # 10% ECE
        prediction_shift_threshold: float = 2.0,  # 2 std devs
    ):
        """
        Initialize Prediction Monitor.

        Args:
            window_size: Rolling window size for predictions
            calibration_bins: Number of bins for calibration curve
            ece_warning_threshold: ECE threshold for warning
            ece_critical_threshold: ECE threshold for critical
            prediction_shift_threshold: Prediction shift threshold (std devs)
        """
        self.window_size = window_size
        self.calibration_bins = calibration_bins
        self.ece_warning_threshold = ece_warning_threshold
        self.ece_critical_threshold = ece_critical_threshold
        self.prediction_shift_threshold = prediction_shift_threshold

        # Storage for predictions and actuals
        self._prediction_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self._actual_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self._confidence_windows: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )

        # Baseline statistics
        self._baseline_stats: Dict[str, PredictionSnapshot] = {}

        # Historical snapshots
        self._prediction_history: Dict[str, List[PredictionSnapshot]] = defaultdict(list)

        logger.info(
            f"PredictionMonitor initialized: "
            f"window_size={window_size}, calibration_bins={calibration_bins}"
        )

    def set_baseline(
        self,
        model_name: str,
        baseline_predictions: np.ndarray
    ) -> PredictionSnapshot:
        """
        Set baseline prediction distribution.

        Args:
            model_name: Name of model
            baseline_predictions: Training/validation predictions

        Returns:
            PredictionSnapshot of baseline
        """
        snapshot = PredictionSnapshot(
            model_name=model_name,
            mean_prediction=float(np.mean(baseline_predictions)),
            std_prediction=float(np.std(baseline_predictions)),
            min_prediction=float(np.min(baseline_predictions)),
            max_prediction=float(np.max(baseline_predictions)),
            sample_count=len(baseline_predictions),
            timestamp=datetime.utcnow()
        )

        self._baseline_stats[model_name] = snapshot

        logger.info(
            f"Baseline set for {model_name}: "
            f"mean={snapshot.mean_prediction:.4f}, "
            f"std={snapshot.std_prediction:.4f}"
        )

        return snapshot

    def track_prediction(
        self,
        model_name: str,
        prediction: float,
        actual: Optional[float] = None,
        confidence: Optional[float] = None
    ):
        """
        Track a single prediction.

        Args:
            model_name: Name of model
            prediction: Predicted value
            actual: Actual outcome (if available)
            confidence: Model confidence score (0-1)
        """
        self._prediction_windows[model_name].append(prediction)

        if actual is not None:
            self._actual_windows[model_name].append(actual)

        if confidence is not None:
            self._confidence_windows[model_name].append(confidence)

    def track_batch(
        self,
        model_name: str,
        predictions: np.ndarray,
        actuals: Optional[np.ndarray] = None,
        confidences: Optional[np.ndarray] = None
    ):
        """
        Track a batch of predictions.

        Args:
            model_name: Name of model
            predictions: Array of predictions
            actuals: Array of actual outcomes (optional)
            confidences: Array of confidence scores (optional)
        """
        for i, pred in enumerate(predictions):
            actual = actuals[i] if actuals is not None else None
            confidence = confidences[i] if confidences is not None else None
            self.track_prediction(model_name, pred, actual, confidence)

        logger.debug(
            f"Tracked batch for {model_name}: {len(predictions)} predictions"
        )

    def check_prediction_drift(
        self,
        model_name: str
    ) -> Optional[PredictionDriftReport]:
        """
        Check if predictions have drifted from baseline.

        Args:
            model_name: Name of model to check

        Returns:
            PredictionDriftReport or None
        """
        if model_name not in self._baseline_stats:
            logger.warning(f"No baseline for {model_name}")
            return None

        if model_name not in self._prediction_windows:
            logger.warning(f"No predictions tracked for {model_name}")
            return None

        window = self._prediction_windows[model_name]
        if len(window) < 10:
            logger.warning(f"Insufficient predictions for {model_name}")
            return None

        # Calculate current stats
        current_preds = np.array(list(window))
        current_mean = float(np.mean(current_preds))
        current_std = float(np.std(current_preds))

        baseline = self._baseline_stats[model_name]

        # Calculate shift (in standard deviations)
        prediction_shift = abs(current_mean - baseline.mean_prediction) / max(
            baseline.std_prediction, 1e-10
        )

        # Determine if drifting
        is_drifting = prediction_shift > self.prediction_shift_threshold

        # Calculate drift magnitude (0-1 scale)
        drift_magnitude = min(
            prediction_shift / self.prediction_shift_threshold,
            1.0
        )

        # Generate recommendation
        recommendation = self._generate_prediction_drift_recommendation(
            model_name, is_drifting, prediction_shift, current_mean, baseline.mean_prediction
        )

        report = PredictionDriftReport(
            model_name=model_name,
            is_drifting=is_drifting,
            drift_magnitude=drift_magnitude,
            baseline_mean=baseline.mean_prediction,
            current_mean=current_mean,
            baseline_std=baseline.std_prediction,
            current_std=current_std,
            prediction_shift=prediction_shift,
            recommendation=recommendation
        )

        logger.info(
            f"Prediction drift check for {model_name}: "
            f"drifting={is_drifting}, shift={prediction_shift:.2f}σ"
        )

        return report

    def check_calibration(
        self,
        model_name: str
    ) -> Optional[CalibrationResult]:
        """
        Check model calibration (predicted probabilities vs actual outcomes).

        Calibration measures whether predicted probabilities match actual
        frequencies. E.g., if model predicts 70% probability, we expect
        ~70% of those predictions to be correct.

        Args:
            model_name: Name of model to check

        Returns:
            CalibrationResult or None
        """
        # Need both predictions and actuals
        if model_name not in self._prediction_windows:
            logger.warning(f"No predictions for {model_name}")
            return None

        if model_name not in self._actual_windows:
            logger.warning(f"No actuals for {model_name}")
            return None

        preds = np.array(list(self._prediction_windows[model_name]))
        actuals = np.array(list(self._actual_windows[model_name]))

        # Must have same length
        min_len = min(len(preds), len(actuals))
        if min_len < 50:
            logger.warning(f"Insufficient prediction-actual pairs for {model_name}")
            return None

        preds = preds[-min_len:]
        actuals = actuals[-min_len:]

        # Calculate calibration curve
        calibration_data = self._calculate_calibration_curve(
            preds, actuals, bins=self.calibration_bins
        )

        # Calculate Expected Calibration Error (ECE)
        ece = self._calculate_ece(calibration_data)

        # Determine calibration status
        is_calibrated = ece < self.ece_warning_threshold
        drift_detected = ece >= self.ece_warning_threshold

        if ece >= self.ece_critical_threshold:
            severity = 'critical'
            recommendation = (
                f"CRITICAL CALIBRATION DRIFT (ECE={ece:.3f})! "
                f"Model confidence scores are unreliable. "
                f"IMMEDIATE ACTION: Recalibrate model or retrain."
            )
        elif ece >= self.ece_warning_threshold:
            severity = 'warning'
            recommendation = (
                f"Calibration drift detected (ECE={ece:.3f}). "
                f"Model confidence scores may be biased. "
                f"Consider recalibration (Platt scaling, isotonic regression)."
            )
        else:
            severity = 'none'
            recommendation = (
                f"Model well-calibrated (ECE={ece:.3f}). "
                f"Confidence scores are reliable."
            )

        result = CalibrationResult(
            model_name=model_name,
            is_calibrated=is_calibrated,
            expected_calibration_error=ece,
            calibration_bins=calibration_data,
            drift_detected=drift_detected,
            severity=severity,
            recommendation=recommendation
        )

        logger.info(
            f"Calibration check for {model_name}: "
            f"ECE={ece:.3f}, severity={severity}"
        )

        return result

    def get_prediction_accuracy(
        self,
        model_name: str,
        metric: str = 'mae'  # 'mae', 'mse', 'rmse'
    ) -> Optional[float]:
        """
        Calculate prediction accuracy (requires actuals).

        Args:
            model_name: Name of model
            metric: Metric to calculate ('mae', 'mse', 'rmse')

        Returns:
            Accuracy metric or None
        """
        if model_name not in self._prediction_windows:
            return None
        if model_name not in self._actual_windows:
            return None

        preds = np.array(list(self._prediction_windows[model_name]))
        actuals = np.array(list(self._actual_windows[model_name]))

        # Must have same length
        min_len = min(len(preds), len(actuals))
        if min_len < 10:
            return None

        preds = preds[-min_len:]
        actuals = actuals[-min_len:]

        errors = preds - actuals

        if metric == 'mae':
            return float(np.mean(np.abs(errors)))
        elif metric == 'mse':
            return float(np.mean(errors ** 2))
        elif metric == 'rmse':
            return float(np.sqrt(np.mean(errors ** 2)))
        else:
            raise ValueError(f"Unknown metric: {metric}")

    def get_model_freshness(
        self,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Calculate model freshness indicators.

        Freshness indicates how recently the model was trained and
        how much the data has changed since training.

        Args:
            model_name: Name of model

        Returns:
            Freshness metrics
        """
        if model_name not in self._baseline_stats:
            return {"error": "No baseline available"}

        baseline = self._baseline_stats[model_name]
        age_days = (datetime.utcnow() - baseline.timestamp).days

        # Check if predictions are drifting
        drift_report = self.check_prediction_drift(model_name)
        is_drifting = drift_report.is_drifting if drift_report else False

        # Calculate accuracy if actuals available
        current_mae = self.get_prediction_accuracy(model_name, 'mae')

        # Determine freshness status
        if age_days > 30 and is_drifting:
            status = 'stale'
            recommendation = "Model is stale and drifting. Retrain immediately."
        elif age_days > 14:
            status = 'aging'
            recommendation = "Model is aging. Schedule retraining soon."
        elif is_drifting:
            status = 'drifting'
            recommendation = "Model is recent but drifting. Investigate data changes."
        else:
            status = 'fresh'
            recommendation = "Model is fresh and stable."

        return {
            "model_name": model_name,
            "status": status,
            "baseline_age_days": age_days,
            "is_drifting": is_drifting,
            "current_mae": current_mae,
            "recommendation": recommendation,
            "checked_at": datetime.utcnow().isoformat()
        }

    def snapshot_predictions(
        self,
        model_name: str
    ) -> Optional[PredictionSnapshot]:
        """
        Create snapshot of current prediction statistics.

        Args:
            model_name: Name of model

        Returns:
            PredictionSnapshot or None
        """
        if model_name not in self._prediction_windows:
            return None

        window = self._prediction_windows[model_name]
        if len(window) < 10:
            return None

        preds = np.array(list(window))

        snapshot = PredictionSnapshot(
            model_name=model_name,
            mean_prediction=float(np.mean(preds)),
            std_prediction=float(np.std(preds)),
            min_prediction=float(np.min(preds)),
            max_prediction=float(np.max(preds)),
            sample_count=len(preds),
            timestamp=datetime.utcnow()
        )

        # Add to history
        self._prediction_history[model_name].append(snapshot)

        return snapshot

    def get_prediction_trend(
        self,
        model_name: str,
        hours: int = 24
    ) -> List[PredictionSnapshot]:
        """
        Get historical prediction trend.

        Args:
            model_name: Name of model
            hours: Hours of history

        Returns:
            List of historical snapshots
        """
        if model_name not in self._prediction_history:
            return []

        cutoff = datetime.utcnow() - timedelta(hours=hours)

        trend = [
            snapshot for snapshot in self._prediction_history[model_name]
            if snapshot.timestamp >= cutoff
        ]

        return sorted(trend, key=lambda s: s.timestamp)

    # Helper methods

    def _calculate_calibration_curve(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
        bins: int = 10
    ) -> List[Dict[str, float]]:
        """
        Calculate calibration curve.

        Returns list of bins with predicted vs actual frequencies.
        """
        # Bin predictions
        bin_edges = np.linspace(0, 1, bins + 1)
        bin_indices = np.digitize(predictions, bin_edges[:-1]) - 1
        bin_indices = np.clip(bin_indices, 0, bins - 1)

        calibration_data = []

        for i in range(bins):
            mask = bin_indices == i
            if not mask.any():
                continue

            bin_preds = predictions[mask]
            bin_actuals = actuals[mask]

            avg_predicted = float(np.mean(bin_preds))
            avg_actual = float(np.mean(bin_actuals))
            count = int(mask.sum())

            calibration_data.append({
                "bin": i,
                "predicted_probability": avg_predicted,
                "actual_frequency": avg_actual,
                "count": count,
                "calibration_error": abs(avg_predicted - avg_actual)
            })

        return calibration_data

    def _calculate_ece(
        self,
        calibration_data: List[Dict[str, float]]
    ) -> float:
        """
        Calculate Expected Calibration Error (ECE).

        ECE is the weighted average of calibration errors across bins.
        """
        if not calibration_data:
            return 0.0

        total_count = sum(bin_data["count"] for bin_data in calibration_data)

        ece = sum(
            (bin_data["count"] / total_count) * bin_data["calibration_error"]
            for bin_data in calibration_data
        )

        return float(ece)

    def _generate_prediction_drift_recommendation(
        self,
        model_name: str,
        is_drifting: bool,
        shift: float,
        current_mean: float,
        baseline_mean: float
    ) -> str:
        """Generate recommendation for prediction drift."""
        if not is_drifting:
            return f"{model_name} predictions are stable. No action needed."

        direction = "higher" if current_mean > baseline_mean else "lower"

        if shift > 3.0:
            return (
                f"{model_name} predictions shifted significantly ({shift:.1f}σ {direction}). "
                f"CRITICAL: Model behavior changed drastically. "
                f"Stop model, investigate, retrain immediately."
            )
        else:
            return (
                f"{model_name} predictions drifting ({shift:.1f}σ {direction}). "
                f"Model adapting to changing patterns. Monitor closely. "
                f"Consider retraining if drift persists."
            )


# Singleton instance
_prediction_monitor_instance = None


def get_prediction_monitor() -> PredictionMonitor:
    """Get or create PredictionMonitor singleton."""
    global _prediction_monitor_instance
    if _prediction_monitor_instance is None:
        _prediction_monitor_instance = PredictionMonitor()
    return _prediction_monitor_instance
