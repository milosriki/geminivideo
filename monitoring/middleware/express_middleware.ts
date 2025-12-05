/**
 * Express middleware for Prometheus metrics and structured logging.
 *
 * Usage:
 *   import { setupMonitoring } from './monitoring/middleware/express_middleware';
 *
 *   const app = express();
 *   setupMonitoring(app, 'my-service');
 */

import express, { Request, Response, NextFunction, Application } from 'express';
import promClient from 'prom-client';
import winston from 'winston';
import { v4 as uuidv4 } from 'uuid';

// ============================================================================
// PROMETHEUS METRICS
// ============================================================================

const register = new promClient.Registry();

// Collect default metrics (CPU, memory, etc.)
promClient.collectDefaultMetrics({ register });

// HTTP metrics
const httpRequestsTotal = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['service', 'method', 'endpoint', 'status'],
  registers: [register],
});

const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request latency in seconds',
  labelNames: ['service', 'method', 'endpoint'],
  buckets: [0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0],
  registers: [register],
});

const httpRequestSize = new promClient.Summary({
  name: 'http_request_size_bytes',
  help: 'HTTP request size in bytes',
  labelNames: ['service', 'method', 'endpoint'],
  registers: [register],
});

const httpResponseSize = new promClient.Summary({
  name: 'http_response_size_bytes',
  help: 'HTTP response size in bytes',
  labelNames: ['service', 'method', 'endpoint'],
  registers: [register],
});

const httpExceptionsTotal = new promClient.Counter({
  name: 'http_exceptions_total',
  help: 'Total HTTP exceptions',
  labelNames: ['service', 'exception_type'],
  registers: [register],
});

// AI API metrics
const aiApiCallsTotal = new promClient.Counter({
  name: 'ai_api_calls_total',
  help: 'Total AI API calls',
  labelNames: ['service', 'provider', 'model', 'operation'],
  registers: [register],
});

const aiApiTokensTotal = new promClient.Counter({
  name: 'ai_api_tokens_total',
  help: 'Total tokens consumed',
  labelNames: ['service', 'provider', 'model', 'token_type'],
  registers: [register],
});

const aiApiCostTotal = new promClient.Counter({
  name: 'ai_api_cost_total',
  help: 'Total AI API cost in USD',
  labelNames: ['service', 'provider', 'model'],
  registers: [register],
});

const aiApiDuration = new promClient.Histogram({
  name: 'ai_api_duration_seconds',
  help: 'AI API call duration in seconds',
  labelNames: ['service', 'provider', 'model', 'operation'],
  buckets: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0],
  registers: [register],
});

const aiApiErrorsTotal = new promClient.Counter({
  name: 'ai_api_errors_total',
  help: 'Total AI API errors',
  labelNames: ['service', 'provider', 'model', 'error_type'],
  registers: [register],
});

// Service info
const serviceInfo = new promClient.Gauge({
  name: 'service_info',
  help: 'Service information',
  labelNames: ['service', 'version', 'environment'],
  registers: [register],
});

const serviceHealth = new promClient.Gauge({
  name: 'service_health',
  help: 'Service health status (1=healthy, 0=unhealthy)',
  labelNames: ['service'],
  registers: [register],
});

// ============================================================================
// STRUCTURED LOGGING
// ============================================================================

