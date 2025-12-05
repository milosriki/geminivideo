"""
Intelligent Budget Allocation System - Agent 76
Multi-Armed Bandit with Thompson Sampling for Budget Optimization

Automatically shifts spend to winning ads using:
- Thompson Sampling with decay for explore/exploit balance
- Risk-adjusted returns for safe scaling
- Bayesian optimization for budget allocation
- Real-time performance tracking

Target: Maximize ROAS while minimizing risk for $20k/day marketers
"""

import logging
import os
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, JSON, Boolean, Numeric, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://geminivideo:geminivideo@localhost:5432/geminivideo"
)

Base = declarative_base()


# ==================== ENUMS ====================

class AllocationStrategy(Enum):
    """Budget allocation strategies"""
    THOMPSON_SAMPLING = "thompson_sampling"  # Thompson Sampling with Beta distribution
    UCB = "ucb"  # Upper Confidence Bound
    EPSILON_GREEDY = "epsilon_greedy"  # Epsilon-Greedy
    SOFTMAX = "softmax"  # Softmax (Boltzmann) exploration


class AdStatus(Enum):
    """Ad status for budget allocation"""
    ACTIVE = "active"
    LEARNING = "learning"
    WINNER = "winner"
    PAUSED = "paused"
    KILLED = "killed"


# ==================== DATABASE MODELS ====================

class BudgetAllocation(Base):
    """Track budget allocations over time"""
    __tablename__ = "budget_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String, nullable=False, index=True)
    campaign_id = Column(String, nullable=False, index=True)
    ad_id = Column(String, nullable=False, index=True)

    # Budget allocation
    allocated_budget = Column(Numeric(10, 2), nullable=False)
    previous_budget = Column(Numeric(10, 2), nullable=True)
    total_daily_budget = Column(Numeric(10, 2), nullable=False)
    allocation_percentage = Column(Float, nullable=False)

    # Performance metrics at allocation time
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    spend = Column(Numeric(10, 2), default=0.0)
    revenue = Column(Numeric(10, 2), default=0.0)
    ctr = Column(Float, default=0.0)
    cvr = Column(Float, default=0.0)
    roas = Column(Float, default=0.0)

    # Thompson Sampling parameters
    alpha = Column(Float, default=1.0)  # Success parameter
    beta = Column(Float, default=1.0)   # Failure parameter
    expected_value = Column(Float, default=0.0)
    confidence_interval = Column(JSON, default={})

    # Risk metrics
    risk_score = Column(Float, default=0.0)
    variance = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)

    # Metadata
    strategy = Column(String, default="thompson_sampling")
    reason = Column(Text, nullable=True)
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default='now()')
    updated_at = Column(DateTime(timezone=True), onupdate='now()')


class BudgetOptimizationHistory(Base):
    """Historical record of budget optimization decisions"""
    __tablename__ = "budget_optimization_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(String, nullable=False, index=True)
    optimization_run_id = Column(String, nullable=False, index=True)

    # Input state
    total_budget = Column(Numeric(10, 2), nullable=False)
    num_ads = Column(Integer, nullable=False)
    strategy = Column(String, nullable=False)

    # Results
    allocations = Column(JSON, nullable=False)  # Ad allocations
    expected_roas = Column(Float, nullable=False)
    expected_revenue = Column(Numeric(10, 2), nullable=False)
    risk_score = Column(Float, nullable=False)

    # Actual results (updated later)
    actual_roas = Column(Float, nullable=True)
    actual_revenue = Column(Numeric(10, 2), nullable=True)
    actual_spend = Column(Numeric(10, 2), nullable=True)

    # Performance
    optimization_accuracy = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default='now()')
    results_updated_at = Column(DateTime(timezone=True), nullable=True)


# ==================== DATA CLASSES ====================

@dataclass
class AdPerformance:
    """Ad performance metrics for budget optimization"""
    ad_id: str
    ad_name: str
    campaign_id: str
    account_id: str

    # Current metrics
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0

    # Calculated rates
    ctr: float = 0.0
    cvr: float = 0.0
    roas: float = 0.0
    cpa: float = 0.0

    # Thompson Sampling parameters
    alpha: float = 1.0
    beta: float = 1.0

    # Risk metrics
    variance: float = 0.0
    std_dev: float = 0.0

    # Current budget
    current_budget: float = 0.0
    status: str = "active"

    # Metadata
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None


