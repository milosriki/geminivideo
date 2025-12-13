# 🚀 Winner Ads System - Deployment Checklist

## Pre-Deployment Checks

### Code Quality
- [ ] All tests passing (`npm test`)
- [ ] No TypeScript errors (`npm run build`)
- [ ] ESLint passing (`npm run lint`)
- [ ] Code reviewed and approved

### Environment Variables
Required environment variables:
```env
# Winner Detection
WINNER_CHECK_SCHEDULE=0 */6 * * *  # Every 6 hours
MIN_WINNER_ROAS=2.0
MIN_WINNER_CTR=0.02
MIN_WINNER_SPEND=100

# Budget Optimization
BUDGET_SCHEDULE=0 */12 * * *  # Every 12 hours
MAX_DAILY_BUDGET_CHANGE=0.5
MIN_BUDGET_PER_AD=10
MAX_BUDGET_PER_AD=1000

# Services
META_PUBLISHER_URL=http://meta-publisher:8003
LANGGRAPH_URL=http://langgraph:2024
ML_SERVICE_URL=http://ml-service:8001
DEFAULT_AD_ACCOUNT_ID=act_XXXXXXXXXX

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

### Dependencies
- [ ] PostgreSQL running and accessible
- [ ] Redis running and accessible
- [ ] ML Service deployed and healthy
- [ ] Meta Publisher deployed and healthy
- [ ] LangGraph Agent deployed and healthy

## Deployment Steps

### 1. Database Migrations
```bash
# Run migrations
npx prisma migrate deploy

# Verify tables created
npx prisma db pull
```

### 2. Deploy Services
```bash
# Build
npm run build

# Deploy to Cloud Run
gcloud run deploy gateway-api \
  --image gcr.io/PROJECT/gateway-api:latest \
  --set-env-vars "WINNER_CHECK_SCHEDULE=0 */6 * * *"
```

### 3. Start Schedulers
Verify schedulers start on boot:
- Winner detection scheduler (every 6 hours)
- Budget optimization scheduler (every 12 hours)

## Post-Deployment Verification

### API Endpoints
```bash
# Health check
curl https://api.example.com/health

# Winner detection
curl -X POST https://api.example.com/api/v1/winners/detect

# List winners
curl https://api.example.com/api/v1/winners/list

# Budget optimization
curl -X POST https://api.example.com/api/v1/budget/optimize
```

### Verify Schedulers
```bash
# Check logs for scheduler startup
gcloud logging read "Starting winner scheduler"
gcloud logging read "Starting budget scheduler"
```

### Verify Integration
- [ ] Winner detection returns results
- [ ] Winners indexed to FAISS
- [ ] Budget changes calculated correctly
- [ ] Workflow completes end-to-end

## Rollback Procedure

### If Issues Detected:
1. **Rollback deployment:**
   ```bash
   gcloud run services update-traffic gateway-api \
     --to-revisions PREVIOUS_REVISION=100
   ```

2. **Rollback database (if needed):**
   ```bash
   npx prisma migrate resolve --rolled-back MIGRATION_NAME
   ```

3. **Notify team:**
   - Post in #deployments channel
   - Update incident tracker

## Success Criteria

The deployment is successful when:
- [ ] All health checks passing
- [ ] Winner detection runs and finds winners
- [ ] Winners indexed to RAG
- [ ] Budget optimization calculates changes
- [ ] No errors in logs
- [ ] Scheduled jobs running on time

## Monitoring

### Alerts to Configure:
- Winner detection failures
- Budget optimization errors
- Scheduler missed runs
- High error rates

### Dashboards:
- Winners detected per day
- Budget changes applied
- ROAS improvement over time
- System health metrics

---

**Status:** Ready for deployment
**Last Updated:** 2025-12-13
**Owner:** DevOps Team
