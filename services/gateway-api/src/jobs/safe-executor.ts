/**
 * SafeExecutor Worker - Anti-Ban Protection for Meta API
 *
 * Purpose:
 *   Executes ad changes via Meta API with safety checks to prevent account bans.
 *   Polls pending_ad_changes table using claim_pending_ad_change() function.
 *
 * Safety Rules:
 *   1. Rate Limiting: Max 15 actions per campaign per hour
 *   2. Budget Velocity: Max 20% budget change in 6-hour window
 *   3. Jitter: Random delays based on DB config (jitter_ms_min to jitter_ms_max)
 *   4. Fuzzy Budgets: ±3% randomization to appear human
 *
 * Flow:
 *   1. Poll pending_ad_changes table via claim_pending_ad_change(workerId)
 *   2. Apply jitter delay from DB config
 *   3. Check rate limit
 *   4. Check budget velocity
 *   5. Execute Meta API call with fuzzy budget
 *   6. Update status in database
 *
 * Created: 2025-12-07
 */

import httpClient from 'axios';
import { Pool } from 'pg';
import { processBatchChanges } from './batch-executor';
import { updateMarketIntelOnScaling } from '../services/market-intel-service';

// Environment variables
const DATABASE_URL = process.env.DATABASE_URL || '';
const META_API_VERSION = process.env.META_API_VERSION || 'v18.0';
const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || '';
const WORKER_ID = process.env.WORKER_ID || 'worker-1';
const POLL_INTERVAL_MS = parseInt(process.env.POLL_INTERVAL_MS || '5000', 10);
const BATCH_MODE_ENABLED = process.env.BATCH_MODE_ENABLED === 'true' || true; // Default enabled
const BATCH_SIZE = parseInt(process.env.BATCH_SIZE || '10', 10); // Min batch size to trigger batch mode

// Safety constants
const MAX_ACTIONS_PER_HOUR = 15;
const MAX_BUDGET_VELOCITY_PCT = 0.20; // 20%
const VELOCITY_WINDOW_HOURS = 6;

interface PendingAdChange {
  id: number;
  tenant_id: string;
  campaign_id: string;
  ad_id?: string;
  change_type: 'BUDGET_INCREASE' | 'BUDGET_DECREASE' | 'STATUS_CHANGE' | 'TARGETING_UPDATE';
  old_value: any;
  new_value: any;
  triggered_by: string;
  ml_confidence?: number;
  reason?: string;
  jitter_ms_min: number;
  jitter_ms_max: number;
  claimed_by?: string;
  claimed_at?: Date;
}

interface SafetyCheckResult {
  passed: boolean;
  reason?: string;
  current_count?: number;
  limit?: number;
}

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
 * Apply random jitter delay based on change config
 */
async function applyJitter(change: PendingAdChange): Promise<number> {
  const jitterMs = Math.floor(Math.random() * (change.jitter_ms_max - change.jitter_ms_min)) + change.jitter_ms_min;
  console.log(`[SafeExecutor] Applying jitter: ${jitterMs}ms (range: ${change.jitter_ms_min}-${change.jitter_ms_max})`);
  await new Promise(resolve => setTimeout(resolve, jitterMs));
  return jitterMs;
}

/**
 * Check rate limit (max 15 actions per campaign per hour)
 */
async function checkRateLimit(change: PendingAdChange): Promise<SafetyCheckResult> {
  const pool = getDbPool();
  const client = await pool.connect();

  try {
    // Count actions in last hour for this campaign
    const result = await client.query(`
      SELECT COUNT(*) as action_count
      FROM ad_change_history
      WHERE campaign_id = $1
        AND status IN ('executing', 'completed')
        AND created_at > NOW() - INTERVAL '1 hour'
    `, [change.campaign_id]);

    const actionCount = parseInt(result.rows[0].action_count, 10);

    if (actionCount >= MAX_ACTIONS_PER_HOUR) {
      return {
        passed: false,
        reason: `Rate limit exceeded: ${actionCount}/${MAX_ACTIONS_PER_HOUR} actions in last hour`,
        current_count: actionCount,
        limit: MAX_ACTIONS_PER_HOUR,
      };
    }

    return {
      passed: true,
      current_count: actionCount,
      limit: MAX_ACTIONS_PER_HOUR,
    };

  } finally {
    client.release();
  }
}

/**
 * Check budget velocity (max 20% change in 6-hour window)
 */
