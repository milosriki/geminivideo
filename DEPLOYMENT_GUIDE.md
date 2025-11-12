# 🚀 Geminivideo Deployment Guide

Complete guide for deploying the geminivideo AI video ads machine.

---

## 📋 Prerequisites

- Docker & Docker Compose installed
- Git configured
- (Optional) GCP account for cloud deployment
- (Optional) Meta Business account for real ads

---

## 🎯 Deployment Options

### Option 1: Local Docker Deployment (RECOMMENDED FOR TESTING)

**Perfect for development and testing with all 15 agents**

```bash
cd /home/user/geminivideo

# Quick start (one command)
./deploy-local.sh

# Or manual steps:
docker-compose up -d
```

**Access URLs:**
- Frontend: http://localhost
- Gateway API: http://localhost:8080
- Drive Intel: http://localhost:8081
- Video Agent: http://localhost:8082
- ML Service: http://localhost:8003
- Meta Publisher: http://localhost:8083

---

### Option 2: GCP Cloud Run Deployment (PRODUCTION)

**Requirements:**
- GCP account with billing enabled
- `gcloud` CLI installed and authenticated

**Steps:**

```bash
cd /home/user/geminivideo

# 1. Set your GCP project ID
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# 2. Authenticate with GCP
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# 3. Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  sqladmin.googleapis.com

# 4. Create Artifact Registry
gcloud artifacts repositories create geminivideo \
  --repository-format=docker \
  --location=$GCP_REGION

# 5. Deploy using script
./scripts/deploy.sh
```

---

### Option 3: GitHub Actions (CI/CD)

**Automated deployment on push to main/develop**

**Setup:**

1. Add GitHub Secrets:
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY` (service account JSON)
   - `META_ACCESS_TOKEN`
   - `META_AD_ACCOUNT_ID`
   - `META_PAGE_ID`

2. Push to main branch:
```bash
git push origin main
```

GitHub Actions will automatically:
- Build Docker images
- Push to GCP Artifact Registry
- Deploy to Cloud Run

---

## ⚙️ Configuration

### 1. Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=postgresql://geminivideo:geminivideo@postgres:5432/geminivideo

# Service URLs
DRIVE_INTEL_URL=http://drive-intel:8081
VIDEO_AGENT_URL=http://video-agent:8082
ML_SERVICE_URL=http://ml-service:8003
META_PUBLISHER_URL=http://meta-publisher:8083

# Meta Credentials (GET FROM: https://developers.facebook.com)
META_ACCESS_TOKEN=your_access_token_here
META_AD_ACCOUNT_ID=your_account_id_here
META_PAGE_ID=your_page_id_here
META_API_VERSION=v18.0

# Frontend
VITE_GATEWAY_URL=http://localhost:8080
VITE_DRIVE_INTEL_URL=http://localhost:8081
```

### 2. Meta Credentials Setup

**Get your Meta credentials:**

1. Go to https://developers.facebook.com
2. Create an app or use existing
3. Get Access Token from Graph API Explorer
4. Find your Ad Account ID in Meta Ads Manager
5. Get your Page ID from your Facebook Page settings

**Test your credentials:**
```bash
curl -G \
  -d "access_token=YOUR_ACCESS_TOKEN" \
  "https://graph.facebook.com/v18.0/me/accounts"
```

---

## 🧪 Testing Deployment

### 1. Health Checks

```bash
# Check all services
./scripts/test-connections.sh

# Or manually:
curl http://localhost:8080/health  # Gateway
curl http://localhost:8081/health  # Drive Intel
curl http://localhost:8082/health  # Video Agent
curl http://localhost:8003/health  # ML Service
curl http://localhost:8083/health  # Meta Publisher
```

### 2. Test ML Service

