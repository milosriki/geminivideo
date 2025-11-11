# Deployment Guide

Complete deployment guide for the AI Ad Intelligence & Creation Suite on Google Cloud Platform.

## Prerequisites

- Google Cloud Project: `gen-lang-client-0427673522`
- Region: `us-west1`
- gcloud CLI installed and authenticated
- Docker installed locally (for testing)

## 1. Initial GCP Setup

### Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  --project=gen-lang-client-0427673522
```

### Create Artifact Registry Repository

```bash
gcloud artifacts repositories create cloud-run-repo \
  --repository-format=docker \
  --location=us-west1 \
  --description="Docker repository for AI Ad Intelligence services" \
  --project=gen-lang-client-0427673522
```

### Create GCS Bucket

```bash
# Create bucket
gsutil mb -p gen-lang-client-0427673522 -c STANDARD -l us-west1 \
  gs://ai-studio-bucket-208288753973-us-west1

# Enable versioning
gsutil versioning set on gs://ai-studio-bucket-208288753973-us-west1

# Set lifecycle policy (optional - retain versions for 30 days)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "numNewerVersions": 3,
          "isLive": false
        }
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://ai-studio-bucket-208288753973-us-west1
```

## 2. Service Account Setup

### Create Service Account

```bash
# Create service account for Cloud Run services
gcloud iam service-accounts create ai-ad-suite-sa \
  --display-name="AI Ad Intelligence Suite Service Account" \
  --project=gen-lang-client-0427673522

# Get the service account email
SA_EMAIL="ai-ad-suite-sa@gen-lang-client-0427673522.iam.gserviceaccount.com"
```

### Grant IAM Roles

```bash
# Storage permissions (read/write to GCS bucket)
gcloud projects add-iam-policy-binding gen-lang-client-0427673522 \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

# Cloud Run permissions
gcloud projects add-iam-policy-binding gen-lang-client-0427673522 \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.invoker"

# Artifact Registry reader (for pulling images)
gcloud projects add-iam-policy-binding gen-lang-client-0427673522 \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.reader"

# Logging permissions
gcloud projects add-iam-policy-binding gen-lang-client-0427673522 \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/logging.logWriter"
```

### Create Service Account Key (for GitHub Actions)

```bash
# Create key
gcloud iam service-accounts keys create ~/gcp-sa-key.json \
  --iam-account=${SA_EMAIL} \
  --project=gen-lang-client-0427673522

# Display key (add to GitHub Secrets as GCP_SA_KEY)
cat ~/gcp-sa-key.json

# IMPORTANT: Delete local key after adding to GitHub
rm ~/gcp-sa-key.json
```

## 3. GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

1. **GCP_SA_KEY**: Service account JSON key (from previous step)

Navigate to: `Settings > Secrets and variables > Actions > New repository secret`

## 4. Manual Deployment (Without GitHub Actions)

### Build Docker Images

```bash
# Navigate to repository root
cd /path/to/geminivideo

# Authenticate Docker with Artifact Registry
gcloud auth configure-docker us-west1-docker.pkg.dev

# Build and push each service
PROJECT_ID="gen-lang-client-0427673522"
REGION="us-west1"
REPO="cloud-run-repo"

# Gateway API
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/gateway-api:latest \
  ./services/gateway-api
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/gateway-api:latest

# Drive Intel
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/drive-intel:latest \
  ./services/drive-intel
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/drive-intel:latest

# Video Agent
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/video-agent:latest \
  ./services/video-agent
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/video-agent:latest

# Meta Publisher
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/meta-publisher:latest \
  ./services/meta-publisher
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/meta-publisher:latest

# Frontend
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/frontend:latest \
  ./services/frontend
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/frontend:latest
```

### Deploy Services to Cloud Run

```bash
PROJECT_ID="gen-lang-client-0427673522"
REGION="us-west1"
REPO="cloud-run-repo"
BUCKET="ai-studio-bucket-208288753973-us-west1"

# Deploy Drive Intel (Internal)
gcloud run deploy drive-intel \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/drive-intel:latest \
  --region=${REGION} \
  --platform=managed \
  --ingress=internal \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION}" \
  --project=${PROJECT_ID}

# Deploy Video Agent (Internal)
gcloud run deploy video-agent \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/video-agent:latest \
  --region=${REGION} \
  --platform=managed \
  --ingress=internal \
  --allow-unauthenticated \
  --memory=4Gi \
  --cpu=2 \
  --timeout=600 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION}" \
  --project=${PROJECT_ID}

# Deploy Meta Publisher (Internal)
gcloud run deploy meta-publisher \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/meta-publisher:latest \
  --region=${REGION} \
  --platform=managed \
  --ingress=internal \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION}" \
  --project=${PROJECT_ID}

