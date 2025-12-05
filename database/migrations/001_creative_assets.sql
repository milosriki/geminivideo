-- ============================================================================
-- Migration 001: Creative Assets Table
-- ============================================================================
-- Purpose: Add creative_assets table for upload management and asset tracking
-- Run with: psql $DATABASE_URL -f 001_creative_assets.sql
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- CREATIVE ASSETS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS creative_assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User and campaign association
    user_id UUID,
    campaign_id UUID,

    -- Asset metadata
    asset_type VARCHAR(50) NOT NULL CHECK (asset_type IN ('image', 'video', 'audio', 'document', 'font', 'template')),
    file_name VARCHAR(255) NOT NULL,
    original_file_name VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),

    -- Storage information
    storage_provider VARCHAR(50) DEFAULT 'local' CHECK (storage_provider IN ('local', 'gcs', 'supabase', 's3', 'cloudinary')),
    storage_path TEXT NOT NULL,
    storage_url TEXT,
    thumbnail_url TEXT,

    -- Media properties (for images/videos)
    width INTEGER,
    height INTEGER,
    duration_seconds FLOAT,
    fps INTEGER,
    bit_rate INTEGER,
    format VARCHAR(50),
    codec VARCHAR(50),

    -- Processing status
    status VARCHAR(50) DEFAULT 'uploading' CHECK (status IN ('uploading', 'processing', 'ready', 'failed', 'archived', 'deleted')),
    processing_progress INTEGER DEFAULT 0 CHECK (processing_progress >= 0 AND processing_progress <= 100),
    error_message TEXT,

    -- AI analysis
    ai_tags TEXT[],
    ai_description TEXT,
    ai_score DECIMAL(5,2),
    face_detected BOOLEAN DEFAULT FALSE,
    text_detected BOOLEAN DEFAULT FALSE,
    objects_detected JSONB DEFAULT '[]'::jsonb,

    -- Usage tracking
    used_in_campaigns UUID[],
    used_in_videos UUID[],
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,

    -- Metadata and custom fields
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[],
    category VARCHAR(100),
    subcategory VARCHAR(100),

    -- Licensing and rights
    license_type VARCHAR(50),
    copyright_holder VARCHAR(255),
    usage_rights TEXT,
    attribution_required BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    deleted_at TIMESTAMPTZ
);

-- ============================================================================
-- INDEXES FOR CREATIVE ASSETS
-- ============================================================================

