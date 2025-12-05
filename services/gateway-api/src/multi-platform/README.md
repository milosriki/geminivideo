# Multi-Platform Publishing Infrastructure

**Agent 19: Multi-Platform Publishing (Meta + Google + TikTok)**

Production-ready infrastructure for publishing video ads to multiple platforms simultaneously. Built for elite marketers managing €5M+ ad budgets.

## 🎯 Overview

This system enables unified publishing to:
- **Meta** (Facebook & Instagram) - Reels, Stories, Feed, In-stream
- **Google Ads** (YouTube) - In-stream, Shorts, Display
- **TikTok** - In-feed vertical video

## 📁 File Structure

```
/services/gateway-api/src/multi-platform/
├── multi_publisher.ts       # Main orchestration logic
├── format_adapter.ts        # Platform format adaptation
├── status_aggregator.ts     # Cross-platform status tracking
└── README.md               # This file

/services/tiktok-ads/        # TikTok placeholder service
└── src/index.ts            # Mock API endpoints

/frontend/src/components/
├── MultiPlatformPublisher.tsx    # UI component
└── MultiPlatformPublisher.css    # Styles
```

## 🚀 Key Features

### 1. **Unified Publishing API**
Single endpoint to publish to multiple platforms:

```typescript
POST /api/publish/multi
{
  "creative_id": "creative_123",
  "video_path": "/path/to/video.mp4",
  "platforms": ["meta", "google", "tiktok"],
  "budget_allocation": {
    "meta": 500,
    "google": 300,
    "tiktok": 200
  },
  "campaign_name": "Summer Sale 2024",
  "creative_config": {
    "caption": "Amazing product!",
    "headline": "Shop Now",
    "cta": "Learn More"
  }
}
```

### 2. **Format Adaptation**
Automatically converts videos to platform-specific formats:

- **Meta**: 1:1 (Feed), 9:16 (Reels/Stories), 16:9 (In-stream)
- **Google**: 16:9 (YouTube), 9:16 (Shorts), 1:1 (Display)
- **TikTok**: 9:16 (In-feed only)

### 3. **Smart Budget Allocation**
Automatic budget optimization based on platform performance:

```typescript
POST /api/platforms/budget-allocation
{
  "platforms": ["meta", "google", "tiktok"],
  "total_budget": 1000
}

// Response (default weights):
{
  "allocation": {
    "meta": 500,    // 50%
    "google": 300,  // 30%
    "tiktok": 200   // 20%
  }
}
```

### 4. **Real-Time Status Tracking**
Monitor publishing progress across all platforms:

```typescript
GET /api/publish/status/:job_id

// Response:
{
  "job": {
    "jobId": "multi_123",
    "overallStatus": "in_progress",
    "successCount": 2,
    "failureCount": 0,
    "totalPlatforms": 3
  },
  "platformStatuses": [
    {
      "platform": "meta",
      "status": "live",
      "campaignId": "meta_campaign_456",
      "adId": "meta_ad_789"
    },
    {
      "platform": "google",
      "status": "processing",
      "campaignId": "google_campaign_321"
    },
    {
      "platform": "tiktok",
      "status": "uploading"
    }
  ]
}
```

### 5. **Aggregated Metrics**
Cross-platform performance comparison:

```typescript
{
  "totalImpressions": 150000,
  "totalClicks": 4500,
  "totalSpend": 1000,
  "averageCtr": 0.03,
  "overallRoas": 2.5,
  "platformBreakdown": {
    "meta": {
      "impressions": 80000,
      "clicks": 2400,
      "spend": 500,
      "ctr": 0.03,
      "roas": 2.8,
      "percentage": 50
    },
    "google": { ... },
    "tiktok": { ... }
  }
}
```

## 📊 Platform Specifications

### Meta (Facebook/Instagram)

| Placement | Aspect Ratio | Resolution | Duration | Max Size |
|-----------|-------------|------------|----------|----------|
| Feed | 1:1 | 1080x1080 | 1-240s | 4000MB |
| Reels | 9:16 | 1080x1920 | 1-60s | 4000MB |
| Stories | 9:16 | 1080x1920 | 1-15s | 4000MB |
| In-stream | 16:9 | 1920x1080 | 1-240s | 4000MB |

### Google Ads (YouTube)

| Placement | Aspect Ratio | Resolution | Duration | Max Size |
|-----------|-------------|------------|----------|----------|
| In-stream | 16:9 | 1920x1080 | 6-360s | 1024MB |
| Shorts | 9:16 | 1080x1920 | 6-60s | 1024MB |
| Display | 1:1 | 1200x1200 | 6-30s | 150MB |

### TikTok

| Placement | Aspect Ratio | Resolution | Duration | Max Size |
|-----------|-------------|------------|----------|----------|
| In-feed | 9:16 | 1080x1920 | 5-60s | 500MB |
| In-feed Mobile | 9:16 | 720x1280 | 5-60s | 500MB |

## 🔧 API Endpoints

### Publishing

```typescript
// Publish to multiple platforms
POST /api/publish/multi

// Check publishing status
GET /api/publish/status/:job_id

// Get all publishing jobs
GET /api/publish/jobs?limit=10

// Get publishing summary
GET /api/publish/summary
```

### Platform Information

