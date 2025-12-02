# 🚀 Deploy Script - Quick Reference Card

## One Command Deploy

```bash
./deploy.sh
```

## Menu Options

| Option | Command | Use Case | Time |
|--------|---------|----------|------|
| **1** | Local Development | Dev/Testing | ~5 min |
| **2** | Cloud Run Backend | Production Backend | ~15 min |
| **3** | Full Stack | Complete Production | ~20 min |
| **4** | Vercel Instructions | Frontend Deploy | Instant |
| **5** | Validate Deployment | Health Check | ~1 min |
| **6** | View Logs | Debugging | Instant |
| **7** | Rollback | Emergency Recovery | ~5 min |

## Prerequisites Checklist

### Local Development
- [ ] Docker installed and running
- [ ] `.env` file configured
- [ ] Ports 8080-8084 available

### Cloud Deployment
- [ ] gcloud CLI installed
- [ ] Authenticated: `gcloud auth login`
- [ ] Project set: `gcloud config set project PROJECT_ID`
- [ ] `.env.production` configured
- [ ] Billing enabled on GCP project

## Quick Start Commands

### First Time Setup
```bash
# Clone and navigate to project
cd /home/user/geminivideo

# Copy environment template
cp .env.production.example .env.production

# Edit environment file
nano .env.production

# Make script executable (already done)
chmod +x deploy.sh
```

### Local Development
```bash
# Start everything locally
./deploy.sh
# Choose: 1

# View logs
docker-compose logs -f

# Stop everything
docker-compose down
```

### Production Deployment
```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy backend
./deploy.sh
# Choose: 2

# Deploy frontend (follow instructions)
./deploy.sh
# Choose: 4
```

## Service URLs

### Local (After Option 1)
```
http://localhost:8080  - Gateway API
http://localhost:8081  - Drive Intel
http://localhost:8082  - Video Agent
http://localhost:8003  - ML Service
http://localhost:8083  - Meta Publisher
http://localhost:8084  - Titan Core
http://localhost:80    - Frontend
```

### Cloud (After Option 2/3)
```
URLs saved to: .env.deployed

View with: cat .env.deployed
```

## Environment Files

| File | Purpose | Required For |
|------|---------|--------------|
| `.env` | Local development | Option 1 |
| `.env.production` | Production deployment | Options 2,3 |
| `.env.deployed` | Deployed URLs (auto-generated) | Option 4 |

## Required Environment Variables

### Minimum (Local)
```env
GEMINI_API_KEY=sk-...
META_ACCESS_TOKEN=...
META_AD_ACCOUNT_ID=act_...
```

### Production
```env
GCP_PROJECT_ID=my-project
GEMINI_API_KEY=sk-...
META_ACCESS_TOKEN=...
META_AD_ACCOUNT_ID=act_...
META_APP_ID=...
META_APP_SECRET=...
```

## Troubleshooting

### Common Errors

**"Docker daemon not running"**
```bash
sudo systemctl start docker  # Linux
open -a Docker              # macOS
```

**"Permission denied: deploy.sh"**
```bash
chmod +x deploy.sh
```

**"gcloud not found"**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**"Environment file not found"**
```bash
cp .env.production.example .env.production
nano .env.production
```

**Build fails**
```bash
# View detailed logs
./deploy.sh
# Choose: 6

# Or check directly
tail -f logs/deployment_*.log
```

**Health checks fail**
```bash
# Validate deployment
./deploy.sh
# Choose: 5

# Check service status
docker-compose ps              # Local
gcloud run services list       # Cloud
```

## Health Checks

### Local
```bash
curl http://localhost:8080/health
curl http://localhost:8081/health
```

### Cloud
```bash
source .env.deployed
curl $GATEWAY_URL/health
curl $DRIVE_INTEL_URL/health
```

## Logs

### View Deployment Logs
```bash
./deploy.sh
# Choose: 6

# Or manually
tail -f logs/deployment_*.log
```

### Service Logs

**Local:**
```bash
docker-compose logs -f                    # All services
docker-compose logs -f gateway-api        # Specific service
```

**Cloud:**
```bash
gcloud run services logs read gateway-api --region=us-central1
```

## Emergency Commands

### Stop Everything (Local)
```bash
docker-compose down
docker system prune -f
```

### Rollback (Cloud)
```bash
./deploy.sh
# Choose: 7
# Confirm: yes
```

### Reset Local Environment
```bash
docker-compose down -v
docker system prune -af
rm -rf data/*
./deploy.sh
# Choose: 1
```

### Delete Cloud Resources
```bash
# Delete Cloud Run services
gcloud run services delete gateway-api --region=us-central1 --quiet
gcloud run services delete drive-intel --region=us-central1 --quiet
# ... repeat for other services

# Delete Artifact Registry
gcloud artifacts repositories delete geminivideo-repo --location=us-central1 --quiet
```

## Performance Tips

### Speed Up Local Builds
```bash
# Build images in parallel
docker-compose build --parallel

# Use BuildKit
export DOCKER_BUILDKIT=1
```

### Speed Up Cloud Builds
```bash
# Increase timeout
# Edit deploy.sh line with gcloud builds submit
# Add: --timeout=30m
```

## Monitoring

### Local Status
```bash
# Check all containers
docker-compose ps

# Check resource usage
docker stats

# Check networks
docker network ls
```

### Cloud Status
```bash
# List all services
gcloud run services list --region=us-central1

# Describe specific service
gcloud run services describe gateway-api --region=us-central1

# View metrics
gcloud monitoring dashboards list
```

## Validation Checklist

### Post-Deployment

- [ ] All services show "✅" in deployment output
- [ ] Health checks pass (Option 5)
- [ ] Can access service URLs
- [ ] Frontend can connect to backend
- [ ] Database migrations completed
- [ ] Redis connection working
- [ ] Meta API integration working
- [ ] Gemini API integration working

### Production Only

- [ ] HTTPS enabled (automatic with Cloud Run)
- [ ] Authentication configured
- [ ] CORS origins set correctly
- [ ] Rate limiting enabled
- [ ] Monitoring dashboards working
- [ ] Error tracking configured
- [ ] Backup strategy in place

## Quick Fixes

### Service Won't Start
```bash
# Check logs
docker-compose logs [service-name]

# Restart specific service
docker-compose restart [service-name]

# Rebuild and restart
docker-compose up -d --build [service-name]
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8080

# Kill process
kill -9 [PID]

# Or change port in docker-compose.yml
```

### Out of Disk Space
```bash
# Clean Docker
docker system prune -af --volumes

# Check disk usage
df -h
du -sh /*
```

## Support Resources

- **Full README**: `DEPLOYMENT_SCRIPT_README.md`
- **Main Docs**: `DEPLOYMENT.md`
- **Logs**: `logs/deployment_*.log`
- **Environment**: `.env.production.example`

## Useful Commands

```bash
# Make executable
chmod +x deploy.sh

# Run deployment
./deploy.sh

# Check syntax
bash -n deploy.sh

# View script
cat deploy.sh | less

# Search logs
grep ERROR logs/deployment_*.log

# Count services deployed
docker-compose ps | wc -l
gcloud run services list --region=us-central1 | wc -l
```

---

**Remember**: Always test locally (Option 1) before deploying to production (Option 2)!
