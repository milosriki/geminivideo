# AI VIDEO GENERATION - 2025 Next-Gen Feature

## COMPETITIVE ADVANTAGE: Elite marketers will pay premium for AI video generation

This module integrates cutting-edge AI video generation providers into the platform, enabling:
- **Text-to-video generation** (describe a scene, get a video)
- **Image-to-video animation** (bring product photos to life)
- **Multi-provider fallback** (Runway, Sora, Kling, Pika)
- **Cost optimization** (use cheap models for drafts, premium for finals)

---

## Supported Providers

### 1. Runway Gen-3 Alpha (RECOMMENDED)
- **Status**: Available NOW
- **API**: https://runwayml.com/
- **Pricing**: ~$0.05/second
- **Quality**: High
- **Speed**: Fast
- **Best for**: Ad creatives, product videos, B-roll footage
- **Capabilities**: Text-to-video, Image-to-video
- **Max duration**: 10 seconds

### 2. OpenAI Sora
- **Status**: Limited availability (as of Dec 2024)
- **API**: https://openai.com/sora
- **Pricing**: ~$0.25/second (estimated)
- **Quality**: Best available
- **Speed**: Slow
- **Best for**: High-budget campaigns, brand videos
- **Capabilities**: Text-to-video
- **Max duration**: 20 seconds
- **Note**: May not be accessible yet. Uses fallback to Runway if unavailable.

### 3. Kling AI
- **Status**: Available
- **API**: https://klingai.com/
- **Pricing**: ~$0.03/second
- **Quality**: Good
- **Speed**: Fast
- **Best for**: Realistic motion, human subjects
- **Capabilities**: Text-to-video, Image-to-video
- **Max duration**: 10 seconds

### 4. Pika Labs
- **Status**: Available
- **API**: https://pika.art/
- **Pricing**: ~$0.02/second
- **Quality**: Good
- **Speed**: Very fast
- **Best for**: Drafts, iterations, quick tests
- **Capabilities**: Text-to-video, Image-to-video
- **Max duration**: 8 seconds

---

## Setup

### 1. Install Dependencies

```bash
cd services/video-agent
pip install aiohttp
```

### 2. Configure API Keys

Add to `.env` file:

```bash
# Runway Gen-3 (recommended for production)
RUNWAY_API_KEY=your_runway_api_key_here

# OpenAI (for Sora when available)
OPENAI_API_KEY=your_openai_api_key_here

# Kling AI (optional)
KLING_API_KEY=your_kling_api_key_here

# Pika Labs (optional)
PIKA_API_KEY=your_pika_api_key_here
```

Get API keys:
- Runway: https://runwayml.com/ (sign up, get API key)
- OpenAI: https://platform.openai.com/
- Kling: https://klingai.com/
- Pika: https://pika.art/

### 3. Integration

The AI video generator is automatically initialized in the video-agent service.

---

## API Endpoints

### Generate AI Video

**POST** `/api/ai-video/generate`

Generate a video from text or image.

**Request:**
```json
{
  "mode": "text_to_video",
  "prompt": "A serene mountain landscape at sunset, cinematic drone shot",
  "duration": 5,
  "quality": "standard",
  "aspect_ratio": "16:9",
  "provider": "runway",
  "async_mode": true
}
```

**Parameters:**
- `mode` (string): Generation mode
  - `text_to_video` - Generate from text description
  - `image_to_video` - Animate a static image
- `prompt` (string, required): Video description or motion prompt
- `duration` (int): Video duration in seconds (3-10)
- `quality` (string): Quality tier
  - `draft` - Fast, cheap (Pika)
  - `standard` - Balanced (Runway)
  - `high` - Best quality (Sora/Runway)
  - `master` - Maximum quality
- `aspect_ratio` (string): Video format (16:9, 9:16, 1:1, 4:5)
- `image_path` (string): For image-to-video mode
- `provider` (string, optional): Preferred provider (sora, runway, kling, pika)
- `style` (string, optional): Style preset (cinematic, realistic, animated)
- `negative_prompt` (string, optional): What to avoid
- `enable_fallback` (bool): Try other providers if preferred fails (default: true)
- `async_mode` (bool): Process in background (default: true)

**Response:**
```json
{
  "status": "queued",
  "job_id": "abc123",
  "mode": "text_to_video",
  "estimated_cost": 0.25,
  "quality": "standard",
  "message": "AI video generation queued",
  "status_url": "/api/ai-video/status/abc123"
}
```

