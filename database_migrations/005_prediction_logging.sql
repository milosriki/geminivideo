-- ============================================================================
-- Migration 005: ML Prediction Logging & Validation System
-- ============================================================================
-- Purpose: Track all ML predictions and compare with actual performance
-- For: €5M Investment Validation - Model Accuracy & ROI Tracking
-- Run with: psql $DATABASE_URL -f 005_prediction_logging.sql
-- ============================================================================

-- Predictions Table
-- Comprehensive prediction tracking for model validation
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
    council_score FLOAT NOT NULL,  -- AI council confidence (0-1)
    hook_type VARCHAR(100) NOT NULL,
    template_type VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',  -- Stores accuracy metrics and additional context

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

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_predictions_platform_created ON predictions(platform, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_hook_created ON predictions(hook_type, created_at DESC);


-- ============================================================================
-- ANALYTICAL VIEWS
-- ============================================================================

-- Overall Model Accuracy View
-- Shows accuracy metrics across all predictions with actuals
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
    ROUND(AVG(council_score)::NUMERIC, 3) as avg_council_score,
    ROUND(CORR(council_score,
        CASE WHEN actual_ctr > 0 THEN actual_ctr ELSE NULL END
    )::NUMERIC, 3) as council_score_ctr_correlation

FROM predictions
WHERE actual_ctr IS NOT NULL;


-- Platform-specific Accuracy View
-- Compare model performance across different platforms
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
    ROUND(AVG(CASE
        WHEN actual_roas = 0 THEN 0
        ELSE (1 - ABS(predicted_roas - actual_roas) / NULLIF(actual_roas, 0)) * 100
    END)::NUMERIC, 2) as avg_roas_accuracy_pct,

    -- Performance
    ROUND(AVG(council_score)::NUMERIC, 3) as avg_council_score,
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    ROUND(SUM(spend)::NUMERIC, 2) as total_spend

FROM predictions
WHERE actual_ctr IS NOT NULL
GROUP BY platform
ORDER BY total_predictions DESC;


-- Hook Type Performance View
-- Analyze which hook types have best prediction accuracy
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


-- Template Type Performance View
-- Analyze template effectiveness
CREATE OR REPLACE VIEW prediction_accuracy_by_template AS
SELECT
    template_type,
    COUNT(*) as total_predictions,
    COUNT(actual_ctr) as predictions_with_actuals,

    -- Accuracy
    ROUND(AVG(ABS(predicted_ctr - actual_ctr))::NUMERIC, 5) as avg_ctr_error,
    ROUND(AVG(ABS(predicted_roas - actual_roas))::NUMERIC, 3) as avg_roas_error,

    -- Performance
    ROUND(AVG(actual_ctr)::NUMERIC, 5) as avg_actual_ctr,
    ROUND(AVG(actual_roas)::NUMERIC, 3) as avg_actual_roas,
    ROUND(AVG(council_score)::NUMERIC, 3) as avg_council_score,

    -- Volume
    SUM(impressions) as total_impressions,
    SUM(clicks) as total_clicks,
    ROUND(SUM(spend)::NUMERIC, 2) as total_spend

FROM predictions
WHERE actual_ctr IS NOT NULL
GROUP BY template_type
ORDER BY avg_actual_ctr DESC;


-- Daily Accuracy Trends View
-- Track model accuracy improvement over time
CREATE OR REPLACE VIEW prediction_accuracy_daily AS
SELECT
    DATE(created_at) as prediction_date,
    COUNT(*) as total_predictions,
    COUNT(actual_ctr) as predictions_with_actuals,

    -- CTR accuracy trend
    ROUND(AVG(ABS(predicted_ctr - actual_ctr))::NUMERIC, 5) as avg_ctr_error,
    ROUND(AVG(CASE
        WHEN actual_ctr = 0 THEN 0
        ELSE (1 - ABS(predicted_ctr - actual_ctr) / NULLIF(actual_ctr, 0)) * 100
    END)::NUMERIC, 2) as avg_ctr_accuracy_pct,

    -- ROAS accuracy trend
    ROUND(AVG(ABS(predicted_roas - actual_roas))::NUMERIC, 3) as avg_roas_error,
    ROUND(AVG(CASE
        WHEN actual_roas = 0 THEN 0
        ELSE (1 - ABS(predicted_roas - actual_roas) / NULLIF(actual_roas, 0)) * 100
    END)::NUMERIC, 2) as avg_roas_accuracy_pct,

    -- Overall metrics
    ROUND(AVG(council_score)::NUMERIC, 3) as avg_council_score,
    SUM(spend) as total_spend

FROM predictions
WHERE actual_ctr IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY prediction_date DESC;


-- High Confidence Predictions View
-- Predictions where council score was high - validate confidence calibration
CREATE OR REPLACE VIEW high_confidence_predictions AS
SELECT
    id,
    video_id,
    ad_id,
    platform,
    hook_type,
    council_score,
    predicted_ctr,
    actual_ctr,
    ROUND(ABS(predicted_ctr - actual_ctr)::NUMERIC, 5) as ctr_error,
    predicted_roas,
    actual_roas,
    ROUND(ABS(predicted_roas - actual_roas)::NUMERIC, 3) as roas_error,
    impressions,
    spend,
    created_at
FROM predictions
WHERE council_score >= 0.8
  AND actual_ctr IS NOT NULL
ORDER BY council_score DESC, created_at DESC;


-- Prediction Outliers View
-- Find predictions with large errors for investigation
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
    ROUND(CASE
        WHEN actual_roas = 0 THEN 100
        ELSE ABS(predicted_roas - actual_roas) / NULLIF(actual_roas, 0) * 100
    END::NUMERIC, 2) as roas_error_pct,
    created_at
FROM predictions
WHERE actual_ctr IS NOT NULL
  AND (
    ABS(predicted_ctr - actual_ctr) > 0.02  -- More than 2% CTR error
    OR (actual_ctr > 0 AND ABS(predicted_ctr - actual_ctr) / actual_ctr > 0.5)  -- More than 50% relative error
    OR ABS(predicted_roas - actual_roas) > 1.0  -- More than 1.0 ROAS error
    OR (actual_roas > 0 AND ABS(predicted_roas - actual_roas) / actual_roas > 0.5)  -- More than 50% relative error
  )
ORDER BY
    CASE
        WHEN actual_ctr = 0 THEN 0
        ELSE ABS(predicted_ctr - actual_ctr) / NULLIF(actual_ctr, 0)
    END DESC;


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


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE predictions IS 'ML prediction tracking for €5M investment validation - tracks predicted vs actual performance';
COMMENT ON COLUMN predictions.council_score IS 'AI council confidence score (0-1) - measure of prediction confidence';
COMMENT ON COLUMN predictions.metadata IS 'Stores calculated accuracy metrics and additional context';
COMMENT ON VIEW prediction_accuracy_summary IS 'Overall model accuracy metrics across all predictions';
COMMENT ON VIEW prediction_accuracy_by_platform IS 'Platform-specific model accuracy comparison';
COMMENT ON VIEW prediction_accuracy_by_hook IS 'Hook type performance and prediction accuracy analysis';
COMMENT ON VIEW prediction_outliers IS 'Predictions with large errors requiring investigation';


-- ============================================================================
-- EXAMPLE QUERIES
-- ============================================================================

/*
-- Get overall model accuracy
SELECT * FROM prediction_accuracy_summary;

-- Compare accuracy across platforms
SELECT * FROM prediction_accuracy_by_platform;

-- Find best performing hook types
SELECT * FROM prediction_accuracy_by_hook ORDER BY avg_actual_ctr DESC LIMIT 10;

-- Check accuracy trends over last 30 days
SELECT * FROM prediction_accuracy_daily
WHERE prediction_date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY prediction_date DESC;

-- Investigate prediction outliers
SELECT * FROM prediction_outliers LIMIT 20;

-- Get predictions pending actuals (older than 7 days)
SELECT id, video_id, ad_id, platform, created_at
FROM predictions
WHERE actual_ctr IS NULL
  AND created_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY created_at ASC;

-- Calculate accuracy for a specific prediction
SELECT
    id,
    calculate_prediction_score(
        predicted_ctr, actual_ctr,
        predicted_roas, actual_roas,
        predicted_conversion, actual_conversion
    ) as accuracy_score
FROM predictions
WHERE actual_ctr IS NOT NULL
LIMIT 10;
*/
