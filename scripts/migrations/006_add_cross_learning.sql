-- ============================================================================
-- Migration 006: Add Cross-Account Learning Tables
-- ============================================================================
-- Purpose: Cross-account learning for pattern discovery across customers
-- For: Platform-wide intelligence and generalized winning patterns
-- Agent: 49 - Cross-Account Learning System
-- ============================================================================

-- ============================================================================
-- CROSS_ACCOUNT_PATTERNS TABLE
-- ============================================================================
-- Global patterns discovered across all accounts

CREATE TABLE IF NOT EXISTS cross_account_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL, -- 'hook', 'visual', 'audio', 'pacing', 'copy', 'cta', 'combined'

    -- Pattern characteristics
    pattern_features JSONB NOT NULL,
    pattern_description TEXT,

    -- Performance metrics (aggregated across accounts)
    sample_size INTEGER NOT NULL,
    account_count INTEGER NOT NULL, -- How many accounts contributed to this pattern
    avg_roas FLOAT,
    median_roas FLOAT,
    avg_ctr FLOAT,
    median_ctr FLOAT,
    avg_conversion_rate FLOAT,

    -- Statistical confidence
    confidence_score FLOAT, -- 0-1 confidence in pattern validity
    std_dev_roas FLOAT,
    std_dev_ctr FLOAT,

    -- Industry/vertical context
    industries TEXT[], -- Industries where this pattern works
    audience_types TEXT[], -- Audience types this pattern resonates with

    -- Pattern metadata
    first_seen_at TIMESTAMPTZ,
    last_validated_at TIMESTAMPTZ,
    validation_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cross_patterns_type ON cross_account_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_cross_patterns_roas ON cross_account_patterns(avg_roas DESC);