---

### Check Generation Status

**GET** `/api/ai-video/status/{job_id}`

Poll for generation progress.

**Response:**
```json
{
  "job_id": "abc123",
  "status": "completed",
  "provider": "runway",
  "video_url": "https://storage.runwayml.com/output.mp4",
  "thumbnail_url": "https://storage.runwayml.com/thumb.jpg",
  "cost": 0.25,
  "progress": 100,
  "error": null
}
```

**Status values:**
- `queued` - Job queued
- `processing` - Generating video
- `completed` - Video ready
- `failed` - Generation failed
- `cancelled` - Job cancelled

---

### Cancel Generation

**POST** `/api/ai-video/cancel/{job_id}`

Cancel a running generation job.

**Response:**
```json
{
  "success": true,
  "job_id": "abc123",
  "message": "Job cancelled"
}
```

---

### Batch Generate

**POST** `/api/ai-video/batch-generate`

Generate multiple videos at once (for B-roll, variations, etc.).

**Request:**
```json
{
  "prompts": [
    "Person running on treadmill in gym",
    "Close-up of fitness tracker",
    "Healthy meal prep in kitchen"
  ],
  "quality": "draft",
  "duration": 5,
  "aspect_ratio": "9:16",
  "use_cost_optimization": true
}
```

**Response:**
```json
{
  "status": "success",
  "batch_id": "batch_xyz",
  "job_ids": ["job1", "job2", "job3"],
  "total_videos": 3,
  "total_estimated_cost": 0.30,
  "message": "Batch generation started for 3 videos"
}
```

---

### List Providers

**GET** `/api/ai-video/providers`

Get available providers and their capabilities.

**Response:**
```json
{
  "status": "success",
  "providers": [
    {
      "name": "runway",
      "display_name": "Runway Gen-3 Alpha",
      "status": "available",
      "capabilities": ["text_to_video", "image_to_video"],
      "pricing": "$0.05/second",
      "max_duration": 10,
      "recommended_for": ["ad_creatives", "product_videos", "b_roll"]
    },
    ...
  ],
  "recommendation": "Use Runway Gen-3 for production, Pika for drafts"
}
```

---

### Estimate Cost

**GET** `/api/ai-video/estimate-cost?duration=5&quality=standard&provider=runway`

Estimate cost before generating.

**Response:**
```json
{
  "estimated_cost": 0.25,
  "duration": 5,
  "quality": "standard",
  "provider": "runway",
  "breakdown_by_provider": {
    "sora": 1.25,
    "runway": 0.25,
    "kling": 0.15,
    "pika": 0.10
  },
  "savings_tip": "Save $1.15 by using Pika instead of Sora"
}
```

---

## Python SDK Usage

### Basic Text-to-Video

```python
from pro.ai_video_generator import (
    AIVideoGenerator,
    VideoGenerationRequest,
    GenerationMode,
    QualityTier
)

# Initialize generator
generator = AIVideoGenerator()

# Create request
request = VideoGenerationRequest(
    mode=GenerationMode.TEXT_TO_VIDEO,
    prompt="A professional product showcase of a smartphone, smooth camera movement",
    duration=5,
    quality=QualityTier.STANDARD,
    aspect_ratio="9:16"
)

# Generate video
result = await generator.generate_video(request)

print(f"Status: {result.status.value}")
print(f"Video URL: {result.video_url}")
print(f"Cost: ${result.cost}")

# Close session
await generator.close()
```

### Image-to-Video Animation

```python
request = VideoGenerationRequest(
    mode=GenerationMode.IMAGE_TO_VIDEO,
    prompt="Slow zoom in and gentle 15-degree rotation",
    image_path="product_photo.jpg",
    duration=5,
    quality=QualityTier.HIGH,
    aspect_ratio="9:16"
)

result = await generator.generate_video(request)
```

### With Specific Provider

```python
from pro.ai_video_generator import VideoProvider

request = VideoGenerationRequest(
    mode=GenerationMode.TEXT_TO_VIDEO,
    prompt="Mountain landscape at sunset",
    duration=5,
    quality=QualityTier.HIGH,
    preferred_provider=VideoProvider.RUNWAY,  # Force Runway
    enable_fallback=True  # Try others if Runway fails
)

result = await generator.generate_video(request)
```

---

## Campaign Integration

### Auto-Generate B-Roll

