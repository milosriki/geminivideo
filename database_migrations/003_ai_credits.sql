-- ============================================================================
-- Migration 003: AI Credits System
-- ============================================================================
-- Purpose: Add AI credits tracking for user operations
-- Run with: psql $DATABASE_URL -f 003_ai_credits.sql
-- ============================================================================

-- AI Credits Table
-- Stores user credit balances
CREATE TABLE IF NOT EXISTS ai_credits (
    user_id VARCHAR(255) PRIMARY KEY,
    total_credits INTEGER NOT NULL DEFAULT 10000,
    used_credits INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- AI Credit Usage Table
-- Stores detailed credit usage history
CREATE TABLE IF NOT EXISTS ai_credit_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    credits_used INTEGER NOT NULL,
    operation VARCHAR(100) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_credit_usage_user ON ai_credit_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_usage_created ON ai_credit_usage(created_at DESC);

-- Initialize default user with credits
INSERT INTO ai_credits (user_id, total_credits, used_credits)
VALUES ('default_user', 10000, 1500)
ON CONFLICT (user_id) DO NOTHING;

-- Seed some sample usage history for the default user
INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
SELECT 'default_user', 500, 'video_generation', '{"duration": 30, "quality": "hd"}'::jsonb, NOW() - INTERVAL '2 days'
WHERE NOT EXISTS (SELECT 1 FROM ai_credit_usage WHERE user_id = 'default_user' LIMIT 1);

INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
SELECT 'default_user', 300, 'video_analysis', '{"clips_analyzed": 5}'::jsonb, NOW() - INTERVAL '1 day'
WHERE NOT EXISTS (SELECT 1 FROM ai_credit_usage WHERE user_id = 'default_user' AND operation = 'video_analysis');

INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
SELECT 'default_user', 200, 'script_generation', '{"variants": 3}'::jsonb, NOW() - INTERVAL '1 day'
WHERE NOT EXISTS (SELECT 1 FROM ai_credit_usage WHERE user_id = 'default_user' AND operation = 'script_generation');

INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
SELECT 'default_user', 400, 'video_generation', '{"duration": 60, "quality": "4k"}'::jsonb, NOW() - INTERVAL '12 hours'
WHERE NOT EXISTS (SELECT 1 FROM ai_credit_usage WHERE user_id = 'default_user' AND credits_used = 400);

INSERT INTO ai_credit_usage (user_id, credits_used, operation, metadata, created_at)
SELECT 'default_user', 100, 'text_analysis', '{"words": 500}'::jsonb, NOW() - INTERVAL '6 hours'
WHERE NOT EXISTS (SELECT 1 FROM ai_credit_usage WHERE user_id = 'default_user' AND operation = 'text_analysis');

COMMENT ON TABLE ai_credits IS 'Stores user AI credit balances for tracking usage';
COMMENT ON TABLE ai_credit_usage IS 'Detailed history of AI credit usage by operation';
