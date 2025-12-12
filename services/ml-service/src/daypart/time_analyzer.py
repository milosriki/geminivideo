"""
Time Analyzer - Day-Part Performance Analysis
Agent 8 - Day-Part Optimizer

Analyzes historical ad performance by time buckets (hour, day of week)
and identifies peak performance windows.

Features:
- Time bucket aggregation (hourly, daily)
- Pattern detection (weekend vs weekday, morning vs evening)
- Timezone normalization
- Statistical significance testing
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from .models import DayPartPerformance, DayPartPattern

logger = logging.getLogger(__name__)


class TimeAnalyzer:
    """
    Analyzes performance data across time dimensions.

    Provides methods to parse, aggregate, and analyze ad performance
    by hour of day, day of week, and detect temporal patterns.
    """

    def __init__(self, db_session: Session):
        """
        Initialize Time Analyzer.

        Args:
            db_session: Database session for data access
        """
        self.db = db_session
        logger.info("TimeAnalyzer initialized")

    def normalize_timezone(
        self,
        timestamp: datetime,
        from_tz: str = 'UTC',
        to_tz: str = 'UTC'
    ) -> datetime:
        """
        Normalize timestamp to target timezone.

        Args:
            timestamp: Original timestamp
            from_tz: Source timezone
            to_tz: Target timezone

        Returns:
            Normalized datetime
        """
        if timestamp.tzinfo is None:
            timestamp = pytz.timezone(from_tz).localize(timestamp)
        else:
            timestamp = timestamp.astimezone(pytz.timezone(from_tz))

        return timestamp.astimezone(pytz.timezone(to_tz))

    def aggregate_by_hour(
        self,
        campaign_id: str,
        lookback_days: int = 30,
        platform: Optional[str] = None
    ) -> Dict[int, Dict[str, float]]:
        """
        Aggregate performance metrics by hour of day.

        Args:
            campaign_id: Campaign identifier
            lookback_days: Days of history to analyze
            platform: Optional platform filter

        Returns:
            Dictionary mapping hour (0-23) to aggregated metrics
        """
        logger.info(f"Aggregating hourly data for campaign {campaign_id}, lookback={lookback_days} days")

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        # Query performance data
        query = self.db.query(DayPartPerformance).filter(
            DayPartPerformance.campaign_id == campaign_id,
            DayPartPerformance.date >= cutoff_date
        )

        if platform:
            query = query.filter(DayPartPerformance.platform == platform)

        performances = query.all()

        if not performances:
            logger.warning(f"No performance data found for campaign {campaign_id}")
            return {}

        # Aggregate by hour
        hour_data = defaultdict(lambda: {
            'impressions': [],
            'clicks': [],
            'conversions': [],
            'spend': [],
            'revenue': [],
            'ctr': [],
            'cvr': [],
            'roas': [],
            'samples': 0
        })

        for perf in performances:
            hour = perf.hour_of_day
            hour_data[hour]['impressions'].append(perf.impressions)
            hour_data[hour]['clicks'].append(perf.clicks)
            hour_data[hour]['conversions'].append(perf.conversions)
            hour_data[hour]['spend'].append(perf.spend)
            hour_data[hour]['revenue'].append(perf.revenue)
            hour_data[hour]['ctr'].append(perf.ctr)
            hour_data[hour]['cvr'].append(perf.cvr)
            hour_data[hour]['roas'].append(perf.roas)
            hour_data[hour]['samples'] += 1

        # Calculate aggregated metrics
        hour_metrics = {}
        for hour in range(24):
            data = hour_data[hour]
            if data['samples'] > 0:
                hour_metrics[hour] = {
                    'total_impressions': sum(data['impressions']),
                    'total_clicks': sum(data['clicks']),
                    'total_conversions': sum(data['conversions']),
                    'total_spend': sum(data['spend']),
                    'total_revenue': sum(data['revenue']),
                    'avg_ctr': statistics.mean(data['ctr']) if data['ctr'] else 0.0,
                    'avg_cvr': statistics.mean(data['cvr']) if data['cvr'] else 0.0,
                    'avg_roas': statistics.mean(data['roas']) if data['roas'] else 0.0,
                    'median_roas': statistics.median(data['roas']) if data['roas'] else 0.0,
                    'std_roas': statistics.stdev(data['roas']) if len(data['roas']) > 1 else 0.0,
                    'samples': data['samples'],
                    'min_roas': min(data['roas']) if data['roas'] else 0.0,
                    'max_roas': max(data['roas']) if data['roas'] else 0.0
                }
            else:
                hour_metrics[hour] = {
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'total_conversions': 0,
                    'total_spend': 0.0,
                    'total_revenue': 0.0,
                    'avg_ctr': 0.0,
                    'avg_cvr': 0.0,
                    'avg_roas': 0.0,
                    'median_roas': 0.0,
                    'std_roas': 0.0,
                    'samples': 0,
                    'min_roas': 0.0,
                    'max_roas': 0.0
                }

        logger.info(f"Aggregated data for {len(hour_metrics)} hours")
        return hour_metrics

    def aggregate_by_day_of_week(
        self,
        campaign_id: str,
        lookback_days: int = 30,
        platform: Optional[str] = None
    ) -> Dict[int, Dict[str, float]]:
        """
        Aggregate performance metrics by day of week.

        Args:
            campaign_id: Campaign identifier
            lookback_days: Days of history to analyze
            platform: Optional platform filter

        Returns:
            Dictionary mapping day (0-6, Mon-Sun) to aggregated metrics
        """
        logger.info(f"Aggregating daily data for campaign {campaign_id}")

        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        query = self.db.query(DayPartPerformance).filter(
            DayPartPerformance.campaign_id == campaign_id,
            DayPartPerformance.date >= cutoff_date
        )

        if platform:
            query = query.filter(DayPartPerformance.platform == platform)

        performances = query.all()

        if not performances:
            return {}

        # Aggregate by day of week
        day_data = defaultdict(lambda: {
            'impressions': [],
            'clicks': [],
            'conversions': [],
            'spend': [],
            'revenue': [],
            'ctr': [],
            'cvr': [],
            'roas': [],
            'samples': 0
        })

        for perf in performances:
            day = perf.day_of_week
            day_data[day]['impressions'].append(perf.impressions)
            day_data[day]['clicks'].append(perf.clicks)
            day_data[day]['conversions'].append(perf.conversions)
            day_data[day]['spend'].append(perf.spend)
            day_data[day]['revenue'].append(perf.revenue)
            day_data[day]['ctr'].append(perf.ctr)
            day_data[day]['cvr'].append(perf.cvr)
            day_data[day]['roas'].append(perf.roas)
            day_data[day]['samples'] += 1

        # Calculate aggregated metrics
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_metrics = {}

        for day in range(7):
            data = day_data[day]
            if data['samples'] > 0:
                day_metrics[day] = {
                    'day_name': day_names[day],
                    'total_impressions': sum(data['impressions']),
                    'total_clicks': sum(data['clicks']),
                    'total_conversions': sum(data['conversions']),
                    'total_spend': sum(data['spend']),
                    'total_revenue': sum(data['revenue']),
                    'avg_ctr': statistics.mean(data['ctr']) if data['ctr'] else 0.0,
                    'avg_cvr': statistics.mean(data['cvr']) if data['cvr'] else 0.0,
                    'avg_roas': statistics.mean(data['roas']) if data['roas'] else 0.0,
                    'median_roas': statistics.median(data['roas']) if data['roas'] else 0.0,
                    'std_roas': statistics.stdev(data['roas']) if len(data['roas']) > 1 else 0.0,
                    'samples': data['samples']
                }
            else:
                day_metrics[day] = {
                    'day_name': day_names[day],
                    'total_impressions': 0,
                    'total_clicks': 0,
                    'total_conversions': 0,
                    'total_spend': 0.0,
                    'total_revenue': 0.0,
                    'avg_ctr': 0.0,
                    'avg_cvr': 0.0,
                    'avg_roas': 0.0,
                    'median_roas': 0.0,
                    'std_roas': 0.0,
                    'samples': 0
                }

        return day_metrics

    def detect_peak_hours(
        self,
        hour_metrics: Dict[int, Dict[str, float]],
        metric: str = 'avg_roas',
        threshold_percentile: float = 0.75,
        min_samples: int = 5
    ) -> List[int]:
        """
        Detect peak performing hours based on metrics.

        Args:
            hour_metrics: Aggregated hourly metrics
            metric: Metric to use for detection ('avg_roas', 'avg_ctr', 'avg_cvr')
            threshold_percentile: Percentile threshold for peak classification
            min_samples: Minimum samples required per hour

        Returns:
            List of peak hour indices
        """
        # Filter hours with sufficient samples
        valid_hours = {
            hour: metrics
            for hour, metrics in hour_metrics.items()
            if metrics.get('samples', 0) >= min_samples
        }

        if not valid_hours:
            logger.warning("No hours with sufficient samples for peak detection")
            return []

        # Get metric values
        metric_values = [metrics[metric] for metrics in valid_hours.values()]

        if not metric_values:
            return []

        # Calculate threshold
        sorted_values = sorted(metric_values)
        threshold_idx = int(len(sorted_values) * threshold_percentile)
        threshold = sorted_values[threshold_idx] if threshold_idx < len(sorted_values) else sorted_values[-1]

        # Identify peak hours
        peak_hours = [
            hour for hour, metrics in valid_hours.items()
            if metrics[metric] >= threshold
        ]

        logger.info(f"Detected {len(peak_hours)} peak hours with {metric} >= {threshold:.4f}")
        return sorted(peak_hours)

    def detect_valley_hours(
        self,
        hour_metrics: Dict[int, Dict[str, float]],
        metric: str = 'avg_roas',
        threshold_percentile: float = 0.25,
        min_samples: int = 5
    ) -> List[int]:
        """
        Detect poor performing hours (valleys).

        Args:
            hour_metrics: Aggregated hourly metrics
            metric: Metric to use for detection
            threshold_percentile: Percentile threshold for valley classification
            min_samples: Minimum samples required per hour

        Returns:
            List of valley hour indices
        """
        valid_hours = {
            hour: metrics
            for hour, metrics in hour_metrics.items()
            if metrics.get('samples', 0) >= min_samples
        }

        if not valid_hours:
            return []

        metric_values = [metrics[metric] for metrics in valid_hours.values()]

        if not metric_values:
            return []

        sorted_values = sorted(metric_values)
        threshold_idx = int(len(sorted_values) * threshold_percentile)
        threshold = sorted_values[threshold_idx] if threshold_idx < len(sorted_values) else sorted_values[0]

        valley_hours = [
            hour for hour, metrics in valid_hours.items()
            if metrics[metric] <= threshold
        ]

        logger.info(f"Detected {len(valley_hours)} valley hours with {metric} <= {threshold:.4f}")
        return sorted(valley_hours)

    def detect_weekend_pattern(
        self,
        day_metrics: Dict[int, Dict[str, float]],
        metric: str = 'avg_roas',
        lift_threshold: float = 1.1
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if weekends perform significantly better or worse.

        Args:
            day_metrics: Aggregated daily metrics
            metric: Metric to analyze
            lift_threshold: Minimum lift to consider significant

        Returns:
            Pattern details or None if no significant pattern
        """
        # Weekend is Saturday (5) and Sunday (6)
        weekend_days = [5, 6]
        weekday_days = [0, 1, 2, 3, 4]

        # Calculate weekend average
        weekend_values = [
            day_metrics[day][metric]
            for day in weekend_days
            if day in day_metrics and day_metrics[day].get('samples', 0) > 0
        ]

        weekday_values = [
            day_metrics[day][metric]
            for day in weekday_days
            if day in day_metrics and day_metrics[day].get('samples', 0) > 0
        ]

        if not weekend_values or not weekday_values:
            return None

        weekend_avg = statistics.mean(weekend_values)
        weekday_avg = statistics.mean(weekday_values)

        # Calculate lift
        lift = weekend_avg / weekday_avg if weekday_avg > 0 else 0.0

        if lift >= lift_threshold or lift <= (1.0 / lift_threshold):
            pattern_type = 'weekend_boost' if lift >= lift_threshold else 'weekday_boost'

            return {
                'pattern_type': pattern_type,
                'weekend_avg': weekend_avg,
                'weekday_avg': weekday_avg,
                'lift': lift,
                'is_significant': True
            }

        return None

    def detect_time_of_day_patterns(
        self,
        hour_metrics: Dict[int, Dict[str, float]],
        metric: str = 'avg_roas'
    ) -> Dict[str, Any]:
        """
        Detect time-of-day patterns (morning, afternoon, evening, night).

        Args:
            hour_metrics: Aggregated hourly metrics
            metric: Metric to analyze

        Returns:
            Dictionary with time-of-day pattern analysis
        """
        # Define time periods
        time_periods = {
            'morning': list(range(6, 12)),    # 6 AM - 12 PM
            'afternoon': list(range(12, 17)), # 12 PM - 5 PM
            'evening': list(range(17, 22)),   # 5 PM - 10 PM
            'night': list(range(22, 24)) + list(range(0, 6))  # 10 PM - 6 AM
        }

        period_performance = {}

        for period_name, hours in time_periods.items():
            values = [
                hour_metrics[hour][metric]
                for hour in hours
                if hour in hour_metrics and hour_metrics[hour].get('samples', 0) > 0
            ]

            if values:
                period_performance[period_name] = {
                    'avg': statistics.mean(values),
                    'median': statistics.median(values),
                    'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                    'samples': len(values)
                }
            else:
                period_performance[period_name] = {
                    'avg': 0.0,
                    'median': 0.0,
                    'std': 0.0,
                    'samples': 0
                }

        # Identify best performing period
        best_period = max(
            period_performance.items(),
            key=lambda x: x[1]['avg'] if x[1]['samples'] > 0 else 0
        )

        return {
            'period_performance': period_performance,
            'best_period': best_period[0],
            'best_period_avg': best_period[1]['avg']
        }

    def calculate_performance_consistency(
        self,
        hour_metrics: Dict[int, Dict[str, float]],
        metric: str = 'avg_roas'
    ) -> float:
        """
        Calculate how consistent performance is across hours.

        Args:
            hour_metrics: Aggregated hourly metrics
            metric: Metric to analyze

        Returns:
            Consistency score (0.0 = highly variable, 1.0 = very consistent)
        """
        values = [
            metrics[metric]
            for metrics in hour_metrics.values()
            if metrics.get('samples', 0) > 0
        ]

        if len(values) < 2:
            return 0.0

        mean_val = statistics.mean(values)
        if mean_val == 0:
            return 0.0

        std_val = statistics.stdev(values)
        cv = std_val / mean_val  # Coefficient of variation

        # Convert to consistency score (inverse of CV, bounded 0-1)
        consistency = 1.0 / (1.0 + cv)

        return consistency

    def get_statistical_summary(
        self,
        campaign_id: str,
        lookback_days: int = 30,
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive statistical summary of time-based performance.

        Args:
            campaign_id: Campaign identifier
            lookback_days: Days of history to analyze
            platform: Optional platform filter

        Returns:
            Complete statistical summary
        """
        logger.info(f"Generating statistical summary for campaign {campaign_id}")

        hour_metrics = self.aggregate_by_hour(campaign_id, lookback_days, platform)
        day_metrics = self.aggregate_by_day_of_week(campaign_id, lookback_days, platform)

        if not hour_metrics or not day_metrics:
            return {
                'error': 'Insufficient data',
                'campaign_id': campaign_id
            }

        peak_hours = self.detect_peak_hours(hour_metrics)
        valley_hours = self.detect_valley_hours(hour_metrics)
        weekend_pattern = self.detect_weekend_pattern(day_metrics)
        time_patterns = self.detect_time_of_day_patterns(hour_metrics)
        consistency = self.calculate_performance_consistency(hour_metrics)

        return {
            'campaign_id': campaign_id,
            'platform': platform,
            'lookback_days': lookback_days,
            'hour_metrics': hour_metrics,
            'day_metrics': day_metrics,
            'peak_hours': peak_hours,
            'valley_hours': valley_hours,
            'weekend_pattern': weekend_pattern,
            'time_of_day_patterns': time_patterns,
            'performance_consistency': consistency,
            'total_samples': sum(m.get('samples', 0) for m in hour_metrics.values())
        }
