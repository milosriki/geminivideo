# 🏆 Winning Ads Generator - Quick Reference

## One-Liner Quick Start

```python
from winning_ads_generator import create_winning_ad, AdTemplate, Platform

output = create_winning_ad(
    video_clips=["clip1.mp4", "clip2.mp4"],
    template=AdTemplate.PROBLEM_SOLUTION,
    platform=Platform.INSTAGRAM
)
```

## Templates (10)

| # | Template | Use Case | Hook |
|---|----------|----------|------|
| 1 | `FITNESS_TRANSFORMATION` | Fitness, health | Transformation |
| 2 | `TESTIMONIAL` | Social proof | Question |
| 3 | `PROBLEM_SOLUTION` | Most products | Pain Point |
| 4 | `LISTICLE` | Tips, education | Promise |
| 5 | `HOOK_STORY_OFFER` | High-ticket | Curiosity Gap |
| 6 | `UGC_STYLE` | Organic reach | Pattern Interrupt |
| 7 | `EDUCATIONAL` | How-to | Question |
| 8 | `PRODUCT_SHOWCASE` | E-commerce | Bold Statement |
| 9 | `COMPARISON` | Competitive | Bold Statement |
| 10 | `BEHIND_SCENES` | Brand building | Curiosity Gap |

## Color Grades (12)

**High Conversion:**
- `TIKTOK_VIRAL` - Algorithm-optimized
- `VIBRANT_SATURATED` - Eye-catching
- `HIGH_CONTRAST_PUNCHY` - Maximum impact

**Platform-Specific:**
- `INSTAGRAM_FEED` - IG aesthetic
- `YOUTUBE_THUMBNAIL` - Clickable

**Mood-Based:**
- `CINEMATIC_TEAL_ORANGE` - Premium
- `WARM_INVITING` - Friendly
- `NATURAL_ORGANIC` - Authentic

## Hook Styles (8)

```python
HookStyle.QUESTION           # "Are you struggling with...?"
HookStyle.BOLD_STATEMENT     # "This will change everything"
HookStyle.PATTERN_INTERRUPT  # "STOP! You need to see this"
HookStyle.PROMISE            # "In 30 seconds, you'll know..."
HookStyle.PAIN_POINT         # "Tired of wasting money on...?"
HookStyle.CURIOSITY_GAP      # "The one thing nobody tells you..."
HookStyle.SHOCKING_STAT      # "97% of people don't know this"
HookStyle.TRANSFORMATION     # "Watch this incredible change"
```

## Caption Styles (7)

```python
CaptionStyle.HORMOZI              # ⭐ HIGHEST CONVERSION
CaptionStyle.ALEX_HORMOZI_CLASSIC # Bold yellow
CaptionStyle.MR_BEAST             # Large centered
CaptionStyle.UGC_CASUAL           # Small, authentic
CaptionStyle.PROFESSIONAL         # Subtle, elegant
CaptionStyle.VIRAL_TIKTOK         # Animated, bouncing
CaptionStyle.NETFLIX_STYLE        # Centered white
```

## Platforms (5)

| Platform | Resolution | FPS | Max Duration |
|----------|-----------|-----|--------------|
| `TIKTOK` | 1080x1920 | 30 | 3 min |
| `INSTAGRAM` | 1080x1920 | 30 | 90 sec |
| `YOUTUBE` | 1920x1080 | 60 | Unlimited |
| `FACEBOOK` | 1280x720 | 30 | Unlimited |
| `TWITTER` | 1280x720 | 30 | 140 sec |

## Complete Example

