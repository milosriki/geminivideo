-- Winner Detection Trigger Migration
-- Automatically detects winning ads and triggers RAG indexing

-- Create function to detect winners based on CTR and ROAS thresholds
CREATE OR REPLACE FUNCTION detect_winner()
RETURNS TRIGGER AS $$
DECLARE
  min_ctr NUMERIC := 0.03;
  min_roas NUMERIC := 3.0;
  min_impressions INTEGER := 1000;
BEGIN
  -- Check if ad meets winner criteria
  IF NEW.ctr >= min_ctr AND NEW.roas >= min_roas AND NEW.impressions >= min_impressions THEN
    -- Notify for async RAG indexing
    PERFORM pg_notify('winner_detected', json_build_object(
      'ad_id', NEW.ad_id,
      'ctr', NEW.ctr,
      'roas', NEW.roas,
      'impressions', NEW.impressions,
      'detected_at', NOW()
    )::text);

    -- Log to audit table
    INSERT INTO winner_audit_log (ad_id, ctr, roas, impressions, detected_at)
    VALUES (NEW.ad_id, NEW.ctr, NEW.roas, NEW.impressions, NOW())
    ON CONFLICT (ad_id) DO UPDATE SET
      ctr = EXCLUDED.ctr,
      roas = EXCLUDED.roas,
      impressions = EXCLUDED.impressions,
      detected_at = NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create winner audit log table if not exists
CREATE TABLE IF NOT EXISTS winner_audit_log (
  id SERIAL PRIMARY KEY,
  ad_id UUID UNIQUE NOT NULL,
  ctr NUMERIC NOT NULL,
  roas NUMERIC NOT NULL,
  impressions INTEGER NOT NULL,
  detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  indexed_at TIMESTAMP WITH TIME ZONE
);

-- Create or replace trigger on performance_metrics table
DROP TRIGGER IF EXISTS winner_detection_trigger ON performance_metrics;
CREATE TRIGGER winner_detection_trigger
  AFTER INSERT OR UPDATE ON performance_metrics
  FOR EACH ROW
  WHEN (NEW.ctr IS NOT NULL AND NEW.roas IS NOT NULL)
  EXECUTE FUNCTION detect_winner();

-- Create index for fast winner lookups
CREATE INDEX IF NOT EXISTS idx_winner_audit_detected ON winner_audit_log(detected_at DESC);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_winners ON performance_metrics(ad_id) WHERE ctr >= 0.03 AND roas >= 3.0;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON winner_audit_log TO app_user;
GRANT USAGE ON SEQUENCE winner_audit_log_id_seq TO app_user;
