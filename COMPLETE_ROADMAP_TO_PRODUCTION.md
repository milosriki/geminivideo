# 🗺️ COMPLETE ROADMAP TO PRODUCTION
## Step-by-Step Guide: From 85% to 100% Production-Ready

**Generated:** 2024-12-08  
**Purpose:** Complete, detailed roadmap covering every aspect of wiring, deployment, and production readiness

**Current Status:** 85% Complete  
**Target:** 100% Production-Ready  
**Timeline:** 4-6 weeks

---

## 📊 EXECUTIVE SUMMARY

### What's Done (85%)
- ✅ Core ML intelligence (BattleHardenedSampler, RAG, Synthetic Revenue)
- ✅ Database migrations (6/6 complete)
- ✅ Backend services (ML, Gateway, Titan-Core, Video-Agent)
- ✅ Safety systems (SafeExecutor, job queue)
- ✅ Self-learning loops (7/7 wired)

### What's Left (15%)
- ⚠️ Final wiring (RAG → Creative Generation)
- ⚠️ Frontend integration (expose all features)
- ⚠️ Deployment automation (Cloud Run, Supabase)
- ⚠️ Monitoring & alerting (production observability)
- ⚠️ Testing & validation (end-to-end tests)

---

## 🎯 PHASE 1: CRITICAL WIRING (Week 1)
**Goal:** Complete all internal service connections

### Step 1.1: Wire RAG to Creative Generation (4 hours)

**Current State:**
- ✅ RAG Winner Index exists (`winner_index.py`)
- ✅ 5 API endpoints exist
- ❌ Not integrated into Director Agent workflow

**Actions:**

1. **Modify Director Agent in Titan-Core** (2 hours)
   ```python
   # services/titan-core/ai_council/director_agent.py
   
   async def create_battle_plan(self, video_id: str):
       # BEFORE creating plan, search for similar winners
       similar_winners = await ml_service_client.post(
           '/api/ml/rag/search-winners',
           json={
               'query': video_creative_dna,
               'top_k': 5
           }
       )
       
       # Use winners as examples in prompt
       prompt = f"""
       Here are 5 winning ads similar to this video:
       {similar_winners}
       
       Create a battle plan that applies their proven patterns...
       """
   ```

2. **Auto-Index Winners** (1 hour)
   ```python
   # services/ml-service/src/main.py
   
   # In feedback endpoint, auto-index winners
   @app.post("/api/ml/battle-hardened/feedback")
   async def battle_hardened_feedback(...):
       # ... existing code ...
       
       # If ad is a winner, auto-index
       if pipeline_roas > 3.0 or ctr > 0.03:
           await winner_index.add_winner(
               ad_id=ad_id,
               embedding=creative_dna_embedding,
               metadata=creative_dna
           )
   ```

3. **Test Integration** (1 hour)
   - Upload test video
   - Verify RAG search returns similar winners
   - Verify Director Agent uses winners in plan
   - Verify winners auto-index when they win

**Success Criteria:**
- ✅ Director Agent receives similar winners before creating plan
- ✅ Winners auto-index when CTR > 3% or ROAS > 3.0
- ✅ RAG search returns relevant results

---

### Step 1.2: Wire HubSpot to Celery Queue (3 hours)

**Current State:**
- ✅ HubSpot webhook exists (`hubspot.ts`)
- ✅ Processes synchronously
- ❌ No Celery queue for async processing

**Actions:**

1. **Create Celery Task** (1 hour)
   ```python
   # services/ml-service/src/tasks.py
   
   from celery import Celery
   
   celery_app = Celery('ml_service')
   celery_app.config_from_object('celeryconfig')
   
   @celery_app.task(name='process_hubspot_webhook')
   def process_hubspot_webhook(webhook_payload: dict):
       # Calculate synthetic revenue
       synthetic_revenue = calculate_synthetic_revenue(...)
       
       # Attribute to ad
       attribution = attribute_conversion(...)
       
       # Send feedback to BattleHardenedSampler
       ml_service_client.post(
           '/api/ml/battle-hardened/feedback',
           json={
               'ad_id': attribution.ad_id,
               'actual_pipeline_value': synthetic_revenue,
               'actual_spend': attribution.spend
           }
       )
   ```

