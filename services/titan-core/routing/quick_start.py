#!/usr/bin/env python3
"""
Quick Start - Smart Model Routing Demo

Run this to see smart routing in action:
    python quick_start.py

This demo shows:
1. Task complexity detection
2. Model selection
3. Cost optimization
4. Analytics tracking
"""

import asyncio
import os
from typing import Dict, Any


def print_header(title: str):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_result(label: str, value: Any, indent: int = 0):
    """Print result with formatting"""
    spaces = "  " * indent
    print(f"{spaces}{label}: {value}")


async def demo_complexity_detection():
    """Demo 1: Task complexity detection"""
    print_header("DEMO 1: Task Complexity Detection")

    from titan_core.routing import ModelRouter

    router = ModelRouter()

    tasks = [
        {
            "text": "Rate this hook",
            "type": "score",
            "description": "Simple task (short text, simple type)"
        },
        {
            "text": "Analyze this marketing strategy" * 30,
            "type": "analysis",
            "description": "Medium task (moderate length)"
        },
        {
            "text": "Long creative content..." * 100,
            "type": "psychology",
            "description": "Complex task (long text, complex type)"
        }
    ]

    for i, task in enumerate(tasks, 1):
        complexity = router.classify_task_complexity(task)
        model = router.get_model_for_complexity(complexity)

        print(f"\nTask {i}: {task['description']}")
        print_result("Complexity", complexity.value, indent=1)
        print_result("Selected Model", model, indent=1)


async def demo_cost_savings():
    """Demo 2: Cost savings simulation"""
    print_header("DEMO 2: Cost Savings Simulation")

    print("\nScenario: 100 requests")
    print("  60% simple tasks")
    print("  30% medium tasks")
    print("  10% complex tasks")

    # Cost calculation
    simple_cost = 60 * 0.000015   # GPT-4o-mini
    medium_cost = 30 * 0.00003    # Claude Sonnet
    complex_cost = 10 * 0.00015   # Gemini Thinking

    routing_cost = simple_cost + medium_cost + complex_cost
    no_routing_cost = 100 * 0.00015  # Always premium

    savings = no_routing_cost - routing_cost
    savings_pct = (savings / no_routing_cost) * 100

    print("\nWith Smart Routing:")
    print_result("Simple tasks", f"${simple_cost:.6f}", indent=1)
    print_result("Medium tasks", f"${medium_cost:.6f}", indent=1)
    print_result("Complex tasks", f"${complex_cost:.6f}", indent=1)
    print_result("Total", f"${routing_cost:.6f}", indent=1)

    print("\nWithout Routing (always premium):")
    print_result("Total", f"${no_routing_cost:.6f}", indent=1)

    print("\nSavings:")
    print_result("Amount", f"${savings:.6f}", indent=1)
    print_result("Percentage", f"{savings_pct:.1f}%", indent=1)

    print("\nAnnual Projection (1M requests):")
    annual_with = routing_cost * 10_000
    annual_without = no_routing_cost * 10_000
    annual_savings = annual_without - annual_with
    print_result("With routing", f"${annual_with:,.2f}", indent=1)
    print_result("Without routing", f"${annual_without:,.2f}", indent=1)
    print_result("Annual savings", f"${annual_savings:,.2f}", indent=1)


async def demo_model_selection():
    """Demo 3: Model selection for different task types"""
    print_header("DEMO 3: Task-Type Specific Routing")

    from titan_core.routing import ModelRouter, TaskComplexity

    router = ModelRouter(cost_optimization_mode=True)

    task_types = [
        ("score", TaskComplexity.SIMPLE, "Scoring/rating tasks"),
        ("classify", TaskComplexity.SIMPLE, "Classification tasks"),
        ("creative", TaskComplexity.COMPLEX, "Creative generation"),
        ("psychology", TaskComplexity.COMPLEX, "Psychological analysis"),
        ("analysis", TaskComplexity.MEDIUM, "Standard analysis"),
    ]

    print("\nOptimal Models by Task Type:")
    for task_type, complexity, description in task_types:
        model = router.get_model_for_complexity(complexity, task_type)
        cost = router._calculate_cost(model, 1_000_000, 1_000_000)

        print(f"\n{description}:")
        print_result("Task Type", task_type, indent=1)
        print_result("Complexity", complexity.value, indent=1)
        print_result("Model", model, indent=1)
        print_result("Cost", f"${cost:.2f} per 1M tokens", indent=1)


