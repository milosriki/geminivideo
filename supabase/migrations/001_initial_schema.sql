-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Index for email lookups
CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- CAMPAIGNS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
CREATE INDEX idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);

-- ============================================================================
-- BLUEPRINTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    hook_text TEXT NOT NULL,
    hook_type TEXT,
    script_json JSONB NOT NULL,
    council_score DECIMAL(5,2),
    predicted_roas DECIMAL(10,2),
    confidence DECIMAL(5,2),
    verdict TEXT CHECK (verdict IN ('approved', 'rejected', 'pending', NULL)),
    rank INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for blueprints
CREATE INDEX idx_blueprints_campaign_id ON blueprints(campaign_id);
CREATE INDEX idx_blueprints_verdict ON blueprints(verdict);
CREATE INDEX idx_blueprints_council_score ON blueprints(council_score DESC);
CREATE INDEX idx_blueprints_rank ON blueprints(rank);
CREATE INDEX idx_blueprints_created_at ON blueprints(created_at DESC);

-- ============================================================================
-- RENDER_JOBS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS render_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id UUID NOT NULL REFERENCES blueprints(id) ON DELETE CASCADE,
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    platform TEXT NOT NULL CHECK (platform IN ('youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin')),
    quality TEXT DEFAULT 'high' CHECK (quality IN ('low', 'medium', 'high', 'ultra')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    current_stage TEXT,
    error TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for render_jobs
CREATE INDEX idx_render_jobs_blueprint_id ON render_jobs(blueprint_id);
CREATE INDEX idx_render_jobs_campaign_id ON render_jobs(campaign_id);
CREATE INDEX idx_render_jobs_status ON render_jobs(status);
CREATE INDEX idx_render_jobs_created_at ON render_jobs(created_at DESC);

-- ============================================================================
-- VIDEOS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    blueprint_id UUID NOT NULL REFERENCES blueprints(id) ON DELETE CASCADE,
    render_job_id UUID REFERENCES render_jobs(id) ON DELETE SET NULL,
    storage_path TEXT NOT NULL,
    storage_url TEXT,
    duration_seconds DECIMAL(10,2),
    resolution TEXT,
    file_size_bytes BIGINT,
    platform TEXT CHECK (platform IN ('youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin')),
    actual_roas DECIMAL(10,2),
    impressions BIGINT DEFAULT 0,
    clicks BIGINT DEFAULT 0,
    conversions BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for videos
CREATE INDEX idx_videos_campaign_id ON videos(campaign_id);
CREATE INDEX idx_videos_blueprint_id ON videos(blueprint_id);
CREATE INDEX idx_videos_render_job_id ON videos(render_job_id);
CREATE INDEX idx_videos_platform ON videos(platform);
CREATE INDEX idx_videos_actual_roas ON videos(actual_roas DESC NULLS LAST);
CREATE INDEX idx_videos_created_at ON videos(created_at DESC);

-- ============================================================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_campaigns_updated_at
    BEFORE UPDATE ON campaigns
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE render_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos ENABLE ROW LEVEL SECURITY;

-- Users table policies
CREATE POLICY "Users can view their own profile"
    ON users FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON users FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON users FOR INSERT
    WITH CHECK (auth.uid() = id);

-- Campaigns table policies
CREATE POLICY "Users can view their own campaigns"
    ON campaigns FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own campaigns"
    ON campaigns FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own campaigns"
    ON campaigns FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own campaigns"
    ON campaigns FOR DELETE
    USING (auth.uid() = user_id);

-- Blueprints table policies
CREATE POLICY "Users can view blueprints from their campaigns"
    ON blueprints FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create blueprints for their campaigns"
    ON blueprints FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update blueprints from their campaigns"
    ON blueprints FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete blueprints from their campaigns"
    ON blueprints FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = blueprints.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

-- Render jobs table policies
CREATE POLICY "Users can view render jobs from their campaigns"
    ON render_jobs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = render_jobs.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create render jobs for their campaigns"
    ON render_jobs FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = render_jobs.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update render jobs from their campaigns"
    ON render_jobs FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = render_jobs.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete render jobs from their campaigns"
    ON render_jobs FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = render_jobs.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

-- Videos table policies
CREATE POLICY "Users can view videos from their campaigns"
    ON videos FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = videos.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create videos for their campaigns"
    ON videos FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = videos.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update videos from their campaigns"
    ON videos FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = videos.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete videos from their campaigns"
    ON videos FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM campaigns
            WHERE campaigns.id = videos.campaign_id
            AND campaigns.user_id = auth.uid()
        )
    );

-- ============================================================================
-- STORAGE BUCKETS
-- ============================================================================

-- Create videos bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('videos', 'videos', false)
ON CONFLICT (id) DO NOTHING;

