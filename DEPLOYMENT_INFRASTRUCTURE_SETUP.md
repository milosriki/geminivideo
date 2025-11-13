# Deployment Infrastructure Setup Guide

## ⚠️ CRITICAL: Missing Infrastructure Components

Your application requires the following infrastructure that is **NOT YET DEPLOYED**:

### 1. PostgreSQL Database (Cloud SQL)
### 2. Redis Cache (Cloud Memorystore)
### 3. Worker Services (Background Job Processors)

---

## Quick Setup Commands

### Step 1: Create Cloud SQL PostgreSQL Instance

```bash
PROJECT_ID="gen-lang-client-0427673522"
REGION="us-west1"
INSTANCE_NAME="geminivideo-db"

# Create Cloud SQL instance (takes ~10 minutes)
gcloud sql instances create ${INSTANCE_NAME} \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=${REGION} \
  --root-password="CHANGE_THIS_PASSWORD" \
  --storage-type=SSD \
  --storage-size=10GB \
  --availability-type=zonal \
  --project=${PROJECT_ID}

# Create database
gcloud sql databases create geminivideo \
  --instance=${INSTANCE_NAME} \
  --project=${PROJECT_ID}

# Create user
gcloud sql users create geminivideo \
  --instance=${INSTANCE_NAME} \
  --password="CHANGE_THIS_PASSWORD" \
  --project=${PROJECT_ID}

# Get connection name
gcloud sql instances describe ${INSTANCE_NAME} \
  --project=${PROJECT_ID} \
  --format='value(connectionName)'
```

**Connection String Format:**
```
postgresql://geminivideo:PASSWORD@/geminivideo?host=/cloudsql/CONNECTION_NAME
```

### Step 2: Create Cloud Memorystore Redis Instance

```bash
REDIS_INSTANCE_NAME="geminivideo-redis"

# Create Redis instance (takes ~5 minutes)
gcloud redis instances create ${REDIS_INSTANCE_NAME} \
  --size=1 \
  --region=${REGION} \
  --redis-version=redis_7_0 \
  --project=${PROJECT_ID}

# Get Redis host
REDIS_HOST=$(gcloud redis instances describe ${REDIS_INSTANCE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(host)')

REDIS_PORT=$(gcloud redis instances describe ${REDIS_INSTANCE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID} \
  --format='value(port)')

echo "REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}"
```

### Step 3: Add GitHub Secrets

Add these secrets at: `https://github.com/milosriki/geminivideo/settings/secrets/actions`

1. **DATABASE_URL**: PostgreSQL connection string from Step 1
2. **REDIS_URL**: Redis connection string from Step 2

Example values:
```
DATABASE_URL=postgresql://geminivideo:PASSWORD@/geminivideo?host=/cloudsql/PROJECT:REGION:INSTANCE
REDIS_URL=redis://10.x.x.x:6379
```

### Step 4: Run Database Migrations

```bash
# Connect to Cloud SQL
gcloud sql connect ${INSTANCE_NAME} --user=geminivideo --project=${PROJECT_ID}

# Then run SQL migration script (paste the content of shared/db.sql)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Cloud Run Services                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ gateway  │  │  drive   │  │  video   │  │   ml    │ │
│  │   api    │  │  intel   │  │  agent   │  │ service │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │             │             │             │       │
│       └─────────────┴─────────────┴─────────────┘       │
│                          │                              │
│         ┌────────────────┴────────────────┐             │
│         │                                  │             │
│         ▼                                  ▼             │
│  ┌─────────────┐                   ┌─────────────┐      │
│  │   Cloud     │                   │   Cloud     │      │
│  │ Memorystore │                   │     SQL     │      │
│  │   (Redis)   │                   │ (PostgreSQL)│      │
│  └─────────────┘                   └─────────────┘      │
│         ▲                                  ▲             │
│         │                                  │             │
│         └────────────────┬─────────────────┘             │
│                          │                              │
│       ┌──────────────────┴──────────────────┐           │
│       │                                      │           │
│       ▼                                      ▼           │
│  ┌──────────┐                         ┌──────────┐      │
│  │  drive   │                         │  video   │      │
│  │  worker  │                         │  worker  │      │
│  │(background)                        │(background)      │
│  └──────────┘                         └──────────┘      │
└─────────────────────────────────────────────────────────┘
```

## Current Deployment Status

### ✅ Deployed Services (6)
- ml-service
- drive-intel
- video-agent
- gateway-api
- meta-publisher
- frontend

### ❌ Missing Infrastructure (4)
- Cloud SQL (PostgreSQL) - **REQUIRED**
- Cloud Memorystore (Redis) - **REQUIRED**
- drive-worker (background processor) - **REQUIRED**
- video-worker (background processor) - **REQUIRED**

---

## Cost Estimate

| Service | Configuration | Monthly Cost (USD) |
|---------|--------------|-------------------|
| Cloud SQL (db-f1-micro) | 10GB SSD | ~$10 |
| Cloud Memorystore (1GB) | Basic tier | ~$50 |
| Worker Services (2) | 512Mi, min=0, max=1 | ~$5 |
| **Total Infrastructure** | | **~$65/month** |

---

## Alternative: Use Existing Services Without Infrastructure

If you want to deploy **WITHOUT** setting up PostgreSQL and Redis:

### Option 1: Use In-Memory Fallbacks (Development Only)

Modify services to use in-memory stores when DATABASE_URL/REDIS_URL are not set.

**Pros**: Quick deployment, no infrastructure costs
**Cons**: No persistence, no async queues, data lost on restart

### Option 2: Use Free External Services

- **PostgreSQL**: Use Supabase free tier or Neon
- **Redis**: Use Redis Cloud free tier (30MB)

**Pros**: Free, managed
**Cons**: Rate limits, not recommended for production

---

## Next Steps

1. **Setup Infrastructure** (45 minutes):
   - [ ] Create Cloud SQL instance
   - [ ] Create Redis instance
   - [ ] Add secrets to GitHub
   - [ ] Run database migrations

2. **Deploy Workers** (5 minutes):
   - [ ] Update deployment workflow
   - [ ] Deploy drive-worker and video-worker

3. **Test End-to-End** (15 minutes):
   - [ ] Submit analysis job via API
   - [ ] Verify worker processes the job
   - [ ] Check database for results

---

## Troubleshooting

### Services can't connect to Cloud SQL
- Enable Cloud SQL API
- Add Cloud SQL Client role to service account
- Use Unix socket connection string format

### Services can't connect to Redis
- Enable VPC connector
- Configure Redis with authorized network
- Check firewall rules

### Workers not processing jobs
- Check Redis queue has items: `LLEN analysis_queue`
- Check worker logs: `gcloud logging read`
- Verify DATABASE_URL and REDIS_URL are set
