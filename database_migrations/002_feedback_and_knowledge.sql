-- ============================================================================
-- Migration 002: Feedback Loop & Knowledge Base Tables
-- ============================================================================
-- Purpose: Add persistent storage for feedback, knowledge patterns, and model performance
-- Run with: psql $DATABASE_URL -f 002_feedback_and_knowledge.sql
-- ============================================================================

-- Feedback Events Table
-- Stores actual performance vs predictions for learning
CREATE TABLE IF NOT EXISTS feedback_events (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(255),
    prediction_id VARCHAR(255),
    predicted_ctr FLOAT,
    actual_ctr FLOAT,
    predicted_score FLOAT,
    actual_performance VARCHAR(50),
    feedback_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_feedback_video ON feedback_events(video_id);
CREATE INDEX IF NOT EXISTS idx_feedback_prediction ON feedback_events(prediction_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created ON feedback_events(created_at DESC);


-- Model Performance Tracking
-- Track accuracy, latency, cost per model over time
CREATE TABLE IF NOT EXISTS model_performance (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    evaluation_type VARCHAR(50),
    predicted_value FLOAT,
    actual_value FLOAT,
    error FLOAT,
    latency_ms FLOAT,
    cost_usd FLOAT,
    input_tokens INT,
    output_tokens INT,
    cache_hit BOOLEAN DEFAULT FALSE,
    early_exit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_model_perf_name ON model_performance(model_name);
CREATE INDEX IF NOT EXISTS idx_model_perf_type ON model_performance(evaluation_type);
CREATE INDEX IF NOT EXISTS idx_model_perf_created ON model_performance(created_at DESC);


-- Winning Patterns Table
-- Store patterns from successful ads for RAG
CREATE TABLE IF NOT EXISTS winning_patterns (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,  -- foreplay, meta_library, tiktok, internal
    hook_type VARCHAR(100),
    emotional_triggers TEXT[],
    visual_style VARCHAR(100),
    pacing VARCHAR(50),
    cta_style VARCHAR(100),
    transcript TEXT,
    performance_tier VARCHAR(50),  -- top_1_percent, top_10_percent, average
    industry VARCHAR(100),
    ctr FLOAT,
    raw_data JSONB DEFAULT '{}',
    embedding VECTOR(384),  -- For pgvector semantic search
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_patterns_source ON winning_patterns(source);
CREATE INDEX IF NOT EXISTS idx_patterns_industry ON winning_patterns(industry);
CREATE INDEX IF NOT EXISTS idx_patterns_tier ON winning_patterns(performance_tier);
CREATE INDEX IF NOT EXISTS idx_patterns_ctr ON winning_patterns(ctr DESC) WHERE ctr IS NOT NULL;

-- Vector index for semantic search (requires pgvector extension)
-- CREATE INDEX IF NOT EXISTS idx_patterns_embedding ON winning_patterns USING ivfflat (embedding vector_cosine_ops);


-- A/B Test Results Table
-- Track experiments and their outcomes
CREATE TABLE IF NOT EXISTS ab_tests (
    id SERIAL PRIMARY KEY,
    experiment_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    description TEXT,
    status VARCHAR(50) DEFAULT 'running',  -- running, completed, stopped

    -- Variants
    control_variant_id VARCHAR(255),
    test_variant_id VARCHAR(255),

    -- Sample sizes
    control_size INT DEFAULT 0,
    test_size INT DEFAULT 0,

    -- Metrics
    metric_name VARCHAR(100),  -- CTR, ROAS, CPC, etc.
    control_value FLOAT,
    test_value FLOAT,
    lift_percent FLOAT,
    p_value FLOAT,
    is_significant BOOLEAN DEFAULT FALSE,

    -- Timestamps
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ab_tests_experiment ON ab_tests(experiment_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);


-- Knowledge Injection Log
-- Track what knowledge was injected and when
CREATE TABLE IF NOT EXISTS knowledge_injections (
    id SERIAL PRIMARY KEY,
    query VARCHAR(500),
    industry VARCHAR(100),

    -- Source counts
    foreplay_count INT DEFAULT 0,
    meta_library_count INT DEFAULT 0,
    tiktok_count INT DEFAULT 0,
    youtube_count INT DEFAULT 0,
    kaggle_count INT DEFAULT 0,
    internal_count INT DEFAULT 0,

    total_patterns INT DEFAULT 0,
    errors TEXT[],

    -- Storage location
    gcs_path VARCHAR(500),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_injections_industry ON knowledge_injections(industry);
CREATE INDEX IF NOT EXISTS idx_injections_created ON knowledge_injections(created_at DESC);


-- Cost Tracking Table
-- Track AI API costs over time
CREATE TABLE IF NOT EXISTS api_costs (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    operation_type VARCHAR(50),  -- evaluation, generation, embedding

    input_tokens INT,
    output_tokens INT,
    total_tokens INT,

    cost_usd FLOAT,
    latency_ms FLOAT,

    cache_hit BOOLEAN DEFAULT FALSE,
    early_exit BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_costs_model ON api_costs(model_name);
CREATE INDEX IF NOT EXISTS idx_costs_created ON api_costs(created_at DESC);

-- Aggregated view for cost reporting
CREATE OR REPLACE VIEW daily_costs AS
SELECT
    DATE(created_at) as date,
    model_name,
    COUNT(*) as calls,
    SUM(cost_usd) as total_cost,
    AVG(latency_ms) as avg_latency,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as cache_hit_rate
FROM api_costs
GROUP BY DATE(created_at), model_name
ORDER BY date DESC, total_cost DESC;


-- Add columns to existing videos table for better tracking
ALTER TABLE videos ADD COLUMN IF NOT EXISTS predicted_ctr FLOAT;
ALTER TABLE videos ADD COLUMN IF NOT EXISTS prediction_confidence FLOAT;
ALTER TABLE videos ADD COLUMN IF NOT EXISTS models_used TEXT[];


-- Add column to blueprints for pattern matching
ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS matched_patterns JSONB DEFAULT '[]';
ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS pattern_similarity_score FLOAT;


-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- Model accuracy over time
CREATE OR REPLACE VIEW model_accuracy AS
SELECT
    model_name,
    DATE(created_at) as date,
    COUNT(*) as predictions,
    AVG(ABS(predicted_value - actual_value)) as mae,
    STDDEV(predicted_value - actual_value) as std_error,
    AVG(CASE WHEN ABS(predicted_value - actual_value) < 0.02 THEN 1.0 ELSE 0.0 END) as accuracy_2pct
FROM model_performance
WHERE actual_value IS NOT NULL
GROUP BY model_name, DATE(created_at)
ORDER BY date DESC, model_name;


-- Pattern effectiveness by source
CREATE OR REPLACE VIEW pattern_effectiveness AS
SELECT
    source,
    industry,
    performance_tier,
    COUNT(*) as pattern_count,
    AVG(ctr) as avg_ctr,
    MAX(ctr) as max_ctr
FROM winning_patterns
WHERE ctr IS NOT NULL
GROUP BY source, industry, performance_tier
ORDER BY avg_ctr DESC;


-- Feedback summary
CREATE OR REPLACE VIEW feedback_summary AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as feedback_count,
    AVG(predicted_ctr) as avg_predicted,
    AVG(actual_ctr) as avg_actual,
    AVG(ABS(predicted_ctr - actual_ctr)) as avg_error,
    CORR(predicted_ctr, actual_ctr) as correlation
FROM feedback_events
WHERE actual_ctr IS NOT NULL
GROUP BY DATE(created_at)
ORDER BY date DESC;


-- ============================================================================
-- GRANTS (adjust user as needed)
-- ============================================================================

-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO geminivideo_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO geminivideo_app;


COMMENT ON TABLE feedback_events IS 'Stores prediction vs actual performance for model learning';
COMMENT ON TABLE model_performance IS 'Tracks per-model accuracy, latency, and cost over time';
COMMENT ON TABLE winning_patterns IS 'RAG knowledge base of successful ad patterns';
COMMENT ON TABLE ab_tests IS 'A/B test experiments and results';
COMMENT ON TABLE knowledge_injections IS 'Log of knowledge injection operations';
COMMENT ON TABLE api_costs IS 'Detailed API cost tracking';
