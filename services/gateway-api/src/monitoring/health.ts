import { createClient } from 'redis';
import { Pool } from 'pg';

interface HealthCheck {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  latency?: number;
  details?: Record<string, any>;
}

interface HealthResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  timestamp: string;
  uptime: number;
  checks: HealthCheck[];
  version?: string;
}

// Database connection pool (singleton)
let dbPool: Pool | null = null;

export function setDatabasePool(pool: Pool) {
  dbPool = pool;
}

// Redis client (singleton)
let redisClient: ReturnType<typeof createClient> | null = null;

export function setRedisClient(client: ReturnType<typeof createClient>) {
  redisClient = client;
}

// Check database connectivity
async function checkDatabase(): Promise<HealthCheck> {
  const start = Date.now();

  try {
    if (!dbPool) {
      return {
        name: 'database',
        status: 'unhealthy',
        details: { error: 'Database pool not initialized' }
      };
    }

    // Simple query to check connection
    await dbPool.query('SELECT 1');

    const latency = Date.now() - start;

    return {
      name: 'database',
      status: latency < 1000 ? 'healthy' : 'degraded',
      latency,
      details: {
        type: 'postgresql',
        connected: true
      }
    };
  } catch (error: any) {
    return {
      name: 'database',
      status: 'unhealthy',
      latency: Date.now() - start,
      details: {
        error: error.message
      }
    };
  }
}

// Check Redis connectivity
async function checkRedis(): Promise<HealthCheck> {
  const start = Date.now();

  try {
    if (!redisClient) {
      return {
        name: 'redis',
        status: 'degraded',
        details: { error: 'Redis client not initialized (optional)' }
      };
    }

    // Simple ping to check connection
    await redisClient.ping();

    const latency = Date.now() - start;

    return {
      name: 'redis',
      status: latency < 500 ? 'healthy' : 'degraded',
      latency,
      details: {
        connected: true
      }
    };
  } catch (error: any) {
    return {
      name: 'redis',
      status: 'degraded', // Redis is optional, so degraded not unhealthy
      latency: Date.now() - start,
      details: {
        error: error.message,
        optional: true
      }
    };
  }
}

// Check Meta API connectivity
async function checkMetaApi(): Promise<HealthCheck> {
  const start = Date.now();

  try {
    // Check if Meta API credentials are configured
    const metaToken = process.env.META_ACCESS_TOKEN;

    if (!metaToken) {
      return {
        name: 'meta_api',
        status: 'degraded',
        details: { error: 'Meta API token not configured' }
      };
    }

    // Just check if token is present, don't make actual API call
    // In production, you might want to make a lightweight API call
    const latency = Date.now() - start;

    return {
      name: 'meta_api',
      status: 'healthy',
      latency,
      details: {
        configured: true
      }
    };
  } catch (error: any) {
    return {
      name: 'meta_api',
      status: 'degraded',
      latency: Date.now() - start,
      details: {
        error: error.message
      }
    };
  }
}

// Check Gemini API connectivity
async function checkGeminiApi(): Promise<HealthCheck> {
  const start = Date.now();

  try {
    const geminiKey = process.env.GEMINI_API_KEY;

    if (!geminiKey) {
      return {
        name: 'gemini_api',
        status: 'degraded',
        details: { error: 'Gemini API key not configured' }
      };
    }

    const latency = Date.now() - start;

    return {
      name: 'gemini_api',
      status: 'healthy',
      latency,
      details: {
        configured: true
      }
    };
  } catch (error: any) {
    return {
      name: 'gemini_api',
      status: 'degraded',
      latency: Date.now() - start,
      details: {
        error: error.message
      }
    };
  }
}

// Check system resources
function checkSystemResources(): HealthCheck {
  const start = Date.now();

  try {
    const memUsage = process.memoryUsage();
    const memUsedMB = Math.round(memUsage.heapUsed / 1024 / 1024);
    const memTotalMB = Math.round(memUsage.heapTotal / 1024 / 1024);
    const memUsagePercent = (memUsedMB / memTotalMB) * 100;

    const cpuUsage = process.cpuUsage();

    const status = memUsagePercent > 90 ? 'degraded' : 'healthy';

    return {
      name: 'system_resources',
      status,
      latency: Date.now() - start,
      details: {
        memory: {
          used_mb: memUsedMB,
          total_mb: memTotalMB,
          usage_percent: Math.round(memUsagePercent)
        },
        cpu: {
          user: cpuUsage.user,
          system: cpuUsage.system
        },
        uptime: Math.round(process.uptime())
      }
    };
  } catch (error: any) {
    return {
      name: 'system_resources',
      status: 'degraded',
      latency: Date.now() - start,
      details: {
        error: error.message
      }
    };
  }
}

// Main health check function
export async function checkHealth(): Promise<HealthResponse> {
  const checks: HealthCheck[] = [];

  // Run all health checks in parallel
  const [dbCheck, redisCheck, metaCheck, geminiCheck, systemCheck] = await Promise.all([
    checkDatabase(),
    checkRedis(),
    checkMetaApi(),
    checkGeminiApi(),
    checkSystemResources()
  ]);

  checks.push(dbCheck, redisCheck, metaCheck, geminiCheck, systemCheck);

  // Determine overall status
  const hasUnhealthy = checks.some(c => c.status === 'unhealthy');
  const hasDegraded = checks.some(c => c.status === 'degraded');

  let overallStatus: 'healthy' | 'unhealthy' | 'degraded';
  if (hasUnhealthy) {
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
    checks,
    version: process.env.npm_package_version || '1.0.0'
  };
}

// Readiness check (is the service ready to accept traffic?)
export async function checkReadiness(): Promise<{ ready: boolean; details: any }> {
  try {
    const dbCheck = await checkDatabase();

    // Service is ready if database is healthy
    const ready = dbCheck.status === 'healthy';

    return {
      ready,
      details: {
        database: dbCheck
      }
    };
  } catch (error: any) {
    return {
      ready: false,
      details: {
        error: error.message
      }
    };
  }
}

// Liveness check (is the service alive?)
export function checkLiveness(): { alive: boolean; timestamp: string; uptime: number } {
  return {
    alive: true,
    timestamp: new Date().toISOString(),
    uptime: Math.round(process.uptime())
  };
}