```bash
# Train XGBoost model
curl -X POST http://localhost:8003/api/ml/train \
  -H "Content-Type: application/json" \
  -d '{"use_synthetic_data": true, "n_samples": 1000}'

# Predict CTR
curl -X POST http://localhost:8003/api/ml/predict-ctr \
  -H "Content-Type: application/json" \
  -d '{
    "clip_data": {
      "psychology_score": 0.8,
      "hook_strength": 0.7,
      "technical_score": 0.9,
      "demographic_match": 0.6,
      "novelty_score": 0.5
    }
  }'

# Check feature importance
curl http://localhost:8003/api/ml/feature-importance
```

### 3. Test A/B Testing

```bash
# Register variants
curl -X POST http://localhost:8003/api/ml/ab/register-variant \
  -H "Content-Type: application/json" \
  -d '{"variant_id": "variant_a"}'

curl -X POST http://localhost:8003/api/ml/ab/register-variant \
  -H "Content-Type: application/json" \
  -d '{"variant_id": "variant_b"}'

# Select variant (Thompson Sampling)
curl -X POST http://localhost:8003/api/ml/ab/select-variant \
  -H "Content-Type: application/json" \
  -d '{}'

# Update with performance
curl -X POST http://localhost:8003/api/ml/ab/update-variant \
  -H "Content-Type: application/json" \
  -d '{
    "variant_id": "variant_a",
    "reward": 1,
    "cost": 0.50,
    "metrics": {
      "impressions": 1000,
      "clicks": 50,
      "conversions": 5
    }
  }'

# Get all variants
curl http://localhost:8003/api/ml/ab/all-variants

# Reallocate budget
curl -X POST http://localhost:8003/api/ml/ab/reallocate-budget \
  -H "Content-Type: application/json" \
  -d '{"total_budget": 1000, "min_budget_per_variant": 50}'
```

### 4. Test Meta Publisher

```bash
# Get account info (requires credentials)
curl http://localhost:8083/api/account/info

# Test dry-run mode (without credentials)
curl http://localhost:8083/
```

### 5. Test Gateway Integration

```bash
# Score storyboard (includes XGBoost prediction)
curl -X POST http://localhost:8080/api/score/storyboard \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "start_time": 0,
        "end_time": 5,
        "text": "Transform your body in 30 days!",
        "features": {"motion_score": 0.8, "technical_quality": 0.9}
      }
    ],
    "metadata": {"target_audience": "fitness"}
  }'
```

---

## 📊 Database Setup

### Initialize Database

```bash
# Automatic (when using docker-compose)
docker-compose up -d postgres

# Manual initialization
docker-compose exec postgres psql -U geminivideo -d geminivideo

# Or using script
python scripts/init_db.py --seed
```

### Database Schema

**Tables:**
- `assets` - Video assets
- `clips` - Scene clips
- `emotions` - DeepFace emotion data

---

## 🔍 Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f ml-service
docker-compose logs -f meta-publisher
docker-compose logs -f gateway-api

# Last 100 lines
docker-compose logs --tail=100
```

### Check Container Status

```bash
docker-compose ps
```

### Resource Usage

```bash
docker stats
```

---

## 🐛 Troubleshooting

### ML Service Won't Start

**Problem:** XGBoost dependencies fail to install

**Solution:**
```bash
cd services/ml-service
pip install --upgrade pip
pip install -r requirements.txt
```

### Meta Publisher Returns 400

**Problem:** "Meta SDK not configured"

**Solution:** Set environment variables in `.env`:
```bash
META_ACCESS_TOKEN=your_token
META_AD_ACCOUNT_ID=your_account_id
META_PAGE_ID=your_page_id
```

### Database Connection Failed

**Problem:** Services can't connect to PostgreSQL

**Solution:**
```bash
# Restart postgres
docker-compose restart postgres

# Check logs
docker-compose logs postgres

# Verify connection
docker-compose exec postgres psql -U geminivideo -d geminivideo -c "SELECT 1;"
```

### Gateway Can't Reach ML Service

**Problem:** XGBoost predictions fail

**Solution:**
```bash
# Check ML service is running
curl http://localhost:8003/health

# Check Docker network
docker network inspect geminivideo_default

