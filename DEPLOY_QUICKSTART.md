# Cloud Run Deployment - Quick Start

Fast-track guide to deploy Gemini Video to Google Cloud Run in 15 minutes.

## Prerequisites

```bash
# Install gcloud CLI (if not already installed)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## 1. Setup Environment (5 min)

```bash
# Clone/navigate to project
cd /path/to/geminivideo

# Create production environment file
cp .env.example .env.production

# Edit with your actual credentials
nano .env.production
```

**Required variables:**
- `GCP_PROJECT_ID` - Your Google Cloud project ID
- `GEMINI_API_KEY` - Get from https://aistudio.google.com/apikey
- `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com/
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `DATABASE_URL` - Supabase or Cloud SQL connection string
- `REDIS_URL` - Upstash or Memorystore connection string

## 2. Enable APIs (2 min)

```bash
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com
```

## 3. Create Service Account (2 min)

```bash
export PROJECT_ID=$(gcloud config get-value project)

# Create service account
gcloud iam service-accounts create geminivideo-cloud-run \
  --display-name="Gemini Video Cloud Run"

# Grant permissions
export SA="geminivideo-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA}" \
  --role="roles/secretmanager.secretAccessor"
```

## 4. Deploy with Script (5 min)

```bash
# Make script executable
chmod +x scripts/deploy-cloud-run.sh

# Deploy all services
./scripts/deploy-cloud-run.sh

# Or deploy specific service
./scripts/deploy-cloud-run.sh titan-core
```

The script will:
- ✅ Create Artifact Registry repository
- ✅ Store secrets in Secret Manager
- ✅ Build Docker images
- ✅ Push to Artifact Registry
- ✅ Deploy to Cloud Run
- ✅ Configure environment variables
- ✅ Test deployments

## 5. Verify Deployment (1 min)

```bash
# List services
gcloud run services list

# Get Gateway URL
gcloud run services describe geminivideo-gateway-api \
  --region=us-central1 \
  --format='value(status.url)'

# Test health endpoint
curl https://YOUR_GATEWAY_URL/health
```

## Database Options

### Option A: Supabase (Fastest - 5 min)

1. Go to https://supabase.com
2. Create new project
3. Copy connection details to `.env.production`:
   ```bash
   DATABASE_URL=postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres
   SUPABASE_URL=https://[project].supabase.co
   SUPABASE_ANON_KEY=your_anon_key
   ```

### Option B: Cloud SQL (More setup)

```bash
# Create instance
gcloud sql instances create geminivideo-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create geminivideo --instance=geminivideo-db

# Get connection name and set DATABASE_URL
```

## Redis Options

### Option A: Upstash (Fastest - 2 min)

1. Go to https://upstash.com
2. Create Redis database
3. Copy Redis URL to `.env.production`:
   ```bash
   REDIS_URL=rediss://default:[password]@[host].upstash.io:6379
   ```

### Option B: Memorystore (More setup)

```bash
gcloud redis instances create geminivideo-redis \
  --size=1 \
  --region=us-central1
```

## Service URLs

After deployment, services will be available at:

```
Gateway API:     https://geminivideo-gateway-api-xxx.run.app
Titan Core:      https://geminivideo-titan-core-xxx.run.app
Video Agent:     https://geminivideo-video-agent-xxx.run.app
ML Service:      https://geminivideo-ml-service-xxx.run.app
Drive Intel:     https://geminivideo-drive-intel-xxx.run.app
Meta Publisher:  https://geminivideo-meta-publisher-xxx.run.app
```

## Common Commands

```bash
# View logs
gcloud run services logs read geminivideo-gateway-api --region=us-central1

# Update service
./scripts/deploy-cloud-run.sh gateway-api

# Delete service
gcloud run services delete SERVICE_NAME --region=us-central1

# Set environment variable
gcloud run services update SERVICE_NAME \
  --set-env-vars="KEY=VALUE" \
  --region=us-central1
```

## Troubleshooting

### Build Failed
```bash
# Check Docker build locally
cd services/titan-core
docker build -t test .
```

### Deployment Failed
```bash
# Check service status
gcloud run services describe SERVICE_NAME --region=us-central1

# View logs
gcloud run services logs read SERVICE_NAME --region=us-central1 --limit=50
```

### Service Not Responding
```bash
# Check health endpoint
curl https://SERVICE_URL/health

# Increase memory/CPU
gcloud run services update SERVICE_NAME \
  --memory=4Gi \
  --cpu=2 \
  --region=us-central1
```

## Cost Estimate

With moderate usage (10K requests/day):
- **Cloud Run**: ~$100-250/month
- **Supabase**: Free tier (or ~$25/month Pro)
- **Upstash**: Free tier (or ~$10/month Pro)
- **Total**: ~$100-300/month

## Next Steps

1. **Custom Domain**: See [DEPLOY_CLOUD_RUN.md](./DEPLOY_CLOUD_RUN.md#custom-domain-setup)
2. **Monitoring**: Setup Cloud Monitoring alerts
3. **CI/CD**: Configure Cloud Build triggers
4. **Scaling**: Adjust min/max instances based on traffic

## Full Documentation

For detailed instructions, see [DEPLOY_CLOUD_RUN.md](./DEPLOY_CLOUD_RUN.md)

## Support

- Check logs: `gcloud run services logs read SERVICE_NAME`
- Review troubleshooting: [DEPLOY_CLOUD_RUN.md#troubleshooting](./DEPLOY_CLOUD_RUN.md#troubleshooting)
- Open GitHub issue for bugs

---

**Last Updated:** 2025-12-02
