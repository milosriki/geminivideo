"""
Day-Part Optimizer Usage Examples
Agent 8 - Day-Part Optimizer

Demonstrates how to use the day-part optimization system for:
- Analyzing campaign performance patterns
- Generating optimal schedules
- Applying niche wisdom
- Tracking results
"""
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import day-part modules
from src.daypart import (
    DayPartOptimizer,
    DayPartScheduler,
    TimeAnalyzer,
    DayPartPerformance
)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def example_1_basic_analysis():
    """Example 1: Basic campaign analysis."""
    print("\n" + "="*60)
    print("Example 1: Basic Campaign Analysis")
    print("="*60)

    db = SessionLocal()

    try:
        # Initialize optimizer
        optimizer = DayPartOptimizer(
            db_session=db,
            ewma_alpha=0.2,  # Balanced time decay
            confidence_level=0.95  # 95% confidence intervals
        )

        # Analyze campaign
        print("\n📊 Analyzing campaign performance...")
        analysis = optimizer.analyze_campaign(
            campaign_id="camp_fitness_001",
            platform="meta",
            niche="fitness",
            lookback_days=30,
            min_samples=100
        )

        if 'error' in analysis:
            print(f"❌ Error: {analysis['error']}")
            return

        # Print results
        print(f"\n✅ Analysis Complete!")
        print(f"   Campaign: {analysis['campaign_id']}")
        print(f"   Platform: {analysis['platform']}")
        print(f"   Confidence: {analysis['analysis_confidence']:.1%}")
        print(f"   Total Samples: {analysis['total_samples']}")

        print(f"\n🎯 Detected Patterns:")
        for pattern in analysis['detected_patterns']:
            print(f"   - {pattern['pattern_type']}")
            print(f"     Strength: {pattern['pattern_strength']:.2f}")
            if 'hours' in pattern:
                print(f"     Hours: {pattern['hours']}")

        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"   {i}. [{rec['priority'].upper()}] {rec['title']}")
            print(f"      {rec['description']}")

    finally:
        db.close()


def example_2_generate_schedule():
    """Example 2: Generate optimized schedule with budget allocation."""
    print("\n" + "="*60)
    print("Example 2: Generate Optimized Schedule")
    print("="*60)

    db = SessionLocal()

    try:
        # Initialize scheduler
        scheduler = DayPartScheduler(db_session=db)

        # Generate balanced schedule
        print("\n📅 Generating balanced schedule...")
        schedule = scheduler.generate_schedule(
            campaign_id="camp_fitness_001",
            platform="meta",
            total_daily_budget=1000.0,
            schedule_type="balanced",
            peak_multiplier=1.5,
            valley_multiplier=0.5
        )

        print(f"\n✅ Schedule Generated!")
        print(f"   Schedule ID: {schedule['schedule_id']}")
        print(f"   Total Budget: ${schedule['total_daily_budget']:.2f}")

        # Budget allocation
        allocation = schedule['budget_allocation']
        print(f"\n💰 Budget Allocation:")
        print(f"   Peak Hours:   ${allocation['peak_hours_budget']:.2f} ({allocation['peak_hours_percentage']:.1f}%)")
        print(f"   Valley Hours: ${allocation['valley_hours_budget']:.2f} ({allocation['valley_hours_percentage']:.1f}%)")
        print(f"   Normal Hours: ${allocation['normal_hours_budget']:.2f} ({allocation['normal_hours_percentage']:.1f}%)")

        # Predicted performance
        metrics = schedule['predicted_metrics']
        print(f"\n📈 Predicted Performance:")
        print(f"   Expected ROAS: {metrics['predicted_roas']:.2f}x")
        print(f"   Baseline ROAS: {metrics['baseline_roas']:.2f}x")
        print(f"   Expected Lift: +{metrics['expected_lift']:.1f}%")
        print(f"   Confidence: {metrics['confidence_score']:.1%}")

        # Show sample hourly schedule
        print(f"\n⏰ Sample Hourly Schedule (Peak Hours):")
        peak_hours = [h for h in schedule['hourly_schedule'] if h['status'] == 'peak'][:5]
        for hour in peak_hours:
            print(f"   {hour['hour_label']}: ${hour['allocated_budget']:.2f} (ROAS: {hour['expected_roas']:.2f}x)")

    finally:
        db.close()


