"""
Creatify AI Integration - URL-to-Video & UGC Performance

Creatify is an AI-powered video creation platform.
API Documentation: https://docs.creatify.ai/

Key Features:
1. URL-to-Video: Generate video ads from product URLs
2. AI Avatars: Digital spokesperson creation
3. Script Generation: AI-powered ad scripts
4. UGC Performance Data: Creator analytics

Connection: API Key (X-API-ID and X-API-KEY headers)
Base URL: https://api.creatify.ai/api/
"""

import os
import json
import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import aiohttp

logger = logging.getLogger(__name__)


# =============================================================================
# URL-to-Video Feature Classes (Creatify AI)
# =============================================================================

class VideoAspectRatio(Enum):
    """Supported aspect ratios"""
    PORTRAIT_9_16 = "9:16"  # TikTok, Reels, Stories
    LANDSCAPE_16_9 = "16:9"  # YouTube
    SQUARE_1_1 = "1:1"  # Feed posts


class VideoStyle(Enum):
    """AI video generation styles"""
    UGC = "ugc"  # User-generated style
    PROFESSIONAL = "professional"
    TESTIMONIAL = "testimonial"
    PRODUCT_DEMO = "product_demo"
    LIFESTYLE = "lifestyle"


@dataclass
class URLAnalysis:
    """Result of analyzing a product URL"""
    url: str
    product_name: str
    product_description: str
    product_images: List[str]
    price: Optional[str]
    brand: Optional[str]
    key_features: List[str]
    suggested_hooks: List[str]


@dataclass
class GeneratedScript:
    """AI-generated video script"""
    id: str
    hook: str
    body: str
    cta: str
    full_script: str
    duration_estimate: int  # seconds
    tone: str
    style: str


@dataclass
class AIAvatar:
    """AI Avatar/Spokesperson"""
    id: str
    name: str
    gender: str
    age_range: str
    ethnicity: str
    preview_url: str
    voice_id: Optional[str]


@dataclass
class VideoGenerationJob:
    """URL-to-Video generation job"""
    id: str
    status: str  # pending, processing, completed, failed
    url: str
    script: Optional[GeneratedScript]
    avatar: Optional[AIAvatar]
    aspect_ratio: VideoAspectRatio
    output_url: Optional[str]
    thumbnail_url: Optional[str]
    duration: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
    error: Optional[str]


@dataclass
class LipsyncJob:
    """Lipsync generation job"""
    id: str
    status: str
    input_video_url: str
    audio_url: str
    output_url: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]


class CreatorStyle(Enum):
    TALKING_HEAD = "talking_head"
    TESTIMONIAL = "testimonial"
    UNBOXING = "unboxing"
    TUTORIAL = "tutorial"
    LIFESTYLE = "lifestyle"
    BEFORE_AFTER = "before_after"
    REACTION = "reaction"
    REVIEW = "review"


class VoiceTone(Enum):
    ENTHUSIASTIC = "enthusiastic"
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    URGENT = "urgent"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"


@dataclass
class CreatorVideo:
    """UGC video from Creatorify"""
    id: str
    title: str
    creator_id: str
    creator_name: str

    # Style
    style: CreatorStyle
    tone: VoiceTone
    duration_seconds: int

    # Script
    script: str
    hook: str
    cta: str

    # Performance (if available)
    views: Optional[int]
    engagement_rate: Optional[float]
    click_rate: Optional[float]
    conversion_rate: Optional[float]

    # Assets
    video_url: Optional[str]
    thumbnail_url: Optional[str]

    # Metadata
    industry: str
    product_type: str
    created_at: datetime
    tags: List[str]


@dataclass
class CreatorProfile:
    """Creator profile from Creatorify"""
    id: str
    name: str
    avatar_url: Optional[str]

    # Stats
    total_videos: int
    avg_engagement: float
    avg_conversion: float

    # Specialties
    styles: List[CreatorStyle]
    industries: List[str]
    tones: List[VoiceTone]

    # Pricing
    price_per_video: Optional[float]


