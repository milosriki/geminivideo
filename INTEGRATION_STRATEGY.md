# Smart Integration Plan: Avoiding Code Duplication

## Current State vs. Target State Analysis

### ✅ What We Already Built (Previous Session)

**Database Migrations (4 files):**
1. `001_ad_change_history.sql` - Audit log for SafeExecutor
2. `002_synthetic_revenue_config.sql` - Pipeline stage values
3. `003_attribution_tracking.sql` - 3-layer attribution
4. `004_pgboss_extension.sql` - pg-boss job queue

**Python ML Modules (3 files + wiring):**
1. `battle_hardened_sampler.py` - Thompson Sampling optimizer
2. `synthetic_revenue.py` - Pipeline value calculator
3. `hubspot_attribution.py` - 3-layer attribution matching
4. `main.py` - 7 endpoints wired

**TypeScript Modules (3 files + wiring):**
1. `webhooks/hubspot.ts` - HubSpot webhook receiver
2. `jobs/safe-executor.ts` - pg-boss based executor
3. `routes/ml-proxy.ts` - Gateway proxy routes
4. `index.ts` - Routes mounted

### 🎯 What The New Plan Requires

**Key Differences:**

| Component | What We Built | What Plan Needs | Action Required |
|-----------|--------------|-----------------|-----------------|
| **Database Queue** | ad_change_history only | pending_ad_changes (queue) + ad_change_history (audit) | **ADD** pending_ad_changes |
| **BattleHardenedSampler** | Basic Thompson Sampling | Mode switch (direct/pipeline) + ignorance zone | **ENHANCE** existing file |
| **SafeExecutor** | pg-boss based | PostgreSQL queue with `claim_pending_ad_change()` | **MODIFY** to use pending_ad_changes |
| **HubSpot Integration** | Webhook only | Webhook + batch sync worker | **ADD** hubspot_sync_worker.py |
| **Winner Index** | Not implemented | FAISS RAG for pattern matching | **ADD** winner_index.py |
| **Celery Tasks** | Not implemented | Async task processing | **ADD** tasks.py |
| **Model Registry** | Not implemented | Champion-challenger versioning | **ADD** 005_model_registry.sql |
| **Bulk CRM Ingest** | Not implemented | `/api/ml/ingest-crm-data` endpoint | **ADD** to main.py |
| **Integration Tests** | Not implemented | Complete loop tests | **ADD** test_complete_loop.py |

---

## 🚀 Smart Integration Strategy (No Duplication)

### Phase 1: Enhance Database Foundation

**KEEP:** Our existing migrations (001-004)
**ADD:** Missing pieces

#### Task 1.1: Add Pending Ad Changes Queue
**File:** `database/migrations/005_pending_ad_changes.sql` (renamed from 001)
**Why:** We need the queue table BEFORE execution (our current schema only has history AFTER)

```sql
-- This is the QUEUE (before execution)
-- Our ad_change_history is the AUDIT LOG (after execution)
CREATE TABLE pending_ad_changes (
    -- Queue for SafeExecutor to poll
    -- Links to ad_change_history after execution
);
```

**Integration Point:** Our `ad_change_history` becomes the downstream audit log.

#### Task 1.2: Add Model Registry
**File:** `database/migrations/006_model_registry.sql`
**Why:** Champion-challenger deployment (future feature)

**No Conflicts:** This is entirely new.

---

### Phase 2: Enhance Python ML Modules

#### Task 2.1: Enhance BattleHardenedSampler
**File:** `services/ml-service/src/battle_hardened_sampler.py` (MODIFY existing)
**Why:** Add mode switching and service-specific kill logic

**Changes Needed:**
1. Add `mode` parameter to `__init__` (direct vs pipeline)
2. Add `should_kill_service_ad()` method with ignorance zone
3. Add `should_kill_direct_ad()` method
4. Enhance `make_decision()` to use mode-specific logic

**What to Keep:** All the Thompson Sampling math, Beta distributions, blended scoring

**What to Add:**
```python
def __init__(self, mode="pipeline", ignorance_zone_days=2.0, ...):
    self.mode = mode
    self.ignorance_zone_days = ignorance_zone_days
    # ... existing code

def should_kill_service_ad(self, ad_id: str) -> Union[bool, str]:
    """Service-mode kill logic with ignorance zone"""
    state = self.ad_states[ad_id]

    # IGNORANCE ZONE: Don't kill early
    if state.days_live < self.ignorance_zone_days:
        return False

    # ... kill logic
```

