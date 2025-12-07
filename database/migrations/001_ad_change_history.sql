-- Migration 001: Ad Change History Table
-- Purpose: Track all ad changes for SafeExecutor rule enforcement
-- Created: 2025-12-07
-- Dependencies: None

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ad Change History Table
-- Stores every ad change with metadata for safety rules (rate limiting, budget velocity)
CREATE TABLE IF NOT EXISTS ad_change_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,
    campaign_id VARCHAR(255) NOT NULL,
    ad_id VARCHAR(255),
    adset_id VARCHAR(255),

    -- Change tracking
    change_type VARCHAR(50) NOT NULL,  -- 'BUDGET_INCREASE', 'BUDGET_DECREASE', 'STATUS_CHANGE', 'TARGETING_UPDATE'
    old_value JSONB NOT NULL,          -- Previous state (e.g., {"budget": 100, "status": "ACTIVE"})
    new_value JSONB NOT NULL,          -- New state (e.g., {"budget": 150, "status": "ACTIVE"})
    change_percentage NUMERIC(10, 4),  -- Percentage change (for budget changes)

    -- Attribution
    triggered_by VARCHAR(100) NOT NULL, -- 'thompson_sampler', 'battle_hardened', 'auto_promoter', 'manual'
    ml_confidence NUMERIC(5, 4),        -- ML confidence score (0-1)
    reason TEXT,                        -- Human-readable reason for change

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'executing', 'completed', 'failed', 'blocked'
    error_message TEXT,                 -- Error details if failed

    -- Safety checks
    rate_limit_passed BOOLEAN DEFAULT true,
    velocity_check_passed BOOLEAN DEFAULT true,
    safety_override BOOLEAN DEFAULT false, -- Manual override flag

    -- Execution tracking
    queued_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    meta_response JSONB,                -- Meta API response
    execution_duration_ms INTEGER,      -- Time taken to execute (milliseconds)

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ad_change_history_tenant_id ON ad_change_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ad_change_history_campaign_id ON ad_change_history(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ad_change_history_ad_id ON ad_change_history(ad_id);
CREATE INDEX IF NOT EXISTS idx_ad_change_history_change_type ON ad_change_history(change_type);
CREATE INDEX IF NOT EXISTS idx_ad_change_history_status ON ad_change_history(status);
CREATE INDEX IF NOT EXISTS idx_ad_change_history_created_at ON ad_change_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ad_change_history_triggered_by ON ad_change_history(triggered_by);

-- Composite index for rate limiting queries (check last N changes per campaign in last hour)
CREATE INDEX IF NOT EXISTS idx_ad_change_history_rate_limit
ON ad_change_history(campaign_id, created_at DESC)
WHERE status IN ('executing', 'completed');

-- Composite index for budget velocity queries (check budget changes in last 6 hours)
CREATE INDEX IF NOT EXISTS idx_ad_change_history_budget_velocity
ON ad_change_history(campaign_id, created_at DESC)
WHERE change_type IN ('BUDGET_INCREASE', 'BUDGET_DECREASE');

-- Updated_at trigger function
CREATE OR REPLACE FUNCTION update_ad_change_history_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Updated_at trigger
CREATE TRIGGER trigger_ad_change_history_updated_at
BEFORE UPDATE ON ad_change_history
FOR EACH ROW
EXECUTE FUNCTION update_ad_change_history_updated_at();

-- View: Recent Budget Changes (last 24 hours)
-- Used for quick debugging and velocity checks
CREATE OR REPLACE VIEW v_recent_budget_changes AS
SELECT
    id,
    tenant_id,
    campaign_id,
    ad_id,
    change_type,
    (old_value->>'budget')::NUMERIC AS old_budget,
    (new_value->>'budget')::NUMERIC AS new_budget,
    change_percentage,
    triggered_by,
    ml_confidence,
    status,
    rate_limit_passed,
    velocity_check_passed,
    created_at,
    completed_at,
    execution_duration_ms
FROM ad_change_history
WHERE
    change_type IN ('BUDGET_INCREASE', 'BUDGET_DECREASE')
    AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- View: Campaign Activity Summary (for rate limiting)
-- Shows how many changes per campaign in last hour
CREATE OR REPLACE VIEW v_campaign_activity_summary AS
SELECT
    campaign_id,
    tenant_id,
    COUNT(*) AS total_changes,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '1 hour') AS changes_last_hour,
    COUNT(*) FILTER (WHERE change_type IN ('BUDGET_INCREASE', 'BUDGET_DECREASE')
                     AND created_at > NOW() - INTERVAL '6 hours') AS budget_changes_last_6h,
    MAX(created_at) AS last_change_at,
    AVG(execution_duration_ms) AS avg_execution_ms
FROM ad_change_history
WHERE status IN ('executing', 'completed')
GROUP BY campaign_id, tenant_id;

-- View: Safety Check Failures (for monitoring)
CREATE OR REPLACE VIEW v_safety_check_failures AS
SELECT
    id,
    tenant_id,
    campaign_id,
    change_type,
    triggered_by,
    CASE
        WHEN NOT rate_limit_passed THEN 'RATE_LIMIT'
        WHEN NOT velocity_check_passed THEN 'VELOCITY_LIMIT'
        WHEN status = 'blocked' THEN 'BLOCKED'
        WHEN status = 'failed' THEN 'FAILED'
    END AS failure_reason,
    error_message,
    created_at
FROM ad_change_history
WHERE
    NOT rate_limit_passed
    OR NOT velocity_check_passed
    OR status IN ('blocked', 'failed')
ORDER BY created_at DESC;

-- Migration complete
COMMENT ON TABLE ad_change_history IS 'Tracks all ad changes for SafeExecutor rule enforcement and audit trail';
COMMENT ON VIEW v_recent_budget_changes IS 'Recent budget changes in last 24 hours for debugging';
COMMENT ON VIEW v_campaign_activity_summary IS 'Campaign activity summary for rate limiting checks';
COMMENT ON VIEW v_safety_check_failures IS 'Safety check failures for monitoring and alerting';