async function checkBudgetVelocity(change: PendingAdChange): Promise<SafetyCheckResult> {
  // Only check for budget changes
  if (change.change_type !== 'BUDGET_INCREASE' && change.change_type !== 'BUDGET_DECREASE') {
    return { passed: true };
  }

  const pool = getDbPool();
  const client = await pool.connect();

  try {
    // Get budget changes in last 6 hours
    const result = await client.query(`
      SELECT
        (old_value->>'budget')::NUMERIC as old_budget,
        (new_value->>'budget')::NUMERIC as new_budget
      FROM ad_change_history
      WHERE campaign_id = $1
        AND change_type IN ('BUDGET_INCREASE', 'BUDGET_DECREASE')
        AND status = 'completed'
        AND created_at > NOW() - INTERVAL '${VELOCITY_WINDOW_HOURS} hours'
      ORDER BY created_at ASC
    `, [change.campaign_id]);

    if (result.rows.length === 0) {
      return { passed: true };
    }

    // Calculate total budget change
    const firstBudget = parseFloat(result.rows[0].old_budget);
    const currentBudget = parseFloat(change.old_value.budget);
    const newBudget = parseFloat(change.new_value.budget);

    const totalChange = Math.abs(newBudget - firstBudget);
    const changePercentage = totalChange / firstBudget;

    if (changePercentage > MAX_BUDGET_VELOCITY_PCT) {
      return {
        passed: false,
        reason: `Budget velocity exceeded: ${(changePercentage * 100).toFixed(1)}% change in ${VELOCITY_WINDOW_HOURS}h (max: ${MAX_BUDGET_VELOCITY_PCT * 100}%)`,
      };
    }

    return { passed: true };

  } finally {
    client.release();
  }
}

/**
 * Apply fuzzy budget (±3% randomization to appear human)
 */
function applyFuzzyBudget(requestedBudget: number): number {
  const fuzzyBudget = requestedBudget * (1 + (Math.random() * 0.06 - 0.03));

  // Round to 2 decimal places
  return Math.round(fuzzyBudget * 100) / 100;
}

/**
 * Execute Meta API call
 */
async function executeMetaApiCall(change: PendingAdChange, fuzzyBudget?: number): Promise<any> {
  const targetId = change.ad_id || change.campaign_id;
  const endpoint = `https://graph.facebook.com/${META_API_VERSION}/${targetId}`;

  let updateData: any = {};

  switch (change.change_type) {
    case 'BUDGET_INCREASE':
    case 'BUDGET_DECREASE':
      updateData = {
        daily_budget: Math.round(fuzzyBudget! * 100), // Meta expects cents
      };
      break;

    case 'STATUS_CHANGE':
      updateData = {
        status: change.new_value.status,
      };
      break;

    case 'TARGETING_UPDATE':
      updateData = {
        targeting: change.new_value.targeting,
      };
      break;
  }

  const response = await httpClient.post(
    endpoint,
    updateData,
    {
      params: {
        access_token: META_ACCESS_TOKEN,
      },
      timeout: 30000,
    }
  );

  return response.data;
}

/**
 * Log execution to database
 */
async function logExecution(
  change: PendingAdChange,
  status: 'completed' | 'failed' | 'blocked',
  duration: number,
  metaResponse?: any,
  error?: Error,
  rateLimitCheck?: SafetyCheckResult,
  velocityCheck?: SafetyCheckResult
): Promise<void> {
  const pool = getDbPool();
  const client = await pool.connect();

  try {
    await client.query(`
      INSERT INTO ad_change_history (
        tenant_id, campaign_id, ad_id, change_type,
        old_value, new_value, triggered_by, ml_confidence, reason,
        status, rate_limit_passed, velocity_check_passed,
        execution_duration_ms, meta_response, error_message
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
    `, [
      change.tenant_id,
      change.campaign_id,
      change.ad_id,
      change.change_type,
      JSON.stringify(change.old_value),
      JSON.stringify(change.new_value),
      change.triggered_by,
      change.ml_confidence,
      change.reason,
      status,
      rateLimitCheck?.passed ?? true,
      velocityCheck?.passed ?? true,
      duration,
      metaResponse ? JSON.stringify(metaResponse) : null,
      error?.message,
    ]);

  } finally {
    client.release();
  }
}

/**
 * Claim and process a pending ad change
 */
