"""
Time-Based Budget Optimization
Part of Agent 47 - Auto-Scaling System

Learns optimal hours for each campaign and automatically
adjusts budgets during peak/valley periods.

Features:
- Learn best/worst hours from historical data
- Automatically scale up during peaks
- Scale down during valleys
- Confidence scoring
- Day-of-week patterns
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
import statistics
import os

from auto_scaler import (
    Base,
    CampaignPerformanceSnapshot,
    OptimalHourProfile,
    ScalingRule
)

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)


class TimeBasedOptimizer:
    """
    Learn and optimize campaign budgets based on time-of-day patterns.

    Analyzes historical performance to identify:
    - Peak performing hours
    - Valley hours
    - Day-of-week patterns
    - Confidence in patterns
    """

    def __init__(self, db_session: Session = None):
        """
        Initialize time optimizer.

        Args:
            db_session: Database session (optional)
        """
        if db_session:
            self.db = db_session
        else:
            from sqlalchemy.orm import sessionmaker
            engine = create_engine(DATABASE_URL)
            Session = sessionmaker(bind=engine)
            self.db = Session()

        logger.info("TimeBasedOptimizer initialized")

    def learn_optimal_hours(
        self,
        campaign_id: str,
        min_samples: int = 24,
        lookback_days: int = 30
    ) -> Optional[OptimalHourProfile]:
        """
        Learn optimal hours from historical performance data.

        Args:
            campaign_id: Campaign ID
            min_samples: Minimum samples per hour to be confident
            lookback_days: Days of history to analyze

        Returns:
            OptimalHourProfile object or None
        """
        logger.info(f"Learning optimal hours for campaign {campaign_id}")

        # Get historical snapshots
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        snapshots = self.db.query(CampaignPerformanceSnapshot).filter(
            CampaignPerformanceSnapshot.campaign_id == campaign_id,
            CampaignPerformanceSnapshot.snapshot_time >= cutoff_date
        ).all()

        if len(snapshots) < min_samples:
            logger.warning(f"Insufficient data for campaign {campaign_id}: {len(snapshots)} < {min_samples}")
            return None

        # Aggregate performance by hour
        hour_data = {h: {'roas': [], 'ctr': [], 'conversion_rate': [], 'samples': 0} for h in range(24)}

        for snapshot in snapshots:
            hour = snapshot.hour_of_day
            hour_data[hour]['roas'].append(snapshot.roas)
            hour_data[hour]['ctr'].append(snapshot.ctr)
            hour_data[hour]['conversion_rate'].append(snapshot.conversion_rate)
            hour_data[hour]['samples'] += 1

        # Calculate average performance per hour
        hour_performance = {}
        for hour in range(24):
            data = hour_data[hour]

            if data['samples'] == 0:
                hour_performance[hour] = {
                    'avg_roas': 0.0,
                    'avg_ctr': 0.0,
                    'avg_conversion_rate': 0.0,
                    'samples': 0
                }
            else:
                hour_performance[hour] = {
                    'avg_roas': statistics.mean(data['roas']),
                    'avg_ctr': statistics.mean(data['ctr']),
                    'avg_conversion_rate': statistics.mean(data['conversion_rate']),
                    'samples': data['samples']
                }

        # Calculate overall averages
        all_roas = [h['avg_roas'] for h in hour_performance.values() if h['samples'] > 0]
        all_ctr = [h['avg_ctr'] for h in hour_performance.values() if h['samples'] > 0]

        if not all_roas or not all_ctr:
            logger.warning(f"No valid hour data for campaign {campaign_id}")
            return None

        overall_avg_roas = statistics.mean(all_roas)
        overall_avg_ctr = statistics.mean(all_ctr)

        # Identify peak hours (ROAS > average + 20%)
        peak_threshold = overall_avg_roas * 1.2
        peak_hours = [
            hour for hour, perf in hour_performance.items()
            if perf['samples'] > 0 and perf['avg_roas'] >= peak_threshold
        ]

        # Identify valley hours (ROAS < average - 20%)
        valley_threshold = overall_avg_roas * 0.8
        valley_hours = [
            hour for hour, perf in hour_performance.items()
            if perf['samples'] > 0 and perf['avg_roas'] <= valley_threshold
        ]

        # Calculate confidence score (0-1)
        total_samples = sum(h['samples'] for h in hour_performance.values())
        avg_samples_per_hour = total_samples / 24
        confidence = min(avg_samples_per_hour / min_samples, 1.0)

        # Create or update profile
        profile = self.db.query(OptimalHourProfile).filter_by(
            campaign_id=campaign_id
        ).first()

        if profile:
            # Update existing
            profile.hour_performance = hour_performance
            profile.peak_hours = peak_hours
            profile.valley_hours = valley_hours
            profile.samples_count = total_samples
            profile.last_learned = datetime.utcnow()
            profile.confidence_score = confidence
        else:
            # Create new
            profile = OptimalHourProfile(
                campaign_id=campaign_id,
                hour_performance=hour_performance,
                peak_hours=peak_hours,
                valley_hours=valley_hours,
                samples_count=total_samples,
                confidence_score=confidence
            )
            self.db.add(profile)

        self.db.commit()

        logger.info(
            f"Learned optimal hours for campaign {campaign_id}: "
            f"{len(peak_hours)} peak hours, {len(valley_hours)} valley hours, "
            f"confidence {confidence:.2f}"
        )

        return profile

    def get_time_multiplier(
        self,
        campaign_id: str,
        current_hour: int = None,
        rule: ScalingRule = None
    ) -> Tuple[float, str]:
        """
        Get budget multiplier for current hour.

        Args:
            campaign_id: Campaign ID
            current_hour: Hour to check (defaults to now)
            rule: Scaling rule with peak multiplier

        Returns:
            Tuple of (multiplier, reason)
        """
        if current_hour is None:
            current_hour = datetime.utcnow().hour

        # Get learned profile
        profile = self.db.query(OptimalHourProfile).filter_by(
            campaign_id=campaign_id
        ).first()

        if not profile:
            return 1.0, "No time profile learned yet"

        # Need minimum confidence to apply time-based scaling
        if profile.confidence_score < 0.3:
            return 1.0, f"Low confidence ({profile.confidence_score:.2f})"

        # Get peak multiplier from rule or use default
        peak_multiplier = rule.peak_hours_multiplier if rule else 1.3
        valley_multiplier = 1.0 / peak_multiplier  # Inverse for valleys

        # Check if current hour is peak
        if current_hour in profile.peak_hours:
            return peak_multiplier, f"Peak hour {current_hour}:00 (confidence {profile.confidence_score:.2f})"

        # Check if current hour is valley
        if current_hour in profile.valley_hours:
            return valley_multiplier, f"Valley hour {current_hour}:00 (confidence {profile.confidence_score:.2f})"

        # Normal hour
        return 1.0, f"Normal hour {current_hour}:00"

    def get_hour_performance(
        self,
        campaign_id: str,
        hour: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for specific hour.

        Args:
            campaign_id: Campaign ID
            hour: Hour (0-23)

        Returns:
            Performance dict or None
        """
        profile = self.db.query(OptimalHourProfile).filter_by(
            campaign_id=campaign_id
        ).first()

        if not profile:
            return None

        return profile.hour_performance.get(str(hour))

    def bulk_learn_campaigns(
        self,
        campaign_ids: List[str] = None,
        min_samples: int = 24
    ) -> Dict[str, Any]:
        """
        Learn optimal hours for multiple campaigns.

        Args:
            campaign_ids: List of campaign IDs (None = all with data)
            min_samples: Minimum samples required

        Returns:
            Summary of learning results
        """
        logger.info("Bulk learning optimal hours")

        if not campaign_ids:
            # Get all campaigns with snapshot data
            campaign_ids = [
                row[0] for row in self.db.query(
                    CampaignPerformanceSnapshot.campaign_id
                ).distinct().all()
            ]

        results = {
            'total_campaigns': len(campaign_ids),
            'learned': 0,
            'insufficient_data': 0,
            'errors': 0,
            'details': []
        }

        for campaign_id in campaign_ids:
            try:
                profile = self.learn_optimal_hours(campaign_id, min_samples)

                if profile:
                    results['learned'] += 1
                    results['details'].append({
                        'campaign_id': campaign_id,
                        'status': 'learned',
                        'peak_hours': profile.peak_hours,
                        'valley_hours': profile.valley_hours,
                        'confidence': profile.confidence_score
                    })
                else:
                    results['insufficient_data'] += 1
                    results['details'].append({
                        'campaign_id': campaign_id,
                        'status': 'insufficient_data'
                    })

            except Exception as e:
                logger.error(f"Error learning hours for campaign {campaign_id}: {e}")
                results['errors'] += 1
                results['details'].append({
                    'campaign_id': campaign_id,
                    'status': 'error',
                    'error': str(e)
                })

        logger.info(
            f"Bulk learning complete: {results['learned']} learned, "
            f"{results['insufficient_data']} insufficient data, "
            f"{results['errors']} errors"
        )

        return results

    def get_campaign_time_report(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed time-based performance report for campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Detailed report dict
        """
        profile = self.db.query(OptimalHourProfile).filter_by(
            campaign_id=campaign_id
        ).first()

        if not profile:
            return None

        # Build hour-by-hour breakdown
        hourly_breakdown = []
        for hour in range(24):
            perf = profile.hour_performance.get(str(hour), {})

            status = "normal"
            if hour in profile.peak_hours:
                status = "peak"
            elif hour in profile.valley_hours:
                status = "valley"

            hourly_breakdown.append({
                'hour': hour,
                'hour_label': f"{hour:02d}:00",
                'status': status,
                'avg_roas': perf.get('avg_roas', 0),
                'avg_ctr': perf.get('avg_ctr', 0),
                'avg_conversion_rate': perf.get('avg_conversion_rate', 0),
                'samples': perf.get('samples', 0)
            })

        return {
            'campaign_id': campaign_id,
            'peak_hours': profile.peak_hours,
            'valley_hours': profile.valley_hours,
            'normal_hours': [h for h in range(24) if h not in profile.peak_hours and h not in profile.valley_hours],
            'confidence_score': profile.confidence_score,
            'total_samples': profile.samples_count,
            'last_learned': profile.last_learned.isoformat(),
            'hourly_breakdown': hourly_breakdown
        }

    def recommend_budget_schedule(
        self,
        campaign_id: str,
        base_daily_budget: float,
        peak_multiplier: float = 1.3
    ) -> List[Dict[str, Any]]:
        """
        Generate recommended hourly budget schedule.

        Args:
            campaign_id: Campaign ID
            base_daily_budget: Base daily budget
            peak_multiplier: Multiplier for peak hours

        Returns:
            List of hourly budget recommendations
        """
        profile = self.db.query(OptimalHourProfile).filter_by(
            campaign_id=campaign_id
        ).first()

        if not profile or profile.confidence_score < 0.3:
            # Not enough confidence - use flat budget
            hourly_budget = base_daily_budget / 24
            return [
                {
                    'hour': h,
                    'hour_label': f"{h:02d}:00",
                    'budget': round(hourly_budget, 2),
                    'multiplier': 1.0,
                    'status': 'normal'
                }
                for h in range(24)
            ]

        # Calculate weighted budget allocation
        valley_multiplier = 1.0 / peak_multiplier

        # Calculate total multiplier units
        total_units = 0
        for hour in range(24):
            if hour in profile.peak_hours:
                total_units += peak_multiplier
            elif hour in profile.valley_hours:
                total_units += valley_multiplier
            else:
                total_units += 1.0

        # Budget per unit
        budget_per_unit = base_daily_budget / total_units

        # Generate schedule
        schedule = []
        for hour in range(24):
            if hour in profile.peak_hours:
                multiplier = peak_multiplier
                status = "peak"
            elif hour in profile.valley_hours:
                multiplier = valley_multiplier
                status = "valley"
            else:
                multiplier = 1.0
                status = "normal"

            hourly_budget = budget_per_unit * multiplier

            schedule.append({
                'hour': hour,
                'hour_label': f"{hour:02d}:00",
                'budget': round(hourly_budget, 2),
                'multiplier': multiplier,
                'status': status
            })

        return schedule


if __name__ == "__main__":
    # Test time optimizer
    optimizer = TimeBasedOptimizer()
    print("TimeBasedOptimizer initialized")
