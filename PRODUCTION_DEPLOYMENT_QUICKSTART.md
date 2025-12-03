# Production Deployment Quickstart

**Complete production deployment in under 30 minutes!**

This guide provides the fastest path to deploying Gemini Video to production.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] GCP account with billing enabled
- [ ] Docker installed locally
- [ ] `gcloud` CLI installed and authenticated
- [ ] Gemini API key
- [ ] Meta API credentials (if using Meta integration)
- [ ] Domain name (optional)

## Option 1: GCP Cloud Run (Recommended)

**Estimated time: 20-30 minutes**

### Step 1: Set Up GCP Project (5 min)

```bash
# Set your project ID
export PROJECT_ID="geminivideo-prod-$(date +%s)"
export REGION="us-central1"

# Create project
gcloud projects create $PROJECT_ID
gcloud config set project $PROJECT_ID

# Enable billing (visit console to link billing account)
open "https://console.cloud.google.com/billing/linkedaccount?project=$PROJECT_ID"

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com

# Create Artifact Registry
gcloud artifacts repositories create geminivideo \
  --repository-format=docker \
  --location=$REGION

# Configure Docker
gcloud auth configure-docker ${REGION}-docker.pkg.dev
```

### Step 2: Store Secrets (2 min)

```bash
# Store API keys in Secret Manager
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key --data-file=-
echo -n "YOUR_META_ACCESS_TOKEN" | gcloud secrets create meta-access-token --data-file=-
echo -n "$(openssl rand -base64 64)" | gcloud secrets create jwt-secret --data-file=-

# Generate database password
DB_PASSWORD=$(openssl rand -base64 32)
echo -n "$DB_PASSWORD" | gcloud secrets create db-password --data-file=-
```

### Step 3: Deploy Database (5 min)

```bash
# Create Cloud SQL instance
gcloud sql instances create geminivideo-db \
  --database-version=POSTGRES_15 \
  --tier=db-g1-small \
  --region=$REGION \
  --storage-auto-increase

# Create database and user
gcloud sql databases create geminivideo --instance=geminivideo-db
gcloud sql users create geminivideo --instance=geminivideo-db --password="$DB_PASSWORD"

# Get connection name
CONNECTION_NAME=$(gcloud sql instances describe geminivideo-db --format='value(connectionName)')

# Store connection string
echo -n "postgresql://geminivideo:${DB_PASSWORD}@/geminivideo?host=/cloudsql/${CONNECTION_NAME}" | \
  gcloud secrets create database-url --data-file=-
```

### Step 4: Configure Deployment (2 min)

```bash
# Clone repository
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# Create production environment file
cp .env.production.example .env.production

# Edit with your values
cat > .env.production << EOF
GCP_PROJECT_ID=$PROJECT_ID
CLOUD_RUN_REGION=$REGION
REGISTRY_URL=${REGION}-docker.pkg.dev/${PROJECT_ID}/geminivideo
GEMINI_API_KEY=$(gcloud secrets versions access latest --secret=gemini-api-key)
DATABASE_URL=$(gcloud secrets versions access latest --secret=database-url)
JWT_SECRET=$(gcloud secrets versions access latest --secret=jwt-secret)
META_ACCESS_TOKEN=$(gcloud secrets versions access latest --secret=meta-access-token)
META_AD_ACCOUNT_ID=act_YOUR_AD_ACCOUNT_ID
META_APP_ID=YOUR_APP_ID
META_APP_SECRET=YOUR_APP_SECRET
CORS_ORIGINS=*
EOF
```

### Step 5: Deploy All Services (10-15 min)

```bash
# Make deploy script executable
chmod +x scripts/deploy-production.sh

# Deploy to Cloud Run
DEPLOYMENT_TARGET=cloud-run ./scripts/deploy-production.sh
```

This will:
- ✅ Build all 7 Docker images
- ✅ Push to Artifact Registry
- ✅ Deploy services in order
- ✅ Configure environment variables
- ✅ Run health checks
- ✅ Display service URLs

### Step 6: Access Your Application

```bash
# Get frontend URL
FRONTEND_URL=$(gcloud run services describe frontend --region=$REGION --format='value(status.url)')
echo "🚀 Application available at: $FRONTEND_URL"

# Open in browser
open $FRONTEND_URL
```

**Done! Your production application is live! 🎉**

---

## Option 2: Docker Compose on VPS

**Estimated time: 15-20 minutes**

### Step 1: Prepare Server (2 min)

```bash
# SSH into your VPS
ssh user@your-server.com

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes to take effect
exit
ssh user@your-server.com
```

### Step 2: Clone and Configure (3 min)

```bash
# Clone repository
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# Create production environment
cp .env.production.example .env.production

# Generate secure credentials
export POSTGRES_PASSWORD=$(openssl rand -base64 32)
export JWT_SECRET=$(openssl rand -base64 64)

# Edit production config
nano .env.production
# Set:
# - POSTGRES_PASSWORD (generated above)
# - GEMINI_API_KEY (your API key)
# - META_* credentials
# - JWT_SECRET (generated above)
# - CORS_ORIGINS (your domain)
```

