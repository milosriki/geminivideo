# Architecture Documentation

**Gemini Video Platform - System Architecture**
Version: 1.0.0
Last Updated: 2025-12-02

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Microservices](#microservices)
4. [Data Flow](#data-flow)
5. [ML Pipeline](#ml-pipeline)
6. [Infrastructure Components](#infrastructure-components)
7. [Security Architecture](#security-architecture)
8. [Scalability & Performance](#scalability--performance)

---

## System Overview

Gemini Video is a cloud-native, microservices-based platform for AI-powered video ad creation and optimization. The architecture is designed for:

- **Scalability:** Handle thousands of concurrent video analyses
- **Reliability:** 99.9% uptime SLA with fault tolerance
- **Performance:** Sub-5-minute video analysis, real-time predictions
- **Security:** OWASP best practices, encryption at rest and in transit
- **Extensibility:** Plugin architecture for new AI models and integrations

### Technology Stack

**Backend Services:**
- Python 3.11+ (FastAPI, Uvicorn)
- Node.js 20+ (Express, TypeScript)
- PostgreSQL 15 (primary database)
- Redis 7 (caching, queues, session management)

**ML & AI:**
- Google Gemini 2.0 (video analysis, generation)
- Anthropic Claude (reasoning, analysis)
- OpenAI GPT-4 (text analysis)
- YOLOv8 (object detection)
- PaddleOCR (text extraction)
- Sentence Transformers (embeddings)
- XGBoost (CTR prediction)
- FFmpeg (video processing)

**Frontend:**
- React 18 (UI framework)
- Vite (build tool)
- TypeScript (type safety)
- FFmpeg.wasm (client-side video processing)
- TailwindCSS (styling)

**Infrastructure:**
- Google Cloud Platform (primary cloud)
- Docker & Docker Compose (containerization)
- Cloud Run (serverless deployment)
- Cloud Storage (GCS) for video storage
- Cloud SQL (managed PostgreSQL)
- Cloud Memorystore (managed Redis)
- Artifact Registry (Docker images)

---

## Architecture Diagram

### High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         GEMINI VIDEO PLATFORM                         │
└──────────────────────────────────────────────────────────────────────┘

                              ┌─────────────┐
                              │   USER      │
                              └──────┬──────┘
                                     │
                          ┌──────────▼──────────┐
                          │   FRONTEND (React)   │
                          │   Port: 80/443       │
                          └──────────┬───────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  GATEWAY API (Node)  │
                          │  Port: 8080          │
                          │  • Routing           │
                          │  • Auth              │
                          │  • Rate Limiting     │
                          └─┬──┬──┬──┬──┬──┬────┘
                            │  │  │  │  │  │
        ┌───────────────────┘  │  │  │  │  └───────────────────┐
        │                      │  │  │  │                      │
┌───────▼────────┐    ┌───────▼──▼──▼──▼────────┐    ┌───────▼────────┐
│  DRIVE INTEL   │    │    VIDEO AGENT          │    │  TITAN CORE    │
│  (Python)      │    │    (Python)             │    │  (Python)      │
│  Port: 8081    │    │    Port: 8082           │    │  Port: 8084    │
│                │    │                         │    │                │
│  • Ingestion   │    │  • Video Rendering      │    │  • Council     │
│  • Scene Det.  │    │  • Compliance Check     │    │  • Gemini API  │
│  • Feature Ext.│    │  • FFmpeg Pipeline      │    │  • Claude API  │
│  • FAISS Search│    │  • Subtitle Gen         │    │  • GPT-4 API   │
└────────┬───────┘    └─────────────────────────┘    └────────┬───────┘
         │                                                     │
         │            ┌─────────────────────────┐             │
         └────────────►   ML SERVICE (Python)   ◄─────────────┘
                      │   Port: 8003            │
                      │                         │
                      │   • CTR Prediction      │
                      │   • XGBoost Models      │
                      │   • Thompson Sampling   │
                      │   • Feature Engineering │
                      └────────┬────────────────┘
                               │
         ┌─────────────────────┴─────────────────────┐
         │                                           │
┌────────▼─────────┐                      ┌─────────▼──────────┐
│  META PUBLISHER  │                      │  SHARED SERVICES   │
│  (Node)          │                      │                    │
│  Port: 8083      │                      │  • PostgreSQL      │
│                  │                      │  • Redis           │
│  • Campaign Mgmt │                      │  • GCS Storage     │
│  • Ad Upload     │                      │  • Config Mgmt     │
│  • Insights      │                      │  • Logging         │
└──────────────────┘                      └────────────────────┘
```

---

### Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         VIDEO ANALYSIS FLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. INGESTION
   User Upload → Gateway API → Drive Intel
                              ↓
                         [Save to GCS]
                              ↓
                      [Queue Redis Job]

2. SCENE DETECTION
   Worker → FFmpeg → Scene Detection → Clip Extraction
          ↓
      [Save Clips]

3. FEATURE EXTRACTION
   For Each Clip:
     → YOLOv8 (objects)
     → PaddleOCR (text)
     → Whisper (audio transcription)
     → Visual CNN (patterns)
     → Sentence Transformer (embeddings)
          ↓
      [Store Features in PostgreSQL]
          ↓
      [Index in FAISS]

4. SCORING
   Features → ML Service → XGBoost Model
                        ↓
                  CTR Prediction
                        ↓
            [Save to predictions table]

5. TITAN COUNCIL
   Clip + Features → Titan Core
                   ↓
        [Gemini, Claude, GPT-4, Video Intelligence]
                   ↓
            Consensus Score
                   ↓
         [Store Final Score]

6. RESPONSE
   Results → Gateway API → Frontend
```

---

### Request Flow (Campaign Creation)

```
┌──────────────────────────────────────────────────────────────┐
│                    CAMPAIGN CREATION FLOW                     │
└──────────────────────────────────────────────────────────────┘

Frontend: User creates campaign
    ↓
Gateway API: Validate input, check auth
    ↓
    ├─→ Drive Intel: Get video analysis
    │       ↓
    │   Return clips + scores
    │
    ├─→ ML Service: Predict CTR
    │       ↓
    │   Return prediction
    │
    ├─→ Titan Core: Get council verdict
    │       ↓
    │   Return recommendations
    │
    └─→ Aggregate results
         ↓
Gateway API: Store campaign in database
    ↓
Meta Publisher: Create Meta campaign
    ↓
    ├─→ Upload video to Meta
    ├─→ Create ad set
    ├─→ Create ad
    └─→ Submit for review
         ↓
Return campaign_id + status to frontend
```

---

## Microservices

### 1. Gateway API

**Technology:** Node.js + Express + TypeScript
**Port:** 8080
**Responsibilities:**
- Unified API gateway for all services
- Authentication & authorization
- Rate limiting & security middleware
- Request routing
- Response aggregation
- Scoring engine coordination
- Reliability logging

**Key Endpoints:**
- `POST /api/analyze` - Queue video analysis
- `POST /api/score/storyboard` - Score ad storyboard
- `GET /api/assets` - List analyzed videos
- `POST /api/search/clips` - Semantic search

**Dependencies:**
- PostgreSQL (predictions, reliability metrics)
- Redis (caching, rate limiting)
- All other microservices (routing)

**Scaling:** Horizontal scaling via Cloud Run (1-10 instances)

---

### 2. Drive Intel

**Technology:** Python + FastAPI
**Port:** 8081
**Responsibilities:**
- Video ingestion (local, Google Drive)
- Scene detection & segmentation
- Feature extraction (visual, audio, text)
- Semantic search (FAISS)
- Clip ranking

**ML Models:**
- YOLOv8n (object detection)
- PaddleOCR (text extraction)
- Sentence Transformers (embeddings)
- Whisper (transcription)
- Visual Pattern CNN (ResNet-50 based)

**Key Endpoints:**
- `POST /ingest/local/folder` - Ingest from filesystem
- `POST /ingest/drive/folder` - Ingest from Google Drive
- `GET /assets/{id}/clips` - Get ranked clips
- `POST /search/clips` - Semantic search

**Resource Requirements:**
- CPU: 2-4 cores
- RAM: 4-8 GB
- GPU: Optional (speeds up YOLOv8, CNN)
- Storage: GCS for videos

**Scaling:** Vertical scaling (larger instances for GPU), background workers for async processing

---

### 3. Video Agent

**Technology:** Python + FastAPI
**Port:** 8082
**Responsibilities:**
- Video rendering & remixing
- Multi-clip composition
- Subtitle generation
- Overlay application
- Compliance checking
- FFmpeg operations

**Key Features:**
- 11 advanced editing operations
- Template-based rendering
- Real-time preview generation
- Platform compliance validation (Meta, TikTok, YouTube)

**Key Endpoints:**
- `POST /render/remix` - Create render job
- `GET /render/{job_id}/status` - Check render status
- `GET /render/{job_id}/download` - Download result
- `POST /compliance/check` - Validate compliance

**Resource Requirements:**
- CPU: 4 cores (FFmpeg encoding)
- RAM: 4 GB
- Storage: Temp storage for rendering

**Scaling:** Horizontal scaling with worker pool (2-10 workers)

---

### 4. ML Service

**Technology:** Python + FastAPI
**Port:** 8003
**Responsibilities:**
- CTR prediction (XGBoost)
- Feature engineering
- Thompson Sampling (A/B testing)
- Model training & retraining
- Creative attribution

**ML Models:**
- XGBoost Regressor (CTR prediction)
- Thompson Sampling (multi-armed bandit)
- Feature importance analysis

**Key Endpoints:**
- `POST /predict/ctr` - Predict click-through rate
- `POST /experiment/create` - Create A/B test
- `GET /experiment/{id}/allocation` - Get budget allocation
- `POST /learning/update` - Trigger model retraining

**Resource Requirements:**
- CPU: 2-4 cores
- RAM: 8-16 GB (model loading)
- Storage: Model persistence

**Scaling:** Vertical scaling for model training, horizontal for inference

---

### 5. Meta Publisher

**Technology:** Node.js + Express
**Port:** 8083
**Responsibilities:**
- Meta Marketing API integration
- Campaign creation & management
- Video upload to Meta
- Insights retrieval
- Conversion tracking (CAPI)

**External APIs:**
- Meta Marketing API v19.0
- Meta Conversions API (CAPI)
- Meta Ads Library API

**Key Endpoints:**
- `POST /meta/campaigns/create` - Create campaign
- `POST /meta/creative/upload` - Upload video
- `GET /meta/campaigns/{id}/insights` - Get performance
- `POST /meta/conversions/track` - Track conversion

**Resource Requirements:**
- CPU: 1 core
- RAM: 1 GB
- Network: High throughput for video uploads

**Scaling:** Horizontal scaling (1-5 instances)

---

### 6. Titan Core

**Technology:** Python + FastAPI
**Port:** 8084
**Responsibilities:**
- AI orchestration (Council of Titans)
- Gemini API integration
- Claude API integration
- GPT-4 API integration
- Deep video intelligence
- Knowledge base management

**Council of Titans:**
```
Input: Video clip + context
    ↓
┌─────────────────────────────┐
│  Parallel AI Analysis:      │
│  • Gemini 2.0 Flash        │
│  • Claude Sonnet           │
│  • GPT-4 Turbo             │
│  • Video Intelligence       │
└─────────────────────────────┘
    ↓
Consensus Algorithm:
  - Weighted average
  - Confidence scoring
  - Outlier detection
    ↓
Final Score + Recommendations
```

**Key Endpoints:**
- `POST /titan/council/score` - Get council verdict
- `POST /titan/analyze/video` - Deep video analysis
- `GET /titan/knowledge/status` - Knowledge base status

**Resource Requirements:**
- CPU: 2 cores
- RAM: 2 GB
- Network: API calls to external AI services

**Scaling:** Horizontal scaling with API quota management

---

## Data Flow

### Video Analysis Pipeline

```
┌────────────────────────────────────────────────────────────┐
│                  VIDEO ANALYSIS PIPELINE                    │
└────────────────────────────────────────────────────────────┘

STAGE 1: INGESTION (5-10 seconds)
────────────────────────────────────
Upload → Validation → GCS Storage → Database Entry → Queue Job

STAGE 2: SCENE DETECTION (10-30 seconds)
────────────────────────────────────
FFmpeg → Shot Detection → Scene Boundaries → Clip Extraction
    ↓
Output: N clips (typically 4-12)

STAGE 3: FEATURE EXTRACTION (30-90 seconds per clip)
────────────────────────────────────
Parallel Processing:

Thread 1: Visual Analysis
  → YOLOv8 (objects)
  → Visual CNN (patterns)
  → Face detection
  → Motion analysis

Thread 2: Text Extraction
  → PaddleOCR (text in frames)
  → Text overlay detection
  → Text coverage calculation

Thread 3: Audio Analysis
  → Whisper (transcription)
  → Audio quality metrics
  → Speech emotion detection

Thread 4: Embedding Generation
  → Sentence Transformer (semantic embeddings)
  → FAISS indexing

STAGE 4: SCORING (5-10 seconds)
────────────────────────────────────
Features → ML Service
           ↓
    XGBoost Prediction
           ↓
    Psychology Scoring
           ↓
    Hook Classification
           ↓
    Composite Score

STAGE 5: COUNCIL VERIFICATION (10-20 seconds)
────────────────────────────────────
Top Clips → Titan Core
            ↓
    4 AI Models (parallel)
            ↓
    Consensus Algorithm
            ↓
    Final Score + Insights

STAGE 6: PERSISTENCE (2-5 seconds)
────────────────────────────────────
Save Results → PostgreSQL
Update FAISS Index
Trigger Webhooks
Notify User

TOTAL PIPELINE TIME: 2-5 minutes per video
```

---

### Campaign Creation Data Flow

```
┌────────────────────────────────────────────────────────────┐
│                 CAMPAIGN CREATION PIPELINE                  │
└────────────────────────────────────────────────────────────┘

1. Frontend Input
   ├─ Creative selection (asset_id, clip_id)
   ├─ Targeting (demographics, interests)
   ├─ Budget (daily/lifetime)
   └─ Schedule (start/end dates)
        ↓
2. Gateway API: Validation
   ├─ Check user permissions
   ├─ Validate budget limits
   ├─ Verify creative compliance
   └─ Check Meta account connection
        ↓
3. Prediction Generation
   ├─ Fetch clip features from database
   ├─ Call ML Service for CTR prediction
   └─ Store prediction record
        ↓
4. Meta Campaign Creation
   ├─ Upload video to Meta (if needed)
   ├─ Create campaign object
   ├─ Create ad set with targeting
   ├─ Create ad with creative
   └─ Submit for review
        ↓
5. Database Persistence
   ├─ Save campaign record
   ├─ Link to prediction
   └─ Set up tracking
        ↓
6. Response to Frontend
   └─ campaign_id, status, meta_campaign_id
```

---

## ML Pipeline

### CTR Prediction Model

```
┌────────────────────────────────────────────────────────────┐
│                    CTR PREDICTION PIPELINE                  │
└────────────────────────────────────────────────────────────┘

FEATURE EXTRACTION (75+ features):
────────────────────────────────────
1. Psychology Features (5)
   - Curiosity score
   - Urgency score
   - Social proof score
   - Transformation score
   - Authority score

2. Hook Features (10)
   - Hook type (one-hot)
   - Hook strength
   - Hook confidence
   - Secondary hooks count

3. Visual Features (15)
   - Visual energy
   - Pattern type (one-hot)
   - Transition count
   - Scene count
   - Face presence

4. Technical Features (12)
   - Resolution score
   - Audio quality
   - Motion score
   - FPS, bitrate
   - Has captions
   - Is vertical format

5. Emotion Features (10)
   - Happy, sad, angry, etc.
   - Face count
   - Emotion variance

6. Object Features (10)
   - Person count
   - Product count
   - Text count
   - Object diversity

7. Novelty Features (8)
   - Embedding distance
   - Temporal decay
   - Similarity to past ads

8. Demographic Features (5)
   - Age alignment
   - Interest match
   - Persona fit

MODEL ARCHITECTURE:
────────────────────────────────────
XGBoost Regressor:
  - 200 estimators
  - Max depth: 8
  - Learning rate: 0.05
  - Subsample: 0.8
  - Objective: reg:squarederror

TARGET ACCURACY:
  - R² > 0.88 (94% accuracy)
  - RMSE < 0.008
  - Mean error < 0.003

PREDICTION OUTPUT:
────────────────────────────────────
{
  "predicted_ctr": 0.048,
  "predicted_band": "high",
  "confidence": 0.89,
  "feature_importance": {...}
}
```

---

### Self-Learning Loop

```
┌────────────────────────────────────────────────────────────┐
│                  SELF-LEARNING PIPELINE                     │
└────────────────────────────────────────────────────────────┘

CONTINUOUS IMPROVEMENT CYCLE:

1. PREDICTION (T=0)
   ├─ User creates campaign
   ├─ ML model predicts CTR
   └─ Log prediction to database

2. CAMPAIGN RUNS (T=1 to T=7 days)
   ├─ Meta reports performance data
   └─ Sync insights daily

3. OUTCOME COLLECTION (T=7 days)
   ├─ Fetch actual CTR
   ├─ Fetch conversions
   ├─ Calculate ROAS
   └─ Link to prediction record

4. ACCURACY ANALYSIS (Weekly)
   ├─ Compare predicted vs actual
   ├─ Calculate error metrics
   ├─ Identify feature drift
   └─ Detect systematic biases

5. MODEL RETRAINING (Monthly or 100+ new samples)
   ├─ Prepare training dataset
   │  └─ Filter: Only campaigns with 50+ conversions
   ├─ Feature engineering
   ├─ Train new model
   ├─ Validate on holdout set
   └─ Deploy if accuracy improves

6. WEIGHT UPDATES (Weekly)
   ├─ Analyze misclassifications
   ├─ Adjust scoring weights
   │  └─ Max change: ±0.1 per weight
   ├─ Update config files
   └─ Hot-reload all services

METRICS TRACKED:
────────────────────────────────────
- Prediction accuracy (R²)
- In-band accuracy (predicted band matches actual)
- Feature importance drift
- Model staleness (days since last train)
- Prediction volume (total predictions)
```

---

## Infrastructure Components

### Database Schema (PostgreSQL)

```sql
-- Assets table
CREATE TABLE assets (
    asset_id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    file_hash VARCHAR(64),
    size_bytes BIGINT,
    duration FLOAT,
    resolution VARCHAR(20),
    fps INTEGER,
    status VARCHAR(20), -- queued, processing, completed, failed
    created_at TIMESTAMP DEFAULT NOW(),
    analyzed_at TIMESTAMP
);

-- Clips table
CREATE TABLE clips (
    clip_id UUID PRIMARY KEY,
    asset_id UUID REFERENCES assets(asset_id),
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    score FLOAT,
    hook_type VARCHAR(50),
    transcript TEXT,
    features JSONB, -- All extracted features
    embedding VECTOR(384), -- Sentence Transformer embedding
    created_at TIMESTAMP DEFAULT NOW()
);

-- Predictions table
CREATE TABLE predictions (
    prediction_id UUID PRIMARY KEY,
    clip_id UUID REFERENCES clips(clip_id),
    predicted_ctr FLOAT NOT NULL,
    predicted_band VARCHAR(20),
    confidence FLOAT,
    model_version VARCHAR(50),
    features_used JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Campaigns table
CREATE TABLE campaigns (
    campaign_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    name VARCHAR(255),
    clip_id UUID REFERENCES clips(clip_id),
    prediction_id UUID REFERENCES predictions(prediction_id),
    meta_campaign_id VARCHAR(100),
    status VARCHAR(20),
    budget_daily FLOAT,
    targeting JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    launched_at TIMESTAMP
);

-- Campaign outcomes table
CREATE TABLE campaign_outcomes (
    outcome_id UUID PRIMARY KEY,
    campaign_id UUID REFERENCES campaigns(campaign_id),
    prediction_id UUID REFERENCES predictions(prediction_id),
    actual_ctr FLOAT,
    actual_conversions INTEGER,
    actual_roas FLOAT,
    date_start DATE,
    date_end DATE,
    logged_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_clips_asset_id ON clips(asset_id);
CREATE INDEX idx_clips_score ON clips(score DESC);
CREATE INDEX idx_predictions_clip_id ON predictions(clip_id);
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_outcomes_campaign_id ON campaign_outcomes(campaign_id);
```

---

### Redis Data Structures

```
# Job Queues (using Redis Lists)
analysis_jobs:      LPUSH, BRPOP (worker consumption)
render_jobs:        LPUSH, BRPOP
upload_jobs:        LPUSH, BRPOP

# Rate Limiting (using Redis Strings with TTL)
rate_limit:user:{user_id}:minute     INCR, EXPIRE 60
rate_limit:ip:{ip}:minute            INCR, EXPIRE 60
rate_limit:global:minute             INCR, EXPIRE 60

# Caching (using Redis Strings with TTL)
cache:asset:{asset_id}               SET, GET, EXPIRE 3600
cache:clips:{asset_id}               SET, GET, EXPIRE 3600
cache:prediction:{prediction_id}     SET, GET, EXPIRE 7200

# Session Management
session:{session_id}                 HSET, HGET, EXPIRE 86400

# Pub/Sub (for real-time updates)
channel:render_updates               PUBLISH, SUBSCRIBE
channel:analysis_updates             PUBLISH, SUBSCRIBE

# Distributed Locks
lock:analysis:{asset_id}             SET NX EX 300
lock:training                        SET NX EX 3600
```

---

### Google Cloud Storage Structure

```
geminivideo-production/
├── videos/
│   ├── raw/
│   │   └── {asset_id}/
│   │       └── original.mp4
│   ├── clips/
│   │   └── {asset_id}/
│   │       ├── clip_001.mp4
│   │       ├── clip_002.mp4
│   │       └── ...
│   └── renders/
│       └── {render_id}/
│           └── output.mp4
├── thumbnails/
│   ├── assets/
│   │   └── {asset_id}.jpg
│   └── clips/
│       └── {clip_id}.jpg
├── models/
│   ├── xgboost/
│   │   ├── ctr_model_v1.pkl
│   │   └── ctr_model_v2.pkl
│   └── faiss/
│       └── embeddings.index
└── knowledge/
    ├── meta_patterns/
    │   └── {date}.json
    └── hooks/
        └── templates.json
```

---

## Security Architecture

### Defense in Depth

```
┌────────────────────────────────────────────────────────────┐
│                     SECURITY LAYERS                         │
└────────────────────────────────────────────────────────────┘

LAYER 1: Network Security
──────────────────────────
- Cloud Armor (WAF)
- DDoS protection
- IP whitelisting (admin endpoints)
- VPC isolation

LAYER 2: Application Security
──────────────────────────
- HTTPS only (TLS 1.3)
- Security headers (HSTS, CSP, etc.)
- CORS restrictions
- Input validation
- SQL injection prevention
- XSS protection

LAYER 3: Authentication & Authorization
──────────────────────────
- Firebase Authentication (JWT)
- API key authentication
- Role-based access control (RBAC)
- Session management (Redis)

LAYER 4: Rate Limiting
──────────────────────────
- Global: 60 req/min per IP
- API: 30 req/min per user
- Upload: 10 req/min per user
- Distributed rate limiting (Redis)

LAYER 5: Data Security
──────────────────────────
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Database encryption
- Secret management (Secret Manager)
- PII data anonymization

LAYER 6: Monitoring & Auditing
──────────────────────────
- Audit logs (all API requests)
- Anomaly detection
- Security scanning (Snyk, Trivy)
- Vulnerability patching
- Incident response plan
```

---

## Scalability & Performance

### Auto-Scaling Configuration

```yaml
# Cloud Run Auto-Scaling

gateway-api:
  min_instances: 1
  max_instances: 10
  cpu_threshold: 70%
  request_threshold: 100 concurrent
  scale_down_delay: 5 minutes

drive-intel:
  min_instances: 1
  max_instances: 5
  cpu_threshold: 80%
  memory_threshold: 80%

video-agent:
  min_instances: 1
  max_instances: 10
  cpu_threshold: 85%
  worker_count: 2 per instance

ml-service:
  min_instances: 2
  max_instances: 5
  cpu_threshold: 75%
  memory_threshold: 75%

meta-publisher:
  min_instances: 1
  max_instances: 3
  cpu_threshold: 60%
```

---

### Performance Targets

```
┌────────────────────────────────────────────────────────────┐
│                   PERFORMANCE TARGETS                       │
└────────────────────────────────────────────────────────────┘

API Response Times:
  - Health check: < 100ms
  - List assets: < 500ms
  - Single asset: < 200ms
  - Search clips: < 1000ms
  - Start analysis: < 300ms (async)
  - Score storyboard: < 2000ms

Video Processing:
  - Scene detection: < 30s per video
  - Feature extraction: < 90s per clip
  - Rendering: < 60s per output minute
  - Upload to Meta: < 120s per video

ML Inference:
  - CTR prediction: < 100ms
  - Hook classification: < 200ms
  - Council verdict: < 20s (parallel)

Database Queries:
  - Simple SELECT: < 10ms
  - Complex JOIN: < 100ms
  - Full-text search: < 500ms
  - FAISS search: < 200ms

Throughput:
  - Video uploads: 100 concurrent
  - Analysis jobs: 50 concurrent
  - Render jobs: 20 concurrent
  - API requests: 1000 req/sec
```

---

### Caching Strategy

```
┌────────────────────────────────────────────────────────────┐
│                     CACHING LAYERS                          │
└────────────────────────────────────────────────────────────┘

LAYER 1: CDN Caching (Cloud CDN)
  - Static assets: 1 year
  - Thumbnails: 7 days
  - Frontend bundles: 1 year (versioned)

LAYER 2: Application Caching (Redis)
  - Asset metadata: 1 hour
  - Clip lists: 1 hour
  - Predictions: 2 hours
  - User sessions: 24 hours

LAYER 3: Database Query Caching
  - PostgreSQL query cache: 5 minutes
  - Prepared statements: Permanent
  - Connection pooling: 20 connections

LAYER 4: ML Model Caching
  - Loaded models: In-memory (permanent)
  - FAISS index: In-memory (hot-reload)
  - Feature vectors: Redis (1 day)

Cache Invalidation:
  - On asset update: Clear asset + clips cache
  - On new prediction: Clear prediction cache
  - On model update: Hot-reload all services
  - Manual: Admin API endpoint
```

---

## Disaster Recovery

### Backup Strategy

```
┌────────────────────────────────────────────────────────────┐
│                    BACKUP & RECOVERY                        │
└────────────────────────────────────────────────────────────┘

PostgreSQL:
  - Automated daily backups (Cloud SQL)
  - Point-in-time recovery (7 days)
  - Cross-region replication
  - Backup retention: 30 days

GCS:
  - Versioning enabled
  - Soft delete (30 days)
  - Cross-region replication
  - Lifecycle policies

Redis:
  - Daily RDB snapshots
  - AOF persistence
  - Backup to GCS
  - Retention: 7 days

Code & Configuration:
  - Git version control
  - Tagged releases
  - Infrastructure as Code (Terraform)
  - Config backups (daily)

Recovery Time Objectives (RTO):
  - Database: < 1 hour
  - Services: < 30 minutes
  - Full system: < 2 hours

Recovery Point Objectives (RPO):
  - Database: < 15 minutes
  - File storage: < 1 hour
  - Redis: < 1 hour
```

---

## Monitoring & Observability

```
┌────────────────────────────────────────────────────────────┐
│                   MONITORING STACK                          │
└────────────────────────────────────────────────────────────┘

Metrics (Cloud Monitoring):
  - Request rate, latency, errors
  - CPU, memory, disk usage
  - Queue depth, worker utilization
  - ML model accuracy drift

Logs (Cloud Logging):
  - Structured JSON logs
  - Log levels: DEBUG, INFO, WARN, ERROR
  - Request/response logging
  - Audit trail

Traces (Cloud Trace):
  - Distributed tracing across services
  - Request flow visualization
  - Performance bottleneck identification

Alerts:
  - Error rate > 1% (5 min window)
  - Latency p95 > 5s (5 min window)
  - CPU > 80% (15 min window)
  - Queue depth > 100 (10 min window)
  - Model accuracy < 0.85 (daily check)

Dashboards:
  - System health overview
  - Per-service metrics
  - ML model performance
  - Business metrics (uploads, campaigns, ROAS)
```

---

*Last Updated: 2025-12-02*
*Version: 1.0.0*
