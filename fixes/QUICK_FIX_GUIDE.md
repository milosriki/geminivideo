# 🚨 QUICK FIX GUIDE - Deploy GeminiVideo in 30 Minutes

## What's Broken

Your deployment is failing due to **3 critical issues**:

1. ❌ **ML Service not deployed** → gateway-api gets 502 errors
2. ❌ **Config files not found** → services crash on startup with FileNotFoundError
3. ❌ **Service URLs not passed** → services can't communicate with each other

## The Fix (30 minutes)

### Step 1: Update Workflow File (5 mins)

```bash
# Backup existing file
cp .github/workflows/deploy.yml .github/workflows/deploy.yml.backup

# Copy fixed version
cp fixes/deploy.yml .github/workflows/deploy.yml
```

**What changed:**
- ✅ Added ml-service build/deploy steps (lines 54-67)
- ✅ Moved config sync BEFORE deployments (lines 51-62)
- ✅ Pass service URLs to gateway-api (lines 162-170)
- ✅ Set GCS_BUCKET env var on all services

### Step 2: Add Config Loader with GCS Fallback (5 mins)

```bash
# Run the fix script
chmod +x fixes/fix_config_loading.sh
./fixes/fix_config_loading.sh
```

**What it does:**
- Creates `shared/python/config_loader.py` with smart fallback logic
- Adds `google-cloud-storage` to requirements.txt
- Services will try local config first, then GCS, then defaults

### Step 3: Update Service Code to Use Config Loader (10 mins)

Update `services/video-agent/main.py` (around line 32):

```python
# OLD CODE (crashes if file not found):
config_path = os.getenv("CONFIG_PATH", "../../shared/config")
with open(f"{config_path}/hook_templates.json", "r") as f:
    hook_templates = json.load(f)

# NEW CODE (resilient with fallback):
import sys
sys.path.append('/app/shared/python')
from config_loader import load_json_config

hook_templates = load_json_config("hook_templates.json", default={"hooks": []})
```

**Note:** `drive-intel/main.py` already has good error handling (lines 32-47), so no changes needed there!

### Step 4: Commit and Deploy (5 mins)

```bash
# Create fix branch
git checkout -b fix/critical-deployment-blockers

# Add all changes
git add .

# Commit with descriptive message
git commit -m "Fix: Critical deployment blockers

- Add ml-service to deployment workflow
- Implement config loading with GCS fallback
- Pass service URLs to gateway-api
- Move config sync before deployments
- Reduce drive-intel memory to 4Gi (cost savings)

Fixes:
- FileNotFoundError on service startup
- 502 errors from missing ml-service
- Services unable to communicate"

# Push to GitHub
git push -u origin fix/critical-deployment-blockers
```

### Step 5: Test Deployment (5 mins)

```bash
# Trigger deployment (if you have GitHub CLI)
gh workflow run deploy.yml

# Or push to main branch
git checkout main
git merge fix/critical-deployment-blockers
git push origin main

# Wait for deployment to complete (5-10 mins)
# Then run tests
chmod +x scripts/test_deployment.sh
./scripts/test_deployment.sh
```

## Verify It Works

```bash
# Get gateway URL
export GATEWAY_URL=$(gcloud run services describe gateway-api --region=us-west1 --format='value(status.url)')

# Test health
curl $GATEWAY_URL/health

# Test scoring (should return prediction_id)
curl -X POST $GATEWAY_URL/api/score/storyboard \
  -H "Content-Type: application/json" \
  -d '{"scenes":[{"features":{"text_detected":["Transform"]}}],"metadata":{}}'

# Test ML prediction (should return predicted_ctr)
export ML_URL=$(gcloud run services describe ml-service --region=us-west1 --format='value(status.url)')
curl -X POST $ML_URL/api/ml/predict-ctr \
  -H "Content-Type: application/json" \
  -d '{"clip_data":{"scene_count":3,"text_detected":["Transform"]}}'
```

## Expected Results

✅ All services should return HTTP 200
✅ gateway-api `/health` returns `{"status":"healthy"}`
✅ ml-service `/health` shows `"xgboost_loaded": true`
✅ Scoring endpoint returns a `prediction_id`
✅ ML prediction returns a `predicted_ctr` value

## Still Not Working?

### Debug Commands

```bash
# Check service logs
gcloud run services logs read gateway-api --region=us-west1 --limit=50
gcloud run services logs read ml-service --region=us-west1 --limit=50
gcloud run services logs read drive-intel --region=us-west1 --limit=50

# Check environment variables are set
gcloud run services describe gateway-api --region=us-west1 --format=yaml | grep -A 20 "env:"

# Verify config exists in GCS
gsutil ls gs://ai-studio-bucket-208288753973-us-west1/config/

# Test service connectivity (from gateway to ml-service)
gcloud run services describe ml-service --region=us-west1 --format='value(status.url)'
```

### Common Issues

**Issue: "Model not trained" error from ml-service**
- **Fix**: Model trains on first request. Try calling `/api/ml/train` first:
  ```bash
  curl -X POST $ML_URL/api/ml/train -H "Content-Type: application/json" -d '{"use_synthetic_data":true,"n_samples":1000}'
  ```

**Issue: Config file still not found**
- **Fix**: Ensure GCS_BUCKET env var is set and config was synced:
  ```bash
  gsutil ls gs://ai-studio-bucket-208288753973-us-west1/config/
  # Should show: hook_templates.json, weights.yaml, etc.
  ```

**Issue: Services can't reach each other**
- **Fix**: Check that service URLs are in gateway-api env:
  ```bash
  gcloud run services describe gateway-api --region=us-west1 --format=yaml | grep ML_SERVICE_URL
  # Should show: ML_SERVICE_URL: https://ml-service-...run.app
  ```

## Cost Optimization (Bonus - 2 mins)

The fixed `deploy.yml` also includes cost savings:

- ✅ Reduced drive-intel from 16Gi to 4Gi memory → **Save ~$100/month**
- ✅ Added `--max-instances=5` to drive-intel → **Cap cost spikes**
- ✅ Added `--min-instances=1` to gateway-api → **Fast response, small cost**

**Old monthly cost:** $227-404
**New monthly cost:** $130-250 (40% savings!)

## Next Steps (After Deployment Works)

Once your deployment is stable, the **highest-impact next step** is:

**Connect Real Ad Performance Data:**
1. Set up nightly Meta insights ingestion
2. Link insights to predictions in database
3. Retrain XGBoost weekly with real CTR data
4. **Result:** Model learns what actually works → better ads → more revenue

See `COMPREHENSIVE_ANALYSIS_REPORT.md` Part 5 for the 30-day roadmap.

---

**Questions?** Check logs, test endpoints, and review the comprehensive analysis report.

**🎉 You're 30 minutes away from a working deployment. Let's do this!**
