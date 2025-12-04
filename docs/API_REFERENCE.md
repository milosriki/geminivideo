# Titan Engine API Reference

This document provides a comprehensive reference for the Titan Engine microservices API.

## 🔐 Authentication & Security

All internal service-to-service communication is secured via VPC or authenticated via Service Account tokens in production.
External access to the **Gateway API** requires an API Key or Bearer Token.

- **Header**: `Authorization: Bearer <token>`
- **Header**: `X-API-Key: <api-key>` (for specific endpoints)

## 🚦 Rate Limiting

Global rate limits are enforced at the Gateway level:
- **Public API**: 60 requests/minute per IP
- **Authenticated API**: 1000 requests/minute per tenant
- **Uploads**: 10 concurrent uploads per user

---

## 1. Gateway API
**Base URL**: `http://localhost:8000` (Local) / `https://ptd-fitness-backend-*.run.app` (Cloud)

The Gateway API is the single entry point for the frontend and external clients. It routes requests to the appropriate microservices.

### Health Check
- **GET** `/health`
- **Response**: `{"status": "ok", "version": "1.0.0"}`

### Knowledge Management
- **POST** `/knowledge/upload`
    - **Description**: Upload a new knowledge base document (PDF, TXT).
    - **Body**: Multipart form data (`file`).
    - **Response**: `{"id": "kb_123", "status": "processing"}`
- **POST** `/knowledge/activate`
    - **Description**: Set a specific knowledge base version as active.
    - **Body**: `{"version_id": "v2"}`

### Scoring
- **POST** `/score/clip`
    - **Description**: Score a video clip for hook strength, psychology, and novelty.
    - **Body**:
      ```json
      {
        "clip_id": "clip_123",
        "metadata": { "duration": 15, "transcript": "..." }
      }
      ```
    - **Response**:
      ```json
      {
        "scores": { "hook": 0.85, "psychology": 0.92, "novelty": 0.78 },
        "overall_score": 0.85
      }
      ```

---

## 2. Drive Intel Service
**Base URL**: `http://localhost:8001`

Handles asset ingestion, storage, and retrieval from Google Drive and Cloud Storage.

### Assets
- **GET** `/assets`
    - **Query**: `limit=10&skip=0&type=video`
    - **Response**: List of assets.
- **GET** `/assets/{asset_id}`
    - **Response**: Asset details.
- **POST** `/assets/ingest`
    - **Description**: Trigger ingestion from a Google Drive folder.
    - **Body**: `{"folder_id": "1A2B3C...", "recursive": true}`

### Search
- **POST** `/search/semantic`
    - **Description**: Search for assets using natural language.
    - **Body**: `{"query": "happy people running", "top_k": 10}`
    - **Response**: List of matching assets with similarity scores.

---

## 3. Video Agent Service
**Base URL**: `http://localhost:8002`

Responsible for deep video analysis, scene detection, and transcription using Gemini 1.5 Pro.

### Analysis
- **POST** `/analyze/video`
    - **Body**: `{"gcs_uri": "gs://bucket/video.mp4"}`
    - **Response**: `{"job_id": "job_123"}` (Async)
- **GET** `/analyze/status/{job_id}`
    - **Response**: `{"status": "completed", "result": { ... }}`

### Scene Detection
- **POST** `/scenes/detect`
    - **Body**: `{"video_id": "vid_123"}`
    - **Response**: List of detected scenes with timestamps.

---

## 4. ML Service
**Base URL**: `http://localhost:8003`

Provides predictive models for CTR, ROAS, and creative scoring.

### Predictions
- **POST** `/predict/ctr`
    - **Body**: `{"features": { "hook_score": 0.8, "duration": 15, ... }}`
    - **Response**: `{"predicted_ctr": 1.25, "confidence": 0.9}`
- **POST** `/predict/roas`
    - **Body**: `{"campaign_id": "camp_123", "spend": 100}`
    - **Response**: `{"predicted_roas": 2.4, "recommendation": "scale"}`

### Self-Learning
- **POST** `/learning/feedback`
    - **Description**: Submit actual performance data to retrain models.
    - **Body**: `{"prediction_id": "pred_123", "actual_value": 1.5}`

---

## 5. Meta Publisher Service
**Base URL**: `http://localhost:8083`

Manages interaction with the Meta Marketing API for publishing ads and retrieving insights.

### Publishing
- **POST** `/ads/publish`
    - **Body**:
      ```json
      {
        "campaign_id": "camp_123",
        "creative_id": "creat_456",
        "ad_set_config": { ... }
      }
      ```
    - **Response**: `{"platform_ad_id": "1234567890"}`

### Insights
- **GET** `/insights/campaign/{campaign_id}`
    - **Query**: `date_preset=last_7d`
    - **Response**: `{"spend": 500, "impressions": 10000, "clicks": 200, "roas": 2.1}`

---

## 6. Titan Core
**Base URL**: `http://localhost:8004`

The orchestration engine that manages workflows, rendering, and campaign generation.

### Rendering
- **POST** `/render/start`
    - **Description**: Start a video rendering job (remixing scenes).
    - **Body**:
      ```json
      {
        "scenes": ["scene_1", "scene_2"],
        "audio_track": "audio_1",
        "overlays": [{ "text": "Buy Now", "time": 0 }]
      }
      ```
    - **Response**: `{"job_id": "render_123"}`

### Pipeline
- **POST** `/pipeline/generate-campaign`
    - **Description**: End-to-end generation of a campaign from a product URL or description.
    - **Body**: `{"product_url": "https://example.com/product"}`
    - **Response**: `{"campaign_id": "camp_new_123", "status": "generating"}`

---

## Error Codes

| Code | Description |
| :--- | :--- |
| `400` | Bad Request - Invalid input parameters |
| `401` | Unauthorized - Missing or invalid API key |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource does not exist |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error - Something went wrong on the server |