2. **Modify HubSpot Webhook** (1 hour)
   ```typescript
   // services/gateway-api/src/webhooks/hubspot.ts
   
   // Instead of processing directly, queue to Celery
   router.post('/webhooks/hubspot', async (req, res) => {
       // Verify signature
       // Queue to Redis/Celery
       await celeryClient.sendTask('process_hubspot_webhook', [req.body])
       
       // Return immediately
       res.status(200).json({ status: 'queued' })
   })
   ```

3. **Start Celery Worker** (1 hour)
   ```yaml
   # docker-compose.yml
   
   hubspot-worker:
     build: ./services/ml-service
     command: celery -A src.tasks worker --loglevel=info -Q hubspot-webhook-events
     depends_on:
       - redis
       - postgres
   ```

**Success Criteria:**
- ✅ Webhook returns immediately (< 200ms)
- ✅ Celery processes webhook asynchronously
- ✅ Feedback reaches BattleHardenedSampler

---

### Step 1.3: Wire Pre-Spend Prediction (3 hours)

**Current State:**
- ✅ Oracle Agent exists
- ✅ CTR prediction exists
- ❌ No pre-spend decision gate

**Actions:**

1. **Create Prediction Endpoint** (1.5 hours)
   ```python
   # services/ml-service/src/main.py
   
   @app.post("/api/ml/predict-creative", tags=["Prediction"])
   async def predict_creative_performance(request: CreativePredictionRequest):
       """
       Predict CTR/ROAS BEFORE spending budget.
       Decision gate: REJECT if < 70% of account average.
       """
       # Get Oracle prediction
       oracle_prediction = await titan_core_client.post(
           '/api/titan/oracle/predict',
           json={'creative_dna': request.creative_dna}
       )
       
       # Get account baseline
       account_baseline = get_account_baseline(request.account_id)
       
       # Decision gate
       if oracle_prediction['predicted_ctr'] < account_baseline * 0.70:
           return {
               'decision': 'REJECT',
               'reason': 'Predicted CTR below 70% of account average',
               'recommendation': 'Fix hook pacing or increase text contrast'
           }
       
       return {
           'decision': 'PROCEED',
           'predicted_ctr': oracle_prediction['predicted_ctr'],
           'confidence': oracle_prediction['confidence']
       }
   ```

2. **Integrate with Director Agent** (1 hour)
   ```python
   # services/titan-core/ai_council/director_agent.py
   
   async def create_battle_plan(self, video_id: str):
       # Get prediction BEFORE creating plan
       prediction = await ml_service_client.post(
           '/api/ml/predict-creative',
           json={'creative_dna': video_creative_dna}
       )
       
       if prediction['decision'] == 'REJECT':
           # Focus plan on fixing identified weaknesses
           return create_fix_plan(prediction['recommendation'])
   ```

3. **Test Integration** (0.5 hours)
   - Test with low-potential creative → Should REJECT
   - Test with high-potential creative → Should PROCEED

**Success Criteria:**
- ✅ Low-potential creatives rejected before spending
- ✅ High-potential creatives approved
- ✅ Director Agent uses predictions in plan

---

### Step 1.4: Wire Real-Time Fatigue Monitoring (3 hours)

**Current State:**
- ✅ Fatigue detector exists (`fatigue_detector.py`)
- ❌ Not running automatically
- ❌ No auto-remediation

**Actions:**