```python
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
    CTAType
)

# 1. Initialize
generator = WinningAdsGenerator(output_dir="/tmp/my_ads")

# 2. Prepare Assets
assets = AdAssets(
    video_clips=["hook.mp4", "main.mp4", "cta.mp4"],
    audio_tracks=["music.mp3"],
    logo="logo.png"
)

# 3. Configure
config = AdConfig(
    # Template & Platform
    template=AdTemplate.PROBLEM_SOLUTION,
    platform=Platform.INSTAGRAM,
    aspect_ratio=AspectRatio.VERTICAL,
    duration=30.0,

    # Hook (First 3 seconds - CRITICAL)
    hook_style=HookStyle.PAIN_POINT,
    hook_text="Tired of wasting money?",
    hook_duration=3.0,

    # Visual
    color_grade=ColorGradePreset.VIBRANT_SATURATED,
    caption_style=CaptionStyle.HORMOZI,
    add_captions=True,

    # Audio
    audio_ducking=True,
    voice_enhancement=True,
    music_volume=0.3,

    # Branding
    show_logo=True,
    logo_position="top_right",

    # CTA
    cta_text="Shop Now",
    cta_style=CTAType.SHOP_NOW,

    # Advanced
    add_urgency=True,
    add_price_tag=True,
    price_text="$29.99",
    add_transitions=True
)

# 4. Generate
output = generator.generate_winning_ad(assets, config, "ad.mp4")

# 5. Results
print(f"Video: {output.video_path}")
print(f"Engagement: {output.metrics['engagement_score']}/10")
print(f"CTR: {output.metrics['predicted_ctr']}")
print(f"Conversion: {output.metrics['predicted_conversion']}")
```

## A/B Testing

```python
from winning_ads_generator import create_ab_test_variants

variants = create_ab_test_variants(
    video_clips=["video.mp4"],
    template=AdTemplate.PROBLEM_SOLUTION,
    platform=Platform.INSTAGRAM,
    count=5
)

# Automatically varies: hook_text, color_grade, cta_text
```

## Standalone Functions

```python
generator = WinningAdsGenerator()

# Hook optimization (first 3 seconds)
hooked = generator.add_hook_optimization(
    "video.mp4", HookStyle.PATTERN_INTERRUPT, "STOP!"
)

# Color grading
graded = generator.apply_winning_color_grade(
    "video.mp4", ColorGradePreset.TIKTOK_VIRAL
)

# Captions (Hormozi style)
captioned = generator.add_captions_hormozi_style(
    "video.mp4", "Your transcript", CaptionStyle.HORMOZI
)

# Audio ducking
ducked = generator.add_audio_ducking("video.mp4", music_volume=0.3)

# Voice enhancement
enhanced = generator.add_voice_enhancement("video.mp4")

# Smart crop to vertical
cropped = generator.smart_crop_vertical(
    "video.mp4", AspectRatio.VERTICAL
)

# CTA overlay
cta = generator.add_cta_overlay(
    "video.mp4", "Shop Now", CTAType.SHOP_NOW, start_time=25.0
)

# Platform optimization
optimized = generator.optimize_for_platform(
    "video.mp4", Platform.TIKTOK
)
```

## Platform Best Practices

### TikTok
```python
AdConfig(
    platform=Platform.TIKTOK,
    duration=15.0,  # Keep short!
    hook_style=HookStyle.PATTERN_INTERRUPT,
    color_grade=ColorGradePreset.TIKTOK_VIRAL,
    caption_style=CaptionStyle.VIRAL_TIKTOK
)
```

### Instagram Reels
```python
AdConfig(
    platform=Platform.INSTAGRAM,
    duration=30.0,
    color_grade=ColorGradePreset.INSTAGRAM_FEED,
    caption_style=CaptionStyle.HORMOZI,
    show_logo=True
)
```

### YouTube
```python
AdConfig(
    platform=Platform.YOUTUBE,
    aspect_ratio=AspectRatio.HORIZONTAL,
    duration=60.0,  # Can be longer
    color_grade=ColorGradePreset.CINEMATIC_TEAL_ORANGE,
    caption_style=CaptionStyle.PROFESSIONAL
)
```

## Template-Specific Assets

### Fitness Transformation
```python
assets = AdAssets(
    video_clips=[
        "hook.mp4",      # 0-3s
        "before.mp4",    # 3-8s
        "progress1.mp4", # 8-13s
        "progress2.mp4", # 13-18s
        "progress3.mp4", # 18-23s
        "after.mp4"      # 23-27s
    ],
    audio_tracks=["motivational.mp3"]
)
```

