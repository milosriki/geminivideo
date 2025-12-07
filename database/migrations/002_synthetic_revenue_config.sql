-- Migration 002: Synthetic Revenue Configuration
-- Purpose: Configure pipeline stage values per tenant for service business optimization
-- Created: 2025-12-07
-- Dependencies: None

-- Synthetic Revenue Configuration Table
-- Maps CRM pipeline stages to synthetic revenue values
-- Enables optimization before deals close (critical for 5-7 day sales cycles)
CREATE TABLE IF NOT EXISTS synthetic_revenue_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(255) NOT NULL UNIQUE,

    -- Stage value configuration (JSONB)
    -- Format: {"stage_name": {"value": 2250.00, "confidence": 0.60}, ...}
    stage_values JSONB NOT NULL,

    -- Business configuration
    avg_deal_value NUMERIC(10, 2),     -- Average closed deal value
    sales_cycle_days INTEGER,           -- Average sales cycle length
    win_rate NUMERIC(5, 4),            -- Historical win rate (0-1)

    -- Active/inactive
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    notes TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_synthetic_revenue_config_tenant_id ON synthetic_revenue_config(tenant_id);
CREATE INDEX IF NOT EXISTS idx_synthetic_revenue_config_is_active ON synthetic_revenue_config(is_active);

-- Updated_at trigger
CREATE TRIGGER trigger_synthetic_revenue_config_updated_at
BEFORE UPDATE ON synthetic_revenue_config
FOR EACH ROW
EXECUTE FUNCTION update_ad_change_history_updated_at();

-- Validation function to ensure stage_values JSONB is properly formatted
CREATE OR REPLACE FUNCTION validate_stage_values(stage_values JSONB)
RETURNS BOOLEAN AS $$
DECLARE
    stage_key TEXT;
    stage_data JSONB;
BEGIN
    -- Check each stage in the JSONB
    FOR stage_key, stage_data IN SELECT * FROM jsonb_each(stage_values)
    LOOP
        -- Each stage must have 'value' and 'confidence'
        IF NOT (stage_data ? 'value' AND stage_data ? 'confidence') THEN
            RAISE EXCEPTION 'Stage % missing required fields (value, confidence)', stage_key;
        END IF;

        -- Confidence must be between 0 and 1
        IF (stage_data->>'confidence')::NUMERIC NOT BETWEEN 0 AND 1 THEN
            RAISE EXCEPTION 'Stage % confidence must be between 0 and 1', stage_key;
        END IF;

        -- Value must be positive
        IF (stage_data->>'value')::NUMERIC < 0 THEN
            RAISE EXCEPTION 'Stage % value must be positive', stage_key;
        END IF;
    END LOOP;

    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Add constraint to validate stage_values format
ALTER TABLE synthetic_revenue_config
ADD CONSTRAINT check_stage_values_format
CHECK (validate_stage_values(stage_values));

-- Insert default configuration for PTD Fitness
-- PTD Fitness: Personal training service with 5-7 day sales cycle
-- Average deal value: $15,000 (12-month training package)
-- Sales stages: lead → appointment_scheduled → show_up → closed_won
INSERT INTO synthetic_revenue_config (
    tenant_id,
    stage_values,
    avg_deal_value,
    sales_cycle_days,
    win_rate,
    created_by,
    notes
) VALUES (
    'ptd_fitness',
    '{
        "lead": {
            "value": 0,
            "confidence": 0.10,
            "description": "Initial lead captured (form submission, call)"
        },
        "appointment_scheduled": {
            "value": 2250,
            "confidence": 0.60,
            "description": "Appointment booked (15% show rate * 60% close rate * $15k = $2,250)"
        },
        "show_up": {
            "value": 9000,
            "confidence": 0.85,
            "description": "Showed up to appointment (60% close rate * $15k = $9,000)"
        },
        "closed_won": {
            "value": 15000,
            "confidence": 1.00,
            "description": "Deal closed (full value)"
        },
        "closed_lost": {
            "value": 0,
            "confidence": 1.00,
            "description": "Deal lost"
        }
    }'::JSONB,
    15000.00,
    6,
    0.60,
    'system',
    'PTD Fitness default configuration based on historical data. Appointment value calculated as: 15% show rate * 60% close rate * $15k avg deal = $2,250'
) ON CONFLICT (tenant_id) DO NOTHING;

