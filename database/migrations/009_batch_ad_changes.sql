-- Migration: Add batch claim function for pending_ad_changes
-- Purpose: Enable 10x faster execution by claiming multiple changes at once
-- Created: 2025-01-08
-- Note: This function works with the schema from 005_pending_ad_changes.sql

-- Function to claim a batch of pending ad changes
-- Works with the existing schema (ad_entity_id, entity_type, etc.)
CREATE OR REPLACE FUNCTION claim_pending_ad_changes_batch(
    worker_id TEXT,
    batch_size INTEGER DEFAULT 50
)
RETURNS TABLE (
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
    claimed_ids UUID[];
BEGIN
    -- Select and lock batch of pending changes
    SELECT ARRAY_AGG(pac.id) INTO claimed_ids
    FROM (
        SELECT id
        FROM pending_ad_changes
        WHERE status = 'pending'
          AND earliest_execute_at <= NOW()
        ORDER BY earliest_execute_at ASC
        LIMIT batch_size
        FOR UPDATE SKIP LOCKED
    ) pac;

    -- If we found records, claim them
    IF claimed_ids IS NOT NULL AND array_length(claimed_ids, 1) > 0 THEN
        UPDATE pending_ad_changes
        SET status = 'claimed',
            claimed_by = worker_id,
            claimed_at = NOW()
        WHERE id = ANY(claimed_ids);

        -- Return the claimed records
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
        WHERE p.id = ANY(claimed_ids)
        ORDER BY p.earliest_execute_at ASC;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION claim_pending_ad_changes_batch IS 
    'Claims a batch of pending ad changes for a worker using FOR UPDATE SKIP LOCKED for distributed locking. Enables 10x faster execution by processing multiple changes in a single API call.';

