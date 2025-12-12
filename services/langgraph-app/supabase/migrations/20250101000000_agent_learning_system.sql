-- Agent Learning System - Unlimited Learning Infrastructure
-- Creates tables and functions for auto-discovery and learning

-- 1. Agent Memory Table (stores all learning)
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT NOT NULL,
    value JSONB NOT NULL,
    type TEXT NOT NULL, -- 'structure_discovery', 'interaction', 'agent_patterns', 'daily_discovery'
    thread_id TEXT,
    agent_name TEXT,
    query TEXT,
    response TEXT,
    embeddings VECTOR(1536), -- For semantic search
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Agents can view own memory"
    ON agent_memory FOR SELECT
    USING (true); -- All agents can view (adjust based on your needs)

CREATE POLICY "Agents can insert memory"
    ON agent_memory FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Agents can update own memory"
    ON agent_memory FOR UPDATE
    USING (true);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_agent_memory_key ON agent_memory(key);
CREATE INDEX IF NOT EXISTS idx_agent_memory_type ON agent_memory(type);
CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_name ON agent_memory(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_memory_created_at ON agent_memory(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_memory_embeddings ON agent_memory USING ivfflat (embeddings vector_cosine_ops);

-- 2. Auto-Discovery Functions

-- Get all tables
CREATE OR REPLACE FUNCTION get_all_tables()
RETURNS TABLE(table_name TEXT, row_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.table_name::TEXT,
        COALESCE(pg_class.reltuples::BIGINT, 0) as row_count
    FROM information_schema.tables t
    LEFT JOIN pg_class ON pg_class.relname = t.table_name
    WHERE t.table_schema = 'public'
    AND t.table_type = 'BASE TABLE'
    ORDER BY t.table_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get all functions
CREATE OR REPLACE FUNCTION get_all_functions()
RETURNS TABLE(function_name TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT p.proname::TEXT as function_name
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public'
    AND p.prokind = 'f'  -- SQL functions
    ORDER BY p.proname;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 3. Semantic Search Function

-- Semantic search memories
CREATE OR REPLACE FUNCTION semantic_search_memories(
    query_embedding VECTOR(1536),
    limit_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    query TEXT,
    response TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        am.id,
        am.query,
        am.response,
        1 - (am.embeddings <=> query_embedding) AS similarity
    FROM agent_memory am
    WHERE am.embeddings IS NOT NULL
    ORDER BY am.embeddings <=> query_embedding
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 4. Human Approval Queue (for dangerous actions)

CREATE TABLE IF NOT EXISTS human_approval_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tool_name TEXT NOT NULL,
    parameters JSONB NOT NULL,
    risk_level TEXT NOT NULL, -- 'LOW', 'MEDIUM', 'HIGH'
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
    requested_by TEXT,
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE human_approval_queue ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Agents can create approval requests"
    ON human_approval_queue FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Agents can view own requests"
    ON human_approval_queue FOR SELECT
    USING (true);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_approval_queue_status ON human_approval_queue(status);
CREATE INDEX IF NOT EXISTS idx_approval_queue_created_at ON human_approval_queue(created_at DESC);

-- 5. Agent Execution Log (for monitoring)

CREATE TABLE IF NOT EXISTS agent_execution_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name TEXT NOT NULL,
    operation TEXT,
    input_data JSONB,
    result JSONB,
    execution_time FLOAT,
    success BOOLEAN,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Enable RLS
ALTER TABLE agent_execution_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Agents can log executions"
    ON agent_execution_log FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Agents can view logs"
    ON agent_execution_log FOR SELECT
    USING (true);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_execution_log_agent_name ON agent_execution_log(agent_name);
CREATE INDEX IF NOT EXISTS idx_execution_log_created_at ON agent_execution_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_log_success ON agent_execution_log(success);

-- 6. Helper function to update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for agent_memory
CREATE TRIGGER update_agent_memory_updated_at
    BEFORE UPDATE ON agent_memory
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

