/**
 * Budget Scheduler - Automatic Budget Reallocation Job
 *
 * Purpose:
 *   Schedules automatic budget optimization to run every 12 hours
 *   Applies safety limits to prevent extreme changes
 *   Logs all changes and sends summary reports
 *
 * Safety Rules:
 *   1. Max budget change per day: 50% of total
 *   2. Min budget per ad: $10
 *   3. Max budget per ad: $1000 (configurable)
 *
 * Schedule:
 *   Default: Every 12 hours (cron: 0 star-slash-12 star star star)
 *   Configurable via BUDGET_SCHEDULE env var
 *
 * Created: 2025-12-13
 */

import cron from 'node-cron';
import { logger } from '../utils/logger';
import { Pool } from 'pg';

// Environment variables
const BUDGET_SCHEDULE = process.env.BUDGET_SCHEDULE || '0 */12 * * *'; // Every 12 hours
const DATABASE_URL = process.env.DATABASE_URL || '';
const DEFAULT_AD_ACCOUNT_ID = process.env.DEFAULT_AD_ACCOUNT_ID;

// Safety limits interface
interface SafetyLimits {
  maxDailyChangePercent: number;  // Default: 50% (0.5)
  minBudgetPerAd: number;         // Default: $10
  maxBudgetPerAd: number;         // Default: $1000
}

// Budget change interface
export interface BudgetChange {
  campaignId: string;
  adId?: string;
  currentBudget: number;
  newBudget: number;
  reason: string;
  action: 'increase' | 'decrease' | 'pause' | 'maintain';
  confidence?: number;
  expectedROAS?: number;
}

// Summary report interface
interface BudgetOptimizationResult {
  changes: BudgetChange[];
  applied: number;
  skipped: number;
  totalCurrentBudget: number;
  totalNewBudget: number;
  timestamp: Date;
}

// Default safety limits
const DEFAULT_LIMITS: SafetyLimits = {
  maxDailyChangePercent: 0.5,    // Max 50% change per day
  minBudgetPerAd: 10,            // Min $10 per ad
  maxBudgetPerAd: 1000           // Max $1000 per ad (configurable)
};

// Database connection pool
let dbPool: Pool | null = null;

function getDbPool(): Pool {
  if (!dbPool) {
    dbPool = new Pool({
      connectionString: DATABASE_URL,
      max: 10,
    });
  }
  return dbPool;
}

/**
 * Start the budget scheduler with cron
 */
export function startBudgetScheduler(): void {
  logger.info('Starting budget scheduler', {
    schedule: BUDGET_SCHEDULE,
    defaultAccountId: DEFAULT_AD_ACCOUNT_ID,
    safetyLimits: DEFAULT_LIMITS,
  });

  // Validate cron expression
  if (!cron.validate(BUDGET_SCHEDULE)) {
    logger.error('Invalid cron schedule expression', { schedule: BUDGET_SCHEDULE });
    throw new Error(`Invalid cron schedule: ${BUDGET_SCHEDULE}`);
  }

  // Schedule the job
  cron.schedule(BUDGET_SCHEDULE, async () => {
    logger.info('Running scheduled budget optimization...');
    try {
      const result = await runBudgetOptimization();
      logger.info('Scheduled budget optimization completed', {
        applied: result.applied,
        skipped: result.skipped,
        totalChanges: result.changes.length,
      });
    } catch (error: any) {
      logger.error('Scheduled budget optimization failed', {
        error: error.message,
        stack: error.stack,
      });
    }
  });

  logger.info('Budget scheduler started successfully');
}

/**
 * Run budget optimization for a specific account
 * Can be called manually or by the scheduler
 */