```python
from pro.ai_campaign_integration import AICampaignIntegration

integration = AICampaignIntegration()

# Generate B-roll footage
b_roll = await integration.generate_b_roll(
    prompts=[
        "Person using fitness app in gym",
        "Close-up of app notification",
        "User celebrating achievement"
    ],
    quality="draft",  # Use draft for cost savings
    aspect_ratio="9:16"
)

for i, result in enumerate(b_roll):
    print(f"B-roll {i+1}: {result.video_url}, Cost: ${result.cost}")

await integration.close()
```

### Animate Product Photos

```python
# Bring product photo to life
result = await integration.animate_product_image(
    image_path="iphone_product_shot.jpg",
    motion="360-degree rotation with professional lighting",
    quality="high"
)

print(f"Product video: {result.video_url}")
```

### Generate Complete Campaign Assets

```python
campaign_brief = {
    "product_name": "FitnessPro App",
    "b_roll_scenes": [
        "User tracking workout on phone",
        "Success notification",
        "Progress chart showing improvement"
    ],
    "product_images": ["app_screen1.jpg", "app_screen2.jpg"],
    "aspect_ratio": "9:16",
    "quality": "standard",
    "transition_count": 3
}

assets = await integration.generate_campaign_assets(campaign_brief)

print(f"B-roll clips: {len(assets['b_roll'])}")
print(f"Product shots: {len(assets['product_shots'])}")
print(f"Transitions: {len(assets['transitions'])}")
```

---

## Cost Optimization Strategies

### 1. Use Drafts for Iterations

```python
# Generate 5 draft variants for testing
variants = await integration.create_video_variants(
    "Fitness app demo showing workout tracking",
    variant_count=5,
    quality="draft"  # Only $0.10 total instead of $1.25
)

# Pick best variant, regenerate in high quality
best_variant = variants[2]  # Example: variant 3 performs best
final_video = await generator.generate_video(
    VideoGenerationRequest(
        mode=GenerationMode.TEXT_TO_VIDEO,
        prompt=best_variant.metadata["prompt"],
        quality=QualityTier.HIGH
    )
)
```

### 2. Cost-Optimized Batch Generation

```python
# Use cheaper providers for non-critical footage
batch_result = await ai_batch_generate({
    "prompts": [
        "B-roll shot 1",
        "B-roll shot 2",
        "B-roll shot 3 (hero shot)"  # Last one gets better quality
    ],
    "quality": "draft",
    "use_cost_optimization": True  # First 2 use Pika ($0.02/s), last uses Runway ($0.05/s)
})
```

### 3. Quality Tier Selection

| Tier | Provider | Cost/sec | Use Case |
|------|----------|----------|----------|
| Draft | Pika | $0.02 | Testing, iterations, non-critical B-roll |
| Standard | Runway | $0.05 | Production B-roll, most ad footage |
| High | Runway/Sora | $0.15 | Hero shots, brand videos |
| Master | Sora | $0.25 | Premium campaigns, high-budget clients |

---

## Use Cases

### 1. Ad Creatives
```python
# Generate product demo video
result = await generator.generate_video(
    VideoGenerationRequest(
        mode=GenerationMode.TEXT_TO_VIDEO,
        prompt="Professional demo of mobile app showing key features, modern UI, smooth animations",
        quality=QualityTier.HIGH,
        aspect_ratio="9:16",
        duration=5,
        style="cinematic"
    )
)
```

### 2. Product Showcases
```python
# Animate product photo
result = await integration.animate_product_image(
    "product_white_background.jpg",
    motion="Elegant 360-degree rotation, studio lighting, professional showcase",
    quality="high"
)
```

### 3. B-Roll Generation
```python
# Auto-generate B-roll when footage is missing
b_roll = await auto_generate_missing_b_roll(
    campaign_data={
        "product_name": "Meditation App",
        "target_audience": "stressed professionals",
        "key_benefits": ["reduce stress", "improve sleep"]
    },
    required_b_roll_count=5
)
```

### 4. Scene Transitions
```python
# Generate smooth transitions between scenes
transitions = await integration.generate_scene_transitions(
    count=3,
    style="smooth",
    duration=3
)
```

### 5. A/B Testing Variants
```python
# Generate multiple variants for testing
variants = await integration.create_video_variants(
    "Fitness app demo on smartphone in gym",
    variant_count=5,
    quality="draft"  # Cheap for testing
)

# Test all variants, pick winner
# Regenerate winner in high quality
```

---

## Best Practices

### 1. Prompt Engineering