1. **Create Celery Periodic Task** (1 hour)
   ```python
   # services/ml-service/src/tasks.py
   
   from celery.schedules import crontab
   
   @celery_app.task(name='monitor_fatigue')
   def monitor_all_ads():
       # Get all active ads
       active_ads = get_active_ads()
       
       for ad in active_ads:
           # Get metrics history
           metrics = get_metrics_history(ad.id, days=7)
           
           # Detect fatigue
           result = detect_fatigue(ad.id, metrics)
           
           if result.status in ['FATIGUING', 'SATURATED']:
               # Auto-remediate
               auto_remediate_fatigue(ad.id, result)
   
   # Schedule every 2 hours
   celery_app.conf.beat_schedule = {
       'monitor-fatigue': {
           'task': 'monitor_fatigue',
           'schedule': crontab(minute=0, hour='*/2'),
       },
   }
   ```

2. **Auto-Remediation Logic** (1 hour)
   ```python
   def auto_remediate_fatigue(ad_id: str, fatigue_result: FatigueResult):
       # Gradually reduce budget
       current_budget = get_ad_budget(ad_id)
       new_budget = current_budget * 0.8  # 20% reduction
       
       # Queue budget reduction
       queue_ad_change(ad_id, {
           'change_type': 'BUDGET_DECREASE',
           'new_budget': new_budget,
           'reason': f'Fatigue detected: {fatigue_result.reason}'
       })
       
       # Trigger replacement creative generation
       trigger_creative_refresh(ad_id)
   ```

3. **Start Celery Beat** (1 hour)
   ```yaml
   # docker-compose.yml
   
   celery-beat:
     build: ./services/ml-service
     command: celery -A src.tasks beat --loglevel=info
     depends_on:
       - redis
       - postgres
   ```

**Success Criteria:**
- ✅ Fatigue monitoring runs every 2 hours
- ✅ Fatiguing ads get budget reduction
- ✅ Replacement creatives generated automatically

---

## 🎯 PHASE 2: FRONTEND INTEGRATION (Week 2)
**Goal:** Expose all backend features in UI

### Step 2.1: Wire BattleHardenedSampler to Frontend (4 hours)

**Current State:**
- ✅ Backend endpoints exist
- ❌ Not exposed in frontend
- ❌ No UI for budget optimization

**Actions:**

1. **Create Budget Optimization Component** (2 hours)
   ```typescript
   // services/frontend/src/components/BudgetOptimizer.tsx
   
   const BudgetOptimizer = ({ campaignId }: Props) => {
       const [recommendations, setRecommendations] = useState([])
       
       const optimizeBudget = async () => {
           const response = await api.post('/api/ml/battle-hardened/select', {
               ad_states: adStates,
               total_budget: totalBudget
           })
           setRecommendations(response.recommendations)
       }
       
       return (
           <div>
               <button onClick={optimizeBudget}>Optimize Budget</button>
               {recommendations.map(rec => (
                   <BudgetRecommendationCard
                       key={rec.ad_id}
                       recommendation={rec}
                   />
               ))}
           </div>
       )
   }
   ```

2. **Create API Client Method** (1 hour)
   ```typescript
   // services/frontend/src/api/ml.ts
   
   export const mlApi = {
       optimizeBudget: async (data: BudgetOptimizationRequest) => {
           return fetch('/api/ml/battle-hardened/select', {
               method: 'POST',
               body: JSON.stringify(data)
           })
       },
       
       getFeedback: async (adId: string, feedback: FeedbackData) => {
           return fetch('/api/ml/battle-hardened/feedback', {
               method: 'POST',
               body: JSON.stringify({ ad_id: adId, ...feedback })
           })
       }
   }
   ```

3. **Add to Campaign Dashboard** (1 hour)
   ```typescript
   // services/frontend/src/pages/CampaignDashboard.tsx
   
   // Add BudgetOptimizer component
   <BudgetOptimizer campaignId={campaign.id} />
   ```

**Success Criteria:**
- ✅ Users can trigger budget optimization from UI
- ✅ Recommendations displayed with confidence scores
- ✅ Users can approve/reject recommendations

---

### Step 2.2: Wire RAG Winner Index to Frontend (3 hours)

**Current State:**
- ✅ Backend endpoints exist
- ❌ No UI for searching winners
- ❌ No visualization of similar ads

**Actions:**

