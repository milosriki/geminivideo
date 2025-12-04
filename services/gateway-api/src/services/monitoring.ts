import * as Sentry from '@sentry/node';
import { Counter, Histogram, Registry, Gauge } from 'prom-client';
import { createClient } from 'redis';
import { Pool } from 'pg';

/**
 * User context for error tracking
 */
export interface UserContext {
  id: string;
  email?: string;
  username?: string;
  ip?: string;
}

/**
 * Health check status
 */
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  dependencies: DependencyStatus[];
}

/**
 * Dependency health status
 */
export interface DependencyStatus {
  name: string;
  status: 'up' | 'down' | 'degraded';
  responseTime?: number;
  error?: string;
  lastChecked: string;
}

/**
 * Log levels
 */
export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

/**
 * Log metadata
 */
export interface LogMetadata {
  [key: string]: any;
  requestId?: string;
  userId?: string;
  traceId?: string;
  spanId?: string;
}

/**
 * Circuit breaker states
 */
export enum CircuitState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open',
}

/**
 * Monitoring Service
 * Provides comprehensive production observability with:
 * - Sentry error tracking
 * - Prometheus metrics
 * - Health checks
 * - Structured logging
 */
export class MonitoringService {
  private registry: Registry;
  private sentryInitialized: boolean = false;
  private startTime: number = Date.now();

  // Prometheus metrics
  private requestCounter: Counter<string>;
  private requestDuration: Histogram<string>;
  private errorCounter: Counter<string>;
  private activeConnections: Gauge<string>;
  private dependencyLatency: Histogram<string>;
  private circuitBreakerState: Gauge<string>;

  // Dependencies for health checks
  private redisClient?: ReturnType<typeof createClient>;
  private pgPool?: Pool;

  constructor() {
    this.registry = new Registry();
    this.initializeMetrics();
  }

  /**
   * Initialize Prometheus metrics
   */
  private initializeMetrics(): void {
    // HTTP request counter
    this.requestCounter = new Counter({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'path', 'status_code'],
      registers: [this.registry],
    });

    // HTTP request duration
    this.requestDuration = new Histogram({
      name: 'http_request_duration_seconds',
      help: 'Duration of HTTP requests in seconds',
      labelNames: ['method', 'path', 'status_code'],
      buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
      registers: [this.registry],
    });

    // Error counter
    this.errorCounter = new Counter({
      name: 'errors_total',
      help: 'Total number of errors',
      labelNames: ['type', 'source'],
      registers: [this.registry],
    });

    // Active connections
    this.activeConnections = new Gauge({
      name: 'active_connections',
      help: 'Number of active connections',
      labelNames: ['type'],
      registers: [this.registry],
    });

    // Dependency latency
    this.dependencyLatency = new Histogram({
      name: 'dependency_latency_seconds',
      help: 'Latency of external dependencies in seconds',
      labelNames: ['dependency', 'operation'],
      buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
      registers: [this.registry],
    });

