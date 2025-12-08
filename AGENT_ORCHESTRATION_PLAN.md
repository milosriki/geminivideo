# 🤖 AGENT ORCHESTRATION PLAN: Maximum Parallel Execution

**Purpose:** Execute 10-30 Claude Code agents in parallel to wire all dormant intelligence  
**Strategy:** Git worktrees + service ownership + dependency graph  
**Goal:** 13 hours of work → 6-8 hours wall time with parallel execution

---

## 🎯 EXECUTION STRATEGY

### Option A: 10 Agents (Recommended)

**Best for:** Maximum speed with minimal coordination overhead

**Agent Assignment:**

| Agent | Task | Files | Time | Dependencies |
|-------|------|-------|------|--------------|
| **1** | Semantic Cache → Sampler | `battle_hardened_sampler.py` | 30m | None |
| **2** | Batch API → SafeExecutor | `safe-executor.ts` | 1h | None |
| **3** | Cross-Learner → Sampler | `battle_hardened_sampler.py` | 1h | None |
| **4** | Winner Index → Director | `director_agent.py` | 1h | None |
| **5** | Precomputer Scheduling | `main.py` | 30m | None |
| **6** | Fatigue → Auto-Promoter | `auto_promoter.py` | 30m | None |
| **7** | HubSpot Sync Worker | `tasks.py` (NEW) | 2h | None |
| **8** | Vector Store Wiring | `creative_dna.py` | 2h | None |
| **9** | Time Optimizer | `main.py` | 1h | None |
| **10** | Integration Tests | All | 2h | Agents 1-9 |

**Total:** 11.5 hours → ~4-5 hours wall time (parallel)

### Option B: 30 Agents (Maximum Parallelism)

**Best for:** Complete coverage, all optimizations at once

**Group 1: Database (5 agents)**
- Agent 1: Verify pending_ad_changes migration
- Agent 2: Verify model_registry migration
- Agent 3: Add Redis persistence for render_jobs
- Agent 4: Optimize database indexes
- Agent 5: Connection pooling optimization

**Group 2: ML-Service Wiring (10 agents)**
- Agent 6: Semantic Cache → BattleHardenedSampler
- Agent 7: Cross-Learner → BattleHardenedSampler
- Agent 8: Winner Index → Director Agent
- Agent 9: Fatigue Detector → Auto-Promoter
- Agent 10: Precomputer scheduling
- Agent 11: Vector Store → Creative DNA
- Agent 12: Time Optimizer activation
- Agent 13: Prediction Logger wiring
- Agent 14: Embedding Pipeline auto-generation
- Agent 15: Batch Processor integration

**Group 3: Gateway & Integration (5 agents)**
- Agent 16: Batch API → SafeExecutor
- Agent 17: Verify Gateway → Titan-Core routes
- Agent 18: Add Gateway → Video-Agent Pro routes
- Agent 19: Webhook signature verification
- Agent 20: Rate limiting enhancement

**Group 4: Workers & Scheduling (5 agents)**
- Agent 21: HubSpot Sync Worker (Celery)
- Agent 22: Actuals Scheduler (Celery Beat)
- Agent 23: Auto-Promotion Scheduler
- Agent 24: Compound Learning Scheduler
- Agent 25: Training Scheduler

**Group 5: Testing & Validation (5 agents)**
- Agent 26: Integration tests
- Agent 27: End-to-end flow tests
- Agent 28: Performance benchmarks
- Agent 29: Load testing
- Agent 30: Documentation updates

**Total:** 14-18 hours → ~6-8 hours wall time (parallel)

---

## 📋 AGENT PROMPTS (Copy-Paste Ready)

### Agent 1: Semantic Cache → BattleHardenedSampler

```
# TASK: Wire Semantic Cache to BattleHardenedSampler

File: services/ml-service/src/battle_hardened_sampler.py

1. Add import at top:
   from src.semantic_cache import get_semantic_cache

2. In select_budget_allocation() method, add caching:
   
   def select_budget_allocation(self, ad_states, total_budget, ...):
       # Generate cache key
       cache_key = self._generate_cache_key(ad_states, total_budget)
       
       # Check cache first
       semantic_cache = get_semantic_cache()
       cached = semantic_cache.get(cache_key, query_type="budget_allocation")
       if cached:
           logger.info(f"Cache hit for budget allocation")
           return cached
       
       # Compute decision (existing logic)
       recommendations = self._compute_recommendations(...)
       
       # Cache result (30 min TTL)
       semantic_cache.set(cache_key, recommendations, query_type="budget_allocation", ttl=1800)
       
       return recommendations
   
   def _generate_cache_key(self, ad_states, total_budget):
       """Generate semantic cache key from ad states"""
       import hashlib
       import json
       
       # Create hashable representation
       state_hash = json.dumps([
           {"ad_id": s.ad_id, "spend": s.spend, "pipeline_value": s.pipeline_value}
           for s in ad_states
       ], sort_keys=True)
       
       return hashlib.sha256(f"{state_hash}:{total_budget}".encode()).hexdigest()

3. Test: Verify cache hits on repeated calls with same inputs

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 1: Quick Wins #1"
```