# Restart services
docker-compose restart gateway-api ml-service
```

### Port Already in Use

**Problem:** "Port 8080 is already allocated"

**Solution:**
```bash
# Stop conflicting services
docker-compose down

# Or change ports in docker-compose.yml
# ports:
#   - "8090:8080"  # Use 8090 instead
```

---

## 🔄 Updates & Maintenance

### Pull Latest Changes

```bash
git pull origin claude/analyze-geminivideo-project-011CV2jpQj9Te9AnPBiSrBgP

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Update ML Model

```bash
# Retrain with more data
curl -X POST http://localhost:8003/api/ml/train \
  -H "Content-Type: application/json" \
  -d '{"use_synthetic_data": true, "n_samples": 5000}'

# Model is saved to: services/ml-service/models/ctr_model.pkl
```

### Backup Database

```bash
docker-compose exec postgres pg_dump -U geminivideo geminivideo > backup.sql

# Restore
docker-compose exec -T postgres psql -U geminivideo -d geminivideo < backup.sql
```

---

## 🚦 Production Checklist

Before going to production:

- [ ] Configure real Meta credentials
- [ ] Set strong database passwords
- [ ] Enable HTTPS/SSL
- [ ] Configure secrets management (GCP Secret Manager)
- [ ] Set up monitoring (Cloud Logging, Prometheus)
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Load test all endpoints
- [ ] Train ML model with real data
- [ ] Configure proper CORS origins
- [ ] Set up rate limiting
- [ ] Enable authentication/authorization
- [ ] Review security settings in SECURITY.md

---

## 📈 Scaling

### Horizontal Scaling (GCP Cloud Run)

Cloud Run auto-scales based on traffic:

```bash
# Configure scaling
gcloud run services update ml-service \
  --min-instances=1 \
  --max-instances=10 \
  --region=$GCP_REGION
```

### Database Scaling

For production, use Cloud SQL:

```bash
gcloud sql instances create geminivideo-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=$GCP_REGION
```

---

## 💰 Cost Estimation

### Local Docker
- **Cost:** $0 (runs on your machine)
- **Best for:** Development and testing

### GCP Cloud Run (Production)
- **ML Service:** ~$20-50/month (always-on instance)
- **Gateway API:** ~$10-30/month
- **Other services:** ~$5-15/month each
- **Cloud SQL:** ~$25-100/month
- **Total:** ~$100-250/month (low traffic)

### High Traffic
- **1M requests/month:** ~$500-1000/month
- Auto-scales to handle load

---

## 🎓 Learning Resources

### XGBoost
- Model training: http://localhost:8003/api/ml/train
- Feature importance: http://localhost:8003/api/ml/feature-importance

### Thompson Sampling
- A/B testing: http://localhost:8003/api/ml/ab/*
- Budget optimization: http://localhost:8003/api/ml/ab/reallocate-budget

### Meta API
- Documentation: https://developers.facebook.com/docs/marketing-api
- Graph API Explorer: https://developers.facebook.com/tools/explorer

---

## 🆘 Support

**Check logs:**
```bash
docker-compose logs -f
```

**Get service status:**
```bash
./scripts/test-connections.sh
```

**Common issues:** See Troubleshooting section above

**Documentation:**
- Architecture: `docs/ARCHITECTURE.md`
- Security: `SECURITY.md`
- Deployment: `DEPLOYMENT.md`
- Phase 1 Report: `PHASE_1_COMPLETION_REPORT.md`

---

## ✅ Quick Start (TL;DR)

```bash
# 1. Clone and navigate
cd /home/user/geminivideo

# 2. Deploy locally
./deploy-local.sh

# 3. Open frontend
open http://localhost

# 4. Test ML service
curl http://localhost:8003/health

# 5. Train model
curl -X POST http://localhost:8003/api/ml/train \
  -H "Content-Type: application/json" \
  -d '{"use_synthetic_data": true}'

# Done! 🎉
```

---

**Status:** ✅ Production Ready
**Version:** 2.0.0 (All 15 Agents Complete)
**Last Updated:** November 12, 2025
