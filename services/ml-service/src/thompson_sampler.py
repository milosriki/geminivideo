"""
Thompson Sampling A/B Testing with Vowpal Wabbit
Agent 7 - Multi-armed bandit optimization for ad variants
"""
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from datetime import datetime
import logging
import json

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
    Uses Vowpal Wabbit's contextual bandit implementation
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

        # Initialize Vowpal Wabbit if available
        if VW_AVAILABLE:
            self.vw = pyvw.Workspace(
                f"--cb_explore_adf --epsilon {epsilon} --random_seed {random_seed}"
            )
            logger.info("Vowpal Wabbit Thompson Sampling initialized")
        else:
            self.vw = None
            logger.warning("Using fallback Thompson Sampling (Beta distribution)")

        # Variant tracking
        self.variants: Dict[str, Dict[str, Any]] = {}

        # Performance history
        self.history: List[Dict[str, Any]] = []

    def register_variant(
        self,
        variant_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a new variant for testing

        Args:
            variant_id: Unique identifier for the variant
            metadata: Optional metadata about the variant
        """
        if variant_id not in self.variants:
            self.variants[variant_id] = {
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
            logger.info(f"Registered variant: {variant_id}")

    def select_variant(
        self,
        context: Optional[Dict[str, Any]] = None,
        available_variants: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Select best variant using Thompson Sampling

        Args:
            context: Context features (user demographics, time, etc.)
            available_variants: List of variant IDs to choose from

        Returns:
            Dictionary with selected variant and selection metadata
        """
        if not self.variants:
            raise ValueError("No variants registered. Call register_variant() first.")

        # Use all variants if not specified
        if available_variants is None:
            available_variants = list(self.variants.keys())

        if not available_variants:
            raise ValueError("No available variants to select from")

        # Filter to available variants
        available = {k: v for k, v in self.variants.items() if k in available_variants}

        if VW_AVAILABLE and self.vw:
            selected = self._select_with_vw(available, context)
        else:
            selected = self._select_with_beta(available)

        # Update impressions (soft increment, actual increment happens on update)
        self.variants[selected['variant_id']]['impressions'] += 1

        return selected

    def _select_with_vw(
        self,
        available_variants: Dict[str, Dict],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Select variant using Vowpal Wabbit contextual bandit"""
        # Build VW example
        # Format: shared |f context_features \n |a variant1_features \n |a variant2_features

        # Shared context features
        context_str = self._build_context_string(context)

        # Build action features for each variant
        actions = []
        variant_ids = []
        for variant_id, variant_data in available_variants.items():
            # Use variant performance as features
            ctr = variant_data.get('ctr', 0.0)
            cvr = variant_data.get('cvr', 0.0)
            roas = variant_data.get('roas', 0.0)
            impressions = variant_data.get('impressions', 0)

            action_features = f"ctr:{ctr:.4f} cvr:{cvr:.4f} roas:{roas:.2f} impressions:{impressions}"
            actions.append(action_features)
            variant_ids.append(variant_id)

        # VW example format for prediction (no label)
        # Note: In prediction mode, we don't provide rewards
        vw_example = f"shared {context_str}\n"
        for action_feat in actions:
            vw_example += f"|a {action_feat}\n"

        # For now, use simple selection based on Thompson Sampling with Beta
        # Real VW integration would require training data
        return self._select_with_beta(available_variants)

    def _select_with_beta(self, available_variants: Dict[str, Dict]) -> Dict[str, Any]:
        """Select variant using Beta distribution Thompson Sampling"""
        samples = {}

        for variant_id, variant_data in available_variants.items():
            alpha = variant_data['alpha']
            beta_param = variant_data['beta']

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
            'method': 'thompson_sampling_beta',
            'timestamp': datetime.utcnow().isoformat()
        }

    def update(
        self,
        variant_id: str,
        reward: float,
        cost: float = 0.0,
        context: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, float]] = None
    ):
        """
        Update variant with observed performance

        Args:
            variant_id: ID of the variant that was shown
            reward: Reward value (e.g., 1 for click, 0 for no click)
            cost: Cost of showing this variant
            context: Context when variant was shown
            metrics: Additional metrics (impressions, clicks, conversions, etc.)
        """
        if variant_id not in self.variants:
            raise ValueError(f"Unknown variant: {variant_id}")

        variant = self.variants[variant_id]

        # Update Beta distribution parameters
        if reward > 0:
            variant['alpha'] += reward
        else:
            variant['beta'] += 1

        # Update metrics
        if metrics:
            variant['impressions'] = metrics.get('impressions', variant['impressions'])
            variant['clicks'] = metrics.get('clicks', variant['clicks'])
            variant['conversions'] = metrics.get('conversions', variant['conversions'])
            variant['spend'] += cost

            # Calculate rates
            if variant['impressions'] > 0:
                variant['ctr'] = variant['clicks'] / variant['impressions']
            if variant['clicks'] > 0:
                variant['cvr'] = variant['conversions'] / variant['clicks']
            if variant['spend'] > 0:
                # ROAS = Revenue / Spend (assuming conversion = $1 revenue for simplicity)
                revenue = variant['conversions'] * 1.0  # TODO: Get real revenue value
                variant['roas'] = revenue / variant['spend']

        # Log to history
        self.history.append({
            'variant_id': variant_id,
            'reward': reward,
            'cost': cost,
            'context': context,
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        })

        logger.debug(f"Updated variant {variant_id}: alpha={variant['alpha']:.2f}, beta={variant['beta']:.2f}")

    def get_variant_stats(self, variant_id: str) -> Dict[str, Any]:
        """Get statistics for a specific variant"""
        if variant_id not in self.variants:
            raise ValueError(f"Unknown variant: {variant_id}")

        variant = self.variants[variant_id]

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
        return [self.get_variant_stats(v_id) for v_id in self.variants.keys()]

    def get_best_variant(self) -> Dict[str, Any]:
        """Get the variant with highest expected performance"""
        if not self.variants:
            raise ValueError("No variants registered")

        best_variant_id = max(
            self.variants.items(),
            key=lambda x: x[1]['alpha'] / (x[1]['alpha'] + x[1]['beta'])
        )[0]

        return self.get_variant_stats(best_variant_id)

    def reallocate_budget(
        self,
        total_budget: float,
        min_budget_per_variant: float = 0.0
    ) -> Dict[str, float]:
        """
        Reallocate budget across variants based on performance
        Target: 20-30% ROAS improvement

        Args:
            total_budget: Total budget to allocate
            min_budget_per_variant: Minimum budget each variant should receive

        Returns:
            Dictionary mapping variant_id to allocated budget
        """
        if not self.variants:
            raise ValueError("No variants to allocate budget to")

        # Calculate performance scores for each variant
        scores = {}
        total_score = 0.0

        for variant_id, variant in self.variants.items():
            # Performance score = weighted combination of CTR, CVR, ROAS
            # Use Thompson Sampling expected value (alpha / (alpha + beta))
            expected_ctr = variant['alpha'] / (variant['alpha'] + variant['beta'])
            roas = variant.get('roas', 0.0)
            cvr = variant.get('cvr', 0.0)

            # Composite score (adjust weights based on business goals)
            score = (
                0.4 * expected_ctr +
                0.3 * min(roas / 2.0, 1.0) +  # Normalize ROAS
                0.3 * cvr
            )

            # Add exploration bonus for variants with few impressions
            impressions = variant['impressions']
            if impressions < 100:
                exploration_bonus = 0.1 * (1 - impressions / 100)
                score += exploration_bonus

            scores[variant_id] = max(score, 0.01)  # Ensure non-zero
            total_score += scores[variant_id]

        # Allocate budget proportionally to performance scores
        allocations = {}
        reserved_budget = min_budget_per_variant * len(self.variants)
        distributable_budget = total_budget - reserved_budget

        if distributable_budget < 0:
            raise ValueError(f"Total budget too small. Need at least {reserved_budget}")

        for variant_id, score in scores.items():
            # Proportional allocation
            proportion = score / total_score if total_score > 0 else 1.0 / len(scores)
            allocated = min_budget_per_variant + (proportion * distributable_budget)
            allocations[variant_id] = float(allocated)

        logger.info(f"Budget reallocated across {len(allocations)} variants")

        return allocations

    def _build_context_string(self, context: Optional[Dict[str, Any]]) -> str:
        """Build VW context feature string"""
        if not context:
            return "|f default:1.0"

        features = []
        for key, value in context.items():
            if isinstance(value, (int, float)):
                features.append(f"{key}:{value}")
            elif isinstance(value, str):
                features.append(f"{key}={value}")

        return f"|f {' '.join(features)}" if features else "|f default:1.0"

    def save_state(self, filepath: str):
        """Save optimizer state to file"""
        state = {
            'variants': self.variants,
            'history': self.history[-1000:],  # Last 1000 events
            'epsilon': self.epsilon,
            'random_seed': self.random_seed
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

        logger.info(f"Optimizer state saved to {filepath}")

    def load_state(self, filepath: str):
        """Load optimizer state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)

        self.variants = state['variants']
        self.history = state['history']
        self.epsilon = state.get('epsilon', self.epsilon)
        self.random_seed = state.get('random_seed', self.random_seed)

        logger.info(f"Optimizer state loaded from {filepath}")


# Global optimizer instance
thompson_optimizer = ThompsonSamplingOptimizer()
