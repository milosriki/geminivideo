-- ============================================================================
-- Migration 008: Add Performance Indexes
-- ============================================================================
-- Purpose: Additional indexes for query optimization and performance
-- For: Production-grade performance across all tables
-- ============================================================================

-- ============================================================================
-- CAMPAIGNS - Additional Performance Indexes
-- ============================================================================

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_campaigns_user_status
    ON campaigns(user_id, status)
    WHERE status IN ('active', 'generating');

CREATE INDEX IF NOT EXISTS idx_campaigns_user_created
    ON campaigns(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_campaigns_performance
    ON campaigns(roas DESC, spend DESC)
    WHERE status = 'active';

COMMENT ON INDEX idx_campaigns_performance IS
'Fast lookup of active campaigns by performance metrics';

-- ============================================================================
-- BLUEPRINTS - Query Optimization Indexes
-- ============================================================================

-- Index for finding top-scoring blueprints per campaign
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign_score
    ON blueprints(campaign_id, council_score DESC, predicted_roas DESC);

-- Index for approved blueprints
CREATE INDEX IF NOT EXISTS idx_blueprints_approved
    ON blueprints(campaign_id, created_at DESC)
    WHERE verdict = 'approved';

-- ============================================================================
-- VIDEOS - Performance Indexes
-- ============================================================================

-- Index for ready videos by campaign
CREATE INDEX IF NOT EXISTS idx_videos_campaign_ready
    ON videos(campaign_id, created_at DESC)
    WHERE status = 'ready';

-- Index for video lookup by platform ID
CREATE INDEX IF NOT EXISTS idx_videos_meta_platform
    ON videos(meta_platform_id)
    WHERE meta_platform_id IS NOT NULL;

-- Composite index for video management
CREATE INDEX IF NOT EXISTS idx_videos_campaign_status_created
    ON videos(campaign_id, status, created_at DESC);

-- ============================================================================
-- ADS - Approval Workflow Indexes
-- ============================================================================

-- Index for pending approvals
CREATE INDEX IF NOT EXISTS idx_ads_pending_approval
    ON ads(created_at DESC)
    WHERE status = 'pending' AND approved = FALSE;

-- Index for published ads by platform
CREATE INDEX IF NOT EXISTS idx_ads_published_platform
    ON ads(platform, created_at DESC)
    WHERE status = 'published';

-- Composite index for ad performance queries
CREATE INDEX IF NOT EXISTS idx_ads_campaign_performance
    ON ads(campaign_id, predicted_roas DESC, predicted_ctr DESC);

-- ============================================================================
-- CLIPS - Scene Analysis Indexes
-- ============================================================================

-- Index for high-scoring clips
CREATE INDEX IF NOT EXISTS idx_clips_top_scoring
    ON clips(ctr_score DESC, engagement_score DESC)
    WHERE ctr_score > 0.7;

-- Index for clip analysis by scene type
CREATE INDEX IF NOT EXISTS idx_clips_video_scene_score
    ON clips(video_id, scene_type, scene_score DESC);

-- Full-text search on transcript (if needed)
CREATE INDEX IF NOT EXISTS idx_clips_transcript_search
    ON clips USING gin(to_tsvector('english', transcript))
    WHERE transcript IS NOT NULL;

-- ============================================================================
-- PERFORMANCE_METRICS - Time-Series Indexes
-- ============================================================================

-- Composite index for time-series queries
CREATE INDEX IF NOT EXISTS idx_perf_metrics_video_date
    ON performance_metrics(video_id, date DESC);

CREATE INDEX IF NOT EXISTS idx_perf_metrics_campaign_date
    ON performance_metrics(campaign_id, date DESC)
    WHERE campaign_id IS NOT NULL;

-- Index for platform performance comparison
CREATE INDEX IF NOT EXISTS idx_perf_metrics_platform_date
    ON performance_metrics(platform, date DESC);

-- Index for high-performing metrics
CREATE INDEX IF NOT EXISTS idx_perf_metrics_high_roas
    ON performance_metrics(date DESC, roas DESC)
    WHERE roas >= 2.0;

-- ============================================================================
-- PREDICTIONS - Validation Indexes
-- ============================================================================

-- Index for pending validations (predictions waiting for actuals)
CREATE INDEX IF NOT EXISTS idx_predictions_pending_validation
    ON predictions(created_at DESC)
    WHERE actual_ctr IS NULL AND created_at < (CURRENT_TIMESTAMP - INTERVAL '7 days');

-- Index for accuracy analysis
CREATE INDEX IF NOT EXISTS idx_predictions_validated
    ON predictions(hook_type, platform, created_at DESC)
    WHERE actual_ctr IS NOT NULL;

-- ============================================================================
-- VIDEO_EMBEDDINGS - Similarity Search Optimization
-- ============================================================================

-- Additional vector index with different parameters for better performance
CREATE INDEX IF NOT EXISTS idx_video_embeddings_vector_hnsw
    ON video_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 200);