### Agent 2: Batch API → SafeExecutor

```
# TASK: Wire Batch API to SafeExecutor

File: services/gateway-api/src/jobs/safe-executor.ts

1. Add import at top:
   import axios from 'axios';

2. Replace individual API calls with batch:
   
   // BEFORE (current):
   for (const change of pendingChanges) {
       await metaAPI.updateAdBudget(change.ad_id, change.budget);
   }
   
   // AFTER (batched):
   const batch = pendingChanges.map(change => ({
       method: "POST",
       relative_url: `act_${account_id}/ads/${change.ad_id}`,
       body: `budget=${change.budget}`
   }));
   
   // Single batch API call
   const response = await axios.post(
       `https://graph.facebook.com/v18.0`,
       { batch },
       { params: { access_token: META_ACCESS_TOKEN } }
   );
   
   // Process batch responses
   for (const result of response.data) {
       if (result.code === 200) {
           await markChangeExecuted(result.body.id);
       } else {
           await markChangeFailed(result.body.id, result.body.error);
       }
   }

3. Test: Verify 50 changes execute in 1 API call instead of 50

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 1: Quick Wins #2"
```

### Agent 3: Cross-Learner → BattleHardenedSampler

```
# TASK: Wire Cross-Learner to BattleHardenedSampler

File: services/ml-service/src/battle_hardened_sampler.py

1. Add import at top:
   from src.cross_learner import get_cross_learner

2. Add method to apply cross-learner boost:
   
   def _apply_cross_learner_boost(self, ad_id: str, base_score: float) -> float:
       """
       Boost score if similar patterns won in other accounts.
       """
       try:
           cross_learner = get_cross_learner()
           
           # Find similar winning patterns across accounts
           similar_winners = cross_learner.find_similar_patterns(
               ad_id=ad_id,
               min_accounts=3,  # Pattern must work in 3+ accounts
               min_roas=2.0
           )
           
           if similar_winners:
               # Boost by 10-20% if pattern proven across accounts
               boost = 1.0 + (len(similar_winners) * 0.05)
               boosted_score = base_score * min(boost, 1.2)  # Max 20% boost
               logger.info(f"Cross-learner boost: {base_score} → {boosted_score} ({len(similar_winners)} similar winners)")
               return boosted_score
           
           return base_score
       except Exception as e:
           logger.warning(f"Cross-learner boost failed: {e}")
           return base_score

3. Call in select_budget_allocation():
   
   for rec in recommendations:
       # Apply cross-learner boost
       rec.confidence = self._apply_cross_learner_boost(rec.ad_id, rec.confidence)
       rec.recommended_budget *= (rec.confidence / original_confidence)

4. Test: Verify scores increase when similar patterns exist

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 1: Quick Wins #3"
```

### Agent 4: Winner Index → Director Agent

```
# TASK: Wire Winner Index to Director Agent for pattern matching

File: services/titan-core/ai_council/director_agent.py

1. Add import at top:
   from services.rag.winner_index import WinnerIndex

2. In generate_blueprints() method, query RAG before generation:
   
   async def generate_blueprints(self, request: BlueprintGenerationRequest):
       # Query RAG for similar winners
       winner_index = WinnerIndex()
       
       # Create query from request
       query = f"{request.product_name} {request.offer} {request.target_avatar}"
       similar_winners = winner_index.find_similar(query, k=5)
       
       # Enhance prompt with winner patterns
       if similar_winners:
           winner_context = "\n".join([
               f"Winner {i+1}: {w.get('hook_text', '')} (CTR: {w.get('ctr', 0):.2%}, ROAS: {w.get('roas', 0):.2f})"
               for i, w in enumerate(similar_winners[:3])
           ])
           
           enhanced_prompt = f"""
           {request.prompt}
           
           Similar winning patterns:
           {winner_context}
           
           Use these patterns as inspiration but create unique variations.
           """
       else:
           enhanced_prompt = request.prompt
       
       # Generate with enhanced prompt
       blueprints = await self._generate_with_prompt(enhanced_prompt, ...)
       
       return blueprints

3. Test: Verify generated blueprints reference winner patterns

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 1: Quick Wins #4"
```

### Agent 5: Precomputer Scheduling

```
# TASK: Activate Precomputer with scheduled tasks

File: services/ml-service/src/main.py

1. Add import at top:
   from apscheduler.schedulers.asyncio import AsyncIOScheduler

