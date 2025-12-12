"""
Model Integrations - Wire drift detection to existing models
============================================================

Integration hooks for:
    - CTR Model
    - Creative DNA
    - Battle-Hardened Sampler

Usage:
    Import this module in your model files and call integration functions.

Author: Agent 10
Created: 2025-12-12
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, List

from .drift_detector import get_drift_detector
from .feature_monitor import get_feature_monitor
from .prediction_monitor import get_prediction_monitor
from .alert_manager import get_alert_manager

logger = logging.getLogger(__name__)


class DriftIntegrationMixin:
    """
    Mixin class to add drift detection to ML models.

    Usage:
        class YourModel(DriftIntegrationMixin):
            def __init__(self):
                super().__init__()
                self.init_drift_monitoring('your_model_name')
    """

    def init_drift_monitoring(
        self,
        model_name: str,
        monitor_features: bool = True,
        monitor_predictions: bool = True
    ):
        """
        Initialize drift monitoring for this model.

        Args:
            model_name: Name of model
            monitor_features: Whether to monitor input features
            monitor_predictions: Whether to monitor predictions
        """
        self._model_name = model_name
        self._monitor_features = monitor_features
        self._monitor_predictions = monitor_predictions

        # Get monitoring instances
        self._drift_detector = get_drift_detector() if monitor_features else None
        self._feature_monitor = get_feature_monitor() if monitor_features else None
        self._prediction_monitor = get_prediction_monitor() if monitor_predictions else None
        self._alert_manager = get_alert_manager()

        logger.info(
            f"Drift monitoring initialized for {model_name}: "
            f"features={monitor_features}, predictions={monitor_predictions}"
        )

    def set_training_baseline(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        feature_names: Optional[List[str]] = None
    ):
        """
        Set baseline distributions from training data.

        Call this after training your model.

        Args:
            X_train: Training features
            y_train: Training predictions
            feature_names: List of feature names
        """
        if not hasattr(self, '_model_name'):
            logger.warning("Drift monitoring not initialized. Call init_drift_monitoring() first.")
            return

        logger.info(f"Setting training baseline for {self._model_name}")

        # Set feature baselines
        if self._feature_monitor and X_train is not None:
            if feature_names:
                for i, feature_name in enumerate(feature_names):
                    self._feature_monitor.set_baseline(
                        feature_name=feature_name,
                        baseline_values=X_train[:, i]
                    )
            else:
                # Use generic feature names
                for i in range(X_train.shape[1]):
                    self._feature_monitor.set_baseline(
                        feature_name=f"feature_{i}",
                        baseline_values=X_train[:, i]
                    )

        # Set prediction baseline
        if self._prediction_monitor and y_train is not None:
            self._prediction_monitor.set_baseline(
                model_name=self._model_name,
                baseline_predictions=y_train
            )

        logger.info(f"Training baseline set for {self._model_name}")

    def track_prediction(
        self,
        features: np.ndarray,
        prediction: float,
        actual: Optional[float] = None,
        feature_names: Optional[List[str]] = None
    ):
        """
        Track a single prediction for drift monitoring.

        Call this every time you make a prediction.

        Args:
            features: Input features
            prediction: Model prediction
            actual: Actual outcome (if available)
            feature_names: Feature names (optional)
        """
        if not hasattr(self, '_model_name'):
            return

        # Track features
        if self._feature_monitor:
            if feature_names:
                feature_dict = {
                    name: float(features[i])
                    for i, name in enumerate(feature_names)
                }
            else:
                feature_dict = {
                    f"feature_{i}": float(features[i])
                    for i in range(len(features))
                }
            self._feature_monitor.track_features(feature_dict)

        # Track prediction
        if self._prediction_monitor:
            self._prediction_monitor.track_prediction(
                model_name=self._model_name,
                prediction=prediction,
                actual=actual
            )

    def check_drift_status(self) -> Dict[str, Any]:
        """
        Check current drift status.

        Returns:
            Dict with drift status for features and predictions
        """
        if not hasattr(self, '_model_name'):
            return {"error": "Drift monitoring not initialized"}

        status = {
            "model_name": self._model_name,
            "feature_drift": {},
            "prediction_drift": {},
            "alerts": []
        }

        # Check feature drift
        if self._feature_monitor:
            feature_reports = self._feature_monitor.check_all_features(
                create_histograms=False
            )
            status["feature_drift"] = {
                "total_features": len(feature_reports),
                "drifting_features": sum(1 for r in feature_reports if r.is_drifting),
                "top_drifting": [
                    {
                        "feature": r.feature_name,
                        "drift_magnitude": r.drift_magnitude,
                        "recommendation": r.recommendation
                    }
                    for r in sorted(feature_reports, key=lambda x: x.drift_magnitude, reverse=True)[:5]
                ]
            }

        # Check prediction drift
        if self._prediction_monitor:
            pred_report = self._prediction_monitor.check_prediction_drift(self._model_name)
            if pred_report:
                status["prediction_drift"] = {
                    "is_drifting": pred_report.is_drifting,
                    "drift_magnitude": pred_report.drift_magnitude,
                    "prediction_shift": pred_report.prediction_shift,
                    "recommendation": pred_report.recommendation
                }

        return status


# CTR Model Integration

def integrate_drift_into_ctr_model():
    """
    Integration example for CTR Model.

    Add this to ctr_model.py:

    from src.drift.model_integrations import DriftIntegrationMixin

    class CTRPredictor(DriftIntegrationMixin):
        def __init__(self, model_path='models/ctr_model.pkl'):
            # ... existing init code ...
            self.init_drift_monitoring('ctr_model')

        def train(self, X, y, feature_names=None, ...):
            # ... existing train code ...
            # After training:
            self.set_training_baseline(X, y, feature_names)

        def predict(self, X, use_cache=True):
            predictions = self.model.predict(X)
            # Track predictions for drift monitoring
            for i, pred in enumerate(predictions):
                self.track_prediction(
                    features=X[i],
                    prediction=pred,
                    feature_names=self.feature_names
                )
            return predictions
    """
    pass


def integrate_drift_into_creative_dna():
    """
    Integration example for Creative DNA.

    Add this to creative_dna.py:

    from src.drift.model_integrations import get_feature_monitor, get_alert_manager

    class CreativeDNA:
        def __init__(self, database_service=None):
            # ... existing init code ...
            self.feature_monitor = get_feature_monitor()
            self.alert_manager = get_alert_manager()

        async def build_winning_formula(self, account_id, ...):
            # ... existing code ...
            formula = { ... }

            # Track formula features for drift
            self.feature_monitor.set_baseline(
                f"formula_{account_id}_hook_score",
                np.array([f["avg_performance"] for f in formula["hook_patterns"]])
            )

            return formula
    """
    pass


def integrate_drift_into_battle_hardened_sampler():
    """
    Integration example for Battle-Hardened Sampler.

    Add this to battle_hardened_sampler.py:

    from src.drift.model_integrations import get_prediction_monitor, get_alert_manager

    class BattleHardenedSampler:
        def __init__(self, ...):
            # ... existing init code ...
            self.prediction_monitor = get_prediction_monitor()
            self.alert_manager = get_alert_manager()

        def _calculate_blended_score(self, ad, ...):
            # ... existing code ...
            score = { ... }

            # Track blended scores for drift
            self.prediction_monitor.track_prediction(
                model_name='battle_hardened_sampler',
                prediction=score['final_score'],
                actual=None  # Will be filled when actuals arrive
            )

            return score

        def register_feedback(self, ad_id, actual_pipeline_value, ...):
            # ... existing code ...
            # Update prediction monitor with actual
            self.prediction_monitor.track_prediction(
                model_name='battle_hardened_sampler',
                prediction=None,  # Already tracked
                actual=actual_pipeline_value / max(actual_spend, 0.01)
            )
    """
    pass


# Utility functions for integration

def check_model_drift(model_name: str) -> Dict[str, Any]:
    """
    Quick drift check for any model.

    Args:
        model_name: Name of model to check

    Returns:
        Drift status
    """
    feature_monitor = get_feature_monitor()
    prediction_monitor = get_prediction_monitor()

    status = {
        "model_name": model_name,
        "checked_at": np.datetime64('now').isoformat(),
        "feature_drift": None,
        "prediction_drift": None,
        "recommendation": None
    }

    # Check prediction drift
    pred_report = prediction_monitor.check_prediction_drift(model_name)
    if pred_report:
        status["prediction_drift"] = {
            "is_drifting": pred_report.is_drifting,
            "drift_magnitude": pred_report.drift_magnitude,
            "recommendation": pred_report.recommendation
        }

    # Check calibration
    calibration = prediction_monitor.check_calibration(model_name)
    if calibration:
        status["calibration"] = {
            "is_calibrated": calibration.is_calibrated,
            "ece": calibration.expected_calibration_error,
            "recommendation": calibration.recommendation
        }

    # Overall recommendation
    if status["prediction_drift"] and status["prediction_drift"]["is_drifting"]:
        if status["prediction_drift"]["drift_magnitude"] > 0.8:
            status["recommendation"] = "CRITICAL: Retrain model immediately"
        else:
            status["recommendation"] = "WARNING: Monitor closely, retrain soon"
    else:
        status["recommendation"] = "Model is stable"

    return status


def set_model_baseline_from_db(
    model_name: str,
    training_data_query: str,
    feature_columns: List[str],
    target_column: str
):
    """
    Set model baseline from database query.

    Args:
        model_name: Name of model
        training_data_query: SQL query to get training data
        feature_columns: List of feature column names
        target_column: Target column name
    """
    import pandas as pd
    from src.data_loader import get_data_loader

    data_loader = get_data_loader()
    if not data_loader:
        logger.warning("Database not available")
        return

    # Query training data
    df = pd.read_sql(training_data_query, data_loader.connection)

    # Extract features and target
    X = df[feature_columns].values
    y = df[target_column].values

    # Set baselines
    feature_monitor = get_feature_monitor()
    prediction_monitor = get_prediction_monitor()

    # Feature baselines
    for i, col in enumerate(feature_columns):
        feature_monitor.set_baseline(col, X[:, i])

    # Prediction baseline
    prediction_monitor.set_baseline(model_name, y)

    logger.info(
        f"Baseline set for {model_name} from database: "
        f"{len(feature_columns)} features, {len(y)} samples"
    )
