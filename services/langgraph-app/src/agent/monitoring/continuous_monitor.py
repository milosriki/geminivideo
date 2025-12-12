"""24/7 Continuous monitoring system."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

from agent.core.orchestrator import AgentOrchestrator, AgentTask, OrchestrationStrategy
from agent.agents import (
    PerformanceMonitoringAgent,
    SecurityAgent,
    ErrorRecoveryAgent,
    CampaignOptimizationAgent,
)

logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """24/7 monitoring agent that runs continuously."""

    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.running = False
        self.orchestrator = AgentOrchestrator(
            strategy=OrchestrationStrategy.PARALLEL
        )

        # Initialize monitoring agents
        self.monitoring_agents = {
            "performance": PerformanceMonitoringAgent(),
            "security": SecurityAgent(),
            "error_recovery": ErrorRecoveryAgent(),
            "campaign_optimization": CampaignOptimizationAgent(),
        }

        # Register agents
        for name, agent in self.monitoring_agents.items():
            self.orchestrator.register_agent(agent)

    async def start(self):
        """Start continuous monitoring."""
        self.running = True
        logger.info("24/7 Monitoring started")

        while self.running:
            try:
                await self._monitoring_cycle()
                await asyncio.sleep(self.interval_minutes * 60)
            except Exception as e:
                logger.error(f"Monitoring cycle error: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def stop(self):
        """Stop monitoring."""
        self.running = False
        logger.info("24/7 Monitoring stopped")

    async def _monitoring_cycle(self):
        """Execute one monitoring cycle."""
        logger.info("Starting monitoring cycle...")

        try:
            # Create monitoring tasks
            tasks = [
                AgentTask(
                    agent=self.monitoring_agents["performance"],
                    input_data={
                        "operation": "monitor",
                        "metrics": {},
                    },
                    priority=1,
                ),
                AgentTask(
                    agent=self.monitoring_agents["security"],
                    input_data={
                        "operation": "scan",
                    },
                    priority=1,
                ),
                AgentTask(
                    agent=self.monitoring_agents["error_recovery"],
                    input_data={
                        "operation": "analyze",
                        "error": {},
                    },
                    priority=2,
                ),
                AgentTask(
                    agent=self.monitoring_agents["campaign_optimization"],
                    input_data={
                        "operation": "suggest_improvements",
                        "campaign_id": None,  # All campaigns
                    },
                    priority=3,
                ),
            ]

            # Execute in parallel
            result = await self.orchestrator.orchestrate(
                tasks, strategy=OrchestrationStrategy.PARALLEL
            )

            # Process alerts
            alerts = await self._process_alerts(result)

            # Send alerts if any
            if alerts:
                await self._send_alerts(alerts)

            logger.info(f"Monitoring cycle complete - {len(alerts)} alerts")

        except Exception as e:
            logger.error(f"Monitoring cycle failed: {e}", exc_info=True)

    async def _process_alerts(
        self, result: Any
    ) -> List[Dict[str, Any]]:
        """Process monitoring results into alerts."""
        alerts = []

        for agent_name, agent_result in result.results.items():
            if not agent_result.success:
                alerts.append(
                    {
                        "type": "error",
                        "agent": agent_name,
                        "message": agent_result.error,
                        "severity": "high",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            # Check for specific alert conditions
            if agent_name == "performance":
                data = agent_result.data or {}
                if data.get("metrics", {}).get("error_rate", 0) > 0.05:
                    alerts.append(
                        {
                            "type": "performance",
                            "agent": agent_name,
                            "message": "High error rate detected",
                            "severity": "medium",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

            elif agent_name == "security":
                data = agent_result.data or {}
                threats = data.get("threats_detected", 0)
                if threats > 0:
                    alerts.append(
                        {
                            "type": "security",
                            "agent": agent_name,
                            "message": f"{threats} security threats detected",
                            "severity": "high",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

        return alerts

    async def _send_alerts(self, alerts: List[Dict[str, Any]]):
        """Send alerts (would integrate with Slack/Telegram in production)."""
        for alert in alerts:
            logger.warning(
                f"🚨 ALERT [{alert['severity'].upper()}]: {alert['message']}"
            )

        # In production:
        # await send_slack_message(alerts)
        # await send_telegram_message(alerts)

    async def run_once(self):
        """Run monitoring cycle once (for cron jobs)."""
        await self._monitoring_cycle()


# Global instance
continuous_monitor = ContinuousMonitor(interval_minutes=5)