-- Composite index for filtered similarity search
CREATE INDEX IF NOT EXISTS idx_video_embeddings_type_video
    ON video_embeddings(embedding_type, video_id);

-- ============================================================================
-- SEMANTIC_CACHE - Cache Hit Optimization
-- ============================================================================

-- Index for cache cleanup (expired entries)
CREATE INDEX IF NOT EXISTS idx_semantic_cache_cleanup
    ON semantic_cache_entries(expires_at)
    WHERE expires_at IS NOT NULL AND expires_at < NOW();

-- Index for LRU eviction (least recently used)
CREATE INDEX IF NOT EXISTS idx_semantic_cache_lru
    ON semantic_cache_entries(last_accessed_at ASC)
    WHERE last_accessed_at IS NOT NULL;

-- Composite index for cache hit ratio analysis
CREATE INDEX IF NOT EXISTS idx_semantic_cache_performance
    ON semantic_cache_entries(query_type, access_count DESC, compute_time_ms DESC);

-- ============================================================================
-- CREATIVE_DNA - Pattern Discovery Indexes
-- ============================================================================

-- Index for finding winning formulas
CREATE INDEX IF NOT EXISTS idx_creative_formulas_performance
    ON creative_formulas(avg_roas DESC, avg_ctr DESC, sample_size DESC);

-- Index for DNA extractions by performance
CREATE INDEX IF NOT EXISTS idx_dna_extractions_winners
    ON creative_dna_extractions(account_id, roas DESC, ctr DESC)
    WHERE roas >= 2.5;

-- JSONB indexes for pattern analysis
CREATE INDEX IF NOT EXISTS idx_dna_hook_patterns
    ON creative_dna_extractions USING gin(hook_dna jsonb_path_ops);

CREATE INDEX IF NOT EXISTS idx_dna_visual_patterns
    ON creative_dna_extractions USING gin(visual_dna jsonb_path_ops);

-- ============================================================================
-- CROSS_ACCOUNT_PATTERNS - Platform Intelligence Indexes
-- ============================================================================

-- Index for high-confidence patterns
CREATE INDEX IF NOT EXISTS idx_cross_patterns_validated
    ON cross_account_patterns(avg_roas DESC, confidence_score DESC)
    WHERE confidence_score >= 0.8 AND sample_size >= 20;

-- Index for pattern discovery by type
CREATE INDEX IF NOT EXISTS idx_cross_patterns_type_perf
    ON cross_account_patterns(pattern_type, avg_roas DESC, account_count DESC);

-- GIN index for industry array searches
CREATE INDEX IF NOT EXISTS idx_cross_patterns_industries_gin
    ON cross_account_patterns USING gin(industries);

-- ============================================================================
-- FEEDBACK_LOOPS - Real-time Processing Indexes
-- ============================================================================

-- Index for active loops needing activation
CREATE INDEX IF NOT EXISTS idx_feedback_loops_active_freq
    ON feedback_loops(frequency, last_activated_at)
    WHERE is_active = TRUE;

-- Index for loop performance monitoring
CREATE INDEX IF NOT EXISTS idx_feedback_loops_performance
    ON feedback_loops(success_rate DESC, avg_improvement_pct DESC)
    WHERE activation_count >= 10;

-- ============================================================================
-- LEARNING_CYCLES - Historical Analysis Indexes
-- ============================================================================

-- Index for cycle performance comparison
CREATE INDEX IF NOT EXISTS idx_learning_cycles_performance
    ON learning_cycles(cycle_type, roas_improvement_pct DESC, start_date DESC)
    WHERE status = 'completed';

-- Index for active cycles
CREATE INDEX IF NOT EXISTS idx_learning_cycles_active
    ON learning_cycles(start_date DESC)
    WHERE status = 'active';

-- ============================================================================
-- IMPROVEMENT_TRAJECTORY - Time-Series Analysis
-- ============================================================================

-- Covering index for trajectory queries
CREATE INDEX IF NOT EXISTS idx_improvement_trajectory_covering
    ON improvement_trajectory(entity_type, entity_id, measurement_date DESC)
    INCLUDE (roas, ctr, conversion_rate, trend_direction);

