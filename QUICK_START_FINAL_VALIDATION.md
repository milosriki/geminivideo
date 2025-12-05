# Quick Start: Final Validation System

**Purpose:** Run comprehensive validation before investor demo

---

## TL;DR

```bash
# 1. Start all services
docker-compose up -d

# 2. Wait 30 seconds for services to start
sleep 30

# 3. Run validation
./scripts/pre-flight.sh

# Expected output: ✓✓✓ GO FOR LAUNCH ✓✓✓
```

---

## What Gets Validated

### ✅ Infrastructure (4 checks)
- PostgreSQL connection
- Database migrations
- pgvector extension
- Redis connection

### ✅ Environment (7 checks)
- AI API keys (Gemini, OpenAI, Anthropic)
- Meta credentials (optional)
- Storage configuration

### ✅ Services (8 checks)
- Gateway API (8080)
- Titan Core (8084)
- ML Service (8003)
- Video Agent (8082)
- Meta Publisher (8083)
- Frontend (3000)
- Drive Intel (8081)
- TikTok Ads (8085)

### ✅ AI Council (4 checks)
- Gemini 2.0 responding
- Claude responding
- GPT-4o responding
- DeepCTR model loaded

### ✅ Critical Flows (5 checks)
- Campaign creation
- Video upload
- AI scoring
- Meta publishing
- Analytics endpoints

### ✅ Investor Demo (4 checks)
- Demo data loaded
- No mock warnings
- HTTPS config
- Error pages styled

**Total: 32 Comprehensive Checks**

---

## Commands

### Run Full Validation
```bash
./scripts/pre-flight.sh
```

### Run Validation with JSON Export
```bash
python scripts/final-checklist.py --json
```

### Check Services Only
```bash
./scripts/test-connections.sh
```

### View Latest Report
```bash
ls -lt reports/ | head -5
cat reports/pre-flight-*.txt | head -100
```

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | GO - All systems operational | Proceed with demo |
| 1 | NO-GO - Critical failures | Fix issues, re-run |
| 130 | Interrupted by user | Re-run when ready |
| 2 | Fatal error | Check logs, contact support |

---

## Output Explanation

### GO Decision
```
✓✓✓ GO FOR LAUNCH ✓✓✓
All systems operational. Ready for €5M investor demo.
```

**Meaning:** All 32 checks passed. You're ready!

**Next Steps:**
1. Review `INVESTOR_DEMO.md`
2. Open http://localhost:3000
3. Test key flows manually
4. Proceed with confidence

---

### Conditional GO
```
⚠ CONDITIONAL GO ⚠
Core systems operational but some non-critical checks failed.
```

**Meaning:** Critical systems work, but some optional features failed.

**Examples:**
- Claude API not configured (non-critical, have Gemini + GPT)
- TikTok Ads service down (optional platform)
- Demo data missing (can create manually)

**Action:** Review failures, decide if acceptable for demo.

---

### NO-GO Decision
```
✗✗✗ NO-GO ✗✗✗
Critical systems failed. DO NOT proceed with demo.
```

**Meaning:** Core infrastructure or services are down.

**Examples:**
- PostgreSQL not running
- Gateway API crashed
- Gemini API key invalid

**Action:** Fix issues immediately, re-run validation.

---

## Troubleshooting

### Services Not Starting
```bash
# Check Docker status
docker-compose ps

# View logs
docker-compose logs -f

# Restart all services
docker-compose down
docker-compose up -d
```

### Database Connection Failed
```bash
# Check PostgreSQL
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
sleep 10
python scripts/init_db.py --demo
```

### AI API Keys Invalid
```bash
# Check .env file
cat .env | grep API_KEY

# Copy from .env.example
cp .env.example .env
# Edit with real keys
nano .env
```

### Port Already in Use
```bash
# Find process using port 8080
lsof -i :8080

# Kill process
kill -9 <PID>

# Or use different port
export GATEWAY_PORT=8090
docker-compose up -d
```

---

## Quick Fixes

