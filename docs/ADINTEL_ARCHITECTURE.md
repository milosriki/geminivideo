# AdIntel OS - Complete Architecture

> **Status: Infrastructure Complete** | Last Updated: Dec 2024

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GEMINIVIDEO PLATFORM                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                         FRONTEND (React + Vite)                          │   │
│  │                              Port: 3000                                  │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                         │   │
│  │   /discovery ──────────► DiscoveryDashboard.tsx                        │   │
│  │       │                     ├── Discovery Tab (search + facets)        │   │
│  │       │                     ├── Spyder Tab (brand tracking)            │   │
│  │       │                     └── Trends Tab (analytics)                 │   │
│  │       │                                                                 │   │
│  │       └──► useAdIntel.ts (React Hook)                                  │   │
│  │                 │                                                       │   │
│  │                 ▼                                                       │   │
│  │            API Calls to /api/intel/*                                   │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                         │
│                                      ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                      GATEWAY API (Node.js/Express)                       │   │
│  │                              Port: 8080                                  │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                         │   │
│  │   /api/intel/*  ──────────► Proxy to intel-api:8090                    │   │
│  │   /api/intel/search ──────► POST /api/v1/discovery/search              │   │
│  │   /api/intel/winners ─────► GET  /api/v1/discovery/winners             │   │
│  │   /api/intel/track-brand ─► POST /api/v1/spyder/track                  │   │
│  │   /api/intel/trends ──────► GET  /api/v1/analytics/trends              │   │
│  │                                                                         │   │
│  │   (existing routes: /api/assets, /api/analyze, /api/publish, etc.)     │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                         │
│                                      ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                        ADINTEL SERVICES LAYER                            │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                         │   │
│  │  ┌─────────────────────┐    ┌─────────────────────┐                    │   │
│  │  │    INTEL-API        │    │   INTEL-WORKER      │                    │   │
│  │  │    Port: 8090       │    │   (Background)      │                    │   │
│  │  ├─────────────────────┤    ├─────────────────────┤                    │   │
│  │  │                     │    │                     │                    │   │
│  │  │  adintel_api.py     │    │  orchestrator.py    │                    │   │
│  │  │  ├─ /discovery/*    │    │  ├─ scrape_worker   │                    │   │
│  │  │  ├─ /spyder/*       │◄───┤  ├─ enrich_worker   │                    │   │
│  │  │  ├─ /enrich         │    │  └─ scheduler       │                    │   │
│  │  │  ├─ /analytics/*    │    │                     │                    │   │
│  │  │  └─ /account/*      │    │  Pulls jobs from    │                    │   │
│  │  │                     │    │  Redis queues       │                    │   │
│  │  │  Credits system     │    │                     │                    │   │
│  │  │  Rate limiting      │    │                     │                    │   │
│  │  │                     │    │                     │                    │   │
│  │  └─────────────────────┘    └─────────────────────┘                    │   │
│  │            │                          │                                 │   │
│  │            ▼                          ▼                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐   │   │
│  │  │                     CORE INTEL MODULES                           │   │   │
│  │  ├─────────────────────────────────────────────────────────────────┤   │   │
│  │  │                                                                 │   │   │
│  │  │  ad_library_scraper.py          ad_enrichment.py                │   │   │
│  │  │  ├─ MetaAdLibraryScraper        ├─ WhisperClient (transcribe)   │   │   │
│  │  │  ├─ BrandTracker                ├─ GeminiAnalyzer (visual)      │   │   │
│  │  │  ├─ WinnerDetector              ├─ LlamaAnalyzer (NLP)          │   │   │
│  │  │  └─ Playwright automation       └─ HookAnalysis                 │   │   │
│  │  │                                                                 │   │   │
│  │  │  search_engine.py               foreplay_scraper.py             │   │   │
│  │  │  ├─ AdSearchEngine              ├─ Official API integration     │   │   │
│  │  │  ├─ AdDocument schema           └─ For learning/comparison      │   │   │
│  │  │  ├─ Faceted search                                              │   │   │
│  │  │  └─ Vector search               creatorify_client.py            │   │   │
│  │  │                                 └─ URL-to-Video AI              │   │   │
│  │  │                                                                 │   │   │
│  │  └─────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                      │                                         │
│                                      ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                           DATA LAYER                                     │   │
│  ├─────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │   │
│  │  │  PostgreSQL  │  │   Typesense  │  │    Redis     │                  │   │
│  │  │  Port: 5432  │  │  Port: 8108  │  │  Port: 6379  │                  │   │
│  │  ├──────────────┤  ├──────────────┤  ├──────────────┤                  │   │
│  │  │              │  │              │  │              │                  │   │
│  │  │ adintel_ads  │  │ ads (index)  │  │ scrape queue │                  │   │
│  │  │ - ad_id      │  │ - facets     │  │ enrich queue │                  │   │
│  │  │ - brand_name │  │ - vectors    │  │ index queue  │                  │   │
│  │  │ - emotion    │  │ - search     │  │              │                  │   │
│  │  │ - hook_type  │  │              │  │ Session      │                  │   │
│  │  │ - patterns   │  │ brands       │  │ cache        │                  │   │
│  │  │ - winner_*   │  │ (index)      │  │              │                  │   │
│  │  │              │  │              │  │              │                  │   │
│  │  │ adintel_     │  │              │  │              │                  │   │
│  │  │ brands       │  │              │  │              │                  │   │
│  │  │              │  │              │  │              │                  │   │
│  │  │ adintel_     │  │              │  │              │                  │   │
│  │  │ collections  │  │              │  │              │                  │   │
│  │  │              │  │              │  │              │                  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘                  │   │
│  │                                                                         │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### 1. Brand Tracking Flow (Spyder)

```
User clicks "Track Brand"
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────►│   Gateway       │────►│   Intel API     │
│   useAdIntel()  │     │   /api/intel/   │     │   /spyder/track │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   PostgreSQL    │
                                                │   INSERT brand  │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   Redis Queue   │
                                                │   RPUSH scrape  │
                                                └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INTEL WORKER (async)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. BLPOP scrape queue                                         │
│   2. MetaAdLibraryScraper.scrape_by_advertiser()               │
│   3. For each ad:                                               │
│      ├─ INSERT into PostgreSQL (adintel_ads)                   │
│      └─ RPUSH to enrich queue                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Enrichment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      INTEL WORKER (async)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   1. BLPOP enrich queue                                         │
│   2. AdEnrichmentPipeline.enrich()                             │
│      │                                                          │
│      ├─► WhisperClient.transcribe()                            │
│      │   └─ Timestamped transcription                          │
│      │                                                          │
│      ├─► GeminiAnalyzer.analyze_video()                        │
│      │   └─ Visual analysis, hooks, CTAs                       │
│      │                                                          │
│      └─► LlamaAnalyzer.analyze_text()                          │
│          └─ Emotions, messaging, patterns                       │
│                                                                 │
│   3. UPDATE PostgreSQL (enriched fields)                        │
│   4. Index to Typesense                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Search Flow

```
User types query + selects facets
         │
         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────►│   Gateway       │────►│   Intel API     │
│   useAdIntel()  │     │   /api/intel/   │     │   /discovery/   │
│   .searchAds()  │     │   search        │     │   search        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │   Typesense     │
                                                │   Faceted query │
                                                │   + filters     │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                              Returns: hits, facets,
                                              total, credits_used
```

---

## File Structure

```
services/intel/
├── __init__.py              # Module exports
├── Dockerfile               # Container build
├── requirements.txt         # Python dependencies
│
├── orchestrator.py          # THE BRAIN - wires everything
│   ├── OrchestratorConfig   # Uses env vars from docker-compose
│   ├── SCHEMA_SQL           # PostgreSQL table definitions
│   ├── JobQueue             # Redis queue wrapper
│   ├── AdIntelOrchestrator  # Main coordinator class
│   │   ├── initialize()     # Boot all components
│   │   ├── track_brand()    # Start tracking
│   │   ├── scrape_brand()   # Run scraper
│   │   ├── enrich_ad()      # Run AI pipeline
│   │   ├── sync_to_search() # PostgreSQL → Typesense
│   │   └── discover_ads()   # Search wrapper
│   └── Workers              # Background job processors
│
├── ad_library_scraper.py    # Meta Ad Library scraper
│   ├── MetaAdLibraryScraper # Playwright-based scraper
│   │   ├── scrape_by_advertiser()
│   │   ├── scrape_by_keyword()
│   │   └── _intercept_graphql()  # Get structured data
│   ├── BrandTracker         # Monitor competitor brands
│   ├── WinnerDetector       # 30+ days = winner
│   └── ScrapedAd            # Data model
│
├── ad_enrichment.py         # AI enrichment pipeline
│   ├── WhisperClient        # Audio transcription
│   ├── GeminiAnalyzer       # Visual analysis (Gemini 2.0)
│   ├── LlamaAnalyzer        # NLP analysis (Llama 4)
│   ├── AdEnrichmentPipeline # Combines all three
│   │   └── enrich()         # Main method
│   ├── TranscriptionResult  # With timestamps
│   ├── HookAnalysis         # First 3 seconds
│   └── EnrichedAd           # Full enriched data
│
├── search_engine.py         # Typesense search
│   ├── AD_COLLECTION_SCHEMA # Index schema with facets
│   ├── AdSearchEngine       # Search client
│   │   ├── search()         # Main search
│   │   ├── search_winners() # Winners only
│   │   ├── search_by_emotion()
│   │   ├── search_similar() # Vector search
│   │   └── get_suggestions()# Autocomplete
│   ├── AdDocument           # Document model
│   └── AdIndexingPipeline   # Bulk indexer
│
├── adintel_api.py           # REST API (FastAPI)
│   ├── /discovery/search    # POST - faceted search
│   ├── /discovery/winners   # GET - winning ads
│   ├── /discovery/similar   # GET - find similar
│   ├── /spyder/track        # POST - track brand
│   ├── /spyder/brands       # GET - list tracked
│   ├── /spyder/brand/{id}   # GET/DELETE - manage
│   ├── /enrich              # POST - AI enrich
│   ├── /analytics/trends    # GET - trends
│   ├── /analytics/emotions  # GET - emotion breakdown
│   ├── /analytics/hooks     # GET - hook patterns
│   └── /account/credits     # GET - credit balance
│
├── foreplay_scraper.py      # Official Foreplay API
│   └── ForeplayIntegration  # For learning/comparison
│
└── creatorify_client.py     # Creatify AI
    └── CreatifyIntegration  # URL-to-Video generation
```

---

## Database Schema

### PostgreSQL Tables

```sql
-- Main ads table
CREATE TABLE adintel_ads (
    id SERIAL PRIMARY KEY,
    ad_id VARCHAR(255) UNIQUE NOT NULL,
    brand_name VARCHAR(255) NOT NULL,
    brand_id VARCHAR(255),
    platform VARCHAR(50) DEFAULT 'meta',
    format VARCHAR(50) DEFAULT 'video',

    -- Content
    headline TEXT,
    body_text TEXT,
    transcription TEXT,
    cta VARCHAR(100),

    -- AI Enrichment
    primary_emotion VARCHAR(100),
    emotional_drivers JSONB DEFAULT '[]',
    hook_type VARCHAR(100),
    hook_text TEXT,
    winning_patterns JSONB DEFAULT '[]',
    winner_score INTEGER DEFAULT 0,

    -- Performance
    running_duration_days INTEGER DEFAULT 0,
    is_winner BOOLEAN DEFAULT FALSE,
    estimated_spend DECIMAL(12,2),

    -- Media URLs
    thumbnail_url TEXT,
    video_url TEXT,
    landing_page_url TEXT,

    -- Classification
    industry VARCHAR(100),
    category VARCHAR(100),
    tags JSONB DEFAULT '[]',

    -- Timestamps
    first_seen TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW(),
    enriched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tracked brands
CREATE TABLE adintel_brands (
    id SERIAL PRIMARY KEY,
    brand_id VARCHAR(255) UNIQUE NOT NULL,
    brand_name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),
    industry VARCHAR(100),
    is_tracked BOOLEAN DEFAULT FALSE,
    check_interval_hours INTEGER DEFAULT 24,
    last_checked TIMESTAMP,
    next_check TIMESTAMP,
    total_ads INTEGER DEFAULT 0,
    winner_count INTEGER DEFAULT 0,
    avg_running_days DECIMAL(6,1) DEFAULT 0,
    platforms JSONB DEFAULT '["meta"]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User collections/boards
CREATE TABLE adintel_collections (
    id SERIAL PRIMARY KEY,
    collection_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ad_ids JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_ads_brand ON adintel_ads(brand_name);
CREATE INDEX idx_ads_winner ON adintel_ads(is_winner);
CREATE INDEX idx_ads_industry ON adintel_ads(industry);
CREATE INDEX idx_ads_emotion ON adintel_ads(primary_emotion);
CREATE INDEX idx_ads_running_days ON adintel_ads(running_duration_days DESC);
CREATE INDEX idx_brands_tracked ON adintel_brands(is_tracked);
```

### Typesense Schema

```javascript
{
  "name": "ads",
  "fields": [
    {"name": "id", "type": "string"},
    {"name": "ad_id", "type": "string", "facet": true},
    {"name": "brand_name", "type": "string", "facet": true},
    {"name": "platform", "type": "string", "facet": true},
    {"name": "format", "type": "string", "facet": true},
    {"name": "industry", "type": "string", "facet": true},
    {"name": "primary_emotion", "type": "string", "facet": true},
    {"name": "hook_type", "type": "string", "facet": true},
    {"name": "winning_patterns", "type": "string[]", "facet": true},
    {"name": "running_duration_days", "type": "int32"},
    {"name": "is_winner", "type": "bool", "facet": true},
    {"name": "winner_score", "type": "int32"},
    {"name": "search_text", "type": "string"},
    {"name": "embedding", "type": "float[]", "num_dim": 768}
  ],
  "default_sorting_field": "running_duration_days"
}
```

---

## API Endpoints Reference

### Discovery API

| Endpoint | Method | Credits | Description |
|----------|--------|---------|-------------|
| `/api/v1/discovery/search` | POST | 1 | Faceted search |
| `/api/v1/discovery/winners` | GET | 1 | Winners only |
| `/api/v1/discovery/similar/{id}` | GET | 2 | Find similar |
| `/api/v1/discovery/suggestions` | GET | 0 | Autocomplete |

### Spyder API (Brand Tracking)

| Endpoint | Method | Credits | Description |
|----------|--------|---------|-------------|
| `/api/v1/spyder/track` | POST | 10 | Start tracking |
| `/api/v1/spyder/brands` | GET | 0 | List tracked |
| `/api/v1/spyder/brand/{id}/ads` | GET | 1 | Brand's ads |
| `/api/v1/spyder/brand/{id}` | DELETE | 0 | Stop tracking |

### Enrichment API

| Endpoint | Method | Credits | Description |
|----------|--------|---------|-------------|
| `/api/v1/enrich` | POST | 5 | AI analysis |
| `/api/v1/enrich/batch` | POST | 3/ad | Bulk enrich |

### Analytics API

| Endpoint | Method | Credits | Description |
|----------|--------|---------|-------------|
| `/api/v1/analytics/trends` | GET | 0 | Industry trends |
| `/api/v1/analytics/emotions` | GET | 0 | Emotion breakdown |
| `/api/v1/analytics/hooks` | GET | 0 | Hook patterns |
| `/api/v1/analytics/brand/{name}` | GET | 1 | Brand analytics |

---

## Docker Services

```yaml
# From docker-compose.yml

services:
  # Infrastructure (existing)
  postgres:      # Port 5432 - Main database
  redis:         # Port 6379 - Queues & cache

  # AdIntel (new)
  typesense:     # Port 8108 - Search engine
  intel-api:     # Port 8090 - REST API
  intel-worker:  # Background - Job processor

  # Gateway (updated)
  gateway-api:   # Port 8080 - Proxies /api/intel/*

  # Frontend (updated)
  frontend:      # Port 3000 - /discovery route added
```

---

## What's Complete vs TODO

### Complete (Code Written)

- [x] `orchestrator.py` - Full orchestration logic
- [x] `ad_library_scraper.py` - Meta scraper with Playwright
- [x] `ad_enrichment.py` - Gemini + Whisper + Llama pipeline
- [x] `search_engine.py` - Typesense integration
- [x] `adintel_api.py` - Full REST API
- [x] `useAdIntel.ts` - React hook
- [x] `DiscoveryDashboard.tsx` - UI with 3 tabs
- [x] Docker config - All services defined
- [x] Gateway proxy - Routes wired
- [x] Database schema - Tables defined

### TODO (Integration Work)

- [ ] Test scraper with real Meta Ad Library
- [ ] Configure Gemini API key
- [ ] Set up residential proxies for production
- [ ] Add error handling & retries
- [ ] Add logging/monitoring
- [ ] Write tests
- [ ] Seed initial data

---

## Quick Start

```bash
# 1. Start infrastructure
docker-compose up -d postgres redis typesense

# 2. Set environment
cp .env.example .env
# Edit .env and add GEMINI_API_KEY

# 3. Build intel services
docker-compose build intel-api intel-worker

# 4. Initialize database
docker-compose run intel-api python -m intel.orchestrator init

# 5. Start everything
docker-compose up -d

# 6. Access
# Frontend: http://localhost:3000/discovery
# API: http://localhost:8090/api/v1/health
# Typesense: http://localhost:8108/health
```

---

## Comparison: Us vs Foreplay

| Feature | Foreplay | AdIntel OS |
|---------|----------|------------|
| Data Source | Meta + TikTok | Meta (TikTok ready) |
| AI Enrichment | Third-party | Gemini + Llama (owned) |
| Search | Elasticsearch | Typesense |
| Pricing | $99+/month | Self-hosted |
| Credits | Limited | Configurable |
| Brand Tracking | Spyder | Built-in |
| Hook Analysis | Basic | AI-powered |
| Vector Search | No | Yes |
