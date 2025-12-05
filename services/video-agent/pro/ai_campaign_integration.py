"""
AI VIDEO GENERATION - CAMPAIGN INTEGRATION
==========================================

Integrate AI video generation into campaign creation workflow.

Features:
- Auto-generate B-roll from text descriptions
- Create product shots from images
- Generate scene transitions
- Cost-optimized workflow (drafts -> finals)

Use cases:
1. Campaign Builder: Generate missing B-roll automatically
2. Product Videos: Animate product photos
3. Scene Fillers: Create transitions between clips
4. Testing Variants: Generate multiple video variations
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import asyncio

from .ai_video_generator import (
    AIVideoGenerator,
    VideoGenerationRequest,
    GenerationMode,
    QualityTier,
    VideoProvider,
    VideoGenerationResult
)

logger = logging.getLogger(__name__)


@dataclass
class CampaignAsset:
    """Asset for a campaign"""
    asset_id: str
    asset_type: str  # 'b_roll', 'product_shot', 'transition', 'intro', 'outro'
    prompt: str
    duration: int = 5
    aspect_ratio: str = "9:16"
    image_path: Optional[str] = None
    priority: str = "standard"  # 'draft', 'standard', 'high'


class AICampaignIntegration:
    """
    Helper class to integrate AI video generation with campaign creation

    Example usage:
        integration = AICampaignIntegration()

        # Generate B-roll for fitness ad
        b_roll = await integration.generate_b_roll(
            prompts=[
                "Person running on treadmill in modern gym",
                "Close-up of fitness tracker showing heart rate",
                "Healthy meal prep in bright kitchen"
            ],
            quality="draft"  # Use draft quality for cost savings
        )

        # Animate product photo
        product_video = await integration.animate_product_image(
            image_path="product_shot.jpg",
            motion="Slow 360-degree rotation, professional lighting"
        )
    """

    def __init__(self):
        self.generator = AIVideoGenerator()

    async def generate_b_roll(
        self,
        prompts: List[str],
        quality: str = "draft",
        duration: int = 5,
        aspect_ratio: str = "9:16",
        use_cost_optimization: bool = True
    ) -> List[VideoGenerationResult]:
        """
        Generate B-roll footage from text descriptions

        Args:
            prompts: List of video descriptions
            quality: Quality tier (draft/standard/high)
            duration: Duration in seconds
            aspect_ratio: Video aspect ratio
            use_cost_optimization: Use cheaper providers for non-critical footage

        Returns:
            List of generation results with video URLs

        Example:
            b_roll = await integration.generate_b_roll([
                "Modern office with people collaborating",
                "Close-up of hands typing on laptop",
                "Coffee being poured in cafe"
            ])
        """
        logger.info(f"Generating {len(prompts)} B-roll clips")

        quality_map = {
            "draft": QualityTier.DRAFT,
            "standard": QualityTier.STANDARD,
            "high": QualityTier.HIGH,
            "master": QualityTier.MASTER
        }
        quality_tier = quality_map.get(quality, QualityTier.DRAFT)

        results = []

        for i, prompt in enumerate(prompts):
            # Use draft quality for all but the last clip if optimizing
            clip_quality = QualityTier.DRAFT if use_cost_optimization and i < len(prompts) - 1 else quality_tier

            request = VideoGenerationRequest(
                mode=GenerationMode.TEXT_TO_VIDEO,
                prompt=f"Professional B-roll footage: {prompt}. Cinematic, stable camera, high quality.",
                quality=clip_quality,
                duration=duration,
                aspect_ratio=aspect_ratio,
                style="cinematic",
                metadata={"type": "b_roll", "index": i}
            )

            result = await self.generator.generate_video(request)
            results.append(result)

            logger.info(f"B-roll {i+1}/{len(prompts)}: {result.status.value}")

        return results

    async def animate_product_image(
        self,
        image_path: str,
        motion: str = "Slow zoom in and gentle rotation",
        duration: int = 5,
        aspect_ratio: str = "9:16",
        quality: str = "high"
    ) -> VideoGenerationResult:
        """
        Animate a static product image

        Perfect for:
        - Product showcases
        - Before/after comparisons
        - Testimonial backgrounds

        Args:
            image_path: Path to product image
            motion: Motion description
            duration: Video duration
            aspect_ratio: Video format
            quality: Quality tier

        Returns:
            Generation result with video URL

        Example:
            result = await integration.animate_product_image(
                "iphone_product_shot.jpg",
                "Elegant 360-degree rotation with subtle zoom"
            )
        """
        logger.info(f"Animating product image: {image_path}")

        quality_map = {
            "draft": QualityTier.DRAFT,
            "standard": QualityTier.STANDARD,
            "high": QualityTier.HIGH,
            "master": QualityTier.MASTER
        }
        quality_tier = quality_map.get(quality, QualityTier.HIGH)

        request = VideoGenerationRequest(
            mode=GenerationMode.IMAGE_TO_VIDEO,
            prompt=motion,
            image_path=image_path,
            quality=quality_tier,
            duration=duration,
            aspect_ratio=aspect_ratio,
            metadata={"type": "product_animation"}
        )

        result = await self.generator.generate_video(request)

        logger.info(f"Product animation: {result.status.value}")

        return result

    async def generate_scene_transitions(
        self,
        count: int = 3,
        style: str = "smooth",
        duration: int = 3,
        aspect_ratio: str = "9:16"
    ) -> List[VideoGenerationResult]:
        """
        Generate transition clips for between scenes

        Args:
            count: Number of transition clips
            style: Transition style (smooth/dynamic/minimal)
            duration: Duration per transition
            aspect_ratio: Video format

        Returns:
            List of transition video results

        Example:
            transitions = await integration.generate_scene_transitions(
                count=5,
                style="dynamic"
            )
        """
        logger.info(f"Generating {count} scene transitions")

        prompts = self._get_transition_prompts(style, count)
        results = []

        for i, prompt in enumerate(prompts[:count]):
            request = VideoGenerationRequest(
                mode=GenerationMode.TEXT_TO_VIDEO,
                prompt=prompt,
                quality=QualityTier.DRAFT,  # Transitions can be draft quality
                duration=duration,
                aspect_ratio=aspect_ratio,
                metadata={"type": "transition", "index": i}
            )

            result = await self.generator.generate_video(request)
            results.append(result)

        return results

    async def generate_campaign_assets(
        self,
        campaign_brief: Dict[str, Any]
    ) -> Dict[str, List[VideoGenerationResult]]:
        """
        Generate all needed video assets for a campaign

        Args:
            campaign_brief: Campaign configuration
                - product_name: str
                - b_roll_scenes: List[str]
                - product_images: List[str]
                - aspect_ratio: str
                - quality: str

        Returns:
            Dictionary of asset types to generation results

        Example:
            brief = {
                "product_name": "FitnessPro App",
                "b_roll_scenes": [
                    "Person using fitness app on phone in gym",
                    "Success notification on phone screen",
                    "Group fitness class celebrating"
                ],
                "product_images": ["app_screenshot.jpg"],
                "aspect_ratio": "9:16",
                "quality": "standard"
            }

            assets = await integration.generate_campaign_assets(brief)
            # Returns: {"b_roll": [...], "product_shots": [...], "transitions": [...]}
        """
        logger.info(f"Generating campaign assets for: {campaign_brief.get('product_name')}")

        assets = {}

        # Generate B-roll
        if campaign_brief.get("b_roll_scenes"):
            assets["b_roll"] = await self.generate_b_roll(
                prompts=campaign_brief["b_roll_scenes"],
                quality=campaign_brief.get("quality", "draft"),
                aspect_ratio=campaign_brief.get("aspect_ratio", "9:16")
            )

        # Animate product images
        if campaign_brief.get("product_images"):
            product_shots = []
            for image_path in campaign_brief["product_images"]:
                result = await self.animate_product_image(
                    image_path=image_path,
                    motion="Professional product showcase with smooth movement",
                    quality=campaign_brief.get("quality", "high"),
                    aspect_ratio=campaign_brief.get("aspect_ratio", "9:16")
                )
                product_shots.append(result)
            assets["product_shots"] = product_shots

        # Generate transitions
        transition_count = campaign_brief.get("transition_count", 3)
        if transition_count > 0:
            assets["transitions"] = await self.generate_scene_transitions(
                count=transition_count,
                style=campaign_brief.get("transition_style", "smooth"),
                aspect_ratio=campaign_brief.get("aspect_ratio", "9:16")
            )

        logger.info(f"Campaign asset generation complete. Total assets: {sum(len(v) for v in assets.values())}")

        return assets

    async def create_video_variants(
        self,
        base_prompt: str,
        variant_count: int = 5,
        quality: str = "draft"
    ) -> List[VideoGenerationResult]:
        """
        Generate multiple variations of a video for A/B testing

        Args:
            base_prompt: Base video description
            variant_count: Number of variants to generate
            quality: Quality tier

        Returns:
            List of variant generation results

        Example:
            variants = await integration.create_video_variants(
                "Fitness app demo showing workout tracking features",
                variant_count=5,
                quality="draft"
            )
        """
        logger.info(f"Creating {variant_count} video variants")

        variations = [
            f"{base_prompt}. Camera angle: front view, bright lighting",
            f"{base_prompt}. Camera angle: over-the-shoulder, natural lighting",
            f"{base_prompt}. Camera angle: close-up, dramatic lighting",
            f"{base_prompt}. Camera angle: wide shot, soft lighting",
            f"{base_prompt}. Camera angle: dynamic movement, cinematic lighting"
        ]

        quality_map = {
            "draft": QualityTier.DRAFT,
            "standard": QualityTier.STANDARD,
            "high": QualityTier.HIGH
        }
        quality_tier = quality_map.get(quality, QualityTier.DRAFT)

        results = []

        for i, prompt in enumerate(variations[:variant_count]):
            request = VideoGenerationRequest(
                mode=GenerationMode.TEXT_TO_VIDEO,
                prompt=prompt,
                quality=quality_tier,
                duration=5,
                aspect_ratio="9:16",
                seed=i,  # Different seed for each variant
                metadata={"variant_index": i}
            )

            result = await self.generator.generate_video(request)
            results.append(result)

        return results

    def _get_transition_prompts(self, style: str, count: int) -> List[str]:
        """Get prompts for transition clips"""
        prompts_by_style = {
            "smooth": [
                "Smooth gradient transition from dark to light",
                "Soft blur transition effect",
                "Gentle fade with particle effects",
                "Elegant light leak transition",
                "Subtle color shift transition"
            ],
            "dynamic": [
                "Fast-paced geometric transition",
                "Dynamic light burst effect",
                "High-energy particle explosion",
                "Quick zoom transition",
                "Energetic color splash"
            ],
            "minimal": [
                "Simple fade to black",
                "Clean white flash",
                "Minimal geometric wipe",
                "Subtle gradient shift",
                "Basic crossfade effect"
            ]
        }

        return prompts_by_style.get(style, prompts_by_style["smooth"])

    async def close(self):
        """Close generator session"""
        await self.generator.close()


# ==================== HELPER FUNCTIONS ====================

async def auto_generate_missing_b_roll(
    campaign_data: Dict[str, Any],
    required_b_roll_count: int = 5
) -> List[VideoGenerationResult]:
    """
    Automatically generate B-roll when campaign is missing footage

    Args:
        campaign_data: Campaign configuration
        required_b_roll_count: Target number of B-roll clips

    Returns:
        List of generated B-roll clips

    Example:
        campaign = {
            "product_name": "Meditation App",
            "target_audience": "stressed professionals",
            "key_benefits": ["reduce stress", "improve sleep", "increase focus"]
        }

        b_roll = await auto_generate_missing_b_roll(campaign, required_b_roll_count=5)
    """
    integration = AICampaignIntegration()

    # Generate intelligent prompts based on campaign data
    product = campaign_data.get("product_name", "product")
    audience = campaign_data.get("target_audience", "users")
    benefits = campaign_data.get("key_benefits", [])

    prompts = [
        f"{audience} using {product} happily",
        f"Close-up of {product} interface, professional and clean",
        f"Person experiencing result: {benefits[0] if benefits else 'positive outcome'}",
        f"{audience} in their environment, aspirational",
        f"Detail shot highlighting {product} key feature"
    ]

    results = await integration.generate_b_roll(
        prompts=prompts[:required_b_roll_count],
        quality="draft",  # Use draft for cost savings
        use_cost_optimization=True
    )

    await integration.close()

    return results


async def enhance_campaign_with_ai_video(
    campaign_id: str,
    campaign_config: Dict[str, Any],
    auto_generate: bool = True
) -> Dict[str, Any]:
    """
    Enhance existing campaign with AI-generated video assets

    Args:
        campaign_id: Campaign identifier
        campaign_config: Campaign configuration
        auto_generate: Automatically generate missing assets

    Returns:
        Enhanced campaign config with AI-generated assets

    Example:
        enhanced = await enhance_campaign_with_ai_video(
            campaign_id="camp_123",
            campaign_config={...},
            auto_generate=True
        )
    """
    integration = AICampaignIntegration()

    enhanced_config = campaign_config.copy()
    ai_assets = {}

    # Check what's missing
    has_b_roll = bool(campaign_config.get("video_clips"))
    has_product_shots = bool(campaign_config.get("product_images"))

    if auto_generate:
        # Generate B-roll if missing
        if not has_b_roll:
            logger.info(f"Generating B-roll for campaign {campaign_id}")
            b_roll_prompts = _generate_b_roll_prompts_from_campaign(campaign_config)
            ai_assets["b_roll"] = await integration.generate_b_roll(b_roll_prompts)

        # Animate product images if available
        if campaign_config.get("static_product_images"):
            logger.info(f"Animating product images for campaign {campaign_id}")
            product_animations = []
            for image_path in campaign_config["static_product_images"]:
                result = await integration.animate_product_image(image_path)
                product_animations.append(result)
            ai_assets["product_animations"] = product_animations

    enhanced_config["ai_generated_assets"] = ai_assets
    enhanced_config["ai_enhanced"] = True

    await integration.close()

    return enhanced_config


def _generate_b_roll_prompts_from_campaign(campaign_config: Dict[str, Any]) -> List[str]:
    """Generate intelligent B-roll prompts from campaign configuration"""
    product = campaign_config.get("product_name", "product")
    hook = campaign_config.get("hook", "")
    target = campaign_config.get("target_avatar", "people")

    prompts = [
        f"Professional footage of {target} using {product}",
        f"Close-up of {product} with professional lighting",
        f"Scene illustrating: {hook}",
        f"{target} experiencing positive results",
        f"Modern environment showcasing {product} use case"
    ]

    return prompts


# ==================== USAGE EXAMPLE ====================

async def example_campaign_integration():
    """Example: Integrate AI video generation into campaign creation"""

    integration = AICampaignIntegration()

    # Example 1: Generate B-roll for fitness campaign
    print("Generating B-roll footage...")
    b_roll = await integration.generate_b_roll(
        prompts=[
            "Person running on treadmill in modern gym, focused expression",
            "Fitness tracker showing heart rate data, close-up",
            "Healthy meal prep bowls on kitchen counter, bright natural light"
        ],
        quality="draft",  # Use draft for cost savings
        duration=5,
        aspect_ratio="9:16"
    )

    for i, result in enumerate(b_roll):
        print(f"B-roll {i+1}: {result.status.value}, Cost: ${result.cost or 0:.2f}")

    # Example 2: Animate product screenshot
    print("\nAnimating product image...")
    product_video = await integration.animate_product_image(
        image_path="/path/to/product_screenshot.jpg",
        motion="Slow zoom in highlighting key features with professional lighting",
        quality="high"
    )

    print(f"Product animation: {product_video.status.value}")

    # Example 3: Generate complete campaign assets
    print("\nGenerating complete campaign...")
    campaign_brief = {
        "product_name": "FitnessPro App",
        "b_roll_scenes": [
            "User tracking workout on phone in gym",
            "Success notification celebration",
            "Progress chart showing improvement"
        ],
        "product_images": ["/path/to/app_screen1.jpg"],
        "aspect_ratio": "9:16",
        "quality": "standard",
        "transition_count": 3
    }

    all_assets = await integration.generate_campaign_assets(campaign_brief)

    print(f"Generated assets:")
    for asset_type, assets in all_assets.items():
        print(f"  {asset_type}: {len(assets)} clips")

    await integration.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_campaign_integration())
