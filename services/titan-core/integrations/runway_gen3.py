"""
Runway Gen-3 Alpha Integration

Generate AI video from text prompts or images.
This enables creating completely new video scenes without filming.

Use cases:
- Generate product shots without photoshoot
- Create lifestyle scenes
- Generate B-roll footage
- Transform images into video
"""

import os
import asyncio
import httpx
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import time

logger = logging.getLogger(__name__)

# Runway API configuration
RUNWAY_API_URL = "https://api.runwayml.com/v1"
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")

class RunwayModel(Enum):
    GEN3_ALPHA = "gen3a_turbo"  # Fastest
    GEN3_ALPHA_TURBO = "gen3a_turbo"
    GEN2 = "gen2"  # Fallback

class VideoAspectRatio(Enum):
    LANDSCAPE = "16:9"
    PORTRAIT = "9:16"
    SQUARE = "1:1"
    WIDESCREEN = "21:9"

@dataclass
class GenerationRequest:
    """Request for video generation"""
    prompt: str
    model: RunwayModel = RunwayModel.GEN3_ALPHA_TURBO
    duration: int = 5  # 5 or 10 seconds
    aspect_ratio: VideoAspectRatio = VideoAspectRatio.PORTRAIT
    seed: Optional[int] = None
    image_url: Optional[str] = None  # For image-to-video
    style_reference: Optional[str] = None

@dataclass
class GenerationResult:
    """Result of video generation"""
    task_id: str
    status: str  # pending, processing, completed, failed
    video_url: Optional[str]
    duration: float
    cost_credits: float
    generation_time: float
    prompt_used: str
    error: Optional[str] = None

