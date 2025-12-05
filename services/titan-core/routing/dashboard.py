"""
Routing Dashboard API

Provides real-time visibility into:
- Model distribution and usage
- Cost metrics and savings
- Quality/confidence scores
- Escalation patterns
- A/B test results

Usage:
    from titan_core.routing.dashboard import router_dashboard

    # Get dashboard data
    dashboard_data = router_dashboard.get_dashboard()
"""

import logging
from typing import Dict, Any, List
from datetime import datetime

from .model_router import router
from .analytics import analytics
from .ab_testing import ab_test_manager

logger = logging.getLogger(__name__)


class RoutingDashboard:
    """
    Real-time dashboard for routing performance monitoring

    Provides comprehensive view of:
    - Current routing statistics
    - Cost analysis and savings
    - Model performance metrics
    - A/B test results
    - Actionable insights
    """

    def __init__(self):
        """Initialize dashboard"""
        self.router = router
        self.analytics = analytics
        self.ab_test_manager = ab_test_manager

    def get_dashboard(self) -> Dict[str, Any]:
        """
        Get complete dashboard data

        Returns:
            Comprehensive dashboard data with all metrics
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overview": self._get_overview(),
            "cost_analysis": self._get_cost_analysis(),
            "model_performance": self._get_model_performance(),
            "quality_metrics": self._get_quality_metrics(),
            "ab_testing": self._get_ab_testing_status(),
            "insights": self._get_insights(),
            "alerts": self._get_alerts()
        }

    def _get_overview(self) -> Dict[str, Any]:
        """Get high-level overview metrics"""
        router_stats = self.router.get_stats()

        return {
            "total_requests": router_stats["total_requests"],
            "avg_cost_per_request": router_stats.get("avg_cost_per_request", 0),
            "cost_savings_percentage": router_stats.get("cost_savings_pct", 0),
            "avg_confidence": round(router_stats["avg_confidence"], 3),
            "escalation_rate": router_stats.get("escalation_rate", 0),
            "status": "healthy" if router_stats["avg_confidence"] > 0.7 else "warning"
        }

    def _get_cost_analysis(self) -> Dict[str, Any]:
        """Get detailed cost analysis"""
        router_stats = self.router.get_stats()
        analytics_summary = self.analytics.get_summary()

        if analytics_summary.get("status") == "no_data":
            return {
                "total_cost": 0,
                "baseline_cost": 0,
                "savings": 0,
                "by_model": {},
                "trend": []
            }

        summary = analytics_summary["summary"]

        return {
            "total_cost": summary["total_cost"],
            "baseline_cost": summary["baseline_cost"],
            "savings": summary["cost_savings"],
            "savings_percentage": summary["cost_savings_percentage"],
            "avg_per_request": summary["avg_cost_per_request"],
            "by_model": analytics_summary["by_model"],
            "by_complexity": analytics_summary["by_complexity"],
            "trend": self.analytics.get_time_series(hours=24)
        }

    def _get_model_performance(self) -> Dict[str, Any]:
        """Get model-by-model performance metrics"""
        router_stats = self.router.get_stats()

        if router_stats["total_requests"] == 0:
            return {"models": {}}

        model_dist = router_stats.get("model_distribution", {})

        model_data = {}
        for model, percentage in model_dist.items():
            count = router_stats["by_model"].get(model, 0)
            model_data[model] = {
                "usage_percentage": round(percentage, 2),
                "request_count": count,
                "avg_confidence": 0.8,  # Would need to track this separately
                "cost_per_1m_tokens": self.router._calculate_cost(model, 1_000_000, 1_000_000)
            }

        return {
            "models": model_data,
            "most_used": max(model_dist.items(), key=lambda x: x[1])[0] if model_dist else None,
            "total_models_used": len(model_data)
        }

    def _get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality and confidence metrics"""
        router_stats = self.router.get_stats()

        return {
            "avg_confidence": round(router_stats["avg_confidence"], 3),
            "escalation_rate": router_stats.get("escalation_rate", 0),
            "by_complexity": router_stats.get("complexity_distribution", {}),
            "confidence_threshold": self.router.escalation_threshold,
            "escalation_enabled": self.router.enable_escalation
        }

    def _get_ab_testing_status(self) -> Dict[str, Any]:
        """Get A/B testing status and results"""
        if not self.ab_test_manager.enabled:
            return {
                "enabled": False,
                "message": "A/B testing is not enabled"
            }

        return {
            "enabled": True,
            **self.ab_test_manager.get_results()
        }

    def _get_insights(self) -> List[str]:
        """Get actionable insights"""
        analytics_summary = self.analytics.get_summary()

        if analytics_summary.get("status") == "no_data":
            return ["No data available yet. Start routing requests to see insights."]

        return analytics_summary.get("insights", [])

    def _get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts based on thresholds"""
        alerts = []
        router_stats = self.router.get_stats()

        if router_stats["total_requests"] == 0:
            return alerts

        # Low confidence alert
        if router_stats["avg_confidence"] < 0.6:
            alerts.append({
                "level": "warning",
                "type": "low_confidence",
                "message": f"Average confidence is low ({router_stats['avg_confidence']:.2f})",
                "action": "Consider using more powerful models or reviewing task complexity classification"
            })

        # High escalation rate alert
        escalation_rate = router_stats.get("escalation_rate", 0)
        if escalation_rate > 30:
            alerts.append({
                "level": "warning",
                "type": "high_escalation",
                "message": f"Escalation rate is high ({escalation_rate:.1f}%)",
                "action": "Review initial model selection strategy or adjust confidence threshold"
            })

        # Cost alert (if costs are unusually high)
        avg_cost = router_stats.get("avg_cost_per_request", 0)
        if avg_cost > 0.01:  # More than 1 cent per request
            alerts.append({
                "level": "info",
                "type": "high_cost",
                "message": f"Average cost per request is ${avg_cost:.4f}",
                "action": "Review if cost optimization mode is enabled and working correctly"
            })

        # Low savings alert
        savings_pct = router_stats.get("cost_savings_pct", 0)
        if savings_pct < 30 and router_stats["total_requests"] > 10:
            alerts.append({
                "level": "warning",
                "type": "low_savings",
                "message": f"Cost savings are only {savings_pct:.1f}%",
                "action": "Enable cost optimization mode or review task complexity classification"
            })

        return alerts

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for quick view"""
        cost_analysis = self._get_cost_analysis()

        return {
            "total_cost": cost_analysis["total_cost"],
            "baseline_cost": cost_analysis.get("baseline_cost", 0),
            "savings": cost_analysis.get("savings", 0),
            "savings_percentage": cost_analysis.get("savings_percentage", 0)
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for quick view"""
        overview = self._get_overview()
        quality = self._get_quality_metrics()

        return {
            "total_requests": overview["total_requests"],
            "avg_confidence": quality["avg_confidence"],
            "escalation_rate": quality["escalation_rate"],
            "status": overview["status"]
        }

    def export_dashboard(self, output_path: str):
        """
        Export dashboard data to JSON file

        Args:
            output_path: Path to save dashboard data
        """
        import json

        dashboard_data = self.get_dashboard()

        try:
            with open(output_path, 'w') as f:
                json.dump(dashboard_data, f, indent=2)
            logger.info(f"Dashboard exported to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export dashboard: {e}")


# Global singleton instance
router_dashboard = RoutingDashboard()
