#!/bin/bash
# setup-infrastructure.sh - Setup GCP Infrastructure for Production
# Creates Cloud SQL, Memorystore, Storage, VPC Connector, etc.

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"geminivideo-prod"}
REGION=${GCP_REGION:-"us-central1"}

echo "🏗️  Setting up GeminiVideo Infrastructure"
echo "==========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "📋 Enabling required APIs..."
gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    redis.googleapis.com \
    storage-component.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    monitoring.googleapis.com \
    logging.googleapis.com \
    artifactregistry.googleapis.com \
    compute.googleapis.com \
    vpcaccess.googleapis.com \
    --project=$PROJECT_ID

# Create Artifact Registry
echo ""
echo "📦 Creating Artifact Registry..."
gcloud artifacts repositories create geminivideo-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="GeminiVideo Docker images" \
    --project=$PROJECT_ID 2>/dev/null || echo "Repository already exists"

# Create Cloud SQL instance
echo ""
echo "🗄️  Creating Cloud SQL instance..."
gcloud sql instances create geminivideo-db \
    --database-version=POSTGRES_15 \
    --tier=db-custom-4-16384 \
    --region=$REGION \
    --backup \
    --enable-bin-log \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=3 \
    --storage-type=SSD \
    --storage-size=100GB \
    --storage-auto-increase \
    --availability-type=REGIONAL \
    --network=default \
    --project=$PROJECT_ID 2>/dev/null || echo "Cloud SQL instance already exists"

# Create database
echo "Creating database..."
gcloud sql databases create geminivideo \
    --instance=geminivideo-db \
    --project=$PROJECT_ID 2>/dev/null || echo "Database already exists"

# Create user
echo "Creating database user..."
DB_PASSWORD=$(openssl rand -base64 32)
gcloud sql users create geminivideo \
    --instance=geminivideo-db \
    --password=$DB_PASSWORD \
    --project=$PROJECT_ID 2>/dev/null || echo "User already exists (password not changed)"

# Store password in Secret Manager
echo "Storing database password in Secret Manager..."
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=- --project=$PROJECT_ID 2>/dev/null || \
    echo -n "$DB_PASSWORD" | gcloud secrets versions add db-password --data-file=- --project=$PROJECT_ID

# Create Memorystore Redis
echo ""
echo "🔴 Creating Memorystore Redis..."
gcloud redis instances create geminivideo-redis \
    --size=5 \
    --region=$REGION \
    --network=default \
    --redis-version=REDIS_7_0 \
    --tier=STANDARD_HA \
    --project=$PROJECT_ID 2>/dev/null || echo "Redis instance already exists"

# Get Redis host
REDIS_HOST=$(gcloud redis instances describe geminivideo-redis --region=$REGION --format="value(host)" --project=$PROJECT_ID)
echo -n "$REDIS_HOST" | gcloud secrets create redis-host --data-file=- --project=$PROJECT_ID 2>/dev/null || \
    echo -n "$REDIS_HOST" | gcloud secrets versions add redis-host --data-file=- --project=$PROJECT_ID

# Create Cloud Storage buckets
echo ""
echo "📦 Creating Cloud Storage buckets..."
for bucket in geminivideo-models geminivideo-patterns geminivideo-assets geminivideo-videos geminivideo-knowledge; do
    gsutil mb -p $PROJECT_ID -l $REGION gs://$bucket 2>/dev/null || echo "Bucket $bucket already exists"
done

# Create service account
echo ""
echo "👤 Creating service account..."
gcloud iam service-accounts create geminivideo-sa \
    --display-name="GeminiVideo Service Account" \
    --project=$PROJECT_ID 2>/dev/null || echo "Service account already exists"

# Grant permissions
echo "Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:geminivideo-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client" \
    --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:geminivideo-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/redis.editor" \
    --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:geminivideo-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin" \
    --condition=None 2>/dev/null || true

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:geminivideo-sa@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None 2>/dev/null || true

# Create VPC connector
echo ""
echo "🔌 Creating VPC connector..."
gcloud compute networks vpc-access connectors create geminivideo-connector \
    --region=$REGION \
    --subnet=default \
    --subnet-project=$PROJECT_ID \
    --min-instances=2 \
    --max-instances=10 \
    --machine-type=e2-micro \
    --project=$PROJECT_ID 2>/dev/null || echo "VPC connector already exists"

echo ""
echo "✅ Infrastructure setup complete!"
echo ""
echo "📋 Summary:"
echo "  - Cloud SQL: geminivideo-db (PostgreSQL 15, HA)"
echo "  - Memorystore: geminivideo-redis (5GB, HA)"
echo "  - Storage: 5 buckets created"
echo "  - Service Account: geminivideo-sa"
echo "  - VPC Connector: geminivideo-connector"
echo ""
echo "📝 Next steps:"
echo "  1. Store API keys in Secret Manager:"
echo "     echo -n 'YOUR_KEY' | gcloud secrets create gemini-api-key --data-file=-"
echo "  2. Run ./deploy-production.sh to deploy services"
echo ""
