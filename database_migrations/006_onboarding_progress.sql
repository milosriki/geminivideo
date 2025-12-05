-- Onboarding Progress Table
-- Tracks elite marketer onboarding steps and completion status

CREATE TABLE IF NOT EXISTS onboarding_progress (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,

  -- Onboarding steps tracking
  step_welcome BOOLEAN DEFAULT FALSE,
  step_connect_meta BOOLEAN DEFAULT FALSE,
  step_connect_google BOOLEAN DEFAULT FALSE,
  step_configure BOOLEAN DEFAULT FALSE,
  step_first_campaign BOOLEAN DEFAULT FALSE,
  step_complete BOOLEAN DEFAULT FALSE,

  -- Current active step (1-6)
  current_step INTEGER DEFAULT 1,

  -- Completion status
  is_completed BOOLEAN DEFAULT FALSE,
  completed_at TIMESTAMPTZ,

  -- Meta connection data (encrypted in production)
  meta_business_id VARCHAR(255),
  meta_ad_account_id VARCHAR(255),
  meta_connected_at TIMESTAMPTZ,

  -- Google connection data
  google_customer_id VARCHAR(255),
  google_connected_at TIMESTAMPTZ,

  -- Configuration preferences
  default_currency VARCHAR(10) DEFAULT 'USD',
  default_timezone VARCHAR(100) DEFAULT 'UTC',
  daily_budget_limit DECIMAL(10, 2),

  -- Notification preferences
  email_notifications BOOLEAN DEFAULT TRUE,
  slack_notifications BOOLEAN DEFAULT FALSE,
  push_notifications BOOLEAN DEFAULT TRUE,

  -- First campaign data
  first_campaign_id UUID REFERENCES campaigns(id),
  first_campaign_created_at TIMESTAMPTZ,

  -- Skipped steps (for analytics)
  skipped_steps JSONB DEFAULT '[]',

  -- Metadata
  started_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),

  -- Ensure one onboarding record per user
  UNIQUE(user_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_onboarding_user ON onboarding_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_step ON onboarding_progress(current_step);
CREATE INDEX IF NOT EXISTS idx_onboarding_completed ON onboarding_progress(is_completed);

-- Auto-update timestamp trigger
CREATE OR REPLACE FUNCTION update_onboarding_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();

  -- Auto-complete when all steps are done
  IF NEW.step_welcome AND
     NEW.step_connect_meta AND
     NEW.step_connect_google AND
     NEW.step_configure AND
     NEW.step_first_campaign AND
     NOT NEW.is_completed THEN
    NEW.is_completed = TRUE;
    NEW.step_complete = TRUE;
    NEW.completed_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_onboarding_timestamp
  BEFORE UPDATE ON onboarding_progress
  FOR EACH ROW
  EXECUTE FUNCTION update_onboarding_timestamp();

-- Comments for documentation
COMMENT ON TABLE onboarding_progress IS 'Tracks elite marketer onboarding flow for $20k/day ad spenders';
COMMENT ON COLUMN onboarding_progress.current_step IS '1=Welcome, 2=Meta, 3=Google, 4=Configure, 5=First Campaign, 6=Complete';
COMMENT ON COLUMN onboarding_progress.skipped_steps IS 'Array of skipped step names for analytics';
