"""
Drift Detection Celery Tasks - Agent 10
========================================

Scheduled tasks for drift monitoring:
    - Daily PSI checks
    - Weekly comprehensive analysis
    - Hourly prediction monitoring
    - Alert dispatch on drift detection

Author: Agent 10
Created: 2025-12-12
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import numpy as np

from src.celery_app import celery_app
from .drift_detector import get_drift_detector
from .feature_monitor import get_feature_monitor
from .prediction_monitor import get_prediction_monitor
from .alert_manager import get_alert_manager

logger = logging.getLogger(__name__)


@celery_app.task(name='check_drift_daily', bind=True)
def check_drift_daily(self) -> Dict[str, Any]:
    """
    Daily drift check using PSI.

    Runs every day to check for feature and prediction drift across
    all models. Sends alerts if drift detected.

    Returns:
        Summary of drift checks
    """
    logger.info("Starting daily drift check...")

    try:
        drift_detector = get_drift_detector()
        feature_monitor = get_feature_monitor()
        prediction_monitor = get_prediction_monitor()
        alert_manager = get_alert_manager()

        results = {
            "check_type": "daily",
            "timestamp": datetime.utcnow().isoformat(),
            "models_checked": [],
            "drift_detected": [],
            "alerts_sent": []
        }

        # Get list of models to check (in production, query from database)
        models_to_check = _get_active_models()

        for model_name in models_to_check:
            logger.info(f"Checking drift for model: {model_name}")

            model_result = {
                "model_name": model_name,
                "features_checked": 0,
                "features_drifted": 0,
                "predictions_drifted": False,
                "alerts": []
            }

            # Check feature drift
            feature_reports = feature_monitor.check_all_features()
            model_result["features_checked"] = len(feature_reports)

            for report in feature_reports:
                if report.is_drifting:
                    model_result["features_drifted"] += 1

                    # Send alert for critical drift
                    if report.drift_magnitude > 0.7:  # High drift
                        alert = alert_manager.send_feature_drift_alert(
                            model_name=model_name,
                            feature_name=report.feature_name,
                            drift_score=report.drift_magnitude,
                            mean_shift=report.mean_shift,
                            std_shift=report.std_shift,
                            severity='critical' if report.drift_magnitude > 0.85 else 'warning',
                            recommendation=report.recommendation
                        )
                        if alert:
                            model_result["alerts"].append(alert.alert_id)
                            results["alerts_sent"].append({
                                "alert_id": alert.alert_id,
                                "model": model_name,
                                "feature": report.feature_name,
                                "severity": alert.severity.value
                            })

            # Check prediction drift
            pred_report = prediction_monitor.check_prediction_drift(model_name)
            if pred_report and pred_report.is_drifting:
                model_result["predictions_drifted"] = True

                if pred_report.drift_magnitude > 0.6:
                    alert = alert_manager.send_prediction_drift_alert(
                        model_name=model_name,
                        drift_score=pred_report.drift_magnitude,
                        prediction_shift=pred_report.prediction_shift,
                        severity='critical' if pred_report.drift_magnitude > 0.8 else 'warning',
                        recommendation=pred_report.recommendation
                    )
                    if alert:
                        model_result["alerts"].append(alert.alert_id)
                        results["alerts_sent"].append({
                            "alert_id": alert.alert_id,
                            "model": model_name,
                            "type": "prediction_drift",
                            "severity": alert.severity.value
                        })

            if model_result["features_drifted"] > 0 or model_result["predictions_drifted"]:
                results["drift_detected"].append(model_result)

            results["models_checked"].append(model_name)

        logger.info(
            f"Daily drift check complete: "
            f"{len(results['models_checked'])} models checked, "
            f"{len(results['drift_detected'])} with drift, "
            f"{len(results['alerts_sent'])} alerts sent"
        )

        return results

    except Exception as e:
        logger.error(f"Error in daily drift check: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='check_drift_weekly', bind=True)
def check_drift_weekly(self) -> Dict[str, Any]:
    """
    Weekly comprehensive drift analysis.

    Runs every week to perform deep analysis including:
        - Multivariate drift detection
        - Calibration analysis
        - Model freshness assessment
        - Trend analysis

    Returns:
        Comprehensive drift report
    """
    logger.info("Starting weekly comprehensive drift analysis...")

    try:
        drift_detector = get_drift_detector()
        feature_monitor = get_feature_monitor()
        prediction_monitor = get_prediction_monitor()
        alert_manager = get_alert_manager()

        results = {
            "check_type": "weekly_comprehensive",
            "timestamp": datetime.utcnow().isoformat(),
            "models_analyzed": [],
            "recommendations": []
        }

        models_to_check = _get_active_models()

        for model_name in models_to_check:
            logger.info(f"Comprehensive analysis for: {model_name}")

            analysis = {
                "model_name": model_name,
                "feature_drift": {},
                "prediction_drift": {},
                "calibration": {},
                "freshness": {},
                "recommendations": []
            }

            # Feature drift analysis
            top_drifting = feature_monitor.get_top_drifting_features(n=10)
            analysis["feature_drift"] = {
                "top_drifting_features": [
                    {
                        "feature": r.feature_name,
                        "drift_magnitude": r.drift_magnitude,
                        "mean_shift": r.mean_shift,
                        "std_shift": r.std_shift
                    }
                    for r in top_drifting
                ],
                "total_drifting": sum(1 for r in top_drifting if r.is_drifting)
            }

            # Prediction drift analysis
            pred_report = prediction_monitor.check_prediction_drift(model_name)
            if pred_report:
                analysis["prediction_drift"] = {
                    "is_drifting": pred_report.is_drifting,
                    "drift_magnitude": pred_report.drift_magnitude,
                    "prediction_shift": pred_report.prediction_shift
                }

            # Calibration analysis
            calibration = prediction_monitor.check_calibration(model_name)
            if calibration:
                analysis["calibration"] = {
                    "is_calibrated": calibration.is_calibrated,
                    "ece": calibration.expected_calibration_error,
                    "severity": calibration.severity
                }

                # Send calibration alert if needed
                if calibration.drift_detected:
                    alert = alert_manager.send_calibration_drift_alert(
                        model_name=model_name,
                        ece=calibration.expected_calibration_error,
                        severity=calibration.severity,
                        recommendation=calibration.recommendation
                    )
                    if alert:
                        analysis["recommendations"].append({
                            "type": "calibration",
                            "alert_id": alert.alert_id,
                            "recommendation": calibration.recommendation
                        })

            # Model freshness
            freshness = prediction_monitor.get_model_freshness(model_name)
            analysis["freshness"] = freshness

            if freshness.get("status") in ['stale', 'aging']:
                analysis["recommendations"].append({
                    "type": "freshness",
                    "status": freshness["status"],
                    "recommendation": freshness["recommendation"]
                })

            # Generate overall recommendations
            if analysis["recommendations"]:
                results["recommendations"].append({
                    "model_name": model_name,
                    "recommendations": analysis["recommendations"]
                })

            results["models_analyzed"].append(analysis)

        logger.info(
            f"Weekly drift analysis complete: "
            f"{len(results['models_analyzed'])} models analyzed"
        )

        return results

    except Exception as e:
        logger.error(f"Error in weekly drift analysis: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='alert_on_drift', bind=True)
def alert_on_drift(
    self,
    model_name: str,
    drift_type: str,
    metric_name: str,
    drift_score: float,
    severity: str,
    details: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send drift alert (can be triggered by other tasks).

    Args:
        model_name: Name of model
        drift_type: Type of drift
        metric_name: Name of drifted metric
        drift_score: Drift score
        severity: Severity level
        details: Additional details

    Returns:
        Alert result
    """
    logger.info(
        f"Sending drift alert: {model_name}/{metric_name} - {severity}"
    )

    try:
        alert_manager = get_alert_manager()

        # Generate message and recommendation based on drift type
        if drift_type == 'feature':
            message = (
                f"Feature drift detected in {model_name}: "
                f"{metric_name} has drifted (score={drift_score:.3f})"
            )
            recommendation = details.get('recommendation', 'Investigate feature and retrain model.')

        elif drift_type == 'prediction':
            message = (
                f"Prediction drift detected in {model_name}: "
                f"Predictions have shifted (score={drift_score:.3f})"
            )
            recommendation = details.get('recommendation', 'Monitor predictions and retrain if needed.')

        elif drift_type == 'concept':
            message = (
                f"Concept drift detected in {model_name}: "
                f"Accuracy has degraded (drop={drift_score:.1%})"
            )
            recommendation = details.get('recommendation', 'Retrain model immediately.')

        elif drift_type == 'calibration':
            message = (
                f"Calibration drift detected in {model_name}: "
                f"ECE={drift_score:.3f}"
            )
            recommendation = details.get('recommendation', 'Recalibrate model.')

        else:
            message = f"Drift detected in {model_name}: {metric_name}"
            recommendation = "Investigate drift cause."

        # Send alert
        alert = alert_manager.send_drift_alert(
            model_name=model_name,
            drift_type=drift_type,
            metric_name=metric_name,
            drift_score=drift_score,
            severity=alert_manager._parse_severity(severity),
            message=message,
            recommendation=recommendation,
            details=details
        )

        if alert:
            return {
                "status": "success",
                "alert_id": alert.alert_id,
                "timestamp": alert.created_at.isoformat()
            }
        else:
            return {
                "status": "skipped",
                "reason": "cooldown",
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Error sending drift alert: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@celery_app.task(name='monitor_predictions_hourly', bind=True)
def monitor_predictions_hourly(self) -> Dict[str, Any]:
    """
    Hourly prediction monitoring.

    Tracks prediction distributions hourly for early drift detection.

    Returns:
        Monitoring summary
    """
    logger.info("Starting hourly prediction monitoring...")

    try:
        prediction_monitor = get_prediction_monitor()

        results = {
            "check_type": "hourly_prediction_monitoring",
            "timestamp": datetime.utcnow().isoformat(),
            "models_monitored": [],
            "snapshots_created": []
        }

        models_to_check = _get_active_models()

        for model_name in models_to_check:
            # Create snapshot
            snapshot = prediction_monitor.snapshot_predictions(model_name)

            if snapshot:
                results["snapshots_created"].append({
                    "model_name": model_name,
                    "mean": snapshot.mean_prediction,
                    "std": snapshot.std_prediction,
                    "samples": snapshot.sample_count
                })

            results["models_monitored"].append(model_name)

        logger.info(
            f"Hourly monitoring complete: "
            f"{len(results['models_monitored'])} models monitored, "
            f"{len(results['snapshots_created'])} snapshots created"
        )

        return results

    except Exception as e:
        logger.error(f"Error in hourly monitoring: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Helper functions

def _get_active_models() -> list:
    """
    Get list of active models to monitor.

    In production, this would query the database for all active models.
    For now, return hardcoded list.
    """
    return [
        'ctr_model',
        'creative_dna',
        'battle_hardened_sampler'
    ]
