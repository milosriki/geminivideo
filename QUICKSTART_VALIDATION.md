# Environment Validation - Quick Start Guide

## 🚀 5-Minute Setup

### Step 1: Copy Environment File (30 seconds)

```bash
# Use the complete example as your starting point
cp .env.example.complete .env.production
```

### Step 2: Fill Required Values (3 minutes)

Edit `.env.production` and fill in these **REQUIRED** fields:

```bash
# Database (REQUIRED)
DATABASE_URL=postgresql://user:password@host:5432/db
POSTGRES_PASSWORD=your_secure_password_min_32_chars

# AI (REQUIRED)
GEMINI_API_KEY=AIza...your_actual_key

# Security (REQUIRED)
JWT_SECRET=$(openssl rand -base64 64)
CORS_ORIGINS=https://your-domain.com
```

### Step 3: Validate (30 seconds)

```bash
# Install dependencies (one-time)
pip install -r scripts/requirements-validation.txt

# Run validation
bash scripts/validate-env.sh .env.production
```

### Step 4: Fix Errors (1 minute)

If validation fails, fix the reported issues:

```bash
# Edit the file
nano .env.production

# Run validation again
bash scripts/validate-env.sh .env.production
```

### Step 5: Deploy ✅

```bash
# Once validation passes
docker-compose up -d
```

---

## 📋 What Was Created

### Core Files

1. **`/scripts/validate-env.py`** (811 lines)
   - Main validation engine
   - Tests 100+ environment variables
   - Live API connectivity tests
   - JSON output for CI/CD

2. **`/scripts/validate-env.sh`** (174 lines)
   - User-friendly wrapper
   - Colored output
   - CI/CD detection
   - Helpful error messages

3. **`.env.example.complete`** (591 lines)
   - Complete environment reference
   - 24 configuration sections
   - 100+ documented variables
   - Security best practices

4. **`docker-compose.override.example.yml`** (602 lines)
   - Production Docker config
   - All 12 services configured
   - Volume mounts for secrets
   - Health checks and scaling

### Documentation

5. **`/docs/ENVIRONMENT_VALIDATION.md`**
   - Complete user guide
   - CI/CD integration examples
   - Troubleshooting

6. **`/scripts/ENV_VALIDATION_README.md`**
   - Technical reference
   - API documentation
   - Best practices

7. **`AGENT_51_DELIVERY_REPORT.md`**
   - Complete delivery summary
   - Statistics and metrics

---

## 💡 Common Commands

```bash
# Basic validation
bash scripts/validate-env.sh

# Specific env file
bash scripts/validate-env.sh .env.production

# Fast mode (skip connectivity tests)
SKIP_CONNECTIVITY=true bash scripts/validate-env.sh

# JSON output
python3 scripts/validate-env.py --env-file .env.production --json

# Save report
python3 scripts/validate-env.py --json --output report.json

# Check if ready for deployment
python3 scripts/validate-env.py --json | jq -r '.summary.ready_for_deployment'
```

---

## ✅ What Gets Validated

### Required Variables
- ✅ **Database**: PostgreSQL connection, password strength
- ✅ **AI APIs**: Gemini API key format and connectivity
- ✅ **Security**: JWT secret strength, CORS configuration

### Optional but Recommended
- ✅ **Cache**: Redis/Upstash connectivity
- ✅ **Storage**: S3/R2 bucket access
- ✅ **AI APIs**: OpenAI, Anthropic (for multi-model)
- ✅ **Ad Platforms**: Meta, Google Ads, TikTok credentials
- ✅ **Edge**: Cloudflare Workers configuration

### Validation Types
- ✅ **Format**: API key prefixes, URL schemes, email formats
- ✅ **Strength**: Password length, secret complexity
- ✅ **Connectivity**: Live database, Redis, API tests
- ✅ **Security**: Placeholder detection, weak password detection

---

## 🔧 Quick Fixes

### "Invalid API key format"
```bash
# Gemini keys start with "AIza"
GEMINI_API_KEY=AIza...

# OpenAI keys start with "sk-"
OPENAI_API_KEY=sk-...

# Anthropic keys start with "sk-ant-"
ANTHROPIC_API_KEY=sk-ant-...
```

### "JWT_SECRET too short"
```bash
# Generate secure secret (64 bytes recommended)
JWT_SECRET=$(openssl rand -base64 64)
```

### "Database connection failed"
```bash
# Check format
DATABASE_URL=postgresql://user:password@host:port/database

# Test manually
psql $DATABASE_URL -c "SELECT 1"
```

### "Placeholder detected"
```bash
# Replace ALL placeholder values:
# ❌ your_api_key_here
# ❌ CHANGE_ME
# ❌ your-project-id
# ✅ Actual values
```

---

## 🎯 CI/CD Integration

### GitHub Actions

```yaml
- name: Validate Environment
  run: |
    pip install -r scripts/requirements-validation.txt
    python3 scripts/validate-env.py \
      --env-file .env.production \
      --skip-connectivity \
      --json
```

### Pre-deployment Hook

```bash
#!/bin/bash
if ! bash scripts/validate-env.sh .env.production; then
    echo "❌ Validation failed"
    exit 1
fi
docker-compose up -d
```

---

## 📚 Full Documentation

- **User Guide**: [docs/ENVIRONMENT_VALIDATION.md](docs/ENVIRONMENT_VALIDATION.md)
- **Technical Reference**: [scripts/ENV_VALIDATION_README.md](scripts/ENV_VALIDATION_README.md)
- **Environment Reference**: [.env.example.complete](.env.example.complete)
- **Docker Config**: [docker-compose.override.example.yml](docker-compose.override.example.yml)
- **Delivery Report**: [AGENT_51_DELIVERY_REPORT.md](AGENT_51_DELIVERY_REPORT.md)

---

## 🆘 Get Help

1. Read error messages carefully (they're specific and actionable)
2. Check `.env.example.complete` for correct formats
3. Review documentation in `/docs/ENVIRONMENT_VALIDATION.md`
4. Run with verbose output: `DEBUG=true bash scripts/validate-env.sh`

---

**Ready to deploy? Run validation first!**

```bash
bash scripts/validate-env.sh .env.production && echo "✅ Ready!" || echo "❌ Fix errors above"
```
