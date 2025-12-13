-- ============================================================================
-- Performance Indexes Migration
-- Agent 16: Database Optimization
-- Created: 2025-12-13
-- Description: Add optimized indexes for winner detection and budget allocation
-- ============================================================================

-- ============================================================================
-- Ads Table Indexes (if table exists)
-- ============================================================================

-- Index for winner detection queries
-- Covers: status, CTR, ROAS, impressions, created_at
CREATE INDEX IF NOT EXISTS idx_ads_winner_criteria
ON ads(status, actual_ctr DESC, actual_roas DESC, impressions DESC, created_at DESC)
WHERE status = 'published' AND impressions >= 1000;

-- Index for finding top performers by profit
CREATE INDEX IF NOT EXISTS idx_ads_profit_ranking
ON ads(campaign_id, status, (revenue - spend) DESC)
WHERE status = 'published';

-- Index for budget allocation queries
CREATE INDEX IF NOT EXISTS idx_ads_budget_allocation
ON ads(campaign_id, status, actual_roas DESC, spend DESC)
WHERE status = 'published';

-- Index for creative DNA pattern lookups (GIN for JSONB)
CREATE INDEX IF NOT EXISTS idx_ads_creative_dna_patterns
ON ads USING GIN(creative_dna jsonb_path_ops);

-- Index for time-based queries
CREATE INDEX IF NOT EXISTS idx_ads_created_at_status
ON ads(created_at DESC, status)
WHERE status IN ('published', 'active');

-- Index for account-level queries
CREATE INDEX IF NOT EXISTS idx_ads_account_performance
ON ads(account_id, status, actual_roas DESC, actual_ctr DESC)
WHERE status = 'published';

-- ============================================================================
-- Campaigns Table Indexes
-- ============================================================================

-- Index for active campaigns lookup
CREATE INDEX IF NOT EXISTS idx_campaigns_active
ON campaigns(user_id, status, created_at DESC)
WHERE status IN ('draft', 'generating', 'completed');

-- Index for campaign budget tracking
CREATE INDEX IF NOT EXISTS idx_campaigns_budget
ON campaigns(user_id, total_generated, approved_count);

-- ============================================================================
-- Blueprints Table Indexes
-- ============================================================================

-- Index for high-scoring blueprints
CREATE INDEX IF NOT EXISTS idx_blueprints_performance
ON blueprints(campaign_id, council_score DESC, predicted_roas DESC)
WHERE council_score IS NOT NULL;

-- Index for blueprint ranking
CREATE INDEX IF NOT EXISTS idx_blueprints_rank_lookup
ON blueprints(campaign_id, rank ASC)
WHERE rank IS NOT NULL;

-- ============================================================================
-- Render Jobs Table Indexes
-- ============================================================================

-- Index for pending jobs processing
CREATE INDEX IF NOT EXISTS idx_render_jobs_pending
ON render_jobs(status, created_at ASC)
WHERE status = 'pending';

-- Index for job completion tracking
CREATE INDEX IF NOT EXISTS idx_render_jobs_completion
ON render_jobs(blueprint_id, status, completed_at DESC);

-- ============================================================================
-- Videos Table Indexes
-- ============================================================================

-- Index for video lookups
CREATE INDEX IF NOT EXISTS idx_videos_lookup
ON videos(render_job_id, created_at DESC);

-- ============================================================================
-- Performance Metrics Table (if exists)
-- ============================================================================

-- Index for metrics aggregation
CREATE INDEX IF NOT EXISTS idx_performance_metrics_aggregation
ON performance_metrics(video_id, platform, date DESC)
WHERE platform = 'meta';

-- ============================================================================
-- Partial Indexes for Common Queries
-- ============================================================================

-- Winners only index (ads with high performance)
CREATE INDEX IF NOT EXISTS idx_ads_winners_only
ON ads(ad_id, video_id, actual_ctr, actual_roas, impressions)
WHERE status = 'published'
  AND actual_ctr >= 0.03
  AND actual_roas >= 2.0
  AND impressions >= 1000;

-- Underperformers index (ads needing budget reduction)
CREATE INDEX IF NOT EXISTS idx_ads_underperformers
ON ads(campaign_id, spend, actual_roas)
WHERE status = 'published'
  AND actual_roas < 1.0
  AND impressions >= 1000;

-- ============================================================================
-- Composite Indexes for JOIN Operations
-- ============================================================================

-- For campaign -> blueprints -> render_jobs joins
CREATE INDEX IF NOT EXISTS idx_blueprints_for_joins
ON blueprints(id, campaign_id);

CREATE INDEX IF NOT EXISTS idx_render_jobs_for_joins
ON render_jobs(id, blueprint_id);

-- ============================================================================
-- Analyze Tables (Update Statistics)
-- ============================================================================

ANALYZE campaigns;
ANALYZE blueprints;
ANALYZE render_jobs;
ANALYZE videos;

-- ============================================================================
-- Comments
-- ============================================================================

COMMENT ON INDEX idx_ads_winner_criteria IS 'Optimized index for winner detection queries - Agent 16';
COMMENT ON INDEX idx_ads_budget_allocation IS 'Index for budget reallocation queries - Agent 16';
COMMENT ON INDEX idx_ads_creative_dna_patterns IS 'GIN index for JSONB creative DNA pattern lookups - Agent 16';
COMMENT ON INDEX idx_ads_winners_only IS 'Partial index covering only winner ads for fast lookups - Agent 16';
