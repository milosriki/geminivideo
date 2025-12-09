/**
 * Self-Learning Cycle Worker
 *
 * Orchestrates all 7 self-learning loops:
 * 1. RAG Winner Index - Indexes winning ads into memory
 * 2. Thompson Sampling - Updates exploration/exploitation metrics
 * 3. Cross Learner - Extracts insights across accounts
 * 4. Creative DNA - Extracts DNA from high-performing creatives
 * 5. Compound Learner - Runs compound learning cycle
 * 6. Actuals Fetcher - Fetches actual performance data
 * 7. Auto Promoter - Auto-promotes high-performing experiments
 *
 * Should run every hour via cron
 */

import axios from 'axios';
import { Pool } from 'pg';

const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://ml-service:8003';
const REQUEST_TIMEOUT = 60000; // 60 seconds

interface SelfLearningCycleResult {
  success: boolean;
  loops_executed: string[];
  loops_failed: string[];
  timestamp: string;
  details: any;
}

/**
 * Loop 1: RAG Winner Index
 * Indexes winning ads (CTR > 3%) into persistent RAG memory
 */
async function executeRAGWinnerIndex(pgPool: Pool): Promise<any> {
  try {
    console.log('[RAG Winner Index] Starting...');

    // Fetch recent winning ads from database
    const query = `
      SELECT
        ad_id,
        asset_id,
        arc_name,
        predicted_ctr,
        predicted_roas,
        actual_ctr,
        actual_roas,
        conversions,
        spend
      FROM ads
      WHERE actual_ctr > 0.03
        AND actual_ctr IS NOT NULL
        AND created_at > NOW() - INTERVAL '7 days'
      ORDER BY actual_ctr DESC
      LIMIT 10
    `;

    const result = await pgPool.query(query);
    const winners = result.rows;

    console.log(`[RAG Winner Index] Found ${winners.length} winning ads to index`);

    // Index each winner
    let indexed = 0;
    for (const winner of winners) {
      try {
        const response = await axios.post(`${ML_SERVICE_URL}/api/ml/rag/index-winner`, {
          ad_id: winner.ad_id,
          ad_data: {
            asset_id: winner.asset_id,
            arc_name: winner.arc_name,
            predicted_ctr: winner.predicted_ctr,
            predicted_roas: winner.predicted_roas
          },
          ctr: winner.actual_ctr,
          roas: winner.actual_roas || 0,
          conversions: winner.conversions || 0,
          spend: winner.spend || 0
        }, { timeout: REQUEST_TIMEOUT });

        if (response.data.status !== 'skipped') {
          indexed++;
        }
      } catch (error: any) {
        console.error(`[RAG Winner Index] Error indexing ad ${winner.ad_id}:`, error.message);
      }
    }

    console.log(`[RAG Winner Index] Successfully indexed ${indexed} winners`);
    return { indexed, total: winners.length };

  } catch (error: any) {
    console.error(`[RAG Winner Index] Error: ${error.message}`);
    throw error;
  }
}

/**
 * Loop 2: Thompson Sampling
 * Updates Thompson sampling metrics for active variants
 */
async function executeThompsonSampling(pgPool: Pool): Promise<any> {
  try {
    console.log('[Thompson Sampling] Starting...');

    // Fetch recent ad performance for Thompson sampling updates
    const query = `
      SELECT
        ad_id,
        impressions,
        conversions
      FROM ads
      WHERE status = 'active'
        AND updated_at > NOW() - INTERVAL '1 hour'
      ORDER BY updated_at DESC
      LIMIT 50
    `;

    const result = await pgPool.query(query);
    const variants = result.rows;

    console.log(`[Thompson Sampling] Found ${variants.length} variants to update`);

    // Update Thompson sampling for each variant
    let updated = 0;
    for (const variant of variants) {
      try {
        await axios.post(`${ML_SERVICE_URL}/api/ml/thompson/impression`, null, {
          params: { variant_id: variant.ad_id },
          timeout: REQUEST_TIMEOUT
        });
        updated++;
      } catch (error: any) {
        console.error(`[Thompson Sampling] Error updating variant ${variant.ad_id}:`, error.message);
      }
    }

    console.log(`[Thompson Sampling] Successfully updated ${updated} variants`);
    return { updated, total: variants.length };

  } catch (error: any) {
    console.error(`[Thompson Sampling] Error: ${error.message}`);
    throw error;
  }
}

/**
 * Loop 3: Cross Learner
 * Extracts anonymized insights across accounts for cross-learning
 */