2. In startup_event(), add scheduler:
   
   @app.on_event("startup")
   async def startup_event():
       # ... existing code ...
       
       # Start precomputation scheduler
       scheduler = AsyncIOScheduler()
       
       # Schedule hourly predictions for ads needing decisions soon
       scheduler.add_job(
           precomputer.schedule_predictions_for_upcoming_decisions,
           'interval',
           hours=1,
           id='precompute_predictions'
       )
       
       # Schedule daily cache refresh
       scheduler.add_job(
           precomputer.refresh_cache_proactively,
           'cron',
           hour=3,  # 3 AM daily
           id='refresh_cache'
       )
       
       scheduler.start()
       logger.info("Precomputation scheduler started")

3. Test: Verify predictions are precomputed before decision time

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 1: Quick Wins #5"
```

### Agent 6: Fatigue Detector → Auto-Promoter

```
# TASK: Wire Fatigue Detector to trigger auto-refresh

File: services/ml-service/src/auto_promoter.py

1. Add import at top:
   from src.fatigue_detector import detect_fatigue

2. In check_and_promote() method, add fatigue check:
   
   async def check_and_promote(self, experiment_id, force_promotion=False):
       # ... existing promotion logic ...
       
       # Check for fatigue on all variants
       for variant in variants:
           metrics_history = await self._get_metrics_history(variant.ad_id, days=7)
           
           if len(metrics_history) >= 3:
               fatigue_result = detect_fatigue(variant.ad_id, metrics_history)
               
               if fatigue_result.status in ["FATIGUING", "SATURATED", "AUDIENCE_EXHAUSTED"]:
                   logger.warning(f"Ad {variant.ad_id} fatiguing: {fatigue_result.reason}")
                   
                   # Trigger creative refresh
                   await self._trigger_creative_refresh(variant.ad_id)
                   
                   return PromotionResult(
                       status=PromotionStatus.REFRESHED,
                       reason=f"Fatigue detected: {fatigue_result.reason}",
                       ...
                   )
       
       # ... continue with normal promotion logic ...

3. Test: Verify fatigued ads trigger refresh automatically

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 1: Quick Wins #6"
```

### Agent 7: HubSpot Sync Worker

```
# TASK: Create HubSpot Sync Worker for batch aggregation

File: services/ml-service/src/tasks.py (NEW FILE)

1. Create Celery task:
   
   from celery import Celery
   from src.synthetic_revenue import get_synthetic_revenue_calculator
   import requests
   
   celery_app = Celery('ml_service')
   
   @celery_app.task(name='aggregate_crm_pipeline_values')
   def aggregate_crm_pipeline_values(tenant_id: str):
       """
       Hourly job: Aggregate HubSpot pipeline values per ad.
       """
       from services.titan_core.integrations.hubspot import HubSpotIntegration
       
       hubspot = HubSpotIntegration()
       calculator = get_synthetic_revenue_calculator()
       
       # Query HubSpot for all deals in pipeline
       deals = hubspot.get_all_deals(tenant_id, lookback_days=7)
       
       # Group by ad_id (custom property)
       ad_pipeline_values = {}
       for deal in deals:
           ad_id = deal.get('custom_properties', {}).get('source_ad_id')
           if ad_id:
               stage = deal['stage']
               value = calculator.calculate_stage_change(
                   tenant_id=tenant_id,
                   stage_to=stage,
                   deal_value=deal.get('amount', 0)
               ).calculated_value
               
               ad_pipeline_values[ad_id] = ad_pipeline_values.get(ad_id, 0) + value
       
       # Send aggregated data to ML service
       ml_service_url = os.getenv('ML_SERVICE_URL', 'http://localhost:8003')
       response = requests.post(
           f"{ml_service_url}/api/ml/ingest-crm-data",
           json={'ad_performances': ad_pipeline_values}
       )
       
       return {
           'status': 'ok',
           'updated_ads': len(ad_pipeline_values),
           'total_pipeline_value': sum(ad_pipeline_values.values())
       }

2. Add to Celery Beat schedule (celeryconfig.py):
   
   beat_schedule = {
       'aggregate-crm-values': {
           'task': 'aggregate_crm_pipeline_values',
           'schedule': crontab(hour='*/1'),  # Every hour
       },
   }

3. Test: Verify hourly aggregation updates ML service

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 2: High Impact #7"
```

### Agent 8: Vector Store Wiring

```
# TASK: Wire Vector Store for creative embeddings

File: services/ml-service/src/creative_dna.py

1. Add imports:
   from src.embedding_pipeline import EmbeddingPipeline
   from src.vector_store import VectorStore

