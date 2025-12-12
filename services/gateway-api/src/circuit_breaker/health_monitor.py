"""
Health Monitor for Circuit Breaker System
==========================================

Continuously monitors API health, tracks latency percentiles,
detects degraded service states, and sends alerts on circuit state changes.

Author: Agent 9 - Circuit Breaker Builder
"""

import time
import logging
import asyncio
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Service health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckConfig:
    """Configuration for health monitoring"""
    check_interval_seconds: float = 30.0    # How often to check health
    check_timeout_seconds: float = 10.0     # Timeout for health check

    # Latency thresholds (milliseconds)
    latency_warning_ms: float = 1000.0      # Warning if p95 exceeds this
    latency_critical_ms: float = 3000.0     # Critical if p95 exceeds this

    # Error rate thresholds
    error_rate_warning: float = 0.05        # 5% error rate warning
    error_rate_critical: float = 0.20       # 20% error rate critical

    # History tracking
    history_size: int = 100                 # Keep last N health checks
    alert_cooldown_seconds: int = 300       # Don't spam alerts (5 minutes)


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service_name: str
    status: HealthStatus
    timestamp: float = field(default_factory=time.time)

    # Metrics
    response_time_ms: Optional[float] = None
    error: Optional[str] = None

    # Details
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ServiceHealthMetrics:
    """Aggregated health metrics for a service"""
    service_name: str
    status: HealthStatus

    # Latency metrics (milliseconds)
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    latency_p99: float = 0.0
    avg_latency: float = 0.0

    # Error metrics
    total_checks: int = 0
    successful_checks: int = 0
    failed_checks: int = 0
    error_rate: float = 0.0

    # Availability
    uptime_percentage: float = 100.0
    last_check_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None

    # Recent history
    recent_results: deque = field(default_factory=lambda: deque(maxlen=100))


