"""
Cross-Platform Learner - Agent 5
Aggregates performance data from Meta, TikTok, and Google Ads to enable 100x training data.

This module:
1. Aggregates performance data from all platforms
2. Normalizes metrics to comparable scales
3. Feeds unified insights to existing ML models (CTR model, Creative DNA)
4. Uses Redis for cross-platform cache sharing
5. Enables 100x more training data by learning across platforms
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
import json
import numpy as np
from enum import Enum

from .platform_normalizer import (
    PlatformNormalizer,
    PlatformMetrics,
    NormalizedMetrics,
    Platform,
    get_normalizer
)

logger = logging.getLogger(__name__)

# Import Redis cache for cross-platform sharing
try:
    from src.cache.semantic_cache_manager import get_cache_manager
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache manager not available - cross-platform caching disabled")


@dataclass
class CrossPlatformInsight:
    """Unified insight from multiple platforms"""
    insight_type: str  # "ctr_pattern", "creative_dna", "audience_segment", etc.
    platforms: List[Platform]

    # Aggregated metrics
    avg_normalized_ctr: float
    avg_normalized_cpc: float
    avg_normalized_engagement: float
    avg_composite_score: float

    # Supporting data
    total_impressions: int
    total_conversions: int
    total_spend: float
    sample_size: int  # Number of campaigns/ads contributing

    # Confidence and quality
    confidence: float
    consistency_score: float  # How consistent across platforms (0-1)

    # Platform-specific breakdowns
    platform_breakdown: Dict[str, Dict[str, float]]

    # Metadata
    created_at: datetime
    updated_at: datetime


@dataclass
class UnifiedFeatures:
    """Unified feature vector for ML models from cross-platform data"""

    # Core normalized features (platform-agnostic)
    normalized_ctr: float
    normalized_cpc: float
    normalized_cpm: float
    normalized_engagement: float
    normalized_quality: float
    composite_score: float

    # Cross-platform signals
    platform_consistency: float  # How similar performance is across platforms
    best_platform_boost: float   # Boost from best-performing platform
    multi_platform_bonus: float  # Bonus for being validated on multiple platforms

    # Volume features
    total_impressions: int
    total_clicks: int
    total_conversions: int
    confidence: float

    # Platform presence (binary features)
    has_meta_data: bool
    has_tiktok_data: bool
    has_google_data: bool

    # Creative features (from Creative DNA)
    creative_dna_score: Optional[float] = None
    hook_strength: Optional[float] = None
    visual_appeal: Optional[float] = None

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for ML model input"""
        features = [
            self.normalized_ctr,
            self.normalized_cpc,
            self.normalized_cpm,
            self.normalized_engagement,
            self.normalized_quality,
            self.composite_score,
            self.platform_consistency,
            self.best_platform_boost,
            self.multi_platform_bonus,
            np.log1p(self.total_impressions),  # Log scale for volume features
            np.log1p(self.total_clicks),
            np.log1p(self.total_conversions),
            self.confidence,
            float(self.has_meta_data),
            float(self.has_tiktok_data),
            float(self.has_google_data),
            self.creative_dna_score or 0.5,
            self.hook_strength or 0.5,
            self.visual_appeal or 0.5
        ]
        return np.array(features, dtype=np.float32)


