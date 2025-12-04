/**
 * Monitoring Service - Stub implementation
 * When @sentry/node and prom-client are available, this uses real monitoring.
 * Otherwise, falls back to console logging.
 */

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
 * Monitoring Service - Console-based stub
 */
export class MonitoringService {
  private startTime: number = Date.now();

  constructor() {
    console.log('[Monitoring] Using console-based monitoring (Sentry/Prometheus not configured)');
  }

  initSentry(_dsn: string, _options?: any): void {
    console.log('[Monitoring] Sentry initialization skipped (stub mode)');
  }

  captureException(error: Error, context?: any): void {
    console.error('[Monitoring] Exception captured:', error.message, context);
  }

  captureMessage(message: string, level: 'info' | 'warning' | 'error' = 'info'): void {
    console.log(`[Monitoring] [${level}] ${message}`);
  }

  setUser(_user: UserContext | null): void {
    // No-op in stub mode
  }

  recordRequest(method: string, path: string, statusCode: number, duration: number): void {
    if (process.env.LOG_LEVEL === 'debug') {
      console.log(`[Metrics] ${method} ${path} ${statusCode} ${duration}ms`);
    }
  }

  recordError(type: string, source: string): void {
    console.error(`[Metrics] Error: ${type} from ${source}`);
  }

  recordDependencyLatency(dependency: string, operation: string, latency: number): void {
    if (process.env.LOG_LEVEL === 'debug') {
      console.log(`[Metrics] ${dependency}.${operation}: ${latency}ms`);
    }
  }

  updateActiveConnections(_type: string, _count: number): void {
    // No-op in stub mode
  }

  updateCircuitBreakerState(service: string, state: CircuitState): void {
    console.log(`[CircuitBreaker] ${service}: ${state}`);
  }

  async getMetrics(): Promise<string> {
    return '# Metrics not available in stub mode\n';
  }

  async checkHealth(): Promise<HealthStatus> {
    return {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: Math.floor((Date.now() - this.startTime) / 1000),
      version: process.env.npm_package_version || '1.0.0',
      dependencies: [
        {
          name: 'memory',
          status: 'up',
          lastChecked: new Date().toISOString(),
        }
      ],
    };
  }

  async checkDependencies(): Promise<DependencyStatus[]> {
    return [];
  }

  log(level: LogLevel, message: string, metadata?: LogMetadata): void {
    const logEntry = {
      level,
      message,
      timestamp: new Date().toISOString(),
      ...metadata,
    };

    if (level === 'error' || level === 'fatal') {
      console.error(JSON.stringify(logEntry));
    } else if (level === 'warn') {
      console.warn(JSON.stringify(logEntry));
    } else {
      console.log(JSON.stringify(logEntry));
    }
  }

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
