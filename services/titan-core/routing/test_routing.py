"""
Tests for Smart Model Routing

Run with: pytest test_routing.py -v
"""

import pytest
import asyncio
from typing import Dict, Any

from .model_router import ModelRouter, TaskComplexity
from .analytics import RoutingAnalytics
from .ab_testing import ABTestManager, RoutingStrategy


class TestTaskComplexityClassification:
    """Test task complexity detection"""

    def test_simple_tasks(self):
        """Simple tasks should be classified correctly"""
        router = ModelRouter()

        # Short text + simple task type
        task = {"text": "Rate this hook", "type": "score"}
        assert router.classify_task_complexity(task) == TaskComplexity.SIMPLE

        task = {"text": "Classify this", "type": "classify"}
        assert router.classify_task_complexity(task) == TaskComplexity.SIMPLE

    def test_complex_tasks(self):
        """Complex tasks should be classified correctly"""
        router = ModelRouter()

        # Long text
        task = {"text": "x" * 2500, "type": "general"}
        assert router.classify_task_complexity(task) == TaskComplexity.COMPLEX

        # Complex task type
        task = {"text": "Analyze psychology", "type": "psychology"}
        assert router.classify_task_complexity(task) == TaskComplexity.COMPLEX

        # Creative reasoning required
        task = {
            "text": "Medium text",
            "type": "general",
            "requirements": {"creative_reasoning": True}
        }
        assert router.classify_task_complexity(task) == TaskComplexity.COMPLEX

    def test_medium_tasks(self):
        """Medium tasks should be classified correctly"""
        router = ModelRouter()

        # Medium length, standard type
        task = {"text": "x" * 1000, "type": "general"}
        assert router.classify_task_complexity(task) == TaskComplexity.MEDIUM

    def test_complexity_override(self):
        """Complexity override should work"""
        router = ModelRouter()

        task = {
            "text": "Short",
            "type": "score",
            "complexity_override": "complex"
        }
        assert router.classify_task_complexity(task) == TaskComplexity.COMPLEX


class TestModelSelection:
    """Test model selection for different complexities"""

    def test_cost_optimization_mode(self):
        """Cost optimization should prefer cheaper models"""
        router = ModelRouter(cost_optimization_mode=True)

        # Simple should use mini
        model = router.get_model_for_complexity(TaskComplexity.SIMPLE)
        assert "mini" in model.lower() or "flash" in model.lower()

        # Complex should still use good model but optimize
        model = router.get_model_for_complexity(TaskComplexity.COMPLEX)
        assert model in [
            "gemini-2.0-flash-thinking-exp-1219",
            "claude-3-5-sonnet-20241022",
            "gpt-4o"
        ]

    def test_quality_mode(self):
        """Quality mode should prefer better models"""
        router = ModelRouter(cost_optimization_mode=False)

        # Even simple tasks should use decent models
        model = router.get_model_for_complexity(TaskComplexity.SIMPLE)
        # Should still use mini for simple tasks

        # Complex should use best
        model = router.get_model_for_complexity(TaskComplexity.COMPLEX)
        assert model in [
            "gemini-2.0-flash-thinking-exp-1219",
            "claude-3-5-sonnet-20241022"
        ]


class TestCostCalculation:
    """Test cost calculation"""

    def test_cost_calculation(self):
        """Cost should be calculated correctly"""
        router = ModelRouter()

        # GPT-4o-mini
        cost = router._calculate_cost("gpt-4o-mini", 1_000_000, 1_000_000)
        # Input: $0.15, Output: $0.45, Total: $0.60
        assert 0.5 < cost < 0.7

        # GPT-4o (more expensive)
        cost = router._calculate_cost("gpt-4o", 1_000_000, 1_000_000)
        # Should be significantly more
        assert cost > 10


class TestStatistics:
    """Test statistics tracking"""

    def test_stats_initialization(self):
        """Stats should initialize correctly"""
        router = ModelRouter()
        stats = router.get_stats()

        assert stats["total_requests"] == 0
        assert stats["total_cost"] == 0.0
        assert stats["avg_confidence"] == 0.0

    def test_stats_update(self):
        """Stats should update correctly"""
        router = ModelRouter()
        router.reset_stats()

        # Simulate stats update
        router._update_stats(
            complexity=TaskComplexity.SIMPLE,
            model="gpt-4o-mini",
            cost=0.0001,
            confidence=0.85
        )

        stats = router.get_stats()
        assert stats["total_requests"] == 1
        assert stats["total_cost"] == 0.0001
        assert stats["avg_confidence"] == 0.85


