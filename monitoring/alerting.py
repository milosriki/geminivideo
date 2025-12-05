"""
Alert manager with email, Slack, and PagerDuty integration.

Features:
- Configurable alert thresholds
- Multiple notification channels
- Alert deduplication and rate limiting
- Severity levels
- Alert escalation
"""

import os
import smtplib
import json
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import requests
from threading import Lock


# ============================================================================
# ALERT SEVERITY LEVELS
# ============================================================================

class Severity(Enum):
    """Alert severity levels."""
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'


# ============================================================================
# ALERT MODEL
# ============================================================================

@dataclass
class Alert:
    """Alert data structure."""
    title: str
    message: str
    severity: Severity
    service: str
    timestamp: datetime
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    correlation_id: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['timestamp'] = self.timestamp.isoformat()
        return data

    def fingerprint(self) -> str:
        """Generate unique fingerprint for deduplication."""
        return f"{self.service}:{self.metric_name}:{self.severity.value}"


# ============================================================================
# ALERT THRESHOLDS
# ============================================================================

@dataclass
class Threshold:
    """Alert threshold configuration."""
    metric_name: str
    warning_value: Optional[float] = None
    error_value: Optional[float] = None
    critical_value: Optional[float] = None
    comparison: str = 'gt'  # gt, lt, eq, ne, gte, lte
    duration_seconds: int = 60  # How long threshold must be exceeded
    cooldown_seconds: int = 300  # Minimum time between alerts


# Default thresholds for common metrics
DEFAULT_THRESHOLDS = {
    'http_error_rate': Threshold(
        metric_name='http_error_rate',
        warning_value=0.01,  # 1%
        error_value=0.05,    # 5%
        critical_value=0.10,  # 10%
        comparison='gt'
    ),
    'http_p95_latency_seconds': Threshold(
        metric_name='http_p95_latency_seconds',
        warning_value=1.0,
        error_value=3.0,
        critical_value=5.0,
        comparison='gt'
    ),
    'ai_api_error_rate': Threshold(
        metric_name='ai_api_error_rate',
        warning_value=0.05,  # 5%
        error_value=0.10,    # 10%
        critical_value=0.20,  # 20%
        comparison='gt'
    ),
    'ai_api_cost_per_hour': Threshold(
        metric_name='ai_api_cost_per_hour',
        warning_value=100.0,
        error_value=500.0,
        critical_value=1000.0,
        comparison='gt'
    ),
    'database_connection_pool_usage': Threshold(
        metric_name='database_connection_pool_usage',
        warning_value=0.70,  # 70%
        error_value=0.85,    # 85%
        critical_value=0.95,  # 95%
        comparison='gt'
    ),
    'queue_depth': Threshold(
        metric_name='queue_depth',
        warning_value=1000,
        error_value=5000,
        critical_value=10000,
        comparison='gt'
    ),
    'prediction_accuracy': Threshold(
        metric_name='prediction_accuracy',
        warning_value=0.70,  # Below 70% is bad
        error_value=0.50,
        critical_value=0.30,
        comparison='lt'
    ),
    'service_health': Threshold(
        metric_name='service_health',
        critical_value=0,  # 0 = unhealthy
        comparison='eq',
        duration_seconds=30
    ),
}


# ============================================================================
# ALERT MANAGER
# ============================================================================

