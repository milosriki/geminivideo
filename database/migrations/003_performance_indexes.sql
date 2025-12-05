-- ============================================================================
-- Migration 003: Performance Indexes
-- ============================================================================
-- Purpose: Add comprehensive indexes for production-grade performance
-- Run with: psql $DATABASE_URL -f 003_performance_indexes.sql
-- ============================================================================

-- ============================================================================
-- CAMPAIGNS TABLE INDEXES
-- ============================================================================

-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_campaigns_updated_at ON campaigns(updated_at DESC);

-- Performance metrics
CREATE INDEX IF NOT EXISTS idx_campaigns_roas ON campaigns(roas DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_campaigns_spend ON campaigns(spend DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_campaigns_revenue ON campaigns(revenue DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_campaigns_conversions ON campaigns(conversions DESC NULLS LAST);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_campaigns_user_status ON campaigns(user_id, status);
CREATE INDEX IF NOT EXISTS idx_campaigns_user_created ON campaigns(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_campaigns_status_roas ON campaigns(status, roas DESC) WHERE status = 'active';

-- JSONB indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_pain_points ON campaigns USING GIN(pain_points);
CREATE INDEX IF NOT EXISTS idx_campaigns_desires ON campaigns USING GIN(desires);
CREATE INDEX IF NOT EXISTS idx_campaigns_target_audience ON campaigns USING GIN(target_audience);

-- ============================================================================
-- BLUEPRINTS TABLE INDEXES
-- ============================================================================

-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign_id ON blueprints(campaign_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_user_id ON blueprints(user_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_created_at ON blueprints(created_at DESC);

-- Filtering and sorting
CREATE INDEX IF NOT EXISTS idx_blueprints_verdict ON blueprints(verdict);
CREATE INDEX IF NOT EXISTS idx_blueprints_status ON blueprints(status);
CREATE INDEX IF NOT EXISTS idx_blueprints_hook_type ON blueprints(hook_type);

-- Scoring and ranking
CREATE INDEX IF NOT EXISTS idx_blueprints_council_score ON blueprints(council_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_blueprints_predicted_roas ON blueprints(predicted_roas DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_blueprints_rank ON blueprints(campaign_id, rank) WHERE rank IS NOT NULL;

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign_verdict ON blueprints(campaign_id, verdict);
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign_score ON blueprints(campaign_id, council_score DESC);
CREATE INDEX IF NOT EXISTS idx_blueprints_hook_score ON blueprints(hook_type, council_score DESC);

-- JSONB indexes
CREATE INDEX IF NOT EXISTS idx_blueprints_script_json ON blueprints USING GIN(script_json);
CREATE INDEX IF NOT EXISTS idx_blueprints_matched_patterns ON blueprints USING GIN(matched_patterns);

-- ============================================================================
-- VIDEOS TABLE INDEXES
-- ============================================================================

-- Primary lookups
CREATE INDEX IF NOT EXISTS idx_videos_campaign_id ON videos(campaign_id);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_blueprint_id ON videos(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_videos_render_job_id ON videos(render_job_id);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_updated_at ON videos(updated_at DESC);

-- Status and platform
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_platform ON videos(platform);
CREATE INDEX IF NOT EXISTS idx_videos_meta_platform_id ON videos(meta_platform_id) WHERE meta_platform_id IS NOT NULL;

-- Performance metrics
CREATE INDEX IF NOT EXISTS idx_videos_actual_roas ON videos(actual_roas DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_videos_impressions ON videos(impressions DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_videos_clicks ON videos(clicks DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_videos_conversions ON videos(conversions DESC NULLS LAST);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_videos_campaign_status ON videos(campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_videos_user_created ON videos(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_videos_platform_status ON videos(platform, status);

-- JSONB indexes
CREATE INDEX IF NOT EXISTS idx_videos_analysis_data ON videos USING GIN(analysis_data);
CREATE INDEX IF NOT EXISTS idx_videos_performance_data ON videos USING GIN(performance_data);
CREATE INDEX IF NOT EXISTS idx_videos_published_to ON videos USING GIN(published_to);

-- Partial indexes for performance
CREATE INDEX IF NOT EXISTS idx_videos_ready ON videos(id, created_at DESC) WHERE status = 'ready';
CREATE INDEX IF NOT EXISTS idx_videos_published ON videos(id, created_at DESC) WHERE status = 'published';

-- ============================================================================
-- ADS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ads_campaign_id ON ads(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ads_video_id ON ads(video_id);
CREATE INDEX IF NOT EXISTS idx_ads_blueprint_id ON ads(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_ads_status ON ads(status);
CREATE INDEX IF NOT EXISTS idx_ads_approved ON ads(approved);
CREATE INDEX IF NOT EXISTS idx_ads_platform ON ads(platform);
CREATE INDEX IF NOT EXISTS idx_ads_created_at ON ads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ads_updated_at ON ads(updated_at DESC);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_ads_campaign_status ON ads(campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_ads_platform_approved ON ads(platform, approved);

-- JSONB indexes
CREATE INDEX IF NOT EXISTS idx_ads_targeting ON ads USING GIN(targeting);
CREATE INDEX IF NOT EXISTS idx_ads_performance ON ads USING GIN(performance);

-- ============================================================================
-- CLIPS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_clips_video_id ON clips(video_id);
CREATE INDEX IF NOT EXISTS idx_clips_asset_id ON clips(asset_id);
CREATE INDEX IF NOT EXISTS idx_clips_clip_id ON clips(clip_id);
CREATE INDEX IF NOT EXISTS idx_clips_created_at ON clips(created_at DESC);

-- Scene analysis
CREATE INDEX IF NOT EXISTS idx_clips_scene_type ON clips(scene_type);
CREATE INDEX IF NOT EXISTS idx_clips_ctr_score ON clips(ctr_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_clips_scene_score ON clips(scene_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_clips_engagement_score ON clips(engagement_score DESC NULLS LAST);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_clips_video_scene ON clips(video_id, scene_type);
CREATE INDEX IF NOT EXISTS idx_clips_scene_ctr ON clips(scene_type, ctr_score DESC);

-- JSONB indexes
CREATE INDEX IF NOT EXISTS idx_clips_emotions ON clips USING GIN(emotions);
CREATE INDEX IF NOT EXISTS idx_clips_visual_elements ON clips USING GIN(visual_elements);
CREATE INDEX IF NOT EXISTS idx_clips_features ON clips USING GIN(features);

-- ============================================================================
-- EMOTIONS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_emotions_clip_id ON emotions(clip_id);
CREATE INDEX IF NOT EXISTS idx_emotions_video_id ON emotions(video_id);
CREATE INDEX IF NOT EXISTS idx_emotions_asset_id ON emotions(asset_id);
CREATE INDEX IF NOT EXISTS idx_emotions_emotion_type ON emotions(emotion_type);
CREATE INDEX IF NOT EXISTS idx_emotions_intensity ON emotions(intensity DESC);
CREATE INDEX IF NOT EXISTS idx_emotions_created_at ON emotions(created_at DESC);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_emotions_clip_type ON emotions(clip_id, emotion_type);
CREATE INDEX IF NOT EXISTS idx_emotions_type_intensity ON emotions(emotion_type, intensity DESC);

-- ============================================================================
-- PERFORMANCE_METRICS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_performance_metrics_video_id ON performance_metrics(video_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_ad_id ON performance_metrics(ad_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_campaign_id ON performance_metrics(campaign_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_platform ON performance_metrics(platform);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_type ON performance_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_created_at ON performance_metrics(created_at DESC);

-- Composite indexes for time-series queries
CREATE INDEX IF NOT EXISTS idx_perf_video_date ON performance_metrics(video_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_perf_campaign_date ON performance_metrics(campaign_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_perf_platform_date ON performance_metrics(platform, date DESC);

-- Performance metrics
CREATE INDEX IF NOT EXISTS idx_performance_metrics_roas ON performance_metrics(roas DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_ctr ON performance_metrics(ctr DESC NULLS LAST);

-- ============================================================================
-- DAILY_ANALYTICS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_roas ON daily_analytics(roas DESC);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_spend ON daily_analytics(spend DESC);
CREATE INDEX IF NOT EXISTS idx_daily_analytics_revenue ON daily_analytics(revenue DESC);

-- ============================================================================
-- JOBS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(type);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_updated_at ON jobs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_type_status ON jobs(type, status);

-- Partial index for pending jobs
CREATE INDEX IF NOT EXISTS idx_jobs_pending ON jobs(created_at ASC) WHERE status IN ('pending', 'processing');

-- ============================================================================
-- RENDER_JOBS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_render_jobs_blueprint_id ON render_jobs(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_campaign_id ON render_jobs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_platform ON render_jobs(platform);
CREATE INDEX IF NOT EXISTS idx_render_jobs_created_at ON render_jobs(created_at DESC);

-- Composite indexes
CREATE INDEX IF NOT EXISTS idx_render_jobs_campaign_status ON render_jobs(campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status_created ON render_jobs(status, created_at DESC);

-- Partial index for active jobs
CREATE INDEX IF NOT EXISTS idx_render_jobs_active ON render_jobs(id, created_at DESC)
    WHERE status IN ('pending', 'processing', 'rendering');

-- ============================================================================
-- PREDICTIONS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_predictions_video ON predictions(video_id);
CREATE INDEX IF NOT EXISTS idx_predictions_ad ON predictions(ad_id);
CREATE INDEX IF NOT EXISTS idx_predictions_platform ON predictions(platform);
CREATE INDEX IF NOT EXISTS idx_predictions_hook_type ON predictions(hook_type);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at DESC);

-- Partial indexes for pending/completed predictions
CREATE INDEX IF NOT EXISTS idx_predictions_pending ON predictions(id, created_at DESC)
    WHERE actual_ctr IS NULL;
CREATE INDEX IF NOT EXISTS idx_predictions_completed ON predictions(id, actuals_fetched_at DESC)
    WHERE actuals_fetched_at IS NOT NULL;

-- Composite indexes for analytics
CREATE INDEX IF NOT EXISTS idx_predictions_platform_created ON predictions(platform, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_hook_created ON predictions(hook_type, created_at DESC);

-- JSONB index
CREATE INDEX IF NOT EXISTS idx_predictions_metadata ON predictions USING GIN(metadata);

-- ============================================================================
-- AB_TESTS TABLE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ab_tests_experiment ON ab_tests(experiment_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created_at ON ab_tests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ab_tests_started_at ON ab_tests(started_at DESC);

-- Partial index for active tests
CREATE INDEX IF NOT EXISTS idx_ab_tests_running ON ab_tests(id, started_at DESC)
    WHERE status = 'running';

-- ============================================================================
-- COMPOSITE INDEXES FOR COMMON QUERY PATTERNS
-- ============================================================================

-- Campaign performance analysis
CREATE INDEX IF NOT EXISTS idx_campaign_perf_analysis ON campaigns(user_id, status, roas DESC)
    WHERE status IN ('active', 'completed');

-- Video performance tracking
CREATE INDEX IF NOT EXISTS idx_video_perf_tracking ON videos(campaign_id, status, actual_roas DESC)
    WHERE status IN ('ready', 'published');

-- Blueprint approval workflow
CREATE INDEX IF NOT EXISTS idx_blueprint_approval ON blueprints(campaign_id, verdict, council_score DESC)
    WHERE verdict IN ('pending', 'approved');

-- Recent activity queries
CREATE INDEX IF NOT EXISTS idx_recent_campaigns ON campaigns(user_id, updated_at DESC)
    WHERE status != 'archived';
CREATE INDEX IF NOT EXISTS idx_recent_videos ON videos(user_id, updated_at DESC)
    WHERE status != 'archived';

-- ============================================================================
-- COVERING INDEXES (Include commonly selected columns)
-- ============================================================================

-- Campaign list view
CREATE INDEX IF NOT EXISTS idx_campaigns_list_view ON campaigns(user_id, created_at DESC)
    INCLUDE (name, status, roas, spend, revenue);

-- Video list view
CREATE INDEX IF NOT EXISTS idx_videos_list_view ON videos(campaign_id, created_at DESC)
    INCLUDE (title, status, duration_seconds, thumbnail_url);

-- Blueprint list view
CREATE INDEX IF NOT EXISTS idx_blueprints_list_view ON blueprints(campaign_id, rank)
    INCLUDE (title, hook_text, council_score, verdict);

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE schemaname = 'public';

    RAISE NOTICE '✅ Migration 003: Performance Indexes completed successfully';
    RAISE NOTICE '   Total indexes in schema: %', index_count;
    RAISE NOTICE '   Composite indexes created';
    RAISE NOTICE '   Partial indexes for common queries';
    RAISE NOTICE '   JSONB GIN indexes for JSON columns';
    RAISE NOTICE '   Covering indexes for list views';
END $$;
