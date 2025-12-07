-- Migration 004: PG-Boss Job Queue Extension
-- Purpose: Set up pg-boss for SafeExecutor job queue with retry logic
-- Created: 2025-12-07
-- Dependencies: None

-- Note: pg-boss automatically creates its own schema and tables when initialized
-- This migration creates additional helper tables and views for our use case

-- Job Configuration Table
-- Custom configuration for different job types
CREATE TABLE IF NOT EXISTS job_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_name VARCHAR(255) NOT NULL UNIQUE,  -- 'ad-change', 'budget-optimization', etc.

    -- Retry configuration
    max_retry_attempts INTEGER NOT NULL DEFAULT 5,
    retry_backoff_ms INTEGER NOT NULL DEFAULT 5000,  -- Exponential backoff base
    retry_limit_minutes INTEGER NOT NULL DEFAULT 60,

    -- Timeout configuration
    expire_in_seconds INTEGER NOT NULL DEFAULT 300,  -- 5 minutes default
    retention_days INTEGER NOT NULL DEFAULT 7,

    -- Rate limiting (jobs per tenant per hour)
    rate_limit_per_tenant_per_hour INTEGER,

    -- Priority
    default_priority INTEGER NOT NULL DEFAULT 0,  -- -1000 to 1000

    -- Active/inactive
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Job Execution History
-- Detailed logging for debugging and monitoring
CREATE TABLE IF NOT EXISTS job_execution_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Job identification
    job_id UUID NOT NULL,                    -- pg-boss job ID
    job_name VARCHAR(255) NOT NULL,
    tenant_id VARCHAR(255),

    -- Execution tracking
    attempt_number INTEGER NOT NULL,
    status VARCHAR(50) NOT NULL,             -- 'active', 'completed', 'failed', 'retry', 'expired'

    -- Payload
    job_data JSONB,
    result_data JSONB,
    error_message TEXT,
    error_stack TEXT,

    -- Timing
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,

    -- Retry context
    will_retry BOOLEAN DEFAULT false,
    next_retry_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Job Rate Limit Tracker
-- Enforces per-tenant rate limits
CREATE TABLE IF NOT EXISTS job_rate_limit_tracker (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    job_count INTEGER NOT NULL DEFAULT 0,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one tracker per tenant per job per hour window
    UNIQUE(tenant_id, job_name, window_start)
);

-- Indexes for job_config
CREATE INDEX IF NOT EXISTS idx_job_config_job_name ON job_config(job_name);
CREATE INDEX IF NOT EXISTS idx_job_config_is_active ON job_config(is_active);

-- Indexes for job_execution_history
CREATE INDEX IF NOT EXISTS idx_job_execution_history_job_id ON job_execution_history(job_id);
CREATE INDEX IF NOT EXISTS idx_job_execution_history_job_name ON job_execution_history(job_name);
CREATE INDEX IF NOT EXISTS idx_job_execution_history_tenant_id ON job_execution_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_execution_history_status ON job_execution_history(status);
CREATE INDEX IF NOT EXISTS idx_job_execution_history_started_at ON job_execution_history(started_at DESC);

-- Indexes for job_rate_limit_tracker
CREATE INDEX IF NOT EXISTS idx_job_rate_limit_tracker_tenant ON job_rate_limit_tracker(tenant_id, job_name);
CREATE INDEX IF NOT EXISTS idx_job_rate_limit_tracker_window ON job_rate_limit_tracker(window_start, window_end);

-- Updated_at triggers
CREATE TRIGGER trigger_job_config_updated_at
BEFORE UPDATE ON job_config
FOR EACH ROW
EXECUTE FUNCTION update_ad_change_history_updated_at();

CREATE TRIGGER trigger_job_rate_limit_tracker_updated_at
BEFORE UPDATE ON job_rate_limit_tracker
FOR EACH ROW
EXECUTE FUNCTION update_ad_change_history_updated_at();

