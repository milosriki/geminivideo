# Environment Validation System

## 🎯 Overview

Investment-grade environment validation system for the €5M ad platform. This system validates ALL environment variables, API keys, database connections, and service configurations before deployment.

## 📦 Components

### 1. `/scripts/validate-env.py` (Main Validator)

Comprehensive Python script that validates:
- ✅ Database connectivity (PostgreSQL, Supabase)
- ✅ Cache connectivity (Redis, Upstash)
- ✅ AI API keys (Gemini, OpenAI, Anthropic) with live tests
- ✅ Storage access (S3, R2, GCS)
- ✅ Ad platform credentials (Meta, Google Ads, TikTok)
- ✅ Security configuration (JWT, CORS, encryption)
- ✅ Service URLs and endpoints
- ✅ Cloudflare Edge configuration
- ✅ Firebase authentication

**Features:**
- Format validation for all API keys
- Live connectivity tests (optional)
- Placeholder detection
- Machine-readable JSON output
- Human-readable summaries
- Exit codes for CI/CD integration

### 2. `/scripts/validate-env.sh` (Shell Wrapper)

User-friendly bash wrapper that:
- Checks for Python availability
- Falls back to basic validation if Python unavailable
- Provides colored output
- Shows helpful next steps
- Detects CI/CD environments

### 3. `/.env.example.complete` (Complete Reference)

Comprehensive environment file template with:
- **500+ lines** of documented variables
- 24 major configuration sections
- Inline documentation for every variable
- Security best practices
- Validation checklist

**Sections:**
1. Deployment Configuration
2. Database (PostgreSQL, Supabase)
3. Cache (Redis, Upstash)
4. AI Models (Gemini, OpenAI, Anthropic, GPT-4)
5. Video Generation (Runway, Kling, Pika, Sora)
6. Voice APIs (ElevenLabs, OpenAI TTS)
7. Meta/Facebook Ads (8 variables)
8. Google Ads (8 variables)
9. TikTok Ads (6 variables)
10. Google Cloud Platform (15 variables)
11. AWS/S3 Storage (8 variables)
12. Cloudflare R2 (6 variables)
13. Cloudflare Edge/Workers (12 variables)
14. Firebase (10 variables)
15. Security (15 variables)
16. Service URLs (15 variables)
17. Application Config (20 variables)
18. Worker Configuration (12 variables)
19. Monitoring (15 variables)
20. Backup & DR (5 variables)
21. Email/Notifications (10 variables)
22. SSL/TLS (6 variables)
23. Third-party Integrations (8 variables)
24. Development/Testing (8 variables)

### 4. `/docker-compose.override.example.yml`

Production-ready Docker Compose configuration showing:
- How to inject all environment variables
- Volume mounts for secrets and data
- Health check configurations
- Resource limits (CPU, memory)
- Network isolation
- Service scaling
- SSL/TLS setup
- Backup volumes

## 🚀 Quick Start

### Installation

```bash
# Install Python dependencies
pip install -r scripts/requirements-validation.txt

# Or install individually
pip install psycopg2-binary redis boto3 google-generativeai openai anthropic
```

### Basic Usage

```bash
# Validate production environment
bash scripts/validate-env.sh .env.production

# Or use Python directly
python3 scripts/validate-env.py --env-file .env.production
```

### CI/CD Usage

```bash
# Fast validation (skip connectivity tests)
SKIP_CONNECTIVITY=true bash scripts/validate-env.sh .env.production

# JSON output for parsing
python3 scripts/validate-env.py --env-file .env.production --json --output report.json

# Check exit code
if [ $? -eq 0 ]; then
  echo "✅ Validation passed - ready to deploy"
else
  echo "❌ Validation failed - fix errors"
  exit 1
fi
```

## 📋 What Gets Validated

### Environment Variable Checks

