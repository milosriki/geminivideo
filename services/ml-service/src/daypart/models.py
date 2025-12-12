"""
Database models for Day-Part Optimization System
Agent 8 - Day-Part Optimizer

Stores time-based performance patterns and scheduling recommendations.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from shared.db.models import Base


class DayPartPerformance(Base):
    """
    Historical performance data aggregated by time buckets.

    Stores performance metrics broken down by hour of day, day of week,
    and platform for pattern detection and optimization.
    """
    __tablename__ = "daypart_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String, nullable=False, index=True)
    ad_id = Column(String, nullable=True, index=True)
    platform = Column(String, nullable=False, index=True)  # 'meta', 'tiktok', 'google'
    niche = Column(String, nullable=True, index=True)  # 'fitness', 'ecommerce', etc.

    # Time dimensions
    hour_of_day = Column(Integer, nullable=False)  # 0-23
    day_of_week = Column(Integer, nullable=False)  # 0-6 (Monday=0)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    timezone = Column(String, default='UTC')

    # Performance metrics
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Float, default=0.0)
    revenue = Column(Float, default=0.0)

    # Calculated metrics
    ctr = Column(Float, default=0.0)
    cvr = Column(Float, default=0.0)
    cpc = Column(Float, default=0.0)
    cpa = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)

    # Metadata
    raw_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_daypart_campaign_time', 'campaign_id', 'hour_of_day', 'day_of_week'),
        Index('idx_daypart_platform_niche', 'platform', 'niche', 'date'),
    )


class DayPartPattern(Base):
    """
    Detected patterns for optimal day-part scheduling.

    Stores learned patterns about when ads perform best for specific
    campaigns, platforms, and niches.
    """
    __tablename__ = "daypart_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pattern_id = Column(String, unique=True, nullable=False, index=True)

    # Scope
    campaign_id = Column(String, nullable=True, index=True)  # Null = niche-level pattern
    platform = Column(String, nullable=False, index=True)
    niche = Column(String, nullable=True, index=True)

    # Pattern type
    pattern_type = Column(String, nullable=False)  # 'peak_hours', 'valley_hours', 'weekend_boost', 'weekday_prime'

    # Time windows (JSON arrays)
    optimal_hours = Column(JSON, default=[])  # List of hours: [9, 10, 11, 18, 19, 20]
    optimal_days = Column(JSON, default=[])  # List of days: [0, 1, 4]  (Mon, Tue, Fri)

    # Performance metrics for this pattern
    avg_ctr = Column(Float, default=0.0)
    avg_cvr = Column(Float, default=0.0)
    avg_roas = Column(Float, default=0.0)
    avg_cpc = Column(Float, default=0.0)

    # Pattern strength (EWMA-based)
    pattern_strength = Column(Float, default=0.0)  # 0.0-1.0
    confidence_score = Column(Float, default=0.0)  # 0.0-1.0
    sample_size = Column(Integer, default=0)

    # Statistical properties
    performance_variance = Column(Float, default=0.0)
    baseline_performance = Column(Float, default=0.0)  # Overall average for comparison
    lift_factor = Column(Float, default=1.0)  # Performance multiplier vs baseline

    # EWMA parameters
    ewma_alpha = Column(Float, default=0.2)  # Decay factor for time weighting
    last_ewma_update = Column(DateTime(timezone=True))

    # Metadata
    pattern_details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_pattern_campaign_platform', 'campaign_id', 'platform'),
        Index('idx_pattern_niche_platform', 'niche', 'platform', 'pattern_type'),
    )


class DayPartSchedule(Base):
    """
    Generated optimal schedules for campaign execution.

    Stores recommended schedules with budget allocation across
    different time windows for maximum performance.
    """
    __tablename__ = "daypart_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id = Column(String, unique=True, nullable=False, index=True)

    # Target
    campaign_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)

    # Schedule configuration
    total_daily_budget = Column(Float, nullable=False)
    schedule_type = Column(String, default='balanced')  # 'aggressive', 'balanced', 'conservative'

    # Schedule details (JSON)
    hourly_schedule = Column(JSON, nullable=False)  # Detailed hour-by-hour plan
    daily_schedule = Column(JSON, nullable=False)  # Day-of-week plan
    budget_allocation = Column(JSON, nullable=False)  # Budget distribution

    # Performance predictions
    predicted_roas = Column(Float, default=0.0)
    predicted_conversions = Column(Integer, default=0)
    expected_lift = Column(Float, default=0.0)  # vs flat scheduling

    # Confidence metrics
    confidence_score = Column(Float, default=0.0)
    confidence_interval_lower = Column(Float, default=0.0)
    confidence_interval_upper = Column(Float, default=0.0)

    # Status
    is_active = Column(Boolean, default=False)
    is_applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    # Actual performance (updated after execution)
    actual_roas = Column(Float, nullable=True)
    actual_conversions = Column(Integer, nullable=True)
    actual_lift = Column(Float, nullable=True)

    # Metadata
    generation_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_schedule_campaign_active', 'campaign_id', 'is_active'),
        Index('idx_schedule_created', 'created_at'),
    )


class DayPartAnalysis(Base):
    """
    Analysis results and insights from day-part optimization.

    Stores comprehensive analysis reports for campaigns including
    detected patterns, recommendations, and actionable insights.
    """
    __tablename__ = "daypart_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(String, unique=True, nullable=False, index=True)

    # Target
    campaign_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)
    niche = Column(String, nullable=True)

    # Analysis parameters
    lookback_days = Column(Integer, default=30)
    min_sample_size = Column(Integer, default=100)
    analysis_type = Column(String, default='full')  # 'full', 'quick', 'pattern_detection'

    # Results
    detected_patterns = Column(JSON, nullable=False)  # List of pattern IDs
    peak_windows = Column(JSON, default=[])  # Best performing time windows
    valley_windows = Column(JSON, default=[])  # Poor performing time windows

    # Performance summary
    overall_metrics = Column(JSON, default={})
    hour_performance = Column(JSON, default={})  # 0-23 hour breakdown
    day_performance = Column(JSON, default={})  # 0-6 day breakdown

    # Recommendations
    recommendations = Column(JSON, nullable=False)
    priority_actions = Column(JSON, default=[])
    expected_impact = Column(JSON, default={})

    # Statistical summary
    total_samples = Column(Integer, default=0)
    data_quality_score = Column(Float, default=0.0)
    analysis_confidence = Column(Float, default=0.0)

    # Metadata
    analysis_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_analysis_campaign_created', 'campaign_id', 'created_at'),
    )
