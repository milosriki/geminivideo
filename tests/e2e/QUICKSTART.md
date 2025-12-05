# Quick Start Guide - Investor Validation

## 5-Minute Setup for Investor Demo

### Step 1: Install Dependencies (1 min)

```bash
# Install Python test dependencies
pip install -r tests/e2e/requirements.txt
```

### Step 2: Start Services (2 min)

```bash
# Terminal 1: Gateway API
cd services/gateway-api
npm install
npm start

# Terminal 2: Meta Publisher
cd services/meta-publisher
npm install
npm start
```

Wait for services to start (~30 seconds each).

### Step 3: Run Validation (2 min)

```bash
# Run complete investor validation
./tests/e2e/run_investor_validation.sh
```

### Expected Output

```
================================================================================
🎯 INVESTOR VALIDATION - MASTER RUNNER
================================================================================

📊 Checking if services are running...
  ✅ Gateway API: RUNNING
  ✅ Meta Publisher: RUNNING

🧪 RUNNING VALIDATION TESTS

TEST 1: Complete User Journey
  ✅ Complete User Journey: PASSED

TEST 2: AI Validation (Proving AI is Real)
  ✅ AI Validation: PASSED

TEST 3: Publishing Validation
  ✅ Publishing Validation: PASSED

TEST 4: ROAS Tracking
  ✅ ROAS Tracking: PASSED

📊 GENERATING REPORTS

================================================================================
DECISION: ✅ GO FOR PRODUCTION
================================================================================

All validation tests passed successfully.
```

---

## Alternative: Quick Demo Mode

If you just want to show the platform without running tests:

```bash
# Setup demo environment
python scripts/investor-demo.py --setup

# Start live demo dashboard
python scripts/investor-demo.py --start
```

**Demo dashboard will show:**
- 3 live campaigns with real-time updates
- Performance metrics updating every 5 seconds
- ROAS calculations
- Campaign portfolio overview

Press `Ctrl+C` to stop.

---

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -i :8000  # Gateway API
lsof -i :8083  # Meta Publisher

# Kill existing processes if needed
kill -9 <PID>
```

### DATABASE_URL Not Set

```bash
# Set temporarily
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Or add to .env file
echo 'DATABASE_URL="postgresql://user:pass@host:5432/dbname"' >> .env
```

### Tests Fail

1. **Check service logs** - Look for errors in service terminals
2. **Verify DATABASE_URL** - `echo $DATABASE_URL`
3. **Check network** - `curl http://localhost:8000/health`
4. **See detailed logs** - Check `reports/investor_validation_*/test_execution.log`

---

## What Each Test Does

### 1. Complete User Journey
- ✅ Simulates real user workflow
- ✅ Tests all integrations
- ✅ Validates end-to-end

### 2. AI Validation
- ✅ Proves AI is real (not mocked)
- ✅ Tests response variance
- ✅ Validates model quality

### 3. Publishing
- ✅ Tests Meta Ads API
- ✅ Tests Google Ads API
- ✅ All campaigns PAUSED (no spending)

### 4. ROAS Tracking
- ✅ Validates prediction logging
- ✅ Tests learning loop
- ✅ Measures accuracy

---

## Next Steps After Validation

✅ **If all tests pass:**
1. Review detailed report in `reports/` folder
2. Run demo mode for investors: `python scripts/investor-demo.py --start`
3. Deploy to production

⚠️ **If tests fail:**
1. Check `test_execution.log` for details
2. Fix critical failures
3. Re-run validation

---

## For Investor Presentation

### Best Approach

1. **Start with demo mode** (shows live platform)
   ```bash
   python scripts/investor-demo.py --start
   ```

2. **Then run validation** (proves everything works)
   ```bash
   ./tests/e2e/run_investor_validation.sh
   ```

3. **Show the report** (confidence in production readiness)
   ```bash
   cat reports/investor_validation_*/SUMMARY.txt
   ```

### Key Talking Points

- ✅ "All 4 E2E tests passing (100% success rate)"
- ✅ "AI is real and learning (not mock data)"
- ✅ "Real integrations with Meta & Google"
- ✅ "ROAS tracking and optimization working"
- ✅ "Production-ready infrastructure"

---

## Full Documentation

For complete documentation, see:
- **Full Guide:** `tests/e2e/README.md`
- **Test Details:** Individual test files in `tests/e2e/`
- **Scripts:** `scripts/investor-demo.py` and `scripts/validate-production.py`
