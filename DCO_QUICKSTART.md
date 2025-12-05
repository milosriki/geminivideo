# DCO Meta Variants - Quick Start Guide

**€5M Investment-Grade Dynamic Creative Optimization**

## 🚀 Quick Start (3 steps)

### Step 1: Generate Variants

```bash
curl -X POST http://localhost:8083/api/dco/generate-meta-variants \
  -H "Content-Type: application/json" \
  -d '{
    "sourceVideoPath": "/path/to/video.mp4",
    "productName": "Your Product",
    "hook": "Your main hook",
    "cta": "Your CTA",
    "variantCount": 3,
    "formats": ["feed", "reels"]
  }'
```

### Step 2: Upload to Meta

```bash
curl -X POST http://localhost:8083/api/dco/upload-variants \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_META_TOKEN" \
  -d '{
    "variants": [...],
    "campaignId": "your_campaign_id",
    "adSetId": "your_adset_id"
  }'
```

### Step 3: Activate Ads

```bash
curl -X PATCH http://localhost:8083/api/ads/{adId}/status \
  -H "Content-Type: application/json" \
  -d '{ "status": "ACTIVE" }'
```

## 📋 Meta Format Cheat Sheet

| Format | Size | Use For |
|--------|------|---------|
| feed | 1080x1080 | Product posts, carousel |
| reels | 1080x1920 | Short videos, stories |
| story | 1080x1920 | Ephemeral content |
| in_stream | 1920x1080 | Video ads, pre-roll |

## 🎯 Example: Full Campaign

```bash
# One-shot campaign creation
curl -X POST http://localhost:8083/api/campaigns/dco \
  -H "Content-Type: application/json" \
  -d '{
    "campaignName": "Launch Campaign",
    "sourceVideoPath": "/videos/launch.mp4",
    "productName": "Product Name",
    "hook": "Main message",
    "cta": "Call to action",
    "dailyBudget": 10000,
    "targeting": {
      "geo_locations": { "countries": ["US"] },
      "age_min": 25,
      "age_max": 45
    }
  }'
```

## 🔧 Configuration

### Required Environment Variables

```bash
# Meta Credentials
export META_ACCESS_TOKEN=your_token
export META_AD_ACCOUNT_ID=your_account_id
export META_PAGE_ID=your_page_id

# Service URLs
export VIDEO_AGENT_URL=http://localhost:8002
```

### Optional Settings

```json
{
  "variantCount": 5,           // Number of variants (3-10 recommended)
  "varyHooks": true,           // Generate hook variations
  "varyCtas": true,            // Generate CTA variations
  "enableSmartCrop": true,     // AI face/object tracking
  "enableCaptions": false,     // Add captions (slower)
  "enableColorGrading": false  // Apply color grading (slower)
}
```

## 📊 Variant Calculation

```
Total Variants = variantCount × formats.length

Examples:
- 3 variants × 2 formats (feed, reels) = 6 videos
- 5 variants × 4 formats (all) = 20 videos
- 10 variants × 3 formats = 30 videos
```

## 🎨 Hook Templates

The system auto-generates hooks using these templates:

**Question Style**:
- "Are you tired of [pain_point]?"
- "Want to [benefit]?"
- "Why do [audience] love [product]?"

**Statement Style**:
- "[Product] is changing how [audience] [action]"
- "[Number]+ [audience] are using [product]"
- "Introducing [product] - [tagline]"

**Urgency Style**:
- "Limited time: Get [product] now"
- "Only [number] spots left"
- "Last chance to [benefit]"

## 🔍 Check Status

```bash
# Check video-agent health
curl http://localhost:8002/health

# Check meta-publisher health
curl http://localhost:8083/health

# Get available formats
curl http://localhost:8002/api/dco/formats

# Get examples
curl http://localhost:8002/api/dco/examples
```

## ⚡ Performance Tips

### Fast Generation (30-60 seconds)
```json
{
  "variantCount": 3,
  "formats": ["feed", "reels"],
  "enableSmartCrop": false
}
```

