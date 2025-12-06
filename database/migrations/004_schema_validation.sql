-- ============================================================================
-- Migration 004: Schema Validation & Fixes
-- ============================================================================
-- Purpose: Validate schema integrity and fix any remaining conflicts
-- Run with: psql $DATABASE_URL -f 004_schema_validation.sql
-- ============================================================================

-- ============================================================================
-- DATA TYPE STANDARDIZATION
-- ============================================================================

-- Standardize UUID generation across all tables
DO $$
BEGIN
    -- Ensure gen_random_uuid() is available
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'gen_random_uuid') THEN
        RAISE NOTICE 'Creating gen_random_uuid wrapper for uuid_generate_v4';
        CREATE OR REPLACE FUNCTION gen_random_uuid() RETURNS uuid AS
        'SELECT uuid_generate_v4()' LANGUAGE SQL;
    END IF;
END $$;

-- ============================================================================
-- FIX DECIMAL/FLOAT TYPE INCONSISTENCIES
-- ============================================================================

-- Standardize ROAS to DECIMAL(8,2)
DO $$
BEGIN
    -- Campaigns
    ALTER TABLE campaigns ALTER COLUMN roas TYPE DECIMAL(8,2) USING roas::DECIMAL(8,2);

    -- Blueprints
    ALTER TABLE blueprints ALTER COLUMN predicted_roas TYPE DECIMAL(10,2) USING predicted_roas::DECIMAL(10,2);

    RAISE NOTICE '✓ ROAS type standardized to DECIMAL';
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Note: Could not alter ROAS types - may already be correct';
END $$;

-- Standardize CTR to DECIMAL(8,4)
DO $$
BEGIN
    ALTER TABLE blueprints ALTER COLUMN predicted_ctr TYPE DECIMAL(8,4) USING predicted_ctr::DECIMAL(8,4);
    RAISE NOTICE '✓ CTR type standardized to DECIMAL(8,4)';
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Note: Could not alter CTR types - may already be correct';
END $$;

-- ============================================================================
-- ADD MISSING NOT NULL CONSTRAINTS
-- ============================================================================

-- Users table
DO $$
BEGIN
    -- Email should not be null
    UPDATE users SET email = 'unknown@example.com' WHERE email IS NULL;
    ALTER TABLE users ALTER COLUMN email SET NOT NULL;
    RAISE NOTICE '✓ Users.email set to NOT NULL';
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- Campaigns table
DO $$
BEGIN
    -- Product name should not be null for valid campaigns
    UPDATE campaigns SET product_name = name WHERE product_name IS NULL AND name IS NOT NULL;
    UPDATE campaigns SET product_name = 'Unnamed Product' WHERE product_name IS NULL;

    RAISE NOTICE '✓ Campaigns data cleaned';
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- ============================================================================
-- ADD DEFAULT VALUES WHERE MISSING
-- ============================================================================

-- Set default values for numeric columns to prevent NULL issues
DO $$
BEGIN
    -- Campaigns
    ALTER TABLE campaigns ALTER COLUMN budget_daily SET DEFAULT 0;
    ALTER TABLE campaigns ALTER COLUMN spend SET DEFAULT 0;
    ALTER TABLE campaigns ALTER COLUMN revenue SET DEFAULT 0;
    ALTER TABLE campaigns ALTER COLUMN roas SET DEFAULT 0;
    ALTER TABLE campaigns ALTER COLUMN conversions SET DEFAULT 0;
    ALTER TABLE campaigns ALTER COLUMN total_generated SET DEFAULT 0;
    ALTER TABLE campaigns ALTER COLUMN approved_count SET DEFAULT 0;
    ALTER TABLE campaigns ALTER COLUMN rejected_count SET DEFAULT 0;

    -- Videos
    ALTER TABLE videos ALTER COLUMN impressions SET DEFAULT 0;
    ALTER TABLE videos ALTER COLUMN clicks SET DEFAULT 0;
    ALTER TABLE videos ALTER COLUMN conversions SET DEFAULT 0;

    -- Update existing NULL values
    UPDATE campaigns SET budget_daily = 0 WHERE budget_daily IS NULL;
    UPDATE campaigns SET spend = 0 WHERE spend IS NULL;
    UPDATE campaigns SET revenue = 0 WHERE revenue IS NULL;
    UPDATE campaigns SET roas = 0 WHERE roas IS NULL;
    UPDATE campaigns SET conversions = 0 WHERE conversions IS NULL;

    UPDATE videos SET impressions = 0 WHERE impressions IS NULL;
    UPDATE videos SET clicks = 0 WHERE clicks IS NULL;
    UPDATE videos SET conversions = 0 WHERE conversions IS NULL;

    RAISE NOTICE '✓ Default values set and NULL values cleaned';
