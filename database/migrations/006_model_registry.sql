-- Migration: 006_model_registry.sql
-- Description: Model versioning table for champion-challenger pattern
-- Purpose: Track ML model versions and manage champion model selection

-- Create the model_registry table
CREATE TABLE IF NOT EXISTS model_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    training_metrics JSONB,
    is_champion BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    promoted_at TIMESTAMPTZ,
    UNIQUE(model_name, version)
);

-- Ensure only one champion model per model_name
-- This is a partial unique index that only applies when is_champion = true
CREATE UNIQUE INDEX idx_champion_per_model ON model_registry(model_name) WHERE is_champion = true;

-- Create index for efficient lookups
CREATE INDEX idx_model_registry_name_version ON model_registry(model_name, version);
CREATE INDEX idx_model_registry_created ON model_registry(created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE model_registry IS 'Model versioning table for champion-challenger pattern: tracks ML model versions and champion selection';
COMMENT ON INDEX idx_champion_per_model IS 'Ensures only one champion model exists per model_name';
COMMENT ON COLUMN model_registry.training_metrics IS 'JSONB field storing training metrics like accuracy, loss, F1 score, etc.';
COMMENT ON COLUMN model_registry.is_champion IS 'Indicates if this version is the active champion model';
COMMENT ON COLUMN model_registry.promoted_at IS 'Timestamp when this version was promoted to champion';
