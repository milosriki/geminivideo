# Docker & Cloud Deployment Plan
## Best Strategy for Production Deployment

**Date:** 2025-12-09  
**Goal:** Deploy to Docker and Cloud (GCP recommended)

---

## 🎯 BEST DEPLOYMENT STRATEGY

### **Recommended: Google Cloud Platform (GCP)**

**Why GCP?**
- ✅ Already using GCS (Google Cloud Storage)
- ✅ Cloud Run for serverless containers (auto-scaling)
- ✅ Cloud SQL for managed PostgreSQL
- ✅ Cloud Memorystore for Redis
- ✅ Vertex AI for ML models (future)
- ✅ Best integration with existing GCS usage

**Alternative:** AWS ECS/Fargate or Azure Container Instances

---

## 🐳 DOCKER DEPLOYMENT PLAN

### Phase 1: Complete Docker Setup

#### 1.1 Add Missing Workers to docker-compose.yml

```yaml
# Add to docker-compose.yml

  # Background Workers
  self-learning-worker:
    build:
      context: ./services/gateway-api
      dockerfile: Dockerfile
    container_name: geminivideo-self-learning-worker
    command: npm run worker:self-learning
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
      - ml-service
    restart: unless-stopped
    networks:
      - geminivideo-network

  batch-executor-worker:
    build:
      context: ./services/gateway-api
      dockerfile: Dockerfile
    container_name: geminivideo-batch-executor-worker
    command: npm run worker:batch
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - geminivideo-network

  safe-executor-worker:
    build:
      context: ./services/gateway-api
      dockerfile: Dockerfile
    container_name: geminivideo-safe-executor-worker
    command: npm run worker:safe-executor
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - geminivideo-network

  celery-worker:
    build:
      context: ./services/ml-service
      dockerfile: Dockerfile
    container_name: geminivideo-celery-worker
    command: celery -A src.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
      - ml-service
    restart: unless-stopped
    networks:
      - geminivideo-network

  celery-beat:
    build:
      context: ./services/ml-service
      dockerfile: Dockerfile
    container_name: geminivideo-celery-beat
    command: celery -A src.celery_app beat --loglevel=info
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: redis://redis:6379
    depends_on:
      - postgres
      - redis
      - celery-worker
    restart: unless-stopped
    networks:
      - geminivideo-network
```

#### 1.2 Create Production docker-compose.prod.yml

```yaml
version: '3.8'

services:
  # Use managed services in production
  # postgres -> Cloud SQL
  # redis -> Cloud Memorystore
  
  gateway-api:
    build:
      context: ./services/gateway-api
      dockerfile: Dockerfile.prod
    environment:
      NODE_ENV: production
      PORT: 8000
      DATABASE_URL: ${CLOUD_SQL_CONNECTION_NAME}
      REDIS_URL: ${CLOUD_MEMORYSTORE_URL}
      ML_SERVICE_URL: ${ML_SERVICE_URL}
      VIDEO_AGENT_URL: ${VIDEO_AGENT_URL}
      DRIVE_INTEL_URL: ${DRIVE_INTEL_URL}
    ports:
      - "8000:8000"
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ml-service:
    build:
      context: ./services/ml-service
      dockerfile: Dockerfile.prod
    environment:
      NODE_ENV: production
      DATABASE_URL: ${CLOUD_SQL_CONNECTION_NAME}
      REDIS_URL: ${CLOUD_MEMORYSTORE_URL}
    ports:
      - "8003:8003"
    restart: always

  video-agent:
    build:
      context: ./services/video-agent
      dockerfile: Dockerfile.prod
    environment:
      NODE_ENV: production
      DATABASE_URL: ${CLOUD_SQL_CONNECTION_NAME}
    ports:
      - "8001:8001"
    restart: always

  drive-intel:
    build:
      context: ./services/drive-intel
      dockerfile: Dockerfile.prod
    environment:
      NODE_ENV: production
      DATABASE_URL: ${CLOUD_SQL_CONNECTION_NAME}
    ports:
      - "8002:8002"
    restart: always
```

---