@dataclass
class BudgetRecommendation:
    """Budget reallocation recommendation"""
    ad_id: str
    current_budget: float
    recommended_budget: float
    change_amount: float
    change_percentage: float

    # Reasoning
    reason: str
    expected_roas: float
    confidence: float
    risk_score: float

    # Thompson Sampling metrics
    alpha: float
    beta: float
    expected_value: float

    # Apply recommendation
    auto_apply: bool = False
    requires_approval: bool = False


# ==================== BUDGET OPTIMIZER ====================

class BudgetOptimizer:
    """
    Intelligent budget allocation using Multi-Armed Bandit algorithms

    Features:
    - Thompson Sampling with Bayesian optimization
    - Risk-adjusted returns (Sharpe ratio)
    - Exploration decay over time
    - Conservative scaling for safety
    """

    def __init__(
        self,
        strategy: AllocationStrategy = AllocationStrategy.THOMPSON_SAMPLING,
        decay_rate: float = 0.95,
        exploration_bonus: float = 0.1,
        risk_aversion: float = 0.5,
        min_impressions: int = 100,
        database_url: Optional[str] = None
    ):
        """
        Initialize Budget Optimizer

        Args:
            strategy: Allocation strategy (Thompson Sampling recommended)
            decay_rate: Decay rate for older observations (0.9-0.99)
            exploration_bonus: Bonus for under-explored ads (0.0-0.3)
            risk_aversion: Risk aversion coefficient (0.0=risk-seeking, 1.0=risk-averse)
            min_impressions: Minimum impressions before optimization
            database_url: Database connection string
        """
        self.strategy = strategy
        self.decay_rate = decay_rate
        self.exploration_bonus = exploration_bonus
        self.risk_aversion = risk_aversion
        self.min_impressions = min_impressions

        # Database connection
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(self.database_url)
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Performance tracking
        self.ad_performances: Dict[str, AdPerformance] = {}
        self.optimization_history: List[Dict[str, Any]] = []

        logger.info(f"Budget Optimizer initialized with strategy: {strategy.value}")

    def update_ad_performance(
        self,
        ad_id: str,
        metrics: Dict[str, Any],
        apply_decay: bool = True
    ):
        """
        Update ad performance metrics

        Args:
            ad_id: Ad identifier
            metrics: Performance metrics dictionary
            apply_decay: Apply time decay to existing metrics
        """
        if ad_id not in self.ad_performances:
            # New ad
            self.ad_performances[ad_id] = AdPerformance(
                ad_id=ad_id,
                ad_name=metrics.get('ad_name', f'Ad {ad_id}'),
                campaign_id=metrics.get('campaign_id', ''),
                account_id=metrics.get('account_id', ''),
                created_at=datetime.utcnow()
            )

        ad_perf = self.ad_performances[ad_id]

        # Apply decay to existing metrics if enabled
        if apply_decay and ad_perf.impressions > 0:
            decay_factor = self.decay_rate
            ad_perf.impressions = int(ad_perf.impressions * decay_factor)
            ad_perf.clicks = int(ad_perf.clicks * decay_factor)
            ad_perf.conversions = int(ad_perf.conversions * decay_factor)
            ad_perf.spend *= decay_factor
            ad_perf.revenue *= decay_factor
            ad_perf.alpha = 1.0 + (ad_perf.alpha - 1.0) * decay_factor
            ad_perf.beta = 1.0 + (ad_perf.beta - 1.0) * decay_factor

        # Update with new metrics
        ad_perf.impressions += metrics.get('impressions', 0)
        ad_perf.clicks += metrics.get('clicks', 0)
        ad_perf.conversions += metrics.get('conversions', 0)
        ad_perf.spend += metrics.get('spend', 0.0)
        ad_perf.revenue += metrics.get('revenue', 0.0)
        ad_perf.current_budget = metrics.get('budget', ad_perf.current_budget)
        ad_perf.status = metrics.get('status', ad_perf.status)

        # Calculate rates
        if ad_perf.impressions > 0:
            ad_perf.ctr = ad_perf.clicks / ad_perf.impressions
        if ad_perf.clicks > 0:
            ad_perf.cvr = ad_perf.conversions / ad_perf.clicks
        if ad_perf.spend > 0:
            ad_perf.roas = ad_perf.revenue / ad_perf.spend
            ad_perf.cpa = ad_perf.spend / ad_perf.conversions if ad_perf.conversions > 0 else 0.0

        # Update Thompson Sampling parameters (Beta distribution)
        # alpha = 1 + conversions, beta = 1 + (clicks - conversions)
        ad_perf.alpha = 1.0 + ad_perf.conversions
        ad_perf.beta = 1.0 + (ad_perf.clicks - ad_perf.conversions)

        # Calculate variance for risk metrics
        if ad_perf.impressions > self.min_impressions:
            # Variance of Beta distribution: (alpha * beta) / ((alpha + beta)^2 * (alpha + beta + 1))
            total = ad_perf.alpha + ad_perf.beta
            ad_perf.variance = (ad_perf.alpha * ad_perf.beta) / (total ** 2 * (total + 1))
            ad_perf.std_dev = np.sqrt(ad_perf.variance)

        ad_perf.last_updated = datetime.utcnow()

        logger.debug(f"Updated ad {ad_id}: ROAS={ad_perf.roas:.2f}, CTR={ad_perf.ctr:.4f}, α={ad_perf.alpha:.1f}, β={ad_perf.beta:.1f}")

    def calculate_thompson_sampling_scores(
        self,
        ad_ids: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        Calculate Thompson Sampling scores for ads

        Args:
            ad_ids: List of ad IDs to score (None = all ads)

        Returns:
            Dictionary mapping ad_id to Thompson Sampling score
        """
        if ad_ids is None:
            ad_ids = list(self.ad_performances.keys())

        scores = {}

        for ad_id in ad_ids:
            if ad_id not in self.ad_performances:
                scores[ad_id] = 0.0
                continue

            ad_perf = self.ad_performances[ad_id]

            # Sample from Beta distribution for Thompson Sampling
            sample = np.random.beta(ad_perf.alpha, ad_perf.beta)

            # Add exploration bonus for under-explored ads
            if ad_perf.impressions < self.min_impressions * 2:
                exploration_factor = 1.0 - (ad_perf.impressions / (self.min_impressions * 2))
                sample += self.exploration_bonus * exploration_factor

            # Risk adjustment using Sharpe-like ratio
            # Higher variance = higher risk = lower score (if risk-averse)
            risk_penalty = self.risk_aversion * ad_perf.std_dev
            sample -= risk_penalty

            # Weight by ROAS if available
            if ad_perf.roas > 0:
                roas_weight = min(ad_perf.roas / 3.0, 2.0)  # Normalize ROAS (3.0 = 1x, 6.0+ = 2x)
                sample *= roas_weight

            scores[ad_id] = max(sample, 0.0)

        return scores

    def calculate_ucb_scores(
        self,
        ad_ids: Optional[List[str]] = None,
        c: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate Upper Confidence Bound (UCB) scores

        Args:
            ad_ids: List of ad IDs to score
            c: Exploration constant (higher = more exploration)

        Returns:
            Dictionary mapping ad_id to UCB score
        """
        if ad_ids is None:
            ad_ids = list(self.ad_performances.keys())

        total_impressions = sum(
            self.ad_performances[aid].impressions
            for aid in ad_ids
            if aid in self.ad_performances
        )

        if total_impressions == 0:
            return {aid: 1.0 for aid in ad_ids}

        scores = {}

        for ad_id in ad_ids:
            if ad_id not in self.ad_performances:
                scores[ad_id] = float('inf')  # Unplayed arm
                continue

            ad_perf = self.ad_performances[ad_id]

            if ad_perf.impressions == 0:
                scores[ad_id] = float('inf')
                continue

            # UCB formula: mean + c * sqrt(log(total_trials) / trials_i)
            mean_cvr = ad_perf.alpha / (ad_perf.alpha + ad_perf.beta)
            exploration_term = c * np.sqrt(np.log(total_impressions) / ad_perf.impressions)

            ucb_score = mean_cvr + exploration_term

            # Weight by ROAS
            if ad_perf.roas > 0:
                ucb_score *= min(ad_perf.roas / 3.0, 2.0)

            scores[ad_id] = ucb_score

        return scores

    def allocate_budget(
        self,
        total_budget: float,
        ad_ids: Optional[List[str]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> List[BudgetRecommendation]:
        """
        Allocate budget across ads using selected strategy

        Args:
            total_budget: Total daily budget to allocate
            ad_ids: List of ad IDs to allocate budget to (None = all ads)
            constraints: Budget constraints (min/max per ad, etc.)

        Returns:
            List of budget recommendations
        """
        if ad_ids is None:
            ad_ids = list(self.ad_performances.keys())

        if not ad_ids:
            logger.warning("No ads to allocate budget to")
            return []

        # Default constraints
        if constraints is None:
            constraints = {}

        min_budget_per_ad = constraints.get('min_budget_per_ad', 5.0)
        max_budget_per_ad = constraints.get('max_budget_per_ad', total_budget * 0.5)

        # Calculate scores based on strategy
        if self.strategy == AllocationStrategy.THOMPSON_SAMPLING:
            scores = self.calculate_thompson_sampling_scores(ad_ids)
        elif self.strategy == AllocationStrategy.UCB:
            scores = self.calculate_ucb_scores(ad_ids)
        else:
            # Fallback to Thompson Sampling
            scores = self.calculate_thompson_sampling_scores(ad_ids)

        # Normalize scores
        total_score = sum(scores.values())
        if total_score == 0:
            # Equal allocation if no data
            scores = {aid: 1.0 for aid in ad_ids}
            total_score = len(ad_ids)

        # Reserve minimum budget for all ads
        reserved_budget = min_budget_per_ad * len(ad_ids)
        if reserved_budget > total_budget:
            logger.warning(f"Total budget too low: ${total_budget:.2f} < ${reserved_budget:.2f} required")
            # Scale down minimums
            min_budget_per_ad = total_budget / len(ad_ids)
            reserved_budget = total_budget

        distributable_budget = total_budget - reserved_budget

        # Allocate budget proportionally to scores
        recommendations = []

        for ad_id in ad_ids:
            if ad_id not in self.ad_performances:
                continue

            ad_perf = self.ad_performances[ad_id]
            score = scores[ad_id]

            # Calculate allocation
            proportion = score / total_score
            allocated = min_budget_per_ad + (proportion * distributable_budget)

            # Apply max constraint
            allocated = min(allocated, max_budget_per_ad)

            # Calculate change from current
            change_amount = allocated - ad_perf.current_budget
            change_percentage = (change_amount / ad_perf.current_budget * 100) if ad_perf.current_budget > 0 else 0.0

            # Expected value (mean of Beta distribution)
            expected_value = ad_perf.alpha / (ad_perf.alpha + ad_perf.beta)

            # Calculate confidence (inverse of variance)
            confidence = 1.0 / (1.0 + ad_perf.variance) if ad_perf.variance > 0 else 0.5

            # Risk score (higher = riskier)
            risk_score = ad_perf.std_dev * (1.0 if ad_perf.impressions < self.min_impressions else 0.5)

            # Determine reason
            reason = self._generate_allocation_reason(ad_perf, score, allocated, change_percentage)

            # Auto-apply logic
            auto_apply = abs(change_percentage) < 20 and ad_perf.impressions >= self.min_impressions
            requires_approval = allocated > 500 or abs(change_percentage) > 50

            recommendation = BudgetRecommendation(
                ad_id=ad_id,
                current_budget=ad_perf.current_budget,
                recommended_budget=allocated,
                change_amount=change_amount,
                change_percentage=change_percentage,
                reason=reason,
                expected_roas=ad_perf.roas,
                confidence=confidence,
                risk_score=risk_score,
                alpha=ad_perf.alpha,
                beta=ad_perf.beta,
                expected_value=expected_value,
                auto_apply=auto_apply,
                requires_approval=requires_approval
            )

            recommendations.append(recommendation)

        # Sort by recommended budget (descending)
        recommendations.sort(key=lambda r: r.recommended_budget, reverse=True)

        # Log optimization run
        self._log_optimization_run(total_budget, recommendations)

        logger.info(f"Budget allocated: ${total_budget:.2f} across {len(recommendations)} ads")

        return recommendations

    def _generate_allocation_reason(
        self,
        ad_perf: AdPerformance,
        score: float,
        allocated: float,
        change_pct: float
    ) -> str:
        """Generate human-readable reason for budget allocation"""
        reasons = []

        if ad_perf.impressions < self.min_impressions:
            reasons.append(f"Learning phase ({ad_perf.impressions}/{self.min_impressions} impressions)")

        if ad_perf.roas > 4.0:
            reasons.append(f"High ROAS ({ad_perf.roas:.2f}x)")
        elif ad_perf.roas > 3.0:
            reasons.append(f"Good ROAS ({ad_perf.roas:.2f}x)")
        elif ad_perf.roas < 1.5:
            reasons.append(f"Low ROAS ({ad_perf.roas:.2f}x)")

        if ad_perf.ctr > 0.05:
            reasons.append(f"Strong CTR ({ad_perf.ctr*100:.2f}%)")
        elif ad_perf.ctr < 0.02:
            reasons.append(f"Weak CTR ({ad_perf.ctr*100:.2f}%)")

        if change_pct > 20:
            reasons.append(f"Scaling up {change_pct:.0f}%")
        elif change_pct < -20:
            reasons.append(f"Scaling down {abs(change_pct):.0f}%")

        if ad_perf.conversions > 50:
            reasons.append(f"{ad_perf.conversions} conversions")

        if not reasons:
            reasons.append("Maintaining budget")

        return " | ".join(reasons)

    def _log_optimization_run(
        self,
        total_budget: float,
        recommendations: List[BudgetRecommendation]
    ):
        """Log optimization run to history"""
        run_id = str(uuid.uuid4())

        # Calculate expected outcomes
        expected_roas = np.mean([r.expected_roas for r in recommendations if r.expected_roas > 0])
        expected_revenue = sum(r.recommended_budget * r.expected_roas for r in recommendations)

        # Calculate risk score
        risk_scores = [r.risk_score for r in recommendations]
        avg_risk = np.mean(risk_scores) if risk_scores else 0.0

        history_entry = {
            'run_id': run_id,
            'timestamp': datetime.utcnow().isoformat(),
            'total_budget': total_budget,
            'num_ads': len(recommendations),
            'strategy': self.strategy.value,
            'expected_roas': float(expected_roas),
            'expected_revenue': float(expected_revenue),
            'risk_score': float(avg_risk),
            'allocations': [
                {
                    'ad_id': r.ad_id,
                    'allocated': r.recommended_budget,
                    'change_pct': r.change_percentage
                }
                for r in recommendations
            ]
        }

        self.optimization_history.append(history_entry)

        # Keep only last 100 runs in memory
        if len(self.optimization_history) > 100:
            self.optimization_history = self.optimization_history[-100:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of current ad performances"""
        if not self.ad_performances:
            return {
                'total_ads': 0,
                'total_spend': 0.0,
                'total_revenue': 0.0,
                'avg_roas': 0.0,
                'ads': []
            }

        ads = list(self.ad_performances.values())

        total_spend = sum(ad.spend for ad in ads)
        total_revenue = sum(ad.revenue for ad in ads)
        avg_roas = total_revenue / total_spend if total_spend > 0 else 0.0

        return {
            'total_ads': len(ads),
            'total_spend': total_spend,
            'total_revenue': total_revenue,
            'avg_roas': avg_roas,
            'best_ad': max(ads, key=lambda a: a.roas).ad_id if ads else None,
            'worst_ad': min(ads, key=lambda a: a.roas).ad_id if ads else None,
            'ads': [
                {
                    'ad_id': ad.ad_id,
                    'ad_name': ad.ad_name,
                    'roas': ad.roas,
                    'spend': ad.spend,
                    'revenue': ad.revenue,
                    'ctr': ad.ctr,
                    'conversions': ad.conversions,
                    'impressions': ad.impressions,
                    'current_budget': ad.current_budget,
                    'status': ad.status
                }
                for ad in sorted(ads, key=lambda a: a.roas, reverse=True)
            ]
        }

    def save_recommendations_to_db(
        self,
        recommendations: List[BudgetRecommendation],
        account_id: str,
        campaign_id: str
    ):
        """Save budget recommendations to database"""
        session = self.SessionLocal()

        try:
            for rec in recommendations:
                if rec.ad_id not in self.ad_performances:
                    continue

                ad_perf = self.ad_performances[rec.ad_id]

                allocation = BudgetAllocation(
                    account_id=account_id,
                    campaign_id=campaign_id,
                    ad_id=rec.ad_id,
                    allocated_budget=rec.recommended_budget,
                    previous_budget=rec.current_budget,
                    total_daily_budget=sum(r.recommended_budget for r in recommendations),
                    allocation_percentage=rec.recommended_budget / sum(r.recommended_budget for r in recommendations) * 100,
                    impressions=ad_perf.impressions,
                    clicks=ad_perf.clicks,
                    conversions=ad_perf.conversions,
                    spend=ad_perf.spend,
                    revenue=ad_perf.revenue,
                    ctr=ad_perf.ctr,
                    cvr=ad_perf.cvr,
                    roas=ad_perf.roas,
                    alpha=rec.alpha,
                    beta=rec.beta,
                    expected_value=rec.expected_value,
                    confidence_interval={'confidence': rec.confidence},
                    risk_score=rec.risk_score,
                    variance=ad_perf.variance,
                    strategy=self.strategy.value,
                    reason=rec.reason,
                    applied=False
                )

                session.add(allocation)

            session.commit()
            logger.info(f"Saved {len(recommendations)} budget recommendations to database")

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save recommendations: {e}")
            raise
        finally:
            session.close()


# Global optimizer instance
budget_optimizer = BudgetOptimizer(
    strategy=AllocationStrategy.THOMPSON_SAMPLING,
    decay_rate=0.95,
    exploration_bonus=0.1,
    risk_aversion=0.5,
    min_impressions=100
)