def example_3_strategy_comparison():
    """Example 3: Compare different scheduling strategies."""
    print("\n" + "="*60)
    print("Example 3: Strategy Comparison")
    print("="*60)

    db = SessionLocal()

    try:
        scheduler = DayPartScheduler(db_session=db)
        strategies = ["conservative", "balanced", "aggressive"]

        print("\n🔍 Comparing scheduling strategies...\n")

        for strategy in strategies:
            schedule = scheduler.generate_schedule(
                campaign_id="camp_fitness_001",
                platform="meta",
                total_daily_budget=1000.0,
                schedule_type=strategy,
                peak_multiplier=1.5 if strategy == "balanced" else (1.2 if strategy == "conservative" else 2.0),
                valley_multiplier=0.5
            )

            metrics = schedule['predicted_metrics']
            allocation = schedule['budget_allocation']

            print(f"📊 {strategy.upper()} Strategy:")
            print(f"   Expected ROAS: {metrics['predicted_roas']:.2f}x")
            print(f"   Expected Lift: +{metrics['expected_lift']:.1f}%")
            print(f"   Peak Budget: ${allocation['peak_hours_budget']:.2f} ({allocation['peak_hours_percentage']:.1f}%)")
            print(f"   Confidence: {metrics['confidence_score']:.1%}")
            print()

    finally:
        db.close()


def example_4_time_analysis():
    """Example 4: Detailed time-based analysis."""
    print("\n" + "="*60)
    print("Example 4: Detailed Time Analysis")
    print("="*60)

    db = SessionLocal()

    try:
        # Initialize analyzer
        analyzer = TimeAnalyzer(db_session=db)

        campaign_id = "camp_fitness_001"
        platform = "meta"

        # Get hourly metrics
        print("\n📊 Analyzing hourly performance...")
        hour_metrics = analyzer.aggregate_by_hour(
            campaign_id=campaign_id,
            lookback_days=30,
            platform=platform
        )

        # Detect peak hours
        peak_hours = analyzer.detect_peak_hours(
            hour_metrics,
            metric='avg_roas',
            threshold_percentile=0.75
        )

        # Detect valley hours
        valley_hours = analyzer.detect_valley_hours(
            hour_metrics,
            metric='avg_roas',
            threshold_percentile=0.25
        )

        print(f"\n⭐ Peak Hours (Top 25%): {peak_hours}")
        print(f"   Average ROAS: {sum(hour_metrics[h]['avg_roas'] for h in peak_hours) / len(peak_hours):.2f}x")

        print(f"\n⬇️  Valley Hours (Bottom 25%): {valley_hours}")
        print(f"   Average ROAS: {sum(hour_metrics[h]['avg_roas'] for h in valley_hours) / len(valley_hours):.2f}x")

        # Day of week analysis
        print("\n📅 Analyzing daily performance...")
        day_metrics = analyzer.aggregate_by_day_of_week(
            campaign_id=campaign_id,
            lookback_days=30,
            platform=platform
        )

        print("\n   Day-by-day breakdown:")
        for day, metrics in day_metrics.items():
            print(f"   {metrics['day_name']:10s}: ROAS {metrics['avg_roas']:.2f}x, CTR {metrics['avg_ctr']:.3%}")

        # Detect weekend pattern
        weekend_pattern = analyzer.detect_weekend_pattern(day_metrics)
        if weekend_pattern:
            print(f"\n🎯 Weekend Pattern Detected: {weekend_pattern['pattern_type']}")
            print(f"   Weekend Avg: {weekend_pattern['weekend_avg']:.2f}x")
            print(f"   Weekday Avg: {weekend_pattern['weekday_avg']:.2f}x")
            print(f"   Lift: {weekend_pattern['lift']:.1%}")

        # Time of day patterns
        time_patterns = analyzer.detect_time_of_day_patterns(hour_metrics)
        print(f"\n🕐 Time of Day Patterns:")
        print(f"   Best Period: {time_patterns['best_period'].title()}")
        print(f"   Performance: {time_patterns['best_period_avg']:.2f}x ROAS")

        # Performance consistency
        consistency = analyzer.calculate_performance_consistency(hour_metrics)
        print(f"\n📐 Performance Consistency: {consistency:.1%}")
        print(f"   {'High consistency - reliable patterns' if consistency > 0.7 else 'Variable - patterns may change'}")

    finally:
        db.close()