### Step 3: Deploy (5-10 min)

```bash
# Build and start all services
DOCKER_BUILDKIT=0 docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# Verify all services are running
docker-compose -f docker-compose.production.yml ps

# Check logs
docker-compose -f docker-compose.production.yml logs -f
```

### Step 4: Configure SSL (5 min)

```bash
# Install nginx-proxy and Let's Encrypt companion
docker network create nginx-proxy

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

# Connect frontend to proxy network
docker network connect nginx-proxy geminivideo-frontend-prod

# Update frontend service with domain
docker-compose -f docker-compose.production.yml down frontend
docker-compose -f docker-compose.production.yml up -d frontend
```

### Step 5: Access Your Application

```bash
# Application is now available at:
# http://YOUR_SERVER_IP (or https://yourdomain.com if SSL configured)

echo "🚀 Application available at: http://$(curl -s ifconfig.me)"
```

**Done! Your application is running in production! 🎉**

---

## Post-Deployment Steps

### 1. Set Up Monitoring

```bash
# Cloud Run
gcloud run services logs read gateway-api --region=$REGION --limit=50

# Docker Compose
docker-compose -f docker-compose.production.yml logs -f
```

### 2. Enable Backups

```bash
# Cloud SQL
gcloud sql backups create --instance=geminivideo-db

# Docker PostgreSQL
docker exec geminivideo-postgres-prod pg_dump -U geminivideo geminivideo > backup.sql
```

### 3. Configure Domain (if needed)

```bash
# Cloud Run
gcloud run domain-mappings create \
  --service=frontend \
  --domain=yourdomain.com \
  --region=$REGION

# Update DNS records as instructed
```

### 4. Test Deployment

```bash
# Test Gateway API
curl -f https://your-gateway-url/health

# Test Frontend
curl -f https://your-frontend-url

# Test video upload
# Use the web interface to upload a video and verify processing
```

---

## Quick Commands Reference

### Cloud Run

```bash
# View all services
gcloud run services list --region=$REGION

# View logs
gcloud run services logs read SERVICE_NAME --region=$REGION

# Update service
gcloud run services update SERVICE_NAME --region=$REGION --set-env-vars="KEY=VALUE"

# Rollback
gcloud run services update-traffic SERVICE_NAME --to-revisions REVISION=100 --region=$REGION
```

### Docker Compose

```bash
# View status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f SERVICE_NAME

# Restart service
docker-compose -f docker-compose.production.yml restart SERVICE_NAME

# Scale workers
docker-compose -f docker-compose.production.yml up -d --scale drive-worker=4
```

---

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker-compose -f docker-compose.production.yml logs SERVICE_NAME

# Or for Cloud Run
gcloud run services logs read SERVICE_NAME --region=$REGION

# Common issues:
# - Missing environment variables
# - Database connection issues
# - Port conflicts
# - Insufficient memory
```

### Database Connection Failed

```bash
# Test connection
docker exec geminivideo-postgres-prod psql -U geminivideo -d geminivideo -c "SELECT 1;"

# Or for Cloud SQL
gcloud sql connect geminivideo-db --user=geminivideo
```

### High Memory Usage

```bash
# Check resources
docker stats

# Increase memory limits in docker-compose.production.yml
# Or increase Cloud Run memory
gcloud run services update SERVICE_NAME --memory=4Gi --region=$REGION
```

---

## Cost Estimates

### Cloud Run (with 10,000 monthly video analyses)

| Component | Cost/Month |
|-----------|------------|
| Cloud Run services | $50-100 |
| Cloud SQL (db-g1-small) | $25 |
| Artifact Registry | $5 |
| Networking | $10 |
| **Total** | **~$90-140/month** |

### VPS (4 CPU, 16GB RAM)

| Component | Cost/Month |
|-----------|------------|
| VPS (DigitalOcean/Linode) | $48-96 |
| Domain name | $10-15/year |
| **Total** | **~$50-100/month** |

---

## Security Checklist

- [ ] Strong database passwords (32+ characters)
- [ ] JWT secret is randomly generated
- [ ] CORS properly configured
- [ ] API keys stored in secrets (not environment files)
- [ ] SSL/TLS enabled for production
- [ ] Firewall rules configured
- [ ] Database backups enabled
- [ ] Monitoring and alerting set up
- [ ] Resource limits configured
- [ ] Regular security updates scheduled

---

## Next Steps

1. **Configure CI/CD**: Set up GitHub Actions for automated deployments
2. **Set up monitoring**: Enable Cloud Monitoring or install Prometheus
3. **Optimize performance**: Add caching, CDN, and database indexes
4. **Scale appropriately**: Adjust instance counts based on traffic
5. **Regular backups**: Set up automated daily backups
6. **Documentation**: Document your specific configuration

For detailed information, see the complete [DEPLOYMENT.md](./DEPLOYMENT.md) guide.

---

**Need help?** Open an issue at https://github.com/milosriki/geminivideo/issues

**Production support:** Contact the Gemini Video team

**Last updated:** December 2024
