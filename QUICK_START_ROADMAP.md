# ⚡ QUICK START ROADMAP
## From 85% to 100% - Prioritized Action Plan

**Current:** 85% Complete  
**Target:** 100% Production-Ready  
**Timeline:** 6 weeks (or 2 weeks intensive)

---

## 🎯 WEEK 1: CRITICAL WIRING (13 hours)

### Day 1: RAG Integration (4 hours)
```bash
# 1. Wire RAG to Director Agent
# File: services/titan-core/ai_council/director_agent.py
# Add: Search for similar winners before creating plan

# 2. Auto-index winners
# File: services/ml-service/src/main.py
# Add: Auto-index when CTR > 3% or ROAS > 3.0

# 3. Test
curl -X POST http://localhost:8003/api/ml/rag/search-winners \
  -d '{"query": "fitness transformation", "top_k": 5}'
```

### Day 2: HubSpot Async (3 hours)
```bash
# 1. Create Celery task
# File: services/ml-service/src/tasks.py
# Add: process_hubspot_webhook task

# 2. Modify webhook
# File: services/gateway-api/src/webhooks/hubspot.ts
# Change: Queue to Celery instead of direct processing

# 3. Start worker
docker-compose up hubspot-worker
```

### Day 3: Pre-Spend Prediction (3 hours)
```bash
# 1. Create endpoint
# File: services/ml-service/src/main.py
# Add: /api/ml/predict-creative endpoint

# 2. Integrate with Director
# File: services/titan-core/ai_council/director_agent.py
# Add: Call prediction before creating plan

# 3. Test
curl -X POST http://localhost:8003/api/ml/predict-creative \
  -d '{"creative_dna": {...}, "account_id": "test"}'
```

### Day 4: Fatigue Monitoring (3 hours)
```bash
# 1. Create Celery periodic task
# File: services/ml-service/src/tasks.py
# Add: monitor_fatigue task (runs every 2 hours)

# 2. Auto-remediation
# Add: Budget reduction + creative refresh

# 3. Start Celery Beat
docker-compose up celery-beat
```

**Week 1 Result:** Core intelligence fully wired ✅

---

## 🎯 WEEK 2: FRONTEND INTEGRATION (11 hours)

### Day 1-2: Budget Optimizer UI (4 hours)
```typescript
// Create: services/frontend/src/components/BudgetOptimizer.tsx
// Wire: /api/ml/battle-hardened/select endpoint
// Add: To Campaign Dashboard
```

### Day 3: Winner Search UI (3 hours)
```typescript
// Create: services/frontend/src/components/WinnerSearch.tsx
// Wire: /api/ml/rag/search-winners endpoint
// Show: Similarity scores + creative DNA comparison
```

### Day 4: Learning Dashboard (2 hours)
```typescript
// Create: services/frontend/src/components/LearningDashboard.tsx
// Wire: /api/ml/self-learning-cycle endpoint
// Show: 7-step progress + results
```

### Day 5: Pipeline Value UI (2 hours)
```typescript
// Create: services/frontend/src/components/PipelineValueDashboard.tsx
// Wire: /api/ml/synthetic-revenue/get-stages endpoint
// Allow: Stage value configuration
```

**Week 2 Result:** All features accessible from UI ✅

---

## 🎯 WEEK 3: INFRASTRUCTURE (13 hours)

### Day 1: Supabase Setup (4 hours)
```bash
# 1. Create Supabase project
# Go to: supabase.com → New Project

# 2. Run migrations
psql $SUPABASE_DB_URL < database/migrations/001_ad_change_history.sql
psql $SUPABASE_DB_URL < database/migrations/002_synthetic_revenue_config.sql
psql $SUPABASE_DB_URL < database/migrations/003_attribution_tracking.sql
psql $SUPABASE_DB_URL < database/migrations/004_pgboss_extension.sql
psql $SUPABASE_DB_URL < database/migrations/005_pending_ad_changes.sql
psql $SUPABASE_DB_URL < database/migrations/006_model_registry.sql

# 3. Update .env
DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
```

### Day 2-3: Cloud Run Deployment (6 hours)
```bash
# 1. Create service definitions
# File: cloud-run/ml-service.yaml
# File: cloud-run/gateway-api.yaml
# File: cloud-run/titan-core.yaml
# File: cloud-run/video-agent.yaml

# 2. Create GitHub Actions
# File: .github/workflows/deploy.yml

# 3. Deploy
gcloud run deploy ml-service --image gcr.io/$PROJECT/ml-service
gcloud run deploy gateway-api --image gcr.io/$PROJECT/gateway-api
gcloud run deploy titan-core --image gcr.io/$PROJECT/titan-core
gcloud run deploy video-agent --image gcr.io/$PROJECT/video-agent
```

