# GeminiVideo Data Flow Documentation

**Version:** 1.0
**Last Updated:** 2025-12-06

This document provides comprehensive data flow diagrams for the GeminiVideo AI video advertising platform, showing how data moves through the system from video upload to performance optimization.

---

## Table of Contents

1. [Video Analysis Flow](#1-video-analysis-flow)
2. [Variation Generation Flow](#2-variation-generation-flow)
3. [Ad Publishing Flow](#3-ad-publishing-flow)
4. [Performance Tracking Flow](#4-performance-tracking-flow)
5. [Learning Loop Flow](#5-learning-loop-flow)
6. [Budget Optimization Flow](#6-budget-optimization-flow)
7. [Complete System Flow](#7-complete-system-flow)

---

## 1. VIDEO ANALYSIS FLOW

**Purpose:** Analyze uploaded videos to extract patterns, moments, and features for optimization.

### Flow Diagram

```
┌─────────────────┐
│  Video Upload   │ ← User uploads video file (MP4, MOV)
│   (Frontend)    │    Format: multipart/form-data
└────────┬────────┘    Size: up to 500MB
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Motion Moment SDK                                           │
│ File: services/video-agent/pro/motion_moment_sdk.py        │
├─────────────────────────────────────────────────────────────┤
│ • Loads video with OpenCV (cv2.VideoCapture)               │
│ • Analyzes 30-frame sliding windows (1 second at 30fps)    │
│ • Calculates optical flow between frames                   │
│ • Detects motion energy peaks                              │
│                                                             │
│ Input:  Video file path                                    │
│ Output: List[MotionMoment]                                 │
│         - frame_start, frame_end                           │
│         - timestamp_start, timestamp_end                   │
│         - motion_energy (float)                            │
│         - moment_type ('hook', 'transition', 'cta')        │
│                                                             │
│ Timing: ~5-10 seconds for 30-second video                  │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Face Detection & Weighting                                  │
│ File: services/video-agent/pro/face_weighted_analyzer.py   │
├─────────────────────────────────────────────────────────────┤
│ • Detects human faces (Haar Cascade or YOLOv8)            │
│ • Applies 3.2x weight to frames with faces                 │
│ • Calculates face engagement score                         │
│                                                             │
│ Input:  Video frames + MotionMoments                       │
│ Output: Enhanced MotionMoments with face_weight            │
│         - face_present: bool                               │
│         - face_weight: 3.2 or 1.0                          │
│                                                             │
│ Decision Point: If face_present → Apply 3.2x multiplier    │
│ Timing: ~2-3 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Hook Optimizer                                              │
│ File: services/video-agent/pro/hook_optimizer.py           │
├─────────────────────────────────────────────────────────────┤
│ • Analyzes first 3 seconds (critical hook period)          │
│ • Identifies attention-grabbing moments                     │
│ • Scores hook effectiveness (0-1 scale)                    │
│                                                             │
│ Input:  MotionMoments (filtered to t < 3.0s)               │
│ Output: HookAnalysis                                        │
│         - hook_score: float (0-1)                          │
│         - hook_type: str                                   │
│         - optimization_suggestions: List[str]              │
│                                                             │
│ Decision Point: If hook_score < 0.6 → Suggest re-edit      │
│ Timing: ~1 second                                          │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Audio Sync Detection                                        │
│ File: services/video-agent/pro/audio_sync.py               │
├─────────────────────────────────────────────────────────────┤
│ • Extracts audio track (librosa/ffmpeg)                    │
│ • Analyzes beat patterns and speech segments               │
│ • Matches audio beats to visual motion moments             │
│                                                             │
│ Input:  Video file + MotionMoments                         │
│ Output: AudioVisualSync                                    │
│         - sync_points: List[float] (timestamps)            │
│         - sync_quality: float (0-1)                        │
│         - beat_matches: int                                │
│                                                             │
│ Timing: ~3-5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Pattern Extraction & Storage                                │
│ File: services/drive-intel/services/winning_patterns_db.py │
├─────────────────────────────────────────────────────────────┤
│ • Aggregates all analysis results                          │
│ • Extracts reusable patterns                               │
│ • Stores in patterns database                              │
│                                                             │
│ Input:  All analysis results                               │
│ Output: VideoPattern (stored in DB)                        │
│         {                                                   │
│           "video_id": str,                                 │
│           "motion_moments": List[Dict],                    │
│           "hook_score": float,                             │
│           "face_engagement": float,                        │
│           "audio_sync_quality": float,                     │
│           "extracted_at": datetime                         │
│         }                                                   │
│                                                             │
│ Timing: ~0.5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Analysis Report │ → Returned to orchestrator
│   (Complete)    │    Ready for variation generation
└─────────────────┘

Total Time: ~12-22 seconds per video
```

### Data Formats

**MotionMoment:**
```python
{
    "frame_start": 0,
    "frame_end": 30,
    "timestamp_start": 0.0,
    "timestamp_end": 1.0,
    "motion_energy": 15.7,
    "peak_frame": 15,
    "peak_energy": 22.3,
    "moment_type": "hook",
    "face_present": True,
    "face_weight": 3.2
}
```

---

## 2. VARIATION GENERATION FLOW

**Purpose:** Generate 50 variations from a single creative concept, rank by predicted performance.

### Flow Diagram

```
┌──────────────────┐
│ Creative Concept │ ← User provides concept
│   (Input Form)   │    Product, benefit, pain point, audience
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Cross-Campaign Learning Recommendations                     │
│ File: services/ml-service/src/cross_campaign_learning.py   │
├─────────────────────────────────────────────────────────────┤
│ • Query similar campaigns (by industry, objective)         │
│ • Extract winning patterns from past campaigns             │
│ • Get industry benchmarks                                  │
│                                                             │
│ Input:  CreativeRequest                                    │
│         {                                                   │
│           "industry": "ecommerce",                         │
│           "objective": "conversions",                      │
│           "target_audience": "25-45 women"                 │
│         }                                                   │
│                                                             │
│ Output: Recommendations                                    │
│         {                                                   │
│           "industry_benchmarks": {                         │
│             "expected_roas": 2.3,                          │
│             "expected_ctr": 0.025,                         │
│             "confidence": 0.85                             │
│           },                                               │
│           "recommended_hooks": List[str],                  │
│           "recommended_ctas": List[str],                   │
│           "patterns_to_avoid": List[Dict]                  │
│         }                                                   │
│                                                             │
│ Decision Point: If confidence < 0.5 → Use general patterns │
│ Timing: ~0.5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Variation Generator                                         │
│ File: services/ml-service/src/variation_generator.py       │
├─────────────────────────────────────────────────────────────┤
│ STRATEGY 1: Hook Variations (10 variations)                │
│   • Template: "Stop scrolling! {pain_point}?"             │
│   • Template: "What if {benefit}?"                         │
│   • Template: "POV: You discovered {product}"             │
│   • Keep CTA, headline, colors constant                    │
│                                                             │
│ STRATEGY 2: CTA Variations (10 variations)                 │
│   • Template: "Get {product} Now →"                        │
│   • Template: "Try {product} Free"                         │
│   • Keep hook, headline constant                           │
│                                                             │
│ STRATEGY 3: Headline Variations (10 variations)            │
│   • Vary main text overlay                                 │
│   • Different benefit positioning                          │
│                                                             │
│ STRATEGY 4: Color Variations (5 variations)                │
│   • Vibrant: ["#FF6B6B", "#4ECDC4", "#45B7D1"]            │
│   • Professional: ["#2C3E50", "#E74C3C", "#ECF0F1"]       │
│   • Modern: ["#9B59B6", "#3498DB", "#1ABC9C"]             │
│                                                             │
│ STRATEGY 5: Pacing × Duration (9 variations)               │
│   • fast/15s, fast/30s, fast/60s                           │
│   • medium/15s, medium/30s, medium/60s                     │
│   • slow/15s, slow/30s, slow/60s                           │
│                                                             │
│ STRATEGY 6: Cross-Combinations (6+ variations)             │
│   • Top 3 hooks × Top 3 CTAs × Top 2 colors                │
│                                                             │
│ Input:  CreativeConcept + Recommendations                  │
│ Output: List[CreativeVariation] (50 items)                 │
│                                                             │
│ Timing: ~1-2 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Performance Prediction (ML Model)                           │
│ File: services/ml-service/src/performance_predictor.py     │
├─────────────────────────────────────────────────────────────┤
│ • Score each variation (0-1 scale)                         │
│ • Features: hook type, CTA urgency, duration, colors       │
│ • Model: XGBoost trained on historical campaign data       │
│                                                             │
│ Input:  Each CreativeVariation                             │
│ Output: predicted_performance: float                       │
│                                                             │
│ Prediction Logic:                                          │
│   base_score = 0.5                                         │
│   + 0.1 if hook contains urgency words                     │
│   + 0.1 if CTA has clear action                            │
│   + 0.05 if duration == 15s                                │
│   + 0.05 if pacing == "fast"                               │
│   - 0.05 if duration == 60s                                │
│                                                             │
│ Timing: ~2-3 seconds for 50 variations                     │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Ranking & Selection                                         │
├─────────────────────────────────────────────────────────────┤
│ • Sort variations by predicted_performance (descending)    │
│ • Select top 10 for rendering                              │
│ • Deduplicate by variation_hash                            │
│                                                             │
│ Input:  50 variations with predictions                     │
│ Output: Top 10 CreativeVariations                          │
│                                                             │
│ Data Format (per variation):                               │
│   {                                                         │
│     "id": "concept_123_var_1",                             │
│     "variation_number": 1,                                 │
│     "hook": "Stop scrolling! Tired of dry skin?",          │
│     "headline": "Get hydrated skin in 7 days",             │
│     "cta": "Shop Now →",                                   │
│     "colors": ["#FF6B6B", "#4ECDC4"],                      │
│     "pacing": "fast",                                      │
│     "duration": 15,                                        │
│     "predicted_score": 0.78,                               │
│     "render_priority": 1                                   │
│   }                                                         │
│                                                             │
│ Decision Point: Only render if predicted_score > 0.5       │
│ Timing: <0.1 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│   Top 10 List    │ → Sent to video rendering
│ (Ready to Render)│
└──────────────────┘

Total Time: ~4-6 seconds for 50 variations
```

### Variation Data Structure

```python
CreativeVariation {
    id: str                           # Unique identifier
    concept_id: str                   # Parent concept
    variation_number: int             # 1-50
    variations_applied: Dict          # What changed
    hook: str                         # Opening text
    headline: str                     # Main message
    cta: str                          # Call to action
    color_scheme: List[str]           # Hex colors
    pacing: str                       # fast/medium/slow
    duration: int                     # 15/30/60 seconds
    created_at: datetime
    predicted_performance: float      # 0-1 score
    variation_hash: str               # For deduplication
}
```

---

## 3. AD PUBLISHING FLOW

**Purpose:** Publish top variations to Meta Ads, Google Ads, and TikTok platforms.

### Flow Diagram

```
┌──────────────────┐
│ Rendered Videos  │ ← Top 10 variations (MP4 files)
│  (Video Files)   │    S3 URLs or local paths
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Platform Router                                             │
│ File: services/titan-core/orchestrator/                    │
│       winning_ads_orchestrator.py                          │
├─────────────────────────────────────────────────────────────┤
│ • Determine target platforms from request                  │
│ • Split budget across platforms                            │
│ • Route to appropriate API clients                         │
│                                                             │
│ Input:  {                                                   │
│   "platforms": ["meta", "google", "tiktok"],               │
│   "budget_daily": 300,                                     │
│   "videos": List[Dict]  # Top 10                           │
│ }                                                           │
│                                                             │
│ Decision Logic:                                            │
│   - If "meta" in platforms → Meta Ads API                  │
│   - If "google" in platforms → Google Ads API              │
│   - If "tiktok" in platforms → TikTok Ads API              │
│   - Budget split: equal across platforms                   │
│                                                             │
│ Timing: <0.1 seconds                                       │
└─┬───────────────────┬───────────────────┬───────────────────┘
  │                   │                   │
  │ Meta              │ Google            │ TikTok
  ▼                   ▼                   ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Meta Ads    │ │ Google Ads   │ │  TikTok Ads  │
│   API Call   │ │   API Call   │ │   API Call   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       ▼                ▼                ▼

┌─────────────────────────────────────────────────────────────┐
│ Meta Ads API Integration                                    │
│ Endpoint: graph.facebook.com/v18.0/act_{ad_account_id}     │
├─────────────────────────────────────────────────────────────┤
│ STEP 1: Upload Video Creative                              │
│   POST /advideos                                            │
│   Body: {                                                   │
│     "file_url": "https://s3.../video.mp4",                 │
│     "title": "Variation #1"                                │
│   }                                                         │
│   Response: { "id": "video_123" }                          │
│                                                             │
│ STEP 2: Create Ad Creative                                 │
│   POST /adcreatives                                         │
│   Body: {                                                   │
│     "object_story_spec": {                                 │
│       "video_data": {                                      │
│         "video_id": "video_123",                           │
│         "message": variation.headline,                     │
│         "call_to_action": {                                │
│           "type": "SHOP_NOW",                              │
│           "value": { "link": landing_url }                 │
│         }                                                   │
│       }                                                     │
│     }                                                       │
│   }                                                         │
│   Response: { "id": "creative_456" }                       │
│                                                             │
│ STEP 3: Create Ad                                          │
│   POST /ads                                                 │
│   Body: {                                                   │
│     "name": f"Variation {variation_number}",               │
│     "adset_id": "adset_789",                               │
│     "creative": { "creative_id": "creative_456" },         │
│     "status": "PAUSED"  # Start paused                     │
│   }                                                         │
│   Response: { "id": "ad_999" }                             │
│                                                             │
│ STEP 4: Set Budget & Activate                              │
│   POST /adsets/{adset_id}                                  │
│   Body: {                                                   │
│     "daily_budget": budget_per_variation * 100,  # cents   │
│     "status": "ACTIVE"                                     │
│   }                                                         │
│                                                             │
│ STEP 5: Install CAPI Webhook                               │
│   POST /adaccounts/{account_id}/activities                 │
│   Body: {                                                   │
│     "event": "CONVERSIONS_API",                            │
│     "callback_url": "https://api.geminivideo.com/capi"     │
│   }                                                         │
│                                                             │
│ Timing: ~2-3 seconds per variation (30-45 sec for 10)      │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Google Ads API Integration                                  │
│ Endpoint: googleads.googleapis.com/v14/customers/{id}       │
├─────────────────────────────────────────────────────────────┤
│ STEP 1: Upload Video Asset                                 │
│   POST /assetService/mutate                                 │
│   Body: {                                                   │
│     "operations": [{                                       │
│       "create": {                                          │
│         "type": "YOUTUBE_VIDEO",                           │
│         "youtube_video_asset": {                           │
│           "youtube_video_id": uploaded_video_id            │
│         }                                                   │
│       }                                                     │
│     }]                                                      │
│   }                                                         │
│                                                             │
│ STEP 2: Create Video Ad                                    │
│   POST /adGroupAdService/mutate                             │
│   Body: {                                                   │
│     "operations": [{                                       │
│       "create": {                                          │
│         "ad_group": "adgroups/123",                        │
│         "ad": {                                            │
│           "video_ad": {                                    │
│             "video": { "asset": "assets/456" },            │
│             "in_stream": {                                 │
│               "companion_banner": headline_asset           │
│             }                                              │
│           },                                               │
│           "final_urls": [landing_url]                      │
│         },                                                 │
│         "status": "PAUSED"                                 │
│       }                                                     │
│     }]                                                      │
│   }                                                         │
│                                                             │
│ STEP 3: Set Budget                                         │
│   POST /campaignService/mutate                              │
│   Body: {                                                   │
│     "operations": [{                                       │
│       "update": {                                          │
│         "resource_name": "campaigns/789",                  │
│         "campaign_budget": {                               │
│           "amount_micros": budget * 1000000                │
│         }                                                   │
│       }                                                     │
│     }]                                                      │
│   }                                                         │
│                                                             │
│ Timing: ~3-4 seconds per variation                         │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Campaign Tracking Setup                                     │
├─────────────────────────────────────────────────────────────┤
│ • Store campaign IDs in database                           │
│ • Link variations to campaigns                             │
│ • Set up conversion tracking pixels                        │
│ • Configure UTM parameters                                 │
│                                                             │
│ Database Record:                                           │
│   {                                                         │
│     "campaign_id": "camp_abc123",                          │
│     "variation_id": "concept_123_var_1",                   │
│     "platform": "meta",                                    │
│     "ad_id": "ad_999",                                     │
│     "creative_id": "creative_456",                         │
│     "budget_daily": 10.0,                                  │
│     "status": "active",                                    │
│     "created_at": "2025-12-06T10:00:00Z",                  │
│     "tracking_url": "https://...?utm_campaign=camp_abc123" │
│   }                                                         │
│                                                             │
│ Timing: ~0.5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Ads Live on     │ → Campaigns running, tracking active
│    Platforms     │    Budget spending, conversions tracked
└──────────────────┘

Total Time: ~60-90 seconds for 10 variations across 3 platforms
```

### Platform API Response Formats

**Meta Ads Response:**
```json
{
  "id": "ad_6123456789",
  "status": "ACTIVE",
  "creative": {
    "id": "creative_456",
    "video_id": "video_123"
  },
  "adset_id": "adset_789",
  "campaign_id": "camp_999"
}
```

**Google Ads Response:**
```json
{
  "results": [{
    "resourceName": "customers/123/adGroupAds/456~789",
    "ad": {
      "id": "789",
      "videoAd": {
        "video": { "asset": "assets/456" }
      }
    }
  }]
}
```

---

## 4. PERFORMANCE TRACKING FLOW

**Purpose:** Track real conversions via CAPI webhooks and optimize budgets in real-time.

### Flow Diagram

```
┌──────────────────┐
│  User Converts   │ ← Customer purchases on website
│  (Website Event) │    Triggered by: checkout, lead form, signup
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Meta Conversions API (CAPI) Webhook                         │
│ Endpoint: POST /api/v1/capi/events                          │
│ File: services/ml-service/src/capi_feedback_loop.py        │
├─────────────────────────────────────────────────────────────┤
│ Webhook receives conversion event from Meta:                │
│                                                             │
│ Request Body:                                               │
│   {                                                         │
│     "event_id": "evt_abc123",                              │
│     "event_name": "Purchase",                              │
│     "event_time": 1733472000,  # Unix timestamp            │
│     "user_data": {                                         │
│       "em": "hash_email",                                  │
│       "ph": "hash_phone",                                  │
│       "client_ip_address": "1.2.3.4",                      │
│       "client_user_agent": "Mozilla/5.0..."               │
│     },                                                      │
│     "custom_data": {                                       │
│       "value": 79.99,                                      │
│       "currency": "USD",                                   │
│       "content_ids": ["var_123"],                          │
│       "campaign_id": "camp_abc123"                         │
│     },                                                      │
│     "event_source_url": "https://shop.com/checkout?        │
│                          utm_campaign=camp_abc123",        │
│     "action_source": "website"                             │
│   }                                                         │
│                                                             │
│ Processing Steps:                                          │
│   1. Validate webhook signature                            │
│   2. Extract campaign_id from URL or custom_data           │
│   3. Extract creative_id from content_ids                  │
│   4. Parse conversion value & currency                     │
│                                                             │
│ Timing: <0.1 seconds (webhook must respond quickly)        │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Campaign Matching & Attribution                             │
│ File: services/ml-service/src/capi_feedback_loop.py        │
│ Function: _extract_campaign_id()                           │
├─────────────────────────────────────────────────────────────┤
│ • Parse event_source_url for UTM parameters                │
│ • Match to campaign record in database                     │
│ • Link to specific creative variation                      │
│                                                             │
│ Matching Logic:                                            │
│   1. Check custom_data['campaign_id'] (most reliable)      │
│   2. Parse utm_campaign from event_source_url              │
│   3. Check fbclid parameter                                │
│   4. Fall back to IP/timestamp matching                    │
│                                                             │
│ Database Query:                                            │
│   SELECT * FROM campaigns                                  │
│   WHERE campaign_id = 'camp_abc123'                        │
│   AND status = 'active'                                    │
│                                                             │
│ Decision Point: If no match found → Log to orphaned_events │
│ Timing: ~0.05 seconds                                      │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Update Campaign Actuals                                     │
│ Table: campaign_actuals                                     │
├─────────────────────────────────────────────────────────────┤
│ • Increment conversion count                               │
│ • Add to total revenue                                     │
│ • Recalculate ROAS, CPA, CVR                               │
│                                                             │
│ SQL Update:                                                │
│   UPDATE campaign_actuals                                  │
│   SET conversions = conversions + 1,                       │
│       revenue = revenue + 79.99,                           │
│       roas = revenue / spend,                              │
│       cpa = spend / conversions,                           │
│       last_conversion_at = NOW()                           │
│   WHERE campaign_id = 'camp_abc123'                        │
│   AND date = CURRENT_DATE                                  │
│                                                             │
│ Updated Record:                                            │
│   {                                                         │
│     "campaign_id": "camp_abc123",                          │
│     "date": "2025-12-06",                                  │
│     "impressions": 12453,                                  │
│     "clicks": 234,                                         │
│     "conversions": 12,  # ← Incremented                    │
│     "revenue": 959.88,  # ← Updated                        │
│     "spend": 150.00,                                       │
│     "ctr": 0.0188,                                         │
│     "cvr": 0.0513,                                         │
│     "cpa": 12.50,                                          │
│     "roas": 6.40  # ← Recalculated                         │
│   }                                                         │
│                                                             │
│ Timing: ~0.02 seconds                                      │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Budget Optimizer Check (Real-time)                          │
│ File: services/ml-service/src/budget_optimizer.py          │
├─────────────────────────────────────────────────────────────┤
│ Triggered every 100 conversions OR every 4 hours            │
│                                                             │
│ Analysis:                                                  │
│   1. Fetch all active campaigns                            │
│   2. Categorize by performance:                            │
│      - Winners: ROAS > 3.0 (150% of target)                │
│      - Stable: ROAS 2.0-3.0 (target range)                 │
│      - Underperforming: ROAS 1.0-2.0                       │
│      - Losers: ROAS < 1.0                                  │
│      - Learning: < 24 hours or < $50 spend                 │
│                                                             │
│ Budget Shift Logic:                                        │
│   Winners: +50% budget (max +$50/day per campaign)         │
│   Losers: -70% budget (min $10/day floor)                  │
│   Underperforming: -30% budget                             │
│                                                             │
│ Example for our campaign (ROAS 6.40 = Winner):             │
│   Current budget: $150/day                                 │
│   New budget: $150 * 1.5 = $225/day                        │
│   Change: +$75/day                                         │
│                                                             │
│ Decision Point: Only shift if confidence > 0.7             │
│   confidence = min(1.0, spend / $100)                      │
│                                                             │
│ Timing: ~0.5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Kill Switch Evaluation                                      │
│ File: services/ml-service/src/loser_kill_switch.py         │
├─────────────────────────────────────────────────────────────┤
│ Automatic Kill Triggers (checked every conversion):        │
│                                                             │
│ 1. CTR Check:                                              │
│    IF impressions > 1000 AND ctr < 0.5%                    │
│    → KILL (low click-through, ad not engaging)             │
│                                                             │
│ 2. CVR Check:                                              │
│    IF clicks > 100 AND cvr < 0.5%                          │
│    → KILL (no landing page conversion)                     │
│                                                             │
│ 3. CPA Check:                                              │
│    IF conversions > 3 AND cpa > $150 (3x target $50)       │
│    → KILL (too expensive per conversion)                   │
│                                                             │
│ 4. ROAS Check:                                             │
│    IF spend > $100 AND roas < 0.5                          │
│    → KILL (losing money, negative return)                  │
│                                                             │
│ 5. No Conversions Check:                                   │
│    IF spend > $100 AND conversions == 0                    │
│    → KILL (complete failure, zero conversions)             │
│                                                             │
│ Kill Execution (if triggered):                             │
│   1. Pause campaign via platform API                       │
│   2. Log kill decision with reason                         │
│   3. Send alert to user                                    │
│   4. Calculate waste prevented                             │
│                                                             │
│ For our campaign (ROAS 6.40):                              │
│   ✓ CTR 1.88% > 0.5% → PASS                                │
│   ✓ CVR 5.13% > 0.5% → PASS                                │
│   ✓ CPA $12.50 < $150 → PASS                               │
│   ✓ ROAS 6.40 > 0.5 → PASS                                 │
│   ✓ Conversions 12 > 0 → PASS                              │
│   → Campaign continues, no kill                            │
│                                                             │
│ Decision Point: If ANY trigger fires → Immediate kill      │
│ Timing: ~0.1 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  Performance     │ → Stats updated, budget optimized
│  Tracked & Live  │    Learning data collected
└──────────────────┘

Webhook Response Time: <200ms total
Budget Update Frequency: Every 4 hours OR every 100 conversions
Kill Switch Check: On every conversion event
```

### CAPI Event Data Structure

```python
CAPIConversionEvent {
    event_id: str              # Unique event ID
    event_name: str            # Purchase, Lead, AddToCart
    event_time: int            # Unix timestamp
    user_data: Dict            # Hashed PII
    custom_data: Dict {        # Conversion details
        value: float           # 79.99
        currency: str          # USD
        content_ids: List      # [variation_id]
        campaign_id: str       # Tracking ID
    }
    event_source_url: str      # Landing page with UTM
    action_source: str         # website, app, email
}
```

---

## 5. LEARNING LOOP FLOW

**Purpose:** Match predictions to actuals, retrain models daily, compound knowledge across campaigns.

### Flow Diagram

```
┌──────────────────┐
│  Daily Trigger   │ ← Cron job at 2 AM
│   (Scheduled)    │    OR manual trigger
└────────┬─────────┘    OR 100+ new data points
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Match Predictions to Actuals                                │
│ File: services/ml-service/src/capi_feedback_loop.py        │
│ Function: match_predictions_to_actuals()                   │
├─────────────────────────────────────────────────────────────┤
│ Query predictions from last 7 days:                        │
│                                                             │
│ SQL:                                                        │
│   SELECT p.*, a.*                                          │
│   FROM prediction_records p                                │
│   JOIN campaign_actuals a                                  │
│     ON p.campaign_id = a.campaign_id                       │
│   WHERE p.created_at >= NOW() - INTERVAL '7 days'          │
│   AND a.conversions > 0                                    │
│                                                             │
│ Create Prediction-Actual Pairs:                            │
│   {                                                         │
│     "prediction_id": "pred_123",                           │
│     "campaign_id": "camp_abc",                             │
│     "creative_id": "var_5",                                │
│                                                             │
│     # What we predicted:                                   │
│     "predicted_ctr": 0.025,                                │
│     "predicted_roas": 2.5,                                 │
│     "predicted_conversions": 15,                           │
│                                                             │
│     # What actually happened:                              │
│     "actual_ctr": 0.0188,                                  │
│     "actual_roas": 6.40,                                   │
│     "actual_conversions": 12,                              │
│     "actual_revenue": 959.88,                              │
│     "actual_spend": 150.00,                                │
│                                                             │
│     # Calculate errors:                                    │
│     "ctr_error": abs(0.025 - 0.0188) = 0.0062,            │
│     "roas_error": abs(2.5 - 6.40) = 3.90,  # Under-pred!  │
│     "conversion_error": abs(15 - 12) = 3,                  │
│                                                             │
│     "timestamp": "2025-12-06T02:00:00Z"                    │
│   }                                                         │
│                                                             │
│ Result: 156 prediction-actual pairs found                  │
│                                                             │
│ Decision Point: If pairs < 100 → Skip retrain (not enough) │
│ Timing: ~1-2 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Error Analysis & Insights                                   │
├─────────────────────────────────────────────────────────────┤
│ Calculate aggregate errors:                                │
│                                                             │
│   avg_ctr_error = mean([0.0062, ...])  = 0.0045  (0.45%)   │
│   avg_roas_error = mean([3.90, ...])   = 1.23    (49%)     │
│   avg_conv_error = mean([3, ...])      = 2.1    (14%)      │
│                                                             │
│ Identify patterns:                                         │
│   - Model tends to under-predict ROAS (good problem!)      │
│   - CTR predictions quite accurate                         │
│   - Conversion count slightly over-predicted               │
│                                                             │
│ Extract learnings:                                         │
│   {                                                         │
│     "model_bias": "conservative_roas",                     │
│     "strongest_feature": "hook_type",                      │
│     "weakest_feature": "color_scheme",                     │
│     "industry_insights": {                                 │
│       "ecommerce": {                                       │
│         "avg_actual_roas": 4.2,  # vs predicted 2.5        │
│         "adjustment_factor": 1.68                          │
│       }                                                     │
│     }                                                       │
│   }                                                         │
│                                                             │
│ Timing: ~0.5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Prepare Training Data                                       │
│ File: services/ml-service/src/auto_retrain_pipeline.py     │
├─────────────────────────────────────────────────────────────┤
│ Convert pairs to ML training format:                       │
│                                                             │
│ Features (X):                                              │
│   [                                                         │
│     {                                                       │
│       "hook_type": "question",      # one-hot encoded      │
│       "cta_urgency": 0.8,           # 0-1 scale            │
│       "duration": 15,               # normalized           │
│       "pacing": "fast",             # one-hot encoded      │
│       "has_face": 1,                # binary               │
│       "color_vibrancy": 0.7,        # calculated           │
│       "industry": "ecommerce",      # one-hot encoded      │
│       "audience_age": "25-45"       # one-hot encoded      │
│     },                                                      │
│     ...  # 156 samples                                     │
│   ]                                                         │
│                                                             │
│ Targets (y):                                               │
│   {                                                         │
│     "ctr": [0.0188, 0.0234, ...],     # 156 values         │
│     "roas": [6.40, 3.2, ...],         # 156 values         │
│     "conversions": [12, 8, ...]       # 156 values         │
│   }                                                         │
│                                                             │
│ Sample Weights (by recency):                               │
│   weight = 1.0 / (1.0 + age_hours / 24)                    │
│   Recent conversions weighted higher                       │
│   [0.95, 0.92, 0.88, ...]  # Decay over time               │
│                                                             │
│ Train/Validation Split:                                    │
│   Training: 125 samples (80%)                              │
│   Validation: 31 samples (20%)                             │
│                                                             │
│ Timing: ~0.5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Model Retraining                                            │
│ File: services/ml-service/src/auto_retrain_pipeline.py     │
│ Function: _train_model()                                   │
├─────────────────────────────────────────────────────────────┤
│ STEP 1: Evaluate Current Model (baseline)                  │
│   Load production model: roas_predictor_v20251205          │
│   Test on validation set                                   │
│   Current accuracy: 0.72 (72% within 20% error)            │
│                                                             │
│ STEP 2: Train New Model                                    │
│   Algorithm: XGBoost Regressor                             │
│   Parameters:                                              │
│     n_estimators: 100                                      │
│     max_depth: 6                                           │
│     learning_rate: 0.1                                     │
│     subsample: 0.8                                         │
│                                                             │
│   Training process:                                        │
│     • Fit on 125 training samples                          │
│     • Apply sample weights (recent data weighted higher)   │
│     • Early stopping on validation set                     │
│                                                             │
│   Training metrics:                                        │
│     Epoch 1:  train_loss=0.85, val_loss=0.91               │
│     Epoch 20: train_loss=0.42, val_loss=0.48               │
│     Epoch 40: train_loss=0.31, val_loss=0.39 ← Best        │
│     Epoch 50: train_loss=0.28, val_loss=0.41 (overfitting) │
│     → Stop at epoch 40                                     │
│                                                             │
│ STEP 3: Validate New Model                                 │
│   Test on validation set (31 samples)                      │
│   New accuracy: 0.78 (78% within 20% error)                │
│   Improvement: +6 percentage points ✓                      │
│                                                             │
│ STEP 4: Compare Models                                     │
│   Old model: 72% accuracy                                  │
│   New model: 78% accuracy                                  │
│   Improvement: 8.3%                                        │
│   Decision: DEPLOY (improvement > 1% threshold)            │
│                                                             │
│ STEP 5: Deploy New Model                                   │
│   Save model: roas_predictor_v20251206_0200                │
│   Update production pointer                                │
│   Archive old model (rollback safety)                      │
│                                                             │
│ Decision Point: If new accuracy < old - 2% → ROLLBACK      │
│ Timing: ~10-15 seconds                                     │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Cross-Campaign Knowledge Update                             │
│ File: services/ml-service/src/cross_campaign_learning.py   │
├─────────────────────────────────────────────────────────────┤
│ Extract winning patterns from recent campaigns:            │
│                                                             │
│ For each high-performing campaign (ROAS > 3.0):            │
│   CampaignLearning {                                       │
│     campaign_id: "camp_abc123"                             │
│     industry: "ecommerce"                                  │
│     objective: "conversions"                               │
│                                                             │
│     winning_patterns: [                                    │
│       {                                                     │
│         "hook_type": "question",                           │
│         "avg_roas": 6.4,                                   │
│         "sample_size": 1                                   │
│       }                                                     │
│     ]                                                       │
│     winning_hooks: [                                       │
│       "Stop scrolling! Tired of dry skin?"                 │
│     ]                                                       │
│     winning_ctas: [                                        │
│       "Shop Now →"                                         │
│     ]                                                       │
│                                                             │
│     best_roas: 6.40                                        │
│     best_ctr: 0.0188                                       │
│     best_cpa: 12.50                                        │
│     confidence_score: 0.85                                 │
│   }                                                         │
│                                                             │
│ Update Industry Insights (running averages):               │
│   industry_insights["ecommerce"]:                          │
│     sample_size: 47 → 48 campaigns                         │
│     avg_roas: 2.8 → 2.87  (weighted average)               │
│     avg_ctr: 0.021 → 0.021                                 │
│     avg_cpa: 35.0 → 34.2                                   │
│     confidence: 0.47 → 0.48                                │
│                                                             │
│ Add to Pattern Database:                                   │
│   pattern_database["winning"]:                             │
│     + Hook: "Stop scrolling! {pain_point}?"                │
│       Performance: 6.4 ROAS                                │
│       Industry: ecommerce                                  │
│       Usage: 1                                             │
│                                                             │
│ Timing: ~1 second                                          │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Retrain Results & Notification                              │
├─────────────────────────────────────────────────────────────┤
│ Summary Report:                                            │
│   {                                                         │
│     "status": "success",                                   │
│     "samples_used": 156,                                   │
│     "old_model_accuracy": 0.72,                            │
│     "new_model_accuracy": 0.78,                            │
│     "improvement": "+8.3%",                                │
│     "model_version": "roas_predictor_v20251206_0200",      │
│     "avg_errors_before": {                                 │
│       "ctr": 0.0045,                                       │
│       "roas": 1.23,                                        │
│       "conversions": 2.1                                   │
│     },                                                      │
│     "campaigns_learned_from": 23,                          │
│     "industries_updated": ["ecommerce", "saas"],           │
│     "next_retrain_eligible": "2025-12-07T02:00:00Z",       │
│     "execution_time": "17.2 seconds"                       │
│   }                                                         │
│                                                             │
│ Actions:                                                   │
│   ✓ Model deployed to production                           │
│   ✓ Industry insights updated                              │
│   ✓ Pattern database enriched                              │
│   ✓ Email notification sent to admin                       │
│   ✓ Slack alert posted                                     │
│                                                             │
│ Timing: ~0.5 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│  System Smarter  │ → Next predictions will be 8.3% better
│   (Compounding)  │    Knowledge compounds across campaigns
└──────────────────┘

Total Retrain Time: ~20-25 seconds
Frequency: Daily at 2 AM OR every 100 new conversions
Improvement Rate: ~2-5% accuracy gain per retrain
```

### Learning Data Structures

**Prediction-Actual Pair:**
```python
{
    "prediction_id": "pred_123",
    "campaign_id": "camp_abc",
    "creative_id": "var_5",

    # Predictions
    "predicted_ctr": 0.025,
    "predicted_roas": 2.5,
    "predicted_conversions": 15,

    # Actuals
    "actual_ctr": 0.0188,
    "actual_roas": 6.40,
    "actual_conversions": 12,

    # Errors
    "ctr_error": 0.0062,
    "roas_error": 3.90,
    "conversion_error": 3,

    "timestamp": "2025-12-06T02:00:00Z"
}
```

---

## 6. BUDGET OPTIMIZATION FLOW

**Purpose:** Automatically shift budget from losers to winners every 4 hours.

### Flow Diagram

```
┌──────────────────┐
│  Trigger Event   │ ← Every 4 hours (cron)
│  (Scheduled or   │    OR 100 conversions
│   On-Demand)     │    OR manual trigger
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Fetch Active Campaigns                                      │
│ File: services/ml-service/src/budget_optimizer.py          │
├─────────────────────────────────────────────────────────────┤
│ Query all active campaigns with recent data:               │
│                                                             │
│ SQL:                                                        │
│   SELECT                                                   │
│     c.campaign_id,                                         │
│     c.daily_budget,                                        │
│     a.impressions,                                         │
│     a.clicks,                                              │
│     a.conversions,                                         │
│     a.revenue,                                             │
│     a.spend,                                               │
│     a.ctr,                                                 │
│     a.cvr,                                                 │
│     a.cpa,                                                 │
│     a.roas,                                                │
│     EXTRACT(EPOCH FROM (NOW() - c.created_at))/3600        │
│       AS hours_active                                      │
│   FROM campaigns c                                         │
│   JOIN campaign_actuals a ON c.campaign_id = a.campaign_id │
│   WHERE c.status = 'active'                                │
│   AND a.date >= CURRENT_DATE - INTERVAL '1 day'            │
│                                                             │
│ Result: 47 active campaigns                                │
│                                                             │
│ Timing: ~0.2 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Categorize Campaigns by Performance                         │
│ Function: analyze_ads()                                    │
├─────────────────────────────────────────────────────────────┤
│ For each campaign, apply categorization logic:             │
│                                                             │
│ LEARNING PHASE (skip optimization):                        │
│   IF hours_active < 24        → learning                   │
│   OR spend < $50              → learning                   │
│   OR conversions < 5          → learning                   │
│                                                             │
│ PERFORMANCE CATEGORIES (for campaigns past learning):      │
│   IF roas >= 3.0 (150% of target 2.0) → WINNERS            │
│   IF roas >= 2.0 AND < 3.0            → STABLE             │
│   IF roas >= 1.0 AND < 2.0            → UNDERPERFORMING    │
│   IF roas < 1.0                       → LOSERS             │
│                                                             │
│ Example categorization of 47 campaigns:                    │
│   {                                                         │
│     "winners": [                                           │
│       {                                                     │
│         "campaign_id": "camp_abc123",                      │
│         "roas": 6.40,                                      │
│         "daily_budget": 150.00,                            │
│         "spend": 142.30,                                   │
│         "conversions": 12                                  │
│       },                                                    │
│       {                                                     │
│         "campaign_id": "camp_def456",                      │
│         "roas": 4.2,                                       │
│         "daily_budget": 200.00,                            │
│         "spend": 195.00,                                   │
│         "conversions": 18                                  │
│       }                                                     │
│       ... 5 more winners (7 total)                         │
│     ],                                                      │
│     "stable": [...],      # 18 campaigns                   │
│     "underperforming": [...],  # 8 campaigns               │
│     "losers": [                                            │
│       {                                                     │
│         "campaign_id": "camp_bad789",                      │
│         "roas": 0.6,                                       │
│         "daily_budget": 100.00,                            │
│         "spend": 98.50,                                    │
│         "conversions": 2                                   │
│       }                                                     │
│       ... 2 more losers (3 total)                          │
│     ],                                                      │
│     "learning": [...]   # 11 campaigns                     │
│   }                                                         │
│                                                             │
│ Timing: ~0.3 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Calculate Budget Shifts                                     │
│ Function: generate_recommendations()                       │
├─────────────────────────────────────────────────────────────┤
│ STEP 1: Calculate available budget from losers             │
│   Total loser budgets:                                     │
│     camp_bad789: $100                                      │
│     camp_bad456: $80                                       │
│     camp_bad123: $60                                       │
│     Total: $240/day                                        │
│                                                             │
│   Budget to reclaim (cut 70%):                             │
│     $240 * 0.70 = $168/day                                 │
│                                                             │
│   Budget from underperforming (cut 30%):                   │
│     8 campaigns * avg $120 = $960/day                      │
│     $960 * 0.30 = $288/day                                 │
│                                                             │
│   Total available to shift: $168 + $288 = $456/day         │
│                                                             │
│ STEP 2: Generate recommendations for LOSERS                │
│   [                                                         │
│     {                                                       │
│       "ad_id": "camp_bad789",                              │
│       "current_budget": 100.00,                            │
│       "recommended_budget": 30.00,  # 70% cut              │
│       "change_amount": -70.00,                             │
│       "change_percent": -70.0,                             │
│       "reason": "ROAS 0.60 below threshold 1.0",           │
│       "confidence": 0.98,                                  │
│       "priority": 1  # Highest priority                    │
│     },                                                      │
│     ... 2 more loser cuts                                  │
│   ]                                                         │
│                                                             │
│ STEP 3: Generate recommendations for WINNERS               │
│   Budget per winner: $456 / 7 = $65 per campaign           │
│   Max increase: 50% of current budget                      │
│                                                             │
│   [                                                         │
│     {                                                       │
│       "ad_id": "camp_abc123",                              │
│       "current_budget": 150.00,                            │
│       "recommended_budget": 215.00,  # +$65 (43% increase) │
│       "change_amount": +65.00,                             │
│       "change_percent": +43.3,                             │
│       "reason": "ROAS 6.40 exceeds scale threshold 3.0",   │
│       "confidence": 0.95,                                  │
│       "priority": 3                                        │
│     },                                                      │
│     {                                                       │
│       "ad_id": "camp_def456",                              │
│       "current_budget": 200.00,                            │
│       "recommended_budget": 265.00,  # +$65 (32% increase) │
│       "change_amount": +65.00,                             │
│       "change_percent": +32.5,                             │
│       "reason": "ROAS 4.20 exceeds scale threshold 3.0",   │
│       "confidence": 0.97,                                  │
│       "priority": 3                                        │
│     },                                                      │
│     ... 5 more winner increases                            │
│   ]                                                         │
│                                                             │
│ STEP 4: Generate recommendations for UNDERPERFORMING       │
│   [                                                         │
│     {                                                       │
│       "ad_id": "camp_meh123",                              │
│       "current_budget": 120.00,                            │
│       "recommended_budget": 84.00,  # 30% cut              │
│       "change_amount": -36.00,                             │
│       "change_percent": -30.0,                             │
│       "reason": "ROAS 1.5 below target 2.0",               │
│       "confidence": 0.75,                                  │
│       "priority": 2                                        │
│     },                                                      │
│     ... 7 more underperforming cuts                        │
│   ]                                                         │
│                                                             │
│ Total recommendations: 18 budget changes                   │
│   3 losers (cut)                                           │
│   7 winners (increase)                                     │
│   8 underperforming (reduce)                               │
│                                                             │
│ Timing: ~0.2 seconds                                       │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Execute Budget Changes via Platform APIs                    │
│ Function: execute_budget_shifts()                          │
├─────────────────────────────────────────────────────────────┤
│ For each recommendation, call platform API:                │
│                                                             │
│ META ADS:                                                  │
│   POST https://graph.facebook.com/v18.0/act_{account}/     │
│        adsets/{adset_id}                                   │
│   Body: {                                                   │
│     "daily_budget": 21500,  # In cents: $215.00           │
│     "status": "ACTIVE"                                     │
│   }                                                         │
│   Headers: {                                               │
│     "Authorization": "Bearer {access_token}"               │
│   }                                                         │
│                                                             │
│ GOOGLE ADS:                                                │
│   POST https://googleads.googleapis.com/v14/customers/     │
│        {customer_id}/campaignBudgets:mutate                │
│   Body: {                                                   │
│     "operations": [{                                       │
│       "update": {                                          │
│         "resourceName": "campaignBudgets/123",             │
│         "amountMicros": 215000000  # In micros: $215.00    │
│       },                                                    │
│       "updateMask": "amountMicros"                         │
│     }]                                                      │
│   }                                                         │
│                                                             │
│ For our 18 changes:                                        │
│   ✓ camp_abc123: $150 → $215 (Meta API)                    │
│   ✓ camp_def456: $200 → $265 (Google API)                  │
│   ✓ camp_bad789: $100 → $30 (Meta API)                     │
│   ... 15 more updates                                      │
│                                                             │
│ Error handling:                                            │
│   - Retry failed updates (3 attempts)                      │
│   - Log all changes to audit trail                         │
│   - Send alerts on failures                                │
│                                                             │
│ Timing: ~5-8 seconds (parallel API calls)                  │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ Update Database & Generate Report                           │
├─────────────────────────────────────────────────────────────┤
│ Update campaign records:                                   │
│   UPDATE campaigns                                         │
│   SET daily_budget = 215.00,                               │
│       last_budget_change = NOW(),                          │
│       budget_change_reason = 'auto_optimization'           │
│   WHERE campaign_id = 'camp_abc123'                        │
│                                                             │
│ Log budget shift event:                                    │
│   INSERT INTO budget_shift_history                         │
│   (campaign_id, old_budget, new_budget, reason, timestamp) │
│   VALUES ('camp_abc123', 150, 215, 'ROAS 6.40', NOW())     │
│                                                             │
│ Generate optimization report:                              │
│   {                                                         │
│     "successful": true,                                    │
│     "changes_made": [                                      │
│       {                                                     │
│         "ad_id": "camp_abc123",                            │
│         "old_budget": 150.00,                              │
│         "new_budget": 215.00,                              │
│         "change": +65.00,                                  │
│         "reason": "ROAS 6.40 exceeds scale threshold"      │
│       },                                                    │
│       ... 17 more                                          │
│     ],                                                      │
│     "total_budget_shifted": 456.00,                        │
│     "expected_impact": {                                   │
│       "estimated_roas_improvement": 0.3,  # +30%           │
│       "estimated_daily_savings": 304.00,  # From cuts      │
│       "estimated_daily_revenue_increase": 650.00           │
│     },                                                      │
│     "distribution": {                                      │
│       "winners": 7,                                        │
│       "stable": 18,                                        │
│       "underperforming": 8,                                │
│       "losers": 3,                                         │
│       "learning": 11                                       │
│     },                                                      │
│     "execution_time": "2025-12-06T10:00:15Z",              │
│     "next_optimization": "2025-12-06T14:00:00Z"            │
│   }                                                         │
│                                                             │
│ Send notifications:                                        │
│   ✓ Email to account manager                               │
│   ✓ Slack alert to #ad-optimization                        │
│   ✓ Dashboard updated in real-time                         │
│                                                             │
│ Timing: ~1 second                                          │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│ Budgets Optimized│ → Winners get more, losers get less
│   (Automatic)    │    ROI maximized automatically
└──────────────────┘

Total Optimization Time: ~7-12 seconds
Frequency: Every 4 hours (6x per day)
Budget Movement: ~$450-500/day shifted from losers to winners
Expected Impact: +20-30% ROAS improvement
```

### Budget Shift Decision Matrix

| ROAS Range | Category | Budget Action | Amount | Priority |
|------------|----------|---------------|--------|----------|
| >= 3.0 | Winner | INCREASE | +50% (max $50/day) | 3 |
| 2.0 - 3.0 | Stable | MAINTAIN | No change | - |
| 1.0 - 2.0 | Underperforming | REDUCE | -30% | 2 |
| < 1.0 | Loser | CUT | -70% (min $10/day) | 1 |
| < 24hr OR <$50 | Learning | SKIP | No change | - |

### Budget Shift Data Structure

```python
BudgetRecommendation {
    ad_id: str                    # Campaign ID
    current_budget: float         # Current daily budget
    recommended_budget: float     # New daily budget
    change_amount: float          # $ change (can be negative)
    change_percent: float         # % change
    reason: str                   # Why this change
    confidence: float             # 0-1 confidence score
    priority: int                 # 1=highest (losers), 3=lowest (winners)
}
```

---

## 7. COMPLETE SYSTEM FLOW

**End-to-end flow from concept to optimized campaigns:**

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INITIATES CAMPAIGN                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  1. CREATIVE INPUT   │
              │  - Product info      │
              │  - Target audience   │
              │  - Budget            │
              │  - Video upload      │
              └──────────┬───────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  2. VIDEO ANALYSIS (12-22 sec)    │
         │  ┌─────────────────────────────┐  │
         │  │ Motion Moment SDK           │  │
         │  │ Face Detection              │  │
         │  │ Hook Optimization           │  │
         │  │ Audio Sync                  │  │
         │  │ Pattern Extraction          │  │
         │  └─────────────────────────────┘  │
         └───────────────┬───────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  3. VARIATION GENERATION (4-6s)   │
         │  ┌─────────────────────────────┐  │
         │  │ Cross-Learning Lookup       │  │
         │  │ Generate 50 Variations      │  │
         │  │ ML Performance Prediction   │  │
         │  │ Rank & Select Top 10        │  │
         │  └─────────────────────────────┘  │
         └───────────────┬───────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  4. VIDEO RENDERING (5-10 min)    │
         │  ┌─────────────────────────────┐  │
         │  │ Render 10 Variations        │  │
         │  │ Apply Text Overlays         │  │
         │  │ Add CTAs                    │  │
         │  │ Export to S3/CDN            │  │
         │  └─────────────────────────────┘  │
         └───────────────┬───────────────────┘
                         │
                         ▼
         ┌───────────────────────────────────┐
         │  5. AD PUBLISHING (60-90 sec)     │
         │  ┌─────────────────────────────┐  │
         │  │ Upload to Meta Ads          │  │
         │  │ Upload to Google Ads        │  │
         │  │ Upload to TikTok Ads        │  │
         │  │ Set Budgets & Launch        │  │
         │  └─────────────────────────────┘  │
         └───────────────┬───────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  CAMPAIGNS LIVE      │
              │  (Ads Running)       │
              └──────────┬───────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│  CONTINUOUS LOOPS   │      │  SCHEDULED JOBS     │
│  (Real-time)        │      │  (Daily/4-hourly)   │
└──────────┬──────────┘      └──────────┬──────────┘
           │                            │
           ▼                            ▼
┌──────────────────────┐    ┌──────────────────────┐
│ 6. PERFORMANCE       │    │ 7. LEARNING LOOP     │
│    TRACKING          │    │    (Daily 2 AM)      │
│                      │    │                      │
│ • CAPI Webhooks      │    │ • Match Predictions  │
│ • Conversion Events  │    │ • Calculate Errors   │
│ • Update Actuals     │    │ • Retrain Models     │
│ • Real-time Metrics  │    │ • Update Insights    │
│                      │    │                      │
│ Frequency: Real-time │    │ Frequency: Daily     │
│ Latency: <200ms      │    │ Duration: ~20-25s    │
└──────────┬───────────┘    └──────────┬───────────┘
           │                            │
           ▼                            │
┌──────────────────────┐                │
│ 8. BUDGET OPTIMIZER  │                │
│    (Every 4 hours)   │                │
│                      │                │
│ • Categorize Ads     │◄───────────────┘
│ • Calculate Shifts   │  (Uses improved models)
│ • Execute Changes    │
│ • Generate Reports   │
│                      │
│ Frequency: 6x/day    │
│ Duration: ~7-12s     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 9. KILL SWITCH       │
│    (Every conversion)│
│                      │
│ • Check Thresholds   │
│ • Pause Bad Ads      │
│ • Prevent Waste      │
│                      │
│ Frequency: Real-time │
│ Decision: <100ms     │
└──────────────────────┘
           │
           │
           ▼
     ┌─────────┐
     │  LOOP   │ ─── Continuous improvement
     │ FOREVER │      Compounding knowledge
     └─────────┘      Automated optimization
```

---

## Key Metrics & Timing Summary

| Flow | Duration | Frequency | Data Volume |
|------|----------|-----------|-------------|
| Video Analysis | 12-22 sec | Per upload | 1 video → 10-20 moments |
| Variation Generation | 4-6 sec | Per concept | 1 concept → 50 variations |
| Ad Publishing | 60-90 sec | Per campaign | 10 videos → 30 ads |
| Performance Tracking | <200ms | Real-time | ~1000 events/day |
| Learning Loop | 20-25 sec | Daily (2 AM) | 100-200 pairs |
| Budget Optimization | 7-12 sec | Every 4 hours | 40-50 campaigns |
| Kill Switch | <100ms | Per conversion | ~50 evaluations/day |

---

## Data Retention & Archival

| Data Type | Retention | Archive Strategy |
|-----------|-----------|------------------|
| Video files | 90 days | Move to Glacier after 30 days |
| Performance data | Forever | Partition by month |
| Prediction records | Forever | Training data |
| CAPI events | 2 years | Compressed JSON |
| Model versions | 10 versions | Keep top 10, delete rest |
| Budget history | Forever | Audit trail |

---

## Error Handling & Alerts

### Critical Errors (Page immediately)
- CAPI webhook down (>5 min)
- Budget API calls failing (>50%)
- Kill switch malfunction
- Model deployment failed

### Warning Alerts (Email + Slack)
- Prediction accuracy drop >10%
- Budget shift execution <80% success
- Video rendering queue >100 items
- Learning loop skipped (insufficient data)

### Info Alerts (Dashboard only)
- Optimization completed
- Model retrained
- New industry insights
- Pattern database updated

---

## Security & Privacy

### PII Handling (CAPI Events)
- All PII is hashed before storage (SHA-256)
- Email: `hash(lowercase_trim(email))`
- Phone: `hash(digits_only(phone))`
- IP addresses: Anonymized after 7 days

### API Keys
- Stored in encrypted vault (AWS Secrets Manager)
- Rotated every 90 days
- Separate keys per environment

### Data Access
- All queries logged
- Row-level security on campaigns
- Users see only their campaigns
- Admin access audit trail

---

## Monitoring Endpoints

```
GET /api/v1/health/video-analysis
GET /api/v1/health/variation-generator
GET /api/v1/health/capi-webhook
GET /api/v1/health/budget-optimizer
GET /api/v1/health/learning-loop
GET /api/v1/health/kill-switch

GET /api/v1/metrics/performance-tracking
GET /api/v1/metrics/budget-optimization
GET /api/v1/metrics/model-accuracy
```

---

**Document maintained by:** GeminiVideo Engineering Team
**Questions?** Contact: engineering@geminivideo.com
**Last reviewed:** 2025-12-06
