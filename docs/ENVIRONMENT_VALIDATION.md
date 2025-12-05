# Environment Validation Guide

## Overview

This guide covers the comprehensive environment validation system for the €5M investment-grade ad platform. The validation system ensures all required environment variables, API keys, and service configurations are properly set before deployment.

## Quick Start

### 1. Basic Validation

```bash
# Validate default production environment
bash scripts/validate-env.sh

# Validate specific env file
bash scripts/validate-env.sh .env.production

# Skip connectivity tests (faster, for CI/CD)
SKIP_CONNECTIVITY=true bash scripts/validate-env.sh
```

### 2. Python Validator (Advanced)

```bash
# Human-readable output
python3 scripts/validate-env.py --env-file .env.production

# JSON output (for CI/CD)
python3 scripts/validate-env.py --env-file .env.production --json

# Save results to file
python3 scripts/validate-env.py --env-file .env.production --json --output validation-report.json

# Skip connectivity tests
python3 scripts/validate-env.py --env-file .env.production --skip-connectivity
```

## What Gets Validated

### 1. Database Configuration ✓
- **PostgreSQL**: Connection string format, password strength
- **Connectivity**: Live connection test, version check
- **Supabase**: URL format, API keys (if used)

### 2. Cache/Redis ✓
- **Redis URL**: Connection string validation
- **Upstash**: REST API credentials (if used)
- **Connectivity**: Ping test, version check

### 3. AI API Keys ✓
- **Gemini API**: Format validation (starts with `AI`), live API test
- **OpenAI API**: Format validation (starts with `sk-`), GPT-3.5 test call
- **Anthropic API**: Format validation (starts with `sk-ant-`), Claude test call

### 4. Storage (S3/R2) ✓
- **AWS Credentials**: Access key ID and secret access key
- **Bucket Access**: Live bucket head request
- **R2 Configuration**: Cloudflare R2 endpoint and credentials

### 5. Ad Platform Credentials ✓

#### Meta/Facebook Ads
- `META_APP_ID`: Numeric format, 10+ digits
- `META_APP_SECRET`: Minimum 32 characters
- `META_ACCESS_TOKEN`: Minimum 50 characters
- `META_AD_ACCOUNT_ID`: Format `act_XXXXXXXXXX`
- `META_PAGE_ID`: Numeric
- `META_PIXEL_ID`: Numeric
- `META_CONVERSION_API_TOKEN`: CAPI token

#### Google Ads
- `GOOGLE_CLIENT_ID`: Format `*.apps.googleusercontent.com`
- `GOOGLE_CLIENT_SECRET`: Valid secret
- `GOOGLE_DEVELOPER_TOKEN`: Developer token
- `GOOGLE_REFRESH_TOKEN`: OAuth refresh token
- `GOOGLE_ADS_CUSTOMER_ID`: 10-digit customer ID

#### TikTok Ads
- `TIKTOK_ACCESS_TOKEN`: Valid access token
- `TIKTOK_ADVERTISER_ID`: Advertiser account ID
- `TIKTOK_APP_ID`: App ID

### 6. Cloudflare Edge ✓
- `CLOUDFLARE_ACCOUNT_ID`: 32-character account ID
- `CLOUDFLARE_API_TOKEN`: Minimum 40 characters
- Stream and Images configuration (optional)

### 7. Security ✓
- **JWT Secret**: Minimum 32 characters (64+ recommended)
- **CORS Origins**: Valid domain list
- **API Secrets**: Proper length and format

### 8. Service URLs ✓
- **Internal URLs**: Docker network URLs
- **External URLs**: Public API endpoints
- **Format Validation**: Proper URL scheme

## Validation Results

### Success Output
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

### Failure Output
```
================================================================================
FAILED CHECKS (must fix):
================================================================================
✗ [AI Services] GEMINI_API_KEY: Invalid format (should start with "AI")
✗ [Database] POSTGRES_PASSWORD: Too short (min 16 chars, got 8)
✗ [Security] JWT_SECRET: Placeholder value detected
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Validate Environment

on:
  push:
    branches: [main, production]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install psycopg2-binary redis boto3 google-generativeai openai anthropic

      - name: Create env file from secrets
        run: |
          echo "DATABASE_URL=${{ secrets.DATABASE_URL }}" >> .env.production
          echo "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" >> .env.production
          # ... add all other secrets

      - name: Validate environment
        run: |
          python3 scripts/validate-env.py \
            --env-file .env.production \
            --skip-connectivity \
            --json \
            --output validation-report.json

      - name: Upload validation report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: validation-report
          path: validation-report.json
```

### GitLab CI

```yaml
validate-environment:
  stage: test
  image: python:3.10
  before_script:
    - pip install psycopg2-binary redis boto3 google-generativeai openai anthropic
  script:
    - |
      cat > .env.production << EOF
      DATABASE_URL=${DATABASE_URL}
      GEMINI_API_KEY=${GEMINI_API_KEY}
      # ... more variables
      EOF
    - python3 scripts/validate-env.py --env-file .env.production --json
  artifacts:
    reports:
      junit: validation-report.json
```

### Docker Pre-deployment

```bash
# In your deployment script
#!/bin/bash

echo "Validating environment before deployment..."

if ! bash scripts/validate-env.sh .env.production; then
    echo "❌ Environment validation failed!"
    echo "Fix the errors above before deploying."
    exit 1
fi

echo "✅ Environment validated successfully!"
echo "Proceeding with deployment..."

docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

## Environment File Setup

### Step 1: Copy Example File

```bash
# Copy the complete example
cp .env.example.complete .env.production