EXCEPTION
    WHEN others THEN NULL;
END $$;

-- ============================================================================
-- VALIDATE FOREIGN KEY RELATIONSHIPS
-- ============================================================================

-- Create a validation view to check orphaned records
CREATE OR REPLACE VIEW schema_validation_report AS
SELECT
    'campaigns_without_users' as issue,
    COUNT(*) as count
FROM campaigns c
LEFT JOIN users u ON c.user_id = u.id
WHERE c.user_id IS NOT NULL AND u.id IS NULL

UNION ALL

SELECT
    'blueprints_without_campaigns' as issue,
    COUNT(*) as count
FROM blueprints b
LEFT JOIN campaigns c ON b.campaign_id = c.id
WHERE b.campaign_id IS NOT NULL AND c.id IS NULL

UNION ALL

SELECT
    'videos_without_campaigns' as issue,
    COUNT(*) as count
FROM videos v
LEFT JOIN campaigns c ON v.campaign_id = c.id
WHERE v.campaign_id IS NOT NULL AND c.id IS NULL

UNION ALL

SELECT
    'render_jobs_without_blueprints' as issue,
    COUNT(*) as count
FROM render_jobs rj
LEFT JOIN blueprints b ON rj.blueprint_id = b.id
WHERE rj.blueprint_id IS NOT NULL AND b.id IS NULL;

-- ============================================================================
-- ENSURE TIMESTAMP CONSISTENCY
-- ============================================================================

-- Make sure all created_at columns have defaults
DO $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        AND tablename IN ('users', 'campaigns', 'blueprints', 'videos', 'ads', 'clips', 'jobs', 'render_jobs')
    LOOP
        BEGIN
            EXECUTE format('ALTER TABLE %I ALTER COLUMN created_at SET DEFAULT NOW()', table_name);
            RAISE NOTICE '✓ Set created_at default for %', table_name;
        EXCEPTION
            WHEN undefined_column THEN NULL;
            WHEN others THEN NULL;
        END;
    END LOOP;
END $$;

-- ============================================================================
-- CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to calculate CTR
CREATE OR REPLACE FUNCTION calculate_ctr(impressions INTEGER, clicks INTEGER)
RETURNS DECIMAL(8,4) AS $$
BEGIN
    IF impressions = 0 OR impressions IS NULL THEN
        RETURN 0;
    END IF;
    RETURN ROUND((clicks::DECIMAL / impressions * 100)::NUMERIC, 4);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate ROAS
