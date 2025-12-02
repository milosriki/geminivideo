#!/usr/bin/env python3
"""
Demo: Complete Winning Ads Generator
Shows all features and templates in action
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from winning_ads_generator import (
    WinningAdsGenerator,
    AdAssets,
    AdConfig,
    AdTemplate,
    ColorGradePreset,
    HookStyle,
    CaptionStyle,
    Platform,
    AspectRatio,
    QualityPreset,
    CTAType,
    create_winning_ad,
    create_ab_test_variants
)


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def demo_1_fitness_transformation():
    """Demo 1: Fitness Transformation Ad"""
    print_section("DEMO 1: Fitness Transformation Ad")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo1")

    assets = AdAssets(
        video_clips=[
            "/path/to/hook_dramatic.mp4",
            "/path/to/before_workout.mp4",
            "/path/to/training_montage_1.mp4",
            "/path/to/training_montage_2.mp4",
            "/path/to/training_montage_3.mp4",
            "/path/to/after_results.mp4",
        ],
        audio_tracks=["/path/to/motivational_music.mp3"],
        logo="/path/to/gym_logo.png"
    )

    config = AdConfig(
        template=AdTemplate.FITNESS_TRANSFORMATION,
        platform=Platform.INSTAGRAM,
        aspect_ratio=AspectRatio.VERTICAL,
        duration=30.0,
        hook_style=HookStyle.TRANSFORMATION,
        hook_text="90 Days. Same Person. Different Life.",
        color_grade=ColorGradePreset.HIGH_CONTRAST_PUNCHY,
        caption_style=CaptionStyle.HORMOZI,
        add_captions=True,
        audio_ducking=True,
        voice_enhancement=True,
        show_logo=True,
        logo_position="top_right",
        cta_text="Start Your Transformation",
        cta_style=CTAType.LEARN_MORE,
        add_urgency=True,
        quality_preset=QualityPreset.HIGH
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Platform: {config.platform.value}")
    print(f"  Hook: {config.hook_text}")
    print(f"  Color Grade: {config.color_grade.value}")
    print(f"  Duration: {config.duration}s")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="fitness_transformation.mp4"
    )

    print("\n✅ Ad Generated!")
    print(f"  Output: {output.video_path}")
    print(f"  Thumbnail: {output.thumbnail_path}")
    print(f"\n📊 Predicted Metrics:")
    print(f"  Engagement Score: {output.metrics['engagement_score']}/10")
    print(f"  CTR: {output.metrics['predicted_ctr']}")
    print(f"  Conversion: {output.metrics['predicted_conversion']}")
    print(f"  Watch Time: {output.metrics['predicted_watch_time']}")


def demo_2_testimonial():
    """Demo 2: Testimonial Ad with Lower Third"""
    print_section("DEMO 2: Testimonial Ad")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo2")

    assets = AdAssets(
        testimonial_clips=["/path/to/customer_testimonial.mp4"],
        logo="/path/to/brand_logo.png"
    )

    config = AdConfig(
        template=AdTemplate.TESTIMONIAL,
        platform=Platform.TIKTOK,
        aspect_ratio=AspectRatio.VERTICAL,
        duration=30.0,
        hook_style=HookStyle.QUESTION,
        hook_text="Does this actually work?",
        color_grade=ColorGradePreset.WARM_INVITING,
        caption_style=CaptionStyle.UGC_CASUAL,
        add_captions=True,
        cta_text="Try It Free",
        add_urgency=False  # Testimonials should feel authentic
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Platform: {config.platform.value}")
    print(f"  Style: Authentic testimonial with lower third")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="testimonial_ad.mp4"
    )

    print(f"\n✅ Testimonial ad created: {output.video_path}")
    print(f"📊 Engagement Score: {output.metrics['engagement_score']}/10")


def demo_3_problem_solution():
    """Demo 3: Problem-Solution Ad"""
    print_section("DEMO 3: Problem-Solution Ad")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo3")

    assets = AdAssets(
        video_clips=[
            "/path/to/frustrated_user.mp4",
            "/path/to/show_problem.mp4",
            "/path/to/introduce_product.mp4",
            "/path/to/product_demo.mp4",
        ],
        audio_tracks=["/path/to/background_music.mp3"],
        product_images=["/path/to/product_shot.jpg"]
    )

    config = AdConfig(
        template=AdTemplate.PROBLEM_SOLUTION,
        platform=Platform.FACEBOOK,
        aspect_ratio=AspectRatio.SQUARE,
        duration=30.0,
        hook_style=HookStyle.PAIN_POINT,
        hook_text="Tired of wasting hours on...",
        color_grade=ColorGradePreset.VIBRANT_SATURATED,
        caption_style=CaptionStyle.HORMOZI,
        add_captions=True,
        cta_text="Get Solution Now",
        add_urgency=True,
        add_price_tag=True,
        price_text="$29.99 Today Only"
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Hook: Pain point identification")
    print(f"  Price tag: {config.price_text}")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="problem_solution_ad.mp4"
    )

    print(f"\n✅ Problem-solution ad created: {output.video_path}")
    print(f"💰 Predicted Conversion: {output.metrics['predicted_conversion']}")


def demo_4_listicle():
    """Demo 4: Listicle Ad (5 Tips)"""
    print_section("DEMO 4: Listicle Ad (5 Tips Format)")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo4")

    assets = AdAssets(
        video_clips=[
            "/path/to/tip1_video.mp4",
            "/path/to/tip2_video.mp4",
            "/path/to/tip3_video.mp4",
            "/path/to/tip4_video.mp4",
            "/path/to/tip5_video.mp4",
        ],
        audio_tracks=["/path/to/upbeat_music.mp3"]
    )

    config = AdConfig(
        template=AdTemplate.LISTICLE,
        platform=Platform.YOUTUBE,
        aspect_ratio=AspectRatio.HORIZONTAL,
        duration=30.0,
        hook_style=HookStyle.PROMISE,
        hook_text="5 Tips to 10X Your Results",
        color_grade=ColorGradePreset.YOUTUBE_THUMBNAIL,
        caption_style=CaptionStyle.MR_BEAST,
        add_captions=True,
        cta_text="Subscribe for More",
        add_transitions=True
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Format: 5 tips with numbered overlays")
    print(f"  Platform: YouTube (16:9)")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="listicle_5tips.mp4"
    )

    print(f"\n✅ Listicle ad created: {output.video_path}")


def demo_5_ugc_style():
    """Demo 5: UGC (User Generated Content) Style Ad"""
    print_section("DEMO 5: UGC Style Ad")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo5")

    assets = AdAssets(
        video_clips=["/path/to/raw_ugc_video.mp4"],
        # No music - keep it raw and authentic
    )

    config = AdConfig(
        template=AdTemplate.UGC_STYLE,
        platform=Platform.TIKTOK,
        aspect_ratio=AspectRatio.VERTICAL,
        duration=30.0,
        hook_style=HookStyle.PATTERN_INTERRUPT,
        hook_text="OK so I tried this and...",
        color_grade=ColorGradePreset.NATURAL_ORGANIC,  # Keep it natural
        caption_style=CaptionStyle.UGC_CASUAL,
        add_captions=True,
        audio_ducking=False,  # No background music
        show_logo=False,  # Keep it authentic
        cta_text="Link in Bio",
        add_urgency=False  # Don't over-polish UGC
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Style: Raw, authentic, unpolished")
    print(f"  Perfect for: TikTok organic reach")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="ugc_style_ad.mp4"
    )

    print(f"\n✅ UGC ad created: {output.video_path}")


def demo_6_product_showcase():
    """Demo 6: Product Showcase Ad"""
    print_section("DEMO 6: Product Showcase Ad")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo6")

    assets = AdAssets(
        product_images=[
            "/path/to/product_angle1.jpg",
            "/path/to/product_angle2.jpg",
            "/path/to/product_angle3.jpg",
        ],
        video_clips=["/path/to/product_demo.mp4"],
        logo="/path/to/brand_logo.png"
    )

    config = AdConfig(
        template=AdTemplate.PRODUCT_SHOWCASE,
        platform=Platform.INSTAGRAM,
        aspect_ratio=AspectRatio.SQUARE,
        duration=30.0,
        hook_style=HookStyle.BOLD_STATEMENT,
        hook_text="The #1 Rated Product",
        color_grade=ColorGradePreset.INSTAGRAM_FEED,
        caption_style=CaptionStyle.PROFESSIONAL,
        add_captions=True,
        cta_text="Shop Now",
        add_price_tag=True,
        price_text="50% OFF - $49.99"
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Features highlighted: 3")
    print(f"  Price: {config.price_text}")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="product_showcase.mp4"
    )

    print(f"\n✅ Product showcase created: {output.video_path}")


def demo_7_hook_story_offer():
    """Demo 7: Hook-Story-Offer (Classic Direct Response)"""
    print_section("DEMO 7: Hook-Story-Offer Format")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo7")

    assets = AdAssets(
        video_clips=[
            "/path/to/hook_video.mp4",
            "/path/to/story_video.mp4",
            "/path/to/offer_video.mp4",
        ],
        audio_tracks=["/path/to/dramatic_music.mp3"]
    )

    config = AdConfig(
        template=AdTemplate.HOOK_STORY_OFFER,
        platform=Platform.FACEBOOK,
        aspect_ratio=AspectRatio.SQUARE,
        duration=30.0,
        hook_style=HookStyle.CURIOSITY_GAP,
        hook_text="The one thing that changed everything...",
        color_grade=ColorGradePreset.CINEMATIC_TEAL_ORANGE,
        caption_style=CaptionStyle.ALEX_HORMOZI_CLASSIC,
        add_captions=True,
        audio_ducking=True,
        cta_text="Claim Your Spot",
        add_urgency=True
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Format: Hook → Story → Offer → CTA")
    print(f"  Best for: Direct response campaigns")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="hook_story_offer.mp4"
    )

    print(f"\n✅ Hook-Story-Offer ad created: {output.video_path}")
    print(f"💰 Predicted Conversion: {output.metrics['predicted_conversion']}")


def demo_8_comparison_ad():
    """Demo 8: Comparison Ad (Before/After or Us vs Them)"""
    print_section("DEMO 8: Comparison Ad")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo8")

    assets = AdAssets(
        video_clips=[
            "/path/to/old_way.mp4",
            "/path/to/new_way.mp4",
        ]
    )

    config = AdConfig(
        template=AdTemplate.COMPARISON,
        platform=Platform.INSTAGRAM,
        aspect_ratio=AspectRatio.VERTICAL,
        duration=30.0,
        hook_style=HookStyle.BOLD_STATEMENT,
        hook_text="The difference is INSANE",
        color_grade=ColorGradePreset.HIGH_CONTRAST_PUNCHY,
        caption_style=CaptionStyle.VIRAL_TIKTOK,
        add_captions=True,
        cta_text="Switch Now"
    )

    print("\n📋 Configuration:")
    print(f"  Template: {config.template.value}")
    print(f"  Format: Old way ❌ vs New way ✅")

    output = generator.generate_winning_ad(
        assets=assets,
        config=config,
        output_filename="comparison_ad.mp4"
    )

    print(f"\n✅ Comparison ad created: {output.video_path}")


def demo_9_ab_testing():
    """Demo 9: A/B Testing - Generate 5 Variants"""
    print_section("DEMO 9: A/B Testing - Generate 5 Variants")

    print("\n🔬 Generating 5 variants for A/B testing...")
    print("   Varying: hook_text, color_grade, cta_text")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo9")

    assets = AdAssets(
        video_clips=[
            "/path/to/main_video.mp4",
            "/path/to/broll_1.mp4",
            "/path/to/broll_2.mp4",
        ]
    )

    config = AdConfig(
        template=AdTemplate.PROBLEM_SOLUTION,
        platform=Platform.INSTAGRAM,
        duration=30.0
    )

    variants = generator.batch_generate_variants(
        base_video=assets.video_clips[0],
        assets=assets,
        config=config,
        count=5,
        vary_params=["hook_text", "color_grade", "cta_text"]
    )

    print(f"\n✅ Generated {len(variants)} variants for A/B testing:")
    for i, variant in enumerate(variants, 1):
        variations = variant.metadata.get("variations", {})
        print(f"\n  Variant {i}:")
        print(f"    File: {variant.video_path}")
        print(f"    Hook: {variations.get('hook_text', 'N/A')}")
        print(f"    Color: {variations.get('color_grade', 'N/A')}")
        print(f"    CTA: {variations.get('cta_text', 'N/A')}")
        print(f"    Engagement Score: {variant.metrics['engagement_score']}/10")

    print("\n💡 Run these variants simultaneously to find the winner!")


def demo_10_all_color_grades():
    """Demo 10: Show All Color Grade Presets"""
    print_section("DEMO 10: All Color Grade Presets")

    print("\n🎨 Available Color Grading Presets:")
    print("\n  Performance-Optimized Presets:")
    print("    • CINEMATIC_TEAL_ORANGE - Classic Hollywood look")
    print("    • HIGH_CONTRAST_PUNCHY - Maximum impact")
    print("    • VIBRANT_SATURATED - Eye-catching colors")
    print("    • TIKTOK_VIRAL - Optimized for TikTok algorithm")
    print("    • INSTAGRAM_FEED - Perfect for IG aesthetic")
    print("    • YOUTUBE_THUMBNAIL - Clickable thumbnails")

    print("\n  Mood-Based Presets:")
    print("    • WARM_INVITING - Friendly, approachable")
    print("    • COOL_PROFESSIONAL - Corporate, trustworthy")
    print("    • MOODY_DARK - Dramatic, mysterious")
    print("    • CLEAN_BRIGHT - Fresh, energetic")
    print("    • NATURAL_ORGANIC - Authentic, raw")
    print("    • VINTAGE_FILM - Nostalgic, classic")

    print("\n🔬 Testing color grades on sample video...")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo10")

    test_video = "/path/to/test_video.mp4"

    # Test a few presets
    presets_to_test = [
        ColorGradePreset.TIKTOK_VIRAL,
        ColorGradePreset.CINEMATIC_TEAL_ORANGE,
        ColorGradePreset.VIBRANT_SATURATED,
    ]

    for preset in presets_to_test:
        output = generator.apply_winning_color_grade(test_video, preset)
        print(f"  ✓ {preset.value} → {output}")


def demo_11_standalone_functions():
    """Demo 11: Standalone Utility Functions"""
    print_section("DEMO 11: Standalone Utility Functions")

    generator = WinningAdsGenerator(output_dir="/tmp/winning_ads/demo11")

    test_video = "/path/to/test_video.mp4"

    print("\n🎯 Testing individual features:")

    # 1. Hook optimization
    print("\n  1. Hook Optimization (first 3 seconds)")
    hooked = generator.add_hook_optimization(
        test_video,
        hook_style=HookStyle.PATTERN_INTERRUPT,
        hook_text="WAIT! Don't scroll yet..."
    )
    print(f"     Output: {hooked}")

    # 2. Color grading
    print("\n  2. Color Grading")
    graded = generator.apply_winning_color_grade(
        test_video,
        ColorGradePreset.VIBRANT_SATURATED
    )
    print(f"     Output: {graded}")

    # 3. Captions
    print("\n  3. Hormozi-Style Captions")
    captioned = generator.add_captions_hormozi_style(
        test_video,
        transcript="This is how you create winning ads",
        style=CaptionStyle.HORMOZI
    )
    print(f"     Output: {captioned}")

    # 4. Audio ducking
    print("\n  4. Audio Ducking")
    ducked = generator.add_audio_ducking(test_video, music_volume=0.3)
    print(f"     Output: {ducked}")

    # 5. Voice enhancement
    print("\n  5. Voice Enhancement")
    enhanced = generator.add_voice_enhancement(test_video)
    print(f"     Output: {enhanced}")

    # 6. Smart cropping
    print("\n  6. Smart Crop to Vertical (9:16)")
    cropped = generator.smart_crop_vertical(
        test_video,
        AspectRatio.VERTICAL,
        auto_detect_subject=True
    )
    print(f"     Output: {cropped}")

    # 7. CTA overlay
    print("\n  7. CTA Overlay")
    cta = generator.add_cta_overlay(
        test_video,
        cta_text="Shop Now",
        cta_type=CTAType.SHOP_NOW,
        start_time=25.0
    )
    print(f"     Output: {cta}")

    # 8. Platform optimization
    print("\n  8. Platform Optimization")
    optimized = generator.optimize_for_platform(test_video, Platform.TIKTOK)
    print(f"     Output: {optimized}")


def demo_12_quick_create():
    """Demo 12: Quick Create with Defaults"""
    print_section("DEMO 12: Quick Create Function")

    print("\n⚡ Quick create winning ad with defaults:")

    video_clips = [
        "/path/to/clip1.mp4",
        "/path/to/clip2.mp4",
        "/path/to/clip3.mp4",
    ]

    # One-liner to create an ad
    output = create_winning_ad(
        video_clips=video_clips,
        template=AdTemplate.PROBLEM_SOLUTION,
        platform=Platform.INSTAGRAM,
        output_dir="/tmp/winning_ads/quick"
    )

    print(f"\n✅ Quick ad created: {output.video_path}")
    print(f"📊 Engagement Score: {output.metrics['engagement_score']}/10")

    print("\n💡 Use create_winning_ad() for fast prototyping!")


def show_all_features():
    """Show comprehensive feature list"""
    print_section("COMPLETE FEATURE LIST")

    print("""
