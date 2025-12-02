# DEPLOYMENT GUIDE - Winning Ads Generator

**Complete step-by-step guide to deploying the Gemini Video AI Ad Intelligence Suite**

Version: 1.0
Last Updated: December 2025
Estimated Setup Time: 45-60 minutes

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Step 1: Supabase Setup (10 minutes)](#step-1-supabase-setup-10-minutes)
4. [Step 2: Upstash Redis Setup (5 minutes)](#step-2-upstash-redis-setup-5-minutes)
5. [Step 3: Firebase Setup (10 minutes)](#step-3-firebase-setup-10-minutes)
6. [Step 4: Google Cloud Setup (20 minutes)](#step-4-google-cloud-setup-20-minutes)
7. [Step 5: Cloud Run Deployment (20 minutes)](#step-5-cloud-run-deployment-20-minutes)
8. [Step 6: Vercel Deployment (10 minutes)](#step-6-vercel-deployment-10-minutes)
9. [Step 7: Connect Everything](#step-7-connect-everything)
10. [Environment Variables Reference](#environment-variables-reference)
11. [Testing the Full Flow](#testing-the-full-flow)
12. [Troubleshooting](#troubleshooting)
13. [Cost Estimate](#cost-estimate)
14. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Architecture Overview

The Winning Ads Generator is a microservices architecture deployed across multiple cloud platforms:

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT BROWSER                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VERCEL (Frontend Host)                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  React SPA (Vite + TypeScript)                          │   │
│  │  - User Dashboard                                       │   │
│  │  - Video Upload Interface                               │   │
│  │  - Campaign Management                                  │   │
│  │  - Analytics & Reports                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  GOOGLE CLOUD RUN (Backend)                     │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────┐  │
│  │ Gateway API  │◄────►│ Drive Intel  │◄────►│ Video Agent │  │
│  │   (8080)     │      │   (8081)     │      │   (8082)    │  │
│  │              │      │              │      │             │  │
│  │ • Auth       │      │ • Drive Scan │      │ • Clip Gen  │  │
│  │ • Routing    │      │ • Content ID │      │ • Analysis  │  │
│  │ • Rate Limit │      │ • RAG        │      │ • Scoring   │  │
│  └──────────────┘      └──────────────┘      └─────────────┘  │
│         │                                                       │
│         │              ┌──────────────┐      ┌─────────────┐  │
│         └─────────────►│  ML Service  │◄────►│ Meta Pub    │  │
│         │              │   (8003)     │      │   (8083)    │  │
│         │              │              │      │             │  │
│         │              │ • Prediction │      │ • Meta API  │  │
│         │              │ • A/B Test   │      │ • Publishing│  │
│         │              │ • Thompson   │      │ • Tracking  │  │
│         │              └──────────────┘      └─────────────┘  │
│         │                                                       │
│         │              ┌──────────────┐                        │
│         └─────────────►│  Titan Core  │                        │
│                        │   (8084)     │                        │
│                        │              │                        │
│                        │ • AI Council │                        │
│                        │ • Gemini AI  │                        │
│                        │ • Generation │                        │
│                        └──────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                               │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────┐  │
│  │  Supabase    │      │ Upstash Redis│      │ GCS Buckets │  │
│  │  PostgreSQL  │      │              │      │             │  │
│  │              │      │ • Cache      │      │ • Videos    │  │
│  │ • Users      │      │ • Sessions   │      │ • Assets    │  │
│  │ • Assets     │      │ • Jobs Queue │      │ • Outputs   │  │
│  │ • Campaigns  │      │ • Rate Limit │      │             │  │
│  │ • Analytics  │      │              │      │             │  │
│  └──────────────┘      └──────────────┘      └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL INTEGRATIONS                         │
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────┐  │
│  │  Meta Ads    │      │  Google AI   │      │  Firebase   │  │
│  │              │      │              │      │             │  │
│  │ • Publishing │      │ • Gemini API │      │ • Auth      │  │
│  │ • Tracking   │      │ • Vision AI  │      │ • Users     │  │
│  │ • Webhooks   │      │              │      │             │  │
│  └──────────────┘      └──────────────┘      └─────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Purpose | Technology Stack |
|-----------|---------|------------------|
| **Frontend** | User interface, dashboard, campaign management | React, TypeScript, Vite, Recharts |
| **Gateway API** | Main entry point, authentication, routing | Node.js, Express, Prisma |
| **Drive Intel** | Google Drive integration, content analysis | Python, Google Drive API |
| **Video Agent** | Video processing, clip generation, scoring | Python, FFmpeg, OpenCV |
| **ML Service** | Predictive modeling, A/B testing, Thompson sampling | Python, scikit-learn, pandas |
| **Meta Publisher** | Meta Ads API integration, campaign publishing | Node.js, Meta Business SDK |
| **Titan Core** | AI orchestration, multi-agent coordination | Python, Gemini API |
| **Supabase** | Primary database, authentication | PostgreSQL, PostgREST |
| **Upstash Redis** | Caching, session storage, job queues | Redis |
| **Firebase** | Frontend authentication | Firebase Auth |
| **GCS** | Video and asset storage | Google Cloud Storage |

---

## Prerequisites

Before starting, ensure you have the following:

### Accounts Required

- [ ] **Google Cloud Platform** account with billing enabled ([Sign up](https://cloud.google.com/))
- [ ] **Vercel** account (free tier works) ([Sign up](https://vercel.com/signup))
- [ ] **Supabase** account (free tier works) ([Sign up](https://supabase.com/))
- [ ] **Upstash** account for Redis (free tier works) ([Sign up](https://upstash.com/))
- [ ] **Firebase** account (free tier works) ([Sign up](https://firebase.google.com/))
- [ ] **GitHub** account for code hosting and CI/CD
- [ ] **Meta Developer** account (optional, for ad publishing) ([Sign up](https://developers.facebook.com/))

### API Keys Required

- [ ] **Google Gemini API Key** ([Get key](https://aistudio.google.com/app/apikey))
- [ ] **Anthropic API Key** (optional) ([Get key](https://console.anthropic.com/))
- [ ] **OpenAI API Key** (optional) ([Get key](https://platform.openai.com/api-keys))

### Tools to Install

```bash
# 1. Node.js 18+ (for frontend and some services)
# Download from https://nodejs.org/
node --version  # Should be v18.0.0 or higher

# 2. Python 3.10+ (for backend services)
# Download from https://www.python.org/
python3 --version  # Should be 3.10.0 or higher

# 3. Google Cloud SDK (gcloud CLI)
# Install from https://cloud.google.com/sdk/docs/install
gcloud --version

# 4. Vercel CLI (for deployment)
npm install -g vercel
vercel --version

# 5. Git (for version control)
git --version

# 6. curl (for testing APIs)
curl --version
```

### Domain Name (Optional but Recommended)

Having a custom domain makes your deployment more professional:
- Purchase from: Namecheap, Google Domains, GoDaddy, etc.
- Cost: ~$10-15/year
- You can also use Vercel's free subdomain: `your-app.vercel.app`

---

## Step 1: Supabase Setup (10 minutes)

Supabase provides our PostgreSQL database with a great developer experience.

### 1.1 Create New Project

1. Go to [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Click **"New Project"**
3. Fill in the details:
   - **Name:** `winning-ads-generator`
   - **Database Password:** Generate a strong password (save it!)
   - **Region:** Choose closest to your users (e.g., `us-east-1`)
   - **Pricing Plan:** Free (or Pro for production)
4. Click **"Create new project"**
5. Wait 2-3 minutes for provisioning

### 1.2 Run Database Migrations

Once your project is ready:

1. Go to **SQL Editor** in the left sidebar
2. Create a new query
3. Copy and paste the following schema:

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set default timezone
SET timezone = 'UTC';

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'USER',
    password_hash TEXT,
    api_key VARCHAR(255) UNIQUE,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_api_key ON users(api_key);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Assets table
CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size BIGINT NOT NULL,
    gcs_url TEXT UNIQUE NOT NULL,
    gcs_bucket VARCHAR(255) NOT NULL,
    gcs_path TEXT NOT NULL,
    thumbnail_url TEXT,
    duration FLOAT,
    width INTEGER,
    height INTEGER,
    fps FLOAT,
    bitrate INTEGER,
    codec VARCHAR(50),
    status VARCHAR(50) DEFAULT 'PENDING',
    processing_error TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_assets_user_id ON assets(user_id);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_created_at ON assets(created_at);
CREATE INDEX idx_assets_gcs_url ON assets(gcs_url);

-- Clips table
CREATE TABLE clips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    duration FLOAT NOT NULL,
    clip_url TEXT,
    thumbnail_url TEXT,
    features JSONB DEFAULT '{}',
    face_count INTEGER,
    has_text BOOLEAN DEFAULT FALSE,
    has_speech BOOLEAN DEFAULT FALSE,
    has_music BOOLEAN DEFAULT FALSE,
    score FLOAT,
    viral_score FLOAT,
    engagement_score FLOAT,
    brand_safety_score FLOAT,
    rank INTEGER,
    status VARCHAR(50) DEFAULT 'PENDING',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_clips_asset_id ON clips(asset_id);
CREATE INDEX idx_clips_score ON clips(score);
CREATE INDEX idx_clips_rank ON clips(rank);
CREATE INDEX idx_clips_status ON clips(status);
CREATE INDEX idx_clips_created_at ON clips(created_at);

-- Campaigns table
CREATE TABLE campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    objective VARCHAR(50) DEFAULT 'CONVERSIONS',
    budget DECIMAL(10, 2) NOT NULL,
    daily_budget DECIMAL(10, 2),
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'DRAFT',
    meta_campaign_id VARCHAR(255) UNIQUE,
    meta_ad_set_id VARCHAR(255),
    meta_account_id VARCHAR(255),
    target_audience JSONB DEFAULT '{}',
    target_locations JSONB DEFAULT '[]',
    target_age_range JSONB DEFAULT '{}',
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    total_spend DECIMAL(10, 2) DEFAULT 0,
    total_impressions BIGINT DEFAULT 0,
    total_clicks BIGINT DEFAULT 0,
    total_conversions BIGINT DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_meta_campaign_id ON campaigns(meta_campaign_id);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at);
CREATE INDEX idx_campaigns_dates ON campaigns(start_date, end_date);

-- Experiments table (A/B Testing)
CREATE TABLE experiments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    variants JSONB DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'DRAFT',
    winner_variant_id VARCHAR(255),
    winner_selected_at TIMESTAMP WITH TIME ZONE,
    metrics JSONB DEFAULT '{}',
    confidence FLOAT,
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_experiments_campaign_id ON experiments(campaign_id);
CREATE INDEX idx_experiments_status ON experiments(status);
CREATE INDEX idx_experiments_created_at ON experiments(created_at);

-- Predictions table (ML)
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    model_version VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) DEFAULT 'roas',
    predicted_roas FLOAT,
    predicted_ctr FLOAT,
    predicted_cpc FLOAT,
    predicted_cpa FLOAT,
    predicted_engagement FLOAT,
    actual_roas FLOAT,
    actual_ctr FLOAT,
    actual_cpc FLOAT,
    actual_cpa FLOAT,
    actual_engagement FLOAT,
    features JSONB DEFAULT '{}',
    confidence FLOAT,
    prediction_error FLOAT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_clip_id ON predictions(clip_id);
CREATE INDEX idx_predictions_model_version ON predictions(model_version);
CREATE INDEX idx_predictions_created_at ON predictions(created_at);

-- Conversions table
CREATE TABLE conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    source VARCHAR(50) DEFAULT 'META',
    external_id VARCHAR(255) UNIQUE,
    value DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    attributed_clip_id VARCHAR(255),
    attributed_ad_id VARCHAR(255),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_conversions_campaign_id ON conversions(campaign_id);
CREATE INDEX idx_conversions_timestamp ON conversions(timestamp);
CREATE INDEX idx_conversions_external_id ON conversions(external_id);
CREATE INDEX idx_conversions_created_at ON conversions(created_at);

-- Knowledge documents table (RAG)
CREATE TABLE knowledge_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    content TEXT NOT NULL,
    embedding FLOAT[] NOT NULL,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    category VARCHAR(100) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    version INTEGER DEFAULT 1,
    source TEXT,
    author VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_knowledge_category ON knowledge_documents(category);
CREATE INDEX idx_knowledge_version ON knowledge_documents(version);
CREATE INDEX idx_knowledge_created_at ON knowledge_documents(created_at);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to all tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_assets_updated_at BEFORE UPDATE ON assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_clips_updated_at BEFORE UPDATE ON clips
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_experiments_updated_at BEFORE UPDATE ON experiments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_predictions_updated_at BEFORE UPDATE ON predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_conversions_updated_at BEFORE UPDATE ON conversions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_knowledge_documents_updated_at BEFORE UPDATE ON knowledge_documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Success message
SELECT 'Database schema created successfully!' AS status;
```

4. Click **"Run"** to execute the migration
5. You should see: `Database schema created successfully!`

### 1.3 Create Storage Buckets

1. Go to **Storage** in the left sidebar
2. Click **"Create a new bucket"**
3. Create bucket for videos:
   - **Name:** `videos`
   - **Public:** No (private)
   - **File size limit:** 500 MB
   - Click **"Create bucket"**
4. Create bucket for assets:
   - **Name:** `assets`
   - **Public:** No (private)
   - **File size limit:** 100 MB
   - Click **"Create bucket"**

### 1.4 Copy Your API Keys

1. Go to **Settings** → **API**
2. Copy the following values (you'll need them later):
   ```
   SUPABASE_URL: https://xxxxx.supabase.co
   SUPABASE_ANON_KEY: eyJhbG...
   SUPABASE_SERVICE_ROLE_KEY: eyJhbG... (keep this secret!)
   ```

### 1.5 Get Database Connection String

1. Go to **Settings** → **Database**
2. Scroll down to **Connection string**
3. Select **URI** tab
4. Copy the connection string:
   ```
   DATABASE_URL: postgresql://postgres:[YOUR-PASSWORD]@db.xxxxx.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual database password

---

## Step 2: Upstash Redis Setup (5 minutes)

Upstash provides serverless Redis for caching and job queues.

### 2.1 Create Redis Database

1. Go to [https://console.upstash.com/](https://console.upstash.com/)
2. Click **"Create Database"**
3. Fill in the details:
   - **Name:** `winning-ads-redis`
   - **Type:** Regional
   - **Region:** Choose same as your Supabase (e.g., `us-east-1`)
   - **TLS:** Enabled
   - **Eviction:** No eviction
4. Click **"Create"**

### 2.2 Copy Redis URL

1. Once created, click on your database
2. Go to **Details** tab
3. Copy the **REST URL**:
   ```
   REDIS_URL: https://xxxxx.upstash.io
   ```
4. Also copy:
   ```
   UPSTASH_REDIS_REST_URL: https://xxxxx.upstash.io
   UPSTASH_REDIS_REST_TOKEN: AXXXXxxxxx
   ```

---

## Step 3: Firebase Setup (10 minutes)

Firebase handles frontend authentication.

### 3.1 Create Firebase Project

1. Go to [https://console.firebase.google.com/](https://console.firebase.google.com/)
2. Click **"Add project"**
3. Enter project name: `winning-ads-generator`
4. Disable Google Analytics (optional)
5. Click **"Create project"**

### 3.2 Enable Authentication

1. In the left sidebar, go to **Authentication**
2. Click **"Get started"**
3. Enable **Email/Password** provider:
   - Click on **Email/Password**
   - Toggle **Enable**
   - Click **"Save"**
4. (Optional) Enable **Google** provider for social login

### 3.3 Create Web App

1. In Project Settings (gear icon), go to **General**
2. Scroll down to **Your apps**
3. Click on **Web** icon (`</>`)
4. Register app:
   - **App nickname:** `winning-ads-frontend`
   - **Firebase Hosting:** No (we're using Vercel)
   - Click **"Register app"**
5. Copy the Firebase config:
   ```javascript
   const firebaseConfig = {
     apiKey: "AIzaSy...",
     authDomain: "your-project.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-project.firebasestorage.app",
     messagingSenderId: "123456789012",
     appId: "1:123456789012:web:abcdef123456",
     measurementId: "G-XXXXXXXXXX"
   };
   ```
6. Save these values for environment variables:
   ```
   VITE_FIREBASE_API_KEY=AIzaSy...
   VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your-project-id
   VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
   VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
   VITE_FIREBASE_APP_ID=1:123456789012:web:abcdef123456
   VITE_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX
   ```

---

## Step 4: Google Cloud Setup (20 minutes)

Google Cloud Platform hosts our backend services and storage.

### 4.1 Create GCP Project

1. Go to [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Click on project dropdown at the top
3. Click **"New Project"**
4. Enter project details:
   - **Project name:** `winning-ads-generator`
   - **Organization:** (your organization or none)
   - Click **"Create"**
5. Wait for project creation (30 seconds)
6. Copy your **Project ID** (e.g., `winning-ads-generator-12345`)

### 4.2 Enable Billing

1. Go to **Billing** in the left menu
2. Link a billing account (required for Cloud Run)
3. If you don't have one:
   - Click **"Create account"**
   - Enter payment details
   - Complete verification

### 4.3 Enable Required APIs

Run these commands in your terminal (or use Cloud Console):

```bash
# Set your project ID
export PROJECT_ID="winning-ads-generator-12345"
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  storage-api.googleapis.com \
  storage-component.googleapis.com \
  compute.googleapis.com \
  vpcaccess.googleapis.com \
  secretmanager.googleapis.com

# Verify APIs are enabled
gcloud services list --enabled
```

This will take 2-3 minutes to complete.

### 4.4 Create Service Account

```bash
# Create service account
gcloud iam service-accounts create geminivideo-cloud-run \
  --display-name="Gemini Video Cloud Run Service Account" \
  --description="Service account for Cloud Run services"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:geminivideo-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:geminivideo-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:geminivideo-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Create and download service account key
gcloud iam service-accounts keys create ~/geminivideo-sa-key.json \
  --iam-account=geminivideo-cloud-run@${PROJECT_ID}.iam.gserviceaccount.com

echo "Service account key saved to: ~/geminivideo-sa-key.json"
echo "Keep this file secure!"
```

### 4.5 Create Artifact Registry Repository

```bash
# Create Artifact Registry repository for Docker images
gcloud artifacts repositories create geminivideo \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for Gemini Video services"

# Configure Docker to use Artifact Registry
gcloud auth configure-docker us-central1-docker.pkg.dev

echo "Artifact Registry created at:"
echo "us-central1-docker.pkg.dev/${PROJECT_ID}/geminivideo"
```

### 4.6 Create GCS Buckets

```bash
# Create bucket for video uploads
gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://${PROJECT_ID}-videos

# Create bucket for generated assets
gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://${PROJECT_ID}-assets

# Set bucket permissions (public read for certain files)
gsutil iam ch allUsers:objectViewer gs://${PROJECT_ID}-assets

echo "GCS Buckets created:"
echo "- gs://${PROJECT_ID}-videos"
echo "- gs://${PROJECT_ID}-assets"
```

### 4.7 Get Gemini API Key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **"Create API key"**
3. Select your GCP project
4. Click **"Create API key in existing project"**
5. Copy the API key:
   ```
   GEMINI_API_KEY=AIzaSy...
   ```

---

## Step 5: Cloud Run Deployment (20 minutes)

Now we'll deploy all backend services to Cloud Run.

### 5.1 Clone Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/geminivideo.git
cd geminivideo

# Install dependencies
npm install
```

### 5.2 Create Production Environment File

Create `.env.production` in the project root:

```bash
cat > .env.production << 'EOF'
# =============================================================================
# PRODUCTION ENVIRONMENT VARIABLES
# =============================================================================

# Deployment
NODE_ENV=production
VITE_ENV=production

# Google Cloud Platform
GCP_PROJECT_ID=YOUR_PROJECT_ID_HERE
GCP_REGION=us-central1
GCS_BUCKET_NAME=YOUR_PROJECT_ID_HERE-videos

# Database (Supabase PostgreSQL)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres

# Redis (Upstash)
REDIS_URL=https://xxxxx.upstash.io
UPSTASH_REDIS_REST_URL=https://xxxxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXXXXxxxxx

# AI API Keys
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL_ID=gemini-2.0-flash-thinking-exp-1219
ANTHROPIC_API_KEY=sk-ant-... (optional)
OPENAI_API_KEY=sk-... (optional)

# Meta Ads Integration (if using)
META_ACCESS_TOKEN=your_long_lived_token
META_AD_ACCOUNT_ID=act_1234567890
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret

# Security
JWT_SECRET=$(openssl rand -base64 64)
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# Service Configuration
CLOUD_RUN_REGION=us-central1
CLOUD_RUN_MIN_INSTANCES=0
CLOUD_RUN_MAX_INSTANCES=10
CLOUD_RUN_TIMEOUT=600

# Registry
REGISTRY_URL=us-central1-docker.pkg.dev/YOUR_PROJECT_ID_HERE/geminivideo
IMAGE_TAG=latest

EOF

# Edit the file with your actual values
nano .env.production
```

Replace all placeholder values with your actual credentials.

### 5.3 Run Deployment Script

```bash
# Make deployment script executable
chmod +x scripts/deploy-production.sh

# Run deployment (this will take 10-15 minutes)
DEPLOYMENT_TARGET=cloud-run ./scripts/deploy-production.sh

# The script will:
# 1. Build Docker images for all 7 services
# 2. Push images to Artifact Registry
# 3. Deploy each service to Cloud Run
# 4. Configure environment variables
# 5. Set up health checks
# 6. Display service URLs
```

### 5.4 Note Service URLs

After deployment completes, you'll see output like:

```
Service URLs:

  frontend:             https://frontend-xxxxx-uc.a.run.app
  gateway-api:          https://gateway-api-xxxxx-uc.a.run.app
  drive-intel:          https://drive-intel-xxxxx-uc.a.run.app
  video-agent:          https://video-agent-xxxxx-uc.a.run.app
  ml-service:           https://ml-service-xxxxx-uc.a.run.app
  meta-publisher:       https://meta-publisher-xxxxx-uc.a.run.app
  titan-core:           https://titan-core-xxxxx-uc.a.run.app

Access your application at: https://frontend-xxxxx-uc.a.run.app
```

**Important:** Save all these URLs! You'll need them for Vercel configuration.

### 5.5 Test Backend Services

```bash
# Test gateway API health
curl https://gateway-api-xxxxx-uc.a.run.app/health

# Expected response:
# {"status":"ok","service":"gateway-api","timestamp":"2025-12-02T..."}

# Test drive-intel service
curl https://drive-intel-xxxxx-uc.a.run.app/health

# Test video-agent service
curl https://video-agent-xxxxx-uc.a.run.app/health
```

---

## Step 6: Vercel Deployment (10 minutes)

Now we'll deploy the frontend to Vercel.

### 6.1 Install Vercel CLI

```bash
npm install -g vercel
vercel login
```

### 6.2 Link Project to Vercel

```bash
cd frontend
vercel link

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? (your account)
# - Link to existing project? No
# - Project name? winning-ads-generator
# - Directory? ./
```

### 6.3 Set Environment Variables

```bash
# Set production environment variables
vercel env add VITE_GATEWAY_URL production
# Enter: https://gateway-api-xxxxx-uc.a.run.app

vercel env add VITE_ENV production
# Enter: production

# Firebase variables
vercel env add VITE_FIREBASE_API_KEY production
# Enter: AIzaSy...

vercel env add VITE_FIREBASE_AUTH_DOMAIN production
# Enter: your-project.firebaseapp.com

vercel env add VITE_FIREBASE_PROJECT_ID production
# Enter: your-project-id

vercel env add VITE_FIREBASE_STORAGE_BUCKET production
# Enter: your-project.firebasestorage.app

vercel env add VITE_FIREBASE_MESSAGING_SENDER_ID production
# Enter: 123456789012

vercel env add VITE_FIREBASE_APP_ID production
# Enter: 1:123456789012:web:abcdef123456

vercel env add VITE_FIREBASE_MEASUREMENT_ID production
# Enter: G-XXXXXXXXXX

# Supabase variables (if using on frontend)
vercel env add VITE_SUPABASE_URL production
# Enter: https://xxxxx.supabase.co

vercel env add VITE_SUPABASE_ANON_KEY production
# Enter: eyJhbG...
```

### 6.4 Deploy to Production

```bash
# Deploy to production
vercel --prod

# Output will show:
# Deployed to production: https://winning-ads-generator.vercel.app
```

### 6.5 (Optional) Add Custom Domain

1. Go to your Vercel project dashboard
2. Click on **Settings** → **Domains**
3. Add your custom domain (e.g., `app.yourcompany.com`)
4. Follow Vercel's DNS configuration instructions
5. Wait for DNS propagation (5-60 minutes)

---

## Step 7: Connect Everything

Now we need to update configurations to connect all services.

### 7.1 Update Cloud Run Services with Supabase

```bash
# Update gateway-api with database URL
gcloud run services update gateway-api \
  --region=us-central1 \
  --update-env-vars="DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"

# Update other services similarly
gcloud run services update drive-intel \
  --region=us-central1 \
  --update-env-vars="DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.xxxxx.supabase.co:5432/postgres"

# Repeat for video-agent, ml-service, meta-publisher, titan-core
```

### 7.2 Update CORS Origins

```bash
# Update gateway-api to allow requests from Vercel domain
gcloud run services update gateway-api \
  --region=us-central1 \
  --update-env-vars="CORS_ORIGINS=https://winning-ads-generator.vercel.app,https://app.yourcompany.com"
```

### 7.3 Test Full Integration

```bash
# Test from Vercel frontend
curl https://winning-ads-generator.vercel.app

# Check browser console for any errors
# Should successfully load and connect to backend
```

---

## Environment Variables Reference

### Frontend (Vercel)

```bash
# Application
VITE_ENV=production
VITE_GATEWAY_URL=https://gateway-api-xxxxx-uc.a.run.app

# Firebase Authentication
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789012
VITE_FIREBASE_APP_ID=1:123456789012:web:abcdef123456
VITE_FIREBASE_MEASUREMENT_ID=G-XXXXXXXXXX

# Supabase (optional, for direct access)
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbG...
```

### Backend Services (Cloud Run)

**Common Variables (All Services):**
```bash
NODE_ENV=production
DATABASE_URL=postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres
REDIS_URL=https://xxxxx.upstash.io
GEMINI_API_KEY=AIzaSy...
JWT_SECRET=your_64_char_secret
```

**Gateway API:**
```bash
PORT=8080
CORS_ORIGINS=https://winning-ads-generator.vercel.app
DRIVE_INTEL_URL=https://drive-intel-xxxxx-uc.a.run.app
VIDEO_AGENT_URL=https://video-agent-xxxxx-uc.a.run.app
ML_SERVICE_URL=https://ml-service-xxxxx-uc.a.run.app
META_PUBLISHER_URL=https://meta-publisher-xxxxx-uc.a.run.app
TITAN_CORE_URL=https://titan-core-xxxxx-uc.a.run.app
```

**Drive Intel:**
```bash
PORT=8081
GCP_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-project-id-videos
```

**Video Agent:**
```bash
PORT=8082
TEMP_STORAGE_PATH=/tmp/video-processing
MAX_VIDEO_SIZE_MB=500
```

**ML Service:**
```bash
PORT=8003
ENABLE_THOMPSON_SAMPLING=true
MIN_SAMPLES_FOR_UPDATE=50
```

**Meta Publisher:**
```bash
PORT=8083
META_ACCESS_TOKEN=your_token
META_AD_ACCOUNT_ID=act_1234567890
META_APP_ID=your_app_id
META_APP_SECRET=your_app_secret
```

**Titan Core:**
```bash
PORT=8084
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

---

## Testing the Full Flow

### Test 1: Frontend Access

1. Open your browser to: `https://winning-ads-generator.vercel.app`
2. You should see the landing page
3. Open browser DevTools (F12) → Console
4. Check for any errors (should be none)

### Test 2: Authentication

```bash
# Create test user via API
curl -X POST https://gateway-api-xxxxx-uc.a.run.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "name": "Test User"
  }'

# Expected response:
# {"success":true,"user":{"id":"...","email":"test@example.com","name":"Test User"}}
```

### Test 3: Video Upload Flow

1. Log into the dashboard
2. Click **"Upload Video"**
3. Upload a test video (MP4, < 50MB)
4. Watch the processing status
5. Should see:
   - Upload progress bar
   - Processing status
   - Generated clips
   - Performance predictions

### Test 4: Campaign Creation

1. Go to **"Campaigns"** tab
2. Click **"Create Campaign"**
3. Fill in campaign details
4. Select top-performing clips
5. Click **"Create"**
6. Should create campaign (or draft if Meta not configured)

---

## Troubleshooting

### Issue: Frontend can't connect to backend

**Symptoms:**
- Network errors in browser console
- "Failed to fetch" errors

**Solutions:**
1. Check CORS settings:
   ```bash
   gcloud run services describe gateway-api \
     --region=us-central1 \
     --format="value(spec.template.spec.containers[0].env)"
   ```
2. Verify CORS_ORIGINS includes your Vercel domain
3. Update if needed:
   ```bash
   gcloud run services update gateway-api \
     --region=us-central1 \
     --update-env-vars="CORS_ORIGINS=https://your-domain.vercel.app"
   ```

### Issue: Database connection errors

**Symptoms:**
- "Connection refused" or "Connection timeout"

**Solutions:**
1. Verify DATABASE_URL is correct
2. Check Supabase project is active
3. Test connection:
   ```bash
   psql "postgresql://postgres:PASSWORD@db.xxxxx.supabase.co:5432/postgres"
   ```
4. Ensure Cloud Run services have database URL set

### Issue: Cloud Run services timing out

**Symptoms:**
- 504 Gateway Timeout errors
- Services restarting frequently

**Solutions:**
1. Increase timeout:
   ```bash
   gcloud run services update SERVICE_NAME \
     --region=us-central1 \
     --timeout=600
   ```
2. Increase memory:
   ```bash
   gcloud run services update SERVICE_NAME \
     --region=us-central1 \
     --memory=4Gi
   ```
3. Check logs:
   ```bash
   gcloud run services logs read SERVICE_NAME \
     --region=us-central1 \
     --limit=50
   ```

### Issue: Out of memory errors

**Symptoms:**
- Services crashing during video processing
- "Container memory exceeded" errors

**Solutions:**
1. Increase memory allocation:
   ```bash
   gcloud run services update video-agent \
     --region=us-central1 \
     --memory=8Gi
   ```
2. Check Cloud Run quotas:
   ```bash
   gcloud run services describe video-agent \
     --region=us-central1
   ```

### Issue: Slow cold starts

**Symptoms:**
- First requests after idle time are slow (> 10 seconds)

**Solutions:**
1. Set minimum instances:
   ```bash
   gcloud run services update gateway-api \
     --region=us-central1 \
     --min-instances=1
   ```
2. Enable CPU boost:
   ```bash
   gcloud run services update gateway-api \
     --region=us-central1 \
     --cpu-boost
   ```

### Issue: API rate limits

**Symptoms:**
- 429 Too Many Requests errors
- Gemini API quota exceeded

**Solutions:**
1. Check Gemini API quota: https://aistudio.google.com/app/apikey
2. Implement request throttling in code
3. Upgrade Gemini API plan if needed
4. Use Redis caching to reduce API calls

### Issue: Deployment fails

**Symptoms:**
- Build errors during deployment
- "Image not found" errors

**Solutions:**
1. Check Artifact Registry permissions:
   ```bash
   gcloud artifacts repositories list --location=us-central1
   ```
2. Re-authenticate Docker:
   ```bash
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```
3. Manually build and push:
   ```bash
   cd services/gateway-api
   docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/geminivideo/gateway-api:latest .
   docker push us-central1-docker.pkg.dev/$PROJECT_ID/geminivideo/gateway-api:latest
   ```

---

## Cost Estimate

### Free Tier Usage (First Month)

| Service | Free Tier | Cost if Exceeded |
|---------|-----------|------------------|
| **Supabase** | 500MB database, 1GB storage, 50K monthly active users | $25/month (Pro) |
| **Upstash Redis** | 10K commands/day, 256MB storage | $0.20 per 100K commands |
| **Vercel** | 100GB bandwidth, unlimited deployments | $20/month (Pro) |
| **Firebase Auth** | 10K sign-ins/month | Free (50K sign-ins included) |
| **Cloud Run** | 2M requests, 360K GB-seconds, 180K vCPU-seconds | Pay per use |
| **Cloud Storage** | 5GB storage, 1GB network egress | $0.02/GB storage, $0.12/GB egress |
| **Gemini API** | 1500 requests/day (free tier) | $0.00035 per 1K characters |

### Expected Monthly Costs

**Light Usage (100 users, 1K videos/month):**
- Supabase: $0 (free tier)
- Upstash: $0 (free tier)
- Vercel: $0 (free tier)
- Cloud Run: $5-10
- Cloud Storage: $2-5
- Gemini API: $10-20
- **Total: $17-35/month**

**Medium Usage (1K users, 10K videos/month):**
- Supabase: $25 (Pro tier)
- Upstash: $5 (additional commands)
- Vercel: $0-20 (may need Pro for bandwidth)
- Cloud Run: $50-100
- Cloud Storage: $20-40
- Gemini API: $100-200
- **Total: $200-390/month**

**Heavy Usage (10K users, 100K videos/month):**
- Supabase: $599 (Team tier)
- Upstash: $50 (additional commands)
- Vercel: $20 (Pro tier)
- Cloud Run: $500-1000
- Cloud Storage: $200-400
- Gemini API: $1000-2000
- **Total: $2,369-4,069/month**

### Cost Optimization Tips

1. **Enable Cloud Run CPU Throttling:**
   ```bash
   gcloud run services update SERVICE_NAME \
     --region=us-central1 \
     --cpu-throttling
   ```

2. **Set Minimum Instances to 0 for Low-Traffic Services:**
   ```bash
   gcloud run services update SERVICE_NAME \
     --region=us-central1 \
     --min-instances=0
   ```

3. **Implement Aggressive Caching:**
   - Cache Gemini API responses in Redis
   - Set long TTLs for static content
   - Use Vercel Edge caching

4. **Use Cloud Storage Lifecycle Rules:**
   ```bash
   # Delete temporary files after 7 days
   gsutil lifecycle set lifecycle.json gs://$PROJECT_ID-videos
   ```

5. **Monitor and Alert on Costs:**
   - Set up GCP budget alerts
   - Monitor API usage dashboards
   - Review Supabase usage weekly

---

## Monitoring and Maintenance

### Set Up Cloud Monitoring

```bash
# Enable Cloud Monitoring API
gcloud services enable monitoring.googleapis.com

# Create uptime checks
gcloud monitoring uptime-checks create \
  --display-name="Gateway API Health Check" \
  --resource-type=uptime-url \
  --monitored-resource-labels=host=gateway-api-xxxxx-uc.a.run.app,path=/health
```

### View Logs

```bash
# View Cloud Run logs
gcloud run services logs read gateway-api \
  --region=us-central1 \
  --limit=100

# Follow logs in real-time
gcloud run services logs tail gateway-api \
  --region=us-central1

# Filter by severity
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" \
  --limit=50
```

### Set Up Alerts

1. Go to [Cloud Monitoring Console](https://console.cloud.google.com/monitoring)
2. Create alerts for:
   - High error rates (> 5%)
   - High latency (> 5 seconds)
   - Service downtime
   - High costs (> $500/month)

### Database Backups

Supabase automatically backs up daily, but you can create manual backups:

1. Go to Supabase dashboard → Database → Backups
2. Click **"Create backup"**
3. Download backup file locally

### Regular Maintenance Tasks

**Weekly:**
- Review error logs
- Check API quotas
- Monitor costs
- Test critical flows

**Monthly:**
- Update dependencies
- Review performance metrics
- Optimize database queries
- Clean up unused assets

**Quarterly:**
- Security audit
- Update API keys
- Review and optimize costs
- Plan capacity upgrades

---

## Next Steps

Congratulations! Your Winning Ads Generator is now deployed and running in production.

### Immediate Actions

1. **Test Everything:**
   - Upload test videos
   - Create test campaigns
   - Verify all features work

2. **Set Up Monitoring:**
   - Configure alerts
   - Set up status page
   - Add error tracking (Sentry)

3. **Secure Your Environment:**
   - Rotate API keys regularly
   - Enable 2FA on all accounts
   - Review IAM permissions

### Growth Checklist

- [ ] Add custom domain
- [ ] Set up CDN for assets
- [ ] Implement rate limiting
- [ ] Add email notifications
- [ ] Create admin dashboard
- [ ] Set up staging environment
- [ ] Document API endpoints
- [ ] Create user onboarding flow

### Support

**Documentation:**
- [Supabase Docs](https://supabase.com/docs)
- [Vercel Docs](https://vercel.com/docs)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Gemini API Docs](https://ai.google.dev/docs)

**Community:**
- GitHub Issues: https://github.com/yourusername/geminivideo/issues
- Discord: [Your Discord Link]
- Email: support@yourcompany.com

---

## Conclusion

You now have a fully-deployed, production-ready AI-powered ad generation platform running on modern cloud infrastructure.

**Architecture Summary:**
- Frontend: Vercel (React)
- Backend: Google Cloud Run (7 microservices)
- Database: Supabase PostgreSQL
- Cache: Upstash Redis
- Storage: Google Cloud Storage
- Auth: Firebase
- AI: Google Gemini API

**Deployment Time:** ~60 minutes
**Monthly Cost:** $17-35 (light usage)
**Scalability:** 0 → 10K users seamlessly

Happy building!