# Or copy existing example
cp .env.production.example .env.production
```

### Step 2: Fill Required Variables

Minimum required variables for deployment:

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@host:5432/db
POSTGRES_PASSWORD=your_secure_password_min_32_chars

# Cache (REQUIRED)
REDIS_URL=redis://redis:6379

# AI (REQUIRED - at least Gemini)
GEMINI_API_KEY=AIza...your_key_here

# Security (REQUIRED)
JWT_SECRET=$(openssl rand -base64 64)
CORS_ORIGINS=https://your-domain.com
```

### Step 3: Validate Configuration

```bash
# Run validation
bash scripts/validate-env.sh .env.production

# Fix any errors
nano .env.production

# Validate again
bash scripts/validate-env.sh .env.production
```

## Common Issues and Solutions

### Issue: "Invalid API key format"

**Solution**: Check that API keys match expected prefixes:
- Gemini: `AIza...`
- OpenAI: `sk-...`
- Anthropic: `sk-ant-...`

### Issue: "Database connection failed"

**Solutions**:
1. Check DATABASE_URL format: `postgresql://user:password@host:port/db`
2. Verify database is running: `docker-compose ps postgres`
3. Check credentials: `psql $DATABASE_URL -c "SELECT 1"`
4. Verify network connectivity

### Issue: "Placeholder value detected"

**Solution**: Replace placeholder values like:
- `your_api_key_here` → Actual API key
- `CHANGE_ME` → Real secure password
- `your-project-id` → Actual project ID

### Issue: "JWT_SECRET too short"

**Solution**: Generate secure secret:
```bash
# Generate 64-byte secret (recommended)
openssl rand -base64 64

# Or 32-byte minimum
openssl rand -base64 32
```

### Issue: "psycopg2 not installed"

**Solution**: Install Python dependencies:
```bash
pip install psycopg2-binary redis boto3 google-generativeai openai anthropic
```

Or use Docker:
```bash
docker run --rm -v $(pwd):/app -w /app python:3.10 \
  bash -c "pip install -r scripts/requirements.txt && python3 scripts/validate-env.py"
```

## Advanced Configuration

### Skip Specific Validations

```python
# Modify scripts/validate-env.py
# Comment out sections you want to skip:

# Skip S3 validation
# self.test_s3_access()

# Skip AI API tests
# self.test_gemini_api()
# self.test_openai_api()
```

### Custom Validation Rules

```python
# Add custom validation in scripts/validate-env.py

def validate_custom_service(self):
    """Validate custom service credentials"""
    api_key = os.getenv('CUSTOM_API_KEY')

    if not api_key:
        self.add_result('Custom Service', 'Custom', 'skip', 'Not configured')
        return True

    # Your validation logic here
    if len(api_key) < 32:
        self.add_result('CUSTOM_API_KEY', 'Custom', 'fail', 'Too short')
        return False

    self.add_result('CUSTOM_API_KEY', 'Custom', 'pass', 'Valid')
    return True

# Call in validate_all():
self.validate_custom_service()
```

### Export Validation Report

```bash
# Generate JSON report
python3 scripts/validate-env.py \
  --env-file .env.production \
  --json \
  --output validation-report.json

# Parse with jq
cat validation-report.json | jq '.summary'

# Check if ready for deployment
if [ $(cat validation-report.json | jq -r '.summary.ready_for_deployment') = "true" ]; then
  echo "✅ Ready to deploy!"
else
  echo "❌ Not ready - failed: $(cat validation-report.json | jq '.summary.failed')"
fi
```

## Security Best Practices

### 1. Never Commit Secrets

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.production" >> .gitignore
echo ".env.local" >> .gitignore
echo "validation-report.json" >> .gitignore
```

### 2. Use Secret Managers in Production

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name geminivideo/production/database \
  --secret-string '{"password":"your-password"}'

# Google Secret Manager
gcloud secrets create database-password --data-file=- <<< "your-password"

# HashiCorp Vault
vault kv put secret/geminivideo/database password="your-password"
```

### 3. Rotate Secrets Regularly

```bash
# Generate new JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 64)

# Update in environment
sed -i "s/JWT_SECRET=.*/JWT_SECRET=$NEW_JWT_SECRET/" .env.production

# Validate
bash scripts/validate-env.sh .env.production

# Restart services
docker-compose restart
```

### 4. Use Environment-Specific Files

```
.env.development       # Local development
.env.staging           # Staging environment
.env.production        # Production environment
.env.test              # Automated testing
```

## Monitoring and Alerts

### Set Up Validation Monitoring

```bash
# Add to crontab - validate every hour
0 * * * * cd /app && python3 scripts/validate-env.py --skip-connectivity --json --output /tmp/validation.json && curl -X POST https://your-monitoring.com/api/validation -d @/tmp/validation.json
```

### Slack Notifications

```python
# Add to scripts/validate-env.py
import requests

def send_slack_notification(summary):
    if summary['summary']['failed'] > 0:
        webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        if webhook_url:
            requests.post(webhook_url, json={
                'text': f"❌ Environment validation failed: {summary['summary']['failed']} checks failed"
            })
```

## Support

For issues with environment validation:

1. Check this documentation
2. Review validation output carefully
3. Verify environment file syntax
4. Check service logs: `docker-compose logs [service]`
5. Run with debug: `DEBUG=true bash scripts/validate-env.sh`

## See Also

- [.env.example.complete](../.env.example.complete) - Complete environment variable reference
- [docker-compose.override.example.yml](../docker-compose.override.example.yml) - Docker Compose configuration
- [Deployment Guide](./DEPLOYMENT.md) - Full deployment documentation
