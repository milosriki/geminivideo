-- Jobs table indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Analytics indexes
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(date);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_date ON performance_metrics(date);

-- Campaigns indexes
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_created_at ON campaigns(created_at);

-- Videos indexes
CREATE INDEX IF NOT EXISTS idx_videos_blueprint_id ON videos(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_videos_render_job_id ON videos(render_job_id);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at);

-- Render jobs indexes
CREATE INDEX IF NOT EXISTS idx_render_jobs_blueprint_id ON render_jobs(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_campaign_id ON render_jobs(campaign_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON render_jobs(status);

-- Feedback indexes
CREATE INDEX IF NOT EXISTS idx_feedback_events_created_at ON feedback_events(created_at);

-- API costs indexes
CREATE INDEX IF NOT EXISTS idx_api_costs_created_at ON api_costs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_costs_model_name ON api_costs(model_name);

-- Credits indexes
CREATE INDEX IF NOT EXISTS idx_ai_credits_user_id ON ai_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_credit_usage_user_id ON ai_credit_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_credit_usage_created_at ON ai_credit_usage(created_at);
