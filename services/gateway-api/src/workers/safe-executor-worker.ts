/**
 * SafeExecutor Worker Entry Point
 * Runs as a separate process/container for background job processing
 */

import { startSafeExecutor } from '../jobs/safe-executor';

// Start the worker
startSafeExecutor().catch((error) => {
  console.error('[SafeExecutor Worker] Fatal error:', error);
  process.exit(1);
});

