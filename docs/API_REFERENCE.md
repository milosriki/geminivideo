# GeminiVideo API Reference

**Version:** 1.0.0
**Base URL:** `https://api.geminivideo.com` (Production) | `http://localhost:8000` (Development)
**Last Updated:** 2025-12-06

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limits](#rate-limits)
3. [REST API Endpoints](#rest-api-endpoints)
   - [Campaigns](#campaigns)
   - [Ads](#ads)
   - [Creatives](#creatives)
   - [Analytics](#analytics)
   - [A/B Testing](#ab-testing)
   - [Predictions](#predictions)
   - [Multi-Platform Publishing](#multi-platform-publishing)
   - [Google Ads](#google-ads)
   - [Meta Ads Library](#meta-ads-library)
   - [AI Services](#ai-services)
   - [Webhooks](#webhooks)
4. [External API Integrations](#external-api-integrations)
   - [Meta Marketing API](#meta-marketing-api)
   - [Meta Conversions API (CAPI)](#meta-conversions-api)
   - [Google Ads API](#google-ads-api-integration)
   - [Runway Gen-3](#runway-gen-3-api)
   - [ElevenLabs Voice](#elevenlabs-voice-api)
5. [Real-Time APIs](#real-time-apis)
6. [Error Handling](#error-handling)

---

## Authentication

All API requests require authentication using one of the following methods:

### API Key Authentication
```http
Authorization: Bearer YOUR_API_KEY
```

### Firebase Authentication
```http
Authorization: Bearer FIREBASE_ID_TOKEN
```

### Example
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.geminivideo.com/api/campaigns
```

---

## Rate Limits

The API implements multiple rate limit tiers to ensure service quality:

### Global Rate Limits
- **Global**: 1000 requests per 15 minutes per IP
- **API Operations**: 300 requests per 15 minutes per user
- **File Uploads**: 50 requests per 15 minutes per user
- **Authentication**: 20 requests per 15 minutes per IP

### Rate Limit Headers
```http
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 299
X-RateLimit-Reset: 1638316800
```

### Rate Limit Response (429)
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 900
}
```

---

## REST API Endpoints

### Campaigns

#### Create Campaign
```http
POST /api/campaigns
```

**Request Body:**
```json
{
  "name": "Summer Sale 2025",
  "budget_daily": 100.00,
  "target_audience": {
    "age_min": 25,
    "age_max": 45,
    "interests": ["fitness", "health"]
  },
  "objective": "conversions",
  "status": "draft"
}
```

**Response (201):**
```json
{
  "status": "success",
  "message": "Campaign created successfully",
  "campaign": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Summer Sale 2025",
    "status": "draft",
    "budget_daily": 100.00,
    "target_audience": {...},
    "created_at": "2025-12-06T10:00:00Z",
    "updated_at": "2025-12-06T10:00:00Z"
  }
}
```

#### List Campaigns
```http
GET /api/campaigns?status=active&limit=20&offset=0
```

**Query Parameters:**
- `status` (optional): `draft`, `active`, `paused`, `completed`
- `limit` (optional): 1-100, default 20
- `offset` (optional): default 0

**Response (200):**
```json
{
  "status": "success",
  "campaigns": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Summer Sale 2025",
      "status": "active",
      "budget_daily": 100.00,
      "stats": {
        "video_count": 5,
        "total_spend": 450.00,
        "total_impressions": 50000,
        "total_clicks": 2500,
        "total_conversions": 125,
        "ctr": 5.0
      }
    }
  ],
  "pagination": {
    "total": 42,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

#### Get Campaign Details
```http
GET /api/campaigns/{id}
```

**Response (200):**
```json
{
  "status": "success",
  "campaign": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Summer Sale 2025",
    "status": "active",
    "budget_daily": 100.00,
    "stats": {...},
    "videos": [
      {
        "id": "video-123",
        "title": "Product Demo",
        "status": "published",
        "video_url": "/videos/demo.mp4",
        "performance": {
          "impressions": 10000,
          "clicks": 500,
          "conversions": 25
        }
      }
    ]
  }
}
```

#### Update Campaign
```http
PUT /api/campaigns/{id}
```

**Request Body:**
```json
{
  "name": "Updated Campaign Name",
  "budget_daily": 150.00,
  "status": "paused"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Campaign updated successfully",
  "campaign": {...}
}
```

#### Delete Campaign
```http
DELETE /api/campaigns/{id}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Campaign deleted successfully",
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### Launch Campaign
```http
POST /api/campaigns/{id}/launch
```

**Request Body:**
```json
{
  "platforms": ["meta", "google"],
  "budget_allocation": {
    "meta": 60.00,
    "google": 40.00
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Campaign launched successfully",
  "campaign": {...},
  "platforms": [
    {
      "platform": "meta",
      "status": "success",
      "data": {...}
    }
  ]
}
```

#### Pause Campaign
```http
POST /api/campaigns/{id}/pause
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Campaign paused successfully",
  "campaign": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Summer Sale 2025",
    "status": "paused"
  }
}
```

#### Resume Campaign
```http
POST /api/campaigns/{id}/resume
```

#### Campaign Predictions
```http
POST /api/campaigns/predict
```

**Request Body:**
```json
{
  "campaign_data": {
    "budget": 1000,
    "target_audience": {...},
    "objective": "conversions"
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "predictions": {
    "predicted_ctr": 0.035,
    "predicted_roas": 2.8,
    "predicted_conversions": 140,
    "predicted_spend": 1000,
    "confidence_score": 0.82,
    "recommendation": "Launch campaign with current settings",
    "risk_level": "low"
  }
}
```

---

### Ads

#### Create Ad
```http
POST /api/ads
```

**Request Body:**
```json
{
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "video_id": "video-456",
  "caption": "Transform your fitness journey today!",
  "predicted_ctr": 0.042,
  "predicted_roas": 3.2,
  "status": "pending_approval"
}
```

**Response (201):**
```json
{
  "status": "success",
  "message": "Ad created successfully",
  "ad": {
    "ad_id": "ad-789",
    "asset_id": "video-456",
    "predicted_ctr": 0.042,
    "predicted_roas": 3.2,
    "status": "pending_approval",
    "approved": false,
    "created_at": "2025-12-06T10:00:00Z"
  }
}
```

#### List Ads
```http
GET /api/ads?status=approved&limit=20
```

**Query Parameters:**
- `campaign_id` (optional): UUID
- `status` (optional): `pending_approval`, `approved`, `rejected`, `published`
- `approved` (optional): boolean
- `limit` (optional): 1-100
- `offset` (optional): default 0

**Response (200):**
```json
{
  "status": "success",
  "ads": [
    {
      "ad_id": "ad-789",
      "campaign_name": "Summer Sale 2025",
      "video_title": "Product Demo",
      "predicted_ctr": 0.042,
      "predicted_roas": 3.2,
      "status": "approved",
      "performance": {
        "impressions": 5000,
        "clicks": 210,
        "conversions": 12,
        "actual_ctr": 4.2
      }
    }
  ],
  "pagination": {...}
}
```

#### Get Ad Details
```http
GET /api/ads/{id}
```

**Response (200):**
```json
{
  "status": "success",
  "ad": {
    "ad_id": "ad-789",
    "campaign": {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "Summer Sale 2025"
    },
    "video": {
      "title": "Product Demo",
      "url": "/videos/demo.mp4",
      "duration_seconds": 30
    },
    "predictions": {
      "ctr": 0.042,
      "roas": 3.2
    },
    "performance": {...}
  }
}
```

#### Update Ad
```http
PUT /api/ads/{id}
```

**Request Body:**
```json
{
  "caption": "Updated caption",
  "status": "approved"
}
```

#### Approve Ad
```http
POST /api/ads/{id}/approve
```

**Request Body:**
```json
{
  "notes": "Approved for publishing"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Ad approved successfully",
  "ad": {
    "ad_id": "ad-789",
    "status": "approved",
    "approved": true,
    "approved_at": "2025-12-06T10:05:00Z",
    "approved_by": "user-123"
  }
}
```

#### Reject Ad
```http
POST /api/ads/{id}/reject
```

**Request Body:**
```json
{
  "reason": "Does not meet brand guidelines"
}
```

#### Delete Ad
```http
DELETE /api/ads/{id}
```

---

### Creatives

#### Upload Creative Assets
```http
POST /api/creatives/upload
Content-Type: multipart/form-data
```

**Form Data:**
- `files`: File[] (max 10 files, max 500MB each)
- `campaign_id` (optional): UUID
- `title` (optional): string
- `description` (optional): string

**Response (201):**
```json
{
  "status": "success",
  "message": "Successfully uploaded 3 creative asset(s)",
  "assets": [
    {
      "id": "asset-123",
      "type": "video",
      "title": "product-demo.mp4",
      "file_url": "/uploads/1234567890-uuid-product-demo.mp4",
      "file_size": 15728640,
      "mime_type": "video/mp4",
      "status": "uploaded",
      "created_at": "2025-12-06T10:00:00Z"
    }
  ],
  "count": 3,
  "upload_summary": {
    "total_files": 3,
    "total_size_bytes": 47185920,
    "total_size_mb": "45.00"
  }
}
```

#### List Creative Assets
```http
GET /api/creatives?type=video&limit=20
```

**Query Parameters:**
- `campaign_id` (optional): UUID
- `type` (optional): `image`, `video`, `other`
- `status` (optional): `uploaded`, `processing`, `ready`, `failed`
- `limit` (optional): 1-100
- `offset` (optional): default 0

**Response (200):**
```json
{
  "status": "success",
  "assets": [
    {
      "id": "asset-123",
      "type": "video",
      "title": "product-demo.mp4",
      "file_url": "/uploads/demo.mp4",
      "file_size": 15728640,
      "thumbnail_url": "/thumbnails/demo.jpg",
      "status": "ready",
      "created_at": "2025-12-06T10:00:00Z"
    }
  ],
  "pagination": {...}
}
```

#### Get Creative Asset
```http
GET /api/creatives/{id}
```

#### Delete Creative Asset
```http
DELETE /api/creatives/{id}
```

---

### Analytics

#### Dashboard Overview
```http
GET /api/analytics/overview?time_range=30d
```

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD
- `time_range` (optional): `today`, `7d`, `30d`, `90d`, `all`

**Response (200):**
```json
{
  "status": "success",
  "time_range": "30d",
  "overview": {
    "campaigns": {
      "total": 42,
      "active": 15,
      "paused": 27
    },
    "videos": {
      "total": 156
    },
    "performance": {
      "spend": 12500.00,
      "impressions": 2500000,
      "clicks": 125000,
      "conversions": 6250,
      "ctr": 5.0,
      "cpc": 0.10,
      "cpa": 2.00,
      "conversion_rate": 5.0
    }
  },
  "top_campaigns": [...],
  "trends": [...]
}
```

#### Campaign Analytics
```http
GET /api/analytics/campaigns/{id}?start_date=2025-11-01&end_date=2025-12-01
```

**Response (200):**
```json
{
  "status": "success",
  "campaign": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "name": "Summer Sale 2025"
  },
  "performance": {
    "total_spend": 1200.00,
    "total_impressions": 150000,
    "total_clicks": 7500,
    "total_conversions": 375,
    "avg_ctr": 5.0,
    "cpc": 0.16,
    "cpa": 3.20
  },
  "daily_trend": [
    {
      "date": "2025-11-01",
      "spend": 40.00,
      "impressions": 5000,
      "clicks": 250,
      "conversions": 12,
      "ctr": 5.0
    }
  ],
  "videos": [...]
}
```

#### Performance Trends
```http
GET /api/analytics/trends?metric=conversions&days=30
```

**Query Parameters:**
- `metric` (optional): `spend`, `impressions`, `clicks`, `conversions`, `ctr`
- `days` (optional): 1-365, default 30

**Response (200):**
```json
{
  "status": "success",
  "metric": "conversions",
  "days": 30,
  "daily_data": [
    {
      "date": "2025-12-01",
      "spend": 150.00,
      "impressions": 15000,
      "clicks": 750,
      "conversions": 38,
      "ctr": 5.0
    }
  ],
  "week_over_week": {
    "spend_growth": 12.5,
    "impressions_growth": 8.3,
    "clicks_growth": 15.2,
    "conversions_growth": 22.1
  }
}
```

#### Predictions vs Actual
```http
GET /api/analytics/predictions-vs-actual?limit=20
```

**Response (200):**
```json
{
  "status": "success",
  "overall_accuracy": {
    "avg_ctr_error_pct": "15.23",
    "avg_roas_error_pct": "18.45",
    "total_comparisons": 20,
    "valid_ctr_comparisons": 18,
    "valid_roas_comparisons": 15
  },
  "comparisons": [
    {
      "ad_id": "ad-789",
      "campaign_name": "Summer Sale 2025",
      "predictions": {
        "ctr": 0.042,
        "roas": 3.2
      },
      "actual": {
        "ctr": 0.038,
        "roas": 2.9,
        "impressions": 10000,
        "clicks": 380,
        "conversions": 19
      },
      "accuracy": {
        "ctr_error_pct": "9.52",
        "roas_error_pct": "9.38",
        "ctr_accurate": true,
        "roas_accurate": true
      }
    }
  ]
}
```

#### Real-Time Analytics
```http
GET /api/analytics/real-time
```

**Response (200):**
```json
{
  "status": "success",
  "timestamp": "2025-12-06T10:00:00Z",
  "time_range": "last_24_hours",
  "active_campaigns": 15,
  "totals": {
    "spend": 1200.00,
    "impressions": 150000,
    "clicks": 7500,
    "conversions": 375,
    "ctr": 5.0,
    "cpc": 0.16,
    "cpa": 3.20
  },
  "by_platform": [
    {
      "platform": "meta",
      "spend": 720.00,
      "impressions": 90000,
      "clicks": 4500,
      "conversions": 225,
      "avg_ctr": 5.0,
      "active_ads": 8
    }
  ]
}
```

#### ROI Performance
```http
GET /api/analytics/roi/performance?timeRange=30d
```

**Query Parameters:**
- `timeRange` (optional): `today`, `7d`, `30d`, `90d`, `all`
- `campaign_id` (optional): UUID

**Response (200):**
```json
{
  "status": "success",
  "time_range": "30d",
  "overall": {
    "total_spend": 12500.00,
    "total_revenue": 37500.00,
    "total_conversions": 750,
    "total_profit": 25000.00,
    "roas": 3.0,
    "roi_percentage": 200.00,
    "avg_aov": 50
  },
  "campaigns": [
    {
      "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
      "campaign_name": "Summer Sale 2025",
      "spend": 1200.00,
      "revenue": 3840.00,
      "conversions": 76,
      "roas": 3.2,
      "roi_percentage": 220.00,
      "profit": 2640.00
    }
  ]
}
```

#### ROI Trends
```http
GET /api/analytics/roi/trends?period=daily&days=30
```

**Query Parameters:**
- `period` (optional): `daily`, `weekly`, `monthly`
- `days` (optional): 1-365, default 30
- `campaign_id` (optional): UUID

**Response (200):**
```json
{
  "status": "success",
  "period": "daily",
  "days": 30,
  "trends": [
    {
      "period": "2025-12-01",
      "spend": 150.00,
      "revenue": 480.00,
      "conversions": 9,
      "profit": 330.00,
      "roas": 3.2,
      "roi_percentage": 220.00,
      "ctr": 5.0,
      "moving_avg_roas": 3.15,
      "moving_avg_roi": 215.00
    }
  ],
  "growth_rates": {
    "roas_growth": 8.5,
    "roi_growth": 12.3,
    "revenue_growth": 15.2
  },
  "summary": {
    "avg_roas": 3.1,
    "avg_roi": 210.00,
    "total_profit": 9900.00,
    "total_revenue": 14400.00,
    "total_spend": 4500.00
  }
}
```

---

### A/B Testing

#### Create A/B Test
```http
POST /api/ab-tests
```

**Request Body:**
```json
{
  "name": "Hook Test - Variant A vs B",
  "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
  "variants": [
    {
      "name": "Variant A - Pain Point",
      "ad_id": "ad-111",
      "video_id": "video-111"
    },
    {
      "name": "Variant B - Benefit Focus",
      "ad_id": "ad-222",
      "video_id": "video-222"
    }
  ],
  "objective": "conversions",
  "budget_split": "thompson_sampling",
  "total_budget": 500.00
}
```

**Response (201):**
```json
{
  "status": "success",
  "message": "A/B test experiment created successfully",
  "experiment": {
    "experiment_id": "exp-456",
    "name": "Hook Test - Variant A vs B",
    "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
    "variants": [...],
    "objective": "conversions",
    "budget_split": "thompson_sampling",
    "total_budget": 500.00,
    "status": "active",
    "created_at": "2025-12-06T10:00:00Z"
  }
}
```

#### List A/B Tests
```http
GET /api/ab-tests?status=active&limit=20
```

#### Get A/B Test Details
```http
GET /api/ab-tests/{id}
```

**Response (200):**
```json
{
  "status": "success",
  "experiment": {
    "experiment_id": "exp-456",
    "name": "Hook Test - Variant A vs B",
    "status": "active",
    "total_budget": 500.00,
    "variants": [
      {
        "variant_id": "var-111",
        "name": "Variant A - Pain Point",
        "impressions": 5000,
        "clicks": 250,
        "conversions": 15,
        "spend": 120.00,
        "roas": 3.5,
        "ctr": 5.0
      },
      {
        "variant_id": "var-222",
        "name": "Variant B - Benefit Focus",
        "impressions": 7000,
        "clicks": 420,
        "conversions": 28,
        "spend": 180.00,
        "roas": 4.2,
        "ctr": 6.0
      }
    ]
  }
}
```

#### Get A/B Test Winner
```http
GET /api/ab-tests/{id}/winner?confidence_level=0.95
```

**Response (200):**
```json
{
  "status": "success",
  "winner": {
    "variant_id": "var-222",
    "variant_name": "Variant B - Benefit Focus",
    "conversions": 28,
    "spend": 180.00,
    "roas": 4.2,
    "confidence": 0.96,
    "statistical_significance": true
  },
  "all_variants": [...],
  "recommendation": "Promote Variant B to full budget"
}
```

#### Promote Winner
```http
POST /api/ab-tests/{id}/promote
```

**Request Body:**
```json
{
  "variant_id": "var-222",
  "new_budget": 1000.00
}
```

#### Start A/B Test
```http
POST /api/ab-tests/{id}/start
```

**Request Body:**
```json
{
  "force_start": false
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "A/B test started successfully",
  "experiment": {...},
  "thompson_sampling": {
    "enabled": true,
    "exploration_rate": 0.2,
    "confidence_threshold": 0.95
  }
}
```

#### Pause A/B Test
```http
POST /api/ab-tests/{id}/pause
```

#### Update A/B Test
```http
PUT /api/ab-tests/{id}
```

#### Delete A/B Test
```http
DELETE /api/ab-tests/{id}
```

---

### Multi-Platform Publishing

#### Publish to Multiple Platforms
```http
POST /api/publish/multi
```

**Request Body:**
```json
{
  "creative_id": "asset-123",
  "video_path": "/uploads/video.mp4",
  "platforms": ["meta", "google", "tiktok"],
  "budget_allocation": {
    "meta": 300.00,
    "google": 200.00,
    "tiktok": 100.00
  },
  "campaign_name": "Multi-Platform Launch",
  "campaign_config": {
    "objective": "conversions",
    "start_date": "2025-12-07"
  }
}
```

**Response (202):**
```json
{
  "status": "accepted",
  "job_id": "job-789",
  "message": "Multi-platform publishing initiated",
  "platforms": ["meta", "google", "tiktok"],
  "total_budget": 600.00,
  "next_steps": {
    "check_status": "/api/publish/status/job-789",
    "monitor_progress": "/api/publish/status/job-789"
  }
}
```

#### Check Publishing Status
```http
GET /api/publish/status/{job_id}
```

**Response (200):**
```json
{
  "status": "success",
  "job": {
    "jobId": "job-789",
    "creativeId": "asset-123",
    "campaignName": "Multi-Platform Launch",
    "platforms": ["meta", "google", "tiktok"],
    "overallStatus": "completed",
    "successCount": 3,
    "failureCount": 0,
    "totalPlatforms": 3,
    "createdAt": "2025-12-06T10:00:00Z",
    "completedAt": "2025-12-06T10:05:00Z"
  },
  "platformStatuses": {
    "meta": {
      "status": "completed",
      "campaign_id": "meta-campaign-123",
      "ad_id": "meta-ad-456"
    },
    "google": {
      "status": "completed",
      "campaign_id": "google-campaign-789"
    },
    "tiktok": {
      "status": "completed",
      "campaign_id": "tiktok-campaign-012"
    }
  },
  "metrics": {
    "total_reach": 150000,
    "total_spend": 600.00,
    "avg_ctr": 4.8
  }
}
```

#### Get Platform Specifications
```http
GET /api/platforms/specs?platforms=meta,google,tiktok
```

**Response (200):**
```json
{
  "status": "success",
  "platforms": ["meta", "google", "tiktok"],
  "specs": [
    {
      "platform": "meta",
      "video_specs": {
        "aspect_ratios": ["9:16", "1:1", "4:5"],
        "max_duration": 240,
        "min_duration": 1,
        "max_file_size_mb": 4000
      }
    }
  ],
  "usage": {
    "meta": "Facebook/Instagram Ads - Various placements",
    "google": "Google Ads - YouTube and Display",
    "tiktok": "TikTok Ads - Vertical video only (9:16)"
  }
}
```

#### Calculate Budget Allocation
```http
POST /api/platforms/budget-allocation
```

**Request Body:**
```json
{
  "platforms": ["meta", "google", "tiktok"],
  "total_budget": 1000.00,
  "custom_weights": {
    "meta": 0.5,
    "google": 0.3,
    "tiktok": 0.2
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "total_budget": 1000.00,
  "platforms": ["meta", "google", "tiktok"],
  "allocation": {
    "meta": 500.00,
    "google": 300.00,
    "tiktok": 200.00
  },
  "percentages": {
    "meta": "50.0%",
    "google": "30.0%",
    "tiktok": "20.0%"
  },
  "note": "Budget allocated using custom weights"
}
```

---

### Google Ads

#### Create Google Ads Campaign
```http
POST /api/google-ads/campaigns
```

**Request Body:**
```json
{
  "name": "YouTube Video Campaign",
  "budget": 500.00,
  "biddingStrategy": "MAXIMIZE_CONVERSIONS",
  "startDate": "2025-12-07",
  "endDate": "2025-12-31",
  "status": "PAUSED"
}
```

**Response (200):**
```json
{
  "status": "success",
  "campaign_id": "google-campaign-123",
  "name": "YouTube Video Campaign"
}
```

#### Create Ad Group
```http
POST /api/google-ads/ad-groups
```

**Request Body:**
```json
{
  "name": "Video Ad Group 1",
  "campaignId": "google-campaign-123",
  "cpcBidMicros": 2000000,
  "status": "ACTIVE"
}
```

#### Upload Creative to YouTube
```http
POST /api/google-ads/upload-creative
```

**Request Body:**
```json
{
  "videoPath": "/uploads/video.mp4",
  "title": "Product Demo Video",
  "description": "Check out our amazing product"
}
```

#### Create Video Ad
```http
POST /api/google-ads/video-ads
```

**Request Body:**
```json
{
  "videoPath": "/uploads/video.mp4",
  "campaignId": "google-campaign-123",
  "adGroupId": "google-adgroup-456",
  "headline": "Transform Your Life Today",
  "description": "Limited time offer",
  "finalUrl": "https://example.com/product"
}
```

#### Get Campaign Performance
```http
GET /api/google-ads/performance/campaign/{campaignId}?startDate=2025-11-01&endDate=2025-12-01
```

**Response (200):**
```json
{
  "status": "success",
  "campaign_id": "google-campaign-123",
  "metrics": {
    "impressions": 50000,
    "clicks": 2500,
    "conversions": 125,
    "spend": 450.00,
    "ctr": 5.0,
    "cpa": 3.60,
    "roas": 4.2
  }
}
```

#### Publish to Google Ads (Complete Workflow)
```http
POST /api/google-ads/publish
```

**Request Body:**
```json
{
  "videoPath": "/uploads/video.mp4",
  "campaignName": "New Product Launch",
  "budget": 1000.00,
  "adGroupName": "Main Ad Group",
  "cpcBidMicros": 3000000,
  "headline": "Revolutionary Product",
  "description": "Get 50% off today",
  "finalUrl": "https://example.com/product"
}
```

---

### Meta Ads Library

#### Search Meta Ads Library
```http
POST /api/meta/ads-library/search
```

**Request Body:**
```json
{
  "search_terms": "fitness supplements",
  "countries": ["US"],
  "platforms": ["facebook", "instagram"],
  "media_type": "VIDEO",
  "active_status": "ACTIVE",
  "limit": 100
}
```

**Response (200):**
```json
{
  "status": "success",
  "ads": [
    {
      "ad_archive_id": "123456789",
      "page_name": "Fitness Brand",
      "ad_creative_body": "Get fit with our supplements",
      "ad_snapshot_url": "https://...",
      "platforms": ["facebook", "instagram"],
      "media_type": "video",
      "is_active": true
    }
  ],
  "count": 50
}
```

#### Get Page Ads
```http
GET /api/meta/ads-library/page/{page_id}?limit=100&active_only=true
```

#### Analyze Ad Patterns
```http
POST /api/meta/ads-library/analyze
```

**Request Body:**
```json
{
  "ads": [
    {
      "ad_archive_id": "123456789",
      "ad_creative_body": "..."
    }
  ]
}
```

**Response (200):**
```json
{
  "status": "success",
  "patterns": {
    "common_themes": ["urgency", "social_proof", "discounts"],
    "avg_text_length": 125,
    "common_ctas": ["Learn More", "Shop Now"],
    "hook_patterns": [...]
  }
}
```

---

### AI Services

#### AI Council Evaluation
```http
POST /api/council/evaluate
```

**Request Body:**
```json
{
  "creative_id": "asset-123",
  "video_uri": "gs://bucket/video.mp4",
  "metadata": {
    "objective": "conversions",
    "target_audience": "fitness enthusiasts"
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "evaluation": {
    "overall_score": 8.5,
    "hook_quality": 9.0,
    "message_clarity": 8.0,
    "cta_strength": 8.5,
    "recommendations": [
      "Shorten hook to 3 seconds",
      "Add urgency to CTA"
    ]
  }
}
```

#### Oracle Predictions
```http
POST /api/oracle/predict
```

**Request Body:**
```json
{
  "campaign_data": {
    "budget": 1000,
    "target_audience": {...},
    "creative_quality_score": 8.5
  },
  "prediction_type": "all"
}
```

**Response (200):**
```json
{
  "status": "success",
  "predictions": {
    "predicted_ctr": 0.042,
    "predicted_roas": 3.2,
    "predicted_conversions": 134,
    "confidence_score": 0.85,
    "risk_factors": [...]
  }
}
```

#### Director Creative Generation
```http
POST /api/director/generate
```

**Request Body:**
```json
{
  "brief": "Create a 30-second video ad for our fitness app",
  "assets": ["/uploads/video1.mp4"],
  "style": "energetic",
  "duration": 30
}
```

**Response (202):**
```json
{
  "status": "accepted",
  "message": "Creative generation started",
  "job_id": "gen-job-123",
  "estimated_time": "2-5 minutes"
}
```

---

### Webhooks

#### Create Webhook
```http
POST /api/webhooks
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhooks/geminivideo",
  "events": ["campaign.launched", "ad.approved", "conversion.tracked"],
  "secret": "your-webhook-secret"
}
```

**Response (201):**
```json
{
  "status": "success",
  "webhook_id": "wh-123",
  "url": "https://your-app.com/webhooks/geminivideo",
  "events": ["campaign.launched", "ad.approved", "conversion.tracked"]
}
```

#### Webhook Events

##### Campaign Launched
```json
{
  "event": "campaign.launched",
  "timestamp": "2025-12-06T10:00:00Z",
  "data": {
    "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
    "campaign_name": "Summer Sale 2025",
    "platforms": ["meta", "google"],
    "budget": 1000.00
  }
}
```

##### Ad Approved
```json
{
  "event": "ad.approved",
  "timestamp": "2025-12-06T10:05:00Z",
  "data": {
    "ad_id": "ad-789",
    "campaign_id": "123e4567-e89b-12d3-a456-426614174000",
    "approved_by": "user-123"
  }
}
```

---

## External API Integrations

### Meta Marketing API

Production-grade integration with Meta Marketing API v19.0 for campaign management.

#### Authentication
Requires Meta access token with `ads_management` permission.

#### Python SDK Usage

##### Create Campaign
```python
from services.titan_core.meta.marketing_api import RealMetaAdsManager, CampaignObjective

manager = RealMetaAdsManager(
    access_token="YOUR_ACCESS_TOKEN",
    ad_account_id="act_123456789"
)

campaign_id = manager.create_campaign(
    name="Summer Sale Campaign",
    objective=CampaignObjective.OUTCOME_SALES,
    daily_budget_cents=10000,  # $100.00
    status="PAUSED"
)
```

##### Create Ad Set with Targeting
```python
targeting = manager.build_targeting(
    countries=["US", "CA"],
    age_min=25,
    age_max=45,
    interests=[{"id": "6003139266461", "name": "Fitness"}],
    publisher_platforms=["facebook", "instagram"]
)

ad_set_id = manager.create_ad_set(
    campaign_id=campaign_id,
    name="Main Ad Set",
    daily_budget_cents=5000,
    targeting=targeting,
    optimization_goal="OFFSITE_CONVERSIONS"
)
```

##### Upload Video and Create Ad
```python
# Upload video
video_id = manager.upload_video(
    video_path="/path/to/video.mp4",
    title="Product Demo"
)

# Create creative
creative_id = manager.create_ad_creative(
    name="Video Creative",
    video_id=video_id,
    message="Check out our amazing product!",
    link="https://example.com/product",
    call_to_action_type="SHOP_NOW",
    page_id="your-facebook-page-id"
)

# Create ad
ad_id = manager.create_ad(
    ad_set_id=ad_set_id,
    creative_id=creative_id,
    name="Video Ad 1",
    status="PAUSED"
)
```

##### Get Campaign Insights
```python
insights = manager.get_campaign_insights(
    campaign_id=campaign_id,
    fields=["impressions", "clicks", "spend", "conversions"],
    date_preset="last_7d"
)
```

#### Rate Limits
- API calls: 200 per hour per user
- Automatic exponential backoff for rate limits (error codes 17, 613, 80004)
- Max retries: 3 attempts

---

### Meta Conversions API

Server-side event tracking for privacy-compliant conversion tracking (CAPI).

#### Authentication
Requires:
- Meta Pixel ID
- Access token
- Optional test event code (for debugging)

#### Python SDK Usage

##### Track Purchase
```python
from services.titan_core.meta.conversions_api import MetaCAPI, UserInfo

capi = MetaCAPI(
    pixel_id="123456789",
    access_token="YOUR_ACCESS_TOKEN",
    test_event_code="TEST12345"  # Optional
)

user = UserInfo(
    email="user@example.com",
    phone="+1234567890",
    first_name="John",
    last_name="Doe",
    city="New York",
    state="NY",
    zip_code="10001",
    country="US",
    client_ip_address="1.2.3.4",
    client_user_agent="Mozilla/5.0...",
    fbc="fb.1.123456789.abcdef",
    fbp="fb.1.123456789.123456"
)

response = capi.send_purchase_event(
    user=user,
    value=99.99,
    currency="USD",
    content_ids=["product-123"],
    order_id="order-456",
    event_id="unique-event-id"
)
```

##### Track Lead
```python
response = capi.send_lead_event(
    user=user,
    lead_id="lead-789",
    content_name="Contact Form",
    event_id="unique-event-id"
)
```

##### Batch Events
```python
events = [...]  # List of Event objects
response = capi.batch_events(events)  # Up to 1000 events
```

#### PII Hashing
All PII fields are automatically normalized and SHA256 hashed.

#### Deduplication
Use the same `event_id` for both pixel and CAPI to prevent double-counting.

---

### Runway Gen-3 API

AI video generation from text prompts or images.

#### Authentication
Requires `RUNWAY_API_KEY` environment variable.

#### Python SDK Usage

##### Generate Video from Text
```python
from services.titan_core.integrations.runway_gen3 import (
    RunwayGen3Client, GenerationRequest, VideoAspectRatio
)

client = RunwayGen3Client(api_key="YOUR_RUNWAY_API_KEY")

result = await client.generate_video(GenerationRequest(
    prompt="Professional product showcase with cinematic lighting",
    duration=5,
    aspect_ratio=VideoAspectRatio.PORTRAIT
))

if result.status == "completed":
    video_url = result.video_url
```

##### Generate Video from Image
```python
result = await client.generate_video(GenerationRequest(
    prompt="Product rotating with dramatic lighting",
    image_url="https://example.com/product.jpg",
    duration=5
))
```

##### Generate Product Shot
```python
result = await client.generate_product_shot(
    product_image="https://example.com/product.jpg",
    scene_description="luxury perfume bottle on marble surface"
)
```

#### Models
- `gen3a_turbo`: Fastest, best quality (recommended)
- `gen2`: Fallback option

#### Pricing
- Gen-3 Alpha: ~0.05 credits/second
- Gen-3 Alpha Turbo: ~0.04 credits/second

---

### ElevenLabs Voice API

Professional AI voiceovers and voice cloning.

#### Authentication
Requires `ELEVENLABS_API_KEY` environment variable.

#### Python SDK Usage

##### Generate Voiceover
```python
from services.titan_core.integrations.elevenlabs_voice import (
    ElevenLabsClient, VoiceOverRequest, VoiceModel, VoiceSettings
)

client = ElevenLabsClient(api_key="YOUR_ELEVENLABS_API_KEY")

result = await client.generate_voiceover(VoiceOverRequest(
    text="Transform your fitness journey today!",
    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel
    model=VoiceModel.ELEVEN_TURBO_V2,
    settings=VoiceSettings(
        stability=0.6,
        similarity_boost=0.8,
        style=0.7
    )
))

audio_data = result.audio_data
```

##### Generate Ad Voiceover
```python
result = await client.generate_ad_voiceover(
    script="Get 50% off your first month!",
    voice_type="energetic_female"
)
```

##### Voice Presets
- `adam`: Deep male voice
- `rachel`: Calm female voice
- `domi`: Young female, energetic
- `josh`: Deep male, American
- `elli`: Young female, American

##### Clone Voice
```python
voice_id = await client.clone_voice(
    name="Brand Voice",
    audio_files=[audio_sample_1, audio_sample_2],
    description="Our brand voice"
)
```

#### Pricing
Approximate: $0.00003 per character

---

## Real-Time APIs

### WebSocket
```
ws://localhost:8000/ws
```

Subscribe to real-time updates:
```json
{
  "action": "subscribe",
  "channels": ["campaigns", "conversions"]
}
```

---

## Error Handling

### Error Response Format
```json
{
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {...}
}
```

### HTTP Status Codes
- `200 OK`: Success
- `201 Created`: Resource created
- `202 Accepted`: Request accepted (async)
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Missing/invalid auth
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service down

---

## Support

For API support:
- Email: api-support@geminivideo.com
- Documentation: https://docs.geminivideo.com
- Status: https://status.geminivideo.com

---

**End of API Reference**