1. **Create Winner Search Component** (2 hours)
   ```typescript
   // services/frontend/src/components/WinnerSearch.tsx
   
   const WinnerSearch = ({ videoId }: Props) => {
       const [winners, setWinners] = useState([])
       
       const searchSimilar = async () => {
           const response = await api.post('/api/ml/rag/search-winners', {
               query: videoCreativeDNA,
               top_k: 5
           })
           setWinners(response.winners)
       }
       
       return (
           <div>
               <button onClick={searchSimilar}>Find Similar Winners</button>
               {winners.map(winner => (
                   <WinnerCard
                       key={winner.ad_id}
                       winner={winner}
                       similarity={winner.similarity}
                   />
               ))}
           </div>
       )
   }
   ```

2. **Create Winner Visualization** (1 hour)
   - Show similarity score (0-100%)
   - Display creative DNA comparison
   - Show performance metrics (CTR, ROAS)

**Success Criteria:**
- ✅ Users can search for similar winners
- ✅ Results displayed with similarity scores
- ✅ Creative DNA comparison visible

---

### Step 2.3: Wire Self-Learning Cycle to Frontend (2 hours)

**Current State:**
- ✅ Backend endpoint exists
- ❌ No UI to trigger/manual cycle
- ❌ No visualization of learning progress

**Actions:**

1. **Create Learning Dashboard** (1.5 hours)
   ```typescript
   // services/frontend/src/components/LearningDashboard.tsx
   
   const LearningDashboard = () => {
       const [cycleStatus, setCycleStatus] = useState(null)
       
       const triggerCycle = async () => {
           const response = await api.post('/api/ml/self-learning-cycle', {
               account_id: accountId,
               trigger_retrain: true
           })
           setCycleStatus(response)
       }
       
       return (
           <div>
               <button onClick={triggerCycle}>Run Learning Cycle</button>
               {cycleStatus && (
                   <LearningProgress steps={cycleStatus.steps} />
               )}
           </div>
       )
   }
   ```

2. **Add Progress Visualization** (0.5 hours)
   - Show 7 steps progress
   - Display results for each step
   - Show improvement metrics

**Success Criteria:**
- ✅ Users can trigger learning cycle manually
- ✅ Progress displayed in real-time
- ✅ Results visible after completion

---

### Step 2.4: Wire Synthetic Revenue to Frontend (2 hours)

**Current State:**
- ✅ Backend endpoints exist
- ❌ No UI for pipeline value visualization
- ❌ No stage configuration UI

**Actions:**

1. **Create Pipeline Value Dashboard** (1.5 hours)
   ```typescript
   // services/frontend/src/components/PipelineValueDashboard.tsx
   
   const PipelineValueDashboard = ({ tenantId }: Props) => {
       const [stages, setStages] = useState([])
       
       useEffect(() => {
           api.get(`/api/ml/synthetic-revenue/get-stages?tenant_id=${tenantId}`)
               .then(setStages)
       }, [tenantId])
       
       return (
           <div>
               <h2>Pipeline Stage Values</h2>
               {stages.map(stage => (
                   <StageValueCard
                       key={stage.stage_name}
                       stage={stage}
                       value={stage.value}
                   />
               ))}
           </div>
       )
   }
   ```

2. **Add Stage Configuration** (0.5 hours)
   - Allow users to edit stage values
   - Save to database
   - Apply to calculations

**Success Criteria:**
- ✅ Users can view pipeline stage values
- ✅ Users can configure stage values
- ✅ Changes apply to calculations

---

## 🎯 PHASE 3: DATABASE & INFRASTRUCTURE (Week 3)
**Goal:** Production-ready database and infrastructure

### Step 3.1: Supabase Setup & Migration (4 hours)

**Current State:**
- ✅ Migrations exist (local PostgreSQL)
- ❌ Not configured for Supabase
- ❌ No production database

**Actions:**

1. **Create Supabase Project** (1 hour)
   - Go to supabase.com
   - Create new project
   - Note connection string
   - Enable pgvector extension

