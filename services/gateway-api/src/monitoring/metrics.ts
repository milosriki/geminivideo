import { Registry, Counter, Histogram, Gauge, collectDefaultMetrics } from 'prom-client';
import { Request, Response, NextFunction } from 'express';

export const register = new Registry();

// Collect default Node.js metrics
collectDefaultMetrics({ register });

// Custom metrics
export const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
  registers: [register],
});

export const httpRequestTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register],
});

export const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  registers: [register],
});

// Business metrics
export const adsProcessed = new Counter({
  name: 'ads_processed_total',
  help: 'Total number of ads processed',
  labelNames: ['status', 'account_id'],
  registers: [register],
});

export const videoGenerationTotal = new Counter({
  name: 'video_generation_total',
  help: 'Total number of video generation requests',
  labelNames: ['status', 'model'],
  registers: [register],
});

export const apiLatency = new Histogram({
  name: 'api_latency_seconds',
  help: 'API endpoint latency in seconds',
  labelNames: ['endpoint', 'method'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 2, 5, 10],
  registers: [register],
});

export const cacheHitRate = new Counter({
  name: 'cache_operations_total',
  help: 'Total number of cache operations',
  labelNames: ['operation', 'result'], // hit, miss, error
  registers: [register],
});

export const databaseQueryDuration = new Histogram({
  name: 'database_query_duration_seconds',
  help: 'Database query duration in seconds',
  labelNames: ['query_type'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
  registers: [register],
});

export const activeJobs = new Gauge({
  name: 'active_jobs',
  help: 'Number of active background jobs',
  labelNames: ['job_type'],
  registers: [register],
});

export const errorTotal = new Counter({
  name: 'errors_total',
  help: 'Total number of errors',
  labelNames: ['type', 'endpoint'],
  registers: [register],
});

// Middleware to track HTTP metrics
export function metricsMiddleware(req: Request, res: Response, next: NextFunction) {
  const start = Date.now();
  const end = httpRequestDuration.startTimer();

  // Increment active connections
  activeConnections.inc();

  // Track when response finishes
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route?.path || req.path;
    const method = req.method;
    const statusCode = res.statusCode;

    // Record metrics
    end({ method, route, status_code: statusCode });
    httpRequestTotal.inc({ method, route, status_code: statusCode });

    // Decrement active connections
    activeConnections.dec();

    // Track errors
    if (statusCode >= 400) {
      errorTotal.inc({
        type: statusCode >= 500 ? 'server_error' : 'client_error',
        endpoint: route
      });
    }
  });

  next();
}

// Helper function to get all metrics
export async function getMetrics(): Promise<string> {
  return register.metrics();
}

// Helper function to record business metrics
export const recordAdProcessed = (status: string, accountId: string) => {
  adsProcessed.inc({ status, account_id: accountId });
};

export const recordVideoGeneration = (status: string, model: string) => {
  videoGenerationTotal.inc({ status, model });
};

export const recordCacheOperation = (operation: 'get' | 'set' | 'del', result: 'hit' | 'miss' | 'error') => {
  cacheHitRate.inc({ operation, result });
};

export const recordDatabaseQuery = async <T>(queryType: string, queryFn: () => Promise<T>): Promise<T> => {
  const end = databaseQueryDuration.startTimer({ query_type: queryType });
  try {
    return await queryFn();
  } finally {
    end();
  }
};
