# 🎯 20-AGENT ORCHESTRATION PLAN
## Complete Wiring & Testing - Zero Conflicts

**Goal:** Wire all services, RAG, logic, and ideas to work 100%  
**Agents 1-15:** Perfect wiring (no conflicts)  
**Agents 16-18:** Integration testing  
**Agents 19-20:** Stress testing & final verification

---

## 📋 AGENT ASSIGNMENTS

### **AGENT 1: BattleHardenedSampler Integration** 🔧
**File:** `services/ml-service/src/battle_hardened_sampler.py`  
**Task:** Replace/merge with `GEMINIVIDEO_COMPLETE.py` BattleHardenedSampler

**Actions:**
1. Import `GEMINIVIDEO_COMPLETE.py` classes
2. Replace existing `BattleHardenedSampler` with complete version
3. Ensure `AdState.__hash__()` and `__eq__()` are present
4. Wire to `main.py` endpoints
5. Test hashability: `{ad_state: value}` works

**Dependencies:** None  
**Conflicts:** None (replaces existing)

---

### **AGENT 2: Database Persistence Layer** 💾
**File:** `services/ml-service/src/db/ad_state_repository.py` (CREATE)  
**Task:** Persist AdState to PostgreSQL

**Actions:**
1. Create `ad_states` table migration
2. Create `AdStateRepository` class:
   ```python
   class AdStateRepository:
       async def save(self, ad_state: AdState) -> None
       async def get(self, ad_id: str) -> Optional[AdState]
       async def get_all_active(self, account_id: str) -> List[AdState]
       async def update_from_meta(self, ad_id: str, insights: Dict) -> None
       async def update_from_hubspot(self, ad_id: str, pipeline: Dict) -> None
   ```
3. Wire to BattleHardenedSampler
4. Test: Save → Retrieve → Verify

**Dependencies:** Agent 1 (needs AdState)  
**Conflicts:** None

---

### **AGENT 3: Celery Worker Setup** ⚙️
**File:** `services/ml-service/src/celery_app.py` (CREATE)  
**Task:** Setup Celery for async processing

**Actions:**
1. Create Celery app:
   ```python
   from celery import Celery
   celery_app = Celery('ml-service')
   celery_app.conf.broker_url = os.getenv('REDIS_URL')
   celery_app.conf.result_backend = os.getenv('REDIS_URL')
   ```
2. Create tasks:
   - `process_hubspot_webhook`
   - `monitor_fatigue`
   - `auto_index_winner`
   - `process_budget_optimization`
3. Wire to `main.py`
4. Test: Queue task → Verify execution

**Dependencies:** Redis (exists)  
**Conflicts:** None

---

### **AGENT 4: Celery Beat (Periodic Tasks)** ⏰
**File:** `services/ml-service/src/celery_beat_tasks.py` (CREATE)  
**Task:** Setup periodic monitoring

**Actions:**
1. Create periodic tasks:
   ```python
   @celery_app.task
   def monitor_all_ads_fatigue():
       # Run every 6 hours
       pass
   
   @celery_app.task
   def auto_index_winners():
       # Run every 12 hours
       pass
   ```
2. Configure in `celery_app.py`:
   ```python
   celery_app.conf.beat_schedule = {
       'monitor-fatigue': {
           'task': 'monitor_all_ads_fatigue',
           'schedule': 21600.0,  # 6 hours
       },
   }
   ```
3. Test: Verify tasks run on schedule

**Dependencies:** Agent 3  
**Conflicts:** None

---

### **AGENT 5: HubSpot Webhook Async Fix** 🔄
**File:** `services/gateway-api/src/webhooks/hubspot.ts`  
**Task:** Make webhook async (no timeouts)

**Actions:**
1. Modify webhook to queue to Celery:
   ```typescript
   // Instead of await axios.post(...)
   await redisClient.lPush('celery:queue', JSON.stringify({
     task: 'process_hubspot_webhook',
     args: [req.body]
   }))
   
   // Return immediately
   return res.status(202).json({ status: 'queued' })
   ```
2. Create Celery task handler (Agent 3)
3. Test: Send webhook → Verify async processing

**Dependencies:** Agent 3  
**Conflicts:** None (modifies existing)

---

### **AGENT 6: RAG Winner Index Database** 🗄️
**File:** `services/ml-service/src/rag/winner_index_db.py` (CREATE)  
**Task:** Wire WinnerIndex to FAISS + GCS

**Actions:**
1. Create database table:
   ```sql
   CREATE TABLE winner_index (
     ad_id VARCHAR PRIMARY KEY,
     embedding VECTOR(384),
     metadata JSONB,
     created_at TIMESTAMP
   );
   ```