async def demo_analytics():
    """Demo 4: Analytics tracking"""
    print_header("DEMO 4: Analytics & Monitoring")

    from titan_core.routing import ModelRouter
    from titan_core.routing.analytics import analytics

    router = ModelRouter()
    analytics.reset()

    print("\nSimulating 10 requests...")

    # Simulate various requests
    tasks = [
        {"text": "x" * 100, "type": "score"},
        {"text": "x" * 100, "type": "classify"},
        {"text": "x" * 1000, "type": "analysis"},
        {"text": "x" * 1000, "type": "analysis"},
        {"text": "x" * 1000, "type": "analysis"},
        {"text": "x" * 2500, "type": "creative"},
        {"text": "x" * 2500, "type": "creative"},
        {"text": "x" * 2500, "type": "psychology"},
        {"text": "x" * 100, "type": "score"},
        {"text": "x" * 100, "type": "score"},
    ]

    for i, task in enumerate(tasks, 1):
        complexity = router.classify_task_complexity(task)
        model = router.get_model_for_complexity(complexity, task["type"])
        cost = router._calculate_cost(model, len(task["text"]) / 4, 250)

        # Simulate result
        result = {
            "complexity": complexity.value,
            "model_used": model,
            "cost": cost,
            "confidence": 0.85,
            "escalated": False,
            "execution_time": 0.5
        }

        analytics.log_request(task, result)
        router._update_stats(complexity, model, cost, 0.85)

    # Show summary
    summary = analytics.get_summary()

    print("\nAnalytics Summary:")
    print_result("Total Requests", summary['summary']['total_requests'], indent=1)
    print_result("Total Cost", f"${summary['summary']['total_cost']:.6f}", indent=1)
    print_result("Baseline Cost", f"${summary['summary']['baseline_cost']:.6f}", indent=1)
    print_result("Savings", f"${summary['summary']['cost_savings']:.6f}", indent=1)
    print_result("Savings %", f"{summary['summary']['cost_savings_percentage']:.1f}%", indent=1)

    print("\nModel Distribution:")
    for model, stats in summary['by_model'].items():
        print(f"  {model}:")
        print_result("Count", f"{stats['count']} ({stats['percentage']:.1f}%)", indent=2)
        print_result("Avg Cost", f"${stats['avg_cost']:.6f}", indent=2)

    print("\nInsights:")
    for insight in summary['insights']:
        print(f"  • {insight}")


async def demo_integration():
    """Demo 5: Integration example"""
    print_header("DEMO 5: Integration Example")

    print("\nEasy Integration:")

    print("\n1. Drop-in Replacement for Ensemble:")
    print("   # Before:")
    print("   from backend_core.engines.ensemble import council")
    print("")
    print("   # After:")
    print("   from backend_core.routing.integration import smart_council as council")
    print("   # Same API, automatic routing!")

    print("\n2. Standalone Executor:")
    print("   from backend_core.routing.integration import smart_executor")
    print("   result = await smart_executor.execute(")
    print("       text='Analyze this ad',")
    print("       task_type='analysis'")
    print("   )")

    print("\n3. REST API:")
    print("   POST /api/v1/routing/execute")
    print("   GET  /api/v1/routing/dashboard")
    print("   GET  /api/v1/routing/stats")

    print("\n4. CLI Tool:")
    print("   python cli.py status")
    print("   python cli.py cost")
    print("   python cli.py dashboard")


