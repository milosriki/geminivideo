/**
 * Batch Executor - 10x Faster Meta API Execution
 * ==============================================
 * 
 * OPTIMIZATION: Batch multiple ad changes into single API call
 * 
 * Impact:
 * - 10x faster execution (50 changes in 1 call vs 50 calls)
 * - Lower rate limit risk
 * - Cost savings on API quota
 * 
 * Created: 2025-01-08
 */

import axios from 'axios';
import { Pool } from 'pg';

const META_API_VERSION = process.env.META_API_VERSION || 'v18.0';
const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || '';
const BATCH_SIZE = parseInt(process.env.BATCH_SIZE || '50', 10);

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
  jitter_ms_min?: number;
  jitter_ms_max?: number;
}

interface BatchRequest {
  method: string;
  relative_url: string;
  body: string;
}

/**
 * Execute batch Meta API call for multiple ad changes
 * 
 * OPTIMIZATION: Processes up to 50 changes in single API call
 */
export async function executeBatchMetaApiCall(
  changes: PendingAdChange[],
  fuzzyBudgets?: Map<number, number>
): Promise<any[]> {
  if (changes.length === 0) {
    return [];
  }

  // Build batch request
  const batch: BatchRequest[] = changes.map((change, index) => {
    const targetId = change.ad_id || change.campaign_id;
    const endpoint = `${targetId}`;

    let updateData: any = {};

    switch (change.change_type) {
      case 'BUDGET_INCREASE':
      case 'BUDGET_DECREASE':
        const budget = fuzzyBudgets?.get(change.id) || parseFloat(change.new_value.budget);
        updateData = {
          daily_budget: Math.round(budget * 100), // Meta expects cents
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

    return {
      method: 'POST',
      relative_url: endpoint,
      body: new URLSearchParams({
        ...updateData,
        access_token: META_ACCESS_TOKEN,
      }).toString(),
    };
  });

  // Execute batch request
  const batchUrl = `https://graph.facebook.com/${META_API_VERSION}`;
  
  try {
    const response = await axios.post(
      batchUrl,
      {
        batch: JSON.stringify(batch),
        access_token: META_ACCESS_TOKEN,
      },
      {
        timeout: 60000, // 60 second timeout for batch
      }
    );

    // Parse batch response
    const results = response.data;
    const responses: any[] = [];

    if (Array.isArray(results)) {
      for (let i = 0; i < results.length; i++) {
        const result = results[i];
        if (result.code === 200) {
          try {
            responses.push(JSON.parse(result.body));
          } catch {
            responses.push(result.body);
          }
        } else {
          // Error in batch item
          responses.push({
            error: {
              message: result.body,
              code: result.code,
            },
          });
        }
      }
    }

    return responses;

  } catch (error: any) {
    console.error('[BatchExecutor] Batch API error:', error.message);
    throw error;
  }
}

/**
 * Process pending changes in batches
 */
export async function processBatchChanges(
  pool: Pool,
  workerId: string,
  batchSize: number = BATCH_SIZE
): Promise<number> {
  const client = await pool.connect();

  try {
    // Claim a batch of pending changes
    // If batch function doesn't exist, claim individually
    let result;
    try {
      result = await client.query(
        `SELECT * FROM claim_pending_ad_changes_batch($1, $2)`,
        [workerId, batchSize]
      );
    } catch (error: any) {
      // Fallback: claim individually if batch function doesn't exist
      if (error.message.includes('does not exist') || error.message.includes('function')) {
        console.log(`[BatchExecutor] Batch function not found, claiming individually...`);
        const changes: PendingAdChange[] = [];
        for (let i = 0; i < batchSize; i++) {
          const singleResult = await client.query(
            `SELECT * FROM claim_pending_ad_change($1)`,
            [workerId]
          );
          if (singleResult.rows.length === 0) {
            break; // No more changes
          }
          changes.push(singleResult.rows[0]);
        }
        result = { rows: changes };
      } else {
        throw error;
      }
    }

    if (result.rows.length === 0) {
      return 0;
    }

    const changes: PendingAdChange[] = result.rows;
    console.log(`[BatchExecutor] Claimed ${changes.length} changes for batch processing`);

    // Apply fuzzy budgets
    const fuzzyBudgets = new Map<number, number>();
    for (const change of changes) {
      if (change.change_type === 'BUDGET_INCREASE' || change.change_type === 'BUDGET_DECREASE') {
        const requestedBudget = parseFloat(change.new_value.budget);
        const fuzzyBudget = requestedBudget * (1 + (Math.random() * 0.06 - 0.03)); // ±3%
        fuzzyBudgets.set(change.id, fuzzyBudget);
      }
    }

    // Execute batch API call
    const startTime = Date.now();
    const responses = await executeBatchMetaApiCall(changes, fuzzyBudgets);
    const duration = Date.now() - startTime;

    // Update status for each change
    for (let i = 0; i < changes.length; i++) {
      const change = changes[i];
      const response = responses[i];

      if (response && !response.error) {
        await client.query(
          'UPDATE pending_ad_changes SET status = $1, executed_at = NOW() WHERE id = $2',
          ['completed', change.id]
        );

        // Log execution
        await client.query(`
          INSERT INTO ad_change_history (
            tenant_id, campaign_id, ad_id, change_type,
            old_value, new_value, triggered_by, ml_confidence, reason,
            status, execution_duration_ms, meta_response
          ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
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
          'completed',
          duration,
          JSON.stringify(response),
        ]);
      } else {
        await client.query(
          'UPDATE pending_ad_changes SET status = $1 WHERE id = $2',
          ['failed', change.id]
        );
      }
    }

    console.log(
      `[BatchExecutor] Processed ${changes.length} changes in ${duration}ms ` +
      `(${(changes.length / (duration / 1000)).toFixed(1)} changes/sec)`
    );

    return changes.length;

  } finally {
    client.release();
  }
}

