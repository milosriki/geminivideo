# DCO Meta Variant Generator - Production Documentation

**€5M Investment-Grade Dynamic Creative Optimization for Meta Ads**

## Overview

The DCO (Dynamic Creative Optimization) Meta Variant Generator automatically creates multiple ad variants optimized for different Meta advertising placements from a single source creative. This system generates variants with different:

- **Formats**: Feed (1:1), Reels (9:16), Story (9:16), In-Stream (16:9), Carousel (1:1), Portrait (4:5)
- **Hooks**: Different opening statements tested with proven templates
- **CTAs**: Varied call-to-action messages for A/B testing
- **Smart Cropping**: AI-powered face/object tracking for optimal framing

## Meta Ad Format Specifications

### Supported Formats

| Format | Dimensions | Aspect Ratio | Placement | Use Cases |
|--------|-----------|--------------|-----------|-----------|
| Feed | 1080x1080 | 1:1 | Instagram Feed | Product showcase, Static ads, Carousel |
| Reels | 1080x1920 | 9:16 | Instagram Reels | Short-form video, Stories, Vertical content |
| Story | 1080x1920 | 9:16 | Instagram Story | Ephemeral content, Direct response, Engagement |
| In-Stream | 1920x1080 | 16:9 | Facebook In-Stream | Video ads, Pre-roll, Mid-roll |
| Carousel | 1080x1080 | 1:1 | Carousel | Multiple products, Step-by-step, Before/after |
| Portrait 4:5 | 1080x1350 | 4:5 | Instagram Explore | Discovery, Explore feed, Portrait content |

## Architecture

```
┌─────────────────┐
│ Source Creative │
│  (Video/Image)  │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  DCO Meta Generator     │
│  - Variant Generator    │
│  - Smart Crop System    │
│  - Format Optimizer     │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  Generated Variants     │
│  Feed: variant_1.mp4    │
│  Reels: variant_2.mp4   │
│  Story: variant_3.mp4   │
│  In-Stream: variant_4.mp4│
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│  Meta Publisher Service │
│  - Upload to Meta       │
│  - Create Campaigns     │
│  - Track Performance    │
└─────────────────────────┘
```

## API Endpoints

### 1. Generate DCO Variants

**Endpoint**: `POST /api/dco/generate-meta-variants`

**Service**: `meta-publisher` (port 8083)

**Request Body**:
```json
{
  "sourceVideoPath": "/path/to/video.mp4",
  "productName": "FitnessPro App",
  "hook": "Transform your body in 30 days",
  "cta": "Start Free Trial",
  "painPoint": "lack of results",
  "benefit": "personalized workouts",
  "targetAudience": "busy professionals",
  "variantCount": 5,
  "varyHooks": true,
  "varyCtas": true,
  "formats": ["feed", "reels", "in_stream"],
  "enableSmartCrop": true
}
```

**Response**:
```json
{
  "status": "success",
  "jobId": "dco_1234567890_abc",
  "totalVariants": 15,
  "variants": [
    {
      "variantId": "base#v1_feed_xyz",
      "format": "feed",
      "placement": "instagram_feed",
      "dimensions": { "width": 1080, "height": 1080 },
      "videoPath": "/tmp/dco_variants/job_id/variant.mp4",
      "thumbnailPath": "/tmp/dco_variants/job_id/variant_thumb.jpg",
      "creative": {
        "hook": "Are you tired of lack of results?",
        "cta": "Start Free Trial"
      },
      "uploadReady": true,
      "metadata": {
        "productName": "FitnessPro App",
        "variantType": "hook+cta",
        "isOriginal": false
      }
    }
  ],
  "manifest": {
    "productName": "FitnessPro App",
    "variantCount": 5,
    "formats": ["feed", "reels", "in_stream"],
    "generatedAt": "2025-01-15T10:30:00Z"
  },
  "message": "Generated 15 Meta-compliant variants",
  "nextSteps": {
    "upload": "POST /api/dco/upload-variants",
    "createCampaign": "POST /api/campaigns/dco"
  }
}
```

