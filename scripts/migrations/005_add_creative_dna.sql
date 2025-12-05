-- ============================================================================
-- Migration 005: Add Creative DNA Tables
-- ============================================================================
-- Purpose: DNA extraction from winning ads for pattern recognition
-- For: Compound success by replicating winning formulas
-- Agent: 48 - DNA Extraction System
-- ============================================================================

-- ============================================================================
-- CREATIVE FORMULAS TABLE
-- ============================================================================
-- Stores winning formulas per account

CREATE TABLE IF NOT EXISTS creative_formulas (
    formula_id VARCHAR(255) PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL UNIQUE,

    -- Formula data
    formula_data JSONB NOT NULL,

    -- Sample statistics
    sample_size INTEGER NOT NULL,
    min_roas_threshold FLOAT NOT NULL DEFAULT 3.0,

    -- Performance metrics
    avg_roas FLOAT,
    avg_ctr FLOAT,
    avg_conversion_rate FLOAT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_creative_formulas_account ON creative_formulas(account_id);
CREATE INDEX IF NOT EXISTS idx_creative_formulas_created ON creative_formulas(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_creative_formulas_roas ON creative_formulas(avg_roas DESC);

COMMENT ON TABLE creative_formulas IS
'Winning creative formulas extracted from high-performing ads per account';

COMMENT ON COLUMN creative_formulas.formula_data IS
'JSONB containing the DNA formula: hooks, visuals, audio, pacing, copy, and CTA patterns';

-- ============================================================================
-- CREATIVE DNA EXTRACTIONS TABLE
-- ============================================================================
-- Individual DNA extraction records

CREATE TABLE IF NOT EXISTS creative_dna_extractions (
    extraction_id VARCHAR(255) PRIMARY KEY,
    creative_id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,

    -- DNA components (each is a JSONB object with patterns)
    hook_dna JSONB,
    visual_dna JSONB,
    audio_dna JSONB,
    pacing_dna JSONB,
    copy_dna JSONB,
    cta_dna JSONB,

    -- Performance metrics
    ctr FLOAT,
    roas FLOAT,
    conversion_rate FLOAT,

    -- Timestamp
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_dna_extractions_creative ON creative_dna_extractions(creative_id);
CREATE INDEX IF NOT EXISTS idx_dna_extractions_account ON creative_dna_extractions(account_id);
CREATE INDEX IF NOT EXISTS idx_dna_extractions_extracted ON creative_dna_extractions(extracted_at DESC);
CREATE INDEX IF NOT EXISTS idx_dna_extractions_roas ON creative_dna_extractions(roas DESC);

-- Composite index for finding winning creatives by account
CREATE INDEX IF NOT EXISTS idx_dna_extractions_account_roas
    ON creative_dna_extractions(account_id, roas DESC)
    WHERE roas >= 3.0;

COMMENT ON TABLE creative_dna_extractions IS
'Individual DNA extractions from creatives with performance data';

COMMENT ON COLUMN creative_dna_extractions.hook_dna IS
'Hook patterns: type, intensity, curiosity_score, emotion, timing';

COMMENT ON COLUMN creative_dna_extractions.visual_dna IS
'Visual patterns: scenes, colors, motion, faces, products';

COMMENT ON COLUMN creative_dna_extractions.audio_dna IS
'Audio patterns: music_type, tempo, voiceover, sound_effects';

COMMENT ON COLUMN creative_dna_extractions.pacing_dna IS
'Pacing patterns: cuts_per_second, scene_duration, rhythm';

COMMENT ON COLUMN creative_dna_extractions.copy_dna IS
'Copy patterns: word_count, tone, power_words, social_proof';

COMMENT ON COLUMN creative_dna_extractions.cta_dna IS
'CTA patterns: type, placement, urgency, clarity';

-- ============================================================================
-- DNA APPLICATIONS TABLE
-- ============================================================================
-- Track DNA applications to creatives

CREATE TABLE IF NOT EXISTS dna_applications (
    application_id VARCHAR(255) PRIMARY KEY,
    creative_id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    formula_id VARCHAR(255) NOT NULL,

    -- Application data
    suggestions JSONB NOT NULL,
    suggestions_count INTEGER DEFAULT 0,

    -- Application status
    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP WITH TIME ZONE,

    -- Performance comparison
    performance_before JSONB,
    performance_after JSONB,

    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_dna_applications_creative ON dna_applications(creative_id);
CREATE INDEX IF NOT EXISTS idx_dna_applications_account ON dna_applications(account_id);
CREATE INDEX IF NOT EXISTS idx_dna_applications_formula ON dna_applications(formula_id);
CREATE INDEX IF NOT EXISTS idx_dna_applications_created ON dna_applications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dna_applications_applied ON dna_applications(applied);

COMMENT ON TABLE dna_applications IS
'Track DNA formula applications to creatives with before/after performance';

-- ============================================================================
-- TRIGGER FUNCTIONS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_creative_formulas_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update updated_at
DROP TRIGGER IF EXISTS trigger_update_creative_formulas_updated_at ON creative_formulas;
CREATE TRIGGER trigger_update_creative_formulas_updated_at
    BEFORE UPDATE ON creative_formulas
    FOR EACH ROW
    EXECUTE FUNCTION update_creative_formulas_updated_at();

-- ============================================================================
-- ANALYTICAL VIEWS
-- ============================================================================

-- View: Top performing DNA extractions
CREATE OR REPLACE VIEW top_performing_dna AS
SELECT
    extraction_id,
    creative_id,
    account_id,
    roas,
    ctr,
    conversion_rate,
    hook_dna->>'hook_type' as hook_type,
    visual_dna->>'dominant_color' as dominant_color,
    audio_dna->>'music_type' as music_type,
    copy_dna->>'tone' as copy_tone,
    cta_dna->>'cta_type' as cta_type,
    extracted_at
FROM creative_dna_extractions
WHERE roas >= 3.0
ORDER BY roas DESC, ctr DESC
LIMIT 100;

COMMENT ON VIEW top_performing_dna IS
'Top 100 DNA extractions from highest performing creatives (ROAS >= 3.0)';

-- View: Formula effectiveness
CREATE OR REPLACE VIEW formula_effectiveness AS
SELECT
    cf.formula_id,
    cf.account_id,
    cf.sample_size,
    cf.avg_roas,
    cf.avg_ctr,
    COUNT(da.application_id) as total_applications,
    COUNT(da.application_id) FILTER (WHERE da.applied = TRUE) as applied_count,
    AVG(
        CASE WHEN da.applied = TRUE AND da.performance_after IS NOT NULL
        THEN (da.performance_after->>'roas')::FLOAT
        ELSE NULL END
    ) as avg_roas_after_application,
    cf.created_at
FROM creative_formulas cf
LEFT JOIN dna_applications da ON cf.formula_id = da.formula_id
GROUP BY cf.formula_id, cf.account_id, cf.sample_size, cf.avg_roas, cf.avg_ctr, cf.created_at
ORDER BY cf.avg_roas DESC;

COMMENT ON VIEW formula_effectiveness IS
'Effectiveness of DNA formulas including application rates and results';

-- View: DNA pattern frequency
CREATE OR REPLACE VIEW dna_pattern_frequency AS
SELECT
    hook_dna->>'hook_type' as hook_type,
    visual_dna->>'visual_pattern' as visual_pattern,
    audio_dna->>'music_type' as music_type,
    copy_dna->>'tone' as copy_tone,
    cta_dna->>'cta_type' as cta_type,
    COUNT(*) as frequency,
    AVG(roas) as avg_roas,
    AVG(ctr) as avg_ctr,
    AVG(conversion_rate) as avg_conversion_rate
FROM creative_dna_extractions
WHERE roas >= 2.0  -- Only winning creatives
GROUP BY
    hook_dna->>'hook_type',
    visual_dna->>'visual_pattern',
    audio_dna->>'music_type',
    copy_dna->>'tone',
    cta_dna->>'cta_type'
ORDER BY avg_roas DESC, frequency DESC;

COMMENT ON VIEW dna_pattern_frequency IS
'Frequency and performance of DNA patterns across winning creatives';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get formula for account
CREATE OR REPLACE FUNCTION get_account_formula(p_account_id VARCHAR)
RETURNS TABLE (
    formula_id VARCHAR,
    formula_data JSONB,
    avg_roas FLOAT,
    avg_ctr FLOAT,
    sample_size INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cf.formula_id,
        cf.formula_data,
        cf.avg_roas,
        cf.avg_ctr,
        cf.sample_size
    FROM creative_formulas cf
    WHERE cf.account_id = p_account_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_account_formula IS
'Retrieve the winning formula for a specific account';

-- Function to count winning creatives for account
CREATE OR REPLACE FUNCTION count_winning_creatives(
    p_account_id VARCHAR,
    p_min_roas FLOAT DEFAULT 3.0
)
RETURNS INTEGER AS $$
DECLARE
    winning_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO winning_count
    FROM creative_dna_extractions
    WHERE account_id = p_account_id
      AND roas >= p_min_roas;

    RETURN winning_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION count_winning_creatives IS
'Count number of winning creatives for an account above ROAS threshold';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 005: Creative DNA tables completed successfully';
    RAISE NOTICE '   - creative_formulas: Winning formulas per account';
    RAISE NOTICE '   - creative_dna_extractions: Individual DNA records';
    RAISE NOTICE '   - dna_applications: DNA application tracking';
    RAISE NOTICE '   - 3 analytical views for insights';
    RAISE NOTICE '   - 2 helper functions';
    RAISE NOTICE '';
    RAISE NOTICE '🧬 Agent 48: DNA Extraction System - READY';
    RAISE NOTICE '   Extract winning patterns, compound success!';
END $$;