class RunwayGen3Client:
    """
    Client for Runway Gen-3 Alpha API.

    Generates AI video from:
    - Text prompts (text-to-video)
    - Images (image-to-video)
    - Combinations (image + prompt)

    Perfect for:
    - Product visualizations
    - Lifestyle scenes
    - B-roll footage
    - Creative variations
    """

    def __init__(self, api_key: str = None):
        self.api_key = api_key or RUNWAY_API_KEY
        self.base_url = RUNWAY_API_URL

        if not self.api_key:
            logger.warning("Runway API key not set. Set RUNWAY_API_KEY environment variable.")

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate video from prompt or image.

        Args:
            request: Generation request with prompt, model, duration, etc.

        Returns:
            GenerationResult with video URL or error
        """
        if not self.api_key:
            return GenerationResult(
                task_id="",
                status="failed",
                video_url=None,
                duration=0,
                cost_credits=0,
                generation_time=0,
                prompt_used=request.prompt,
                error="API key not configured"
            )

        start_time = time.time()

        # Prepare request payload
        payload = {
            "prompt": request.prompt,
            "model": request.model.value,
            "duration": request.duration,
            "aspect_ratio": request.aspect_ratio.value
        }

        if request.seed:
            payload["seed"] = request.seed

        if request.image_url:
            payload["image_url"] = request.image_url

        if request.style_reference:
            payload["style_reference"] = request.style_reference

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=300) as client:
                # Start generation
                response = await client.post(
                    f"{self.base_url}/generations",
                    json=payload,
                    headers=headers
                )

                if response.status_code != 200:
                    return GenerationResult(
                        task_id="",
                        status="failed",
                        video_url=None,
                        duration=0,
                        cost_credits=0,
                        generation_time=0,
                        prompt_used=request.prompt,
                        error=f"API error: {response.status_code} - {response.text}"
                    )

                data = response.json()
                task_id = data.get("id", "")

                # Poll for completion
                video_url = await self._poll_for_completion(client, task_id, headers)

                generation_time = time.time() - start_time

                return GenerationResult(
                    task_id=task_id,
                    status="completed" if video_url else "failed",
                    video_url=video_url,
                    duration=request.duration,
                    cost_credits=self._calculate_credits(request.duration, request.model),
                    generation_time=generation_time,
                    prompt_used=request.prompt
                )

        except Exception as e:
            logger.error(f"Runway generation failed: {e}")
            return GenerationResult(
                task_id="",
                status="failed",
                video_url=None,
                duration=0,
                cost_credits=0,
                generation_time=time.time() - start_time,
                prompt_used=request.prompt,
                error=str(e)
            )

    async def _poll_for_completion(self, client: httpx.AsyncClient,
                                    task_id: str, headers: Dict,
                                    max_wait: int = 300) -> Optional[str]:
        """Poll for generation completion"""
        poll_interval = 5
        elapsed = 0

        while elapsed < max_wait:
            response = await client.get(
                f"{self.base_url}/generations/{task_id}",
                headers=headers
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get("status")

                if status == "completed":
                    return data.get("video_url")
                elif status == "failed":
                    logger.error(f"Generation failed: {data.get('error')}")
                    return None

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        logger.error("Generation timed out")
        return None

    def _calculate_credits(self, duration: int, model: RunwayModel) -> float:
        """Estimate credit cost"""
        # Approximate costs (check actual Runway pricing)
        base_credits = {
            RunwayModel.GEN3_ALPHA: 0.05,
            RunwayModel.GEN3_ALPHA_TURBO: 0.04,
            RunwayModel.GEN2: 0.02
        }
        return base_credits.get(model, 0.05) * duration

    async def generate_product_shot(self, product_image: str,
                                     scene_description: str) -> GenerationResult:
        """Generate product video from image"""
        prompt = f"Product showcase: {scene_description}. Cinematic lighting, smooth camera movement, professional commercial quality."

        return await self.generate_video(GenerationRequest(
            prompt=prompt,
            image_url=product_image,
            duration=5,
            aspect_ratio=VideoAspectRatio.PORTRAIT
        ))

    async def generate_lifestyle_scene(self, description: str,
                                        mood: str = "energetic") -> GenerationResult:
        """Generate lifestyle B-roll"""
        mood_modifiers = {
            "energetic": "dynamic camera movement, vibrant colors, fast-paced",
            "calm": "slow motion, soft lighting, peaceful atmosphere",
            "luxury": "elegant movements, golden lighting, premium feel",
            "playful": "bouncy movements, bright colors, fun atmosphere"
        }

        modifier = mood_modifiers.get(mood, mood_modifiers["energetic"])
        prompt = f"Lifestyle scene: {description}. {modifier}. Professional commercial quality."

        return await self.generate_video(GenerationRequest(
            prompt=prompt,
            duration=5,
            aspect_ratio=VideoAspectRatio.PORTRAIT
        ))

    async def generate_variations(self, base_prompt: str,
                                   count: int = 3) -> List[GenerationResult]:
        """Generate multiple variations of a scene"""
        variations = []
        modifiers = [
            "close-up shot",
            "wide establishing shot",
            "dynamic camera movement",
            "slow motion reveal",
            "dramatic lighting"
        ]

        for i in range(min(count, len(modifiers))):
            modified_prompt = f"{base_prompt}. {modifiers[i]}."
            result = await self.generate_video(GenerationRequest(
                prompt=modified_prompt,
                duration=5,
                seed=i * 1000  # Different seeds for variety
            ))
            variations.append(result)

        return variations


# Fallback for when API is not available
class MockRunwayClient:
    """Mock client for testing without API"""

    async def generate_video(self, request: GenerationRequest) -> GenerationResult:
        await asyncio.sleep(2)  # Simulate API delay
        return GenerationResult(
            task_id="mock_task_123",
            status="completed",
            video_url="https://example.com/mock_video.mp4",
            duration=request.duration,
            cost_credits=0.0,
            generation_time=2.0,
            prompt_used=request.prompt
        )


def get_runway_client() -> RunwayGen3Client:
    """Get Runway client (real or mock based on config)"""
    if RUNWAY_API_KEY:
        return RunwayGen3Client()
    else:
        logger.warning("Using mock Runway client - set RUNWAY_API_KEY for real generation")
        return MockRunwayClient()