-- Create assets bucket (for images, audio, etc.)
INSERT INTO storage.buckets (id, name, public)
VALUES ('assets', 'assets', false)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for videos bucket
CREATE POLICY "Users can upload videos to their own folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'videos' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can view their own videos"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'videos' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can update their own videos"
    ON storage.objects FOR UPDATE
    USING (
        bucket_id = 'videos' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own videos"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'videos' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- Storage policies for assets bucket
CREATE POLICY "Users can upload assets to their own folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can view their own assets"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can update their own assets"
    ON storage.objects FOR UPDATE
    USING (
        bucket_id = 'assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own assets"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'assets' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to update campaign counters when blueprints change verdict
CREATE OR REPLACE FUNCTION update_campaign_counters()
RETURNS TRIGGER AS $$
BEGIN
    -- Handle INSERT or UPDATE
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- If verdict changed to approved
        IF NEW.verdict = 'approved' AND (OLD IS NULL OR OLD.verdict IS DISTINCT FROM 'approved') THEN
            UPDATE campaigns
            SET approved_count = approved_count + 1,
                total_generated = total_generated + CASE WHEN OLD IS NULL THEN 1 ELSE 0 END
            WHERE id = NEW.campaign_id;
        END IF;

        -- If verdict changed to rejected
        IF NEW.verdict = 'rejected' AND (OLD IS NULL OR OLD.verdict IS DISTINCT FROM 'rejected') THEN
            UPDATE campaigns
            SET rejected_count = rejected_count + 1,
                total_generated = total_generated + CASE WHEN OLD IS NULL THEN 1 ELSE 0 END
            WHERE id = NEW.campaign_id;
        END IF;

        -- If just inserted with pending or NULL
        IF TG_OP = 'INSERT' AND (NEW.verdict IS NULL OR NEW.verdict = 'pending') THEN
            UPDATE campaigns
            SET total_generated = total_generated + 1
            WHERE id = NEW.campaign_id;
        END IF;

        -- Handle verdict change from approved/rejected to something else
        IF TG_OP = 'UPDATE' AND OLD.verdict IS DISTINCT FROM NEW.verdict THEN
            IF OLD.verdict = 'approved' THEN
                UPDATE campaigns
                SET approved_count = GREATEST(0, approved_count - 1)
                WHERE id = NEW.campaign_id;
            ELSIF OLD.verdict = 'rejected' THEN
                UPDATE campaigns
                SET rejected_count = GREATEST(0, rejected_count - 1)
                WHERE id = NEW.campaign_id;
            END IF;
        END IF;
    END IF;

    -- Handle DELETE
    IF TG_OP = 'DELETE' THEN
        UPDATE campaigns
        SET total_generated = GREATEST(0, total_generated - 1),
            approved_count = CASE WHEN OLD.verdict = 'approved' THEN GREATEST(0, approved_count - 1) ELSE approved_count END,
            rejected_count = CASE WHEN OLD.verdict = 'rejected' THEN GREATEST(0, rejected_count - 1) ELSE rejected_count END
        WHERE id = OLD.campaign_id;
        RETURN OLD;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update campaign counters
CREATE TRIGGER blueprint_verdict_changes
    AFTER INSERT OR UPDATE OR DELETE ON blueprints
    FOR EACH ROW
    EXECUTE FUNCTION update_campaign_counters();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- View for campaign statistics
CREATE OR REPLACE VIEW campaign_stats AS
SELECT
    c.id,
    c.user_id,
    c.product_name,
    c.status,
    c.total_generated,
    c.approved_count,
    c.rejected_count,
    COUNT(DISTINCT v.id) as video_count,
    AVG(v.actual_roas) as avg_roas,
    SUM(v.impressions) as total_impressions,
    SUM(v.clicks) as total_clicks,
    SUM(v.conversions) as total_conversions,
    c.created_at,
    c.updated_at
FROM campaigns c
LEFT JOIN videos v ON v.campaign_id = c.id
GROUP BY c.id;

-- View for top performing blueprints
CREATE OR REPLACE VIEW top_blueprints AS
SELECT
    b.id,
    b.campaign_id,
    b.title,
    b.hook_text,
    b.council_score,
    b.predicted_roas,
    b.verdict,
    AVG(v.actual_roas) as avg_actual_roas,
    COUNT(v.id) as video_count,
    SUM(v.impressions) as total_impressions,
    SUM(v.conversions) as total_conversions
FROM blueprints b
LEFT JOIN videos v ON v.blueprint_id = b.id
WHERE b.verdict = 'approved'
GROUP BY b.id
ORDER BY avg_actual_roas DESC NULLS LAST, b.council_score DESC;

-- ============================================================================
-- GRANT PERMISSIONS
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;

-- Grant all on all tables
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- Grant all on all sequences
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, service_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Grant execute on all functions
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres, anon, authenticated, service_role;