### Day 4: Redis & Celery (3 hours)
```bash
# 1. Setup Cloud Memorystore
gcloud redis instances create geminivideo-redis \
  --size=1 --region=us-central1

# 2. Deploy Celery workers
gcloud run jobs create celery-worker \
  --image gcr.io/$PROJECT/ml-service \
  --command celery -A src.tasks worker

# 3. Deploy Celery Beat
gcloud run jobs create celery-beat \
  --image gcr.io/$PROJECT/ml-service \
  --command celery -A src.tasks beat
```

**Week 3 Result:** Production infrastructure ready ✅

---

## 🎯 WEEK 4: MONITORING (7 hours)

### Day 1-2: Prometheus & Grafana (4 hours)
```bash
# 1. Deploy Prometheus
kubectl apply -f prometheus/prometheus.yml

# 2. Add metrics to services
# File: services/ml-service/src/main.py
from prometheus_client import Counter, Histogram

# 3. Deploy Grafana
kubectl apply -f grafana/grafana.yml

# 4. Create dashboards
# - Service health
# - API latency
# - Error rates
# - Queue depth
```

### Day 3: Error Tracking (3 hours)
```bash
# 1. Setup Sentry
# File: services/ml-service/src/main.py
import sentry_sdk
sentry_sdk.init(dsn="[SENTRY_DSN]")

# 2. Structured logging
import structlog
logger = structlog.get_logger()

# 3. Cloud Logging
# Configure log exports
# Setup log-based alerts
```

**Week 4 Result:** Full observability ✅

---

## 🎯 WEEK 5: TESTING (12 hours)

### Day 1-3: E2E Tests (8 hours)
```python
# tests/e2e/test_complete_flow.py
def test_complete_creative_generation():
    # Upload → Process → Render → Publish
    pass

def test_complete_budget_optimization():
    # Feedback → Decision → Queue → Execute
    pass

def test_complete_self_learning():
    # All 7 loops execute
    pass
```

### Day 4: Load Testing (4 hours)
```python
# tests/load/test_api_load.py
# Test: 100 concurrent users
# Test: 1000 requests/minute
# Measure: Response times, error rates
```

**Week 5 Result:** Production-ready testing ✅

---

## 🎯 WEEK 6: SECURITY (6 hours)

### Day 1-2: Security Hardening (4 hours)
```typescript
// 1. API Authentication
// File: services/gateway-api/src/middleware/auth.ts

// 2. Rate Limiting
import rateLimit from 'express-rate-limit'

// 3. Input Validation
// Add Pydantic validation
```

### Day 3: Secrets Management (2 hours)
```bash
# 1. Move to Secret Manager
gcloud secrets create database-url --data-file=-
gcloud secrets create api-keys --data-file=-

# 2. Update services
# Reference secrets in Cloud Run config
```

**Week 6 Result:** Production security ✅

---

## 📋 COMPLETE CHECKLIST

### ✅ Week 1: Critical Wiring (13h)
- [ ] Wire RAG to Creative Generation
- [ ] Wire HubSpot to Celery
- [ ] Wire Pre-Spend Prediction
- [ ] Wire Fatigue Monitoring

### ✅ Week 2: Frontend (11h)
- [ ] Budget Optimizer UI
- [ ] Winner Search UI
- [ ] Learning Dashboard
- [ ] Pipeline Value Dashboard

### ✅ Week 3: Infrastructure (13h)
- [ ] Supabase Setup
- [ ] Cloud Run Deployment
- [ ] Redis & Celery

### ✅ Week 4: Monitoring (7h)
- [ ] Prometheus & Grafana
- [ ] Error Tracking

### ✅ Week 5: Testing (12h)
- [ ] E2E Tests
- [ ] Load Tests

### ✅ Week 6: Security (6h)
- [ ] Security Hardening
- [ ] Secrets Management

**Total: 62 hours over 6 weeks**

---

## 🚀 THIS WEEK (Quick Start)

### Today (4 hours)
1. Wire RAG to Director Agent (2h)
2. Auto-index winners (1h)
3. Test integration (1h)

### Tomorrow (3 hours)
1. Create Celery task for HubSpot (1h)
2. Modify webhook to queue (1h)
3. Test async processing (1h)

### Day 3 (3 hours)
1. Create pre-spend prediction endpoint (2h)
2. Integrate with Director (1h)

### Day 4 (3 hours)
1. Create fatigue monitoring task (2h)
2. Add auto-remediation (1h)

**Week 1 Goal: Core intelligence fully wired**

---

## 📊 SUCCESS METRICS

### Technical
- ✅ All services deployed
- ✅ All endpoints accessible
- ✅ Database migrations applied
- ✅ Monitoring active

### Business
- ✅ Users can optimize budgets
- ✅ System learns automatically
- ✅ Fatigue auto-remediated
- ✅ Pipeline value visible

---

**This roadmap takes you from 85% to 100% in 6 weeks (or 2 weeks intensive).**