-- Insert default job configurations
INSERT INTO job_config (job_name, max_retry_attempts, retry_backoff_ms, expire_in_seconds, rate_limit_per_tenant_per_hour, default_priority, description) VALUES
    ('ad-change', 5, 5000, 300, 15, 10, 'Ad budget/status changes via Meta API with safety checks'),
    ('budget-optimization', 3, 10000, 600, 10, 5, 'Thompson/Battle-Hardened sampler optimization decisions'),
    ('creative-dna-extraction', 2, 15000, 900, 5, 0, 'Extract creative DNA from winning ads'),
    ('actuals-sync', 5, 5000, 300, NULL, -5, 'Fetch actual performance data from Meta API'),
    ('attribution-matching', 10, 2000, 60, NULL, -10, 'Match conversions to clicks (3-layer attribution)'),
    ('synthetic-revenue-calculation', 3, 5000, 120, NULL, 0, 'Calculate synthetic revenue from CRM stage changes')
ON CONFLICT (job_name) DO NOTHING;

-- View: Job Queue Health (monitoring)
CREATE OR REPLACE VIEW v_job_queue_health AS
WITH recent_jobs AS (
    SELECT
        job_name,
        status,
        COUNT(*) AS job_count,
        AVG(duration_ms) AS avg_duration_ms,
        MAX(duration_ms) AS max_duration_ms,
        COUNT(*) FILTER (WHERE will_retry = true) AS retry_count
    FROM job_execution_history
    WHERE started_at > NOW() - INTERVAL '1 hour'
    GROUP BY job_name, status
)
SELECT
    job_name,
    status,
    job_count,
    ROUND(avg_duration_ms::NUMERIC, 2) AS avg_duration_ms,
    max_duration_ms,
    retry_count,
    ROUND(100.0 * retry_count / NULLIF(job_count, 0), 2) AS retry_rate_pct
FROM recent_jobs
ORDER BY job_name, status;

-- View: Failed Jobs (requires attention)
CREATE OR REPLACE VIEW v_failed_jobs AS
SELECT
    jeh.id,
    jeh.job_id,
    jeh.job_name,
    jeh.tenant_id,
    jeh.attempt_number,
    jeh.error_message,
    jeh.started_at,
    jeh.duration_ms,
    jeh.will_retry,
    jeh.next_retry_at
FROM job_execution_history jeh
WHERE jeh.status = 'failed'
    AND jeh.started_at > NOW() - INTERVAL '24 hours'
ORDER BY jeh.started_at DESC;

-- View: Job Performance by Tenant
CREATE OR REPLACE VIEW v_job_performance_by_tenant AS
SELECT
    tenant_id,
    job_name,
    COUNT(*) AS total_jobs,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_jobs,
    COUNT(*) FILTER (WHERE status = 'failed') AS failed_jobs,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / NULLIF(COUNT(*), 0), 2) AS success_rate_pct,
    AVG(duration_ms) FILTER (WHERE status = 'completed') AS avg_duration_ms,
    MIN(started_at) AS first_job_at,
    MAX(started_at) AS last_job_at
FROM job_execution_history
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY tenant_id, job_name
ORDER BY tenant_id, total_jobs DESC;

-- View: Rate Limit Status (current hour)
CREATE OR REPLACE VIEW v_rate_limit_status AS
SELECT
    rlt.tenant_id,
    rlt.job_name,
    rlt.job_count AS jobs_this_hour,
    jc.rate_limit_per_tenant_per_hour AS hourly_limit,
    CASE
        WHEN jc.rate_limit_per_tenant_per_hour IS NULL THEN 'NO_LIMIT'
        WHEN rlt.job_count >= jc.rate_limit_per_tenant_per_hour THEN 'LIMIT_REACHED'
        WHEN rlt.job_count >= jc.rate_limit_per_tenant_per_hour * 0.8 THEN 'WARNING'
        ELSE 'OK'
    END AS status,
    ROUND(100.0 * rlt.job_count / NULLIF(jc.rate_limit_per_tenant_per_hour, 0), 2) AS usage_pct,
    rlt.window_start,
    rlt.window_end
FROM job_rate_limit_tracker rlt
JOIN job_config jc ON rlt.job_name = jc.job_name
WHERE rlt.window_end > NOW()
ORDER BY rlt.tenant_id, rlt.job_name;

-- Function: Check rate limit before queuing job
CREATE OR REPLACE FUNCTION check_job_rate_limit(
    p_tenant_id VARCHAR(255),
    p_job_name VARCHAR(255)
)
RETURNS TABLE(
    allowed BOOLEAN,
    current_count INTEGER,
    limit_value INTEGER,
    window_end TIMESTAMPTZ
) AS $$
DECLARE
    v_config RECORD;
    v_tracker RECORD;
    v_current_window_start TIMESTAMPTZ;
    v_current_window_end TIMESTAMPTZ;
