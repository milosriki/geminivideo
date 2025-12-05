"""
A/B Testing for Model Routing Strategies

Test different routing strategies to optimize for:
- Cost reduction
- Quality/confidence
- Latency
- Escalation rates

Strategies:
- Strategy A: Aggressive cost optimization (always start with mini)
- Strategy B: Quality-first (start with standard models)
- Strategy C: Dynamic (adaptive based on past performance)
- Strategy D: Task-type specific routing
"""

import os
import logging
import random
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """Different routing strategies for A/B testing"""
    COST_AGGRESSIVE = "cost_aggressive"      # Always start with cheapest
    QUALITY_FIRST = "quality_first"          # Start with better models
    DYNAMIC_ADAPTIVE = "dynamic_adaptive"    # Learn from past performance
    TASK_TYPE_OPTIMIZED = "task_type_optimized"  # Route by task type
    CONTROL = "control"                      # Current production strategy


class ABTestManager:
    """
    A/B Testing manager for routing strategies

    Features:
    - Traffic splitting between strategies
    - Performance tracking per strategy
    - Statistical significance testing
    - Automatic winner selection
    """

    def __init__(
        self,
        enabled: bool = False,
        traffic_split: Optional[Dict[RoutingStrategy, float]] = None
    ):
        """
        Initialize A/B test manager

        Args:
            enabled: Whether A/B testing is enabled
            traffic_split: Traffic allocation per strategy (must sum to 1.0)
        """
        self.enabled = enabled

        # Default traffic split
        self.traffic_split = traffic_split or {
            RoutingStrategy.CONTROL: 0.50,           # 50% control
            RoutingStrategy.COST_AGGRESSIVE: 0.20,   # 20% cost optimization
            RoutingStrategy.QUALITY_FIRST: 0.15,     # 15% quality
            RoutingStrategy.DYNAMIC_ADAPTIVE: 0.15   # 15% adaptive
        }

        # Validate traffic split
        total = sum(self.traffic_split.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Traffic split must sum to 1.0, got {total}")

        # Performance metrics per strategy
        self.metrics = {
            strategy: {
                "requests": 0,
                "total_cost": 0.0,
                "total_confidence": 0.0,
                "escalations": 0,
                "avg_latency": 0.0,
                "quality_score": 0.0
            }
            for strategy in RoutingStrategy
        }

        # Task type preferences learned over time
        self.task_type_models = defaultdict(lambda: defaultdict(int))

        logger.info(f"ABTestManager initialized (enabled={enabled})")

    def assign_strategy(self, user_id: Optional[str] = None) -> RoutingStrategy:
        """
        Assign a routing strategy to the request

        Args:
            user_id: Optional user ID for consistent assignment

        Returns:
            Assigned routing strategy
        """
        if not self.enabled:
            return RoutingStrategy.CONTROL

        # Consistent assignment for same user
        if user_id:
            import hashlib
            hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
            rand_val = (hash_val % 10000) / 10000.0
        else:
            rand_val = random.random()

        # Select strategy based on traffic split
        cumulative = 0.0
        for strategy, probability in self.traffic_split.items():
            cumulative += probability
            if rand_val < cumulative:
                return strategy

        # Fallback to control
        return RoutingStrategy.CONTROL

    def apply_strategy(
        self,
        strategy: RoutingStrategy,
        task: Dict[str, Any],
        base_complexity: str
    ) -> Dict[str, Any]:
        """
        Apply routing strategy to modify task routing behavior

        Args:
            strategy: Assigned strategy
            task: Original task dict
            base_complexity: Base complexity classification

        Returns:
            Modified task dict with routing hints
        """
        task = task.copy()

        if strategy == RoutingStrategy.COST_AGGRESSIVE:
            # Always try to use mini models first
            if base_complexity == "complex":
                task["complexity_override"] = "medium"
            elif base_complexity == "medium":
                task["complexity_override"] = "simple"

        elif strategy == RoutingStrategy.QUALITY_FIRST:
            # Always use better models
            if base_complexity == "simple":
                task["complexity_override"] = "medium"
            elif base_complexity == "medium":
                task["complexity_override"] = "complex"

        elif strategy == RoutingStrategy.DYNAMIC_ADAPTIVE:
            # Use learned preferences for task type
            task_type = task.get('type', 'general')
            if task_type in self.task_type_models:
                # Use most successful model for this task type
                best_model = max(
                    self.task_type_models[task_type].items(),
                    key=lambda x: x[1],
                    default=(None, 0)
                )[0]
                if best_model:
                    task["preferred_model"] = best_model

        elif strategy == RoutingStrategy.TASK_TYPE_OPTIMIZED:
            # Route based on task type
            task_type = task.get('type', 'general')
            type_to_model = {
                'score': 'gpt-4o-mini',
                'classify': 'gpt-4o-mini',
                'extract': 'gpt-4o-mini',
                'creative': 'gemini-2.0-flash-thinking-exp-1219',
                'reasoning': 'gemini-2.0-flash-thinking-exp-1219',
                'psychology': 'claude-3-5-sonnet-20241022',
                'analysis': 'claude-3-5-sonnet-20241022',
            }
            if task_type in type_to_model:
                task["preferred_model"] = type_to_model[task_type]

        # Add strategy metadata
        task["_ab_strategy"] = strategy.value

        return task

    def log_result(
        self,
        strategy: RoutingStrategy,
        task: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """
        Log result for strategy performance tracking

        Args:
            strategy: Strategy used
            task: Original task
            result: Routing result
        """
        metrics = self.metrics[strategy]

        metrics["requests"] += 1
        metrics["total_cost"] += result.get('cost', 0)
        metrics["total_confidence"] += result.get('confidence', 0)

        if result.get('escalated', False):
            metrics["escalations"] += 1

        # Update latency
        latency = result.get('execution_time', 0)
        n = metrics["requests"]
        metrics["avg_latency"] = (metrics["avg_latency"] * (n - 1) + latency) / n

        # Calculate quality score (confidence weighted by cost)
        confidence = result.get('confidence', 0)
        cost = result.get('cost', 0.001)
        quality = confidence / (cost * 1000)  # Normalize
        metrics["quality_score"] = (metrics["quality_score"] * (n - 1) + quality) / n

        # Learn task type preferences for adaptive strategy
        if strategy == RoutingStrategy.DYNAMIC_ADAPTIVE:
            task_type = task.get('type', 'general')
            model_used = result.get('model_used')
            if model_used and confidence > 0.75:  # Only learn from high-confidence results
                self.task_type_models[task_type][model_used] += 1

    def get_results(self) -> Dict[str, Any]:
        """
        Get A/B test results with statistical analysis

        Returns:
            Comprehensive test results with winner determination
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "A/B testing is not enabled"
            }

        results = {}
        for strategy, metrics in self.metrics.items():
            if metrics["requests"] == 0:
                results[strategy.value] = {
                    "requests": 0,
                    "status": "no_data"
                }
                continue

            n = metrics["requests"]
            avg_cost = metrics["total_cost"] / n
            avg_confidence = metrics["total_confidence"] / n
            escalation_rate = (metrics["escalations"] / n * 100)

            results[strategy.value] = {
                "requests": n,
                "avg_cost": round(avg_cost, 6),
                "avg_confidence": round(avg_confidence, 3),
                "escalation_rate": round(escalation_rate, 2),
                "avg_latency": round(metrics["avg_latency"], 3),
                "quality_score": round(metrics["quality_score"], 3),
                "total_cost": round(metrics["total_cost"], 4)
            }

        # Determine winner
        winner = self._determine_winner(results)

        return {
            "status": "active",
            "traffic_split": {k.value: v for k, v in self.traffic_split.items()},
            "results": results,
            "winner": winner,
            "recommendations": self._generate_recommendations(results, winner)
        }

    def _determine_winner(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine winning strategy based on multiple criteria

        Strategy wins if:
        - Cost < 50% of control with confidence > 80% of control, OR
        - Confidence > 110% of control with cost < 150% of control
        """
        control = results.get(RoutingStrategy.CONTROL.value)
        if not control or control["requests"] < 10:
            return {
                "strategy": "none",
                "reason": "Insufficient data for control group"
            }

        control_cost = control["avg_cost"]
        control_confidence = control["avg_confidence"]

        winners = []

        for strategy_name, metrics in results.items():
            if strategy_name == RoutingStrategy.CONTROL.value:
                continue

            if metrics["requests"] < 10:
                continue

            cost = metrics["avg_cost"]
            confidence = metrics["avg_confidence"]

            # Cost winner: < 50% cost with > 80% confidence
            if cost < control_cost * 0.5 and confidence > control_confidence * 0.8:
                winners.append({
                    "strategy": strategy_name,
                    "reason": "cost_optimization",
                    "cost_savings": round((1 - cost / control_cost) * 100, 1),
                    "confidence_ratio": round(confidence / control_confidence, 2)
                })

            # Quality winner: > 110% confidence with < 150% cost
            if confidence > control_confidence * 1.1 and cost < control_cost * 1.5:
                winners.append({
                    "strategy": strategy_name,
                    "reason": "quality_improvement",
                    "confidence_gain": round((confidence / control_confidence - 1) * 100, 1),
                    "cost_ratio": round(cost / control_cost, 2)
                })

        if not winners:
            return {
                "strategy": RoutingStrategy.CONTROL.value,
                "reason": "no_significant_improvement"
            }

        # Return best winner (highest quality score)
        best_winner = max(
            winners,
            key=lambda w: results[w["strategy"]]["quality_score"]
        )
        return best_winner

    def _generate_recommendations(
        self,
        results: Dict[str, Any],
        winner: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []

        if winner["strategy"] == "none":
            recommendations.append("Continue testing until sufficient data is collected (>10 requests per strategy)")
            return recommendations

        if winner["strategy"] != RoutingStrategy.CONTROL.value:
            recommendations.append(
                f"Consider switching to {winner['strategy']} strategy: {winner['reason']}"
            )

        # Check for low performing strategies
        for strategy_name, metrics in results.items():
            if metrics["requests"] < 5:
                continue

            if metrics["avg_confidence"] < 0.6:
                recommendations.append(
                    f"{strategy_name} has low confidence ({metrics['avg_confidence']:.2f}), consider disabling"
                )

            if metrics["escalation_rate"] > 40:
                recommendations.append(
                    f"{strategy_name} has high escalation rate ({metrics['escalation_rate']:.1f}%), review initial routing"
                )

        return recommendations

    def get_learned_preferences(self) -> Dict[str, Any]:
        """Get learned task type preferences for adaptive strategy"""
        return {
            task_type: dict(models)
            for task_type, models in self.task_type_models.items()
        }

    def reset(self):
        """Reset all A/B test data (for testing)"""
        self.metrics = {
            strategy: {
                "requests": 0,
                "total_cost": 0.0,
                "total_confidence": 0.0,
                "escalations": 0,
                "avg_latency": 0.0,
                "quality_score": 0.0
            }
            for strategy in RoutingStrategy
        }
        self.task_type_models = defaultdict(lambda: defaultdict(int))


# Global singleton instance
ab_test_manager = ABTestManager(
    enabled=os.getenv("ROUTING_AB_TEST_ENABLED", "false").lower() == "true"
)