async function executeCrossLearner(pgPool: Pool): Promise<any> {
  try {
    console.log('[Cross Learner] Starting...');

    // Fetch distinct accounts that have recent activity
    const query = `
      SELECT DISTINCT account_id
      FROM ads
      WHERE account_id IS NOT NULL
        AND created_at > NOW() - INTERVAL '7 days'
      LIMIT 5
    `;

    const result = await pgPool.query(query);
    const accounts = result.rows;

    console.log(`[Cross Learner] Found ${accounts.length} accounts to analyze`);

    // Extract insights from each account
    let extracted = 0;
    for (const account of accounts) {
      try {
        const response = await axios.post(`${ML_SERVICE_URL}/api/cross-learning/extract-insights`, {
          account_id: account.account_id
        }, { timeout: REQUEST_TIMEOUT });

        if (response.data.success) {
          extracted++;
        }
      } catch (error: any) {
        console.error(`[Cross Learner] Error extracting insights for account ${account.account_id}:`, error.message);
      }
    }

    console.log(`[Cross Learner] Successfully extracted insights from ${extracted} accounts`);
    return { extracted, total: accounts.length };

  } catch (error: any) {
    console.error(`[Cross Learner] Error: ${error.message}`);
    throw error;
  }
}

/**
 * Loop 4: Creative DNA
 * Extracts DNA patterns from high-performing creatives
 */
async function executeCreativeDNA(pgPool: Pool): Promise<any> {
  try {
    console.log('[Creative DNA] Starting...');

    // Fetch high-performing creatives (top 10% CTR)
    const query = `
      SELECT DISTINCT asset_id
      FROM ads
      WHERE actual_ctr > 0.05
        AND asset_id IS NOT NULL
        AND created_at > NOW() - INTERVAL '7 days'
      ORDER BY actual_ctr DESC
      LIMIT 10
    `;

    const result = await pgPool.query(query);
    const creatives = result.rows;

    console.log(`[Creative DNA] Found ${creatives.length} high-performing creatives`);

    // Extract DNA from each creative
    let extracted = 0;
    for (const creative of creatives) {
      try {
        const response = await axios.post(`${ML_SERVICE_URL}/api/ml/dna/extract`, {
          creative_id: creative.asset_id
        }, { timeout: REQUEST_TIMEOUT });

        if (response.data.success) {
          extracted++;
        }
      } catch (error: any) {
        console.error(`[Creative DNA] Error extracting DNA from creative ${creative.asset_id}:`, error.message);
      }
    }

    console.log(`[Creative DNA] Successfully extracted DNA from ${extracted} creatives`);
    return { extracted, total: creatives.length };

  } catch (error: any) {
    console.error(`[Creative DNA] Error: ${error.message}`);
    throw error;
  }
}

/**
 * Loop 5: Compound Learner
 * Runs compound learning cycle to track improvement trajectory
 */
async function executeCompoundLearner(pgPool: Pool): Promise<any> {
  try {
    console.log('[Compound Learner] Starting...');

    // Fetch distinct accounts for compound learning
    const query = `
      SELECT DISTINCT account_id
      FROM ads
      WHERE account_id IS NOT NULL
        AND created_at > NOW() - INTERVAL '30 days'
      LIMIT 5
    `;

    const result = await pgPool.query(query);
    const accounts = result.rows;

    console.log(`[Compound Learner] Found ${accounts.length} accounts for learning cycle`);

    // Run learning cycle for each account
    let processed = 0;
    for (const account of accounts) {
      try {
        const response = await axios.post(`${ML_SERVICE_URL}/api/ml/compound/learning-cycle`, {
          account_id: account.account_id
        }, { timeout: REQUEST_TIMEOUT });

        if (response.data.success) {
          processed++;
        }
      } catch (error: any) {
        console.error(`[Compound Learner] Error processing account ${account.account_id}:`, error.message);
      }
    }

    console.log(`[Compound Learner] Successfully processed ${processed} accounts`);
    return { processed, total: accounts.length };

  } catch (error: any) {
    console.error(`[Compound Learner] Error: ${error.message}`);
    throw error;
  }
}

/**
 * Loop 6: Actuals Fetcher
 * Fetches actual performance data from Meta API
 */
async function executeActualsFetcher(pgPool: Pool): Promise<any> {
  try {
    console.log('[Actuals Fetcher] Starting...');

    // Fetch ads that need actuals data (active ads from last 7 days)
    const query = `
      SELECT
        ad_id,
        asset_id as video_id
      FROM ads
      WHERE status = 'active'
        AND actual_ctr IS NULL
        AND created_at > NOW() - INTERVAL '7 days'
      ORDER BY created_at DESC
      LIMIT 20
    `;

    const result = await pgPool.query(query);
    const ads = result.rows;

    console.log(`[Actuals Fetcher] Found ${ads.length} ads needing actuals data`);

    // Fetch actuals for each ad
    let fetched = 0;
    for (const ad of ads) {
      try {
        const response = await axios.post(`${ML_SERVICE_URL}/api/ml/actuals/fetch`, {
          ad_id: ad.ad_id,
          video_id: ad.video_id,
          days_back: 7
        }, { timeout: REQUEST_TIMEOUT });

        if (response.data.success) {
          fetched++;
        }
      } catch (error: any) {
        console.error(`[Actuals Fetcher] Error fetching actuals for ad ${ad.ad_id}:`, error.message);
      }
    }

    console.log(`[Actuals Fetcher] Successfully fetched actuals for ${fetched} ads`);
    return { fetched, total: ads.length };

  } catch (error: any) {
    console.error(`[Actuals Fetcher] Error: ${error.message}`);
    throw error;
  }
}

