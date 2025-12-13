/**
 * Monitoring & Observability Module
 *
 * This module provides comprehensive monitoring capabilities including:
 * - Prometheus metrics collection
 * - Health check endpoints
 * - Distributed tracing with OpenTelemetry
 *
 * Usage:
 *
 * ```typescript
 * import { metricsMiddleware, checkHealth } from './monitoring';
 *
 * // Add to Express app
 * app.use(metricsMiddleware);
 *
 * // Health check endpoint
 * app.get('/health', async (req, res) => {
 *   const health = await checkHealth();
 *   res.json(health);
 * });
 * ```
 */

// Re-export all monitoring functionality
export * from './metrics';
export * from './health';
export * from './tracing';
