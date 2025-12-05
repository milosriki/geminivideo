# AI VIDEO GENERATION - QUICK START

## 2025's Hottest Feature: Generate Videos from Text

This guide gets you generating AI videos in **5 minutes**.

---

## Why This Matters

**Traditional workflow:**
- Hire videographer: $500-2000
- Wait 1-2 weeks for footage
- Limited revisions

**AI video generation:**
- Cost: $0.10-1.25 per 5-second clip
- Time: 1-2 minutes
- Unlimited revisions

---

## Step 1: Get API Keys (5 minutes)

### Runway Gen-3 (Recommended - Available NOW)

1. Go to https://runwayml.com/
2. Sign up for account
3. Navigate to Settings > API Keys
4. Create new API key
5. Copy key

**Pricing:** ~$0.05/second (~$10 for 200 seconds of video)

### Optional Providers

- **OpenAI Sora**: https://platform.openai.com/ (limited access)
- **Kling AI**: https://klingai.com/
- **Pika Labs**: https://pika.art/

---

## Step 2: Configure Environment (1 minute)

Add to `.env` file:

```bash
# Runway Gen-3 (recommended)
RUNWAY_API_KEY=your_api_key_here

# Optional: OpenAI (for Sora when available)
OPENAI_API_KEY=your_openai_key

# Optional: Others
KLING_API_KEY=your_kling_key
PIKA_API_KEY=your_pika_key
```

---

## Step 3: Test API (2 minutes)

### Using cURL

```bash
# Generate video from text
curl -X POST http://localhost:8002/api/ai-video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "text_to_video",
    "prompt": "Professional product showcase of a smartphone, smooth 360-degree rotation, studio lighting",
    "duration": 5,
    "quality": "draft",
    "aspect_ratio": "9:16",
    "provider": "runway"
  }'

# Response:
# {
#   "status": "queued",
#   "job_id": "abc123",
#   "estimated_cost": 0.10,
#   "status_url": "/api/ai-video/status/abc123"
# }

# Check status
curl http://localhost:8002/api/ai-video/status/abc123

# Response when complete:
# {
#   "status": "completed",
#   "video_url": "https://storage.runwayml.com/output.mp4",
#   "cost": 0.10
# }
```

### Using Python

```python
import asyncio
from pro.ai_video_generator import (
    AIVideoGenerator,
    VideoGenerationRequest,
    GenerationMode,
    QualityTier
)

async def generate_test_video():
    generator = AIVideoGenerator()

    request = VideoGenerationRequest(
        mode=GenerationMode.TEXT_TO_VIDEO,
        prompt="Professional product showcase, smooth camera movement",
        duration=5,
        quality=QualityTier.DRAFT,  # Only $0.10
        aspect_ratio="9:16"
    )

    result = await generator.generate_video(request)

    print(f"Status: {result.status.value}")
    print(f"Video URL: {result.video_url}")
    print(f"Cost: ${result.cost}")

    await generator.close()

asyncio.run(generate_test_video())
```

---

## Common Use Cases

### 1. Generate B-Roll for Ads

```bash
curl -X POST http://localhost:8002/api/ai-video/batch-generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": [
      "Person running on treadmill in modern gym",
      "Close-up of fitness tracker showing data",
      "Healthy meal prep in bright kitchen"
    ],
    "quality": "draft",
    "duration": 5,
    "aspect_ratio": "9:16"
  }'

# Cost: 3 clips × 5 seconds × $0.02/sec = $0.30
```

### 2. Animate Product Photo

```bash
curl -X POST http://localhost:8002/api/ai-video/generate \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "image_to_video",
    "prompt": "Slow zoom in and gentle rotation",
    "image_path": "/path/to/product_photo.jpg",
    "duration": 5,
    "quality": "high",
    "aspect_ratio": "9:16"
  }'

# Cost: 5 seconds × $0.05/sec = $0.25
```

### 3. Create Multiple Variants (A/B Testing)

```python
from pro.ai_campaign_integration import AICampaignIntegration

integration = AICampaignIntegration()

# Generate 5 variants for testing
variants = await integration.create_video_variants(
    "Fitness app demo showing workout tracking",
    variant_count=5,
    quality="draft"  # Only $0.50 total
)

# Test all variants, pick winner
# Regenerate winner in high quality
```

