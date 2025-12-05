-- Migration: Add reports table for Agent 18
-- Campaign Performance Report Generator

-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_type VARCHAR(50) NOT NULL,
    format VARCHAR(10) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    campaign_ids TEXT[],
    ad_ids TEXT[],
    company_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'generated',
    file_size_bytes BIGINT,
    generated_by VARCHAR(100),
    metadata JSONB
);

-- Create index on created_at for efficient listing
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);

-- Create index on report_type for filtering
CREATE INDEX IF NOT EXISTS idx_reports_type ON reports(report_type);

-- Create index on status
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);

-- Add comments
COMMENT ON TABLE reports IS 'Generated campaign performance reports';
COMMENT ON COLUMN reports.report_id IS 'Unique report identifier';
COMMENT ON COLUMN reports.report_type IS 'Type of report (campaign_performance, ad_creative_analysis, etc.)';
COMMENT ON COLUMN reports.format IS 'Report format (pdf or excel)';
COMMENT ON COLUMN reports.start_date IS 'Report date range start';
COMMENT ON COLUMN reports.end_date IS 'Report date range end';
COMMENT ON COLUMN reports.campaign_ids IS 'Array of campaign IDs included in report';
COMMENT ON COLUMN reports.ad_ids IS 'Array of ad IDs included in report';
COMMENT ON COLUMN reports.company_name IS 'Company name for report branding';
COMMENT ON COLUMN reports.status IS 'Report generation status';
COMMENT ON COLUMN reports.metadata IS 'Additional report metadata (filters, summary, etc.)';
