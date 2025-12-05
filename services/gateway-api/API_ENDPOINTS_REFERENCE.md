# Gateway API - Complete Endpoint Reference

**Base URL**: `http://localhost:8000/api`

---

## 🎯 Campaigns API

### Create Campaign
```http
POST /api/campaigns
Content-Type: application/json

{
  "name": "Summer Sale 2025",
  "budget_daily": 500.00,
  "target_audience": {
    "age_range": "25-45",
    "interests": ["fitness", "wellness"]
  },
  "objective": "conversions",
  "status": "draft"
}
```

### List Campaigns
```http
GET /api/campaigns?status=active&limit=20&offset=0
```

### Get Campaign Details
```http
GET /api/campaigns/{campaign_id}
```

### Update Campaign
```http
PUT /api/campaigns/{campaign_id}
Content-Type: application/json

{
  "name": "Updated Campaign Name",
  "budget_daily": 750.00,
  "status": "active"
}
```

### Delete Campaign
```http
DELETE /api/campaigns/{campaign_id}
```

### Launch Campaign
```http
POST /api/campaigns/{campaign_id}/launch
Content-Type: application/json

{
  "platforms": ["meta", "google"],
  "budget_allocation": {
    "meta": 300,
    "google": 200
  }
}
```

### Pause Campaign
```http
POST /api/campaigns/{campaign_id}/pause
```

---

## 📊 Analytics API

### Dashboard Overview
```http
GET /api/analytics/overview?time_range=30d
```

**Response:**
```json
{
  "status": "success",
  "time_range": "30d",
  "overview": {
    "campaigns": { "total": 15, "active": 8, "paused": 7 },
    "videos": { "total": 45 },
    "performance": {
      "spend": 12500.50,
      "impressions": 500000,
      "clicks": 12500,
      "conversions": 625,
      "ctr": 2.5,
      "cpc": 1.0,
      "cpa": 20.0,
      "conversion_rate": 5.0
    }
  },
  "top_campaigns": [...],
  "trends": [...]
}
```

### Campaign Analytics
```http
GET /api/analytics/campaigns/{campaign_id}?start_date=2025-01-01&end_date=2025-01-31
```

### Performance Trends
```http
GET /api/analytics/trends?metric=conversions&days=30
```

### Predictions vs Actual
```http
GET /api/analytics/predictions-vs-actual?limit=20
```

### Real-time Metrics (Last 24h)
```http
GET /api/analytics/real-time
```

---

## 🧪 A/B Testing API

### Create A/B Test
```http
POST /api/ab-tests
Content-Type: application/json

{
  "name": "Hook Test - Question vs Statement",
  "campaign_id": "uuid-here",
  "variants": [
    {
      "name": "Question Hook",
      "ad_id": "uuid-1",
      "video_id": "uuid-vid-1"
    },
    {
      "name": "Statement Hook",
      "ad_id": "uuid-2",
      "video_id": "uuid-vid-2"
    }
  ],
  "objective": "conversions",
  "budget_split": "thompson_sampling",
  "total_budget": 1000
}
```

### List A/B Tests
```http
GET /api/ab-tests?campaign_id=uuid&status=active&limit=20
```

### Get Experiment Details
```http
GET /api/ab-tests/{experiment_id}
```

### Get Winner
```http
GET /api/ab-tests/{experiment_id}/winner?confidence_level=0.95
```

**Response:**
```json
{
  "status": "success",
  "winner": {
    "variant_id": "uuid-1",
    "conversions": 125,
    "spend": 450,
    "roas": 5.5,
    "confidence": 0.97
  },
  "all_variants": [...]
}
```

### Promote Winner
```http
POST /api/ab-tests/{experiment_id}/promote
Content-Type: application/json

{
  "variant_id": "uuid-1",
  "new_budget": 2000
}
```

### Pause Experiment
```http
POST /api/ab-tests/{experiment_id}/pause
```

### Get Detailed Results
```http
GET /api/ab-tests/{experiment_id}/results
```

