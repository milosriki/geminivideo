# COMMANDS FOR OTHER BROWSER (GROUP A - MECHANICAL TASKS)
## You're doing mechanical execution - no deep understanding needed!

---

## 🚀 STEP 1: Create Your Branch

```bash
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo
git checkout main
git pull origin main
git checkout -b group-a-wiring
git branch
# Should show: * group-a-wiring
```

---

## 🚀 STEP 2: Your Assignment (GROUP A)

**You own these files (mechanical tasks only):**
- `services/gateway-api/**/*.ts` (ALL Gateway files)
- `frontend/**/*` (ALL Frontend files)
- `docker-compose.yml`
- `shared/config/*.yaml`
- `*.md` files

**What you do:**
- ✅ Add endpoints (just copy patterns)
- ✅ Wire routes (just connect)
- ✅ Add error handling (just add try/catch)
- ✅ Update frontend (just wire API calls)
- ✅ Update Docker (just add config)
- ✅ Write docs (just document)

**What you DON'T need:**
- ❌ No understanding of ML models
- ❌ No understanding of learning loops
- ❌ No understanding of system architecture
- ❌ Just execute tasks mechanically

---

## 🚀 STEP 3: Start Working

### Priority 1: Gateway Routes (Agents 1-3)
**Just do this:**
1. Open `services/gateway-api/src/routes/campaigns.ts`
2. Look at existing endpoints
3. Copy the pattern
4. Add missing endpoint
5. Done

**Example pattern to copy:**
```typescript
app.post('/api/campaigns', async (req, res) => {
  try {
    const result = await pgPool.query('INSERT INTO campaigns ...', [...]);
    res.json({ success: true, data: result.rows[0] });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

### Priority 2: Frontend (Agents 14-15)
**Just do this:**
1. Open frontend file
2. Add API call using `api.ts`
3. Wire to component
4. Done

**Example:**
```typescript
import api from '@/lib/api';

const response = await api.post('/api/campaigns', data);
```

### Priority 3: Docker/Config (Agents 16-17)
**Just do this:**
1. Open `docker-compose.yml`
2. Add env var
3. Update config file
4. Done

---

## 📝 COMMIT FORMAT

```bash
git commit -m "[GROUP-A] Agent X: Description"
```

**Examples:**
```bash
git commit -m "[GROUP-A] Agent 1: Add campaign activation endpoint"
git commit -m "[GROUP-A] Agent 14: Wire campaign list to frontend"
git commit -m "[GROUP-A] Agent 16: Add REDIS_URL to docker-compose"
```

---

## 🚫 DO NOT TOUCH

**These files belong to GROUP B (other browser):**
- `services/ml-service/**/*.py` (ALL ML Service)
- `services/video-agent/**/*.py` (ALL Video Agent)
- `services/drive-intel/**/*.py` (ALL Drive Intel)
- `services/rag/**/*.py` (ALL RAG)
- `migrations/*.sql` (ALL migrations)

**If you need something from GROUP B:**
- Don't modify their files
- Just note what you need
- They'll handle it

---

## ⚡ QUICK COMMANDS

```bash
# Check your branch
git branch

# Check what you changed
git status

# Commit your work
git add .
git commit -m "[GROUP-A] Agent X: Description"

# Push (optional)
git push origin group-a-wiring
```

---

## 🎯 YOUR GOAL

**Just execute these tasks:**
1. Add all missing Gateway endpoints
2. Wire all routes
3. Update frontend to use endpoints
4. Update Docker config
5. Write documentation

**No thinking needed - just execution!**

**Estimated Time:** 6-8 hours with 20 agents

---

## ✅ CHECKLIST

- [ ] Create branch `group-a-wiring`
- [ ] Read `QUICK_START_GROUP_A.md`
- [ ] Start with Gateway routes (just copy patterns)
- [ ] Use `[GROUP-A]` prefix in commits
- [ ] Don't touch GROUP B files
- [ ] Just execute - no deep thinking!

---

**READY? START WITH GATEWAY ROUTES - JUST COPY PATTERNS!** 🚀

