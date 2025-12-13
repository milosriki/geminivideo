/**
 * Comprehensive Health Check System
 * Agent 20: Health Check System
 * Created: 2025-12-13
 *
 * Features:
 * - Database connectivity check
 * - ML Service health verification
 * - RAG Service status
 * - Meta API connectivity
 * - Redis availability
 * - Winner metrics (24h count, ROI improvement)
 * - Error rate monitoring
 */

import { Request, Response, Router } from 'express';
import { Pool } from 'pg';
import Redis from 'ioredis';
import axios from 'axios';

// ============================================================================
// Types
// ============================================================================

export interface ServiceCheck {
  name: string;
  status: 'ok' | 'degraded' | 'error';
  latency?: number;
  details?: Record<string, any>;
  error?: string;
}

export interface MetricsCheck {
  winners_detected_24h: number;
  roi_improvement: number;
  error_rate: number;
  avg_response_time_ms: number;
  cache_hit_rate: number;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  services: ServiceCheck[];
  metrics: MetricsCheck;
  circuit_breakers: Record<string, string>;
}

export interface ReadinessResponse {
  ready: boolean;
  timestamp: string;
  details: {
    database: boolean;
    essential_services: boolean;
  };
}

export interface LivenessResponse {
  alive: boolean;
  timestamp: string;
  uptime: number;
}

// ============================================================================
// Configuration
// ============================================================================

const SERVICE_URLS = {
  ml_service: process.env.ML_SERVICE_URL || 'http://localhost:8081',
  rag_service: process.env.RAG_SERVICE_URL || 'http://localhost:8082',
  meta_publisher: process.env.META_PUBLISHER_URL || 'http://localhost:8083',
  video_agent: process.env.VIDEO_AGENT_URL || 'http://localhost:8084',
  titan_core: process.env.TITAN_CORE_URL || 'http://localhost:8085'
};

const HEALTH_CHECK_TIMEOUT = 5000; // 5 seconds

// ============================================================================
// State
// ============================================================================

let dbPool: Pool | null = null;
let redisClient: Redis | null = null;
let metricsStore = {
  requestCount: 0,
  errorCount: 0,
  totalResponseTime: 0,
  cacheHits: 0,
  cacheMisses: 0,
  winnersDetected24h: 0,
  roiImprovement: 0
};

// Circuit breaker states (would come from actual circuit breakers)
let circuitBreakerStates: Record<string, string> = {
  meta_api: 'closed',
  hubspot_api: 'closed',
  google_api: 'closed'
};

// ============================================================================
// Initialize
// ============================================================================

export function setDatabasePool(pool: Pool): void {
  dbPool = pool;
}

export function setRedisClient(client: Redis): void {
  redisClient = client;
}

export function updateMetrics(update: Partial<typeof metricsStore>): void {
  metricsStore = { ...metricsStore, ...update };
}

export function updateCircuitBreaker(service: string, state: string): void {
  circuitBreakerStates[service] = state;
}

export function recordRequest(responseTime: number, isError: boolean): void {
  metricsStore.requestCount++;
  metricsStore.totalResponseTime += responseTime;
  if (isError) {
    metricsStore.errorCount++;
  }
}

export function recordCacheOperation(hit: boolean): void {
  if (hit) {
    metricsStore.cacheHits++;
  } else {
    metricsStore.cacheMisses++;
  }
}

// ============================================================================
// Service Checks
// ============================================================================

