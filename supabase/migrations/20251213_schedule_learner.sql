-- Migration to schedule the agent-background-learner function
-- This requires the pg_cron extension to be enabled

-- Enable pg_cron if not already enabled
create extension if not exists pg_cron;

-- Schedule the function to run every hour
-- Note: You need to replace the URL with your actual project URL if it differs
-- The URL is constructed dynamically using the project ID if possible, but for cron we often need a static URL or a net request

-- We use a safe block to avoid errors if the job already exists
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'agent-learning-hourly') THEN
    PERFORM cron.schedule(
      'agent-learning-hourly',
      '0 * * * *', -- Every hour
      $$
      SELECT net.http_post(
        url := 'https://akhirugwpozlxfvtqmvj.supabase.co/functions/v1/agent-background-learner',
        headers := '{"Authorization": "Bearer ' || current_setting('supabase.anon_key') || '"}'::jsonb
      );
      $$
    );
  END IF;
END
$$;