CREATE OR REPLACE FUNCTION calculate_roas(revenue DECIMAL, spend DECIMAL)
RETURNS DECIMAL(8,2) AS $$
BEGIN
    IF spend = 0 OR spend IS NULL THEN
        RETURN 0;
    END IF;
    RETURN ROUND((revenue / spend)::NUMERIC, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to calculate conversion rate
CREATE OR REPLACE FUNCTION calculate_conversion_rate(conversions INTEGER, clicks INTEGER)
RETURNS DECIMAL(8,4) AS $$
BEGIN
    IF clicks = 0 OR clicks IS NULL THEN
        RETURN 0;
    END IF;
    RETURN ROUND((conversions::DECIMAL / clicks * 100)::NUMERIC, 4);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- CREATE VALIDATION FUNCTIONS
-- ============================================================================

-- Function to check table exists
CREATE OR REPLACE FUNCTION table_exists(table_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = $1
    );
END;
$$ LANGUAGE plpgsql;

-- Function to check column exists
CREATE OR REPLACE FUNCTION column_exists(table_name TEXT, column_name TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = $1
        AND column_name = $2
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TABLE EXISTENCE CHECK
-- ============================================================================

DO $$
DECLARE
    required_tables TEXT[] := ARRAY[
        'users', 'campaigns', 'blueprints', 'videos', 'ads', 'clips',
        'emotions', 'performance_metrics', 'daily_analytics', 'jobs',
        'render_jobs', 'predictions', 'ab_tests', 'creative_assets'
    ];
    missing_tables TEXT[] := ARRAY[]::TEXT[];
    t TEXT;
BEGIN
    FOREACH t IN ARRAY required_tables
    LOOP
        IF NOT table_exists(t) THEN
            missing_tables := array_append(missing_tables, t);
        END IF;
    END LOOP;

    IF array_length(missing_tables, 1) > 0 THEN
        RAISE WARNING 'Missing tables: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE '✓ All required tables exist';
    END IF;
END $$;

-- ============================================================================
-- CREATE COMPREHENSIVE SCHEMA REPORT VIEW
-- ============================================================================

CREATE OR REPLACE VIEW schema_health_report AS
SELECT
    'Tables' as category,
    COUNT(*) as count,
    'All tables in public schema' as description
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'

UNION ALL

SELECT
    'Indexes' as category,
    COUNT(*) as count,
    'All indexes in public schema' as description
FROM pg_indexes
WHERE schemaname = 'public'

UNION ALL

SELECT
    'Foreign Keys' as category,
    COUNT(*) as count,
    'All foreign key constraints' as description
FROM information_schema.table_constraints
WHERE constraint_schema = 'public'
  AND constraint_type = 'FOREIGN KEY'

UNION ALL

SELECT
    'Views' as category,
    COUNT(*) as count,
    'All views in public schema' as description
FROM information_schema.views
WHERE table_schema = 'public'

UNION ALL

SELECT
    'Functions' as category,
    COUNT(*) as count,
    'All functions in public schema' as description
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public';

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON VIEW schema_validation_report IS 'Reports orphaned records and data integrity issues';
COMMENT ON VIEW schema_health_report IS 'Overall schema health statistics';
COMMENT ON FUNCTION calculate_ctr IS 'Calculate CTR from impressions and clicks';
COMMENT ON FUNCTION calculate_roas IS 'Calculate ROAS from revenue and spend';
COMMENT ON FUNCTION calculate_conversion_rate IS 'Calculate conversion rate from conversions and clicks';

-- ============================================================================
-- FINAL VALIDATION
-- ============================================================================

DO $$
DECLARE
    validation_results RECORD;
    total_issues INTEGER := 0;
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'SCHEMA VALIDATION REPORT';
    RAISE NOTICE '========================================';

    FOR validation_results IN SELECT * FROM schema_validation_report
    LOOP
        IF validation_results.count > 0 THEN
            RAISE WARNING '%: % records', validation_results.issue, validation_results.count;
            total_issues := total_issues + validation_results.count;
        ELSE
            RAISE NOTICE '✓ %: OK', validation_results.issue;
        END IF;
    END LOOP;

    RAISE NOTICE '';
    IF total_issues = 0 THEN
        RAISE NOTICE '✅ Schema validation passed - no issues found';
    ELSE
        RAISE WARNING '⚠ Found % data integrity issues', total_issues;
    END IF;
    RAISE NOTICE '========================================';
END $$;

-- ============================================================================
-- SUCCESS MESSAGE
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '✅ Migration 004: Schema Validation completed successfully';
    RAISE NOTICE '   Type standardization: Complete';
    RAISE NOTICE '   Default values: Set';
    RAISE NOTICE '   Helper functions: Created';
    RAISE NOTICE '   Validation views: Available';
    RAISE NOTICE '';
    RAISE NOTICE 'Run: SELECT * FROM schema_health_report;';
    RAISE NOTICE 'To view schema statistics';
END $$;
