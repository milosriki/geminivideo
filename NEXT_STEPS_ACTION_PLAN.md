# 🎯 NEXT STEPS - ACTION PLAN
## What to Do Right Now

**Status:** Agents 1-15 code is ready. Time to apply and test.

---

## ✅ WHAT'S DONE

1. ✅ **Agent 1:** AdState hashability fixed (committed)
2. ✅ **Agent 2:** Database persistence layer created (committed)
3. ✅ **Agent 3:** Celery worker setup (committed)
4. ✅ **Agent 4:** Celery Beat tasks (committed)
5. ✅ **Agents 5-15:** Complete code provided in `AGENTS_5_TO_20_IMPLEMENTATION.md`

---

## 🚀 IMMEDIATE NEXT STEPS (Priority Order)

### **STEP 1: Apply Database Migrations** (5 minutes)

```bash
# Run migrations
psql -U geminivideo -d geminivideo -f database/migrations/008_ad_states.sql
psql -U geminivideo -d geminivideo -f database/migrations/009_winner_index.sql
psql -U geminivideo -d geminivideo -f database/migrations/010_account_configurations.sql
```

**Verify:**
```sql
-- Check tables exist
\dt ad_states
\dt winner_index
\dt account_configurations
```

---

### **STEP 2: Apply Agent 5 - HubSpot Webhook Async** (10 minutes)

**File:** `services/gateway-api/src/webhooks/hubspot.ts`

**Change:** Replace lines 255-366 with async version from `AGENTS_5_TO_20_IMPLEMENTATION.md`

**Test:**
```bash
# Send test webhook
curl -X POST http://localhost:8080/webhook/hubspot \
  -H "Content-Type: application/json" \
  -d '[{"objectId": 123, "propertyName": "dealstage", "propertyValue": "assessment_booked"}]'

# Should return: {"status": "queued"}
```

---

### **STEP 3: Apply Agent 6 - RAG Database** (15 minutes)

1. **Create migration file:** `database/migrations/009_winner_index.sql` (copy from guide)
2. **Create Python file:** `services/ml-service/src/rag/winner_index_db.py` (copy from guide)
3. **Run migration:**
   ```bash
   psql -U geminivideo -d geminivideo -f database/migrations/009_winner_index.sql
   ```

**Test:**
```python
# In Python shell
from services.ml_service.src.rag.winner_index_db import WinnerIndexDB
# Test add_winner and search
```

---

### **STEP 4: Apply Agent 7 - Auto-Indexing** (5 minutes)

**File:** `services/ml-service/src/main.py`

**Find:** `/api/ml/battle-hardened/feedback` endpoint

**Add:** Auto-indexing code from guide (around line 3100+)

**Test:**
```bash
# Send feedback with high ROAS
curl -X POST http://localhost:8003/api/ml/battle-hardened/feedback \
  -H "Content-Type: application/json" \
  -d '{"ad_id": "test-123", "actual_pipeline_value": 10000, "actual_spend": 2000}'

# Should trigger auto-indexing (check Celery logs)
```

---

### **STEP 5: Apply Agent 8 - RAG → Creative** (10 minutes)

**File:** `services/titan-core/ai_council/director_agent.py`

**Find:** `create_battle_plan` method

**Add:** RAG search code from guide (before prompt generation)

**Test:**
```bash
# Upload video and create battle plan
# Should see RAG search in logs
```

---

### **STEP 6: Apply Agent 9 - Embedding Service** (5 minutes)

**File:** `services/ml-service/src/rag/embedding_service.py` (CREATE)

**Copy:** Code from guide

**Test:**
```python
from services.ml_service.src.rag.embedding_service import generate_creative_dna_embedding
embedding = await generate_creative_dna_embedding({"hook_type": "testimonial"})
assert len(embedding) == 384
```

---

### **STEP 7: Apply Agent 10 - Model Registry** (10 minutes)

**File:** `services/ml-service/src/mlops/model_registry.py` (CREATE)

**Copy:** Code from guide