### Testimonial
```python
assets = AdAssets(
    testimonial_clips=["customer_review.mp4"],
    logo="logo.png"
)
```

### Problem-Solution
```python
assets = AdAssets(
    video_clips=[
        "frustrated_user.mp4",
        "show_problem.mp4",
        "introduce_product.mp4",
        "product_demo.mp4"
    ]
)
```

### Listicle
```python
assets = AdAssets(
    video_clips=[
        "tip1.mp4",
        "tip2.mp4",
        "tip3.mp4",
        "tip4.mp4",
        "tip5.mp4"
    ]
)
```

### UGC Style
```python
assets = AdAssets(
    video_clips=["raw_ugc_video.mp4"]
    # Keep it raw - no music, minimal editing
)
```

## Predicted Metrics

```python
output.metrics = {
    "engagement_score": 8.5,      # 0-10
    "predicted_ctr": "5.25%",     # Target: 3-5%
    "predicted_conversion": "2.05%",  # Target: 2-3%
    "predicted_watch_time": "75.5%",  # Target: 70%+
    "confidence": "High"
}
```

## Pro Tips

### 🎯 Hook (80% of Success)
- Keep under 3 seconds
- Test 10+ variations
- Use pattern interrupts on TikTok
- Show end result immediately

### 💬 Captions (80% Watch Without Sound)
- Always add captions
- Use Hormozi style for direct response
- Minimum 52pt font size

### 🎨 Color Grading
- TikTok: Use TIKTOK_VIRAL
- Instagram: Use INSTAGRAM_FEED
- Premium products: Use CINEMATIC_TEAL_ORANGE
- Action products: Use HIGH_CONTRAST_PUNCHY

### 🎵 Audio
- Always duck background music (30% volume)
- Always enhance voice clarity
- Poor audio = instant scroll

### 📱 Platform Optimization
- TikTok: 15s, vertical, high energy
- Instagram: 30s, vertical, aesthetic
- YouTube: 60s, horizontal, cinematic
- Always optimize for each platform

### 🧪 A/B Testing Priority
1. Hook text (highest impact)
2. Color grading
3. CTA text
4. Caption style
5. Video length

### ⚡ Quick Wins
- Add urgency elements (+20% conversion)
- Use social proof (+25% trust)
- Show price early (+15% qualified clicks)
- Mobile-first design (90% mobile traffic)

## Common Mistakes to Avoid

❌ No hook or weak hook
❌ No captions
❌ Poor audio quality
❌ Wrong aspect ratio
❌ No CTA
❌ Too long (TikTok/IG)
❌ Over-polished UGC
❌ Hidden branding
❌ Generic messaging
❌ Not testing variants

## Conversion Boosters

✅ Strong hook (first 3s)
✅ Hormozi-style captions
✅ Audio ducking + voice enhancement
✅ Platform-specific optimization
✅ Clear, visible CTA
✅ Urgency elements
✅ Social proof
✅ Results shown early
✅ Mobile-optimized
✅ A/B testing

## Files

- **Main Module**: `winning_ads_generator.py` (1949 lines)
- **Demo Script**: `demo_winning_ads.py`
- **Full Docs**: `WINNING_ADS_README.md`
- **Quick Ref**: `WINNING_ADS_QUICKREF.md` (this file)

## Status

✅ Production Ready
✅ No Mock Data
✅ Real FFmpeg Implementation
✅ All Features Integrated
✅ 10 Templates
✅ 12 Color Grades
✅ 8 Hook Styles
✅ 7 Caption Styles
✅ 5 Platform Optimizations
✅ A/B Testing
✅ Engagement Prediction

---

**Quick Start in 3 Lines:**

```python
from winning_ads_generator import create_winning_ad, AdTemplate, Platform
output = create_winning_ad(["video.mp4"], AdTemplate.PROBLEM_SOLUTION, Platform.INSTAGRAM)
print(f"✅ Ad created: {output.video_path}")
```

**That's it! You're ready to create winning ads! 🚀**