---

## Cost Examples

| Use Case | Videos | Duration | Quality | Cost |
|----------|--------|----------|---------|------|
| B-roll (5 clips) | 5 | 5s each | Draft | $0.50 |
| Product shots (2) | 2 | 5s each | High | $0.50 |
| Transitions (3) | 3 | 3s each | Draft | $0.18 |
| A/B variants (5) | 5 | 5s each | Draft | $0.50 |
| Hero shot (1) | 1 | 10s | Master | $2.50 |

**Total for complete campaign: ~$4.18**

vs. Hiring videographer: $500-2000+

---

## Provider Recommendations

| Provider | Use For | Speed | Quality | Cost |
|----------|---------|-------|---------|------|
| **Pika** | Drafts, iterations | Very Fast | Good | $0.02/s |
| **Runway** | Production (DEFAULT) | Fast | High | $0.05/s |
| **Kling** | Realistic motion | Fast | Good | $0.03/s |
| **Sora** | Premium campaigns | Slow | Best | $0.25/s |

**Default strategy:**
- Use **Pika** for drafts and iterations
- Use **Runway** for final production
- Use **Sora** only for high-budget clients

---

## Integration with Campaigns

### Auto-Generate Missing B-Roll

```python
from pro.ai_campaign_integration import auto_generate_missing_b_roll

campaign = {
    "product_name": "Meditation App",
    "target_audience": "stressed professionals",
    "key_benefits": ["reduce stress", "improve sleep", "increase focus"]
}

# Automatically generates 5 B-roll clips based on campaign
b_roll = await auto_generate_missing_b_roll(campaign, required_b_roll_count=5)

# Cost: ~$0.50 (using draft quality)
```

### Enhance Campaign with AI Assets

```python
from pro.ai_campaign_integration import enhance_campaign_with_ai_video

enhanced = await enhance_campaign_with_ai_video(
    campaign_id="camp_123",
    campaign_config={
        "product_name": "FitnessPro App",
        "b_roll_scenes": [...],
        "product_images": ["app_screen.jpg"],
        ...
    },
    auto_generate=True
)

# Returns campaign with AI-generated B-roll and product animations
```

---

## Troubleshooting

### "Provider not configured"

```bash
# Check environment variables
echo $RUNWAY_API_KEY

# If empty, add to .env:
RUNWAY_API_KEY=your_key_here
```

### "API key invalid"

- Verify API key is correct
- Check if you have credits (Runway requires payment setup)
- Test with provider's playground first

### "Generation failed"

Common reasons:
- **NSFW content detected** - Modify prompt to be more professional
- **Copyright violation** - Don't mention copyrighted brands/characters
- **Server error** - Retry with fallback enabled
- **Insufficient credits** - Add payment method to provider

### Slow generation?

- **Pika**: 5-30 seconds
- **Runway**: 1-2 minutes
- **Sora**: 5-10 minutes

Always use `async_mode: true` to avoid blocking.

---

## Next Steps

1. ✅ **Test API** with simple text-to-video
2. ✅ **Generate B-roll** for a real campaign
3. ✅ **Animate product photo** to see image-to-video
4. ✅ **Try batch generation** for cost savings
5. ✅ **Integrate into workflow** - auto-generate missing assets

---

## Full Documentation

See `services/video-agent/pro/AI_VIDEO_GENERATION_README.md` for:
- Complete API reference
- Advanced usage examples
- Cost optimization strategies
- Campaign integration patterns
- Best practices

---

## Summary

**You can now:**
- ✅ Generate videos from text descriptions
- ✅ Animate static product photos
- ✅ Auto-generate B-roll for campaigns
- ✅ Create A/B testing variants
- ✅ Save $500-2000 per campaign

**This is a MAJOR competitive advantage for 2025.**

Elite marketers will pay premium for AI video generation capabilities.

**Start generating:**
```bash
curl -X POST http://localhost:8002/api/ai-video/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Your video description here", "quality": "draft"}'
```