**Wire to training endpoint:**
```python
# In main.py training endpoint, after training:
from .mlops.model_registry import ModelRegistry
registry = ModelRegistry(pool)
await registry.register_model(
    model_type="ctr_predictor",
    version="1.0.0",
    stage="challenger",
    metrics={"accuracy": 0.95}
)
```

---

### **STEP 8: Apply Agent 11 - Vertex AI Endpoints** (5 minutes)

**File:** `services/titan-core/api/main.py`

**Add:** Two endpoints from guide

**Test:**
```bash
curl -X POST http://localhost:8084/api/titan/generate-embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "test hook testimonial"}'
```

---

### **STEP 9: Apply Agent 12 - Fatigue Auto-Remediation** (10 minutes)

**File:** `services/ml-service/src/fatigue_auto_remediation.py` (CREATE)

**Copy:** Code from guide

**Wire to fatigue monitoring:**
```python
# In celery_tasks.py monitor_fatigue function:
from .fatigue_auto_remediation import handle_fatigue
await handle_fatigue(ad.ad_id, result, ad.spend)
```

---

### **STEP 10: Apply Agent 13 - Docker Compose** (5 minutes)

**File:** `docker-compose.yml`

**Add:** Celery worker and beat services from guide

**Test:**
```bash
docker-compose up -d celery-worker celery-beat
docker-compose ps  # Should show both running
docker-compose logs celery-worker  # Check logs
```

---

### **STEP 11: Apply Agent 14 - Multi-Account** (10 minutes)

**File:** `services/ml-service/src/account_scoping.py` (CREATE)

**Copy:** Code from guide

**Wire to main.py:**
```python
# In battle-hardened endpoints:
from .account_scoping import AccountScopedSampler
account_id = request.account_id or "default"
sampler = AccountScopedSampler(account_id)
await sampler.initialize()
decision = await sampler.decide(ad)
```

---

### **STEP 12: Apply Agent 15 - Configuration** (10 minutes)

1. **Create migration:** `database/migrations/010_account_configurations.sql`
2. **Add endpoints to main.py:** Copy from guide
3. **Run migration:**
   ```bash
   psql -U geminivideo -d geminivideo -f database/migrations/010_account_configurations.sql
   ```

**Test:**
```bash
# Set config
curl -X POST http://localhost:8003/api/ml/account-config/ptd_fitness \
  -H "Content-Type: application/json" \
  -d '{"aov": 7000, "ignorance_zone_days": 2.0}'

# Get config
curl http://localhost:8003/api/ml/account-config/ptd_fitness
```

---

## 🧪 TESTING PHASE (Agents 16-20)

### **STEP 13: Create Integration Tests** (30 minutes)

**File:** `tests/integration/test_complete_flow.py` (CREATE)

```python
"""
Agent 16: Integration Test Suite
"""
import pytest
import asyncio

@pytest.mark.asyncio
async def test_complete_flow():
    """Test end-to-end flow"""
    # 1. Upload video
    # 2. Generate Creative DNA
    # 3. RAG search
    # 4. Create battle plan
    # 5. Launch ad
    # 6. HubSpot webhook
    # 7. Synthetic revenue
    # 8. BattleHardened decision
    # 9. Auto-index winner
    pass
```

**Run:**
```bash
pytest tests/integration/test_complete_flow.py -v
```

---

### **STEP 14: Create Performance Tests** (20 minutes)

**File:** `tests/performance/test_performance.py` (CREATE)

```python
"""
Agent 17: Performance Tests
"""
import asyncio
import time

async def test_battle_hardened_performance():
    """Test 100 concurrent requests"""
    tasks = [call_endpoint() for _ in range(100)]
    start = time.time()
    await asyncio.gather(*tasks)
    duration = time.time() - start
    assert duration < 5.0  # Should complete in < 5 seconds
```

---

### **STEP 15: Create Consistency Tests** (15 minutes)

**File:** `tests/consistency/test_data_consistency.py` (CREATE)

