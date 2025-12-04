# 🚀 One-Click Deployment Script

Complete deployment automation for the Winning Ads Generator platform.

## 📋 Overview

The `deploy.sh` script is your central deployment orchestration tool that handles:

- ✅ **Prerequisites checking** - Validates all required tools and dependencies
- ✅ **Environment management** - Loads and validates configuration
- ✅ **Local deployment** - Docker Compose for development
- ✅ **Cloud deployment** - Automated Cloud Run deployment to GCP
- ✅ **Health checks** - Validates deployed services
- ✅ **Rollback capability** - Safety net for failed deployments
- ✅ **Beautiful CLI** - Color-coded output with progress indicators
- ✅ **Comprehensive logging** - Every action logged for debugging

## 🎯 Quick Start

### Option 1: Local Development

```bash
./deploy.sh
# Choose option 1: Local Development (Docker Compose)
```

This will:
1. Build all Docker images
2. Start all services with docker-compose
3. Initialize databases
4. Display service URLs

**Access your services:**
- Gateway API: http://localhost:8080
- Drive Intel: http://localhost:8081
- Video Agent: http://localhost:8082
- ML Service: http://localhost:8003
- Meta Publisher: http://localhost:8083
- Titan Core: http://localhost:8084
- Frontend: http://localhost:80

### Option 2: Cloud Run Deployment

```bash
./deploy.sh
# Choose option 2: Backend to Cloud Run (GCP)
```

This will:
1. Enable required GCP APIs
2. Create Artifact Registry
3. Build and push Docker images
4. Deploy all services to Cloud Run
5. Configure inter-service networking
6. Run health checks
7. Display production URLs

### Option 3: Full Stack Deployment

```bash
./deploy.sh
# Choose option 3: Full Stack (Backend + Vercel Instructions)
```

Deploys backend to Cloud Run and provides instructions for Vercel frontend deployment.

## 📦 Prerequisites

### Required Tools

- **Docker** (v20.10+) - Container runtime
- **Docker Compose** (v2.0+) - Multi-container orchestration
- **Node.js** (v18+) - JavaScript runtime
- **npm** (v8+) - Package manager

### For Cloud Deployment

- **gcloud CLI** - Google Cloud SDK
- **Active GCP project** - With billing enabled
- **Proper IAM permissions** - To create resources

### Installation

**Docker & Docker Compose:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# macOS
brew install docker docker-compose
```

**Node.js & npm:**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node
```

**gcloud CLI:**
```bash
# Linux
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# macOS
brew install google-cloud-sdk

# Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## ⚙️ Configuration

### Local Development

Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your values
```

**Minimum required variables:**
```env
GEMINI_API_KEY=your_api_key_here
META_ACCESS_TOKEN=your_token_here
META_AD_ACCOUNT_ID=act_1234567890
```

### Production Deployment

Create `.env.production` file:
```bash
cp .env.production.example .env.production
# Edit .env.production with your production values
```

**Required production variables:**
```env
GCP_PROJECT_ID=your-gcp-project
GCP_REGION=us-central1
GEMINI_API_KEY=your_production_api_key
META_ACCESS_TOKEN=your_production_token
META_AD_ACCOUNT_ID=act_1234567890
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
```

## 🎨 Features

### Color-Coded Output

The script uses beautiful terminal colors for clarity:
- 🔵 **Blue** - Current step/action
- 🟢 **Green** - Success messages
- 🔴 **Red** - Errors and failures
- 🟡 **Yellow** - Warnings and important info
- 🔷 **Cyan** - Information and details

### Progress Indicators

- **Spinner animations** for long-running tasks
- **Progress bars** for multi-step operations
- **Real-time status updates** during builds

### Comprehensive Logging

All actions are logged to:
```
logs/deployment_YYYYMMDD_HHMMSS.log
```

View logs:
```bash
# Real-time log viewing
./deploy.sh
# Choose option 6: View Deployment Logs

# Or manually
tail -f logs/deployment_*.log
```

### Health Checks

The script validates deployment success by:
1. Checking service endpoints
2. Verifying health check responses
3. Testing inter-service communication
4. Confirming database connectivity

### Error Handling

- **Automatic rollback** on critical failures
- **Detailed error messages** with troubleshooting hints
- **Graceful degradation** for non-critical issues
- **Interrupt handling** (Ctrl+C) for clean exits

## 🔧 Menu Options

### 1. Local Development
Deploy entire stack locally with Docker Compose.

**Use case:** Development, testing, debugging

**Requirements:**
- Docker & Docker Compose
- `.env` file

**What it does:**
- Stops existing containers
- Builds all images
- Starts services with docker-compose
- Runs health checks
- Displays service URLs

### 2. Backend to Cloud Run
Deploy backend services to Google Cloud Run.

**Use case:** Production backend deployment

**Requirements:**
- gcloud CLI authenticated
- `.env.production` file
- GCP project with billing

**What it does:**
- Sets up GCP project
- Enables required APIs
- Creates Artifact Registry
- Builds and pushes images
- Deploys to Cloud Run
- Configures networking
- Runs validation

