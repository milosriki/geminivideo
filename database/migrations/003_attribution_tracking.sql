-- Migration 003: Attribution Tracking Tables
-- Purpose: 3-layer attribution recovery (URL params, fingerprint, probabilistic)
-- Created: 2025-12-07
-- Dependencies: None

-- Click Tracking Table
-- Stores every ad click with device fingerprint for iOS 18 attribution recovery
CREATE TABLE IF NOT EXISTS click_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Click identifiers
    click_id VARCHAR(255) NOT NULL UNIQUE,  -- Our custom click ID
    fbclid VARCHAR(255),                     -- Facebook click ID (if available)
    gclid VARCHAR(255),                      -- Google click ID (if available)

    -- Ad context
    tenant_id VARCHAR(255) NOT NULL,
    campaign_id VARCHAR(255) NOT NULL,
    adset_id VARCHAR(255),
    ad_id VARCHAR(255) NOT NULL,
    creative_id VARCHAR(255),

    -- Device fingerprint (for iOS 18 attribution recovery)
    fingerprint_hash VARCHAR(64),            -- SHA-256 hash of device signature
    fingerprint_components JSONB,            -- Raw components used for fingerprinting

    -- Network data
    ip_address INET,
    ip_country VARCHAR(2),
    ip_city VARCHAR(100),

    -- Device data
    user_agent TEXT,
    device_type VARCHAR(50),                 -- 'mobile', 'desktop', 'tablet'
    os VARCHAR(50),                          -- 'iOS', 'Android', 'Windows', etc.
    os_version VARCHAR(50),
    browser VARCHAR(50),
    browser_version VARCHAR(50),

    -- Screen/viewport
    screen_width INTEGER,
    screen_height INTEGER,
    viewport_width INTEGER,
    viewport_height INTEGER,

    -- Timing
    timezone VARCHAR(100),
    timezone_offset INTEGER,                 -- Minutes offset from UTC

    -- Landing page
    landing_page_url TEXT,
    referrer_url TEXT,
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    utm_content VARCHAR(255),
    utm_term VARCHAR(255),

    -- Metadata
    click_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,                  -- Attribution window expiration (7 days default)
    is_valid BOOLEAN DEFAULT true,           -- Flagged as invalid if suspicious

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Conversion Tracking Table
-- Stores conversions with 3-layer attribution matching
CREATE TABLE IF NOT EXISTS conversion_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Conversion identifiers
    conversion_id VARCHAR(255) NOT NULL UNIQUE,  -- Our custom conversion ID
    external_id VARCHAR(255),                     -- External system ID (HubSpot, Shopify, etc.)

    -- Tenant context
    tenant_id VARCHAR(255) NOT NULL,

    -- Conversion data
    conversion_type VARCHAR(100) NOT NULL,   -- 'lead', 'appointment', 'purchase', 'signup', etc.
    conversion_value NUMERIC(10, 2),         -- Actual or synthetic revenue
    is_synthetic BOOLEAN DEFAULT false,       -- True if using synthetic revenue

    -- CRM data (if available)
    crm_deal_id VARCHAR(255),
    crm_contact_id VARCHAR(255),
    crm_stage VARCHAR(100),

    -- Attribution (3-layer system)
    attributed_click_id UUID REFERENCES click_tracking(id),
    attribution_method VARCHAR(50),           -- 'url_param', 'fingerprint', 'probabilistic', 'unattributed'
    attribution_confidence NUMERIC(5, 4),     -- 0-1 confidence score
    attribution_window_hours INTEGER,         -- Hours between click and conversion

    -- Fingerprint matching (for Layer 2)
    conversion_fingerprint_hash VARCHAR(64),
    fingerprint_match_score NUMERIC(5, 4),   -- Similarity score if fingerprint matched

    -- Probabilistic matching (for Layer 3)
    probabilistic_candidates JSONB,           -- Array of candidate clicks with scores

    -- Device data (captured at conversion time)
    ip_address INET,
    user_agent TEXT,
    device_type VARCHAR(50),

    -- Timing
    conversion_timestamp TIMESTAMPTZ NOT NULL,
    attributed_at TIMESTAMPTZ,                -- When attribution was assigned

    -- Metadata
    raw_data JSONB,                           -- Original webhook/API data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Attribution Performance Log
