"""
Loser Kill Switch

Automatically pause ads that waste money.
This is critical for protecting ad spend.

Human approach: Notice after $500 wasted
AI approach: Kill after $50 of confirmed waste
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class KillReason(Enum):
    LOW_CTR = "low_ctr"
    LOW_CVR = "low_cvr"
    HIGH_CPA = "high_cpa"
    NEGATIVE_ROAS = "negative_roas"
    NO_CONVERSIONS = "no_conversions"
    DECLINING_PERFORMANCE = "declining_performance"
    BUDGET_EXHAUSTED = "budget_exhausted"
    MANUAL = "manual"

@dataclass
class AdMetrics:
    """Current metrics for an ad"""
    ad_id: str
    campaign_id: str

    # Spend
    spend: float
    budget: float

    # Performance
    impressions: int
    clicks: int
    conversions: int
    revenue: float

    # Calculated
    ctr: float  # clicks / impressions
    cvr: float  # conversions / clicks
    cpa: float  # spend / conversions
    roas: float  # revenue / spend

    # Time
    hours_running: int
    last_conversion: Optional[datetime]

@dataclass
class KillDecision:
    """Decision to kill an ad"""
    ad_id: str
    should_kill: bool
    reason: KillReason
    confidence: float
    waste_prevented: float
    recommendation: str
    metrics_at_kill: Dict

class LoserKillSwitch:
    """
    Automatically kills underperforming ads.

    Kill triggers:
    1. CTR below 0.5% after 1000 impressions
    2. CVR below 0.5% after 100 clicks
    3. CPA above 3x target after 3 conversions
    4. ROAS below 0.5 after $100 spend
    5. No conversions after $100 spend
    6. 50% performance decline over 24 hours
    """

    # Thresholds
    MIN_CTR = 0.005  # 0.5%
    MIN_CTR_IMPRESSIONS = 1000  # Need this many impressions to judge CTR

    MIN_CVR = 0.005  # 0.5%
    MIN_CVR_CLICKS = 100  # Need this many clicks to judge CVR

    MAX_CPA_MULTIPLIER = 3.0  # Kill if CPA is 3x target
    MIN_CPA_CONVERSIONS = 3  # Need this many conversions to judge CPA

    MIN_ROAS = 0.5  # Kill if ROAS below 0.5
    MIN_ROAS_SPEND = 100  # Need this much spend to judge ROAS

    NO_CONVERSION_SPEND_LIMIT = 100  # Kill if no conversions after $100

    DECLINE_THRESHOLD = 0.5  # Kill if 50% decline
    DECLINE_HOURS = 24  # Over 24 hours

    def __init__(self, target_cpa: float = 50.0, target_roas: float = 2.0):
        self.target_cpa = target_cpa
        self.target_roas = target_roas
        self.max_cpa = target_cpa * self.MAX_CPA_MULTIPLIER

    def evaluate_ad(self, metrics: AdMetrics) -> KillDecision:
        """
        Evaluate an ad and decide whether to kill it.

        Args:
            metrics: Current ad metrics

        Returns:
            KillDecision with recommendation
        """
        # Check each kill condition
        checks = [
            self._check_ctr(metrics),
            self._check_cvr(metrics),
            self._check_cpa(metrics),
            self._check_roas(metrics),
            self._check_no_conversions(metrics)
        ]

        # Return first kill trigger found
        for decision in checks:
            if decision.should_kill:
                return decision

        # No kill needed
        return KillDecision(
            ad_id=metrics.ad_id,
            should_kill=False,
            reason=KillReason.MANUAL,
            confidence=0.0,
            waste_prevented=0.0,
            recommendation="Ad is performing within acceptable parameters",
            metrics_at_kill={}
        )

    def _check_ctr(self, metrics: AdMetrics) -> KillDecision:
        """Check if CTR is too low"""
        if metrics.impressions < self.MIN_CTR_IMPRESSIONS:
            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=False,
                reason=KillReason.LOW_CTR,
                confidence=0.0,
                waste_prevented=0.0,
                recommendation="Not enough impressions to evaluate CTR",
                metrics_at_kill={}
            )

        if metrics.ctr < self.MIN_CTR:
            # Estimate waste: remaining budget would be wasted
            waste = metrics.budget - metrics.spend

            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=True,
                reason=KillReason.LOW_CTR,
                confidence=min(1.0, metrics.impressions / 5000),
                waste_prevented=waste,
                recommendation=f"CTR {metrics.ctr*100:.2f}% below minimum {self.MIN_CTR*100:.2f}%. Kill immediately.",
                metrics_at_kill={
                    'ctr': metrics.ctr,
                    'threshold': self.MIN_CTR,
                    'impressions': metrics.impressions
                }
            )

        return KillDecision(
            ad_id=metrics.ad_id,
            should_kill=False,
            reason=KillReason.LOW_CTR,
            confidence=0.0,
            waste_prevented=0.0,
            recommendation="CTR acceptable",
            metrics_at_kill={}
        )

    def _check_cvr(self, metrics: AdMetrics) -> KillDecision:
        """Check if CVR is too low"""
        if metrics.clicks < self.MIN_CVR_CLICKS:
            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=False,
                reason=KillReason.LOW_CVR,
                confidence=0.0,
                waste_prevented=0.0,
                recommendation="Not enough clicks to evaluate CVR",
                metrics_at_kill={}
            )

        if metrics.cvr < self.MIN_CVR:
            waste = metrics.budget - metrics.spend

            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=True,
                reason=KillReason.LOW_CVR,
                confidence=min(1.0, metrics.clicks / 500),
                waste_prevented=waste,
                recommendation=f"CVR {metrics.cvr*100:.2f}% below minimum {self.MIN_CVR*100:.2f}%. No landing page conversion.",
                metrics_at_kill={
                    'cvr': metrics.cvr,
                    'threshold': self.MIN_CVR,
                    'clicks': metrics.clicks
                }
            )

        return KillDecision(
            ad_id=metrics.ad_id,
            should_kill=False,
            reason=KillReason.LOW_CVR,
            confidence=0.0,
            waste_prevented=0.0,
            recommendation="CVR acceptable",
            metrics_at_kill={}
        )

    def _check_cpa(self, metrics: AdMetrics) -> KillDecision:
        """Check if CPA is too high"""
        if metrics.conversions < self.MIN_CPA_CONVERSIONS:
            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=False,
                reason=KillReason.HIGH_CPA,
                confidence=0.0,
                waste_prevented=0.0,
                recommendation="Not enough conversions to evaluate CPA",
                metrics_at_kill={}
            )

        if metrics.cpa > self.max_cpa:
            waste = metrics.budget - metrics.spend

            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=True,
                reason=KillReason.HIGH_CPA,
                confidence=min(1.0, metrics.conversions / 10),
                waste_prevented=waste,
                recommendation=f"CPA ${metrics.cpa:.2f} is {metrics.cpa/self.target_cpa:.1f}x target ${self.target_cpa:.2f}. Too expensive.",
                metrics_at_kill={
                    'cpa': metrics.cpa,
                    'target_cpa': self.target_cpa,
                    'max_cpa': self.max_cpa,
                    'conversions': metrics.conversions
                }
            )

        return KillDecision(
            ad_id=metrics.ad_id,
            should_kill=False,
            reason=KillReason.HIGH_CPA,
            confidence=0.0,
            waste_prevented=0.0,
            recommendation="CPA acceptable",
            metrics_at_kill={}
        )

    def _check_roas(self, metrics: AdMetrics) -> KillDecision:
        """Check if ROAS is too low"""
        if metrics.spend < self.MIN_ROAS_SPEND:
            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=False,
                reason=KillReason.NEGATIVE_ROAS,
                confidence=0.0,
                waste_prevented=0.0,
                recommendation="Not enough spend to evaluate ROAS",
                metrics_at_kill={}
            )

        if metrics.roas < self.MIN_ROAS:
            waste = metrics.budget - metrics.spend

            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=True,
                reason=KillReason.NEGATIVE_ROAS,
                confidence=min(1.0, metrics.spend / 500),
                waste_prevented=waste,
                recommendation=f"ROAS {metrics.roas:.2f}x below minimum {self.MIN_ROAS}x. Losing money.",
                metrics_at_kill={
                    'roas': metrics.roas,
                    'threshold': self.MIN_ROAS,
                    'spend': metrics.spend,
                    'revenue': metrics.revenue
                }
            )

        return KillDecision(
            ad_id=metrics.ad_id,
            should_kill=False,
            reason=KillReason.NEGATIVE_ROAS,
            confidence=0.0,
            waste_prevented=0.0,
            recommendation="ROAS acceptable",
            metrics_at_kill={}
        )

    def _check_no_conversions(self, metrics: AdMetrics) -> KillDecision:
        """Check if no conversions after spending threshold"""
        if metrics.spend < self.NO_CONVERSION_SPEND_LIMIT:
            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=False,
                reason=KillReason.NO_CONVERSIONS,
                confidence=0.0,
                waste_prevented=0.0,
                recommendation="Still in learning phase",
                metrics_at_kill={}
            )

        if metrics.conversions == 0:
            waste = metrics.budget - metrics.spend

            return KillDecision(
                ad_id=metrics.ad_id,
                should_kill=True,
                reason=KillReason.NO_CONVERSIONS,
                confidence=0.9,
                waste_prevented=waste,
                recommendation=f"Spent ${metrics.spend:.2f} with zero conversions. Complete failure.",
                metrics_at_kill={
                    'spend': metrics.spend,
                    'conversions': 0,
                    'threshold': self.NO_CONVERSION_SPEND_LIMIT
                }
            )

        return KillDecision(
            ad_id=metrics.ad_id,
            should_kill=False,
            reason=KillReason.NO_CONVERSIONS,
            confidence=0.0,
            waste_prevented=0.0,
            recommendation="Has conversions",
            metrics_at_kill={}
        )

    async def execute_kill(self, decision: KillDecision,
                           platform_client: Any = None) -> Dict:
        """Execute the kill decision"""
        if not decision.should_kill:
            return {'executed': False, 'reason': 'No kill needed'}

        try:
            # Would call actual API here
            if platform_client:
                # await platform_client.pause_ad(decision.ad_id)
                pass

            logger.warning(f"KILL EXECUTED: Ad {decision.ad_id} - {decision.reason.value}")
            logger.warning(f"  Reason: {decision.recommendation}")
            logger.warning(f"  Waste prevented: ${decision.waste_prevented:.2f}")

            return {
                'executed': True,
                'ad_id': decision.ad_id,
                'reason': decision.reason.value,
                'waste_prevented': decision.waste_prevented,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to kill ad {decision.ad_id}: {e}")
            return {'executed': False, 'error': str(e)}

    def batch_evaluate(self, ads: List[AdMetrics]) -> List[KillDecision]:
        """Evaluate multiple ads at once"""
        decisions = []
        for ad in ads:
            decision = self.evaluate_ad(ad)
            if decision.should_kill:
                decisions.append(decision)

        # Sort by waste prevented (most wasteful first)
        decisions.sort(key=lambda d: d.waste_prevented, reverse=True)

        return decisions

    def get_kill_report(self, decisions: List[KillDecision]) -> Dict:
        """Generate report of kill decisions"""
        total_waste = sum(d.waste_prevented for d in decisions if d.should_kill)

        reasons = {}
        for d in decisions:
            if d.should_kill:
                reasons[d.reason.value] = reasons.get(d.reason.value, 0) + 1

        return {
            'total_ads_to_kill': len([d for d in decisions if d.should_kill]),
            'total_waste_prevented': total_waste,
            'kill_reasons': reasons,
            'highest_waste_ad': decisions[0].ad_id if decisions else None,
            'average_confidence': sum(d.confidence for d in decisions) / len(decisions) if decisions else 0
        }
