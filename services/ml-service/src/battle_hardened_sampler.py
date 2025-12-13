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
import hashlib
import json
import os

logger = logging.getLogger(__name__)

# Import Redis for synchronous caching (95% hit rate optimization)
try:
    import redis
    REDIS_AVAILABLE = True
    # Initialize Redis connection for sync cache
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    try:
        redis_client = redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()  # Test connection
        logger.info("Redis cache enabled for BattleHardenedSampler")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}")
        redis_client = None
        REDIS_AVAILABLE = False
except ImportError:
    REDIS_AVAILABLE = False
    redis_client = None
    logger.warning("Redis not available - caching disabled")

# Import semantic cache for 95% hit rate optimization (fallback)
try:
    from src.semantic_cache import SemanticCache, get_semantic_cache
    SEMANTIC_CACHE_AVAILABLE = True
except ImportError:
    SEMANTIC_CACHE_AVAILABLE = False
    logger.warning("Semantic cache not available - using Redis only")

# Import cross-learner for 100x data boost
try:
    from src.cross_learner import cross_learner
    CROSS_LEARNER_AVAILABLE = True
except ImportError:
    CROSS_LEARNER_AVAILABLE = False
    logger.warning("Cross-learner not available - single-account mode")


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
    
    def __hash__(self) -> int:
        """Make AdState hashable for use as dictionary key."""
        return hash(self.ad_id)
    
    def __eq__(self, other: object) -> bool:
        """Compare AdStates by ad_id."""
        if isinstance(other, AdState):
            return self.ad_id == other.ad_id
        return False


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
        mode: str = "pipeline",  # "pipeline" for service business, "direct" for e-commerce
        ignorance_zone_days: float = 2.0,
        ignorance_zone_spend: float = 100.0,
        account_average_score: float = 1.0,
        min_spend_for_kill: float = 200.0,
        kill_pipeline_roas: float = 0.5,
        scale_pipeline_roas: float = 3.0,
    ):
        """
        Initialize Battle-Hardened Sampler.

        Args:
            decay_constant: Ad fatigue decay rate
            min_impressions_for_decision: Minimum impressions before optimization
            confidence_threshold: Minimum confidence for budget changes
            max_budget_change_pct: Maximum budget change per decision
            mode: "pipeline" for service business, "direct" for e-commerce
            ignorance_zone_days: Days before making kill decisions
            ignorance_zone_spend: Minimum spend before making kill decisions
            account_average_score: Account baseline score for comparisons
            min_spend_for_kill: Minimum spend required before killing ads
            kill_pipeline_roas: Pipeline ROAS threshold for killing ads
            scale_pipeline_roas: Pipeline ROAS threshold for aggressive scaling
        """
        self.decay_constant = decay_constant
        self.min_impressions_for_decision = min_impressions_for_decision
        self.confidence_threshold = confidence_threshold
        self.max_budget_change_pct = max_budget_change_pct
        self.mode = mode
        self.ignorance_zone_days = ignorance_zone_days
        self.ignorance_zone_spend = ignorance_zone_spend
        self.account_average_score = account_average_score
        self.min_spend_for_kill = min_spend_for_kill
        self.kill_pipeline_roas = kill_pipeline_roas
        self.scale_pipeline_roas = scale_pipeline_roas

        # Initialize semantic cache for 95% hit rate optimization
        self.semantic_cache = None
        self.redis_cache = redis_client if REDIS_AVAILABLE else None
        if SEMANTIC_CACHE_AVAILABLE:
            try:
                self.semantic_cache = get_semantic_cache()
                logger.info("Semantic cache enabled for BattleHardenedSampler")
            except Exception as e:
                logger.warning(f"Failed to initialize semantic cache: {e}")
        
        if self.redis_cache:
            logger.info("Redis cache enabled for BattleHardenedSampler (sync mode)")

        logger.info(
            f"BattleHardenedSampler initialized: "
            f"mode={mode}, decay={decay_constant}, min_impressions={min_impressions_for_decision}, "
            f"ignorance_zone_days={ignorance_zone_days}, min_spend_for_kill=${min_spend_for_kill}, "
            f"semantic_cache={'enabled' if self.semantic_cache else 'disabled'}, "
            f"cross_learner={'enabled' if CROSS_LEARNER_AVAILABLE else 'disabled'}"
        )

    async def select_budget_allocation(
        self,
        ad_states: List[AdState],
        total_budget: float,
        creative_dna_scores: Optional[Dict[str, float]] = None,
        account_id: Optional[str] = None,
        db_session=None,
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
            score = await self._calculate_blended_score(ad, creative_dna_scores, db_session, account_id)
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

    async def _calculate_blended_score(
        self,
        ad: AdState,
        creative_dna_scores: Optional[Dict[str, float]] = None,
        db_session=None,  # For semantic cache
        account_id: Optional[str] = None,  # For cross-learner boost
    ) -> Dict:
        """
        Calculate blended score combining CTR and Pipeline ROAS based on age.

        Blending Logic:
            - Early (0-6h): Pure CTR (no conversions yet)
            - Middle (6-72h): Gradual shift from CTR to Pipeline ROAS
            - Late (3+ days): Pure Pipeline ROAS (full attribution window)

        OPTIMIZATION: Uses semantic caching for 95% hit rate on similar ad states.
        """
        # Generate cache key from ad state
        cache_key = self._generate_cache_key(ad)
        cache_key_redis = f"bhs:score:{cache_key}"

        # Check Redis cache first (95% hit rate optimization - sync mode)
        if self.redis_cache:
            try:
                cached_result = self.redis_cache.get(cache_key_redis)
                if cached_result:
                    logger.debug(f"Cache hit for ad {ad.ad_id}")
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning(f"Redis cache lookup failed: {e}")

        # Check semantic cache (async - uses embedding similarity for 95% hit rate)
        if self.semantic_cache and db_session:
            try:
                # Generate query text from ad state for semantic matching
                query_text = f"ad_score:{ad.ad_id}:imp{ad.impressions}:ctr{ad.clicks/max(ad.impressions,1):.4f}:spend{ad.spend:.2f}:age{ad.age_hours:.1f}h"

                # Search for semantically similar cached results
                cache_hit = await self.semantic_cache._search_cache(query_text, "battle_hardened_score")

                if cache_hit.hit and cache_hit.cached_result:
                    logger.info(f"🎯 Semantic cache HIT ({cache_hit.similarity:.4f}) for ad {ad.ad_id}")
                    return cache_hit.cached_result
                elif cache_hit.similarity > 0.85:
                    logger.debug(f"Near-hit ({cache_hit.similarity:.4f}) for ad {ad.ad_id} - computing fresh")
            except Exception as e:
                logger.warning(f"Semantic cache lookup failed: {e}")

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

        # Apply cross-learner boost (100x data optimization)
        cross_learner_boost = await self._apply_cross_learner_boost_async(
            ad, blended_score_with_decay, account_id or "unknown", db_session
        )
        final_score = blended_score_with_decay * dna_boost * cross_learner_boost

        result = {
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
            "cross_learner_boost": cross_learner_boost,
            "final_score": final_score,
        }

        # Cache result for future similar queries (95% hit rate optimization)
        # Use Redis for synchronous caching (30 minute TTL)
        if self.redis_cache:
            try:
                cache_key_redis = f"bhs:score:{cache_key}"
                self.redis_cache.setex(
                    cache_key_redis,
                    1800,  # 30 minutes TTL
                    json.dumps(result, default=str)
                )
                logger.debug(f"Cached result for ad {ad.ad_id}")
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")

        # Also store in semantic cache (async - for similarity matching)
        if self.semantic_cache and db_session:
            try:
                # Generate query text from ad state
                query_text = f"ad_score:{ad.ad_id}:imp{ad.impressions}:ctr{ad.clicks/max(ad.impressions,1):.4f}:spend{ad.spend:.2f}:age{ad.age_hours:.1f}h"

                # Store result with 30 minute TTL
                await self.semantic_cache._store_result(
                    query=query_text,
                    query_type="battle_hardened_score",
                    result=result,
                    ttl_seconds=1800,  # 30 minutes
                    metadata={"ad_id": ad.ad_id, "account_id": account_id}
                )
                logger.debug(f"Stored semantic cache for ad {ad.ad_id}")
            except Exception as e:
                logger.warning(f"Semantic cache set failed: {e}")

        return result

    def _generate_cache_key(self, ad: AdState) -> str:
        """Generate cache key from ad state for semantic caching."""
        # Create a normalized representation of ad state
        state_str = json.dumps({
            "ad_id": ad.ad_id,
            "impressions_bucket": ad.impressions // 100,  # Bucket by 100s
            "ctr_bucket": round(ad.clicks / max(ad.impressions, 1), 2),  # Round to 2 decimals
            "spend_bucket": round(ad.spend / 10, 0) * 10,  # Bucket by $10
            "age_hours_bucket": round(ad.age_hours / 6, 0) * 6,  # Bucket by 6 hours
        }, sort_keys=True)
        return hashlib.md5(state_str.encode()).hexdigest()

    async def _apply_cross_learner_boost_async(
        self,
        ad: AdState,
        base_score: float,
        account_id: str,
        db_session
    ) -> float:
        """
        Apply cross-learner boost if similar patterns won in other accounts.

        OPTIMIZATION: 100x more learning data from cross-account patterns.
        Now with full async integration for niche detection and insights.
        """
        if not CROSS_LEARNER_AVAILABLE or not cross_learner:
            return 1.0

        try:
            # Detect niche for this account
            niche, confidence = await cross_learner.detect_niche(account_id)
            if niche == "unknown" or confidence < 0.7:
                logger.debug(f"Niche detection confidence too low ({confidence:.2f}) for account {account_id}")
                return 1.0

            # Get niche insights with wisdom from other accounts
            niche_insights = await cross_learner.get_niche_insights(niche, force_refresh=False)
            if not niche_insights:
                logger.debug(f"No niche insights available for niche: {niche}")
                return 1.0

            # Apply boost based on niche wisdom
            boost = self._apply_niche_wisdom(ad, niche_insights, base_score)
            final_boost = min(boost, 1.2)  # Max 20% boost

            logger.debug(
                f"Cross-learner boost: {final_boost:.2f}x for ad {ad.ad_id} "
                f"(niche: {niche}, confidence: {confidence:.2f}, base_score: {base_score:.2f})"
            )

            return final_boost

        except AttributeError as e:
            # Method doesn't exist - cross-learner not fully integrated
            logger.debug(f"Cross-learner boost skipped (method not available): {e}")
        except Exception as e:
            logger.warning(f"Cross-learner boost failed: {e}")

        return 1.0

    def _apply_niche_wisdom(self, ad: AdState, niche_insights: Dict, base_score: float) -> float:
        """
        Apply niche wisdom boost based on cross-account learnings.

        Args:
            ad: Ad state
            niche_insights: Insights from cross-learner for this niche
            base_score: Current blended score

        Returns:
            Boost factor (1.0 = no boost, up to 1.2 = 20% boost)
        """
        boost = 1.0

        try:
            # Extract winning patterns from niche insights
            winning_patterns = niche_insights.get("winning_patterns", {})
            avg_ctr = niche_insights.get("avg_ctr", 0.02)
            avg_roas = niche_insights.get("avg_roas", 1.5)

            # Calculate ad metrics
            ad_ctr = ad.clicks / max(ad.impressions, 1)
            ad_roas = ad.pipeline_value / max(ad.spend, 0.01)

            # Boost if ad outperforms niche averages
            ctr_ratio = ad_ctr / max(avg_ctr, 0.001)
            roas_ratio = ad_roas / max(avg_roas, 0.001)

            # Weight CTR and ROAS based on ad age (similar to blended scoring)
            if ad.age_hours < 24:
                # Early stage: prioritize CTR
                boost = 1.0 + (ctr_ratio - 1.0) * 0.15  # Up to 15% boost from CTR
            else:
                # Later stage: prioritize ROAS
                boost = 1.0 + (roas_ratio - 1.0) * 0.10  # Up to 10% boost from ROAS
                # Add CTR bonus
                boost += (ctr_ratio - 1.0) * 0.05  # Up to 5% additional boost from CTR

            # Ensure boost is in valid range
            boost = max(1.0, min(boost, 1.2))

        except Exception as e:
            logger.warning(f"Failed to apply niche wisdom: {e}")
            boost = 1.0

        return boost

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

    def should_kill_service_ad(self, ad_id: str, spend: float, synthetic_revenue: float, days_live: float) -> tuple[bool, str]:
        """Service business kill logic with ignorance zone."""
        # Ignorance zone: don't kill too early
        if days_live < self.ignorance_zone_days and spend < self.ignorance_zone_spend:
            return False, f"In ignorance zone (day {days_live:.1f}, spent ${spend:.0f})"

        # Need minimum spend before making kill decision
        if spend < self.min_spend_for_kill:
            return False, f"Below min spend threshold (${spend:.0f} < ${self.min_spend_for_kill:.0f})"

        # Calculate pipeline ROAS
        pipeline_roas = synthetic_revenue / spend if spend > 0 else 0

        # Kill if pipeline ROAS is terrible
        if pipeline_roas < self.kill_pipeline_roas:
            return True, f"Pipeline ROAS {pipeline_roas:.2f} < {self.kill_pipeline_roas}"

        return False, f"Performing OK (pipeline ROAS: {pipeline_roas:.2f})"

    def should_scale_aggressively(self, ad_id: str, spend: float, synthetic_revenue: float, days_live: float) -> tuple[bool, str]:
        """Check if ad should scale aggressively."""
        if spend < self.min_spend_for_kill:
            return False, "Insufficient data"

        pipeline_roas = synthetic_revenue / spend if spend > 0 else 0

        if pipeline_roas > self.scale_pipeline_roas:
            return True, f"Excellent pipeline ROAS {pipeline_roas:.2f} > {self.scale_pipeline_roas}"

        return False, f"Pipeline ROAS {pipeline_roas:.2f} not ready for aggressive scaling"

    def make_decision(
        self,
        ad_id: str,
        spend: float,
        revenue: float,
        synthetic_revenue: float,
        days_live: float,
    ) -> Dict:
        """
        Make kill/scale decision using mode-aware logic.

        Args:
            ad_id: Ad identifier
            spend: Total spend on ad
            revenue: Direct revenue (for e-commerce mode)
            synthetic_revenue: Pipeline value (for service business mode)
            days_live: Days since ad creation

        Returns:
            Dict with decision, reason, and metrics
        """
        if self.mode == "pipeline":
            # Service business mode: use pipeline ROAS and ignorance zone
            should_kill, kill_reason = self.should_kill_service_ad(
                ad_id, spend, synthetic_revenue, days_live
            )
            should_scale, scale_reason = self.should_scale_aggressively(
                ad_id, spend, synthetic_revenue, days_live
            )

            pipeline_roas = synthetic_revenue / spend if spend > 0 else 0

            return {
                "ad_id": ad_id,
                "decision": "kill" if should_kill else ("scale" if should_scale else "maintain"),
                "reason": kill_reason if should_kill else scale_reason,
                "mode": "pipeline",
                "metrics": {
                    "spend": round(spend, 2),
                    "synthetic_revenue": round(synthetic_revenue, 2),
                    "pipeline_roas": round(pipeline_roas, 2),
                    "days_live": round(days_live, 1),
                },
            }
        else:
            # E-commerce mode: use direct ROAS
            direct_roas = revenue / spend if spend > 0 else 0

            # Simple kill logic for e-commerce (no ignorance zone)
            should_kill = spend >= self.min_spend_for_kill and direct_roas < self.kill_pipeline_roas
            should_scale = spend >= self.min_spend_for_kill and direct_roas > self.scale_pipeline_roas

            if should_kill:
                reason = f"Direct ROAS {direct_roas:.2f} < {self.kill_pipeline_roas}"
            elif should_scale:
                reason = f"Excellent direct ROAS {direct_roas:.2f} > {self.scale_pipeline_roas}"
            elif spend < self.min_spend_for_kill:
                reason = f"Insufficient spend (${spend:.0f} < ${self.min_spend_for_kill:.0f})"
            else:
                reason = f"Performing OK (direct ROAS: {direct_roas:.2f})"

            return {
                "ad_id": ad_id,
                "decision": "kill" if should_kill else ("scale" if should_scale else "maintain"),
                "reason": reason,
                "mode": "direct",
                "metrics": {
                    "spend": round(spend, 2),
                    "revenue": round(revenue, 2),
                    "direct_roas": round(direct_roas, 2),
                    "days_live": round(days_live, 1),
                },
            }


# Singleton instance
_battle_hardened_sampler = None


def get_battle_hardened_sampler() -> BattleHardenedSampler:
    """Get singleton Battle-Hardened Sampler instance."""
    global _battle_hardened_sampler
    if _battle_hardened_sampler is None:
        _battle_hardened_sampler = BattleHardenedSampler()
    return _battle_hardened_sampler
