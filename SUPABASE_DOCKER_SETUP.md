# Supabase & Docker Extensions Setup Guide

**Date:** 2025-12-10  
**Purpose:** Complete setup for Supabase database and Docker MCP extensions

---

## 📋 SUPABASE SETUP

### **1. Supabase Project Setup**

#### **Option A: Local Development (Supabase CLI)**

```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Initialize Supabase (if not already done)
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo
supabase init

# Start local Supabase
supabase start

# This will give you:
# - API URL: http://localhost:54321
# - DB URL: postgresql://postgres:postgres@localhost:54322/postgres
# - Studio URL: http://localhost:54323
```

#### **Option B: Cloud (Supabase Cloud)**

1. Go to https://supabase.com/dashboard
2. Create new project: `geminivideo`
3. Get your credentials:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon Key: `eyJhbGc...`
   - Service Role Key: `eyJhbGc...` (keep secret!)

---

### **2. Run Database Schema**

#### **For Local Supabase:**

```bash
# Apply schema
supabase db reset

# Or manually via SQL Editor (Studio)
# Go to: http://localhost:54323 → SQL Editor
# Copy and paste: supabase/SCHEMA.sql
```

#### **For Cloud Supabase:**

1. Go to Supabase Dashboard → SQL Editor
2. Copy contents of `supabase/SCHEMA.sql`
3. Paste and run
4. Verify tables created:
   - `profiles`
   - `campaigns`
   - `blueprints`
   - `render_jobs`
   - `videos`
   - `ad_performance`
   - `video_analysis`
   - `campaign_insights`

---

### **3. Environment Variables**

Add to your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=http://localhost:54321  # Local
# OR
SUPABASE_URL=https://xxxxx.supabase.co  # Cloud

SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here  # For admin operations

# Database (if using Supabase DB)
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres  # Local
# OR
DATABASE_URL=postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres  # Cloud
```

---

### **4. Add Supabase to Docker Compose**

Add this service to `docker-compose.yml`:

```yaml
  supabase:
    image: supabase/postgres:15.1.0.147
    container_name: geminivideo-supabase-db
    environment:
      POSTGRES_HOST: /var/run/postgresql
      POSTGRES_PORT: 5432
      POSTGRES_DB: postgres
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${SUPABASE_DB_PASSWORD:-postgres}
    ports:
      - "54322:5432"  # Supabase DB port
    volumes:
      - supabase_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - geminivideo-network

  supabase-studio:
    image: supabase/studio:20231218-0b97c34
    container_name: geminivideo-supabase-studio
    environment:
      SUPABASE_URL: http://localhost:54321
      STUDIO_PG_META_URL: http://postgres-meta:8080
      POSTGRES_PASSWORD: ${SUPABASE_DB_PASSWORD:-postgres}
    ports:
      - "54323:3000"  # Supabase Studio
    depends_on:
      - supabase
    restart: unless-stopped
    networks:
      - geminivideo-network

volumes:
  # ... existing volumes ...
  supabase_data:
```

**OR** use Supabase CLI locally (recommended):

```bash
# Start Supabase locally
supabase start

