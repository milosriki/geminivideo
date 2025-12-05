/**
 * ROAS Dashboard Integration - Agent 14
 *
 * To integrate the ROAS dashboard into the gateway API, add the following lines to index.ts:
 *
 * 1. Add import at the top (around line 19):
 *    import { initializeROASRoutes } from './routes/roas-dashboard';
 *
 * 2. Add route mounting after other routes are defined (around line 1575, before health check):
 *    // ROAS Tracking Dashboard Routes
 *    app.use('/api/roas', initializeROASRoutes(pgPool));
 *
 * This will enable all ROAS dashboard endpoints:
 * - GET /api/roas/dashboard - Full dashboard data
 * - GET /api/roas/campaigns - Campaign performance
 * - GET /api/roas/metrics - Real-time metrics
 */

import { Express } from 'express';
import { Pool } from 'pg';
import { initializeROASRoutes } from './routes/roas-dashboard';

/**
 * Mount ROAS dashboard routes to the Express app
 */
export function mountROASRoutes(app: Express, pgPool: Pool): void {
  console.log('[ROAS] Mounting ROAS dashboard routes at /api/roas');
  app.use('/api/roas', initializeROASRoutes(pgPool));
  console.log('[ROAS] ROAS dashboard routes mounted successfully');
}