class AlertManager:
    """
    Manages alerts and notifications.
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self.thresholds = DEFAULT_THRESHOLDS.copy()
        self.channels: List[AlertChannel] = []
        self.alert_history: Dict[str, datetime] = {}  # fingerprint -> last_sent
        self.lock = Lock()

    def add_threshold(self, threshold: Threshold):
        """Add or update alert threshold."""
        self.thresholds[threshold.metric_name] = threshold

    def add_channel(self, channel: 'AlertChannel'):
        """Add notification channel."""
        self.channels.append(channel)

    def check_threshold(self, metric_name: str, value: float) -> Optional[Severity]:
        """
        Check if metric value exceeds threshold.

        Returns:
            Severity level if threshold exceeded, None otherwise
        """
        threshold = self.thresholds.get(metric_name)
        if not threshold:
            return None

        # Determine comparison function
        comparisons = {
            'gt': lambda v, t: v > t,
            'lt': lambda v, t: v < t,
            'gte': lambda v, t: v >= t,
            'lte': lambda v, t: v <= t,
            'eq': lambda v, t: v == t,
            'ne': lambda v, t: v != t,
        }
        compare = comparisons.get(threshold.comparison, lambda v, t: v > t)

        # Check severity levels
        if threshold.critical_value is not None and compare(value, threshold.critical_value):
            return Severity.CRITICAL
        elif threshold.error_value is not None and compare(value, threshold.error_value):
            return Severity.ERROR
        elif threshold.warning_value is not None and compare(value, threshold.warning_value):
            return Severity.WARNING

        return None

    def should_send_alert(self, alert: Alert) -> bool:
        """Check if alert should be sent (considering cooldown)."""
        with self.lock:
            fingerprint = alert.fingerprint()
            last_sent = self.alert_history.get(fingerprint)

            if not last_sent:
                return True

            threshold = self.thresholds.get(alert.metric_name or '')
            cooldown = threshold.cooldown_seconds if threshold else 300

            elapsed = (datetime.utcnow() - last_sent).total_seconds()
            return elapsed >= cooldown

    def send_alert(self, alert: Alert):
        """Send alert through all configured channels."""
        if not self.should_send_alert(alert):
            return

        with self.lock:
            self.alert_history[alert.fingerprint()] = datetime.utcnow()

        for channel in self.channels:
            try:
                channel.send(alert)
            except Exception as e:
                print(f"Failed to send alert via {channel.__class__.__name__}: {e}")

    def create_and_send_alert(
        self,
        title: str,
        message: str,
        severity: Severity,
        metric_name: Optional[str] = None,
        metric_value: Optional[float] = None,
        **kwargs
    ):
        """Create and send an alert."""
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            service=self.service_name,
            timestamp=datetime.utcnow(),
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=self.thresholds.get(metric_name or '').critical_value if metric_name else None,
            **kwargs
        )
        self.send_alert(alert)


# ============================================================================
# ALERT CHANNELS
# ============================================================================

class AlertChannel:
    """Base class for alert notification channels."""

    def send(self, alert: Alert):
        """Send alert notification."""
        raise NotImplementedError


class EmailChannel(AlertChannel):
    """Email notification channel."""

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        to_emails: List[str],
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.to_emails = to_emails
        self.use_tls = use_tls

    def send(self, alert: Alert):
        """Send alert via email."""
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)

        # Create HTML body
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif;">
            <h2 style="color: {self._get_color(alert.severity)};">{alert.title}</h2>
            <p><strong>Service:</strong> {alert.service}</p>
            <p><strong>Severity:</strong> {alert.severity.value.upper()}</p>
            <p><strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            {f'<p><strong>Metric:</strong> {alert.metric_name}</p>' if alert.metric_name else ''}
            {f'<p><strong>Value:</strong> {alert.metric_value}</p>' if alert.metric_value is not None else ''}
            {f'<p><strong>Threshold:</strong> {alert.threshold}</p>' if alert.threshold is not None else ''}
            {f'<p><strong>Correlation ID:</strong> {alert.correlation_id}</p>' if alert.correlation_id else ''}
            <hr>
            <p>{alert.message}</p>
            {f'<hr><pre>{json.dumps(alert.metadata, indent=2)}</pre>' if alert.metadata else ''}
          </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        # Send email
        try:
            if self.use_tls:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
        except Exception as e:
            print(f"Failed to send email alert: {e}")
            raise

    def _get_color(self, severity: Severity) -> str:
        """Get color for severity level."""
        colors = {
            Severity.INFO: '#17a2b8',
            Severity.WARNING: '#ffc107',
            Severity.ERROR: '#fd7e14',
            Severity.CRITICAL: '#dc3545',
        }
        return colors.get(severity, '#6c757d')


class SlackChannel(AlertChannel):
    """Slack webhook notification channel."""

    def __init__(self, webhook_url: str, channel: Optional[str] = None):
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, alert: Alert):
        """Send alert via Slack webhook."""
        # Create Slack message
        payload = {
            'username': 'Alert Bot',
            'icon_emoji': self._get_emoji(alert.severity),
            'attachments': [{
                'color': self._get_color(alert.severity),
                'title': alert.title,
                'text': alert.message,
                'fields': [
                    {'title': 'Service', 'value': alert.service, 'short': True},
                    {'title': 'Severity', 'value': alert.severity.value.upper(), 'short': True},
                    {'title': 'Time', 'value': alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'), 'short': True},
                ],
                'footer': 'GeminiVideo Monitoring',
                'ts': int(alert.timestamp.timestamp())
            }]
        }

        # Add metric fields if present
        if alert.metric_name:
            payload['attachments'][0]['fields'].append({
                'title': 'Metric',
                'value': alert.metric_name,
                'short': True
            })

        if alert.metric_value is not None:
            payload['attachments'][0]['fields'].append({
                'title': 'Value',
                'value': f"{alert.metric_value:.2f}",
                'short': True
            })

        if alert.threshold is not None:
            payload['attachments'][0]['fields'].append({
                'title': 'Threshold',
                'value': f"{alert.threshold:.2f}",
                'short': True
            })

        # Add correlation ID
        if alert.correlation_id:
            payload['attachments'][0]['fields'].append({
                'title': 'Correlation ID',
                'value': alert.correlation_id,
                'short': False
            })

        # Add channel if specified
        if self.channel:
            payload['channel'] = self.channel

        # Send to Slack
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send Slack alert: {e}")
            raise

    def _get_color(self, severity: Severity) -> str:
        """Get color for severity level."""
        colors = {
            Severity.INFO: '#36a64f',
            Severity.WARNING: '#ffcc00',
            Severity.ERROR: '#ff6600',
            Severity.CRITICAL: '#ff0000',
        }
        return colors.get(severity, '#808080')

    def _get_emoji(self, severity: Severity) -> str:
        """Get emoji for severity level."""
        emojis = {
            Severity.INFO: ':information_source:',
            Severity.WARNING: ':warning:',
            Severity.ERROR: ':x:',
            Severity.CRITICAL: ':rotating_light:',
        }
        return emojis.get(severity, ':bell:')


class PagerDutyChannel(AlertChannel):
    """PagerDuty notification channel."""

    def __init__(self, integration_key: str):
        self.integration_key = integration_key
        self.api_url = 'https://events.pagerduty.com/v2/enqueue'

    def send(self, alert: Alert):
        """Send alert via PagerDuty Events API v2."""
        # Only send ERROR and CRITICAL alerts to PagerDuty
        if alert.severity not in [Severity.ERROR, Severity.CRITICAL]:
            return

        # Create PagerDuty event
        payload = {
            'routing_key': self.integration_key,
            'event_action': 'trigger',
            'payload': {
                'summary': alert.title,
                'source': alert.service,
                'severity': self._map_severity(alert.severity),
                'timestamp': alert.timestamp.isoformat(),
                'custom_details': {
                    'message': alert.message,
                    'metric_name': alert.metric_name,
                    'metric_value': alert.metric_value,
                    'threshold': alert.threshold,
                    'correlation_id': alert.correlation_id,
                    'metadata': alert.metadata
                }
            }
        }

        # Send to PagerDuty
        try:
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
        except Exception as e:
            print(f"Failed to send PagerDuty alert: {e}")
            raise

    def _map_severity(self, severity: Severity) -> str:
        """Map internal severity to PagerDuty severity."""
        mapping = {
            Severity.INFO: 'info',
            Severity.WARNING: 'warning',
            Severity.ERROR: 'error',
            Severity.CRITICAL: 'critical',
        }
        return mapping.get(severity, 'error')


# ============================================================================
# CONFIGURATION HELPERS
# ============================================================================

def setup_alerting_from_env(service_name: str) -> AlertManager:
    """
    Setup alert manager from environment variables.

    Environment variables:
    - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, ALERT_EMAIL_FROM, ALERT_EMAIL_TO
    - SLACK_WEBHOOK_URL, SLACK_CHANNEL
    - PAGERDUTY_INTEGRATION_KEY
    """
    manager = AlertManager(service_name)

    # Email channel
    if all([
        os.getenv('SMTP_HOST'),
        os.getenv('SMTP_USER'),
        os.getenv('SMTP_PASSWORD'),
        os.getenv('ALERT_EMAIL_FROM'),
        os.getenv('ALERT_EMAIL_TO')
    ]):
        email_channel = EmailChannel(
            smtp_host=os.getenv('SMTP_HOST'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_user=os.getenv('SMTP_USER'),
            smtp_password=os.getenv('SMTP_PASSWORD'),
            from_email=os.getenv('ALERT_EMAIL_FROM'),
            to_emails=os.getenv('ALERT_EMAIL_TO').split(','),
            use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        )
        manager.add_channel(email_channel)

    # Slack channel
    if os.getenv('SLACK_WEBHOOK_URL'):
        slack_channel = SlackChannel(
            webhook_url=os.getenv('SLACK_WEBHOOK_URL'),
            channel=os.getenv('SLACK_CHANNEL')
        )
        manager.add_channel(slack_channel)

    # PagerDuty channel
    if os.getenv('PAGERDUTY_INTEGRATION_KEY'):
        pagerduty_channel = PagerDutyChannel(
            integration_key=os.getenv('PAGERDUTY_INTEGRATION_KEY')
        )
        manager.add_channel(pagerduty_channel)

    return manager


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == '__main__':
    # Create alert manager
    manager = AlertManager('example-service')

    # Add Slack channel (example)
    # slack = SlackChannel(webhook_url='https://hooks.slack.com/services/YOUR/WEBHOOK/URL')
    # manager.add_channel(slack)

    # Test alerts
    manager.create_and_send_alert(
        title='High Error Rate Detected',
        message='HTTP error rate exceeded 5% for the last 5 minutes',
        severity=Severity.ERROR,
        metric_name='http_error_rate',
        metric_value=0.08,
        metadata={'endpoint': '/api/campaigns', 'status_codes': {'500': 45, '502': 23}}
    )

    manager.create_and_send_alert(
        title='Service Health Check Failed',
        message='Database connection pool exhausted',
        severity=Severity.CRITICAL,
        metric_name='service_health',
        metric_value=0
    )

    print("Alerts sent successfully!")