2. Integrate FAISS (as in existing `winner_index.py`)
3. Integrate GCS for embeddings storage
4. Wire to `main.py` endpoints
5. Test: Add winner → Search → Verify

**Dependencies:** None  
**Conflicts:** None

---

### **AGENT 7: RAG Auto-Indexing** 🔍
**File:** `services/ml-service/src/main.py`  
**Task:** Auto-index winners in feedback endpoint

**Actions:**
1. Modify `/api/ml/battle-hardened/feedback`:
   ```python
   # After feedback registered
   if pipeline_roas > 3.0 or ctr > 0.03:
       # Auto-index winner
       await winner_index.add_winner(
           ad_id=ad_id,
           embedding=creative_dna_embedding,
           metadata=creative_dna
       )
   ```
2. Generate embedding from Creative DNA (use Vertex AI)
3. Test: Winner feedback → Verify auto-indexing

**Dependencies:** Agent 6, Vertex AI  
**Conflicts:** None (adds to existing)

---

### **AGENT 8: RAG → Creative Generation** 🎨
**File:** `services/titan-core/ai_council/director_agent.py`  
**Task:** Wire RAG search to Director Agent

**Actions:**
1. Add RAG search before creating battle plan:
   ```python
   async def create_battle_plan(self, video_id: str):
       # Get Creative DNA
       creative_dna = await get_creative_dna(video_id)
       
       # Search for similar winners (NEW)
       similar_winners = await ml_service_client.post(
           '/api/ml/rag/search-winners',
           json={
               'query_embedding': creative_dna.embedding,
               'top_k': 5
           }
       )
       
       # Use winners in prompt
       prompt = f"""
       Here are 5 winning ads similar to this video:
       {similar_winners}
       
       Create a battle plan that applies their proven patterns...
       """
   ```
2. Test: Upload video → Verify RAG search → Verify plan uses winners

**Dependencies:** Agent 6  
**Conflicts:** None (adds to existing)

---

### **AGENT 9: Vertex AI Embedding Generation** 🧬
**File:** `services/ml-service/src/rag/embedding_service.py` (CREATE)  
**Task:** Generate embeddings from Creative DNA

**Actions:**
1. Create embedding service:
   ```python
   from services.titan_core.engines.vertex_ai import VertexAIService
   
   async def generate_creative_dna_embedding(creative_dna: Dict) -> List[float]:
       # Convert Creative DNA to text
       text = f"{creative_dna['hook_type']} {creative_dna['visual_style']}..."
       
       # Use Vertex AI embeddings
       vertex = VertexAIService(...)
       embedding = await vertex.generate_text_embedding(text)
       return embedding
   ```
2. Wire to WinnerIndex
3. Test: Generate embedding → Verify format

**Dependencies:** Vertex AI (exists)  
**Conflicts:** None

---

### **AGENT 10: Model Registry Wrapper** 📊
**File:** `services/ml-service/src/mlops/model_registry.py` (CREATE)  
**Task:** Create Python wrapper for model_registry table

**Actions:**
1. Create wrapper:
   ```python
   class ModelRegistry:
       async def register_model(
           self,
           model_type: str,
           version: str,
           stage: str,  # 'champion' or 'challenger'
           metrics: Dict
       ) -> str:
           # Insert into model_registry table
           pass
       
       async def promote_challenger(self, model_id: str) -> None:
           # Update stage to 'champion'
           pass
   ```
2. Wire to training endpoints
3. Test: Train model → Register → Verify

**Dependencies:** Database (exists)  
**Conflicts:** None

---

### **AGENT 11: Vertex AI API Endpoints** 🌐
**File:** `services/titan-core/api/main.py`  
**Task:** Expose Vertex AI via API

**Actions:**
1. Add endpoints:
   ```python
   @app.post("/api/titan/analyze-video")
   async def analyze_video_vertex(video_id: str):
       return await vertex_service.analyze_video(video_id)
   
   @app.post("/api/titan/generate-embedding")
   async def generate_embedding(text: str):
       return await vertex_service.generate_text_embedding(text)
   ```
2. Test: Call endpoint → Verify response

**Dependencies:** Vertex AI (exists)  
**Conflicts:** None (adds to existing)

---

### **AGENT 12: Fatigue Auto-Remediation** 🔄
**File:** `services/ml-service/src/fatigue_auto_remediation.py` (CREATE)  
**Task:** Auto-queue to SafeExecutor when fatigue detected

