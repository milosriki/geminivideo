#!/usr/bin/env python3
"""
Example usage of Motion Graphics Engine with actual FFmpeg commands
"""

from motion_graphics import (
    MotionGraphicsEngine,
    AnimationType,
    LowerThirdStyle,
    TitleCardStyle,
    CTAType,
    AnimatedTextParams,
    LowerThirdParams,
    TitleCardParams,
    create_lower_third,
    create_title_card,
    create_animated_text
)


def example_1_simple_lower_third():
    """Example 1: Add a simple lower third to a video"""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Simple Lower Third")
    print("=" * 70)

    # Create lower third filter
    filter_str = create_lower_third(
        name="John Smith",
        title="CEO & Founder",
        style=LowerThirdStyle.CORPORATE,
        duration=5.0,
        start_time=2.0
    )

    # Show the FFmpeg command
    print("\nFFmpeg Command:")
    print("-" * 70)
    print(f"""
ffmpeg -i input.mp4 \\
  -vf "{filter_str}" \\
  -c:v libx264 -preset medium -crf 23 \\
  -c:a copy \\
  output.mp4
    """)

    print("\nThis will add a corporate-style lower third showing:")
    print("  Name: John Smith")
    print("  Title: CEO & Founder")
    print("  Appears at: 2.0 seconds")
    print("  Duration: 5.0 seconds")


def example_2_animated_title():
    """Example 2: Add animated title card"""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Animated Title Card")
    print("=" * 70)

    # Create title card
    filter_str = create_title_card(
        text="Welcome to Our Show",
        style=TitleCardStyle.CINEMATIC_EPIC,
        duration=3.0,
        subtitle="Season 2, Episode 1"
    )

    print("\nFFmpeg Command:")
    print("-" * 70)
    print(f"""
ffmpeg -i input.mp4 \\
  -vf "{filter_str}" \\
  -c:v libx264 -preset medium -crf 23 \\
  -c:a copy \\
  output.mp4
    """)

    print("\nThis creates a cinematic title card with:")
    print("  Main title: Welcome to Our Show")
    print("  Subtitle: Season 2, Episode 1")
    print("  Style: Epic cinematic with fade-in")


def example_3_bouncing_text():
    """Example 3: Bouncing animated text"""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Bouncing Animated Text")
    print("=" * 70)

    # Create bouncing text
    filter_str = create_animated_text(
        text="SUBSCRIBE NOW!",
        animation_type=AnimationType.BOUNCE_IN,
        duration=2.0,
        font_size=72,
        font_color="yellow"
    )

    print("\nFFmpeg Command:")
    print("-" * 70)
    print(f"""
ffmpeg -i input.mp4 \\
  -vf "{filter_str}" \\
  -c:v libx264 -preset medium -crf 23 \\
  -c:a copy \\
  output.mp4
    """)

    print("\nThis adds bouncing text animation:")
    print("  Text: SUBSCRIBE NOW!")
    print("  Color: Yellow")
    print("  Size: 72pt")
    print("  Animation: Bounce in effect")


def example_4_multiple_elements():
    """Example 4: Multiple motion graphics elements"""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Multiple Elements (Complete Video)")
    print("=" * 70)

    engine = MotionGraphicsEngine()

    # Add multiple elements
    print("\nAdding elements:")
    print("  1. Opening title card (0-3s)")
    engine.create_title_card(
        text="Tutorial: Python Basics",
        style=TitleCardStyle.YOUTUBE_INTRO,
        duration=3.0,
        params=TitleCardParams(start_time=0.0)
    )

    print("  2. Speaker lower third (5-10s)")
    engine.create_lower_third(
        name="Dr. Jane Doe",
        title="Python Expert",
        style=LowerThirdStyle.TECH_NEON,
        duration=5.0,
        params=LowerThirdParams(start_time=5.0)
    )

    print("  3. Subscribe CTA (20-25s)")
    engine.create_cta_overlay(
        CTAType.SUBSCRIBE,
        params=CTAParams(start_time=20.0, duration=5.0)
    )

    print("  4. Progress bar (0-30s)")
    engine.create_progress_bar(total_duration=30.0)

    # Get complete filter
    filter_complex = engine.get_ffmpeg_filter_complex()

    print("\nFFmpeg Command:")
    print("-" * 70)
    print(f"""
ffmpeg -i input.mp4 \\
  -vf "{filter_complex}" \\
  -c:v libx264 -preset medium -crf 23 \\
  -c:a copy \\
  output.mp4
    """)

    print(f"\nTotal elements: {len(engine.elements)}")
    print(f"Filter complex length: {len(filter_complex)} characters")


def example_5_news_broadcast():
    """Example 5: News broadcast style"""
    print("\n" + "=" * 70)
    print("EXAMPLE 5: News Broadcast Style")
    print("=" * 70)

    engine = MotionGraphicsEngine()

    # Breaking news banner
    print("\nCreating breaking news setup:")
    print("  1. Breaking news lower third")
    engine.create_lower_third(
        name="BREAKING NEWS",
        title="Major announcement at City Hall",
        style=LowerThirdStyle.NEWS_BREAKING,
        duration=8.0,
        params=LowerThirdParams(start_time=0.0, accent_color="#CC0000")
    )

    print("  2. Reporter lower third")
    engine.create_lower_third(
        name="Sarah Johnson",
        title="Live from Downtown",
        style=LowerThirdStyle.NEWS_LIVE,
        duration=10.0,
        params=LowerThirdParams(start_time=8.0)
    )

    filter_complex = engine.get_ffmpeg_filter_complex()

    print("\nFFmpeg Command:")
    print("-" * 70)
    print(f"""
ffmpeg -i input.mp4 \\
  -vf "{filter_complex}" \\
  -c:v libx264 -preset medium -crf 23 \\
  -c:a copy \\
  output.mp4
    """)