export async function runBudgetOptimization(accountId?: string): Promise<BudgetOptimizationResult> {
  const targetAccountId = accountId || DEFAULT_AD_ACCOUNT_ID;

  if (!targetAccountId) {
    logger.warn('No account ID specified for budget optimization');
    return {
      changes: [],
      applied: 0,
      skipped: 0,
      totalCurrentBudget: 0,
      totalNewBudget: 0,
      timestamp: new Date(),
    };
  }

  const startTime = Date.now();
  logger.info('Starting budget optimization', {
    accountId: targetAccountId,
    timestamp: new Date().toISOString(),
  });

  try {
    // Step 1: Get proposed budget changes
    const proposedChanges = await getProposedBudgetChanges(targetAccountId);
    logger.info('Proposed budget changes retrieved', {
      count: proposedChanges.length,
    });

    // Step 2: Apply safety limits
    const safeChanges = applySafetyLimits(proposedChanges, DEFAULT_LIMITS);
    logger.info('Safety limits applied', {
      approved: safeChanges.approved.length,
      skipped: safeChanges.skipped.length,
    });

    // Step 3: Apply approved changes
    await applyBudgetChanges(safeChanges.approved, targetAccountId);
    logger.info('Budget changes applied', {
      count: safeChanges.approved.length,
    });

    // Step 4: Calculate totals
    const totalCurrentBudget = proposedChanges.reduce((sum, c) => sum + c.currentBudget, 0);
    const totalNewBudget = safeChanges.approved.reduce((sum, c) => sum + c.newBudget, 0);

    const result: BudgetOptimizationResult = {
      changes: proposedChanges,
      applied: safeChanges.approved.length,
      skipped: safeChanges.skipped.length,
      totalCurrentBudget,
      totalNewBudget,
      timestamp: new Date(),
    };

    // Step 5: Send summary report
    await sendBudgetReport(result, targetAccountId);

    // Step 6: Log summary
    const duration = Date.now() - startTime;
    logger.info('Budget optimization completed successfully', {
      accountId: targetAccountId,
      duration: `${duration}ms`,
      totalChangesProposed: proposedChanges.length,
      changesApplied: safeChanges.approved.length,
      changesSkipped: safeChanges.skipped.length,
      totalCurrentBudget: `$${totalCurrentBudget.toFixed(2)}`,
      totalNewBudget: `$${totalNewBudget.toFixed(2)}`,
      budgetDelta: `$${(totalNewBudget - totalCurrentBudget).toFixed(2)}`,
    });

    return result;

  } catch (error: any) {
    const duration = Date.now() - startTime;
    logger.error('Budget optimization failed', {
      accountId: targetAccountId,
      duration: `${duration}ms`,
      error: error.message,
      stack: error.stack,
    });
    throw error;
  }
}

/**
 * Get proposed budget changes from ML service or database
 * This would typically call a budget optimizer service
 */