async def demo_configuration():
    """Demo 6: Configuration options"""
    print_header("DEMO 6: Configuration Options")

    print("\nEnvironment Variables:")
    print("  ROUTER_ESCALATION_THRESHOLD=0.7    # Confidence threshold")
    print("  ROUTER_ENABLE_ESCALATION=true      # Enable escalation")
    print("  ROUTER_COST_OPTIMIZATION=true      # Cost optimization mode")

    print("\nCode Configuration:")
    print("  router = ModelRouter(")
    print("      escalation_threshold=0.7,      # Lower = more cost savings")
    print("      enable_escalation=True,         # Disable for fixed routing")
    print("      cost_optimization_mode=True     # False = quality first")
    print("  )")

    print("\nConfiguration Profiles:")

    profiles = [
        {
            "name": "Cost Optimized",
            "threshold": 0.6,
            "cost_mode": True,
            "description": "Maximum cost savings"
        },
        {
            "name": "Balanced (Default)",
            "threshold": 0.7,
            "cost_mode": True,
            "description": "Balance cost and quality"
        },
        {
            "name": "Quality First",
            "threshold": 0.8,
            "cost_mode": False,
            "description": "Prioritize quality over cost"
        }
    ]

    for profile in profiles:
        print(f"\n{profile['name']}:")
        print_result("Threshold", profile['threshold'], indent=1)
        print_result("Cost Mode", profile['cost_mode'], indent=1)
        print_result("Best For", profile['description'], indent=1)


async def demo_monitoring():
    """Demo 7: Monitoring and alerts"""
    print_header("DEMO 7: Monitoring & Alerts")

    print("\nReal-time Monitoring:")

    print("\n1. Dashboard:")
    print("   from titan_core.routing.dashboard import router_dashboard")
    print("   dashboard = router_dashboard.get_dashboard()")

    print("\n2. Cost Summary:")
    print("   cost = router_dashboard.get_cost_summary()")
    print("   print(f\"Savings: {cost['savings_percentage']:.1f}%\")")

    print("\n3. Performance Summary:")
    print("   perf = router_dashboard.get_performance_summary()")
    print("   print(f\"Confidence: {perf['avg_confidence']:.3f}\")")

    print("\nAlerts:")
    alerts = [
        {"level": "WARNING", "message": "Low confidence (0.58)", "action": "Consider using better models"},
        {"level": "WARNING", "message": "High escalation rate (35%)", "action": "Review routing strategy"},
        {"level": "INFO", "message": "Cost savings at 82%", "action": "Continue monitoring"}
    ]

    for alert in alerts:
        print(f"  [{alert['level']}] {alert['message']}")
        print(f"           Action: {alert['action']}")


async def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("  SMART MODEL ROUTING - QUICK START DEMO")
    print("="*60)
    print("\nThis demo shows the power of intelligent model routing:")
    print("  ✓ 80% cost reduction")
    print("  ✓ Quality maintenance")
    print("  ✓ Comprehensive analytics")
    print("  ✓ Easy integration")

    try:
        await demo_complexity_detection()
        await demo_cost_savings()
        await demo_model_selection()
        await demo_analytics()
        await demo_integration()
        await demo_configuration()
        await demo_monitoring()

        print("\n" + "="*60)
        print("  DEMO COMPLETE!")
        print("="*60)

        print("\nNext Steps:")
        print("  1. Set API keys:")
        print("     export OPENAI_API_KEY='sk-...'")
        print("     export ANTHROPIC_API_KEY='sk-ant-...'")
        print("     export GEMINI_API_KEY='...'")
        print("")
        print("  2. Run examples:")
        print("     python example_usage.py")
        print("")
        print("  3. Try CLI tool:")
        print("     python cli.py status")
        print("")
        print("  4. Read documentation:")
        print("     cat README.md")
        print("")
        print("  5. Start integration:")
        print("     cat MIGRATION_GUIDE.md")

        print("\n" + "="*60)
        print("  Ready to save 80% on AI costs!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: This demo uses simulated data.")
        print("For real API calls, ensure API keys are set.")


if __name__ == "__main__":
    asyncio.run(main())
