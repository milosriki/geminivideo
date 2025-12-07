/**
 * SafeExecutor Worker - Anti-Ban Protection for Meta API
 *
 * Purpose:
 *   Executes ad changes via Meta API with safety checks to prevent account bans.
 *   Uses pg-boss job queue with retry logic and multiple safety layers.
 *
 * Safety Rules:
 *   1. Rate Limiting: Max 15 actions per campaign per hour
 *   2. Budget Velocity: Max 20% budget change in 6-hour window
 *   3. Jitter: Random 3-18 second delays between calls
 *   4. Fuzzy Budgets: ±3% randomization to appear human
 *
 * Flow:
 *   1. Receive job from pg-boss queue
 *   2. Apply jitter delay
 *   3. Check rate limit
 *   4. Check budget velocity
 *   5. Execute Meta API call with fuzzy budget
 *   6. Log results to database
 *
 * Created: 2025-12-07
 */

import PgBoss from 'pg-boss';
import axios from 'axios';
import { Pool } from 'pg';

// Environment variables
const DATABASE_URL = process.env.DATABASE_URL || '';
const META_API_VERSION = process.env.META_API_VERSION || 'v18.0';
const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || '';

// Job types
const JOB_AD_CHANGE = 'ad-change';
const JOB_BUDGET_OPTIMIZATION = 'budget-optimization';

// Safety constants
const MAX_ACTIONS_PER_HOUR = 15;
const MAX_BUDGET_VELOCITY_PCT = 0.20; // 20%
const VELOCITY_WINDOW_HOURS = 6;
const MIN_JITTER_MS = 3000; // 3 seconds
const MAX_JITTER_MS = 18000; // 18 seconds
const FUZZY_BUDGET_PCT = 0.03; // ±3%

interface AdChangeJob {
  tenant_id: string;
  campaign_id: string;
  ad_id?: string;
  change_type: 'BUDGET_INCREASE' | 'BUDGET_DECREASE' | 'STATUS_CHANGE' | 'TARGETING_UPDATE';
  old_value: any;
  new_value: any;
  triggered_by: string;
  ml_confidence?: number;
  reason?: string;
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
 * Apply random jitter delay (3-18 seconds)
 */
async function applyJitter(): Promise<number> {
  const jitterMs = Math.floor(Math.random() * (MAX_JITTER_MS - MIN_JITTER_MS)) + MIN_JITTER_MS;
  console.log(`[SafeExecutor] Applying jitter: ${jitterMs}ms`);
  await new Promise(resolve => setTimeout(resolve, jitterMs));
  return jitterMs;
}

/**
 * Check rate limit (max 15 actions per campaign per hour)
 */
async function checkRateLimit(job: AdChangeJob): Promise<SafetyCheckResult> {
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
    `, [job.campaign_id]);

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
async function checkBudgetVelocity(job: AdChangeJob): Promise<SafetyCheckResult> {
  // Only check for budget changes
  if (job.change_type !== 'BUDGET_INCREASE' && job.change_type !== 'BUDGET_DECREASE') {
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
    `, [job.campaign_id]);

    if (result.rows.length === 0) {
      return { passed: true };
    }

