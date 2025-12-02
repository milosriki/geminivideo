"""
Titan Core - Third-Party Integrations

Production-ready integrations for:
- HubSpot CRM (sales cycle tracking)
- Anytrack (conversion tracking & affiliate analytics)
- Meta Ads (campaign management)
- Analytics platforms
"""

from .hubspot import (
    HubSpotIntegration,
    Contact,
    Deal,
    StageChange,
    DealStage,
    LifecycleStage
)

from .anytrack import (
    AnytrackIntegration,
    AnytrackConversion,
    AffiliatePerformance,
    ConversionType,
    AnytrackAPIError
)

__all__ = [
    # HubSpot
    'HubSpotIntegration',
    'Contact',
    'Deal',
    'StageChange',
    'DealStage',
    'LifecycleStage',
    # Anytrack
    'AnytrackIntegration',
    'AnytrackConversion',
    'AffiliatePerformance',
    'ConversionType',
    'AnytrackAPIError'
]
