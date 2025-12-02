# Environment Setup Guide

This guide explains how to configure environment variables for Gemini Video deployment.

## Quick Start

### Option 1: Interactive Setup (Recommended)

Run the interactive setup script that will guide you through all configuration steps:

```bash
bash scripts/setup-env.sh
```

The script will:
- ✓ Prompt you for all required values
- ✓ Validate API keys and connections
- ✓ Generate .env files for all services
- ✓ Test configurations
- ✓ Provide deployment instructions

### Option 2: Manual Setup

1. **Copy the template:**
   ```bash
   cp .env.deployment .env.production
   ```

2. **Edit the file:**
   ```bash
   nano .env.production
   # or
   vim .env.production
   ```

3. **Fill in required values:**
   - Replace all `YOUR_*` and `your-*` placeholders
   - See sections below for where to get each value

4. **Copy to service directories:**
   ```bash
   # Gateway API
   cp .env.production services/gateway-api/.env

   # Titan-Core
   cp .env.production services/titan-core/api/.env

   # Other services
   cp .env.production services/drive-intel/.env
   cp .env.production services/video-agent/.env
   cp .env.production services/ml-service/.env
   ```

## Required Configuration

### 1. Database (Required)

**Option A: Supabase (Easiest)**
```bash
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

Get from: https://app.supabase.com/project/_/settings/api

**Option B: Self-hosted PostgreSQL**
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=geminivideo
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=geminivideo
DATABASE_URL=postgresql://user:password@host:5432/database
```

### 2. Redis Cache (Required)

**Option A: Upstash (Recommended for serverless)**
```bash
UPSTASH_REDIS_REST_URL=https://xxxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token
```

Get from: https://console.upstash.com/

**Option B: Self-hosted Redis**
```bash
REDIS_URL=redis://localhost:6379
```

### 3. AI API Keys (Required)

**Gemini (Required):**
```bash
GEMINI_API_KEY=your-key
```
Get from: https://aistudio.google.com/app/apikey

**OpenAI (Recommended):**
```bash
OPENAI_API_KEY=sk-...
```
Get from: https://platform.openai.com/api-keys

**Anthropic (Recommended):**
```bash
ANTHROPIC_API_KEY=sk-ant-...
```
Get from: https://console.anthropic.com/

### 4. Google Cloud Platform (Required for Cloud Run)

```bash
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
GCS_BUCKET_NAME=your-bucket-name
CLOUD_RUN_SERVICE_ACCOUNT=service-account@project.iam.gserviceaccount.com
```

Setup:
```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable storage.googleapis.com

# Create bucket
gsutil mb gs://YOUR_BUCKET_NAME

# Create service account
gcloud iam service-accounts create geminivideo-sa

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:geminivideo-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"
```

## Optional Configuration

### Meta/Facebook Ads (for publishing)

```bash
META_APP_ID=your-app-id
META_APP_SECRET=your-app-secret
META_ACCESS_TOKEN=your-long-lived-token
META_AD_ACCOUNT_ID=act_1234567890
META_PAGE_ID=your-page-id
```

Get from: https://developers.facebook.com/apps/

### Firebase (for frontend authentication)

```bash
VITE_FIREBASE_API_KEY=AIza...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abc123
```

Get from: https://console.firebase.google.com/project/_/settings/general

## Testing Configuration

After setting up your environment variables:

```bash
# Test all connections
bash scripts/test-connections.sh

# Test individual services
docker-compose -f docker-compose.yml up -d
docker-compose ps
docker-compose logs -f gateway-api
```

## Deployment

### Docker Compose (Self-hosted)

```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f

# Access services
# Frontend: http://localhost:3000
# Gateway API: http://localhost:8080
# Titan-Core: http://localhost:8084
```

### Google Cloud Run (Serverless)

```bash
# Deploy all services
bash scripts/deploy-production.sh

# The script will:
# 1. Build Docker images
# 2. Push to Artifact Registry
# 3. Deploy to Cloud Run
# 4. Run health checks
# 5. Output service URLs
```

## Security Best Practices

### ✓ DO:
- Use strong passwords (minimum 32 characters)
- Generate JWT secret with: `openssl rand -base64 64`
- Store secrets in environment variables, not in code
- Use `.env.local` for local development (never commit)
- Use Secret Manager for production (GCP, AWS, etc.)
- Rotate credentials regularly
- Enable 2FA on all cloud accounts

### ✗ DON'T:
- Commit `.env` files to version control
- Use default passwords
- Share credentials in chat/email
- Use same password across services
- Store credentials in code comments
- Leave debug mode enabled in production

## Troubleshooting

### Database connection fails
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Test connection manually
psql "postgresql://user:password@host:5432/database" -c "SELECT 1;"

# Check logs
docker-compose logs postgres
```

### Redis connection fails
```bash
# Check if Redis is running
docker-compose ps redis

# Test connection
redis-cli -h localhost -p 6379 ping

# Check logs
docker-compose logs redis
```

### API key validation fails
```bash
# Test Gemini API key
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro?key=YOUR_KEY"

# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

### Service won't start
```bash
# Check environment variables are loaded
docker-compose config

# Check container logs
docker-compose logs SERVICE_NAME

# Restart specific service
docker-compose restart SERVICE_NAME
```

## Environment Variables Reference

### Critical (Required)
- `GEMINI_API_KEY` - Google Gemini API access
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis cache connection
- `JWT_SECRET` - API authentication

### Important (Recommended)
- `OPENAI_API_KEY` - Enhanced AI capabilities
- `ANTHROPIC_API_KEY` - Claude integration
- `GCP_PROJECT_ID` - Cloud deployment
- `GCS_BUCKET_NAME` - File storage

### Optional (Features)
- `META_ACCESS_TOKEN` - Ad publishing
- `VITE_FIREBASE_*` - User authentication
- `UPSTASH_REDIS_REST_URL` - Serverless Redis
- `SUPABASE_URL` - Managed PostgreSQL

## Getting Help

### Documentation
- Deployment: `docs/DEPLOYMENT.md`
- Configuration: `docs/CONFIGURATION.md`
- API Reference: `docs/API.md`

### Logs Location
- Docker Compose: `docker-compose logs SERVICE_NAME`
- Cloud Run: Google Cloud Console > Cloud Run > Service > Logs

### Support Resources
- Check existing `.env.example` files in each service directory
- Review `scripts/test-connections.sh` for validation examples
- See `scripts/deploy-production.sh` for deployment flow

## File Structure

```
geminivideo/
├── .env.deployment          # Master template (this file)
├── .env.production          # Your production config (create from template)
├── .env.local               # Local development (not committed)
├── scripts/
│   ├── setup-env.sh         # Interactive setup script
│   ├── test-connections.sh  # Test configurations
│   └── deploy-production.sh # Deployment script
├── services/
│   ├── gateway-api/.env
│   ├── titan-core/api/.env
│   ├── drive-intel/.env
│   ├── video-agent/.env
│   ├── ml-service/.env
│   └── meta-publisher/.env
└── frontend/.env
```

## Next Steps

1. ✓ Run `bash scripts/setup-env.sh` to configure environment
2. ✓ Run `bash scripts/test-connections.sh` to validate setup
3. ✓ Run `bash scripts/deploy-production.sh` to deploy
4. ✓ Monitor logs and health checks
5. ✓ Set up monitoring and alerts
6. ✓ Configure backups
7. ✓ Review security settings

Good luck with your deployment! 🚀