    // Calculate total budget change
    const firstBudget = parseFloat(result.rows[0].old_budget);
    const currentBudget = parseFloat(job.old_value.budget);
    const newBudget = parseFloat(job.new_value.budget);

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
function applyFuzzyBudget(budget: number): number {
  const randomFactor = 1 + (Math.random() * 2 - 1) * FUZZY_BUDGET_PCT;
  const fuzzyBudget = budget * randomFactor;

  // Round to 2 decimal places
  return Math.round(fuzzyBudget * 100) / 100;
}

/**
 * Execute Meta API call
 */
async function executeMetaApiCall(job: AdChangeJob, fuzzyBudget?: number): Promise<any> {
  const targetId = job.ad_id || job.campaign_id;
  const endpoint = `https://graph.facebook.com/${META_API_VERSION}/${targetId}`;

  let updateData: any = {};

  switch (job.change_type) {
    case 'BUDGET_INCREASE':
    case 'BUDGET_DECREASE':
      updateData = {
        daily_budget: Math.round(fuzzyBudget! * 100), // Meta expects cents
      };
      break;

    case 'STATUS_CHANGE':
      updateData = {
        status: job.new_value.status,
      };
      break;

    case 'TARGETING_UPDATE':
      updateData = {
        targeting: job.new_value.targeting,
      };
      break;
  }

  const response = await axios.post(
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
 * Log job execution to database
 */
async function logJobExecution(
  jobId: string,
  job: AdChangeJob,
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
      job.tenant_id,
      job.campaign_id,
      job.ad_id,
      job.change_type,
      JSON.stringify(job.old_value),
      JSON.stringify(job.new_value),
      job.triggered_by,
      job.ml_confidence,
      job.reason,
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
 * Main job handler
 */
async function handleAdChangeJob(job: PgBoss.Job<AdChangeJob>): Promise<void> {
  const startTime = Date.now();
  const data = job.data;

  console.log(`[SafeExecutor] Processing ad change job ${job.id} for campaign ${data.campaign_id}`);

  try {
    // Step 1: Apply jitter
    await applyJitter();

    // Step 2: Check rate limit
    const rateLimitCheck = await checkRateLimit(data);
    if (!rateLimitCheck.passed) {
      console.warn(`[SafeExecutor] Rate limit check failed: ${rateLimitCheck.reason}`);
      await logJobExecution(job.id, data, 'blocked', Date.now() - startTime, undefined, undefined, rateLimitCheck);
      throw new Error(rateLimitCheck.reason); // Will trigger retry
    }

    // Step 3: Check budget velocity
    const velocityCheck = await checkBudgetVelocity(data);
    if (!velocityCheck.passed) {
      console.warn(`[SafeExecutor] Velocity check failed: ${velocityCheck.reason}`);
      await logJobExecution(job.id, data, 'blocked', Date.now() - startTime, undefined, undefined, rateLimitCheck, velocityCheck);
      throw new Error(velocityCheck.reason); // Will trigger retry
    }

    // Step 4: Apply fuzzy budget (if budget change)
    let fuzzyBudget: number | undefined;
    if (data.change_type === 'BUDGET_INCREASE' || data.change_type === 'BUDGET_DECREASE') {
      fuzzyBudget = applyFuzzyBudget(data.new_value.budget);
      console.log(`[SafeExecutor] Fuzzy budget: $${data.new_value.budget} → $${fuzzyBudget}`);
    }

    // Step 5: Execute Meta API call
    const metaResponse = await executeMetaApiCall(data, fuzzyBudget);

    // Step 6: Log success
    const duration = Date.now() - startTime;
    await logJobExecution(job.id, data, 'completed', duration, metaResponse, undefined, rateLimitCheck, velocityCheck);

    console.log(`[SafeExecutor] Job ${job.id} completed successfully in ${duration}ms`);

  } catch (error: any) {
    // Log failure
    const duration = Date.now() - startTime;
    await logJobExecution(job.id, data, 'failed', duration, undefined, error);

    console.error(`[SafeExecutor] Job ${job.id} failed:`, error.message);
    throw error; // Re-throw to trigger pg-boss retry
  }
}

/**
 * Start SafeExecutor worker
 */
export async function startSafeExecutor(): Promise<PgBoss> {
  console.log('[SafeExecutor] Starting worker...');

  const pgBoss = new PgBoss({
    connectionString: DATABASE_URL,
    retryLimit: 5,
    retryDelay: 60, // 1 minute
    retryBackoff: true,
    expireInHours: 24,
  });

  await pgBoss.start();

  // Subscribe to ad-change jobs
  await pgBoss.work(JOB_AD_CHANGE, {
    teamSize: 3, // Max 3 concurrent jobs
    teamConcurrency: 1, // 1 job per worker at a time
  }, handleAdChangeJob);

  console.log('[SafeExecutor] Worker started and listening for ad-change jobs');

  return pgBoss;
}

/**
 * Queue an ad change job
 */
export async function queueAdChange(boss: PgBoss, job: AdChangeJob): Promise<string> {
  const jobId = await boss.send(JOB_AD_CHANGE, job, {
    priority: 10, // Higher priority for ad changes
    singletonKey: `${job.campaign_id}-${job.change_type}`, // Prevent duplicate jobs
  });

  console.log(`[SafeExecutor] Queued ad change job ${jobId} for campaign ${job.campaign_id}`);

  return jobId;
}

export { PgBoss };
