# 🚀 Production Deployment Quick Start

## Prerequisites (5 minutes)

1. **Install gcloud CLI:**
   ```bash
   # macOS
   brew install --cask google-cloud-sdk

   # Linux
   curl https://sdk.cloud.google.com | bash
   ```

2. **Install Terraform:**
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

3. **Authenticate with GCP:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

## Option 1: Automated Deployment (15 minutes)

**Single command deployment:**

```bash
./scripts/deploy-terraform.sh
```

This script will:
- ✅ Check prerequisites
- ✅ Enable required GCP APIs
- ✅ Create Terraform state bucket
- ✅ Create Secret Manager secrets
- ✅ Deploy all infrastructure
- ✅ Output service URLs

## Option 2: Manual Deployment (20 minutes)

### Step 1: Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**Required values:**
- `project_id` - Your GCP project ID
- `database_password` - Strong password (min 32 chars)
- `github_owner` - Your GitHub username

### Step 2: Create State Bucket

```bash
export PROJECT_ID="your-project-id"
gsutil mb -p $PROJECT_ID -l us-central1 gs://${PROJECT_ID}-terraform-state
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### Step 3: Enable APIs

```bash
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  sqladmin.googleapis.com \
  redis.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  servicenetworking.googleapis.com \
  vpcaccess.googleapis.com
```

### Step 4: Create Secrets

```bash
# Generate and store JWT secret
openssl rand -base64 64 | \
  gcloud secrets create geminivideo-jwt-secret --data-file=-

# Store API keys (replace with actual values)
echo -n "YOUR_GEMINI_API_KEY" | \
  gcloud secrets create geminivideo-gemini-api-key --data-file=-

echo -n "YOUR_META_ACCESS_TOKEN" | \
  gcloud secrets create geminivideo-meta-access-token --data-file=-

echo -n "YOUR_META_APP_SECRET" | \
  gcloud secrets create geminivideo-meta-app-secret --data-file=-
```

### Step 5: Deploy Infrastructure

```bash
cd terraform

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy
terraform apply
```

Wait 10-15 minutes for infrastructure to provision.

### Step 6: Get Service URLs

```bash
terraform output
```

## Option 3: GitHub Actions CI/CD (30 minutes)

### Step 1: Create Service Account

```bash
export PROJECT_ID="your-project-id"

# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-sa-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com
```

### Step 2: Add GitHub Secrets

In your GitHub repository:

1. Go to **Settings > Secrets and variables > Actions**
2. Click **New repository secret**
3. Add these secrets:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_SA_KEY`: Contents of `github-sa-key.json`
   - `SLACK_WEBHOOK_URL`: (Optional) Slack webhook for notifications

### Step 3: Push to Main

```bash
git add .
git commit -m "Add Cloud Run deployment automation"
git push origin main
```

The deployment will automatically trigger!

## Post-Deployment

### Update Secret Values

Replace placeholder secrets with real values:

```bash
# Update Gemini API key
echo -n "YOUR_REAL_GEMINI_KEY" | \
  gcloud secrets versions add geminivideo-gemini-api-key --data-file=-

# Update Meta access token
echo -n "YOUR_REAL_META_TOKEN" | \
  gcloud secrets versions add geminivideo-meta-access-token --data-file=-

# Update database URL (after Cloud SQL is provisioned)
DB_HOST=$(gcloud sql instances describe geminivideo-postgres-production \
  --format='value(ipAddresses[0].ipAddress)')

echo -n "postgresql://geminivideo:YOUR_PASSWORD@${DB_HOST}:5432/geminivideo" | \
  gcloud secrets versions add geminivideo-database-url --data-file=-

# Update Redis URL (after Memorystore is provisioned)
REDIS_HOST=$(gcloud redis instances describe geminivideo-redis-production \
  --region=us-central1 --format='value(host)')

echo -n "redis://${REDIS_HOST}:6379" | \
  gcloud secrets versions add geminivideo-redis-url --data-file=-
```

### Build and Push Docker Images

```bash
# Authenticate Docker
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build all images
docker-compose -f docker-compose.production.yml build

# Tag images
export PROJECT_ID="your-project-id"
export REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/geminivideo"

for service in gateway-api drive-intel video-agent ml-service meta-publisher titan-core frontend; do
  docker tag geminivideo-${service}-prod:latest ${REGISTRY}/${service}:latest
  docker push ${REGISTRY}/${service}:latest
done
```

### Deploy Services

```bash
# Deploy all services (Cloud Build will do this automatically)
gcloud builds submit --config=cloudbuild.yaml
```

## Verify Deployment

### Test Service Health

