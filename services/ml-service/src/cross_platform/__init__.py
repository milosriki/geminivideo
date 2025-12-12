"""
Cross-Platform Learning Module - Agent 5
Wire the existing cross-platform learning system to share insights between
Meta, TikTok, and Google Ads - enabling 100x training data.

This module aggregates performance data from all platforms, normalizes metrics
to comparable scales, and feeds unified insights to existing ML models.
"""

from .cross_learner import CrossPlatformLearner, get_cross_platform_learner
from .platform_normalizer import PlatformNormalizer, NormalizedMetrics, PlatformMetrics

__all__ = [
    'CrossPlatformLearner',
    'get_cross_platform_learner',
    'PlatformNormalizer',
    'NormalizedMetrics',
    'PlatformMetrics',
]