// Sensitive data patterns
const SENSITIVE_PATTERNS = [
  { name: 'credit_card', pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g },
  { name: 'email', pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g },
  { name: 'api_key', pattern: /(api[_-]?key|apikey|access[_-]?token|secret[_-]?key)[\s:=]+['"]?([a-zA-Z0-9_\-]{20,})/gi },
  { name: 'password', pattern: /(password|passwd|pwd)[\s:=]+['"]?([^\s'",]+)/gi },
  { name: 'bearer_token', pattern: /Bearer\s+([A-Za-z0-9\-._~+/]+={0,2})/g },
  { name: 'jwt', pattern: /eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*/g },
];

const SENSITIVE_FIELDS = new Set([
  'password', 'passwd', 'pwd', 'secret', 'api_key', 'apikey', 'access_token',
  'refresh_token', 'private_key', 'client_secret', 'authorization',
  'credit_card', 'ssn', 'social_security', 'cvv', 'pin',
]);

function maskSensitiveData(data: any): any {
  if (typeof data === 'string') {
    let masked = data;
    for (const { pattern } of SENSITIVE_PATTERNS) {
      masked = masked.replace(pattern, '********');
    }
    return masked;
  } else if (Array.isArray(data)) {
    return data.map(maskSensitiveData);
  } else if (typeof data === 'object' && data !== null) {
    const masked: any = {};
    for (const [key, value] of Object.entries(data)) {
      if (SENSITIVE_FIELDS.has(key.toLowerCase())) {
        masked[key] = '********';
      } else {
        masked[key] = maskSensitiveData(value);
      }
    }
    return masked;
  }
  return data;
}

function createLogger(serviceName: string, environment: string = 'production'): winston.Logger {
  return winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format: winston.format.combine(
      winston.format.timestamp({ format: 'YYYY-MM-DDTHH:mm:ss.SSSZ' }),
      winston.format.errors({ stack: true }),
      winston.format.printf((info) => {
        const logData = {
          timestamp: info.timestamp,
          level: info.level,
          service: serviceName,
          environment,
          message: info.message,
          ...info.metadata,
        };

        // Mask sensitive data
        const masked = maskSensitiveData(logData);

        return JSON.stringify(masked);
      })
    ),
    defaultMeta: { service: serviceName },
    transports: [
      new winston.transports.Console(),
    ],
  });
}

// ============================================================================
// MIDDLEWARE
// ============================================================================

interface MonitoringOptions {
  serviceName: string;
  environment?: string;
  version?: string;
  logLevel?: string;
}

export function setupMonitoring(app: Application, options: MonitoringOptions): winston.Logger {
  const {
    serviceName,
    environment = process.env.ENVIRONMENT || 'production',
    version = process.env.SERVICE_VERSION || '1.0.0',
    logLevel = process.env.LOG_LEVEL || 'info',
  } = options;

  // Create logger
  const logger = createLogger(serviceName, environment);

  // Update service info
  serviceInfo.labels(serviceName, version, environment).set(1);
  serviceHealth.labels(serviceName).set(1);

  // Correlation ID middleware
  app.use((req: Request, res: Response, next: NextFunction) => {
    const correlationId = req.headers['x-correlation-id'] as string || uuidv4();
    (req as any).correlationId = correlationId;
    res.setHeader('X-Correlation-ID', correlationId);
    next();
  });

  // Logging middleware
  app.use((req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();

    // Log request
    logger.info('HTTP Request', {
      event_type: 'http_request',
      method: req.method,
      path: req.path,
      query: req.query,
      correlation_id: (req as any).correlationId,
    });

    // Capture response
    const originalSend = res.send;
    res.send = function (data: any): Response {
      const duration = Date.now() - startTime;

      // Log response
      logger.info('HTTP Response', {
        event_type: 'http_response',
        method: req.method,
        path: req.path,
        status_code: res.statusCode,
        duration_ms: duration,
        correlation_id: (req as any).correlationId,
      });

      return originalSend.call(this, data);
    };

    next();
  });

  // Metrics middleware
  app.use((req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();
    const requestSize = parseInt(req.headers['content-length'] || '0', 10);

    // Track request size
    if (requestSize > 0) {
      httpRequestSize.labels(serviceName, req.method, req.path).observe(requestSize);
    }

    // Capture response
    const originalSend = res.send;
    res.send = function (data: any): Response {
      const duration = (Date.now() - startTime) / 1000;

      // Track metrics
      httpRequestsTotal.labels(serviceName, req.method, req.path, res.statusCode.toString()).inc();
      httpRequestDuration.labels(serviceName, req.method, req.path).observe(duration);

      // Track response size
      const responseSize = Buffer.byteLength(data || '');
      if (responseSize > 0) {
        httpResponseSize.labels(serviceName, req.method, req.path).observe(responseSize);
      }

      return originalSend.call(this, data);
    };

    next();
  });

  // Error handling middleware
  app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
    // Track exception
    httpExceptionsTotal.labels(serviceName, err.name).inc();

    // Log error
    logger.error('HTTP Exception', {
      event_type: 'error',
      error_type: err.name,
      error_message: err.message,
      stack: err.stack,
      method: req.method,
      path: req.path,
      correlation_id: (req as any).correlationId,
    });

    // Send error response
    res.status(500).json({
      error: 'Internal Server Error',
      correlation_id: (req as any).correlationId,
    });
  });

  // Metrics endpoint
  app.get('/metrics', async (req: Request, res: Response) => {
    res.set('Content-Type', register.contentType);
    res.send(await register.metrics());
  });

  // Health endpoint
  app.get('/health', (req: Request, res: Response) => {
    res.json({
      status: 'healthy',
      service: serviceName,
      version,
      environment,
    });
  });

  logger.info('Monitoring initialized', {
    service: serviceName,
    version,
    environment,
  });

  return logger;
}

