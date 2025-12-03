# Cloud Run Deployment Guide for Gemini Video

Complete guide to deploying the Gemini Video backend services to Google Cloud Run.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Database Setup](#database-setup)
- [Redis Setup](#redis-setup)
- [Manual Deployment](#manual-deployment)
- [Automated Deployment](#automated-deployment)
- [Environment Variables](#environment-variables)
- [Custom Domain Setup](#custom-domain-setup)
- [Monitoring & Logging](#monitoring--logging)
- [Troubleshooting](#troubleshooting)
- [Cost Optimization](#cost-optimization)

---

## Architecture Overview

The Gemini Video platform consists of multiple microservices:

- **Gateway API** (Node.js/TypeScript) - Main entry point, handles routing and authentication
- **Titan Core** (Python/FastAPI) - AI Council, orchestration, and master pipeline
- **Video Agent** (Python/FastAPI) - Video processing and analysis
- **ML Service** (Python/FastAPI) - Machine learning models and predictions
- **Drive Intel** (Python/FastAPI) - Google Drive integration
- **Meta Publisher** (Python/FastAPI) - Meta Ads publishing
- **Frontend** (React/Vite) - User interface (deployed separately to Vercel/Cloud Run)

### Service Communication

```
Internet → Gateway API → Backend Services (Titan Core, Video Agent, etc.)
                  ↓
            PostgreSQL / Supabase
                  ↓
            Redis / Upstash
```

---

## Prerequisites

### 1. Install Required Tools

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud init

# Verify installation
gcloud --version

# Install Docker (if building locally)
# Visit: https://docs.docker.com/get-docker/

# Install jq (for JSON parsing in scripts)
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```

### 2. Google Cloud Project Setup

```bash
# Create a new project (or use existing)
export PROJECT_ID="geminivideo-prod"
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  sql-component.googleapis.com \
  redis.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudtasks.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com

# Set default region
export REGION="us-central1"
gcloud config set run/region $REGION
```

### 3. Create Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create geminivideo-cloud-run \
  --display-name="Gemini Video Cloud Run Service Account"

# Get service account email
export SERVICE_ACCOUNT="geminivideo-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/aiplatform.user"
```

### 4. Create Artifact Registry Repository

```bash
# Create repository for Docker images
gcloud artifacts repositories create geminivideo \
  --repository-format=docker \
  --location=$REGION \
  --description="Gemini Video Docker images"

# Configure Docker authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

---

## Database Setup

You have two options: **Cloud SQL (PostgreSQL)** or **Supabase** (recommended for faster setup).

### Option A: Supabase (Recommended)

1. **Create Supabase Project**
   - Go to https://supabase.com
   - Create a new project
   - Note your project URL, anon key, and service role key

2. **Set up database schema**
   ```bash
   # Use Supabase SQL Editor to run migrations
   # Or use the Prisma schema from services/gateway-api/prisma/schema.prisma
   ```

3. **Environment Variables**
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
   ```

### Option B: Cloud SQL (PostgreSQL)

1. **Create Cloud SQL Instance**
   ```bash
   gcloud sql instances create geminivideo-db \
     --database-version=POSTGRES_15 \
     --tier=db-f1-micro \
     --region=$REGION \
     --network=default \
     --no-assign-ip

   # Create database
   gcloud sql databases create geminivideo \
     --instance=geminivideo-db

   # Create user
   gcloud sql users create geminivideo \
     --instance=geminivideo-db \
     --password=YOUR_SECURE_PASSWORD
   ```

2. **Enable Cloud SQL Proxy for Cloud Run**
   ```bash
   # Get connection name
   export CONNECTION_NAME=$(gcloud sql instances describe geminivideo-db \
     --format='value(connectionName)')

   echo "Connection name: $CONNECTION_NAME"
   # Format: PROJECT_ID:REGION:INSTANCE_NAME
   ```

3. **Database URL Format**
   ```bash
   DATABASE_URL=postgresql://geminivideo:PASSWORD@localhost/geminivideo?host=/cloudsql/${CONNECTION_NAME}
   ```

---

## Redis Setup

You have two options: **Upstash** (serverless, recommended) or **Memorystore**.

### Option A: Upstash (Recommended)

1. **Create Upstash Database**
   - Go to https://upstash.com
   - Create a new Redis database
   - Select region closest to your Cloud Run deployment
   - Note your Redis URL (includes authentication)

2. **Environment Variable**
   ```bash
   REDIS_URL=rediss://default:YOUR_PASSWORD@your-db.upstash.io:6379
   ```

### Option B: Google Cloud Memorystore

1. **Create Memorystore Instance**
   ```bash
   gcloud redis instances create geminivideo-redis \
     --size=1 \
     --region=$REGION \
     --redis-version=redis_7_0 \
     --network=default

   # Get instance details
   gcloud redis instances describe geminivideo-redis \
     --region=$REGION
   ```

2. **Setup Serverless VPC Connector** (required for Cloud Run to access Memorystore)
   ```bash
   gcloud compute networks vpc-access connectors create geminivideo-connector \
     --region=$REGION \
     --network=default \
     --range=10.8.0.0/28 \
     --min-instances=2 \
     --max-instances=10
   ```

3. **Environment Variable**
   ```bash
   REDIS_URL=redis://MEMORYSTORE_IP:6379
   ```

---

## Manual Deployment

### Step 1: Prepare Environment Variables

Create a `.env.production` file:

```bash
cp .env.example .env.production
# Edit with your production values
```

Required variables:
```bash
# AI APIs
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key

# Database
DATABASE_URL=your_database_url
REDIS_URL=your_redis_url

# Meta Ads (optional)
META_ACCESS_TOKEN=your_token
META_AD_ACCOUNT_ID=act_xxxxx
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret

# GCP
GCP_PROJECT_ID=your_project_id
GCS_BUCKET_NAME=your_bucket_name

# Service URLs (will be updated after deployment)
GATEWAY_API_URL=https://gateway-api-xxx.run.app
TITAN_CORE_URL=https://titan-core-xxx.run.app
VIDEO_AGENT_URL=https://video-agent-xxx.run.app
ML_SERVICE_URL=https://ml-service-xxx.run.app
```

### Step 2: Store Secrets in Secret Manager

```bash
# Store sensitive environment variables
gcloud secrets create gemini-api-key --data-file=<(echo -n "$GEMINI_API_KEY")
gcloud secrets create anthropic-api-key --data-file=<(echo -n "$ANTHROPIC_API_KEY")
gcloud secrets create openai-api-key --data-file=<(echo -n "$OPENAI_API_KEY")
gcloud secrets create database-url --data-file=<(echo -n "$DATABASE_URL")
gcloud secrets create redis-url --data-file=<(echo -n "$REDIS_URL")
gcloud secrets create meta-access-token --data-file=<(echo -n "$META_ACCESS_TOKEN")

# Grant service account access to secrets
for secret in gemini-api-key anthropic-api-key openai-api-key database-url redis-url meta-access-token; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor"
done
```

### Step 3: Build and Push Docker Images

```bash
# Set variables
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export REPO="geminivideo"

# Build and push each service
services=("gateway-api" "titan-core" "video-agent" "ml-service" "drive-intel" "meta-publisher")

for service in "${services[@]}"; do
  echo "Building $service..."
  docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${service}:latest \
    ./services/${service}

  echo "Pushing $service..."
  docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${service}:latest
done
```

### Step 4: Deploy Services to Cloud Run

Deploy services in order (dependencies first):

#### 1. Deploy Video Agent
```bash
gcloud run deploy geminivideo-video-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/video-agent:latest \
  --region=$REGION \
  --platform=managed \
  --service-account=${SERVICE_ACCOUNT} \
  --memory=2Gi \
  --cpu=2 \
  --timeout=600 \
  --max-instances=10 \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --allow-unauthenticated
```

#### 2. Deploy ML Service
```bash
gcloud run deploy geminivideo-ml-service \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/ml-service:latest \
  --region=$REGION \
  --platform=managed \
  --service-account=${SERVICE_ACCOUNT} \
  --memory=4Gi \
  --cpu=2 \
  --timeout=900 \
  --max-instances=5 \
  --set-secrets="DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest" \
  --allow-unauthenticated
```

#### 3. Deploy Drive Intel
```bash
gcloud run deploy geminivideo-drive-intel \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/drive-intel:latest \
  --region=$REGION \
  --platform=managed \
  --service-account=${SERVICE_ACCOUNT} \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
  --allow-unauthenticated
```

#### 4. Deploy Meta Publisher
```bash
gcloud run deploy geminivideo-meta-publisher \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/meta-publisher:latest \
  --region=$REGION \
  --platform=managed \
  --service-account=${SERVICE_ACCOUNT} \
  --memory=1Gi \
  --cpu=1 \
  --set-secrets="META_ACCESS_TOKEN=meta-access-token:latest" \
  --allow-unauthenticated
```

#### 5. Deploy Titan Core
```bash
# Get service URLs
VIDEO_AGENT_URL=$(gcloud run services describe geminivideo-video-agent --region=$REGION --format='value(status.url)')
ML_SERVICE_URL=$(gcloud run services describe geminivideo-ml-service --region=$REGION --format='value(status.url)')

gcloud run deploy geminivideo-titan-core \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/titan-core:latest \
  --region=$REGION \
  --platform=managed \
  --service-account=${SERVICE_ACCOUNT} \
  --memory=4Gi \
  --cpu=2 \
  --timeout=900 \
  --max-instances=10 \
  --set-env-vars="VIDEO_AGENT_URL=${VIDEO_AGENT_URL},ML_SERVICE_URL=${ML_SERVICE_URL},GCP_PROJECT_ID=${PROJECT_ID}" \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,ANTHROPIC_API_KEY=anthropic-api-key:latest,OPENAI_API_KEY=openai-api-key:latest,DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest" \
  --allow-unauthenticated
```

#### 6. Deploy Gateway API
```bash
# Get all service URLs
TITAN_CORE_URL=$(gcloud run services describe geminivideo-titan-core --region=$REGION --format='value(status.url)')
VIDEO_AGENT_URL=$(gcloud run services describe geminivideo-video-agent --region=$REGION --format='value(status.url)')
ML_SERVICE_URL=$(gcloud run services describe geminivideo-ml-service --region=$REGION --format='value(status.url)')
DRIVE_INTEL_URL=$(gcloud run services describe geminivideo-drive-intel --region=$REGION --format='value(status.url)')
META_PUBLISHER_URL=$(gcloud run services describe geminivideo-meta-publisher --region=$REGION --format='value(status.url)')

gcloud run deploy geminivideo-gateway-api \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/gateway-api:latest \
  --region=$REGION \
  --platform=managed \
  --service-account=${SERVICE_ACCOUNT} \
  --memory=1Gi \
  --cpu=1 \
  --timeout=300 \
  --max-instances=20 \
  --set-env-vars="TITAN_CORE_URL=${TITAN_CORE_URL},VIDEO_AGENT_URL=${VIDEO_AGENT_URL},ML_SERVICE_URL=${ML_SERVICE_URL},DRIVE_INTEL_URL=${DRIVE_INTEL_URL},META_PUBLISHER_URL=${META_PUBLISHER_URL}" \
  --set-secrets="DATABASE_URL=database-url:latest,REDIS_URL=redis-url:latest" \
  --allow-unauthenticated
```

### Step 5: Verify Deployment

```bash
# Get Gateway URL
GATEWAY_URL=$(gcloud run services describe geminivideo-gateway-api --region=$REGION --format='value(status.url)')

# Test health endpoint
curl ${GATEWAY_URL}/health

# View logs
gcloud run services logs read geminivideo-gateway-api --region=$REGION
```

---

## Automated Deployment

Use the provided deployment script for streamlined deployment:

```bash
# Make script executable
chmod +x scripts/deploy-cloud-run.sh

# Run deployment
./scripts/deploy-cloud-run.sh

# Or deploy specific service
./scripts/deploy-cloud-run.sh titan-core
```

### Using Cloud Build (CI/CD)

The project includes `cloudbuild.yaml` for automated deployments:

```bash
# Trigger manual build
gcloud builds submit --config=cloudbuild.yaml

# Create trigger for automatic deployments on push
gcloud builds triggers create github \
  --name="geminivideo-deploy" \
  --repo-name="geminivideo" \
  --repo-owner="YOUR_GITHUB_USERNAME" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml"
```

---

## Environment Variables

### Gateway API
```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
TITAN_CORE_URL=https://...
VIDEO_AGENT_URL=https://...
ML_SERVICE_URL=https://...
DRIVE_INTEL_URL=https://...
META_PUBLISHER_URL=https://...
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET=your_secret
```

### Titan Core
```bash
GEMINI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
OPENAI_API_KEY=xxx
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
VIDEO_AGENT_URL=https://...
ML_SERVICE_URL=https://...
GCP_PROJECT_ID=xxx
GCS_BUCKET_NAME=xxx
```

### Video Agent
```bash
GEMINI_API_KEY=xxx
GCP_PROJECT_ID=xxx
TEMP_STORAGE_PATH=/tmp/video
MAX_VIDEO_SIZE_MB=500
```

### ML Service
```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
MIN_SAMPLES_FOR_UPDATE=50
LEARNING_RATE=0.01
```

---

## Custom Domain Setup

### 1. Map Custom Domain to Cloud Run

```bash
# Add domain mapping to Gateway API
gcloud run domain-mappings create \
  --service=geminivideo-gateway-api \
  --domain=api.yourdomain.com \
  --region=$REGION
```

### 2. Update DNS Records

Cloud Run will provide DNS records (A and AAAA). Add these to your DNS provider:

```
Type: A
Name: api
Value: 216.239.32.21

Type: AAAA
Name: api
Value: 2001:4860:4802:32::15
```

### 3. Enable SSL (Automatic)

Cloud Run automatically provisions and manages SSL certificates for custom domains.

---

## Monitoring & Logging

### Cloud Logging

```bash
# View logs for specific service
gcloud run services logs read geminivideo-gateway-api \
  --region=$REGION \
  --limit=50

# Stream logs
gcloud run services logs tail geminivideo-gateway-api \
  --region=$REGION

# Filter logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=geminivideo-gateway-api AND severity>=ERROR" \
  --limit=50 \
  --format=json
```

### Cloud Monitoring

1. **Create Uptime Checks**
   ```bash
   # Via Cloud Console: Monitoring > Uptime checks
   # Monitor /health endpoints for all services
   ```

2. **Set Up Alerts**
   - Error rate > 5%
   - Request latency > 5s
   - Instance count > 80% of max

3. **Create Dashboard**
   - Request count
   - Error rate
   - Latency (p50, p95, p99)
   - Instance count
   - Memory usage
   - CPU utilization

### Application Performance Monitoring (APM)

Consider integrating:
- **Google Cloud Trace** - Distributed tracing
- **Google Cloud Profiler** - Performance profiling
- **Sentry** - Error tracking
- **DataDog** / **New Relic** - Full-stack observability

---

## Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check logs
gcloud run services logs read SERVICE_NAME --region=$REGION

# Check revisions
gcloud run revisions list --service=SERVICE_NAME --region=$REGION

# Common causes:
# - Missing environment variables
# - Database connection issues
# - Port misconfiguration (must listen on $PORT)
```

#### 2. Database Connection Timeout

```bash
# For Cloud SQL: Ensure Cloud SQL Proxy is configured
# Add --add-cloudsql-instances flag to deployment

gcloud run services update SERVICE_NAME \
  --add-cloudsql-instances=${CONNECTION_NAME} \
  --region=$REGION

# For Supabase: Check connection string and pooling
```

#### 3. Out of Memory Errors

```bash
# Increase memory allocation
gcloud run services update SERVICE_NAME \
  --memory=4Gi \
  --region=$REGION
```

#### 4. Request Timeout

```bash
# Increase timeout (max 60 minutes)
gcloud run services update SERVICE_NAME \
  --timeout=900 \
  --region=$REGION
```

#### 5. Cold Start Issues

```bash
# Set minimum instances
gcloud run services update SERVICE_NAME \
  --min-instances=1 \
  --region=$REGION

# Note: This increases costs but eliminates cold starts
```

### Debug Mode

Enable detailed logging:

```bash
gcloud run services update SERVICE_NAME \
  --set-env-vars="DEBUG=true,LOG_LEVEL=debug" \
  --region=$REGION
```

---

## Cost Optimization

### 1. Right-size Resources

Start with minimal resources and scale up based on metrics:

```bash
# Recommended starting configuration
--memory=1Gi \
--cpu=1 \
--min-instances=0 \
--max-instances=10
```

### 2. Use Minimum Instances Strategically

Only set `--min-instances` for critical services that need instant response:

```bash
# Gateway API: min-instances=1 (user-facing)
# Backend services: min-instances=0 (can tolerate cold starts)
```

### 3. Implement Caching

- Use Redis for frequently accessed data
- Enable Cloud CDN for static assets
- Implement response caching in API

### 4. Monitor and Optimize

```bash
# View cost breakdown
gcloud billing accounts list
gcloud billing projects describe $PROJECT_ID

# Analyze usage
# Cloud Console > Billing > Cost table
```

### 5. Use Preemptible/Spot Instances for Batch Jobs

For non-critical background tasks:

```bash
gcloud run jobs create batch-job \
  --image=IMAGE_URL \
  --region=$REGION \
  --task-timeout=1h \
  --max-retries=3
```

### Estimated Monthly Costs

| Service | Config | Est. Cost* |
|---------|--------|-----------|
| Gateway API | 1Gi, 1 CPU, min=1 | $15-30 |
| Titan Core | 4Gi, 2 CPU, min=0 | $20-50 |
| Video Agent | 2Gi, 2 CPU, min=0 | $15-40 |
| ML Service | 4Gi, 2 CPU, min=0 | $20-50 |
| Other Services | 1Gi, 1 CPU, min=0 | $10-20 each |
| **Total** | | **$100-250/month** |

*Based on moderate traffic (10K requests/day). Includes free tier.

---

## Best Practices

1. **Security**
   - Never commit secrets to git
   - Use Secret Manager for sensitive data
   - Enable VPC Service Controls for enhanced security
   - Use service accounts with minimal permissions
   - Enable Cloud Armor for DDoS protection

2. **Performance**
   - Implement health checks properly
   - Use connection pooling for databases
   - Enable HTTP/2 and gRPC where applicable
   - Optimize Docker images (multi-stage builds)
   - Use caching aggressively

3. **Reliability**
   - Set appropriate timeout values
   - Implement retry logic with exponential backoff
   - Use Circuit Breakers for external dependencies
   - Monitor error rates and set up alerts
   - Test failover scenarios

4. **Development Workflow**
   - Use separate projects for dev/staging/prod
   - Implement blue-green deployments
   - Use Cloud Build for CI/CD
   - Tag images with git commit SHA
   - Implement database migrations carefully

---

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Best Practices for Cloud Run](https://cloud.google.com/run/docs/tips)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Supabase Documentation](https://supabase.com/docs)
- [Upstash Documentation](https://docs.upstash.com/)

---

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review logs in Cloud Logging
- Open an issue in the GitHub repository
- Contact the development team

---

**Last Updated:** 2025-12-02
**Version:** 1.0.0
