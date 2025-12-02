# Deployment Guide

**Gemini Video Platform - Production Deployment**
Version: 1.0.0
Last Updated: 2025-12-02

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Cloud Deployment (GCP)](#cloud-deployment-gcp)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring Setup](#monitoring-setup)
8. [Scaling Guide](#scaling-guide)

---

## Prerequisites

### Required Software

**Development Machine:**
- Docker Desktop 20.10+ (required)
- Docker Compose 2.0+ (required)
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend services)
- Git 2.30+ (version control)

**Cloud Deployment:**
- Google Cloud SDK (gcloud CLI)
- Terraform 1.5+ (infrastructure as code)
- kubectl (Kubernetes CLI, optional)

### Required Accounts & API Keys

**Essential:**
- Google Cloud Platform account
- Gemini API key (AI analysis)
- Meta Business account + App ID (Meta integration)
- Firebase project (authentication)

**Optional:**
- Anthropic API key (Claude)
- OpenAI API key (GPT-4)
- Sentry account (error tracking)
- Datadog/New Relic (monitoring)

### System Requirements

**Minimum (Development):**
- CPU: 4 cores
- RAM: 8 GB
- Disk: 20 GB free
- Internet: 10 Mbps

**Recommended (Production):**
- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 100 GB+ SSD
- Internet: 100+ Mbps
- GPU: Optional (speeds up ML inference)

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo
```

### 2. Create Environment File

Copy the example environment file:

```bash
cp .env.production.example .env.production
```

Edit `.env.production` with your actual credentials:

```bash
nano .env.production
```

**Critical Variables to Set:**

```bash
# Database (generate strong password)
POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD_MIN_32_CHARS

# JWT Secret (generate with: openssl rand -base64 64)
JWT_SECRET=YOUR_SECURE_JWT_SECRET_64_CHARS

# Gemini API (required)
GEMINI_API_KEY=your_gemini_api_key_here

# Meta API (required for publishing)
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_1234567890
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret

# GCP Project
GCP_PROJECT_ID=your-gcp-project-id
GCS_BUCKET_NAME=your-gcs-bucket-name

# Firebase (frontend auth)
VITE_FIREBASE_API_KEY=your_firebase_api_key
VITE_FIREBASE_PROJECT_ID=your-firebase-project-id
```

**Security Checklist:**
- [ ] Passwords are 32+ characters
- [ ] JWT secret is randomly generated
- [ ] All API keys are valid
- [ ] .env.production is in .gitignore
- [ ] No credentials committed to Git

---

### 3. Obtain API Keys

#### Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy and save to `.env.production`

#### Meta API Credentials

1. Go to https://developers.facebook.com
2. Create a new app (Business type)
3. Add "Marketing API" product
4. Generate access token (Settings > Basic)
5. Get Ad Account ID from Ads Manager

**Required Permissions:**
- ads_management
- ads_read
- business_management
- pages_read_engagement

#### Firebase Setup

1. Go to https://console.firebase.google.com
2. Create new project
3. Enable Authentication (Email/Password, Google)
4. Get config from Project Settings > General
5. Add to `.env.production`

---

## Local Development

### Quick Start (Recommended)

Start all services with one command:

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

**Access Services:**
- Frontend: http://localhost:3000
- Gateway API: http://localhost:8080
- Drive Intel: http://localhost:8081
- Video Agent: http://localhost:8082
- ML Service: http://localhost:8003
- Meta Publisher: http://localhost:8083
- Titan Core: http://localhost:8084

---

### Individual Service Development

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Access at http://localhost:5173
```

**Gateway API:**
```bash
cd services/gateway-api
npm install
npm run dev
# Runs on http://localhost:8080
```

**Drive Intel (Python):**
```bash
cd services/drive-intel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8081
```

**Verify Setup:**
```bash
# Test Gateway API
curl http://localhost:8080/health

# Test Drive Intel
curl http://localhost:8081/health

# Expected response:
{"status":"healthy","timestamp":"2025-12-02T10:30:00Z"}
```

---

## Docker Deployment

### Production Docker Compose

Use the production-optimized Docker Compose file:

```bash
# Build all images
docker-compose -f docker-compose.production.yml build

# Start all services
docker-compose -f docker-compose.production.yml up -d

# View logs
docker-compose -f docker-compose.production.yml logs -f gateway-api

# Stop all services
docker-compose -f docker-compose.production.yml down

# Stop and remove volumes (⚠️ destroys data)
docker-compose -f docker-compose.production.yml down -v
```

### Resource Allocation

Edit `docker-compose.production.yml` to adjust resources:

```yaml
ml-service:
  deploy:
    resources:
      limits:
        cpus: '4'      # Max 4 CPU cores
        memory: 16G    # Max 16 GB RAM
      reservations:
        cpus: '2'      # Minimum 2 cores
        memory: 8G     # Minimum 8 GB
```

### Health Checks

All services include health checks:

```bash
# Check service health
docker inspect --format='{{.State.Health.Status}}' geminivideo-gateway-api-prod

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' geminivideo-gateway-api-prod
```

---

## Cloud Deployment (GCP)

### Option 1: Automated Deployment Script

Use the provided deployment script:

```bash
# Set up GCP project
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# Authenticate
gcloud auth login
gcloud config set project $GCP_PROJECT_ID

# Run deployment script
./scripts/deploy.sh
```

**Deployment Script Does:**
1. ✅ Enables required GCP APIs
2. ✅ Creates GCS bucket for storage
3. ✅ Sets up Cloud SQL (PostgreSQL)
4. ✅ Sets up Cloud Memorystore (Redis)
5. ✅ Builds Docker images
6. ✅ Pushes to Artifact Registry
7. ✅ Deploys to Cloud Run
8. ✅ Configures networking
9. ✅ Sets up monitoring

---

### Option 2: Manual GCP Setup

#### Step 1: Enable APIs

```bash
gcloud services enable \
  cloudrun.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  monitoring.googleapis.com
```

#### Step 2: Create Artifact Registry

```bash
# Create Docker repository
gcloud artifacts repositories create geminivideo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Gemini Video Docker images"

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev
```

#### Step 3: Set Up Cloud SQL (PostgreSQL)

```bash
# Create instance
gcloud sql instances create geminivideo-db \
  --database-version=POSTGRES_15 \
  --tier=db-n1-standard-2 \
  --region=us-central1 \
  --backup-start-time=03:00 \
  --enable-bin-log

# Create database
gcloud sql databases create geminivideo \
  --instance=geminivideo-db

# Create user
gcloud sql users create geminivideo \
  --instance=geminivideo-db \
  --password=YOUR_SECURE_PASSWORD
```

#### Step 4: Set Up Cloud Memorystore (Redis)

```bash
gcloud redis instances create geminivideo-redis \
  --size=5 \
  --region=us-central1 \
  --tier=standard \
  --redis-version=redis_7_0
```

#### Step 5: Create GCS Bucket

```bash
gsutil mb -p $GCP_PROJECT_ID -c STANDARD -l us-central1 gs://geminivideo-production

# Set lifecycle policy
cat > lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["videos/temp/"]
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://geminivideo-production
```

#### Step 6: Store Secrets

```bash
# Create secrets in Secret Manager
echo -n "YOUR_JWT_SECRET" | gcloud secrets create jwt-secret --data-file=-
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_META_ACCESS_TOKEN" | gcloud secrets create meta-access-token --data-file=-
```

#### Step 7: Build and Push Images

```bash
# Set variables
export PROJECT_ID=your-project-id
export REGION=us-central1
export REGISTRY=$REGION-docker.pkg.dev/$PROJECT_ID/geminivideo

# Build Gateway API
docker build -t $REGISTRY/gateway-api:latest ./services/gateway-api
docker push $REGISTRY/gateway-api:latest

# Build Drive Intel
docker build -t $REGISTRY/drive-intel:latest ./services/drive-intel
docker push $REGISTRY/drive-intel:latest

# Build Video Agent
docker build -t $REGISTRY/video-agent:latest ./services/video-agent
docker push $REGISTRY/video-agent:latest

# Build ML Service
docker build -t $REGISTRY/ml-service:latest ./services/ml-service
docker push $REGISTRY/ml-service:latest

# Build Meta Publisher
docker build -t $REGISTRY/meta-publisher:latest ./services/meta-publisher
docker push $REGISTRY/meta-publisher:latest

# Build Titan Core
docker build -t $REGISTRY/titan-core:latest ./services/titan-core
docker push $REGISTRY/titan-core:latest

# Build Frontend
docker build -t $REGISTRY/frontend:latest ./frontend
docker push $REGISTRY/frontend:latest
```

#### Step 8: Deploy to Cloud Run

**Gateway API:**
```bash
gcloud run deploy gateway-api \
  --image=$REGISTRY/gateway-api:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=10 \
  --timeout=300 \
  --set-env-vars="DATABASE_URL=postgresql://...,REDIS_URL=redis://..." \
  --set-secrets="JWT_SECRET=jwt-secret:latest,GEMINI_API_KEY=gemini-api-key:latest"
```

**Drive Intel:**
```bash
gcloud run deploy drive-intel \
  --image=$REGISTRY/drive-intel:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=4Gi \
  --cpu=4 \
  --min-instances=1 \
  --max-instances=5 \
  --timeout=600 \
  --set-env-vars="GCS_BUCKET_NAME=geminivideo-production"
```

**Video Agent:**
```bash
gcloud run deploy video-agent \
  --image=$REGISTRY/video-agent:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=4Gi \
  --cpu=4 \
  --min-instances=1 \
  --max-instances=10 \
  --timeout=900
```

**ML Service:**
```bash
gcloud run deploy ml-service \
  --image=$REGISTRY/ml-service:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=8Gi \
  --cpu=4 \
  --min-instances=2 \
  --max-instances=5
```

**Meta Publisher:**
```bash
gcloud run deploy meta-publisher \
  --image=$REGISTRY/meta-publisher:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=3 \
  --set-secrets="META_ACCESS_TOKEN=meta-access-token:latest"
```

**Titan Core:**
```bash
gcloud run deploy titan-core \
  --image=$REGISTRY/titan-core:latest \
  --region=$REGION \
  --platform=managed \
  --no-allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --min-instances=1 \
  --max-instances=5
```

**Frontend:**
```bash
gcloud run deploy frontend \
  --image=$REGISTRY/frontend:latest \
  --region=$REGION \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=3
```

#### Step 9: Get Service URLs

```bash
# Get all service URLs
gcloud run services list --platform=managed

# Set URLs as environment variables
export GATEWAY_URL=$(gcloud run services describe gateway-api --region=$REGION --format='value(status.url)')
echo $GATEWAY_URL
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy-production.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main
  workflow_dispatch:

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1
  REGISTRY: us-central1-docker.pkg.dev

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    permissions:
      contents: read
      id-token: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGISTRY }}

      - name: Build and push Gateway API
        run: |
          docker build -t ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/geminivideo/gateway-api:${{ github.sha }} ./services/gateway-api
          docker push ${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/geminivideo/gateway-api:${{ github.sha }}

      # Repeat for all services...

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy gateway-api \
            --image=${{ env.REGISTRY }}/${{ env.PROJECT_ID }}/geminivideo/gateway-api:${{ github.sha }} \
            --region=${{ env.REGION }} \
            --platform=managed

      - name: Verify deployment
        run: |
          GATEWAY_URL=$(gcloud run services describe gateway-api --region=${{ env.REGION }} --format='value(status.url)')
          curl -f $GATEWAY_URL/health || exit 1
```

### Required GitHub Secrets

Add these secrets in GitHub Settings > Secrets:

- `GCP_PROJECT_ID` - Your GCP project ID
- `GCP_SA_KEY` - Service account JSON key
- `JWT_SECRET` - JWT secret
- `GEMINI_API_KEY` - Gemini API key
- `META_ACCESS_TOKEN` - Meta access token

---

## Monitoring Setup

### Cloud Monitoring (Stackdriver)

Enable monitoring:

```bash
# Create notification channel (email)
gcloud alpha monitoring channels create \
  --display-name="Alerts Email" \
  --type=email \
  --channel-labels=email_address=alerts@yourdomain.com

# Create uptime check
gcloud monitoring uptime-checks create gateway-health \
  --resource-type=url \
  --host=GATEWAY_URL \
  --path=/health \
  --period=300
```

### Alert Policies

Create alerts for critical metrics:

```bash
# High error rate alert
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 1%" \
  --condition-threshold-value=0.01 \
  --condition-threshold-duration=300s
```

### Dashboards

Create custom dashboard:

1. Go to Cloud Console > Monitoring > Dashboards
2. Click "Create Dashboard"
3. Add charts for:
   - Request rate
   - Latency (p50, p95, p99)
   - Error rate
   - CPU & Memory usage
   - Active instances

---

## Scaling Guide

### Horizontal Scaling

**Auto-scaling based on CPU:**
```bash
gcloud run services update gateway-api \
  --min-instances=2 \
  --max-instances=20 \
  --cpu-throttling \
  --cpu-boost
```

**Auto-scaling based on requests:**
```bash
gcloud run services update gateway-api \
  --concurrency=100 \
  --max-instances=20
```

### Vertical Scaling

Increase resources per instance:

```bash
gcloud run services update ml-service \
  --memory=16Gi \
  --cpu=8
```

### Database Scaling

**Scale Cloud SQL:**
```bash
gcloud sql instances patch geminivideo-db \
  --tier=db-n1-standard-4 \
  --storage-size=100
```

**Add read replicas:**
```bash
gcloud sql instances create geminivideo-db-replica \
  --master-instance-name=geminivideo-db \
  --tier=db-n1-standard-2 \
  --region=us-central1
```

### Redis Scaling

```bash
gcloud redis instances update geminivideo-redis \
  --size=10
```

---

## Production Checklist

Before going live:

**Security:**
- [ ] All secrets in Secret Manager
- [ ] HTTPS enforced
- [ ] CORS configured correctly
- [ ] Rate limiting enabled
- [ ] SQL injection protection active
- [ ] XSS protection enabled

**Infrastructure:**
- [ ] Auto-scaling configured
- [ ] Health checks working
- [ ] Backups enabled
- [ ] Monitoring dashboards created
- [ ] Alert policies set up
- [ ] SSL certificates valid

**Performance:**
- [ ] CDN configured
- [ ] Caching enabled
- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Image optimization enabled

**Compliance:**
- [ ] GDPR compliance reviewed
- [ ] Data retention policies set
- [ ] Privacy policy updated
- [ ] Terms of service updated
- [ ] Cookie consent implemented

**Testing:**
- [ ] Load testing completed
- [ ] Security scanning done
- [ ] Penetration testing passed
- [ ] Backup restore tested
- [ ] Disaster recovery tested

---

## Rollback Procedure

If deployment fails:

```bash
# List revisions
gcloud run revisions list --service=gateway-api

# Rollback to previous revision
gcloud run services update-traffic gateway-api \
  --to-revisions=PREVIOUS_REVISION=100

# Verify rollback
curl https://GATEWAY_URL/health
```

---

## Cost Optimization

**Reduce costs:**

1. **Right-size instances:**
   - Monitor actual usage
   - Adjust min/max instances
   - Reduce CPU/memory if underutilized

2. **Use committed use discounts:**
   - 1-year or 3-year commitments
   - 30-70% savings on compute

3. **Enable auto-pause:**
   - Scale to zero for dev environments
   - Use Cloud Scheduler to wake up

4. **Optimize storage:**
   - Set lifecycle policies
   - Delete old renders/videos
   - Compress thumbnails

5. **Use cheaper regions:**
   - us-central1 (cheapest US region)
   - Consider europe-west1, asia-southeast1

**Estimated Costs (Monthly):**
- Small (1K videos/mo): $100-200
- Medium (10K videos/mo): $500-1000
- Large (100K videos/mo): $3000-5000

---

*Last Updated: 2025-12-02*
*Version: 1.0.0*