### Get Variant Performance
```http
GET /api/ab-tests/{experiment_id}/variants
```

---

## 🎬 Ads Management API

### Create Ad
```http
POST /api/ads
Content-Type: application/json

{
  "campaign_id": "uuid-campaign",
  "video_id": "uuid-video",
  "arc_name": "fitness_transformation",
  "clip_ids": ["clip-1", "clip-2", "clip-3"],
  "caption": "Transform your body in 30 days! 💪",
  "status": "pending_approval"
}
```

**Note:** CTR and ROAS predictions are automatically generated via ML service.

### List Ads
```http
GET /api/ads?campaign_id=uuid&status=approved&limit=20&offset=0
```

### Get Ad Details
```http
GET /api/ads/{ad_id}
```

**Response:**
```json
{
  "status": "success",
  "ad": {
    "ad_id": "uuid",
    "campaign": { "id": "uuid", "name": "Summer Sale", "status": "active" },
    "video": {
      "title": "Transformation Story",
      "url": "gs://bucket/video.mp4",
      "thumbnail": "gs://bucket/thumb.jpg",
      "duration_seconds": 30
    },
    "predictions": {
      "ctr": 0.025,
      "roas": 3.5
    },
    "status": "approved",
    "performance": {
      "impressions": 50000,
      "clicks": 1250,
      "conversions": 62,
      "spend": 125.50,
      "actual_ctr": 2.5,
      "actual_roas": 4.2
    }
  }
}
```

### Update Ad
```http
PUT /api/ads/{ad_id}
Content-Type: application/json

{
  "caption": "Updated caption text",
  "status": "approved"
}
```

### Delete Ad
```http
DELETE /api/ads/{ad_id}
```

**Note:** Cannot delete published ads.

### Approve Ad
```http
POST /api/ads/{ad_id}/approve
Content-Type: application/json

{
  "notes": "Great creative! Approved for publishing."
}
```

### Reject Ad
```http
POST /api/ads/{ad_id}/reject
Content-Type: application/json

{
  "reason": "Hook needs improvement. Please revise."
}
```

---

## 🔮 Predictions API

### Predict CTR
```http
POST /api/predictions/ctr
Content-Type: application/json

{
  "video_id": "uuid-video",
  "clip_ids": ["clip-1", "clip-2"],
  "arc_name": "fitness_transformation",
  "include_confidence": true
}
```

**Response:**
```json
{
  "status": "success",
  "prediction": {
    "predicted_ctr": 0.0245,
    "predicted_roas": 3.2,
    "confidence": 0.75,
    "confidence_interval": {
      "lower": 0.0196,
      "upper": 0.0294
    },
    "model_version": "xgboost-v1",
    "timestamp": "2025-12-05T10:30:00Z"
  }
}
```

### Predict ROAS
```http
POST /api/predictions/roas
Content-Type: application/json

{
  "campaign_id": "uuid-campaign",
  "budget": 1000,
  "target_audience": {
    "age_range": "25-45",
    "interests": ["fitness"]
  },
  "platform": "meta"
}
```

### Predict Campaign Performance
```http
POST /api/predictions/campaign
Content-Type: application/json

{
  "campaign_data": {
    "budget": 5000,
    "duration_days": 30,
    "target_audience": {...}
  },
  "prediction_days": 30
}
```

### Get Prediction Accuracy
```http
GET /api/predictions/accuracy?start_date=2025-01-01&metric=all
```

### Batch Predict
```http
POST /api/predictions/batch
Content-Type: application/json

{
  "creatives": [
    { "id": "creative-1", "clip_ids": [...] },
    { "id": "creative-2", "clip_ids": [...] },
    { "id": "creative-3", "clip_ids": [...] }
  ]
}
```

---

## 📄 Reports API

### Generate Report
```http
POST /api/reports/generate
Content-Type: application/json

{
  "report_type": "campaign_performance",
  "format": "pdf",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "campaign_ids": ["uuid-1", "uuid-2"],
  "company_name": "Acme Inc.",
  "company_logo": "https://example.com/logo.png"
}
```

