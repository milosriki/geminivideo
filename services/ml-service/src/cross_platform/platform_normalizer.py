"""
Platform Normalizer - Agent 5
Normalizes metrics across Meta, TikTok, and Google Ads to comparable scales.

Each platform has different baseline metrics:
- Meta: CTR 1-3%, CPC $0.50-2.00, CPM $5-15
- TikTok: CTR 1.5-5%, CPC $0.20-1.00, CPM $3-10
- Google Ads: CTR 2-8%, CPC $1.00-5.00, CPM $10-30

This normalizer converts all metrics to a 0-1 scale for fair comparison.
"""

import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported advertising platforms"""
    META = "meta"
    TIKTOK = "tiktok"
    GOOGLE_ADS = "google_ads"
    UNKNOWN = "unknown"


@dataclass
class PlatformMetrics:
    """Raw metrics from a platform"""
    platform: Platform
    ctr: float
    cpc: float
    cpm: float
    impressions: int
    clicks: int
    spend: float
    conversions: int = 0
    revenue: float = 0.0

    # Platform-specific metrics
    engagement_rate: Optional[float] = None  # TikTok
    quality_score: Optional[float] = None     # Google Ads
    relevance_score: Optional[float] = None   # Meta

    # Metadata
    campaign_id: Optional[str] = None
    ad_id: Optional[str] = None


@dataclass
class NormalizedMetrics:
    """Normalized metrics (0-1 scale) for cross-platform comparison"""
    platform: Platform

    # Core normalized metrics (0-1 scale)
    normalized_ctr: float
    normalized_cpc: float
    normalized_cpm: float
    normalized_engagement: float
    normalized_quality: float

    # Composite score (0-1 scale)
    composite_score: float

    # Original metrics (for reference)
    original_ctr: float
    original_cpc: float
    original_cpm: float

    # Performance indicators
    spend: float
    conversions: int
    roas: float

    # Confidence score (0-1, based on data volume)
    confidence: float


class PlatformNormalizer:
    """
    Normalize metrics across advertising platforms for fair comparison.

    Uses platform-specific benchmarks and statistical normalization
    to enable cross-platform learning.
    """

    # Platform baseline ranges (10th to 90th percentile)
    PLATFORM_BENCHMARKS = {
        Platform.META: {
            "ctr": {"min": 0.005, "max": 0.030, "ideal": 0.015},      # 0.5% - 3%
            "cpc": {"min": 0.20, "max": 3.00, "ideal": 1.00},         # $0.20 - $3.00
            "cpm": {"min": 3.0, "max": 20.0, "ideal": 10.0},          # $3 - $20
            "engagement": {"min": 0.01, "max": 0.10, "ideal": 0.05},  # 1% - 10%
            "relevance": {"min": 1.0, "max": 10.0, "ideal": 7.0}      # 1-10 scale
        },
        Platform.TIKTOK: {
            "ctr": {"min": 0.010, "max": 0.060, "ideal": 0.030},      # 1% - 6%
            "cpc": {"min": 0.10, "max": 1.50, "ideal": 0.50},         # $0.10 - $1.50
            "cpm": {"min": 2.0, "max": 15.0, "ideal": 6.0},           # $2 - $15
            "engagement": {"min": 0.02, "max": 0.15, "ideal": 0.08},  # 2% - 15%
            "quality": {"min": 0.3, "max": 1.0, "ideal": 0.7}         # 0-1 scale
        },
        Platform.GOOGLE_ADS: {
            "ctr": {"min": 0.015, "max": 0.100, "ideal": 0.040},      # 1.5% - 10%
            "cpc": {"min": 0.50, "max": 6.00, "ideal": 2.00},         # $0.50 - $6.00
            "cpm": {"min": 5.0, "max": 40.0, "ideal": 15.0},          # $5 - $40
            "engagement": {"min": 0.01, "max": 0.08, "ideal": 0.04},  # 1% - 8%
            "quality": {"min": 1.0, "max": 10.0, "ideal": 7.0}        # 1-10 scale
        }
    }

    def __init__(self):
        """Initialize Platform Normalizer"""
        logger.info("PlatformNormalizer initialized for Meta, TikTok, and Google Ads")

    def normalize(self, metrics: PlatformMetrics) -> NormalizedMetrics:
        """
        Normalize platform metrics to 0-1 scale.

        Args:
            metrics: Raw platform metrics

        Returns:
            Normalized metrics for cross-platform comparison
        """
        platform = metrics.platform

        if platform not in self.PLATFORM_BENCHMARKS:
            logger.warning(f"Unknown platform {platform}, using default normalization")
            platform = Platform.META

        benchmarks = self.PLATFORM_BENCHMARKS[platform]

        # Normalize CTR (higher is better)
        normalized_ctr = self._normalize_value(
            metrics.ctr,
            benchmarks["ctr"]["min"],
            benchmarks["ctr"]["max"]
        )

        # Normalize CPC (lower is better - invert)
        normalized_cpc = 1.0 - self._normalize_value(
            metrics.cpc,
            benchmarks["cpc"]["min"],
            benchmarks["cpc"]["max"]
        )

        # Normalize CPM (lower is better - invert)
        normalized_cpm = 1.0 - self._normalize_value(
            metrics.cpm,
            benchmarks["cpm"]["min"],
            benchmarks["cpm"]["max"]
        )

        # Normalize engagement (platform-specific)
        normalized_engagement = self._normalize_engagement(metrics, benchmarks)

        # Normalize quality score (platform-specific)
        normalized_quality = self._normalize_quality(metrics, benchmarks)

        # Calculate composite score (weighted average)
        composite_score = self._calculate_composite_score(
            normalized_ctr=normalized_ctr,
            normalized_cpc=normalized_cpc,
            normalized_cpm=normalized_cpm,
            normalized_engagement=normalized_engagement,
            normalized_quality=normalized_quality
        )

        # Calculate ROAS
        roas = metrics.revenue / metrics.spend if metrics.spend > 0 else 0.0

        # Calculate confidence based on data volume
        confidence = self._calculate_confidence(metrics)

        return NormalizedMetrics(
            platform=platform,
            normalized_ctr=normalized_ctr,
            normalized_cpc=normalized_cpc,
            normalized_cpm=normalized_cpm,
            normalized_engagement=normalized_engagement,
            normalized_quality=normalized_quality,
            composite_score=composite_score,
            original_ctr=metrics.ctr,
            original_cpc=metrics.cpc,
            original_cpm=metrics.cpm,
            spend=metrics.spend,
            conversions=metrics.conversions,
            roas=roas,
            confidence=confidence
        )

    def _normalize_value(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to 0-1 scale using min-max normalization.

        Values below min get 0.0, values above max get 1.0.
        """
        if value <= min_val:
            return 0.0
        elif value >= max_val:
            return 1.0
        else:
            return (value - min_val) / (max_val - min_val)

    def _normalize_engagement(
        self,
        metrics: PlatformMetrics,
        benchmarks: Dict
    ) -> float:
        """Normalize engagement rate (platform-specific)"""

        if metrics.engagement_rate is not None:
            # Use provided engagement rate
            engagement = metrics.engagement_rate
        else:
            # Calculate from CTR as proxy
            engagement = metrics.ctr

        return self._normalize_value(
            engagement,
            benchmarks["engagement"]["min"],
            benchmarks["engagement"]["max"]
        )

    def _normalize_quality(
        self,
        metrics: PlatformMetrics,
        benchmarks: Dict
    ) -> float:
        """Normalize quality score (platform-specific)"""

        # Get platform-specific quality metric
        if metrics.platform == Platform.GOOGLE_ADS and metrics.quality_score is not None:
            quality = metrics.quality_score
            quality_key = "quality"
        elif metrics.platform == Platform.META and metrics.relevance_score is not None:
            quality = metrics.relevance_score
            quality_key = "relevance"
        elif metrics.platform == Platform.TIKTOK:
            # TikTok doesn't have explicit quality score, use engagement as proxy
            quality = metrics.engagement_rate or metrics.ctr * 10  # Scale CTR to 0-1
            quality_key = "quality"
        else:
            # Default: use CTR as quality proxy
            quality = metrics.ctr * 10  # Scale to 0-1
            quality_key = "quality" if "quality" in benchmarks else "relevance"

        if quality_key not in benchmarks:
            quality_key = "engagement"

        return self._normalize_value(
            quality,
            benchmarks[quality_key]["min"],
            benchmarks[quality_key]["max"]
        )

    def _calculate_composite_score(
        self,
        normalized_ctr: float,
        normalized_cpc: float,
        normalized_cpm: float,
        normalized_engagement: float,
        normalized_quality: float
    ) -> float:
        """
        Calculate composite score as weighted average.

        Weights:
        - CTR: 30% (primary engagement metric)
        - CPC: 25% (cost efficiency)
        - CPM: 15% (reach efficiency)
        - Engagement: 15% (secondary engagement)
        - Quality: 15% (platform quality signals)
        """
        weights = {
            "ctr": 0.30,
            "cpc": 0.25,
            "cpm": 0.15,
            "engagement": 0.15,
            "quality": 0.15
        }

        composite = (
            weights["ctr"] * normalized_ctr +
            weights["cpc"] * normalized_cpc +
            weights["cpm"] * normalized_cpm +
            weights["engagement"] * normalized_engagement +
            weights["quality"] * normalized_quality
        )

        return min(max(composite, 0.0), 1.0)

    def _calculate_confidence(self, metrics: PlatformMetrics) -> float:
        """
        Calculate confidence score based on data volume.

        More impressions = higher confidence.
        - < 100 impressions: Low confidence (0.3)
        - 100-1000 impressions: Medium confidence (0.6)
        - 1000-10000 impressions: High confidence (0.9)
        - > 10000 impressions: Very high confidence (1.0)
        """
        impressions = metrics.impressions

        if impressions < 100:
            return 0.3
        elif impressions < 1000:
            # Linear interpolation between 0.3 and 0.6
            return 0.3 + (impressions - 100) / 900 * 0.3
        elif impressions < 10000:
            # Linear interpolation between 0.6 and 0.9
            return 0.6 + (impressions - 1000) / 9000 * 0.3
        else:
            # Linear interpolation between 0.9 and 1.0 (capped at 1.0)
            return min(0.9 + (impressions - 10000) / 40000 * 0.1, 1.0)

    def compare_platforms(
        self,
        metrics_list: list[PlatformMetrics]
    ) -> Dict[Platform, NormalizedMetrics]:
        """
        Compare metrics across multiple platforms.

        Args:
            metrics_list: List of platform metrics to compare

        Returns:
            Dictionary mapping platform to normalized metrics
        """
        results = {}

        for metrics in metrics_list:
            normalized = self.normalize(metrics)
            results[metrics.platform] = normalized

        # Log comparison
        logger.info("Cross-platform comparison:")
        for platform, normalized in results.items():
            logger.info(
                f"  {platform.value}: composite_score={normalized.composite_score:.3f}, "
                f"CTR={normalized.normalized_ctr:.3f}, "
                f"CPC={normalized.normalized_cpc:.3f}, "
                f"confidence={normalized.confidence:.3f}"
            )

        return results

    def get_best_platform(
        self,
        metrics_list: list[PlatformMetrics],
        min_confidence: float = 0.6
    ) -> Tuple[Platform, NormalizedMetrics]:
        """
        Get the best performing platform from a list.

        Args:
            metrics_list: List of platform metrics
            min_confidence: Minimum confidence threshold

        Returns:
            Tuple of (best_platform, normalized_metrics)
        """
        results = self.compare_platforms(metrics_list)

        # Filter by minimum confidence
        filtered = {
            platform: metrics
            for platform, metrics in results.items()
            if metrics.confidence >= min_confidence
        }

        if not filtered:
            logger.warning(
                f"No platforms meet minimum confidence {min_confidence}, "
                f"using all platforms"
            )
            filtered = results

        # Find platform with highest composite score
        best_platform = max(
            filtered.items(),
            key=lambda x: x[1].composite_score
        )

        logger.info(
            f"Best platform: {best_platform[0].value} "
            f"(score: {best_platform[1].composite_score:.3f})"
        )

        return best_platform

    def convert_to_meta_equivalent(
        self,
        metrics: PlatformMetrics
    ) -> PlatformMetrics:
        """
        Convert metrics from any platform to Meta-equivalent values.

        Useful for creating unified reports in "Meta terms".

        Args:
            metrics: Platform metrics to convert

        Returns:
            Metrics scaled to Meta benchmarks
        """
        if metrics.platform == Platform.META:
            return metrics

        # Normalize first
        normalized = self.normalize(metrics)

        # Get Meta benchmarks
        meta_benchmarks = self.PLATFORM_BENCHMARKS[Platform.META]

        # Convert normalized values back to Meta scale
        meta_ctr = (
            normalized.normalized_ctr *
            (meta_benchmarks["ctr"]["max"] - meta_benchmarks["ctr"]["min"]) +
            meta_benchmarks["ctr"]["min"]
        )

        meta_cpc = (
            (1.0 - normalized.normalized_cpc) *
            (meta_benchmarks["cpc"]["max"] - meta_benchmarks["cpc"]["min"]) +
            meta_benchmarks["cpc"]["min"]
        )

        meta_cpm = (
            (1.0 - normalized.normalized_cpm) *
            (meta_benchmarks["cpm"]["max"] - meta_benchmarks["cpm"]["min"]) +
            meta_benchmarks["cpm"]["min"]
        )

        # Create Meta-equivalent metrics
        return PlatformMetrics(
            platform=Platform.META,
            ctr=meta_ctr,
            cpc=meta_cpc,
            cpm=meta_cpm,
            impressions=metrics.impressions,
            clicks=int(metrics.impressions * meta_ctr),
            spend=metrics.spend,
            conversions=metrics.conversions,
            revenue=metrics.revenue,
            relevance_score=normalized.normalized_quality * 10,  # Scale to 1-10
            campaign_id=f"meta_equiv_{metrics.campaign_id}",
            ad_id=f"meta_equiv_{metrics.ad_id}"
        )


# Singleton instance
_normalizer_instance: Optional[PlatformNormalizer] = None


def get_normalizer() -> PlatformNormalizer:
    """Get or create singleton normalizer instance"""
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = PlatformNormalizer()
    return _normalizer_instance
