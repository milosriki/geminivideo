-- ============================================================================
-- Migration 002: Add Predictions Table
-- ============================================================================
-- Purpose: ML prediction tracking and validation for model accuracy
-- For: €5M Investment Validation - Track predicted vs actual performance
-- ============================================================================

-- ============================================================================
-- PREDICTIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS predictions (
    -- Primary identifiers
    id VARCHAR(255) PRIMARY KEY,
    video_id VARCHAR(255) NOT NULL,
    ad_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,

    -- Predicted metrics (set at prediction time)
    predicted_ctr FLOAT NOT NULL,
    predicted_roas FLOAT NOT NULL,
    predicted_conversion FLOAT NOT NULL,

    -- Actual metrics (populated after campaign runs)
    actual_ctr FLOAT,
    actual_roas FLOAT,
    actual_conversion FLOAT,

    -- Additional performance data
    impressions INTEGER,
    clicks INTEGER,
    spend DECIMAL(10, 2),

    -- Model metadata
    council_score FLOAT NOT NULL,
    hook_type VARCHAR(100) NOT NULL,
    template_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    actuals_fetched_at TIMESTAMP
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_predictions_video ON predictions(video_id);
CREATE INDEX IF NOT EXISTS idx_predictions_ad ON predictions(ad_id);
CREATE INDEX IF NOT EXISTS idx_predictions_platform ON predictions(platform);
CREATE INDEX IF NOT EXISTS idx_predictions_hook_type ON predictions(hook_type);
CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_pending ON predictions(actual_ctr) WHERE actual_ctr IS NULL;
CREATE INDEX IF NOT EXISTS idx_predictions_completed ON predictions(actuals_fetched_at) WHERE actuals_fetched_at IS NOT NULL;

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_predictions_platform_created ON predictions(platform, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_hook_created ON predictions(hook_type, created_at DESC);

COMMENT ON TABLE predictions IS 'ML prediction tracking for investment validation - tracks predicted vs actual performance';
COMMENT ON COLUMN predictions.council_score IS 'AI council confidence score (0-1) - measure of prediction confidence';
COMMENT ON COLUMN predictions.metadata IS 'Stores calculated accuracy metrics and additional context';

-- ============================================================================
-- ANALYTICAL VIEWS
-- ============================================================================

-- Overall Model Accuracy View
CREATE OR REPLACE VIEW prediction_accuracy_summary AS
SELECT
    COUNT(*) as total_predictions,
    COUNT(actual_ctr) as predictions_with_actuals,
    ROUND(COUNT(actual_ctr)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 2) as completion_rate_pct,

    -- CTR accuracy
    ROUND(AVG(ABS(predicted_ctr - actual_ctr))::NUMERIC, 5) as avg_ctr_error,
    ROUND(STDDEV(predicted_ctr - actual_ctr)::NUMERIC, 5) as ctr_error_stddev,
    ROUND(AVG(CASE
        WHEN actual_ctr = 0 THEN 0
        ELSE (1 - ABS(predicted_ctr - actual_ctr) / NULLIF(actual_ctr, 0)) * 100
    END)::NUMERIC, 2) as avg_ctr_accuracy_pct,

    -- ROAS accuracy
    ROUND(AVG(ABS(predicted_roas - actual_roas))::NUMERIC, 3) as avg_roas_error,
    ROUND(STDDEV(predicted_roas - actual_roas)::NUMERIC, 3) as roas_error_stddev,
    ROUND(AVG(CASE
        WHEN actual_roas = 0 THEN 0
        ELSE (1 - ABS(predicted_roas - actual_roas) / NULLIF(actual_roas, 0)) * 100
    END)::NUMERIC, 2) as avg_roas_accuracy_pct,

    -- Conversion accuracy
    ROUND(AVG(ABS(predicted_conversion - actual_conversion))::NUMERIC, 5) as avg_conversion_error,
    ROUND(AVG(CASE
        WHEN actual_conversion = 0 THEN 0
        ELSE (1 - ABS(predicted_conversion - actual_conversion) / NULLIF(actual_conversion, 0)) * 100
    END)::NUMERIC, 2) as avg_conversion_accuracy_pct,

    -- Council score correlation
    ROUND(AVG(council_score)::NUMERIC, 3) as avg_council_score
FROM predictions
WHERE actual_ctr IS NOT NULL;

COMMENT ON VIEW prediction_accuracy_summary IS 'Overall model accuracy metrics across all predictions';

-- Platform-specific Accuracy View
CREATE OR REPLACE VIEW prediction_accuracy_by_platform AS
SELECT
    platform,
    COUNT(*) as total_predictions,
    COUNT(actual_ctr) as predictions_with_actuals,

    -- CTR metrics
    ROUND(AVG(predicted_ctr)::NUMERIC, 5) as avg_predicted_ctr,
    ROUND(AVG(actual_ctr)::NUMERIC, 5) as avg_actual_ctr,
    ROUND(AVG(ABS(predicted_ctr - actual_ctr))::NUMERIC, 5) as avg_ctr_error,
    ROUND(AVG(CASE
        WHEN actual_ctr = 0 THEN 0
        ELSE (1 - ABS(predicted_ctr - actual_ctr) / NULLIF(actual_ctr, 0)) * 100
    END)::NUMERIC, 2) as avg_ctr_accuracy_pct,

    -- ROAS metrics
    ROUND(AVG(predicted_roas)::NUMERIC, 3) as avg_predicted_roas,
    ROUND(AVG(actual_roas)::NUMERIC, 3) as avg_actual_roas,
    ROUND(AVG(ABS(predicted_roas - actual_roas))::NUMERIC, 3) as avg_roas_error,

    -- Performance
    ROUND(AVG(council_score)::NUMERIC, 3) as avg_council_score,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    ROUND(SUM(spend)::NUMERIC, 2) as total_spend
FROM predictions
WHERE actual_ctr IS NOT NULL
GROUP BY platform
ORDER BY total_predictions DESC;

COMMENT ON VIEW prediction_accuracy_by_platform IS 'Platform-specific model accuracy comparison';

-- Hook Type Performance View
CREATE OR REPLACE VIEW prediction_accuracy_by_hook AS
SELECT
    hook_type,
    COUNT(*) as total_predictions,
    COUNT(actual_ctr) as predictions_with_actuals,

    -- Prediction accuracy
    ROUND(AVG(ABS(predicted_ctr - actual_ctr))::NUMERIC, 5) as avg_ctr_error,
    ROUND(AVG(ABS(predicted_roas - actual_roas))::NUMERIC, 3) as avg_roas_error,

    -- Average performance
    ROUND(AVG(actual_ctr)::NUMERIC, 5) as avg_actual_ctr,
    ROUND(AVG(actual_roas)::NUMERIC, 3) as avg_actual_roas,
    ROUND(AVG(actual_conversion)::NUMERIC, 5) as avg_actual_conversion,

    -- Council confidence
    ROUND(AVG(council_score)::NUMERIC, 3) as avg_council_score,

    -- Business metrics
    ROUND(AVG(CASE WHEN clicks > 0 THEN spend / clicks ELSE NULL END)::NUMERIC, 3) as avg_cpc,
    ROUND(AVG(CASE WHEN impressions > 0 THEN spend / impressions * 1000 ELSE NULL END)::NUMERIC, 3) as avg_cpm
FROM predictions
WHERE actual_ctr IS NOT NULL
GROUP BY hook_type
ORDER BY avg_actual_ctr DESC;

COMMENT ON VIEW prediction_accuracy_by_hook IS 'Hook type performance and prediction accuracy analysis';

-- Prediction Outliers View
CREATE OR REPLACE VIEW prediction_outliers AS
SELECT
    id,
    video_id,
    ad_id,
    platform,
    hook_type,
    template_type,
    council_score,
    predicted_ctr,
    actual_ctr,
    ROUND(ABS(predicted_ctr - actual_ctr)::NUMERIC, 5) as ctr_error,
    ROUND(CASE
        WHEN actual_ctr = 0 THEN 100
        ELSE ABS(predicted_ctr - actual_ctr) / NULLIF(actual_ctr, 0) * 100
    END::NUMERIC, 2) as ctr_error_pct,
    predicted_roas,
    actual_roas,
    ROUND(ABS(predicted_roas - actual_roas)::NUMERIC, 3) as roas_error,
    created_at
FROM predictions
WHERE actual_ctr IS NOT NULL
  AND (
    ABS(predicted_ctr - actual_ctr) > 0.02
    OR (actual_ctr > 0 AND ABS(predicted_ctr - actual_ctr) / actual_ctr > 0.5)
    OR ABS(predicted_roas - actual_roas) > 1.0
    OR (actual_roas > 0 AND ABS(predicted_roas - actual_roas) / actual_roas > 0.5)
  )
ORDER BY
    CASE
        WHEN actual_ctr = 0 THEN 0
        ELSE ABS(predicted_ctr - actual_ctr) / NULLIF(actual_ctr, 0)
    END DESC;

COMMENT ON VIEW prediction_outliers IS 'Predictions with large errors requiring investigation';

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Function to calculate prediction accuracy score (0-100)
CREATE OR REPLACE FUNCTION calculate_prediction_score(
    p_predicted_ctr FLOAT,
    p_actual_ctr FLOAT,
    p_predicted_roas FLOAT,
    p_actual_roas FLOAT,
    p_predicted_conversion FLOAT,
    p_actual_conversion FLOAT
)
RETURNS FLOAT AS $$
DECLARE
    ctr_accuracy FLOAT;
    roas_accuracy FLOAT;
    conversion_accuracy FLOAT;
    overall_score FLOAT;
BEGIN
    -- Calculate CTR accuracy (0-100)
    IF p_actual_ctr = 0 THEN
        ctr_accuracy := CASE WHEN p_predicted_ctr = 0 THEN 100 ELSE 0 END;
    ELSE
        ctr_accuracy := GREATEST(0, 100 - (ABS(p_predicted_ctr - p_actual_ctr) / p_actual_ctr * 100));
    END IF;

    -- Calculate ROAS accuracy (0-100)
    IF p_actual_roas = 0 THEN
        roas_accuracy := CASE WHEN p_predicted_roas = 0 THEN 100 ELSE 0 END;
    ELSE
        roas_accuracy := GREATEST(0, 100 - (ABS(p_predicted_roas - p_actual_roas) / p_actual_roas * 100));
    END IF;

    -- Calculate conversion accuracy (0-100)
    IF p_actual_conversion = 0 THEN
        conversion_accuracy := CASE WHEN p_predicted_conversion = 0 THEN 100 ELSE 0 END;
    ELSE
        conversion_accuracy := GREATEST(0, 100 - (ABS(p_predicted_conversion - p_actual_conversion) / p_actual_conversion * 100));
    END IF;

    -- Weighted average (CTR and ROAS weighted higher)
    overall_score := (0.4 * ctr_accuracy) + (0.4 * roas_accuracy) + (0.2 * conversion_accuracy);

    RETURN ROUND(overall_score::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION calculate_prediction_score IS 'Calculate overall prediction accuracy score (0-100)';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002: Predictions table completed successfully';
    RAISE NOTICE '   - predictions table with full tracking';
    RAISE NOTICE '   - 4 analytical views for accuracy monitoring';
    RAISE NOTICE '   - calculate_prediction_score() function';
END $$;
