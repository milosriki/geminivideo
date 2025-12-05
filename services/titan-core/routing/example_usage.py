"""
Example Usage of Smart Model Routing

Demonstrates:
1. Basic routing
2. Integration with existing ensemble
3. Analytics and monitoring
4. A/B testing
5. Dashboard usage
"""

import asyncio
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_routing():
    """Example 1: Basic smart routing"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Smart Routing")
    print("="*60)

    from titan_core.routing import ModelRouter, TaskComplexity

    router = ModelRouter(
        escalation_threshold=0.7,
        enable_escalation=True,
        cost_optimization_mode=True
    )

    # Simple task - should use mini model
    simple_task = {
        "text": "Rate this hook: 'Lose weight fast!'",
        "type": "score"
    }

    result = await router.route_and_execute(
        task=simple_task,
        prompt="Rate this ad hook on a scale of 0-100. Respond with JSON: {\"score\": 75, \"confidence\": 0.9}"
    )

    print(f"\nSimple Task:")
    print(f"  Model used: {result['model_used']}")
    print(f"  Complexity: {result['complexity']}")
    print(f"  Cost: ${result['cost']:.6f}")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Escalated: {result['escalated']}")

    # Complex task - should use premium model
    complex_task = {
        "text": "A 2000-word ad script about fitness transformation...",
        "type": "psychology",
        "requirements": {
            "creative_reasoning": True,
            "deep_analysis": True
        }
    }

    result = await router.route_and_execute(
        task=complex_task,
        prompt="Analyze the psychological triggers in this script in detail..."
    )

    print(f"\nComplex Task:")
    print(f"  Model used: {result['model_used']}")
    print(f"  Complexity: {result['complexity']}")
    print(f"  Cost: ${result['cost']:.6f}")
    print(f"  Confidence: {result['confidence']:.2f}")

    # Show router stats
    stats = router.get_stats()
    print(f"\nRouter Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Total cost: ${stats['total_cost']:.6f}")
    print(f"  Cost savings: {stats['cost_savings_pct']:.1f}%")
    print(f"  Avg confidence: {stats['avg_confidence']:.2f}")


async def example_ensemble_integration():
    """Example 2: Integration with existing ensemble"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Ensemble Integration")
    print("="*60)

    from titan_core.routing.integration import smart_council

    script = """
    HOOK: Are you tired of yo-yo dieting?
    BODY: Discover the science-backed method that helped 10,000+ people lose weight and keep it off.
    CTA: Download our free guide now!
    """

    result = await smart_council.evaluate_script(
        script_content=script,
        niche="fitness"
    )

    print(f"\nScript Evaluation:")
    print(f"  Verdict: {result['verdict']}")
    print(f"  Score: {result['final_score']}/100")
    print(f"  Confidence: {result['confidence']:.2f}")
    print(f"  Feedback: {result['feedback']}")

    # Show routing metadata
    metadata = result.get("_routing_metadata", {})
    print(f"\nRouting Metadata:")
    print(f"  Model: {metadata.get('model_used')}")
    print(f"  Cost: ${metadata.get('cost', 0):.6f}")
    print(f"  Escalated: {metadata.get('escalated')}")


