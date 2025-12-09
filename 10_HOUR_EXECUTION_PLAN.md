# 10-HOUR EXECUTION PLAN
## Optimal Agent Count + Exact Instructions

**Goal:** Complete all remaining work in 10 hours  
**Agents:** 30-40 agents (technically excellent, need exact instructions)  
**Strategy:** Maximum parallelization + Precise task breakdown

---

## 📊 TIME ANALYSIS

### Current Estimate: 13-18 hours
- Phase 4 (Wiring): 6-8 hours
- Phase 5 (Polish): 4-6 hours  
- Phase 6 (Testing): 3-4 hours
- **Total:** 13-18 hours

### To Finish in 10 Hours:
- Need 1.3-1.8x speedup
- Solution: **30-40 agents** (instead of 20+20)
- More parallelization = faster completion

---

## 🎯 OPTIMAL AGENT COUNT

### Recommended: **35 Agents**

**Breakdown:**
- **GROUP A (Remote):** 18 agents (Gateway, Frontend, Docker, Config)
- **GROUP B (Local):** 17 agents (ML Service, Video Agent, RAG, Database)

**Why 35?**
- Phase 4: 20 agents (wiring)
- Phase 5: 10 agents (polish)
- Phase 6: 5 agents (testing)
- **Total:** 35 agents working in parallel

**Time:** 10 hours with perfect parallelization

---

## 📋 DETAILED AGENT ASSIGNMENTS

### GROUP A (18 Agents) - Gateway, Frontend, Docker

#### Agents 1-4: Gateway Routes (4 agents)
**Files:**
- Agent 1: `services/gateway-api/src/routes/campaigns.ts`
- Agent 2: `services/gateway-api/src/routes/ads.ts`
- Agent 3: `services/gateway-api/src/routes/analytics.ts`
- Agent 4: `services/gateway-api/src/routes/predictions.ts`, `ab-tests.ts`, `onboarding.ts`

**Exact Instructions:**
1. Open assigned file
2. Find existing endpoint pattern (e.g., `app.post('/api/campaigns', ...)`)
3. Add missing endpoints using EXACT same pattern:
   ```typescript
   app.post('/api/campaigns/:id/activate',
     apiRateLimiter,
     validateInput({ params: { id: { type: 'uuid', required: true } } }),
     async (req: Request, res: Response) => {
       try {
         const { id } = req.params;
         const result = await pgPool.query(
           'UPDATE campaigns SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *',
           ['active', id]
         );
         if (result.rows.length === 0) {
           return res.status(404).json({ error: 'Campaign not found' });
         }
         res.json({ success: true, data: result.rows[0] });
       } catch (error: any) {
         res.status(500).json({ error: error.message });
       }
     }
   );
   ```
4. Add ALL missing endpoints from `COMPLETE_WIRING_PLAN_CONFIGURABLE.md`
5. Test: Each endpoint must return proper JSON response
6. Commit: `[GROUP-A] Agent X: Add missing endpoints to [file]`

**Time:** 1.5 hours per agent

---

#### Agents 5-6: Gateway Core (2 agents)
**Files:**
- Agent 5: `services/gateway-api/src/index.ts` (endpoints section only)
- Agent 6: `services/gateway-api/src/middleware/security.ts`

**Exact Instructions:**
1. **Agent 5:** Add missing endpoint registrations to `index.ts`
   - Find `app.use('/api/campaigns', campaignsRouter);` pattern
   - Add any missing router registrations
   - Ensure all routes from `routes/` folder are registered
   - Pattern:
     ```typescript
     import { createCampaignsRouter } from './routes/campaigns';
     const campaignsRouter = createCampaignsRouter(pgPool);
     app.use('/api/campaigns', campaignsRouter);
     ```

2. **Agent 6:** Enhance security middleware
   - Add missing security headers
   - Add rate limiting for new endpoints
   - Pattern: Copy from existing middleware

**Time:** 1 hour per agent

---

