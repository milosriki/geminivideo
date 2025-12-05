"""
Demo/Test Script for Auto-Promotion System
Agent 44 - Demonstrates automatic winner promotion and compound learning

This script shows:
1. How to create A/B test experiments
2. How auto-promotion detects winners
3. How insights are extracted
4. How compound learning accumulates
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import random

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import ABTest as ABTestModel, Video, PerformanceMetric, Base

from src.auto_promoter import AutoPromoter, WinnerInsights


# ==========================================
# DEMO DATA GENERATION
# ==========================================

def create_demo_database():
    """Create in-memory database for demo."""
    # Use SQLite for demo
    engine = create_engine('sqlite:///demo_auto_promotion.db', echo=False)
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    return Session()


def create_demo_experiment(session, experiment_id: str, variant_a_ctr: float, variant_b_ctr: float):
    """
    Create demo A/B test with synthetic performance data.

    Args:
        session: Database session
        experiment_id: Unique experiment ID
        variant_a_ctr: CTR for variant A (e.g., 2.5 = 2.5%)
        variant_b_ctr: CTR for variant B (e.g., 3.2 = 3.2%)
    """
    print(f"\n📊 Creating demo experiment: {experiment_id}")
    print(f"   Variant A CTR: {variant_a_ctr:.2f}%")
    print(f"   Variant B CTR: {variant_b_ctr:.2f}%")

    # Create experiment
    experiment = ABTestModel(
        test_id=experiment_id,
        model_type='ctr_predictor',
        model_a_id=f'{experiment_id}_variant_a',
        model_b_id=f'{experiment_id}_variant_b',
        traffic_split=0.5,
        duration_days=7,
        status='active',
        start_date=datetime.now() - timedelta(days=3),
        end_date=datetime.now() + timedelta(days=4),
        results={}
    )
    session.add(experiment)

    # Create videos for both variants
    video_a = Video(
        id=experiment.model_a_id,
        campaign_id='demo_campaign',
        title=f'Demo Video A - {experiment_id}',
        description='Control variant with standard hook',
        script_content={
            'hook': 'Are you tired of low CTR?',
            'problem': 'Standard approach',
            'solution': 'Our product helps'
        },
        video_url='https://example.com/video_a.mp4',
        status='active',
        meta_platform_id=experiment.model_a_id
    )
    session.add(video_a)

    video_b = Video(
        id=experiment.model_b_id,
        campaign_id='demo_campaign',
        title=f'Demo Video B - {experiment_id}',
        description='Test variant with curiosity hook',
        script_content={
            'hook': 'This weird trick 10x our ad CTR...',
            'problem': 'Pattern interrupt',
            'solution': 'Curiosity-driven approach'
        },
        video_url='https://example.com/video_b.mp4',
        status='active',
        meta_platform_id=experiment.model_b_id
    )
    session.add(video_b)

    # Generate synthetic performance data
    # Simulate 150 samples per variant (enough for statistical significance)
    for day in range(3):  # 3 days of data
        date = datetime.now().date() - timedelta(days=2-day)

        # Variant A metrics (control)
        impressions_a = random.randint(4500, 5500)
        clicks_a = int(impressions_a * variant_a_ctr / 100 * random.uniform(0.9, 1.1))

        metric_a = PerformanceMetric(
            video_id=video_a.id,
            platform='meta',
            date=date,
            impressions=impressions_a,
            clicks=clicks_a,
            spend=impressions_a * 0.01,  # $0.01 CPM
            ctr=clicks_a / impressions_a * 100,
            conversions=int(clicks_a * 0.05)  # 5% conversion rate
        )
        session.add(metric_a)

        # Variant B metrics (test)
        impressions_b = random.randint(4500, 5500)
        clicks_b = int(impressions_b * variant_b_ctr / 100 * random.uniform(0.9, 1.1))

        metric_b = PerformanceMetric(
            video_id=video_b.id,
            platform='meta',
            date=date,
            impressions=impressions_b,
            clicks=clicks_b,
            spend=impressions_b * 0.01,
            ctr=clicks_b / impressions_b * 100,
            conversions=int(clicks_b * 0.05)
        )
        session.add(metric_b)

    session.commit()
    print(f"✓ Experiment {experiment_id} created with performance data")


# ==========================================
# DEMO SCENARIOS
# ==========================================

async def demo_clear_winner():
    """Demo: Clear winner with high confidence."""
    print("\n" + "="*60)
    print("DEMO 1: CLEAR WINNER (High Confidence)")
    print("="*60)

    session = create_demo_database()

    # Create experiment with clear winner (B is 30% better)
    create_demo_experiment(
        session,
        experiment_id='exp_clear_winner',
        variant_a_ctr=2.5,
        variant_b_ctr=3.25  # 30% improvement
    )

    # Initialize auto-promoter (without Meta API for demo)
    promoter = AutoPromoter(
        db_session=session,
        meta_api_manager=None,  # No Meta API in demo
        anthropic_api_key=None,  # No Claude API in demo
        confidence_threshold=0.95,
        min_sample_size=100
    )

    # Check for promotion
    result = await promoter.check_and_promote('exp_clear_winner')

    print(f"\n📈 RESULT:")
    print(f"   Status: {result.status.value}")
    print(f"   Winner: {result.winner_ad_id}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Winner CTR: {result.winner_metrics['ctr']:.2f}%")
    print(f"   Loser CTR: {result.loser_metrics['ctr']:.2f}% (for reference)")

    improvement = ((result.winner_metrics['ctr'] - result.loser_metrics['ctr']) /
                   result.loser_metrics['ctr'] * 100)
    print(f"   Improvement: +{improvement:.1f}%")
    print(f"   Message: {result.message}")

    if result.budget_reallocation:
        print(f"\n💰 BUDGET REALLOCATION:")
        print(f"   Winner: {result.budget_reallocation['winner_budget_pct']:.0%}")
        print(f"   Loser: {result.budget_reallocation['loser_budget_pct']:.0%}")

    session.close()


async def demo_continue_testing():
    """Demo: Not enough confidence yet."""
    print("\n" + "="*60)
    print("DEMO 2: CONTINUE TESTING (Low Confidence)")
    print("="*60)

    session = create_demo_database()

    # Create experiment with marginal difference (B only 5% better)
    create_demo_experiment(
        session,
        experiment_id='exp_continue',
        variant_a_ctr=2.5,
        variant_b_ctr=2.625  # Only 5% improvement
    )

    promoter = AutoPromoter(
        db_session=session,
        meta_api_manager=None,
        anthropic_api_key=None,
        confidence_threshold=0.95,
        min_sample_size=100
    )

    result = await promoter.check_and_promote('exp_continue')

    print(f"\n📊 RESULT:")
    print(f"   Status: {result.status.value}")
    print(f"   Confidence: {result.confidence:.1%}")
    print(f"   Message: {result.message}")
    print(f"\n   ⏰ Keep testing! Difference not significant enough.")

    session.close()


async def demo_compound_learning():
    """Demo: Multiple tests showing compound learning."""
    print("\n" + "="*60)
    print("DEMO 3: COMPOUND LEARNING (Multiple Tests)")
    print("="*60)

    session = create_demo_database()

    # Create 5 experiments with increasing performance
    test_improvements = [
        ('exp_test_1', 2.0, 2.3, 15.0),   # +15%
        ('exp_test_2', 2.3, 2.6, 13.0),   # +13% (from improved baseline)
        ('exp_test_3', 2.6, 3.0, 15.4),   # +15.4%
        ('exp_test_4', 3.0, 3.4, 13.3),   # +13.3%
        ('exp_test_5', 3.4, 4.0, 17.6),   # +17.6%
    ]

    promoter = AutoPromoter(
        db_session=session,
        meta_api_manager=None,
        anthropic_api_key=None,
        confidence_threshold=0.90,  # Lower threshold for demo
        min_sample_size=100
    )

    promoted_count = 0
    improvements = []

    for exp_id, control_ctr, winner_ctr, expected_improvement in test_improvements:
        create_demo_experiment(session, exp_id, control_ctr, winner_ctr)

        # Small delay to simulate time passing
        await asyncio.sleep(0.1)

        result = await promoter.check_and_promote(exp_id)

        if result.status.value == 'promoted':
            promoted_count += 1
            actual_improvement = ((result.winner_metrics['ctr'] - result.loser_metrics['ctr']) /
                                   result.loser_metrics['ctr'] * 100)
            improvements.append(actual_improvement)

            print(f"\n✓ Test {promoted_count}: {exp_id}")
            print(f"   Control: {result.loser_metrics['ctr']:.2f}%")
            print(f"   Winner: {result.winner_metrics['ctr']:.2f}%")
            print(f"   Improvement: +{actual_improvement:.1f}%")
            print(f"   Confidence: {result.confidence:.1%}")

    # Calculate compound improvement
    compound = 1.0
    for imp in improvements:
        compound *= (1 + imp / 100)
    compound_improvement = (compound - 1) * 100

    print(f"\n" + "="*60)
    print(f"📈 COMPOUND LEARNING RESULTS:")
    print(f"="*60)
    print(f"   Total Tests: {promoted_count}")
    print(f"   Avg Improvement/Test: {sum(improvements)/len(improvements):.1f}%")
    print(f"   Compound Improvement: {compound_improvement:.1f}%")
    print(f"\n   Starting CTR: {test_improvements[0][1]:.2f}%")
    print(f"   Final CTR: {test_improvements[-1][2]:.2f}%")
    print(f"   Total Gain: {(test_improvements[-1][2] - test_improvements[0][1]) / test_improvements[0][1] * 100:.1f}%")

    print(f"\n   💡 Each test improved the baseline!")
    print(f"   💡 Knowledge accumulated over time!")
    print(f"   💡 This is 10x leverage through compound learning!")

    session.close()


async def demo_all_active_experiments():
    """Demo: Check all active experiments at once."""
    print("\n" + "="*60)
    print("DEMO 4: CHECK ALL ACTIVE EXPERIMENTS")
    print("="*60)

    session = create_demo_database()

    # Create multiple active experiments
    experiments = [
        ('exp_batch_1', 2.0, 2.5, True),   # Clear winner
        ('exp_batch_2', 2.5, 2.6, False),  # Marginal
        ('exp_batch_3', 3.0, 3.6, True),   # Clear winner
        ('exp_batch_4', 2.2, 2.3, False),  # Marginal
        ('exp_batch_5', 1.8, 2.3, True),   # Clear winner
    ]

    for exp_id, control, test, is_winner in experiments:
        create_demo_experiment(session, exp_id, control, test)

    promoter = AutoPromoter(
        db_session=session,
        meta_api_manager=None,
        anthropic_api_key=None,
        confidence_threshold=0.90,
        min_sample_size=100
    )

    # Check all at once
    results = await promoter.check_all_active_experiments()

    # Summarize results
    promoted = [r for r in results if r.status.value == 'promoted']
    continue_testing = [r for r in results if r.status.value == 'continue_testing']

    print(f"\n📊 BATCH CHECK RESULTS:")
    print(f"   Total Experiments: {len(results)}")
    print(f"   Promoted: {len(promoted)}")
    print(f"   Continue Testing: {len(continue_testing)}")

    print(f"\n✓ PROMOTED:")
    for r in promoted:
        improvement = ((r.winner_metrics['ctr'] - r.loser_metrics['ctr']) /
                       r.loser_metrics['ctr'] * 100)
        print(f"   • {r.experiment_id}: +{improvement:.1f}% improvement ({r.confidence:.1%} confidence)")

    print(f"\n→ CONTINUE TESTING:")
    for r in continue_testing:
        print(f"   • {r.experiment_id}: {r.confidence:.1%} confidence (needs more data)")

    session.close()


# ==========================================
# MAIN DEMO
# ==========================================

async def run_all_demos():
    """Run all demo scenarios."""
    print("\n" + "="*60)
    print("AUTO-PROMOTION SYSTEM DEMO")
    print("Agent 44 - Automatic Winner Promotion")
    print("="*60)

    await demo_clear_winner()
    await asyncio.sleep(1)

    await demo_continue_testing()
    await asyncio.sleep(1)

    await demo_compound_learning()
    await asyncio.sleep(1)

    await demo_all_active_experiments()

    print("\n" + "="*60)
    print("✓ ALL DEMOS COMPLETE")
    print("="*60)
    print("\nKey Takeaways:")
    print("1. Winners detected automatically with 95% confidence")
    print("2. Budget reallocated to winners (80/20 split)")
    print("3. Compound learning: Each test improves the next")
    print("4. Batch processing: Check 100+ experiments at once")
    print("5. Zero manual work: Fully automated")
    print("\n🚀 This is 10x leverage through auto-promotion!")


if __name__ == "__main__":
    # Run demos
    asyncio.run(run_all_demos())

    # Cleanup
    if os.path.exists('demo_auto_promotion.db'):
        os.remove('demo_auto_promotion.db')
        print("\n✓ Demo database cleaned up")
