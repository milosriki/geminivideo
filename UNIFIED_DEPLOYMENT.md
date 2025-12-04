# UNIFIED DEPLOYMENT PLAN

## YOUR SITUATION
You have 3 repos and multiple Vercel deployments. Here's what to do:

## WHAT TO USE

| Repo | Decision | Reason |
|------|----------|--------|
| **geminivideo** | USE THIS | Has ALL features (PRO video, AI Council, Meta) |
| video-edit | Archive | Older version, subset of features |
| titan-ad-engine | Archive | Even older, basic features |

## YOUR VERCEL PROJECTS (What They Are)

| Project | Source | Keep? |
|---------|--------|-------|
| titan-ad-engine-vbpo.vercel.app | video-edit | No - Replace |
| ptd-elite-dashboard.vercel.app | video-edit | No - Replace |
| titan-ad-engine.vercel.app | titan-ad-engine | No - Replace |

## DEPLOY GEMINIVIDEO NOW

### Step 1: Deploy Frontend to Vercel (5 min)

```bash
cd /home/user/geminivideo/frontend

# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

**Add these env vars in Vercel Dashboard:**
```
VITE_SUPABASE_URL=https://akhirugwpozlxfvtqmvj.supabase.co
VITE_SUPABASE_ANON_KEY=sb_publishable_c09vjqrYUN4vpQj2XcGANg_NeVu6WDG
VITE_GEMINI_API_KEY=AIzaSyDRynwFYxvHY34mLHXhxmKMVwx2wCyXUwI
VITE_FIREBASE_API_KEY=AIzaSyCamMhfOYNAqnKnK-nQ78f1u5o8VDx9IaU
VITE_FIREBASE_AUTH_DOMAIN=ptd-fitness-demo.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=ptd-fitness-demo
VITE_GOOGLE_API_KEY=AIzaSyChrr8jepLbUdvOlg4n0QS9p1ITNcMTr68
```

### Step 2: Deploy Backend to Cloud Run (10 min)

```bash
cd /home/user/geminivideo/services/titan-core

# Build and deploy
gcloud run deploy titan-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=AIzaSyDRynwFYxvHY34mLHXhxmKMVwx2wCyXUwI,OPENAI_API_KEY=sk-svcacct-UiB...,ANTHROPIC_API_KEY=sk-ant-api03-dl8..."
```

### Step 3: Setup Supabase Database (5 min)

Go to https://supabase.com/dashboard → SQL Editor → Run:

```sql
-- Core Tables
CREATE TABLE IF NOT EXISTS campaigns (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  name TEXT NOT NULL,
  status TEXT DEFAULT 'draft',
  target_audience JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS blueprints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id),
  hook_type TEXT NOT NULL,
  script TEXT NOT NULL,
  council_score FLOAT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS render_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  blueprint_id UUID REFERENCES blueprints(id),
  status TEXT DEFAULT 'queued',
  progress INT DEFAULT 0,
  output_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS videos (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id UUID REFERENCES campaigns(id),
  storage_url TEXT NOT NULL,
  duration_seconds FLOAT,
  analysis_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE render_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;
```

## WHAT YOU GET

After deployment:
- **Frontend**: https://geminivideo.vercel.app (or your domain)
- **Backend API**: https://titan-backend-xxxxx.run.app
- **Database**: Supabase PostgreSQL

## FEATURES AVAILABLE

### AI Council (Working)
- Gemini 2.0 (40% weight)
- Claude 3.5 (30% weight)
- GPT-4o (20% weight)
- DeepCTR (10% weight)

### Video Processing (Working)
- GPU-accelerated rendering
- 66 transitions
- 10 color grading LUTs
- Whisper auto-captions (5 styles)
- Smart crop with face detection

### Meta Integration (Working)
- Marketing API
- Conversions API
- Ads Library scraping

## VERCEL AI GATEWAY

Your AI Gateway key has been configured:
```
VERCEL_AI_GATEWAY_KEY=vck_2iOkmopjXqJC4dTInb6tzXpYI5ZSN5wEWicGyw4TH9Jewn5p4L1YqRjH
```

## DELETE OLD VERCEL PROJECTS

Once geminivideo is deployed and working:
1. Go to Vercel Dashboard
2. Delete: titan-ad-engine-vbpo, ptd-elite-dashboard, titan-ad-engine
3. Keep only your new geminivideo deployment

## QUESTIONS?

All your API keys are configured in `.env.production`:
- 3 AI APIs (Gemini, OpenAI, Anthropic)
- Supabase (URL + Keys + Database)
- Redis/Upstash (Queue + WebSocket)
- Firebase (Auth)
- Meta/Facebook (Marketing + Conversions)
- Vercel AI Gateway
