# Exact Code Enhancements (No Duplication)

## File-by-File Enhancement Guide

### 1. BattleHardenedSampler: Add Mode Switching

**File:** `services/ml-service/src/battle_hardened_sampler.py`

**Current Lines to Keep:** 1-200 (all Thompson Sampling logic)

**Add After Line 76 (inside `__init__`):**
```python
# ADD THESE PARAMETERS
def __init__(
    self,
    ad_ids: List[str],
    mode: str = "pipeline",  # ← ADD THIS
    account_average_score: float = 1.0,  # ← ADD THIS
    roas_threshold: float = 2.0,
    decay_const: float = 0.0001,
    # Service-mode kill logic thresholds ← ADD ALL BELOW
    ignorance_zone_days: float = 2.0,
    ignorance_zone_spend: float = 100.0,
    min_spend_for_kill: float = 200.0,
    kill_pipeline_roas: float = 0.5,
    scale_pipeline_roas: float = 3.0
):
    self.mode = mode  # ← ADD
    self.account_average_score = account_average_score  # ← ADD
    self.ignorance_zone_days = ignorance_zone_days  # ← ADD
    self.ignorance_zone_spend = ignorance_zone_spend  # ← ADD
    self.min_spend_for_kill = min_spend_for_kill  # ← ADD
    self.kill_pipeline_roas = kill_pipeline_roas  # ← ADD
    self.scale_pipeline_roas = scale_pipeline_roas  # ← ADD

    # ... rest of existing __init__ code
```

**Add New Methods (After Line 200):**
```python
def should_kill_service_ad(
    self,
    ad_id: str,
    spend: float = None,
    synthetic_revenue: float = None,
    days_live: float = None
) -> Union[bool, str]:
    """
    Service-mode kill logic with ignorance zone.

    Returns:
        False: Don't kill (keep running)
        True: Kill (wasting money)
        "SCALE_AGGRESSIVELY": Scale budget significantly
    """
    state = self.ad_states[ad_id]

    # Use provided values or state values
    spend = spend if spend is not None else state.spend
    synthetic_revenue = synthetic_revenue if synthetic_revenue is not None else state.synthetic_revenue
    days_live = days_live if days_live is not None else state.days_live

    # IGNORANCE ZONE: Don't kill early
    if days_live < self.ignorance_zone_days and spend < self.ignorance_zone_spend:
        return False

    pipeline_roas = synthetic_revenue / max(spend, 1)

    # Kill if clearly wasting money
    if spend > self.min_spend_for_kill and pipeline_roas < self.kill_pipeline_roas:
        logger.info(f"KILL {ad_id}: spend=${spend:.2f}, pipeline_roas={pipeline_roas:.2f}")
        return True

    # Scale aggressively if performing well
    if pipeline_roas > self.scale_pipeline_roas:
        logger.info(f"SCALE_AGGRESSIVELY {ad_id}: pipeline_roas={pipeline_roas:.2f}")
        return "SCALE_AGGRESSIVELY"

    return False

def should_kill_direct_ad(self, ad_id: str) -> bool:
    """
    Direct-mode kill logic (e-commerce).

    Kill if score is 50% below account average after 6 hours.
    """
    state = self.ad_states[ad_id]

    # Never kill in first 6 hours
    if state.hours_live < 6:
        return False

    score = self.calculate_blended_score(
        state.clicks,
        state.impressions,
        state.spend,
        state.revenue,
        state.hours_live
    )

    # Kill if 50% below account average
    if score < self.account_average_score * 0.5:
        logger.info(f"KILL {ad_id}: score={score:.4f} < {self.account_average_score * 0.5:.4f}")
        return True

    return False
```