### 2. Upload Variants to Meta

**Endpoint**: `POST /api/dco/upload-variants`

**Service**: `meta-publisher` (port 8083)

**Request Body**:
```json
{
  "variants": [...],
  "campaignId": "campaign_123",
  "adSetId": "adset_456"
}
```

**Response**:
```json
{
  "status": "completed",
  "totalVariants": 15,
  "successCount": 14,
  "failCount": 1,
  "results": [
    {
      "variantId": "base#v1_feed_xyz",
      "status": "success",
      "videoId": "video_789",
      "creativeId": "creative_101",
      "adId": "ad_112",
      "placement": "instagram_feed"
    }
  ],
  "message": "Uploaded 14/15 variants successfully"
}
```

### 3. Create Complete DCO Campaign

**Endpoint**: `POST /api/campaigns/dco`

**Service**: `meta-publisher` (port 8083)

**Request Body**:
```json
{
  "campaignName": "FitnessPro Q1 2025",
  "sourceVideoPath": "/path/to/video.mp4",
  "productName": "FitnessPro App",
  "hook": "Transform your body in 30 days",
  "cta": "Start Free Trial",
  "targeting": {
    "geo_locations": { "countries": ["US", "CA"] },
    "age_min": 25,
    "age_max": 45,
    "interests": ["Fitness", "Health"]
  },
  "dailyBudget": 10000,
  "bidAmount": 2000
}
```

**Response**:
```json
{
  "status": "success",
  "campaign": {
    "campaignId": "campaign_123",
    "adSetId": "adset_456",
    "name": "FitnessPro Q1 2025"
  },
  "variants": {
    "total": 9,
    "uploaded": 9,
    "failed": 0
  },
  "message": "DCO campaign created successfully",
  "nextSteps": {
    "review": "Review campaign in Meta Ads Manager",
    "activate": "PATCH /api/ads/:adId/status with status=ACTIVE"
  }
}
```

### 4. Get Meta Format Specifications

**Endpoint**: `GET /api/dco/formats`

**Service**: `video-agent` (port 8002)

**Response**: List of all supported Meta ad formats with specifications.

### 5. Get DCO Examples

**Endpoint**: `GET /api/dco/examples`

**Service**: `video-agent` (port 8002)

**Response**: Complete example requests for basic, advanced, and carousel DCO generation.

## Usage Examples

### Example 1: Basic DCO Generation

Generate 3 variants in Feed and Reels formats:

```bash
curl -X POST http://localhost:8083/api/dco/generate-meta-variants \
  -H "Content-Type: application/json" \
  -d '{
    "sourceVideoPath": "/videos/fitness_ad.mp4",
    "productName": "FitnessPro",
    "hook": "Get fit in 30 days",
    "cta": "Start Now",
    "variantCount": 3,
    "formats": ["feed", "reels"]
  }'
```

**Output**: 6 variants (3 creative variants × 2 formats)

### Example 2: Advanced Multi-Format Campaign

Generate 5 variants across all major Meta formats:

```bash
curl -X POST http://localhost:8083/api/dco/generate-meta-variants \
  -H "Content-Type: application/json" \
  -d '{
    "sourceVideoPath": "/videos/product_demo.mp4",
    "productName": "SaaS Platform",
    "hook": "Automate your workflow",
    "cta": "Get Started",
    "painPoint": "manual processes",
    "benefit": "automation",
    "targetAudience": "business owners",
    "variantCount": 5,
    "varyHooks": true,
    "varyCtas": true,
    "formats": ["feed", "reels", "story", "in_stream"],
    "enableSmartCrop": true
  }'
```

**Output**: 20 variants (5 creative variants × 4 formats)

### Example 3: Complete Campaign Creation

Create a complete Meta campaign with DCO variants:

```bash
curl -X POST http://localhost:8083/api/campaigns/dco \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "campaignName": "Q1 2025 Launch",
    "sourceVideoPath": "/videos/launch_video.mp4",
    "productName": "New Product",
    "hook": "Revolutionary new solution",
    "cta": "Pre-Order Now",
    "targeting": {
      "geo_locations": { "countries": ["US"] },
      "age_min": 25,
      "age_max": 55
    },
    "dailyBudget": 20000,
    "bidAmount": 3000
  }'
```

## Variant Generation Process

### Step 1: Creative Variant Generation

The system generates multiple creative variants with different:

- **Hooks**: Question, Statement, Challenge, Urgency templates
- **CTAs**: Learn More, Shop Now, Sign Up, Limited Time
- **Combinations**: Smart pairing of hooks and CTAs

**Example Variants**:
1. "Are you tired of lack of results?" → "Start Free Trial"
2. "Transform your body in 30 days" → "Learn More"
3. "1000+ customers are using FitnessPro" → "Join Now"

### Step 2: Format Optimization

Each creative variant is optimized for each requested format:

- **Feed (1:1)**: Center-crop with padding
- **Reels (9:16)**: Vertical smart crop with face tracking
- **Story (9:16)**: Same as Reels with story-optimized framing
- **In-Stream (16:9)**: Horizontal crop or letterbox
- **Carousel (1:1)**: Multiple 1:1 frames from video

### Step 3: Smart Cropping (Optional)

When enabled, the system uses AI to:

1. **Detect faces** using OpenCV DNN
2. **Track motion** across frames
3. **Smooth panning** with easing functions
4. **Maintain subject** in safe zone (80% center)

### Step 4: Quality Optimization

Final output is optimized for Meta specs:

- **Video Codec**: H.264 (libx264)
- **Quality**: CRF 23 (high quality, reasonable size)
- **Audio**: AAC 128kbps
- **Fast Start**: Moov atom at beginning for streaming

## Configuration Options

### DCO Generation Config

```python
{
  "source_video_path": str,        # Required: Path to source video
  "output_dir": str,                # Required: Output directory
  "product_name": str,              # Required: Product name
  "pain_point": str,                # Pain point being addressed
  "benefit": str,                   # Key benefit
  "target_audience": str,           # Target audience description
  "base_hook": str,                 # Required: Base hook text
  "base_cta": str,                  # Required: Base CTA text
  "cta_type": str,                  # learn_more, shop_now, sign_up, limited
  "variant_count": int,             # Number of creative variants (default: 5)
  "vary_hooks": bool,               # Generate hook variants (default: true)
  "vary_ctas": bool,                # Generate CTA variants (default: true)
  "formats": List[str],             # List of formats to generate
  "enable_smart_crop": bool,        # Enable AI smart cropping (default: true)
  "enable_captions": bool,          # Add captions (default: false)
  "enable_color_grading": bool,     # Apply color grading (default: false)
  "video_codec": str,               # Video codec (default: libx264)
  "video_quality": int,             # CRF value (default: 23)
  "audio_codec": str,               # Audio codec (default: aac)
  "audio_bitrate": str              # Audio bitrate (default: 128k)
}
```

## Performance & Scaling

### Expected Generation Times

| Variants | Formats | Smart Crop | Estimated Time |
|----------|---------|------------|----------------|
| 3 | 2 | No | 30-60 seconds |
| 3 | 2 | Yes | 2-4 minutes |
| 5 | 4 | No | 2-3 minutes |
| 5 | 4 | Yes | 8-12 minutes |

### Optimization Tips

1. **Disable smart crop** for faster generation if source is already well-framed
2. **Reduce variant count** for initial testing (3-5 recommended)
3. **Use specific formats** rather than generating all formats
4. **Background processing** via job queue for large batches

### Storage Requirements

- **Per variant**: ~5-20 MB (depending on duration and quality)
- **15 variants**: ~150 MB
- **Thumbnails**: ~100 KB each

## Integration with Meta Ads API

### Required Meta Credentials

Set these environment variables:

