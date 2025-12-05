"""
DCO Image Integration - AI Image Generation for Dynamic Creative Optimization
Agent 37: Image Generation Integration with DCO System

Integrates ImageGenerator with DCO system to:
- Auto-generate product variants
- Create platform-specific thumbnails
- Generate A/B test variations
- Produce complete ad creatives from product descriptions

This enables FULLY AUTOMATED ad creation from just a product description.
"""

import os
import sys
import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
import json

# Import DCO system
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.dco_meta_generator import (
    DCOMetaGenerator,
    DCOGenerationConfig,
    MetaAdFormat,
    MetaVariant
)

# Import image generator
from image_generator import (
    ImageGenerator,
    ImageProvider,
    AspectRatio,
    ImageStyle,
    GenerationConfig,
    GeneratedImage
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DCOImageConfig:
    """Configuration for DCO image generation"""
    # Product information
    product_name: str
    product_desc: str
    brand_style: str = "modern and professional"

    # Image generation
    generate_product_shots: bool = True
    generate_lifestyle: bool = True
    generate_thumbnails: bool = True

    # Variant settings
    num_product_variants: int = 3
    num_lifestyle_variants: int = 2

    # Provider settings
    product_provider: ImageProvider = ImageProvider.FLUX_PRO
    lifestyle_provider: ImageProvider = ImageProvider.FLUX_DEV
    thumbnail_provider: ImageProvider = ImageProvider.FLUX_SCHNELL

    # Output
    output_dir: str = "/tmp/dco_images"


@dataclass
class DCOImagePackage:
    """Complete image package for DCO"""
    product_shots: List[GeneratedImage]
    lifestyle_images: List[GeneratedImage]
    thumbnails: Dict[str, GeneratedImage]  # platform -> image
    total_cost: float
    generation_time: float
    metadata: Dict[str, Any]


class DCOImageIntegration:
    """
    Integrates AI Image Generation with DCO System

    Enables fully automated ad creation pipeline:
    1. Product Description → Product Shots
    2. Brand Style → Lifestyle Images
    3. Video Content → Platform Thumbnails
    4. Auto-generate A/B test variants
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        replicate_api_key: Optional[str] = None,
        vertex_project_id: Optional[str] = None
    ):
        """
        Initialize DCO Image Integration.

        Args:
            openai_api_key: OpenAI API key
            replicate_api_key: Replicate API key
            vertex_project_id: GCP project ID
        """
        self.image_generator = ImageGenerator(
            openai_api_key=openai_api_key,
            replicate_api_key=replicate_api_key,
            vertex_project_id=vertex_project_id,
            output_dir="/tmp/dco_images"
        )

        self.dco_generator = DCOMetaGenerator()

        logger.info("✅ DCO Image Integration initialized")

    # ========================================================================
    # COMPLETE IMAGE PACKAGE GENERATION
    # ========================================================================

    async def generate_complete_package(
        self,
        config: DCOImageConfig
    ) -> DCOImagePackage:
        """
        Generate complete image package for DCO campaign.

        Args:
            config: DCO image configuration

        Returns:
            DCOImagePackage with all generated assets
        """
        logger.info(f"📦 Generating complete image package for: {config.product_name}")

        import time
        start_time = time.time()

        product_shots = []
        lifestyle_images = []
        thumbnails = {}
        total_cost = 0.0

        # 1. Generate product shots (if enabled)
        if config.generate_product_shots:
            logger.info(f"🎨 Generating {config.num_product_variants} product shots...")

            product_config = GenerationConfig(
                provider=config.product_provider,
                aspect_ratio=AspectRatio.SQUARE_1_1,
                style=ImageStyle.PRODUCT,
                quality="high"
            )

            # Generate variants
            product_shots = await self.image_generator.generate_variant_batch(
                base_prompt=f"Professional product photography of {config.product_desc}",
                num_variants=config.num_product_variants,
                config=product_config
            )

            total_cost += sum(img.cost_estimate for img in product_shots)
            logger.info(f"  ✅ Generated {len(product_shots)} product shots")

        # 2. Generate lifestyle images (if enabled)
        if config.generate_lifestyle:
            logger.info(f"🎨 Generating {config.num_lifestyle_variants} lifestyle images...")

            lifestyle_config = GenerationConfig(
                provider=config.lifestyle_provider,
                aspect_ratio=AspectRatio.PORTRAIT_4_5,
                style=ImageStyle.LIFESTYLE,
                quality="high"
            )

            # Generate lifestyle scenes
            lifestyle_prompts = self._generate_lifestyle_prompts(
                config.product_name,
                config.brand_style,
                config.num_lifestyle_variants
            )

            lifestyle_tasks = [
                self.image_generator.generate_lifestyle(prompt, config.brand_style, lifestyle_config)
                for prompt in lifestyle_prompts
            ]

            lifestyle_images = await asyncio.gather(*lifestyle_tasks)
            total_cost += sum(img.cost_estimate for img in lifestyle_images)
            logger.info(f"  ✅ Generated {len(lifestyle_images)} lifestyle images")

        # 3. Generate platform-specific thumbnails (if enabled)
        if config.generate_thumbnails:
            logger.info("🎨 Generating platform-specific thumbnails...")

            platforms = ["instagram", "facebook", "youtube", "tiktok"]
            thumbnail_config = GenerationConfig(
                provider=config.thumbnail_provider,
                style=ImageStyle.VIBRANT,
                quality="medium"
            )

            video_summary = f"Ad showcasing {config.product_name} - {config.product_desc}"

            thumbnail_tasks = []
            for platform in platforms:
                thumbnail_tasks.append(
                    self.image_generator.generate_thumbnail(
                        video_summary,
                        style="attention-grabbing",
                        platform=platform,
                        config=thumbnail_config
                    )
                )

            thumbnail_results = await asyncio.gather(*thumbnail_tasks)

            thumbnails = dict(zip(platforms, thumbnail_results))
            total_cost += sum(img.cost_estimate for img in thumbnail_results)
            logger.info(f"  ✅ Generated {len(thumbnails)} thumbnails")

        generation_time = time.time() - start_time

        package = DCOImagePackage(
            product_shots=product_shots,
            lifestyle_images=lifestyle_images,
            thumbnails=thumbnails,
            total_cost=total_cost,
            generation_time=generation_time,
            metadata={
                "product_name": config.product_name,
                "brand_style": config.brand_style,
                "num_product_shots": len(product_shots),
                "num_lifestyle": len(lifestyle_images),
                "num_thumbnails": len(thumbnails)
            }
        )

        logger.info(f"✅ Complete package generated in {generation_time:.2f}s, cost: ${total_cost:.4f}")

        return package

    # ========================================================================
    # DCO-SPECIFIC GENERATION
    # ========================================================================

    async def generate_product_variants_for_dco(
        self,
        product_desc: str,
        num_variants: int = 5,
        formats: List[MetaAdFormat] = None
    ) -> Dict[str, List[GeneratedImage]]:
        """
        Generate product shot variants for all Meta ad formats.

        Args:
            product_desc: Product description
            num_variants: Number of variants per format
            formats: Meta ad formats to generate for

        Returns:
            Dictionary mapping format name to list of images
        """
        if not formats:
            formats = [
                MetaAdFormat.FEED,
                MetaAdFormat.STORY,
                MetaAdFormat.REELS,
                MetaAdFormat.IN_STREAM
            ]

        logger.info(f"📦 Generating {num_variants} variants for {len(formats)} formats")

        results = {}

        for format_type in formats:
            format_spec = format_type.value

            # Map Meta aspect ratio to AspectRatio enum
            aspect_ratio = self._meta_aspect_to_image_aspect(format_spec['aspect_ratio'])

            config = GenerationConfig(
                provider=ImageProvider.FLUX_PRO,
                aspect_ratio=aspect_ratio,
                style=ImageStyle.PRODUCT,
                quality="high"
            )

            # Generate variants
            variants = await self.image_generator.generate_variant_batch(
                base_prompt=f"Professional product photography of {product_desc}",
                num_variants=num_variants,
                config=config
            )

            results[format_spec['name']] = variants
            logger.info(f"  ✅ {format_spec['name']}: {len(variants)} variants")

        return results

    async def generate_ab_test_variations(
        self,
        base_prompt: str,
        variation_strategy: str = "style",
        num_variations: int = 4
    ) -> List[GeneratedImage]:
        """
        Generate A/B test variations with different strategies.

        Args:
            base_prompt: Base image prompt
            variation_strategy: Strategy (style, composition, color, lighting)
            num_variations: Number of variations

        Returns:
            List of generated image variations
        """
        logger.info(f"🔬 Generating {num_variations} A/B test variations ({variation_strategy})")

        # Define variation strategies
        strategies = {
            "style": [
                ImageStyle.PHOTOREALISTIC,
                ImageStyle.CINEMATIC,
                ImageStyle.MINIMAL,
                ImageStyle.VIBRANT
            ],
            "composition": [
                "centered composition",
                "rule of thirds",
                "dynamic angle",
                "close-up detail"
            ],
            "color": [
                "vibrant and saturated",
                "muted and pastel",
                "high contrast",
                "monochromatic"
            ],
            "lighting": [
                "natural daylight",
                "dramatic studio lighting",
                "soft diffused light",
                "golden hour glow"
            ]
        }

        variations = strategies.get(variation_strategy, ["variation"] * num_variations)

        tasks = []
        for i, variation in enumerate(variations[:num_variations]):
            if variation_strategy == "style":
                config = GenerationConfig(
                    provider=ImageProvider.FLUX_DEV,
                    style=variation,
                    quality="high",
                    seed=42 + i  # Different seeds for variation
                )
                prompt = base_prompt
            else:
                config = GenerationConfig(
                    provider=ImageProvider.FLUX_DEV,
                    style=ImageStyle.PHOTOREALISTIC,
                    quality="high",
                    seed=42 + i
                )
                prompt = f"{base_prompt}, {variation}"

            tasks.append(self.image_generator.generate(prompt, config))

        results = await asyncio.gather(*tasks)

        logger.info(f"✅ Generated {len(results)} A/B test variations")
        return results

    async def generate_platform_optimized_creatives(
        self,
        product_desc: str,
        platforms: List[str] = ["meta", "google", "tiktok"]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate platform-optimized creatives (images + specs).

        Args:
            product_desc: Product description
            platforms: List of platforms

        Returns:
            Dictionary with platform-specific creatives
        """
        logger.info(f"🎯 Generating platform-optimized creatives for: {', '.join(platforms)}")

        results = {}

        for platform in platforms:
            if platform == "meta":
                # Meta: Feed (1:1), Story (9:16), Reels (9:16)
                feed_config = GenerationConfig(
                    provider=ImageProvider.FLUX_PRO,
                    aspect_ratio=AspectRatio.SQUARE_1_1,
                    style=ImageStyle.PRODUCT
                )
                story_config = GenerationConfig(
                    provider=ImageProvider.FLUX_DEV,
                    aspect_ratio=AspectRatio.PORTRAIT_9_16,
                    style=ImageStyle.VIBRANT
                )

                feed = await self.image_generator.generate_product_shot(
                    product_desc,
                    style="clean product photography",
                    config=feed_config
                )

                story = await self.image_generator.generate_product_shot(
                    product_desc,
                    style="dynamic and eye-catching",
                    config=story_config
                )

                results["meta"] = {
                    "feed": feed,
                    "story": story,
                    "specs": {
                        "feed": "1080x1080",
                        "story": "1080x1920"
                    }
                }

            elif platform == "google":
                # Google: YouTube (16:9), Display (various)
                youtube_config = GenerationConfig(
                    provider=ImageProvider.FLUX_DEV,
                    aspect_ratio=AspectRatio.LANDSCAPE_16_9,
                    style=ImageStyle.CINEMATIC
                )

                youtube = await self.image_generator.generate_thumbnail(
                    f"Product showcase: {product_desc}",
                    style="attention-grabbing",
                    platform="youtube",
                    config=youtube_config
                )

                results["google"] = {
                    "youtube": youtube,
                    "specs": {
                        "youtube": "1920x1080"
                    }
                }

            elif platform == "tiktok":
                # TikTok: Vertical only (9:16)
                tiktok_config = GenerationConfig(
                    provider=ImageProvider.FLUX_SCHNELL,
                    aspect_ratio=AspectRatio.PORTRAIT_9_16,
                    style=ImageStyle.VIBRANT
                )

                tiktok = await self.image_generator.generate_product_shot(
                    product_desc,
                    style="bold and trendy",
                    config=tiktok_config
                )

                results["tiktok"] = {
                    "vertical": tiktok,
                    "specs": {
                        "vertical": "1080x1920"
                    }
                }

        logger.info(f"✅ Generated creatives for {len(results)} platforms")
        return results

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _generate_lifestyle_prompts(
        self,
        product_name: str,
        brand_style: str,
        num_prompts: int
    ) -> List[str]:
        """Generate diverse lifestyle scene prompts"""
        scenarios = [
            f"Person using {product_name} in modern home office",
            f"Active lifestyle with {product_name} outdoors",
            f"Professional setting showcasing {product_name}",
            f"Casual everyday moments with {product_name}",
            f"Aspirational lifestyle featuring {product_name}"
        ]

        return [
            f"{scenarios[i % len(scenarios)]}, {brand_style} aesthetic"
            for i in range(num_prompts)
        ]

    def _meta_aspect_to_image_aspect(self, meta_aspect) -> AspectRatio:
        """Convert Meta AspectRatio enum to ImageGenerator AspectRatio enum"""
        # Meta AspectRatio is imported from smart_crop
        # Map to image generator AspectRatio
        aspect_map = {
            "SQUARE_1_1": AspectRatio.SQUARE_1_1,
            "PORTRAIT_4_5": AspectRatio.PORTRAIT_4_5,
            "PORTRAIT_9_16": AspectRatio.PORTRAIT_9_16,
            "LANDSCAPE_16_9": AspectRatio.LANDSCAPE_16_9,
        }

        aspect_str = str(meta_aspect).split('.')[-1]
        return aspect_map.get(aspect_str, AspectRatio.SQUARE_1_1)

    # ========================================================================
    # EXPORT & MANIFEST
    # ========================================================================

    def generate_manifest(
        self,
        package: DCOImagePackage,
        output_path: str
    ):
        """Generate JSON manifest of image package"""
        manifest = {
            "generated_at": package.metadata.get("generated_at", ""),
            "product_name": package.metadata.get("product_name", ""),
            "brand_style": package.metadata.get("brand_style", ""),
            "total_cost": package.total_cost,
            "generation_time": package.generation_time,
            "product_shots": [
                {
                    "path": img.image_path,
                    "provider": img.provider.value,
                    "cost": img.cost_estimate
                }
                for img in package.product_shots
            ],
            "lifestyle_images": [
                {
                    "path": img.image_path,
                    "provider": img.provider.value,
                    "cost": img.cost_estimate
                }
                for img in package.lifestyle_images
            ],
            "thumbnails": {
                platform: {
                    "path": img.image_path,
                    "provider": img.provider.value,
                    "cost": img.cost_estimate
                }
                for platform, img in package.thumbnails.items()
            }
        }

        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"📋 Manifest saved: {output_path}")