BEGIN
    -- Get job config
    SELECT * INTO v_config
    FROM job_config
    WHERE job_name = p_job_name AND is_active = true;

    -- If no rate limit configured, allow
    IF v_config.rate_limit_per_tenant_per_hour IS NULL THEN
        RETURN QUERY SELECT true, 0, NULL::INTEGER, NULL::TIMESTAMPTZ;
        RETURN;
    END IF;

    -- Calculate current hour window
    v_current_window_start := DATE_TRUNC('hour', NOW());
    v_current_window_end := v_current_window_start + INTERVAL '1 hour';

    -- Get or create tracker for current window
    INSERT INTO job_rate_limit_tracker (tenant_id, job_name, window_start, window_end, job_count)
    VALUES (p_tenant_id, p_job_name, v_current_window_start, v_current_window_end, 0)
    ON CONFLICT (tenant_id, job_name, window_start)
    DO NOTHING;

    -- Get current count
    SELECT * INTO v_tracker
    FROM job_rate_limit_tracker
    WHERE tenant_id = p_tenant_id
        AND job_name = p_job_name
        AND window_start = v_current_window_start;

    -- Check if limit reached
    RETURN QUERY SELECT
        (v_tracker.job_count < v_config.rate_limit_per_tenant_per_hour),
        v_tracker.job_count,
        v_config.rate_limit_per_tenant_per_hour,
        v_tracker.window_end;
END;
$$ LANGUAGE plpgsql;

-- Function: Increment rate limit counter (call when job is queued)
CREATE OR REPLACE FUNCTION increment_job_rate_limit(
    p_tenant_id VARCHAR(255),
    p_job_name VARCHAR(255)
)
RETURNS VOID AS $$
DECLARE
    v_current_window_start TIMESTAMPTZ;
    v_current_window_end TIMESTAMPTZ;
BEGIN
    v_current_window_start := DATE_TRUNC('hour', NOW());
    v_current_window_end := v_current_window_start + INTERVAL '1 hour';

    INSERT INTO job_rate_limit_tracker (tenant_id, job_name, window_start, window_end, job_count)
    VALUES (p_tenant_id, p_job_name, v_current_window_start, v_current_window_end, 1)
    ON CONFLICT (tenant_id, job_name, window_start)
    DO UPDATE SET
        job_count = job_rate_limit_tracker.job_count + 1,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function: Clean up old job execution history
CREATE OR REPLACE FUNCTION cleanup_old_job_history()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    -- Delete job execution history older than retention period
    DELETE FROM job_execution_history
    WHERE started_at < NOW() - (
        SELECT COALESCE(MAX(retention_days), 7)::INTEGER * INTERVAL '1 day'
        FROM job_config
    );

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;

    -- Delete old rate limit trackers (keep last 30 days)
    DELETE FROM job_rate_limit_tracker
    WHERE window_end < NOW() - INTERVAL '30 days';

    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Migration complete
COMMENT ON TABLE job_config IS 'Configuration for pg-boss job types (retry, timeout, rate limits)';
COMMENT ON TABLE job_execution_history IS 'Detailed execution history for all jobs (debugging and monitoring)';
COMMENT ON TABLE job_rate_limit_tracker IS 'Per-tenant rate limit enforcement for job queuing';
COMMENT ON VIEW v_job_queue_health IS 'Job queue health metrics (last hour)';
COMMENT ON VIEW v_failed_jobs IS 'Failed jobs in last 24 hours requiring investigation';
COMMENT ON VIEW v_job_performance_by_tenant IS 'Job performance metrics by tenant (last 7 days)';
COMMENT ON VIEW v_rate_limit_status IS 'Current rate limit status for active jobs';
COMMENT ON FUNCTION check_job_rate_limit IS 'Check if job can be queued without exceeding rate limit';
COMMENT ON FUNCTION increment_job_rate_limit IS 'Increment rate limit counter when job is queued';
COMMENT ON FUNCTION cleanup_old_job_history IS 'Cleanup old job execution history (run daily via cron)';