async function checkDatabase(): Promise<ServiceCheck> {
  const start = Date.now();

  try {
    if (!dbPool) {
      return {
        name: 'database',
        status: 'error',
        error: 'Database pool not initialized'
      };
    }

    await dbPool.query('SELECT 1');
    const latency = Date.now() - start;

    return {
      name: 'database',
      status: latency < 1000 ? 'ok' : 'degraded',
      latency,
      details: {
        type: 'postgresql',
        connected: true,
        poolSize: (dbPool as any).totalCount || 'unknown'
      }
    };
  } catch (error) {
    return {
      name: 'database',
      status: 'error',
      latency: Date.now() - start,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

async function checkRedis(): Promise<ServiceCheck> {
  const start = Date.now();

  try {
    if (!redisClient) {
      return {
        name: 'redis',
        status: 'degraded',
        details: { message: 'Redis not configured (optional)' }
      };
    }

    await redisClient.ping();
    const latency = Date.now() - start;

    return {
      name: 'redis',
      status: latency < 500 ? 'ok' : 'degraded',
      latency,
      details: { connected: true }
    };
  } catch (error) {
    return {
      name: 'redis',
      status: 'degraded', // Redis is optional
      latency: Date.now() - start,
      error: error instanceof Error ? error.message : 'Unknown error',
      details: { optional: true }
    };
  }
}

async function checkExternalService(
  name: string,
  url: string
): Promise<ServiceCheck> {
  const start = Date.now();

  try {
    const response = await axios.get(`${url}/health`, {
      timeout: HEALTH_CHECK_TIMEOUT
    });

    const latency = Date.now() - start;

    return {
      name,
      status: response.status === 200 ? 'ok' : 'degraded',
      latency,
      details: {
        statusCode: response.status,
        response: response.data?.status || 'unknown'
      }
    };
  } catch (error) {
    return {
      name,
      status: 'error',
      latency: Date.now() - start,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

async function checkMLService(): Promise<ServiceCheck> {
  return checkExternalService('ml_service', SERVICE_URLS.ml_service);
}

async function checkRAGService(): Promise<ServiceCheck> {
  return checkExternalService('rag_service', SERVICE_URLS.rag_service);
}

async function checkMetaAPI(): Promise<ServiceCheck> {
  const start = Date.now();

  try {
    // Check if Meta API credentials are configured
    const metaToken = process.env.META_ACCESS_TOKEN;

    if (!metaToken) {
      return {
        name: 'meta_api',
        status: 'degraded',
        details: { message: 'Meta API token not configured' }
      };
    }

    // Check meta-publisher service
    const response = await axios.get(
      `${SERVICE_URLS.meta_publisher}/health`,
      { timeout: HEALTH_CHECK_TIMEOUT }
    );

    const latency = Date.now() - start;

    return {
      name: 'meta_api',
      status: response.status === 200 ? 'ok' : 'degraded',
      latency,
      details: {
        configured: true,
        circuitBreaker: circuitBreakerStates.meta_api
      }
    };
  } catch (error) {
    return {
      name: 'meta_api',
      status: 'degraded',
      latency: Date.now() - start,
      error: error instanceof Error ? error.message : 'Unknown error',
      details: {
        circuitBreaker: circuitBreakerStates.meta_api
      }
    };
  }
}

// ============================================================================
// Metrics Calculation
// ============================================================================

function calculateMetrics(): MetricsCheck {
  const totalRequests = metricsStore.requestCount || 1;
  const totalCacheOps = metricsStore.cacheHits + metricsStore.cacheMisses || 1;

  return {
    winners_detected_24h: metricsStore.winnersDetected24h,
    roi_improvement: metricsStore.roiImprovement,
    error_rate: (metricsStore.errorCount / totalRequests) * 100,
    avg_response_time_ms: metricsStore.totalResponseTime / totalRequests,
    cache_hit_rate: (metricsStore.cacheHits / totalCacheOps) * 100
  };
}

// ============================================================================
// Health Check Handlers
// ============================================================================

export async function checkHealth(): Promise<HealthResponse> {
  // Run all checks in parallel
  const [
    dbCheck,
    redisCheck,
    mlCheck,
    ragCheck,
    metaCheck
  ] = await Promise.all([
    checkDatabase(),
    checkRedis(),
    checkMLService(),
    checkRAGService(),
    checkMetaAPI()
  ]);

  const services = [dbCheck, redisCheck, mlCheck, ragCheck, metaCheck];
  const metrics = calculateMetrics();

  // Determine overall status
  const hasError = services.some(s => s.status === 'error');
  const hasDegraded = services.some(s => s.status === 'degraded');

  // Database is critical - if it's down, system is unhealthy
  const databaseOk = dbCheck.status !== 'error';

  let overallStatus: 'healthy' | 'degraded' | 'unhealthy';
  if (!databaseOk || hasError) {
    overallStatus = 'unhealthy';
  } else if (hasDegraded) {
    overallStatus = 'degraded';
  } else {
    overallStatus = 'healthy';
  }

  return {
    status: overallStatus,
    timestamp: new Date().toISOString(),
    uptime: Math.round(process.uptime()),
    version: process.env.npm_package_version || '1.0.0',
    services,
    metrics,
    circuit_breakers: circuitBreakerStates
  };
}

export async function checkReadiness(): Promise<ReadinessResponse> {
  const dbCheck = await checkDatabase();
  const databaseReady = dbCheck.status !== 'error';

  // Check at least ML service is up
  const mlCheck = await checkMLService();
  const essentialServicesReady = mlCheck.status !== 'error';

  return {
    ready: databaseReady && essentialServicesReady,
    timestamp: new Date().toISOString(),
    details: {
      database: databaseReady,
      essential_services: essentialServicesReady
    }
  };
}

export function checkLiveness(): LivenessResponse {
  return {
    alive: true,
    timestamp: new Date().toISOString(),
    uptime: Math.round(process.uptime())
  };
}

// ============================================================================
// Express Router
// ============================================================================

export function createHealthRouter(): Router {
  const router = Router();

  /**
   * GET /health
   * Full health check with all service statuses
   */
  router.get('/health', async (req: Request, res: Response) => {
    try {
      const health = await checkHealth();
      const statusCode = health.status === 'healthy' ? 200 :
                         health.status === 'degraded' ? 200 : 503;
      res.status(statusCode).json(health);
    } catch (error) {
      res.status(503).json({
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Health check failed'
      });
    }
  });

  /**
   * GET /health/ready
   * Readiness probe for Kubernetes/Cloud Run
   */
  router.get('/health/ready', async (req: Request, res: Response) => {
    try {
      const readiness = await checkReadiness();
      res.status(readiness.ready ? 200 : 503).json(readiness);
    } catch (error) {
      res.status(503).json({
        ready: false,
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Readiness check failed'
      });
    }
  });

  /**
   * GET /health/live
   * Liveness probe for Kubernetes/Cloud Run
   */
  router.get('/health/live', (req: Request, res: Response) => {
    const liveness = checkLiveness();
    res.status(200).json(liveness);
  });

  /**
   * GET /health/metrics
   * Business metrics summary
   */
  router.get('/health/metrics', (req: Request, res: Response) => {
    const metrics = calculateMetrics();
    res.status(200).json({
      success: true,
      metrics,
      timestamp: new Date().toISOString()
    });
  });

  /**
   * GET /health/services
   * Detailed service status
   */
  router.get('/health/services', async (req: Request, res: Response) => {
    try {
      const health = await checkHealth();
      res.status(200).json({
        success: true,
        services: health.services,
        circuit_breakers: health.circuit_breakers,
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        error: error instanceof Error ? error.message : 'Service check failed'
      });
    }
  });

  return router;
}

export default {
  checkHealth,
  checkReadiness,
  checkLiveness,
  createHealthRouter,
  setDatabasePool,
  setRedisClient,
  updateMetrics,
  updateCircuitBreaker,
  recordRequest,
  recordCacheOperation
};
