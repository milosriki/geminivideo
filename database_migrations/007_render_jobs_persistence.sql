-- ============================================================================
-- Migration 007: Render Jobs Persistence
-- Purpose: Add tables for persistent job tracking, video outputs, and audit logs
-- Author: Automated Migration
-- ============================================================================

-- Render Jobs table for persistent job tracking
CREATE TABLE IF NOT EXISTS render_jobs (
    id VARCHAR(64) PRIMARY KEY,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    job_type VARCHAR(50),
    input_config JSONB,
    output_url TEXT,
    output_metadata JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    user_id VARCHAR(255),
    campaign_id VARCHAR(64) REFERENCES campaigns(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_user ON render_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_created ON render_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_render_jobs_campaign ON render_jobs(campaign_id);

-- Pro Jobs table for sub-jobs (captions, color grading, etc.)
CREATE TABLE IF NOT EXISTS pro_jobs (
    id VARCHAR(64) PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    input_data JSONB,
    output_data JSONB,
    error TEXT,
    parent_job_id VARCHAR(64) REFERENCES render_jobs(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pro_jobs_status ON pro_jobs(status);
CREATE INDEX IF NOT EXISTS idx_pro_jobs_parent ON pro_jobs(parent_job_id);
CREATE INDEX IF NOT EXISTS idx_pro_jobs_type ON pro_jobs(job_type);

-- Audit Log for all actions (security compliance)
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255),
    details JSONB,
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);

-- Generated Videos tracking (outputs with GCS paths and signed URLs)
CREATE TABLE IF NOT EXISTS generated_videos (
    id VARCHAR(64) PRIMARY KEY,
    render_job_id VARCHAR(64) REFERENCES render_jobs(id) ON DELETE SET NULL,
    campaign_id VARCHAR(64) REFERENCES campaigns(id) ON DELETE SET NULL,
    video_type VARCHAR(50),
    gcs_path TEXT NOT NULL,
    gcs_bucket VARCHAR(255),
    signed_url TEXT,
    signed_url_expires_at TIMESTAMPTZ,
    duration_seconds FLOAT,
    resolution VARCHAR(20),
    file_size_bytes BIGINT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_generated_videos_campaign ON generated_videos(campaign_id);
CREATE INDEX IF NOT EXISTS idx_generated_videos_job ON generated_videos(render_job_id);
CREATE INDEX IF NOT EXISTS idx_generated_videos_created ON generated_videos(created_at DESC);

-- Pipeline runs tracking
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id VARCHAR(64) PRIMARY KEY,
    pipeline_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    config JSONB,
    results JSONB,
    error TEXT,
    blueprints_generated INTEGER DEFAULT 0,
    blueprints_approved INTEGER DEFAULT 0,
    blueprints_rejected INTEGER DEFAULT 0,
    avg_council_score FLOAT,
    avg_predicted_roas FLOAT,
    duration_seconds FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    user_id VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_type ON pipeline_runs(pipeline_type);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_created ON pipeline_runs(created_at DESC);

-- Add updated_at trigger function if not exists
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_render_jobs_updated_at ON render_jobs;
CREATE TRIGGER update_render_jobs_updated_at
    BEFORE UPDATE ON render_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pro_jobs_updated_at ON pro_jobs;
CREATE TRIGGER update_pro_jobs_updated_at
    BEFORE UPDATE ON pro_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_pipeline_runs_updated_at ON pipeline_runs;
CREATE TRIGGER update_pipeline_runs_updated_at
    BEFORE UPDATE ON pipeline_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment for documentation
COMMENT ON TABLE render_jobs IS 'Persistent tracking for video render jobs, replacing in-memory dictionaries';
COMMENT ON TABLE pro_jobs IS 'Sub-jobs for pro features like captions, color grading, transitions';
COMMENT ON TABLE audit_log IS 'Security audit trail for all system actions';
COMMENT ON TABLE generated_videos IS 'Tracking generated video outputs with GCS paths and signed URLs';
COMMENT ON TABLE pipeline_runs IS 'Tracking AI pipeline executions and their results';