| Category | Variables Checked | Validation Type |
|----------|------------------|-----------------|
| Database | `DATABASE_URL`, `POSTGRES_PASSWORD` | Format, connectivity, strength |
| Cache | `REDIS_URL`, `UPSTASH_*` | Format, connectivity, ping test |
| AI APIs | `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` | Format, live API test |
| Storage | `AWS_ACCESS_KEY_ID`, `S3_BUCKET`, `R2_*` | Format, bucket access |
| Meta Ads | `META_APP_ID`, `META_APP_SECRET`, `META_ACCESS_TOKEN`, etc. | Format, length |
| Google Ads | `GOOGLE_CLIENT_ID`, `GOOGLE_DEVELOPER_TOKEN`, etc. | Format, OAuth validation |
| TikTok Ads | `TIKTOK_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_ID` | Format, length |
| Security | `JWT_SECRET`, `CORS_ORIGINS` | Strength, format |
| Cloudflare | `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` | Format, length |

### API Key Format Validation

| Service | Expected Format | Minimum Length |
|---------|----------------|----------------|
| Gemini | Starts with `AI` | 30 chars |
| OpenAI | Starts with `sk-` | 40 chars |
| Anthropic | Starts with `sk-ant-` | 40 chars |
| Meta App ID | Numeric | 10 digits |
| Google Client ID | Ends with `.apps.googleusercontent.com` | - |
| JWT Secret | Any | 32 chars (64 recommended) |

### Connectivity Tests

When `--skip-connectivity` is NOT used:

1. **PostgreSQL**: Connection test, version check
2. **Redis**: Ping test, version info
3. **S3/R2**: Bucket head request
4. **Gemini**: Minimal content generation test
5. **OpenAI**: GPT-3.5-turbo test call
6. **Anthropic**: Claude Haiku test call

## 📊 Output Formats

### Human-Readable (Default)

```
================================================================================
ENVIRONMENT VALIDATION SUMMARY
================================================================================

Total Checks: 45
✓ Passed:     42
✗ Failed:     0
⚠ Warnings:   3
⊘ Skipped:    0

Success Rate: 93.33%

🎉 READY FOR DEPLOYMENT
================================================================================
```

### JSON (CI/CD)

```json
{
  "timestamp": "2025-12-05T10:30:00Z",
  "summary": {
    "total_checks": 45,
    "passed": 42,
    "failed": 0,
    "warnings": 3,
    "skipped": 0,
    "success_rate": 93.33,
    "ready_for_deployment": true
  },
  "by_category": {
    "Database": [...],
    "AI Services": [...],
    "Ad Platforms": [...]
  },
  "all_results": [...]
}
```

## 🔧 Configuration

### Environment File Setup

```bash
# 1. Copy complete example
cp .env.example.complete .env.production

# 2. Fill in required values
nano .env.production

# 3. Validate
bash scripts/validate-env.sh .env.production

# 4. Fix errors and re-validate
```

### Docker Setup

```bash
# 1. Copy Docker override example
cp docker-compose.override.example.yml docker-compose.override.yml

# 2. Customize for your environment
nano docker-compose.override.yml

# 3. Validate environment
bash scripts/validate-env.sh .env.production

# 4. Start services
docker-compose up -d
```

## 🎯 Integration Examples

### GitHub Actions

```yaml
- name: Validate Environment
  run: |
    pip install -r scripts/requirements-validation.txt
    python3 scripts/validate-env.py \
      --env-file .env.production \
      --skip-connectivity \
      --json \
      --output validation-report.json

- name: Check if ready for deployment
  run: |
    READY=$(cat validation-report.json | jq -r '.summary.ready_for_deployment')
    if [ "$READY" != "true" ]; then
      echo "❌ Environment validation failed"
      cat validation-report.json | jq '.summary'
      exit 1
    fi
```

### GitLab CI

```yaml
validate:
  stage: validate
  script:
    - pip install -r scripts/requirements-validation.txt
    - python3 scripts/validate-env.py --env-file .env.production --json
  artifacts:
    reports:
      junit: validation-report.json
```

### Pre-deployment Hook

