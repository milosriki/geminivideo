-- ============================================================================
-- Migration 004: Missing Tables
-- ============================================================================
-- Purpose: Add tables referenced by frontend but missing from schema
-- Run with: psql $DATABASE_URL -f 004_missing_tables.sql
-- ============================================================================

-- Jobs table for background job tracking
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,  -- video, image, script, analysis
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    progress INTEGER DEFAULT 0,
    error TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- Daily Analytics table for chart data
CREATE TABLE IF NOT EXISTS daily_analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    spend DECIMAL(12, 2) DEFAULT 0,
    revenue DECIMAL(12, 2) DEFAULT 0,
    roas DECIMAL(8, 2) DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    ctr DECIMAL(8, 4) DEFAULT 0,
    cpc DECIMAL(8, 2) DEFAULT 0,
    cpa DECIMAL(8, 2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(date DESC);

-- Performance Metrics table (may already exist in some shared schemas)
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,  -- roas, ctr, conversions, etc.
    value DECIMAL(12, 4) NOT NULL,
    campaign_id UUID,
    video_id UUID,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type ON performance_metrics(metric_type);

-- Clips table for video segment analysis
CREATE TABLE IF NOT EXISTS clips (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    clip_id UUID DEFAULT uuid_generate_v4(),  -- Alternative ID for queries
    video_id UUID,
    asset_id VARCHAR(255),  -- Reference to source asset
    name VARCHAR(255),
    start_time DECIMAL(10, 3) DEFAULT 0,  -- seconds
    end_time DECIMAL(10, 3) DEFAULT 0,
    duration DECIMAL(10, 3) DEFAULT 0,
    transcript TEXT,
    scene_type VARCHAR(100),  -- hook, problem, solution, cta, etc.
    emotions JSONB DEFAULT '[]',
    visual_elements JSONB DEFAULT '[]',
    engagement_score DECIMAL(5, 2),
    ctr_score DECIMAL(5, 2) DEFAULT 0,  -- CTR prediction score
    scene_score DECIMAL(5, 2) DEFAULT 0,  -- Scene quality score
    storage_path TEXT,
    thumbnail_path TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clips_video ON clips(video_id);
CREATE INDEX IF NOT EXISTS idx_clips_asset ON clips(asset_id);
CREATE INDEX IF NOT EXISTS idx_clips_scene_type ON clips(scene_type);
CREATE INDEX IF NOT EXISTS idx_clips_ctr_score ON clips(ctr_score DESC);

-- Emotions table for emotional analysis
CREATE TABLE IF NOT EXISTS emotions (
    id SERIAL PRIMARY KEY,
    clip_id UUID REFERENCES clips(id) ON DELETE CASCADE,
    video_id UUID,
    emotion_type VARCHAR(50) NOT NULL,  -- happy, sad, excited, curious, etc.
    intensity DECIMAL(5, 2) DEFAULT 0,  -- 0-100
    timestamp_start DECIMAL(10, 3),
    timestamp_end DECIMAL(10, 3),
    confidence DECIMAL(5, 2),
    source VARCHAR(50),  -- face_detection, audio_analysis, text_analysis
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emotions_clip ON emotions(clip_id);
CREATE INDEX IF NOT EXISTS idx_emotions_video ON emotions(video_id);
CREATE INDEX IF NOT EXISTS idx_emotions_type ON emotions(emotion_type);

-- Ads table for ad creatives and approval workflow
CREATE TABLE IF NOT EXISTS ads (
    ad_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID,
    video_id UUID,
    blueprint_id UUID,
    asset_id VARCHAR(255),  -- Source asset reference
    clip_ids TEXT[],  -- Array of clip IDs used in this ad
    arc_name VARCHAR(255),  -- Story arc name (e.g., "problem-solution")
    title VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected, published
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(255),
    notes TEXT,
    platform VARCHAR(50),  -- facebook, instagram, tiktok, youtube
    format VARCHAR(50),  -- story, feed, reel, in-stream
    thumbnail_url TEXT,
    video_url TEXT,
    cta_text VARCHAR(100),
    cta_url TEXT,
    targeting JSONB DEFAULT '{}',
    budget DECIMAL(12, 2),
    predicted_ctr DECIMAL(8, 4),  -- ML-predicted CTR
    predicted_roas DECIMAL(8, 2),  -- ML-predicted ROAS
    performance JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ads_campaign ON ads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ads_status ON ads(status);
CREATE INDEX IF NOT EXISTS idx_ads_approved ON ads(approved);
CREATE INDEX IF NOT EXISTS idx_ads_platform ON ads(platform);
CREATE INDEX IF NOT EXISTS idx_ads_created_at ON ads(created_at DESC);

-- ============================================================================
-- SEED DATA FOR DEVELOPMENT
-- ============================================================================

-- Insert sample job if table is empty
INSERT INTO jobs (type, name, status, progress)
SELECT 'video', 'Welcome Video Generation', 'completed', 100
WHERE NOT EXISTS (SELECT 1 FROM jobs LIMIT 1);

-- Insert sample daily analytics for last 7 days
INSERT INTO daily_analytics (date, spend, revenue, roas, impressions, clicks, conversions, ctr, cpc, cpa)
SELECT
    CURRENT_DATE - i,
    (100 + random() * 400)::DECIMAL(12,2),
    (300 + random() * 1200)::DECIMAL(12,2),
    (2.0 + random() * 3.0)::DECIMAL(8,2),
    (5000 + random() * 15000)::INTEGER,
    (100 + random() * 500)::INTEGER,
    (5 + random() * 30)::INTEGER,
    (1.5 + random() * 3.0)::DECIMAL(8,4),
    (0.3 + random() * 1.0)::DECIMAL(8,2),
    (8 + random() * 20)::DECIMAL(8,2)
FROM generate_series(0, 6) AS i
WHERE NOT EXISTS (SELECT 1 FROM daily_analytics LIMIT 1);

-- Add missing columns to existing campaigns table
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS budget_daily DECIMAL(12, 2) DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS spend DECIMAL(12, 2) DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS revenue DECIMAL(12, 2) DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS roas DECIMAL(8, 2) DEFAULT 0;
ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS conversions INTEGER DEFAULT 0;

-- Update name from product_name if name is null
UPDATE campaigns SET name = product_name WHERE name IS NULL AND product_name IS NOT NULL;

COMMENT ON TABLE jobs IS 'Background job queue for async processing';
COMMENT ON TABLE daily_analytics IS 'Daily aggregated analytics for dashboard charts';
COMMENT ON TABLE performance_metrics IS 'Granular performance metrics by date and type';
COMMENT ON TABLE clips IS 'Video segments with timing and analysis';
COMMENT ON TABLE emotions IS 'Emotional analysis data for video clips';
COMMENT ON TABLE ads IS 'Ad creatives with approval workflow';
