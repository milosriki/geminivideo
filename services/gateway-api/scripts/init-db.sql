-- Initial Database Setup Script
-- Creates extensions and configurations for GeminiVideo

-- Enable UUID extension for generating UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for password hashing
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Enable pg_trgm for full-text search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create custom types (if needed)
-- These will be created by Prisma migrations

-- Set default timezone
SET timezone = 'UTC';

-- Create schema (if not exists)
CREATE SCHEMA IF NOT EXISTS public;

-- Grant privileges
GRANT ALL PRIVILEGES ON SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully for GeminiVideo';
END $$;