class HealthMonitor:
    """
    Monitors service health and tracks metrics over time

    Usage:
        monitor = HealthMonitor()

        # Register a service with health check function
        async def check_openai_health():
            # Perform health check
            return True

        monitor.register_service(
            "openai_api",
            check_openai_health,
            config=HealthCheckConfig()
        )

        # Start monitoring
        await monitor.start()

        # Get current health
        health = monitor.get_service_health("openai_api")
    """

    def __init__(self):
        self._services: Dict[str, ServiceHealthMetrics] = {}
        self._health_checks: Dict[str, Callable] = {}
        self._configs: Dict[str, HealthCheckConfig] = {}
        self._alert_handlers: List[Callable] = []
        self._last_alert_time: Dict[str, float] = {}

        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("Health monitor initialized")

    def register_service(
        self,
        name: str,
        health_check: Callable,
        config: Optional[HealthCheckConfig] = None
    ):
        """
        Register a service for health monitoring

        Args:
            name: Service name
            health_check: Async function that returns bool (True = healthy)
            config: Health check configuration
        """
        self._services[name] = ServiceHealthMetrics(
            service_name=name,
            status=HealthStatus.UNKNOWN
        )
        self._health_checks[name] = health_check
        self._configs[name] = config or HealthCheckConfig()

        logger.info(f"Registered health monitoring for service: {name}")

    def register_alert_handler(self, handler: Callable):
        """
        Register a function to be called when alerts are triggered

        Handler signature: async def handler(service_name: str, alert_type: str, details: dict)
        """
        self._alert_handlers.append(handler)
        logger.info(f"Registered alert handler: {handler.__name__}")

    async def check_service_health(self, service_name: str) -> HealthCheckResult:
        """
        Perform a single health check for a service

        Args:
            service_name: Name of the service to check

        Returns:
            HealthCheckResult with status and metrics
        """
        if service_name not in self._health_checks:
            raise ValueError(f"Service '{service_name}' not registered")

        config = self._configs[service_name]
        health_check = self._health_checks[service_name]

        start_time = time.time()
        result = HealthCheckResult(service_name=service_name, status=HealthStatus.UNKNOWN)

        try:
            # Execute health check with timeout
            is_healthy = await asyncio.wait_for(
                health_check(),
                timeout=config.check_timeout_seconds
            )

            response_time_ms = (time.time() - start_time) * 1000
            result.response_time_ms = response_time_ms

            if is_healthy:
                # Determine status based on latency
                if response_time_ms > config.latency_critical_ms:
                    result.status = HealthStatus.DEGRADED
                    result.details["reason"] = "High latency (critical threshold)"
                elif response_time_ms > config.latency_warning_ms:
                    result.status = HealthStatus.DEGRADED
                    result.details["reason"] = "High latency (warning threshold)"
                else:
                    result.status = HealthStatus.HEALTHY
            else:
                result.status = HealthStatus.UNHEALTHY
                result.details["reason"] = "Health check returned False"

        except asyncio.TimeoutError:
            result.status = HealthStatus.UNHEALTHY
            result.error = "Health check timed out"
            result.response_time_ms = config.check_timeout_seconds * 1000

        except Exception as e:
            result.status = HealthStatus.UNHEALTHY
            result.error = str(e)
            result.response_time_ms = (time.time() - start_time) * 1000

        # Update metrics
        self._update_metrics(service_name, result)

        return result

    def _update_metrics(self, service_name: str, result: HealthCheckResult):
        """Update service metrics with new health check result"""
        metrics = self._services[service_name]
        config = self._configs[service_name]

        # Add to history
        metrics.recent_results.append(result)

        # Update counters
        metrics.total_checks += 1
        if result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]:
            metrics.successful_checks += 1
            metrics.last_success_time = result.timestamp
        else:
            metrics.failed_checks += 1
            metrics.last_failure_time = result.timestamp

        metrics.last_check_time = result.timestamp

        # Calculate error rate
        if metrics.total_checks > 0:
            metrics.error_rate = metrics.failed_checks / metrics.total_checks

        # Calculate uptime percentage
        if metrics.total_checks > 0:
            metrics.uptime_percentage = (
                metrics.successful_checks / metrics.total_checks * 100
            )

        # Calculate latency percentiles from recent history
        latencies = [
            r.response_time_ms
            for r in metrics.recent_results
            if r.response_time_ms is not None
        ]

        if latencies:
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)

            metrics.avg_latency = statistics.mean(latencies)
            metrics.latency_p50 = sorted_latencies[int(n * 0.50)] if n > 0 else 0
            metrics.latency_p95 = sorted_latencies[int(n * 0.95)] if n > 0 else 0
            metrics.latency_p99 = sorted_latencies[int(n * 0.99)] if n > 0 else 0

        # Determine overall status
        if metrics.error_rate > config.error_rate_critical:
            metrics.status = HealthStatus.UNHEALTHY
        elif (
            metrics.error_rate > config.error_rate_warning or
            metrics.latency_p95 > config.latency_warning_ms
        ):
            metrics.status = HealthStatus.DEGRADED
        else:
            metrics.status = HealthStatus.HEALTHY

        # Check if we should send alerts
        self._check_alerts(service_name, metrics, config)

    def _check_alerts(
        self,
        service_name: str,
        metrics: ServiceHealthMetrics,
        config: HealthCheckConfig
    ):
        """Check if alerts should be triggered"""
        now = time.time()
        last_alert = self._last_alert_time.get(service_name, 0)

        # Check cooldown
        if now - last_alert < config.alert_cooldown_seconds:
            return

        alerts = []

        # High error rate alert
        if metrics.error_rate > config.error_rate_critical:
            alerts.append({
                "type": "high_error_rate",
                "severity": "critical",
                "message": f"Error rate is {metrics.error_rate*100:.1f}% (threshold: {config.error_rate_critical*100:.1f}%)",
                "metrics": {
                    "error_rate": metrics.error_rate,
                    "failed_checks": metrics.failed_checks,
                    "total_checks": metrics.total_checks
                }
            })
        elif metrics.error_rate > config.error_rate_warning:
            alerts.append({
                "type": "elevated_error_rate",
                "severity": "warning",
                "message": f"Error rate is {metrics.error_rate*100:.1f}% (threshold: {config.error_rate_warning*100:.1f}%)",
                "metrics": {
                    "error_rate": metrics.error_rate
                }
            })

        # High latency alert
        if metrics.latency_p95 > config.latency_critical_ms:
            alerts.append({
                "type": "high_latency",
                "severity": "critical",
                "message": f"P95 latency is {metrics.latency_p95:.0f}ms (threshold: {config.latency_critical_ms:.0f}ms)",
                "metrics": {
                    "p50": metrics.latency_p50,
                    "p95": metrics.latency_p95,
                    "p99": metrics.latency_p99
                }
            })
        elif metrics.latency_p95 > config.latency_warning_ms:
            alerts.append({
                "type": "elevated_latency",
                "severity": "warning",
                "message": f"P95 latency is {metrics.latency_p95:.0f}ms (threshold: {config.latency_warning_ms:.0f}ms)",
                "metrics": {
                    "p95": metrics.latency_p95
                }
            })

        # Send alerts
        if alerts:
            self._last_alert_time[service_name] = now
            asyncio.create_task(self._send_alerts(service_name, alerts))

    async def _send_alerts(self, service_name: str, alerts: List[Dict]):
        """Send alerts to all registered handlers"""
        for alert in alerts:
            logger.warning(
                f"HEALTH ALERT [{service_name}] {alert['severity'].upper()}: "
                f"{alert['message']}"
            )

            for handler in self._alert_handlers:
                try:
                    await handler(service_name, alert["type"], alert)
                except Exception as e:
                    logger.error(f"Alert handler failed: {e}")

    def get_service_health(self, service_name: str) -> Optional[ServiceHealthMetrics]:
        """Get current health metrics for a service"""
        return self._services.get(service_name)

    def get_all_health(self) -> Dict[str, ServiceHealthMetrics]:
        """Get health metrics for all services"""
        return self._services.copy()

    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of all service health"""
        summary = {
            "timestamp": time.time(),
            "total_services": len(self._services),
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "unknown": 0,
            "services": {}
        }

        for name, metrics in self._services.items():
            # Count by status
            if metrics.status == HealthStatus.HEALTHY:
                summary["healthy"] += 1
            elif metrics.status == HealthStatus.DEGRADED:
                summary["degraded"] += 1
            elif metrics.status == HealthStatus.UNHEALTHY:
                summary["unhealthy"] += 1
            else:
                summary["unknown"] += 1

            # Add service summary
            summary["services"][name] = {
                "status": metrics.status.value,
                "uptime": round(metrics.uptime_percentage, 2),
                "error_rate": round(metrics.error_rate * 100, 2),
                "latency_p95_ms": round(metrics.latency_p95, 2),
                "last_check": metrics.last_check_time
            }

        return summary

    async def start(self):
        """Start continuous health monitoring"""
        if self._running:
            logger.warning("Health monitor already running")
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")

    async def stop(self):
        """Stop health monitoring"""
        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Check all services in parallel
                tasks = [
                    self.check_service_health(name)
                    for name in self._services.keys()
                ]

                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)

                # Wait for next check interval (use minimum interval from all configs)
                min_interval = min(
                    (config.check_interval_seconds for config in self._configs.values()),
                    default=30.0
                )
                await asyncio.sleep(min_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait before retrying


# Global health monitor instance
global_monitor = HealthMonitor()