**Report Types:**
- `campaign_performance` - Overall campaign metrics
- `ad_creative_analysis` - Creative performance breakdown
- `audience_insights` - Demographics and targeting
- `roas_breakdown` - Revenue attribution
- `weekly_summary` - Week-over-week comparison
- `monthly_executive` - Executive summary

### List Reports
```http
GET /api/reports?limit=20
```

### Download Report
```http
GET /api/reports/{report_id}/download
```

### Delete Report
```http
DELETE /api/reports/{report_id}
```

### Get Report Templates
```http
GET /api/reports/templates
```

---

## 🚀 Existing Endpoints (Already Implemented)

### Video Assets
```http
GET /api/assets
GET /api/assets/{assetId}/clips
POST /api/analyze
POST /api/ingest/local/folder
POST /api/search/clips
```

### Scoring & Predictions
```http
POST /api/score/storyboard
```

### Rendering
```http
POST /api/render/remix
POST /api/render/story_arc
GET /api/render/status/{jobId}
```

### Publishing
```http
POST /api/publish/meta
POST /api/publish/multi
GET /api/publish/status/{job_id}
GET /api/publish/jobs
GET /api/publish/summary
```

### Google Ads
```http
POST /api/google-ads/campaigns
POST /api/google-ads/ad-groups
POST /api/google-ads/video-ads
GET /api/google-ads/performance/campaign/{campaignId}
POST /api/google-ads/publish
```

### Meta Insights
```http
GET /api/insights
```

### Approval Queue
```http
GET /api/approval/queue
POST /api/approval/approve/{ad_id}
```

### AI Features
```http
POST /api/council/evaluate
POST /api/oracle/predict
POST /api/director/generate
POST /api/pipeline/generate-campaign
```

### Experiments (A/B Tests - Alternative Endpoint)
```http
GET /api/experiments
```

### Trending Ads
```http
GET /api/ads/trending?category=fitness&limit=10
```

### Avatars
```http
GET /avatars
```

---

## 🔐 Authentication & Security

All endpoints support:
- **Rate Limiting**: 100 req/min (general), 20 req/min (auth), 10 req/min (uploads)
- **Input Validation**: Type checking, length limits, sanitization
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: HTML sanitization for text fields
- **API Key Validation**: `validateApiKey` middleware (optional)

### Headers
```http
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY (optional)
```

---

## 📊 Response Status Codes

- **200 OK** - Success
- **201 Created** - Resource created
- **202 Accepted** - Async operation queued
- **400 Bad Request** - Validation error
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Not allowed (e.g., unpublished ad)
- **404 Not Found** - Resource doesn't exist
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error
- **503 Service Unavailable** - Dependency unavailable

---

## 🧪 Example Usage

### Complete Campaign Workflow
```bash
# 1. Create campaign
curl -X POST http://localhost:8000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "Q1 Campaign", "budget_daily": 500}'

# 2. Create ad
curl -X POST http://localhost:8000/api/ads \
  -H "Content-Type: application/json" \
  -d '{"campaign_id": "uuid", "video_id": "uuid-video"}'

# 3. Get prediction
curl -X POST http://localhost:8000/api/predictions/ctr \
  -H "Content-Type: application/json" \
  -d '{"video_id": "uuid-video"}'

# 4. Approve ad
curl -X POST http://localhost:8000/api/ads/{ad_id}/approve

# 5. Launch campaign
curl -X POST http://localhost:8000/api/campaigns/{campaign_id}/launch \
  -H "Content-Type: application/json" \
  -d '{"platforms": ["meta"]}'

# 6. Monitor analytics
curl http://localhost:8000/api/analytics/campaigns/{campaign_id}
```

---

## 📚 Additional Resources

- **OpenAPI Spec**: (TODO: Generate from code)
- **Postman Collection**: (TODO: Create collection)
- **SDK**: (TODO: Generate TypeScript SDK)

---

**Last Updated**: 2025-12-05
**Agent**: Agent 58 - API Gateway Final Wiring
**Version**: 1.0.0