-- Index for trend analysis
CREATE INDEX IF NOT EXISTS idx_improvement_trajectory_trends
    ON improvement_trajectory(entity_type, trend_direction, measurement_date DESC);

-- ============================================================================
-- JOBS - Background Processing Indexes
-- ============================================================================

-- Index for job queue processing
CREATE INDEX IF NOT EXISTS idx_jobs_queue
    ON jobs(status, created_at ASC)
    WHERE status IN ('pending', 'processing');

-- Index for failed jobs requiring retry
CREATE INDEX IF NOT EXISTS idx_jobs_failed
    ON jobs(type, created_at DESC)
    WHERE status = 'failed';

-- Composite index for job monitoring
CREATE INDEX IF NOT EXISTS idx_jobs_type_status_created
    ON jobs(type, status, created_at DESC);

-- ============================================================================
-- RENDER_JOBS - Video Processing Indexes
-- ============================================================================

-- Index for active render queue
CREATE INDEX IF NOT EXISTS idx_render_jobs_queue
    ON render_jobs(status, created_at ASC)
    WHERE status IN ('pending', 'processing');

-- Index for render job history by campaign
CREATE INDEX IF NOT EXISTS idx_render_jobs_campaign_status
    ON render_jobs(campaign_id, status, created_at DESC);

-- ============================================================================
-- DATABASE MAINTENANCE INDEXES
-- ============================================================================

-- Index for audit log cleanup
CREATE INDEX IF NOT EXISTS idx_audit_logs_cleanup
    ON audit_logs(created_at)
    WHERE created_at < (CURRENT_TIMESTAMP - INTERVAL '90 days');

-- Partial index for recent audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_recent
    ON audit_logs(entity_type, created_at DESC)
    WHERE created_at >= (CURRENT_TIMESTAMP - INTERVAL '30 days');

-- ============================================================================
-- STATISTICS UPDATE
-- ============================================================================
-- Update table statistics for query planner

DO $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'ANALYZE ' || quote_ident(table_name);
    END LOOP;

    RAISE NOTICE '✅ Updated statistics for all tables';
END $$;

-- ============================================================================
-- INDEX MONITORING VIEW
-- ============================================================================

-- View to monitor index usage
CREATE OR REPLACE VIEW index_usage_stats AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

COMMENT ON VIEW index_usage_stats IS
'Monitor index usage statistics for optimization';

-- View for unused indexes
CREATE OR REPLACE VIEW unused_indexes AS
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;

COMMENT ON VIEW unused_indexes IS
'Identify potentially unused indexes for removal';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
DECLARE
    index_count INTEGER;
    total_size TEXT;
BEGIN
    -- Count total indexes
    SELECT COUNT(*), pg_size_pretty(SUM(pg_relation_size(indexrelid)))
    INTO index_count, total_size
    FROM pg_stat_user_indexes
    WHERE schemaname = 'public';

    RAISE NOTICE '✅ Migration 008: Performance indexes completed successfully';
    RAISE NOTICE '   Total indexes in database: %', index_count;
    RAISE NOTICE '   Total index size: %', total_size;
    RAISE NOTICE '';
    RAISE NOTICE '📊 Performance Indexes:';
    RAISE NOTICE '   - Campaigns: Optimized for user queries and performance';
    RAISE NOTICE '   - Blueprints: Fast scoring and approval lookups';
    RAISE NOTICE '   - Videos: Platform integration and status queries';
    RAISE NOTICE '   - Ads: Approval workflow and performance tracking';
    RAISE NOTICE '   - Clips: Scene analysis and scoring';
    RAISE NOTICE '   - Performance Metrics: Time-series optimization';
    RAISE NOTICE '   - Predictions: Validation and accuracy analysis';
    RAISE NOTICE '   - Embeddings: Vector similarity search';
    RAISE NOTICE '   - Semantic Cache: Hit rate optimization';
    RAISE NOTICE '   - Creative DNA: Pattern discovery';
    RAISE NOTICE '   - Cross-Account: Platform intelligence';
    RAISE NOTICE '   - Feedback Loops: Real-time processing';
    RAISE NOTICE '   - Learning Cycles: Historical analysis';
    RAISE NOTICE '';
    RAISE NOTICE '🚀 Database is production-ready with comprehensive indexing!';
    RAISE NOTICE '   Run index_usage_stats view to monitor performance';
END $$;
