# Multi-Platform Publishing Integration Examples

## Quick Start Guide

### 1. Start Services

```bash
# Start all services with Docker Compose
docker-compose up -d gateway-api meta-publisher google-ads tiktok-ads

# Verify services are running
curl http://localhost:8000/health  # Gateway API
curl http://localhost:8083/health  # Meta Publisher
curl http://localhost:8084/health  # Google Ads
curl http://localhost:8085/health  # TikTok Ads (Placeholder)
```

### 2. Publish to All Platforms

```bash
curl -X POST http://localhost:8000/api/publish/multi \
  -H "Content-Type: application/json" \
  -d '{
    "creative_id": "summer_sale_2024",
    "video_path": "/videos/summer_promo.mp4",
    "platforms": ["meta", "google", "tiktok"],
    "budget_allocation": {
      "meta": 500,
      "google": 300,
      "tiktok": 200
    },
    "campaign_name": "Summer Sale 2024",
    "creative_config": {
      "headline": "50% Off Summer Collection",
      "caption": "Limited time offer! Shop now and save big on our summer collection.",
      "cta": "Shop Now"
    },
    "campaign_config": {
      "meta": {
        "objective": "OUTCOME_ENGAGEMENT",
        "placements": ["instagram_reels", "facebook_reels"],
        "targeting": {
          "geo_locations": { "countries": ["US"] },
          "age_min": 18,
          "age_max": 65,
          "interests": ["Fashion", "Shopping"]
        }
      },
      "google": {
        "headline": "Summer Sale: 50% Off",
        "description": "Shop our summer collection with exclusive discounts",
        "finalUrl": "https://example.com/summer-sale",
        "biddingStrategy": "MAXIMIZE_CONVERSIONS"
      },
      "tiktok": {
        "objective": "TRAFFIC",
        "targeting": {
          "age_groups": ["18-24", "25-34"]
        }
      }
    }
  }'
```

Response:
```json
{
  "status": "accepted",
  "success": true,
  "job_id": "multi_1701234567_abc123",
  "platforms": ["meta", "google", "tiktok"],
  "overall_status": "in_progress",
  "platform_statuses": [
    {
      "platform": "meta",
      "status": "processing"
    },
    {
      "platform": "google",
      "status": "processing"
    },
    {
      "platform": "tiktok",
      "status": "processing"
    }
  ],
  "message": "Publishing in progress... (0/3 completed)",
  "next_steps": {
    "check_status": "/api/publish/status/multi_1701234567_abc123",
    "monitor_progress": "/api/publish/status/multi_1701234567_abc123"
  }
}
```

### 3. Check Publishing Status

```bash
curl http://localhost:8000/api/publish/status/multi_1701234567_abc123
```

Response:
```json
{
  "status": "success",
  "job": {
    "jobId": "multi_1701234567_abc123",
    "creativeId": "summer_sale_2024",
    "campaignName": "Summer Sale 2024",
    "platforms": ["meta", "google", "tiktok"],
    "overallStatus": "completed",
    "successCount": 3,
    "failureCount": 0,
    "totalPlatforms": 3,
    "createdAt": "2024-12-05T10:30:00Z",
    "completedAt": "2024-12-05T10:32:15Z"
  },
  "platformStatuses": [
    {
      "platform": "meta",
      "status": "live",
      "campaignId": "meta_campaign_789",
      "adSetId": "meta_adset_456",
      "adId": "meta_ad_123",
      "videoId": "meta_video_999",
      "lastUpdated": "2024-12-05T10:31:30Z"
    },
    {
      "platform": "google",
      "status": "live",
      "campaignId": "google_campaign_321",
      "adGroupId": "google_adgroup_654",
      "adId": "google_ad_987",
      "videoId": "YT_dQw4w9WgXcQ",
      "lastUpdated": "2024-12-05T10:32:10Z"
    },
    {
      "platform": "tiktok",
      "status": "live",
      "campaignId": "tiktok_campaign_555",
      "adId": "tiktok_ad_444",
      "lastUpdated": "2024-12-05T10:32:15Z"
    }
  ],
  "metrics": {
    "totalImpressions": 0,
    "totalClicks": 0,
    "totalSpend": 0,
    "averageCtr": 0,
    "overallRoas": 0,
    "platformBreakdown": {}
  },
  "budgetAllocation": {
    "meta": 500,
    "google": 300,
    "tiktok": 200
  }
}
```

## Advanced Examples

### Selective Platform Publishing

Publish to Meta and Google only:

```bash
curl -X POST http://localhost:8000/api/publish/multi \
  -H "Content-Type: application/json" \
  -d '{
    "creative_id": "brand_awareness_q4",
    "video_path": "/videos/brand_story.mp4",
    "platforms": ["meta", "google"],
    "budget_allocation": {
      "meta": 600,
      "google": 400
    },
    "campaign_name": "Q4 Brand Awareness"
  }'
```