## ☁️ CLOUD DEPLOYMENT PLAN (GCP)

### Phase 2: GCP Cloud Run Deployment

#### 2.1 Cloud Run Setup (Serverless Containers)

**Best for:** Gateway API, ML Service, Video Agent, Drive Intel

**Advantages:**
- ✅ Auto-scaling (0 to N instances)
- ✅ Pay per use (only when handling requests)
- ✅ Automatic HTTPS
- ✅ Built-in load balancing
- ✅ No server management

**Deployment Steps:**

```bash
# 1. Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/gateway-api
gcloud builds submit --tag gcr.io/PROJECT_ID/ml-service
gcloud builds submit --tag gcr.io/PROJECT_ID/video-agent
gcloud builds submit --tag gcr.io/PROJECT_ID/drive-intel

# 2. Deploy to Cloud Run
gcloud run deploy gateway-api \
  --image gcr.io/PROJECT_ID/gateway-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$CLOUD_SQL_URL,REDIS_URL=$MEMORYSTORE_URL

gcloud run deploy ml-service \
  --image gcr.io/PROJECT_ID/ml-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy video-agent \
  --image gcr.io/PROJECT_ID/video-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

gcloud run deploy drive-intel \
  --image gcr.io/PROJECT_ID/drive-intel \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### 2.2 Cloud SQL (Managed PostgreSQL)

```bash
# Create Cloud SQL instance
gcloud sql instances create geminivideo-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create geminivideo --instance=geminivideo-db

# Get connection name
gcloud sql instances describe geminivideo-db --format="value(connectionName)"
```

#### 2.3 Cloud Memorystore (Managed Redis)

```bash
# Create Redis instance
gcloud redis instances create geminivideo-redis \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0
```

#### 2.4 Cloud Run Jobs (For Background Workers)

```bash
# Deploy self-learning worker as Cloud Run Job
gcloud run jobs create self-learning-worker \
  --image gcr.io/PROJECT_ID/gateway-api \
  --command npm \
  --args run,worker:self-learning \
  --region us-central1 \
  --schedule "*/5 * * * *"  # Run every 5 minutes

# Deploy batch executor worker
gcloud run jobs create batch-executor-worker \
  --image gcr.io/PROJECT_ID/gateway-api \
  --command npm \
  --args run,worker:batch \
  --region us-central1 \
  --schedule "*/10 * * * *"  # Run every 10 minutes
```

---

## 🚀 COMPLETE DEPLOYMENT PLAN

### Option A: Full Docker (Local/On-Premise)

**Best for:** Development, testing, on-premise deployment

**Steps:**
1. ✅ Complete docker-compose.yml with all workers
2. ✅ Create .env.production file
3. ✅ Run: `docker-compose -f docker-compose.yml up -d`
4. ✅ All services + workers running locally

**Pros:**
- ✅ Full control
- ✅ No cloud costs
- ✅ Easy to debug

**Cons:**
- ❌ Manual scaling
- ❌ Need to manage infrastructure
- ❌ No auto-scaling

---

### Option B: Hybrid (Docker + Cloud Services)

**Best for:** Production with managed databases

**Steps:**
1. ✅ Deploy services to Cloud Run (serverless)
2. ✅ Use Cloud SQL for database
3. ✅ Use Cloud Memorystore for Redis
4. ✅ Use Cloud Run Jobs for workers
5. ✅ Keep Docker for local development

**Pros:**
- ✅ Auto-scaling services
- ✅ Managed databases (no maintenance)
- ✅ Pay per use
- ✅ High availability

**Cons:**
- ❌ Cloud costs
- ❌ Need GCP account

---

### Option C: Full Cloud (GCP Everything)

**Best for:** Maximum scalability and reliability

**Steps:**
1. ✅ All services on Cloud Run
2. ✅ Cloud SQL for database
3. ✅ Cloud Memorystore for Redis
4. ✅ Cloud Run Jobs for workers
5. ✅ Cloud Load Balancer for routing
6. ✅ Cloud CDN for static assets

**Pros:**
- ✅ Maximum scalability
- ✅ High availability
- ✅ Global distribution
- ✅ Auto-scaling everything

**Cons:**
- ❌ Highest cloud costs
- ❌ More complex setup

---

## 📋 RECOMMENDED: Option B (Hybrid)

### Why Hybrid is Best:

1. **Cost Effective:**
   - Cloud Run: Pay per request (cheap when idle)
   - Cloud SQL: Managed but affordable
   - Cloud Memorystore: Small instance is cheap

2. **Scalable:**
   - Auto-scales from 0 to thousands of instances
   - No need to manage servers

3. **Reliable:**
   - Managed databases (backups, updates automatic)
   - High availability built-in

4. **Flexible:**
   - Can still use Docker locally
   - Easy to switch between local and cloud

---

## 🛠️ DEPLOYMENT STEPS (Option B - Hybrid)

### Step 1: Prepare Docker Images

```bash
# Create production Dockerfiles
# services/gateway-api/Dockerfile.prod
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Step 2: Set Up GCP Resources