-- Insert template for e-commerce businesses (for comparison)
INSERT INTO synthetic_revenue_config (
    tenant_id,
    stage_values,
    avg_deal_value,
    sales_cycle_days,
    win_rate,
    created_by,
    notes
) VALUES (
    'template_ecommerce',
    '{
        "add_to_cart": {
            "value": 15,
            "confidence": 0.25,
            "description": "Product added to cart (25% checkout rate * $60 AOV)"
        },
        "initiated_checkout": {
            "value": 45,
            "confidence": 0.75,
            "description": "Checkout initiated (75% completion rate * $60 AOV)"
        },
        "purchase": {
            "value": 60,
            "confidence": 1.00,
            "description": "Purchase completed"
        }
    }'::JSONB,
    60.00,
    0,
    0.75,
    'system',
    'E-commerce template with immediate conversion (no sales cycle)'
) ON CONFLICT (tenant_id) DO NOTHING;

-- Insert template for B2B SaaS (for comparison)
INSERT INTO synthetic_revenue_config (
    tenant_id,
    stage_values,
    avg_deal_value,
    sales_cycle_days,
    win_rate,
    created_by,
    notes
) VALUES (
    'template_b2b_saas',
    '{
        "marketing_qualified_lead": {
            "value": 100,
            "confidence": 0.05,
            "description": "MQL (5% SQL conversion * 20% close rate * $10k ACV)"
        },
        "sales_qualified_lead": {
            "value": 2000,
            "confidence": 0.20,
            "description": "SQL (20% close rate * $10k ACV)"
        },
        "demo_scheduled": {
            "value": 3500,
            "confidence": 0.35,
            "description": "Demo scheduled (35% close rate * $10k ACV)"
        },
        "proposal_sent": {
            "value": 6000,
            "confidence": 0.60,
            "description": "Proposal sent (60% close rate * $10k ACV)"
        },
        "closed_won": {
            "value": 10000,
            "confidence": 1.00,
            "description": "Deal closed"
        }
    }'::JSONB,
    10000.00,
    45,
    0.20,
    'system',
    'B2B SaaS template with 45-day sales cycle'
) ON CONFLICT (tenant_id) DO NOTHING;

-- View: Stage Value Lookup (helper for quick lookups)
CREATE OR REPLACE VIEW v_stage_values AS
SELECT
    src.tenant_id,
    src.is_active,
    stage_data.key AS stage_name,
    (stage_data.value->>'value')::NUMERIC AS stage_value,
    (stage_data.value->>'confidence')::NUMERIC AS stage_confidence,
    stage_data.value->>'description' AS stage_description,
    src.avg_deal_value,
    src.sales_cycle_days,
    src.win_rate
FROM
    synthetic_revenue_config src,
    LATERAL jsonb_each(src.stage_values) AS stage_data
WHERE
    src.is_active = true
ORDER BY
    src.tenant_id,
    (stage_data.value->>'value')::NUMERIC ASC;

-- View: Tenant Summary (for monitoring)
CREATE OR REPLACE VIEW v_synthetic_revenue_summary AS
SELECT
    tenant_id,
    jsonb_object_keys(stage_values) AS stage_count,
    avg_deal_value,
    sales_cycle_days,
    win_rate,
    is_active,
    created_at,
    updated_at
FROM synthetic_revenue_config
ORDER BY tenant_id;

-- Migration complete
COMMENT ON TABLE synthetic_revenue_config IS 'Pipeline stage value configuration for synthetic revenue calculation';
COMMENT ON COLUMN synthetic_revenue_config.stage_values IS 'JSONB mapping of stage names to {value, confidence} pairs';
COMMENT ON VIEW v_stage_values IS 'Flattened view of all stage values for easy lookup';
COMMENT ON VIEW v_synthetic_revenue_summary IS 'Summary of synthetic revenue configurations per tenant';