**Good prompts:**
- ✅ "Professional product showcase of iPhone 15, slow 360-degree rotation, studio lighting, white background"
- ✅ "Person running on treadmill in modern gym, focused expression, cinematic camera movement"
- ✅ "Close-up of hands typing on laptop, bright office environment, shallow depth of field"

**Bad prompts:**
- ❌ "Phone" (too vague)
- ❌ "Make a video" (no details)
- ❌ "Cool gym scene" (subjective, unclear)

### 2. Quality Selection

- Use **draft** for: Testing, iterations, non-critical B-roll
- Use **standard** for: Most ad footage, production B-roll
- Use **high** for: Hero shots, key scenes, client presentations
- Use **master** for: Premium campaigns, high-budget clients

### 3. Provider Selection

- **Runway**: Default choice for production
- **Pika**: Use for drafts and iterations (save $)
- **Kling**: Use for realistic human motion
- **Sora**: Use for highest quality when available (expensive)

### 4. Cost Management

```python
# Calculate cost before generating
cost = estimate_cost(duration=5, quality=QualityTier.DRAFT)
if cost > budget:
    # Use cheaper provider or lower quality
    pass
```

### 5. Error Handling

```python
try:
    result = await generator.generate_video(request)

    if result.status == GenerationStatus.FAILED:
        # Handle failure - maybe try different provider
        if request.enable_fallback:
            # Fallback already tried, escalate error
            logger.error(f"All providers failed: {result.error}")
        else:
            # Retry with fallback enabled
            request.enable_fallback = True
            result = await generator.generate_video(request)

except Exception as e:
    logger.error(f"Generation error: {e}")
```

---

## Pricing Summary

| Provider | Price/Second | 5-Second Video | Use Case |
|----------|--------------|----------------|----------|
| Pika Labs | $0.02 | $0.10 | Drafts, iterations |
| Kling AI | $0.03 | $0.15 | Realistic motion |
| Runway Gen-3 | $0.05 | $0.25 | Production (recommended) |
| OpenAI Sora | $0.25 | $1.25 | Premium campaigns |

**Example campaign:**
- 5 B-roll clips (5s each, draft) = $0.50
- 2 Product shots (5s each, high) = $0.50
- 3 Transitions (3s each, draft) = $0.18
- **Total: $1.18**

vs. hiring videographer: $500-2000+

---

## Troubleshooting

### Provider Not Available

If a provider fails:
```python
# Enable fallback to try alternative providers
request.enable_fallback = True
```

### API Key Not Configured

```bash
# Check environment variables
echo $RUNWAY_API_KEY
echo $OPENAI_API_KEY

# If missing, add to .env file
```

### Generation Failed

Check logs for error:
```python
result = await generator.generate_video(request)

if result.status == GenerationStatus.FAILED:
    print(f"Error: {result.error}")
    # Common errors:
    # - Invalid API key
    # - Insufficient credits
    # - Invalid prompt (NSFW, copyright)
    # - Server error (retry)
```

### Slow Generation

- Use **Pika** for faster generation (5-30 seconds)
- **Runway** takes 1-2 minutes
- **Sora** can take 5-10 minutes
- Always use `async_mode=True` for non-blocking

---

## Future Enhancements

- [ ] Video-to-video style transfer
- [ ] Multi-clip stitching
- [ ] Custom motion paths
- [ ] Prompt templates library
- [ ] Automatic prompt optimization
- [ ] Batch download and storage
- [ ] Integration with video editor
- [ ] Cost tracking and budgeting

---

## Support

For issues or questions:
- Check logs: `/tmp/ai_video_generation.log`
- Review provider docs:
  - Runway: https://docs.runwayml.com/
  - OpenAI: https://platform.openai.com/docs
  - Kling: https://docs.klingai.com/
  - Pika: https://docs.pika.art/

---

## Summary

AI video generation is a **MAJOR competitive advantage** for 2025:

- ✅ **Generate videos from text** - No videographer needed
- ✅ **Animate product photos** - Bring static images to life
- ✅ **Auto-generate B-roll** - Fill gaps in campaigns
- ✅ **Multi-provider fallback** - Always have a backup
- ✅ **Cost optimization** - Drafts cost $0.10, finals $0.25-1.25
- ✅ **Campaign integration** - Auto-enhance campaigns with AI

Elite marketers will pay **premium prices** for this capability.

**Get Started:**
1. Add API keys to `.env`
2. Call `/api/ai-video/generate`
3. Generate professional videos in minutes
