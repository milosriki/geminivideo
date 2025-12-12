"""
Day-Part Optimizer - Core Optimization Engine
Agent 8 - Day-Part Optimizer

Optimizes ad scheduling based on historical performance patterns using
exponential weighted moving average (EWMA) for time decay and provides
confidence intervals for recommendations.

Features:
- EWMA-based time decay for recent data emphasis
- Confidence interval calculation
- Niche-specific optimization
- Platform-aware recommendations
- Pattern strength scoring
"""
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import statistics
import math
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import DayPartPerformance, DayPartPattern, DayPartAnalysis
from .time_analyzer import TimeAnalyzer

logger = logging.getLogger(__name__)


class DayPartOptimizer:
    """
    Core day-part optimization engine.

    Uses EWMA for time-weighted pattern detection and provides
    actionable recommendations with confidence intervals.
    """

    def __init__(
        self,
        db_session: Session,
        ewma_alpha: float = 0.2,
        confidence_level: float = 0.95
    ):
        """
        Initialize Day-Part Optimizer.

        Args:
            db_session: Database session
            ewma_alpha: EWMA decay factor (0-1, higher = more weight on recent data)
            confidence_level: Confidence level for intervals (0-1)
        """
        self.db = db_session
        self.ewma_alpha = ewma_alpha
        self.confidence_level = confidence_level
        self.analyzer = TimeAnalyzer(db_session)
        logger.info(f"DayPartOptimizer initialized (alpha={ewma_alpha}, confidence={confidence_level})")

    def calculate_ewma(
        self,
        values: List[float],
        timestamps: List[datetime],
        alpha: Optional[float] = None
    ) -> float:
        """
        Calculate exponentially weighted moving average.

        More recent values get higher weights, with exponential decay
        for older values.

        Args:
            values: List of metric values
            timestamps: Corresponding timestamps
            alpha: Decay factor (uses instance default if None)

        Returns:
            EWMA value
        """
        if not values or not timestamps:
            return 0.0

        if len(values) != len(timestamps):
            raise ValueError("Values and timestamps must have same length")

        alpha = alpha or self.ewma_alpha

        # Sort by timestamp (oldest first)
        sorted_data = sorted(zip(timestamps, values), key=lambda x: x[0])

        # Calculate EWMA
        ewma = sorted_data[0][1]  # Start with first value

        for i in range(1, len(sorted_data)):
            value = sorted_data[i][1]
            ewma = alpha * value + (1 - alpha) * ewma

        return ewma

    def calculate_confidence_interval(
        self,
        values: List[float],
        confidence_level: Optional[float] = None
    ) -> Tuple[float, float, float]:
        """
        Calculate confidence interval for metric values.

        Args:
            values: List of metric values
            confidence_level: Confidence level (uses instance default if None)

        Returns:
            Tuple of (mean, lower_bound, upper_bound)
        """
        if not values:
            return 0.0, 0.0, 0.0

        if len(values) == 1:
            return values[0], values[0], values[0]

        confidence_level = confidence_level or self.confidence_level

        mean = statistics.mean(values)
        std = statistics.stdev(values)
        n = len(values)

        # Use t-distribution for small samples, normal for large
        if n < 30:
            # Approximate t-critical value for 95% confidence
            t_critical = 2.0 if n < 10 else 1.96
        else:
            # Z-score for confidence level
            if confidence_level >= 0.99:
                t_critical = 2.576
            elif confidence_level >= 0.95:
                t_critical = 1.96
            else:
                t_critical = 1.645

        margin = t_critical * (std / math.sqrt(n))
        lower = mean - margin
        upper = mean + margin

        return mean, lower, upper

    def calculate_pattern_strength(
        self,
        metric_values: List[float],
        baseline: float,
        min_lift: float = 1.1
    ) -> float:
        """
        Calculate pattern strength score (0-1).

        Measures how strongly the pattern performs vs baseline.

        Args:
            metric_values: Performance values for the pattern
            baseline: Baseline performance to compare against
            min_lift: Minimum lift to consider pattern strong

        Returns:
            Strength score (0.0 = weak, 1.0 = very strong)
        """
        if not metric_values or baseline == 0:
            return 0.0

        mean_performance = statistics.mean(metric_values)
        lift = mean_performance / baseline if baseline > 0 else 0.0

        # Pattern is stronger with higher lift and more consistency
        consistency = 1.0 / (1.0 + statistics.stdev(metric_values) / mean_performance) if mean_performance > 0 else 0.0

        # Combine lift and consistency
        if lift >= min_lift:
            # Positive pattern
            lift_score = min((lift - 1.0) / (min_lift - 1.0), 1.0)
        elif lift <= (1.0 / min_lift):
            # Negative pattern (valley)
            lift_score = min((1.0 - lift) / (1.0 - 1.0 / min_lift), 1.0)
        else:
            # Weak pattern
            lift_score = 0.0

        strength = (lift_score * 0.7) + (consistency * 0.3)

        return max(0.0, min(1.0, strength))

    def analyze_campaign(
        self,
        campaign_id: str,
        platform: str,
        niche: Optional[str] = None,
        lookback_days: int = 30,
        min_samples: int = 100
    ) -> Dict[str, Any]:
        """
        Perform comprehensive day-part analysis for a campaign.

        Args:
            campaign_id: Campaign identifier
            platform: Platform ('meta', 'tiktok', 'google')
            niche: Optional niche identifier
            lookback_days: Days of history to analyze
            min_samples: Minimum samples required

        Returns:
            Complete analysis results with patterns and recommendations
        """
        logger.info(f"Analyzing campaign {campaign_id} on {platform}")

        # Get statistical summary from analyzer
        summary = self.analyzer.get_statistical_summary(
            campaign_id,
            lookback_days,
            platform
        )

        if 'error' in summary:
            logger.warning(f"Analysis failed: {summary['error']}")
            return summary

        if summary['total_samples'] < min_samples:
            logger.warning(f"Insufficient samples: {summary['total_samples']} < {min_samples}")
            return {
                'error': 'Insufficient data',
                'campaign_id': campaign_id,
                'samples': summary['total_samples'],
                'required': min_samples
            }

        # Calculate baseline performance
        all_roas_values = [
            m['avg_roas'] for m in summary['hour_metrics'].values()
            if m.get('samples', 0) > 0
        ]
        baseline_roas = statistics.mean(all_roas_values) if all_roas_values else 0.0

        # Detect and score patterns
        detected_patterns = []

        # Peak hours pattern
        if summary['peak_hours']:
            peak_values = [
                summary['hour_metrics'][h]['avg_roas']
                for h in summary['peak_hours']
            ]
            peak_timestamps = [
                datetime.utcnow() - timedelta(hours=i)
                for i in range(len(peak_values))
            ]

            peak_ewma = self.calculate_ewma(peak_values, peak_timestamps)
            peak_mean, peak_lower, peak_upper = self.calculate_confidence_interval(peak_values)
            peak_strength = self.calculate_pattern_strength(peak_values, baseline_roas)

            detected_patterns.append({
                'pattern_type': 'peak_hours',
                'hours': summary['peak_hours'],
                'ewma_roas': peak_ewma,
                'mean_roas': peak_mean,
                'confidence_interval': {
                    'lower': peak_lower,
                    'upper': peak_upper,
                    'level': self.confidence_level
                },
                'pattern_strength': peak_strength,
                'lift_vs_baseline': peak_mean / baseline_roas if baseline_roas > 0 else 0.0,
                'samples': sum(summary['hour_metrics'][h]['samples'] for h in summary['peak_hours'])
            })

        # Valley hours pattern
        if summary['valley_hours']:
            valley_values = [
                summary['hour_metrics'][h]['avg_roas']
                for h in summary['valley_hours']
            ]
            valley_timestamps = [
                datetime.utcnow() - timedelta(hours=i)
                for i in range(len(valley_values))
            ]

            valley_ewma = self.calculate_ewma(valley_values, valley_timestamps)
            valley_mean, valley_lower, valley_upper = self.calculate_confidence_interval(valley_values)
            valley_strength = self.calculate_pattern_strength(valley_values, baseline_roas, min_lift=0.9)

            detected_patterns.append({
                'pattern_type': 'valley_hours',
                'hours': summary['valley_hours'],
                'ewma_roas': valley_ewma,
                'mean_roas': valley_mean,
                'confidence_interval': {
                    'lower': valley_lower,
                    'upper': valley_upper,
                    'level': self.confidence_level
                },
                'pattern_strength': valley_strength,
                'lift_vs_baseline': valley_mean / baseline_roas if baseline_roas > 0 else 0.0,
                'samples': sum(summary['hour_metrics'][h]['samples'] for h in summary['valley_hours'])
            })

        # Weekend pattern
        if summary['weekend_pattern']:
            detected_patterns.append({
                'pattern_type': summary['weekend_pattern']['pattern_type'],
                'details': summary['weekend_pattern'],
                'pattern_strength': 0.7 if summary['weekend_pattern']['is_significant'] else 0.3
            })

        # Time of day pattern
        best_period = summary['time_of_day_patterns']['best_period']
        detected_patterns.append({
            'pattern_type': f'{best_period}_prime',
            'details': summary['time_of_day_patterns'],
            'pattern_strength': 0.6
        })

        # Generate recommendations
        recommendations = self._generate_recommendations(
            summary,
            detected_patterns,
            baseline_roas
        )

        # Calculate overall analysis confidence
        analysis_confidence = self._calculate_analysis_confidence(
            summary['total_samples'],
            summary['performance_consistency'],
            len(detected_patterns)
        )

        analysis_result = {
            'campaign_id': campaign_id,
            'platform': platform,
            'niche': niche,
            'lookback_days': lookback_days,
            'baseline_roas': baseline_roas,
            'detected_patterns': detected_patterns,
            'recommendations': recommendations,
            'performance_consistency': summary['performance_consistency'],
            'analysis_confidence': analysis_confidence,
            'total_samples': summary['total_samples'],
            'peak_windows': summary['peak_hours'],
            'valley_windows': summary['valley_hours'],
            'analyzed_at': datetime.utcnow().isoformat()
        }

        # Store analysis in database
        self._store_analysis(analysis_result)

        logger.info(f"Analysis complete: {len(detected_patterns)} patterns detected")
        return analysis_result

    def _generate_recommendations(
        self,
        summary: Dict[str, Any],
        patterns: List[Dict[str, Any]],
        baseline: float
    ) -> List[Dict[str, Any]]:
        """
        Generate actionable recommendations based on patterns.

        Args:
            summary: Statistical summary
            patterns: Detected patterns
            baseline: Baseline performance

        Returns:
            List of recommendations with priority and expected impact
        """
        recommendations = []

        # Peak hours recommendation
        peak_pattern = next((p for p in patterns if p['pattern_type'] == 'peak_hours'), None)
        if peak_pattern and peak_pattern['pattern_strength'] > 0.5:
            expected_lift = (peak_pattern['lift_vs_baseline'] - 1.0) * 100
            recommendations.append({
                'priority': 'high',
                'action': 'concentrate_budget',
                'title': 'Concentrate Budget on Peak Hours',
                'description': f"Increase ad spend during hours {peak_pattern['hours']} which show {expected_lift:.1f}% better performance",
                'expected_impact': {
                    'roas_lift': expected_lift,
                    'confidence': peak_pattern['pattern_strength']
                },
                'implementation': {
                    'target_hours': peak_pattern['hours'],
                    'budget_multiplier': min(peak_pattern['lift_vs_baseline'], 2.0)
                }
            })

        # Valley hours recommendation
        valley_pattern = next((p for p in patterns if p['pattern_type'] == 'valley_hours'), None)
        if valley_pattern and valley_pattern['pattern_strength'] > 0.5:
            expected_savings = (1.0 - valley_pattern['lift_vs_baseline']) * 100
            recommendations.append({
                'priority': 'medium',
                'action': 'reduce_valley_spend',
                'title': 'Reduce Spending During Valley Hours',
                'description': f"Decrease ad spend during hours {valley_pattern['hours']} which underperform by {expected_savings:.1f}%",
                'expected_impact': {
                    'cost_savings': expected_savings,
                    'confidence': valley_pattern['pattern_strength']
                },
                'implementation': {
                    'target_hours': valley_pattern['hours'],
                    'budget_multiplier': max(valley_pattern['lift_vs_baseline'], 0.5)
                }
            })

        # Weekend pattern recommendation
        weekend_pattern = next((p for p in patterns if 'weekend' in p['pattern_type']), None)
        if weekend_pattern and weekend_pattern['pattern_strength'] > 0.5:
            recommendations.append({
                'priority': 'medium',
                'action': 'weekend_adjustment',
                'title': f"Adjust Weekend Strategy",
                'description': f"{weekend_pattern['pattern_type'].replace('_', ' ').title()} detected",
                'expected_impact': {
                    'lift': weekend_pattern['details'].get('lift', 1.0),
                    'confidence': weekend_pattern['pattern_strength']
                }
            })

        # Time of day recommendation
        time_pattern = next((p for p in patterns if 'prime' in p['pattern_type']), None)
        if time_pattern:
            recommendations.append({
                'priority': 'low',
                'action': 'time_of_day_optimization',
                'title': f"Focus on {time_pattern['pattern_type'].split('_')[0].title()} Performance",
                'description': f"Best performance during {time_pattern['pattern_type'].split('_')[0]} hours",
                'expected_impact': {
                    'confidence': time_pattern['pattern_strength']
                }
            })

        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        recommendations.sort(key=lambda x: priority_order.get(x['priority'], 3))

        return recommendations

    def _calculate_analysis_confidence(
        self,
        sample_size: int,
        consistency: float,
        pattern_count: int
    ) -> float:
        """
        Calculate overall confidence in the analysis.

        Args:
            sample_size: Total number of samples
            consistency: Performance consistency score
            pattern_count: Number of detected patterns

        Returns:
            Confidence score (0-1)
        """
        # Sample size contribution (0-1)
        sample_score = min(sample_size / 1000, 1.0)

        # Consistency contribution (0-1)
        consistency_score = consistency

        # Pattern detection contribution (0-1)
        pattern_score = min(pattern_count / 5, 1.0)

        # Weighted combination
        confidence = (
            sample_score * 0.4 +
            consistency_score * 0.3 +
            pattern_score * 0.3
        )

        return confidence

    def _store_analysis(self, analysis_result: Dict[str, Any]) -> None:
        """
        Store analysis results in database.

        Args:
            analysis_result: Analysis results to store
        """
        try:
            analysis_id = f"{analysis_result['campaign_id']}_{analysis_result['platform']}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            analysis = DayPartAnalysis(
                analysis_id=analysis_id,
                campaign_id=analysis_result['campaign_id'],
                platform=analysis_result['platform'],
                niche=analysis_result.get('niche'),
                lookback_days=analysis_result['lookback_days'],
                detected_patterns=analysis_result['detected_patterns'],
                peak_windows=analysis_result['peak_windows'],
                valley_windows=analysis_result['valley_windows'],
                recommendations=analysis_result['recommendations'],
                overall_metrics={
                    'baseline_roas': analysis_result['baseline_roas'],
                    'consistency': analysis_result['performance_consistency']
                },
                total_samples=analysis_result['total_samples'],
                data_quality_score=analysis_result['performance_consistency'],
                analysis_confidence=analysis_result['analysis_confidence'],
                analysis_metadata={
                    'ewma_alpha': self.ewma_alpha,
                    'confidence_level': self.confidence_level
                }
            )

            self.db.add(analysis)
            self.db.commit()

            logger.info(f"Analysis stored: {analysis_id}")

        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")
            self.db.rollback()

    def get_niche_patterns(
        self,
        niche: str,
        platform: str,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Get learned patterns for a specific niche.

        Args:
            niche: Niche identifier
            platform: Platform name
            min_confidence: Minimum confidence threshold

        Returns:
            List of niche patterns
        """
        patterns = self.db.query(DayPartPattern).filter(
            and_(
                DayPartPattern.niche == niche,
                DayPartPattern.platform == platform,
                DayPartPattern.confidence_score >= min_confidence
            )
        ).all()

        return [
            {
                'pattern_id': p.pattern_id,
                'pattern_type': p.pattern_type,
                'optimal_hours': p.optimal_hours,
                'optimal_days': p.optimal_days,
                'avg_roas': p.avg_roas,
                'confidence': p.confidence_score,
                'lift_factor': p.lift_factor
            }
            for p in patterns
        ]

    def apply_niche_wisdom(
        self,
        campaign_id: str,
        niche: str,
        platform: str
    ) -> Dict[str, Any]:
        """
        Apply niche-level patterns to a campaign.

        Args:
            campaign_id: Campaign identifier
            niche: Niche identifier
            platform: Platform name

        Returns:
            Applied wisdom and recommendations
        """
        logger.info(f"Applying niche wisdom: {niche} -> campaign {campaign_id}")

        niche_patterns = self.get_niche_patterns(niche, platform)

        if not niche_patterns:
            return {
                'applied': False,
                'reason': 'No niche patterns available'
            }

        # Combine patterns to create recommendations
        combined_recommendations = []

        for pattern in niche_patterns:
            combined_recommendations.append({
                'source': 'niche_wisdom',
                'niche': niche,
                'pattern_type': pattern['pattern_type'],
                'optimal_hours': pattern['optimal_hours'],
                'expected_roas': pattern['avg_roas'],
                'confidence': pattern['confidence'],
                'lift_factor': pattern['lift_factor']
            })

        return {
            'applied': True,
            'campaign_id': campaign_id,
            'niche': niche,
            'platform': platform,
            'patterns_applied': len(combined_recommendations),
            'recommendations': combined_recommendations
        }
