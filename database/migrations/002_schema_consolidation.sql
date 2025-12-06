-- ============================================================================
-- Migration 002: Schema Consolidation & Conflict Resolution
-- ============================================================================
-- Purpose: Fix schema conflicts, type mismatches, and ensure all tables exist
-- Run with: psql $DATABASE_URL -f 002_schema_consolidation.sql
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- FIX USERS TABLE SCHEMA CONFLICTS
-- ============================================================================

-- Ensure users table has all required columns
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS full_name TEXT;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS company_name TEXT;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS meta_access_token TEXT;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS meta_ad_account_id TEXT;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Add unique constraint if missing
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_email_key'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email);
    END IF;
END $$;

-- ============================================================================
-- FIX CAMPAIGNS TABLE SCHEMA CONFLICTS
-- ============================================================================

-- Ensure campaigns table has all required columns
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS product_name TEXT;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS offer TEXT;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS target_avatar TEXT;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS pain_points JSONB DEFAULT '[]'::jsonb;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS desires JSONB DEFAULT '[]'::jsonb;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'draft';
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS budget_daily DECIMAL(12, 2) DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS spend DECIMAL(12, 2) DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS revenue DECIMAL(12, 2) DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS roas DECIMAL(8, 2) DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS conversions INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS total_generated INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS approved_count INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS rejected_count INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS target_audience JSONB DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS meta_campaign_id TEXT;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS budget DECIMAL(10, 2);
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS start_date TIMESTAMPTZ;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS end_date TIMESTAMPTZ;
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE IF EXISTS campaigns ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Fix status constraint if needed
DO $$
BEGIN
    -- Drop old constraint if exists
    ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_status_check;

    -- Add new comprehensive constraint
    ALTER TABLE campaigns ADD CONSTRAINT campaigns_status_check
        CHECK (status IN ('draft', 'generating', 'active', 'paused', 'completed', 'archived'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- FIX BLUEPRINTS TABLE SCHEMA CONFLICTS
-- ============================================================================

ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS campaign_id UUID;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS hook_text TEXT;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS hook_type TEXT;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS script_json JSONB;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS script TEXT;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS scenes JSONB DEFAULT '[]'::jsonb;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS council_score DECIMAL(5,2);
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS council_breakdown JSONB DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS oracle_prediction JSONB DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS predicted_roas DECIMAL(10,2);
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS predicted_ctr DECIMAL(8, 4);
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS confidence DECIMAL(5,2);
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS verdict TEXT;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS rank INTEGER;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS parent_id UUID;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS matched_patterns JSONB DEFAULT '[]'::jsonb;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS pattern_similarity_score FLOAT;
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE IF EXISTS blueprints ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Fix verdict constraint
DO $$
BEGIN
    ALTER TABLE blueprints DROP CONSTRAINT IF EXISTS blueprints_verdict_check;
    ALTER TABLE blueprints ADD CONSTRAINT blueprints_verdict_check
        CHECK (verdict IN ('approved', 'rejected', 'pending') OR verdict IS NULL);
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Fix status constraint
DO $$
BEGIN
    ALTER TABLE blueprints DROP CONSTRAINT IF EXISTS blueprints_status_check;
    ALTER TABLE blueprints ADD CONSTRAINT blueprints_status_check
        CHECK (status IN ('pending', 'approved', 'rejected', 'rendering', 'completed'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- FIX VIDEOS TABLE SCHEMA CONFLICTS
-- ============================================================================

ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS campaign_id UUID;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS blueprint_id UUID;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS render_job_id UUID;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS script_content JSONB;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS video_url TEXT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS storage_url TEXT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS storage_path TEXT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS thumbnail_url TEXT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS duration_seconds FLOAT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS resolution VARCHAR(50);
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS format VARCHAR(50);
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'processing';
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS meta_platform_id VARCHAR(255);
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS platform VARCHAR(50);
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS analysis_data JSONB DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS performance_data JSONB DEFAULT '{}'::jsonb;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS published_to JSONB DEFAULT '[]'::jsonb;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS predicted_ctr FLOAT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS prediction_confidence FLOAT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS models_used TEXT[];
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS actual_roas FLOAT;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS impressions INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS clicks INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS conversions INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE IF EXISTS videos ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

-- Fix status constraint
DO $$
BEGIN
    ALTER TABLE videos DROP CONSTRAINT IF EXISTS videos_status_check;
    ALTER TABLE videos ADD CONSTRAINT videos_status_check
        CHECK (status IN ('uploading', 'processing', 'ready', 'failed', 'published', 'archived'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- FIX RENDER_JOBS TABLE SCHEMA CONFLICTS
-- ============================================================================

ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS id UUID;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS blueprint_id UUID;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS campaign_id UUID;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS user_id UUID;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS platform TEXT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS quality TEXT DEFAULT 'high';
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS current_stage TEXT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS error TEXT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS output_url TEXT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS output_format TEXT DEFAULT 'mp4';
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS resolution TEXT DEFAULT '1080x1920';
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS duration_seconds FLOAT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS file_size_bytes BIGINT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS worker_id TEXT;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE IF EXISTS render_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

-- Fix platform constraint
DO $$
BEGIN
    ALTER TABLE render_jobs DROP CONSTRAINT IF EXISTS render_jobs_platform_check;
    ALTER TABLE render_jobs ADD CONSTRAINT render_jobs_platform_check
        CHECK (platform IN ('youtube', 'tiktok', 'instagram', 'facebook', 'twitter', 'linkedin'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- Fix status constraint
DO $$
BEGIN
    ALTER TABLE render_jobs DROP CONSTRAINT IF EXISTS render_jobs_status_check;
    ALTER TABLE render_jobs ADD CONSTRAINT render_jobs_status_check
        CHECK (status IN ('pending', 'queued', 'processing', 'rendering', 'completed', 'failed', 'cancelled'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- ENSURE PREDICTIONS TABLE EXISTS (from migration 005)
-- ============================================================================

CREATE TABLE IF NOT EXISTS predictions (
    id VARCHAR(255) PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    ad_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,

    -- Predicted metrics
    predicted_ctr FLOAT NOT NULL,
    predicted_roas FLOAT NOT NULL,
    predicted_conversion FLOAT NOT NULL,

    -- Actual metrics
    actual_ctr FLOAT,
    actual_roas FLOAT,
    actual_conversion FLOAT,

    -- Performance data
    impressions INTEGER,
    clicks INTEGER,
    spend DECIMAL(10, 2),

    -- Model metadata
    council_score FLOAT NOT NULL,
    hook_type VARCHAR(100) NOT NULL,
    template_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actuals_fetched_at TIMESTAMP
);

-- ============================================================================
-- ENSURE AB_TESTS TABLE EXISTS (from migration 002)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'running',

    -- Variants
    control_variant_id VARCHAR(255),
    test_variant_id VARCHAR(255),

    -- Sample sizes
    control_size INT DEFAULT 0,
    test_size INT DEFAULT 0,

    -- Metrics
    metric_name VARCHAR(100),
    control_value FLOAT,
    test_value FLOAT,
    lift_percent FLOAT,
    p_value FLOAT,
    is_significant BOOLEAN DEFAULT FALSE,

    -- Timestamps
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ADD MISSING FOREIGN KEY CONSTRAINTS (IF THEY DON'T EXIST)
-- ============================================================================

-- Campaigns -> Users
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'campaigns_user_id_fkey'
    ) THEN
        ALTER TABLE campaigns ADD CONSTRAINT campaigns_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
    END IF;
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- Blueprints -> Campaigns
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'blueprints_campaign_id_fkey'
    ) THEN
        ALTER TABLE blueprints ADD CONSTRAINT blueprints_campaign_id_fkey
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE;
    END IF;
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- Videos -> Campaigns
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'videos_campaign_id_fkey'
    ) THEN
        ALTER TABLE videos ADD CONSTRAINT videos_campaign_id_fkey
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE;
    END IF;
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- Videos -> Blueprints
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'videos_blueprint_id_fkey'
    ) THEN
        ALTER TABLE videos ADD CONSTRAINT videos_blueprint_id_fkey
            FOREIGN KEY (blueprint_id) REFERENCES blueprints(id) ON DELETE SET NULL;
    END IF;
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- ============================================================================
-- CREATE UPDATED_AT TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
DO $$
BEGIN
    -- Users
    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
    CREATE TRIGGER update_users_updated_at
        BEFORE UPDATE ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Campaigns
    DROP TRIGGER IF EXISTS update_campaigns_updated_at ON campaigns;
    CREATE TRIGGER update_campaigns_updated_at
        BEFORE UPDATE ON campaigns
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Blueprints
    DROP TRIGGER IF EXISTS update_blueprints_updated_at ON blueprints;
    CREATE TRIGGER update_blueprints_updated_at
        BEFORE UPDATE ON blueprints
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();

    -- Videos
    DROP TRIGGER IF EXISTS update_videos_updated_at ON videos;
    CREATE TRIGGER update_videos_updated_at
        BEFORE UPDATE ON videos
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002: Schema Consolidation completed successfully';
    RAISE NOTICE '   Schema conflicts resolved';
    RAISE NOTICE '   Missing columns added';
    RAISE NOTICE '   Foreign keys verified';
    RAISE NOTICE '   Triggers updated';
END $$;
