"""
Market Intelligence Integration for ML Service
Auto-tracks competitor ads and analyzes trends
"""

import os
import sys
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add market-intel to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'market-intel'))

logger = logging.getLogger(__name__)

# Try to import Market Intel
try:
    from services.market_intel import CompetitorTracker, CSVImporter
    MARKET_INTEL_AVAILABLE = True
except ImportError:
    MARKET_INTEL_AVAILABLE = False
    logger.warning("Market Intel not available - competitor tracking disabled")

_tracker: Optional[Any] = None

def get_tracker():
    """Get or create CompetitorTracker instance"""
    global _tracker
    if not MARKET_INTEL_AVAILABLE:
        return None
    
    if _tracker is None:
        # Use database path or default
        db_path = os.getenv('MARKET_INTEL_DB_PATH', '/app/data/competitor_tracking.json')
        _tracker = CompetitorTracker(db_path=db_path)
    
    return _tracker

async def track_competitor_ad(ad_data: Dict[str, Any]) -> bool:
    """
    Track a competitor ad
    
    Args:
        ad_data: Dictionary with brand, hook_text, platform, etc.
    
    Returns:
        True if tracked successfully
    """
    if not MARKET_INTEL_AVAILABLE:
        return False
    
    try:
        tracker = get_tracker()
        if tracker:
            tracker.track_ad(ad_data)
            logger.info(f"Tracked competitor ad: {ad_data.get('brand')} - {ad_data.get('hook_text', '')[:50]}")
            return True
    except Exception as e:
        logger.error(f"Failed to track competitor ad: {e}")
    
    return False

async def analyze_trends(days: int = 30) -> Dict[str, Any]:
    """
    Analyze market trends from tracked competitor ads
    
    Args:
        days: Number of days to analyze
    
    Returns:
        Dictionary with trend analysis
    """
    if not MARKET_INTEL_AVAILABLE:
        return {"error": "Market Intel not available"}
    
    try:
        tracker = get_tracker()
        if tracker:
            trends = tracker.analyze_trends(days=days)
            logger.info(f"Analyzed trends for last {days} days: {trends.get('total_ads', 0)} ads")
            return trends
    except Exception as e:
        logger.error(f"Failed to analyze trends: {e}")
        return {"error": str(e)}
    
    return {"error": "Tracker not available"}

async def get_winning_hooks(top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Get top performing hooks from competitor analysis
    
    Args:
        top_n: Number of top hooks to return
    
    Returns:
        List of top performing hooks
    """
    if not MARKET_INTEL_AVAILABLE:
        return []
    
    try:
        tracker = get_tracker()
        if tracker:
            hooks = tracker.get_winning_hooks(top_n=top_n)
            return hooks
    except Exception as e:
        logger.error(f"Failed to get winning hooks: {e}")
    
    return []

async def get_competitor_ads(brand: Optional[str] = None, days: int = 30) -> List[Dict[str, Any]]:
    """
    Get tracked competitor ads
    
    Args:
        brand: Filter by specific brand
        days: Only return ads from last N days
    
    Returns:
        List of competitor ads
    """
    if not MARKET_INTEL_AVAILABLE:
        return []
    
    try:
        tracker = get_tracker()
        if tracker:
            ads = tracker.get_competitor_ads(brand=brand, days=days)
            return ads
    except Exception as e:
        logger.error(f"Failed to get competitor ads: {e}")
    
    return []

