"""
Demo: Cross-Account Learning System
Agent 49 - 10x Leverage Through Network Effects

This demo shows how cross-account learning creates compound value:
1. Each account learns independently
2. Patterns are extracted anonymously
3. Insights are shared across similar accounts
4. New accounts benefit from all previous learning

Network Effect: More accounts = Better insights for everyone
"""

import asyncio
import json
from datetime import datetime, timedelta
import requests


# ML Service base URL
ML_SERVICE_URL = "http://localhost:8003"


def print_header(title: str):
    """Print a nice header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(label: str, data: dict):
    """Print a formatted result."""
    print(f"\n{label}:")
    print(json.dumps(data, indent=2))
    print()


async def demo_cross_learning():
    """
    Demonstrate the power of cross-account learning.
    """
    print_header("CROSS-ACCOUNT LEARNING DEMO - Agent 49")

    print("This demo shows how network effects create 10x leverage:")
    print("- Account A learns from their own data")
    print("- Account B learns from their own data")
    print("- Both accounts benefit from shared patterns")
    print("- New Account C starts with wisdom from A + B")
    print()

    # ========================================================================
    # Step 1: Extract insights from Account A (Fitness niche)
    # ========================================================================
    print_header("STEP 1: Extract Insights from Account A (Fitness)")

    account_a_id = "fitness_account_123"

    print(f"Extracting anonymized insights from Account A ({account_a_id})...")
    print("This account has been running fitness ad campaigns...")
    print()

    response = requests.post(
        f"{ML_SERVICE_URL}/api/cross-learning/extract-insights",
        json={"account_id": account_a_id}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print_result("Account A Insights", result.get("insights", {}))
            print("✓ Insights extracted successfully!")
            print(f"  - Niche: {result['insights'].get('niche', 'N/A')}")
            print(f"  - Avg CTR: {result['insights'].get('avg_ctr', 0):.2%}")
            print(f"  - Top Hook Types: {len(result['insights'].get('top_hook_types', []))} types identified")
        else:
            print(f"⚠ {result.get('message', 'Insufficient data')}")
    else:
        print(f"✗ Error: {response.status_code}")

    # ========================================================================
    # Step 2: Extract insights from Account B (Fitness niche)
    # ========================================================================
    print_header("STEP 2: Extract Insights from Account B (Also Fitness)")

    account_b_id = "fitness_account_456"

    print(f"Extracting anonymized insights from Account B ({account_b_id})...")
    print("This is another fitness account with different campaigns...")
    print()

    response = requests.post(
        f"{ML_SERVICE_URL}/api/cross-learning/extract-insights",
        json={"account_id": account_b_id}
    )

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            print_result("Account B Insights", result.get("insights", {}))
            print("✓ Insights extracted successfully!")
            print(f"  - Niche: {result['insights'].get('niche', 'N/A')}")
            print(f"  - Avg CTR: {result['insights'].get('avg_ctr', 0):.2%}")
        else:
            print(f"⚠ {result.get('message', 'Insufficient data')}")
    else:
        print(f"✗ Error: {response.status_code}")

    # ========================================================================
    # Step 3: Get Niche Wisdom (Aggregated from A + B)
    # ========================================================================
    print_header("STEP 3: Get Fitness Niche Wisdom (Aggregated)")

    print("Aggregating insights from all fitness accounts...")
    print("This creates niche-specific best practices!")
    print()

    response = requests.get(
        f"{ML_SERVICE_URL}/api/cross-learning/niche-wisdom/fitness"
    )

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            wisdom = result.get("wisdom", {})
            print_result("Fitness Niche Wisdom", wisdom)
            print("✓ Niche wisdom generated!")
            print(f"  - Sample size: {wisdom.get('sample_size', 0)} accounts")
            print(f"  - Niche avg CTR: {wisdom.get('niche_avg_ctr', 0):.2%}")
            print(f"  - Confidence: {wisdom.get('confidence_score', 0):.2f}")
            print()
            print("Top Winning Patterns:")
            for i, pattern in enumerate(wisdom.get('top_hook_types', [])[:3], 1):
                print(f"  {i}. {pattern.get('item', 'N/A')} ({pattern.get('frequency', 0)} accounts)")
        else:
            print(f"⚠ {result.get('message', 'Insufficient data')}")
    else:
        print(f"✗ Error: {response.status_code}")

    # ========================================================================
    # Step 4: New Account C Benefits from Network
    # ========================================================================
    print_header("STEP 4: New Account C Benefits from Network")

    account_c_id = "new_fitness_account_789"

    print(f"New fitness account ({account_c_id}) joins the platform...")
    print("Even though they have NO history, they benefit from A + B!")
    print()

    print("Step 4a: Detect their niche...")
    response = requests.post(
        f"{ML_SERVICE_URL}/api/cross-learning/detect-niche",
        json={"account_id": account_c_id}
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✓ Niche detected: {result.get('niche', 'N/A')} ({result.get('confidence', 0):.1%} confidence)")
    else:
        print(f"✗ Error detecting niche: {response.status_code}")

    print()
    print("Step 4b: Apply niche wisdom to bootstrap their success...")
    response = requests.post(
        f"{ML_SERVICE_URL}/api/cross-learning/apply-wisdom",
        json={
            "account_id": account_c_id,
            "auto_apply": False  # Just show recommendations
        }
    )

    if response.status_code == 200:
        result = response.json()
        if result.get("success"):
            recommendations = result.get("recommendations", {})
            print_result("Recommendations for Account C", recommendations)
            print("✓ Network effect in action!")
            print()
            print("Account C now knows:")
            print(f"  - Best hook types from {recommendations.get('based_on_accounts', 0)} successful accounts")
            print(f"  - Optimal video duration: {recommendations.get('recommended_patterns', {}).get('optimal_duration', {})}")
            print(f"  - Best posting times: {recommendations.get('recommended_patterns', {}).get('best_posting_hours', [])}")
            print(f"  - Proven CTA styles")
            print()
            print("WITHOUT network effects: Account C would start from zero")
            print("WITH network effects: Account C starts with proven patterns")
            print("Result: 10x faster time to success!")
        else:
            print(f"⚠ {result.get('message', 'Could not apply wisdom')}")
    else:
        print(f"✗ Error: {response.status_code}")

    # ========================================================================
    # Step 5: Cross-Learning Dashboard
    # ========================================================================
    print_header("STEP 5: Cross-Learning Dashboard")

    print(f"View comprehensive dashboard for Account A...")
    print()

    response = requests.get(
        f"{ML_SERVICE_URL}/api/cross-learning/dashboard/{account_a_id}"
    )

    if response.status_code == 200:
        dashboard = response.json()
        if not dashboard.get("error"):
            print_result("Account A Dashboard", dashboard)
            print("Dashboard shows:")
            print("  - Account's niche and confidence")
            print("  - Performance vs. niche benchmarks")
            print("  - Improvement opportunities")
            print("  - Network stats")
        else:
            print(f"⚠ Error: {dashboard.get('error')}")
    else:
        print(f"✗ Error: {response.status_code}")

    # ========================================================================
    # Step 6: System-Wide Network Stats
    # ========================================================================
    print_header("STEP 6: Network Effect Statistics")

    print("Get system-wide cross-learning statistics...")
    print()

    response = requests.get(f"{ML_SERVICE_URL}/api/cross-learning/stats")

    if response.status_code == 200:
        stats = response.json()
        print_result("Network Effect Stats", stats)
        print()
        print("Network Effects Summary:")
        network = stats.get("network_effects", {})
        print(f"  - Total accounts: {network.get('total_accounts', 0)}")
        print(f"  - Active niches: {network.get('active_niches', 0)}")
        print(f"  - Learning power: {network.get('learning_power', 'N/A')}")
        print()
        print("Privacy Guarantee:")
        privacy = stats.get("privacy", {})
        print(f"  - Content shared: {privacy.get('content_shared', True)}")
        print(f"  - Only patterns: {privacy.get('only_patterns', False)}")
        print(f"  - Anonymized: {privacy.get('anonymized', False)}")
        print(f"  - Opt-in required: {privacy.get('opt_in_required', False)}")
    else:
        print(f"✗ Error: {response.status_code}")

    # ========================================================================
    # Summary
    # ========================================================================
    print_header("SUMMARY: The Power of Network Effects")

    print("Traditional Approach:")
    print("  - Each account learns independently")
    print("  - Repeats the same mistakes")
    print("  - Slow learning curve")
    print("  - No compound effect")
    print()
    print("Cross-Account Learning Approach:")
    print("  - Accounts share anonymized patterns")
    print("  - Learn from collective success")
    print("  - New accounts bootstrap instantly")
    print("  - Compound knowledge growth")
    print()
    print("RESULT: 10X LEVERAGE")
    print("  - Platform gets smarter with every account")
    print("  - More accounts = Better insights for everyone")
    print("  - Privacy-preserving (no content shared)")
    print("  - Sustainable competitive advantage")
    print()
    print_header("Demo Complete!")


def demo_niche_detection():
    """
    Demonstrate AI-powered niche detection.
    """
    print_header("NICHE DETECTION DEMO")

    # Test different account types
    test_accounts = [
        {"id": "fitness_pro_123", "expected": "fitness"},
        {"id": "beauty_brand_456", "expected": "beauty"},
        {"id": "saas_startup_789", "expected": "saas"},
        {"id": "ecommerce_shop_101", "expected": "ecommerce"},
    ]

    print("Testing niche detection on various accounts...")
    print()

    for account in test_accounts:
        print(f"Account: {account['id']}")
        print(f"Expected niche: {account['expected']}")

        response = requests.post(
            f"{ML_SERVICE_URL}/api/cross-learning/detect-niche",
            json={"account_id": account['id']}
        )

        if response.status_code == 200:
            result = response.json()
            detected = result.get('niche', 'unknown')
            confidence = result.get('confidence', 0)

            status = "✓" if detected == account['expected'] else "✗"
            print(f"{status} Detected: {detected} ({confidence:.1%} confidence)")
        else:
            print(f"✗ Error: {response.status_code}")

        print()


if __name__ == "__main__":
    print("\n\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  CROSS-ACCOUNT LEARNING SYSTEM - Agent 49".center(78) + "║")
    print("║" + "  Network Effects Create 10x Leverage".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    print("BEFORE RUNNING THIS DEMO:")
    print("1. Ensure ML service is running: python src/main.py")
    print("2. Service should be available at: http://localhost:8003")
    print()
    input("Press Enter to start the demo...")

    # Run main demo
    asyncio.run(demo_cross_learning())

    print()
    print("=" * 80)
    print()

    # Run niche detection demo
    demo_niche_detection()

    print("\n\n")
    print("Demo complete! Cross-account learning is ready to create network effects.")
    print()
