"""Observability and monitoring for agents."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for agent monitoring."""

    agent_name: str
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    last_execution: Optional[datetime] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)


class ObservabilityManager:
    """Manages observability and monitoring for all agents."""

    def __init__(self):
        self.metrics: Dict[str, AgentMetrics] = {}
        self.execution_history: List[Dict[str, Any]] = []

    def record_execution(
        self,
        agent_name: str,
        success: bool,
        execution_time: float,
        error: Optional[str] = None,
    ):
        """Record agent execution."""
        if agent_name not in self.metrics:
            self.metrics[agent_name] = AgentMetrics(agent_name=agent_name)

        metrics = self.metrics[agent_name]
        metrics.execution_count += 1
        metrics.last_execution = datetime.now()

        if success:
            metrics.success_count += 1
        else:
            metrics.error_count += 1
            if error:
                metrics.errors.append({
                    "timestamp": datetime.now().isoformat(),
                    "error": error,
                })

        metrics.total_execution_time += execution_time
        metrics.avg_execution_time = (
            metrics.total_execution_time / metrics.execution_count
        )

        # Record in history
        self.execution_history.append({
            "agent_name": agent_name,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "execution_time": execution_time,
            "error": error,
        })

        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]

    def get_metrics(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for agent(s)."""
        if agent_name:
            if agent_name in self.metrics:
                metrics = self.metrics[agent_name]
                return {
                    "agent_name": metrics.agent_name,
                    "execution_count": metrics.execution_count,
                    "success_count": metrics.success_count,
                    "error_count": metrics.error_count,
                    "success_rate": (
                        metrics.success_count / metrics.execution_count
                        if metrics.execution_count > 0
                        else 0.0
                    ),
                    "avg_execution_time": metrics.avg_execution_time,
                    "last_execution": (
                        metrics.last_execution.isoformat()
                        if metrics.last_execution
                        else None
                    ),
                    "recent_errors": metrics.errors[-10:],  # Last 10 errors
                }
            return {}

        # Return all metrics
        return {
            name: self.get_metrics(name) for name in self.metrics.keys()
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status."""
        total_executions = sum(m.execution_count for m in self.metrics.values())
        total_errors = sum(m.error_count for m in self.metrics.values())
        total_success = sum(m.success_count for m in self.metrics.values())

        overall_success_rate = (
            total_success / total_executions if total_executions > 0 else 0.0
        )

        return {
            "status": "healthy" if overall_success_rate > 0.9 else "degraded",
            "total_executions": total_executions,
            "total_success": total_success,
            "total_errors": total_errors,
            "overall_success_rate": overall_success_rate,
            "agents": len(self.metrics),
            "timestamp": datetime.now().isoformat(),
        }

    def get_recent_executions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent execution history."""
        return self.execution_history[-limit:]


# Global observability manager
observability_manager = ObservabilityManager()