```bash
# Get gateway URL
GATEWAY_URL=$(gcloud run services describe geminivideo-gateway-api \
  --region=us-central1 --format='value(status.url)')

# Test health endpoint
curl $GATEWAY_URL/health

# Expected response:
# {"status":"healthy","timestamp":"2025-12-02T12:00:00Z"}
```

### Test Frontend

```bash
# Get frontend URL
FRONTEND_URL=$(gcloud run services describe geminivideo-frontend \
  --region=us-central1 --format='value(status.url)')

# Open in browser
open $FRONTEND_URL
```

### Check Logs

```bash
# View gateway logs
gcloud run services logs read geminivideo-gateway-api --limit=50

# View all service logs
gcloud logging read "resource.type=cloud_run_revision" --limit=100
```

## Monitoring

### Cloud Console Dashboards

- **Cloud Run:** https://console.cloud.google.com/run
- **Cloud SQL:** https://console.cloud.google.com/sql
- **Logs:** https://console.cloud.google.com/logs
- **Metrics:** https://console.cloud.google.com/monitoring

### Set Up Alerts

```bash
# Create budget alert
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Gemini Video Monthly Budget" \
  --budget-amount=500USD

# Create log-based alert
gcloud logging metrics create error_rate \
  --description="Error rate metric" \
  --log-filter='severity>=ERROR'
```

## Cost Management

### View Current Costs

```bash
# Install billing CLI
gcloud components install alpha

# View costs
gcloud alpha billing accounts list
gcloud alpha billing projects describe $PROJECT_ID
```

### Reduce Costs

```bash
# Scale down non-critical services
for service in drive-intel video-agent ml-service; do
  gcloud run services update geminivideo-$service \
    --min-instances=0 \
    --region=us-central1
done

# Use smaller database tier for dev/staging
# Edit terraform.tfvars:
# db_tier = "db-custom-1-3840"  # 1 vCPU, 3.75 GB RAM
# Then: terraform apply
```

## Troubleshooting

### Issue: Service won't start

```bash
# Check logs
gcloud run services logs read SERVICE_NAME --limit=50

# Check service configuration
gcloud run services describe SERVICE_NAME --region=us-central1

# Redeploy
gcloud run services update SERVICE_NAME \
  --image=REGISTRY_URL/SERVICE_NAME:latest \
  --region=us-central1
```

### Issue: Database connection failed

```bash
# Verify Cloud SQL is running
gcloud sql instances list

# Check VPC connector
gcloud compute networks vpc-access connectors list --region=us-central1

# Test connection from Cloud Shell
gcloud sql connect geminivideo-postgres-production --user=geminivideo
```

### Issue: High costs

```bash
# Check instance counts
gcloud run services list --format='table(name,status.url,status.latestCreatedRevisionName,status.latestReadyRevisionName)'

# Scale down
gcloud run services update SERVICE_NAME \
  --min-instances=0 --max-instances=2
```

## Rollback

### Rollback specific service

```bash
# List revisions
gcloud run revisions list --service=SERVICE_NAME

# Route traffic to previous revision
gcloud run services update-traffic SERVICE_NAME \
  --to-revisions=REVISION_NAME=100
```

### Complete infrastructure rollback

```bash
cd terraform

# Restore previous state
terraform state pull > current-state.json
gsutil cp gs://PROJECT_ID-terraform-state/terraform/state/default.tfstate .
terraform state push default.tfstate

# Apply previous configuration
terraform apply
```

## Next Steps

1. **Configure custom domain** (optional)
2. **Set up monitoring alerts**
3. **Run load tests**
4. **Configure backup strategy**
5. **Security audit**
6. **Performance tuning**

## Support Resources

- **Terraform Docs:** See `/terraform/README.md`
- **Full Guide:** See `/AGENT_24_CLOUD_RUN_DEPLOYMENT.md`
- **GCP Documentation:** https://cloud.google.com/run/docs
- **GitHub Issues:** Open issue in repository

## Quick Commands Reference

```bash
# Deploy infrastructure
./scripts/deploy-terraform.sh

# View service URLs
terraform output

# Check service health
curl $(gcloud run services describe SERVICE_NAME --format='value(status.url)')/health

# View logs
gcloud run services logs read SERVICE_NAME --limit=50

# Scale service
gcloud run services update SERVICE_NAME --min-instances=N --max-instances=N

# Update secret
echo -n "VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# Redeploy service
gcloud builds submit --config=cloudbuild.yaml

# Check costs
gcloud alpha billing projects describe PROJECT_ID

# Destroy everything (WARNING!)
terraform destroy
```

---

**Estimated deployment time:** 15-20 minutes
**Estimated monthly cost:** $245-495
**Production-ready:** Yes

For detailed documentation, see `/terraform/README.md` and `/AGENT_24_CLOUD_RUN_DEPLOYMENT.md`