📋 10 AD TEMPLATES:
   1. Fitness Transformation (before/after)
   2. Testimonial with lower third
   3. Problem-Solution format
   4. Listicle (5 tips format)
   5. Hook-Story-Offer
   6. UGC style
   7. Educational/how-to
   8. Product showcase
   9. Comparison ad
   10. Behind-the-scenes

🎨 12 COLOR GRADING PRESETS:
   • Cinematic Teal Orange    • High Contrast Punchy
   • Warm Inviting            • Cool Professional
   • Vibrant Saturated        • Moody Dark
   • Clean Bright             • Vintage Film
   • Instagram Feed           • TikTok Viral
   • YouTube Thumbnail        • Natural Organic

🎯 8 HOOK STYLES:
   • Question                 • Bold Statement
   • Pattern Interrupt        • Promise
   • Pain Point               • Curiosity Gap
   • Shocking Stat            • Transformation

💬 7 CAPTION STYLES:
   • Hormozi (yellow emphasis)    • Alex Hormozi Classic
   • Mr Beast (large centered)    • UGC Casual
   • Professional                 • Viral TikTok
   • Netflix Style

📱 PLATFORM OPTIMIZATION:
   • TikTok (1080x1920, 30fps, 3min max)
   • Instagram Reels (1080x1920, 30fps, 90s max)
   • YouTube (1920x1080, 60fps, unlimited)
   • Facebook (1280x720, 30fps)
   • Twitter (1280x720, 30fps, 140s max)

