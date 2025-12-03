# 🚀 DEPLOY NOW - 3 Simple Steps

Everything is configured! Just follow these steps:

---

## STEP 1: Set Up Database (5 min)

1. Go to **https://supabase.com** → Your project → **SQL Editor**
2. Copy and paste this SQL:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    product_name VARCHAR(255) NOT NULL,
    offer TEXT NOT NULL,
    target_avatar VARCHAR(255),
    pain_points JSONB DEFAULT '[]',
    desires JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'draft',
    total_generated INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Blueprints table
CREATE TABLE IF NOT EXISTS blueprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    title VARCHAR(255),
    hook_text TEXT,
    hook_type VARCHAR(100),
    script_json JSONB,
    council_score FLOAT,
    predicted_roas FLOAT,
    confidence FLOAT,
    verdict VARCHAR(20),
    rank INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Render jobs table
CREATE TABLE IF NOT EXISTS render_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blueprint_id UUID REFERENCES blueprints(id),
    campaign_id UUID REFERENCES campaigns(id),
    platform VARCHAR(50),
    quality VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    progress FLOAT DEFAULT 0,
    current_stage VARCHAR(100),
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id),
    blueprint_id UUID REFERENCES blueprints(id),
    render_job_id UUID REFERENCES render_jobs(id),
    storage_path TEXT,
    storage_url TEXT,
    duration_seconds FLOAT,
    resolution VARCHAR(50),
    file_size_bytes BIGINT,
    platform VARCHAR(50),
    actual_roas FLOAT,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign ON blueprints(campaign_id);
CREATE INDEX IF NOT EXISTS idx_videos_campaign ON videos(campaign_id);
```

3. Click **Run** ✅

---

## STEP 2: Deploy Frontend to Vercel (5 min)

1. Go to **https://vercel.com**
2. Click **"Add New Project"**
3. Import your GitHub repo: `milosriki/geminivideo`
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework**: Vite
5. Add Environment Variables (click "Environment Variables"):
   ```
   VITE_SUPABASE_URL = https://akhirugwpozlxfvtqmvj.supabase.co
   VITE_SUPABASE_ANON_KEY = sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
   VITE_FIREBASE_API_KEY = AIzaSyCamMhfOYNAqnKnK-nQ78f1u5o8VDx9IaU
   VITE_FIREBASE_PROJECT_ID = ptd-fitness-demo
   VITE_GEMINI_API_KEY = AIzaSyDRynwFYxvHY34mLHXhxmKMVwx2wCyXUwI
   ```
6. Click **Deploy** ✅

---

## STEP 3: Deploy Backend to Cloud Run (10 min)

On your local machine (with gcloud installed):

```bash
# 1. Clone the repo
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# 2. Copy the .env.production file (already configured!)

# 3. Login to GCP
gcloud auth login
gcloud config set project ptd-fitness-demo

# 4. Enable APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com

# 5. Build and deploy titan-core
cd services/titan-core
gcloud run deploy titan-core \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="$(cat ../../.env.production | grep -v '^#' | tr '\n' ',')"

# 6. Copy the URL and update Vercel VITE_API_BASE_URL
```

---

## 🎉 DONE!

Your app will be live at: `https://your-app.vercel.app`

Generate winning ads from any browser or phone!
