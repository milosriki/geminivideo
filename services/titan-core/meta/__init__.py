"""
Meta Integration Module
Agent 7, 8 & 9/30 - ULTIMATE Production Plan
Includes Marketing API v19.0, Conversions API, and Ads Library
"""

from .marketing_api import (
    RealMetaAdsManager,
    CampaignObjective,
    OptimizationGoal,
    BillingEvent,
    MetaAPIError,
    MetaRateLimitError,
    RetryConfig,
)

from .conversions_api import MetaCAPI, UserInfo

from .ads_library_scraper import (
    RealAdsLibraryScraper,
    AdLibraryAd,
    AdPlatform,
    AdActiveStatus
)

__all__ = [
    # Marketing API (Agent 7)
    'RealMetaAdsManager',
    'CampaignObjective',
    'OptimizationGoal',
    'BillingEvent',
    'MetaAPIError',
    'MetaRateLimitError',
    'RetryConfig',
    # Conversions API (Agent 8)
    'MetaCAPI',
    'UserInfo',
    # Ads Library (Agent 9)
    'RealAdsLibraryScraper',
    'AdLibraryAd',
    'AdPlatform',
    'AdActiveStatus'
]