✨ PRO FEATURES:
   ✓ Hook optimization (first 3 seconds)
   ✓ Auto-captions with speech sync
   ✓ Audio ducking (auto-lower music)
   ✓ Voice enhancement
   ✓ Smart cropping (AI subject detection)
   ✓ Motion graphics (CTAs, overlays)
   ✓ Transition library
   ✓ A/B test variant generation
   ✓ Engagement prediction
   ✓ Batch processing

🎬 RENDER QUALITY:
   • Draft (fast preview)
   • Standard (good quality)
   • High (production ready)
   • Master (maximum quality)
    """)


def main():
    """Main demo runner"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "    COMPLETE WINNING ADS GENERATOR - PRO DEMO".center(78) + "║")
    print("║" + "    Master Orchestrator for High-Converting Video Ads".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")

    show_all_features()

    print("\n\n" + "=" * 80)
    print("  SELECT DEMO TO RUN")
    print("=" * 80)
    print("""
  1.  Fitness Transformation Ad
  2.  Testimonial Ad
  3.  Problem-Solution Ad
  4.  Listicle (5 Tips) Ad
  5.  UGC Style Ad
  6.  Product Showcase Ad
  7.  Hook-Story-Offer Ad
  8.  Comparison Ad
  9.  A/B Testing (5 Variants)
  10. All Color Grades
  11. Standalone Functions
  12. Quick Create Demo
  13. Run ALL Demos

  0.  Exit
    """)

    # For documentation purposes, show what each demo does
    print("\n💡 TIP: This is a demonstration script.")
    print("   Update video paths before running in production.")
    print("   All paths currently use placeholder '/path/to/' values.\n")

    # Demo selection (commented out for documentation)
    # choice = input("Enter demo number (1-13, or 0 to exit): ").strip()

    # In a real scenario, you would uncomment and run:
    """
    demos = {
        "1": demo_1_fitness_transformation,
        "2": demo_2_testimonial,
        "3": demo_3_problem_solution,
        "4": demo_4_listicle,
        "5": demo_5_ugc_style,
        "6": demo_6_product_showcase,
        "7": demo_7_hook_story_offer,
        "8": demo_8_comparison_ad,
        "9": demo_9_ab_testing,
        "10": demo_10_all_color_grades,
        "11": demo_11_standalone_functions,
        "12": demo_12_quick_create,
    }

    if choice == "13":
        for demo_func in demos.values():
            demo_func()
    elif choice in demos:
        demos[choice]()
    elif choice == "0":
        print("\n👋 Goodbye!")
        return
    else:
        print("\n❌ Invalid choice")
    """

    print("\n" + "=" * 80)
    print("  QUICK START EXAMPLES")
    print("=" * 80)

    print("""
# Example 1: Quick one-liner
from winning_ads_generator import create_winning_ad, AdTemplate, Platform

output = create_winning_ad(
    video_clips=["clip1.mp4", "clip2.mp4"],
    template=AdTemplate.PROBLEM_SOLUTION,
    platform=Platform.INSTAGRAM
)

# Example 2: Full control
from winning_ads_generator import (
    WinningAdsGenerator, AdAssets, AdConfig,
    ColorGradePreset, CaptionStyle
)

generator = WinningAdsGenerator()
assets = AdAssets(video_clips=["video.mp4"])
config = AdConfig(
    template=AdTemplate.FITNESS_TRANSFORMATION,
    color_grade=ColorGradePreset.TIKTOK_VIRAL,
    caption_style=CaptionStyle.HORMOZI
)
output = generator.generate_winning_ad(assets, config)

# Example 3: A/B testing
from winning_ads_generator import create_ab_test_variants

variants = create_ab_test_variants(
    video_clips=["base.mp4"],
    template=AdTemplate.HOOK_STORY_OFFER,
    platform=Platform.TIKTOK,
    count=5
)

print(f"Created {len(variants)} test variants!")
    """)

    print("\n" + "=" * 80)
    print("✅ Demo script ready!")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
