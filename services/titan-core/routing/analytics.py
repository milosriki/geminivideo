"""
Routing Analytics - Track and analyze model routing performance

Key Metrics:
- Cost savings vs. baseline (always using premium models)
- Quality metrics (confidence, accuracy)
- Model distribution and usage patterns
- Escalation rates and triggers
- Performance by task complexity
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class RoutingAnalytics:
    """
    Analytics engine for model routing performance

    Tracks:
    - Request history with outcomes
    - Cost metrics and savings
    - Quality metrics and confidence scores
    - Model performance by task type
    - Escalation patterns
    """

    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize analytics tracker

        Args:
            storage_path: Path to store analytics data (defaults to /tmp)
        """
        self.storage_path = storage_path or "/tmp/routing_analytics.jsonl"
        self.session_data = []

        # In-memory aggregated metrics
        self.metrics = {
            "total_requests": 0,
            "total_cost": 0.0,
            "total_cost_baseline": 0.0,  # Cost if always using premium
            "total_escalations": 0,
            "by_model": defaultdict(lambda: {
                "count": 0,
                "total_cost": 0.0,
                "avg_confidence": 0.0,
                "escalation_rate": 0.0
            }),
            "by_complexity": defaultdict(lambda: {
                "count": 0,
                "total_cost": 0.0,
                "avg_confidence": 0.0
            }),
            "by_task_type": defaultdict(lambda: {
                "count": 0,
                "preferred_model": None,
                "avg_cost": 0.0
            }),
            "time_series": []  # For time-based analysis
        }

        logger.info(f"RoutingAnalytics initialized (storage: {self.storage_path})")

    def log_request(
        self,
        task: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """
        Log a routing request and its outcome

        Args:
            task: Original task dict
            result: Routing result with model, cost, confidence, etc.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "task_type": task.get('type', 'general'),
            "complexity": result['complexity'],
            "model_used": result['model_used'],
            "cost": result['cost'],
            "confidence": result['confidence'],
            "escalated": result.get('escalated', False),
            "execution_time": result.get('execution_time', 0),
            "text_length": len(task.get('text', ''))
        }

        # Add to session data
        self.session_data.append(entry)

        # Update aggregated metrics
        self._update_metrics(entry)

        # Persist to storage
        self._persist_entry(entry)

    def _update_metrics(self, entry: Dict[str, Any]):
        """Update aggregated metrics with new entry"""
        # Total metrics
        self.metrics["total_requests"] += 1
        self.metrics["total_cost"] += entry['cost']

        # Baseline cost (assume premium model at $15/1M tokens, ~1000 tokens avg)
        baseline_cost = (entry['text_length'] / 4 + 250) / 1_000_000 * 15 * 4  # Input + output
        self.metrics["total_cost_baseline"] += baseline_cost

        if entry['escalated']:
            self.metrics["total_escalations"] += 1

        # By model metrics
        model = entry['model_used']
        model_stats = self.metrics["by_model"][model]
        model_stats["count"] += 1
        model_stats["total_cost"] += entry['cost']

        # Update rolling average confidence
        n = model_stats["count"]
        model_stats["avg_confidence"] = (
            (model_stats["avg_confidence"] * (n - 1) + entry['confidence']) / n
        )

        # By complexity metrics
        complexity = entry['complexity']
        complexity_stats = self.metrics["by_complexity"][complexity]
        complexity_stats["count"] += 1
        complexity_stats["total_cost"] += entry['cost']

        n = complexity_stats["count"]
        complexity_stats["avg_confidence"] = (
            (complexity_stats["avg_confidence"] * (n - 1) + entry['confidence']) / n
        )

        # By task type metrics
        task_type = entry['task_type']
        task_stats = self.metrics["by_task_type"][task_type]
        task_stats["count"] += 1
        task_stats["avg_cost"] += entry['cost']

        # Time series data (for charting)
        self.metrics["time_series"].append({
            "timestamp": entry['timestamp'],
            "cost": entry['cost'],
            "confidence": entry['confidence'],
            "model": model
        })

    def _persist_entry(self, entry: Dict[str, Any]):
        """Persist entry to JSONL file"""
        try:
            # Ensure directory exists
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

            # Append to JSONL file
            with open(self.storage_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist analytics entry: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """
        Get analytics summary with key insights

        Returns:
            Comprehensive summary of routing performance
        """
        if self.metrics["total_requests"] == 0:
            return {
                "status": "no_data",
                "message": "No routing requests logged yet"
            }

        total = self.metrics["total_requests"]
        total_cost = self.metrics["total_cost"]
        baseline_cost = self.metrics["total_cost_baseline"]

        # Calculate cost savings
        cost_savings = baseline_cost - total_cost
        cost_savings_pct = (cost_savings / baseline_cost * 100) if baseline_cost > 0 else 0

        # Model distribution
        model_dist = {
            model: {
                "count": stats["count"],
                "percentage": (stats["count"] / total * 100),
                "avg_cost": stats["total_cost"] / stats["count"],
                "avg_confidence": round(stats["avg_confidence"], 3)
            }
            for model, stats in self.metrics["by_model"].items()
        }

        # Complexity distribution
        complexity_dist = {
            complexity: {
                "count": stats["count"],
                "percentage": (stats["count"] / total * 100),
                "avg_cost": stats["total_cost"] / stats["count"],
                "avg_confidence": round(stats["avg_confidence"], 3)
            }
            for complexity, stats in self.metrics["by_complexity"].items()
        }

        # Escalation rate
        escalation_rate = (self.metrics["total_escalations"] / total * 100)

        return {
            "summary": {
                "total_requests": total,
                "total_cost": round(total_cost, 4),
                "baseline_cost": round(baseline_cost, 4),
                "cost_savings": round(cost_savings, 4),
                "cost_savings_percentage": round(cost_savings_pct, 2),
                "avg_cost_per_request": round(total_cost / total, 6),
                "escalation_rate": round(escalation_rate, 2)
            },
            "by_model": model_dist,
            "by_complexity": complexity_dist,
            "insights": self._generate_insights()
        }

    def _generate_insights(self) -> List[str]:
        """Generate actionable insights from analytics data"""
        insights = []
        total = self.metrics["total_requests"]

        if total == 0:
            return insights

        # Cost savings insight
        baseline = self.metrics["total_cost_baseline"]
        actual = self.metrics["total_cost"]
        if baseline > 0:
            savings_pct = (baseline - actual) / baseline * 100
            if savings_pct > 70:
                insights.append(
                    f"Excellent cost optimization: {savings_pct:.1f}% cost savings vs. always using premium models"
                )
            elif savings_pct > 40:
                insights.append(
                    f"Good cost optimization: {savings_pct:.1f}% savings. Consider routing more simple tasks to mini models"
                )
            else:
                insights.append(
                    f"Low cost savings ({savings_pct:.1f}%). Review task complexity classification"
                )

        # Escalation rate insight
        escalation_rate = (self.metrics["total_escalations"] / total * 100)
        if escalation_rate > 30:
            insights.append(
                f"High escalation rate ({escalation_rate:.1f}%). Consider adjusting confidence threshold or improving initial model selection"
            )
        elif escalation_rate < 5:
            insights.append(
                f"Low escalation rate ({escalation_rate:.1f}%). System is routing effectively"
            )

        # Model usage insights
        model_usage = sorted(
            self.metrics["by_model"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        if model_usage:
            top_model = model_usage[0]
            pct = (top_model[1]["count"] / total * 100)
            insights.append(
                f"Most used model: {top_model[0]} ({pct:.1f}% of requests)"
            )

        # Confidence insights
        avg_confidences = [
            stats["avg_confidence"]
            for stats in self.metrics["by_model"].values()
            if stats["count"] > 0
        ]
        if avg_confidences:
            overall_confidence = sum(avg_confidences) / len(avg_confidences)
            if overall_confidence < 0.7:
                insights.append(
                    f"Low average confidence ({overall_confidence:.2f}). Consider using more powerful models"
                )

        return insights

    def get_cost_breakdown(self) -> Dict[str, Any]:
        """Get detailed cost breakdown by model and complexity"""
        return {
            "by_model": {
                model: {
                    "total_cost": round(stats["total_cost"], 4),
                    "count": stats["count"],
                    "avg_cost": round(stats["total_cost"] / stats["count"], 6) if stats["count"] > 0 else 0
                }
                for model, stats in self.metrics["by_model"].items()
            },
            "by_complexity": {
                complexity: {
                    "total_cost": round(stats["total_cost"], 4),
                    "count": stats["count"],
                    "avg_cost": round(stats["total_cost"] / stats["count"], 6) if stats["count"] > 0 else 0
                }
                for complexity, stats in self.metrics["by_complexity"].items()
            }
        }

    def get_time_series(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get time series data for the last N hours

        Args:
            hours: Number of hours to look back

        Returns:
            List of time series data points
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        return [
            entry for entry in self.metrics["time_series"]
            if entry["timestamp"] >= cutoff_str
        ]

    def export_report(self, output_path: str):
        """
        Export comprehensive analytics report to JSON file

        Args:
            output_path: Path to save report
        """
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": self.get_summary(),
            "cost_breakdown": self.get_cost_breakdown(),
            "time_series": self.get_time_series(hours=168),  # Last week
            "raw_metrics": self.metrics
        }

        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Analytics report exported to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export report: {e}")

    def reset(self):
        """Reset all analytics data (for testing)"""
        self.session_data = []
        self.metrics = {
            "total_requests": 0,
            "total_cost": 0.0,
            "total_cost_baseline": 0.0,
            "total_escalations": 0,
            "by_model": defaultdict(lambda: {
                "count": 0,
                "total_cost": 0.0,
                "avg_confidence": 0.0
            }),
            "by_complexity": defaultdict(lambda: {
                "count": 0,
                "total_cost": 0.0,
                "avg_confidence": 0.0
            }),
            "by_task_type": defaultdict(lambda: {
                "count": 0,
                "preferred_model": None,
                "avg_cost": 0.0
            }),
            "time_series": []
        }


# Global singleton instance
analytics = RoutingAnalytics(
    storage_path=os.getenv("ROUTING_ANALYTICS_PATH", "/tmp/routing_analytics.jsonl")
)