# Deploy Gateway API (Public)
gcloud run deploy gateway-api \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/gateway-api:latest \
  --region=${REGION} \
  --platform=managed \
  --ingress=all \
  --allow-unauthenticated \
  --memory=1Gi \
  --cpu=1 \
  --set-env-vars="PROJECT_ID=${PROJECT_ID},GCS_BUCKET=${BUCKET},GCP_REGION=${REGION}" \
  --project=${PROJECT_ID}

# Deploy Frontend (Public)
gcloud run deploy frontend \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/frontend:latest \
  --region=${REGION} \
  --platform=managed \
  --ingress=all \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --project=${PROJECT_ID}
```

### Sync Configuration to GCS

```bash
# Sync shared config
gsutil -m rsync -r -d ./shared/config gs://${BUCKET}/config/

# Sync knowledge base
gsutil -m rsync -r -d ./knowledge gs://${BUCKET}/knowledge/
```

## 5. Verify Deployment

### Get Service URLs

```bash
# Gateway API
gcloud run services describe gateway-api \
  --region=us-west1 \
  --format='value(status.url)' \
  --project=gen-lang-client-0427673522

# Frontend
gcloud run services describe frontend \
  --region=us-west1 \
  --format='value(status.url)' \
  --project=gen-lang-client-0427673522

# Internal services (requires VPC access or Cloud Run proxy)
gcloud run services describe drive-intel \
  --region=us-west1 \
  --format='value(status.url)' \
  --project=gen-lang-client-0427673522
```

### Test Health Endpoints

```bash
# Get Gateway URL
GATEWAY_URL=$(gcloud run services describe gateway-api --region=us-west1 --format='value(status.url)' --project=gen-lang-client-0427673522)

# Test health
curl ${GATEWAY_URL}/health
```

## 6. Continuous Deployment with GitHub Actions

Once GitHub Secrets are configured, the workflow automatically:

1. Triggers on push to `main` branch
2. Builds Docker images for all services
3. Pushes images to Artifact Registry
4. Deploys services to Cloud Run
5. Syncs configuration to GCS

Monitor deployment: `Actions` tab in GitHub repository

## 7. Nightly Learning Scripts

### Setup Cloud Scheduler for Nightly Learning

```bash
# Create Cloud Run job for nightly learning
gcloud run jobs create nightly-learning \
  --image=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/gateway-api:latest \
  --region=${REGION} \
  --command="python3,/app/scripts/nightly_learning.py" \
  --memory=1Gi \
  --cpu=1 \
  --project=${PROJECT_ID}

# Create Cloud Scheduler job (runs at 2 AM daily)
gcloud scheduler jobs create http nightly-learning-cron \
  --location=${REGION} \
  --schedule="0 2 * * *" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/nightly-learning:run" \
  --http-method=POST \
  --oauth-service-account-email=${SA_EMAIL} \
  --project=${PROJECT_ID}
```

## 8. Monitoring and Logging

### View Logs

```bash
# Gateway API logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gateway-api" \
  --limit=50 \
  --project=gen-lang-client-0427673522

# All services
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --project=gen-lang-client-0427673522
```

### Set Up Alerts (Optional)

```bash
# Create alert for high error rates
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate - Gateway API" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=300s
```

## 9. Teardown / Cleanup

```bash
PROJECT_ID="gen-lang-client-0427673522"
REGION="us-west1"

# Delete Cloud Run services
gcloud run services delete gateway-api --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete drive-intel --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete video-agent --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete meta-publisher --region=${REGION} --project=${PROJECT_ID} --quiet
gcloud run services delete frontend --region=${REGION} --project=${PROJECT_ID} --quiet

# Delete Artifact Registry repository
gcloud artifacts repositories delete cloud-run-repo \
  --location=${REGION} \
  --project=${PROJECT_ID} \
  --quiet

# Delete GCS bucket (CAUTION: This deletes all data)
# gsutil -m rm -r gs://ai-studio-bucket-208288753973-us-west1
```

## 10. Troubleshooting

### Service fails to start

```bash
# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=SERVICE_NAME" \
  --limit=100 \
  --project=gen-lang-client-0427673522

# Check service details
gcloud run services describe SERVICE_NAME --region=us-west1 --project=gen-lang-client-0427673522
```

### Permission errors

Verify service account has required roles:

```bash
gcloud projects get-iam-policy gen-lang-client-0427673522 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:ai-ad-suite-sa@gen-lang-client-0427673522.iam.gserviceaccount.com"
```

### Configuration not loading

Verify GCS sync:

```bash
gsutil ls -r gs://ai-studio-bucket-208288753973-us-west1/config/
gsutil ls -r gs://ai-studio-bucket-208288753973-us-west1/knowledge/
```

## Support

For issues or questions, refer to:
- Google Cloud Run Documentation: https://cloud.google.com/run/docs
- Project Issues: GitHub repository issues tab