-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_creative_assets_user_id ON creative_assets(user_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_campaign_id ON creative_assets(campaign_id) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_asset_type ON creative_assets(asset_type) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_status ON creative_assets(status);

-- Temporal queries
CREATE INDEX IF NOT EXISTS idx_creative_assets_created_at ON creative_assets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_creative_assets_updated_at ON creative_assets(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_creative_assets_last_used ON creative_assets(last_used_at DESC NULLS LAST);

-- Search and filtering
CREATE INDEX IF NOT EXISTS idx_creative_assets_category ON creative_assets(category) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_tags ON creative_assets USING GIN(tags) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_metadata ON creative_assets USING GIN(metadata) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_ai_tags ON creative_assets USING GIN(ai_tags) WHERE deleted_at IS NULL;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_creative_assets_user_type ON creative_assets(user_id, asset_type) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_user_created ON creative_assets(user_id, created_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_creative_assets_campaign_type ON creative_assets(campaign_id, asset_type) WHERE deleted_at IS NULL;

-- Storage optimization
CREATE INDEX IF NOT EXISTS idx_creative_assets_storage_path ON creative_assets(storage_path) WHERE status = 'ready';
CREATE INDEX IF NOT EXISTS idx_creative_assets_file_size ON creative_assets(file_size_bytes DESC) WHERE deleted_at IS NULL;

-- ============================================================================
-- ASSET VARIATIONS TABLE (for different sizes/formats)
-- ============================================================================
CREATE TABLE IF NOT EXISTS creative_asset_variations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL,

    -- Variation details
    variation_type VARCHAR(50) NOT NULL CHECK (variation_type IN ('thumbnail', 'preview', 'optimized', 'compressed', 'resized', 'converted')),
    file_name VARCHAR(255),
    file_size_bytes BIGINT,

    -- Storage
    storage_path TEXT NOT NULL,
    storage_url TEXT,

    -- Media properties
    width INTEGER,
    height INTEGER,
    format VARCHAR(50),
    quality INTEGER,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_asset_variations_asset_id ON creative_asset_variations(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_variations_type ON creative_asset_variations(asset_id, variation_type);

-- ============================================================================
-- ASSET USAGE TRACKING TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS creative_asset_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL,

    -- Usage context
    used_in_type VARCHAR(50) NOT NULL CHECK (used_in_type IN ('campaign', 'video', 'ad', 'blueprint', 'template')),
    used_in_id UUID NOT NULL,

    -- Usage details
    usage_purpose VARCHAR(100),
    usage_duration_seconds INTEGER,
    start_time DECIMAL(10,3),
    end_time DECIMAL(10,3),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    removed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_asset_usage_asset_id ON creative_asset_usage(asset_id);
CREATE INDEX IF NOT EXISTS idx_asset_usage_used_in ON creative_asset_usage(used_in_type, used_in_id);
CREATE INDEX IF NOT EXISTS idx_asset_usage_created_at ON creative_asset_usage(created_at DESC);

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_creative_assets_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER creative_assets_updated_at
    BEFORE UPDATE ON creative_assets
    FOR EACH ROW
    EXECUTE FUNCTION update_creative_assets_updated_at();

-- Increment usage count when asset is used
CREATE OR REPLACE FUNCTION increment_asset_usage()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE creative_assets
    SET
        usage_count = usage_count + 1,
        last_used_at = NOW(),
        used_in_campaigns = CASE
            WHEN NEW.used_in_type = 'campaign'
            THEN array_append(used_in_campaigns, NEW.used_in_id)
            ELSE used_in_campaigns
        END,
        used_in_videos = CASE
            WHEN NEW.used_in_type = 'video'
            THEN array_append(used_in_videos, NEW.used_in_id)
            ELSE used_in_videos
        END
    WHERE id = NEW.asset_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_asset_usage_trigger
    AFTER INSERT ON creative_asset_usage
    FOR EACH ROW
    EXECUTE FUNCTION increment_asset_usage();

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Active assets view (excluding deleted)
CREATE OR REPLACE VIEW active_creative_assets AS
SELECT
    id,
    user_id,
    campaign_id,
    asset_type,
    file_name,
    file_size_bytes,
    storage_url,
    thumbnail_url,
    width,
    height,
    duration_seconds,
    status,
    usage_count,
    last_used_at,
    ai_tags,
    tags,
    category,
    created_at,
    updated_at
FROM creative_assets
WHERE deleted_at IS NULL
ORDER BY created_at DESC;

-- Asset statistics by user
CREATE OR REPLACE VIEW creative_assets_stats_by_user AS
SELECT
    user_id,
    COUNT(*) as total_assets,
    COUNT(*) FILTER (WHERE asset_type = 'image') as image_count,
    COUNT(*) FILTER (WHERE asset_type = 'video') as video_count,
    COUNT(*) FILTER (WHERE asset_type = 'audio') as audio_count,
    SUM(file_size_bytes) as total_storage_bytes,
    ROUND(AVG(usage_count)::numeric, 2) as avg_usage_count,
    MAX(created_at) as last_upload_at
FROM creative_assets
WHERE deleted_at IS NULL
GROUP BY user_id;

-- Most used assets
CREATE OR REPLACE VIEW most_used_creative_assets AS
SELECT
    id,
    file_name,
    asset_type,
    usage_count,
    last_used_at,
    storage_url,
    thumbnail_url,
    created_at
FROM creative_assets
WHERE deleted_at IS NULL
  AND usage_count > 0
ORDER BY usage_count DESC, last_used_at DESC
LIMIT 100;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE creative_assets IS 'Uploaded creative assets (images, videos, audio, etc.) for use in campaigns';
COMMENT ON TABLE creative_asset_variations IS 'Different sizes/formats of the same asset';
COMMENT ON TABLE creative_asset_usage IS 'Track where and how assets are used';
COMMENT ON COLUMN creative_assets.ai_tags IS 'AI-generated tags from image/video analysis';
COMMENT ON COLUMN creative_assets.ai_score IS 'AI quality/engagement score (0-100)';
COMMENT ON COLUMN creative_assets.usage_count IS 'Number of times this asset has been used';
COMMENT ON COLUMN creative_assets.metadata IS 'Flexible JSON storage for custom properties';

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 001: Creative Assets completed successfully';
    RAISE NOTICE '   Tables created:';
    RAISE NOTICE '   - creative_assets';
    RAISE NOTICE '   - creative_asset_variations';
    RAISE NOTICE '   - creative_asset_usage';
    RAISE NOTICE '   Views created: 3';
    RAISE NOTICE '   Functions created: 2';
    RAISE NOTICE '   Indexes created: 20+';
END $$;