```typescript
// Get platform specifications
GET /api/platforms/specs?platforms=meta,google,tiktok

// Calculate budget allocation
POST /api/platforms/budget-allocation
{
  "platforms": ["meta", "google", "tiktok"],
  "total_budget": 1000,
  "custom_weights": {  // Optional
    "meta": 0.6,
    "google": 0.3,
    "tiktok": 0.1
  }
}
```

## 🎨 Frontend Component

### Usage

```tsx
import MultiPlatformPublisher from './components/MultiPlatformPublisher';

function App() {
  return (
    <MultiPlatformPublisher
      creativeId="creative_123"
      videoPath="/videos/summer_sale.mp4"
      onPublishSuccess={(jobId) => {
        console.log('Published!', jobId);
      }}
      onPublishError={(error) => {
        console.error('Publish failed:', error);
      }}
    />
  );
}
```

### Features

- ✅ Platform selection with checkboxes
- ✅ Budget allocation sliders with auto-optimization
- ✅ Real-time publishing progress
- ✅ Platform-specific previews
- ✅ Cross-platform performance comparison
- ✅ Creative specifications viewer

## 🏗️ Architecture

### Multi-Platform Publisher
- Orchestrates parallel publishing to all platforms
- Handles format adaptation automatically
- Manages platform-specific configurations
- Provides unified error handling

### Format Adapter
- Converts videos to platform specifications
- Smart cropping for aspect ratio conversion
- Quality optimization per platform
- Validation against platform requirements

### Status Aggregator
- Tracks job status across platforms
- Aggregates metrics in real-time
- Compares platform performance
- Maintains job history

## 🔒 Production Considerations

### Budget Allocation Strategy

Default weights based on typical performance:
- **Meta**: 50% - Largest reach, best targeting
- **Google**: 30% - High intent, YouTube dominance
- **TikTok**: 20% - Growing platform, younger audience

Customize weights based on:
- Historical campaign performance
- Target audience demographics
- Platform-specific KPIs
- Seasonal trends

### Error Handling

The system provides graceful degradation:
- If one platform fails, others continue
- Partial success is tracked and reported
- Failed platforms can be retried individually
- All errors are logged with context

### Performance Optimization

- Parallel publishing reduces wait time
- Format adaptation is asynchronous
- Status polling is efficient (3s intervals)
- Old jobs are cleaned up automatically

## 🚀 Deployment

### Environment Variables

```bash
# Service URLs
META_PUBLISHER_URL=http://localhost:8083
GOOGLE_ADS_URL=http://localhost:8084
TIKTOK_ADS_URL=http://localhost:8085
VIDEO_AGENT_URL=http://localhost:8002

# Platform Credentials (see individual services)
META_ACCESS_TOKEN=...
GOOGLE_CLIENT_ID=...
TIKTOK_ACCESS_TOKEN=...
```

### TikTok Service

Currently a placeholder service that returns mock responses. To enable real TikTok integration:

1. Set up TikTok Business API access
2. Implement authentication flow
3. Replace mock endpoints with real API calls
4. Update error handling

See: https://business-api.tiktok.com/portal/docs

## 📈 Risk Mitigation for €5M Investment

### Diversification Benefits

Publishing to multiple platforms reduces risk:
- Platform algorithm changes affect only portion of budget
- Ad account issues isolated to single platform
- Testing reveals best-performing platforms
- Redundancy ensures continuous reach

### Cost Control

- Budget caps per platform prevent overspend
- Real-time monitoring enables quick adjustments
- Automated pausing on poor performance
- Historical data guides future allocation

### Quality Assurance

- Format validation before upload
- Creative specifications enforced
- Review workflow integration
- A/B testing across platforms

## 🧪 Testing

### Local Testing

```bash
# Start all services
docker-compose up gateway-api meta-publisher google-ads tiktok-ads

# Test multi-platform publish
curl -X POST http://localhost:8000/api/publish/multi \
  -H "Content-Type: application/json" \
  -d '{
    "creative_id": "test_123",
    "video_path": "/tmp/test_video.mp4",
    "platforms": ["meta", "google", "tiktok"],
    "budget_allocation": {"meta": 50, "google": 30, "tiktok": 20},
    "campaign_name": "Test Campaign"
  }'

# Check status
curl http://localhost:8000/api/publish/status/multi_123
```

### Platform Specs

```bash
# Get all platform specs
curl http://localhost:8000/api/platforms/specs

# Calculate budget allocation
curl -X POST http://localhost:8000/api/platforms/budget-allocation \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["meta", "google", "tiktok"],
    "total_budget": 1000
  }'
```

## 📚 Next Steps

### Immediate
- [ ] Deploy TikTok placeholder service
- [ ] Test multi-platform publishing flow
- [ ] Verify format adaptation
- [ ] Monitor performance metrics

### Short-term
- [ ] Implement TikTok Business API
- [ ] Add advanced targeting options
- [ ] Create platform-specific optimizations
- [ ] Build reporting dashboard

### Long-term
- [ ] Add Snapchat, LinkedIn, Twitter
- [ ] Implement machine learning for budget allocation
- [ ] Create predictive performance models
- [ ] Build automated optimization rules

## 🤝 Support

For issues or questions:
- Check platform documentation links
- Review error logs in gateway-api
- Verify environment variables
- Test individual platform services

## 📄 License

Production code for elite marketers. Handle with care - €5M budgets at stake!