    // Circuit breaker state (0 = closed, 1 = half-open, 2 = open)
    this.circuitBreakerState = new Gauge({
      name: 'circuit_breaker_state',
      help: 'Circuit breaker state (0=closed, 1=half-open, 2=open)',
      labelNames: ['service'],
      registers: [this.registry],
    });
  }

  /**
   * Initialize Sentry for error tracking
   */
  initSentry(dsn: string, options?: Sentry.NodeOptions): void {
    if (this.sentryInitialized) {
      console.warn('Sentry already initialized');
      return;
    }

    Sentry.init({
      dsn,
      environment: process.env.NODE_ENV || 'development',
      tracesSampleRate: 1.0,
      integrations: [
        new Sentry.Integrations.Http({ tracing: true }),
        new Sentry.Integrations.Express({ app: undefined }),
      ],
      beforeSend(event, hint) {
        // Filter out sensitive data
        if (event.request?.headers) {
          delete event.request.headers['authorization'];
          delete event.request.headers['cookie'];
        }
        return event;
      },
      ...options,
    });

    this.sentryInitialized = true;
    console.log('Sentry initialized successfully');
  }

  /**
   * Capture an exception in Sentry
   */
  captureException(error: Error, context?: any): void {
    if (!this.sentryInitialized) {
      console.error('Sentry not initialized, logging error:', error);
      return;
    }

    Sentry.withScope((scope) => {
      if (context) {
        scope.setContext('additional', context);
      }
      Sentry.captureException(error);
    });

    // Also record in Prometheus
    this.recordError(error.name, context?.source || 'unknown');
  }

  /**
   * Capture a message in Sentry
   */
  captureMessage(
    message: string,
    level: 'info' | 'warning' | 'error' = 'info'
  ): void {
    if (!this.sentryInitialized) {
      console.log(`Sentry not initialized, logging message [${level}]:`, message);
      return;
    }

    const sentryLevel =
      level === 'info'
        ? Sentry.Severity.Info
        : level === 'warning'
        ? Sentry.Severity.Warning
        : Sentry.Severity.Error;

    Sentry.captureMessage(message, sentryLevel);
  }

  /**
   * Set user context for error tracking
   */
  setUser(user: UserContext | null): void {
    if (!this.sentryInitialized) {
      return;
    }

    Sentry.setUser(user);
  }

  /**
   * Record an HTTP request in metrics
   */
  recordRequest(
    method: string,
    path: string,
    statusCode: number,
    duration: number
  ): void {
    const labels = {
      method: method.toUpperCase(),
      path: this.normalizePath(path),
      status_code: statusCode.toString(),
    };

    this.requestCounter.inc(labels);
    this.requestDuration.observe(labels, duration / 1000); // Convert to seconds
  }

  /**
   * Record an error in metrics
   */
  recordError(type: string, source: string): void {
    this.errorCounter.inc({ type, source });
  }

  /**
   * Record dependency latency
   */
  recordDependencyLatency(
    dependency: string,
    operation: string,
    latency: number
  ): void {
    this.dependencyLatency.observe({ dependency, operation }, latency / 1000);
  }

  /**
   * Update active connections count
   */
  updateActiveConnections(type: string, count: number): void {
    this.activeConnections.set({ type }, count);
  }

  /**
   * Update circuit breaker state
   */
  updateCircuitBreakerState(service: string, state: CircuitState): void {
    const stateValue =
      state === CircuitState.CLOSED
        ? 0
        : state === CircuitState.HALF_OPEN
        ? 1
        : 2;
    this.circuitBreakerState.set({ service }, stateValue);
  }

  /**
   * Get Prometheus metrics
   */
  async getMetrics(): Promise<string> {
    return this.registry.metrics();
  }

  /**
   * Normalize path for metrics (remove IDs, etc.)
   */
  private normalizePath(path: string): string {
    return path
      .replace(/\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/gi, '/:id')
      .replace(/\/\d+/g, '/:id')
      .replace(/\/[a-f0-9]{24}/g, '/:id');
  }

  /**
   * Set Redis client for health checks
   */
  setRedisClient(client: ReturnType<typeof createClient>): void {
    this.redisClient = client;
  }

  /**
   * Set PostgreSQL pool for health checks
   */
  setPostgresPool(pool: Pool): void {
    this.pgPool = pool;
  }

  /**
   * Check overall system health
   */
  async checkHealth(): Promise<HealthStatus> {
    const dependencies = await this.checkDependencies();
    const hasUnhealthy = dependencies.some((dep) => dep.status === 'down');
    const hasDegraded = dependencies.some((dep) => dep.status === 'degraded');

    let status: 'healthy' | 'degraded' | 'unhealthy';
    if (hasUnhealthy) {
      status = 'unhealthy';
    } else if (hasDegraded) {
      status = 'degraded';
    } else {
      status = 'healthy';
    }

    return {
      status,
      timestamp: new Date().toISOString(),
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      version: process.env.npm_package_version || '1.0.0',
      dependencies,
    };
  }

  /**
   * Check all dependencies
   */
  async checkDependencies(): Promise<DependencyStatus[]> {
    const checks: Promise<DependencyStatus>[] = [];

    // Check Redis
    if (this.redisClient) {
      checks.push(this.checkRedis());
    }

    // Check PostgreSQL
    if (this.pgPool) {
      checks.push(this.checkPostgres());
    }

    // Check memory
    checks.push(this.checkMemory());

    return Promise.all(checks);
  }

  /**
   * Check Redis connection
   */
  private async checkRedis(): Promise<DependencyStatus> {
    const start = Date.now();
    try {
      await this.redisClient!.ping();
      const responseTime = Date.now() - start;

      this.recordDependencyLatency('redis', 'ping', responseTime);

      return {
        name: 'redis',
        status: responseTime > 1000 ? 'degraded' : 'up',
        responseTime,
        lastChecked: new Date().toISOString(),
      };
    } catch (error) {
      return {
        name: 'redis',
        status: 'down',
        error: error instanceof Error ? error.message : 'Unknown error',
        lastChecked: new Date().toISOString(),
      };
    }
  }

  /**
   * Check PostgreSQL connection
   */
  private async checkPostgres(): Promise<DependencyStatus> {
    const start = Date.now();
    try {
      await this.pgPool!.query('SELECT 1');
      const responseTime = Date.now() - start;

      this.recordDependencyLatency('postgres', 'query', responseTime);

      return {
        name: 'postgres',
        status: responseTime > 1000 ? 'degraded' : 'up',
        responseTime,
        lastChecked: new Date().toISOString(),
      };
    } catch (error) {
      return {
        name: 'postgres',
        status: 'down',
        error: error instanceof Error ? error.message : 'Unknown error',
        lastChecked: new Date().toISOString(),
      };
    }
  }

  /**
   * Check memory usage
   */
  private async checkMemory(): Promise<DependencyStatus> {
    const usage = process.memoryUsage();
    const heapUsedPercent = (usage.heapUsed / usage.heapTotal) * 100;

    let status: 'up' | 'degraded' | 'down';
    if (heapUsedPercent > 90) {
      status = 'down';
    } else if (heapUsedPercent > 75) {
      status = 'degraded';
    } else {
      status = 'up';
    }

    return {
      name: 'memory',
      status,
      responseTime: heapUsedPercent,
      lastChecked: new Date().toISOString(),
    };
  }

  /**
   * Structured logging
   */
  log(level: LogLevel, message: string, metadata?: LogMetadata): void {
    const logEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...metadata,
    };

    // In production, this would use Winston or Pino
    // For now, use console with JSON formatting
    if (level === 'error' || level === 'fatal') {
      console.error(JSON.stringify(logEntry));
    } else if (level === 'warn') {
      console.warn(JSON.stringify(logEntry));
    } else {
      console.log(JSON.stringify(logEntry));
    }
  }

  /**
   * Create a child logger with default metadata
   */
  createLogger(defaultMetadata: LogMetadata): {
    debug: (msg: string, meta?: LogMetadata) => void;
    info: (msg: string, meta?: LogMetadata) => void;
    warn: (msg: string, meta?: LogMetadata) => void;
    error: (msg: string, meta?: LogMetadata) => void;
    fatal: (msg: string, meta?: LogMetadata) => void;
  } {
    return {
      debug: (msg, meta) => this.log('debug', msg, { ...defaultMetadata, ...meta }),
      info: (msg, meta) => this.log('info', msg, { ...defaultMetadata, ...meta }),
      warn: (msg, meta) => this.log('warn', msg, { ...defaultMetadata, ...meta }),
      error: (msg, meta) => this.log('error', msg, { ...defaultMetadata, ...meta }),
      fatal: (msg, meta) => this.log('fatal', msg, { ...defaultMetadata, ...meta }),
    };
  }
}

// Export singleton instance
export const monitoring = new MonitoringService();
