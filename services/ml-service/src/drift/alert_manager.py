"""
Alert Manager - Send drift detection alerts
===========================================

Sends alerts when model drift is detected:
    - Slack notifications
    - Email alerts
    - Severity levels (warning, critical, emergency)
    - Actionable recommendations

Integrates with existing alerting infrastructure.

Author: Agent 10
Created: 2025-12-12
"""

import logging
import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class DriftAlert:
    """Drift detection alert"""
    alert_id: str
    severity: AlertSeverity
    model_name: str
    drift_type: str  # 'feature', 'prediction', 'concept', 'calibration'
    metric_name: str
    drift_score: float
    message: str
    recommendation: str
    details: Dict[str, Any]
    created_at: datetime

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['severity'] = self.severity.value
        data['created_at'] = self.created_at.isoformat()
        return data


class AlertManager:
    """
    Manages drift detection alerts across multiple channels.

    Sends notifications via:
        - Slack
        - Email
        - Webhook
        - Database logging
    """

    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        email_enabled: bool = False,
        email_recipients: Optional[List[str]] = None,
        alert_cooldown_minutes: int = 60,  # Prevent alert spam
    ):
        """
        Initialize Alert Manager.

        Args:
            slack_webhook_url: Slack webhook URL for notifications
            email_enabled: Whether to send email alerts
            email_recipients: List of email addresses
            alert_cooldown_minutes: Minimum time between same alerts
        """
        self.slack_webhook_url = slack_webhook_url or os.getenv('SLACK_DRIFT_WEBHOOK_URL')
        self.email_enabled = email_enabled
        self.email_recipients = email_recipients or []
        self.alert_cooldown_minutes = alert_cooldown_minutes

        # Track recent alerts to prevent spam
        self._recent_alerts: Dict[str, datetime] = {}

        # Alert history (in production, use database)
        self._alert_history: List[DriftAlert] = []

        logger.info(
            f"AlertManager initialized: "
            f"slack={'enabled' if self.slack_webhook_url else 'disabled'}, "
            f"email={'enabled' if email_enabled else 'disabled'}, "
            f"cooldown={alert_cooldown_minutes}min"
        )

    def send_drift_alert(
        self,
        model_name: str,
        drift_type: str,
        metric_name: str,
        drift_score: float,
        severity: AlertSeverity,
        message: str,
        recommendation: str,
        details: Optional[Dict] = None
    ) -> DriftAlert:
        """
        Send drift detection alert.

        Args:
            model_name: Name of model
            drift_type: Type of drift ('feature', 'prediction', 'concept', 'calibration')
            metric_name: Name of drifted metric
            drift_score: Drift score/magnitude
            severity: Alert severity
            message: Alert message
            recommendation: Recommended action
            details: Additional details

        Returns:
            DriftAlert object
        """
        # Check cooldown
        alert_key = f"{model_name}_{metric_name}"
        if not self._check_cooldown(alert_key):
            logger.info(f"Alert {alert_key} in cooldown period, skipping")
            return None

        # Create alert
        alert = DriftAlert(
            alert_id=self._generate_alert_id(),
            severity=severity,
            model_name=model_name,
            drift_type=drift_type,
            metric_name=metric_name,
            drift_score=drift_score,
            message=message,
            recommendation=recommendation,
            details=details or {},
            created_at=datetime.utcnow()
        )

        # Send to channels
        if self.slack_webhook_url:
            self._send_slack_alert(alert)

        if self.email_enabled:
            self._send_email_alert(alert)

        # Log alert
        self._log_alert(alert)

        # Store in history
        self._alert_history.append(alert)

        # Update cooldown
        self._recent_alerts[alert_key] = datetime.utcnow()

        logger.info(
            f"Drift alert sent: {alert.alert_id} - {severity.value} - "
            f"{model_name}/{metric_name}"
        )

        return alert

    def send_feature_drift_alert(
        self,
        model_name: str,
        feature_name: str,
        drift_score: float,
        mean_shift: float,
        std_shift: float,
        severity: str,
        recommendation: str
    ) -> Optional[DriftAlert]:
        """
        Send feature drift alert.

        Args:
            model_name: Model name
            feature_name: Drifted feature name
            drift_score: PSI or KS score
            mean_shift: Mean shift in std devs
            std_shift: Std deviation shift
            severity: Severity level
            recommendation: Recommendation

        Returns:
            DriftAlert or None
        """
        severity_enum = self._parse_severity(severity)

        message = (
            f"Feature drift detected in {model_name}: "
            f"{feature_name} has drifted (score={drift_score:.3f}, "
            f"mean_shift={mean_shift:.1f}σ, std_shift={std_shift:.1%})"
        )

        return self.send_drift_alert(
            model_name=model_name,
            drift_type='feature',
            metric_name=feature_name,
            drift_score=drift_score,
            severity=severity_enum,
            message=message,
            recommendation=recommendation,
            details={
                "drift_score": drift_score,
                "mean_shift": mean_shift,
                "std_shift": std_shift
            }
        )

    def send_prediction_drift_alert(
        self,
        model_name: str,
        drift_score: float,
        prediction_shift: float,
        severity: str,
        recommendation: str
    ) -> Optional[DriftAlert]:
        """
        Send prediction drift alert.

        Args:
            model_name: Model name
            drift_score: Drift magnitude
            prediction_shift: Shift in std devs
            severity: Severity level
            recommendation: Recommendation

        Returns:
            DriftAlert or None
        """
        severity_enum = self._parse_severity(severity)

        message = (
            f"Prediction drift detected in {model_name}: "
            f"Predictions shifted by {prediction_shift:.1f}σ "
            f"(drift_score={drift_score:.3f})"
        )

        return self.send_drift_alert(
            model_name=model_name,
            drift_type='prediction',
            metric_name='predictions',
            drift_score=drift_score,
            severity=severity_enum,
            message=message,
            recommendation=recommendation,
            details={
                "drift_score": drift_score,
                "prediction_shift": prediction_shift
            }
        )

    def send_concept_drift_alert(
        self,
        model_name: str,
        accuracy_drop: float,
        baseline_accuracy: float,
        current_accuracy: float,
        severity: str,
        recommendation: str
    ) -> Optional[DriftAlert]:
        """
        Send concept drift (accuracy degradation) alert.

        Args:
            model_name: Model name
            accuracy_drop: Accuracy drop (0-1)
            baseline_accuracy: Baseline accuracy
            current_accuracy: Current accuracy
            severity: Severity level
            recommendation: Recommendation

        Returns:
            DriftAlert or None
        """
        severity_enum = self._parse_severity(severity)

        message = (
            f"Concept drift detected in {model_name}: "
            f"Accuracy dropped from {baseline_accuracy:.1%} to {current_accuracy:.1%} "
            f"(-{accuracy_drop:.1%})"
        )

        return self.send_drift_alert(
            model_name=model_name,
            drift_type='concept',
            metric_name='accuracy',
            drift_score=accuracy_drop,
            severity=severity_enum,
            message=message,
            recommendation=recommendation,
            details={
                "accuracy_drop": accuracy_drop,
                "baseline_accuracy": baseline_accuracy,
                "current_accuracy": current_accuracy
            }
        )

    def send_calibration_drift_alert(
        self,
        model_name: str,
        ece: float,
        severity: str,
        recommendation: str
    ) -> Optional[DriftAlert]:
        """
        Send calibration drift alert.

        Args:
            model_name: Model name
            ece: Expected Calibration Error
            severity: Severity level
            recommendation: Recommendation

        Returns:
            DriftAlert or None
        """
        severity_enum = self._parse_severity(severity)

        message = (
            f"Calibration drift detected in {model_name}: "
            f"Expected Calibration Error = {ece:.3f}"
        )

        return self.send_drift_alert(
            model_name=model_name,
            drift_type='calibration',
            metric_name='calibration',
            drift_score=ece,
            severity=severity_enum,
            message=message,
            recommendation=recommendation,
            details={"ece": ece}
        )

    def get_alert_history(
        self,
        hours: int = 24,
        severity: Optional[AlertSeverity] = None
    ) -> List[DriftAlert]:
        """
        Get alert history.

        Args:
            hours: Hours to look back
            severity: Filter by severity (optional)

        Returns:
            List of alerts
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        alerts = [
            alert for alert in self._alert_history
            if alert.created_at >= cutoff
        ]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Get summary of alerts.

        Returns:
            Summary statistics
        """
        total_alerts = len(self._alert_history)

        severity_counts = {
            severity.value: sum(1 for a in self._alert_history if a.severity == severity)
            for severity in AlertSeverity
        }

        drift_type_counts = {}
        for alert in self._alert_history:
            drift_type_counts[alert.drift_type] = drift_type_counts.get(alert.drift_type, 0) + 1

        return {
            "total_alerts": total_alerts,
            "severity_counts": severity_counts,
            "drift_type_counts": drift_type_counts,
            "last_alert": self._alert_history[-1].to_dict() if self._alert_history else None
        }

    # Private methods

    def _send_slack_alert(self, alert: DriftAlert):
        """Send alert to Slack."""
        if not self.slack_webhook_url:
            return

        try:
            # Choose emoji based on severity
            emoji_map = {
                AlertSeverity.INFO: ":information_source:",
                AlertSeverity.WARNING: ":warning:",
                AlertSeverity.CRITICAL: ":rotating_light:",
                AlertSeverity.EMERGENCY: ":fire:"
            }
            emoji = emoji_map.get(alert.severity, ":bell:")

            # Choose color based on severity
            color_map = {
                AlertSeverity.INFO: "#36a64f",  # green
                AlertSeverity.WARNING: "#ff9900",  # orange
                AlertSeverity.CRITICAL: "#ff0000",  # red
                AlertSeverity.EMERGENCY: "#8b0000"  # dark red
            }
            color = color_map.get(alert.severity, "#808080")

            # Build Slack message
            payload = {
                "text": f"{emoji} *Model Drift Alert* - {alert.severity.value.upper()}",
                "attachments": [
                    {
                        "color": color,
                        "fields": [
                            {
                                "title": "Model",
                                "value": alert.model_name,
                                "short": True
                            },
                            {
                                "title": "Drift Type",
                                "value": alert.drift_type,
                                "short": True
                            },
                            {
                                "title": "Metric",
                                "value": alert.metric_name,
                                "short": True
                            },
                            {
                                "title": "Drift Score",
                                "value": f"{alert.drift_score:.3f}",
                                "short": True
                            },
                            {
                                "title": "Message",
                                "value": alert.message,
                                "short": False
                            },
                            {
                                "title": "Recommendation",
                                "value": alert.recommendation,
                                "short": False
                            }
                        ],
                        "footer": "GeminiVideo Drift Detection",
                        "ts": int(alert.created_at.timestamp())
                    }
                ]
            }

            # Send to Slack
            with httpx.Client() as client:
                response = client.post(
                    self.slack_webhook_url,
                    json=payload,
                    timeout=10.0
                )
                response.raise_for_status()

            logger.info(f"Slack alert sent: {alert.alert_id}")

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}", exc_info=True)

    def _send_email_alert(self, alert: DriftAlert):
        """Send alert via email."""
        if not self.email_enabled or not self.email_recipients:
            return

        try:
            # Import email service from existing infrastructure
            from src.alerts.alert_service import get_alert_service

            alert_service = get_alert_service()

            subject = f"[{alert.severity.value.upper()}] Model Drift Alert - {alert.model_name}"

            body = f"""
Model Drift Alert
=================

Severity: {alert.severity.value.upper()}
Model: {alert.model_name}
Drift Type: {alert.drift_type}
Metric: {alert.metric_name}
Drift Score: {alert.drift_score:.3f}

Message:
{alert.message}

Recommendation:
{alert.recommendation}

Details:
{json.dumps(alert.details, indent=2)}

Alert ID: {alert.alert_id}
Timestamp: {alert.created_at.isoformat()}
"""

            for recipient in self.email_recipients:
                alert_service.send_email(
                    to=recipient,
                    subject=subject,
                    body=body
                )

            logger.info(f"Email alert sent: {alert.alert_id}")

        except ImportError:
            logger.warning("Alert service not available for email alerts")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}", exc_info=True)

    def _log_alert(self, alert: DriftAlert):
        """Log alert to system logs."""
        log_level_map = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.CRITICAL: logging.ERROR,
            AlertSeverity.EMERGENCY: logging.CRITICAL
        }

        log_level = log_level_map.get(alert.severity, logging.INFO)

        logger.log(
            log_level,
            f"DRIFT ALERT [{alert.severity.value}] {alert.model_name}/{alert.metric_name}: "
            f"{alert.message} | {alert.recommendation}"
        )

    def _check_cooldown(self, alert_key: str) -> bool:
        """Check if alert is in cooldown period."""
        if alert_key not in self._recent_alerts:
            return True

        last_alert_time = self._recent_alerts[alert_key]
        elapsed = (datetime.utcnow() - last_alert_time).total_seconds() / 60

        return elapsed >= self.alert_cooldown_minutes

    def _generate_alert_id(self) -> str:
        """Generate unique alert ID."""
        import uuid
        return f"drift_alert_{uuid.uuid4().hex[:12]}"

    def _parse_severity(self, severity: str) -> AlertSeverity:
        """Parse severity string to enum."""
        severity_map = {
            'info': AlertSeverity.INFO,
            'warning': AlertSeverity.WARNING,
            'critical': AlertSeverity.CRITICAL,
            'emergency': AlertSeverity.EMERGENCY,
            'none': AlertSeverity.INFO
        }
        return severity_map.get(severity.lower(), AlertSeverity.WARNING)


# Singleton instance
_alert_manager_instance = None


def get_alert_manager() -> AlertManager:
    """Get or create AlertManager singleton."""
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager()
    return _alert_manager_instance
