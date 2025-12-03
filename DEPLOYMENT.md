# Gemini Video - Complete Deployment Guide

Complete guide to deploying the Gemini Video AI Ad Intelligence Suite across local development, cloud environments, and production.

**Table of Contents**
- [1. Quick Start (Local Development)](#1-quick-start-local-development)
- [2. Production Deployment](#2-production-deployment)
  - [2.1. Docker Compose Production](#21-docker-compose-production)
  - [2.2. GCP Cloud Run Production](#22-gcp-cloud-run-production)
  - [2.3. GitHub Actions CI/CD](#23-github-actions-cicd)
- [3. Cloud Deployment (Vercel + GCP)](#3-cloud-deployment-vercel--gcp)
- [4. Environment Variables Reference](#4-environment-variables-reference)
- [5. Testing the System](#5-testing-the-system)
- [6. Monitoring and Scaling](#6-monitoring-and-scaling)
- [7. Troubleshooting](#7-troubleshooting)
- [8. Architecture Diagram](#8-architecture-diagram)

---

## 1. Quick Start (Local Development)

### Prerequisites

Before starting, ensure you have installed:

- **Node.js 18+** - [Download](https://nodejs.org/)
  ```bash
  node --version  # Should be v18.0.0 or higher
  ```

- **Python 3.10+** - [Download](https://www.python.org/)
  ```bash
  python --version  # Should be 3.10.0 or higher
  ```

- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)
  ```bash
  docker --version
  docker-compose --version
  ```

- **Git** - [Download](https://git-scm.com/)
  ```bash
  git --version
  ```

- **curl** - For testing API endpoints
  ```bash
  curl --version
  ```

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# Install Node dependencies for frontend
cd frontend
npm install
cd ..

# Create .env file from template
cp .env.example .env
```

### Step 2: Configure Environment Variables

Edit `.env` file with your local configuration:

```bash
# Essential for local development
NODE_ENV=development
VITE_ENV=development

# Database (local PostgreSQL)
DATABASE_URL=postgresql://geminivideo:geminivideo@localhost:5432/geminivideo

# Redis (local)
REDIS_URL=redis://localhost:6379

# Service URLs (local Docker network)
GATEWAY_API_URL=http://localhost:8000
DRIVE_INTEL_URL=http://localhost:8001
VIDEO_AGENT_URL=http://localhost:8002
ML_SERVICE_URL=http://localhost:8003
META_PUBLISHER_URL=http://localhost:8083
TITAN_CORE_URL=http://localhost:8084

# API Keys (get from respective platforms)
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Meta API (optional for local testing)
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_1234567890
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret

# Port Configuration
PORT=8000
GATEWAY_PORT=8000
DRIVE_INTEL_PORT=8001
VIDEO_AGENT_PORT=8002
ML_SERVICE_PORT=8003
META_PUBLISHER_PORT=8083

# Feature Flags
ENABLE_ANALYTICS=true
ENABLE_PERFORMANCE_MONITORING=true
DEBUG=false
LOG_LEVEL=info
```

### Step 3: Run All 6 Services Locally

**Option A: Using Docker Compose (Recommended)**

```bash
# Start all services with automatic health checks
./deploy-local.sh
```

This will:
- Build Docker images for all services
- Start PostgreSQL and Redis
- Start all 6 microservices
- Verify health of each service
- Display access URLs

**Option B: Manual Docker Compose**

```bash
# Build all images (disable BuildKit for npm compatibility)
DOCKER_BUILDKIT=0 docker compose build

# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# View logs
docker compose logs -f
```

**Option C: Run Services Individually (For Development)**

If you prefer running services outside Docker for development:

Terminal 1 - PostgreSQL & Redis:
```bash
docker run --name postgres -e POSTGRES_PASSWORD=geminivideo \
  -e POSTGRES_DB=geminivideo -p 5432:5432 -d postgres:15-alpine

docker run --name redis -p 6379:6379 -d redis:7-alpine
```

Terminal 2 - Gateway API (Node):
```bash
cd services/gateway-api
npm install
npm run dev  # Runs on port 8000
```

Terminal 3 - Drive Intel (Python):
```bash
cd services/drive-intel
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Terminal 4 - Video Agent (Python):
```bash
cd services/video-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8002
```

Terminal 5 - ML Service (Python):
```bash
cd services/ml-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

Terminal 6 - Meta Publisher (Node):
```bash
cd services/meta-publisher
npm install
npm run dev  # Runs on port 8083
```

Terminal 7 - Frontend (React/Vite):
```bash
cd frontend
npm install
npm run dev  # Runs on port 5173
```

Terminal 8 - Titan Core (Python):
```bash
cd services/titan-core
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python orchestrator.py
```

### Step 4: Testing Local Endpoints

Verify all services are running:

```bash
# Test Gateway API
curl http://localhost:8000/health

# Test Drive Intel
curl http://localhost:8001/health

# Test Video Agent
curl http://localhost:8002/health

# Test ML Service
curl http://localhost:8003/health

# Test Meta Publisher
curl http://localhost:8083/health

# Access Frontend
open http://localhost:5173
```

### Step 5: Local Development Workflow

#### Start All Services
```bash
./deploy-local.sh
```

#### View Real-Time Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f gateway-api
```

#### Rebuild After Code Changes
```bash
# Rebuild specific service
docker compose build gateway-api
docker compose up -d gateway-api

# Or rebuild all
DOCKER_BUILDKIT=0 docker compose build
docker compose up -d
```

#### Stop Services
```bash
docker compose down

# Stop and remove volumes
docker compose down -v
```

#### Run Database Migrations
```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U geminivideo -d geminivideo

# Check tables
\dt

# Exit
\q
```

---

## 2. Production Deployment

### 2.1. Docker Compose Production

Production deployment using Docker Compose with optimized configuration, resource limits, and health checks.

#### Prerequisites

- Docker 20.10+ with Docker Compose
- Production server (4+ CPU cores, 16GB+ RAM recommended)
- SSL certificates (for HTTPS)
- Domain name configured

#### Step 1: Prepare Production Environment

```bash
# Clone repository on production server
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# Create production environment file
cp .env.production.example .env.production

# Edit with production credentials
nano .env.production
```

#### Step 2: Configure Production Variables

Edit `.env.production` with your production values:

```bash
# Database (use strong passwords!)
POSTGRES_PASSWORD=YOUR_STRONG_PASSWORD_HERE
DATABASE_URL=postgresql://geminivideo:YOUR_STRONG_PASSWORD_HERE@postgres:5432/geminivideo

# Redis
REDIS_URL=redis://redis:6379

# API Keys
GEMINI_API_KEY=your_production_api_key
META_ACCESS_TOKEN=your_production_token

# Security
JWT_SECRET=$(openssl rand -base64 64)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Image registry (optional, for private registry)
REGISTRY_URL=your-registry.com/geminivideo
IMAGE_TAG=v1.0.0
```

#### Step 3: Deploy with Production Compose

```bash
# Build images
DOCKER_BUILDKIT=0 docker-compose -f docker-compose.production.yml build

# Start services
docker-compose -f docker-compose.production.yml up -d

# Verify all services are healthy
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f
```

#### Step 4: Configure SSL/TLS (Nginx Proxy)

For production HTTPS, use nginx-proxy with Let's Encrypt:

```bash
# Create nginx proxy network
docker network create nginx-proxy

# Run nginx proxy with Let's Encrypt
docker run -d -p 80:80 -p 443:443 \
  --name nginx-proxy \
  --network nginx-proxy \
  -v /var/run/docker.sock:/tmp/docker.sock:ro \
  -v nginx-certs:/etc/nginx/certs:ro \
  -v nginx-vhost:/etc/nginx/vhost.d \
  -v nginx-html:/usr/share/nginx/html \
  nginxproxy/nginx-proxy

docker run -d \
  --name nginx-proxy-acme \
  --network nginx-proxy \
  --volumes-from nginx-proxy \
  -v nginx-certs:/etc/nginx/certs:rw \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e DEFAULT_EMAIL=admin@yourdomain.com \
  nginxproxy/acme-companion
```

Update `docker-compose.production.yml` frontend service:

```yaml
frontend:
  # ... existing config ...
  environment:
    VIRTUAL_HOST: yourdomain.com,www.yourdomain.com
    LETSENCRYPT_HOST: yourdomain.com,www.yourdomain.com
    LETSENCRYPT_EMAIL: admin@yourdomain.com
  networks:
    - geminivideo-network
    - nginx-proxy
```

#### Step 5: Production Monitoring

```bash
# View all service statuses
docker-compose -f docker-compose.production.yml ps

# Check resource usage
docker stats

# View specific service logs
docker-compose -f docker-compose.production.yml logs -f gateway-api

# Restart specific service
docker-compose -f docker-compose.production.yml restart gateway-api
```

#### Step 6: Backup and Maintenance

```bash
# Backup database
docker exec geminivideo-postgres-prod pg_dump -U geminivideo geminivideo > backup-$(date +%Y%m%d).sql

# Backup volumes
docker run --rm -v geminivideo_postgres_data:/data -v $(pwd)/backups:/backup alpine tar czf /backup/postgres-$(date +%Y%m%d).tar.gz /data

# Update services (zero-downtime)
docker-compose -f docker-compose.production.yml pull
docker-compose -f docker-compose.production.yml up -d --no-deps --build gateway-api

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale drive-worker=4 --scale video-worker=2
```

---

### 2.2. GCP Cloud Run Production

Production deployment to Google Cloud Platform using Cloud Run for automatic scaling and managed infrastructure.

#### Prerequisites

- GCP account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally
- GitHub repository (for CI/CD)

#### Step 1: GCP Project Setup

```bash
# Set variables
export PROJECT_ID="geminivideo-prod"
export REGION="us-central1"
export REGISTRY_NAME="geminivideo"

# Create GCP project
gcloud projects create $PROJECT_ID --name="Gemini Video Production"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  storage.googleapis.com \
  sql.googleapis.com \
  redis.googleapis.com

# Set up billing (required for Cloud Run)
# Visit: https://console.cloud.google.com/billing
```

#### Step 2: Create Artifact Registry

```bash
# Create Docker repository
gcloud artifacts repositories create $REGISTRY_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="Gemini Video Production Images"

# Configure Docker authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

#### Step 3: Set Up Managed Database (Cloud SQL)

```bash
# Create Cloud SQL PostgreSQL instance
gcloud sql instances create geminivideo-db \
  --database-version=POSTGRES_15 \
  --tier=db-g1-small \
  --region=$REGION \
  --storage-auto-increase \
  --backup-start-time=03:00

# Create database
gcloud sql databases create geminivideo --instance=geminivideo-db

# Create user
gcloud sql users create geminivideo \
  --instance=geminivideo-db \
  --password=YOUR_STRONG_PASSWORD

# Get connection string
gcloud sql instances describe geminivideo-db --format="value(connectionName)"
```

#### Step 4: Set Up Secrets

```bash
# Store secrets in Secret Manager
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_META_ACCESS_TOKEN" | gcloud secrets create meta-access-token --data-file=-
echo -n "YOUR_JWT_SECRET" | gcloud secrets create jwt-secret --data-file=-
echo -n "postgresql://user:pass@/dbname?host=/cloudsql/CONNECTION_NAME" | gcloud secrets create database-url --data-file=-

# Grant Cloud Run service account access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

for secret in gemini-api-key meta-access-token jwt-secret database-url; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

#### Step 5: Use Production Deployment Script

```bash
# Create production environment file
cp .env.production.example .env.production

# Edit with your values
nano .env.production

# Make deploy script executable (if not already)
chmod +x scripts/deploy-production.sh

# Deploy to Cloud Run
DEPLOYMENT_TARGET=cloud-run ./scripts/deploy-production.sh
```

The deployment script will:
- ✅ Build all Docker images
- ✅ Push to Artifact Registry
- ✅ Deploy services in dependency order
- ✅ Configure environment variables
- ✅ Set up health checks
- ✅ Verify deployment success
- ✅ Display service URLs

#### Step 6: Configure Custom Domain (Optional)

```bash
# Map custom domain to frontend
gcloud run services update frontend \
  --region=$REGION \
  --update-env-vars="VITE_GATEWAY_URL=https://api.yourdomain.com"

# Add domain mapping
gcloud run domain-mappings create \
  --service=frontend \
  --domain=yourdomain.com \
  --region=$REGION

# Configure DNS (add the records shown in the output)
```

#### Step 7: Set Up Monitoring

```bash
# Enable Cloud Monitoring
gcloud services enable monitoring.googleapis.com

# Create uptime check
gcloud monitoring uptime create frontend-uptime \
  --resource-type=uptime-url \
  --host=your-frontend-url.run.app \
  --path=/health

# View logs
gcloud run services logs read gateway-api --region=$REGION --limit=50
```

#### Production Deployment Options

The deployment script supports several options:

```bash
# Full deployment
./scripts/deploy-production.sh

# Skip build step (use existing images)
./scripts/deploy-production.sh --skip-build

# Skip push step
./scripts/deploy-production.sh --skip-push

# Deploy to Docker Compose
./scripts/deploy-production.sh --target docker-compose

# Rollback to previous version
./scripts/deploy-production.sh --rollback

# View help
./scripts/deploy-production.sh --help
```

---

### 2.3. GitHub Actions CI/CD

Automated production deployment using GitHub Actions.

#### Step 1: Configure GitHub Secrets

In your GitHub repository, go to **Settings** → **Secrets and variables** → **Actions** and add:

| Secret Name | Description | Example |
|------------|-------------|---------|
| `GCP_PROJECT_ID` | GCP project ID | `geminivideo-prod` |
| `GCP_SA_KEY` | Service account key (base64) | See below |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` |
| `REDIS_URL` | Redis connection string | `redis://...` |
| `GEMINI_API_KEY` | Gemini API key | `AIza...` |
| `META_ACCESS_TOKEN` | Meta access token | `EAAx...` |
| `META_AD_ACCOUNT_ID` | Meta ad account ID | `act_123...` |
| `META_APP_ID` | Meta app ID | `123456789` |
| `META_APP_SECRET` | Meta app secret | `abc123...` |
| `JWT_SECRET` | JWT secret key | Generated with `openssl rand -base64 64` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://yourdomain.com` |
| `SLACK_WEBHOOK_URL` | Slack webhook (optional) | `https://hooks.slack.com/...` |

#### Step 2: Create Service Account Key

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployer"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

# Base64 encode for GitHub secret
cat key.json | base64 -w 0

# Copy the output and add as GCP_SA_KEY secret in GitHub
```

#### Step 3: Workflow Configuration

The workflow file `.github/workflows/deploy-production.yml` is already configured with:

✅ **Build and Test Job**
- Runs linting and tests
- Validates code quality

✅ **Build Images Job**
- Builds all Docker images
- Pushes to Artifact Registry
- Tags with timestamp and git SHA

✅ **Deploy Production Job**
- Deploys to Cloud Run
- Updates environment variables
- Verifies service health

✅ **Smoke Tests Job**
- Runs post-deployment tests
- Verifies all services are responding

#### Step 4: Trigger Deployment

Deployments are triggered automatically on:

1. **Push to main branch**
   ```bash
   git push origin main
   ```

2. **Manual workflow dispatch**
   - Go to **Actions** → **Deploy to Production** → **Run workflow**

#### Step 5: Monitor Deployment

```bash
# View workflow progress in GitHub Actions tab
# Monitor logs in real-time

# After deployment, check service status
gcloud run services list --region=$REGION

# View deployment logs
gcloud run services logs read gateway-api --region=$REGION
```

#### Deployment Flow

```
┌─────────────────────────────────────────────────────────┐
│                  GitHub Actions Workflow                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Trigger (push to main or manual)                    │
│        ↓                                                 │
│  2. Build & Test                                        │
│     - Install dependencies                              │
│     - Run linters                                       │
│     - Run unit tests                                    │
│        ↓                                                 │
│  3. Build Docker Images                                 │
│     - Build all 7 services                              │
│     - Tag with timestamp-SHA                            │
│     - Push to Artifact Registry                         │
│        ↓                                                 │
│  4. Deploy to Cloud Run                                 │
│     - Deploy ML Service (independent)                   │
│     - Deploy Drive Intel, Video Agent                   │
│     - Deploy Meta Publisher, Titan Core                 │
│     - Deploy Gateway API (with service URLs)            │
│     - Deploy Frontend (with gateway URL)                │
│        ↓                                                 │
│  5. Health Checks                                       │
│     - Verify all services responding                    │
│     - Run smoke tests                                   │
│        ↓                                                 │
│  6. Notify (Slack)                                      │
│     - Send deployment status                            │
│     - Include service URLs                              │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### Rollback Strategy

If deployment fails or issues are detected:

```bash
# List revisions
gcloud run revisions list --service=gateway-api --region=$REGION

# Rollback to previous revision
gcloud run services update-traffic gateway-api \
  --to-revisions=PREVIOUS_REVISION=100 \
  --region=$REGION

# Rollback all services
for service in gateway-api drive-intel video-agent ml-service meta-publisher titan-core frontend; do
  PREV_REVISION=$(gcloud run revisions list --service=$service --region=$REGION --format="value(REVISION)" --limit=2 | tail -1)
  gcloud run services update-traffic $service \
    --to-revisions=$PREV_REVISION=100 \
    --region=$REGION
done
```

---

## 3. Cloud Deployment (Vercel + GCP)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    PRODUCTION DEPLOYMENT                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend (Vercel)                                         │
│  ├─ React/Vite app                                        │
│  └─ Custom domain SSL/TLS                                 │
│                                                             │
│  GCP Cloud Run (Microservices)                            │
│  ├─ Gateway API (Node/Express)                           │
│  ├─ Drive Intel (Python/FastAPI)                         │
│  ├─ Video Agent (Python/FastAPI)                         │
│  ├─ ML Service (Python/FastAPI)                          │
│  ├─ Meta Publisher (Node/Express)                        │
│  └─ Titan Core (Python)                                  │
│                                                             │
│  Supabase (Database)                                       │
│  ├─ PostgreSQL (Primary data)                            │
│  ├─ Backups & replication                                │
│  └─ Real-time subscriptions                              │
│                                                             │
│  External Services                                         │
│  ├─ Meta Marketing API                                   │
│  ├─ Google Drive API                                     │
│  ├─ Google Cloud Vision                                  │
│  └─ Gemini API                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Database Setup (Supabase)

#### Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign in
2. Click "New Project"
3. Fill in project details:
   - **Name**: `geminivideo-prod`
   - **Database Password**: Generate strong password (save it!)
   - **Region**: Choose closest to you
   - **Pricing Plan**: Select "Pro" for production

4. Wait for project initialization (5-10 minutes)

#### Get Connection Details

Once project is created:

1. Go to **Project Settings** → **Database**
2. Copy **JDBC Connection String** (contains password)
3. Format should be: `postgresql://postgres:PASSWORD@db.PROJECT_ID.supabase.co:5432/postgres`

#### Set Environment Variables

```bash
export SUPABASE_URL="https://YOUR_PROJECT_ID.supabase.co"
export SUPABASE_ANON_KEY="your_anon_key"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_ID.supabase.co:5432/postgres"
```

### 2.2 GCP Cloud Run Setup

#### Prerequisites

```bash
# Install Google Cloud SDK
# macOS:
brew install --cask google-cloud-sdk

# Linux:
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

#### Step 1: Create GCP Project

```bash
# Authenticate with Google
gcloud auth login

# Create new project
export PROJECT_ID="geminivideo-prod"
export REGION="us-central1"

gcloud projects create $PROJECT_ID \
  --name="Gemini Video Production"

# Set as default project
gcloud config set project $PROJECT_ID

# Enable billing (required)
# Go to https://console.cloud.google.com/billing
```

#### Step 2: Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  storage.googleapis.com
```

#### Step 3: Create Artifact Registry

```bash
export REGISTRY_NAME="geminivideo"

# Create Docker repository
gcloud artifacts repositories create $REGISTRY_NAME \
  --repository-format=docker \
  --location=$REGION \
  --description="Gemini Video Container Images"

# Configure Docker authentication
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

#### Step 4: Create Secrets

```bash
# Meta API Access Token
echo -n "your_meta_access_token" | \
  gcloud secrets create meta-access-token \
  --data-file=- \
  --replication-policy="automatic"

# Gemini API Key
echo -n "your_gemini_api_key" | \
  gcloud secrets create gemini-api-key \
  --data-file=- \
  --replication-policy="automatic"

# Database Password (for non-Supabase)
echo -n "your_db_password" | \
  gcloud secrets create db-password \
  --data-file=- \
  --replication-policy="automatic"

# Grant Cloud Run service account access
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

gcloud secrets add-iam-policy-binding meta-access-token \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### Step 5: Build and Push Docker Images

```bash
export IMAGE_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}"

# Build and push each service
echo "Building services..."

# 1. Titan Core
docker build -t ${IMAGE_PREFIX}/titan-core:latest ./services/titan-core
docker push ${IMAGE_PREFIX}/titan-core:latest

# 2. Drive Intel
DOCKER_BUILDKIT=0 docker build -t ${IMAGE_PREFIX}/drive-intel:latest ./services/drive-intel
docker push ${IMAGE_PREFIX}/drive-intel:latest

# 3. Video Agent
DOCKER_BUILDKIT=0 docker build -t ${IMAGE_PREFIX}/video-agent:latest ./services/video-agent
docker push ${IMAGE_PREFIX}/video-agent:latest

# 4. ML Service
DOCKER_BUILDKIT=0 docker build -t ${IMAGE_PREFIX}/ml-service:latest ./services/ml-service
docker push ${IMAGE_PREFIX}/ml-service:latest

# 5. Meta Publisher
docker build -t ${IMAGE_PREFIX}/meta-publisher:latest ./services/meta-publisher
docker push ${IMAGE_PREFIX}/meta-publisher:latest

# 6. Gateway API
docker build -t ${IMAGE_PREFIX}/gateway-api:latest ./services/gateway-api
docker push ${IMAGE_PREFIX}/gateway-api:latest

echo "All images pushed successfully!"
```

#### Step 6: Deploy Services to Cloud Run

**Deploy Backend Services** (in this order):

```bash
# 1. Deploy Titan Core (independent)
gcloud run deploy titan-core \
  --image=${IMAGE_PREFIX}/titan-core:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --timeout=600 \
  --set-env-vars="GEMINI_API_KEY=${GEMINI_API_KEY},META_APP_ID=${META_APP_ID},META_ACCESS_TOKEN=${META_ACCESS_TOKEN},META_AD_ACCOUNT_ID=${META_AD_ACCOUNT_ID},META_APP_SECRET=${META_APP_SECRET}" \
  --quiet

# 2. Deploy ML Service (independent)
gcloud run deploy ml-service \
  --image=${IMAGE_PREFIX}/ml-service:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=16Gi \
  --cpu=4 \
  --timeout=600 \
  --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
  --quiet

# 3. Deploy Drive Intel
gcloud run deploy drive-intel \
  --image=${IMAGE_PREFIX}/drive-intel:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --timeout=600 \
  --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
  --quiet

# 4. Deploy Video Agent
gcloud run deploy video-agent \
  --image=${IMAGE_PREFIX}/video-agent:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --timeout=600 \
  --set-env-vars="DATABASE_URL=${DATABASE_URL}" \
  --quiet

# 5. Deploy Meta Publisher (placeholder)
gcloud run deploy meta-publisher \
  --image=${IMAGE_PREFIX}/meta-publisher:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --timeout=600 \
  --set-env-vars="META_ACCESS_TOKEN=${META_ACCESS_TOKEN},META_AD_ACCOUNT_ID=${META_AD_ACCOUNT_ID},META_PAGE_ID=${META_PAGE_ID},META_APP_ID=${META_APP_ID},GATEWAY_URL=https://placeholder" \
  --quiet

# Get service URLs
TITAN_URL=$(gcloud run services describe titan-core --region=${REGION} --format='value(status.url)')
ML_URL=$(gcloud run services describe ml-service --region=${REGION} --format='value(status.url)')
DRIVE_URL=$(gcloud run services describe drive-intel --region=${REGION} --format='value(status.url)')
VIDEO_URL=$(gcloud run services describe video-agent --region=${REGION} --format='value(status.url)')
META_URL=$(gcloud run services describe meta-publisher --region=${REGION} --format='value(status.url)')

echo "Service URLs:"
echo "Titan Core: $TITAN_URL"
echo "ML Service: $ML_URL"
echo "Drive Intel: $DRIVE_URL"
echo "Video Agent: $VIDEO_URL"
echo "Meta Publisher: $META_URL"
```

**Deploy Gateway API** (with all service URLs):

```bash
# 6. Deploy Gateway API (central hub)
gcloud run deploy gateway-api \
  --image=${IMAGE_PREFIX}/gateway-api:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --timeout=600 \
  --set-env-vars="DRIVE_INTEL_URL=${DRIVE_URL},VIDEO_AGENT_URL=${VIDEO_URL},ML_SERVICE_URL=${ML_URL},META_PUBLISHER_URL=${META_URL},TITAN_CORE_URL=${TITAN_URL},DATABASE_URL=${DATABASE_URL}" \
  --quiet

# Get Gateway URL
GATEWAY_URL=$(gcloud run services describe gateway-api --region=${REGION} --format='value(status.url)')

echo "Gateway API: $GATEWAY_URL"
```

**Update Meta Publisher with Gateway URL**:

```bash
gcloud run services update meta-publisher \
  --region=${REGION} \
  --update-env-vars="GATEWAY_URL=${GATEWAY_URL}"
```

### 2.3 Frontend Deployment (Vercel)

#### Prerequisites

- Vercel account (free or Pro)
- Frontend code pushed to GitHub

#### Step 1: Link Frontend to Vercel

```bash
# Option A: Using Vercel CLI
npm i -g vercel
cd frontend
vercel

# Option B: Via Vercel Dashboard
# 1. Go to https://vercel.com
# 2. Click "New Project"
# 3. Select your GitHub repository
# 4. Click "Import"
```

#### Step 2: Configure Environment Variables in Vercel

In Vercel Dashboard → Project Settings → Environment Variables:

```
VITE_API_URL=https://YOUR_GATEWAY_URL
VITE_FIREBASE_API_KEY=your_firebase_key
VITE_FIREBASE_AUTH_DOMAIN=your_firebase_domain
VITE_FIREBASE_PROJECT_ID=your_firebase_project
VITE_FIREBASE_STORAGE_BUCKET=your_storage_bucket
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
VITE_FIREBASE_MEASUREMENT_ID=your_measurement_id
VITE_ENV=production
VITE_ENABLE_ANALYTICS=true
```

#### Step 3: Deploy Frontend

```bash
# Deploy from GitHub
# Vercel automatically deploys on push to main branch

# Or deploy manually
cd frontend
vercel --prod

# Get production URL from Vercel
# https://YOUR_PROJECT_NAME.vercel.app
```

#### Step 4: Configure Custom Domain (Optional)

1. In Vercel Dashboard → Domains
2. Click "Add"
3. Enter your domain (e.g., `geminivideo.com`)
4. Follow DNS configuration instructions

---

## 3. Environment Variables Reference

### Complete List with Descriptions

#### AI Model API Keys (Required)

```bash
# Gemini API
GEMINI_API_KEY=abc123...
GEMINI_MODEL_ID=gemini-2.0-flash-thinking-exp-1219

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI API
OPENAI_API_KEY=sk-...
```

#### Database Configuration

```bash
# PostgreSQL / Supabase
DATABASE_URL=postgresql://user:password@host:5432/database

# Redis (for caching and async queues)
REDIS_URL=redis://host:6379
```

#### Service URLs (Internal Communication)

```bash
# Main Gateway (entry point for frontend)
GATEWAY_API_URL=http://localhost:8000

# Microservices (internal only)
DRIVE_INTEL_URL=http://localhost:8001
VIDEO_AGENT_URL=http://localhost:8002
ML_SERVICE_URL=http://localhost:8003
META_PUBLISHER_URL=http://localhost:8083
TITAN_CORE_URL=http://localhost:8084
```

#### Meta Ads Integration

```bash
# Meta Marketing API (for publishing to Meta)
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=act_1234567890      # Format: act_XXXXXXXXXX
META_PAGE_ID=your_meta_page_id
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret
META_CLIENT_TOKEN=your_client_token
```

#### Firebase Configuration (Frontend)

```bash
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_AUTH_DOMAIN=project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=project-id
VITE_FIREBASE_STORAGE_BUCKET=project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abc123...
VITE_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
```

#### GCP Configuration

```bash
# Google Cloud Project
GCP_PROJECT_ID=your-gcp-project
GCP_SERVICE_ACCOUNT_JSON=/path/to/service-account.json

# Cloud Storage (for ML models, logs)
GCS_BUCKET_NAME=your-gcs-bucket
```

#### Application Configuration

```bash
# Environment mode
NODE_ENV=development|staging|production
VITE_ENV=development|staging|production

# Port Configuration
PORT=8000                    # Gateway API
GATEWAY_PORT=8000
DRIVE_INTEL_PORT=8001
VIDEO_AGENT_PORT=8002
ML_SERVICE_PORT=8003
META_PUBLISHER_PORT=8083

# Logging
DEBUG=false
LOG_LEVEL=info|debug|warn|error

# Storage Paths
TEMP_STORAGE_PATH=/tmp/geminivideo
OUTPUT_STORAGE_PATH=/tmp/geminivideo/output
CONFIG_PATH=./shared/config
```

#### Feature Flags

```bash
ENABLE_ANALYTICS=true|false
ENABLE_PERFORMANCE_MONITORING=true|false
ENABLE_THOMPSON_SAMPLING=true|false
ENABLE_MCP_INTEGRATION=false
```

#### ML Configuration

```bash
# Model Training
MIN_SAMPLES_FOR_UPDATE=50
LEARNING_RATE=0.01
MAX_WEIGHT_DELTA=0.1

# A/B Testing
MIN_CONVERSIONS_FOR_WINNER=30
```

#### Security

```bash
# JWT Authentication
JWT_SECRET=your_very_long_random_secret_key

# CORS Origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://example.com

# Video Processing
MAX_VIDEO_SIZE_MB=500
```

#### Supabase (if using instead of PostgreSQL)

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

---

## 4. Testing the System

### 4.1 Test Meta Learning Agent

The Meta Learning Agent analyzes performance data and automatically updates scoring weights.

#### Test Data Ingestion

```bash
# Send sample conversion data to the learning system
curl -X POST http://localhost:8000/api/internal/learning/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "predictions": [
      {
        "scene_id": "scene_001",
        "predicted_ctr_band": "high",
        "predicted_ctr_value": 0.85,
        "actual_ctr": 0.82,
        "metadata": {
          "timestamp": "2024-01-15T10:30:00Z",
          "campaign": "test_campaign"
        }
      }
    ]
  }'

# Expected Response:
# {
#   "status": "success",
#   "processed": 1,
#   "in_band": 1,
#   "out_of_band": 0
# }
```

#### Trigger Learning Update

```bash
# Trigger weight update (if enough samples available)
curl -X POST http://localhost:8000/api/internal/learning/update \
  -H "Content-Type: application/json" \
  -d '{
    "force": true
  }'

# Expected Response:
# {
#   "status": "success",
#   "message": "Learning update triggered",
#   "weights_updated": true,
#   "model_version": "2024-01-15-v3"
# }
```

#### Check Learning Status

```bash
# Get current learning metrics
curl http://localhost:8000/api/internal/learning/status

# Expected Response:
# {
#   "total_predictions": 1523,
#   "in_band_predictions": 1421,
#   "out_of_band_predictions": 102,
#   "accuracy_percentage": 93.3,
#   "last_update": "2024-01-15T10:00:00Z",
#   "next_update_eligible": "2024-01-15T12:00:00Z"
# }
```

### 4.2 Test Google Drive Bulk Analyzer

The Drive Intel service analyzes videos from Google Drive or local folders.

#### Ingest Local Folder

```bash
# Ingest videos from local folder
curl -X POST http://localhost:8000/api/ingest/local/folder \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/home/user/videos",
    "recursive": true,
    "video_extensions": [".mp4", ".mov", ".mkv"]
  }'

# Expected Response:
# {
#   "status": "success",
#   "asset_id": "asset_12345",
#   "ingestion_job_id": "job_67890",
#   "videos_found": 5,
#   "estimated_processing_time_minutes": 12
# }
```

#### Get Ingestion Status

```bash
# Check ingestion progress
curl http://localhost:8000/api/ingestion/job_67890/status

# Expected Response:
# {
#   "job_id": "job_67890",
#   "status": "processing",
#   "progress_percentage": 40,
#   "videos_processed": 2,
#   "videos_total": 5,
#   "elapsed_time_seconds": 180,
#   "estimated_remaining_seconds": 270
# }
```

#### Get Ranked Clips

```bash
# Get clips ranked by composite score
curl "http://localhost:8000/api/assets/asset_12345/clips?ranked=true&top=10"

# Expected Response:
# {
#   "asset_id": "asset_12345",
#   "clips": [
#     {
#       "clip_id": "clip_001",
#       "start_time": 12.5,
#       "duration": 5.2,
#       "composite_score": 0.87,
#       "psychology_score": 0.91,
#       "hook_strength": 0.85,
#       "technical_score": 0.80,
#       "demographic_match": 0.75,
#       "novelty_score": 0.88,
#       "thumbnail_url": "..."
#     }
#   ],
#   "total_clips": 47
# }
```

#### Semantic Search

```bash
# Search for clips by natural language description
curl -X POST http://localhost:8000/api/search/clips \
  -H "Content-Type: application/json" \
  -d '{
    "query": "person doing squats with good form",
    "asset_id": "asset_12345",
    "top_k": 5,
    "filter": {
      "min_duration": 3.0,
      "max_duration": 30.0
    }
  }'

# Expected Response:
# {
#   "query": "person doing squats with good form",
#   "results": [
#     {
#       "clip_id": "clip_042",
#       "relevance_score": 0.92,
#       "start_time": 45.3,
#       "duration": 8.1
#     }
#   ]
# }
```

### 4.3 Test Conversion Tracking

#### Log Prediction

```bash
# Log a prediction for later tracking
curl -X POST http://localhost:8000/api/predictions/log \
  -H "Content-Type: application/json" \
  -d '{
    "scene_id": "scene_001",
    "predicted_ctr_band": "high",
    "predicted_ctr_value": 0.87,
    "campaign_id": "camp_123",
    "variant": "reels",
    "timestamp": "2024-01-15T10:30:00Z"
  }'

# Expected Response:
# {
#   "status": "success",
#   "prediction_id": "pred_999",
#   "logged_at": "2024-01-15T10:30:00Z"
# }
```

#### Ingest Meta Performance Data

```bash
# Update prediction with actual Meta performance
curl -X POST http://localhost:8000/api/predictions/ingest-meta \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "camp_123",
    "insights": [
      {
        "metric": "ctr",
        "value": 0.85,
        "impressions": 10000,
        "clicks": 850
      },
      {
        "metric": "cpc",
        "value": 0.45
      }
    ]
  }'

# Expected Response:
# {
#   "status": "success",
#   "updated_predictions": 3,
#   "accuracy": 0.933
# }
```

#### Get Reliability Metrics

```bash
# Get prediction accuracy and reliability metrics
curl http://localhost:8000/api/internal/reliability/metrics

# Expected Response:
# {
#   "total_tracked": 523,
#   "in_band": 487,
#   "out_of_band": 36,
#   "accuracy_percentage": 93.1,
#   "confidence_level": "high",
#   "by_band": {
#     "high": { "total": 150, "accuracy": 0.96 },
#     "medium": { "total": 250, "accuracy": 0.92 },
#     "low": { "total": 123, "accuracy": 0.87 }
#   }
# }
```

### 4.4 Test Human Workflow API

#### Create Render Job

```bash
# Create video remix job
curl -X POST http://localhost:8000/api/render/remix \
  -H "Content-Type: application/json" \
  -d '{
    "asset_id": "asset_12345",
    "clips": [
      {
        "clip_id": "clip_001",
        "start_time": 12.5,
        "duration": 5.2,
        "text_overlay": "GET STRONGER",
        "text_position": "top"
      },
      {
        "clip_id": "clip_042",
        "start_time": 45.3,
        "duration": 8.1,
        "text_overlay": "PROVEN FORM",
        "text_position": "bottom"
      }
    ],
    "variant": "reels",
    "transition_style": "quick_cut",
    "output_quality": "1080p"
  }'

# Expected Response:
# {
#   "status": "success",
#   "render_job_id": "render_789",
#   "status_url": "http://localhost:8000/api/render/render_789/status",
#   "estimated_processing_time_seconds": 45
# }
```

#### Check Render Job Status

```bash
# Get render job progress
curl http://localhost:8000/api/render/render_789/status

# Expected Response:
# {
#   "job_id": "render_789",
#   "status": "rendering",
#   "progress_percentage": 60,
#   "current_step": "applying_overlays",
#   "compliance_checks": {
#     "text_length": "pass",
#     "color_contrast": "pass",
#     "audio_levels": "pass"
#   },
#   "output_video_url": null,
#   "estimated_remaining_seconds": 30
# }
```

#### Get Render Output

```bash
# Once complete, retrieve the rendered video
curl http://localhost:8000/api/render/render_789/output

# Expected Response (HTTP 200 with video file) or:
# {
#   "status": "success",
#   "video_url": "gs://bucket/output/render_789/video.mp4",
#   "metadata": {
#     "duration": 30.5,
#     "resolution": "1080x1920",
#     "file_size_mb": 125.4,
#     "created_at": "2024-01-15T10:35:00Z"
#   }
# }
```

#### Publish to Meta

```bash
# Publish rendered video directly to Meta
curl -X POST http://localhost:8000/api/publish/meta \
  -H "Content-Type: application/json" \
  -d '{
    "render_job_id": "render_789",
    "campaign_id": "camp_123",
    "account_id": "act_1234567890",
    "caption": "Build stronger glutes in 30 days! #FitnessGoals",
    "hashtags": ["fitness", "strength", "training"],
    "target_format": "reel"
  }'

# Expected Response:
# {
#   "status": "success",
#   "published_id": "pub_555",
#   "platform": "meta",
#   "post_url": "https://instagram.com/p/abc123...",
#   "published_at": "2024-01-15T10:40:00Z"
# }
```

#### Get Diversification Metrics

```bash
# Check content variety across campaigns
curl http://localhost:8000/api/analytics/diversification

# Expected Response:
# {
#   "total_clips_published": 45,
#   "unique_scenes": 32,
#   "variety_score": 0.78,
#   "by_category": {
#     "movement_types": 8,
#     "body_parts": 5,
#     "equipment": 12,
#     "environments": 4
#   },
#   "recommendations": [
#     "Increase variety in equipment usage (currently 40% dumbbells)",
#     "Consider outdoor environment clips (only 15% of content)"
#   ]
# }
```

---

## 6. Monitoring and Scaling

### 6.1. Production Monitoring

#### Cloud Run Monitoring

```bash
# View service metrics
gcloud monitoring dashboards list
gcloud run services describe gateway-api --region=$REGION

# Create custom dashboard
gcloud monitoring dashboards create --config-from-file=monitoring-dashboard.json
```

#### Key Metrics to Monitor

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Request latency (p95) | < 500ms | > 1000ms |
| Error rate | < 1% | > 5% |
| CPU utilization | < 70% | > 85% |
| Memory utilization | < 80% | > 90% |
| Instance count | 1-10 | > 15 |
| Database connections | < 80 | > 90 |

#### Set Up Alerting

```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s

# Create alert for high latency
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Latency" \
  --condition-display-name="P95 latency > 1000ms" \
  --condition-threshold-value=1000 \
  --condition-threshold-duration=300s
```

#### Log Aggregation

```bash
# View logs from all services
gcloud logging read "resource.type=cloud_run_revision" --limit=100 --format=json

# Filter by severity
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50

# Export logs to BigQuery for analysis
gcloud logging sinks create bigquery-sink \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/logs_dataset \
  --log-filter='resource.type="cloud_run_revision"'

# Export logs to Cloud Storage for archival
gcloud logging sinks create gcs-sink \
  storage.googleapis.com/BUCKET_NAME \
  --log-filter='resource.type="cloud_run_revision"'
```

#### Application Performance Monitoring (APM)

For detailed performance monitoring, integrate with APM tools:

**Option 1: Google Cloud Trace**
```javascript
// In your Node.js services
const tracing = require('@google-cloud/trace-agent');
tracing.start({
  projectId: process.env.GCP_PROJECT_ID,
  keyFilename: process.env.GCP_SERVICE_ACCOUNT_JSON
});
```

**Option 2: Sentry**
```javascript
const Sentry = require('@sentry/node');
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1
});
```

**Option 3: New Relic**
```bash
# Add New Relic to package.json
npm install newrelic

# Add to start of your app
require('newrelic');
```

### 6.2. Scaling Guidelines

#### Horizontal Scaling (Cloud Run)

Cloud Run automatically scales based on load, but you can configure limits:

```bash
# Update scaling configuration
gcloud run services update gateway-api \
  --region=$REGION \
  --min-instances=2 \
  --max-instances=20 \
  --concurrency=100

# Scale based on CPU
gcloud run services update gateway-api \
  --region=$REGION \
  --cpu-throttling \
  --no-cpu-boost

# Scale ML Service for high compute
gcloud run services update ml-service \
  --region=$REGION \
  --min-instances=2 \
  --max-instances=5 \
  --memory=32Gi \
  --cpu=8
```

#### Scaling Recommendations by Service

| Service | Min Instances | Max Instances | Memory | CPU | Notes |
|---------|--------------|---------------|---------|-----|-------|
| Gateway API | 1-2 | 10-20 | 2Gi | 2 | High availability |
| Drive Intel | 1 | 10 | 4-8Gi | 4 | CPU intensive |
| Video Agent | 1 | 5 | 4-8Gi | 2-4 | Memory intensive |
| ML Service | 1 | 5 | 16-32Gi | 4-8 | High compute |
| Meta Publisher | 1 | 5 | 1Gi | 1 | Low resource |
| Titan Core | 0 | 3 | 2Gi | 1 | On-demand |
| Frontend | 1 | 10 | 512Mi | 1 | Static content |

#### Docker Compose Scaling

```bash
# Scale worker services
docker-compose -f docker-compose.production.yml up -d \
  --scale drive-worker=4 \
  --scale video-worker=2

# Monitor resource usage
docker stats

# Scale down during off-hours (using cron)
0 22 * * * cd /path/to/geminivideo && docker-compose -f docker-compose.production.yml up -d --scale drive-worker=1 --scale video-worker=1
0 6 * * * cd /path/to/geminivideo && docker-compose -f docker-compose.production.yml up -d --scale drive-worker=4 --scale video-worker=2
```

#### Database Scaling

**Cloud SQL**
```bash
# Increase instance size
gcloud sql instances patch geminivideo-db \
  --tier=db-n1-standard-2

# Enable high availability
gcloud sql instances patch geminivideo-db \
  --availability-type=REGIONAL

# Add read replicas
gcloud sql instances create geminivideo-replica \
  --master-instance-name=geminivideo-db \
  --region=$REGION
```

**PostgreSQL (Docker)**
```bash
# Enable connection pooling with PgBouncer
docker run -d \
  --name pgbouncer \
  --network geminivideo-network \
  -e DATABASES_HOST=postgres \
  -e DATABASES_PORT=5432 \
  -e DATABASES_USER=geminivideo \
  -e DATABASES_PASSWORD=$POSTGRES_PASSWORD \
  -e DATABASES_DBNAME=geminivideo \
  -e POOL_MODE=transaction \
  -e MAX_CLIENT_CONN=1000 \
  -e DEFAULT_POOL_SIZE=20 \
  -p 6432:6432 \
  edoburu/pgbouncer

# Update connection string to use PgBouncer
DATABASE_URL=postgresql://geminivideo:password@pgbouncer:6432/geminivideo
```

#### Redis Scaling

```bash
# For high throughput, use Redis Cluster
docker run -d \
  --name redis-cluster \
  --network geminivideo-network \
  -p 7000-7005:7000-7005 \
  redis:7-alpine redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
  --cluster-replicas 1

# Or use managed Redis (Memorystore on GCP)
gcloud redis instances create geminivideo-redis \
  --size=5 \
  --region=$REGION \
  --redis-version=redis_7_0
```

### 6.3. Cost Optimization

#### Cloud Run Cost Optimization

```bash
# Set CPU throttling (save costs when idle)
gcloud run services update gateway-api \
  --region=$REGION \
  --cpu-throttling

# Set min instances to 0 for low-traffic services
gcloud run services update titan-core \
  --region=$REGION \
  --min-instances=0

# Use execution environment gen2 for better performance
gcloud run services update gateway-api \
  --region=$REGION \
  --execution-environment=gen2
```

#### Cost Monitoring

```bash
# View estimated costs
gcloud billing projects describe $PROJECT_ID

# Set budget alerts
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Monthly Budget Alert" \
  --budget-amount=500 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100

# Analyze costs by service
gcloud billing export describe
```

#### Best Practices for Cost Savings

1. **Use appropriate instance sizes** - Don't over-provision
2. **Enable autoscaling** - Scale to zero when not in use
3. **Optimize images** - Smaller images = faster cold starts
4. **Use caching** - Reduce redundant API calls
5. **Batch processing** - Process multiple items together
6. **Schedule non-critical jobs** - Run during off-peak hours
7. **Monitor and alert** - Track spending in real-time

### 6.4. Performance Optimization

#### Frontend Optimization

```bash
# Enable CDN for static assets
gcloud compute backend-services update frontend-backend \
  --enable-cdn \
  --cache-mode=CACHE_ALL_STATIC

# Configure cache headers in nginx
location / {
  expires 1y;
  add_header Cache-Control "public, immutable";
}
```

#### API Response Caching

```javascript
// In Gateway API - cache expensive operations
const redis = require('redis');
const client = redis.createClient(process.env.REDIS_URL);

app.get('/api/clips/:id', async (req, res) => {
  const cacheKey = `clips:${req.params.id}`;

  // Try cache first
  const cached = await client.get(cacheKey);
  if (cached) {
    return res.json(JSON.parse(cached));
  }

  // Fetch from database
  const data = await fetchClips(req.params.id);

  // Cache for 5 minutes
  await client.setEx(cacheKey, 300, JSON.stringify(data));

  res.json(data);
});
```

#### Database Query Optimization

```sql
-- Add indexes for frequent queries
CREATE INDEX idx_clips_composite_score ON clips(asset_id, composite_score DESC);
CREATE INDEX idx_predictions_campaign ON predictions(campaign_id, created_at DESC);
CREATE INDEX idx_assets_user_created ON assets(user_id, created_at DESC);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM clips WHERE asset_id = 'xyz' ORDER BY composite_score DESC LIMIT 10;

-- Update statistics
ANALYZE clips;
VACUUM ANALYZE;
```

#### Image Optimization

```dockerfile
# Multi-stage builds for smaller images
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
CMD ["node", "index.js"]
```

---

## 7. Troubleshooting

### Common Issues and Solutions

#### Import Errors (Python Services)

**Problem**: `ModuleNotFoundError: No module named 'torch'`

**Solution**:
```bash
# Ensure you're in the correct virtual environment
cd services/drive-intel
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt

# Verify installation
python -c "import torch; print(torch.__version__)"
```

**Problem**: `ImportError: cannot import name 'Vision' from google.cloud`

**Solution**:
```bash
# Update Google Cloud Vision library
pip install --upgrade google-cloud-vision==3.7.2

# Verify API is enabled in GCP
gcloud services enable vision.googleapis.com
```

#### Meta API Authentication

**Problem**: `Invalid OAuth token` or `Access token expired`

**Solution**:
```bash
# 1. Verify token is set
echo $META_ACCESS_TOKEN

# 2. Check token expiration
# Go to https://developers.facebook.com/tools/debug/accesstoken

# 3. Refresh token (if it's a long-lived token)
curl -X POST "https://graph.instagram.com/refresh_access_token" \
  -d "grant_type=fb_exchange_token" \
  -d "client_id=YOUR_APP_ID" \
  -d "client_secret=YOUR_APP_SECRET" \
  -d "fb_exchange_token=YOUR_TOKEN"

# 4. Update .env with new token
export META_ACCESS_TOKEN="new_token_here"
```

**Problem**: `No page access` or `Account not accessible`

**Solution**:
```bash
# Verify you have correct permissions
# 1. Check if token has ads_management scope
# 2. Verify ad account ID format: act_XXXXXXXXXX
# 3. Check page ownership: go to Meta Business Suite

# Test connection
curl -X GET "https://graph.instagram.com/me" \
  -d "access_token=YOUR_TOKEN"

# Should return your account information
```

#### Google Drive OAuth

**Problem**: `403: Forbidden - Insufficient Permission`

**Solution**:
```bash
# 1. Check if Google Drive API is enabled
gcloud services enable drive.googleapis.com

# 2. Ensure service account has access
# Share the folder with service account email:
# your-service-account@project.iam.gserviceaccount.com

# 3. Verify credentials file
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Test connection
python -c "from google.oauth2 import service_account; \
  creds = service_account.Credentials.from_service_account_file('/path/to/service-account.json'); \
  print('Credentials loaded successfully')"
```

**Problem**: `No shared drives accessible`

**Solution**:
```bash
# 1. Check if service account is member of shared drive
# Go to Google Drive Shared Drives → Settings → Members

# 2. Update code to use correct drive ID
# Example: https://drive.google.com/drive/folders/0AH... → 0AH...

# 3. Test with API
curl -X GET "https://www.googleapis.com/drive/v3/drives" \
  -H "Authorization: Bearer ACCESS_TOKEN"
```

#### Database Connection Issues

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# 1. Check if database is running
docker compose ps postgres

# If not running:
docker compose up -d postgres

# 2. Check connection string format
# Should be: postgresql://user:password@host:port/database

# 3. Test connection
psql postgresql://geminivideo:geminivideo@localhost:5432/geminivideo -c "SELECT 1;"

# 4. If using Supabase, verify:
# - Project is not paused
# - Password is correct
# - Region is accessible
```

**Problem**: `DatabaseError: relation "public.assets" does not exist`

**Solution**:
```bash
# 1. Check if tables exist
docker compose exec postgres psql -U geminivideo -d geminivideo -c "\dt"

# 2. Run migrations
# Create migration script in services/gateway-api/migrations/init.sql

docker compose exec postgres psql -U geminivideo -d geminivideo \
  -f /migrations/init.sql

# 3. Verify tables created
docker compose exec postgres psql -U geminivideo -d geminivideo -c "\dt"
```

**Problem**: `Connection pool exhausted`

**Solution**:
```bash
# In production, increase connection pool size
# Edit .env:
DATABASE_MAX_CONNECTIONS=20

# Restart services
docker compose down
docker compose up -d

# Monitor connections
docker compose exec postgres psql -U geminivideo -d geminivideo \
  -c "SELECT count(*) FROM pg_stat_activity;"
```

#### Service Connection Issues

**Problem**: `Failed to reach http://drive-intel:8001`

**Solution**:
```bash
# 1. Check if service is running
docker compose ps drive-intel

# If not running:
docker compose up -d drive-intel

# 2. Check logs for errors
docker compose logs drive-intel | head -50

# 3. Verify network connectivity
docker compose exec gateway-api curl http://drive-intel:8001/health

# 4. If using Cloud Run, verify URLs in environment variables
gcloud run services list --region=us-central1
```

**Problem**: `Network Unreachable` on Cloud Run

**Solution**:
```bash
# 1. Verify services are deployed
gcloud run services list

# 2. Check service URLs
DRIVE_URL=$(gcloud run services describe drive-intel \
  --region=us-central1 --format='value(status.url)')
echo $DRIVE_URL

# 3. Test connectivity from another service
gcloud run services update gateway-api \
  --update-env-vars="DRIVE_INTEL_URL=${DRIVE_URL}" \
  --region=us-central1

# 4. If still failing, use VPC Connector
# See GCP documentation for VPC setup
```

#### Memory and Performance Issues

**Problem**: `Out of memory` when processing large videos

**Solution**:
```bash
# 1. Increase container memory
# In docker-compose.yml or Cloud Run:
# memory=4Gi  # Increase from 2Gi

# 2. Implement streaming/chunked processing
# Edit services/video-agent/main.py:
# Process video in 30-second chunks instead of loading whole file

# 3. Monitor memory usage
docker stats geminivideo-drive-intel

# On Cloud Run:
gcloud run services describe drive-intel \
  --region=us-central1 \
  --format='value(spec.template.spec.containers[0].resources.limits.memory)'

# 4. Set memory limits in docker-compose.yml:
services:
  drive-intel:
    mem_limit: 4g
    memswap_limit: 4g
```

**Problem**: `Service timeout after 30 minutes`

**Solution**:
```bash
# 1. Increase timeout (max 60 minutes on Cloud Run)
gcloud run services update drive-intel \
  --timeout=1800 \
  --region=us-central1

# 2. Implement job queue for long tasks
# Use Redis + Celery or Cloud Tasks

# 3. Split large jobs
# Example: Process 1 video at a time instead of folder
```

#### Frontend Issues

**Problem**: `Cannot reach API from frontend on Vercel`

**Solution**:
```bash
# 1. Verify VITE_API_URL is set correctly
# In Vercel dashboard → Settings → Environment Variables
# Should be: https://your-gateway-url.run.app

# 2. Check CORS configuration on backend
# Edit services/gateway-api/src/index.ts:
const cors = require('cors');
app.use(cors({
  origin: ['https://your-frontend.vercel.app', 'http://localhost:3000'],
  credentials: true
}));

# 3. Rebuild and redeploy frontend
cd frontend
vercel --prod

# 4. Check browser console for specific error
# Open DevTools → Console tab
```

**Problem**: `Authentication fails from frontend`

**Solution**:
```bash
# 1. Check Firebase configuration
# In frontend/.env.local:
VITE_FIREBASE_API_KEY=your_key
VITE_FIREBASE_PROJECT_ID=your_project

# 2. Verify API key has correct restrictions
# Go to Firebase Console → Settings → API Keys
# Remove IP/HTTP restrictions for development

# 3. Check CORS headers from gateway
curl -I http://localhost:8000 \
  -H "Origin: http://localhost:3000"

# Should include:
# Access-Control-Allow-Origin: http://localhost:3000
```

---

## 8. Architecture Diagram

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   GEMINI VIDEO - PRODUCTION ARCHITECTURE            │
└─────────────────────────────────────────────────────────────────────┘

                         ┌──────────────────┐
                         │   End User       │
                         │   (Browser)      │
                         └────────┬─────────┘
                                  │ HTTPS
                                  ▼
          ┌───────────────────────────────────────────┐
          │           VERCEL (Frontend)               │
          │  ┌─────────────────────────────────────┐  │
          │  │  React/Vite Single Page App         │  │
          │  │  - Video Upload                     │  │
          │  │  - Scoring Dashboard                │  │
          │  │  - Analytics Dashboards             │  │
          │  │  - Content Management               │  │
          │  └─────────────────────────────────────┘  │
          │              vercel.app                    │
          └────────────────┬──────────────────────────┘
                           │ HTTPS
                           ▼
┌───────────────────────────────────────────────────────────────────┐
│           GCP CLOUD RUN (Microservices Architecture)              │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │            GATEWAY API (Node/Express) - Port 8080           │ │
│  │  ┌───────────────────────────────────────────────────────┐  │ │
│  │  │ - Request routing & authentication                    │  │ │
│  │  │ - Scoring engine (psychology + quality)              │  │ │
│  │  │ - Prediction logging                                 │  │ │
│  │  │ - Learning loop orchestration                        │  │ │
│  │  │ - Analytics aggregation                              │  │ │
│  │  └───────────────────────────────────────────────────────┘  │ │
│  │              gateway-api.run.app                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                         │                                         │
│          ┌──────────────┼──────────────┐                          │
│          ▼              ▼              ▼                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ DRIVE INTEL  │ │ VIDEO AGENT  │ │  ML SERVICE  │             │
│  │(Python/FastAPI)│(Python/FastAPI)│(Python/FastAPI)│           │
│  │ Port 8001     │ Port 8002     │ Port 8003     │             │
│  │              │              │              │             │
│  │ - Scene      │ - Video      │ - XGBoost    │             │
│  │   detection  │   rendering  │   model      │             │
│  │ - Feature    │ - Overlays   │ - Weight     │             │
│  │   extraction │ - Compliance │   updates    │             │
│  │ - Semantic   │   checks     │ - Prediction │             │
│  │   search     │ - Quality    │   refinement │             │
│  │              │   encoding   │              │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │    META PUBLISHER (Node/Express) - Port 8083             │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ - Meta Marketing API integration                  │  │   │
│  │  │ - Campaign creation & management                 │  │   │
│  │  │ - Direct publishing to Instagram/Facebook        │  │   │
│  │  │ - Performance insights ingestion                 │  │   │
│  │  │ - A/B testing variant management                 │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │              meta-publisher.run.app                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │     TITAN CORE (Python) - Port 8084 (Optional)           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │ - Gemini API orchestration                        │  │   │
│  │  │ - Advanced reasoning & planning                  │  │   │
│  │  │ - Content strategy optimization                 │  │   │
│  │  │ - Multi-model coordination                       │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │              titan-core.run.app                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                           │
                ┌──────────┴──────────┐
                ▼                     ▼
    ┌──────────────────────┐ ┌──────────────────────┐
    │  SUPABASE (Database) │ │   EXTERNAL APIs      │
    │  ┌────────────────┐  │ ├──────────────────────┤
    │  │ PostgreSQL     │  │ │ - Meta Marketing API │
    │  │ - Assets       │  │ │ - Google Drive API   │
    │  │ - Clips        │  │ │ - Vision API         │
    │  │ - Predictions  │  │ │ - Gemini API         │
    │  │ - Performance  │  │ │ - Anthropic API      │
    │  │ - Scores       │  │ │ - OpenAI API         │
    │  └────────────────┘  │ └──────────────────────┘
    │  https://project.     │
    │  supabase.co          │
    └──────────────────────┘


DATA FLOW
═════════════════════════════════════════════════════════════════════

1. VIDEO INGESTION
   Frontend → Gateway → Drive Intel → Database
   - User uploads video or specifies folder
   - Drive Intel extracts scenes and features
   - Results stored in Supabase

2. CONTENT ANALYSIS
   Drive Intel + ML Service → Gateway → Frontend
   - Scene detection and ranking
   - Scoring engine evaluation
   - Prediction logging

3. VIDEO CREATION
   Frontend → Gateway → Video Agent → Output
   - User selects clips and creates remix
   - Video Agent renders with overlays
   - Compliance checks applied

4. META PUBLISHING
   Frontend → Gateway → Meta Publisher → Meta APIs
   - Video published to Instagram/Facebook
   - Campaign configuration
   - Performance tracking setup

5. LEARNING LOOP
   Meta APIs → Meta Publisher → Gateway → ML Service → Database
   - Performance data ingested
   - Accuracy metrics calculated
   - Weights updated (if >50 samples)


DEPLOYMENT LEVELS
═════════════════════════════════════════════════════════════════════

LOCAL (Development)
├─ Docker Compose
├─ PostgreSQL + Redis (local)
├─ All 6 services on localhost
└─ Frontend on http://localhost:3000

STAGING (Pre-production)
├─ Cloud Run (1-2 instances per service)
├─ Supabase (shared staging database)
├─ Reduced autoscaling limits
└─ Staging domain (staging.example.com)

PRODUCTION (Live)
├─ Cloud Run (3+ instances per service)
├─ Supabase (dedicated production database with backups)
├─ Load balancing & autoscaling
├─ CDN for frontend (Vercel)
├─ Custom domain (example.com)
├─ SSL/TLS certificates
├─ Monitoring & alerts
└─ Automated backups & disaster recovery
```

### Service Dependencies

```
DEPENDENCY GRAPH
════════════════════════════════════════════════════════════════════

Frontend
  └─> Gateway API
      ├─> Drive Intel
      │   └─> Database (Supabase)
      ├─> Video Agent
      │   └─> Database (Supabase)
      ├─> ML Service
      │   └─> Database (Supabase)
      ├─> Meta Publisher
      │   ├─> Database (Supabase)
      │   └─> Meta Marketing APIs
      └─> Titan Core (optional)
          └─> Gemini API


INTERACTION MATRIX
════════════════════════════════════════════════════════════════════

                  Gateway  Drive   Video   ML      Meta    Titan
                          Intel   Agent   Svc     Pub     Core
────────────────────────────────────────────────────────────────────
Gateway (→)        -       ✓✓     ✓✓      ✓✓      ✓✓      ✓
Drive Intel        ✓       -      ✓       ✓       ✗       ✗
Video Agent        ✓       ✓      -       ✓       ✓       ✗
ML Service         ✓       ✓      ✓       -       ✓       ✗
Meta Publisher     ✓       ✗      ✓       ✓       -       ✗
Titan Core         ✓       ✓      ✓       ✓       ✓       -

Legend:
✓✓  = Real-time synchronous communication
✓   = Asynchronous or conditional
✗   = No direct communication


RESOURCE REQUIREMENTS
════════════════════════════════════════════════════════════════════

Service              Memory   CPU    Storage   Notes
─────────────────────────────────────────────────────────────────────
Gateway API          1-2 Gi   1-2   500 MB    Request routing only
Drive Intel          4 Gi     2     2 GB      Vision & ML models
Video Agent          4 Gi     2     5 GB      Video encoding
ML Service          16 Gi     4     2 GB      Large ML models
Meta Publisher       1 Gi     1     500 MB    API client only
Titan Core           2 Gi     1     1 GB      Reasoning models
────────────────────────────────────────────────────────────────────
TOTAL (Production)  28-30 Gi  11-12         ~11 GB

Supabase             -        -     100 GB+   Managed by Supabase
Redis                512 MB   1     1 GB      (if using separate cache)
```

### Scaling Strategy

```
HORIZONTAL SCALING
════════════════════════════════════════════════════════════════════

Service              Min Instances  Max Instances  Scale Metric
─────────────────────────────────────────────────────────────────────
Gateway API          1-2           10             CPU > 70%
Drive Intel          1             5              CPU > 75%
Video Agent          1             5              Memory > 80%
ML Service           1             3              CPU > 60%
Meta Publisher       1             3              Requests/sec
Titan Core           0             2              On-demand

Cloud Run automatically scales based on:
- Incoming request rate
- CPU utilization
- Custom metrics (if configured)

CACHING STRATEGY
════════════════════════════════════════════════════════════════════

Layer                Content                 TTL
─────────────────────────────────────────────────────────────────────
CDN (Vercel)        Frontend assets         24 hours
                    API responses           5 minutes

Redis (Cache)       Scene rankings          30 minutes
                    Prediction results      24 hours
                    User sessions           7 days

Database            All persistent data     N/A
(Supabase)          with backups
```

---

## Quick Reference

### Local Deployment Commands

```bash
# One-line startup (Docker Compose)
./deploy-local.sh

# View logs
docker compose logs -f [service_name]

# Restart specific service
docker compose restart gateway-api

# Stop all services
docker compose down

# Clean everything (including data)
docker compose down -v
```

### Cloud Deployment Commands

```bash
# Deploy all services to Cloud Run
export PROJECT_ID="your-project"
export REGION="us-central1"
gcloud config set project $PROJECT_ID

# Build and push images
DOCKER_BUILDKIT=0 docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/geminivideo/gateway-api ./services/gateway-api
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/geminivideo/gateway-api

# Deploy to Cloud Run
gcloud run deploy gateway-api \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/geminivideo/gateway-api \
  --region=${REGION} \
  --allow-unauthenticated

# View deployment logs
gcloud run services logs read gateway-api --region=${REGION}

# Get service URL
gcloud run services describe gateway-api --region=${REGION} --format='value(status.url)'
```

### Useful Links

- [Supabase Dashboard](https://app.supabase.com)
- [GCP Console](https://console.cloud.google.com)
- [Vercel Dashboard](https://vercel.com)
- [Meta Developer Platform](https://developers.facebook.com)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Tutorials](https://cloud.google.com/run/docs/quickstarts)

---

## Support & Troubleshooting

For additional help:

1. **Check logs first**
   ```bash
   docker compose logs [service]
   gcloud run services logs read [service] --region=[REGION]
   ```

2. **Test connectivity**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Review environment variables**
   ```bash
   docker compose config | grep environment
   ```

4. **Check GitHub Issues**: https://github.com/milosriki/geminivideo/issues

5. **Contact Support**: Open an issue with:
   - Error message (full logs)
   - Steps to reproduce
   - Environment (local/cloud, OS, versions)
   - Expected vs actual behavior

---

**Last Updated**: December 2024
**Version**: 1.0.0
**Maintainers**: Gemini Video Team
