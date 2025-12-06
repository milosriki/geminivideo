"""
Meta Ad Library Scraper - Our Own Data Collection

Scrapes PUBLIC data from Meta Ad Library (no login required).
Dubai jurisdiction - public data scraping is legal.

Key insight from Foreplay:
- running_duration_days > 30 = proven winner
- timestamped_transcription = hook analysis
- emotional_drivers = pre-classified (we do with Llama 4)

This replaces Foreplay dependency over time.
"""

import os
import json
import asyncio
import hashlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import aiohttp
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# Data Models (Matching Foreplay structure for easy migration)
# =============================================================================

class Platform(Enum):
    META = "meta"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"


class MediaType(Enum):
    VIDEO = "video"
    IMAGE = "image"
    CAROUSEL = "carousel"


@dataclass
class ScrapedAd:
    """
    Ad from Meta Ad Library

    Structure matches Foreplay's ForeplayAd for easy data migration
    """
    # Identifiers
    id: str
    ad_archive_id: str
    page_id: str
    page_name: str

    # Creative
    media_type: MediaType
    media_url: str
    media_hash: str  # SHA-256 for deduplication
    thumbnail_url: str

    # Copy
    body_text: str
    headline: str
    link_caption: str
    link_description: str
    cta_type: str
    landing_page_url: str

    # Timing (KEY - longer running = winner)
    first_seen: datetime
    last_seen: datetime
    running_duration_days: int
    is_active: bool

    # Platform info
    platform: Platform = Platform.META
    platforms_shown: List[str] = field(default_factory=list)  # fb, ig, messenger

    # Geographic
    countries: List[str] = field(default_factory=list)

    # AI Enriched (filled by enrichment pipeline)
    transcript: Optional[str] = None
    timestamped_transcription: List[Dict] = field(default_factory=list)
    emotional_drivers: List[str] = field(default_factory=list)
    product_category: Optional[str] = None
    hook_text: Optional[str] = None
    hook_type: Optional[str] = None
    winning_patterns: List[str] = field(default_factory=list)

    # Storage
    local_media_path: Optional[str] = None
    indexed_at: Optional[datetime] = None


@dataclass
class BrandProfile:
    """Brand tracking profile"""
    page_id: str
    page_name: str
    total_ads: int
    active_ads: int
    avg_running_days: float
    creative_velocity: float  # ads per day
    top_patterns: List[str]
    platforms: List[str]
    last_checked: datetime
    tracking_since: datetime


# =============================================================================
# Meta Ad Library Scraper
# =============================================================================

