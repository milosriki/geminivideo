-- Migration: 005_pending_ad_changes.sql
-- Description: Job queue table for SafeExecutor pattern
-- Purpose: Store and manage pending ad entity changes with jitter and distributed locking

-- Create the pending_ad_changes table
CREATE TABLE IF NOT EXISTS pending_ad_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id TEXT NOT NULL,
    ad_entity_id TEXT NOT NULL,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('campaign', 'adset', 'ad')),
    change_type TEXT NOT NULL CHECK (change_type IN ('budget', 'status', 'bid')),
    current_value NUMERIC,
    requested_value NUMERIC,
    jitter_ms_min INTEGER DEFAULT 3000,
    jitter_ms_max INTEGER DEFAULT 18000,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'claimed', 'executing', 'completed', 'failed')),
    earliest_execute_at TIMESTAMPTZ NOT NULL,
    confidence_score FLOAT,
    claimed_by TEXT,
    claimed_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX idx_pending_ad_changes_status_time ON pending_ad_changes(status, earliest_execute_at);
CREATE INDEX idx_pending_ad_changes_tenant ON pending_ad_changes(tenant_id, ad_entity_id);

-- Function to claim a pending ad change using distributed locking
-- This ensures that multiple workers don't process the same change
CREATE OR REPLACE FUNCTION claim_pending_ad_change(worker_id TEXT)
RETURNS TABLE(
    id UUID,
    tenant_id TEXT,
    ad_entity_id TEXT,
    entity_type TEXT,
    change_type TEXT,
    current_value NUMERIC,
    requested_value NUMERIC,
    jitter_ms_min INTEGER,
    jitter_ms_max INTEGER,
    status TEXT,
    earliest_execute_at TIMESTAMPTZ,
    confidence_score FLOAT,
    claimed_by TEXT,
    claimed_at TIMESTAMPTZ,
    executed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ
) AS $$
DECLARE
    claimed_record RECORD;
BEGIN
    -- Select the next pending change that's ready to execute
    -- FOR UPDATE SKIP LOCKED ensures distributed locking without blocking
    SELECT * INTO claimed_record
    FROM pending_ad_changes
    WHERE status = 'pending'
      AND earliest_execute_at <= NOW()
    ORDER BY earliest_execute_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    -- If we found a record, claim it
    IF claimed_record.id IS NOT NULL THEN
        UPDATE pending_ad_changes
        SET status = 'claimed',
            claimed_by = worker_id,
            claimed_at = NOW()
        WHERE pending_ad_changes.id = claimed_record.id;

        -- Return the claimed record
        RETURN QUERY
        SELECT
            p.id,
            p.tenant_id,
            p.ad_entity_id,
            p.entity_type,
            p.change_type,
            p.current_value,
            p.requested_value,
            p.jitter_ms_min,
            p.jitter_ms_max,
            p.status,
            p.earliest_execute_at,
            p.confidence_score,
            p.claimed_by,
            p.claimed_at,
            p.executed_at,
            p.error_message,
            p.created_at
        FROM pending_ad_changes p
        WHERE p.id = claimed_record.id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Add comment for documentation
COMMENT ON TABLE pending_ad_changes IS 'Job queue for SafeExecutor: stores pending ad entity changes with jitter and distributed locking';
COMMENT ON FUNCTION claim_pending_ad_change IS 'Claims the next available pending change for a worker using FOR UPDATE SKIP LOCKED for distributed locking';
