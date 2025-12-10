# QUICK START - GROUP A (This Browser)
## 20 Agents - Gateway API, Frontend, Docker, Config

**Branch:** `group-a-wiring`  
**Prefix:** `[GROUP-A]`  
**Files:** See `PARALLEL_AGENTS_COORDINATION.md` for full list

---

## 🚀 START HERE

### Step 1: Verify Branch
```bash
git branch
# Should show: * group-a-wiring
```

### Step 2: Your Files (EXCLUSIVE)
You own these files - no one else touches them:

#### Gateway API Routes (Agents 1-3)
- `services/gateway-api/src/routes/campaigns.ts`
- `services/gateway-api/src/routes/ads.ts`
- `services/gateway-api/src/routes/analytics.ts`
- `services/gateway-api/src/routes/predictions.ts`
- `services/gateway-api/src/routes/ab-tests.ts`
- `services/gateway-api/src/routes/onboarding.ts`
- `services/gateway-api/src/routes/demo.ts`
- `services/gateway-api/src/routes/alerts.ts`
- `services/gateway-api/src/routes/reports.ts`
- `services/gateway-api/src/routes/image-generation.ts`
- `services/gateway-api/src/routes/streaming.ts`

#### Gateway API Core (Agents 4-5)
- `services/gateway-api/src/index.ts` (Agent 4: Endpoints only)
- `services/gateway-api/src/middleware/security.ts` (Agent 5)

#### Gateway API Services (Agents 6-7)
- `services/gateway-api/src/services/scoring-engine.ts` (Agent 6)
- `services/gateway-api/src/services/learning-service.ts` (Agent 7)

#### Gateway API Workers (Agents 8-9)
- `services/gateway-api/src/workers/self-learning-cycle.ts` (Agent 8)
- `services/gateway-api/src/jobs/batch-executor.ts` (Agent 9)
- `services/gateway-api/src/jobs/safe-executor.ts` (Agent 9)

#### Multi-Platform (Agents 10-11)
- `services/gateway-api/src/multi-platform/multi_publisher.ts` (Agent 10)
- `services/gateway-api/src/multi-platform/format_adapter.ts` (Agent 11)

#### Webhooks & Realtime (Agents 12-13)
- `services/gateway-api/src/webhooks/hubspot.ts` (Agent 12)
- `services/gateway-api/src/realtime/*.ts` (Agent 13)

#### Frontend (Agents 14-15)
- `frontend/src/lib/api.ts` (Agent 14)
- `frontend/src/**/*.tsx` (Agent 15)

#### Docker & Config (Agents 16-17)
- `docker-compose.yml` (Agent 16)
- `shared/config/*.yaml` (Agent 17)
- `.env.example` (Agent 17)

#### Documentation (Agents 18-19)
- `*.md` files (Agent 18)
- `README.md` (Agent 19)

#### Testing (Agent 20)
- `services/gateway-api/src/**/*.test.ts` (Agent 20)

---

## ✅ YOUR TASKS (Phase 4: Wiring)

### For Each File:
1. ✅ Add missing endpoints
2. ✅ Wire auto-triggers
3. ✅ Add error handling
4. ✅ Add input validation
5. ✅ Add logging
6. ✅ Add tests (if Agent 20)

### Priority Order:
1. **Gateway Routes** (Agents 1-3) - Most critical
2. **Gateway Core** (Agents 4-5) - Foundation
3. **Gateway Services** (Agents 6-7) - Business logic
4. **Gateway Workers** (Agents 8-9) - Background jobs
5. **Multi-Platform** (Agents 10-11) - Publishing
6. **Webhooks/Realtime** (Agents 12-13) - Integrations
7. **Frontend** (Agents 14-15) - UI
8. **Docker/Config** (Agents 16-17) - Infrastructure
9. **Documentation** (Agents 18-19) - Docs
10. **Testing** (Agent 20) - Quality

---

## 🚫 DO NOT TOUCH

These files belong to GROUP B:
- `services/ml-service/**/*.py` (ALL ML Service files)
- `services/video-agent/**/*.py` (ALL Video Agent files)
- `services/drive-intel/**/*.py` (ALL Drive Intel files)
- `services/rag/**/*.py` (ALL RAG files)
- `migrations/*.sql` (ALL migrations)

**If you need something from GROUP B files:**
- Create a note/issue
- Don't modify their files
- GROUP B will handle it

---

## 📝 COMMIT FORMAT

```bash
git commit -m "[GROUP-A] Agent X: Description of changes"
```

Examples:
```bash
git commit -m "[GROUP-A] Agent 1: Add missing campaign endpoints"
git commit -m "[GROUP-A] Agent 4: Wire auto-triggers in index.ts"
git commit -m "[GROUP-A] Agent 8: Enhance self-learning cycle worker"
```

---

## ⚡ QUICK COMMANDS

```bash
# Check your branch
git branch

# Check what files you've changed
git status

# See your changes
git diff

# Commit your work
git add .
git commit -m "[GROUP-A] Agent X: Description"

# Push to remote (optional)
git push origin group-a-wiring
```

---

## 🎯 GOAL

Complete Phase 4 wiring for all GROUP A files:
- ✅ All endpoints wired
- ✅ All auto-triggers working
- ✅ All error handling added
- ✅ All tests passing

**Estimated Time:** 6-8 hours with 20 agents

---

## 🚨 IF YOU SEE CONFLICTS

1. **Stop immediately**
2. **Check** `PARALLEL_AGENTS_COORDINATION.md`
3. **Verify** file ownership
4. **Report** the conflict
5. **Don't merge** until resolved

---

**READY? START WITH AGENT 1-3 (Gateway Routes)!** 🚀