#### Agents 7-8: Gateway Services (2 agents)
**Files:**
- Agent 7: `services/gateway-api/src/services/scoring-engine.ts`
- Agent 8: `services/gateway-api/src/services/learning-service.ts`

**Exact Instructions:**
1. Open assigned service file
2. Find existing method pattern
3. Add missing methods using EXACT pattern:
   ```typescript
   async methodName(params: any): Promise<any> {
     try {
       // Implementation
       return result;
     } catch (error) {
       logger.error(`Error in methodName: ${error}`);
       throw error;
     }
   }
   ```
4. Ensure all methods from interface are implemented
5. Add error handling to ALL methods
6. Commit: `[GROUP-A] Agent X: Add missing methods to [service]`

**Time:** 1.5 hours per agent

---

#### Agents 9-10: Gateway Workers (2 agents)
**Files:**
- Agent 9: `services/gateway-api/src/workers/self-learning-cycle.ts` (enhance)
- Agent 10: `services/gateway-api/src/jobs/batch-executor.ts`, `safe-executor.ts`

**Exact Instructions:**
1. **Agent 9:** Enhance self-learning cycle
   - Add missing loop implementations
   - Wire to ML service endpoints
   - Add error handling and retries
   - Pattern: Copy from existing loop implementations

2. **Agent 10:** Complete batch and safe executors
   - Add missing batch operations
   - Add missing safety checks
   - Pattern: Copy from existing executor code

**Time:** 2 hours per agent

---

#### Agents 11-12: Multi-Platform (2 agents)
**Files:**
- Agent 11: `services/gateway-api/src/multi-platform/multi_publisher.ts`
- Agent 12: `services/gateway-api/src/multi-platform/format_adapter.ts`

**Exact Instructions:**
1. Add missing platform adapters
2. Add missing format conversions
3. Pattern: Copy from existing adapter
4. Ensure all platforms (Meta, Google, TikTok) are supported
5. Commit: `[GROUP-A] Agent X: Add [platform] support`

**Time:** 1.5 hours per agent

---

#### Agents 13-14: Webhooks/Realtime (2 agents)
**Files:**
- Agent 13: `services/gateway-api/src/webhooks/hubspot.ts`
- Agent 14: `services/gateway-api/src/realtime/*.ts`

**Exact Instructions:**
1. Add missing webhook handlers
2. Add missing realtime channels
3. Pattern: Copy from existing handlers
4. Ensure all webhook types are handled
5. Commit: `[GROUP-A] Agent X: Add [webhook/realtime] support`

**Time:** 1.5 hours per agent

---

#### Agents 15-16: Frontend (2 agents)
**Files:**
- Agent 15: `frontend/src/lib/api.ts` (enhance)
- Agent 16: `frontend/src/**/*.tsx` (all frontend files)

**Exact Instructions:**
1. **Agent 15:** Enhance API client
   - Add missing API methods
   - Add error handling
   - Pattern:
     ```typescript
     export const activateCampaign = async (id: string) => {
       return api.post(`/api/campaigns/${id}/activate`);
     };
     ```

2. **Agent 16:** Wire frontend to backend
   - Add API calls to components
   - Add error handling
   - Add loading states
   - Pattern: Copy from existing components

**Time:** 2 hours per agent

---

#### Agents 17-18: Docker/Config (2 agents)
**Files:**
- Agent 17: `docker-compose.yml`
- Agent 18: `shared/config/*.yaml`, `.env.example`

**Exact Instructions:**
1. **Agent 17:** Update docker-compose
   - Add missing environment variables
   - Add missing service configurations
   - Ensure all services are configured
   - Pattern: Copy from existing service config

2. **Agent 18:** Update config files
   - Add missing configuration options
   - Update `.env.example` with all required vars
   - Pattern: Copy from existing config entries

**Time:** 1 hour per agent

---

### GROUP B (17 Agents) - ML Service, Video Agent, RAG

