-- ============================================================================
-- Migration 007: Add Compound Learning Tables
-- ============================================================================
-- Purpose: Track learning compounds over time with feedback loops
-- For: Continuous improvement through systematic learning
-- Agent: 50 - Compound Learning System
-- ============================================================================

-- ============================================================================
-- LEARNING_CYCLES TABLE
-- ============================================================================
-- Track distinct learning cycles (e.g., weekly, monthly, quarterly)

CREATE TABLE IF NOT EXISTS learning_cycles (
    cycle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_name VARCHAR(255) NOT NULL,
    cycle_type VARCHAR(50) NOT NULL, -- 'weekly', 'monthly', 'quarterly', 'campaign'

    -- Cycle timing
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    -- Cycle metrics (baseline)
    baseline_roas FLOAT,
    baseline_ctr FLOAT,
    baseline_conversion_rate FLOAT,
    baseline_sample_size INTEGER,

    -- Results (measured at end of cycle)
    result_roas FLOAT,
    result_ctr FLOAT,
    result_conversion_rate FLOAT,
    result_sample_size INTEGER,

    -- Improvements
    roas_improvement_pct FLOAT,
    ctr_improvement_pct FLOAT,
    conversion_improvement_pct FLOAT,

    -- Learning insights
    insights_generated INTEGER DEFAULT 0,
    patterns_discovered INTEGER DEFAULT 0,
    recommendations_applied INTEGER DEFAULT 0,

    -- Status
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'completed', 'analyzed'

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_learning_cycles_type ON learning_cycles(cycle_type);
CREATE INDEX IF NOT EXISTS idx_learning_cycles_status ON learning_cycles(status);
CREATE INDEX IF NOT EXISTS idx_learning_cycles_start ON learning_cycles(start_date DESC);
CREATE INDEX IF NOT EXISTS idx_learning_cycles_improvement ON learning_cycles(roas_improvement_pct DESC);

COMMENT ON TABLE learning_cycles IS
'Track distinct learning cycles and their performance improvements';

-- ============================================================================
-- LEARNING_METRICS TABLE
-- ============================================================================
-- Detailed metrics tracked over time

CREATE TABLE IF NOT EXISTS learning_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_id UUID REFERENCES learning_cycles(cycle_id) ON DELETE CASCADE,

    -- Metric identification
    metric_name VARCHAR(100) NOT NULL,
    metric_category VARCHAR(50) NOT NULL, -- 'performance', 'quality', 'efficiency', 'accuracy'

    -- Values
    previous_value FLOAT,
    current_value FLOAT,
    target_value FLOAT,

    -- Change tracking
    absolute_change FLOAT,
    percentage_change FLOAT,
    trend VARCHAR(20), -- 'improving', 'declining', 'stable'

    -- Context
    account_id VARCHAR(255),
    campaign_id UUID,

    -- Timestamp
    measured_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_learning_metrics_cycle ON learning_metrics(cycle_id);
CREATE INDEX IF NOT EXISTS idx_learning_metrics_name ON learning_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_learning_metrics_category ON learning_metrics(metric_category);
CREATE INDEX IF NOT EXISTS idx_learning_metrics_trend ON learning_metrics(trend);
CREATE INDEX IF NOT EXISTS idx_learning_metrics_account ON learning_metrics(account_id);

COMMENT ON TABLE learning_metrics IS
'Detailed metrics tracked across learning cycles';

-- ============================================================================
-- FEEDBACK_LOOPS TABLE
-- ============================================================================
-- Track feedback loops and their effectiveness

CREATE TABLE IF NOT EXISTS feedback_loops (
    loop_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loop_name VARCHAR(255) NOT NULL,
    loop_type VARCHAR(100) NOT NULL, -- 'performance_optimization', 'pattern_refinement', 'model_tuning'

    -- Loop configuration
    trigger_condition JSONB NOT NULL, -- Conditions that trigger this loop
    actions JSONB NOT NULL, -- Actions taken when triggered
    frequency VARCHAR(50), -- 'realtime', 'hourly', 'daily', 'weekly'

    -- Effectiveness tracking
    activation_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    success_rate FLOAT,

    -- Performance impact
    avg_improvement_pct FLOAT,
    total_value_generated FLOAT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_activated_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_loops_type ON feedback_loops(loop_type);
CREATE INDEX IF NOT EXISTS idx_feedback_loops_active ON feedback_loops(is_active);
CREATE INDEX IF NOT EXISTS idx_feedback_loops_success ON feedback_loops(success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_loops_activated ON feedback_loops(last_activated_at DESC);

COMMENT ON TABLE feedback_loops IS
'Automated feedback loops for continuous improvement';

-- ============================================================================
-- FEEDBACK_EVENTS TABLE
-- ============================================================================
-- Log individual feedback loop activations

CREATE TABLE IF NOT EXISTS feedback_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loop_id UUID NOT NULL REFERENCES feedback_loops(loop_id) ON DELETE CASCADE,

    -- Event details
    trigger_data JSONB NOT NULL,
    actions_taken JSONB NOT NULL,

    -- Results
    outcome VARCHAR(50), -- 'success', 'failure', 'partial'
    result_data JSONB,

    -- Impact
    improvement_value FLOAT,
    metrics_affected TEXT[],

    -- Timestamp
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_events_loop ON feedback_events(loop_id);
CREATE INDEX IF NOT EXISTS idx_feedback_events_outcome ON feedback_events(outcome);
CREATE INDEX IF NOT EXISTS idx_feedback_events_occurred ON feedback_events(occurred_at DESC);

COMMENT ON TABLE feedback_events IS
'Log of individual feedback loop activations and outcomes';

-- ============================================================================
-- COMPOUND_LEARNINGS TABLE
-- ============================================================================
-- Track how learnings compound over time

CREATE TABLE IF NOT EXISTS compound_learnings (
    learning_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    learning_name VARCHAR(255) NOT NULL,

    -- Source cycles
    source_cycle_ids UUID[], -- Array of cycle_ids that contributed
    first_cycle_id UUID REFERENCES learning_cycles(cycle_id),

    -- Learning content
    learning_type VARCHAR(100) NOT NULL, -- 'pattern', 'insight', 'optimization', 'strategy'
    learning_data JSONB NOT NULL,
    confidence_score FLOAT,

    -- Compounding metrics
    initial_impact FLOAT, -- Impact when first discovered
    current_impact FLOAT, -- Current cumulative impact
    compound_rate FLOAT, -- Rate of improvement over time
    applications_count INTEGER DEFAULT 0,

    -- Validation
    validation_status VARCHAR(50) DEFAULT 'hypothesis', -- 'hypothesis', 'testing', 'validated', 'invalidated'
    validation_cycles INTEGER DEFAULT 0,

    -- Timestamps
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    last_validated_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_compound_learnings_type ON compound_learnings(learning_type);
CREATE INDEX IF NOT EXISTS idx_compound_learnings_status ON compound_learnings(validation_status);
CREATE INDEX IF NOT EXISTS idx_compound_learnings_impact ON compound_learnings(current_impact DESC);
CREATE INDEX IF NOT EXISTS idx_compound_learnings_confidence ON compound_learnings(confidence_score DESC);
CREATE INDEX IF NOT EXISTS idx_compound_learnings_first_cycle ON compound_learnings(first_cycle_id);

COMMENT ON TABLE compound_learnings IS
'Learnings that compound over time through repeated validation and application';

-- ============================================================================
-- IMPROVEMENT_TRAJECTORY TABLE
-- ============================================================================
-- Track the trajectory of improvements over time

CREATE TABLE IF NOT EXISTS improvement_trajectory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'account', 'campaign', 'platform'
    entity_id VARCHAR(255) NOT NULL,

    -- Trajectory data points
    measurement_date DATE NOT NULL,
    cycle_id UUID REFERENCES learning_cycles(cycle_id),

    -- Performance metrics
    roas FLOAT,
    ctr FLOAT,
    conversion_rate FLOAT,
    efficiency_score FLOAT,

    -- Learning indicators
    learnings_applied INTEGER DEFAULT 0,
    feedback_loops_active INTEGER DEFAULT 0,

    -- Trend
    trend_direction VARCHAR(20), -- 'improving', 'declining', 'stable'
    velocity FLOAT, -- Rate of change

    -- Timestamp
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_improvement_trajectory_entity ON improvement_trajectory(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_improvement_trajectory_date ON improvement_trajectory(measurement_date DESC);
CREATE INDEX IF NOT EXISTS idx_improvement_trajectory_cycle ON improvement_trajectory(cycle_id);
CREATE INDEX IF NOT EXISTS idx_improvement_trajectory_trend ON improvement_trajectory(trend_direction);

-- Composite index for time-series queries
CREATE INDEX IF NOT EXISTS idx_improvement_trajectory_entity_date
    ON improvement_trajectory(entity_type, entity_id, measurement_date DESC);

COMMENT ON TABLE improvement_trajectory IS
'Track performance improvement trajectories over time';

-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Update updated_at for feedback_loops
CREATE OR REPLACE FUNCTION update_feedback_loops_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_feedback_loops ON feedback_loops;
CREATE TRIGGER trigger_update_feedback_loops
    BEFORE UPDATE ON feedback_loops
    FOR EACH ROW
    EXECUTE FUNCTION update_feedback_loops_timestamp();

-- Update updated_at for compound_learnings
CREATE OR REPLACE FUNCTION update_compound_learnings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_compound_learnings ON compound_learnings;
CREATE TRIGGER trigger_update_compound_learnings
    BEFORE UPDATE ON compound_learnings
    FOR EACH ROW
    EXECUTE FUNCTION update_compound_learnings_timestamp();

-- ============================================================================
-- ANALYTICAL VIEWS
-- ============================================================================

-- View: Learning cycle performance
CREATE OR REPLACE VIEW learning_cycle_performance AS
SELECT
    cycle_id,
    cycle_name,
    cycle_type,
    start_date,
    end_date,
    baseline_roas,
    result_roas,
    roas_improvement_pct,
    baseline_ctr,
    result_ctr,
    ctr_improvement_pct,
    insights_generated,
    patterns_discovered,
    recommendations_applied,
    status
FROM learning_cycles
ORDER BY start_date DESC;

COMMENT ON VIEW learning_cycle_performance IS
'Performance summary of all learning cycles';

-- View: Compound learning effectiveness
CREATE OR REPLACE VIEW compound_learning_effectiveness AS
SELECT
    learning_id,
    learning_name,
    learning_type,
    validation_status,
    initial_impact,
    current_impact,
    current_impact - initial_impact as total_compound_value,
    ROUND(
        CASE
            WHEN initial_impact > 0 THEN
                ((current_impact - initial_impact) / initial_impact * 100)::NUMERIC
            ELSE 0
        END, 2
    ) as compound_growth_pct,
    compound_rate,
    applications_count,
    validation_cycles,
    confidence_score,
    discovered_at
FROM compound_learnings
WHERE validation_status = 'validated'
ORDER BY current_impact DESC, compound_rate DESC;

COMMENT ON VIEW compound_learning_effectiveness IS
'Effectiveness and compounding value of validated learnings';

-- View: Feedback loop effectiveness
CREATE OR REPLACE VIEW feedback_loop_effectiveness AS
SELECT
    loop_id,
    loop_name,
    loop_type,
    activation_count,
    success_count,
    ROUND((success_count::NUMERIC / NULLIF(activation_count, 0) * 100)::NUMERIC, 2) as success_rate_pct,
    avg_improvement_pct,
    total_value_generated,
    is_active,
    last_activated_at
FROM feedback_loops
WHERE activation_count > 0
ORDER BY success_rate_pct DESC, total_value_generated DESC;

COMMENT ON VIEW feedback_loop_effectiveness IS
'Effectiveness metrics for all feedback loops';

-- View: Improvement trends
CREATE OR REPLACE VIEW improvement_trends AS
SELECT
    entity_type,
    entity_id,
    COUNT(*) as measurement_count,
    MIN(measurement_date) as first_measurement,
    MAX(measurement_date) as last_measurement,
    AVG(roas) as avg_roas,
    AVG(ctr) as avg_ctr,
    AVG(velocity) as avg_velocity,
    MODE() WITHIN GROUP (ORDER BY trend_direction) as dominant_trend
FROM improvement_trajectory
GROUP BY entity_type, entity_id
ORDER BY avg_roas DESC;

COMMENT ON VIEW improvement_trends IS
'Aggregated improvement trends by entity';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate compound growth rate
CREATE OR REPLACE FUNCTION calculate_compound_rate(
    p_learning_id UUID,
    p_periods INTEGER DEFAULT 4
)
RETURNS FLOAT AS $$
DECLARE
    initial_val FLOAT;
    current_val FLOAT;
    compound_rate FLOAT;
BEGIN
    SELECT initial_impact, current_impact
    INTO initial_val, current_val
    FROM compound_learnings
    WHERE learning_id = p_learning_id;

    IF initial_val IS NULL OR initial_val = 0 OR p_periods = 0 THEN
        RETURN 0;
    END IF;

    -- Calculate CAGR: ((Current/Initial)^(1/periods) - 1) * 100
    compound_rate := (POWER(current_val / initial_val, 1.0 / p_periods) - 1) * 100;

    RETURN ROUND(compound_rate::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_compound_rate IS
'Calculate compound growth rate for a learning over specified periods';

-- Function to get active feedback loops
CREATE OR REPLACE FUNCTION get_active_feedback_loops()
RETURNS TABLE (
    loop_id UUID,
    loop_name VARCHAR,
    loop_type VARCHAR,
    success_rate FLOAT,
    last_activated_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fl.loop_id,
        fl.loop_name,
        fl.loop_type,
        fl.success_rate,
        fl.last_activated_at
    FROM feedback_loops fl
    WHERE fl.is_active = TRUE
    ORDER BY fl.success_rate DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_active_feedback_loops IS
'Get all active feedback loops with their performance metrics';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 007: Compound learning tables completed successfully';
    RAISE NOTICE '   - learning_cycles: Track learning cycles';
    RAISE NOTICE '   - learning_metrics: Detailed metric tracking';
    RAISE NOTICE '   - feedback_loops: Automated improvement loops';
    RAISE NOTICE '   - feedback_events: Loop activation logs';
    RAISE NOTICE '   - compound_learnings: Compounding insights';
    RAISE NOTICE '   - improvement_trajectory: Performance trends';
    RAISE NOTICE '   - 4 analytical views';
    RAISE NOTICE '   - 2 helper functions';
    RAISE NOTICE '';
    RAISE NOTICE '📈 Agent 50: Compound Learning System - READY';
    RAISE NOTICE '   Small improvements compound into massive gains!';
END $$;
