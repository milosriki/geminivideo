# COMMANDS FOR OTHER BROWSER (GROUP B)
## Copy and paste these commands

---

## 🚀 STEP 1: Read the Plan

```bash
# Navigate to project
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo

# Read the coordination plan
cat PARALLEL_AGENTS_COORDINATION.md

# Read your quick start guide
cat QUICK_START_GROUP_B.md
```

---

## 🚀 STEP 2: Create Your Branch

```bash
# Make sure you're on main first
git checkout main

# Pull latest changes (in case GROUP A pushed)
git pull origin main

# Create your branch
git checkout -b group-b-wiring

# Verify you're on the right branch
git branch
# Should show: * group-b-wiring
```

---

## 🚀 STEP 3: Verify Your Files

```bash
# Check what files you own (GROUP B files)
ls -la services/ml-service/src/
ls -la services/video-agent/
ls -la services/drive-intel/
ls -la services/rag/
ls -la migrations/
```

---

## 🚀 STEP 4: Start Working

**Your assignment:**
- ML Service (all Python files)
- Video Agent (all Python files)
- Drive Intel (all Python files)
- RAG Service (all Python files)
- Database migrations (all SQL files)

**Priority order:**
1. ML Service Main (Agents 1-4)
2. ML Service Learning (Agents 5-8)
3. ML Service Workers (Agents 9-10)
4. Video Agent (Agents 13-14)
5. Drive Intel (Agents 15-16)
6. RAG Service (Agents 17-18)
7. Database (Agent 19)
8. Testing (Agent 20)

---

## 📝 COMMIT FORMAT

```bash
# Always use this prefix
git commit -m "[GROUP-B] Agent X: Description"

# Examples:
git commit -m "[GROUP-B] Agent 1: Add missing ML endpoints"
git commit -m "[GROUP-B] Agent 5: Wire cross-learner training"
git commit -m "[GROUP-B] Agent 19: Create database triggers"
```

---

## 🚫 DO NOT TOUCH

**These files belong to GROUP A (other browser):**
- `services/gateway-api/**/*` (ALL Gateway files)
- `frontend/**/*` (ALL Frontend files)
- `docker-compose.yml`
- `shared/config/*.yaml`
- `*.md` files (except you can read them)

**If you need something from GROUP A:**
- Don't modify their files
- Create a note/issue
- GROUP A will handle it

---

## ⚡ QUICK COMMANDS

```bash
# Check your branch
git branch

# Check what you've changed
git status

# See your changes
git diff

# Commit your work
git add .
git commit -m "[GROUP-B] Agent X: Description"

# Push to remote (optional, but recommended)
git push origin group-b-wiring
```

---

## 🎯 YOUR GOAL

Complete Phase 4 wiring for all GROUP B files:
- ✅ All endpoints wired
- ✅ All auto-triggers working
- ✅ All error handling added
- ✅ Database triggers created
- ✅ All tests passing

**Estimated Time:** 6-8 hours with 20 agents

---

## 🚨 IF YOU SEE CONFLICTS

1. **Stop immediately**
2. **Check** `PARALLEL_AGENTS_COORDINATION.md`
3. **Verify** file ownership
4. **Report** the conflict
5. **Don't merge** until resolved

**Note:** Conflicts shouldn't happen because files don't overlap!

---

## 📞 COORDINATION

- **File ownership questions:** Check `PARALLEL_AGENTS_COORDINATION.md`
- **Shared file needs:** GROUP A owns shared files, request changes
- **Status:** Update progress in coordination doc

---

## ✅ CHECKLIST

- [ ] Read `PARALLEL_AGENTS_COORDINATION.md`
- [ ] Read `QUICK_START_GROUP_B.md`
- [ ] Create branch `group-b-wiring`
- [ ] Verify file ownership
- [ ] Start with Agent 1-4 (ML Service Main)
- [ ] Use `[GROUP-B]` prefix in commits
- [ ] Don't touch GROUP A files

---

**READY? START WITH AGENT 1-4 (ML Service Main)!** 🚀

