# Gemini Video - Terraform Infrastructure

This directory contains Terraform configurations for deploying Gemini Video to Google Cloud Platform (GCP) using Cloud Run.

## Architecture Overview

The infrastructure includes:

- **6 Cloud Run Services**: gateway-api, drive-intel, video-agent, ml-service, meta-publisher, titan-core
- **1 Frontend Service**: React/Vite application served via Cloud Run
- **Cloud SQL PostgreSQL**: Managed database with automatic backups
- **Redis Memorystore**: High-availability caching layer
- **Secret Manager**: Secure credential storage
- **Cloud Armor**: WAF and DDoS protection
- **VPC Network**: Private networking with VPC connector
- **Artifact Registry**: Docker image repository
- **Cloud Build**: Automated deployment triggers

## Prerequisites

1. **GCP Project**: Create a GCP project or use an existing one
2. **gcloud CLI**: Install and authenticate
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. **Terraform**: Install version >= 1.5.0
   ```bash
   brew install terraform  # macOS
   # or download from https://www.terraform.io/downloads
   ```
4. **Enable Billing**: Ensure billing is enabled on your GCP project

## Initial Setup

### 1. Create Terraform State Bucket

```bash
# Replace YOUR_PROJECT_ID with your actual project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"

# Create bucket for Terraform state
gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${PROJECT_ID}-terraform-state

# Enable versioning
gsutil versioning set on gs://${PROJECT_ID}-terraform-state
```

### 2. Configure Variables

```bash
# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

Required variables:
- `project_id`: Your GCP project ID
- `database_password`: Secure password for PostgreSQL (min 32 chars)
- `github_owner`: Your GitHub username/org
- `github_repo`: Repository name

### 3. Create Secret Manager Secrets

```bash
# Database URL
echo -n "postgresql://user:password@host/db" | \
  gcloud secrets create geminivideo-database-url --data-file=-

# Redis URL
echo -n "redis://host:6379" | \
  gcloud secrets create geminivideo-redis-url --data-file=-

# JWT Secret
openssl rand -base64 64 | \
  gcloud secrets create geminivideo-jwt-secret --data-file=-

# Gemini API Key
echo -n "YOUR_GEMINI_API_KEY" | \
  gcloud secrets create geminivideo-gemini-api-key --data-file=-

# Meta Access Token
echo -n "YOUR_META_ACCESS_TOKEN" | \
  gcloud secrets create geminivideo-meta-access-token --data-file=-

# Meta App Secret
echo -n "YOUR_META_APP_SECRET" | \
  gcloud secrets create geminivideo-meta-app-secret --data-file=-
```

## Deployment

### Initialize Terraform

```bash
cd terraform
terraform init
```

### Plan Deployment

```bash
terraform plan
```

Review the plan carefully to ensure all resources are correct.

### Apply Configuration

```bash
terraform apply
```

Type `yes` when prompted to create the infrastructure.

This will take approximately 10-15 minutes to:
1. Create VPC network and subnet
2. Provision Cloud SQL PostgreSQL
3. Create Redis Memorystore instance
4. Set up Secret Manager secrets
5. Create Artifact Registry repository
6. Deploy Cloud Run services
7. Configure Cloud Armor security policies
8. Set up IAM permissions

### Get Service URLs

```bash
terraform output
```

This will display all deployed service URLs.

## Managing Infrastructure

### Update Services

After making changes to `main.tf` or `variables.tf`:

```bash
terraform plan
terraform apply
```

### Scale Services

Edit `terraform.tfvars`:

```hcl
gateway_min_instances = 2
gateway_max_instances = 20
```

Then apply:

```bash
terraform apply
```

### View State

```bash
terraform show
terraform state list
```

### Destroy Infrastructure

**WARNING**: This will delete all resources and data.

```bash
terraform destroy
```

## GitHub Actions Integration

The project includes a GitHub Actions workflow for automated deployments.

### Setup GitHub Secrets

1. Create a service account key:
   ```bash
   gcloud iam service-accounts create github-actions \
     --display-name="GitHub Actions"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/run.admin"

   gcloud projects add-iam-policy-binding $PROJECT_ID \
     --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
     --role="roles/storage.admin"

   gcloud iam service-accounts keys create github-sa-key.json \
     --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com
   ```

2. Add secrets to GitHub:
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_SA_KEY`: Contents of `github-sa-key.json`
   - `SLACK_WEBHOOK_URL`: (Optional) Slack webhook for notifications