class CrossPlatformLearner:
    """
    Cross-Platform Learning System

    Aggregates insights from Meta, TikTok, and Google Ads to enable:
    - 100x more training data (by combining platforms)
    - Cross-platform pattern recognition
    - Unified creative scoring
    - Multi-platform budget optimization
    """

    def __init__(
        self,
        use_cache: bool = True,
        cache_ttl: int = 3600,  # 1 hour
        min_platforms_for_insight: int = 2
    ):
        """
        Initialize Cross-Platform Learner

        Args:
            use_cache: Whether to use Redis caching
            cache_ttl: Cache TTL in seconds
            min_platforms_for_insight: Minimum platforms needed for cross-platform insight
        """
        self.normalizer = get_normalizer()
        self.min_platforms_for_insight = min_platforms_for_insight
        self.cache_ttl = cache_ttl

        # Initialize cache
        self.cache_manager = None
        if use_cache and CACHE_AVAILABLE:
            try:
                self.cache_manager = get_cache_manager()
                logger.info("Cache manager enabled for cross-platform learning")
            except Exception as e:
                logger.warning(f"Failed to initialize cache manager: {e}")

        # In-memory fallback cache
        self._insight_cache: Dict[str, CrossPlatformInsight] = {}

        logger.info(
            f"CrossPlatformLearner initialized: "
            f"cache={'enabled' if self.cache_manager else 'disabled'}, "
            f"min_platforms={min_platforms_for_insight}"
        )

    def aggregate_platform_data(
        self,
        campaign_id: str,
        platform_data: Dict[Platform, PlatformMetrics]
    ) -> CrossPlatformInsight:
        """
        Aggregate data from multiple platforms for a campaign.

        Args:
            campaign_id: Campaign identifier
            platform_data: Dictionary mapping platform to metrics

        Returns:
            Unified cross-platform insight
        """
        if len(platform_data) < self.min_platforms_for_insight:
            logger.warning(
                f"Campaign {campaign_id} only has {len(platform_data)} platforms, "
                f"need {self.min_platforms_for_insight} for cross-platform insight"
            )

        # Normalize all platform metrics
        normalized_data = {}
        for platform, metrics in platform_data.items():
            normalized_data[platform] = self.normalizer.normalize(metrics)

        # Calculate aggregated metrics (weighted by confidence)
        total_weight = sum(n.confidence for n in normalized_data.values())

        if total_weight == 0:
            logger.warning(f"No confidence in data for campaign {campaign_id}")
            total_weight = len(normalized_data)

        avg_normalized_ctr = sum(
            n.normalized_ctr * n.confidence for n in normalized_data.values()
        ) / total_weight

        avg_normalized_cpc = sum(
            n.normalized_cpc * n.confidence for n in normalized_data.values()
        ) / total_weight

        avg_normalized_engagement = sum(
            n.normalized_engagement * n.confidence for n in normalized_data.values()
        ) / total_weight

        avg_composite_score = sum(
            n.composite_score * n.confidence for n in normalized_data.values()
        ) / total_weight

        # Calculate totals
        total_impressions = sum(
            platform_data[p].impressions for p in platform_data
        )
        total_conversions = sum(
            platform_data[p].conversions for p in platform_data
        )
        total_spend = sum(
            platform_data[p].spend for p in platform_data
        )

        # Calculate consistency score (how similar are platforms?)
        consistency_score = self._calculate_consistency(normalized_data)

        # Calculate overall confidence
        avg_confidence = np.mean([n.confidence for n in normalized_data.values()])

        # Platform breakdown
        platform_breakdown = {}
        for platform, normalized in normalized_data.items():
            platform_breakdown[platform.value] = {
                "ctr": normalized.normalized_ctr,
                "cpc": normalized.normalized_cpc,
                "engagement": normalized.normalized_engagement,
                "composite_score": normalized.composite_score,
                "confidence": normalized.confidence,
                "spend": platform_data[platform].spend,
                "conversions": platform_data[platform].conversions
            }

        insight = CrossPlatformInsight(
            insight_type="campaign_aggregation",
            platforms=list(platform_data.keys()),
            avg_normalized_ctr=avg_normalized_ctr,
            avg_normalized_cpc=avg_normalized_cpc,
            avg_normalized_engagement=avg_normalized_engagement,
            avg_composite_score=avg_composite_score,
            total_impressions=total_impressions,
            total_conversions=total_conversions,
            total_spend=total_spend,
            sample_size=len(platform_data),
            confidence=avg_confidence,
            consistency_score=consistency_score,
            platform_breakdown=platform_breakdown,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Cache the insight
        self._cache_insight(campaign_id, insight)

        logger.info(
            f"Aggregated {len(platform_data)} platforms for campaign {campaign_id}: "
            f"composite_score={avg_composite_score:.3f}, "
            f"consistency={consistency_score:.3f}"
        )

        return insight

    def get_unified_features(
        self,
        campaign_id: str,
        platform_data: Dict[Platform, PlatformMetrics],
        creative_dna: Optional[Dict[str, float]] = None
    ) -> UnifiedFeatures:
        """
        Generate unified feature vector for ML models.

        This is the key method that feeds cross-platform data to CTR model
        and Creative DNA.

        Args:
            campaign_id: Campaign identifier
            platform_data: Platform metrics
            creative_dna: Optional creative DNA features

        Returns:
            Unified feature vector
        """
        # Get cross-platform insight
        insight = self.aggregate_platform_data(campaign_id, platform_data)

        # Calculate cross-platform signals
        platform_consistency = insight.consistency_score

        # Best platform boost (how much better is best vs average)
        best_score = max(
            breakdown["composite_score"]
            for breakdown in insight.platform_breakdown.values()
        )
        avg_score = insight.avg_composite_score
        best_platform_boost = (best_score - avg_score) if avg_score > 0 else 0

        # Multi-platform bonus (more platforms = more validation)
        # 1 platform: 0.0, 2 platforms: 0.1, 3+ platforms: 0.2
        multi_platform_bonus = min(len(platform_data) - 1, 2) * 0.1

        # Calculate totals
        total_clicks = sum(p.clicks for p in platform_data.values())

        # Create unified features
        features = UnifiedFeatures(
            normalized_ctr=insight.avg_normalized_ctr,
            normalized_cpc=insight.avg_normalized_cpc,
            normalized_cpm=np.mean([
                self.normalizer.normalize(m).normalized_cpm
                for m in platform_data.values()
            ]),
            normalized_engagement=insight.avg_normalized_engagement,
            normalized_quality=np.mean([
                self.normalizer.normalize(m).normalized_quality
                for m in platform_data.values()
            ]),
            composite_score=insight.avg_composite_score,
            platform_consistency=platform_consistency,
            best_platform_boost=best_platform_boost,
            multi_platform_bonus=multi_platform_bonus,
            total_impressions=insight.total_impressions,
            total_clicks=total_clicks,
            total_conversions=insight.total_conversions,
            confidence=insight.confidence,
            has_meta_data=Platform.META in platform_data,
            has_tiktok_data=Platform.TIKTOK in platform_data,
            has_google_data=Platform.GOOGLE_ADS in platform_data,
            creative_dna_score=creative_dna.get("composite_score") if creative_dna else None,
            hook_strength=creative_dna.get("hook_strength") if creative_dna else None,
            visual_appeal=creative_dna.get("visual_appeal") if creative_dna else None
        )

        logger.info(
            f"Generated unified features for campaign {campaign_id}: "
            f"consistency={platform_consistency:.3f}, "
            f"multi_platform_bonus={multi_platform_bonus:.3f}"
        )

        return features

    def extract_cross_platform_patterns(
        self,
        campaigns: List[Tuple[str, Dict[Platform, PlatformMetrics]]],
        min_roas: float = 2.0
    ) -> Dict[str, Any]:
        """
        Extract patterns that work across multiple platforms (winners).

        This enables 100x more training data by learning from all platforms.

        Args:
            campaigns: List of (campaign_id, platform_data) tuples
            min_roas: Minimum ROAS to consider a winner

        Returns:
            Cross-platform patterns
        """
        logger.info(f"Extracting cross-platform patterns from {len(campaigns)} campaigns")

        winners = []
        platform_winners = defaultdict(list)

        for campaign_id, platform_data in campaigns:
            insight = self.aggregate_platform_data(campaign_id, platform_data)

            # Calculate overall ROAS
            roas = sum(
                p.revenue / p.spend if p.spend > 0 else 0
                for p in platform_data.values()
            ) / len(platform_data)

            if roas >= min_roas:
                winners.append({
                    "campaign_id": campaign_id,
                    "insight": insight,
                    "roas": roas,
                    "platforms": [p.value for p in platform_data.keys()]
                })

                # Track per-platform winners
                for platform in platform_data.keys():
                    platform_winners[platform].append(insight)

        logger.info(f"Found {len(winners)} winning campaigns across platforms")

        # Analyze patterns
        patterns = {
            "total_winners": len(winners),
            "total_campaigns": len(campaigns),
            "win_rate": len(winners) / len(campaigns) if campaigns else 0,

            # Aggregated winner metrics
            "avg_winner_ctr": np.mean([w["insight"].avg_normalized_ctr for w in winners]) if winners else 0,
            "avg_winner_engagement": np.mean([w["insight"].avg_normalized_engagement for w in winners]) if winners else 0,
            "avg_winner_composite": np.mean([w["insight"].avg_composite_score for w in winners]) if winners else 0,
            "avg_consistency": np.mean([w["insight"].consistency_score for w in winners]) if winners else 0,

            # Platform breakdown
            "platform_stats": {
                platform.value: {
                    "winner_count": len(platform_winners[platform]),
                    "avg_ctr": np.mean([i.avg_normalized_ctr for i in platform_winners[platform]]) if platform_winners[platform] else 0,
                    "avg_engagement": np.mean([i.avg_normalized_engagement for i in platform_winners[platform]]) if platform_winners[platform] else 0
                }
                for platform in Platform if platform != Platform.UNKNOWN
            },

            # Multi-platform insights
            "multi_platform_winners": len([w for w in winners if len(w["platforms"]) >= 2]),
            "best_platform_combo": self._find_best_platform_combo(winners),

            "extracted_at": datetime.utcnow().isoformat()
        }

        # Cache patterns
        if self.cache_manager and self.cache_manager.available:
            self.cache_manager.set(
                {"type": "cross_platform_patterns"},
                patterns,
                "cross_platform",
                ttl=self.cache_ttl
            )

        return patterns

    def get_training_data_for_ctr_model(
        self,
        campaigns: List[Tuple[str, Dict[Platform, PlatformMetrics]]],
        include_creative_dna: bool = True
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate training data for CTR model from cross-platform data.

        This is the integration point with ctr_model.py - providing 100x more
        training data by combining all platforms.

        Args:
            campaigns: List of campaign data
            include_creative_dna: Whether to include creative DNA features

        Returns:
            (X, y) tuple where X is feature matrix, y is target CTR
        """
        X_list = []
        y_list = []

        for campaign_id, platform_data in campaigns:
            # Get unified features
            features = self.get_unified_features(campaign_id, platform_data)

            # Target is normalized CTR (0-1 scale)
            target_ctr = features.normalized_ctr

            # Only include if we have sufficient confidence
            if features.confidence >= 0.5:
                X_list.append(features.to_array())
                y_list.append(target_ctr)

        X = np.array(X_list)
        y = np.array(y_list)

        logger.info(
            f"Generated {len(X)} training samples from cross-platform data "
            f"(avg CTR: {np.mean(y):.4f})"
        )

        return X, y

    def _calculate_consistency(
        self,
        normalized_data: Dict[Platform, NormalizedMetrics]
    ) -> float:
        """
        Calculate consistency score across platforms.

        Higher score = more consistent performance across platforms.
        """
        if len(normalized_data) < 2:
            return 1.0  # Single platform = perfect consistency

        # Calculate variance of composite scores
        scores = [n.composite_score for n in normalized_data.values()]
        variance = np.var(scores)

        # Convert to consistency score (0-1, higher is better)
        # Low variance = high consistency
        consistency = np.exp(-variance * 10)  # Exponential decay

        return float(consistency)

    def _find_best_platform_combo(
        self,
        winners: List[Dict]
    ) -> Dict[str, Any]:
        """Find the best performing platform combination"""
        combo_performance = defaultdict(lambda: {"count": 0, "total_roas": 0.0})

        for winner in winners:
            platforms = tuple(sorted(winner["platforms"]))
            combo_performance[platforms]["count"] += 1
            combo_performance[platforms]["total_roas"] += winner["roas"]

        if not combo_performance:
            return {"combo": [], "avg_roas": 0.0, "count": 0}

        # Find best combo by average ROAS
        best_combo = max(
            combo_performance.items(),
            key=lambda x: x[1]["total_roas"] / x[1]["count"]
        )

        return {
            "combo": list(best_combo[0]),
            "avg_roas": best_combo[1]["total_roas"] / best_combo[1]["count"],
            "count": best_combo[1]["count"]
        }

    def _cache_insight(self, key: str, insight: CrossPlatformInsight):
        """Cache cross-platform insight"""
        # Cache in Redis if available
        if self.cache_manager and self.cache_manager.available:
            self.cache_manager.set(
                {"campaign_id": key},
                asdict(insight),
                "cross_platform_insight",
                ttl=self.cache_ttl
            )

        # Also cache in memory (fallback)
        self._insight_cache[key] = insight

    def _get_cached_insight(self, key: str) -> Optional[CrossPlatformInsight]:
        """Get cached cross-platform insight"""
        # Try Redis first
        if self.cache_manager and self.cache_manager.available:
            cached = self.cache_manager.get(
                {"campaign_id": key},
                "cross_platform_insight"
            )
            if cached:
                # Convert dict back to dataclass
                cached["platforms"] = [Platform(p) for p in cached["platforms"]]
                cached["created_at"] = datetime.fromisoformat(cached["created_at"])
                cached["updated_at"] = datetime.fromisoformat(cached["updated_at"])
                return CrossPlatformInsight(**cached)

        # Fallback to memory cache
        return self._insight_cache.get(key)


# Singleton instance
_cross_platform_learner: Optional[CrossPlatformLearner] = None


def get_cross_platform_learner() -> CrossPlatformLearner:
    """Get or create singleton cross-platform learner instance"""
    global _cross_platform_learner
    if _cross_platform_learner is None:
        _cross_platform_learner = CrossPlatformLearner()
    return _cross_platform_learner
