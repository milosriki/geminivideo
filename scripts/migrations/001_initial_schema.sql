-- ============================================================================
-- Migration 001: Initial Schema
-- ============================================================================
-- Purpose: Core tables for campaigns, videos, ads, and performance tracking
-- For: €5M Investment-Grade Ad Platform
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    company_name TEXT,
    role TEXT DEFAULT 'user',
    meta_access_token TEXT,
    meta_ad_account_id TEXT,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

COMMENT ON TABLE users IS 'Platform users with Meta Ads integration';

-- ============================================================================
-- CAMPAIGNS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    product_name TEXT NOT NULL,
    offer TEXT NOT NULL,
    target_avatar TEXT,
    pain_points JSONB DEFAULT '[]'::jsonb,
    desires JSONB DEFAULT '[]'::jsonb,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'generating', 'active', 'paused', 'completed', 'archived')),

    -- Budget and spend tracking
    budget_daily DECIMAL(12, 2) DEFAULT 0,
    spend DECIMAL(12, 2) DEFAULT 0,
    revenue DECIMAL(12, 2) DEFAULT 0,
    roas DECIMAL(8, 2) DEFAULT 0,
    conversions INTEGER DEFAULT 0,

    -- Generation tracking
    total_generated INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,

    -- Platform targeting
    target_audience JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_campaigns_roas ON campaigns(roas DESC);

COMMENT ON TABLE campaigns IS 'Ad campaigns with budget tracking and performance metrics';

-- ============================================================================
-- BLUEPRINTS TABLE (Script/Creative Ideas)
-- ============================================================================
CREATE TABLE IF NOT EXISTS blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    hook_text TEXT NOT NULL,
    hook_type TEXT,
    script_json JSONB NOT NULL,

    -- AI Council scoring
    council_score DECIMAL(5,2),
    predicted_roas DECIMAL(10,2),
    predicted_ctr DECIMAL(8, 4),
    confidence DECIMAL(5,2),

    -- Approval workflow
    verdict TEXT CHECK (verdict IN ('approved', 'rejected', 'pending', NULL)),
    rank INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_blueprints_campaign_id ON blueprints(campaign_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_verdict ON blueprints(verdict);
CREATE INDEX IF NOT EXISTS idx_blueprints_council_score ON blueprints(council_score DESC);
CREATE INDEX IF NOT EXISTS idx_blueprints_rank ON blueprints(rank);
CREATE INDEX IF NOT EXISTS idx_blueprints_created_at ON blueprints(created_at DESC);

COMMENT ON TABLE blueprints IS 'AI-generated video scripts with council scoring';

-- ============================================================================
-- VIDEOS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE SET NULL,

    -- Video metadata
    title VARCHAR(255),
    description TEXT,
    script_content JSONB,
    video_url TEXT,
    thumbnail_url TEXT,
    storage_path TEXT,

    -- Video properties
    duration_seconds FLOAT,
    resolution VARCHAR(50),
    format VARCHAR(50),
    file_size_bytes BIGINT,

    -- Processing status
    status VARCHAR(50) DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'failed', 'archived')),

    -- Platform integration
    meta_platform_id VARCHAR(255),
    platform VARCHAR(50),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_videos_campaign_id ON videos(campaign_id);
CREATE INDEX IF NOT EXISTS idx_videos_blueprint_id ON videos(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_meta_platform_id ON videos(meta_platform_id);

COMMENT ON TABLE videos IS 'Generated video assets with processing status';

-- ============================================================================
-- ADS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS ads (
    ad_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
    video_id UUID REFERENCES videos(id) ON DELETE SET NULL,
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE SET NULL,

    -- Ad metadata
    asset_id VARCHAR(255),
    clip_ids TEXT[],
    arc_name VARCHAR(255),
    title VARCHAR(255),
    description TEXT,

    -- Approval workflow
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'published', 'archived')),
    approved BOOLEAN DEFAULT FALSE,
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(255),
    notes TEXT,

    -- Platform targeting
    platform VARCHAR(50),
    format VARCHAR(50),
    thumbnail_url TEXT,
    video_url TEXT,
    cta_text VARCHAR(100),
    cta_url TEXT,
    targeting JSONB DEFAULT '{}'::jsonb,

    -- Budget and predictions
    budget DECIMAL(12, 2),
    predicted_ctr DECIMAL(8, 4),
    predicted_roas DECIMAL(8, 2),

    -- Performance tracking
    performance JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ads_campaign_id ON ads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ads_video_id ON ads(video_id);
CREATE INDEX IF NOT EXISTS idx_ads_status ON ads(status);
CREATE INDEX IF NOT EXISTS idx_ads_approved ON ads(approved);
CREATE INDEX IF NOT EXISTS idx_ads_platform ON ads(platform);
CREATE INDEX IF NOT EXISTS idx_ads_created_at ON ads(created_at DESC);

COMMENT ON TABLE ads IS 'Ad creatives with approval workflow and targeting';

