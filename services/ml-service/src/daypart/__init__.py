"""
Day-Part Optimization System
Agent 8 - Day-Part Optimizer

A comprehensive system for analyzing and optimizing ad scheduling based on
historical performance patterns.

Components:
- TimeAnalyzer: Parse and analyze performance by time buckets
- DayPartOptimizer: EWMA-based optimization with confidence intervals
- DayPartScheduler: Budget-aware schedule generation
- REST API: Endpoints for analysis and scheduling

Features:
- Hour-of-day and day-of-week pattern detection
- Exponential weighted moving average (EWMA) for time decay
- Confidence intervals for recommendations
- Niche-specific optimization
- Multi-platform support (Meta, TikTok, Google Ads)
- Timezone normalization
- Budget-aware scheduling strategies
"""

from .models import (
    DayPartPerformance,
    DayPartPattern,
    DayPartSchedule,
    DayPartAnalysis
)
from .time_analyzer import TimeAnalyzer
from .day_part_optimizer import DayPartOptimizer
from .scheduler import DayPartScheduler, router as daypart_router

__version__ = "1.0.0"
__all__ = [
    "DayPartPerformance",
    "DayPartPattern",
    "DayPartSchedule",
    "DayPartAnalysis",
    "TimeAnalyzer",
    "DayPartOptimizer",
    "DayPartScheduler",
    "daypart_router"
]
