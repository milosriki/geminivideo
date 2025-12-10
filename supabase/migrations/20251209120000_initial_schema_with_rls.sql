-- ============================================================================
-- INITIAL SCHEMA WITH RLS (Row Level Security)
-- Generated: 2025-12-09
-- Description: Complete schema with RLS policies and indexes
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
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index for email lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users
CREATE POLICY "Users can view own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

-- ============================================================================
-- CAMPAIGNS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    product_name TEXT NOT NULL,
    offer TEXT NOT NULL,
    target_avatar TEXT,
    pain_points JSONB DEFAULT '[]'::jsonb,
    desires JSONB DEFAULT '[]'::jsonb,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'generating', 'completed', 'archived')),
    total_generated INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    rejected_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for campaigns
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at DESC);

-- Enable RLS
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;

-- RLS Policies for campaigns
CREATE POLICY "Users can view own campaigns"
    ON campaigns FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own campaigns"
    ON campaigns FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own campaigns"
    ON campaigns FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own campaigns"
    ON campaigns FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- BLUEPRINTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    title TEXT,
    hook_text TEXT,
    hook_type TEXT,
    script_json JSONB,
    council_score FLOAT,
    predicted_roas FLOAT,
    confidence FLOAT,
    verdict TEXT,
    rank INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for blueprints
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign_id ON blueprints(campaign_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_rank ON blueprints(rank);
CREATE INDEX IF NOT EXISTS idx_blueprints_created_at ON blueprints(created_at DESC);

-- Enable RLS
ALTER TABLE blueprints ENABLE ROW LEVEL SECURITY;

-- RLS Policies for blueprints (via campaign ownership)
CREATE POLICY "Users can view blueprints of own campaigns"
    ON blueprints FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert blueprints to own campaigns"
    ON blueprints FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update blueprints of own campaigns"
    ON blueprints FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete blueprints of own campaigns"
    ON blueprints FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

-- ============================================================================
-- RENDER JOBS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS render_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id UUID NOT NULL REFERENCES blueprints(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    video_url TEXT,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    completed_at TIMESTAMPTZ
);

-- Indexes for render_jobs
CREATE INDEX IF NOT EXISTS idx_render_jobs_blueprint_id ON render_jobs(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_created_at ON render_jobs(created_at DESC);

-- Enable RLS
ALTER TABLE render_jobs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for render_jobs (via blueprint -> campaign ownership)
CREATE POLICY "Users can view render jobs of own campaigns"
    ON render_jobs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM blueprints
            JOIN campaigns ON campaigns.id = blueprints.campaign_id
            WHERE blueprints.id = render_jobs.blueprint_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert render jobs for own campaigns"
    ON render_jobs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM blueprints
            JOIN campaigns ON campaigns.id = blueprints.campaign_id
            WHERE blueprints.id = render_jobs.blueprint_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update render jobs of own campaigns"
    ON render_jobs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM blueprints
            JOIN campaigns ON campaigns.id = blueprints.campaign_id
            WHERE blueprints.id = render_jobs.blueprint_id
            AND campaigns.user_id = auth.uid()
        )
    );

-- ============================================================================
-- VIDEOS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    render_job_id UUID NOT NULL REFERENCES render_jobs(id) ON DELETE CASCADE,
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration_seconds INTEGER,
    file_size_bytes BIGINT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for videos
CREATE INDEX IF NOT EXISTS idx_videos_render_job_id ON videos(render_job_id);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);

-- Enable RLS
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;

-- RLS Policies for videos (via render_job -> blueprint -> campaign ownership)
CREATE POLICY "Users can view videos of own campaigns"
    ON videos FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM render_jobs
            JOIN blueprints ON blueprints.id = render_jobs.blueprint_id
            JOIN campaigns ON campaigns.id = blueprints.campaign_id
            WHERE render_jobs.id = videos.render_job_id
            AND campaigns.user_id = auth.uid()
        )
    );

-- ============================================================================
-- UPDATE TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_blueprints_updated_at
    BEFORE UPDATE ON blueprints
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_render_jobs_updated_at
    BEFORE UPDATE ON render_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE users IS 'User profiles linked to auth.users';
COMMENT ON TABLE campaigns IS 'Marketing campaigns created by users';
COMMENT ON TABLE blueprints IS 'Video blueprints/scripts for campaigns';
COMMENT ON TABLE render_jobs IS 'Video rendering job queue';
COMMENT ON TABLE videos IS 'Completed video assets';