**Modify Existing `make_decision()` Method:**
```python
def make_decision(
    self,
    ad_id: str,
    output_mode: str = "direct"
) -> Union[Tuple[Decision, float], Dict]:
    """Make optimization decision for an ad"""
    if ad_id not in self.ad_states:
        return (Decision.MAINTAIN, 0.0) if output_mode == "direct" else {
            "decision": "MAINTAIN", "confidence": 0.0, "score": 0.0
        }

    state = self.ad_states[ad_id]

    # ← ADD MODE-SPECIFIC KILL LOGIC
    if self.mode == "pipeline":
        kill_result = self.should_kill_service_ad(ad_id)
        if kill_result == True:
            decision = Decision.KILL
            confidence = 0.9
        elif kill_result == "SCALE_AGGRESSIVELY":
            decision = Decision.SCALE_AGGRESSIVELY
            confidence = 0.85
        else:
            # Use Thompson Sampling for non-extreme cases
            decision, confidence = self._thompson_decision(ad_id)
    else:
        # Direct mode
        if self.should_kill_direct_ad(ad_id):
            decision = Decision.KILL
            confidence = 0.9
        else:
            decision, confidence = self._thompson_decision(ad_id)

    # ... rest of existing code
```

---

### 2. Main.py: Add Missing Endpoints

**File:** `services/ml-service/src/main.py`

**Keep All Existing Endpoints (Lines 3585-3870)**

**Add After Line 3870 (before health check):**

```python
# ============================================================
# BULK CRM INGESTION (for HubSpot sync worker)
# ============================================================

class BulkCRMData(BaseModel):
    """Bulk ingest from HubSpot sync worker"""
    ad_performances: Dict[str, float]  # ad_id -> synthetic_revenue

@app.post("/api/ml/ingest-crm-data")
async def ingest_crm_data(
    data: BulkCRMData,
    tenant_id: str = "ptd_fitness"
):
    """
    Bulk ingest synthetic revenue from CRM sync worker.

    Called by: titan-core/integrations/hubspot_sync_worker.py
    """
    # Get tenant config
    # (Use existing get_synthetic_revenue_calculator from our code)
    calculator = get_synthetic_revenue_calculator()
    sampler = get_battle_hardened_sampler()

    updated = 0
    for ad_id, synthetic_revenue in data.ad_performances.items():
        # Ingest using existing battle_hardened_sampler
        sampler.ingest_feedback(ad_id, {
            "synthetic_revenue": synthetic_revenue
        }, is_synthetic=True)
        updated += 1

    logger.info(f"Bulk CRM ingest: updated {updated} ads for {tenant_id}")

    return {"status": "ok", "updated_ads": updated}


# ============================================================
# WINNER INDEX (RAG) ENDPOINTS - NEW
# ============================================================

class SimilarAdsRequest(BaseModel):
    query_embedding: List[float]
    k: int = 5

@app.post("/api/ml/rag/find-similar")
async def find_similar_winners(request: SimilarAdsRequest):
    """Find similar winning ads based on creative embedding"""
    from .winner_index import get_winner_index
    import numpy as np

    winner_index = get_winner_index()
    query_vector = np.array(request.query_embedding, dtype='float32')
    results = winner_index.search(query_vector, k=request.k)

    return {
        "similar_ads": [
            {
                "ad_id": ad_id,
                "distance": distance,
                "metadata": metadata
            }
            for ad_id, distance, metadata in results
        ]
    }

@app.post("/api/ml/rag/add-winner")
async def add_winner(
    ad_id: str,
    embedding: List[float],
    metadata: Optional[Dict] = None
):
    """Add a winning ad to the index"""
    from .winner_index import get_winner_index
    import numpy as np

    winner_index = get_winner_index()
    embedding_array = np.array(embedding, dtype='float32')
    winner_index.add(ad_id, embedding_array, metadata)

    return {"status": "added", "ad_id": ad_id, "index_size": winner_index.get_count()}
```

---

### 3. SafeExecutor: Use Pending Queue

**File:** `services/gateway-api/src/jobs/safe-executor.ts`

**Replace Lines 1-50 (pg-boss imports) With:**
```typescript
import { Pool } from 'pg';

const DATABASE_URL = process.env.DATABASE_URL || 'postgresql://localhost:5432/geminivideo';
const pool = new Pool({ connectionString: DATABASE_URL });

interface PendingJob {
    id: string;
    tenant_id: string;
    ad_account_id: string;
    ad_entity_id: string;
    entity_type: 'campaign' | 'ad_set' | 'ad';
    change_type: string;
    requested_value: number | null;
    change_payload: any;
    jitter_ms_min: number;
    jitter_ms_max: number;
}

/**
 * Claim the next pending job using SKIP LOCKED
 */
async function claimNextJob(workerId: string): Promise<PendingJob | null> {
    const result = await pool.query(
        'SELECT * FROM claim_pending_ad_change($1)',
        [workerId]
    );
    return result.rows[0] || null;
}
```