class MetaAdLibraryScraper:
    """
    Scrapes Meta Ad Library (PUBLIC data - no auth needed)

    Strategy:
    1. Use Meta's Graph API for ad library (limited but legal)
    2. Fallback: Browser automation with Playwright
    3. Track ad longevity for winner detection

    Key learnings from Foreplay:
    - They intercept GraphQL responses from the ad library page
    - They track first_seen/last_seen to calculate running_duration
    - Ads running 30+ days are statistically winners
    """

    # Meta Ad Library API (for political/social issue ads - limited)
    AD_LIBRARY_API = "https://graph.facebook.com/v18.0/ads_archive"

    # Ad Library web interface (for browser scraping)
    AD_LIBRARY_WEB = "https://www.facebook.com/ads/library/"

    def __init__(
        self,
        access_token: str = None,
        storage_path: str = None,
        proxy_url: str = None
    ):
        """
        Initialize scraper.

        Args:
            access_token: Meta access token (for API access)
            storage_path: Where to store downloaded media
            proxy_url: Residential proxy for scraping
        """
        self.access_token = access_token or os.getenv("META_ACCESS_TOKEN")
        self.storage_path = storage_path or "/home/user/geminivideo/data/ads"
        self.proxy_url = proxy_url or os.getenv("PROXY_URL")

        # Ensure storage exists
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)

        # Cache for deduplication
        self._seen_hashes: set = set()

    async def search_ads(
        self,
        search_term: str = None,
        page_id: str = None,
        ad_type: str = "ALL",  # ALL, POLITICAL_AND_ISSUE_ADS
        country: str = "AE",  # UAE
        limit: int = 100
    ) -> List[ScrapedAd]:
        """
        Search ads via Meta Ad Library API.

        Note: Full API access requires approved app.
        For now, we get what's publicly available.
        """
        params = {
            "access_token": self.access_token,
            "ad_type": ad_type,
            "ad_reached_countries": country,
            "limit": min(limit, 100),
            "fields": ",".join([
                "id",
                "ad_archive_id",
                "page_id",
                "page_name",
                "ad_creative_bodies",
                "ad_creative_link_captions",
                "ad_creative_link_descriptions",
                "ad_creative_link_titles",
                "ad_delivery_start_time",
                "ad_delivery_stop_time",
                "bylines",
                "currency",
                "estimated_audience_size",
                "impressions",
                "languages",
                "publisher_platforms",
                "spend"
            ])
        }

        if search_term:
            params["search_terms"] = search_term
        if page_id:
            params["search_page_ids"] = page_id

        ads = []

        async with aiohttp.ClientSession() as session:
            async with session.get(self.AD_LIBRARY_API, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for ad_data in data.get("data", []):
                        ad = self._parse_api_ad(ad_data)
                        if ad:
                            ads.append(ad)
                    logger.info(f"Found {len(ads)} ads via API")
                else:
                    error = await resp.text()
                    logger.warning(f"API error {resp.status}: {error}")
                    # Fall back to browser scraping

        return ads

    async def scrape_brand_page(
        self,
        page_name: str,
        page_id: str = None,
        max_ads: int = 100
    ) -> List[ScrapedAd]:
        """
        Scrape all ads for a brand using browser automation.

        This is the Playwright-based approach (like Foreplay's Spyder).
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed. Run: pip install playwright && playwright install")
            return []

        ads = []
        captured_responses = []

        async with async_playwright() as p:
            # Launch browser with stealth
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-infobars',
                ]
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
            )

            # Inject stealth scripts
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)

            page = await context.new_page()

            # Capture XHR/GraphQL responses
            async def capture_response(response):
                if 'graphql' in response.url or 'ads_archive' in response.url:
                    try:
                        data = await response.json()
                        captured_responses.append(data)
                    except:
                        pass

            page.on('response', capture_response)

            # Build URL
            url = f"{self.AD_LIBRARY_WEB}?active_status=all&ad_type=all&country=ALL&q={page_name}"

            await page.goto(url, wait_until='networkidle')
            await asyncio.sleep(3)  # Wait for initial load

            # Scroll to load more
            scroll_count = 0
            while len(captured_responses) < max_ads and scroll_count < 20:
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(2)
                scroll_count += 1

            await browser.close()

        # Parse captured responses
        for response_data in captured_responses:
            parsed = self._parse_graphql_response(response_data)
            ads.extend(parsed)

        # Deduplicate
        unique_ads = self._deduplicate_ads(ads)

        logger.info(f"Scraped {len(unique_ads)} unique ads for {page_name}")
        return unique_ads[:max_ads]

    async def download_media(self, ad: ScrapedAd) -> str:
        """
        Download media file for permanent storage.

        Returns local file path.
        """
        if not ad.media_url:
            return ""

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ad.media_url) as resp:
                    if resp.status == 200:
                        content = await resp.read()

                        # Calculate hash for deduplication
                        file_hash = hashlib.sha256(content).hexdigest()

                        # Check if already downloaded
                        if file_hash in self._seen_hashes:
                            logger.debug(f"Duplicate media skipped: {file_hash[:16]}")
                            return ""

                        self._seen_hashes.add(file_hash)

                        # Determine extension
                        ext = 'mp4' if ad.media_type == MediaType.VIDEO else 'jpg'

                        # Save file
                        filename = f"{file_hash[:16]}.{ext}"
                        filepath = f"{self.storage_path}/{filename}"

                        with open(filepath, 'wb') as f:
                            f.write(content)

                        ad.media_hash = file_hash
                        ad.local_media_path = filepath

                        logger.info(f"Downloaded: {filepath}")
                        return filepath

        except Exception as e:
            logger.error(f"Download failed: {e}")

        return ""

    def _parse_api_ad(self, data: Dict) -> Optional[ScrapedAd]:
        """Parse Meta Ad Library API response"""
        try:
            # Calculate running duration
            start_time = data.get('ad_delivery_start_time')
            stop_time = data.get('ad_delivery_stop_time')

            if start_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                if stop_time:
                    end_dt = datetime.fromisoformat(stop_time.replace('Z', '+00:00'))
                    is_active = False
                else:
                    end_dt = datetime.now(start_dt.tzinfo) if start_dt.tzinfo else datetime.now()
                    is_active = True

                running_days = (end_dt - start_dt).days
            else:
                start_dt = datetime.now()
                running_days = 0
                is_active = True

            # Extract body text
            bodies = data.get('ad_creative_bodies', [])
            body_text = bodies[0] if bodies else ""

            # Extract headline
            titles = data.get('ad_creative_link_titles', [])
            headline = titles[0] if titles else ""

            return ScrapedAd(
                id=data.get('id', ''),
                ad_archive_id=data.get('ad_archive_id', ''),
                page_id=data.get('page_id', ''),
                page_name=data.get('page_name', ''),
                media_type=MediaType.IMAGE,  # API doesn't provide media directly
                media_url="",
                media_hash="",
                thumbnail_url="",
                body_text=body_text,
                headline=headline,
                link_caption=data.get('ad_creative_link_captions', [''])[0] if data.get('ad_creative_link_captions') else "",
                link_description=data.get('ad_creative_link_descriptions', [''])[0] if data.get('ad_creative_link_descriptions') else "",
                cta_type="",
                landing_page_url="",
                first_seen=start_dt,
                last_seen=end_dt if not is_active else datetime.now(),
                running_duration_days=running_days,
                is_active=is_active,
                platforms_shown=data.get('publisher_platforms', []),
                countries=data.get('ad_reached_countries', []),
            )

        except Exception as e:
            logger.warning(f"Failed to parse ad: {e}")
            return None

    def _parse_graphql_response(self, data: Dict) -> List[ScrapedAd]:
        """Parse GraphQL response from browser scraping"""
        ads = []

        # Navigate nested structure (Meta changes this frequently)
        try:
            # Try different response structures
            results = []

            if 'data' in data:
                data = data['data']

            # Look for ad results in various locations
            for key in ['ad_library_main', 'ads_archive', 'search_results', 'results']:
                if key in data:
                    container = data[key]
                    if isinstance(container, dict):
                        results = container.get('results', container.get('ads', []))
                    elif isinstance(container, list):
                        results = container
                    break

            for ad_data in results:
                ad = self._parse_graphql_ad(ad_data)
                if ad:
                    ads.append(ad)

        except Exception as e:
            logger.warning(f"GraphQL parse error: {e}")

        return ads

    def _parse_graphql_ad(self, data: Dict) -> Optional[ScrapedAd]:
        """Parse single ad from GraphQL response"""
        try:
            snapshot = data.get('snapshot', data)

            # Determine media type and URL
            media_type = MediaType.IMAGE
            media_url = ""
            thumbnail_url = ""

            if snapshot.get('videos'):
                media_type = MediaType.VIDEO
                video = snapshot['videos'][0]
                media_url = video.get('video_hd_url') or video.get('video_sd_url', '')
                thumbnail_url = video.get('video_preview_image_url', '')
            elif snapshot.get('images'):
                media_url = snapshot['images'][0].get('url', '')
                thumbnail_url = media_url
            elif snapshot.get('cards'):
                media_type = MediaType.CAROUSEL
                card = snapshot['cards'][0]
                media_url = card.get('video_url') or card.get('image_url', '')

            # Calculate running duration
            start_ts = data.get('ad_delivery_start_time', 0)
            stop_ts = data.get('ad_delivery_stop_time')

            if start_ts:
                start_dt = datetime.fromtimestamp(start_ts)
                if stop_ts:
                    end_dt = datetime.fromtimestamp(stop_ts)
                    is_active = False
                else:
                    end_dt = datetime.now()
                    is_active = True
                running_days = (end_dt - start_dt).days
            else:
                start_dt = datetime.now()
                end_dt = datetime.now()
                running_days = 0
                is_active = data.get('is_active', True)

            # Extract text
            body = snapshot.get('body', {})
            body_text = body.get('text', '') if isinstance(body, dict) else str(body)

            return ScrapedAd(
                id=data.get('ad_id', data.get('id', '')),
                ad_archive_id=data.get('ad_archive_id', ''),
                page_id=data.get('page_id', ''),
                page_name=data.get('page_name', ''),
                media_type=media_type,
                media_url=media_url,
                media_hash="",
                thumbnail_url=thumbnail_url,
                body_text=body_text,
                headline=snapshot.get('title', ''),
                link_caption=snapshot.get('link_caption', ''),
                link_description=snapshot.get('link_description', ''),
                cta_type=snapshot.get('cta_type', ''),
                landing_page_url=snapshot.get('link_url', ''),
                first_seen=start_dt,
                last_seen=end_dt,
                running_duration_days=running_days,
                is_active=is_active,
                platforms_shown=data.get('publisher_platforms', ['facebook']),
            )

        except Exception as e:
            logger.warning(f"Failed to parse GraphQL ad: {e}")
            return None

    def _deduplicate_ads(self, ads: List[ScrapedAd]) -> List[ScrapedAd]:
        """Remove duplicate ads by ID"""
        seen_ids = set()
        unique = []

        for ad in ads:
            if ad.id and ad.id not in seen_ids:
                seen_ids.add(ad.id)
                unique.append(ad)

        return unique


# =============================================================================
# Brand Tracker (Like Foreplay Spyder)
# =============================================================================

class BrandTracker:
    """
    Track brands and monitor for new ads.

    Like Foreplay's "Spyder" - automated brand monitoring.
    """

    def __init__(self, scraper: MetaAdLibraryScraper, db=None):
        self.scraper = scraper
        self.db = db  # Database connection
        self.tracked_brands: Dict[str, BrandProfile] = {}

    async def add_brand(self, page_name: str, page_id: str = None):
        """Add brand to tracking"""
        profile = BrandProfile(
            page_id=page_id or "",
            page_name=page_name,
            total_ads=0,
            active_ads=0,
            avg_running_days=0,
            creative_velocity=0,
            top_patterns=[],
            platforms=[],
            last_checked=datetime.now(),
            tracking_since=datetime.now()
        )

        self.tracked_brands[page_name] = profile

        # Initial scrape
        await self.check_brand(page_name)

        logger.info(f"Now tracking: {page_name}")

    async def check_brand(self, page_name: str) -> List[ScrapedAd]:
        """Check brand for new ads"""
        if page_name not in self.tracked_brands:
            await self.add_brand(page_name)

        ads = await self.scraper.scrape_brand_page(page_name)

        # Update profile
        profile = self.tracked_brands[page_name]
        profile.total_ads = len(ads)
        profile.active_ads = sum(1 for a in ads if a.is_active)
        profile.avg_running_days = sum(a.running_duration_days for a in ads) / len(ads) if ads else 0
        profile.last_checked = datetime.now()

        # Calculate creative velocity (ads per day over last 30 days)
        recent_ads = [a for a in ads if a.first_seen > datetime.now() - timedelta(days=30)]
        profile.creative_velocity = len(recent_ads) / 30

        return ads

    async def check_all_brands(self) -> Dict[str, List[ScrapedAd]]:
        """Check all tracked brands"""
        results = {}

        for page_name in self.tracked_brands:
            try:
                ads = await self.check_brand(page_name)
                results[page_name] = ads
                await asyncio.sleep(2)  # Rate limiting
            except Exception as e:
                logger.error(f"Failed to check {page_name}: {e}")

        return results

    def get_profile(self, page_name: str) -> Optional[BrandProfile]:
        """Get brand profile"""
        return self.tracked_brands.get(page_name)

    def get_high_velocity_brands(self, min_velocity: float = 0.5) -> List[BrandProfile]:
        """Get brands launching ads frequently"""
        return [
            p for p in self.tracked_brands.values()
            if p.creative_velocity >= min_velocity
        ]


# =============================================================================
# Winner Detection (Key Feature)
# =============================================================================

class WinnerDetector:
    """
    Detect winning ads based on longevity.

    Key insight from Foreplay:
    - Ads running 30+ days are statistically profitable
    - Brands don't keep unprofitable ads running
    - Longer running = more confident it's a winner
    """

    MIN_WINNER_DAYS = 30

    def __init__(self, ads: List[ScrapedAd] = None):
        self.ads = ads or []

    def get_winners(self, min_days: int = None) -> List[ScrapedAd]:
        """Get ads running longer than threshold"""
        threshold = min_days or self.MIN_WINNER_DAYS

        winners = [
            ad for ad in self.ads
            if ad.running_duration_days >= threshold and ad.is_active
        ]

        # Sort by running duration (longest first)
        winners.sort(key=lambda a: a.running_duration_days, reverse=True)

        return winners

    def get_winners_by_category(
        self,
        category: str,
        min_days: int = None
    ) -> List[ScrapedAd]:
        """Get winners in a specific category"""
        winners = self.get_winners(min_days)
        return [w for w in winners if w.product_category == category]

    def calculate_winner_score(self, ad: ScrapedAd) -> float:
        """
        Calculate a "winner score" based on multiple signals.

        Score 0-100 where:
        - 30+ days running = base 50
        - Each additional 10 days = +10
        - Active status = +10
        - Has video = +10
        - Multiple platforms = +5 each
        """
        score = 0

        # Running duration (main signal)
        if ad.running_duration_days >= 30:
            score += 50
            score += min(40, (ad.running_duration_days - 30) // 10 * 10)
        elif ad.running_duration_days >= 14:
            score += 30
        elif ad.running_duration_days >= 7:
            score += 15

        # Active status
        if ad.is_active:
            score += 10

        # Video format (typically higher intent)
        if ad.media_type == MediaType.VIDEO:
            score += 10

        # Multi-platform (more investment)
        platform_count = len(ad.platforms_shown)
        score += min(15, platform_count * 5)

        return min(100, score)

    def rank_ads_by_score(self) -> List[tuple]:
        """Rank all ads by winner score"""
        scored = [(ad, self.calculate_winner_score(ad)) for ad in self.ads]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored


# =============================================================================
# Convenience Functions
# =============================================================================

async def scrape_brand(page_name: str, max_ads: int = 100) -> List[ScrapedAd]:
    """Quick function to scrape a brand"""
    scraper = MetaAdLibraryScraper()
    return await scraper.scrape_brand_page(page_name, max_ads=max_ads)


async def find_winners(
    page_name: str = None,
    category: str = None,
    min_days: int = 30
) -> List[ScrapedAd]:
    """Find winning ads for a brand or category"""
    scraper = MetaAdLibraryScraper()

    if page_name:
        ads = await scraper.scrape_brand_page(page_name, max_ads=200)
    else:
        # Would search across database
        ads = []

    detector = WinnerDetector(ads)

    if category:
        return detector.get_winners_by_category(category, min_days)
    else:
        return detector.get_winners(min_days)


def to_foreplay_format(ad: ScrapedAd) -> Dict:
    """
    Convert our ad format to match Foreplay's structure.

    This allows easy integration with existing code that expects
    Foreplay's data structure.

    IMPORTANT: Field names must match what AdDocument.from_enriched_ad() expects:
    - ad_id (not id)
    - brand_name (not advertiser_name)
    - format (not display_format)
    """
    return {
        # Core identifiers - MUST match AdDocument schema
        "ad_id": ad.id,
        "brand_name": ad.page_name,
        "brand_id": ad.page_id,
        "platform": ad.platform.value,
        "format": ad.media_type.value,

        # Media
        "video_url": ad.media_url,
        "thumbnail_url": ad.thumbnail_url,

        # Copy
        "headline": ad.headline,
        "body_text": ad.body_text,
        "cta": ad.cta_type,
        "landing_page_url": ad.landing_page_url,

        # Transcription
        "transcription": ad.transcript,

        # AI Analysis (will be populated by enrichment)
        "emotional_drivers": ad.emotional_drivers or [],
        "hook_text": ad.hook_text,
        "winning_patterns": ad.winning_patterns or [],

        # Timing
        "running_duration_days": ad.running_duration_days,
        "first_seen": ad.first_seen,
        "last_seen": ad.last_seen,
        "is_active": ad.is_active,

        # Classification
        "industry": ad.product_category,
    }