```python
"""
Agent 18: Data Consistency Tests
"""
def test_ad_state_persistence():
    """Test AdState save → retrieve"""
    # Save
    # Retrieve
    # Verify match
    pass

def test_winner_index_consistency():
    """Test winner indexed → searchable"""
    # Index
    # Search
    # Verify found
    pass
```

---

### **STEP 16: Create Stress Tests** (20 minutes)

**File:** `tests/stress/test_high_load.py` (CREATE)

```python
"""
Agent 19: Stress Tests
"""
async def test_1000_ads():
    """Simulate 1000 ads running"""
    # Create 1000 ad states
    # Run budget allocation
    # Verify no errors
    pass

async def test_100_webhooks_per_second():
    """Test webhook throughput"""
    # Send 100 webhooks
    # Verify all queued
    # Verify processing
    pass
```

---

### **STEP 17: Final Verification** (10 minutes)

**File:** `PRODUCTION_READY_CHECKLIST.md` (CREATE)

```markdown
# Production Ready Checklist

## Services
- [ ] All services running
- [ ] Celery worker running
- [ ] Celery beat running
- [ ] Database migrations applied

## Endpoints
- [ ] BattleHardened endpoints working
- [ ] RAG endpoints working
- [ ] Vertex AI endpoints working
- [ ] Configuration endpoints working

## Background Jobs
- [ ] HubSpot webhook processing
- [ ] Fatigue monitoring running
- [ ] Auto-indexing working

## Tests
- [ ] Integration tests passing
- [ ] Performance tests passing
- [ ] Consistency tests passing
- [ ] Stress tests passing
```

---

## 📊 QUICK REFERENCE: FILE CHECKLIST

### Files to Create:
- [ ] `services/ml-service/src/rag/winner_index_db.py`
- [ ] `services/ml-service/src/rag/embedding_service.py`
- [ ] `services/ml-service/src/mlops/model_registry.py`
- [ ] `services/ml-service/src/fatigue_auto_remediation.py`
- [ ] `services/ml-service/src/account_scoping.py`
- [ ] `database/migrations/009_winner_index.sql`
- [ ] `database/migrations/010_account_configurations.sql`
- [ ] `tests/integration/test_complete_flow.py`
- [ ] `tests/performance/test_performance.py`
- [ ] `tests/consistency/test_data_consistency.py`
- [ ] `tests/stress/test_high_load.py`
- [ ] `PRODUCTION_READY_CHECKLIST.md`

### Files to Modify:
- [x] `services/ml-service/src/battle_hardened_sampler.py` ✅
- [ ] `services/gateway-api/src/webhooks/hubspot.ts`
- [ ] `services/ml-service/src/main.py`
- [ ] `services/titan-core/ai_council/director_agent.py`
- [ ] `services/titan-core/api/main.py`
- [ ] `services/ml-service/src/celery_tasks.py` (wire fatigue remediation)
- [ ] `docker-compose.yml`

---

## 🎯 RECOMMENDED ORDER

**Today (2 hours):**
1. Apply migrations (Step 1)
2. Apply Agents 5-7 (Steps 2-4)
3. Test basic flow

**Tomorrow (3 hours):**
4. Apply Agents 8-12 (Steps 5-9)
5. Apply Agent 13 (Step 10)
6. Test all integrations

**Day 3 (2 hours):**
7. Apply Agents 14-15 (Steps 11-12)
8. Create test suite (Steps 13-16)
9. Final verification (Step 17)

**Total: 7 hours to 100% production-ready**

---

## 🚨 CRITICAL: Test After Each Step

After applying each agent:
1. **Start services:** `docker-compose up -d`
2. **Check logs:** `docker-compose logs -f`
3. **Test endpoint:** Use curl commands provided
4. **Verify database:** Check tables/data
5. **Fix issues:** Before moving to next step

---

## 💡 PRO TIP

**Don't apply all at once!**

Apply one agent at a time:
1. Apply code
2. Test immediately
3. Fix any issues
4. Move to next agent

This prevents cascading failures.

---

**You're ready! Start with Step 1 (migrations) and work through systematically.**

