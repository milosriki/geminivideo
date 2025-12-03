# API Reference

**Gemini Video Platform - Production API Documentation**
Version: 1.0.0
Last Updated: 2025-12-02

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Rate Limits](#rate-limits)
4. [Error Codes](#error-codes)
5. [Gateway API Endpoints](#gateway-api-endpoints)
6. [Drive Intel Endpoints](#drive-intel-endpoints)
7. [Video Agent Endpoints](#video-agent-endpoints)
8. [ML Service Endpoints](#ml-service-endpoints)
9. [Meta Publisher Endpoints](#meta-publisher-endpoints)
10. [Titan Core Endpoints](#titan-core-endpoints)
11. [WebSocket API](#websocket-api)
12. [Webhooks](#webhooks)

---

## Overview

The Gemini Video Platform provides a comprehensive REST API for AI-powered video ad creation, analysis, and optimization. All API endpoints follow RESTful conventions and return JSON responses.

### Base URLs

**Production:**
```
Gateway API:      https://gateway-api-xxxxx.run.app
Drive Intel:      https://drive-intel-xxxxx.run.app
Video Agent:      https://video-agent-xxxxx.run.app
ML Service:       https://ml-service-xxxxx.run.app
Meta Publisher:   https://meta-publisher-xxxxx.run.app
Titan Core:       https://titan-core-xxxxx.run.app
```

**Development:**
```
Gateway API:      http://localhost:8080
Drive Intel:      http://localhost:8081
Video Agent:      http://localhost:8082
ML Service:       http://localhost:8003
Meta Publisher:   http://localhost:8083
Titan Core:       http://localhost:8084
```

### API Versioning

Current API version: `v1` (implied in all endpoints)

---

## Authentication

### API Key Authentication

All requests must include an API key in the `X-API-Key` header:

```http
X-API-Key: your_api_key_here
```

### JWT Authentication (Coming Soon - Agent 2)

Firebase JWT tokens for user authentication:

```http
Authorization: Bearer <firebase_jwt_token>
```

### Obtaining an API Key

1. Sign in to the Gemini Video dashboard
2. Navigate to Settings > API Keys
3. Click "Generate New API Key"
4. Copy and securely store your API key

**Security Best Practices:**
- Never commit API keys to version control
- Use environment variables for API keys
- Rotate API keys every 90 days
- Use different keys for development and production

---

## Rate Limits

### Global Rate Limits

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|----------------|---------------|--------------|
| Free | 60 | 1,000 | 10,000 |
| Pro | 600 | 10,000 | 100,000 |
| Enterprise | Custom | Custom | Custom |

### Rate Limit Headers

All responses include rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1701475200
```

### Rate Limit Response

When rate limit is exceeded (HTTP 429):

```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMIT_EXCEEDED",
  "message": "You have exceeded the rate limit of 60 requests per minute",
  "retry_after": 30
}
```

### Service-Specific Limits

- **Upload Endpoints:** 10 requests/minute (large files)
- **Analysis Endpoints:** 30 requests/minute (compute-intensive)
- **Search Endpoints:** 100 requests/minute
- **Health Check:** Unlimited

---

## Error Codes

### Standard HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 202 | Accepted | Request accepted for processing |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Application Error Codes

```json
{
  "error": "VALIDATION_ERROR",
  "message": "Invalid video format",
  "details": {
    "field": "video_path",
    "expected": ".mp4, .mov, .avi",
    "received": ".wmv"
  }
}
```

**Common Error Codes:**

- `INVALID_API_KEY` - API key is missing or invalid
- `VALIDATION_ERROR` - Request validation failed
- `RESOURCE_NOT_FOUND` - Requested resource does not exist
- `QUOTA_EXCEEDED` - Account quota exceeded
- `PROCESSING_ERROR` - Error during video processing
- `UPLOAD_ERROR` - File upload failed
- `DATABASE_ERROR` - Database operation failed
- `EXTERNAL_API_ERROR` - Third-party API error (Meta, Gemini, etc.)

---

## Gateway API Endpoints

The Gateway API serves as the unified entry point to all services.

### Health Check

**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-02T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "drive_intel": "healthy",
    "video_agent": "healthy",
    "ml_service": "healthy"
  }
}
```

---

### Video Analysis

#### Analyze Video (Async)

**POST** `/api/analyze`

Queue a video for comprehensive AI analysis.

**Request Body:**
```json
{
  "path": "/path/to/video.mp4",
  "filename": "fitness_ad_v1.mp4",
  "size_bytes": 15728640,
  "duration_seconds": 30.5
}
```

**Response (202 Accepted):**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Video queued for analysis",
  "estimated_completion": "2025-12-02T10:35:00Z"
}
```

**Rate Limit:** 30 requests/minute

---

#### Get Analysis Status

**GET** `/api/analyze/{asset_id}/status`

Check the status of a video analysis job.

**Response:**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "started_at": "2025-12-02T10:30:00Z",
  "completed_at": "2025-12-02T10:34:23Z",
  "result": {
    "clips_detected": 8,
    "top_clip_score": 0.87,
    "predicted_ctr": 0.045,
    "predicted_band": "high"
  }
}
```

**Possible Status Values:**
- `queued` - Waiting to be processed
- `processing` - Currently being analyzed
- `completed` - Analysis complete
- `failed` - Analysis failed
- `cancelled` - Analysis cancelled by user

---

### Scoring

#### Score Storyboard

**POST** `/api/score/storyboard`

Get AI-powered scoring for a video storyboard.

**Request Body:**
```json
{
  "scenes": [
    {
      "clip_id": "clip_001",
      "start_time": 0,
      "end_time": 3,
      "hook_text": "Are you tired of slow results?",
      "visuals": "trainer_closeup"
    },
    {
      "clip_id": "clip_002",
      "start_time": 3,
      "end_time": 8,
      "hook_text": "Transform in 30 days",
      "visuals": "before_after_split"
    }
  ],
  "metadata": {
    "target_audience": "fitness_beginners",
    "platform": "instagram_reels",
    "objective": "conversions"
  }
}
```

**Response (200 OK):**
```json
{
  "prediction_id": "pred_123abc",
  "composite_score": 0.782,
  "predicted_ctr": 0.048,
  "predicted_band": "high",
  "confidence": 0.89,
  "breakdown": {
    "psychology_score": 0.85,
    "hook_strength": 0.78,
    "technical_score": 0.72,
    "demographic_match": 0.88,
    "novelty_score": 0.65
  },
  "recommendations": [
    "Add social proof in first 5 seconds",
    "Increase motion in opening scene",
    "Consider adding numbers to hook"
  ]
}
```

---

#### Score Single Clip

**POST** `/api/score/clip`

Score an individual video clip.

**Request Body:**
```json
{
  "clip_id": "clip_001",
  "duration": 5.2,
  "transcript": "Are you tired of slow results? Here's the secret...",
  "features": {
    "has_face": true,
    "motion_score": 0.72,
    "text_overlay": "3 simple steps",
    "audio_quality": 0.88
  }
}
```

**Response:**
```json
{
  "clip_id": "clip_001",
  "score": 0.81,
  "breakdown": {
    "hook_analysis": {
      "primary_hook": "curiosity_gap",
      "hook_strength": 0.78,
      "secondary_hooks": ["question", "negative_hook"]
    },
    "visual_patterns": {
      "dominant_pattern": "face_closeup",
      "visual_energy": 0.72
    },
    "technical_quality": {
      "resolution_score": 0.95,
      "audio_quality": 0.88
    }
  }
}
```

---

### Assets & Clips

#### List Assets

**GET** `/api/assets`

Retrieve all analyzed video assets.

**Query Parameters:**
- `limit` (integer, default: 50) - Number of results
- `offset` (integer, default: 0) - Pagination offset
- `status` (string) - Filter by status: `queued`, `processing`, `completed`, `failed`
- `sort` (string) - Sort by: `created_at`, `score`, `name`
- `order` (string) - Sort order: `asc`, `desc`

**Example Request:**
```http
GET /api/assets?limit=20&status=completed&sort=score&order=desc
```

**Response:**
```json
{
  "total": 127,
  "limit": 20,
  "offset": 0,
  "assets": [
    {
      "asset_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "fitness_ad_v1.mp4",
      "status": "completed",
      "duration": 30.5,
      "clips_count": 8,
      "top_score": 0.87,
      "created_at": "2025-12-02T10:30:00Z",
      "analyzed_at": "2025-12-02T10:34:23Z"
    }
  ]
}
```

---

#### Get Asset Details

**GET** `/api/assets/{asset_id}`

Get detailed information about a specific asset.

**Response:**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "fitness_ad_v1.mp4",
  "path": "/uploads/fitness_ad_v1.mp4",
  "size_bytes": 15728640,
  "duration": 30.5,
  "resolution": "1080x1920",
  "fps": 30,
  "status": "completed",
  "clips": [
    {
      "clip_id": "clip_001",
      "start_time": 0,
      "end_time": 3.5,
      "score": 0.87,
      "hook_type": "curiosity_gap",
      "transcript": "Are you tired of slow results?"
    }
  ],
  "metadata": {
    "created_at": "2025-12-02T10:30:00Z",
    "analyzed_at": "2025-12-02T10:34:23Z",
    "file_hash": "a1b2c3d4e5f6..."
  }
}
```

---

#### Get Asset Clips (Ranked)

**GET** `/api/assets/{asset_id}/clips`

Get ranked clips for an asset.

**Query Parameters:**
- `ranked` (boolean, default: true) - Return clips sorted by score
- `top` (integer) - Return only top N clips
- `min_score` (float) - Filter clips with score >= value
- `hook_type` (string) - Filter by hook type

**Example Request:**
```http
GET /api/assets/550e8400/clips?ranked=true&top=5&min_score=0.7
```

**Response:**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_clips": 8,
  "filtered_clips": 5,
  "clips": [
    {
      "clip_id": "clip_003",
      "rank": 1,
      "score": 0.91,
      "start_time": 8.2,
      "end_time": 12.5,
      "duration": 4.3,
      "hook_type": "transformation",
      "thumbnail": "/thumbnails/clip_003.jpg",
      "confidence": 0.88
    }
  ]
}
```

---

### Semantic Search

#### Search Clips

**POST** `/api/search/clips`

Perform semantic search across all video clips.

**Request Body:**
```json
{
  "query": "person doing squats in gym",
  "top_k": 10,
  "filters": {
    "min_score": 0.5,
    "min_duration": 3.0,
    "max_duration": 10.0,
    "hook_types": ["action_motion", "tutorial_demo"]
  }
}
```

**Response:**
```json
{
  "query": "person doing squats in gym",
  "total_results": 47,
  "returned": 10,
  "results": [
    {
      "clip_id": "clip_089",
      "asset_id": "550e8400-e29b-41d4-a716-446655440000",
      "similarity_score": 0.94,
      "clip_score": 0.82,
      "start_time": 15.3,
      "end_time": 19.8,
      "transcript": "proper squat form demonstration",
      "thumbnail": "/thumbnails/clip_089.jpg"
    }
  ]
}
```

---

### Learning & Reliability

#### Log Prediction Outcome

**POST** `/api/learning/log-outcome`

Log actual performance results to improve predictions.

**Request Body:**
```json
{
  "prediction_id": "pred_123abc",
  "actual_ctr": 0.052,
  "actual_conversions": 127,
  "actual_roas": 3.2,
  "campaign_id": "camp_meta_001",
  "date_range": {
    "start": "2025-12-01",
    "end": "2025-12-07"
  }
}
```

**Response:**
```json
{
  "logged": true,
  "prediction_id": "pred_123abc",
  "accuracy": {
    "ctr_error": 0.004,
    "was_in_band": true,
    "confidence_validated": true
  },
  "message": "Outcome logged successfully"
}
```

---

#### Trigger Learning Update

**POST** `/api/learning/update`

Manually trigger the self-learning weight update.

**Request Body:**
```json
{
  "min_samples": 50,
  "force": false
}
```

**Response:**
```json
{
  "update_triggered": true,
  "samples_used": 127,
  "weight_changes": {
    "psychology_score": 0.02,
    "hook_strength": -0.01,
    "technical_score": 0.00
  },
  "new_accuracy": 0.94,
  "timestamp": "2025-12-02T10:45:00Z"
}
```

---

#### Get Reliability Metrics

**GET** `/api/reliability/metrics`

Retrieve prediction accuracy metrics.

**Query Parameters:**
- `date_from` (date) - Start date (YYYY-MM-DD)
- `date_to` (date) - End date (YYYY-MM-DD)
- `band` (string) - Filter by predicted band

**Response:**
```json
{
  "total_predictions": 342,
  "accuracy": {
    "overall": 0.94,
    "in_band": 0.89,
    "by_band": {
      "viral": 0.87,
      "high": 0.92,
      "mid": 0.95,
      "low": 0.93
    }
  },
  "calibration": {
    "mean_error": 0.003,
    "rmse": 0.008,
    "r_squared": 0.88
  }
}
```

---

## Drive Intel Endpoints

Video ingestion, scene detection, and feature extraction.

### Ingest Videos

#### Ingest Local Folder

**POST** `/ingest/local/folder`

Ingest videos from a local folder.

**Request Body:**
```json
{
  "folder_path": "/data/videos/campaign_001",
  "recursive": true,
  "skip_existing": true,
  "auto_analyze": true
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "ingest_001",
  "status": "queued",
  "folder_path": "/data/videos/campaign_001",
  "estimated_files": 23,
  "message": "Ingestion job queued"
}
```

---

#### Ingest from Google Drive

**POST** `/ingest/drive/folder`

Ingest videos from a Google Drive folder.

**Request Body:**
```json
{
  "folder_id": "1a2b3c4d5e6f7g8h9i0j",
  "credentials": {
    "type": "service_account",
    "client_email": "service@project.iam.gserviceaccount.com",
    "private_key": "-----BEGIN PRIVATE KEY-----\n..."
  },
  "auto_analyze": true
}
```

**Response:**
```json
{
  "job_id": "drive_ingest_001",
  "status": "queued",
  "folder_id": "1a2b3c4d5e6f7g8h9i0j",
  "files_found": 15,
  "message": "Google Drive ingestion started"
}
```

---

### Scene Detection

#### Detect Scenes

**POST** `/scenes/detect`

Detect scenes in a video using AI.

**Request Body:**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "sensitivity": "medium",
  "min_scene_duration": 1.0
}
```

**Response:**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_scenes": 12,
  "scenes": [
    {
      "scene_id": "scene_001",
      "start_time": 0.0,
      "end_time": 3.2,
      "duration": 3.2,
      "shot_type": "close_up",
      "motion_score": 0.65,
      "dominant_objects": ["person", "text_overlay"],
      "thumbnail": "/thumbnails/scene_001.jpg"
    }
  ]
}
```

---

## Video Agent Endpoints

Video rendering, remixing, and compliance checking.

### Render Jobs

#### Create Render Job

**POST** `/render/remix`

Create a video remix render job.

**Request Body:**
```json
{
  "scenes": [
    {
      "asset_id": "550e8400-e29b-41d4-a716-446655440000",
      "clip_id": "clip_001",
      "start_time": 0,
      "end_time": 3.5
    },
    {
      "asset_id": "660f9511-f3ac-52e5-b827-557766551111",
      "clip_id": "clip_042",
      "start_time": 5.2,
      "end_time": 9.8
    }
  ],
  "variant": "reels",
  "config": {
    "resolution": "1080x1920",
    "fps": 30,
    "add_subtitles": true,
    "overlay_template": "hook_001",
    "background_music": "motivational_001",
    "volume": 0.7
  }
}
```

**Response (202 Accepted):**
```json
{
  "job_id": "render_001",
  "status": "queued",
  "estimated_duration": 45,
  "position_in_queue": 3,
  "message": "Render job queued successfully"
}
```

---

#### Get Render Job Status

**GET** `/render/{job_id}/status`

Check render job progress.

**Response:**
```json
{
  "job_id": "render_001",
  "status": "rendering",
  "progress": 67,
  "stage": "encoding",
  "started_at": "2025-12-02T11:00:00Z",
  "estimated_completion": "2025-12-02T11:03:00Z",
  "output_url": null
}
```

---

#### Download Rendered Video

**GET** `/render/{job_id}/download`

Download the completed render.

**Response:**
```
Content-Type: video/mp4
Content-Disposition: attachment; filename="remix_render_001.mp4"

<binary video data>
```

---

### Compliance Checking

#### Check Video Compliance

**POST** `/compliance/check`

Check video against platform compliance rules.

**Request Body:**
```json
{
  "video_path": "/renders/output_001.mp4",
  "platform": "meta",
  "ad_type": "feed"
}
```

**Response:**
```json
{
  "compliant": true,
  "platform": "meta",
  "checks": {
    "duration": {
      "passed": true,
      "value": 15.2,
      "requirement": "5-60 seconds"
    },
    "aspect_ratio": {
      "passed": true,
      "value": "9:16",
      "requirement": "4:5, 1:1, 9:16"
    },
    "file_size": {
      "passed": true,
      "value": 12.5,
      "requirement": "< 100 MB"
    },
    "text_overlay": {
      "passed": true,
      "value": 18,
      "requirement": "< 20% of frame"
    }
  },
  "issues": []
}
```

---

## ML Service Endpoints

Machine learning predictions and A/B testing.

### CTR Prediction

#### Predict CTR

**POST** `/predict/ctr`

Predict click-through rate using ML models.

**Request Body:**
```json
{
  "features": {
    "psychology_score": 0.85,
    "hook_strength": 0.78,
    "visual_energy": 0.72,
    "has_face": true,
    "duration": 15.5,
    "platform": "instagram_reels"
  }
}
```

**Response:**
```json
{
  "predicted_ctr": 0.048,
  "predicted_band": "high",
  "confidence": 0.89,
  "model": "xgboost_enhanced_v2",
  "feature_importance": {
    "hook_strength": 0.28,
    "psychology_score": 0.24,
    "visual_energy": 0.18
  }
}
```

---

### Thompson Sampling

#### Create Experiment

**POST** `/experiment/create`

Create an A/B test experiment.

**Request Body:**
```json
{
  "name": "Hook Type Test - December 2025",
  "variants": [
    {
      "variant_id": "curiosity",
      "name": "Curiosity Gap Hook",
      "asset_id": "550e8400-e29b-41d4-a716-446655440000"
    },
    {
      "variant_id": "transformation",
      "name": "Transformation Hook",
      "asset_id": "660f9511-f3ac-52e5-b827-557766551111"
    }
  ],
  "budget": 500,
  "optimization_metric": "conversions"
}
```

**Response:**
```json
{
  "experiment_id": "exp_001",
  "status": "active",
  "variants": 2,
  "initial_allocation": {
    "curiosity": 0.5,
    "transformation": 0.5
  }
}
```

---

#### Get Budget Allocation

**GET** `/experiment/{experiment_id}/allocation`

Get Thompson Sampling budget recommendations.

**Response:**
```json
{
  "experiment_id": "exp_001",
  "total_budget": 500,
  "spent": 127.50,
  "remaining": 372.50,
  "allocation": {
    "curiosity": {
      "probability": 0.34,
      "budget": 126.65,
      "conversions": 23,
      "cost_per_conversion": 2.45
    },
    "transformation": {
      "probability": 0.66,
      "budget": 245.85,
      "conversions": 58,
      "cost_per_conversion": 1.89
    }
  },
  "recommendation": "Shift 66% of remaining budget to 'transformation' variant"
}
```

---

## Meta Publisher Endpoints

Meta Ads platform integration.

### Campaign Management

#### Create Campaign

**POST** `/meta/campaigns/create`

Create a new Meta Ads campaign.

**Request Body:**
```json
{
  "name": "Fitness Q4 2025 - Transformation",
  "objective": "OUTCOME_ENGAGEMENT",
  "status": "PAUSED",
  "special_ad_categories": ["NONE"],
  "budget": {
    "daily_budget": 50,
    "lifetime_budget": null
  },
  "targeting": {
    "age_min": 25,
    "age_max": 45,
    "genders": [1, 2],
    "geo_locations": {
      "countries": ["US"]
    },
    "interests": ["fitness", "health"]
  }
}
```

**Response:**
```json
{
  "campaign_id": "120210387319050719",
  "name": "Fitness Q4 2025 - Transformation",
  "status": "PAUSED",
  "created_at": "2025-12-02T11:30:00Z"
}
```

---

#### Upload Video Creative

**POST** `/meta/creative/upload`

Upload video to Meta for ad creative.

**Request Body (multipart/form-data):**
```
video: <file>
name: "Transformation Hook v1"
description: "15s transformation story"
```

**Response:**
```json
{
  "video_id": "1234567890123456",
  "status": "ready",
  "thumbnail": "https://scontent.xx.fbcdn.net/...",
  "url": "https://video.xx.fbcdn.net/..."
}
```

---

#### Get Campaign Insights

**GET** `/meta/campaigns/{campaign_id}/insights`

Retrieve campaign performance data.

**Query Parameters:**
- `date_preset` - Date range: `today`, `last_7d`, `last_30d`, `lifetime`
- `fields` - Comma-separated metrics

**Response:**
```json
{
  "campaign_id": "120210387319050719",
  "date_range": {
    "start": "2025-11-25",
    "end": "2025-12-02"
  },
  "insights": {
    "impressions": 45678,
    "reach": 32145,
    "clicks": 2134,
    "ctr": 0.047,
    "spend": 342.50,
    "conversions": 89,
    "cost_per_conversion": 3.85,
    "roas": 3.2
  }
}
```

---

## Titan Core Endpoints

Advanced AI orchestration and Council of Titans.

### Council Scoring

#### Get Council Verdict

**POST** `/titan/council/score`

Get consensus scoring from all 4 Titan models.

**Request Body:**
```json
{
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "clip_id": "clip_001",
  "context": {
    "target_audience": "fitness_beginners",
    "objective": "conversions"
  }
}
```

**Response:**
```json
{
  "council_verdict": {
    "consensus_score": 0.84,
    "confidence": 0.91,
    "recommendation": "APPROVE"
  },
  "individual_titans": {
    "gemini": {
      "score": 0.87,
      "reasoning": "Strong curiosity hook with clear transformation promise"
    },
    "claude": {
      "score": 0.82,
      "reasoning": "Effective pattern interrupt, could strengthen social proof"
    },
    "gpt4": {
      "score": 0.85,
      "reasoning": "High engagement potential, well-structured narrative"
    },
    "video_intelligence": {
      "score": 0.83,
      "reasoning": "Good visual composition, motion holds attention"
    }
  },
  "actionable_insights": [
    "Add testimonial in seconds 5-8",
    "Increase text size for mobile viewing",
    "Consider faster cuts in opening 3 seconds"
  ]
}
```

---

## WebSocket API

Real-time updates for long-running operations.

### Connection

```javascript
const ws = new WebSocket('wss://gateway-api-xxxxx.run.app/ws');

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['render_jobs', 'analysis_jobs']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

### Events

**Render Progress:**
```json
{
  "type": "render_progress",
  "job_id": "render_001",
  "progress": 75,
  "stage": "encoding",
  "eta_seconds": 15
}
```

**Analysis Complete:**
```json
{
  "type": "analysis_complete",
  "asset_id": "550e8400-e29b-41d4-a716-446655440000",
  "clips_detected": 8,
  "top_score": 0.87
}
```

---

## Webhooks

Configure webhooks to receive event notifications.

### Setup Webhook

**POST** `/api/webhooks/create`

```json
{
  "url": "https://your-domain.com/webhooks/geminivideo",
  "events": ["analysis.completed", "render.completed", "experiment.winner"],
  "secret": "your_webhook_secret"
}
```

### Webhook Payload

```json
{
  "event": "analysis.completed",
  "timestamp": "2025-12-02T11:45:00Z",
  "data": {
    "asset_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "clips_detected": 8
  },
  "signature": "sha256=a1b2c3d4e5f6..."
}
```

### Verify Signature

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## SDK Examples

### Python

```python
import requests

class GeminiVideoClient:
    def __init__(self, api_key, base_url="https://gateway-api-xxxxx.run.app"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def analyze_video(self, video_path, filename):
        response = requests.post(
            f"{self.base_url}/api/analyze",
            headers=self.headers,
            json={
                "path": video_path,
                "filename": filename
            }
        )
        return response.json()

    def get_analysis_status(self, asset_id):
        response = requests.get(
            f"{self.base_url}/api/analyze/{asset_id}/status",
            headers=self.headers
        )
        return response.json()

# Usage
client = GeminiVideoClient("your_api_key")
result = client.analyze_video("/videos/ad.mp4", "ad.mp4")
print(result)
```

### JavaScript/TypeScript

```typescript
class GeminiVideoClient {
  constructor(
    private apiKey: string,
    private baseUrl = "https://gateway-api-xxxxx.run.app"
  ) {}

  async analyzeVideo(path: string, filename: string) {
    const response = await fetch(`${this.baseUrl}/api/analyze`, {
      method: "POST",
      headers: {
        "X-API-Key": this.apiKey,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ path, filename })
    });
    return response.json();
  }

  async getAnalysisStatus(assetId: string) {
    const response = await fetch(
      `${this.baseUrl}/api/analyze/${assetId}/status`,
      {
        headers: { "X-API-Key": this.apiKey }
      }
    );
    return response.json();
  }
}

// Usage
const client = new GeminiVideoClient("your_api_key");
const result = await client.analyzeVideo("/videos/ad.mp4", "ad.mp4");
console.log(result);
```

---

## Best Practices

1. **Use Async Endpoints** - For video processing, always use async endpoints and poll for status
2. **Handle Rate Limits** - Implement exponential backoff when rate limited
3. **Validate Inputs** - Always validate request data before sending
4. **Secure API Keys** - Never expose API keys in client-side code
5. **Cache Responses** - Cache GET requests when appropriate
6. **Use Webhooks** - For long-running operations, use webhooks instead of polling
7. **Error Handling** - Implement robust error handling for all API calls
8. **Versioning** - Pin to specific API versions in production

---

## Support

- **Documentation:** https://docs.geminivideo.com
- **API Status:** https://status.geminivideo.com
- **GitHub Issues:** https://github.com/milosriki/geminivideo/issues
- **Email:** support@geminivideo.com

---

*Last Updated: 2025-12-02*