@dataclass
class ScriptTemplate:
    """UGC script template"""
    id: str
    name: str
    style: CreatorStyle
    industry: str

    # Structure
    hook_template: str
    body_template: str
    cta_template: str

    # Timing
    hook_duration: int  # seconds
    body_duration: int
    cta_duration: int

    # Performance
    avg_engagement: float
    usage_count: int


class CreatifyIntegration:
    """
    Creatify AI API Integration

    Features:
    1. URL-to-Video: Generate video ads from product URLs
    2. AI Avatars: Digital spokespersons
    3. Script Generation: AI ad scripts
    4. Lipsync: Add voice to video
    5. UGC Analytics: Performance tracking

    API Docs: https://docs.creatify.ai/
    """

    BASE_URL = "https://api.creatify.ai/api"

    def __init__(
        self,
        api_id: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize Creatify client.

        Args:
            api_id: Creatify API ID (X-API-ID header)
            api_key: Creatify API Key (X-API-KEY header)
        """
        self.api_id = api_id or os.getenv("CREATIFY_API_ID")
        self.api_key = api_key or os.getenv("CREATIFY_API_KEY")
        self.session = None
        self.connected = False
        self._avatars_cache: List[AIAvatar] = []

        if self.api_id and self.api_key:
            logger.info("✅ Creatify API credentials configured")
        else:
            logger.warning("⚠️ CREATIFY_API_ID or CREATIFY_API_KEY not set")

    async def connect(self) -> bool:
        """Test connection to Creatify API"""
        if not self.api_id or not self.api_key:
            logger.error("API ID and API Key required")
            return False

        try:
            self.session = aiohttp.ClientSession(headers={
                "X-API-ID": self.api_id,
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json"
            })

            # Test connection with avatars endpoint
            async with self.session.get(f"{self.BASE_URL}/avatars/") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._avatars_cache = self._parse_avatars(data)
                    logger.info(f"✅ Connected to Creatify API ({len(self._avatars_cache)} avatars available)")
                    self.connected = True
                    return True
                elif resp.status == 401:
                    logger.error("❌ Creatify API: Invalid credentials")
                    return False
                else:
                    error = await resp.text()
                    logger.error(f"❌ Creatify connection failed: {resp.status} - {error}")
                    return False

        except Exception as e:
            logger.error(f"❌ Creatify connection error: {e}")
            return False

    async def disconnect(self):
        """Close connection"""
        if self.session:
            await self.session.close()
            self.session = None
            self.connected = False

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Dict[str, Any]:
        """Make API request with error handling"""
        if not self.session:
            await self.connect()

        if not self.connected:
            raise Exception("Not connected to Creatify API")

        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        try:
            async with self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                response_text = await resp.text()

                if resp.status in [200, 201]:
                    return json.loads(response_text) if response_text else {}
                elif resp.status == 401:
                    raise Exception("Invalid API credentials")
                elif resp.status == 429:
                    raise Exception("Rate limited - slow down")
                else:
                    raise Exception(f"API error {resp.status}: {response_text}")

        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {e}")

    # =========================================================================
    # URL-to-Video Generation (Core Feature)
    # =========================================================================

    async def analyze_url(self, url: str) -> URLAnalysis:
        """
        Analyze a product URL to extract information.

        Step 1 of URL-to-Video: Scrape product details.

        Args:
            url: Product page URL

        Returns:
            Extracted product information
        """
        logger.info(f"Analyzing URL: {url}")

        response = await self._request(
            "POST",
            "link_to_videos/",
            data={"url": url}
        )

        return URLAnalysis(
            url=url,
            product_name=response.get("product_name", ""),
            product_description=response.get("description", ""),
            product_images=response.get("images", []),
            price=response.get("price"),
            brand=response.get("brand"),
            key_features=response.get("features", []),
            suggested_hooks=response.get("suggested_hooks", [])
        )

    async def generate_script(
        self,
        url: str,
        style: VideoStyle = VideoStyle.UGC,
        tone: str = "enthusiastic",
        target_duration: int = 30
    ) -> GeneratedScript:
        """
        Generate AI script from product URL.

        Step 2: Create ad script from product info.

        Args:
            url: Product URL
            style: Video style
            tone: Voice tone
            target_duration: Target video length

        Returns:
            AI-generated script
        """
        logger.info(f"Generating script for: {url}")

        response = await self._request(
            "POST",
            "scripts/",
            data={
                "url": url,
                "style": style.value,
                "tone": tone,
                "target_duration": target_duration
            }
        )

        return GeneratedScript(
            id=response.get("id", ""),
            hook=response.get("hook", ""),
            body=response.get("body", ""),
            cta=response.get("cta", ""),
            full_script=response.get("script", response.get("full_script", "")),
            duration_estimate=response.get("duration", target_duration),
            tone=tone,
            style=style.value
        )

    async def get_avatars(self, refresh: bool = False) -> List[AIAvatar]:
        """
        Get available AI avatars.

        Args:
            refresh: Force refresh cache

        Returns:
            List of available avatars
        """
        if self._avatars_cache and not refresh:
            return self._avatars_cache

        response = await self._request("GET", "avatars/")

        self._avatars_cache = self._parse_avatars(response)
        logger.info(f"Loaded {len(self._avatars_cache)} AI avatars")
        return self._avatars_cache

    async def create_video_from_url(
        self,
        url: str,
        avatar_id: str,
        script: Optional[str] = None,
        aspect_ratio: VideoAspectRatio = VideoAspectRatio.PORTRAIT_9_16,
        style: VideoStyle = VideoStyle.UGC,
        wait_for_completion: bool = True,
        poll_interval: int = 5,
        timeout: int = 300
    ) -> VideoGenerationJob:
        """
        Generate video ad from product URL (Full URL-to-Video flow).

        This is the main method - it:
        1. Analyzes the URL
        2. Generates a script (or uses provided)
        3. Creates video with AI avatar
        4. Returns the completed video

        Args:
            url: Product page URL
            avatar_id: AI avatar to use
            script: Optional custom script (auto-generates if not provided)
            aspect_ratio: Video aspect ratio
            style: Video style
            wait_for_completion: Wait for video to finish
            poll_interval: Seconds between status checks
            timeout: Max seconds to wait

        Returns:
            Video generation job with output URL
        """
        logger.info(f"Creating video from URL: {url}")

        # Create the video generation job
        response = await self._request(
            "POST",
            "link_to_videos/",
            data={
                "url": url,
                "avatar_id": avatar_id,
                "script": script,
                "aspect_ratio": aspect_ratio.value,
                "style": style.value if isinstance(style, VideoStyle) else style
            }
        )

        job_id = response.get("id")
        logger.info(f"Video job created: {job_id}")

        job = VideoGenerationJob(
            id=job_id,
            status="pending",
            url=url,
            script=None,
            avatar=None,
            aspect_ratio=aspect_ratio,
            output_url=None,
            thumbnail_url=None,
            duration=None,
            created_at=datetime.now(),
            completed_at=None,
            error=None
        )

        if not wait_for_completion:
            return job

        # Poll for completion
        return await self._poll_video_job(job_id, poll_interval, timeout)

    async def get_video_status(self, job_id: str) -> VideoGenerationJob:
        """
        Check status of a video generation job.

        Args:
            job_id: Job identifier

        Returns:
            Updated job status
        """
        response = await self._request("GET", f"link_to_videos/{job_id}/")

        return VideoGenerationJob(
            id=job_id,
            status=response.get("status", "unknown"),
            url=response.get("url", ""),
            script=self._parse_script(response.get("script")) if response.get("script") else None,
            avatar=None,
            aspect_ratio=VideoAspectRatio(response.get("aspect_ratio", "9:16")),
            output_url=response.get("output_url", response.get("video_url")),
            thumbnail_url=response.get("thumbnail_url"),
            duration=response.get("duration"),
            created_at=datetime.fromisoformat(response["created_at"]) if response.get("created_at") else datetime.now(),
            completed_at=datetime.fromisoformat(response["completed_at"]) if response.get("completed_at") else None,
            error=response.get("error")
        )

    async def _poll_video_job(
        self,
        job_id: str,
        poll_interval: int,
        timeout: int
    ) -> VideoGenerationJob:
        """Poll video job until completion"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            job = await self.get_video_status(job_id)

            if job.status == "completed":
                logger.info(f"✅ Video completed: {job.output_url}")
                return job
            elif job.status == "failed":
                logger.error(f"❌ Video failed: {job.error}")
                return job
            elif job.status in ["pending", "processing"]:
                logger.info(f"⏳ Video {job.status}... waiting {poll_interval}s")
                await asyncio.sleep(poll_interval)
            else:
                logger.warning(f"Unknown status: {job.status}")
                await asyncio.sleep(poll_interval)

        # Timeout
        job = await self.get_video_status(job_id)
        job.error = "Timeout waiting for video completion"
        return job

    async def batch_create_videos(
        self,
        urls: List[str],
        avatar_id: str,
        aspect_ratio: VideoAspectRatio = VideoAspectRatio.PORTRAIT_9_16,
        max_concurrent: int = 3
    ) -> List[VideoGenerationJob]:
        """
        Create multiple videos in parallel.

        Args:
            urls: List of product URLs
            avatar_id: AI avatar to use
            aspect_ratio: Video aspect ratio
            max_concurrent: Max parallel jobs

        Returns:
            List of video jobs
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def create_with_limit(url: str) -> VideoGenerationJob:
            async with semaphore:
                try:
                    return await self.create_video_from_url(
                        url=url,
                        avatar_id=avatar_id,
                        aspect_ratio=aspect_ratio,
                        wait_for_completion=True
                    )
                except Exception as e:
                    logger.error(f"Failed to create video for {url}: {e}")
                    return VideoGenerationJob(
                        id="",
                        status="failed",
                        url=url,
                        script=None,
                        avatar=None,
                        aspect_ratio=aspect_ratio,
                        output_url=None,
                        thumbnail_url=None,
                        duration=None,
                        created_at=datetime.now(),
                        completed_at=None,
                        error=str(e)
                    )

        tasks = [create_with_limit(url) for url in urls]
        results = await asyncio.gather(*tasks)

        successful = sum(1 for r in results if r.status == "completed")
        logger.info(f"Batch complete: {successful}/{len(urls)} videos created")

        return results

    # =========================================================================
    # Lipsync Feature
    # =========================================================================

    async def create_lipsync(
        self,
        video_url: str,
        audio_url: str,
        wait_for_completion: bool = True
    ) -> LipsyncJob:
        """
        Add lipsync to video.

        Takes an existing video and syncs lips to new audio.

        Args:
            video_url: Input video URL
            audio_url: Audio to sync
            wait_for_completion: Wait for job

        Returns:
            Lipsync job
        """
        logger.info("Creating lipsync job")

        response = await self._request(
            "POST",
            "lipsyncs/",
            data={
                "video_url": video_url,
                "audio_url": audio_url
            }
        )

        job_id = response.get("id")

        job = LipsyncJob(
            id=job_id,
            status="pending",
            input_video_url=video_url,
            audio_url=audio_url,
            output_url=None,
            created_at=datetime.now(),
            completed_at=None
        )

        if not wait_for_completion:
            return job

        # Poll for completion
        return await self._poll_lipsync_job(job_id)

    async def get_lipsync_status(self, job_id: str) -> LipsyncJob:
        """Check lipsync job status"""
        response = await self._request("GET", f"lipsyncs/{job_id}/")

        return LipsyncJob(
            id=job_id,
            status=response.get("status", "unknown"),
            input_video_url=response.get("video_url", ""),
            audio_url=response.get("audio_url", ""),
            output_url=response.get("output_url"),
            created_at=datetime.fromisoformat(response["created_at"]) if response.get("created_at") else datetime.now(),
            completed_at=datetime.fromisoformat(response["completed_at"]) if response.get("completed_at") else None
        )

    async def _poll_lipsync_job(self, job_id: str, timeout: int = 300) -> LipsyncJob:
        """Poll lipsync job until completion"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            job = await self.get_lipsync_status(job_id)

            if job.status == "completed":
                logger.info(f"✅ Lipsync completed: {job.output_url}")
                return job
            elif job.status == "failed":
                logger.error("❌ Lipsync failed")
                return job

            await asyncio.sleep(5)

        return await self.get_lipsync_status(job_id)

    # =========================================================================
    # Video Methods
    # =========================================================================

    async def get_videos(
        self,
        limit: int = 100,
        style: CreatorStyle = None,
        industry: str = None
    ) -> List[CreatorVideo]:
        """
        Get UGC videos from account.

        Args:
            limit: Max videos to return
            style: Filter by style
            industry: Filter by industry

        Returns:
            List of creator videos
        """
        if not self.connected:
            await self.connect()

        if not self.connected:
            return []

        try:
            params = {"limit": limit}
            if style:
                params["style"] = style.value
            if industry:
                params["industry"] = industry

            async with self.session.get(
                f"{self.BASE_URL}/videos",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    videos = [self._parse_video(v) for v in data.get("videos", [])]
                    logger.info(f"Retrieved {len(videos)} videos from Creatorify")
                    return videos
                else:
                    logger.error(f"Failed to get videos: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Error getting videos: {e}")
            return []

    async def get_video_performance(self, video_id: str) -> Dict[str, Any]:
        """Get detailed performance for a video"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return {}

        try:
            async with self.session.get(
                f"{self.BASE_URL}/videos/{video_id}/performance"
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {}
        except Exception as e:
            logger.error(f"Error getting video performance: {e}")
            return {}

    async def get_top_performing_videos(
        self,
        metric: str = "conversion_rate",
        limit: int = 20,
        industry: str = None
    ) -> List[CreatorVideo]:
        """Get top performing videos by metric"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return []

        try:
            params = {
                "sort_by": metric,
                "order": "desc",
                "limit": limit
            }
            if industry:
                params["industry"] = industry

            async with self.session.get(
                f"{self.BASE_URL}/videos/top",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [self._parse_video(v) for v in data.get("videos", [])]
                else:
                    return []
        except Exception as e:
            logger.error(f"Error getting top videos: {e}")
            return []

    # =========================================================================
    # Creator Methods
    # =========================================================================

    async def get_creators(self, limit: int = 50) -> List[CreatorProfile]:
        """Get available creators"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return []

        try:
            async with self.session.get(
                f"{self.BASE_URL}/creators",
                params={"limit": limit}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [self._parse_creator(c) for c in data.get("creators", [])]
                else:
                    return []
        except Exception as e:
            logger.error(f"Error getting creators: {e}")
            return []

    async def get_top_creators(
        self,
        industry: str = None,
        style: CreatorStyle = None,
        limit: int = 10
    ) -> List[CreatorProfile]:
        """Get top performing creators"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return []

        try:
            params = {"limit": limit, "sort_by": "avg_conversion"}
            if industry:
                params["industry"] = industry
            if style:
                params["style"] = style.value

            async with self.session.get(
                f"{self.BASE_URL}/creators/top",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [self._parse_creator(c) for c in data.get("creators", [])]
                else:
                    return []
        except Exception as e:
            logger.error(f"Error getting top creators: {e}")
            return []

    # =========================================================================
    # Script Templates
    # =========================================================================

    async def get_script_templates(
        self,
        style: CreatorStyle = None,
        industry: str = None
    ) -> List[ScriptTemplate]:
        """Get UGC script templates"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return []

        try:
            params = {}
            if style:
                params["style"] = style.value
            if industry:
                params["industry"] = industry

            async with self.session.get(
                f"{self.BASE_URL}/templates",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [self._parse_template(t) for t in data.get("templates", [])]
                else:
                    return []
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []

    async def get_top_templates(
        self,
        industry: str = None,
        limit: int = 10
    ) -> List[ScriptTemplate]:
        """Get top performing script templates"""
        if not self.connected:
            await self.connect()

        if not self.connected:
            return []

        try:
            params = {"sort_by": "avg_engagement", "limit": limit}
            if industry:
                params["industry"] = industry

            async with self.session.get(
                f"{self.BASE_URL}/templates/top",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [self._parse_template(t) for t in data.get("templates", [])]
                else:
                    return []
        except Exception as e:
            logger.error(f"Error getting top templates: {e}")
            return []

    # =========================================================================
    # Pattern Extraction
    # =========================================================================

    def extract_ugc_patterns(self, videos: List[CreatorVideo]) -> Dict[str, Any]:
        """
        Extract UGC patterns from videos.

        Analyzes what makes UGC content perform well.
        """
        patterns = {
            "styles": {},
            "tones": {},
            "industries": {},
            "durations": [],
            "top_hooks": [],
            "top_ctas": [],
            "avg_performance": {
                "engagement": 0,
                "click_rate": 0,
                "conversion_rate": 0
            },
            "total_analyzed": len(videos)
        }

        total_engagement = 0
        total_clicks = 0
        total_conversions = 0
        valid_count = 0

        for video in videos:
            # Count styles
            style = video.style.value
            patterns["styles"][style] = patterns["styles"].get(style, 0) + 1

            # Count tones
            tone = video.tone.value
            patterns["tones"][tone] = patterns["tones"].get(tone, 0) + 1

            # Count industries
            industry = video.industry
            patterns["industries"][industry] = patterns["industries"].get(industry, 0) + 1

            # Track durations
            patterns["durations"].append(video.duration_seconds)

            # Collect hooks and CTAs
            if video.hook:
                patterns["top_hooks"].append({
                    "text": video.hook,
                    "style": style,
                    "conversion": video.conversion_rate or 0
                })

            if video.cta:
                patterns["top_ctas"].append({
                    "text": video.cta,
                    "style": style,
                    "conversion": video.conversion_rate or 0
                })

            # Aggregate performance
            if video.engagement_rate is not None:
                total_engagement += video.engagement_rate
                valid_count += 1
            if video.click_rate is not None:
                total_clicks += video.click_rate
            if video.conversion_rate is not None:
                total_conversions += video.conversion_rate

        # Calculate averages
        if valid_count > 0:
            patterns["avg_performance"] = {
                "engagement": total_engagement / valid_count,
                "click_rate": total_clicks / valid_count,
                "conversion_rate": total_conversions / valid_count
            }

        # Calculate avg duration
        if patterns["durations"]:
            patterns["avg_duration"] = sum(patterns["durations"]) / len(patterns["durations"])

        # Sort hooks by conversion
        patterns["top_hooks"] = sorted(
            patterns["top_hooks"],
            key=lambda x: x["conversion"],
            reverse=True
        )[:20]

        patterns["top_ctas"] = sorted(
            patterns["top_ctas"],
            key=lambda x: x["conversion"],
            reverse=True
        )[:20]

        # Find best performing style
        if patterns["styles"]:
            patterns["best_style"] = max(patterns["styles"].items(), key=lambda x: x[1])[0]

        if patterns["tones"]:
            patterns["best_tone"] = max(patterns["tones"].items(), key=lambda x: x[1])[0]

        logger.info(f"Extracted UGC patterns from {len(videos)} videos")
        return patterns

    def get_style_performance(
        self,
        videos: List[CreatorVideo]
    ) -> Dict[str, Dict[str, float]]:
        """Get average performance by style"""
        style_stats = {}

        for video in videos:
            style = video.style.value
            if style not in style_stats:
                style_stats[style] = {
                    "count": 0,
                    "total_engagement": 0,
                    "total_conversion": 0
                }

            style_stats[style]["count"] += 1
            if video.engagement_rate:
                style_stats[style]["total_engagement"] += video.engagement_rate
            if video.conversion_rate:
                style_stats[style]["total_conversion"] += video.conversion_rate

        # Calculate averages
        result = {}
        for style, stats in style_stats.items():
            if stats["count"] > 0:
                result[style] = {
                    "count": stats["count"],
                    "avg_engagement": stats["total_engagement"] / stats["count"],
                    "avg_conversion": stats["total_conversion"] / stats["count"]
                }

        return result

    # =========================================================================
    # Integration with Learning System
    # =========================================================================

    async def sync_to_patterns_db(
        self,
        videos: List[CreatorVideo],
        patterns_db
    ) -> int:
        """
        Sync UGC patterns to winning_patterns_db.

        Args:
            videos: Videos to sync
            patterns_db: WinningPatternsDB instance

        Returns:
            Number of patterns synced
        """
        patterns = self.extract_ugc_patterns(videos)
        synced = 0

        # Sync hooks
        for hook in patterns["top_hooks"]:
            await patterns_db.add_hook_pattern(
                text=hook["text"],
                hook_type="ugc_" + hook["style"],
                industry="ugc",
                source="creatorify",
                performance_score=hook["conversion"]
            )
            synced += 1

        # Sync CTAs
        for cta in patterns["top_ctas"]:
            await patterns_db.add_cta_pattern(
                text=cta["text"],
                industry="ugc",
                source="creatorify",
                performance_score=cta["conversion"]
            )
            synced += 1

        # Sync style recommendations
        style_perf = self.get_style_performance(videos)
        for style, stats in style_perf.items():
            await patterns_db.add_style_pattern(
                style=style,
                avg_engagement=stats["avg_engagement"],
                avg_conversion=stats["avg_conversion"],
                source="creatorify"
            )
            synced += 1

        logger.info(f"Synced {synced} UGC patterns to database")
        return synced

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _parse_video(self, data: Dict) -> CreatorVideo:
        """Parse API response to CreatorVideo"""
        return CreatorVideo(
            id=data.get("id", ""),
            title=data.get("title", ""),
            creator_id=data.get("creator_id", ""),
            creator_name=data.get("creator_name", data.get("creator", {}).get("name", "")),
            style=CreatorStyle(data.get("style", "talking_head")),
            tone=VoiceTone(data.get("tone", "casual")),
            duration_seconds=data.get("duration", data.get("duration_seconds", 30)),
            script=data.get("script", ""),
            hook=data.get("hook", self._extract_hook(data.get("script", ""))),
            cta=data.get("cta", ""),
            views=data.get("views"),
            engagement_rate=data.get("engagement_rate"),
            click_rate=data.get("click_rate", data.get("ctr")),
            conversion_rate=data.get("conversion_rate", data.get("cvr")),
            video_url=data.get("video_url"),
            thumbnail_url=data.get("thumbnail_url"),
            industry=data.get("industry", "general"),
            product_type=data.get("product_type", ""),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            tags=data.get("tags", [])
        )

    def _parse_creator(self, data: Dict) -> CreatorProfile:
        """Parse API response to CreatorProfile"""
        return CreatorProfile(
            id=data.get("id", ""),
            name=data.get("name", ""),
            avatar_url=data.get("avatar_url"),
            total_videos=data.get("total_videos", 0),
            avg_engagement=data.get("avg_engagement", 0),
            avg_conversion=data.get("avg_conversion", 0),
            styles=[CreatorStyle(s) for s in data.get("styles", ["talking_head"])],
            industries=data.get("industries", []),
            tones=[VoiceTone(t) for t in data.get("tones", ["casual"])],
            price_per_video=data.get("price_per_video")
        )

    def _parse_template(self, data: Dict) -> ScriptTemplate:
        """Parse API response to ScriptTemplate"""
        return ScriptTemplate(
            id=data.get("id", ""),
            name=data.get("name", ""),
            style=CreatorStyle(data.get("style", "talking_head")),
            industry=data.get("industry", "general"),
            hook_template=data.get("hook_template", ""),
            body_template=data.get("body_template", ""),
            cta_template=data.get("cta_template", ""),
            hook_duration=data.get("hook_duration", 3),
            body_duration=data.get("body_duration", 20),
            cta_duration=data.get("cta_duration", 5),
            avg_engagement=data.get("avg_engagement", 0),
            usage_count=data.get("usage_count", 0)
        )

    def _extract_hook(self, script: str) -> str:
        """Extract hook from script (first sentence)"""
        if not script:
            return ""
        lines = script.split('\n')
        return lines[0].strip() if lines else ""

    def _parse_avatars(self, data: Any) -> List[AIAvatar]:
        """Parse avatars API response"""
        avatars = []
        avatar_list = data if isinstance(data, list) else data.get("avatars", data.get("data", []))

        for a in avatar_list:
            avatars.append(AIAvatar(
                id=a.get("id", a.get("avatar_id", "")),
                name=a.get("name", ""),
                gender=a.get("gender", "unknown"),
                age_range=a.get("age_range", a.get("age", "")),
                ethnicity=a.get("ethnicity", ""),
                preview_url=a.get("preview_url", a.get("thumbnail_url", "")),
                voice_id=a.get("voice_id")
            ))

        return avatars

    def _parse_script(self, data: Any) -> Optional[GeneratedScript]:
        """Parse script from API response"""
        if not data:
            return None

        if isinstance(data, str):
            return GeneratedScript(
                id="",
                hook="",
                body=data,
                cta="",
                full_script=data,
                duration_estimate=30,
                tone="casual",
                style="ugc"
            )

        return GeneratedScript(
            id=data.get("id", ""),
            hook=data.get("hook", ""),
            body=data.get("body", ""),
            cta=data.get("cta", ""),
            full_script=data.get("script", data.get("full_script", "")),
            duration_estimate=data.get("duration", 30),
            tone=data.get("tone", "casual"),
            style=data.get("style", "ugc")
        )


# =============================================================================
# Convenience Functions
# =============================================================================

async def create_video_from_product_url(
    url: str,
    avatar_id: str = None,
    api_id: str = None,
    api_key: str = None,
    aspect_ratio: str = "9:16"
) -> VideoGenerationJob:
    """
    Quick function to create a video from a product URL.

    Args:
        url: Product page URL
        avatar_id: Optional avatar ID (uses first available if not specified)
        api_id: Creatify API ID
        api_key: Creatify API Key
        aspect_ratio: Video aspect ratio

    Returns:
        Video generation job with output URL
    """
    client = CreatifyIntegration(api_id, api_key)
    await client.connect()

    # Get avatar if not specified
    if not avatar_id:
        avatars = await client.get_avatars()
        if avatars:
            avatar_id = avatars[0].id
        else:
            raise Exception("No avatars available")

    # Create video
    job = await client.create_video_from_url(
        url=url,
        avatar_id=avatar_id,
        aspect_ratio=VideoAspectRatio(aspect_ratio)
    )

    await client.disconnect()
    return job


async def batch_generate_videos(
    urls: List[str],
    api_id: str = None,
    api_key: str = None
) -> List[VideoGenerationJob]:
    """
    Generate videos for multiple product URLs.

    Args:
        urls: List of product URLs
        api_id: Creatify API ID
        api_key: Creatify API Key

    Returns:
        List of video jobs
    """
    client = CreatifyIntegration(api_id, api_key)
    await client.connect()

    avatars = await client.get_avatars()
    if not avatars:
        raise Exception("No avatars available")

    jobs = await client.batch_create_videos(
        urls=urls,
        avatar_id=avatars[0].id
    )

    await client.disconnect()
    return jobs


# Keep old class name for backwards compatibility
CreatorifyIntegration = CreatifyIntegration
