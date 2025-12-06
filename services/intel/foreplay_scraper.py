"""
Foreplay Official API Integration v0.14.4b

Official API client for Foreplay - the winning ads swipe file platform.
Uses the public API to pull ads, transcriptions, and emotional analysis.

API Documentation: https://public.api.foreplay.co/docs
Base URL: https://public.api.foreplay.co/

Key Features:
- Full transcriptions with timestamps for hook analysis
- Emotional drivers pre-classified
- Running duration tracking (longer running = winner signal)
- Multi-platform support (Meta, TikTok, LinkedIn, etc.)
- Brand tracking via Spyder

Connection: API key in Authorization header
"""

import os
import json
import logging
import asyncio
import hashlib
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


# =============================================================================
# Enums matching Foreplay API
# =============================================================================

class DisplayFormat(Enum):
    """Foreplay display formats"""
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"
    DCO = "dco"  # Dynamic Creative Optimization
    DPA = "dpa"  # Dynamic Product Ads


class Platform(Enum):
    """Supported ad platforms"""
    META = "meta"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    YOUTUBE = "youtube"
    TWITTER = "twitter"


class SortOrder(Enum):
    """Sort options for ads"""
    NEWEST = "newest"
    OLDEST = "oldest"
    LONGEST_RUNNING = "longest_running"
    SHORTEST_RUNNING = "shortest_running"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class TimestampedTranscription:
    """Timestamped transcription segment"""
    start_time: float
    end_time: float
    text: str

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class EmotionalDriver:
    """Pre-classified emotional driver from Foreplay"""
    emotion: str
    intensity: float  # 0-1
    keywords: List[str]


@dataclass
class ForeplayAd:
    """
    Winning ad from Foreplay API

    Maps to /api/swipefile/ads and /api/discovery/ads response
    """
    # Core identifiers
    id: str
    external_id: Optional[str]  # Platform's ad ID

    # Advertiser info
    advertiser_name: str
    advertiser_id: Optional[str]
    page_profile_picture_url: Optional[str]

    # Creative
    display_format: DisplayFormat
    media_url: Optional[str]
    thumbnail_url: Optional[str]
    video_duration: Optional[float]  # seconds

    # Copy elements
    headline: str
    primary_text: str
    cta_text: str
    description: Optional[str]
    landing_page_url: Optional[str]

    # Transcriptions - KEY FEATURE
    full_transcription: Optional[str]
    timestamped_transcription: List[TimestampedTranscription]

    # Emotional analysis - PRE-CLASSIFIED BY FOREPLAY
    emotional_drivers: List[EmotionalDriver]

    # Performance signals
    running_duration_days: int  # Longer = winner signal
    first_seen: datetime
    last_seen: Optional[datetime]
    is_active: bool

    # Categorization
    niches: List[str]
    market_target: Optional[str]
    languages: List[str]
    platform: Platform

    # User data (from swipefile)
    boards: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    saved_at: Optional[datetime] = None

    # Extracted patterns
    hook_text: str = ""
    hook_timing_ms: int = 0
    patterns: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ForeplayBoard:
    """Swipefile board/folder"""
    id: str
    name: str
    ad_count: int
    created_at: datetime
    is_shared: bool


@dataclass
class TrackedBrand:
    """Brand being tracked via Spyder"""
    id: str
    name: str
    domain: Optional[str]
    ad_count: int
    platforms: List[str]
    tracking_since: datetime


@dataclass
class BrandAnalytics:
    """Brand analytics data"""
    brand_id: str
    total_ads: int
    active_ads: int
    avg_running_duration: float
    top_formats: Dict[str, int]
    top_niches: List[str]
    emotional_breakdown: Dict[str, int]


# =============================================================================
# API Error Handling
# =============================================================================

class ForeplayAPIError(Exception):
    """Foreplay API error"""
    def __init__(self, message: str, status_code: int = None, response_body: str = None):
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


# =============================================================================
# Main Integration Class
# =============================================================================