async function claimAndProcessChange(): Promise<boolean> {
  const pool = getDbPool();
  const client = await pool.connect();

  try {
    // Claim a pending change
    const result = await client.query('SELECT * FROM claim_pending_ad_change($1)', [WORKER_ID]);

    if (result.rows.length === 0) {
      // No pending changes
      return false;
    }

    const change: PendingAdChange = result.rows[0];
    console.log(`[SafeExecutor] Claimed change ${change.id} for campaign ${change.campaign_id}`);

    const startTime = Date.now();

    try {
      // Step 1: Apply jitter from DB config
      const jitterMs = Math.floor(Math.random() * (change.jitter_ms_max - change.jitter_ms_min)) + change.jitter_ms_min;
      console.log(`[SafeExecutor] Applying jitter: ${jitterMs}ms`);
      await new Promise(resolve => setTimeout(resolve, jitterMs));

      // Step 2: Check rate limit
      const rateLimitCheck = await checkRateLimit(change);
      if (!rateLimitCheck.passed) {
        console.warn(`[SafeExecutor] Rate limit check failed: ${rateLimitCheck.reason}`);
        await logExecution(change, 'blocked', Date.now() - startTime, undefined, undefined, rateLimitCheck);
        // Update status to failed so it can be retried later
        await client.query('UPDATE pending_ad_changes SET status = $1 WHERE id = $2', ['failed', change.id]);
        return true;
      }

      // Step 3: Check budget velocity
      const velocityCheck = await checkBudgetVelocity(change);
      if (!velocityCheck.passed) {
        console.warn(`[SafeExecutor] Velocity check failed: ${velocityCheck.reason}`);
        await logExecution(change, 'blocked', Date.now() - startTime, undefined, undefined, rateLimitCheck, velocityCheck);
        // Update status to failed so it can be retried later
        await client.query('UPDATE pending_ad_changes SET status = $1 WHERE id = $2', ['failed', change.id]);
        return true;
      }

      // Step 4: Apply fuzzy budget (if budget change)
      let fuzzyBudget: number | undefined;
      if (change.change_type === 'BUDGET_INCREASE' || change.change_type === 'BUDGET_DECREASE') {
        const requestedBudget = parseFloat(change.new_value.budget);
        fuzzyBudget = requestedBudget * (1 + (Math.random() * 0.06 - 0.03));
        console.log(`[SafeExecutor] Fuzzy budget: $${requestedBudget} → $${fuzzyBudget}`);
      }

      // Step 5: Execute Meta API call
      const metaResponse = await executeMetaApiCall(change, fuzzyBudget);

      // Step 6: Update Market Intelligence on scaling (if budget increase)
      if ((change.change_type === 'BUDGET_INCREASE') && fuzzyBudget) {
        try {
          const oldBudget = parseFloat(change.old_value.budget);
          const changePercentage = (fuzzyBudget - oldBudget) / oldBudget;
          
          if (changePercentage >= 0.20) { // 20%+ increase
            await updateMarketIntelOnScaling({
              campaign_id: change.campaign_id,
              ad_id: change.ad_id,
              old_budget: oldBudget,
              new_budget: fuzzyBudget,
              change_percentage: changePercentage,
              reason: change.reason || 'Budget increase',
              triggered_by: change.triggered_by || 'ml-service'
            });
          }
        } catch (marketIntelError: any) {
          // Non-fatal - don't block execution
          console.debug(`[SafeExecutor] Market Intel update failed (non-fatal): ${marketIntelError.message}`);
        }
      }

      // Step 7: Update status and log success
      await client.query('UPDATE pending_ad_changes SET status = $1, executed_at = NOW() WHERE id = $2', ['completed', change.id]);

      const duration = Date.now() - startTime;
      await logExecution(change, 'completed', duration, metaResponse, undefined, rateLimitCheck, velocityCheck);

      console.log(`[SafeExecutor] Change ${change.id} completed successfully in ${duration}ms`);
      return true;

    } catch (error: any) {
      // Log failure and update status
      const duration = Date.now() - startTime;
      await logExecution(change, 'failed', duration, undefined, error);
      await client.query('UPDATE pending_ad_changes SET status = $1 WHERE id = $2', ['failed', change.id]);

      console.error(`[SafeExecutor] Change ${change.id} failed:`, error.message);
      return true;
    }

  } finally {
    client.release();
  }
}

/**
 * Check how many pending changes are available
 */
async function countPendingChanges(): Promise<number> {
  const pool = getDbPool();
  const client = await pool.connect();

  try {
    const result = await client.query(
      `SELECT COUNT(*) as count FROM pending_ad_changes WHERE status = 'pending'`
    );
    return parseInt(result.rows[0].count, 10);
  } finally {
    client.release();
  }
}

/**
 * Start SafeExecutor worker
 */
export async function startSafeExecutor(): Promise<void> {
  console.log(`[SafeExecutor] Starting worker ${WORKER_ID}...`);
  console.log(`[SafeExecutor] Poll interval: ${POLL_INTERVAL_MS}ms`);
  console.log(`[SafeExecutor] Batch mode: ${BATCH_MODE_ENABLED ? 'enabled' : 'disabled'}`);

  // Continuous polling loop
  while (true) {
    try {
      // Check if batch mode should be used
      if (BATCH_MODE_ENABLED) {
        const pendingCount = await countPendingChanges();
        
        if (pendingCount >= BATCH_SIZE) {
          // Use batch processing for 10x faster execution
          console.log(`[SafeExecutor] Processing batch: ${pendingCount} pending changes`);
          const processed = await processBatchChanges(getDbPool(), WORKER_ID, BATCH_SIZE);
          
          if (processed > 0) {
            console.log(`[SafeExecutor] Batch processed ${processed} changes`);
            // Continue immediately to process more
            continue;
          }
        }
      }

      // Fall back to individual processing
      const processed = await claimAndProcessChange();

      if (!processed) {
        // No changes found, wait before polling again
        await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
      }
      // If we processed something, immediately check for more work

    } catch (error: any) {
      console.error(`[SafeExecutor] Polling error:`, error.message);
      // Wait before retrying on error
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
    }
  }
}