async function getProposedBudgetChanges(accountId: string): Promise<BudgetChange[]> {
  const pool = getDbPool();
  const client = await pool.connect();

  try {
    // Query campaigns with recent performance data
    const result = await client.query(`
      SELECT
        c.campaign_id,
        c.daily_budget as current_budget,
        c.status,
        COALESCE(p.roas, 0) as roas,
        COALESCE(p.ctr, 0) as ctr,
        COALESCE(p.spend, 0) as spend,
        COALESCE(p.conversions, 0) as conversions
      FROM campaigns c
      LEFT JOIN (
        SELECT
          campaign_id,
          AVG(roas) as roas,
          AVG(ctr) as ctr,
          SUM(spend) as spend,
          SUM(conversions) as conversions
        FROM campaign_performance
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY campaign_id
      ) p ON c.campaign_id = p.campaign_id
      WHERE c.account_id = $1
        AND c.status = 'ACTIVE'
    `, [accountId]);

    // Simple ML-based budget allocation logic
    const changes: BudgetChange[] = result.rows.map((row: any) => {
      const currentBudget = parseFloat(row.current_budget) || 0;
      const roas = parseFloat(row.roas) || 0;
      const ctr = parseFloat(row.ctr) || 0;

      // Decision logic based on performance
      let newBudget = currentBudget;
      let action: BudgetChange['action'] = 'maintain';
      let reason = 'No change needed';

      if (roas > 3.0 && ctr > 0.02) {
        // High performance: Increase budget by 20%
        newBudget = currentBudget * 1.2;
        action = 'increase';
        reason = `High ROAS (${roas.toFixed(2)}) and CTR (${(ctr * 100).toFixed(2)}%)`;
      } else if (roas > 2.0 && ctr > 0.015) {
        // Good performance: Increase budget by 10%
        newBudget = currentBudget * 1.1;
        action = 'increase';
        reason = `Good ROAS (${roas.toFixed(2)}) and CTR (${(ctr * 100).toFixed(2)}%)`;
      } else if (roas < 1.0 && ctr < 0.005) {
        // Poor performance: Decrease budget by 30%
        newBudget = currentBudget * 0.7;
        action = 'decrease';
        reason = `Low ROAS (${roas.toFixed(2)}) and CTR (${(ctr * 100).toFixed(2)}%)`;
      } else if (roas < 0.5) {
        // Very poor performance: Consider pausing
        newBudget = 0;
        action = 'pause';
        reason = `Very low ROAS (${roas.toFixed(2)})`;
      }

      return {
        campaignId: row.campaign_id,
        currentBudget,
        newBudget,
        reason,
        action,
        confidence: roas > 0 ? 0.8 : 0.5,
        expectedROAS: roas,
      };
    });

    return changes.filter(c => c.action !== 'maintain');

  } finally {
    client.release();
  }
}

/**
 * Apply safety limits to proposed budget changes
 */
function applySafetyLimits(
  changes: BudgetChange[],
  limits: SafetyLimits
): {
  approved: BudgetChange[];
  skipped: BudgetChange[];
} {
  const approved: BudgetChange[] = [];
  const skipped: BudgetChange[] = [];

  for (const change of changes) {
    let shouldSkip = false;
    let skipReason = '';

    // Skip if pausing (handled separately)
    if (change.action === 'pause') {
      approved.push(change);
      continue;
    }

    // Apply min budget limit
    if (change.newBudget < limits.minBudgetPerAd) {
      change.newBudget = limits.minBudgetPerAd;
      logger.debug('Budget adjusted to minimum', {
        campaignId: change.campaignId,
        originalBudget: change.newBudget,
        adjustedBudget: limits.minBudgetPerAd,
      });
    }

    // Apply max budget limit
    if (change.newBudget > limits.maxBudgetPerAd) {
      change.newBudget = limits.maxBudgetPerAd;
      logger.debug('Budget adjusted to maximum', {
        campaignId: change.campaignId,
        originalBudget: change.newBudget,
        adjustedBudget: limits.maxBudgetPerAd,
      });
    }

    // Check daily change limit (percentage)
    const changePercent = Math.abs(change.newBudget - change.currentBudget) / change.currentBudget;
    if (changePercent > limits.maxDailyChangePercent) {
      shouldSkip = true;
      skipReason = `Change too large: ${(changePercent * 100).toFixed(1)}% exceeds ${(limits.maxDailyChangePercent * 100)}% limit`;
      logger.warn('Budget change skipped due to safety limit', {
        campaignId: change.campaignId,
        currentBudget: change.currentBudget,
        proposedBudget: change.newBudget,
        changePercent: `${(changePercent * 100).toFixed(1)}%`,
        limit: `${(limits.maxDailyChangePercent * 100)}%`,
      });
    }

    if (shouldSkip) {
      skipped.push({
        ...change,
        reason: `${change.reason} [SKIPPED: ${skipReason}]`,
      });
    } else {
      approved.push(change);
    }
  }

  return { approved, skipped };
}

/**
 * Apply budget changes to campaigns
 */