```bash
# 1. Create GCP project
gcloud projects create geminivideo-prod

# 2. Enable APIs
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  cloudbuild.googleapis.com

# 3. Create Cloud SQL
gcloud sql instances create geminivideo-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro

# 4. Create Cloud Memorystore
gcloud redis instances create geminivideo-redis \
  --size=1 \
  --region=us-central1
```

### Step 3: Build and Deploy

```bash
# Build images
gcloud builds submit --tag gcr.io/PROJECT_ID/gateway-api ./services/gateway-api
gcloud builds submit --tag gcr.io/PROJECT_ID/ml-service ./services/ml-service
gcloud builds submit --tag gcr.io/PROJECT_ID/video-agent ./services/video-agent
gcloud builds submit --tag gcr.io/PROJECT_ID/drive-intel ./services/drive-intel

# Deploy to Cloud Run
gcloud run deploy gateway-api \
  --image gcr.io/PROJECT_ID/gateway-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=$CLOUD_SQL_URL

# Deploy workers as Cloud Run Jobs
gcloud run jobs create self-learning-worker \
  --image gcr.io/PROJECT_ID/gateway-api \
  --command npm \
  --args run,worker:self-learning \
  --region us-central1
```

### Step 4: Configure DNS & Load Balancer

```bash
# Set up custom domain
gcloud run domain-mappings create \
  --service gateway-api \
  --domain api.geminivideo.com \
  --region us-central1
```

---

## 📊 COST ESTIMATE (GCP Hybrid)

### Monthly Costs (Estimated):

- **Cloud Run:** $0-50 (pay per request, free tier: 2M requests)
- **Cloud SQL (db-f1-micro):** ~$10/month
- **Cloud Memorystore (1GB):** ~$30/month
- **Cloud Storage (GCS):** ~$5/month (for patterns)
- **Total:** ~$45-95/month (low traffic)

**High Traffic (1M requests/day):**
- Cloud Run: ~$200/month
- Cloud SQL: ~$50/month (upgrade tier)
- Cloud Memorystore: ~$100/month (larger)
- **Total:** ~$350/month

---

## ✅ QUICK START: Deploy Now

### Fastest Path to Production:

1. **Complete docker-compose.yml** (add workers)
2. **Test locally:** `docker-compose up`
3. **Deploy to Cloud Run:** Use provided scripts
4. **Configure managed services:** Cloud SQL + Memorystore
5. **Set up workers:** Cloud Run Jobs

**Time to Production:** 2-4 hours

---

## 🎯 RECOMMENDATION

**Best Plan: Option B (Hybrid)**

1. ✅ Use Docker for local development
2. ✅ Deploy services to Cloud Run (auto-scaling)
3. ✅ Use Cloud SQL for database (managed)
4. ✅ Use Cloud Memorystore for Redis (managed)
5. ✅ Use Cloud Run Jobs for workers (scheduled)

**Why:**
- Best balance of cost and scalability
- Easy to maintain
- Production-ready
- Can scale from 0 to millions of requests

---

**Ready to deploy? I can create the complete docker-compose.yml with workers and GCP deployment scripts!** 🚀