**Actions:**
1. Create auto-remediation:
   ```python
   async def handle_fatigue(ad_id: str, fatigue_result: FatigueResult):
       if fatigue_result.fatigue_level == "critical":
           # Queue to SafeExecutor
           await db.execute("""
               INSERT INTO pending_ad_changes (ad_id, action, current_budget, target_budget)
               VALUES (:ad_id, 'pause', :current, 0)
           """, {"ad_id": ad_id, "current": current_budget})
   ```
2. Wire to fatigue monitoring (Agent 4)
3. Test: Detect fatigue → Verify queue

**Dependencies:** Agent 4, SafeExecutor (exists)  
**Conflicts:** None

---

### **AGENT 13: Docker Compose Celery Services** 🐳
**File:** `docker-compose.yml`  
**Task:** Add Celery worker and beat services

**Actions:**
1. Add services:
   ```yaml
   celery-worker:
     build: ./services/ml-service
     command: celery -A src.celery_app worker -Q hubspot-webhook-events,fatigue-monitoring,budget-optimization
     environment:
       DATABASE_URL: postgresql://geminivideo:geminivideo@postgres:5432/geminivideo
       REDIS_URL: redis://redis:6379
     depends_on:
       - redis
       - postgres
   
   celery-beat:
     build: ./services/ml-service
     command: celery -A src.celery_app beat
     environment:
       DATABASE_URL: postgresql://geminivideo:geminivideo@postgres:5432/geminivideo
       REDIS_URL: redis://redis:6379
     depends_on:
       - redis
       - postgres
   ```
2. Test: `docker-compose up` → Verify services start

**Dependencies:** Agent 3, Agent 4  
**Conflicts:** None (adds to existing)

---

### **AGENT 14: Multi-Account Support** 👥
**File:** `services/ml-service/src/account_scoping.py` (CREATE)  
**Task:** Add account isolation

**Actions:**
1. Create account scoping:
   ```python
   class AccountScopedSampler:
       def __init__(self, account_id: str):
           self.account_id = account_id
           self.sampler = BattleHardenedSampler(...)
       
       async def decide(self, ad_id: str):
           # Load account config
           config = await get_account_config(self.account_id)
           # Use config for thresholds
           return self.sampler.decide(ad, config)
   ```
2. Add `account_id` to all database queries
3. Test: Two accounts → Verify isolation

**Dependencies:** Agent 1, Agent 2  
**Conflicts:** None

---

### **AGENT 15: Configuration Management** ⚙️
**File:** `database/migrations/007_account_configurations.sql` (CREATE)  
**Task:** Per-account configuration table

**Actions:**
1. Create table:
   ```sql
   CREATE TABLE account_configurations (
     account_id VARCHAR PRIMARY KEY,
     aov DECIMAL,
     ignorance_zone_days DECIMAL,
     ignorance_zone_spend DECIMAL,
     kill_roas_threshold DECIMAL,
     scale_roas_threshold DECIMAL,
     blending_curve VARCHAR,
     created_at TIMESTAMP
   );
   ```
2. Create API endpoints for config management
3. Wire to BattleHardenedSampler
4. Test: Set config → Verify used in decisions

**Dependencies:** Agent 14  
**Conflicts:** None

---

### **AGENT 16: Integration Test Suite** 🧪
**File:** `tests/integration/test_complete_flow.py` (CREATE)  
**Task:** End-to-end integration tests

**Actions:**
1. Create test suite:
   ```python
   async def test_complete_flow():
       # 1. Upload video
       # 2. Generate Creative DNA
       # 3. RAG search for winners
       # 4. Create battle plan
       # 5. Launch ad
       # 6. HubSpot webhook → Synthetic revenue
       # 7. BattleHardened decision
       # 8. Auto-index winner
       # 9. Verify all steps
   ```
2. Test all 15 agent integrations
3. Verify no conflicts

**Dependencies:** Agents 1-15  
**Conflicts:** None

---

### **AGENT 17: Performance Testing** ⚡
**File:** `tests/performance/test_performance.py` (CREATE)  
**Task:** Load testing

**Actions:**
1. Test endpoints:
   - `/api/ml/battle-hardened/select` (100 concurrent)
   - `/api/ml/rag/search-winners` (50 concurrent)
   - HubSpot webhook (1000 events)
2. Measure:
   - Response times
   - Database query performance
   - Celery task throughput
3. Verify: All < 200ms p95

**Dependencies:** Agents 1-15  
**Conflicts:** None

---

### **AGENT 18: Data Consistency Checks** ✅
**File:** `tests/consistency/test_data_consistency.py` (CREATE)  
**Task:** Verify data integrity

**Actions:**
1. Test:
   - AdState saved → Retrieved correctly
   - Winner indexed → Searchable
   - HubSpot webhook → Synthetic revenue calculated
   - Fatigue detected → Queued correctly
