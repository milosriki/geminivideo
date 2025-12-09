/**
 * Self-Learning Cycle Background Worker
 * Orchestrates all 7 learning loops based on learning_config.yaml
 * 
 * Agent 6: Self-Learning Loop Orchestrator
 */

import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { Pool } from 'pg';
import axios, { AxiosRequestConfig } from 'axios';

// Load configuration
const configPath = process.env.CONFIG_PATH || '../../shared/config';
let learningConfig: any = {};

try {
  const configFile = fs.readFileSync(
    path.join(configPath, 'learning_config.yaml'),
    'utf8'
  );
  learningConfig = yaml.load(configFile) as any;
} catch (error) {
  console.error('Failed to load learning_config.yaml:', error);
  // Use defaults
  learningConfig = {
    self_learning_cycle: {
      enabled: true,
      interval_seconds: 3600,
      loops: {}
    }
  };
}

const config = learningConfig.self_learning_cycle || {};
const isEnabled = config.enabled !== false;
const intervalSeconds = config.interval_seconds || 3600;
const loops = config.loops || {};
const continueOnError = config.continue_on_error !== false;
const maxRetries = config.max_retries || 3;
const retryDelaySeconds = config.retry_delay_seconds || 60;

// Service URLs
const ML_SERVICE_URL = process.env.ML_SERVICE_URL || 'http://localhost:8003';
const RAG_SERVICE_URL = process.env.RAG_SERVICE_URL || 'http://localhost:8005';

// HTTP client with timeout
const httpClient = axios.create({
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
});

/**
 * Execute a single learning loop
 */
async function executeLoop(
  loopName: string,
  loopConfig: any,
  pgPool: Pool
): Promise<{ success: boolean; duration: number; error?: string }> {
  const startTime = Date.now();
  const timeout = (loopConfig.timeout_seconds || 300) * 1000;
  
  try {
    console.log(`[Self-Learning] Starting loop: ${loopName}`);
    
    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error(`Timeout after ${timeout}ms`)), timeout);
    });
    
    // Execute loop based on name
    const loopPromise = (async () => {
      switch (loopName) {
        case 'rag_winner_index':
          return await executeRAGWinnerIndex(pgPool);
        
        case 'thompson_sampling':
          return await executeThompsonSampling(pgPool);
        
        case 'cross_learner':
          return await executeCrossLearner(pgPool);
        
        case 'creative_dna':
          return await executeCreativeDNA(pgPool);
        
        case 'compound_learner':
          return await executeCompoundLearner(pgPool);
        
        case 'actuals_fetcher':
          return await executeActualsFetcher(pgPool);
        
        case 'auto_promoter':
          return await executeAutoPromoter(pgPool);
        
        default:
          console.warn(`[Self-Learning] Unknown loop: ${loopName}`);
          return { success: false, error: 'Unknown loop' };
      }
    })();
    
    // Race between execution and timeout
    const result = await Promise.race([loopPromise, timeoutPromise]);
    
    const duration = Date.now() - startTime;
    console.log(`[Self-Learning] Loop ${loopName} completed in ${duration}ms`);
    
    return { success: true, duration };
    
  } catch (error: any) {
    const duration = Date.now() - startTime;
    console.error(`[Self-Learning] Loop ${loopName} failed after ${duration}ms:`, error.message);
    return { success: false, duration, error: error.message };
  }
}

/**
 * RAG Winner Index Loop
 */
async function executeRAGWinnerIndex(pgPool: Pool): Promise<any> {
  // Find winners that haven't been indexed
  const query = `
    SELECT ad_id, creative_dna, ctr, roas, impressions
    FROM ads
    WHERE ctr >= $1
      AND roas >= $2
      AND impressions >= $3
      AND indexed_to_rag = false
    LIMIT 10
  `;
  
  const winnerThreshold = learningConfig.winner_detection || {};
  const results = await pgPool.query(query, [
    winnerThreshold.ctr_threshold || 0.03,
    winnerThreshold.roas_threshold || 3.0,
    winnerThreshold.min_impressions || 1000
  ]);
  
  if (results.rows.length === 0) {
    return { indexed: 0, message: 'No new winners to index' };
  }
  
  // Index each winner
  let indexed = 0;
  for (const row of results.rows) {
    try {
      await httpClient.post(`${RAG_SERVICE_URL}/api/rag/index-winner`, {
        ad_id: row.ad_id,
        creative_dna: row.creative_dna,
        ctr: row.ctr,
        roas: row.roas
      });
      
      // Mark as indexed
      await pgPool.query(
        'UPDATE ads SET indexed_to_rag = true WHERE ad_id = $1',
        [row.ad_id]
      );
      
      indexed++;
    } catch (error: any) {
      console.error(`Failed to index winner ${row.ad_id}:`, error.message);
    }
  }
  
  return { indexed, total: results.rows.length };
}