/**
 * Loop 7: Auto Promoter
 * Auto-promotes high-performing experiments to production
 */
async function executeAutoPromoter(pgPool: Pool): Promise<any> {
  try {
    console.log('[Auto Promoter] Starting...');

    // Fetch experiments that might be ready for promotion
    const query = `
      SELECT
        ad_id as experiment_id,
        actual_ctr,
        actual_roas,
        impressions
      FROM ads
      WHERE status = 'active'
        AND actual_ctr > 0.04
        AND impressions > 1000
        AND created_at > NOW() - INTERVAL '7 days'
      ORDER BY actual_ctr DESC
      LIMIT 10
    `;

    const result = await pgPool.query(query);
    const experiments = result.rows;

    console.log(`[Auto Promoter] Found ${experiments.length} experiments to check for promotion`);

    // Check each experiment for auto-promotion
    let promoted = 0;
    for (const experiment of experiments) {
      try {
        const response = await axios.post(`${ML_SERVICE_URL}/api/ml/auto-promote/check`, {
          experiment_id: experiment.experiment_id,
          force_promotion: false
        }, { timeout: REQUEST_TIMEOUT });

        if (response.data.promoted) {
          promoted++;
        }
      } catch (error: any) {
        console.error(`[Auto Promoter] Error checking experiment ${experiment.experiment_id}:`, error.message);
      }
    }

    console.log(`[Auto Promoter] Successfully promoted ${promoted} experiments`);
    return { promoted, total: experiments.length };

  } catch (error: any) {
    console.error(`[Auto Promoter] Error: ${error.message}`);
    throw error;
  }
}

/**
 * Main Self-Learning Cycle
 * Orchestrates all 7 loops in sequence
 */
export async function runSelfLearningCycle(pgPool: Pool): Promise<SelfLearningCycleResult> {
  console.log('========================================');
  console.log('Starting Self-Learning Cycle');
  console.log('========================================');

  const startTime = Date.now();
  const loopsExecuted: string[] = [];
  const loopsFailed: string[] = [];
  const details: any = {};

  // Execute all 7 loops
  const loops = [
    { name: 'RAG Winner Index', fn: executeRAGWinnerIndex },
    { name: 'Thompson Sampling', fn: executeThompsonSampling },
    { name: 'Cross Learner', fn: executeCrossLearner },
    { name: 'Creative DNA', fn: executeCreativeDNA },
    { name: 'Compound Learner', fn: executeCompoundLearner },
    { name: 'Actuals Fetcher', fn: executeActualsFetcher },
    { name: 'Auto Promoter', fn: executeAutoPromoter }
  ];

  for (const loop of loops) {
    try {
      const result = await loop.fn(pgPool);
      loopsExecuted.push(loop.name);
      details[loop.name] = result;
      console.log(`✓ ${loop.name} completed successfully`);
    } catch (error: any) {
      loopsFailed.push(loop.name);
      details[loop.name] = { error: error.message };
      console.error(`✗ ${loop.name} failed:`, error.message);
    }
  }

  const duration = Date.now() - startTime;

  console.log('========================================');
  console.log(`Self-Learning Cycle Complete (${duration}ms)`);
  console.log(`Success: ${loopsExecuted.length}/${loops.length} loops`);
  console.log('========================================');

  return {
    success: loopsFailed.length === 0,
    loops_executed: loopsExecuted,
    loops_failed: loopsFailed,
    timestamp: new Date().toISOString(),
    details
  };
}

/**
 * Start Self-Learning Cycle Worker
 * Runs cycle on startup and then every hour
 */
export async function startSelfLearningCycleWorker(pgPool: Pool): Promise<void> {
  console.log('[Self-Learning Worker] Starting...');

  // Run immediately on startup
  try {
    await runSelfLearningCycle(pgPool);
  } catch (error: any) {
    console.error('[Self-Learning Worker] Initial cycle failed:', error.message);
  }

  // Schedule to run every hour
  const HOUR_IN_MS = 60 * 60 * 1000;
  setInterval(async () => {
    try {
      await runSelfLearningCycle(pgPool);
    } catch (error: any) {
      console.error('[Self-Learning Worker] Cycle failed:', error.message);
    }
  }, HOUR_IN_MS);

  console.log('[Self-Learning Worker] Scheduled to run every hour');
}
