# PARALLEL AGENTS COORDINATION PLAN
## 40 Agents (20 + 20) - Zero Conflict Strategy

**Goal:** Deploy 20 agents here + 20 agents in another Claude Code Browser  
**Strategy:** Service/File Ownership + Feature Boundaries  
**Merge Strategy:** Git branches + conflict-free file assignments

---

## 🎯 STRATEGY OVERVIEW

### Core Principle: **NO FILE OVERLAP**

Each agent group owns **exclusive files/services**. No two agents touch the same file.

### Split Method:
1. **By Service** - Different services = different agents
2. **By Feature** - Different features in same service = different files
3. **By Directory** - Different directories = different agents

---

## 📋 GROUP ASSIGNMENTS

### GROUP A (This Claude Code Browser) - 20 Agents
**Owns:** Gateway API, Frontend, Docker, Config, Documentation

### GROUP B (Other Claude Code Browser) - 20 Agents  
**Owns:** ML Service, Video Agent, Drive Intel, RAG, Database

---

## 🔀 DETAILED FILE OWNERSHIP

### GROUP A FILES (20 Agents) - NO CONFLICTS

#### Agent 1-3: Gateway API Routes (3 agents)
- ✅ `services/gateway-api/src/routes/campaigns.ts`
- ✅ `services/gateway-api/src/routes/ads.ts`
- ✅ `services/gateway-api/src/routes/analytics.ts`
- ✅ `services/gateway-api/src/routes/predictions.ts`
- ✅ `services/gateway-api/src/routes/ab-tests.ts`
- ✅ `services/gateway-api/src/routes/onboarding.ts`
- ✅ `services/gateway-api/src/routes/demo.ts`
- ✅ `services/gateway-api/src/routes/alerts.ts`
- ✅ `services/gateway-api/src/routes/reports.ts`
- ✅ `services/gateway-api/src/routes/image-generation.ts`
- ✅ `services/gateway-api/src/routes/streaming.ts`

#### Agent 4-5: Gateway API Core (2 agents)
- ✅ `services/gateway-api/src/index.ts` (Agent 4: Endpoints only)
- ✅ `services/gateway-api/src/middleware/security.ts` (Agent 5)

#### Agent 6-7: Gateway API Services (2 agents)
- ✅ `services/gateway-api/src/services/scoring-engine.ts` (Agent 6)
- ✅ `services/gateway-api/src/services/learning-service.ts` (Agent 7)

#### Agent 8-9: Gateway API Workers (2 agents)
- ✅ `services/gateway-api/src/workers/self-learning-cycle.ts` (Agent 8: Enhance)
- ✅ `services/gateway-api/src/jobs/batch-executor.ts` (Agent 9)
- ✅ `services/gateway-api/src/jobs/safe-executor.ts` (Agent 9)

#### Agent 10-11: Gateway API Multi-Platform (2 agents)
- ✅ `services/gateway-api/src/multi-platform/multi_publisher.ts` (Agent 10)
- ✅ `services/gateway-api/src/multi-platform/format_adapter.ts` (Agent 11)

#### Agent 12-13: Gateway API Webhooks & Realtime (2 agents)
- ✅ `services/gateway-api/src/webhooks/hubspot.ts` (Agent 12)
- ✅ `services/gateway-api/src/realtime/*.ts` (Agent 13)

#### Agent 14-15: Frontend (2 agents)
- ✅ `frontend/src/lib/api.ts` (Agent 14: Enhance)
- ✅ `frontend/src/**/*.tsx` (Agent 15: All frontend files)

#### Agent 16-17: Docker & Config (2 agents)
- ✅ `docker-compose.yml` (Agent 16)
- ✅ `shared/config/*.yaml` (Agent 17)
- ✅ `.env.example` (Agent 17)

#### Agent 18-19: Documentation (2 agents)
- ✅ `*.md` files (Agent 18: All markdown docs)
- ✅ `README.md` (Agent 19)

#### Agent 20: Integration & Testing (1 agent)
- ✅ `services/gateway-api/src/**/*.test.ts` (Agent 20: Gateway tests)

---

### GROUP B FILES (20 Agents) - NO CONFLICTS

#### Agent 1-4: ML Service Main (4 agents)
- ✅ `services/ml-service/src/main.py` (Agent 1: Endpoints only)
- ✅ `services/ml-service/src/ctr_model.py` (Agent 2)
- ✅ `services/ml-service/src/thompson_sampler.py` (Agent 3)
- ✅ `services/ml-service/src/feature_engineering.py` (Agent 4)

#### Agent 5-8: ML Service Learning (4 agents)
- ✅ `services/ml-service/src/cross_learner.py` (Agent 5)
- ✅ `services/ml-service/src/creative_dna.py` (Agent 6)
- ✅ `services/ml-service/src/compound_learner.py` (Agent 7)
- ✅ `services/ml-service/src/actuals_fetcher.py` (Agent 8)