#### Agents 1-5: ML Service Main (5 agents)
**Files:**
- Agent 1: `services/ml-service/src/main.py` (endpoints section)
- Agent 2: `services/ml-service/src/ctr_model.py`
- Agent 3: `services/ml-service/src/thompson_sampler.py`
- Agent 4: `services/ml-service/src/feature_engineering.py`
- Agent 5: `services/ml-service/src/enhanced_ctr_model.py`

**Exact Instructions:**
1. **Agent 1:** Add missing endpoints to `main.py`
   - Find existing endpoint pattern:
     ```python
     @app.post("/api/ml/endpoint")
     async def endpoint_name(request: RequestModel):
         try:
             # Implementation
             return {"success": True, "data": result}
         except Exception as e:
             logger.error(f"Error: {e}")
             raise HTTPException(status_code=500, detail=str(e))
     ```
   - Add ALL missing endpoints from wiring plan
   - Ensure all endpoints have error handling

2. **Agents 2-5:** Enhance ML models
   - Add missing methods to model classes
   - Ensure all methods have error handling
   - Pattern: Copy from existing methods

**Time:** 2 hours per agent

---

#### Agents 6-9: ML Service Learning (4 agents)
**Files:**
- Agent 6: `services/ml-service/src/cross_learner.py`
- Agent 7: `services/ml-service/src/creative_dna.py`
- Agent 8: `services/ml-service/src/compound_learner.py`
- Agent 9: `services/ml-service/src/actuals_fetcher.py`

**Exact Instructions:**
1. Open assigned learning module file
2. Find existing method pattern:
   ```python
   async def method_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
       try:
           # Implementation
           return {"success": True, "result": result}
       except Exception as e:
           logger.error(f"Error in method_name: {e}")
           raise
   ```
3. Add missing methods
4. Wire to endpoints in `main.py`
5. Add error handling to ALL methods
6. Commit: `[GROUP-B] Agent X: Enhance [module]`

**Time:** 2.5 hours per agent

---

#### Agents 10-11: ML Service Workers (2 agents)
**Files:**
- Agent 10: `services/ml-service/src/celery_tasks.py`
- Agent 11: `services/ml-service/src/training_scheduler.py`

**Exact Instructions:**
1. Add missing Celery tasks
2. Add missing scheduler jobs
3. Pattern: Copy from existing tasks
4. Ensure all tasks have error handling
5. Commit: `[GROUP-B] Agent X: Add [task/job]`

**Time:** 2 hours per agent

---

#### Agents 12-13: ML Service Utils (2 agents)
**Files:**
- Agent 12: `services/ml-service/src/webhook_security.py` (enhance)
- Agent 13: `services/ml-service/src/data_loader.py` (enhance)

**Exact Instructions:**
1. Enhance security functions
2. Enhance data loading functions
3. Add missing error handling
4. Pattern: Copy from existing functions
5. Commit: `[GROUP-B] Agent X: Enhance [module]`

**Time:** 1.5 hours per agent

---

#### Agents 14-15: Video Agent (2 agents)
**Files:**
- Agent 14: `services/video-agent/main.py`
- Agent 15: `services/video-agent/pro/**/*.py` (all pro modules)

**Exact Instructions:**
1. **Agent 14:** Add missing endpoints to `main.py`
   - Pattern: Copy from existing endpoints
   - Ensure all pro modules are wired
   - Add error handling

2. **Agent 15:** Enhance pro video modules
   - Add missing methods to each module
   - Ensure all modules are complete
   - Pattern: Copy from existing module methods

**Time:** 2.5 hours per agent

---

#### Agents 16-17: Drive Intel & RAG (2 agents)
**Files:**
- Agent 16: `services/drive-intel/main.py`, `services/drive-intel/services/*.py`
- Agent 17: `services/rag/winner_index.py`, `services/rag/**/*.py`

**Exact Instructions:**
1. Add missing endpoints
2. Add missing methods
3. Pattern: Copy from existing code
4. Ensure all functionality is wired
5. Commit: `[GROUP-B] Agent X: Enhance [service]`

**Time:** 2 hours per agent