-- Tracks attribution attempts for monitoring recovery rates
CREATE TABLE IF NOT EXISTS attribution_performance_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL,

    -- Attempt tracking
    conversion_id VARCHAR(255) NOT NULL,
    attempt_number INTEGER NOT NULL DEFAULT 1,

    -- Layer results
    layer_1_result VARCHAR(50),  -- 'success', 'no_param', 'expired', 'invalid'
    layer_2_result VARCHAR(50),  -- 'success', 'no_match', 'low_confidence'
    layer_3_result VARCHAR(50),  -- 'success', 'no_candidates', 'low_probability'

    -- Final result
    final_method VARCHAR(50),
    final_confidence NUMERIC(5, 4),
    success BOOLEAN NOT NULL,

    -- Timing
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for click_tracking
CREATE INDEX IF NOT EXISTS idx_click_tracking_click_id ON click_tracking(click_id);
CREATE INDEX IF NOT EXISTS idx_click_tracking_fbclid ON click_tracking(fbclid) WHERE fbclid IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_click_tracking_tenant_id ON click_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_click_tracking_ad_id ON click_tracking(ad_id);
CREATE INDEX IF NOT EXISTS idx_click_tracking_fingerprint ON click_tracking(fingerprint_hash) WHERE fingerprint_hash IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_click_tracking_timestamp ON click_tracking(click_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_click_tracking_expires_at ON click_tracking(expires_at) WHERE is_valid = true;

-- Composite index for fingerprint matching (Layer 2)
CREATE INDEX IF NOT EXISTS idx_click_tracking_fingerprint_match
ON click_tracking(fingerprint_hash, click_timestamp DESC)
WHERE fingerprint_hash IS NOT NULL AND is_valid = true;

-- Composite index for probabilistic matching (Layer 3)
CREATE INDEX IF NOT EXISTS idx_click_tracking_probabilistic
ON click_tracking(ip_address, device_type, click_timestamp DESC)
WHERE is_valid = true;

-- Indexes for conversion_tracking
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_conversion_id ON conversion_tracking(conversion_id);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_external_id ON conversion_tracking(external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_tenant_id ON conversion_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_click_id ON conversion_tracking(attributed_click_id);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_method ON conversion_tracking(attribution_method);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_timestamp ON conversion_tracking(conversion_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_conversion_tracking_crm_deal ON conversion_tracking(crm_deal_id) WHERE crm_deal_id IS NOT NULL;

-- Indexes for attribution_performance_log
CREATE INDEX IF NOT EXISTS idx_attribution_perf_tenant_id ON attribution_performance_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_attribution_perf_success ON attribution_performance_log(success);
CREATE INDEX IF NOT EXISTS idx_attribution_perf_created_at ON attribution_performance_log(created_at DESC);

-- Updated_at triggers
CREATE TRIGGER trigger_conversion_tracking_updated_at
BEFORE UPDATE ON conversion_tracking
FOR EACH ROW
EXECUTE FUNCTION update_ad_change_history_updated_at();

-- Set expires_at automatically (7-day attribution window)
CREATE OR REPLACE FUNCTION set_click_expires_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expires_at IS NULL THEN
        NEW.expires_at := NEW.click_timestamp + INTERVAL '7 days';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_click_tracking_expires_at
BEFORE INSERT ON click_tracking
FOR EACH ROW
EXECUTE FUNCTION set_click_expires_at();

-- View: Attribution Recovery Rate (monitoring)
CREATE OR REPLACE VIEW v_attribution_recovery_rate AS
WITH daily_stats AS (
    SELECT
        DATE(created_at) AS date,
        tenant_id,
        COUNT(*) AS total_conversions,
        COUNT(*) FILTER (WHERE success = true) AS attributed_conversions,
        COUNT(*) FILTER (WHERE final_method = 'url_param') AS layer_1_success,
        COUNT(*) FILTER (WHERE final_method = 'fingerprint') AS layer_2_success,
        COUNT(*) FILTER (WHERE final_method = 'probabilistic') AS layer_3_success,
        AVG(final_confidence) FILTER (WHERE success = true) AS avg_confidence,
        AVG(processing_time_ms) AS avg_processing_ms
    FROM attribution_performance_log
    GROUP BY DATE(created_at), tenant_id
)
SELECT
    date,
    tenant_id,
    total_conversions,
    attributed_conversions,
    ROUND(100.0 * attributed_conversions / NULLIF(total_conversions, 0), 2) AS recovery_rate_pct,
    layer_1_success,
    layer_2_success,
    layer_3_success,
    ROUND(avg_confidence::NUMERIC, 4) AS avg_confidence,
    avg_processing_ms
FROM daily_stats
ORDER BY date DESC, tenant_id;

-- View: Active Clicks (within attribution window)
CREATE OR REPLACE VIEW v_active_clicks AS
SELECT
    id,
    click_id,
    fbclid,
    tenant_id,
    ad_id,
    fingerprint_hash,
    ip_address,
    device_type,
    click_timestamp,
    expires_at,
    EXTRACT(EPOCH FROM (expires_at - NOW())) / 3600 AS hours_until_expiration
FROM click_tracking
WHERE
    is_valid = true
    AND expires_at > NOW()
ORDER BY click_timestamp DESC;

-- View: Conversion Attribution Summary
CREATE OR REPLACE VIEW v_conversion_attribution_summary AS
SELECT
    ct.tenant_id,
    ct.conversion_type,
    ct.attribution_method,
    COUNT(*) AS conversion_count,
    SUM(ct.conversion_value) AS total_value,
    AVG(ct.attribution_confidence) AS avg_confidence,
    AVG(ct.attribution_window_hours) AS avg_attribution_hours,
    MIN(ct.conversion_timestamp) AS first_conversion,
    MAX(ct.conversion_timestamp) AS last_conversion
FROM conversion_tracking ct
WHERE ct.conversion_timestamp > NOW() - INTERVAL '30 days'
GROUP BY ct.tenant_id, ct.conversion_type, ct.attribution_method
ORDER BY ct.tenant_id, conversion_count DESC;

-- View: Unattributed Conversions (for investigation)
CREATE OR REPLACE VIEW v_unattributed_conversions AS
SELECT
    id,
    conversion_id,
    external_id,
    tenant_id,
    conversion_type,
    conversion_value,
    conversion_fingerprint_hash,
    ip_address,
    user_agent,
    conversion_timestamp,
    raw_data
FROM conversion_tracking
WHERE
    attribution_method = 'unattributed'
    OR attributed_click_id IS NULL
ORDER BY conversion_timestamp DESC;

-- Migration complete
COMMENT ON TABLE click_tracking IS '3-layer attribution: Tracks ad clicks with device fingerprints for iOS 18 recovery';
COMMENT ON TABLE conversion_tracking IS '3-layer attribution: Stores conversions with confidence-scored attribution';
COMMENT ON TABLE attribution_performance_log IS 'Attribution attempt tracking for monitoring recovery rates';
COMMENT ON VIEW v_attribution_recovery_rate IS 'Daily attribution recovery rate by method (Layer 1/2/3)';
COMMENT ON VIEW v_active_clicks IS 'Clicks within attribution window (7 days)';
COMMENT ON VIEW v_conversion_attribution_summary IS 'Conversion attribution summary by method';
COMMENT ON VIEW v_unattributed_conversions IS 'Conversions that failed all 3 attribution layers';