def example_5_niche_wisdom():
    """Example 5: Apply niche wisdom to new campaign."""
    print("\n" + "="*60)
    print("Example 5: Apply Niche Wisdom")
    print("="*60)

    db = SessionLocal()

    try:
        optimizer = DayPartOptimizer(db_session=db)

        # Get niche patterns
        print("\n🧠 Retrieving niche wisdom for 'fitness'...")
        niche_patterns = optimizer.get_niche_patterns(
            niche="fitness",
            platform="meta",
            min_confidence=0.6
        )

        print(f"\n✅ Found {len(niche_patterns)} proven patterns for fitness niche")

        for pattern in niche_patterns[:3]:  # Show top 3
            print(f"\n   Pattern: {pattern['pattern_type']}")
            print(f"   Optimal Hours: {pattern['optimal_hours']}")
            print(f"   Expected ROAS: {pattern['avg_roas']:.2f}x")
            print(f"   Confidence: {pattern['confidence']:.1%}")
            print(f"   Lift Factor: {pattern['lift_factor']:.2f}x")

        # Apply to new campaign
        print("\n\n🎯 Applying niche wisdom to new campaign...")
        wisdom_result = optimizer.apply_niche_wisdom(
            campaign_id="camp_fitness_new",
            niche="fitness",
            platform="meta"
        )

        if wisdom_result['applied']:
            print(f"✅ Applied {wisdom_result['patterns_applied']} patterns")
            print(f"\n   Recommendations:")
            for rec in wisdom_result['recommendations'][:3]:
                print(f"   - {rec['pattern_type']}: Hours {rec['optimal_hours']}")
                print(f"     Expected ROAS: {rec['expected_roas']:.2f}x (Lift: {rec['lift_factor']:.2f}x)")

    finally:
        db.close()


def example_6_create_sample_data():
    """Example 6: Create sample performance data for testing."""
    print("\n" + "="*60)
    print("Example 6: Create Sample Data")
    print("="*60)

    db = SessionLocal()

    try:
        campaign_id = "camp_demo_001"
        platform = "meta"

        print(f"\n📝 Creating sample data for {campaign_id}...")

        # Create 30 days of hourly data
        base_date = datetime.utcnow() - timedelta(days=30)
        created_count = 0

        for day in range(30):
            for hour in range(24):
                current_date = base_date + timedelta(days=day, hours=hour)

                # Simulate realistic patterns
                # Peak: 18-22 (evening)
                # Valley: 2-6 (late night/early morning)
                if 18 <= hour <= 22:
                    roas = 3.5 + (day % 5) * 0.2
                    ctr = 0.045
                    impressions_base = 2000
                elif 2 <= hour <= 6:
                    roas = 1.2 + (day % 3) * 0.1
                    ctr = 0.015
                    impressions_base = 500
                else:
                    roas = 2.0 + (day % 4) * 0.15
                    ctr = 0.025
                    impressions_base = 1000

                impressions = impressions_base + hour * 50
                clicks = int(impressions * ctr)
                conversions = clicks // 5
                spend = 100 + hour * 5
                revenue = spend * roas

                perf = DayPartPerformance(
                    campaign_id=campaign_id,
                    platform=platform,
                    hour_of_day=hour,
                    day_of_week=current_date.weekday(),
                    date=current_date,
                    timezone='UTC',
                    impressions=impressions,
                    clicks=clicks,
                    conversions=conversions,
                    spend=spend,
                    revenue=revenue,
                    ctr=ctr,
                    cvr=conversions / clicks if clicks > 0 else 0.0,
                    cpc=spend / clicks if clicks > 0 else 0.0,
                    cpa=spend / conversions if conversions > 0 else 0.0,
                    roas=roas
                )

                db.add(perf)
                created_count += 1

                if created_count % 100 == 0:
                    db.commit()

        db.commit()
        print(f"✅ Created {created_count} performance records")
        print(f"   Date Range: {base_date.date()} to {datetime.utcnow().date()}")
        print(f"   Simulated Patterns:")
        print(f"   - Peak Hours: 18-22 (ROAS ~3.5x)")
        print(f"   - Valley Hours: 2-6 (ROAS ~1.2x)")
        print(f"   - Normal Hours: Others (ROAS ~2.0x)")

    finally:
        db.close()


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Day-Part Optimizer - Usage Examples")
    print("Agent 8 - Day-Part Optimizer")
    print("="*60)

    examples = [
        ("Create Sample Data", example_6_create_sample_data),
        ("Basic Analysis", example_1_basic_analysis),
        ("Generate Schedule", example_2_generate_schedule),
        ("Strategy Comparison", example_3_strategy_comparison),
        ("Time Analysis", example_4_time_analysis),
        ("Niche Wisdom", example_5_niche_wisdom),
    ]

    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  0. Run All")

    choice = input("\nSelect example (0-6): ").strip()

    if choice == "0":
        for name, func in examples:
            try:
                func()
            except Exception as e:
                print(f"\n❌ Error in {name}: {e}")
    elif choice.isdigit() and 1 <= int(choice) <= len(examples):
        try:
            examples[int(choice) - 1][1]()
        except Exception as e:
            print(f"\n❌ Error: {e}")
    else:
        print("Invalid choice")

    print("\n" + "="*60)
    print("Examples Complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
