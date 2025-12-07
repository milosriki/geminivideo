-- Job queue table for SafeExecutor
CREATE TABLE IF NOT EXISTS pending_ad_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    ad_entity_id VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL, -- 'campaign', 'ad_set', 'ad'
    change_type VARCHAR(50) NOT NULL, -- 'budget_update', 'bid_update', 'pause', 'activate'
    current_value JSONB,
    requested_value JSONB NOT NULL,
    jitter_ms_min INT DEFAULT 3000,
    jitter_ms_max INT DEFAULT 18000,
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'claimed', 'executed', 'failed'
    earliest_execute_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confidence_score FLOAT DEFAULT 1.0,
    claimed_by VARCHAR(255),
    claimed_at TIMESTAMP WITH TIME ZONE,
    executed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pending_ad_changes_status_execution 
ON pending_ad_changes(status, earliest_execute_at);

CREATE INDEX IF NOT EXISTS idx_pending_ad_changes_tenant_entity 
ON pending_ad_changes(tenant_id, ad_entity_id);

-- Function to claim pending ad changes safely
CREATE OR REPLACE FUNCTION claim_pending_ad_change(worker_id VARCHAR) 
RETURNS TABLE (
    id UUID,
    tenant_id UUID,
    ad_entity_id VARCHAR,
    entity_type VARCHAR,
    change_type VARCHAR,
    current_value JSONB,
    requested_value JSONB
) AS $$
BEGIN
    RETURN QUERY
    UPDATE pending_ad_changes
    SET 
        status = 'claimed',
        claimed_by = worker_id,
        claimed_at = NOW(),
        updated_at = NOW()
    WHERE id = (
        SELECT id
        FROM pending_ad_changes
        WHERE status = 'pending'
        AND earliest_execute_at <= NOW()
        ORDER BY earliest_execute_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    RETURNING 
        id, 
        tenant_id, 
        ad_entity_id, 
        entity_type, 
        change_type, 
        current_value, 
        requested_value;
END;
$$ LANGUAGE plpgsql;