### High Quality (2-4 minutes)
```json
{
  "variantCount": 5,
  "formats": ["feed", "reels", "story", "in_stream"],
  "enableSmartCrop": true,
  "enableCaptions": true
}
```

## 🐛 Troubleshooting

| Error | Solution |
|-------|----------|
| "Source video not found" | Check file path and permissions |
| "Video agent not available" | Start video-agent service on port 8002 |
| "Meta SDK not configured" | Set META_* environment variables |
| "Smart crop failed" | System falls back to simple resize |

## 📈 Expected Results

From 1 source video, generate:

✅ **3-10 creative variants** (different hooks/CTAs)
✅ **1-6 format versions** per variant
✅ **3-60 total ads** ready for testing
✅ **Optimized for Meta specs** (no rejections)
✅ **Upload-ready files** with thumbnails

## 🎯 Best Practices

1. **Start small**: Test with 3 variants × 2 formats = 6 ads
2. **Measure**: Track CTR, conversion rate for 3-7 days
3. **Scale winners**: Use best performers as new base
4. **Iterate**: Generate new variants weekly

## 📚 Full Documentation

See `DCO_META_VARIANTS_README.md` for complete documentation including:
- Architecture details
- API reference
- Configuration options
- Production deployment
- Scaling strategies

## 🚨 Production Checklist

- [ ] Set META_ACCESS_TOKEN
- [ ] Set META_AD_ACCOUNT_ID
- [ ] Set META_PAGE_ID
- [ ] Configure VIDEO_AGENT_URL
- [ ] Test with 1 variant first
- [ ] Verify uploads to Meta
- [ ] Set up monitoring/alerts
- [ ] Configure storage (S3/GCS)
- [ ] Enable job queue (Redis)
- [ ] Scale video-agent instances

## 💡 Pro Tips

**Tip 1**: Use descriptive variant IDs for tracking
```json
{
  "productName": "FitnessPro_Q1_2025"
}
```

**Tip 2**: Test hooks systematically
```
Week 1: Question hooks
Week 2: Statement hooks
Week 3: Urgency hooks
Week 4: Winners vs new variants
```

**Tip 3**: Format-specific content
```
Feed: Product-focused, clean
Reels: Dynamic, energetic, fast-paced
Story: Direct-to-camera, personal
In-Stream: Longer, explanatory
```

## 🎬 Example Output

From this input:
```json
{
  "sourceVideoPath": "/videos/demo.mp4",
  "productName": "FitnessPro",
  "hook": "Transform in 30 days",
  "cta": "Start Now",
  "variantCount": 3,
  "formats": ["feed", "reels"]
}
```

You get:
```
✅ variant_1_feed.mp4      - "Transform in 30 days" → "Start Now" (1080x1080)
✅ variant_1_reels.mp4     - "Transform in 30 days" → "Start Now" (1080x1920)
✅ variant_2_feed.mp4      - "Are you tired of lack of results?" → "Start Now" (1080x1080)
✅ variant_2_reels.mp4     - "Are you tired of lack of results?" → "Start Now" (1080x1920)
✅ variant_3_feed.mp4      - "1000+ customers transformed" → "Join Now" (1080x1080)
✅ variant_3_reels.mp4     - "1000+ customers transformed" → "Join Now" (1080x1920)
```

## 🔗 Related Endpoints

```
POST /api/campaigns              - Create campaign
POST /api/adsets                 - Create ad set
POST /api/video-ads             - Create video ad
GET  /api/insights/ad/:adId     - Get ad performance
PATCH /api/ads/:adId/status     - Activate/pause ad
```

## 🌟 Success Metrics

Track these KPIs:
- **CTR**: Click-through rate (target: 2-5%)
- **CPM**: Cost per 1000 impressions
- **CPC**: Cost per click
- **Conversion Rate**: % of clicks that convert
- **ROAS**: Return on ad spend (target: 3-5x)

## 📞 Support

Questions? Check:
1. `DCO_META_VARIANTS_README.md` - Full documentation
2. `GET /api/dco/examples` - Example requests
3. `GET /api/dco/formats` - Format specifications

---

**Ready for €5M Elite Marketer Validation** 🚀