# This runs all Supabase services in Docker automatically
```

---

## 🐳 DOCKER EXTENSIONS (MCP SERVERS)

### **Recommended MCP Extensions for GeminiVideo:**

Based on your Docker Desktop setup, here are useful MCP extensions:

#### **1. GitHub Official MCP Server** ✅ (Already installed)

**Purpose:** GitHub integration for code management  
**Docker Image:** `ghcr.io/github/github-mcp-server`  
**Use Cases:**
- Create/update GitHub issues
- Manage pull requests
- Access repository files
- Code search and analysis

**Configuration:**
```bash
# In Docker Desktop → Extensions → GitHub Official
# Add GitHub Personal Access Token:
# Settings → Developer settings → Personal access tokens → Generate
# Scopes needed: repo, workflow, read:org
```

---

#### **2. Supabase MCP Server** (Recommended)

**Purpose:** Direct Supabase database access  
**Docker Image:** `supabase/mcp-server` (if available)  
**Use Cases:**
- Query database directly
- Run migrations
- Manage tables
- Access real-time subscriptions

**Setup:**
```bash
# Add to Docker Desktop Extensions
# Configure with:
# - SUPABASE_URL
# - SUPABASE_SERVICE_ROLE_KEY
```

---

#### **3. Supadata MCP Server** (For Video/Web Scraping)

**Purpose:** Video & web scraping (as shown in your image)  
**Docker Image:** `ghcr.io/supadata-ai/mcp`  
**Use Cases:**
- YouTube video scraping
- TikTok content extraction
- Web scraping
- Transcript generation
- Whisper integration

**Setup:**
```bash
# Add extension in Docker Desktop
# Repository: https://github.com/supadata-ai/mcp
# No special config needed (uses public API)
```

---

#### **4. PostgreSQL MCP Server** (For Direct DB Access)

**Purpose:** Direct PostgreSQL queries  
**Docker Image:** `postgres-mcp-server` (if available)  
**Use Cases:**
- Run SQL queries
- Database schema management
- Performance monitoring

---

### **How to Add MCP Extensions in Docker Desktop:**

1. Open Docker Desktop
2. Go to **Extensions** tab
3. Click **"Add Extension"** or **"Browse Marketplace"**
4. Search for MCP server you want
5. Click **"Install"**
6. Configure with required secrets/API keys
7. Restart Docker Desktop if needed

---

## 🔧 COMPLETE SETUP CHECKLIST

### **Supabase:**
- [ ] Install Supabase CLI OR create cloud project
- [ ] Run `supabase/SCHEMA.sql` in database
- [ ] Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
- [ ] Test connection with `supabase_connector.py`
- [ ] Verify tables created in Supabase Studio

### **Docker Extensions:**
- [ ] GitHub Official MCP (already installed ✅)
- [ ] Configure GitHub Personal Access Token
- [ ] Add Supadata MCP (for video scraping)
- [ ] Add PostgreSQL MCP (optional, for direct DB access)
- [ ] Test MCP connections

### **Integration:**
- [ ] Update `docker-compose.yml` with Supabase (if using local)
- [ ] Update service environment variables
- [ ] Test Supabase connector in services
- [ ] Verify data persistence

---

## 🚀 QUICK START

### **1. Start Supabase Locally:**

```bash
# Install Supabase CLI
brew install supabase/tap/supabase

# Start Supabase
cd /Users/milosvukovic/Downloads/geminivideo/geminivideo
supabase start

# This will output:
# API URL: http://localhost:54321
# DB URL: postgresql://postgres:postgres@localhost:54322/postgres
# Studio URL: http://localhost:54323
```

### **2. Run Schema:**

```bash
# Via Supabase Studio (recommended)
# Open: http://localhost:54323
# Go to: SQL Editor
# Paste: supabase/SCHEMA.sql
# Click: Run

# OR via CLI
supabase db reset
```

### **3. Add Environment Variables:**

```bash
# Add to .env file
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=<from supabase start output>
SUPABASE_SERVICE_ROLE_KEY=<from supabase start output>
```

### **4. Add Docker Extensions:**

1. Open Docker Desktop
2. Go to Extensions
3. Add **Supadata MCP** (for video scraping)
4. Configure **GitHub Official** with token

---

## 📊 VERIFICATION

### **Test Supabase Connection:**

```python
# Test in Python
from services.titan-core.services.supabase_connector import supabase_connector

if supabase_connector.enabled:
    print("✅ Supabase connected!")
    # Test save
    supabase_connector.save_analysis("test.mp4", {"test": "data"})
else:
    print("❌ Supabase not configured")
```

### **Test MCP Extensions:**

In Docker Desktop → Extensions:
- Check status: All should show "Running"
- Check logs: No errors
- Test tools: Use MCP tools in Cursor/Claude

---

## 🎯 NEXT STEPS

1. **Start Supabase:** `supabase start`
2. **Run Schema:** Copy `supabase/SCHEMA.sql` to SQL Editor
3. **Add to .env:** Set Supabase credentials
4. **Add Extensions:** Supadata MCP in Docker Desktop
5. **Test:** Verify connection and data persistence

**Everything is ready to go!** 🚀