async def example_analytics():
    """Example 3: Analytics and monitoring"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Analytics & Monitoring")
    print("="*60)

    from titan_core.routing import ModelRouter
    from titan_core.routing.analytics import analytics

    router = ModelRouter()

    # Simulate multiple requests
    tasks = [
        {"text": "Short text", "type": "score"},
        {"text": "Medium length analysis text", "type": "analysis"},
        {"text": "Long creative reasoning task" * 100, "type": "creative"},
    ]

    for task in tasks:
        result = await router.route_and_execute(
            task=task,
            prompt=f"Process this: {task['text'][:50]}..."
        )
        analytics.log_request(task, result)

    # Get analytics summary
    summary = analytics.get_summary()
    print(f"\nAnalytics Summary:")
    print(f"  Total requests: {summary['summary']['total_requests']}")
    print(f"  Total cost: ${summary['summary']['total_cost']:.6f}")
    print(f"  Baseline cost: ${summary['summary']['baseline_cost']:.6f}")
    print(f"  Cost savings: ${summary['summary']['cost_savings']:.6f} ({summary['summary']['cost_savings_percentage']:.1f}%)")

    print(f"\nModel Distribution:")
    for model, stats in summary['by_model'].items():
        print(f"  {model}:")
        print(f"    Requests: {stats['count']} ({stats['percentage']:.1f}%)")
        print(f"    Avg cost: ${stats['avg_cost']:.6f}")
        print(f"    Avg confidence: {stats['avg_confidence']:.2f}")

    print(f"\nInsights:")
    for insight in summary['insights']:
        print(f"  • {insight}")


async def example_ab_testing():
    """Example 4: A/B testing different routing strategies"""
    print("\n" + "="*60)
    print("EXAMPLE 4: A/B Testing")
    print("="*60)

    from titan_core.routing.ab_testing import ABTestManager, RoutingStrategy

    # Enable A/B testing
    ab_test = ABTestManager(enabled=True)

    # Simulate requests from different users
    users = ["user1", "user2", "user3", "user4", "user5"]
    task = {
        "text": "Analyze this ad script",
        "type": "analysis"
    }

    print("\nRunning A/B test with different users...")
    for user in users:
        strategy = ab_test.assign_strategy(user)
        modified_task = ab_test.apply_strategy(strategy, task, "medium")

        print(f"  {user}: {strategy.value}")

        # Simulate result
        mock_result = {
            "cost": 0.001 if strategy == RoutingStrategy.COST_AGGRESSIVE else 0.003,
            "confidence": 0.75 if strategy == RoutingStrategy.QUALITY_FIRST else 0.70,
            "escalated": False,
            "execution_time": 1.2,
            "model_used": "gpt-4o-mini" if strategy == RoutingStrategy.COST_AGGRESSIVE else "gpt-4o"
        }

        ab_test.log_result(strategy, modified_task, mock_result)

    # Get test results
    results = ab_test.get_results()
    print(f"\nA/B Test Results:")
    print(f"  Status: {results['status']}")

    for strategy, metrics in results['results'].items():
        if metrics.get('requests', 0) > 0:
            print(f"\n  {strategy}:")
            print(f"    Requests: {metrics['requests']}")
            print(f"    Avg cost: ${metrics['avg_cost']:.6f}")
            print(f"    Avg confidence: {metrics['avg_confidence']:.2f}")
            print(f"    Escalation rate: {metrics['escalation_rate']:.1f}%")

    print(f"\nWinner: {results['winner']['strategy']}")
    print(f"Reason: {results['winner']['reason']}")

    print(f"\nRecommendations:")
    for rec in results['recommendations']:
        print(f"  • {rec}")


async def example_dashboard():
    """Example 5: Dashboard usage"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Dashboard")
    print("="*60)

    from titan_core.routing.dashboard import router_dashboard

    # Get complete dashboard
    dashboard = router_dashboard.get_dashboard()

    print("\nDashboard Overview:")
    overview = dashboard['overview']
    print(f"  Total requests: {overview['total_requests']}")
    print(f"  Avg cost per request: ${overview['avg_cost_per_request']:.6f}")
    print(f"  Cost savings: {overview['cost_savings_percentage']:.1f}%")
    print(f"  Avg confidence: {overview['avg_confidence']:.2f}")
    print(f"  Status: {overview['status']}")

    print("\nCost Analysis:")
    cost = dashboard['cost_analysis']
    print(f"  Total cost: ${cost['total_cost']:.6f}")
    print(f"  Baseline cost: ${cost.get('baseline_cost', 0):.6f}")
    print(f"  Savings: ${cost.get('savings', 0):.6f}")

    print("\nInsights:")
    for insight in dashboard['insights']:
        print(f"  • {insight}")

    if dashboard['alerts']:
        print("\nAlerts:")
        for alert in dashboard['alerts']:
            print(f"  [{alert['level'].upper()}] {alert['message']}")
            print(f"    Action: {alert['action']}")


async def example_cost_comparison():
    """Example 6: Cost comparison - routing vs. always premium"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Cost Comparison")
    print("="*60)

    from titan_core.routing import ModelRouter

    # Scenario: 100 requests with typical distribution
    # 60% simple, 30% medium, 10% complex

    print("\nScenario: 100 requests")
    print("  60% simple tasks (e.g., scoring, classification)")
    print("  30% medium tasks (e.g., standard analysis)")
    print("  10% complex tasks (e.g., creative reasoning)")

    # With smart routing
    routing_cost = (
        60 * 0.000015 +  # Simple tasks with mini model
        30 * 0.00003 +   # Medium tasks with standard model
        10 * 0.00015     # Complex tasks with premium model
    )

    # Without routing (always premium)
    no_routing_cost = 100 * 0.00015  # All tasks with premium model

    savings = no_routing_cost - routing_cost
    savings_pct = (savings / no_routing_cost) * 100

    print(f"\nCost Analysis:")
    print(f"  With smart routing: ${routing_cost:.6f}")
    print(f"  Without routing (always premium): ${no_routing_cost:.6f}")
    print(f"  Savings: ${savings:.6f} ({savings_pct:.1f}%)")

    print(f"\nProjected Annual Savings (1M requests):")
    annual_savings = savings * 10_000
    print(f"  ${annual_savings:,.2f}")


async def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("SMART MODEL ROUTING - EXAMPLE USAGE")
    print("="*60)

    try:
        await example_basic_routing()
        await example_ensemble_integration()
        await example_analytics()
        await example_ab_testing()
        await example_dashboard()
        await example_cost_comparison()

        print("\n" + "="*60)
        print("All examples completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        logger.error(f"Example failed: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