/**
 * Thompson Sampling Loop
 */
async function executeThompsonSampling(pgPool: Pool): Promise<any> {
  // Trigger Thompson sampling update
  try {
    const response = await httpClient.post(`${ML_SERVICE_URL}/api/ml/thompson/update`);
    return response.data;
  } catch (error: any) {
    throw new Error(`Thompson sampling failed: ${error.message}`);
  }
}

/**
 * Cross-Learner Loop
 */
async function executeCrossLearner(pgPool: Pool): Promise<any> {
  // Trigger cross-learner training
  try {
    const response = await httpClient.post(`${ML_SERVICE_URL}/api/ml/cross-learner/train`);
    return response.data;
  } catch (error: any) {
    throw new Error(`Cross-learner failed: ${error.message}`);
  }
}

/**
 * Creative DNA Loop
 */
async function executeCreativeDNA(pgPool: Pool): Promise<any> {
  // Trigger Creative DNA extraction
  try {
    const response = await httpClient.post(`${ML_SERVICE_URL}/api/ml/dna/extract`);
    return response.data;
  } catch (error: any) {
    throw new Error(`Creative DNA failed: ${error.message}`);
  }
}

/**
 * Compound Learner Loop
 */
async function executeCompoundLearner(pgPool: Pool): Promise<any> {
  // Trigger compound learner training
  try {
    const response = await httpClient.post(`${ML_SERVICE_URL}/api/ml/compound/train`);
    return response.data;
  } catch (error: any) {
    throw new Error(`Compound learner failed: ${error.message}`);
  }
}

/**
 * Actuals Fetcher Loop
 */
async function executeActualsFetcher(pgPool: Pool): Promise<any> {
  // Fetch actual performance from Meta API
  try {
    const response = await httpClient.post(`${ML_SERVICE_URL}/api/ml/actuals/fetch`);
    return response.data;
  } catch (error: any) {
    throw new Error(`Actuals fetcher failed: ${error.message}`);
  }
}

/**
 * Auto-Promoter Loop
 */
async function executeAutoPromoter(pgPool: Pool): Promise<any> {
  // Trigger auto-promoter (scale winners, kill losers)
  try {
    const response = await httpClient.post(`${ML_SERVICE_URL}/api/ml/auto-promoter/run`);
    return response.data;
  } catch (error: any) {
    throw new Error(`Auto-promoter failed: ${error.message}`);
  }
}

/**
 * Main self-learning cycle orchestrator
 */
export async function runSelfLearningCycle(pgPool: Pool): Promise<void> {
  if (!isEnabled) {
    console.log('[Self-Learning] Cycle disabled in config');
    return;
  }
  
  console.log(`[Self-Learning] Starting cycle (interval: ${intervalSeconds}s)`);
  
  // Sort loops by priority
  const sortedLoops = Object.entries(loops)
    .filter(([_, config]: [string, any]) => config.enabled !== false)
    .sort(([_, a]: [string, any], [__, b]: [string, any]) => 
      (a.priority || 999) - (b.priority || 999)
    );
  
  const results: Record<string, any> = {};
  
  // Execute loops in priority order
  for (const [loopName, loopConfig] of sortedLoops) {
    let retries = 0;
    let result: any = null;
    
    while (retries < maxRetries) {
      result = await executeLoop(loopName, loopConfig, pgPool);
      
      if (result.success) {
        results[loopName] = result;
        break;
      }
      
      retries++;
      if (retries < maxRetries) {
        console.log(`[Self-Learning] Retrying ${loopName} (${retries}/${maxRetries})...`);
        await new Promise(resolve => setTimeout(resolve, retryDelaySeconds * 1000));
      }
    }
    
    if (!result.success) {
      results[loopName] = result;
      if (!continueOnError) {
        console.error(`[Self-Learning] Stopping cycle due to ${loopName} failure`);
        break;
      }
    }
  }
  
  console.log(`[Self-Learning] Cycle completed:`, results);
}

/**
 * Start the self-learning cycle worker
 */
export function startSelfLearningCycleWorker(pgPool: Pool): NodeJS.Timeout {
  if (!isEnabled) {
    console.log('[Self-Learning] Worker disabled in config');
    return setInterval(() => {}, 60000); // Dummy interval
  }
  
  // Run immediately on start
  runSelfLearningCycle(pgPool).catch(err => {
    console.error('[Self-Learning] Initial cycle failed:', err);
  });
  
  // Then run on interval
  const interval = setInterval(() => {
    runSelfLearningCycle(pgPool).catch(err => {
      console.error('[Self-Learning] Cycle failed:', err);
    });
  }, intervalSeconds * 1000);
  
  console.log(`[Self-Learning] Worker started (interval: ${intervalSeconds}s)`);
  
  return interval;
}

