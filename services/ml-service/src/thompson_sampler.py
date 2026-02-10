"""
Thompson Sampling A/B Testing with Vowpal Wabbit
Agent 7 - Multi-armed bandit optimization for ad variants
"""
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime
import logging
import json
import os
import redis

try:
    from vowpalwabbit import pyvw
    VW_AVAILABLE = True
except ImportError:
    VW_AVAILABLE = False
    logging.warning("Vowpal Wabbit not available, using fallback implementation")

logger = logging.getLogger(__name__)


class ThompsonSamplingOptimizer:
    """
    Thompson Sampling for A/B testing and budget optimization
    Uses Redis for persistence and Vowpal Wabbit/Beta distribution for sampling
    """

    def __init__(self, epsilon: float = 0.1, random_seed: int = 1):
        """
        Initialize Thompson Sampling Optimizer

        Args:
            epsilon: Exploration parameter (0-1), higher = more exploration
            random_seed: Random seed for reproducibility
        """
        self.epsilon = epsilon
        self.random_seed = random_seed
        
        # Initialize Redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.redis = redis.from_url(redis_url, decode_responses=True)
            logger.info(f"✅ Thompson Sampling connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.redis = None

        # Initialize Vowpal Wabbit if available
        if VW_AVAILABLE:
            self.vw = pyvw.Workspace(
                f"--cb_explore_adf --epsilon {epsilon} --random_seed {random_seed}"
            )
            logger.info("Vowpal Wabbit Thompson Sampling initialized")
        else:
            self.vw = None
            logger.warning("Using fallback Thompson Sampling (Beta distribution)")

    def _get_variant_key(self, variant_id: str) -> str:
        return f"ab_variant:{variant_id}"

    def _get_variant(self, variant_id: str) -> Optional[Dict[str, Any]]:
        """Fetch variant data from Redis"""
        if not self.redis:
            logger.warning("Redis unavailable, returning None for variant")
            return None
            
        data = self.redis.get(self._get_variant_key(variant_id))
        if data:
            return json.loads(data)
        return None

    def _save_variant(self, variant_id: str, data: Dict[str, Any]):
        """Save variant data to Redis"""
        if not self.redis:
            logger.warning("Redis unavailable, cannot save variant")
            return
            
        self.redis.set(self._get_variant_key(variant_id), json.dumps(data))

    def _get_all_variant_ids(self) -> List[str]:
        """Get all registered variant IDs"""
        if not self.redis:
            return []
        keys = self.redis.keys("ab_variant:*")
        return [k.split(":")[-1] for k in keys]

    def register_variant(
        self,
        variant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a new variant for testing
        """
        existing = self._get_variant(variant_id)
        if not existing:
            variant_data = {
                'id': variant_id,
                'impressions': 0,
                'clicks': 0,
                'conversions': 0,
                'spend': 0.0,
                'ctr': 0.0,
                'cvr': 0.0,
                'roas': 0.0,
                'alpha': 1.0,  # Prior for success (Beta distribution)
                'beta': 1.0,   # Prior for failure (Beta distribution)
                'created_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            self._save_variant(variant_id, variant_data)
            logger.info(f"Registered variant: {variant_id}")

    def select_variant(
        self,
        context: Optional[Dict[str, Any]] = None,
        available_variants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Select best variant using Thompson Sampling
        """
        # Use all variants if not specified
        if available_variants is None:
            available_variants = self._get_all_variant_ids()

        if not available_variants:
            raise ValueError("No available variants to select from")

        # Load variant data
        variants_data = {}
        for vid in available_variants:
            v_data = self._get_variant(vid)
            if v_data:
                variants_data[vid] = v_data

        if not variants_data:
             raise ValueError("No valid variant data found")

        if VW_AVAILABLE and self.vw:
            selected = self._select_with_vw(variants_data, context)
        else:
            selected = self._select_with_beta(variants_data)

        # Update impressions (soft increment, actual increment happens on update)
        # We don't save this soft increment to Redis to avoid write contention, 
        # relying on the explicit update() call later.
        
        return selected

    def _select_with_vw(
        self,
        available_variants: Dict[str, Dict],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select variant using Vowpal Wabbit contextual bandit"""
        # ... (VW logic same as before, but using passed available_variants) ...
        # For now, fallback to Beta as in original code
        return self._select_with_beta(available_variants)

    def _select_with_beta(self, available_variants: Dict[str, Dict], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Select variant using Beta distribution Thompson Sampling with contextual boost"""
        samples = {}

        for variant_id, variant_data in available_variants.items():
            alpha = variant_data.get('alpha', 1.0)
            beta_param = variant_data.get('beta', 1.0)

            # Apply context-based boost if context provided
            if context:
                context_boost = self._calculate_context_boost(variant_id, variant_data, context)
                alpha = alpha * (1 + context_boost)

            # Sample from Beta distribution
            sample = np.random.beta(alpha, beta_param)
            samples[variant_id] = sample

        # Select variant with highest sample
        selected_id = max(samples.items(), key=lambda x: x[1])[0]
        selected_score = samples[selected_id]

        return {
            'variant_id': selected_id,
            'selection_score': float(selected_score),
            'all_scores': {k: float(v) for k, v in samples.items()},
            'method': 'thompson_sampling_contextual_beta',
            'timestamp': datetime.utcnow().isoformat()
        }

    def _calculate_context_boost(self, variant_id: str, variant_data: Dict, context: Dict) -> float:
        """Calculate context-based boost for variant (simpler alternative to VW)"""
        boost = 0.0

        # Time-based boost (ads perform differently at different times)
        hour = context.get('hour', 12)
        if 9 <= hour <= 17:  # Business hours
            metadata = variant_data.get('metadata', {})
            if metadata.get('target_audience') == 'business':
                boost += 0.1

        # Device-based boost
        device = context.get('device', 'mobile')
        metadata = variant_data.get('metadata', {})
        if device == 'mobile' and metadata.get('optimized_for') == 'mobile':
            boost += 0.15

        # Audience age-based boost
        age_group = context.get('age_group', 3)  # 1=18-24, 2=25-34, 3=35-44, etc.
        target_age = metadata.get('target_age_group')
        if target_age and abs(age_group - target_age) <= 1:
            boost += 0.1

        # Performance recency boost (favor recently updated variants)
        last_updated = variant_data.get('last_updated')
        if last_updated:
            try:
                from datetime import datetime
                last_update_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                days_old = (datetime.utcnow() - last_update_dt).days
                if days_old < 7:  # Recent data
                    boost += 0.05
            except (ValueError, TypeError):
                pass

        return min(boost, 0.5)  # Cap at 50% boost

    def update(
        self,
        variant_id: str,
        reward: float,
        cost: float,  # REQUIRED - No default to prevent zero spend!
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, float]] = None,
        conversion_value: float = 0.0  # Actual revenue from conversion
    ):
        """
        Update variant with observed performance

        Args:
            variant_id: Variant identifier
            reward: 1.0 for conversion, 0.0 for no conversion
            cost: ACTUAL ad spend (REQUIRED - prevents ROAS calculation errors)
            context: Context when variant was shown
            metrics: Additional metrics (impressions, clicks, etc.)
            conversion_value: Actual revenue from conversion
        """
        variant = self._get_variant(variant_id)
        if not variant:
            raise ValueError(f"Unknown variant: {variant_id}")

        # Update Beta distribution parameters
        if reward > 0:
            variant['alpha'] += reward
            variant['conversions'] = variant.get('conversions', 0) + 1
            # Track revenue
            if 'revenue' not in variant:
                variant['revenue'] = 0.0
            variant['revenue'] += conversion_value
        else:
            variant['beta'] += 1

        # Update spend (always accumulate, even if no conversion)
        variant['spend'] += cost
        variant['impressions'] = variant.get('impressions', 0) + 1

        # Update metrics if provided
        if metrics:
            variant['impressions'] = metrics.get('impressions', variant['impressions'])
            variant['clicks'] = metrics.get('clicks', variant['clicks'])
            variant['conversions'] = metrics.get('conversions', variant['conversions'])

            # If metrics has revenue, use it (overrides conversion_value)
            if 'revenue' in metrics:
                variant['revenue'] = metrics['revenue']

        # Calculate rates
        if variant['impressions'] > 0:
            variant['ctr'] = variant['clicks'] / variant['impressions'] if variant.get('clicks', 0) > 0 else 0.0
        if variant.get('clicks', 0) > 0:
            variant['cvr'] = variant['conversions'] / variant['clicks']
        if variant['spend'] > 0:
            revenue = variant.get('revenue', 0.0)
            variant['roas'] = revenue / variant['spend']
            variant['cpa'] = variant['spend'] / max(variant['conversions'], 1)

        # Track last update time
        variant['last_updated'] = datetime.utcnow().isoformat()

        self._save_variant(variant_id, variant)
        logger.debug(f"Updated variant {variant_id}: alpha={variant['alpha']:.2f}, beta={variant['beta']:.2f}, spend=${variant['spend']:.2f}, roas={variant.get('roas', 0):.2f}")

    def get_variant_stats(self, variant_id: str) -> Dict[str, Any]:
        """Get statistics for a specific variant"""
        variant = self._get_variant(variant_id)
        if not variant:
            raise ValueError(f"Unknown variant: {variant_id}")

        # Calculate confidence intervals for CTR using Beta distribution
        alpha = variant['alpha']
        beta_param = variant['beta']

        mean_ctr = alpha / (alpha + beta_param)
        std_ctr = np.sqrt(
            (alpha * beta_param) / ((alpha + beta_param) ** 2 * (alpha + beta_param + 1))
        )

        # 95% confidence interval
        ci_lower = np.percentile(np.random.beta(alpha, beta_param, 10000), 2.5)
        ci_upper = np.percentile(np.random.beta(alpha, beta_param, 10000), 97.5)

        return {
            **variant,
            'estimated_ctr': float(mean_ctr),
            'ctr_std': float(std_ctr),
            'ctr_ci_lower': float(ci_lower),
            'ctr_ci_upper': float(ci_upper),
            'total_events': int(alpha + beta_param - 2)
        }

    def get_all_variants_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all variants"""
        ids = self._get_all_variant_ids()
        stats = []
        for vid in ids:
            try:
                stats.append(self.get_variant_stats(vid))
            except ValueError:
                continue
        return stats

    def get_best_variant(self) -> Dict[str, Any]:
        """Get the variant with highest expected performance"""
        stats = self.get_all_variants_stats()
        if not stats:
            raise ValueError("No variants registered")

        best_variant = max(
            stats,
            key=lambda x: x['alpha'] / (x['alpha'] + x['beta'])
        )

        return best_variant

    def reallocate_budget(
        self,
        total_budget: float,
        min_budget_per_variant: float = 0.0
    ) -> Dict[str, float]:
        """
        Reallocate budget across variants based on performance
        """
        variants = self.get_all_variants_stats()
        if not variants:
            raise ValueError("No variants to allocate budget to")

        # Calculate performance scores for each variant
        scores = {}
        total_score = 0.0

        for variant in variants:
            variant_id = variant['id']
            # Performance score = weighted combination of CTR, CVR, ROAS
            expected_ctr = variant['alpha'] / (variant['alpha'] + variant['beta'])
            roas = variant.get('roas', 0.0)
            cvr = variant.get('cvr', 0.0)

            # Composite score
            score = (
                0.4 * expected_ctr +
                0.3 * min(roas / 2.0, 1.0) +
                0.3 * cvr
            )

            # Add exploration bonus
            impressions = variant['impressions']
            if impressions < 100:
                exploration_bonus = 0.1 * (1 - impressions / 100)
                score += exploration_bonus

            scores[variant_id] = max(score, 0.01)
            total_score += scores[variant_id]

        # Allocate budget
        allocations = {}
        reserved_budget = min_budget_per_variant * len(variants)
        distributable_budget = total_budget - reserved_budget

        if distributable_budget < 0:
            raise ValueError(f"Total budget too small. Need at least {reserved_budget}")

        for variant_id, score in scores.items():
            proportion = score / total_score if total_score > 0 else 1.0 / len(scores)
            allocated = min_budget_per_variant + (proportion * distributable_budget)
            allocations[variant_id] = float(allocated)

        logger.info(f"Budget reallocated across {len(allocations)} variants")

        return allocations

    def apply_time_decay(self, decay_factor: float = 0.99):
        """
        Apply time decay to all variants to prevent ad fatigue
        Call this daily via cron/scheduler

        Args:
            decay_factor: Daily decay rate (0.99 = 1% decay per day)
        """
        variant_ids = self._get_all_variant_ids()
        decayed_count = 0

        for variant_id in variant_ids:
            variant = self._get_variant(variant_id)
            if not variant:
                continue

            last_updated = variant.get('last_updated')
            if not last_updated:
                continue

            try:
                last_update_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                days_old = (datetime.utcnow() - last_update_dt).days

                if days_old > 0:
                    decay = decay_factor ** days_old

                    # Decay the Beta priors (makes old data less influential)
                    variant['alpha'] = max(1.0, variant['alpha'] * decay)
                    variant['beta'] = max(1.0, variant['beta'] * decay)

                    # Track decay for debugging
                    variant['decay_applied'] = decay
                    variant['days_since_update'] = days_old

                    self._save_variant(variant_id, variant)
                    decayed_count += 1

                    logger.info(f"Applied {decay:.4f} decay to variant {variant_id} ({days_old} days old)")
            except Exception as e:
                logger.warning(f"Failed to apply decay to {variant_id}: {e}")

        logger.info(f"✅ Time decay applied to {decayed_count} variants")
        return decayed_count

    # Legacy save/load methods (no longer needed with Redis, but kept for interface compatibility)
    def save_state(self, filepath: str):
        pass

    def load_state(self, filepath: str):
        pass


# Global optimizer instance
thompson_optimizer = ThompsonSamplingOptimizer()