-- ============================================================================
-- CLIPS TABLE (Video Segments)
-- ============================================================================
CREATE TABLE IF NOT EXISTS clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    asset_id VARCHAR(255),

    -- Clip metadata
    name VARCHAR(255),
    start_time DECIMAL(10, 3) DEFAULT 0,
    end_time DECIMAL(10, 3) DEFAULT 0,
    duration DECIMAL(10, 3) DEFAULT 0,

    -- Content analysis
    transcript TEXT,
    scene_type VARCHAR(100),
    emotions JSONB DEFAULT '[]'::jsonb,
    visual_elements JSONB DEFAULT '[]'::jsonb,

    -- Scoring
    engagement_score DECIMAL(5, 2),
    ctr_score DECIMAL(5, 2) DEFAULT 0,
    scene_score DECIMAL(5, 2) DEFAULT 0,

    -- Storage
    storage_path TEXT,
    thumbnail_path TEXT,

    -- Features for ML
    features JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_clips_video_id ON clips(video_id);
CREATE INDEX IF NOT EXISTS idx_clips_asset_id ON clips(asset_id);
CREATE INDEX IF NOT EXISTS idx_clips_scene_type ON clips(scene_type);
CREATE INDEX IF NOT EXISTS idx_clips_ctr_score ON clips(ctr_score DESC);
CREATE INDEX IF NOT EXISTS idx_clips_clip_id ON clips(clip_id);

COMMENT ON TABLE clips IS 'Video segments with AI-powered scene analysis';

-- ============================================================================
-- EMOTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS emotions (
    id SERIAL PRIMARY KEY,
    clip_id UUID REFERENCES clips(id) ON DELETE CASCADE,
    video_id UUID,
    asset_id VARCHAR(255),

    -- Emotion data
    emotion VARCHAR(50),
    emotion_type VARCHAR(50) NOT NULL,
    intensity DECIMAL(5, 2) DEFAULT 0,
    confidence DECIMAL(5, 2),
    emotion_scores JSONB DEFAULT '{}'::jsonb,

    -- Timing
    timestamp FLOAT,
    timestamp_start DECIMAL(10, 3),
    timestamp_end DECIMAL(10, 3),

    -- Source
    source VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emotions_clip_id ON emotions(clip_id);
CREATE INDEX IF NOT EXISTS idx_emotions_video_id ON emotions(video_id);
CREATE INDEX IF NOT EXISTS idx_emotions_emotion_type ON emotions(emotion_type);
CREATE INDEX IF NOT EXISTS idx_emotions_asset_id ON emotions(asset_id);

COMMENT ON TABLE emotions IS 'Emotional analysis data for video segments';

-- ============================================================================
-- PERFORMANCE METRICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    ad_id UUID,
    campaign_id UUID,

    -- Platform
    platform VARCHAR(50) DEFAULT 'meta',

    -- Date tracking
    date DATE NOT NULL,

    -- Core metrics
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10, 2) DEFAULT 0.0,
    revenue DECIMAL(12, 2) DEFAULT 0.0,
    conversions INTEGER DEFAULT 0,

    -- Calculated metrics
    ctr DECIMAL(8, 4),
    cpc DECIMAL(8, 2),
    cpm DECIMAL(8, 2),
    cpa DECIMAL(8, 2),
    roas DECIMAL(8, 2),
    conversion_rate DECIMAL(8, 4),

    -- Additional data
    metric_type VARCHAR(50),
    value DECIMAL(12, 4),
    metadata JSONB DEFAULT '{}'::jsonb,
    raw_data JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_performance_metrics_video_id ON performance_metrics(video_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_platform ON performance_metrics(platform);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_ad_id ON performance_metrics(ad_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_campaign_id ON performance_metrics(campaign_id);

COMMENT ON TABLE performance_metrics IS 'Daily performance metrics from ad platforms';

-- ============================================================================
-- DAILY ANALYTICS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS daily_analytics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,

    -- Financial metrics
    spend DECIMAL(12, 2) DEFAULT 0,
    revenue DECIMAL(12, 2) DEFAULT 0,
    roas DECIMAL(8, 2) DEFAULT 0,

    -- Engagement metrics
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,

    -- Calculated metrics
    ctr DECIMAL(8, 4) DEFAULT 0,
    cpc DECIMAL(8, 2) DEFAULT 0,
    cpa DECIMAL(8, 2) DEFAULT 0,

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(date DESC);

COMMENT ON TABLE daily_analytics IS 'Aggregated daily analytics for dashboard';

-- ============================================================================
-- JOBS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    type VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    error TEXT,
    result JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

COMMENT ON TABLE jobs IS 'Background job queue for async processing';

-- ============================================================================
-- RENDER JOBS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS render_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE CASCADE,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,

    -- Render configuration
    platform TEXT NOT NULL CHECK (platform IN ('youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin')),
    quality TEXT DEFAULT 'high' CHECK (quality IN ('low', 'medium', 'high', 'ultra')),

    -- Status tracking
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_stage TEXT,
    error TEXT,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_render_jobs_blueprint_id ON render_jobs(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_campaign_id ON render_jobs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_created_at ON render_jobs(created_at DESC);

COMMENT ON TABLE render_jobs IS 'Video rendering job queue';

-- ============================================================================
-- AUDIT LOGS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50),
    entity_id UUID,
    action VARCHAR(50),
    user_id UUID,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);

COMMENT ON TABLE audit_logs IS 'Audit trail for all system actions';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001: Initial schema completed successfully';
    RAISE NOTICE '   Core tables created:';
    RAISE NOTICE '   - users, campaigns, blueprints';
    RAISE NOTICE '   - videos, ads, clips, emotions';
    RAISE NOTICE '   - performance_metrics, daily_analytics';
    RAISE NOTICE '   - jobs, render_jobs, audit_logs';
END $$;