```bash
META_ACCESS_TOKEN=your_access_token
META_AD_ACCOUNT_ID=your_account_id
META_PAGE_ID=your_page_id
VIDEO_AGENT_URL=http://localhost:8002
```

### Upload Flow

1. **Generate variants** → DCO Generator creates video files
2. **Upload videos** → Meta Ads API accepts video files
3. **Create creatives** → Associate videos with creative data
4. **Create ads** → Link creatives to ad sets
5. **Activate** → Set ads to ACTIVE status

## Monitoring & Analytics

### Variant Manifest

Each generation creates a `variants_manifest.json`:

```json
{
  "generated_at": "job_id",
  "total_variants": 15,
  "variants": [
    {
      "variant_id": "unique_id",
      "format": "feed",
      "dimensions": "1080x1080",
      "video_path": "/path/to/variant.mp4",
      "hook": "Hook text",
      "cta": "CTA text",
      "upload_ready": true
    }
  ]
}
```

### Performance Tracking

Track variant performance using Meta Insights API:

```bash
GET /api/insights/ad/:adId?datePreset=last_7d
```

Metrics tracked:
- Impressions
- Clicks
- CTR
- Spend
- Conversions
- ROAS

## Best Practices

### 1. Source Creative Quality

- **Resolution**: Minimum 1920x1080 for best results
- **Duration**: 15-60 seconds optimal
- **Content**: Clear subject, good lighting, minimal camera shake
- **Audio**: Clean audio track, no background noise

### 2. Hook & CTA Testing

- **Test systematically**: 3-5 hooks × 2-3 CTAs
- **Measure performance**: Track CTR, conversion rate
- **Iterate**: Use winning variants as new base

### 3. Format Selection

- **Feed**: Product showcases, static demos
- **Reels/Story**: Dynamic content, testimonials
- **In-Stream**: Longer explanations, tutorials
- **Carousel**: Multiple products, step-by-step guides

### 4. Smart Crop Settings

- Enable for: Interviews, talking heads, product demos
- Disable for: Pre-edited videos, graphics, text-heavy content

## Troubleshooting

### Common Issues

**Issue**: "Source video file not found"
- **Solution**: Verify file path and permissions

**Issue**: "Video agent not available"
- **Solution**: Ensure video-agent service is running on port 8002

**Issue**: "Smart crop failed"
- **Solution**: Falls back to simple resize automatically, check logs

**Issue**: "Meta SDK not configured"
- **Solution**: Set META_ACCESS_TOKEN, META_AD_ACCOUNT_ID, META_PAGE_ID

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL=DEBUG
export VIDEO_AGENT_DEBUG=true
```

## Production Deployment

### Service Dependencies

```yaml
services:
  video-agent:
    build: ./services/video-agent
    ports:
      - "8002:8002"
    environment:
      - OUTPUT_DIR=/data/variants
      - REDIS_URL=redis://redis:6379
    volumes:
      - variant-storage:/data/variants

  meta-publisher:
    build: ./services/meta-publisher
    ports:
      - "8083:8083"
    environment:
      - META_ACCESS_TOKEN=${META_ACCESS_TOKEN}
      - META_AD_ACCOUNT_ID=${META_AD_ACCOUNT_ID}
      - META_PAGE_ID=${META_PAGE_ID}
      - VIDEO_AGENT_URL=http://video-agent:8002
```

### Scaling Considerations

- **Horizontal scaling**: Deploy multiple video-agent instances
- **Job queue**: Use Redis/RabbitMQ for async processing
- **Storage**: Use S3/GCS for variant storage
- **Caching**: Cache generated variants for reuse

## Support & Resources

- **Meta Creative Specs**: https://developers.facebook.com/docs/marketing-api/creative-specs
- **Meta Ads API**: https://developers.facebook.com/docs/marketing-api/
- **FFmpeg Documentation**: https://ffmpeg.org/documentation.html

## License

€5M Investment-Grade Production System
Copyright © 2025 GeminiVideo