// ============================================================================
// AI API TRACKING HELPERS
// ============================================================================

export function trackAICall(
  serviceName: string,
  provider: string,
  model: string,
  operation: string
) {
  const startTime = Date.now();

  aiApiCallsTotal.labels(serviceName, provider, model, operation).inc();

  return {
    end: (inputTokens: number, outputTokens: number, cost: number = 0, error?: Error) => {
      const duration = (Date.now() - startTime) / 1000;

      aiApiDuration.labels(serviceName, provider, model, operation).observe(duration);

      if (error) {
        aiApiErrorsTotal.labels(serviceName, provider, model, error.name).inc();
      } else {
        aiApiTokensTotal.labels(serviceName, provider, model, 'input').inc(inputTokens);
        aiApiTokensTotal.labels(serviceName, provider, model, 'output').inc(outputTokens);

        if (cost > 0) {
          aiApiCostTotal.labels(serviceName, provider, model).inc(cost);
        }
      }
    },
  };
}

// AI pricing (per 1M tokens)
const AI_PRICING: Record<string, Record<string, { input: number; output: number }>> = {
  openai: {
    'gpt-4-turbo': { input: 10.0, output: 30.0 },
    'gpt-4': { input: 30.0, output: 60.0 },
    'gpt-3.5-turbo': { input: 0.5, output: 1.5 },
  },
  anthropic: {
    'claude-3-opus': { input: 15.0, output: 75.0 },
    'claude-3-sonnet': { input: 3.0, output: 15.0 },
    'claude-3-haiku': { input: 0.25, output: 1.25 },
    'claude-sonnet-4-5': { input: 3.0, output: 15.0 },
  },
  google: {
    'gemini-pro': { input: 0.5, output: 1.5 },
    'gemini-pro-vision': { input: 0.5, output: 1.5 },
    'gemini-1.5-pro': { input: 1.25, output: 5.0 },
    'gemini-1.5-flash': { input: 0.075, output: 0.3 },
  },
};

export function calculateAICost(
  provider: string,
  model: string,
  inputTokens: number,
  outputTokens: number
): number {
  const pricing = AI_PRICING[provider]?.[model];
  if (!pricing) return 0;

  const inputCost = (inputTokens / 1_000_000) * pricing.input;
  const outputCost = (outputTokens / 1_000_000) * pricing.output;

  return inputCost + outputCost;
}

// ============================================================================
// EXPORT METRICS
// ============================================================================

export {
  register,
  httpRequestsTotal,
  httpRequestDuration,
  aiApiCallsTotal,
  aiApiTokensTotal,
  aiApiCostTotal,
  serviceHealth,
};