2. In extract_dna() method, generate and store embeddings:
   
   async def extract_dna(self, creative_id: str):
       # ... existing DNA extraction ...
       
       # Generate embedding for semantic search
       embedding_pipeline = EmbeddingPipeline()
       creative_text = f"{dna['hook_text']} {dna['cta_text']} {dna['description']}"
       embedding = embedding_pipeline.generate_embedding(creative_text)
       
       # Store in vector store
       vector_store = VectorStore()
       vector_store.add(creative_id, embedding, metadata={
           'ctr': dna.get('ctr', 0),
           'roas': dna.get('roas', 0),
           'hook_type': dna.get('hook_type'),
           'cta_style': dna.get('cta_style')
       })
       
       return dna

3. Add similarity search method:
   
   async def find_similar_creatives(self, creative_id: str, k: int = 5):
       """Find similar creatives using vector similarity"""
       vector_store = VectorStore()
       creative_embedding = vector_store.get(creative_id)
       
       if creative_embedding:
           similar = vector_store.find_similar(creative_embedding, k)
           return similar
       
       return []

4. Test: Verify embeddings generated and stored

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 2: High Impact #8"
```

### Agent 9: Time Optimizer Activation

```
# TASK: Activate Time Optimizer endpoint

File: services/ml-service/src/main.py

1. Add import:
   from src.time_optimizer import get_time_optimizer

2. Add endpoint:
   
   @app.post("/api/ml/time-optimizer/recommend")
   async def recommend_posting_time(request: Dict[str, Any]):
       """Recommend optimal posting times based on historical data"""
       account_id = request.get("account_id")
       
       if not account_id:
           raise HTTPException(400, "account_id required")
       
       optimizer = get_time_optimizer()
       recommendations = optimizer.recommend_best_times(account_id)
       
       return {
           "account_id": account_id,
           "recommended_times": recommendations,
           "confidence": optimizer.get_confidence(account_id)
       }

3. Test: Verify recommendations returned

Reference: MASTER_DEEP_ANALYSIS.md, section "TIER 2: High Impact #9"
```

### Agent 10: Integration Tests

```
# TASK: Create comprehensive integration tests

File: tests/integration/test_full_intelligence_loop.py

1. Test full flow:
   - Video upload → RAG query → Generation → Prediction → Allocation → Execution
   
2. Test each wiring:
   - Semantic cache hits
   - Batch API batching
   - Cross-learner boost
   - Winner index pattern matching
   - Fatigue detection → refresh

3. Verify all connections work end-to-end

Reference: MASTER_DEEP_ANALYSIS.md, section "Testing"
```

---

## 🔧 GIT WORKTREE SETUP (Run Once)

```bash
# Create worktrees for parallel execution
cd ~/geminivideo

for task in semantic-cache batch-api cross-learner winner-index precomputer fatigue hubspot-sync vector-store time-optimizer tests; do
  git worktree add "trees/agent-$task" -b "wire/$task"
done

# Launch agents (each in separate terminal/tmux session)
cd trees/agent-semantic-cache && claude
cd trees/agent-batch-api && claude
# ... etc
```

---

## ✅ SUCCESS CRITERIA

After all agents complete:

1. **Semantic Cache:** 95%+ hit rate on repeated queries
2. **Batch API:** 50 changes execute in 1 API call
3. **Cross-Learner:** Scores boost when similar patterns exist
4. **Winner Index:** Generated blueprints reference winner patterns
5. **Precomputer:** Predictions ready before decision time
6. **Fatigue Detector:** Auto-refreshes fatigued ads
7. **HubSpot Sync:** Hourly aggregation updates ML service
8. **Vector Store:** Embeddings generated for all creatives
9. **Time Optimizer:** Recommendations returned
10. **Integration Tests:** All tests pass

---

## 📊 EXPECTED RESULTS

**Before Wiring:**
- Decision latency: 2000ms
- API calls: 50 for 50 changes
- Cache hit rate: 70%
- Creative hit rate: 20%
- Learning data: Single account

**After Wiring:**
- Decision latency: 40ms (95% cache hits)
- API calls: 1 for 50 changes (batch)
- Cache hit rate: 95%
- Creative hit rate: 60-70% (winner patterns)
- Learning data: 100 accounts (cross-learner)

**ROI:** 200x+ improvement potential

---

## 🚨 CRITICAL DEPENDENCIES

**Execute in this order:**

1. Agent 1-6 (can run in parallel) - Core wiring
2. Agent 7 (depends on /ingest-crm-data endpoint) - HubSpot sync
3. Agent 8 (depends on embedding pipeline) - Vector store
4. Agent 9 (independent) - Time optimizer
5. Agent 10 (depends on 1-9) - Integration tests

**Merge Order:**

1. Merge Agent 1-6 (core wiring)
2. Merge Agent 7-9 (high impact)
3. Merge Agent 10 (tests)

---

## 📝 NOTES

- Each agent works in isolated worktree (no conflicts)
- All agents can run simultaneously (no file overlap)
- Merge conflicts only possible if same file modified (unlikely with service ownership)
- Test after each agent completes
- Rollback plan: Each agent branch can be reverted independently