3. Push to `main` branch to trigger deployment

## Cost Estimation

Estimated monthly costs (based on moderate usage):

| Resource | Configuration | Est. Cost/Month |
|----------|--------------|-----------------|
| Cloud Run (7 services) | 1-10 instances each | $50-200 |
| Cloud SQL PostgreSQL | db-custom-2-7680 | $100-150 |
| Redis Memorystore | 2GB HA | $60-80 |
| VPC Connector | Standard | $20-30 |
| Cloud Armor | Security policies | $10-20 |
| Artifact Registry | Storage & egress | $5-15 |
| Cloud Build | 120 builds/month | $0 (free tier) |
| **TOTAL** | | **$245-495/month** |

### Cost Optimization Tips

1. **Reduce min instances** for non-critical services to 0
2. **Use BASIC tier Redis** for development ($30/month vs $60)
3. **Lower database tier** to db-custom-1-3840 for staging
4. **Enable autoscaling** to scale down during off-peak hours
5. **Set budget alerts** to monitor spending

## Monitoring

### View Logs

```bash
# All Cloud Run services
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Specific service
gcloud logging read "resource.labels.service_name=geminivideo-gateway-api" --limit=50
```

### View Metrics

```bash
# Service metrics
gcloud monitoring dashboards list

# Create alert policy
gcloud alpha monitoring policies create --policy-from-file=alert-policy.yaml
```

### Access Cloud Console

- **Cloud Run**: https://console.cloud.google.com/run
- **Cloud SQL**: https://console.cloud.google.com/sql
- **Logs**: https://console.cloud.google.com/logs
- **Metrics**: https://console.cloud.google.com/monitoring

## Troubleshooting

### Service Won't Deploy

1. Check Cloud Run logs:
   ```bash
   gcloud run services logs read geminivideo-gateway-api --limit=50
   ```

2. Verify secrets exist:
   ```bash
   gcloud secrets list
   ```

3. Check service account permissions:
   ```bash
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:geminivideo-cloud-run*"
   ```

### Database Connection Issues

1. Verify Cloud SQL is running:
   ```bash
   gcloud sql instances list
   ```

2. Check VPC connector:
   ```bash
   gcloud compute networks vpc-access connectors list --region=$REGION
   ```

3. Test connection from Cloud Shell:
   ```bash
   gcloud sql connect geminivideo-postgres-production --user=geminivideo
   ```

### High Costs

1. Check current spending:
   ```bash
   gcloud billing accounts list
   gcloud billing projects describe $PROJECT_ID
   ```

2. Review resource usage:
   ```bash
   gcloud run services list
   gcloud sql instances list
   ```

3. Scale down unused services:
   ```bash
   gcloud run services update SERVICE_NAME --min-instances=0
   ```

## Security Best Practices

1. **Rotate secrets regularly** (every 90 days)
2. **Enable Cloud Armor** for all public services
3. **Use VPC connector** for database access
4. **Enable audit logging** for compliance
5. **Set up budget alerts** to prevent overspending
6. **Use least privilege IAM** roles
7. **Enable binary authorization** for production

## Backup and Recovery

### Database Backups

Automatic backups are configured:
- Daily backups at 2:00 AM UTC
- 30-day retention
- Point-in-time recovery enabled

Restore from backup:
```bash
gcloud sql backups list --instance=geminivideo-postgres-production
gcloud sql backups restore BACKUP_ID --backup-instance=geminivideo-postgres-production
```

### Disaster Recovery

1. **Export Terraform state**:
   ```bash
   terraform state pull > state-backup.json
   ```

2. **Export database**:
   ```bash
   gcloud sql export sql geminivideo-postgres-production \
     gs://$PROJECT_ID-backups/db-backup-$(date +%Y%m%d).sql
   ```

3. **Document service URLs** and configurations

## Support

For issues or questions:
- Check [GCP Documentation](https://cloud.google.com/docs)
- Review [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- Open an issue in the project repository

## License

Copyright (c) 2024 Gemini Video. All rights reserved.
