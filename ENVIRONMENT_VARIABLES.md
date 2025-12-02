# Environment Variables - Complete Reference

## Overview

This document provides a complete reference of all environment variables used across the Gemini Video platform.

## File Locations

```
geminivideo/
├── .env.deployment          # Master template (all variables)
├── .env.production          # Production configuration (generated)
├── .env.local               # Local development (not committed)
├── ENV_SETUP_GUIDE.md       # Setup documentation
├── ENVIRONMENT_VARIABLES.md # This file
├── scripts/
│   ├── setup-env.sh         # Interactive setup
│   └── validate-env.sh      # Validation
└── services/
    ├── gateway-api/.env
    ├── titan-core/api/.env
    ├── drive-intel/.env
    ├── video-agent/.env
    ├── ml-service/.env
    ├── meta-publisher/.env
    └── frontend/.env
```

## Variable Categories

### Core Infrastructure (Required)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `NODE_ENV` | Environment mode | `production` | Set to `development`, `staging`, or `production` |
| `DEPLOYMENT_TARGET` | Deployment platform | `cloud-run` | `cloud-run` or `docker-compose` |
| `JWT_SECRET` | API authentication | `openssl rand -base64 64` | Generate with OpenSSL |
| `CORS_ORIGINS` | Allowed origins | `https://app.example.com` | Your frontend domain(s) |

### Database (Required)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pass@host:5432/db` | Your database |
| `POSTGRES_USER` | Database user | `geminivideo` | Set during DB setup |
| `POSTGRES_PASSWORD` | Database password | Strong password (32+ chars) | Generate securely |
| `POSTGRES_DB` | Database name | `geminivideo` | Your choice |
| `POSTGRES_HOST` | Database host | `localhost` | Your DB host |
| `POSTGRES_PORT` | Database port | `5432` | Default: 5432 |