### 3. Full Stack Deployment
Backend to Cloud Run + Vercel instructions.

**Use case:** Complete production deployment

**Includes:**
- Everything from option 2
- Frontend deployment guide
- Environment variable instructions
- Vercel configuration help

### 4. Show Vercel Instructions
Display frontend deployment instructions only.

**Use case:** Separate frontend deployment

**Shows:**
- Vercel CLI commands
- Environment variables to set
- Deployment URLs

### 5. Validate Deployment
Check health of deployed services.

**Use case:** Post-deployment verification, troubleshooting

**Validates:**
- Service availability
- Health endpoint responses
- API connectivity

### 6. View Deployment Logs
Real-time log viewing.

**Use case:** Debugging, monitoring

**Shows:**
- All deployment actions
- Build output
- Error messages
- Timestamps

### 7. Rollback Deployment
Revert to previous version.

**Use case:** Failed deployment recovery

**Warning:** This action is destructive!

## 🏗️ Architecture

### Services Deployed

| Service | Port | Purpose |
|---------|------|---------|
| gateway-api | 8080 | Main API gateway |
| drive-intel | 8081 | Google Drive intelligence |
| video-agent | 8082 | Video processing |
| ml-service | 8003 | Machine learning models |
| meta-publisher | 8083 | Meta Ads publishing |
| titan-core | 8084 | Core AI orchestration |

### Deployment Flow

```
1. Prerequisites Check
   ├── Docker installed?
   ├── gcloud configured?
   └── Environment files exist?

2. Environment Loading
   ├── Load .env or .env.production
   └── Validate required variables

3. Build Phase
   ├── Build Docker images
   └── Push to registry (Cloud only)

4. Deploy Phase
   ├── Deploy independent services
   ├── Get service URLs
   ├── Deploy dependent services
   └── Configure inter-service networking

5. Validation Phase
   ├── Health checks
   ├── Connectivity tests
   └── Display URLs

6. Success!
   └── Save deployment info
```

## 🐛 Troubleshooting

### Common Issues

**1. Docker not running**
```
❌ Docker daemon is not running
```
**Solution:**
```bash
sudo systemctl start docker
# or on macOS
open -a Docker
```

**2. Missing gcloud**
```
❌ gcloud CLI not installed
```
**Solution:**
```bash
curl https://sdk.cloud.google.com | bash
gcloud auth login
```

**3. Permission denied**
```
Permission denied: deploy.sh
```
**Solution:**
```bash
chmod +x deploy.sh
```

**4. Environment file missing**
```
❌ .env.production not found
```
**Solution:**
```bash
cp .env.production.example .env.production
# Edit with your values
```

**5. GCP quota exceeded**
```
ERROR: Quota exceeded for resource
```
**Solution:**
- Check GCP quotas in Cloud Console
- Request quota increase
- Use different region

**6. Build timeout**
```
ERROR: Build exceeded timeout
```
**Solution:**
```bash
# Increase timeout in script or manual build
gcloud builds submit --timeout=30m
```

### Debug Mode

Run with verbose logging:
```bash
set -x  # Enable debug mode
./deploy.sh
```

View detailed logs:
```bash
tail -f logs/deployment_*.log | grep ERROR
```

## 📊 Monitoring

### Check Service Status

**Local:**
```bash
docker-compose ps
docker-compose logs -f [service-name]
```

**Cloud:**
```bash
gcloud run services list --region=us-central1
gcloud run services describe [service] --region=us-central1
gcloud logging read "resource.type=cloud_run_revision"
```

### Health Endpoints

All services expose health checks at:
```
GET /health
```

Test manually:
```bash
curl http://localhost:8080/health
curl https://your-service.run.app/health
```

## 🔒 Security Best Practices

1. **Never commit secrets** - Use `.env` files (already in `.gitignore`)
2. **Use service accounts** - For Cloud Run deployments
3. **Enable authentication** - Update `--allow-unauthenticated` for production
4. **Rotate credentials** - Regular API key rotation
5. **Use Secret Manager** - For sensitive values in production
6. **Enable VPC** - For service-to-service security
7. **Set up WAF** - Cloud Armor for DDoS protection

## 🚀 Production Checklist

Before deploying to production:

- [ ] All environment variables set in `.env.production`
- [ ] API keys are production (not test) keys
- [ ] Database is production-ready (managed service recommended)
- [ ] Domain names configured
- [ ] SSL/TLS certificates ready
- [ ] Monitoring and alerting configured
- [ ] Backup strategy in place
- [ ] Disaster recovery plan documented
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Security scanning completed
- [ ] Load testing performed
- [ ] Documentation up to date

## 📚 Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Vercel Deployment Guide](https://vercel.com/docs)
- [Project Main README](/README.md)
- [Production Deployment Guide](/DEPLOYMENT.md)

## 🆘 Support

If you encounter issues:

1. Check logs: `./deploy.sh` → Option 6
2. Run validation: `./deploy.sh` → Option 5
3. Review this README
4. Check service-specific logs
5. Open an issue with deployment logs attached

## 📝 License

This deployment script is part of the Winning Ads Generator project.
