-- ============================================================================
-- Migration 003: Add pgvector Extension and Embedding Tables
-- ============================================================================
-- Purpose: Enable vector similarity search for semantic matching
-- For: AI-powered content similarity and recommendation
-- Agent: 39 - Vector Embeddings Infrastructure
-- ============================================================================

-- ============================================================================
-- INSTALL PGVECTOR EXTENSION
-- ============================================================================

-- Install pgvector extension (handles both PostgreSQL 14 and 16)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE NOTICE '✅ pgvector extension installed successfully';
    ELSE
        RAISE EXCEPTION '❌ Failed to install pgvector extension';
    END IF;
END $$;

-- ============================================================================
-- VIDEO EMBEDDINGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS video_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL,

    -- Embedding vector (OpenAI text-embedding-3-large = 3072 dimensions)
    embedding vector(3072) NOT NULL,

    -- Metadata
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    model_version VARCHAR(50),
    embedding_type VARCHAR(50) NOT NULL, -- 'full_transcript', 'visual', 'audio', 'combined'

    -- Source data
    source_text TEXT,
    source_metadata JSONB DEFAULT '{}'::jsonb,

    -- Performance tracking
    generation_time_ms INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_video_embeddings_video_id ON video_embeddings(video_id);
CREATE INDEX IF NOT EXISTS idx_video_embeddings_type ON video_embeddings(embedding_type);

-- Vector similarity index (IVFFlat for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_video_embeddings_vector
    ON video_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON TABLE video_embeddings IS 'Vector embeddings for video content similarity search';
COMMENT ON COLUMN video_embeddings.embedding IS '3072-dimensional embedding vector for semantic search';

-- ============================================================================
-- SCRIPT EMBEDDINGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS script_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    blueprint_id UUID REFERENCES blueprints(id) ON DELETE CASCADE,

    -- Embedding vector
    embedding vector(3072) NOT NULL,

    -- Metadata
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    embedding_type VARCHAR(50) NOT NULL, -- 'hook', 'full_script', 'cta'

    -- Source data
    source_text TEXT NOT NULL,
    script_section VARCHAR(50), -- 'hook', 'problem', 'solution', 'cta'

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_script_embeddings_blueprint ON script_embeddings(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_script_embeddings_type ON script_embeddings(embedding_type);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS idx_script_embeddings_vector
    ON script_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON TABLE script_embeddings IS 'Vector embeddings for script content similarity';

-- ============================================================================
-- AD CREATIVE EMBEDDINGS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS ad_creative_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_id UUID NOT NULL,

    -- Embedding vector
    embedding vector(3072) NOT NULL,

    -- Creative components
    creative_type VARCHAR(50) NOT NULL, -- 'visual', 'copy', 'combined'

    -- Performance association
    performance_score DECIMAL(5, 2),
    ctr DECIMAL(8, 4),
    roas DECIMAL(8, 2),

    -- Metadata
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    source_data JSONB,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ad_creative_embeddings_ad ON ad_creative_embeddings(ad_id);
CREATE INDEX IF NOT EXISTS idx_ad_creative_embeddings_type ON ad_creative_embeddings(creative_type);
CREATE INDEX IF NOT EXISTS idx_ad_creative_embeddings_performance ON ad_creative_embeddings(performance_score DESC);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS idx_ad_creative_embeddings_vector
    ON ad_creative_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

COMMENT ON TABLE ad_creative_embeddings IS 'Vector embeddings for ad creative similarity and recommendations';

-- ============================================================================
-- WINNING AD PATTERNS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS winning_ad_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pattern_name VARCHAR(255) NOT NULL,

    -- Pattern embedding (average of winning ads)
    pattern_embedding vector(3072) NOT NULL,

    -- Performance thresholds
    min_roas DECIMAL(8, 2) DEFAULT 3.0,
    min_ctr DECIMAL(8, 4) DEFAULT 0.02,

    -- Pattern characteristics
    sample_size INTEGER NOT NULL,
    avg_roas DECIMAL(8, 2),
    avg_ctr DECIMAL(8, 4),

    -- Pattern metadata
    hook_types TEXT[],
    visual_patterns JSONB,
    copy_patterns JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Account/industry context
    account_id VARCHAR(255),
    industry VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_winning_patterns_account ON winning_ad_patterns(account_id);
CREATE INDEX IF NOT EXISTS idx_winning_patterns_industry ON winning_ad_patterns(industry);
CREATE INDEX IF NOT EXISTS idx_winning_patterns_roas ON winning_ad_patterns(avg_roas DESC);

-- Vector similarity index
CREATE INDEX IF NOT EXISTS idx_winning_patterns_vector
    ON winning_ad_patterns
    USING ivfflat (pattern_embedding vector_cosine_ops)
    WITH (lists = 50);

COMMENT ON TABLE winning_ad_patterns IS 'Learned patterns from high-performing ad creatives';

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to find similar videos by embedding
CREATE OR REPLACE FUNCTION find_similar_videos(
    query_embedding vector(3072),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    video_id UUID,
    similarity float,
    embedding_type VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ve.video_id,
        1 - (ve.embedding <=> query_embedding) as similarity,
        ve.embedding_type
    FROM video_embeddings ve
    WHERE 1 - (ve.embedding <=> query_embedding) > match_threshold
    ORDER BY ve.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_similar_videos IS 'Find videos similar to a given embedding vector';

-- Function to find similar scripts
CREATE OR REPLACE FUNCTION find_similar_scripts(
    query_embedding vector(3072),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    blueprint_id UUID,
    similarity float,
    embedding_type VARCHAR(50),
    script_section VARCHAR(50)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        se.blueprint_id,
        1 - (se.embedding <=> query_embedding) as similarity,
        se.embedding_type,
        se.script_section
    FROM script_embeddings se
    WHERE 1 - (se.embedding <=> query_embedding) > match_threshold
    ORDER BY se.embedding <=> query_embedding
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_similar_scripts IS 'Find scripts similar to a given embedding vector';

-- Function to find winning patterns
CREATE OR REPLACE FUNCTION find_matching_patterns(
    query_embedding vector(3072),
    min_similarity float DEFAULT 0.8,
    limit_count int DEFAULT 5
)
RETURNS TABLE (
    pattern_id UUID,
    pattern_name VARCHAR(255),
    similarity float,
    avg_roas DECIMAL(8, 2),
    avg_ctr DECIMAL(8, 4),
    sample_size INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        wp.id,
        wp.pattern_name,
        1 - (wp.pattern_embedding <=> query_embedding) as similarity,
        wp.avg_roas,
        wp.avg_ctr,
        wp.sample_size
    FROM winning_ad_patterns wp
    WHERE 1 - (wp.pattern_embedding <=> query_embedding) > min_similarity
    ORDER BY wp.pattern_embedding <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION find_matching_patterns IS 'Find winning ad patterns matching a given embedding';

-- ============================================================================
-- Success message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Migration 003: pgvector and embeddings completed successfully';
    RAISE NOTICE '   - pgvector extension installed';
    RAISE NOTICE '   - video_embeddings table created';
    RAISE NOTICE '   - script_embeddings table created';
    RAISE NOTICE '   - ad_creative_embeddings table created';
    RAISE NOTICE '   - winning_ad_patterns table created';
    RAISE NOTICE '   - 3 helper functions for similarity search';
    RAISE NOTICE '';
    RAISE NOTICE '🔍 Vector similarity search is now available!';
END $$;