### Supabase (Alternative to self-hosted DB)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` | [Supabase Dashboard](https://app.supabase.com) → Settings → API |
| `SUPABASE_ANON_KEY` | Public API key | `eyJ...` | [Supabase Dashboard](https://app.supabase.com) → Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Private API key | `eyJ...` | [Supabase Dashboard](https://app.supabase.com) → Settings → API |

### Redis Cache (Required)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `REDIS_URL` | Redis connection | `redis://localhost:6379` | Your Redis instance |
| `UPSTASH_REDIS_REST_URL` | Upstash REST URL | `https://xxx.upstash.io` | [Upstash Console](https://console.upstash.com) |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash token | `xxx...` | [Upstash Console](https://console.upstash.com) |

### AI API Keys (Required: Gemini, Recommended: Others)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `GEMINI_API_KEY` | Google Gemini API | `AIza...` | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GEMINI_MODEL_ID` | Model version | `gemini-2.0-flash-thinking-exp-1219` | See Gemini docs |
| `OPENAI_API_KEY` | OpenAI API | `sk-...` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | Anthropic Claude | `sk-ant-...` | [Anthropic Console](https://console.anthropic.com) |

### Google Cloud Platform (Required for Cloud Run)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `GCP_PROJECT_ID` | GCP project ID | `my-project-123` | [GCP Console](https://console.cloud.google.com) |
| `GCP_REGION` | Deployment region | `us-central1` | Choose from GCP regions |
| `GCS_BUCKET_NAME` | Storage bucket | `geminivideo-storage` | Create with `gsutil mb` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account path | `/path/to/key.json` | Download from GCP Console |
| `CLOUD_RUN_SERVICE_ACCOUNT` | Service account email | `sa@project.iam.gserviceaccount.com` | Create in GCP IAM |
| `CLOUD_RUN_REGION` | Cloud Run region | `us-central1` | Usually same as GCP_REGION |
| `REGISTRY_URL` | Container registry | `us-central1-docker.pkg.dev/...` | Auto-generated |

### Meta/Facebook Ads (Optional)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `META_APP_ID` | Facebook app ID | `123456789012345` | [Meta Developers](https://developers.facebook.com/apps) |
| `META_APP_SECRET` | App secret | `abc...` | [Meta Developers](https://developers.facebook.com/apps) → Settings → Basic |
| `META_ACCESS_TOKEN` | User access token | `EAA...` | [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer) |
| `META_AD_ACCOUNT_ID` | Ad account ID | `act_1234567890` | [Meta Ads Manager](https://business.facebook.com/adsmanager) |
| `META_PAGE_ID` | Facebook page ID | `123456789012345` | Page settings |
| `META_CLIENT_TOKEN` | Client token | `xxx...` | [Meta Developers](https://developers.facebook.com/apps) → Settings → Advanced |

### Firebase (Optional - for Authentication)

| Variable | Description | Example | Where to Get |
|----------|-------------|---------|--------------|
| `VITE_FIREBASE_API_KEY` | Firebase API key | `AIza...` | [Firebase Console](https://console.firebase.google.com) → Project Settings |
| `VITE_FIREBASE_AUTH_DOMAIN` | Auth domain | `project.firebaseapp.com` | [Firebase Console](https://console.firebase.google.com) → Project Settings |
| `VITE_FIREBASE_PROJECT_ID` | Project ID | `my-project` | [Firebase Console](https://console.firebase.google.com) → Project Settings |
| `VITE_FIREBASE_STORAGE_BUCKET` | Storage bucket | `project.firebasestorage.app` | [Firebase Console](https://console.firebase.google.com) → Project Settings |
| `VITE_FIREBASE_MESSAGING_SENDER_ID` | Messaging ID | `123456789012` | [Firebase Console](https://console.firebase.google.com) → Project Settings |
| `VITE_FIREBASE_APP_ID` | App ID | `1:xxx:web:xxx` | [Firebase Console](https://console.firebase.google.com) → Project Settings |
| `VITE_FIREBASE_MEASUREMENT_ID` | Analytics ID | `G-XXXXXXXXXX` | [Firebase Console](https://console.firebase.google.com) → Project Settings |

### Service URLs

| Variable | Description | Example | Used By |
|----------|-------------|---------|---------|
| `GATEWAY_URL` | Gateway API URL | `https://gateway-xxx.run.app` | Frontend, Services |
| `VITE_GATEWAY_URL` | Gateway (frontend) | `https://gateway-xxx.run.app` | Frontend only |
| `DRIVE_INTEL_URL` | Drive Intel service | `http://drive-intel:8081` | Gateway |
| `VIDEO_AGENT_URL` | Video Agent service | `http://video-agent:8082` | Gateway |
| `ML_SERVICE_URL` | ML Service | `http://ml-service:8003` | Gateway |
| `META_PUBLISHER_URL` | Meta Publisher | `http://meta-publisher:8083` | Gateway |
| `TITAN_CORE_URL` | Titan-Core API | `http://titan-core:8084` | Gateway |

### Application Configuration

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `PORT` | Main app port | `8080` | Cloud Run requires 8080 |
| `DEBUG` | Debug mode | `false` | Set to `true` only in development |
| `LOG_LEVEL` | Logging level | `info` | `error`, `warn`, `info`, `debug` |
| `MAX_VIDEO_SIZE_MB` | Max upload size | `500` | In megabytes |
| `VIDEO_QUALITY` | Video quality | `high` | `low`, `medium`, `high`, `ultra` |
| `TEMP_STORAGE_PATH` | Temp files path | `/tmp/geminivideo` | Writable directory |
| `OUTPUT_STORAGE_PATH` | Output path | `/app/data/outputs` | Writable directory |
| `CONFIG_PATH` | Config directory | `/app/shared/config` | Shared configs |

### ML & Processing

| Variable | Description | Default | Notes |
|----------|-------------|---------|-------|
| `MIN_SAMPLES_FOR_UPDATE` | Min samples for ML | `50` | Before updating weights |
| `LEARNING_RATE` | ML learning rate | `0.01` | Model training |
| `MAX_WEIGHT_DELTA` | Max weight change | `0.1` | Per update |
| `ENABLE_THOMPSON_SAMPLING` | A/B testing | `true` | Variant selection |
| `MIN_CONVERSIONS_FOR_WINNER` | Min conversions | `30` | Before declaring winner |
| `MAX_CONCURRENT_RENDERS` | Concurrent renders | `5` | Titan-Core processing |
| `DEFAULT_NUM_VARIATIONS` | Default variations | `10` | Generated per request |
| `APPROVAL_THRESHOLD` | Approval score | `85.0` | Minimum quality score |

### Feature Flags

| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_ANALYTICS` | Enable analytics | `true` |
| `ENABLE_PERFORMANCE_MONITORING` | Performance monitoring | `true` |
| `ENABLE_MCP_INTEGRATION` | MCP integration | `false` |
| `VITE_ENABLE_ANALYTICS` | Frontend analytics | `true` |
| `VITE_ENABLE_PERFORMANCE` | Frontend performance | `true` |

### Worker Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `DRIVE_INTEL_MAX_WORKERS` | Max Drive Intel workers | `4` |
| `DRIVE_INTEL_BATCH_SIZE` | Batch processing size | `10` |
| `DRIVE_WORKER_CONCURRENCY` | Worker concurrency | `4` |
| `DRIVE_WORKER_REPLICAS` | Worker replicas | `2` |
| `VIDEO_WORKER_CONCURRENCY` | Video worker concurrency | `2` |
| `VIDEO_WORKER_REPLICAS` | Video worker replicas | `2` |

## Environment-Specific Values

### Development

```bash
NODE_ENV=development
VITE_ENV=development
DEBUG=true
LOG_LEVEL=debug
GATEWAY_URL=http://localhost:8080
REDIS_URL=redis://localhost:6379
DATABASE_URL=postgresql://user:pass@localhost:5432/geminivideo
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### Production (Docker Compose)

```bash
NODE_ENV=production
VITE_ENV=production
DEBUG=false
LOG_LEVEL=info
DEPLOYMENT_TARGET=docker-compose
GATEWAY_URL=http://gateway-api:8080
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://user:pass@postgres:5432/geminivideo
```

### Production (Cloud Run)

```bash
NODE_ENV=production
VITE_ENV=production
DEBUG=false
LOG_LEVEL=info
DEPLOYMENT_TARGET=cloud-run
GATEWAY_URL=https://gateway-api-xxxxx-uc.a.run.app
UPSTASH_REDIS_REST_URL=https://xxxxx.upstash.io
SUPABASE_URL=https://xxxxx.supabase.co
```

## Security Guidelines

### Passwords & Secrets
- Minimum 32 characters for production passwords
- Use `openssl rand -base64 64` for JWT_SECRET
- Never use default or placeholder values
- Store production secrets in Secret Manager (GCP, AWS, etc.)

### API Keys
- Rotate keys every 90 days
- Use separate keys for dev/staging/production
- Set up usage alerts and quotas
- Enable IP restrictions where available

### CORS Configuration
- List exact domains (avoid wildcards in production)
- Include both www and non-www versions
- Don't include development URLs in production

### File Permissions
- .env files should be 600 (read/write owner only)
- Never commit .env files to version control
- Add .env* to .gitignore (except .env.example)

## Validation

Run validation script:
```bash
bash scripts/validate-env.sh
```

This checks:
- All required variables are set
- No placeholder values remain
- URLs are properly formatted
- Secrets meet minimum length requirements

## Quick Reference Commands

```bash
# Generate secure JWT secret
openssl rand -base64 64

# Generate secure password
openssl rand -base64 32

# Test database connection
psql "$DATABASE_URL" -c "SELECT 1;"

# Test Redis connection
redis-cli -u "$REDIS_URL" ping

# Validate Gemini API key
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro?key=$GEMINI_API_KEY"

# Check all environment variables
printenv | grep -E "(GEMINI|DATABASE|REDIS|JWT)" | sort
```

## Troubleshooting

### Variable not being read
1. Check file location (.env in correct directory)
2. Verify file format (no spaces around `=`)
3. Restart service after changes
4. Check for typos in variable names

### Connection failures
1. Verify URLs/hosts are correct
2. Check network connectivity
3. Validate credentials
4. Review firewall rules
5. Check service is running

### API key errors
1. Verify key is active
2. Check quota limits
3. Ensure correct project/account
4. Validate key format (no extra whitespace)

## Related Documentation

- [ENV_SETUP_GUIDE.md](./ENV_SETUP_GUIDE.md) - Setup instructions
- [.env.deployment](./.env.deployment) - Master template
- [scripts/setup-env.sh](./scripts/setup-env.sh) - Interactive setup
- [scripts/validate-env.sh](./scripts/validate-env.sh) - Validation script

## Support

For issues with environment configuration:
1. Run validation: `bash scripts/validate-env.sh`
2. Check logs: `docker-compose logs SERVICE_NAME`
3. Test connections: `bash scripts/test-connections.sh`
4. Review this document for correct values

---

Last Updated: 2025-12-02
