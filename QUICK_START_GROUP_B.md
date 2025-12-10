# QUICK START - GROUP B (Other Browser)
## 20 Agents - ML Service, Video Agent, Drive Intel, RAG

**Branch:** `group-b-wiring`  
**Prefix:** `[GROUP-B]`  
**Files:** See `PARALLEL_AGENTS_COORDINATION.md` for full list

---

## 🚀 START HERE

### Step 1: Create Branch
```bash
git checkout -b group-b-wiring
```

### Step 2: Your Files (EXCLUSIVE)
You own these files - no one else touches them:

#### ML Service Main (Agents 1-4)
- `services/ml-service/src/main.py` (Agent 1: Endpoints only)
- `services/ml-service/src/ctr_model.py` (Agent 2)
- `services/ml-service/src/thompson_sampler.py` (Agent 3)
- `services/ml-service/src/feature_engineering.py` (Agent 4)

#### ML Service Learning (Agents 5-8)
- `services/ml-service/src/cross_learner.py` (Agent 5)
- `services/ml-service/src/creative_dna.py` (Agent 6)
- `services/ml-service/src/compound_learner.py` (Agent 7)
- `services/ml-service/src/actuals_fetcher.py` (Agent 8)

#### ML Service Workers (Agents 9-10)
- `services/ml-service/src/celery_tasks.py` (Agent 9)
- `services/ml-service/src/training_scheduler.py` (Agent 10)

#### ML Service Utils (Agents 11-12)
- `services/ml-service/src/webhook_security.py` (Agent 11)
- `services/ml-service/src/data_loader.py` (Agent 12)

#### Video Agent (Agents 13-14)
- `services/video-agent/main.py` (Agent 13)
- `services/video-agent/pro/**/*.py` (Agent 14: All pro modules)

#### Drive Intel (Agents 15-16)
- `services/drive-intel/main.py` (Agent 15)
- `services/drive-intel/services/*.py` (Agent 16)

#### RAG Service (Agents 17-18)
- `services/rag/winner_index.py` (Agent 17)
- `services/rag/**/*.py` (Agent 18: All RAG files)

#### Database (Agent 19)
- `migrations/*.sql` (Agent 19: All SQL migrations)
- Database trigger creation

#### Testing (Agent 20)
- `services/ml-service/tests/**/*.py` (Agent 20: All ML tests)

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
1. **ML Service Main** (Agents 1-4) - Most critical
2. **ML Service Learning** (Agents 5-8) - Self-learning loops
3. **ML Service Workers** (Agents 9-10) - Background jobs
4. **ML Service Utils** (Agents 11-12) - Support
5. **Video Agent** (Agents 13-14) - Rendering
6. **Drive Intel** (Agents 15-16) - Ingestion
7. **RAG Service** (Agents 17-18) - Memory
8. **Database** (Agent 19) - Triggers
9. **Testing** (Agent 20) - Quality

---

## 🚫 DO NOT TOUCH

These files belong to GROUP A:
- `services/gateway-api/**/*.ts` (ALL Gateway API files)
- `frontend/**/*` (ALL Frontend files)
- `docker-compose.yml` (GROUP A owns)
- `shared/config/*.yaml` (GROUP A owns)
- `*.md` files (GROUP A owns)

**If you need something from GROUP A files:**
- Create a note/issue
- Don't modify their files
- GROUP A will handle it

---

## 📝 COMMIT FORMAT

```bash
git commit -m "[GROUP-B] Agent X: Description of changes"
```

Examples:
```bash
git commit -m "[GROUP-B] Agent 1: Add missing ML endpoints"
git commit -m "[GROUP-B] Agent 5: Wire cross-learner training"
git commit -m "[GROUP-B] Agent 19: Create database triggers"
```

---

## ⚡ QUICK COMMANDS

```bash
# Create your branch
git checkout -b group-b-wiring

# Check your branch
git branch

# Check what files you've changed
git status

# See your changes
git diff

# Commit your work
git add .
git commit -m "[GROUP-B] Agent X: Description"

# Push to remote (optional)
git push origin group-b-wiring
```

---

## 🎯 GOAL

Complete Phase 4 wiring for all GROUP B files:
- ✅ All endpoints wired
- ✅ All auto-triggers working
- ✅ All error handling added
- ✅ All tests passing
- ✅ Database triggers created

**Estimated Time:** 6-8 hours with 20 agents

---

## 🚨 IF YOU SEE CONFLICTS

1. **Stop immediately**
2. **Check** `PARALLEL_AGENTS_COORDINATION.md`
3. **Verify** file ownership
4. **Report** the conflict
5. **Don't merge** until resolved

---

## ⏰ TIMING

**Recommended:** Start 1 hour after GROUP A (they own critical path)

**Or:** Start immediately if you want (no conflicts anyway)

---

**READY? START WITH AGENT 1-4 (ML Service Main)!** 🚀

