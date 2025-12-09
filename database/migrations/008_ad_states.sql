-- Agent 2: AdState persistence table
CREATE TABLE IF NOT EXISTS ad_states (
    ad_id VARCHAR PRIMARY KEY,
    account_id VARCHAR,
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    spend DECIMAL(10, 2) DEFAULT 0.0,
    pipeline_value DECIMAL(10, 2) DEFAULT 0.0,
    cash_revenue DECIMAL(10, 2) DEFAULT 0.0,
    age_hours DECIMAL(10, 2) DEFAULT 0.0,
    status VARCHAR DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ad_states_account_id ON ad_states(account_id);
CREATE INDEX IF NOT EXISTS idx_ad_states_status ON ad_states(status);
CREATE INDEX IF NOT EXISTS idx_ad_states_last_updated ON ad_states(last_updated);

