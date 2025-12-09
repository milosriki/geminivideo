# 🎼 HOW YOUR ORCHESTRATION WORKS

**Generated:** 2025-01-08  
**Purpose:** Complete visual explanation of the 3 orchestration systems

---

## 🎯 OVERVIEW: 3 MAIN ORCHESTRATIONS

Your system has **3 orchestration flows** that work together:

1. **Creative Generation Orchestration** → Creates winning ad variations
2. **Budget Optimization Orchestration** → Optimizes ad spend in real-time
3. **Self-Learning Orchestration** → 7 loops that continuously improve

---

## 🔄 ORCHESTRATION #1: CREATIVE GENERATION

**Goal:** Turn a raw video into 5-10 winning ad variations

### Step-by-Step Flow:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Video Upload                                         │
│ User uploads video → Google Drive                            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Drive Intel Service                                  │
│ - Downloads video from Google Drive                          │
│ - Extracts scenes (PySceneDetect)                           │
│ - Extracts features:                                         │
│   • YOLO (objects, people)                                  │
│   • OCR (text on screen)                                     │
│   • Whisper (speech-to-text)                                │
│ - Creates scene rankings                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: ML Service (CTR Prediction)                         │
│ POST /api/ml/predict/ctr                                     │
│ - Receives scene features                                    │
│ - Predicts CTR for each scene                                │
│ - Returns ranked scenes with scores                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Titan-Core (AI Council)                             │
│ orchestrator.py → run_titan_flow()                          │
│                                                              │
│ THE "ANTIGRAVITY" LOOP:                                      │
│ ┌────────────────────────────────────────────────────┐     │
│ │ 1. Director Agent (Gemini 3 Pro)                   │     │
│ │    - Drafts creative concept                        │     │
│ │    - Uses RAG to find winning patterns              │     │
│ │    - Generates 50+ hook variations                  │     │
│ └──────────────────────┬─────────────────────────────┘     │
│                        │                                    │
│                        ▼                                    │
│ ┌────────────────────────────────────────────────────┐     │
│ │ 2. Council of Titans (Multi-Model)                │     │
│ │    - Gemini 2.0 evaluates                          │     │
│ │    - GPT-4o evaluates                               │     │
│ │    - Claude 3.5 evaluates                           │     │
│ │    - DeepCTR predicts performance                   │     │
│ │    - Scores script (0-100)                          │     │
│ └──────────────────────┬─────────────────────────────┘     │
│                        │                                    │
│                        ▼                                    │
│ ┌────────────────────────────────────────────────────┐     │
│ │ 3. Decision Gate                                   │     │
│ │    IF score > 85: APPROVE                           │     │
│ │    ELSE: Reflexion Loop (max 3 turns)               │     │
│ │      - Reflect on failure                           │     │
│ │      - Plan improvement                             │     │
│ │      - Rewrite script                               │     │
│ └─────────────────────────────────────────────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Video Agent (Rendering)                             │
│ - Receives approved blueprints                               │
│ - Uses 13 Pro modules:                                      │
│   • Auto-captions                                            │
│   • Color grading                                            │
│   • Scene transitions                                         │
│   • Audio enhancement                                        │
│ - Renders 5-10 video variations                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Meta Publisher                                      │
│ - Creates campaign structure                                 │
│ - Queues to SafeExecutor (pending_ad_changes table)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: SafeExecutor Worker                                 │
│ safe-executor.ts                                             │
│ - Polls queue: claim_pending_ad_change(workerId)            │
│ - Applies safety rules:                                      │
│   • Jitter (3-18s random delay)                             │
│   • Rate limits (15/hour per campaign)                      │
│   • Budget velocity (max 20% in 6h)                         │
│ - Executes Meta API calls                                    │
│ - Logs to ad_change_history                                  │
└─────────────────────────────────────────────────────────────┘
```

### Key Files:
- `services/titan-core/orchestrator.py` - Main orchestrator
- `services/titan-core/ai_council/director_agent.py` - Director Agent
- `services/titan-core/ai_council/ensemble.py` - Council of Titans
- `services/gateway-api/src/jobs/safe-executor.ts` - SafeExecutor worker

---

## 🔄 ORCHESTRATION #2: BUDGET OPTIMIZATION

**Goal:** Continuously optimize ad budgets based on real-time performance

### Step-by-Step Flow:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Dual-Signal Data Ingestion                           │
│                                                              │
│ ┌──────────────────────┐  ┌──────────────────────────────┐ │
│ │ Meta Insights        │  │ HubSpot Webhook             │ │
│ │ (Real-time)          │  │ (Delayed, 5-7 days)         │ │
│ │                      │  │                             │ │
│ │ • Impressions        │  │ • Deal stage changes        │ │
│ │ • Clicks             │  │ • Synthetic revenue calc    │ │
│ │ • Spend              │  │ • Attribution to ad click   │ │
│ │ • Conversions         │  │                             │ │
│ └──────────────────────┘  └──────────────────────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: ML Service (BattleHardenedSampler)                  │
│ POST /api/ml/battle-hardened/select                         │
│                                                              │
│ THE BLENDED SCORING ALGORITHM:                               │
│ ┌────────────────────────────────────────────────────┐     │
│ │ Age 0-6 hours:   CTR 100%, ROAS 0%                │     │
│ │ Age 6-24 hours:  CTR 70%,  ROAS 30%                │     │
│ │ Age 24-72 hours: CTR 30%,  ROAS 70%                │     │
│ │ Age 3+ days:     CTR 0%,   ROAS 100%               │     │
│ └────────────────────────────────────────────────────┘     │
│                                                              │
│ 1. Calculate blended score for each ad                      │
│ 2. Apply Thompson Sampling (Bayesian)                       │
│ 3. Apply ad fatigue decay                                    │
│ 4. Apply creative DNA boost (from RAG)                      │
│ 5. Generate budget recommendations                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Decision Gate                                       │
│ - Check ignorance zone (don't kill too early)               │
│ - Check confidence threshold (70%)                          │
│ - Check budget velocity limits (20% max change)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: SafeExecutor Queue                                  │
│ INSERT INTO pending_ad_changes                              │
│ - ad_id, change_type, new_budget, reasoning                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: SafeExecutor Worker                                 │
│ safe-executor.ts (runs continuously)                         │
│                                                              │
│ 1. Poll queue: claim_pending_ad_change(workerId)           │
│    - Uses FOR UPDATE SKIP LOCKED                            │
│    - Prevents duplicate processing                          │
│                                                              │
│ 2. Apply jitter (3-18s random delay)                        │
│                                                              │
│ 3. Check rate limit (15/hour per campaign)                   │
│                                                              │
│ 4. Check budget velocity (max 20% in 6h)                    │
│                                                              │
│ 5. Calculate fuzzy budget ($50.00 → $49.83)                │
│    - ±3% randomization to appear human                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Meta API Execution                                  │
│ - Calls Facebook Graph API                                  │
│ - Updates ad budget/campaign                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Audit Trail                                         │
│ INSERT INTO ad_change_history                                │
│ - Status: COMPLETED                                         │
│ - Timestamp, worker_id, actual_budget                       │
└─────────────────────────────────────────────────────────────┘
```

