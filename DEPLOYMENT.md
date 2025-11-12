# Deployment Guide

This guide covers deploying the Gemini Video AI Ad Intelligence Suite to Google Cloud Platform (GCP).

## Prerequisites

- GCP Project with billing enabled
- `gcloud` CLI installed and authenticated
- GitHub repository with code
- Docker installed locally for testing

## GCP Setup

### 1. Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

### 2. Create Artifact Registry

```bash
# Set variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export REGISTRY_NAME="geminivideo"

# Create registry
gcloud artifacts repositories create ${REGISTRY_NAME} \
  --repository-format=docker \
  --location=${REGION} \
  --description="Gemini Video container images"
```

### 3. Configure Docker Authentication

```bash
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

### 4. Create Secrets

```bash
# Meta API Access Token (optional)
echo -n "your_meta_access_token" | \
  gcloud secrets create meta-access-token \
  --data-file=- \
  --replication-policy="automatic"

# Grant Cloud Run service account access
gcloud secrets add-iam-policy-binding meta-access-token \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Build and Push Images

### Manual Build

```bash
# Set image registry prefix
export IMAGE_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REGISTRY_NAME}"

# Build and push drive-intel
docker build -t ${IMAGE_PREFIX}/drive-intel:latest ./services/drive-intel
docker push ${IMAGE_PREFIX}/drive-intel:latest

# Build and push video-agent
docker build -t ${IMAGE_PREFIX}/video-agent:latest ./services/video-agent
docker push ${IMAGE_PREFIX}/video-agent:latest

# Build and push gateway-api
docker build -t ${IMAGE_PREFIX}/gateway-api:latest ./services/gateway-api
docker push ${IMAGE_PREFIX}/gateway-api:latest

# Build and push meta-publisher
docker build -t ${IMAGE_PREFIX}/meta-publisher:latest ./services/meta-publisher
docker push ${IMAGE_PREFIX}/meta-publisher:latest

# Build and push frontend
docker build -t ${IMAGE_PREFIX}/frontend:latest ./frontend
docker push ${IMAGE_PREFIX}/frontend:latest
```

### GitHub Actions (Automated)

GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically builds and pushes images on push to main branch.

Required GitHub Secrets:
- `GCP_PROJECT_ID` - Your GCP project ID
- `GCP_SA_KEY` - Service account JSON key with Artifact Registry Writer permissions

## Deploy to Cloud Run

### Deploy Services

```bash
# Deploy drive-intel
gcloud run deploy drive-intel \
  --image=${IMAGE_PREFIX}/drive-intel:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --set-env-vars="CONFIG_PATH=/app/config"

# Deploy video-agent
gcloud run deploy video-agent \
  --image=${IMAGE_PREFIX}/video-agent:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --set-env-vars="CONFIG_PATH=/app/config"

# Deploy meta-publisher
gcloud run deploy meta-publisher \
  --image=${IMAGE_PREFIX}/meta-publisher:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --set-secrets="META_ACCESS_TOKEN=meta-access-token:latest"

# Get service URLs
export DRIVE_INTEL_URL=$(gcloud run services describe drive-intel --region=${REGION} --format='value(status.url)')
export VIDEO_AGENT_URL=$(gcloud run services describe video-agent --region=${REGION} --format='value(status.url)')
export META_PUBLISHER_URL=$(gcloud run services describe meta-publisher --region=${REGION} --format='value(status.url)')

# Deploy gateway-api
gcloud run deploy gateway-api \
  --image=${IMAGE_PREFIX}/gateway-api:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=1Gi \
  --set-env-vars="CONFIG_PATH=/app/config,DRIVE_INTEL_URL=${DRIVE_INTEL_URL},VIDEO_AGENT_URL=${VIDEO_AGENT_URL},META_PUBLISHER_URL=${META_PUBLISHER_URL}"

# Get gateway URL
export GATEWAY_URL=$(gcloud run services describe gateway-api --region=${REGION} --format='value(status.url)')

# Deploy frontend
gcloud run deploy frontend \
  --image=${IMAGE_PREFIX}/frontend:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --set-env-vars="VITE_API_URL=${GATEWAY_URL}"
```

### Deployment Script

