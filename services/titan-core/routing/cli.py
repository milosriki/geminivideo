#!/usr/bin/env python3
"""
CLI Tool for Smart Model Routing

Usage:
    python cli.py status              # Show current status
    python cli.py stats               # Show statistics
    python cli.py dashboard           # Show dashboard
    python cli.py cost                # Show cost analysis
    python cli.py ab-test             # Show A/B test results
    python cli.py export              # Export analytics
    python cli.py reset               # Reset statistics
"""

import asyncio
import sys
import json
from typing import Optional
import argparse

from .model_router import router
from .analytics import analytics
from .ab_testing import ab_test_manager
from .dashboard import router_dashboard


def print_section(title: str):
    """Print section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_metric(label: str, value: any, indent: int = 0):
    """Print a metric with formatting"""
    spaces = "  " * indent
    print(f"{spaces}{label}: {value}")


def cmd_status():
    """Show current routing status"""
    print_section("ROUTING STATUS")

    stats = router.get_stats()

    print_metric("Total Requests", stats["total_requests"])
    print_metric("Total Cost", f"${stats['total_cost']:.6f}")
    print_metric("Avg Confidence", f"{stats['avg_confidence']:.3f}")
    print_metric("Escalation Rate", f"{stats.get('escalation_rate', 0):.2f}%")
    print_metric("Cost Savings", f"{stats.get('cost_savings_pct', 0):.2f}%")

    print("\nRouter Configuration:")
    print_metric("Escalation Threshold", router.escalation_threshold, indent=1)
    print_metric("Escalation Enabled", router.enable_escalation, indent=1)
    print_metric("Cost Optimization", router.cost_optimization_mode, indent=1)

    print("\nAPI Availability:")
    print_metric("OpenAI", "✓" if router.openai_available else "✗", indent=1)
    print_metric("Claude", "✓" if router.claude_available else "✗", indent=1)
    print_metric("Gemini", "✓" if router.gemini_available else "✗", indent=1)


def cmd_stats():
    """Show detailed statistics"""
    print_section("ROUTING STATISTICS")

    stats = router.get_stats()

    if stats["total_requests"] == 0:
        print("\nNo requests processed yet.")
        return

    # Complexity distribution
    print("\nComplexity Distribution:")
    complexity_dist = stats.get("complexity_distribution", {})
    for complexity, percentage in complexity_dist.items():
        count = stats["by_complexity"].get(complexity, 0)
        print_metric(f"{complexity}", f"{count} ({percentage:.1f}%)", indent=1)

    # Model distribution
    print("\nModel Distribution:")
    model_dist = stats.get("model_distribution", {})
    for model, percentage in model_dist.items():
        count = stats["by_model"].get(model, 0)
        print_metric(f"{model}", f"{count} ({percentage:.1f}%)", indent=1)

    # Cost metrics
    print("\nCost Metrics:")
    print_metric("Total Cost", f"${stats['total_cost']:.6f}", indent=1)
    print_metric("Avg per Request", f"${stats.get('avg_cost_per_request', 0):.6f}", indent=1)
    print_metric("Cost Savings", f"{stats.get('cost_savings_pct', 0):.2f}%", indent=1)

    # Quality metrics
    print("\nQuality Metrics:")
    print_metric("Avg Confidence", f"{stats['avg_confidence']:.3f}", indent=1)
    print_metric("Escalations", f"{stats['escalations']}", indent=1)
    print_metric("Escalation Rate", f"{stats.get('escalation_rate', 0):.2f}%", indent=1)


def cmd_dashboard():
    """Show dashboard"""
    print_section("ROUTING DASHBOARD")

    dashboard = router_dashboard.get_dashboard()

    # Overview
    print("\nOverview:")
    overview = dashboard['overview']
    print_metric("Status", overview['status'].upper(), indent=1)
    print_metric("Total Requests", overview['total_requests'], indent=1)
    print_metric("Avg Cost", f"${overview['avg_cost_per_request']:.6f}", indent=1)
    print_metric("Cost Savings", f"{overview['cost_savings_percentage']:.1f}%", indent=1)
    print_metric("Avg Confidence", f"{overview['avg_confidence']:.3f}", indent=1)

    # Insights
    insights = dashboard.get('insights', [])
    if insights:
        print("\nInsights:")
        for insight in insights:
            print(f"  • {insight}")

    # Alerts
    alerts = dashboard.get('alerts', [])
    if alerts:
        print("\nAlerts:")
        for alert in alerts:
            level = alert['level'].upper()
            print(f"  [{level}] {alert['message']}")
            print(f"          Action: {alert['action']}")


def cmd_cost():
    """Show cost analysis"""
    print_section("COST ANALYSIS")

    summary = analytics.get_summary()

    if summary.get("status") == "no_data":
        print("\nNo analytics data available yet.")
        return

    cost_summary = summary['summary']

    print("\nCost Summary:")
    print_metric("Total Cost", f"${cost_summary['total_cost']:.6f}", indent=1)
    print_metric("Baseline Cost", f"${cost_summary['baseline_cost']:.6f}", indent=1)
    print_metric("Savings", f"${cost_summary['cost_savings']:.6f}", indent=1)
    print_metric("Savings %", f"{cost_summary['cost_savings_percentage']:.1f}%", indent=1)
    print_metric("Avg per Request", f"${cost_summary['avg_cost_per_request']:.6f}", indent=1)

    # By model
    print("\nCost by Model:")
    for model, stats in summary['by_model'].items():
        print_metric(model, f"${stats['avg_cost']:.6f} avg ({stats['count']} requests)", indent=1)

    # By complexity
    print("\nCost by Complexity:")
    for complexity, stats in summary['by_complexity'].items():
        print_metric(complexity, f"${stats['avg_cost']:.6f} avg ({stats['count']} requests)", indent=1)


def cmd_ab_test():
    """Show A/B test results"""
    print_section("A/B TESTING")

    results = ab_test_manager.get_results()

    if results.get("status") == "disabled":
        print("\nA/B testing is not enabled.")
        print("Set ROUTING_AB_TEST_ENABLED=true to enable.")
        return

    print(f"\nStatus: {results['status']}")

    # Traffic split
    print("\nTraffic Split:")
    for strategy, percentage in results['traffic_split'].items():
        print_metric(strategy, f"{percentage * 100:.1f}%", indent=1)

    # Results by strategy
    print("\nResults by Strategy:")
    for strategy, metrics in results['results'].items():
        if metrics.get('requests', 0) == 0:
            continue

        print(f"\n  {strategy}:")
        print_metric("Requests", metrics['requests'], indent=2)
        print_metric("Avg Cost", f"${metrics['avg_cost']:.6f}", indent=2)
        print_metric("Avg Confidence", f"{metrics['avg_confidence']:.3f}", indent=2)
        print_metric("Escalation Rate", f"{metrics['escalation_rate']:.1f}%", indent=2)

    # Winner
    winner = results.get('winner', {})
    if winner.get('strategy') != 'none':
        print(f"\nWinner: {winner['strategy']}")
        print_metric("Reason", winner['reason'], indent=1)

    # Recommendations
    recommendations = results.get('recommendations', [])
    if recommendations:
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"  • {rec}")


def cmd_export(output_path: Optional[str] = None):
    """Export analytics to JSON"""
    output_path = output_path or "/tmp/routing_export.json"

    print_section("EXPORT ANALYTICS")

    try:
        analytics.export_report(output_path)
        print(f"\n✓ Analytics exported to: {output_path}")

        # Also export dashboard
        dashboard_path = output_path.replace('.json', '_dashboard.json')
        router_dashboard.export_dashboard(dashboard_path)
        print(f"✓ Dashboard exported to: {dashboard_path}")

    except Exception as e:
        print(f"\n✗ Export failed: {e}")


def cmd_reset():
    """Reset all statistics"""
    print_section("RESET STATISTICS")

    confirm = input("\n⚠️  This will clear all routing statistics. Continue? (yes/no): ")

    if confirm.lower() != 'yes':
        print("\nCancelled.")
        return

    try:
        router.reset_stats()
        analytics.reset()
        ab_test_manager.reset()

        print("\n✓ All statistics reset successfully.")

    except Exception as e:
        print(f"\n✗ Reset failed: {e}")


def cmd_help():
    """Show help"""
    print_section("SMART MODEL ROUTING CLI")

    print("""
