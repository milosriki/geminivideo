"""
Battle-Hardened Sampler - Attribution-Lag-Aware Optimization
============================================================

Purpose:
    Handles service business optimization (5-7 day sales cycles) with blended scoring
    that shifts from CTR (early) to Pipeline ROAS (later) based on impression age.

Problem Solved:
    Standard Thompson Sampling optimizes for immediate ROAS, but service businesses
    need to trust CTR early (no conversions yet) and gradually shift to Pipeline ROAS
    as attribution data becomes available.

Blended Scoring Algorithm:
    - Hours 0-6:   Trust CTR 100%, Pipeline ROAS 0% (too early for conversions)
    - Hours 6-24:  Trust CTR 70%, Pipeline ROAS 30% (leads starting)
    - Hours 24-72: Trust CTR 30%, Pipeline ROAS 70% (appointments booking)
    - Days 3+:     Trust CTR 0%, Pipeline ROAS 100% (full attribution)

Created: 2025-12-07
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class AdState:
    """Ad state with performance metrics"""
    ad_id: str
    impressions: int
    clicks: int
    spend: float
    pipeline_value: float  # Synthetic revenue from pipeline stages
    cash_revenue: float    # Actual closed deals (if any)
    age_hours: float       # Hours since ad creation
    last_updated: datetime


@dataclass
class BudgetRecommendation:
    """Budget allocation recommendation"""
    ad_id: str
    current_budget: float
    recommended_budget: float
    change_percentage: float
    confidence: float
    reason: str
    metrics: Dict


class BattleHardenedSampler:
    """
    Attribution-lag-aware Thompson Sampling variant for service businesses.

    Combines:
    1. Thompson Sampling (Bayesian bandit)
    2. Blended scoring (CTR early → Pipeline ROAS later)
    3. Decay function for ad fatigue
    4. Contextual boost for creative DNA similarity
    """

    def __init__(
        self,
        decay_constant: float = 0.0001,
        min_impressions_for_decision: int = 100,
        confidence_threshold: float = 0.70,
        max_budget_change_pct: float = 0.50,  # Max 50% increase per decision
    ):
        """
        Initialize Battle-Hardened Sampler.

        Args:
            decay_constant: Ad fatigue decay rate
            min_impressions_for_decision: Minimum impressions before optimization
            confidence_threshold: Minimum confidence for budget changes
            max_budget_change_pct: Maximum budget change per decision
        """
        self.decay_constant = decay_constant
        self.min_impressions_for_decision = min_impressions_for_decision
        self.confidence_threshold = confidence_threshold
        self.max_budget_change_pct = max_budget_change_pct

        logger.info(
            f"BattleHardenedSampler initialized: "
            f"decay={decay_constant}, min_impressions={min_impressions_for_decision}"
        )

    def select_budget_allocation(
        self,
        ad_states: List[AdState],
        total_budget: float,
        creative_dna_scores: Optional[Dict[str, float]] = None,
    ) -> List[BudgetRecommendation]:
        """
        Allocate budget across ads using blended scoring.

        Args:
            ad_states: List of ad performance states
            total_budget: Total budget to allocate
            creative_dna_scores: Optional DNA similarity scores (0-1)

        Returns:
            List of budget recommendations per ad
        """
        logger.info(f"Selecting budget allocation for {len(ad_states)} ads, total budget: ${total_budget}")

        if not ad_states:
            logger.warning("No ad states provided")
            return []

        # Step 1: Calculate blended scores for each ad
        ad_scores = []
        for ad in ad_states:
            score = self._calculate_blended_score(ad, creative_dna_scores)
            ad_scores.append((ad, score))

        # Step 2: Sample from Thompson distributions
        thompson_samples = []
        for ad, blended_score in ad_scores:
            sample = self._thompson_sample(ad, blended_score)
            thompson_samples.append((ad, sample))

        # Step 3: Softmax allocation (probabilistic)
        allocations = self._softmax_allocation(thompson_samples, total_budget)

        # Step 4: Generate recommendations with confidence scores
        recommendations = []
        for ad, new_budget in allocations:
            current_budget = ad.spend / max(ad.age_hours / 24, 1)  # Daily budget estimate

            rec = self._generate_recommendation(
                ad=ad,
                current_budget=current_budget,
                recommended_budget=new_budget,
                blended_score=dict(ad_scores)[ad],
            )
            recommendations.append(rec)

        logger.info(f"Generated {len(recommendations)} budget recommendations")
        return recommendations

    def _calculate_blended_score(
        self,
        ad: AdState,
        creative_dna_scores: Optional[Dict[str, float]] = None,
    ) -> Dict:
        """
        Calculate blended score combining CTR and Pipeline ROAS based on age.

        Blending Logic:
            - Early (0-6h): Pure CTR (no conversions yet)
            - Middle (6-72h): Gradual shift from CTR to Pipeline ROAS
            - Late (3+ days): Pure Pipeline ROAS (full attribution window)
        """
        # Calculate base metrics
        ctr = ad.clicks / max(ad.impressions, 1)
        pipeline_roas = ad.pipeline_value / max(ad.spend, 0.01)
        cash_roas = ad.cash_revenue / max(ad.spend, 0.01)

        # Calculate blended weight (0 = pure ROAS, 1 = pure CTR)
        ctr_weight = self._calculate_blended_weight(ad)
        roas_weight = 1.0 - ctr_weight

        # Blended score = weighted combination
        # Normalize CTR to 0-1 range (assume 5% CTR = 1.0)
        normalized_ctr = min(ctr / 0.05, 1.0)

        # Normalize ROAS to 0-1 range (assume 3.0 ROAS = 1.0)
        normalized_roas = min(pipeline_roas / 3.0, 1.0)

        blended_score = (ctr_weight * normalized_ctr) + (roas_weight * normalized_roas)

        # Apply ad fatigue decay
        decay_factor = np.exp(-self.decay_constant * ad.impressions)
        blended_score_with_decay = blended_score * decay_factor

        # Apply creative DNA boost (if available)
        dna_boost = 1.0
        if creative_dna_scores and ad.ad_id in creative_dna_scores:
            dna_score = creative_dna_scores[ad.ad_id]
            dna_boost = 1.0 + (dna_score * 0.2)  # Up to 20% boost for perfect DNA match

        final_score = blended_score_with_decay * dna_boost

        return {
            "ctr": ctr,
            "pipeline_roas": pipeline_roas,
            "cash_roas": cash_roas,
            "ctr_weight": ctr_weight,
            "roas_weight": roas_weight,
            "normalized_ctr": normalized_ctr,
            "normalized_roas": normalized_roas,
            "blended_score": blended_score,
            "decay_factor": decay_factor,
            "dna_boost": dna_boost,
            "final_score": final_score,
        }

    def _calculate_blended_weight(self, ad: AdState) -> float:
        """
        Calculate blended weight (CTR vs ROAS) based on ad age.

        Returns:
            Float 0-1 where 1.0 = pure CTR, 0.0 = pure ROAS
        """
        age_hours = ad.age_hours

        if age_hours < 6:
            # Hours 0-6: Pure CTR (too early for conversions)
            return 1.0

        elif age_hours < 24:
            # Hours 6-24: Linear shift from CTR 100% to CTR 70%
            # At hour 6: weight = 1.0
            # At hour 24: weight = 0.7
            progress = (age_hours - 6) / 18  # 0 to 1
            return 1.0 - (0.3 * progress)

        elif age_hours < 72:
            # Hours 24-72: Linear shift from CTR 70% to CTR 30%
            # At hour 24: weight = 0.7
            # At hour 72: weight = 0.3
            progress = (age_hours - 24) / 48  # 0 to 1
            return 0.7 - (0.4 * progress)

        else:
            # Days 3+: Exponential decay to pure ROAS
            # At hour 72: weight = 0.3
            # Eventually: weight → 0.1 (never fully 0 to maintain some CTR signal)
            days_old = (age_hours - 72) / 24
            return max(0.1, 0.3 * np.exp(-0.1 * days_old))

    def _thompson_sample(self, ad: AdState, blended_score: Dict) -> float:
        """
        Sample from Thompson distribution based on blended score.

        Uses Beta distribution for Bayesian sampling:
        - Alpha (successes) = impressions * blended_score
        - Beta (failures) = impressions * (1 - blended_score)
        """
        final_score = blended_score["final_score"]

        # Ensure minimum impressions for statistical significance
        effective_impressions = max(ad.impressions, self.min_impressions_for_decision)

        # Beta distribution parameters
        alpha = max(1, effective_impressions * final_score + 1)
        beta = max(1, effective_impressions * (1 - final_score) + 1)

        # Sample from Beta(alpha, beta)
        sample = np.random.beta(alpha, beta)

        return sample

    def _softmax_allocation(
        self,
        thompson_samples: List[Tuple[AdState, float]],
        total_budget: float,
    ) -> List[Tuple[AdState, float]]:
        """
        Allocate budget using softmax (probabilistic allocation).

        Ensures:
        1. Budget sums to total_budget
        2. No ad gets 0 budget (minimum allocation)
        3. High performers get more, but not all
        """
        # Extract samples
        samples = np.array([sample for _, sample in thompson_samples])

        # Softmax with temperature = 1
        exp_samples = np.exp(samples)
        probabilities = exp_samples / exp_samples.sum()

        # Allocate budget proportionally
        allocations = []
        remaining_budget = total_budget

        for i, (ad, _) in enumerate(thompson_samples):
            if i == len(thompson_samples) - 1:
                # Last ad gets remaining budget (avoid rounding errors)
                budget = remaining_budget
            else:
                budget = total_budget * probabilities[i]
                remaining_budget -= budget

            allocations.append((ad, max(budget, 1.0)))  # Minimum $1/day

        return allocations

    def _generate_recommendation(
        self,
        ad: AdState,
        current_budget: float,
        recommended_budget: float,
        blended_score: Dict,
    ) -> BudgetRecommendation:
        """Generate budget recommendation with confidence and reason."""

        # Calculate change percentage
        if current_budget > 0:
            change_pct = (recommended_budget - current_budget) / current_budget
        else:
            change_pct = 1.0

        # Cap change to max_budget_change_pct
        if abs(change_pct) > self.max_budget_change_pct:
            capped_change = self.max_budget_change_pct if change_pct > 0 else -self.max_budget_change_pct
            recommended_budget = current_budget * (1 + capped_change)
            change_pct = capped_change

        # Calculate confidence based on:
        # 1. Impressions (more data = higher confidence)
        # 2. Blended score stability
        # 3. Age (older ads = higher confidence)

        impression_confidence = min(ad.impressions / 1000, 1.0)  # 1000 impr = full confidence
        age_confidence = min(ad.age_hours / 72, 1.0)  # 3 days = full confidence
        score_confidence = blended_score["final_score"]

        confidence = np.mean([impression_confidence, age_confidence, score_confidence])

        # Generate reason
        reason = self._generate_reason(ad, blended_score, change_pct)

        return BudgetRecommendation(
            ad_id=ad.ad_id,
            current_budget=round(current_budget, 2),
            recommended_budget=round(recommended_budget, 2),
            change_percentage=round(change_pct * 100, 2),
            confidence=round(confidence, 4),
            reason=reason,
            metrics={
                "impressions": ad.impressions,
                "clicks": ad.clicks,
                "ctr": round(blended_score["ctr"] * 100, 2),
                "pipeline_roas": round(blended_score["pipeline_roas"], 2),
                "ctr_weight": round(blended_score["ctr_weight"], 2),
                "roas_weight": round(blended_score["roas_weight"], 2),
                "blended_score": round(blended_score["blended_score"], 4),
                "decay_factor": round(blended_score["decay_factor"], 4),
                "age_hours": round(ad.age_hours, 1),
            },
        )

    def _generate_reason(self, ad: AdState, blended_score: Dict, change_pct: float) -> str:
        """Generate human-readable reason for budget change."""

        ctr = blended_score["ctr"] * 100
        pipeline_roas = blended_score["pipeline_roas"]
        ctr_weight = blended_score["ctr_weight"]
        age_hours = ad.age_hours

        if change_pct > 0.2:
            # Significant increase
            if ctr_weight > 0.7:
                return f"Strong CTR ({ctr:.1f}%) in early phase (age: {age_hours:.1f}h). Scaling up."
            else:
                return f"Excellent Pipeline ROAS ({pipeline_roas:.2f}x) with mature data. Scaling up."

        elif change_pct > 0:
            # Moderate increase
            return f"Good performance (CTR: {ctr:.1f}%, ROAS: {pipeline_roas:.2f}x). Gradual scale."

        elif change_pct > -0.2:
            # Moderate decrease
            decay = blended_score["decay_factor"]
            if decay < 0.5:
                return f"Ad fatigue detected (decay: {decay:.2f}). Reducing budget."
            else:
                return f"Below-average performance. Reallocating budget to winners."

        else:
            # Significant decrease
            return f"Poor performance (CTR: {ctr:.1f}%, ROAS: {pipeline_roas:.2f}x). Cutting budget."

    def register_feedback(
        self,
        ad_id: str,
        actual_pipeline_value: float,
        actual_spend: float,
        timestamp: Optional[datetime] = None,
    ) -> Dict:
        """
        Register actual performance feedback for model improvement.

        This is called by the Actuals Fetcher to provide ground truth.
        """
        timestamp = timestamp or datetime.now(timezone.utc)

        logger.info(
            f"Feedback registered for {ad_id}: "
            f"pipeline_value=${actual_pipeline_value}, spend=${actual_spend}"
        )

        # Calculate actual ROAS
        actual_roas = actual_pipeline_value / max(actual_spend, 0.01)

        # TODO: Store in database for model retraining
        # This would update our priors for Thompson Sampling

        return {
            "ad_id": ad_id,
            "actual_pipeline_value": actual_pipeline_value,
            "actual_spend": actual_spend,
            "actual_roas": actual_roas,
            "timestamp": timestamp.isoformat(),
        }


# Singleton instance
_battle_hardened_sampler = None


def get_battle_hardened_sampler() -> BattleHardenedSampler:
    """Get singleton Battle-Hardened Sampler instance."""
    global _battle_hardened_sampler
    if _battle_hardened_sampler is None:
        _battle_hardened_sampler = BattleHardenedSampler()
    return _battle_hardened_sampler