def example_6_social_media_reel():
    """Example 6: Social media reel with CTAs"""
    print("\n" + "=" * 70)
    print("EXAMPLE 6: Social Media Reel")
    print("=" * 70)

    engine = MotionGraphicsEngine()

    print("\nCreating viral social media content:")
    print("  1. Attention-grabbing hook (0-2s)")
    engine.create_title_card(
        text="You Won't Believe This!",
        style=TitleCardStyle.SOCIAL_HOOK,
        duration=2.0,
        params=TitleCardParams(start_time=0.0, accent_color="#FF00FF")
    )

    print("  2. Social engagement elements (5-10s)")
    engine.create_social_element(
        "like",
        count=15000,
        params=AnimatedTextParams(
            start_time=5.0,
            duration=5.0,
            position_x="50",
            position_y="200"
        )
    )

    print("  3. Follow CTA (12-17s)")
    engine.create_cta_overlay(
        CTAType.FOLLOW,
        custom_text="FOLLOW FOR MORE",
        params=CTAParams(start_time=12.0, duration=5.0, pulse_animation=True)
    )

    print("  4. Link in bio (20-25s)")
    engine.create_cta_overlay(
        CTAType.LINK_IN_BIO,
        params=CTAParams(start_time=20.0, duration=5.0)
    )

    filter_complex = engine.get_ffmpeg_filter_complex()

    print("\nFFmpeg Command:")
    print("-" * 70)
    print(f"""
ffmpeg -i input.mp4 \\
  -vf "{filter_complex}" \\
  -c:v libx264 -preset medium -crf 23 \\
  -c:a copy \\
  output.mp4
    """)

    print(f"\nTotal elements: {len(engine.elements)}")


def example_7_apply_to_video():
    """Example 7: Actually apply filters to a video (if input exists)"""
    print("\n" + "=" * 70)
    print("EXAMPLE 7: Apply to Real Video")
    print("=" * 70)

    engine = MotionGraphicsEngine()

    # Create a simple setup
    engine.create_title_card(
        text="Motion Graphics Demo",
        style=TitleCardStyle.CINEMATIC_EPIC,
        duration=3.0
    )

    engine.create_lower_third(
        name="Demo User",
        title="Motion Graphics Expert",
        style=LowerThirdStyle.CORPORATE,
        duration=5.0,
        params=LowerThirdParams(start_time=3.0)
    )

    print("\nTo apply these filters to a video:")
    print("-" * 70)
    print("""
# Method 1: Using the engine's apply_to_video method
engine.apply_to_video(
    input_video="input.mp4",
    output_video="output.mp4",
    preset="medium",
    crf=23
)

# Method 2: Manual FFmpeg command
filter_complex = engine.get_ffmpeg_filter_complex()
cmd = [
    'ffmpeg',
    '-i', 'input.mp4',
    '-vf', filter_complex,
    '-c:v', 'libx264',
    '-preset', 'medium',
    '-crf', '23',
    '-c:a', 'copy',
    '-y',
    'output.mp4'
]
subprocess.run(cmd, check=True)
    """)

    print("\nNote: Make sure input.mp4 exists before running!")


def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("MOTION GRAPHICS ENGINE - USAGE EXAMPLES")
    print("=" * 70)
    print("\nThese examples show how to use the motion graphics engine")
    print("with real FFmpeg commands for production video editing.")

    # Run all examples
    example_1_simple_lower_third()
    example_2_animated_title()
    example_3_bouncing_text()
    example_4_multiple_elements()
    example_5_news_broadcast()
    example_6_social_media_reel()
    example_7_apply_to_video()

    # Final tips
    print("\n" + "=" * 70)
    print("USAGE TIPS")
    print("=" * 70)
    print("""
1. SINGLE ELEMENT:
   - Use helper functions: create_lower_third(), create_title_card(), etc.
   - Get filter string and use directly in FFmpeg -vf parameter

2. MULTIPLE ELEMENTS:
   - Use MotionGraphicsEngine()
   - Add elements with create_* methods
   - Get complete filter with get_ffmpeg_filter_complex()

3. TIMING:
   - Set start_time parameter for when element appears
   - Set duration for how long it's visible
   - Use enable expressions for precise control

4. CUSTOMIZATION:
   - Use *Params classes for detailed control
   - Adjust colors, sizes, positions, animations
   - Mix and match styles

5. PRODUCTION:
   - Test on short clips first
   - Use preset="fast" for testing, "medium" for production
   - Add -c:a copy to preserve audio without re-encoding
   - Use -y flag to overwrite output files

6. PERFORMANCE:
   - Complex filters may slow rendering
   - Consider using hardware acceleration (-hwaccel)
   - Batch process multiple videos with same settings
    """)

    print("\n" + "=" * 70)
    print("Ready for production use!")
    print("=" * 70)


if __name__ == "__main__":
    main()