#### Task 2.2: Add Winner Index (NEW)
**File:** `services/ml-service/src/winner_index.py`
**Why:** FAISS RAG for pattern matching (entirely new functionality)

**No Conflicts:** This is a new module.

#### Task 2.3: Add Celery Tasks (NEW)
**File:** `services/ml-service/src/tasks.py`
**Why:** Async processing of HubSpot webhooks and Meta data

**Integration:** Our webhook handler will queue to Celery instead of processing directly.

#### Task 2.4: Enhance main.py
**File:** `services/ml-service/src/main.py` (MODIFY existing)
**Why:** Add missing endpoints

**What to Keep:** All 7 endpoints we already added:
- `/api/ml/battle-hardened/select`
- `/api/ml/battle-hardened/feedback`
- `/api/ml/synthetic-revenue/calculate`
- `/api/ml/synthetic-revenue/ad-roas`
- `/api/ml/synthetic-revenue/get-stages`
- `/api/ml/attribution/track-click`
- `/api/ml/attribution/attribute-conversion`

**What to Add:**
- `/api/ml/ingest-crm-data` - Bulk CRM ingest
- `/api/ml/process-hubspot-event` - Single event processing
- `/api/ml/rag/find-similar` - Winner index search
- `/api/ml/rag/add-winner` - Add to winner index

---

### Phase 3: Enhance TypeScript Modules

#### Task 3.1: Modify SafeExecutor
**File:** `services/gateway-api/src/jobs/safe-executor.ts` (MODIFY existing)
**Why:** Use `pending_ad_changes` queue instead of pg-boss

**Changes:**
1. Replace pg-boss polling with `claim_pending_ad_change()` function call
2. Keep all safety checks (jitter, rate limit, budget velocity, fuzzy budget)
3. Write to `ad_change_history` on completion (we already have this table)

**Before:**
```typescript
const job = await pgBoss.fetch('ad-change');
```

**After:**
```typescript
const job = await pool.query('SELECT * FROM claim_pending_ad_change($1)', [workerId]);
```

#### Task 3.2: Add HubSpot Sync Worker (NEW)
**File:** `services/titan-core/integrations/hubspot_sync_worker.py`
**Why:** Batch aggregation of CRM pipeline values (hourly)