class ForeplayIntegration:
    """
    Official Foreplay API Integration

    Endpoints:
    - /api/swipefile/ads - User's saved winning ads
    - /api/discovery/ads - Search all ads with filters
    - /api/spyder/brands - Tracked brands
    - /api/spyder/brand/ads - Brand's ads
    - /api/brand/analytics - Brand analytics

    Usage:
        client = ForeplayIntegration(api_key="your_key")
        await client.connect()

        # Get saved winning ads
        ads = await client.get_swipefile_ads(limit=100)

        # Search discovery
        ads = await client.search_discovery_ads(
            niches=["fitness", "health"],
            display_formats=["video"],
            min_running_days=30
        )

        # Extract patterns for learning
        patterns = client.extract_winning_patterns(ads)
    """

    BASE_URL = "https://public.api.foreplay.co"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Foreplay client.

        Args:
            api_key: Foreplay API key from settings
        """
        self.api_key = api_key or os.getenv("FOREPLAY_API_KEY")
        self.session: Optional[aiohttp.ClientSession] = None
        self.connected = False
        self.user_info: Dict = {}

        if not self.api_key:
            logger.warning("⚠️ FOREPLAY_API_KEY not set - Foreplay integration disabled")
        else:
            logger.info("✅ Foreplay API key configured")

    async def connect(self) -> bool:
        """
        Initialize API session and verify connection.

        Returns:
            True if connected successfully
        """
        if not self.api_key:
            logger.error("Cannot connect: No API key provided")
            return False

        try:
            self.session = aiohttp.ClientSession(headers={
                "Authorization": self.api_key,  # Just the key, no Bearer
                "Content-Type": "application/json",
                "Accept": "application/json"
            })

            # Test with a simple request
            async with self.session.get(
                f"{self.BASE_URL}/api/swipefile/ads",
                params={"page": 1, "per_page": 1}
            ) as resp:
                if resp.status == 200:
                    self.connected = True
                    logger.info("✅ Connected to Foreplay API")
                    return True
                elif resp.status == 401:
                    logger.error("❌ Foreplay API: Invalid API key")
                    return False
                else:
                    error_text = await resp.text()
                    logger.error(f"❌ Foreplay API error {resp.status}: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Failed to connect to Foreplay: {e}")
            return False

    async def disconnect(self):
        """Close API session"""
        if self.session:
            await self.session.close()
            self.session = None
            self.connected = False

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Dict[str, Any]:
        """
        Make API request with error handling.

        Args:
            method: HTTP method
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body

        Returns:
            API response as dict
        """
        if not self.session:
            await self.connect()

        if not self.connected:
            raise ForeplayAPIError("Not connected to Foreplay API")

        url = f"{self.BASE_URL}{endpoint}"

        try:
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                response_text = await resp.text()

                if resp.status == 200:
                    return json.loads(response_text) if response_text else {}
                elif resp.status == 401:
                    raise ForeplayAPIError("Invalid API key", 401)
                elif resp.status == 404:
                    raise ForeplayAPIError("Resource not found", 404)
                elif resp.status == 429:
                    raise ForeplayAPIError("Rate limited - slow down", 429)
                else:
                    raise ForeplayAPIError(
                        f"API error: {resp.status}",
                        resp.status,
                        response_text
                    )

        except aiohttp.ClientError as e:
            raise ForeplayAPIError(f"Network error: {e}")

    # =========================================================================
    # Swipefile Endpoints - User's Saved Ads
    # =========================================================================

    async def get_swipefile_ads(
        self,
        page: int = 1,
        per_page: int = 50,
        board_ids: List[str] = None,
        display_formats: List[str] = None,
        niches: List[str] = None,
        languages: List[str] = None,
        sort: SortOrder = SortOrder.NEWEST,
        search_query: str = None
    ) -> List[ForeplayAd]:
        """
        Get user's saved ads from swipefile.

        API: GET /api/swipefile/ads

        Args:
            page: Page number (1-indexed)
            per_page: Results per page (max 100)
            board_ids: Filter by board IDs
            display_formats: Filter by format (video, image, carousel, dco, dpa)
            niches: Filter by niches
            languages: Filter by languages
            sort: Sort order
            search_query: Search in ad text

        Returns:
            List of saved ads
        """
        params = {
            "page": page,
            "per_page": min(per_page, 100),
            "sort": sort.value
        }

        if board_ids:
            params["board_ids"] = ",".join(board_ids)
        if display_formats:
            params["display_formats"] = ",".join(display_formats)
        if niches:
            params["niches"] = ",".join(niches)
        if languages:
            params["languages"] = ",".join(languages)
        if search_query:
            params["search"] = search_query

        logger.info(f"Fetching swipefile ads (page {page}, {per_page} per page)")
        response = await self._request("GET", "/api/swipefile/ads", params=params)

        ads = []
        for ad_data in response.get("data", response.get("ads", [])):
            ad = self._parse_ad(ad_data, source="swipefile")
            if ad:
                ads.append(ad)

        logger.info(f"Retrieved {len(ads)} ads from swipefile")
        return ads

    async def get_all_swipefile_ads(
        self,
        max_ads: int = 1000,
        **filters
    ) -> List[ForeplayAd]:
        """
        Get ALL saved ads with pagination.

        Args:
            max_ads: Maximum ads to retrieve
            **filters: Additional filters passed to get_swipefile_ads

        Returns:
            All matching ads
        """
        all_ads = []
        page = 1
        per_page = 100

        while len(all_ads) < max_ads:
            ads = await self.get_swipefile_ads(
                page=page,
                per_page=per_page,
                **filters
            )

            if not ads:
                break

            all_ads.extend(ads)

            if len(ads) < per_page:
                break

            page += 1
            await asyncio.sleep(0.2)  # Rate limit respect

        logger.info(f"Retrieved total {len(all_ads)} ads from swipefile")
        return all_ads[:max_ads]

    async def get_swipefile_boards(self) -> List[ForeplayBoard]:
        """
        Get user's swipefile boards/folders.

        API: GET /api/swipefile/boards

        Returns:
            List of boards
        """
        response = await self._request("GET", "/api/swipefile/boards")

        boards = []
        for board_data in response.get("data", response.get("boards", [])):
            boards.append(ForeplayBoard(
                id=board_data["id"],
                name=board_data["name"],
                ad_count=board_data.get("ad_count", 0),
                created_at=datetime.fromisoformat(board_data.get("created_at", datetime.now().isoformat())),
                is_shared=board_data.get("is_shared", False)
            ))

        return boards

    # =========================================================================
    # Discovery Endpoints - Search All Ads
    # =========================================================================

    async def search_discovery_ads(
        self,
        page: int = 1,
        per_page: int = 50,
        display_formats: List[str] = None,
        niches: List[str] = None,
        market_targets: List[str] = None,
        languages: List[str] = None,
        platforms: List[str] = None,
        min_running_days: int = None,
        max_running_days: int = None,
        has_transcription: bool = None,
        sort: SortOrder = SortOrder.LONGEST_RUNNING,
        search_query: str = None
    ) -> List[ForeplayAd]:
        """
        Search all ads in Foreplay discovery.

        API: GET /api/discovery/ads

        Args:
            page: Page number
            per_page: Results per page
            display_formats: Filter formats
            niches: Filter niches (e.g., "fitness", "ecommerce")
            market_targets: Filter by target market
            languages: Filter languages
            platforms: Filter platforms (meta, tiktok, linkedin)
            min_running_days: Minimum days running (winner signal!)
            max_running_days: Maximum days running
            has_transcription: Only ads with transcriptions
            sort: Sort order (LONGEST_RUNNING recommended for winners)
            search_query: Search query

        Returns:
            List of discovery ads
        """
        params = {
            "page": page,
            "per_page": min(per_page, 100),
            "sort": sort.value
        }

        if display_formats:
            params["display_formats"] = ",".join(display_formats)
        if niches:
            params["niches"] = ",".join(niches)
        if market_targets:
            params["market_targets"] = ",".join(market_targets)
        if languages:
            params["languages"] = ",".join(languages)
        if platforms:
            params["platforms"] = ",".join(platforms)
        if min_running_days:
            params["min_running_days"] = min_running_days
        if max_running_days:
            params["max_running_days"] = max_running_days
        if has_transcription is not None:
            params["has_transcription"] = str(has_transcription).lower()
        if search_query:
            params["search"] = search_query

        logger.info(f"Searching discovery ads (page {page})")
        response = await self._request("GET", "/api/discovery/ads", params=params)

        ads = []
        for ad_data in response.get("data", response.get("ads", [])):
            ad = self._parse_ad(ad_data, source="discovery")
            if ad:
                ads.append(ad)

        logger.info(f"Found {len(ads)} ads in discovery")
        return ads

    async def get_long_running_winners(
        self,
        min_days: int = 30,
        niches: List[str] = None,
        max_ads: int = 500
    ) -> List[ForeplayAd]:
        """
        Get long-running ads (proven winners).

        Ads running 30+ days are statistically likely winners.
        This is the KEY method for bootstrapping learning.

        Args:
            min_days: Minimum days running
            niches: Filter by niche
            max_ads: Maximum to retrieve

        Returns:
            List of proven winner ads
        """
        all_ads = []
        page = 1

        while len(all_ads) < max_ads:
            ads = await self.search_discovery_ads(
                page=page,
                per_page=100,
                niches=niches,
                min_running_days=min_days,
                has_transcription=True,  # We want transcriptions for analysis
                sort=SortOrder.LONGEST_RUNNING
            )

            if not ads:
                break

            all_ads.extend(ads)

            if len(ads) < 100:
                break

            page += 1
            await asyncio.sleep(0.2)

        logger.info(f"Found {len(all_ads)} long-running winners (30+ days)")
        return all_ads[:max_ads]

    # =========================================================================
    # Spyder Endpoints - Brand Tracking
    # =========================================================================

    async def get_tracked_brands(self) -> List[TrackedBrand]:
        """
        Get brands being tracked via Spyder.

        API: GET /api/spyder/brands

        Returns:
            List of tracked brands
        """
        response = await self._request("GET", "/api/spyder/brands")

        brands = []
        for brand_data in response.get("data", response.get("brands", [])):
            brands.append(TrackedBrand(
                id=brand_data["id"],
                name=brand_data["name"],
                domain=brand_data.get("domain"),
                ad_count=brand_data.get("ad_count", 0),
                platforms=brand_data.get("platforms", []),
                tracking_since=datetime.fromisoformat(
                    brand_data.get("tracking_since", datetime.now().isoformat())
                )
            ))

        return brands

    async def get_brand_ads(
        self,
        brand_id: str,
        page: int = 1,
        per_page: int = 50,
        display_formats: List[str] = None,
        sort: SortOrder = SortOrder.NEWEST
    ) -> List[ForeplayAd]:
        """
        Get ads for a tracked brand.

        API: GET /api/spyder/brand/ads

        Args:
            brand_id: Brand identifier
            page: Page number
            per_page: Results per page
            display_formats: Filter formats
            sort: Sort order

        Returns:
            Brand's ads
        """
        params = {
            "brand_id": brand_id,
            "page": page,
            "per_page": min(per_page, 100),
            "sort": sort.value
        }

        if display_formats:
            params["display_formats"] = ",".join(display_formats)

        response = await self._request("GET", "/api/spyder/brand/ads", params=params)

        ads = []
        for ad_data in response.get("data", response.get("ads", [])):
            ad = self._parse_ad(ad_data, source="brand")
            if ad:
                ads.append(ad)

        return ads

    async def get_brand_analytics(self, brand_id: str) -> BrandAnalytics:
        """
        Get analytics for a tracked brand.

        API: GET /api/brand/analytics

        Args:
            brand_id: Brand identifier

        Returns:
            Brand analytics data
        """
        response = await self._request(
            "GET",
            "/api/brand/analytics",
            params={"brand_id": brand_id}
        )

        data = response.get("data", response)
        return BrandAnalytics(
            brand_id=brand_id,
            total_ads=data.get("total_ads", 0),
            active_ads=data.get("active_ads", 0),
            avg_running_duration=data.get("avg_running_duration", 0),
            top_formats=data.get("top_formats", {}),
            top_niches=data.get("top_niches", []),
            emotional_breakdown=data.get("emotional_breakdown", {})
        )

    # =========================================================================
    # Pattern Extraction - For Learning System
    # =========================================================================

    def extract_winning_patterns(self, ads: List[ForeplayAd]) -> Dict[str, Any]:
        """
        Extract winning patterns from Foreplay ads.

        This analyzes winning ads and extracts:
        - Hook patterns (from timestamped transcriptions)
        - Emotional drivers (pre-classified by Foreplay)
        - CTA patterns
        - Format performance
        - Niche-specific patterns

        Args:
            ads: List of winning ads

        Returns:
            Extracted patterns for learning system
        """
        patterns = {
            "total_analyzed": len(ads),
            "hooks": [],
            "hook_timings": [],
            "ctas": [],
            "emotional_drivers": {},
            "formats": {},
            "niches": {},
            "avg_running_days": 0,
            "transcription_patterns": [],
            "top_hook_words": {},
            "platforms": {}
        }

        total_running_days = 0

        for ad in ads:
            # Extract hooks from timestamped transcriptions
            if ad.timestamped_transcription:
                hook_segments = [
                    seg for seg in ad.timestamped_transcription
                    if seg.start_time < 3.0  # First 3 seconds
                ]

                if hook_segments:
                    hook_text = " ".join(seg.text for seg in hook_segments)
                    patterns["hooks"].append({
                        "text": hook_text,
                        "timing_ms": int(hook_segments[0].start_time * 1000),
                        "niche": ad.niches[0] if ad.niches else "general",
                        "running_days": ad.running_duration_days,
                        "platform": ad.platform.value
                    })

                    # Extract hook words
                    for word in hook_text.lower().split():
                        if len(word) > 3:
                            patterns["top_hook_words"][word] = patterns["top_hook_words"].get(word, 0) + 1

            # Use full transcription if no timestamps
            elif ad.full_transcription:
                first_sentence = ad.full_transcription.split('.')[0]
                patterns["hooks"].append({
                    "text": first_sentence,
                    "timing_ms": 0,
                    "niche": ad.niches[0] if ad.niches else "general",
                    "running_days": ad.running_duration_days
                })

            # Extract emotional drivers (pre-classified!)
            for driver in ad.emotional_drivers:
                emotion = driver.emotion.lower()
                patterns["emotional_drivers"][emotion] = patterns["emotional_drivers"].get(emotion, 0) + 1

            # Extract CTAs
            if ad.cta_text:
                patterns["ctas"].append({
                    "text": ad.cta_text,
                    "niche": ad.niches[0] if ad.niches else "general"
                })

            # Count formats
            format_name = ad.display_format.value
            patterns["formats"][format_name] = patterns["formats"].get(format_name, 0) + 1

            # Count niches
            for niche in ad.niches:
                patterns["niches"][niche] = patterns["niches"].get(niche, 0) + 1

            # Count platforms
            patterns["platforms"][ad.platform.value] = patterns["platforms"].get(ad.platform.value, 0) + 1

            # Running days
            total_running_days += ad.running_duration_days

        # Calculate averages
        if ads:
            patterns["avg_running_days"] = total_running_days / len(ads)

        # Sort top patterns
        patterns["top_emotions"] = sorted(
            patterns["emotional_drivers"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        patterns["top_niches"] = sorted(
            patterns["niches"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        patterns["top_hook_words"] = sorted(
            patterns["top_hook_words"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:50]

        logger.info(f"Extracted patterns from {len(ads)} winning ads")
        return patterns

    def get_hooks_by_niche(
        self,
        ads: List[ForeplayAd],
        niche: str,
        min_running_days: int = 14
    ) -> List[Dict[str, Any]]:
        """
        Get top hooks for a specific niche.

        Args:
            ads: List of ads to analyze
            niche: Niche to filter (e.g., "fitness", "ecommerce")
            min_running_days: Minimum days running

        Returns:
            List of hook patterns for the niche
        """
        hooks = []

        for ad in ads:
            if ad.running_duration_days < min_running_days:
                continue

            if niche.lower() not in [n.lower() for n in ad.niches]:
                continue

            hook_text = ""
            if ad.timestamped_transcription:
                hook_segments = [s for s in ad.timestamped_transcription if s.start_time < 3.0]
                hook_text = " ".join(s.text for s in hook_segments)
            elif ad.full_transcription:
                hook_text = ad.full_transcription.split('.')[0]
            elif ad.hook_text:
                hook_text = ad.hook_text

            if hook_text:
                hooks.append({
                    "text": hook_text,
                    "running_days": ad.running_duration_days,
                    "format": ad.display_format.value,
                    "emotions": [d.emotion for d in ad.emotional_drivers],
                    "advertiser": ad.advertiser_name
                })

        # Sort by running days (longer = more proven)
        hooks.sort(key=lambda x: x["running_days"], reverse=True)
        return hooks[:50]

    # =========================================================================
    # Integration with Learning System
    # =========================================================================

    async def sync_to_patterns_db(
        self,
        ads: List[ForeplayAd],
        patterns_db
    ) -> int:
        """
        Sync extracted patterns to winning_patterns_db.

        Args:
            ads: Winning ads to sync
            patterns_db: WinningPatternsDB instance

        Returns:
            Number of patterns synced
        """
        patterns = self.extract_winning_patterns(ads)
        synced = 0

        # Sync hooks with timing data
        for hook in patterns["hooks"]:
            await patterns_db.add_hook_pattern(
                text=hook["text"],
                hook_type="timestamped",
                industry=hook["niche"],
                timing_ms=hook.get("timing_ms", 0),
                running_days=hook.get("running_days", 0),
                source="foreplay"
            )
            synced += 1

        # Sync CTAs
        for cta in patterns["ctas"]:
            await patterns_db.add_cta_pattern(
                text=cta["text"],
                industry=cta["niche"],
                source="foreplay"
            )
            synced += 1

        # Sync emotional driver weights
        for emotion, count in patterns["emotional_drivers"].items():
            await patterns_db.update_emotion_weight(
                emotion=emotion,
                weight=count / len(ads),  # Normalize
                source="foreplay"
            )

        logger.info(f"Synced {synced} patterns to database from Foreplay")
        return synced

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_ad(self, data: Dict, source: str = "api") -> Optional[ForeplayAd]:
        """Parse API response to ForeplayAd dataclass"""
        try:
            # Parse timestamped transcription
            timestamped = []
            if data.get("timestamped_transcription"):
                for segment in data["timestamped_transcription"]:
                    timestamped.append(TimestampedTranscription(
                        start_time=float(segment.get("start", segment.get("start_time", 0))),
                        end_time=float(segment.get("end", segment.get("end_time", 0))),
                        text=segment.get("text", "")
                    ))

            # Parse emotional drivers
            emotional_drivers = []
            if data.get("emotional_drivers"):
                for driver in data["emotional_drivers"]:
                    if isinstance(driver, str):
                        emotional_drivers.append(EmotionalDriver(
                            emotion=driver,
                            intensity=0.8,
                            keywords=[]
                        ))
                    else:
                        emotional_drivers.append(EmotionalDriver(
                            emotion=driver.get("emotion", driver.get("name", "unknown")),
                            intensity=float(driver.get("intensity", driver.get("score", 0.8))),
                            keywords=driver.get("keywords", [])
                        ))

            # Parse display format
            format_str = data.get("display_format", data.get("format", "video")).lower()
            try:
                display_format = DisplayFormat(format_str)
            except ValueError:
                display_format = DisplayFormat.VIDEO

            # Parse platform
            platform_str = data.get("platform", "meta").lower()
            try:
                platform = Platform(platform_str)
            except ValueError:
                platform = Platform.META

            # Calculate running duration
            first_seen = data.get("first_seen", data.get("created_at"))
            last_seen = data.get("last_seen", data.get("updated_at"))

            if first_seen:
                first_dt = datetime.fromisoformat(first_seen.replace("Z", "+00:00"))
                if last_seen:
                    last_dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
                else:
                    last_dt = datetime.now(first_dt.tzinfo) if first_dt.tzinfo else datetime.now()
                running_days = (last_dt - first_dt).days
            else:
                running_days = data.get("running_duration_days", data.get("running_days", 0))
                first_dt = datetime.now()
                last_dt = None

            # Extract hook from transcription or primary text
            hook_text = ""
            hook_timing = 0
            if timestamped:
                hook_segments = [s for s in timestamped if s.start_time < 3.0]
                if hook_segments:
                    hook_text = " ".join(s.text for s in hook_segments)
                    hook_timing = int(hook_segments[0].start_time * 1000)
            elif data.get("full_transcription"):
                hook_text = data["full_transcription"].split('.')[0]
            else:
                primary = data.get("primary_text", "")
                hook_text = primary.split('\n')[0] if primary else ""

            return ForeplayAd(
                id=str(data.get("id", data.get("_id", hashlib.md5(str(data).encode()).hexdigest()[:16]))),
                external_id=data.get("external_id", data.get("ad_id")),
                advertiser_name=data.get("advertiser_name", data.get("page_name", data.get("advertiser", "Unknown"))),
                advertiser_id=data.get("advertiser_id", data.get("page_id")),
                page_profile_picture_url=data.get("page_profile_picture_url"),
                display_format=display_format,
                media_url=data.get("media_url", data.get("video_url")),
                thumbnail_url=data.get("thumbnail_url", data.get("image_url")),
                video_duration=float(data.get("video_duration", 0)) if data.get("video_duration") else None,
                headline=data.get("headline", ""),
                primary_text=data.get("primary_text", data.get("body", "")),
                cta_text=data.get("cta_text", data.get("cta", data.get("call_to_action", ""))),
                description=data.get("description"),
                landing_page_url=data.get("landing_page_url", data.get("link")),
                full_transcription=data.get("full_transcription", data.get("transcription")),
                timestamped_transcription=timestamped,
                emotional_drivers=emotional_drivers,
                running_duration_days=running_days,
                first_seen=first_dt,
                last_seen=datetime.fromisoformat(last_seen.replace("Z", "+00:00")) if last_seen else None,
                is_active=data.get("is_active", True),
                niches=data.get("niches", data.get("niche", ["general"])) if isinstance(data.get("niches", data.get("niche")), list) else [data.get("niches", data.get("niche", "general"))],
                market_target=data.get("market_target"),
                languages=data.get("languages", [data.get("language", "en")]) if isinstance(data.get("languages"), list) else [data.get("languages", "en")],
                platform=platform,
                boards=data.get("boards", []),
                tags=data.get("tags", []),
                notes=data.get("notes"),
                saved_at=datetime.fromisoformat(data["saved_at"].replace("Z", "+00:00")) if data.get("saved_at") else None,
                hook_text=hook_text,
                hook_timing_ms=hook_timing,
                patterns=self._extract_ad_patterns(data)
            )

        except Exception as e:
            logger.warning(f"Failed to parse ad: {e}")
            return None

    def _extract_ad_patterns(self, data: Dict) -> Dict[str, Any]:
        """Extract additional patterns from ad data"""
        primary_text = str(data.get("primary_text", ""))
        return {
            "has_emoji": any(ord(c) > 127 for c in primary_text),
            "has_hashtags": "#" in primary_text,
            "has_url": "http" in primary_text.lower(),
            "text_length": len(primary_text),
            "headline_length": len(data.get("headline", "")),
            "has_numbers_in_hook": any(c.isdigit() for c in primary_text[:50]),
            "has_question": "?" in primary_text[:100],
            "cta_type": self._classify_cta(data.get("cta_text", ""))
        }

    def _classify_cta(self, cta: str) -> str:
        """Classify CTA type"""
        cta_lower = cta.lower()

        if any(w in cta_lower for w in ["shop", "buy", "order", "get"]):
            return "purchase"
        elif any(w in cta_lower for w in ["learn", "read", "discover"]):
            return "learn"
        elif any(w in cta_lower for w in ["sign", "subscribe", "join"]):
            return "signup"
        elif any(w in cta_lower for w in ["download", "install"]):
            return "download"
        elif any(w in cta_lower for w in ["watch", "see", "view"]):
            return "watch"
        elif any(w in cta_lower for w in ["contact", "call", "message"]):
            return "contact"
        else:
            return "other"


# =============================================================================
# Convenience Functions
# =============================================================================

async def get_foreplay_winners(
    api_key: str = None,
    niche: str = None,
    min_running_days: int = 30,
    max_ads: int = 500
) -> List[ForeplayAd]:
    """
    Quick function to get proven winners from Foreplay.

    Args:
        api_key: Foreplay API key
        niche: Filter by niche
        min_running_days: Minimum days running (30+ recommended)
        max_ads: Maximum ads to retrieve

    Returns:
        List of proven winner ads
    """
    client = ForeplayIntegration(api_key)
    await client.connect()

    niches = [niche] if niche else None
    ads = await client.get_long_running_winners(
        min_days=min_running_days,
        niches=niches,
        max_ads=max_ads
    )

    await client.disconnect()
    return ads


async def analyze_competitor_brand(
    api_key: str,
    brand_id: str
) -> Dict[str, Any]:
    """
    Analyze a competitor brand's ad strategy.

    Args:
        api_key: Foreplay API key
        brand_id: Brand to analyze

    Returns:
        Brand analysis with patterns
    """
    client = ForeplayIntegration(api_key)
    await client.connect()

    # Get brand ads and analytics
    ads = await client.get_brand_ads(brand_id, per_page=100)
    analytics = await client.get_brand_analytics(brand_id)

    # Extract patterns
    patterns = client.extract_winning_patterns(ads)

    await client.disconnect()

    return {
        "analytics": asdict(analytics),
        "patterns": patterns,
        "total_ads_analyzed": len(ads)
    }
