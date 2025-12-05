"""
Alert Notifier
Handles sending notifications via Email, Slack, Webhooks
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
import os
import asyncio
import aiohttp
from enum import Enum

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    DATABASE = "database"  # Store in DB for frontend
    WEBSOCKET = "websocket"  # Real-time push via WebSocket


@dataclass
class NotificationConfig:
    """Configuration for notification channels"""
    email_enabled: bool = False
    email_recipients: List[str] = field(default_factory=list)
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_sender: str = ""
    email_password: str = ""

    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"

    webhook_enabled: bool = False
    webhook_urls: List[str] = field(default_factory=list)
    webhook_headers: Dict[str, str] = field(default_factory=dict)

    database_enabled: bool = True  # Always store in DB
    websocket_enabled: bool = True  # Real-time push

    @classmethod
    def from_env(cls) -> 'NotificationConfig':
        """Load configuration from environment variables"""
        return cls(
            email_enabled=os.getenv('ALERT_EMAIL_ENABLED', 'false').lower() == 'true',
            email_recipients=os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(','),
            email_smtp_host=os.getenv('ALERT_EMAIL_SMTP_HOST', ''),
            email_smtp_port=int(os.getenv('ALERT_EMAIL_SMTP_PORT', '587')),
            email_sender=os.getenv('ALERT_EMAIL_SENDER', ''),
            email_password=os.getenv('ALERT_EMAIL_PASSWORD', ''),

            slack_enabled=os.getenv('ALERT_SLACK_ENABLED', 'false').lower() == 'true',
            slack_webhook_url=os.getenv('ALERT_SLACK_WEBHOOK_URL', ''),
            slack_channel=os.getenv('ALERT_SLACK_CHANNEL', '#alerts'),

            webhook_enabled=os.getenv('ALERT_WEBHOOK_ENABLED', 'false').lower() == 'true',
            webhook_urls=os.getenv('ALERT_WEBHOOK_URLS', '').split(','),
            webhook_headers=json.loads(os.getenv('ALERT_WEBHOOK_HEADERS', '{}')),

            database_enabled=True,
            websocket_enabled=True,
        )


class AlertNotifier:
    """
    Handles alert notification delivery across multiple channels
    """

    def __init__(self, config: Optional[NotificationConfig] = None):
        """
        Initialize alert notifier

        Args:
            config: Notification configuration (loads from env if not provided)
        """
        self.config = config or NotificationConfig.from_env()
        self.websocket_handlers: List[Any] = []  # WebSocket connections

    def register_websocket_handler(self, handler: Any):
        """Register a WebSocket handler for real-time push"""
        self.websocket_handlers.append(handler)
        logger.info(f"Registered WebSocket handler: {handler}")

    def unregister_websocket_handler(self, handler: Any):
        """Unregister a WebSocket handler"""
        if handler in self.websocket_handlers:
            self.websocket_handlers.remove(handler)
            logger.info(f"Unregistered WebSocket handler: {handler}")

    async def notify(self, alert_data: Dict[str, Any], channels: Optional[List[NotificationChannel]] = None) -> Dict[str, bool]:
        """
        Send alert notification to configured channels

        Args:
            alert_data: Alert information
            channels: Specific channels to notify (None = all enabled)

        Returns:
            Dict mapping channel to success status
        """
        results = {}

        # Determine which channels to use
        if channels is None:
            channels = self._get_enabled_channels()

        # Send to each channel
        tasks = []
        for channel in channels:
            if channel == NotificationChannel.EMAIL and self.config.email_enabled:
                tasks.append(self._send_email(alert_data))
            elif channel == NotificationChannel.SLACK and self.config.slack_enabled:
                tasks.append(self._send_slack(alert_data))
            elif channel == NotificationChannel.WEBHOOK and self.config.webhook_enabled:
                tasks.append(self._send_webhook(alert_data))
            elif channel == NotificationChannel.WEBSOCKET and self.config.websocket_enabled:
                tasks.append(self._send_websocket(alert_data))

        # Execute all notifications concurrently
        if tasks:
            channel_results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, channel in enumerate([ch for ch in channels if ch != NotificationChannel.DATABASE]):
                results[channel.value] = not isinstance(channel_results[i], Exception)

        # Always log to database (synchronous for now)
        if NotificationChannel.DATABASE in channels or self.config.database_enabled:
            results['database'] = self._log_to_database(alert_data)

        return results

    def _get_enabled_channels(self) -> List[NotificationChannel]:
        """Get list of enabled notification channels"""
        channels = []
        if self.config.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        if self.config.slack_enabled:
            channels.append(NotificationChannel.SLACK)
        if self.config.webhook_enabled:
            channels.append(NotificationChannel.WEBHOOK)
        if self.config.websocket_enabled:
            channels.append(NotificationChannel.WEBSOCKET)
        if self.config.database_enabled:
            channels.append(NotificationChannel.DATABASE)
        return channels

    async def _send_email(self, alert_data: Dict[str, Any]) -> bool:
        """Send email notification"""
        try:
            import aiosmtplib
            from email.message import EmailMessage

            # Create email message
            message = EmailMessage()
            message['From'] = self.config.email_sender
            message['To'] = ', '.join(self.config.email_recipients)
            message['Subject'] = f"[{alert_data.get('severity', 'ALERT').upper()}] {alert_data.get('title', 'Performance Alert')}"

            # Email body
            body = self._format_email_body(alert_data)
            message.set_content(body)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=self.config.email_smtp_host,
                port=self.config.email_smtp_port,
                username=self.config.email_sender,
                password=self.config.email_password,
                use_tls=True
            )

            logger.info(f"Email notification sent for alert: {alert_data.get('alert_id')}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
            return False

    def _format_email_body(self, alert_data: Dict[str, Any]) -> str:
        """Format email body"""
        return f"""