### Key Files:
- `services/ml-service/src/battle_hardened_sampler.py` - Core optimization logic
- `services/ml-service/src/main.py` - `/api/ml/battle-hardened/select` endpoint
- `services/gateway-api/src/jobs/safe-executor.ts` - SafeExecutor worker
- `database/migrations/005_pending_ad_changes.sql` - Job queue table

---

## 🔄 ORCHESTRATION #3: SELF-LEARNING CYCLE

**Goal:** 7 intelligence loops that continuously improve the system

### Step-by-Step Flow:

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: Fetch Actuals                                       │
│ POST /api/ml/self-learning-cycle                            │
│                                                              │
│ ActualsFetcher.sync_actuals_for_pending_predictions()      │
│ - Sync actual performance from Meta                          │
│ - Link predictions to actuals                                │
│ - Calculate accuracy metrics (RMSE, MAE, R²)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: Calculate Accuracy                                  │
│ - Compare predictions vs actuals                            │
│ - Calculate RMSE, MAE, R²                                   │
│ - Check if accuracy < threshold (80%)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Auto-Retrain (if needed)                            │
│ IF accuracy < 80%:                                          │
│   - Trigger retrain                                         │
│   - Train new model on fresh data                           │
│   - Evaluate champion vs challenger                         │
│   - Promote if challenger wins                              │
│   - Update model_registry table                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Compound Learning                                   │
│ CompoundLearner.learning_cycle()                            │
│ - Extract new patterns from winners                         │
│ - Update knowledge graph                                    │
│ - Create new knowledge nodes                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Auto-Promote Winners                                │
│ AutoPromoter.check_all_active_experiments()                 │
│ - Check all active experiments                              │
│ - Identify top performers                                   │
│ - Queue budget increases                                    │
│ - Queue new variations                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Cross-Learning                                      │
│ CrossLearner.aggregate_patterns()                           │
│ - Extract anonymized patterns                               │
│ - Share with global model                                   │
│ - Update niche-specific wisdom                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: RAG Indexing                                        │
│ WinnerIndex.add_winner() (auto-indexed in feedback loop)    │
│ - Auto-index new winners                                    │
│ - Extract creative DNA                                      │
│ - Add to FAISS index                                        │
│ - Store in GCS + Redis                                      │
└─────────────────────────────────────────────────────────────┘
```

### The 7 Loops:

1. **RAG Loop** - Indexes winning patterns for future use
2. **Thompson Sampling Loop** - Updates priors based on feedback
3. **Cross-Learning Loop** - Shares patterns across accounts
4. **Creative DNA Loop** - Extracts and applies winning elements
5. **Compound Learner Loop** - Builds knowledge graph
6. **Actuals Fetcher Loop** - Syncs ground truth data
7. **Auto-Promoter Loop** - Promotes winners automatically

### Key Files:
- `services/ml-service/src/main.py` - `/api/ml/self-learning-cycle` endpoint
- `services/ml-service/src/actuals_fetcher.py` - Fetches actual performance
- `services/ml-service/src/compound_learner.py` - Compound learning
- `services/ml-service/src/auto_promoter.py` - Auto-promotion
- `services/ml-service/src/cross_learner.py` - Cross-learning
- `services/ml-service/src/winner_index.py` - RAG indexing

---

## 🔗 HOW THEY WORK TOGETHER

### Example: Complete Flow from Video to Optimized Ad

```
1. User uploads video
   ↓