2. **Run Migrations on Supabase** (1 hour)
   ```bash
   # Connect to Supabase
   psql $SUPABASE_DB_URL
   
   # Run all migrations
   \i database/migrations/001_ad_change_history.sql
   \i database/migrations/002_synthetic_revenue_config.sql
   \i database/migrations/003_attribution_tracking.sql
   \i database/migrations/004_pgboss_extension.sql
   \i database/migrations/005_pending_ad_changes.sql
   \i database/migrations/006_model_registry.sql
   ```

3. **Update Connection Strings** (1 hour)
   ```bash
   # .env files
   DATABASE_URL=postgresql://postgres:[password]@[host]:5432/postgres
   SUPABASE_URL=https://[project].supabase.co
   SUPABASE_KEY=[anon key]
   ```

4. **Test Connection** (1 hour)
   - Test all services can connect
   - Test migrations applied correctly
   - Test queries work

**Success Criteria:**
- ✅ All migrations applied to Supabase
- ✅ All services connect successfully
- ✅ Queries execute correctly

---

### Step 3.2: Cloud Run Deployment Setup (6 hours)

**Current State:**
- ✅ Dockerfiles exist
- ✅ docker-compose.yml exists
- ❌ No Cloud Run configuration
- ❌ No CI/CD pipeline

**Actions:**

1. **Create Cloud Run Service Definitions** (2 hours)
   ```yaml
   # cloud-run/ml-service.yaml
   
   apiVersion: serving.knative.dev/v1
   kind: Service
   metadata:
     name: ml-service
   spec:
     template:
       spec:
         containers:
         - image: gcr.io/[project]/ml-service:latest
           env:
           - name: DATABASE_URL
             valueFrom:
               secretKeyRef:
                 name: database-secret
                 key: url
           - name: REDIS_URL
             valueFrom:
               secretKeyRef:
                 name: redis-secret
                 key: url
         resources:
           limits:
             cpu: "2"
             memory: 4Gi
   ```

2. **Create GitHub Actions Workflow** (2 hours)
   ```yaml
   # .github/workflows/deploy.yml
   
   name: Deploy to Cloud Run
   
   on:
     push:
       branches: [main]
   
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v2
       
       - name: Build and Push
         run: |
           docker build -t gcr.io/$PROJECT/ml-service ./services/ml-service
           docker push gcr.io/$PROJECT/ml-service
       
       - name: Deploy to Cloud Run
         run: |
           gcloud run deploy ml-service \
             --image gcr.io/$PROJECT/ml-service \
             --platform managed \
             --region us-central1
   ```

3. **Configure Secrets** (1 hour)
   - Store secrets in Google Secret Manager
   - Reference in Cloud Run config
   - Test secret access

4. **Deploy All Services** (1 hour)
   - Deploy ml-service
   - Deploy gateway-api
   - Deploy titan-core
   - Deploy video-agent
   - Deploy meta-publisher

**Success Criteria:**
- ✅ All services deployed to Cloud Run
- ✅ Services accessible via HTTPS
- ✅ Secrets configured correctly
- ✅ CI/CD pipeline working

---

### Step 3.3: Redis & Celery Setup (3 hours)

**Current State:**
- ✅ Redis in docker-compose
- ❌ Not configured for production
- ❌ Celery workers not deployed

**Actions:**

1. **Setup Redis on Cloud Memorystore** (1 hour)
   - Create Cloud Memorystore instance
   - Configure VPC peering
   - Update connection strings

2. **Deploy Celery Workers** (1 hour)
   ```yaml
   # cloud-run/celery-worker.yaml
   
   apiVersion: batch/v1
   kind: Job
   metadata:
     name: celery-worker
   spec:
     template:
       spec:
         containers:
         - name: worker
           image: gcr.io/[project]/ml-service:latest
           command: ["celery", "-A", "src.tasks", "worker", "--loglevel=info"]
   ```

3. **Deploy Celery Beat** (1 hour)
   - Deploy as Cloud Run Job
   - Schedule periodic tasks
   - Test execution

**Success Criteria:**
- ✅ Redis accessible from all services
- ✅ Celery workers processing jobs
- ✅ Celery Beat scheduling tasks