# Convenience function
async def generate_full_ad_from_product(
    product_name: str,
    product_desc: str,
    brand_style: str = "modern and professional"
) -> DCOImagePackage:
    """
    FULLY AUTOMATED: Generate complete ad package from product description.

    Example:
        package = await generate_full_ad_from_product(
            "AirPods Pro",
            "Premium wireless earbuds with active noise cancellation",
            "Apple minimalist"
        )
    """
    integration = DCOImageIntegration()

    config = DCOImageConfig(
        product_name=product_name,
        product_desc=product_desc,
        brand_style=brand_style,
        generate_product_shots=True,
        generate_lifestyle=True,
        generate_thumbnails=True,
        num_product_variants=3,
        num_lifestyle_variants=2
    )

    return await integration.generate_complete_package(config)


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        print("=" * 80)
        print("DCO Image Integration - Agent 37")
        print("FULLY AUTOMATED Ad Creation from Product Description")
        print("=" * 80)

        integration = DCOImageIntegration()

        # Example: Complete package
        print("\n[Example] Generating complete ad package...")
        config = DCOImageConfig(
            product_name="FitnessPro Smartwatch",
            product_desc="Advanced fitness tracker with heart rate monitoring and GPS",
            brand_style="modern and energetic",
            num_product_variants=2,
            num_lifestyle_variants=1
        )

        package = await integration.generate_complete_package(config)

        print(f"\n✅ Package Complete:")
        print(f"  Product Shots: {len(package.product_shots)}")
        print(f"  Lifestyle Images: {len(package.lifestyle_images)}")
        print(f"  Thumbnails: {len(package.thumbnails)}")
        print(f"  Total Cost: ${package.total_cost:.4f}")
        print(f"  Generation Time: {package.generation_time:.2f}s")

        # Save manifest
        integration.generate_manifest(package, "/tmp/dco_images/manifest.json")

        print("\n" + "=" * 80)
        print("FULLY AUTOMATED Ad Creation - READY FOR PRODUCTION")
        print("=" * 80)

    # Run example
    # asyncio.run(main())

    print("DCO Image Integration initialized. Ready for production use.")