2. Verify:
   - No orphaned records
   - All foreign keys valid
   - All embeddings generated

**Dependencies:** Agents 1-15  
**Conflicts:** None

---

### **AGENT 19: Stress Test - High Load** 🔥
**File:** `tests/stress/test_high_load.py` (CREATE)  
**Task:** Maximum load testing

**Actions:**
1. Simulate:
   - 1000 ads running simultaneously
   - 100 HubSpot webhooks/second
   - 50 RAG searches/second
   - 20 budget optimizations/minute
2. Monitor:
   - Database connections
   - Redis memory
   - Celery queue depth
   - Response times
3. Verify: System handles load gracefully

**Dependencies:** Agents 1-18  
**Conflicts:** None

---

### **AGENT 20: Final Verification & Documentation** 📝
**File:** `PRODUCTION_READY_VERIFICATION.md` (CREATE)  
**Task:** Final checklist and documentation

**Actions:**
1. Verify all 19 agents completed
2. Create production checklist:
   - [ ] All services wired
   - [ ] All tests passing
   - [ ] Performance verified
   - [ ] Documentation complete
3. Create deployment guide
4. Create monitoring setup guide

**Dependencies:** Agents 1-19  
**Conflicts:** None

---

## 🔄 EXECUTION ORDER (No Conflicts)

### Phase 1: Core Wiring (Agents 1-5)
1. Agent 1: BattleHardenedSampler ✅
2. Agent 2: Database Persistence ✅
3. Agent 3: Celery Worker ✅
4. Agent 4: Celery Beat ✅
5. Agent 5: HubSpot Async ✅

### Phase 2: RAG Integration (Agents 6-9)
6. Agent 6: RAG Database ✅
7. Agent 7: Auto-Indexing ✅
8. Agent 8: RAG → Creative ✅
9. Agent 9: Embedding Generation ✅

### Phase 3: MLOps & Advanced (Agents 10-12)
10. Agent 10: Model Registry ✅
11. Agent 11: Vertex AI API ✅
12. Agent 12: Fatigue Auto-Remediation ✅

### Phase 4: Infrastructure (Agents 13-15)
13. Agent 13: Docker Compose ✅
14. Agent 14: Multi-Account ✅
15. Agent 15: Configuration ✅

### Phase 5: Testing (Agents 16-20)
16. Agent 16: Integration Tests ✅
17. Agent 17: Performance Tests ✅
18. Agent 18: Consistency Checks ✅
19. Agent 19: Stress Tests ✅
20. Agent 20: Final Verification ✅

---

## 🎯 SUCCESS CRITERIA

### All Agents Complete When:
- ✅ All 20 agents have working code
- ✅ All tests pass
- ✅ No conflicts between agents
- ✅ Performance targets met
- ✅ Documentation complete

### Production Ready When:
- ✅ All services wired
- ✅ All endpoints working
- ✅ All background jobs running
- ✅ All tests passing
- ✅ Stress tests passed
- ✅ Monitoring configured

---

## 📊 CONFLICT PREVENTION

### File Ownership:
- Agent 1: `battle_hardened_sampler.py` (replaces)
- Agent 2: `db/ad_state_repository.py` (creates)
- Agent 3: `celery_app.py` (creates)
- Agent 4: `celery_beat_tasks.py` (creates)
- Agent 5: `webhooks/hubspot.ts` (modifies)
- Agent 6: `rag/winner_index_db.py` (creates)
- Agent 7: `main.py` (modifies - adds to endpoint)
- Agent 8: `director_agent.py` (modifies - adds to method)
- Agent 9: `rag/embedding_service.py` (creates)
- Agent 10: `mlops/model_registry.py` (creates)
- Agent 11: `api/main.py` (modifies - adds endpoints)
- Agent 12: `fatigue_auto_remediation.py` (creates)
- Agent 13: `docker-compose.yml` (modifies - adds services)
- Agent 14: `account_scoping.py` (creates)
- Agent 15: `007_account_configurations.sql` (creates)
- Agents 16-20: Test files (creates)

### No Conflicts Because:
- Each agent owns specific files
- Modifications are additive (not destructive)
- Database migrations are sequential
- Dependencies are clear

---

## 🚀 QUICK START

### To Execute All Agents:

```bash
# Phase 1: Core Wiring
# Agent 1-5 code goes here

# Phase 2: RAG Integration
# Agent 6-9 code goes here

# Phase 3: MLOps
# Agent 10-12 code goes here

# Phase 4: Infrastructure
# Agent 13-15 code goes here

# Phase 5: Testing
# Agent 16-20 code goes here

# Final: Verify
python tests/integration/test_complete_flow.py
```

---

**This plan ensures zero conflicts and 100% completion!**