CREATE INDEX IF NOT EXISTS idx_cross_patterns_confidence ON cross_account_patterns(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_cross_patterns_sample_size ON cross_account_patterns(sample_size DESC);
CREATE INDEX IF NOT EXISTS idx_cross_patterns_industries ON cross_account_patterns USING GIN(industries);

COMMENT ON TABLE cross_account_patterns IS
'Platform-wide winning patterns discovered across multiple accounts';

COMMENT ON COLUMN cross_account_patterns.pattern_features IS
'JSONB containing the pattern characteristics and rules';

COMMENT ON COLUMN cross_account_patterns.confidence_score IS
'Statistical confidence in pattern validity based on sample size and consistency';

-- ============================================================================
-- PATTERN_CONTRIBUTIONS TABLE
-- ============================================================================
-- Track which accounts contributed to which patterns

CREATE TABLE IF NOT EXISTS pattern_contributions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES cross_account_patterns(pattern_id) ON DELETE CASCADE,
    account_id VARCHAR(255) NOT NULL,
    creative_id VARCHAR(255),

    -- Contribution metrics
    roas FLOAT,
    ctr FLOAT,
    conversion_rate FLOAT,

    -- Metadata
    industry VARCHAR(100),
    audience_type VARCHAR(100),
    contributed_features JSONB,

    -- Timestamp
    contributed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pattern_contributions_pattern ON pattern_contributions(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_contributions_account ON pattern_contributions(account_id);
CREATE INDEX IF NOT EXISTS idx_pattern_contributions_creative ON pattern_contributions(creative_id);

-- Composite index for pattern-account lookups
CREATE INDEX IF NOT EXISTS idx_pattern_contributions_pattern_account
    ON pattern_contributions(pattern_id, account_id);

COMMENT ON TABLE pattern_contributions IS
'Track account contributions to cross-account patterns';

-- ============================================================================
-- PATTERN_APPLICATIONS TABLE
-- ============================================================================
-- Track when patterns are applied to new accounts

CREATE TABLE IF NOT EXISTS pattern_applications (
    application_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_id UUID NOT NULL REFERENCES cross_account_patterns(pattern_id),
    account_id VARCHAR(255) NOT NULL,
    creative_id VARCHAR(255),

    -- Application details
    applied_features JSONB NOT NULL,
    customizations JSONB, -- Account-specific customizations

    -- Pre-application baseline
    baseline_roas FLOAT,
    baseline_ctr FLOAT,
    baseline_conversion_rate FLOAT,

    -- Post-application results
    result_roas FLOAT,
    result_ctr FLOAT,
    result_conversion_rate FLOAT,

    -- Improvement metrics
    roas_lift_pct FLOAT, -- Percentage improvement
    ctr_lift_pct FLOAT,
    conversion_lift_pct FLOAT,

    -- Status
    status VARCHAR(50) DEFAULT 'applied', -- 'applied', 'testing', 'validated', 'failed'
    validation_date TIMESTAMPTZ,

    -- Timestamps
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    measured_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_pattern_applications_pattern ON pattern_applications(pattern_id);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_account ON pattern_applications(account_id);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_status ON pattern_applications(status);
CREATE INDEX IF NOT EXISTS idx_pattern_applications_applied ON pattern_applications(applied_at DESC);

-- Index for successful applications
CREATE INDEX IF NOT EXISTS idx_pattern_applications_success
    ON pattern_applications(pattern_id, roas_lift_pct DESC)
    WHERE status = 'validated' AND roas_lift_pct > 0;

COMMENT ON TABLE pattern_applications IS
'Track applications of cross-account patterns to new accounts with results';

-- ============================================================================
-- INDUSTRY_BENCHMARKS TABLE
-- ============================================================================
-- Industry-specific performance benchmarks

CREATE TABLE IF NOT EXISTS industry_benchmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    industry VARCHAR(100) NOT NULL UNIQUE,

    -- Benchmark metrics
    sample_size INTEGER NOT NULL,
    account_count INTEGER NOT NULL,

    -- Performance percentiles
    roas_p25 FLOAT,
    roas_p50 FLOAT,
    roas_p75 FLOAT,
    roas_p90 FLOAT,

    ctr_p25 FLOAT,
    ctr_p50 FLOAT,
    ctr_p75 FLOAT,
    ctr_p90 FLOAT,

    conversion_rate_p25 FLOAT,
    conversion_rate_p50 FLOAT,
    conversion_rate_p75 FLOAT,
    conversion_rate_p90 FLOAT,

    -- Top patterns for this industry
    top_patterns JSONB, -- Array of pattern_ids with performance

    -- Timestamps
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_industry ON industry_benchmarks(industry);

COMMENT ON TABLE industry_benchmarks IS
'Performance benchmarks by industry for comparison and recommendations';

-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_cross_patterns_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_cross_patterns ON cross_account_patterns;
CREATE TRIGGER trigger_update_cross_patterns
    BEFORE UPDATE ON cross_account_patterns
    FOR EACH ROW
    EXECUTE FUNCTION update_cross_patterns_timestamp();

-- ============================================================================
-- ANALYTICAL VIEWS
-- ============================================================================

-- View: Top cross-account patterns
CREATE OR REPLACE VIEW top_cross_patterns AS
SELECT
    pattern_id,
    pattern_name,
    pattern_type,
    sample_size,
    account_count,
    avg_roas,
    avg_ctr,
    confidence_score,
    industries,
    created_at
FROM cross_account_patterns
WHERE confidence_score >= 0.7
  AND sample_size >= 10
ORDER BY avg_roas DESC, confidence_score DESC
LIMIT 50;

COMMENT ON VIEW top_cross_patterns IS
'Top 50 validated cross-account patterns with high confidence';

-- View: Pattern effectiveness by industry
CREATE OR REPLACE VIEW pattern_effectiveness_by_industry AS
SELECT
    pc.industry,
    cp.pattern_id,
    cp.pattern_name,
    cp.pattern_type,
    COUNT(DISTINCT pc.account_id) as accounts_using,
    AVG(pc.roas) as avg_roas,
    AVG(pc.ctr) as avg_ctr,
    COUNT(*) as creative_count
FROM pattern_contributions pc
JOIN cross_account_patterns cp ON pc.pattern_id = cp.pattern_id
WHERE pc.industry IS NOT NULL
GROUP BY pc.industry, cp.pattern_id, cp.pattern_name, cp.pattern_type
HAVING COUNT(DISTINCT pc.account_id) >= 3
ORDER BY pc.industry, avg_roas DESC;

COMMENT ON VIEW pattern_effectiveness_by_industry IS
'Pattern effectiveness broken down by industry';

-- View: Pattern application success rate
CREATE OR REPLACE VIEW pattern_success_metrics AS
SELECT
    cp.pattern_id,
    cp.pattern_name,
    cp.pattern_type,
    COUNT(pa.application_id) as total_applications,
    COUNT(pa.application_id) FILTER (WHERE pa.status = 'validated') as successful_applications,
    ROUND(
        COUNT(pa.application_id) FILTER (WHERE pa.status = 'validated')::NUMERIC /
        NULLIF(COUNT(pa.application_id), 0) * 100, 2
    ) as success_rate_pct,
    AVG(pa.roas_lift_pct) FILTER (WHERE pa.status = 'validated' AND pa.roas_lift_pct IS NOT NULL) as avg_roas_lift,
    AVG(pa.ctr_lift_pct) FILTER (WHERE pa.status = 'validated' AND pa.ctr_lift_pct IS NOT NULL) as avg_ctr_lift
FROM cross_account_patterns cp
LEFT JOIN pattern_applications pa ON cp.pattern_id = pa.pattern_id
GROUP BY cp.pattern_id, cp.pattern_name, cp.pattern_type
HAVING COUNT(pa.application_id) > 0
ORDER BY success_rate_pct DESC, total_applications DESC;

COMMENT ON VIEW pattern_success_metrics IS
'Success rates and performance lifts from pattern applications';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get patterns for industry
CREATE OR REPLACE FUNCTION get_patterns_for_industry(
    p_industry VARCHAR,
    p_min_confidence FLOAT DEFAULT 0.7,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    pattern_id UUID,
    pattern_name VARCHAR,
    pattern_type VARCHAR,
    avg_roas FLOAT,
    avg_ctr FLOAT,
    confidence_score FLOAT,
    sample_size INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cp.pattern_id,
        cp.pattern_name,
        cp.pattern_type,
        cp.avg_roas,
        cp.avg_ctr,
        cp.confidence_score,
        cp.sample_size
    FROM cross_account_patterns cp
    WHERE p_industry = ANY(cp.industries)
      AND cp.confidence_score >= p_min_confidence
    ORDER BY cp.avg_roas DESC, cp.confidence_score DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_patterns_for_industry IS
'Get top performing patterns for a specific industry';

-- Function to calculate pattern ROI
CREATE OR REPLACE FUNCTION calculate_pattern_roi(p_pattern_id UUID)
RETURNS TABLE (
    total_applications INTEGER,
    successful_applications INTEGER,
    avg_roas_lift FLOAT,
    total_revenue_impact FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER as total_applications,
        COUNT(*) FILTER (WHERE status = 'validated' AND roas_lift_pct > 0)::INTEGER as successful_applications,
        AVG(roas_lift_pct) FILTER (WHERE status = 'validated') as avg_roas_lift,
        SUM((result_roas - baseline_roas) * baseline_roas) FILTER (WHERE status = 'validated') as total_revenue_impact
    FROM pattern_applications
    WHERE pattern_id = p_pattern_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_pattern_roi IS
'Calculate ROI metrics for a pattern across all applications';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 006: Cross-account learning tables completed successfully';
    RAISE NOTICE '   - cross_account_patterns: Platform-wide patterns';
    RAISE NOTICE '   - pattern_contributions: Account contributions tracking';
    RAISE NOTICE '   - pattern_applications: Application results tracking';
    RAISE NOTICE '   - industry_benchmarks: Industry performance data';
    RAISE NOTICE '   - 3 analytical views for insights';
    RAISE NOTICE '   - 2 helper functions';
    RAISE NOTICE '';
    RAISE NOTICE '🌐 Agent 49: Cross-Account Learning System - READY';
    RAISE NOTICE '   Learn from the best across all accounts!';
END $$;
