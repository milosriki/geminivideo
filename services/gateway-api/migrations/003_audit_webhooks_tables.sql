-- Audit Log and Webhooks Tables Migration
-- Supports comprehensive audit logging and webhook management

-- Create audit_log table
CREATE TABLE IF NOT EXISTS audit_log (
  id SERIAL PRIMARY KEY,
  action VARCHAR(50) NOT NULL,
  resource VARCHAR(100) NOT NULL,
  resource_id UUID,
  user_id UUID,
  ip_address VARCHAR(45),
  user_agent TEXT,
  request_body JSONB,
  response_status INTEGER,
  duration_ms INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create webhooks table
CREATE TABLE IF NOT EXISTS webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url TEXT NOT NULL,
  events JSONB NOT NULL DEFAULT '[]',
  secret VARCHAR(255),
  is_active BOOLEAN DEFAULT true,
  last_triggered_at TIMESTAMP WITH TIME ZONE,
  failure_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create webhook_deliveries table for tracking
CREATE TABLE IF NOT EXISTS webhook_deliveries (
  id SERIAL PRIMARY KEY,
  webhook_id UUID REFERENCES webhooks(id),
  event_type VARCHAR(100) NOT NULL,
  payload JSONB NOT NULL,
  response_status INTEGER,
  response_body TEXT,
  success BOOLEAN,
  attempts INTEGER DEFAULT 1,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create report_shares table (needed for report sharing)
CREATE TABLE IF NOT EXISTS report_shares (
  id SERIAL PRIMARY KEY,
  report_id UUID NOT NULL,
  shared_with_email VARCHAR(255) NOT NULL,
  message TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_audit_log_resource ON audit_log(resource, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhooks_active ON webhooks(is_active) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook ON webhook_deliveries(webhook_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_shares_report ON report_shares(report_id);

-- Create function to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for webhooks updated_at
DROP TRIGGER IF EXISTS webhooks_updated_at ON webhooks;
CREATE TRIGGER webhooks_updated_at
  BEFORE UPDATE ON webhooks
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Partition audit_log by month for performance (optional, for high-volume)
-- Note: Requires PostgreSQL 10+
-- CREATE TABLE audit_log_y2024m01 PARTITION OF audit_log FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Grant permissions
GRANT SELECT, INSERT ON audit_log TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON webhooks TO app_user;
GRANT SELECT, INSERT ON webhook_deliveries TO app_user;
GRANT SELECT, INSERT ON report_shares TO app_user;
GRANT USAGE ON SEQUENCE audit_log_id_seq TO app_user;
GRANT USAGE ON SEQUENCE webhook_deliveries_id_seq TO app_user;
GRANT USAGE ON SEQUENCE report_shares_id_seq TO app_user;

-- Add comments
COMMENT ON TABLE audit_log IS 'Audit trail for all API operations';
COMMENT ON TABLE webhooks IS 'Webhook configurations for event notifications';
COMMENT ON TABLE webhook_deliveries IS 'Delivery attempts and results for webhooks';
COMMENT ON TABLE report_shares IS 'Report sharing records';
