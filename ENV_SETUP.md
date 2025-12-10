# 🔐 Environment Variables Setup

## 📋 Overview

All configuration is managed via environment variables. **Nothing is hardcoded.**

---

## 📁 Environment Files

### 1. `.env` (Base Configuration)
- **Purpose:** Default configuration for all environments
- **Status:** Committed to Git (with `.example` values)
- **Usage:** Base config, can be overridden

### 2. `.env.local` (Local Development)
- **Purpose:** Local development overrides
- **Status:** **NOT committed** (in `.gitignore`)
- **Usage:** Overrides `.env` for local dev
- **Get values from:** `supabase start` output

### 3. `supabase/.env.prod` (Production Secrets)
- **Purpose:** Edge Function secrets for production
- **Status:** **NOT committed** (in `.gitignore`)
- **Usage:** `supabase secrets set --env-file supabase/.env.prod`

### 4. GitHub Secrets (CI/CD)
- **Purpose:** Production deployment secrets
- **Location:** GitHub → Settings → Secrets → Actions
- **Usage:** Auto-loaded in GitHub Actions

---

## 🚀 Quick Setup

### 1. Create `.env` from example:
```bash
cp .env.example .env
```

### 2. Create `.env.local` for local dev:
```bash
cp .env.local.example .env.local
```

### 3. Get local Supabase values:
```bash
supabase start
# Copy the printed values to .env.local
```

### 4. Load environment variables:
```bash
source load-env.sh
# Or in your shell:
export $(grep -v '^#' .env.local | xargs)
```

---

## 📊 Required Environment Variables

### **Supabase (Required)**
```bash
SUPABASE_URL=http://localhost:54321  # Local or cloud URL
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
SUPABASE_PROJECT_REF=your_project_ref
SUPABASE_ACCESS_TOKEN=your_access_token
SUPABASE_DB_URL=postgresql://...
```

### **Database (Required)**
```bash
POSTGRES_USER=geminivideo
POSTGRES_PASSWORD=changeme
POSTGRES_DB=geminivideo
DATABASE_URL=postgresql://...
```

### **Redis (Required)**
```bash
REDIS_URL=redis://redis:6379
```

### **AI APIs (Optional)**
```bash
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

### **Ad Platforms (Optional)**
```bash
META_ACCESS_TOKEN=your_token
GOOGLE_CLIENT_ID=your_id
TIKTOK_ACCESS_TOKEN=your_token
```

---

## 🔄 Loading Environment Variables

### **In Shell Scripts:**
```bash
# Load all env files
source load-env.sh

# Or manually
export $(grep -v '^#' .env.local | xargs)
```

### **In Node.js/TypeScript:**
```typescript
import dotenv from 'dotenv';

// Load .env.local first (highest priority)
dotenv.config({ path: '.env.local' });
// Then .env (base config)
dotenv.config({ path: '.env' });
```

### **In Python:**
```python
from dotenv import load_dotenv
import os

# Load .env.local first
load_dotenv('.env.local')
# Then .env
load_dotenv('.env')

# Access
supabase_url = os.getenv('SUPABASE_URL')
```

### **In Docker:**
```yaml
# docker-compose.yml
services:
  gateway-api:
    env_file:
      - .env.local  # Highest priority
      - .env        # Base config
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - DATABASE_URL=${DATABASE_URL}
```

---

## 🔐 GitHub Secrets Setup

Go to: `https://github.com/milosriki/geminivideo/settings/secrets/actions`

### **Required Secrets:**
| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `SUPABASE_ACCESS_TOKEN` | Supabase access token | Dashboard → Account → Access Tokens |
| `SUPABASE_PROJECT_REF` | Project reference ID | Dashboard → Project Settings → General |
| `SUPABASE_DB_URL` | Database connection string | Dashboard → Settings → Database → Connection string |
| `SUPABASE_URL` | Supabase API URL | Dashboard → Project Settings → API |
| `SUPABASE_ANON_KEY` | Anonymous key | Dashboard → Project Settings → API |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key | Dashboard → Project Settings → API |

### **Optional Secrets (if using in CI/CD):**
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `META_ACCESS_TOKEN`
- `GOOGLE_CLIENT_ID`
- etc.

---

## 🎯 Environment Priority

**Highest to Lowest:**
1. `.env.local` (local overrides)
2. `.env` (base config)
3. `supabase/.env.prod` (function secrets)
4. System environment variables
5. GitHub Secrets (CI/CD only)

---

## ✅ Verification

### **Check if variables are loaded:**
```bash
# Load env
source load-env.sh

# Verify
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
```

### **Test in code:**
```typescript
console.log('SUPABASE_URL:', process.env.SUPABASE_URL);
console.log('DATABASE_URL:', process.env.DATABASE_URL);
```

---

## 🚨 Security Best Practices

1. **Never commit `.env` files with real values**
   - Use `.env.example` with placeholder values
   - `.env.local` and `.env.prod` are in `.gitignore`

2. **Use different keys for different environments**
   - Local: Get from `supabase start`
   - Staging: Separate Supabase project
   - Production: Production Supabase project

3. **Rotate secrets regularly**
   - Update in Supabase Dashboard
   - Update in GitHub Secrets
   - Update in `.env.local` (local dev)

4. **Use GitHub Secrets for CI/CD**
   - Never hardcode in workflows
   - Use `${{ secrets.SECRET_NAME }}`

---

## 📚 Examples

### **Local Development:**
```bash
# .env.local
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_URL=postgresql://postgres:postgres@localhost:54322/postgres
```

### **Production (GitHub Secrets):**
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_DB_URL=postgresql://postgres:[password]@db.your-project.supabase.co:5432/postgres
```

### **Edge Functions:**
```bash
# supabase/.env.prod
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key

# Set in Supabase
supabase secrets set --env-file supabase/.env.prod
```

---

## 🔄 Migration from Hardcoded Values

If you have hardcoded values:

1. **Find hardcoded values:**
   ```bash
   grep -r "localhost:54321" services/
   grep -r "your_key_here" services/
   ```

2. **Replace with env vars:**
   ```typescript
   // Before
   const supabaseUrl = "http://localhost:54321";
   
   // After
   const supabaseUrl = process.env.SUPABASE_URL || "http://localhost:54321";
   ```

3. **Update all services:**
   - Gateway API
   - ML Service
   - Video Agent
   - Drive Intel
   - etc.

---

## ✅ Checklist

- [ ] `.env.example` created with all variables
- [ ] `.env.local` created (gitignored)
- [ ] `supabase/.env.prod` created (gitignored)
- [ ] GitHub Secrets set (6 required secrets)
- [ ] All services use `process.env.*` instead of hardcoded
- [ ] `load-env.sh` script works
- [ ] Docker Compose uses `env_file`
- [ ] CI/CD uses GitHub Secrets

---

**Everything is now in environment variables!** ✅

