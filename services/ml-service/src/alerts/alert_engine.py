"""
Alert Engine - Core Alert Processing Logic
Monitors metrics and triggers alerts based on configurable rules
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import asyncio
import uuid

from src.alerts.alert_rules import AlertRule, AlertType, AlertSeverity, alert_rule_manager
from src.alerts.alert_notifier import AlertNotifier, NotificationChannel, alert_notifier

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """
    Alert instance representing a triggered alert

    Attributes:
        alert_id: Unique alert identifier
        rule_id: ID of the rule that triggered this alert
        alert_type: Type of alert
        severity: Alert severity
        title: Alert title
        message: Human-readable alert message
        campaign_id: ID of affected campaign
        campaign_name: Name of affected campaign
        ad_id: ID of affected ad (optional)
        metric_name: Name of the metric that triggered alert
        metric_value: Current value of the metric
        threshold_value: Threshold value from rule
        details: Additional alert details
        timestamp: When alert was triggered
        acknowledged: Whether alert has been acknowledged
        acknowledged_at: When alert was acknowledged
        acknowledged_by: Who acknowledged the alert
        resolved: Whether issue has been resolved
        resolved_at: When alert was resolved
        notification_status: Status of notifications sent
    """
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    alert_type: AlertType = AlertType.ROAS_DROP
    severity: AlertSeverity = AlertSeverity.MEDIUM
    title: str = ""
    message: str = ""
    campaign_id: str = ""
    campaign_name: str = ""
    ad_id: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    threshold_value: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[str] = None
    notification_status: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['severity'] = self.severity.value
        return data

    def acknowledge(self, user_id: str):
        """Mark alert as acknowledged"""
        self.acknowledged = True
        self.acknowledged_at = datetime.utcnow().isoformat()
        self.acknowledged_by = user_id
        logger.info(f"Alert {self.alert_id} acknowledged by {user_id}")

    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.utcnow().isoformat()
        logger.info(f"Alert {self.alert_id} resolved")


class AlertEngine:
    """
    Core alert engine for monitoring performance and triggering alerts
    """

    def __init__(
        self,
        rule_manager=alert_rule_manager,
        notifier: AlertNotifier = alert_notifier
    ):
        """
        Initialize alert engine

        Args:
            rule_manager: AlertRuleManager instance
            notifier: AlertNotifier instance
        """
        self.rule_manager = rule_manager
        self.notifier = notifier

        # Alert storage (in-memory, should be persisted to DB in production)
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Cooldown tracking: {entity_id: {rule_id: last_alert_time}}
        self.cooldown_tracker: Dict[str, Dict[str, datetime]] = defaultdict(dict)

        logger.info("AlertEngine initialized")

    def check_metric(
        self,
        metric_name: str,
        metric_value: float,
        campaign_id: str,
        campaign_name: str,
        ad_id: str = "",
        context: Optional[Dict[str, Any]] = None,
        alert_types: Optional[List[AlertType]] = None
    ) -> List[Alert]:
        """
        Check a metric against all relevant alert rules

        Args:
            metric_name: Name of the metric (e.g., 'roas', 'ctr', 'budget_spent_pct')
            metric_value: Current value of the metric
            campaign_id: ID of the campaign
            campaign_name: Name of the campaign
            ad_id: ID of the ad (optional)
            context: Additional context for rule evaluation
            alert_types: Specific alert types to check (None = all enabled)

        Returns:
            List of triggered alerts
        """
        triggered_alerts = []

        # Get rules to evaluate
        if alert_types:
            rules = []
            for alert_type in alert_types:
                rules.extend(self.rule_manager.get_rules_by_type(alert_type))
        else:
            rules = self.rule_manager.get_enabled_rules()

        # Evaluate each rule
        for rule in rules:
            # Check cooldown
            entity_id = f"{campaign_id}:{ad_id}" if ad_id else campaign_id
            if not self._check_cooldown(entity_id, rule.rule_id, rule.cooldown_minutes):
                continue

            # Evaluate rule
            if rule.evaluate(metric_value, context):
                alert = self._create_alert(
                    rule=rule,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    campaign_id=campaign_id,
                    campaign_name=campaign_name,
                    ad_id=ad_id,
                    context=context or {}
                )
                triggered_alerts.append(alert)

                # Update cooldown tracker
                self.cooldown_tracker[entity_id][rule.rule_id] = datetime.utcnow()

                # Store alert
                self.active_alerts[alert.alert_id] = alert
                self.alert_history.append(alert)

                logger.info(f"Alert triggered: {alert.alert_id} ({alert.alert_type.value})")

        return triggered_alerts

    def _check_cooldown(self, entity_id: str, rule_id: str, cooldown_minutes: int) -> bool:
        """Check if cooldown period has passed for entity/rule combination"""
        if cooldown_minutes == 0:
            return True

        last_alert = self.cooldown_tracker.get(entity_id, {}).get(rule_id)
        if not last_alert:
            return True

        elapsed = datetime.utcnow() - last_alert
        return elapsed > timedelta(minutes=cooldown_minutes)

    def _create_alert(
        self,
        rule: AlertRule,
        metric_name: str,
        metric_value: float,
        campaign_id: str,
        campaign_name: str,
        ad_id: str,
        context: Dict[str, Any]
    ) -> Alert:
        """Create an alert from a triggered rule"""

        # Generate alert message
        title, message = self._generate_alert_message(
            rule.alert_type,
            metric_name,
            metric_value,
            rule.threshold,
            campaign_name
        )

        # Create alert
        alert = Alert(
            rule_id=rule.rule_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            title=title,
            message=message,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            ad_id=ad_id,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_value=rule.threshold,
            details={
                'rule_name': rule.name,
                'operator': rule.threshold_operator,
                'action': rule.metadata.get('action', 'Review performance'),
                **context
            }
        )

        return alert

    def _generate_alert_message(
        self,
        alert_type: AlertType,
        metric_name: str,
        metric_value: float,
        threshold: float,
        campaign_name: str
    ) -> Tuple[str, str]:
        """Generate human-readable alert title and message"""

        messages = {
            AlertType.ROAS_DROP: (
                f"ROAS Drop Alert: {campaign_name}",
                f"ROAS has dropped to {metric_value:.2f}x (threshold: {threshold:.2f}x). Immediate review recommended."
            ),
            AlertType.BUDGET_WARNING: (
                f"Budget Warning: {campaign_name}",
                f"Campaign has spent {metric_value:.1f}% of daily budget (threshold: {threshold:.1f}%). Monitor spend rate."
            ),
            AlertType.BUDGET_DEPLETED: (
                f"Budget Depleted: {campaign_name}",
                f"Campaign has exhausted {metric_value:.1f}% of daily budget. Consider increasing budget or wait for reset."
            ),
            AlertType.AD_DISAPPROVED: (
                f"Ad Disapproved: {campaign_name}",
                f"Meta has disapproved an ad in this campaign. Review ad content and resubmit."
            ),
            AlertType.CTR_ANOMALY: (
                f"CTR Anomaly: {campaign_name}",
                f"CTR has dropped {metric_value:.1f}% from average (threshold: {threshold:.1f}%). Check creative fatigue."
            ),
            AlertType.CONVERSION_SPIKE: (
                f"Conversion Spike: {campaign_name}",
                f"Conversions increased {metric_value:.1f}% (threshold: {threshold:.1f}%). Verify quality for potential fraud."
            ),
            AlertType.PREDICTION_MISS: (
                f"Prediction Error: {campaign_name}",
                f"Prediction error is {metric_value:.1f}% (threshold: {threshold:.1f}%). Model may need retraining."
            ),
            AlertType.HIGH_CPA: (
                f"High CPA Alert: {campaign_name}",
                f"Cost per acquisition is ${metric_value:.2f} (threshold: ${threshold:.2f}). Optimize targeting."
            ),
            AlertType.LOW_IMPRESSIONS: (
                f"Low Impressions: {campaign_name}",
                f"Receiving {metric_value:.0f} impressions/hour (threshold: {threshold:.0f}). Check delivery issues."
            ),
            AlertType.CAMPAIGN_PAUSED: (
                f"Campaign Paused: {campaign_name}",
                f"Campaign has been automatically paused. Review performance metrics."
            ),
        }

        return messages.get(
            alert_type,
            (f"Alert: {campaign_name}", f"Metric {metric_name} is {metric_value} (threshold: {threshold})")
        )

    async def send_alert_notifications(self, alert: Alert, channels: Optional[List[NotificationChannel]] = None) -> Dict[str, bool]:
        """
        Send notifications for an alert

        Args:
            alert: Alert to send
            channels: Specific channels to use (None = all enabled)

        Returns:
            Dict mapping channel to success status
        """
        alert_data = alert.to_dict()
        results = await self.notifier.notify(alert_data, channels)
        alert.notification_status = results
        return results

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """
        Acknowledge an alert

        Args:
            alert_id: ID of alert to acknowledge
            user_id: ID of user acknowledging

        Returns:
            True if successful
        """
        alert = self.active_alerts.get(alert_id)
        if alert:
            alert.acknowledge(user_id)
            return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """
        Mark alert as resolved

        Args:
            alert_id: ID of alert to resolve

        Returns:
            True if successful
        """
        alert = self.active_alerts.get(alert_id)
        if alert:
            alert.resolve()
            # Move to history and remove from active
            if alert_id in self.active_alerts:
                del self.active_alerts[alert_id]
            return True
        return False

    def get_active_alerts(
        self,
        campaign_id: Optional[str] = None,
        alert_type: Optional[AlertType] = None,
        severity: Optional[AlertSeverity] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get active alerts with optional filtering

        Args:
            campaign_id: Filter by campaign ID
            alert_type: Filter by alert type
            severity: Filter by severity
            limit: Maximum number of alerts to return

        Returns:
            List of alerts
        """
        alerts = list(self.active_alerts.values())

        # Apply filters
        if campaign_id:
            alerts = [a for a in alerts if a.campaign_id == campaign_id]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return alerts[:limit]

    def get_alert_history(
        self,
        campaign_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Alert]:
        """
        Get alert history with optional filtering

        Args:
            campaign_id: Filter by campaign ID
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of alerts to return

        Returns:
            List of historical alerts
        """
        alerts = self.alert_history.copy()

        # Apply filters
        if campaign_id:
            alerts = [a for a in alerts if a.campaign_id == campaign_id]

        if start_date:
            start_iso = start_date.isoformat()
            alerts = [a for a in alerts if a.timestamp >= start_iso]

        if end_date:
            end_iso = end_date.isoformat()
            alerts = [a for a in alerts if a.timestamp <= end_iso]

        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        return alerts[:limit]

    def get_alert_stats(self, campaign_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get alert statistics

        Args:
            campaign_id: Filter by campaign ID (optional)

        Returns:
            Dictionary of statistics
        """
        alerts = self.alert_history if not campaign_id else [
            a for a in self.alert_history if a.campaign_id == campaign_id
        ]

        # Count by type
        by_type = defaultdict(int)
        for alert in alerts:
            by_type[alert.alert_type.value] += 1

        # Count by severity
        by_severity = defaultdict(int)
        for alert in alerts:
            by_severity[alert.severity.value] += 1

        # Count acknowledged/resolved
        total = len(alerts)
        acknowledged = sum(1 for a in alerts if a.acknowledged)
        resolved = sum(1 for a in alerts if a.resolved)

        return {
            'total_alerts': total,
            'active_alerts': len(self.active_alerts),
            'acknowledged': acknowledged,
            'resolved': resolved,
            'by_type': dict(by_type),
            'by_severity': dict(by_severity),
            'campaign_id': campaign_id
        }

    def check_roas(self, campaign_id: str, campaign_name: str, roas: float, context: Optional[Dict[str, Any]] = None) -> List[Alert]:
        """Convenience method to check ROAS metric"""
        return self.check_metric(
            metric_name='roas',
            metric_value=roas,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            context=context,
            alert_types=[AlertType.ROAS_DROP]
        )

    def check_budget(self, campaign_id: str, campaign_name: str, budget_spent_pct: float, context: Optional[Dict[str, Any]] = None) -> List[Alert]:
        """Convenience method to check budget spending"""
        return self.check_metric(
            metric_name='budget_spent_pct',
            metric_value=budget_spent_pct,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            context=context,
            alert_types=[AlertType.BUDGET_WARNING, AlertType.BUDGET_DEPLETED]
        )

    def check_ctr(self, campaign_id: str, campaign_name: str, ctr_drop_pct: float, context: Optional[Dict[str, Any]] = None) -> List[Alert]:
        """Convenience method to check CTR anomalies"""
        return self.check_metric(
            metric_name='ctr_drop_pct',
            metric_value=ctr_drop_pct,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            context=context,
            alert_types=[AlertType.CTR_ANOMALY]
        )

    def check_conversions(self, campaign_id: str, campaign_name: str, conversion_spike_pct: float, context: Optional[Dict[str, Any]] = None) -> List[Alert]:
        """Convenience method to check conversion spikes"""
        return self.check_metric(
            metric_name='conversion_spike_pct',
            metric_value=conversion_spike_pct,
            campaign_id=campaign_id,
            campaign_name=campaign_name,
            context=context,
            alert_types=[AlertType.CONVERSION_SPIKE]
        )


# Global instance
alert_engine = AlertEngine()