---

## 🎯 PHASE 4: MONITORING & OBSERVABILITY (Week 4)
**Goal:** Production-grade monitoring

### Step 4.1: Prometheus & Grafana Setup (4 hours)

**Actions:**

1. **Deploy Prometheus** (1.5 hours)
   ```yaml
   # prometheus/prometheus.yml
   
   scrape_configs:
     - job_name: 'ml-service'
       static_configs:
         - targets: ['ml-service:8003']
     - job_name: 'gateway-api'
       static_configs:
         - targets: ['gateway-api:8080']
   ```

2. **Add Metrics to Services** (1.5 hours)
   ```python
   # services/ml-service/src/main.py
   
   from prometheus_client import Counter, Histogram
   
   prediction_requests = Counter('prediction_requests_total', 'Total predictions')
   prediction_duration = Histogram('prediction_duration_seconds', 'Prediction time')
   
   @app.post("/api/ml/predict/ctr")
   async def predict_ctr(...):
       with prediction_duration.time():
           prediction_requests.inc()
           # ... prediction logic ...
   ```

3. **Deploy Grafana** (1 hour)
   - Create dashboards
   - Configure alerts
   - Test visualization

**Success Criteria:**
- ✅ Metrics collected from all services
- ✅ Grafana dashboards showing key metrics
- ✅ Alerts configured

---

### Step 4.2: Error Tracking & Logging (3 hours)

**Actions:**

1. **Setup Sentry** (1 hour)
   ```python
   # services/ml-service/src/main.py
   
   import sentry_sdk
   sentry_sdk.init(dsn="[SENTRY_DSN]")
   ```

2. **Structured Logging** (1 hour)
   ```python
   import structlog
   
   logger = structlog.get_logger()
   logger.info("prediction_complete", ad_id=ad_id, ctr=predicted_ctr)
   ```

3. **Log Aggregation** (1 hour)
   - Setup Cloud Logging
   - Configure log exports
   - Test log search

**Success Criteria:**
- ✅ Errors tracked in Sentry
- ✅ Logs searchable in Cloud Logging
- ✅ Alerts on critical errors

---

## 🎯 PHASE 5: TESTING & VALIDATION (Week 5)
**Goal:** Comprehensive test coverage

### Step 5.1: End-to-End Test Suite (8 hours)

**Actions:**

1. **Create E2E Test Framework** (2 hours)
   ```python
   # tests/e2e/test_complete_flow.py
   
   def test_complete_creative_generation():
       # Upload video
       # Wait for processing
       # Verify variations created
       # Verify Meta ads created
   ```

2. **Test All Orchestrations** (4 hours)
   - Creative generation flow
   - Budget optimization flow
   - Self-learning cycle

3. **Test Failure Recovery** (2 hours)
   - Service failures
   - Database failures
   - API failures

**Success Criteria:**
- ✅ All E2E tests passing
- ✅ Failure recovery verified
- ✅ Performance benchmarks met

---

### Step 5.2: Load Testing (4 hours)

**Actions:**

1. **Create Load Test Scripts** (2 hours)
   ```python
   # tests/load/test_api_load.py
   
   from locust import HttpUser, task
   
   class ApiUser(HttpUser):
       @task
       def predict_ctr(self):
           self.client.post("/api/ml/predict/ctr", json=data)
   ```

2. **Run Load Tests** (1 hour)
   - Test 100 concurrent users
   - Test 1000 requests/minute
   - Measure response times

3. **Optimize Performance** (1 hour)
   - Identify bottlenecks
   - Optimize queries
   - Add caching

**Success Criteria:**
- ✅ System handles 100 concurrent users
- ✅ Response times < 500ms (p95)
- ✅ No errors under load

---

## 🎯 PHASE 6: SECURITY & COMPLIANCE (Week 6)
**Goal:** Production security

### Step 6.1: Security Hardening (4 hours)

**Actions:**