Performance Alert Notification
{'=' * 50}

Alert Type: {alert_data.get('alert_type', 'Unknown')}
Severity: {alert_data.get('severity', 'Unknown')}
Campaign: {alert_data.get('campaign_name', 'N/A')}

Message: {alert_data.get('message', 'No message')}

Details:
{json.dumps(alert_data.get('details', {}), indent=2)}

Timestamp: {alert_data.get('timestamp', datetime.utcnow().isoformat())}

Action Required: {alert_data.get('action', 'Review campaign performance')}

--
GeminiVideo Performance Monitoring System
"""

    async def _send_slack(self, alert_data: Dict[str, Any]) -> bool:
        """Send Slack notification"""
        try:
            # Format Slack message
            payload = self._format_slack_message(alert_data)

            # Send to Slack webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.slack_webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent for alert: {alert_data.get('alert_id')}")
                        return True
                    else:
                        logger.error(f"Slack notification failed: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def _format_slack_message(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format Slack message with rich formatting"""
        severity = alert_data.get('severity', 'info')
        severity_emoji = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '⚡',
            'low': 'ℹ️',
            'info': '📊'
        }.get(severity.lower(), 'ℹ️')

        color = {
            'critical': '#FF0000',
            'high': '#FF8C00',
            'medium': '#FFD700',
            'low': '#00CED1',
            'info': '#1E90FF'
        }.get(severity.lower(), '#1E90FF')

        return {
            'channel': self.config.slack_channel,
            'username': 'Performance Alerts',
            'icon_emoji': ':chart_with_upwards_trend:',
            'attachments': [
                {
                    'color': color,
                    'title': f"{severity_emoji} {alert_data.get('title', 'Performance Alert')}",
                    'text': alert_data.get('message', ''),
                    'fields': [
                        {
                            'title': 'Campaign',
                            'value': alert_data.get('campaign_name', 'N/A'),
                            'short': True
                        },
                        {
                            'title': 'Severity',
                            'value': severity.upper(),
                            'short': True
                        },
                        {
                            'title': 'Type',
                            'value': alert_data.get('alert_type', 'Unknown'),
                            'short': True
                        },
                        {
                            'title': 'Timestamp',
                            'value': alert_data.get('timestamp', datetime.utcnow().isoformat()),
                            'short': True
                        },
                    ],
                    'footer': 'GeminiVideo Performance Monitoring',
                    'ts': int(datetime.utcnow().timestamp())
                }
            ]
        }

    async def _send_webhook(self, alert_data: Dict[str, Any]) -> bool:
        """Send webhook notification"""
        try:
            success_count = 0
            async with aiohttp.ClientSession() as session:
                for webhook_url in self.config.webhook_urls:
                    if not webhook_url.strip():
                        continue

                    try:
                        async with session.post(
                            webhook_url,
                            json=alert_data,
                            headers=self.config.webhook_headers
                        ) as response:
                            if response.status in [200, 201, 202]:
                                success_count += 1
                                logger.info(f"Webhook notification sent to: {webhook_url}")
                            else:
                                logger.error(f"Webhook failed ({webhook_url}): {response.status}")
                    except Exception as e:
                        logger.error(f"Webhook request failed ({webhook_url}): {e}")

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send webhook notifications: {e}")
            return False

    async def _send_websocket(self, alert_data: Dict[str, Any]) -> bool:
        """Send real-time WebSocket notification"""
        try:
            if not self.websocket_handlers:
                logger.warning("No WebSocket handlers registered")
                return False

            success_count = 0
            for handler in self.websocket_handlers:
                try:
                    # Send to WebSocket handler
                    await handler.send_json({
                        'type': 'alert',
                        'data': alert_data
                    })
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to send to WebSocket handler: {e}")

            return success_count > 0

        except Exception as e:
            logger.error(f"Failed to send WebSocket notifications: {e}")
            return False

    def _log_to_database(self, alert_data: Dict[str, Any]) -> bool:
        """Log alert to database for frontend retrieval"""
        try:
            # This would typically save to a database
            # For now, we'll log it for the API to pick up
            logger.info(f"Alert logged: {json.dumps(alert_data)}")
            return True
        except Exception as e:
            logger.error(f"Failed to log alert to database: {e}")
            return False

    def send_test_notification(self, channel: NotificationChannel) -> bool:
        """Send a test notification to verify configuration"""
        test_alert = {
            'alert_id': 'test_' + datetime.utcnow().strftime('%Y%m%d_%H%M%S'),
            'alert_type': 'test',
            'severity': 'info',
            'title': 'Test Alert',
            'message': 'This is a test alert to verify notification configuration',
            'campaign_name': 'Test Campaign',
            'timestamp': datetime.utcnow().isoformat(),
            'details': {
                'test': True
            }
        }

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        result = loop.run_until_complete(self.notify(test_alert, [channel]))
        return result.get(channel.value, False)


# Global instance
alert_notifier = AlertNotifier()
