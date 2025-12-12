"""
Drift Detection System - Agent 10
==================================

Monitors ML model performance degradation due to changing data distributions.

Detects:
    - Feature drift (input distribution changes)
    - Prediction drift (output distribution changes)
    - Concept drift (model accuracy degradation)
    - Calibration drift (confidence vs accuracy mismatch)

Metrics:
    - Population Stability Index (PSI)
    - Kolmogorov-Smirnov Test (KS)
    - Statistical moments (mean, std, skew, kurtosis)
    - Model freshness indicators

Alerting:
    - Slack/email notifications
    - Severity levels (warning, critical, emergency)
    - Actionable recommendations

Created: 2025-12-12
"""

from .drift_detector import DriftDetector, get_drift_detector
from .feature_monitor import FeatureMonitor, get_feature_monitor
from .prediction_monitor import PredictionMonitor, get_prediction_monitor
from .alert_manager import AlertManager, get_alert_manager

__all__ = [
    'DriftDetector',
    'get_drift_detector',
    'FeatureMonitor',
    'get_feature_monitor',
    'PredictionMonitor',
    'get_prediction_monitor',
    'AlertManager',
    'get_alert_manager',
]