Commands:
    status      Show current routing status
    stats       Show detailed statistics
    dashboard   Show dashboard with insights
    cost        Show cost analysis
    ab-test     Show A/B test results
    export      Export analytics to JSON
    reset       Reset all statistics
    help        Show this help message

Examples:
    python cli.py status
    python cli.py stats
    python cli.py export /tmp/report.json
    python cli.py reset

Environment Variables:
    ROUTER_ESCALATION_THRESHOLD    Confidence threshold (default: 0.7)
    ROUTER_ENABLE_ESCALATION       Enable escalation (default: true)
    ROUTER_COST_OPTIMIZATION       Cost optimization mode (default: true)
    ROUTING_AB_TEST_ENABLED        Enable A/B testing (default: false)
""")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Smart Model Routing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'command',
        choices=['status', 'stats', 'dashboard', 'cost', 'ab-test', 'export', 'reset', 'help'],
        help='Command to execute'
    )
    parser.add_argument(
        '--output',
        '-o',
        help='Output path for export command',
        default=None
    )

    args = parser.parse_args()

    try:
        if args.command == 'status':
            cmd_status()
        elif args.command == 'stats':
            cmd_stats()
        elif args.command == 'dashboard':
            cmd_dashboard()
        elif args.command == 'cost':
            cmd_cost()
        elif args.command == 'ab-test':
            cmd_ab_test()
        elif args.command == 'export':
            cmd_export(args.output)
        elif args.command == 'reset':
            cmd_reset()
        elif args.command == 'help':
            cmd_help()

    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