#### Agent 9-10: ML Service Workers (2 agents)
- ✅ `services/ml-service/src/celery_tasks.py` (Agent 9)
- ✅ `services/ml-service/src/training_scheduler.py` (Agent 10)

#### Agent 11-12: ML Service Security & Utils (2 agents)
- ✅ `services/ml-service/src/webhook_security.py` (Agent 11: Enhance)
- ✅ `services/ml-service/src/data_loader.py` (Agent 12)

#### Agent 13-14: Video Agent (2 agents)
- ✅ `services/video-agent/main.py` (Agent 13)
- ✅ `services/video-agent/pro/**/*.py` (Agent 14: All pro modules)

#### Agent 15-16: Drive Intel (2 agents)
- ✅ `services/drive-intel/main.py` (Agent 15)
- ✅ `services/drive-intel/services/*.py` (Agent 16)

#### Agent 17-18: RAG Service (2 agents)
- ✅ `services/rag/winner_index.py` (Agent 17)
- ✅ `services/rag/**/*.py` (Agent 18: All RAG files)

#### Agent 19: Database & Migrations (1 agent)
- ✅ `migrations/*.sql` (Agent 19: All SQL migrations)
- ✅ Database trigger creation

#### Agent 20: ML Service Testing (1 agent)
- ✅ `services/ml-service/tests/**/*.py` (Agent 20: All ML tests)

---

## 🚫 CONFLICT PREVENTION RULES

### Rule 1: File Ownership
- **One file = One agent group**
- If file is in GROUP A list → Only GROUP A touches it
- If file is in GROUP B list → Only GROUP B touches it

### Rule 2: Shared Files (Handle Carefully)
**Files that BOTH groups might need:**
- `docker-compose.yml` → **GROUP A ONLY** (Agent 16)
- `shared/config/learning_config.yaml` → **GROUP A ONLY** (Agent 17)
- `README.md` → **GROUP A ONLY** (Agent 19)

**Solution:** GROUP A owns all shared files. GROUP B reads but doesn't modify.

### Rule 3: Service Boundaries
- Gateway API → GROUP A
- ML Service → GROUP B
- Video Agent → GROUP B
- Drive Intel → GROUP B
- RAG → GROUP B
- Frontend → GROUP A

### Rule 4: Git Strategy
- **GROUP A:** Work on branch `group-a-wiring`
- **GROUP B:** Work on branch `group-b-wiring`
- **Merge:** Both branches merge to `main` (no conflicts due to file separation)

---

## 📝 AGENT INSTRUCTIONS TEMPLATE

### For GROUP A Agents (This Browser)

```markdown
# AGENT ASSIGNMENT - GROUP A

## Your Files (EXCLUSIVE - No one else touches these):
[List of files from GROUP A section above]

## Your Tasks:
1. Complete Phase 4 wiring for your assigned files
2. Add missing endpoints
3. Wire auto-triggers
4. Add error handling
5. Add tests

## Rules:
- ✅ ONLY touch files in your assignment
- ✅ If you need a file from GROUP B, create an issue/note
- ✅ Commit to branch: `group-a-wiring`
- ✅ Use prefix: `[GROUP-A]` in commit messages

## Coordination:
- Check `PARALLEL_AGENTS_COORDINATION.md` before starting
- If file is in GROUP B list, DON'T TOUCH IT
- Report conflicts immediately
```

### For GROUP B Agents (Other Browser)

```markdown
# AGENT ASSIGNMENT - GROUP B

## Your Files (EXCLUSIVE - No one else touches these):
[List of files from GROUP B section above]

## Your Tasks:
1. Complete Phase 4 wiring for your assigned files
2. Add missing endpoints
3. Wire auto-triggers
4. Add error handling
5. Add tests

## Rules:
- ✅ ONLY touch files in your assignment
- ✅ If you need a file from GROUP A, create an issue/note
- ✅ Commit to branch: `group-b-wiring`
- ✅ Use prefix: `[GROUP-B]` in commit messages

## Coordination:
- Check `PARALLEL_AGENTS_COORDINATION.md` before starting
- If file is in GROUP A list, DON'T TOUCH IT
- Report conflicts immediately
```

---

## 🔄 MERGE STRATEGY

### Step 1: Create Branches
```bash
# GROUP A (This browser)
git checkout -b group-a-wiring

# GROUP B (Other browser)
git checkout -b group-b-wiring
```

### Step 2: Work in Parallel
- GROUP A commits to `group-a-wiring`
- GROUP B commits to `group-b-wiring`
- No conflicts because files don't overlap

