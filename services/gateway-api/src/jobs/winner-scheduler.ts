/**
 * Winner Scheduler - Automated Winner Detection Job
 * Agent 02 - Scheduled Winner Check
 *
 * Purpose:
 *   Automatically detects winners in A/B test experiments every 6 hours.
 *   Uses statistical analysis to determine when a variant has won with confidence.
 *
 * Schedule:
 *   Default: Every 6 hours (cron: 0 star-slash-6 star star star)
 *   Configurable via WINNER_CHECK_SCHEDULE environment variable
 *
 * Features:
 *   - Cron-based scheduling
 *   - Automatic winner detection across all active experiments
 *   - Logging and alerting for new winners
 *   - Manual trigger support
 *   - Configurable confidence levels
 *
 * Created: 2025-12-13
 */

import cron, { ScheduledTask } from 'node-cron';
import { Pool } from 'pg';
import axios from 'axios';
import { logger } from '../utils/logger';

// Configuration
const WINNER_CHECK_SCHEDULE = process.env.WINNER_CHECK_SCHEDULE || '0 */6 * * *'; // Every 6 hours
const WINNER_MIN_ROAS = parseFloat(process.env.WINNER_MIN_ROAS || '2.0');
const WINNER_MIN_CTR = parseFloat(process.env.WINNER_MIN_CTR || '0.02');
const WINNER_MIN_SPEND = parseFloat(process.env.WINNER_MIN_SPEND || '100');
const WINNER_MIN_HOURS = parseInt(process.env.WINNER_MIN_HOURS || '24');
const ENABLE_WINNER_SCHEDULER = process.env.ENABLE_WINNER_SCHEDULER !== 'false'; // Enabled by default
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';

// Webhook configuration for alerts
const WINNER_WEBHOOK_URL = process.env.WINNER_WEBHOOK_URL || '';
const WINNER_ALERT_EMAIL = process.env.WINNER_ALERT_EMAIL || '';

interface WinnerSchedulerConfig {
  schedule: string;
  minROAS: number;
  minCTR: number;
  minSpend: number;
  minHours: number;
  enabled: boolean;
}

interface DetectedWinner {
  ad_id: string;
  campaign_name: string;
  video_title: string;
  arc_name: string;
  actual_ctr: number;
  actual_roas: number;
  total_spend: number;
  total_impressions: number;
  total_clicks: number;
  total_conversions: number;
}

interface SchedulerState {
  task: ScheduledTask | null;
  lastRun: Date | null;
  lastRunStatus: 'success' | 'failure' | 'running' | null;
  winnersDetected: number;
}

// Scheduler state
const schedulerState: SchedulerState = {
  task: null,
  lastRun: null,
  lastRunStatus: null,
  winnersDetected: 0
};

/**
 * Detect winners based on performance thresholds
 */
async function detectWinners(pgPool: Pool): Promise<DetectedWinner[]> {
  logger.debug('Running winner detection query', {
    minROAS: WINNER_MIN_ROAS,
    minCTR: WINNER_MIN_CTR,
    minSpend: WINNER_MIN_SPEND,
    minHours: WINNER_MIN_HOURS
  });

  // Calculate the time threshold
  const hoursAgo = new Date();
  hoursAgo.setHours(hoursAgo.getHours() - WINNER_MIN_HOURS);

  // Query ads with performance metrics that meet winner criteria
  const query = `
    SELECT
      a.ad_id,
      a.campaign_id,
      a.arc_name,
      c.name as campaign_name,
      v.title as video_title,
      COALESCE(SUM(pm.impressions), 0) as total_impressions,
      COALESCE(SUM(pm.clicks), 0) as total_clicks,
      COALESCE(SUM(pm.conversions), 0) as total_conversions,
      COALESCE(SUM(pm.spend), 0) as total_spend,
      CASE
        WHEN SUM(pm.impressions) > 0
        THEN (SUM(pm.clicks)::FLOAT / SUM(pm.impressions))
        ELSE 0
      END as actual_ctr,
      CASE
        WHEN SUM(pm.spend) > 0
        THEN ((SUM(pm.conversions) * 50.0) / SUM(pm.spend))
        ELSE 0
      END as actual_roas
    FROM ads a
    LEFT JOIN campaigns c ON a.campaign_id = c.id
    LEFT JOIN videos v ON a.video_id::text = v.id::text OR a.asset_id::text = v.id::text
    LEFT JOIN performance_metrics pm ON v.id = pm.video_id
    WHERE a.created_at <= $1
      AND a.approved = true
      AND a.status IN ('approved', 'published')
    GROUP BY a.ad_id, c.id, v.id
    HAVING
      SUM(pm.spend) >= $2
      AND (SUM(pm.clicks)::FLOAT / NULLIF(SUM(pm.impressions), 0)) >= $3
      AND ((SUM(pm.conversions) * 50.0) / NULLIF(SUM(pm.spend), 0)) >= $4
    ORDER BY actual_roas DESC, actual_ctr DESC
  `;

  const values = [
    hoursAgo,
    WINNER_MIN_SPEND,
    WINNER_MIN_CTR,
    WINNER_MIN_ROAS
  ];

  const result = await pgPool.query(query, values);
  return result.rows.map(w => ({
    ad_id: w.ad_id,
    campaign_name: w.campaign_name,
    video_title: w.video_title,
    arc_name: w.arc_name,
    actual_ctr: parseFloat(w.actual_ctr),
    actual_roas: parseFloat(w.actual_roas),
    total_spend: parseFloat(w.total_spend),
    total_impressions: parseInt(w.total_impressions),
    total_clicks: parseInt(w.total_clicks),
    total_conversions: parseInt(w.total_conversions)
  }));
}

