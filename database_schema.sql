-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop existing tables to ensure clean state
DROP TABLE IF EXISTS videos CASCADE;
DROP TABLE IF EXISTS render_jobs CASCADE;
DROP TABLE IF EXISTS blueprints CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255),
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  product_name VARCHAR(255) NOT NULL,
  offer TEXT NOT NULL,
  target_avatar VARCHAR(255),
  pain_points JSONB DEFAULT '[]',
  desires JSONB DEFAULT '[]',
  status VARCHAR(50) DEFAULT 'draft',
  total_generated INTEGER DEFAULT 0,
  approved_count INTEGER DEFAULT 0,
  rejected_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Blueprints table
CREATE TABLE IF NOT EXISTS blueprints (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  campaign_id UUID REFERENCES campaigns(id) ON DELETE CASCADE,
  title VARCHAR(255),
  hook_text TEXT,
  hook_type VARCHAR(100),
  script_json JSONB,
  council_score FLOAT,
  predicted_roas FLOAT,
  confidence FLOAT,
  verdict VARCHAR(20),
  rank INTEGER,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Render jobs table
CREATE TABLE IF NOT EXISTS render_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  blueprint_id UUID REFERENCES blueprints(id),
  campaign_id UUID REFERENCES campaigns(id),
  platform VARCHAR(50),
  quality VARCHAR(50),
  status VARCHAR(50) DEFAULT 'pending',
  progress FLOAT DEFAULT 0,
  current_stage VARCHAR(100),
  error TEXT,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  campaign_id UUID REFERENCES campaigns(id),
  blueprint_id UUID REFERENCES blueprints(id),
  render_job_id UUID REFERENCES render_jobs(id),
  storage_path TEXT,
  storage_url TEXT,
  duration_seconds FLOAT,
  resolution VARCHAR(50),
  file_size_bytes BIGINT,
  platform VARCHAR(50),
  actual_roas FLOAT,
  impressions INTEGER DEFAULT 0,
  clicks INTEGER DEFAULT 0,
  conversions INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_user ON campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign ON blueprints(campaign_id);
CREATE INDEX IF NOT EXISTS idx_videos_campaign ON videos(campaign_id);