```bash
#!/bin/bash
# deploy.sh

echo "🔍 Validating environment..."

if ! bash scripts/validate-env.sh .env.production; then
    echo "❌ Environment validation failed!"
    exit 1
fi

echo "✅ Environment validated - deploying..."
docker-compose up -d
```

## 🛡️ Security Features

### Placeholder Detection

Automatically detects and rejects placeholder values:
- `your_api_key_here`
- `CHANGE_ME`
- `YOUR_*`
- `xxxx`, `XXXX`
- `*_here`

### Password Strength

- Minimum length enforcement (16-64 chars depending on use)
- No weak passwords
- Recommendations for generation

### Secret Validation

- JWT secrets: 32+ characters
- API keys: Format-specific validation
- Tokens: Length validation
- Credentials: Strength checks

## 📈 Performance

### Validation Speed

- **Basic checks**: ~100ms (format validation only)
- **With connectivity**: ~5-10 seconds (includes API calls)
- **Skip connectivity**: ~500ms (recommended for CI/CD)

### Resource Usage

- **Memory**: < 50MB
- **CPU**: Minimal (mostly I/O bound)
- **Network**: ~5-10 API calls if connectivity tests enabled

## 🐛 Troubleshooting

### Common Issues

#### "Python not found"
```bash
# Install Python 3.7+
apt-get install python3 python3-pip  # Debian/Ubuntu
yum install python3 python3-pip      # RHEL/CentOS
brew install python3                 # macOS
```

#### "psycopg2 not installed"
```bash
pip install psycopg2-binary
# Or use Docker
docker run --rm -v $(pwd):/app python:3.10 \
  bash -c "pip install -r /app/scripts/requirements-validation.txt"
```

#### "API test failed"
- Check internet connectivity
- Verify API keys are valid
- Check API quotas/rate limits
- Use `--skip-connectivity` to bypass tests

#### "Database connection failed"
- Verify `DATABASE_URL` format
- Check database is running
- Verify credentials
- Test connectivity: `psql $DATABASE_URL`

## 📚 Documentation

- **Complete Guide**: [docs/ENVIRONMENT_VALIDATION.md](../docs/ENVIRONMENT_VALIDATION.md)
- **Environment Reference**: [.env.example.complete](../.env.example.complete)
- **Docker Configuration**: [docker-compose.override.example.yml](../docker-compose.override.example.yml)

## 🔄 Continuous Validation

### Scheduled Validation (Cron)

```bash
# Add to crontab
0 */6 * * * cd /app && python3 scripts/validate-env.py --skip-connectivity --json > /var/log/validation.json
```

### Monitoring Integration

```python
# Send to monitoring service
python3 scripts/validate-env.py --json | \
  curl -X POST https://monitoring.example.com/validation \
       -H "Content-Type: application/json" \
       -d @-
```

## 📝 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | One or more validations failed |

## 🆘 Support

If validation fails:

1. **Read the error messages** - They're specific and actionable
2. **Check the format** - Ensure values match expected patterns
3. **Verify credentials** - Test API keys in their respective dashboards
4. **Review documentation** - Check `.env.example.complete` for examples
5. **Run with verbose output** - Add `DEBUG=true` for more details

## 🎓 Best Practices

1. **Always validate before deployment**
   ```bash
   bash scripts/validate-env.sh .env.production && deploy.sh
   ```

2. **Use CI/CD integration**
   - Validate on every push to main/production
   - Block deployment if validation fails

3. **Keep secrets secure**
   - Never commit `.env` files
   - Use secret managers in production
   - Rotate secrets regularly

4. **Document custom variables**
   - Add to `.env.example.complete`
   - Update validation script if needed

5. **Monitor validation results**
   - Track success rates over time
   - Alert on failures
   - Review warnings regularly

## 📄 License

Part of the GeminiVideo Ad Platform - €5M Investment Grade System

---

**Created by**: AGENT 51: ENVIRONMENT VALIDATOR
**Last Updated**: 2025-12-05
**Version**: 1.0.0
