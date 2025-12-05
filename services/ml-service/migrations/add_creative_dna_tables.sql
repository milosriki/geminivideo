-- Creative DNA Tables Migration
-- Agent 48: DNA Extraction for Compounding Success
-- Run this migration to add Creative DNA tables to the database

-- Table 1: Creative Formulas
-- Stores winning formulas per account
CREATE TABLE IF NOT EXISTS creative_formulas (
    formula_id VARCHAR(255) PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL UNIQUE,
    formula_data JSONB NOT NULL,
    sample_size INTEGER NOT NULL,
    min_roas_threshold FLOAT NOT NULL DEFAULT 3.0,
    avg_roas FLOAT,
    avg_ctr FLOAT,
    avg_conversion_rate FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_creative_formulas_account ON creative_formulas(account_id);
CREATE INDEX IF NOT EXISTS idx_creative_formulas_created ON creative_formulas(created_at);


-- Table 2: Creative DNA Extractions
-- Individual DNA extraction records
CREATE TABLE IF NOT EXISTS creative_dna_extractions (
    extraction_id VARCHAR(255) PRIMARY KEY,
    creative_id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    hook_dna JSONB,
    visual_dna JSONB,
    audio_dna JSONB,
    pacing_dna JSONB,
    copy_dna JSONB,
    cta_dna JSONB,
    ctr FLOAT,
    roas FLOAT,
    conversion_rate FLOAT,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_dna_extractions_creative ON creative_dna_extractions(creative_id);
CREATE INDEX IF NOT EXISTS idx_dna_extractions_account ON creative_dna_extractions(account_id);
CREATE INDEX IF NOT EXISTS idx_dna_extractions_extracted ON creative_dna_extractions(extracted_at);


-- Table 3: DNA Applications
-- Track DNA applications to creatives
CREATE TABLE IF NOT EXISTS dna_applications (
    application_id VARCHAR(255) PRIMARY KEY,
    creative_id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    formula_id VARCHAR(255) NOT NULL,
    suggestions JSONB NOT NULL,
    suggestions_count INTEGER DEFAULT 0,
    applied BOOLEAN DEFAULT FALSE,
    applied_at TIMESTAMP WITH TIME ZONE,
    performance_before JSONB,
    performance_after JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_dna_applications_creative ON dna_applications(creative_id);
CREATE INDEX IF NOT EXISTS idx_dna_applications_account ON dna_applications(account_id);
CREATE INDEX IF NOT EXISTS idx_dna_applications_created ON dna_applications(created_at);


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


-- Sample queries for verification

-- Get all formulas
-- SELECT formula_id, account_id, sample_size, avg_roas, created_at FROM creative_formulas;

-- Get DNA extractions for an account
-- SELECT extraction_id, creative_id, roas, ctr, extracted_at
-- FROM creative_dna_extractions
-- WHERE account_id = 'your_account_id'
-- ORDER BY extracted_at DESC;

-- Get DNA applications for a creative
-- SELECT application_id, suggestions_count, applied, created_at
-- FROM dna_applications
-- WHERE creative_id = 'your_creative_id';

-- Get top performing creatives with DNA
-- SELECT
--     e.creative_id,
--     e.roas,
--     e.ctr,
--     e.hook_dna->>'hook_type' as hook_type,
--     e.visual_dna->>'visual_pattern' as visual_pattern
-- FROM creative_dna_extractions e
-- WHERE e.account_id = 'your_account_id' AND e.roas >= 3.0
-- ORDER BY e.roas DESC
-- LIMIT 10;

COMMIT;

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Creative DNA tables created successfully';
    RAISE NOTICE '   - creative_formulas: Winning formulas per account';
    RAISE NOTICE '   - creative_dna_extractions: Individual DNA records';
    RAISE NOTICE '   - dna_applications: DNA application tracking';
    RAISE NOTICE '';
    RAISE NOTICE '🧬 Agent 48: DNA Extraction System - READY';
END $$;