### Fix 1: Install Dependencies
```bash
pip install httpx psycopg2-binary redis
```

### Fix 2: Load Demo Data
```bash
python scripts/init_db.py --demo
```

### Fix 3: Restart Services
```bash
docker-compose restart
```

### Fix 4: Clear Cache
```bash
docker-compose exec redis redis-cli FLUSHALL
```

### Fix 5: Check Logs
```bash
docker-compose logs gateway-api | tail -50
```

---

## Pre-Demo Checklist

### 24 Hours Before
- [ ] Run pre-flight check
- [ ] All checks pass
- [ ] Demo data loaded
- [ ] Practice demo flow

### 1 Hour Before
- [ ] Restart all services (fresh state)
- [ ] Run pre-flight again
- [ ] Test on demo laptop
- [ ] Clear browser cache

### 5 Minutes Before
- [ ] Run pre-flight one last time
- [ ] Open frontend (http://localhost:3000)
- [ ] Have backup plan ready
- [ ] Close unnecessary apps

---

## Files Created by Agent 60

| File | Purpose | Lines |
|------|---------|-------|
| `/scripts/final-checklist.py` | Validation script | 1,287 |
| `/scripts/pre-flight.sh` | Shell wrapper | 330 |
| `/INVESTOR_DEMO.md` | Demo guide | 500+ |
| `/AGENT_60_FINAL_DEPLOYMENT_SUMMARY.md` | Summary report | 1,000+ |
| `/reports/README.md` | Reports directory | 20 |
| This file | Quick start guide | You're reading it |

---

## Success Criteria

✅ **You're ready if:**
- All 32 checks pass
- Exit code 0
- Green "GO FOR LAUNCH" message
- Reports generated successfully

❌ **Not ready if:**
- Any critical check fails
- Exit code 1
- Red "NO-GO" message
- Services unreachable

---

## Get Help

### Check Documentation
```bash
cat INVESTOR_DEMO.md
cat DEPLOYMENT.md
cat AGENT_60_FINAL_DEPLOYMENT_SUMMARY.md
```

### View Service Logs
```bash
docker-compose logs <service-name>
```

### Test Individual Service
```bash
curl http://localhost:8080/health
curl http://localhost:8084/health
curl http://localhost:8003/health
```

---

## Example Session

```bash
$ ./scripts/pre-flight.sh

╔════════════════════════════════════════════════════════════════════════════╗
║                    GEMINI VIDEO PRE-FLIGHT CHECK                           ║
║                 Final Validation for €5M Investor Demo                     ║
╚════════════════════════════════════════════════════════════════════════════╝

▶ Checking Dependencies
────────────────────────────────────────────────────────────────────────────
✓ Python 3 installed (v3.10.12)
✓ httpx installed
✓ psycopg2 installed
✓ redis installed
✓ Docker installed
✓ docker-compose installed

▶ Checking Services Status
────────────────────────────────────────────────────────────────────────────
✓ postgres running on port 5432
✓ redis running on port 6379
✓ gateway-api running on port 8080
✓ frontend running on port 3000

▶ Running Comprehensive Validation
────────────────────────────────────────────────────────────────────────────

[... 32 checks execute ...]

════════════════════════════════════════════════════════════════════════════
SUMMARY
════════════════════════════════════════════════════════════════════════════

  Total Checks:      32
  Passed:            32
  Failed:            0
  Critical Failed:   0

  Total Duration:    8243ms (8.24s)

════════════════════════════════════════════════════════════════════════════

✓✓✓ GO FOR LAUNCH ✓✓✓
All systems operational. Ready for €5M investor demo.

Next Steps:
  1. Review demo script: cat INVESTOR_DEMO.md
  2. Open frontend: http://localhost:3000
  3. Test key flows manually
  4. Proceed with confidence!

Reports saved to:
  • Text:  reports/pre-flight-20251205_143022.txt
  • JSON:  reports/pre-flight-20251205_143022.json

$ echo $?
0
```

---

**You're ready to impress investors! 🚀**

---

*Quick Start Guide created by Agent 60*
