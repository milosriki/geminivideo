-- Batch Jobs Table Migration
-- Supports batch processing of campaigns, ads, and ML operations

-- Create batch_jobs table
CREATE TABLE IF NOT EXISTS batch_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  data JSONB NOT NULL DEFAULT '{}',
  priority INTEGER DEFAULT 0,
  attempts INTEGER DEFAULT 0,
  max_attempts INTEGER DEFAULT 3,
  error TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  started_at TIMESTAMP WITH TIME ZONE,
  completed_at TIMESTAMP WITH TIME ZONE,
  created_by UUID,

  CONSTRAINT valid_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')),
  CONSTRAINT valid_type CHECK (type IN ('campaign_launch', 'ad_approval', 'performance_update', 'prediction_batch', 'report_generation', 'winner_indexing'))
);

-- Create execution_failures table for circuit breaker monitoring
CREATE TABLE IF NOT EXISTS execution_failures (
  id SERIAL PRIMARY KEY,
  operation_name VARCHAR(100) NOT NULL,
  error_message TEXT NOT NULL,
  circuit_state VARCHAR(20) NOT NULL,
  stack_trace TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_batch_jobs_status ON batch_jobs(status);
CREATE INDEX IF NOT EXISTS idx_batch_jobs_type ON batch_jobs(type);
CREATE INDEX IF NOT EXISTS idx_batch_jobs_priority ON batch_jobs(priority DESC, created_at ASC) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_batch_jobs_created ON batch_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_failures_operation ON execution_failures(operation_name);
CREATE INDEX IF NOT EXISTS idx_execution_failures_created ON execution_failures(created_at DESC);

-- Create function to automatically update completed_at
CREATE OR REPLACE FUNCTION update_batch_job_completed()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status IN ('completed', 'failed', 'cancelled') AND OLD.status NOT IN ('completed', 'failed', 'cancelled') THEN
    NEW.completed_at = NOW();
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for auto-updating completed_at
DROP TRIGGER IF EXISTS batch_job_completed_trigger ON batch_jobs;
CREATE TRIGGER batch_job_completed_trigger
  BEFORE UPDATE ON batch_jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_batch_job_completed();

-- Create function to retry failed jobs
CREATE OR REPLACE FUNCTION retry_failed_batch_jobs()
RETURNS INTEGER AS $$
DECLARE
  retried_count INTEGER;
BEGIN
  UPDATE batch_jobs
  SET status = 'pending',
      attempts = attempts + 1,
      error = NULL
  WHERE status = 'failed'
    AND attempts < max_attempts
    AND created_at > NOW() - INTERVAL '24 hours';

  GET DIAGNOSTICS retried_count = ROW_COUNT;
  RETURN retried_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to clean up old jobs
CREATE OR REPLACE FUNCTION cleanup_old_batch_jobs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM batch_jobs
  WHERE status IN ('completed', 'cancelled')
    AND completed_at < NOW() - (days_to_keep || ' days')::INTERVAL;

  GET DIAGNOSTICS deleted_count = ROW_COUNT;

  -- Also clean up old execution failures
  DELETE FROM execution_failures
  WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL;

  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON batch_jobs TO app_user;
GRANT SELECT, INSERT ON execution_failures TO app_user;
GRANT USAGE ON SEQUENCE execution_failures_id_seq TO app_user;

-- Insert some initial job types documentation
COMMENT ON TABLE batch_jobs IS 'Queue for batch processing operations including campaign launches, ad approvals, and ML predictions';
COMMENT ON TABLE execution_failures IS 'Log of operation failures for circuit breaker monitoring and debugging';