Use the provided deployment script for easier deployment:

```bash
./scripts/deploy.sh
```

## Configuration Management

### Update Shared Config

The shared configuration files are baked into the Docker images. To update config:

1. Edit files in `shared/config/`
2. Rebuild and push images
3. Redeploy services

For production, consider using Cloud Storage or Config Management service to externalize configuration.

## Storage Options

### Data Persistence

Cloud Run is stateless. For persistent data:

**Option 1: Cloud Storage**
```bash
# Create bucket
gsutil mb -l ${REGION} gs://${PROJECT_ID}-geminivideo-data

# Grant service account access
gsutil iam ch serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com:roles/storage.objectAdmin \
  gs://${PROJECT_ID}-geminivideo-data

# Update services to use GCS
gcloud run services update drive-intel \
  --set-env-vars="DATA_DIR=gs://${PROJECT_ID}-geminivideo-data"
```

**Option 2: Cloud Filestore (NFS)**
For shared file access across services.

**Option 3: Cloud SQL / Firestore**
For structured data storage (future enhancement).

### Logs and Predictions

Store prediction logs in Cloud Storage:

```bash
# Create logs bucket
gsutil mb -l ${REGION} gs://${PROJECT_ID}-geminivideo-logs

# Update gateway-api
gcloud run services update gateway-api \
  --set-env-vars="LOG_DIR=/logs"

# Consider Cloud Logging for centralized log management
```

## Monitoring and Logging

### Cloud Monitoring

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gateway-api" \
  --limit 50 \
  --format json

# Create uptime checks
gcloud monitoring uptime create web-check \
  --display-name="Gateway API Health" \
  --resource-type=uptime-url \
  --http-check-path="/health"
```

### Metrics

Cloud Run automatically provides:
- Request count
- Request latency
- Container CPU/memory utilization
- Billable instance time

Access via GCP Console → Cloud Run → Service → Metrics

## Cost Optimization

- Use minimum instances = 0 for development
- Set maximum instances to control costs
- Use appropriate CPU/memory allocation
- Consider Cloud Run Jobs for batch processing
- Enable request-based autoscaling

## CI/CD Pipeline

The GitHub Actions workflow automates:
1. Linting and type checking
2. Running tests
3. Building Docker images
4. Pushing to Artifact Registry
5. (Optional) Deploying to Cloud Run

### Workflow Configuration

Edit `.github/workflows/deploy.yml` to customize:
- Deployment triggers (branches, tags)
- Build matrix
- Test suites
- Deployment targets (dev/staging/prod)

## Security Best Practices

1. **Use Secret Manager** for sensitive data
2. **Enable VPC Connector** for private service communication
3. **Implement IAM roles** with least privilege
4. **Enable Cloud Armor** for DDoS protection
5. **Use Cloud CDN** for frontend static assets
6. **Implement authentication** for production (Cloud IAP, Firebase Auth)

## Troubleshooting

### Container fails to start
```bash
gcloud run services logs read SERVICE_NAME --region=${REGION}
```

### Out of memory
Increase memory allocation:
```bash
gcloud run services update SERVICE_NAME --memory=4Gi
```

### Service timeout
Increase timeout (max 60 minutes):
```bash
gcloud run services update SERVICE_NAME --timeout=600
```

### Connection refused between services
Check service URLs are correct:
```bash
gcloud run services list --region=${REGION}
```

## Rollback

```bash
# List revisions
gcloud run revisions list --service=SERVICE_NAME --region=${REGION}

# Rollback to previous revision
gcloud run services update-traffic SERVICE_NAME \
  --to-revisions=REVISION_NAME=100 \
  --region=${REGION}
```

## Production Checklist

- [ ] Enable Cloud Armor
- [ ] Set up Cloud CDN for frontend
- [ ] Configure custom domain
- [ ] Enable SSL/TLS
- [ ] Set up monitoring alerts
- [ ] Configure log retention
- [ ] Implement backup strategy
- [ ] Set up staging environment
- [ ] Document runbook
- [ ] Configure autoscaling limits
- [ ] Enable VPC Service Controls
- [ ] Set up Cloud Trace for distributed tracing

## Support

For deployment issues, consult:
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- Project GitHub Issues