### Step 3: Merge (No Conflicts Expected)
```bash
# After both groups finish
git checkout main
git merge group-a-wiring  # Should merge cleanly
git merge group-b-wiring  # Should merge cleanly
```

### Step 4: Verify
```bash
git log --oneline --graph --all
# Should show both branches merged cleanly
```

---

## 📊 PROGRESS TRACKING

### GROUP A Progress
- [ ] Agent 1-3: Gateway Routes (0/11 files)
- [ ] Agent 4-5: Gateway Core (0/2 files)
- [ ] Agent 6-7: Gateway Services (0/2 files)
- [ ] Agent 8-9: Gateway Workers (0/3 files)
- [ ] Agent 10-11: Multi-Platform (0/2 files)
- [ ] Agent 12-13: Webhooks/Realtime (0/2 files)
- [ ] Agent 14-15: Frontend (0/2 files)
- [ ] Agent 16-17: Docker/Config (0/3 files)
- [ ] Agent 18-19: Documentation (0/2 files)
- [ ] Agent 20: Testing (0/1 files)

### GROUP B Progress
- [ ] Agent 1-4: ML Service Main (0/4 files)
- [ ] Agent 5-8: ML Service Learning (0/4 files)
- [ ] Agent 9-10: ML Service Workers (0/2 files)
- [ ] Agent 11-12: ML Service Utils (0/2 files)
- [ ] Agent 13-14: Video Agent (0/2 files)
- [ ] Agent 15-16: Drive Intel (0/2 files)
- [ ] Agent 17-18: RAG Service (0/2 files)
- [ ] Agent 19: Database (0/1 files)
- [ ] Agent 20: Testing (0/1 files)

---

## ⚡ FASTEST DEPLOYMENT STRATEGY

### Option 1: Sequential (Safest)
1. GROUP A starts first, completes in 6-8 hours
2. GROUP B starts after GROUP A finishes
3. Merge both branches
4. **Total: 12-16 hours**

### Option 2: Parallel (Fastest) ⚡
1. GROUP A and GROUP B start simultaneously
2. Both work in parallel (no conflicts)
3. Merge both branches when done
4. **Total: 6-8 hours** (same as single group, but 2x work done)

### Option 3: Hybrid (Recommended) 🎯
1. GROUP A starts immediately (Gateway/Frontend - critical path)
2. GROUP B starts 1 hour later (ML/Video - can wait)
3. Both finish around same time
4. Merge both branches
5. **Total: 7-9 hours**

---

## 🎯 RECOMMENDED APPROACH

**Use Option 3: Hybrid**

**Why:**
- Gateway API is critical path (needed first)
- ML Service can start slightly later
- Minimal coordination needed
- Fastest overall completion

**Execution:**
1. **NOW:** Start GROUP A (20 agents) on Gateway/Frontend
2. **+1 hour:** Start GROUP B (20 agents) on ML/Video
3. **+6-8 hours:** Both groups finish
4. **Merge:** Clean merge, no conflicts

---

## ✅ CHECKLIST BEFORE STARTING

### GROUP A Checklist
- [ ] Read `PARALLEL_AGENTS_COORDINATION.md`
- [ ] Create branch: `group-a-wiring`
- [ ] Verify file ownership list
- [ ] Start with Agent 1-3 (Gateway Routes)

### GROUP B Checklist
- [ ] Read `PARALLEL_AGENTS_COORDINATION.md`
- [ ] Create branch: `group-b-wiring`
- [ ] Verify file ownership list
- [ ] Wait 1 hour OR start immediately (your choice)
- [ ] Start with Agent 1-4 (ML Service Main)

---

## 🚨 CONFLICT RESOLUTION

### If Conflict Occurs (Shouldn't Happen)

1. **Stop immediately**
2. **Check file ownership** in this document
3. **Identify which group should own the file**
4. **One group reverts their changes**
5. **Update this document** to clarify ownership
6. **Resume work**

### Prevention
- Always check this document before editing
- Use `git status` before committing
- Use descriptive commit messages with `[GROUP-A]` or `[GROUP-B]` prefix

---

## 📞 COORDINATION

### Communication Protocol
- **File ownership questions:** Check this document first
- **Shared file needs:** GROUP A owns shared files, GROUP B requests changes
- **Merge conflicts:** Shouldn't happen, but if they do, follow conflict resolution

### Status Updates
- Update progress tracking section above
- Commit frequently with clear messages
- Use branch prefixes: `[GROUP-A]` or `[GROUP-B]`

---

**READY TO START?**
1. GROUP A: Create branch `group-a-wiring` and begin
2. GROUP B: Create branch `group-b-wiring` and begin (or wait 1 hour)
3. Work in parallel with zero conflicts! 🚀