---

## 🎯 PHASE 5: PRODUCTION POLISH (10 Agents)

### Agents 19-23: API Versioning & Docs (5 agents)
**Exact Instructions:**
1. Add `/api/v1/` prefix to all endpoints
2. Create versioning middleware
3. Generate OpenAPI docs
4. Add endpoint documentation
5. Pattern: Copy from existing versioned endpoints

**Time:** 1.5 hours per agent

---

### Agents 24-26: Circuit Breakers (3 agents)
**Exact Instructions:**
1. Add circuit breaker for Meta API
2. Add circuit breaker for Google API
3. Add circuit breaker for service-to-service calls
4. Pattern: Use existing circuit breaker library

**Time:** 2 hours per agent

---

### Agents 27-28: Error Handling (2 agents)
**Exact Instructions:**
1. Standardize error response format
2. Add error codes
3. Add error logging
4. Pattern: Copy from existing error handlers

**Time:** 1.5 hours per agent

---

## 🎯 PHASE 6: TESTING (5 Agents)

### Agents 29-33: Integration Tests (5 agents)
**Exact Instructions:**
1. Create test files for each service
2. Test all endpoints
3. Test service-to-service communication
4. Pattern: Copy from existing tests
5. Ensure all tests pass

**Time:** 2 hours per agent

---

## ⏱️ TIMELINE WITH 35 AGENTS

### Hour 0-2: Phase 4 Start
- All 18 GROUP A agents start (Gateway, Frontend)
- All 17 GROUP B agents start (ML Service, Video Agent)

### Hour 2-4: Phase 4 Continue
- Agents complete their first tasks
- Start second tasks

### Hour 4-6: Phase 4 Finish + Phase 5 Start
- Phase 4 agents finish
- Phase 5 agents (10) start (Polish)

### Hour 6-8: Phase 5 Continue
- Polish agents continue

### Hour 8-10: Phase 5 Finish + Phase 6
- Phase 5 agents finish
- Phase 6 agents (5) start and finish (Testing)

**Total: 10 hours** ✅

---

## 📝 EXACT INSTRUCTIONS FOR EACH AGENT

### Template for All Agents:

```markdown
# AGENT X: [Task Name]

## File: [exact file path]

## Task:
1. Open file: [path]
2. Find existing pattern: [show example]
3. Add missing [items] using EXACT pattern
4. Ensure error handling on ALL methods
5. Test: [how to test]
6. Commit: `[GROUP-X] Agent X: [description]`

## Pattern to Copy:
[exact code pattern]

## What NOT to Change:
- Don't modify existing working code
- Don't change function signatures
- Don't remove any functionality
- Only ADD missing pieces

## Success Criteria:
- [ ] All missing items added
- [ ] Error handling on all methods
- [ ] Tests pass
- [ ] No functionality lost
```

---

## ✅ QUALITY CHECKLIST

### Before Each Commit:
- [ ] Code follows existing patterns
- [ ] Error handling added
- [ ] No functionality removed
- [ ] Tests pass (if applicable)
- [ ] Commit message follows format

### Before Merging:
- [ ] All agents completed tasks
- [ ] All tests pass
- [ ] No conflicts
- [ ] All functionality preserved

---

## 🚀 EXECUTION ORDER

### Parallel Execution:
1. **Hour 0:** All 35 agents start simultaneously
2. **Hour 2:** First tasks complete, start second tasks
3. **Hour 4:** Phase 4 complete, Phase 5 starts
4. **Hour 6:** Phase 5 continues
5. **Hour 8:** Phase 5 complete, Phase 6 starts
6. **Hour 10:** All complete ✅

---

## 📊 PROGRESS TRACKING

### Use This Format:
```markdown
## Agent X Status
- [ ] Task 1: [status]
- [ ] Task 2: [status]
- [ ] Task 3: [status]
- Estimated completion: [time]
```

---

**READY TO EXECUTE WITH 35 AGENTS IN 10 HOURS!** 🚀

