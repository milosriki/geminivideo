#!/bin/bash
set -e

# GeminVideo Infrastructure Setup Script
# This script sets up Cloud SQL and Redis for the GeminVideo application

PROJECT_ID="gen-lang-client-0427673522"
REGION="us-west1"
SQL_INSTANCE="geminivideo-db"
REDIS_INSTANCE="geminivideo-redis"

echo "========================================="
echo "GeminVideo Infrastructure Setup"
echo "========================================="
echo ""
echo "This script will create:"
echo "  1. Cloud SQL PostgreSQL instance"
echo "  2. Cloud Memorystore Redis instance"
echo ""
echo "Estimated time: 15-20 minutes"
echo "Estimated cost: ~$65/month"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

# Generate secure passwords
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo "Generated secure database password: ${DB_PASSWORD}"
echo "⚠️  Save this password securely!"

# Step 1: Create Cloud SQL instance
echo ""
echo "========================================="
echo "Step 1: Creating Cloud SQL instance..."
echo "========================================="
echo "This will take ~10 minutes..."

gcloud sql instances create ${SQL_INSTANCE} \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=${REGION} \
  --root-password="${DB_PASSWORD}" \
  --storage-type=SSD \
  --storage-size=10GB \
  --availability-type=zonal \
  --project=${PROJECT_ID} \
  --no-backup || echo "Instance may already exist"

# Create database
echo "Creating database..."
gcloud sql databases create geminivideo \
  --instance=${SQL_INSTANCE} \
  --project=${PROJECT_ID} || echo "Database may already exist"

# Create user
echo "Creating database user..."
gcloud sql users create geminivideo \
  --instance=${SQL_INSTANCE} \
  --password="${DB_PASSWORD}" \
  --project=${PROJECT_ID} || echo "User may already exist"

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe ${SQL_INSTANCE} \
  --project=${PROJECT_ID} \
  --format='value(connectionName)')

echo "✅ Cloud SQL instance created!"
echo "Connection name: ${CONNECTION_NAME}"

# Step 2: Create Redis instance
echo ""
echo "========================================="
echo "Step 2: Creating Redis instance..."
echo "========================================="
echo "This will take ~5 minutes..."

gcloud redis instances create ${REDIS_INSTANCE} \
  --size=1 \
  --region=${REGION} \
  --redis-version=redis_7_0 \
  --project=${PROJECT_ID} || echo "Redis may already exist"

# Get Redis details
REDIS_HOST=$(gcloud redis instances describe ${REDIS_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(host)')

REDIS_PORT=$(gcloud redis instances describe ${REDIS_INSTANCE} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(port)')

echo "✅ Redis instance created!"
echo "Redis host: ${REDIS_HOST}:${REDIS_PORT}"

# Step 3: Generate connection strings
echo ""
echo "========================================="
echo "Step 3: GitHub Secrets Configuration"
echo "========================================="
echo ""
echo "Add these secrets to GitHub:"
echo "https://github.com/milosriki/geminivideo/settings/secrets/actions"
echo ""
echo "SECRET NAME: DATABASE_URL"
echo "VALUE:"
echo "postgresql://geminivideo:${DB_PASSWORD}@/geminivideo?host=/cloudsql/${CONNECTION_NAME}"
echo ""
echo "SECRET NAME: REDIS_URL"
echo "VALUE:"
echo "redis://${REDIS_HOST}:${REDIS_PORT}"
echo ""
echo "========================================="
echo "✅ Infrastructure setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Add the secrets above to GitHub"
echo "2. Run: gh secret set DATABASE_URL --body='<value>'"
echo "3. Run: gh secret set REDIS_URL --body='<value>'"
echo "4. Re-run the deployment workflow"
echo ""
echo "Cost: ~$65/month for this infrastructure"