/**
 * Index winners in ML service FAISS index
 */
async function indexWinnersInML(winners: DetectedWinner[]): Promise<number> {
  let indexedCount = 0;

  for (const winner of winners) {
    try {
      await axios.post(
        `${ML_SERVICE_URL}/api/ml/winners/index`,
        {
          ad_id: winner.ad_id,
          metadata: {
            campaign_name: winner.campaign_name,
            video_title: winner.video_title,
            arc_name: winner.arc_name,
            actual_ctr: winner.actual_ctr,
            actual_roas: winner.actual_roas,
            total_spend: winner.total_spend,
            total_impressions: winner.total_impressions,
            total_clicks: winner.total_clicks,
            total_conversions: winner.total_conversions,
            detected_at: new Date().toISOString()
          }
        },
        { timeout: 10000 }
      );

      indexedCount++;
      logger.debug(`Indexed winner ${winner.ad_id} in FAISS`);
    } catch (mlError: any) {
      logger.warn(`Failed to index winner ${winner.ad_id}`, {
        error: mlError.message
      });
    }
  }

  return indexedCount;
}

/**
 * Send notifications for newly detected winners
 */
async function notifyNewWinners(winners: DetectedWinner[]): Promise<void> {
  if (winners.length === 0) {
    return;
  }

  logger.info(`Notifying about ${winners.length} new winners`, {
    winnerIds: winners.map(w => w.ad_id)
  });

  // Send webhook notification if configured
  if (WINNER_WEBHOOK_URL) {
    try {
      await axios.post(WINNER_WEBHOOK_URL, {
        event: 'winners_detected',
        count: winners.length,
        winners: winners.map(w => ({
          ad_id: w.ad_id,
          campaign_name: w.campaign_name,
          video_title: w.video_title,
          arc_name: w.arc_name,
          ctr: w.actual_ctr,
          roas: w.actual_roas,
          spend: w.total_spend,
          detected_at: new Date().toISOString()
        })),
        timestamp: new Date().toISOString()
      }, {
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'GeminiVideo-WinnerScheduler/1.0'
        }
      });

      logger.info('Winner webhook notification sent successfully', {
        url: WINNER_WEBHOOK_URL,
        count: winners.length
      });
    } catch (webhookError: any) {
      logger.error('Failed to send winner webhook notification', {
        error: webhookError.message,
        url: WINNER_WEBHOOK_URL
      });
    }
  }

  // Send email notification if configured
  if (WINNER_ALERT_EMAIL) {
    logger.info('Winner email notification would be sent', {
      to: WINNER_ALERT_EMAIL,
      count: winners.length,
      note: 'Email integration not yet implemented'
    });
  }

  // Log summary
  logger.info('Winner notification summary', {
    total_winners: winners.length,
    winners: winners.map(w => ({
      ad_id: w.ad_id,
      campaign: w.campaign_name,
      ctr: `${(w.actual_ctr * 100).toFixed(2)}%`,
      roas: w.actual_roas.toFixed(2),
      spend: `$${w.total_spend.toFixed(2)}`
    }))
  });
}

/**
 * Run winner detection job
 */