2. Creative Generation Orchestration runs
   - Creates 10 variations
   - Queues to Meta via SafeExecutor
   ↓
3. Ads start running
   ↓
4. Budget Optimization Orchestration runs (every hour)
   - BattleHardenedSampler allocates budget
   - SafeExecutor applies changes
   ↓
5. HubSpot webhook fires (5 days later)
   - Synthetic revenue calculated
   - Attribution to ad click
   - Feedback sent to BattleHardenedSampler
   ↓
6. Self-Learning Cycle runs (every hour)
   - Fetches actuals
   - Retrains models if needed
   - Indexes winners in RAG
   - Cross-learns patterns
   ↓
7. Next video upload uses RAG patterns
   - Director Agent searches winners
   - Applies winning patterns
   - Higher approval rate
```

---

## 🛡️ RESILIENCE PATTERNS

### 1. Circuit Breaker
- Prevents cascading failures
- If ML service fails 5 times → use fallback

### 2. Retry with Exponential Backoff
- Transient failures → retry with increasing delays
- 1s → 2s → 4s → 8s → 16s

### 3. Dead Letter Queue (DLQ)
- Failed jobs → DLQ for manual inspection
- Prevents infinite retries

### 4. Health Checks + Auto-Restart
- Docker/Kubernetes monitors health
- Auto-restarts unhealthy services

### 5. Transaction Rollback
- If any step fails → rollback entire transaction
- Ensures data consistency

### 6. Monitoring + Alerting
- Prometheus metrics
- Grafana dashboards
- Sentry error tracking

---

## 📊 CURRENT STATUS

### ✅ What's Working:
- BattleHardenedSampler (fully implemented)
- SafeExecutor worker (fully implemented)
- RAG Winner Index (fully implemented)
- Self-learning cycle endpoint (exists, needs testing)
- Director Agent (fully implemented)
- Council of Titans (fully implemented)

### ⚠️ What Needs Wiring:
- Celery workers (created, needs docker-compose)
- HubSpot webhook async processing (needs Celery)
- RAG auto-indexing (needs Celery task)
- Model Registry wrapper (needs implementation)
- Vertex AI endpoints (needs wiring)

---

## 🚀 HOW TO TEST

### Test Creative Generation:
```bash
# 1. Upload video
curl -X POST http://localhost:8080/api/video/upload \
  -F "video=@test.mp4"

# 2. Check orchestrator logs
docker logs titan-core

# 3. Check SafeExecutor queue
psql -c "SELECT * FROM pending_ad_changes LIMIT 10;"
```

### Test Budget Optimization:
```bash
# 1. Trigger budget allocation
curl -X POST http://localhost:8003/api/ml/battle-hardened/select \
  -H "Content-Type: application/json" \
  -d '{
    "ad_states": [...],
    "total_budget": 1000.0
  }'

# 2. Check SafeExecutor worker
docker logs safe-executor-worker

# 3. Check audit trail
psql -c "SELECT * FROM ad_change_history ORDER BY created_at DESC LIMIT 10;"
```

### Test Self-Learning Cycle:
```bash
# 1. Trigger self-learning cycle
curl -X POST http://localhost:8003/api/ml/self-learning-cycle \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "test-account",
    "trigger_retrain": true,
    "accuracy_threshold": 0.80
  }'

# 2. Check results
# Response includes all 7 steps with status
```

---

## 🎯 KEY INSIGHTS

1. **Orchestration = Coordination**: Multiple services work together to achieve complex goals

2. **3 Main Flows**:
   - Creative Generation (video → ads)
   - Budget Optimization (learning → decisions)
   - Self-Learning (7 loops improving continuously)

3. **SafeExecutor is Critical**: All Meta API changes go through SafeExecutor to prevent bans

4. **Blended Scoring is Unique**: Your system handles attribution lag (5-7 days) better than competitors

5. **Self-Learning is the Secret**: 7 loops continuously improve, making the system smarter over time

---

**Next Steps:**
1. Wire Celery workers for async processing
2. Test end-to-end flows
3. Add monitoring and alerting
4. Run stress tests