### Custom Budget Allocation

Calculate recommended allocation:

```bash
curl -X POST http://localhost:8000/api/platforms/budget-allocation \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["meta", "google", "tiktok"],
    "total_budget": 5000
  }'
```

Response:
```json
{
  "status": "success",
  "total_budget": 5000,
  "platforms": ["meta", "google", "tiktok"],
  "allocation": {
    "meta": 2500,
    "google": 1500,
    "tiktok": 1000
  },
  "percentages": {
    "meta": "50.0%",
    "google": "30.0%",
    "tiktok": "20.0%"
  },
  "note": "Budget allocated using default platform weights (Meta: 50%, Google: 30%, TikTok: 20%)"
}
```

With custom weights:

```bash
curl -X POST http://localhost:8000/api/platforms/budget-allocation \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["meta", "google", "tiktok"],
    "total_budget": 5000,
    "custom_weights": {
      "meta": 0.40,
      "google": 0.40,
      "tiktok": 0.20
    }
  }'
```

### View Platform Specifications

```bash
# All platforms
curl http://localhost:8000/api/platforms/specs

# Specific platforms
curl "http://localhost:8000/api/platforms/specs?platforms=meta,google"
```

Response:
```json
{
  "status": "success",
  "platforms": ["meta", "google", "tiktok"],
  "specs": [
    {
      "platform": "meta",
      "aspectRatio": "9:16",
      "width": 1080,
      "height": 1920,
      "maxDuration": 60,
      "minDuration": 1,
      "maxFileSize": 4000,
      "formats": ["mp4", "mov"],
      "placement": "reels"
    },
    {
      "platform": "google",
      "aspectRatio": "16:9",
      "width": 1920,
      "height": 1080,
      "maxDuration": 360,
      "minDuration": 6,
      "maxFileSize": 1024,
      "formats": ["mp4", "mov", "avi"],
      "placement": "youtube_in_stream"
    }
    // ... more specs
  ],
  "total_specs": 9,
  "usage": {
    "meta": "Facebook/Instagram Ads - Various placements (Feed, Reels, Stories)",
    "google": "Google Ads - YouTube and Display Network",
    "tiktok": "TikTok Ads - Vertical video only (9:16)"
  }
}
```

### List All Publishing Jobs

```bash
curl "http://localhost:8000/api/publish/jobs?limit=10"
```

Response:
```json
{
  "status": "success",
  "jobs": [
    {
      "jobId": "multi_1701234567_abc123",
      "creativeId": "summer_sale_2024",
      "campaignName": "Summer Sale 2024",
      "platforms": ["meta", "google", "tiktok"],
      "overallStatus": "completed",
      "successCount": 3,
      "failureCount": 0,
      "totalPlatforms": 3,
      "createdAt": "2024-12-05T10:30:00Z",
      "completedAt": "2024-12-05T10:32:15Z"
    }
    // ... more jobs
  ],
  "summary": {
    "totalJobs": 15,
    "pendingJobs": 2,
    "inProgressJobs": 3,
    "completedJobs": 8,
    "failedJobs": 1,
    "partialSuccessJobs": 1
  },
  "count": 10
}
```

## Frontend Integration

### React Component Usage

```tsx
import React from 'react';
import MultiPlatformPublisher from './components/MultiPlatformPublisher';

function CampaignManager() {
  const handlePublishSuccess = (jobId: string) => {
    console.log('Campaign published successfully:', jobId);
    // Navigate to monitoring dashboard
    window.location.href = `/campaigns/monitor/${jobId}`;
  };

  const handlePublishError = (error: string) => {
    console.error('Publishing failed:', error);
    // Show error notification
    alert(`Failed to publish: ${error}`);
  };

  return (
    <div className="campaign-manager">
      <h1>Create Multi-Platform Campaign</h1>

      <MultiPlatformPublisher
        creativeId="summer_sale_2024"
        videoPath="/uploads/summer_promo.mp4"
        onPublishSuccess={handlePublishSuccess}
        onPublishError={handlePublishError}
      />
    </div>
  );
}

export default CampaignManager;
```

### With Pre-filled Data

```tsx
<MultiPlatformPublisher
  creativeId="flash_sale_nov"
  videoPath="/videos/flash_sale.mp4"
  initialBudget={2000}
  initialPlatforms={['meta', 'google']}
  initialCampaignName="Black Friday Flash Sale"
/>
```

## Error Handling

### Partial Success

When some platforms succeed and others fail:

```json
{
  "success": true,
  "job_id": "multi_123",
  "overall_status": "partial_success",
  "platform_statuses": [
    {
      "platform": "meta",
      "status": "live",
      "campaignId": "meta_campaign_456"
    },
    {
      "platform": "google",
      "status": "failed",
      "error": "Invalid video format for YouTube"
    },
    {
      "platform": "tiktok",
      "status": "live",
      "campaignId": "tiktok_campaign_789"
    }
  ],
  "message": "Published to 2/3 platform(s). 1 failed.",
  "errors": [
    {
      "platform": "google",
      "error": "Invalid video format for YouTube"
    }
  ]
}
```

### Complete Failure

When all platforms fail:

```json
{
  "success": false,
  "job_id": "multi_456",
  "overall_status": "failed",
  "platform_statuses": [
    {
      "platform": "meta",
      "status": "failed",
      "error": "Invalid access token"
    },
    {
      "platform": "google",
      "status": "failed",
      "error": "Quota exceeded"
    },
    {
      "platform": "tiktok",
      "status": "failed",
      "error": "Account not configured"
    }
  ],
  "message": "Failed to publish to all 3 platform(s)",
  "errors": [
    { "platform": "meta", "error": "Invalid access token" },
    { "platform": "google", "error": "Quota exceeded" },
    { "platform": "tiktok", "error": "Account not configured" }
  ]
}
```

## Performance Monitoring

Monitor real-time metrics after publishing:

```bash
# Poll status every 5 seconds
while true; do
  curl http://localhost:8000/api/publish/status/multi_123 | jq '.platformStatuses[].metrics'
  sleep 5
done
```

Sample output with metrics:
```json
{
  "platform": "meta",
  "status": "live",
  "metrics": {
    "impressions": 15234,
    "clicks": 456,
    "spend": 87.50,
    "conversions": 23,
    "ctr": 0.0299,
    "cpa": 3.80,
    "roas": 2.85
  }
}
```

## Best Practices

### 1. Test with Single Platform First

```bash
# Test Meta only
curl -X POST http://localhost:8000/api/publish/multi \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["meta"],
    "budget_allocation": {"meta": 100},
    ...
  }'
```

### 2. Use Recommended Budget Allocation

Always call budget allocation endpoint first:

```bash
# 1. Get recommended allocation
ALLOCATION=$(curl -X POST http://localhost:8000/api/platforms/budget-allocation \
  -H "Content-Type: application/json" \
  -d '{"platforms": ["meta", "google", "tiktok"], "total_budget": 1000}')

# 2. Use in publish request
curl -X POST http://localhost:8000/api/publish/multi \
  -H "Content-Type: application/json" \
  -d "{
    \"platforms\": [\"meta\", \"google\", \"tiktok\"],
    \"budget_allocation\": $(echo $ALLOCATION | jq '.allocation'),
    ...
  }"
```

### 3. Monitor Job Status

Set up status polling after publishing:

```javascript
async function monitorJob(jobId) {
  const maxAttempts = 60; // 5 minutes max
  const interval = 5000; // 5 seconds

  for (let i = 0; i < maxAttempts; i++) {
    const response = await fetch(`/api/publish/status/${jobId}`);
    const data = await response.json();

    console.log(`Status: ${data.job.overallStatus}`);
    console.log(`Progress: ${data.job.successCount}/${data.job.totalPlatforms}`);

    if (['completed', 'partial_success', 'failed'].includes(data.job.overallStatus)) {
      return data;
    }

    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error('Job monitoring timeout');
}
```

### 4. Handle Platform-Specific Errors

```typescript
function retryFailedPlatforms(job) {
  const failedPlatforms = job.platformStatuses
    .filter(ps => ps.status === 'failed')
    .map(ps => ps.platform);

  if (failedPlatforms.length === 0) return;

  console.log('Retrying failed platforms:', failedPlatforms);

  // Publish only to failed platforms
  publishMultiPlatform({
    ...originalRequest,
    platforms: failedPlatforms
  });
}
```

## Troubleshooting

### Video Format Issues

If format adaptation fails, check video specs:

```bash
ffprobe -v error -show_format -show_streams /path/to/video.mp4
```

### Platform Authentication

Verify platform credentials:

```bash
# Meta
curl http://localhost:8083/api/account/info

# Google
curl http://localhost:8084/api/account/info

# TikTok
curl http://localhost:8085/api/account/info
```

### Budget Allocation Not Adding Up

Ensure total budget matches sum of allocations:

```javascript
const allocation = { meta: 500, google: 300, tiktok: 200 };
const total = Object.values(allocation).reduce((a, b) => a + b, 0);
console.log(total); // Should equal total_budget (1000)
```

## Next Steps

1. Deploy services to production
2. Set up monitoring and alerting
3. Configure real platform credentials
4. Test with small budgets first
5. Scale up gradually

For more information, see the main [README.md](./README.md).
