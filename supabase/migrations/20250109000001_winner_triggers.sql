-- ============================================================================
-- WINNER DETECTION AND AUTO-INDEXING TRIGGERS
-- Migration: 20250109000001
-- Description: Automatic detection of winning ads and triggering RAG indexing
-- ============================================================================

-- Create pending_jobs table if it doesn't exist (for background job queue)
CREATE TABLE IF NOT EXISTS pending_jobs (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_type VARCHAR(100) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3
);

-- Indexes for efficient job processing
CREATE INDEX IF NOT EXISTS idx_pending_jobs_status ON pending_jobs(status);
CREATE INDEX IF NOT EXISTS idx_pending_jobs_type ON pending_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_pending_jobs_created ON pending_jobs(created_at DESC);

-- ============================================================================
-- WINNER DETECTION FUNCTION
-- ============================================================================

-- Function to check if ad is a winner and trigger RAG indexing
CREATE OR REPLACE FUNCTION check_winner_and_index()
RETURNS TRIGGER AS $$
DECLARE
    v_ctr FLOAT;
    v_roas FLOAT;
    v_hours_live INT;
    v_video_id UUID;
    v_ad_id UUID;
    v_is_winner BOOLEAN;
BEGIN
    -- Get performance metrics
    v_ctr := NEW.ctr;
    v_roas := COALESCE((NEW.raw_data->>'roas')::FLOAT, 0.0);
    v_hours_live := EXTRACT(EPOCH FROM (NOW() - NEW.created_at)) / 3600;
    
    -- Determine if this is a winner
    -- Criteria: CTR > 3% OR ROAS > 3.0, at least 24h old, 1000+ impressions
    v_is_winner := (
        v_hours_live >= 24 
        AND NEW.impressions >= 1000 
        AND (v_ctr > 0.03 OR v_roas > 3.0)
    );
    
    -- Only proceed if it's a winner
    IF v_is_winner THEN
        v_video_id := NEW.video_id;
        
        -- Try to get associated ad_id from ads table
        SELECT ad_id INTO v_ad_id
        FROM ads
        WHERE video_id = v_video_id
        LIMIT 1;
        
        -- Check if we already queued this for indexing (avoid duplicates)
        IF NOT EXISTS (
            SELECT 1 FROM pending_jobs
            WHERE job_type = 'rag_index_winner'
            AND payload->>'video_id' = v_video_id::TEXT
            AND status IN ('pending', 'processing')
        ) THEN
            -- Queue RAG indexing job
            INSERT INTO pending_jobs (job_type, payload, status, created_at)
            VALUES (
                'rag_index_winner',
                jsonb_build_object(
                    'video_id', v_video_id,
                    'ad_id', v_ad_id,
                    'ctr', v_ctr,
                    'roas', v_roas,
                    'impressions', NEW.impressions,
                    'platform', NEW.platform,
                    'date', NEW.date,
                    'winner_criteria', CASE
                        WHEN v_ctr > 0.03 AND v_roas > 3.0 THEN 'both'
                        WHEN v_ctr > 0.03 THEN 'ctr'
                        ELSE 'roas'
                    END
                ),
                'pending',
                NOW()
            );
            
            -- Log the winner detection (optional, for analytics)
            RAISE NOTICE 'Winner detected: video_id=%, ctr=%, roas=%, impressions=%', 
                v_video_id, v_ctr, v_roas, NEW.impressions;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Drop existing trigger if it exists
DROP TRIGGER IF EXISTS trigger_winner_detection ON performance_metrics;

-- Create trigger on performance_metrics table
-- Fires after INSERT or UPDATE when impressions >= 1000
CREATE TRIGGER trigger_winner_detection
AFTER INSERT OR UPDATE ON performance_metrics
FOR EACH ROW
WHEN (NEW.impressions >= 1000)
EXECUTE FUNCTION check_winner_and_index();

-- ============================================================================
-- WINNER REPLICATION SUPPORT
-- ============================================================================

