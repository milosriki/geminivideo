"""
Unit Tests for Day-Part Optimization System
Agent 8 - Day-Part Optimizer

Tests for time analysis, EWMA optimization, and schedule generation.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import statistics

# Import day-part modules
from src.daypart.models import (
    Base,
    DayPartPerformance,
    DayPartPattern,
    DayPartSchedule,
    DayPartAnalysis
)
from src.daypart.time_analyzer import TimeAnalyzer
from src.daypart.day_part_optimizer import DayPartOptimizer
from src.daypart.scheduler import DayPartScheduler


# Test Fixtures
@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_performance_data(db_session):
    """Create sample performance data for testing."""
    campaign_id = "test_campaign_001"
    platform = "meta"

    # Create 30 days of hourly performance data
    performances = []
    base_date = datetime.utcnow() - timedelta(days=30)

    for day in range(30):
        for hour in range(24):
            current_date = base_date + timedelta(days=day, hours=hour)
            day_of_week = current_date.weekday()

            # Simulate patterns: peak hours 18-22, valleys 2-6
            if 18 <= hour <= 22:
                roas = 3.5 + (day % 5) * 0.2  # Peak performance
                ctr = 0.045
            elif 2 <= hour <= 6:
                roas = 1.2 + (day % 3) * 0.1  # Valley performance
                ctr = 0.015
            else:
                roas = 2.0 + (day % 4) * 0.15  # Normal performance
                ctr = 0.025

            perf = DayPartPerformance(
                campaign_id=campaign_id,
                platform=platform,
                hour_of_day=hour,
                day_of_week=day_of_week,
                date=current_date,
                impressions=1000 + hour * 50,
                clicks=int((1000 + hour * 50) * ctr),
                conversions=10 + hour // 3,
                spend=100 + hour * 5,
                revenue=(100 + hour * 5) * roas,
                ctr=ctr,
                cvr=0.01,
                roas=roas
            )
            performances.append(perf)

    db_session.add_all(performances)
    db_session.commit()

    return campaign_id, platform


# TimeAnalyzer Tests
class TestTimeAnalyzer:
    """Tests for TimeAnalyzer class."""

    def test_initialization(self, db_session):
        """Test TimeAnalyzer initialization."""
        analyzer = TimeAnalyzer(db_session)
        assert analyzer.db == db_session

    def test_aggregate_by_hour(self, db_session, sample_performance_data):
        """Test hourly aggregation."""
        campaign_id, platform = sample_performance_data
        analyzer = TimeAnalyzer(db_session)

        hour_metrics = analyzer.aggregate_by_hour(
            campaign_id=campaign_id,
            lookback_days=30,
            platform=platform
        )

        assert len(hour_metrics) == 24
        assert all(0 <= h <= 23 for h in hour_metrics.keys())

        # Check that peak hours have higher ROAS
        peak_roas = statistics.mean([
            hour_metrics[h]['avg_roas']
            for h in range(18, 23)
        ])
        valley_roas = statistics.mean([
            hour_metrics[h]['avg_roas']
            for h in range(2, 7)
        ])

        assert peak_roas > valley_roas

    def test_aggregate_by_day_of_week(self, db_session, sample_performance_data):
        """Test daily aggregation."""
        campaign_id, platform = sample_performance_data
        analyzer = TimeAnalyzer(db_session)

        day_metrics = analyzer.aggregate_by_day_of_week(
            campaign_id=campaign_id,
            lookback_days=30,
            platform=platform
        )

        assert len(day_metrics) == 7
        assert all(0 <= d <= 6 for d in day_metrics.keys())
        assert all('day_name' in metrics for metrics in day_metrics.values())

    def test_detect_peak_hours(self, db_session, sample_performance_data):
        """Test peak hour detection."""
        campaign_id, platform = sample_performance_data
        analyzer = TimeAnalyzer(db_session)

        hour_metrics = analyzer.aggregate_by_hour(campaign_id, 30, platform)
        peak_hours = analyzer.detect_peak_hours(
            hour_metrics,
            metric='avg_roas',
            threshold_percentile=0.75
        )

        # Should detect hours 18-22 as peaks
        assert len(peak_hours) > 0
        assert any(h in range(18, 23) for h in peak_hours)

    def test_detect_valley_hours(self, db_session, sample_performance_data):
        """Test valley hour detection."""
        campaign_id, platform = sample_performance_data
        analyzer = TimeAnalyzer(db_session)

        hour_metrics = analyzer.aggregate_by_hour(campaign_id, 30, platform)
        valley_hours = analyzer.detect_valley_hours(
            hour_metrics,
            metric='avg_roas',
            threshold_percentile=0.25
        )

        # Should detect hours 2-6 as valleys
        assert len(valley_hours) > 0
        assert any(h in range(2, 7) for h in valley_hours)

    def test_timezone_normalization(self, db_session):
        """Test timezone conversion."""
        analyzer = TimeAnalyzer(db_session)

        utc_time = datetime(2024, 1, 15, 12, 0, 0)
        normalized = analyzer.normalize_timezone(
            utc_time,
            from_tz='UTC',
            to_tz='US/Pacific'
        )

        # Should be 4 AM Pacific (8 hour difference)
        assert normalized.hour == 4

    def test_performance_consistency(self, db_session, sample_performance_data):
        """Test consistency calculation."""
        campaign_id, platform = sample_performance_data
        analyzer = TimeAnalyzer(db_session)

        hour_metrics = analyzer.aggregate_by_hour(campaign_id, 30, platform)
        consistency = analyzer.calculate_performance_consistency(
            hour_metrics,
            metric='avg_roas'
        )

        assert 0.0 <= consistency <= 1.0


# DayPartOptimizer Tests
class TestDayPartOptimizer:
    """Tests for DayPartOptimizer class."""

    def test_initialization(self, db_session):
        """Test DayPartOptimizer initialization."""
        optimizer = DayPartOptimizer(db_session, ewma_alpha=0.2)
        assert optimizer.db == db_session
        assert optimizer.ewma_alpha == 0.2
        assert optimizer.confidence_level == 0.95

    def test_calculate_ewma(self, db_session):
        """Test EWMA calculation."""
        optimizer = DayPartOptimizer(db_session)

        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        timestamps = [
            datetime.utcnow() - timedelta(hours=i)
            for i in range(5, 0, -1)
        ]

        ewma = optimizer.calculate_ewma(values, timestamps, alpha=0.3)

        # Most recent value (5.0) should have highest weight
        assert ewma > 3.0  # Should be weighted toward recent values

    def test_confidence_interval(self, db_session):
        """Test confidence interval calculation."""
        optimizer = DayPartOptimizer(db_session)

        values = [2.0, 2.5, 3.0, 2.8, 3.2, 2.7, 3.1]
        mean, lower, upper = optimizer.calculate_confidence_interval(values)

        assert lower < mean < upper
        assert mean == statistics.mean(values)

    def test_pattern_strength(self, db_session):
        """Test pattern strength calculation."""
        optimizer = DayPartOptimizer(db_session)

        # Strong positive pattern
        strong_values = [4.0, 4.2, 4.1, 4.3, 4.0]
        baseline = 2.0
        strength = optimizer.calculate_pattern_strength(
            strong_values,
            baseline,
            min_lift=1.1
        )

        assert strength > 0.5  # Should be strong

        # Weak pattern
        weak_values = [2.1, 2.0, 2.2, 2.1, 2.0]
        weak_strength = optimizer.calculate_pattern_strength(
            weak_values,
            baseline,
            min_lift=1.1
        )

        assert weak_strength < 0.3  # Should be weak

    def test_analyze_campaign(self, db_session, sample_performance_data):
        """Test complete campaign analysis."""
        campaign_id, platform = sample_performance_data
        optimizer = DayPartOptimizer(db_session)

        analysis = optimizer.analyze_campaign(
            campaign_id=campaign_id,
            platform=platform,
            lookback_days=30,
            min_samples=100
        )

        assert 'campaign_id' in analysis
        assert 'detected_patterns' in analysis
        assert 'recommendations' in analysis
        assert 'analysis_confidence' in analysis
        assert len(analysis['detected_patterns']) > 0
        assert len(analysis['recommendations']) > 0

    def test_generate_recommendations(self, db_session):
        """Test recommendation generation."""
        optimizer = DayPartOptimizer(db_session)

        summary = {
            'peak_hours': [18, 19, 20, 21, 22],
            'valley_hours': [2, 3, 4, 5, 6],
            'performance_consistency': 0.8,
            'total_samples': 1000
        }

        patterns = [
            {
                'pattern_type': 'peak_hours',
                'hours': [18, 19, 20, 21, 22],
                'pattern_strength': 0.7,
                'lift_vs_baseline': 1.5
            },
            {
                'pattern_type': 'valley_hours',
                'hours': [2, 3, 4, 5, 6],
                'pattern_strength': 0.6,
                'lift_vs_baseline': 0.6
            }
        ]

        baseline = 2.0

        recommendations = optimizer._generate_recommendations(
            summary,
            patterns,
            baseline
        )

        assert len(recommendations) > 0
        assert any(r['action'] == 'concentrate_budget' for r in recommendations)


# DayPartScheduler Tests
class TestDayPartScheduler:
    """Tests for DayPartScheduler class."""

    def test_initialization(self, db_session):
        """Test DayPartScheduler initialization."""
        scheduler = DayPartScheduler(db_session)
        assert scheduler.db == db_session
        assert scheduler.optimizer is not None

    def test_generate_schedule(self, db_session, sample_performance_data):
        """Test schedule generation."""
        campaign_id, platform = sample_performance_data
        scheduler = DayPartScheduler(db_session)

        # First, create an analysis
        optimizer = DayPartOptimizer(db_session)
        optimizer.analyze_campaign(campaign_id, platform)

        # Generate schedule
        schedule = scheduler.generate_schedule(
            campaign_id=campaign_id,
            platform=platform,
            total_daily_budget=1000.0,
            schedule_type='balanced',
            peak_multiplier=1.5,
            valley_multiplier=0.5
        )

        assert 'schedule_id' in schedule
        assert 'hourly_schedule' in schedule
        assert 'daily_schedule' in schedule
        assert 'budget_allocation' in schedule
        assert len(schedule['hourly_schedule']) == 24

        # Verify budget allocation
        total_allocated = sum(
            h['allocated_budget']
            for h in schedule['hourly_schedule']
        )
        assert abs(total_allocated - 1000.0) < 1.0  # Within $1

    def test_hourly_schedule_generation(self, db_session, sample_performance_data):
        """Test hourly schedule with multipliers."""
        campaign_id, platform = sample_performance_data
        scheduler = DayPartScheduler(db_session)

        # Create mock analysis
        optimizer = DayPartOptimizer(db_session)
        optimizer.analyze_campaign(campaign_id, platform)

        analysis = db_session.query(DayPartAnalysis).filter_by(
            campaign_id=campaign_id
        ).first()

        hourly_schedule = scheduler._generate_hourly_schedule(
            analysis,
            total_daily_budget=1000.0,
            peak_multiplier=2.0,
            valley_multiplier=0.5
        )

        assert len(hourly_schedule) == 24

        # Peak hours should have higher budget
        peak_budgets = [
            h['allocated_budget']
            for h in hourly_schedule
            if h['status'] == 'peak'
        ]
        normal_budgets = [
            h['allocated_budget']
            for h in hourly_schedule
            if h['status'] == 'normal'
        ]

        if peak_budgets and normal_budgets:
            avg_peak = statistics.mean(peak_budgets)
            avg_normal = statistics.mean(normal_budgets)
            assert avg_peak > avg_normal

    def test_budget_allocation_summary(self, db_session):
        """Test budget allocation calculation."""
        scheduler = DayPartScheduler(db_session)

        hourly_schedule = [
            {'hour': i, 'allocated_budget': 50.0, 'status': 'peak' if i >= 18 else 'normal'}
            for i in range(24)
        ]

        allocation = scheduler._calculate_budget_allocation(
            hourly_schedule,
            total_daily_budget=1200.0
        )

        assert 'total_budget' in allocation
        assert 'peak_hours_budget' in allocation
        assert 'peak_hours_percentage' in allocation
        assert allocation['total_budget'] == 1200.0


# Integration Tests
class TestDayPartIntegration:
    """Integration tests for complete day-part workflow."""

    def test_end_to_end_workflow(self, db_session, sample_performance_data):
        """Test complete workflow from analysis to schedule."""
        campaign_id, platform = sample_performance_data

        # Step 1: Analyze campaign
        optimizer = DayPartOptimizer(db_session)
        analysis = optimizer.analyze_campaign(
            campaign_id=campaign_id,
            platform=platform
        )

        assert 'detected_patterns' in analysis
        assert len(analysis['detected_patterns']) > 0

        # Step 2: Generate schedule
        scheduler = DayPartScheduler(db_session)
        schedule = scheduler.generate_schedule(
            campaign_id=campaign_id,
            platform=platform,
            total_daily_budget=1000.0
        )

        assert 'schedule_id' in schedule
        assert 'predicted_metrics' in schedule

        # Step 3: Retrieve schedule
        retrieved = scheduler.get_schedule(schedule['schedule_id'])

        assert retrieved is not None
        assert retrieved['campaign_id'] == campaign_id

    def test_insufficient_data_handling(self, db_session):
        """Test handling of campaigns with insufficient data."""
        optimizer = DayPartOptimizer(db_session)

        analysis = optimizer.analyze_campaign(
            campaign_id="nonexistent_campaign",
            platform="meta"
        )

        assert 'error' in analysis


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