1. **API Authentication** (2 hours)
   ```typescript
   // services/gateway-api/src/middleware/auth.ts
   
   export const authenticate = async (req, res, next) => {
       const token = req.headers.authorization
       const user = await verifyToken(token)
       req.user = user
       next()
   }
   ```

2. **Rate Limiting** (1 hour)
   ```typescript
   import rateLimit from 'express-rate-limit'
   
   const limiter = rateLimit({
       windowMs: 15 * 60 * 1000, // 15 minutes
       max: 100 // limit each IP to 100 requests per windowMs
   })
   ```

3. **Input Validation** (1 hour)
   - Add Pydantic validation
   - Sanitize inputs
   - Prevent SQL injection

**Success Criteria:**
- ✅ All endpoints authenticated
- ✅ Rate limiting active
- ✅ Input validation working

---

### Step 6.2: Secrets Management (2 hours)

**Actions:**

1. **Move Secrets to Secret Manager** (1 hour)
   - Store all API keys
   - Store database passwords
   - Store service credentials

2. **Update Services** (1 hour)
   - Reference secrets from Secret Manager
   - Remove hardcoded secrets
   - Test secret access

**Success Criteria:**
- ✅ No secrets in code
- ✅ All secrets in Secret Manager
- ✅ Services access secrets correctly

---

## 📋 COMPLETE CHECKLIST

### Week 1: Critical Wiring
- [ ] Wire RAG to Creative Generation (4h)
- [ ] Wire HubSpot to Celery (3h)
- [ ] Wire Pre-Spend Prediction (3h)
- [ ] Wire Fatigue Monitoring (3h)
- **Total: 13 hours**

### Week 2: Frontend Integration
- [ ] Wire BattleHardenedSampler UI (4h)
- [ ] Wire RAG Winner Search UI (3h)
- [ ] Wire Self-Learning Dashboard (2h)
- [ ] Wire Pipeline Value Dashboard (2h)
- **Total: 11 hours**

### Week 3: Infrastructure
- [ ] Supabase Setup (4h)
- [ ] Cloud Run Deployment (6h)
- [ ] Redis & Celery Setup (3h)
- **Total: 13 hours**

### Week 4: Monitoring
- [ ] Prometheus & Grafana (4h)
- [ ] Error Tracking (3h)
- **Total: 7 hours**

### Week 5: Testing
- [ ] E2E Test Suite (8h)
- [ ] Load Testing (4h)
- **Total: 12 hours**

### Week 6: Security
- [ ] Security Hardening (4h)
- [ ] Secrets Management (2h)
- **Total: 6 hours**

**Grand Total: 62 hours (1.5 months at 10h/week)**

---

## 🚀 QUICK START (This Week)

### Day 1-2: Critical Wiring (13 hours)
1. Wire RAG to Creative Generation
2. Wire HubSpot to Celery
3. Wire Pre-Spend Prediction
4. Wire Fatigue Monitoring

### Day 3-4: Frontend Basics (6 hours)
1. Wire BattleHardenedSampler UI
2. Wire RAG Winner Search UI

### Day 5: Infrastructure Setup (4 hours)
1. Supabase setup
2. Test connections

**Week 1 Goal: Core functionality wired and accessible**

---

## 📊 SUCCESS METRICS

### Technical Metrics
- ✅ All services deployed to Cloud Run
- ✅ All endpoints accessible
- ✅ Database migrations applied
- ✅ Monitoring active
- ✅ Tests passing

### Business Metrics
- ✅ Users can optimize budgets from UI
- ✅ System learns from winners automatically
- ✅ Fatigue detected and remediated
- ✅ Pipeline value visible in dashboard

---

## 🎯 LONG-TERM ROADMAP (Months 2-3)

### Month 2: Advanced Features
- Federated Cross-Learner (8-12h)
- Proactive Pattern Sharing (8-10h)
- Hook Generation (4-6h)

### Month 3: Scale & Optimize
- Multi-region deployment
- Advanced caching
- Performance optimization
- Cost optimization

---

**This roadmap takes you from 85% to 100% production-ready in 6 weeks.**