-- Create winner_insights table to store analyzed winner data
CREATE TABLE IF NOT EXISTS winner_insights (
    insight_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID REFERENCES videos(id) ON DELETE CASCADE,
    ad_id UUID,
    winner_type VARCHAR(50), -- 'ctr', 'roas', 'both'
    metrics JSONB NOT NULL, -- Full metrics snapshot
    creative_elements JSONB, -- Extracted creative DNA
    hook_analysis JSONB, -- Hook classification and effectiveness
    script_patterns JSONB, -- Script structure patterns
    audience_insights JSONB, -- Targeting and audience data
    indexed_at TIMESTAMPTZ DEFAULT NOW(),
    rag_indexed BOOLEAN DEFAULT FALSE,
    rag_indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for winner_insights
CREATE INDEX IF NOT EXISTS idx_winner_insights_video ON winner_insights(video_id);
CREATE INDEX IF NOT EXISTS idx_winner_insights_ad ON winner_insights(ad_id);
CREATE INDEX IF NOT EXISTS idx_winner_insights_type ON winner_insights(winner_type);
CREATE INDEX IF NOT EXISTS idx_winner_insights_rag ON winner_insights(rag_indexed);
CREATE INDEX IF NOT EXISTS idx_winner_insights_created ON winner_insights(created_at DESC);

-- ============================================================================
-- WINNER STATS FUNCTION
-- ============================================================================

-- Function to get winner statistics
CREATE OR REPLACE FUNCTION get_winner_stats(
    p_days_back INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_winners BIGINT,
    ctr_winners BIGINT,
    roas_winners BIGINT,
    both_winners BIGINT,
    avg_winner_ctr FLOAT,
    avg_winner_roas FLOAT,
    pending_index_jobs BIGINT,
    indexed_winners BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(DISTINCT wi.video_id) AS total_winners,
        COUNT(DISTINCT wi.video_id) FILTER (WHERE wi.winner_type IN ('ctr', 'both')) AS ctr_winners,
        COUNT(DISTINCT wi.video_id) FILTER (WHERE wi.winner_type IN ('roas', 'both')) AS roas_winners,
        COUNT(DISTINCT wi.video_id) FILTER (WHERE wi.winner_type = 'both') AS both_winners,
        AVG((wi.metrics->>'ctr')::FLOAT) FILTER (WHERE wi.metrics->>'ctr' IS NOT NULL) AS avg_winner_ctr,
        AVG((wi.metrics->>'roas')::FLOAT) FILTER (WHERE wi.metrics->>'roas' IS NOT NULL) AS avg_winner_roas,
        (SELECT COUNT(*) FROM pending_jobs WHERE job_type = 'rag_index_winner' AND status = 'pending') AS pending_index_jobs,
        COUNT(DISTINCT wi.video_id) FILTER (WHERE wi.rag_indexed = TRUE) AS indexed_winners
    FROM winner_insights wi
    WHERE wi.created_at >= NOW() - (p_days_back || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- JOB CLEANUP FUNCTION
-- ============================================================================

-- Function to clean up old completed/failed jobs
CREATE OR REPLACE FUNCTION cleanup_old_jobs(
    p_days_old INTEGER DEFAULT 7
)
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM pending_jobs
    WHERE status IN ('completed', 'failed')
    AND completed_at < NOW() - (p_days_old || ' days')::INTERVAL;
    
    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE pending_jobs IS 'Background job queue for async tasks';
COMMENT ON TABLE winner_insights IS 'Analyzed data from winning ads for replication';
COMMENT ON FUNCTION check_winner_and_index() IS 'Detects winning ads and queues them for RAG indexing';
COMMENT ON FUNCTION get_winner_stats(INTEGER) IS 'Returns winner statistics for the specified period';
COMMENT ON FUNCTION cleanup_old_jobs(INTEGER) IS 'Removes old completed/failed jobs from the queue';

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Add any existing high-performing ads to the queue for indexing (one-time backfill)
-- This will analyze historical data and index any ads that meet winner criteria
DO $$
DECLARE
    v_processed_count INTEGER := 0;
BEGIN
    INSERT INTO pending_jobs (job_type, payload, status)
    SELECT DISTINCT
        'rag_index_winner',
        jsonb_build_object(
            'video_id', pm.video_id,
            'ctr', pm.ctr,
            'roas', COALESCE((pm.raw_data->>'roas')::FLOAT, 0.0),
            'impressions', pm.impressions,
            'platform', pm.platform,
            'date', pm.date,
            'backfill', TRUE,
            'winner_criteria', CASE
                WHEN pm.ctr > 0.03 AND COALESCE((pm.raw_data->>'roas')::FLOAT, 0.0) > 3.0 THEN 'both'
                WHEN pm.ctr > 0.03 THEN 'ctr'
                ELSE 'roas'
            END
        ),
        'pending'
    FROM performance_metrics pm
    WHERE pm.impressions >= 1000
    AND (
        pm.ctr > 0.03
        OR COALESCE((pm.raw_data->>'roas')::FLOAT, 0.0) > 3.0
    )
    AND pm.created_at >= NOW() - INTERVAL '90 days'
    AND NOT EXISTS (
        SELECT 1 FROM pending_jobs pj
        WHERE pj.job_type = 'rag_index_winner'
        AND pj.payload->>'video_id' = pm.video_id::TEXT
    );
    
    GET DIAGNOSTICS v_processed_count = ROW_COUNT;
    
    IF v_processed_count > 0 THEN
        RAISE NOTICE 'Queued % historical winners for indexing', v_processed_count;
    END IF;
END $$;