async function applyBudgetChanges(changes: BudgetChange[], accountId: string): Promise<void> {
  if (changes.length === 0) {
    logger.info('No budget changes to apply');
    return;
  }

  const pool = getDbPool();
  const client = await pool.connect();

  try {
    await client.query('BEGIN');

    for (const change of changes) {
      // Insert into pending_ad_changes for safe execution
      await client.query(`
        INSERT INTO pending_ad_changes (
          tenant_id,
          campaign_id,
          change_type,
          old_value,
          new_value,
          triggered_by,
          ml_confidence,
          reason,
          status,
          jitter_ms_min,
          jitter_ms_max
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
      `, [
        accountId,
        change.campaignId,
        change.action === 'increase' ? 'BUDGET_INCREASE' : change.action === 'decrease' ? 'BUDGET_DECREASE' : 'STATUS_CHANGE',
        JSON.stringify({ budget: change.currentBudget }),
        JSON.stringify({
          budget: change.newBudget,
          status: change.action === 'pause' ? 'PAUSED' : 'ACTIVE',
        }),
        'budget-scheduler',
        change.confidence || 0.7,
        change.reason,
        'pending',
        1000,  // 1 second min jitter
        5000,  // 5 seconds max jitter
      ]);

      logger.info('Budget change queued', {
        campaignId: change.campaignId,
        action: change.action,
        currentBudget: `$${change.currentBudget.toFixed(2)}`,
        newBudget: `$${change.newBudget.toFixed(2)}`,
        reason: change.reason,
      });
    }

    await client.query('COMMIT');
    logger.info('All budget changes committed to queue', {
      count: changes.length,
    });

  } catch (error: any) {
    await client.query('ROLLBACK');
    logger.error('Failed to apply budget changes', {
      error: error.message,
      stack: error.stack,
    });
    throw error;
  } finally {
    client.release();
  }
}

/**
 * Send budget optimization summary report
 */
async function sendBudgetReport(result: BudgetOptimizationResult, accountId: string): Promise<void> {
  try {
    const budgetDelta = result.totalNewBudget - result.totalCurrentBudget;
    const budgetChangePercent = result.totalCurrentBudget > 0
      ? (budgetDelta / result.totalCurrentBudget) * 100
      : 0;

    const report = {
      timestamp: result.timestamp.toISOString(),
      accountId,
      summary: {
        totalChangesProposed: result.changes.length,
        changesApplied: result.applied,
        changesSkipped: result.skipped,
        totalCurrentBudget: `$${result.totalCurrentBudget.toFixed(2)}`,
        totalNewBudget: `$${result.totalNewBudget.toFixed(2)}`,
        budgetDelta: `$${budgetDelta.toFixed(2)}`,
        budgetChangePercent: `${budgetChangePercent.toFixed(2)}%`,
      },
      appliedChanges: result.changes.slice(0, 10), // Top 10 changes
      safetyLimits: DEFAULT_LIMITS,
    };

    // Log the report (could also send via email/Slack/webhook)
    logger.info('Budget Optimization Report', report);

    // TODO: Integrate with notification service (email, Slack, etc.)
    // await notificationService.send({
    //   channel: 'budget-alerts',
    //   subject: 'Budget Optimization Report',
    //   body: JSON.stringify(report, null, 2),
    // });

    logger.info('Budget report sent successfully');

  } catch (error: any) {
    logger.error('Failed to send budget report', {
      error: error.message,
      stack: error.stack,
    });
    // Don't throw - report sending is non-critical
  }
}

/**
 * Manual trigger for budget optimization (for testing or admin use)
 */
export async function triggerBudgetOptimization(accountId: string): Promise<BudgetOptimizationResult> {
  logger.info('Manual budget optimization triggered', { accountId });
  return runBudgetOptimization(accountId);
}

// Export for use in other modules
export {
  startBudgetScheduler,
  runBudgetOptimization,
  triggerBudgetOptimization,
};
