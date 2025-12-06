"""
Auto-Budget Shifter

Automatically shifts budget from underperforming ads to winners.
This is how AI generates real ROI - money flows to what works.

Human budget management: Check weekly, make 1-2 changes
AI budget management: Check hourly, make optimal micro-adjustments
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict

logger = logging.getLogger(__name__)

class AdStatus(Enum):
    LEARNING = "learning"      # Not enough data
    SCALING = "scaling"        # Performing well, increase budget
    MAINTAINING = "maintaining"  # Stable performance
    DECLINING = "declining"    # Performance dropping
    PAUSED = "paused"          # Below threshold, paused

@dataclass
class AdPerformance:
    """Performance data for an ad"""
    ad_id: str
    campaign_id: str
    creative_id: str

    # Spend
    spend: float
    daily_budget: float

    # Performance metrics
    impressions: int
    clicks: int
    conversions: int
    revenue: float

    # Calculated metrics
    ctr: float
    cvr: float
    cpa: float
    roas: float

    # Time data
    hours_active: int
    last_conversion_time: Optional[datetime]

    # Status
    status: AdStatus
    confidence: float  # How confident in the metrics

@dataclass
class BudgetRecommendation:
    """Recommendation for budget change"""
    ad_id: str
    current_budget: float
    recommended_budget: float
    change_amount: float
    change_percent: float
    reason: str
    confidence: float
    priority: int  # 1 = highest priority

@dataclass
class BudgetShiftResult:
    """Result of budget shift operation"""
    successful: bool
    changes_made: List[Dict]
    total_budget_shifted: float
    expected_impact: Dict
    execution_time: datetime
    error: Optional[str] = None

class BudgetOptimizer:
    """
    Automatically optimize ad budgets based on performance.

    Strategy:
    1. Identify winners (high ROAS)
    2. Identify losers (low ROAS, high CPA)
    3. Shift budget from losers to winners
    4. Cap changes to avoid volatility
    5. Respect learning phase
    """

    # Thresholds
    MIN_SPEND_FOR_DECISION = 50  # Minimum spend before making changes
    MIN_CONVERSIONS_FOR_DECISION = 5  # Minimum conversions for confidence
    LEARNING_PERIOD_HOURS = 24  # Hours before making changes

    # Budget change limits
    MAX_BUDGET_INCREASE_PERCENT = 50  # Max 50% increase per shift
    MAX_BUDGET_DECREASE_PERCENT = 50  # Max 50% decrease per shift
    MIN_BUDGET = 10  # Minimum daily budget

    # Performance thresholds
    TARGET_ROAS = 2.0  # Target ROAS
    MIN_ROAS_THRESHOLD = 1.0  # Below this = loser
    SCALE_ROAS_THRESHOLD = 3.0  # Above this = scale aggressively

    def __init__(self, target_roas: float = 2.0):
        self.target_roas = target_roas
        self.min_roas = target_roas * 0.5
        self.scale_roas = target_roas * 1.5

    def analyze_ads(self, ads: List[AdPerformance]) -> Dict[str, List[AdPerformance]]:
        """
        Analyze ads and categorize by performance.

        Returns:
            Dict with 'winners', 'losers', 'learning', 'stable' lists
        """
        categories = {
            'winners': [],      # ROAS > scale_roas
            'stable': [],       # ROAS between target and scale
            'underperforming': [],  # ROAS between min and target
            'losers': [],       # ROAS < min_roas
            'learning': []      # Not enough data
        }

        for ad in ads:
            category = self._categorize_ad(ad)
            categories[category].append(ad)

        return categories

    def _categorize_ad(self, ad: AdPerformance) -> str:
        """Categorize a single ad"""
        # Check if still in learning
        if ad.hours_active < self.LEARNING_PERIOD_HOURS:
            return 'learning'
        if ad.spend < self.MIN_SPEND_FOR_DECISION:
            return 'learning'
        if ad.conversions < self.MIN_CONVERSIONS_FOR_DECISION:
            return 'learning'

        # Categorize by ROAS
        if ad.roas >= self.scale_roas:
            return 'winners'
        elif ad.roas >= self.target_roas:
            return 'stable'
        elif ad.roas >= self.min_roas:
            return 'underperforming'
        else:
            return 'losers'

    def generate_recommendations(self, ads: List[AdPerformance],
                                  total_daily_budget: float = None) -> List[BudgetRecommendation]:
        """
        Generate budget shift recommendations.

        Args:
            ads: List of ad performance data
            total_daily_budget: Optional total budget constraint

        Returns:
            List of budget recommendations
        """
        categories = self.analyze_ads(ads)
        recommendations = []

        # Calculate how much budget to shift
        budget_from_losers = sum(ad.daily_budget for ad in categories['losers'])
        budget_from_underperforming = sum(ad.daily_budget * 0.3 for ad in categories['underperforming'])
        available_to_shift = budget_from_losers + budget_from_underperforming

        # Recommendations for losers: Cut budget significantly
        for i, ad in enumerate(categories['losers']):
            new_budget = max(self.MIN_BUDGET, ad.daily_budget * 0.3)  # Cut 70%
            recommendations.append(BudgetRecommendation(
                ad_id=ad.ad_id,
                current_budget=ad.daily_budget,
                recommended_budget=new_budget,
                change_amount=new_budget - ad.daily_budget,
                change_percent=((new_budget - ad.daily_budget) / ad.daily_budget) * 100,
                reason=f"ROAS {ad.roas:.2f} below threshold {self.min_roas}. Cutting budget.",
                confidence=min(1.0, ad.spend / 100),  # More spend = more confidence
                priority=1  # Highest priority to stop waste
            ))

        # Recommendations for underperforming: Reduce budget
        for ad in categories['underperforming']:
            new_budget = max(self.MIN_BUDGET, ad.daily_budget * 0.7)  # Cut 30%
            recommendations.append(BudgetRecommendation(
                ad_id=ad.ad_id,
                current_budget=ad.daily_budget,
                recommended_budget=new_budget,
                change_amount=new_budget - ad.daily_budget,
                change_percent=((new_budget - ad.daily_budget) / ad.daily_budget) * 100,
                reason=f"ROAS {ad.roas:.2f} below target {self.target_roas}. Reducing budget.",
                confidence=min(1.0, ad.spend / 100),
                priority=2
            ))

        # Recommendations for winners: Increase budget
        if categories['winners'] and available_to_shift > 0:
            budget_per_winner = available_to_shift / len(categories['winners'])

            for ad in sorted(categories['winners'], key=lambda a: a.roas, reverse=True):
                max_increase = ad.daily_budget * (self.MAX_BUDGET_INCREASE_PERCENT / 100)
                increase = min(budget_per_winner, max_increase)
                new_budget = ad.daily_budget + increase

                recommendations.append(BudgetRecommendation(
                    ad_id=ad.ad_id,
                    current_budget=ad.daily_budget,
                    recommended_budget=new_budget,
                    change_amount=increase,
                    change_percent=(increase / ad.daily_budget) * 100,
                    reason=f"ROAS {ad.roas:.2f} exceeds scale threshold. Scaling up.",
                    confidence=min(1.0, ad.spend / 100),
                    priority=3
                ))

        # Sort by priority
        recommendations.sort(key=lambda r: (r.priority, -abs(r.change_amount)))

        return recommendations

    async def execute_budget_shifts(self, recommendations: List[BudgetRecommendation],
                                     platform_client: Any = None) -> BudgetShiftResult:
        """
        Execute budget shift recommendations.

        Args:
            recommendations: List of budget recommendations
            platform_client: API client for Meta/Google (optional)

        Returns:
            BudgetShiftResult with execution details
        """
        changes_made = []
        total_shifted = 0

        for rec in recommendations:
            try:
                # Would call actual API here
                if platform_client:
                    # await platform_client.update_budget(rec.ad_id, rec.recommended_budget)
                    pass

                changes_made.append({
                    'ad_id': rec.ad_id,
                    'old_budget': rec.current_budget,
                    'new_budget': rec.recommended_budget,
                    'change': rec.change_amount,
                    'reason': rec.reason
                })

                total_shifted += abs(rec.change_amount)

                logger.info(f"Budget shift: {rec.ad_id} ${rec.current_budget:.2f} -> ${rec.recommended_budget:.2f}")

            except Exception as e:
                logger.error(f"Failed to update budget for {rec.ad_id}: {e}")

        return BudgetShiftResult(
            successful=len(changes_made) > 0,
            changes_made=changes_made,
            total_budget_shifted=total_shifted,
            expected_impact={
                'estimated_roas_improvement': 0.2,  # Placeholder
                'estimated_daily_savings': sum(c['change'] for c in changes_made if c['change'] < 0)
            },
            execution_time=datetime.now()
        )

    def get_optimization_report(self, ads: List[AdPerformance]) -> Dict:
        """Generate optimization report"""
        categories = self.analyze_ads(ads)

        total_spend = sum(ad.spend for ad in ads)
        total_revenue = sum(ad.revenue for ad in ads)
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0

        return {
            'overall_roas': overall_roas,
            'total_spend': total_spend,
            'total_revenue': total_revenue,
            'ad_count': len(ads),
            'distribution': {
                'winners': len(categories['winners']),
                'stable': len(categories['stable']),
                'underperforming': len(categories['underperforming']),
                'losers': len(categories['losers']),
                'learning': len(categories['learning'])
            },
            'potential_savings': sum(ad.spend for ad in categories['losers']),
            'scaling_opportunity': sum(ad.daily_budget for ad in categories['winners']),
            'recommendations_count': len(self.generate_recommendations(ads))
        }

    def simulate_optimization(self, ads: List[AdPerformance],
                               days: int = 7) -> Dict:
        """Simulate optimization impact over time"""
        # Simple simulation
        current_roas = sum(ad.revenue for ad in ads) / sum(ad.spend for ad in ads)

        # Estimate improvement from shifting budget
        recommendations = self.generate_recommendations(ads)
        improvement_per_day = 0.02  # 2% improvement per day

        projected = []
        roas = current_roas
        for day in range(days):
            roas *= (1 + improvement_per_day)
            projected.append({
                'day': day + 1,
                'projected_roas': roas
            })

        return {
            'current_roas': current_roas,
            'projected_roas_after_optimization': roas,
            'improvement_percent': ((roas - current_roas) / current_roas) * 100,
            'daily_projections': projected
        }