**Keep All Safety Check Functions (Lines 100-300):**
- `applyJitter()`
- `fuzzifyBudget()`
- `validateBudgetChange()`
- `executeMetaApiCall()`
- `logExecution()`

**Replace Worker Loop (Lines 400-450) With:**
```typescript
async function runWorker(): Promise<void> {
    const workerId = process.env.WORKER_ID || `safe-executor-${Date.now()}`;
    console.log(`SafeExecutor starting: ${workerId}`);

    while (true) {
        try {
            const job = await claimNextJob(workerId);  // ← USE QUEUE INSTEAD OF PG-BOSS

            if (job) {
                await processJob(job);
            } else {
                // No jobs, wait before polling again
                await new Promise(resolve => setTimeout(resolve, 5000));
            }
        } catch (error) {
            console.error('Worker error:', error);
            await new Promise(resolve => setTimeout(resolve, 10000));
        }
    }
}
```

---

### 4. HubSpot Webhook: Add Celery Queue

**File:** `services/gateway-api/src/webhooks/hubspot.ts`

**Keep Existing Signature Verification (Lines 1-50)**

**Replace Event Processing (Lines 100-200) With:**
```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL || 'redis://localhost:6379');

/**
 * Queue task to Celery via Redis
 */
async function queueCeleryTask(taskName: string, args: any[]): Promise<void> {
    await redis.lpush('hubspot', JSON.stringify({
        body: JSON.stringify([args, {}, {}]),
        headers: { task: taskName, id: crypto.randomUUID() },
        'content-type': 'application/json',
        'content-encoding': 'utf-8'
    }));
}

router.post('/webhook/hubspot', async (req: Request, res: Response) => {
    // Keep existing signature verification

    const events = Array.isArray(req.body) ? req.body : [req.body];

    // ← REPLACE direct ML-Service calls with Celery queue
    try {
        await queueCeleryTask('process_hubspot_deal_change', events);

        return res.status(200).json({
            status: 'queued',
            events_received: events.length
        });
    } catch (error) {
        console.error('Error queueing events:', error);
        return res.status(500).json({ error: 'Failed to queue events' });
    }
});
```

---

## Summary: Minimal Changes Required

| File | Action | Lines Changed |
|------|--------|---------------|
| `battle_hardened_sampler.py` | ENHANCE | +150 lines (add mode switching) |
| `main.py` | ADD | +100 lines (4 new endpoints) |
| `safe-executor.ts` | MODIFY | ~50 lines (replace pg-boss with queue) |
| `hubspot.ts` | MODIFY | ~30 lines (add Celery queue) |
| `winner_index.py` | NEW | +200 lines (FAISS RAG) |
| `tasks.py` | NEW | +150 lines (Celery workers) |
| `hubspot_sync_worker.py` | NEW | +200 lines (batch sync) |

**Total New Code:** ~880 lines
**Total Modified Code:** ~230 lines
**Total Preserved Code:** ~3,600 lines (87% reuse!)

---

## Quick Commands to Apply Changes

```bash
# 1. Add new database migrations
psql -d geminivideo -f database/migrations/005_pending_ad_changes.sql
psql -d geminivideo -f database/migrations/006_model_registry.sql

# 2. Create new Python files
touch services/ml-service/src/winner_index.py
touch services/ml-service/src/tasks.py
touch services/titan-core/integrations/hubspot_sync_worker.py

# 3. Modify existing files (use diffs above)
code services/ml-service/src/battle_hardened_sampler.py
code services/ml-service/src/main.py
code services/gateway-api/src/jobs/safe-executor.ts
code services/gateway-api/src/webhooks/hubspot.ts

# 4. Add tests
touch tests/integration/test_complete_loop.py

# 5. Add startup script
touch scripts/start-all.sh
chmod +x scripts/start-all.sh
```

Would you like me to:
1. **Apply these enhancements incrementally** (modify existing files)
2. **Create the missing modules** (winner_index, tasks, hubspot_sync_worker)
3. **Both** (complete the integration)