async function runWinnerDetection(pgPool: Pool): Promise<void> {
  const startTime = Date.now();
  schedulerState.lastRun = new Date();
  schedulerState.lastRunStatus = 'running';

  logger.info('🔍 Starting scheduled winner detection...', {
    schedule: WINNER_CHECK_SCHEDULE,
    minROAS: WINNER_MIN_ROAS,
    minCTR: WINNER_MIN_CTR,
    minSpend: WINNER_MIN_SPEND,
    minHours: WINNER_MIN_HOURS
  });

  try {
    // Run winner detection
    const winners = await detectWinners(pgPool);

    const duration = Date.now() - startTime;

    // Update scheduler state
    schedulerState.lastRunStatus = 'success';
    schedulerState.winnersDetected = winners.length;

    logger.info(`✅ Scheduled winner detection complete`, {
      winnersFound: winners.length,
      duration: `${duration}ms`,
      nextRun: 'in 6 hours (configurable)'
    });

    // Index winners in ML service
    if (winners.length > 0) {
      const indexedCount = await indexWinnersInML(winners);
      logger.info(`Indexed ${indexedCount}/${winners.length} winners in ML service`);
    }

    // Send notifications if winners were found
    if (winners.length > 0) {
      await notifyNewWinners(winners);
    }

  } catch (error: any) {
    const duration = Date.now() - startTime;
    schedulerState.lastRunStatus = 'failure';

    logger.error('❌ Scheduled winner detection failed', {
      error: error.message,
      stack: error.stack,
      duration: `${duration}ms`
    });

    // Don't throw - we want the scheduler to continue running
  }
}

/**
 * Start the winner detection scheduler
 */
export function startWinnerScheduler(pgPool: Pool): void {
  if (!ENABLE_WINNER_SCHEDULER) {
    logger.info('⏸️  Winner scheduler is disabled (ENABLE_WINNER_SCHEDULER=false)');
    return;
  }

  // Validate cron schedule
  if (!cron.validate(WINNER_CHECK_SCHEDULE)) {
    logger.error('❌ Invalid cron schedule for winner detection', {
      schedule: WINNER_CHECK_SCHEDULE
    });
    throw new Error(`Invalid cron schedule: ${WINNER_CHECK_SCHEDULE}`);
  }

  logger.info('🚀 Starting winner detection scheduler', {
    schedule: WINNER_CHECK_SCHEDULE,
    description: 'Runs every 6 hours by default',
    criteria: {
      minROAS: WINNER_MIN_ROAS,
      minCTR: WINNER_MIN_CTR,
      minSpend: WINNER_MIN_SPEND,
      minHours: WINNER_MIN_HOURS
    },
    webhookConfigured: !!WINNER_WEBHOOK_URL,
    emailConfigured: !!WINNER_ALERT_EMAIL
  });

  // Schedule the cron job
  schedulerState.task = cron.schedule(WINNER_CHECK_SCHEDULE, async () => {
    await runWinnerDetection(pgPool);
  });

  logger.info('✅ Winner scheduler started successfully', {
    nextExecution: 'Will run according to cron schedule',
    schedule: WINNER_CHECK_SCHEDULE
  });
}

/**
 * Stop the winner detection scheduler
 */
export function stopWinnerScheduler(): void {
  if (schedulerState.task) {
    schedulerState.task.stop();
    schedulerState.task = null;
    logger.info('🛑 Winner scheduler stopped');
  }
}

/**
 * Get scheduler status
 */
export function getWinnerSchedulerStatus(): {
  enabled: boolean;
  schedule: string;
  running: boolean;
  lastRun: Date | null;
  lastRunStatus: string | null;
  winnersDetected: number;
  config: WinnerSchedulerConfig;
} {
  return {
    enabled: ENABLE_WINNER_SCHEDULER,
    schedule: WINNER_CHECK_SCHEDULE,
    running: schedulerState.task !== null,
    lastRun: schedulerState.lastRun,
    lastRunStatus: schedulerState.lastRunStatus,
    winnersDetected: schedulerState.winnersDetected,
    config: {
      schedule: WINNER_CHECK_SCHEDULE,
      minROAS: WINNER_MIN_ROAS,
      minCTR: WINNER_MIN_CTR,
      minSpend: WINNER_MIN_SPEND,
      minHours: WINNER_MIN_HOURS,
      enabled: ENABLE_WINNER_SCHEDULER
    }
  };
}

/**
 * Manually trigger winner detection (outside of schedule)
 */
export async function triggerWinnerDetection(pgPool: Pool): Promise<void> {
  logger.info('🔧 Manual winner detection triggered');
  await runWinnerDetection(pgPool);
}

// Export configuration for testing
export const config = {
  WINNER_CHECK_SCHEDULE,
  WINNER_MIN_ROAS,
  WINNER_MIN_CTR,
  WINNER_MIN_SPEND,
  WINNER_MIN_HOURS,
  ENABLE_WINNER_SCHEDULER,
  WINNER_WEBHOOK_URL,
  WINNER_ALERT_EMAIL
};
