-- Migration 007: Render Jobs Persistence
-- Provides persistent job tracking for render operations

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
    campaign_id VARCHAR(64) REFERENCES campaigns(id)
);

CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_user ON render_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_created ON render_jobs(created_at DESC);

-- Pro Jobs table
CREATE TABLE IF NOT EXISTS pro_jobs (
    id VARCHAR(64) PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    input_data JSONB,
    output_data JSONB,
    error TEXT,
    parent_job_id VARCHAR(64) REFERENCES render_jobs(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pro_jobs_status ON pro_jobs(status);
CREATE INDEX IF NOT EXISTS idx_pro_jobs_parent ON pro_jobs(parent_job_id);

-- Audit Log for all actions
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(255),
    details JSONB,
    user_id VARCHAR(255),
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created ON audit_log(created_at DESC);

-- Generated Videos tracking
CREATE TABLE IF NOT EXISTS generated_videos (
    id VARCHAR(64) PRIMARY KEY,
    render_job_id VARCHAR(64) REFERENCES render_jobs(id),
    campaign_id VARCHAR(64) REFERENCES campaigns(id),
    video_type VARCHAR(50),
    gcs_path TEXT NOT NULL,
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

-- Comments for documentation
COMMENT ON TABLE render_jobs IS 'Persistent render job tracking for async video processing';
COMMENT ON TABLE pro_jobs IS 'Sub-tasks for PRO video processing modules';
COMMENT ON TABLE audit_log IS 'Comprehensive audit trail for all actions';
COMMENT ON TABLE generated_videos IS 'Tracking for all generated video assets';