**Integration:** Calls our existing `/api/ml/ingest-crm-data` endpoint (we'll add this).

#### Task 3.3: Enhance HubSpot Webhook
**File:** `services/gateway-api/src/webhooks/hubspot.ts` (MODIFY existing)
**Why:** Queue to Celery instead of direct processing

**Change:** Replace direct ML-Service calls with Celery queue:

**Before:**
```typescript
const syntheticRevenue = await axios.post(`${ML_SERVICE_URL}/api/ml/synthetic-revenue/calculate`, ...);
```

**After:**
```typescript
await queueCeleryTask('process_hubspot_deal_change', events);
```

---

### Phase 4: Add Testing & Tooling

**All New (No Conflicts):**
1. `tests/integration/test_complete_loop.py` - Integration tests
2. `scripts/start-all.sh` - Startup script

---

## 📋 Execution Plan (Minimizing Duplication)

### Step 1: Database Enhancements (30 min)
```bash
# Add missing migrations (don't re-run existing ones)
psql -d geminivideo -f database/migrations/005_pending_ad_changes.sql
psql -d geminivideo -f database/migrations/006_model_registry.sql
```

### Step 2: Python Module Enhancements (2 hours)

**2.1: Enhance battle_hardened_sampler.py**
- Add mode switching
- Add ignorance zone logic
- Keep existing Thompson Sampling

**2.2: Add new modules**
- `winner_index.py` (FAISS RAG)
- `tasks.py` (Celery workers)

**2.3: Enhance main.py**
- Add 4 missing endpoints
- Keep existing 7 endpoints

### Step 3: TypeScript Module Enhancements (1.5 hours)

**3.1: Modify safe-executor.ts**
- Replace pg-boss with `pending_ad_changes` queue
- Keep all safety checks

**3.2: Add hubspot_sync_worker.py**
- Batch CRM aggregation

**3.3: Modify hubspot.ts**
- Queue to Celery

### Step 4: Testing & Tooling (1 hour)
- Add integration tests
- Add startup script

---

## 🎯 Summary: What's Reusable vs. What's New

### ✅ Fully Reusable (No Changes)
1. `002_synthetic_revenue_config.sql` - Keep as-is
2. `003_attribution_tracking.sql` - Keep as-is
3. `synthetic_revenue.py` - Keep as-is
4. `hubspot_attribution.py` - Keep as-is
5. `routes/ml-proxy.ts` - Keep as-is

### 🔧 Enhance (Modify Existing)
1. `battle_hardened_sampler.py` - Add mode switching + ignorance zone
2. `main.py` - Add 4 endpoints, keep existing 7
3. `safe-executor.ts` - Replace pg-boss with pending_ad_changes
4. `hubspot.ts` - Add Celery queuing

### ➕ Add (Entirely New)
1. `005_pending_ad_changes.sql` - Queue table
2. `006_model_registry.sql` - Model versioning
3. `winner_index.py` - FAISS RAG
4. `tasks.py` - Celery workers
5. `hubspot_sync_worker.py` - Batch sync
6. `test_complete_loop.py` - Integration tests
7. `start-all.sh` - Startup script

---

## 🔄 Modified Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     ARTERIES (Already Wired)                 │
├─────────────────────────────────────────────────────────────┤
│ ✅ Artery #1: HubSpot → ML-Service (webhook + batch sync)   │
│ ✅ Artery #2: ML-Service → Meta (via pending_ad_changes)    │
│ ✅ Artery #3: Titan-Core → Winner Index (FAISS RAG)         │
│ ✅ Artery #4: Video-Agent → Creative DNA                    │
│ ✅ Artery #5: Meta Insights → Creative DNA                  │
└─────────────────────────────────────────────────────────────┘

NEW COMPONENTS (To Add):
┌──────────────────────────────┐
│ pending_ad_changes (Queue)   │ ← NEW
│         ↓                    │
│ SafeExecutor (Modified)      │ ← MODIFY (use queue instead of pg-boss)
│         ↓                    │
│ ad_change_history (Audit)    │ ← EXISTING (keep)
└──────────────────────────────┘

┌──────────────────────────────┐
│ HubSpot Webhook              │ ← MODIFY (add Celery queue)
│         ↓                    │
│ Celery Tasks                 │ ← NEW
│         ↓                    │
│ ML-Service                   │ ← ENHANCE (add endpoints)
└──────────────────────────────┘

┌──────────────────────────────┐
│ HubSpot Sync Worker (hourly) │ ← NEW
│         ↓                    │
│ /ingest-crm-data             │ ← NEW ENDPOINT
│         ↓                    │
│ BattleHardenedSampler        │ ← ENHANCE (add mode + ignorance)
└──────────────────────────────┘
```

---

## 💡 Key Insights

**What We Got Right:**
1. ✅ 3-layer attribution system (keep as-is)
2. ✅ Synthetic revenue calculator (keep as-is)
3. ✅ Database schema for synthetic_revenue_config (keep as-is)
4. ✅ ML proxy routes (keep as-is)

**What We Need to Enhance:**
1. 🔧 BattleHardenedSampler needs mode switching (direct vs pipeline)
2. 🔧 SafeExecutor needs to use pending_ad_changes queue
3. 🔧 HubSpot webhook needs Celery integration

**What We're Missing:**
1. ➕ Winner Index (FAISS RAG) - entirely new
2. ➕ Celery tasks - entirely new
3. ➕ HubSpot batch sync - entirely new
4. ➕ pending_ad_changes queue - entirely new
5. ➕ Model registry - entirely new

---

## 🎬 Next Steps

**Option 1: Incremental Enhancement (Recommended)**
1. Add `pending_ad_changes` migration
2. Enhance `battle_hardened_sampler.py` with mode switching
3. Add `winner_index.py`
4. Add `tasks.py`
5. Modify `safe-executor.ts` to use queue
6. Add integration tests

**Option 2: Fresh Implementation**
Follow the complete plan from scratch (more work, but cleaner)

**Which approach do you prefer?**