class TestAnalytics:
    """Test analytics tracking"""

    def test_analytics_initialization(self):
        """Analytics should initialize correctly"""
        analytics = RoutingAnalytics()
        summary = analytics.get_summary()

        assert summary["status"] == "no_data"

    def test_log_request(self):
        """Analytics should log requests correctly"""
        analytics = RoutingAnalytics()
        analytics.reset()

        task = {"text": "Test", "type": "score"}
        result = {
            "complexity": "simple",
            "model_used": "gpt-4o-mini",
            "cost": 0.0001,
            "confidence": 0.85,
            "escalated": False,
            "execution_time": 0.5
        }

        analytics.log_request(task, result)

        summary = analytics.get_summary()
        assert summary["summary"]["total_requests"] == 1
        assert summary["summary"]["total_cost"] == 0.0001

    def test_cost_savings_calculation(self):
        """Analytics should calculate cost savings correctly"""
        analytics = RoutingAnalytics()
        analytics.reset()

        # Log a cheap request
        task = {"text": "x" * 100, "type": "score"}
        result = {
            "complexity": "simple",
            "model_used": "gpt-4o-mini",
            "cost": 0.0001,  # Cheap
            "confidence": 0.85,
            "escalated": False,
            "execution_time": 0.5
        }

        analytics.log_request(task, result)
        summary = analytics.get_summary()

        # Should show savings vs. baseline
        assert summary["summary"]["cost_savings"] > 0
        assert summary["summary"]["cost_savings_percentage"] > 50


class TestABTesting:
    """Test A/B testing functionality"""

    def test_strategy_assignment(self):
        """Strategies should be assigned consistently"""
        ab_test = ABTestManager(enabled=True)

        # Same user should get same strategy
        user1_strategy1 = ab_test.assign_strategy("user1")
        user1_strategy2 = ab_test.assign_strategy("user1")
        assert user1_strategy1 == user1_strategy2

        # Different users may get different strategies
        user2_strategy = ab_test.assign_strategy("user2")
        # Not necessarily different, but assignment should work

    def test_strategy_application(self):
        """Strategies should modify tasks correctly"""
        ab_test = ABTestManager(enabled=True)

        task = {"text": "Test", "type": "general"}

        # Cost aggressive should downgrade complexity
        modified = ab_test.apply_strategy(
            RoutingStrategy.COST_AGGRESSIVE,
            task,
            "complex"
        )
        assert modified.get("complexity_override") == "medium"

        # Quality first should upgrade complexity
        modified = ab_test.apply_strategy(
            RoutingStrategy.QUALITY_FIRST,
            task,
            "simple"
        )
        assert modified.get("complexity_override") == "medium"

    def test_results_tracking(self):
        """A/B test results should be tracked correctly"""
        ab_test = ABTestManager(enabled=True)
        ab_test.reset()

        task = {"text": "Test", "type": "general"}
        result = {
            "cost": 0.001,
            "confidence": 0.8,
            "escalated": False,
            "execution_time": 1.0,
            "model_used": "gpt-4o-mini"
        }

        # Log result
        ab_test.log_result(RoutingStrategy.COST_AGGRESSIVE, task, result)

        results = ab_test.get_results()
        assert results["status"] == "active"
        assert "cost_aggressive" in results["results"]


class TestIntegration:
    """Integration tests"""

    @pytest.mark.asyncio
    async def test_end_to_end_routing(self):
        """Test complete routing flow"""
        router = ModelRouter()
        router.reset_stats()

        task = {"text": "Test hook", "type": "score"}
        prompt = "Rate this: Test hook"

        # This would make actual API call in real scenario
        # For testing, we'd mock the API calls
        # result = await router.route_and_execute(task, prompt)
        # assert "result" in result
        # assert "confidence" in result
        # assert "cost" in result

    @pytest.mark.asyncio
    async def test_escalation_flow(self):
        """Test escalation on low confidence"""
        router = ModelRouter(
            escalation_threshold=0.9,  # High threshold to trigger escalation
            enable_escalation=True
        )
        router.reset_stats()

        # Would need to mock low confidence response
        # to test escalation logic


def test_imports():
    """Test that all imports work"""
    from titan_core.routing import ModelRouter, TaskComplexity, RoutingAnalytics, ABTestManager
    from titan_core.routing.dashboard import router_dashboard
    from titan_core.routing.integration import smart_council, smart_executor

    assert ModelRouter is not None
    assert TaskComplexity is not None
    assert RoutingAnalytics is not None
    assert ABTestManager is not None
    assert router_dashboard is not None
    assert smart_council is not None
    assert smart_executor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
