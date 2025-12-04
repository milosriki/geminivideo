/**
 * Logger Utility - Console-based implementation
 * Falls back to console logging when Winston is not available.
 */

import { v4 as uuidv4 } from 'uuid';

/**
 * Log levels
 */
export enum LogLevel {
  DEBUG = 'debug',
  INFO = 'info',
  WARN = 'warn',
  ERROR = 'error',
  FATAL = 'fatal',
}

/**
 * Log context for request tracking
 */
export interface LogContext {
  requestId?: string;
  userId?: string;
  traceId?: string;
  spanId?: string;
  [key: string]: any;
}

/**
 * Logger configuration
 */
interface LoggerConfig {
  level?: string;
  serviceName?: string;
  enableConsole?: boolean;
  enableFile?: boolean;
  filename?: string;
}

/**
 * Console-based logger implementation
 */
export class Logger {
  private serviceName: string;
  private defaultContext: LogContext;
  private logLevel: string;

  constructor(config: LoggerConfig = {}) {
    this.serviceName = config.serviceName || 'gateway-api';
    this.defaultContext = {};
    this.logLevel = config.level || process.env.LOG_LEVEL || 'info';
  }

  private shouldLog(level: string): boolean {
    const levels = ['debug', 'info', 'warn', 'error', 'fatal'];
    const currentIndex = levels.indexOf(this.logLevel);
    const messageIndex = levels.indexOf(level);
    return messageIndex >= currentIndex;
  }

  private formatLog(level: string, message: string, context?: LogContext): string {
    const timestamp = new Date().toISOString();
    const mergedContext = { ...this.defaultContext, ...context };

    if (process.env.NODE_ENV === 'production') {
      return JSON.stringify({
        timestamp,
        level,
        service: this.serviceName,
        message,
        ...mergedContext,
      });
    }

    const contextStr = Object.keys(mergedContext).length > 0
      ? ` ${JSON.stringify(mergedContext)}`
      : '';
    return `${timestamp} [${level.toUpperCase()}] [${this.serviceName}]: ${message}${contextStr}`;
  }

  setDefaultContext(context: LogContext): void {
    this.defaultContext = { ...this.defaultContext, ...context };
  }

  clearDefaultContext(): void {
    this.defaultContext = {};
  }

  debug(message: string, context?: LogContext): void {
    if (this.shouldLog('debug')) {
      console.debug(this.formatLog('debug', message, context));
    }
  }

  info(message: string, context?: LogContext): void {
    if (this.shouldLog('info')) {
      console.log(this.formatLog('info', message, context));
    }
  }

  warn(message: string, context?: LogContext): void {
    if (this.shouldLog('warn')) {
      console.warn(this.formatLog('warn', message, context));
    }
  }

  error(message: string, error?: Error | unknown, context?: LogContext): void {
    if (!this.shouldLog('error')) return;

    const errorContext: any = { ...context };
    if (error instanceof Error) {
      errorContext.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    } else if (error) {
      errorContext.error = error;
    }

    console.error(this.formatLog('error', message, errorContext));
  }

  fatal(message: string, error?: Error | unknown, context?: LogContext): void {
    if (!this.shouldLog('fatal')) return;

    const errorContext: any = { ...context };
    if (error instanceof Error) {
      errorContext.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    } else if (error) {
      errorContext.error = error;
    }

    console.error(this.formatLog('fatal', message, errorContext));
  }

  child(context: LogContext): Logger {
    const childLogger = new Logger({
      serviceName: this.serviceName,
      level: this.logLevel,
    });
    childLogger.setDefaultContext({ ...this.defaultContext, ...context });
    return childLogger;
  }

  static generateRequestId(): string {
    return uuidv4();
  }
}

/**
 * Request logger middleware
 */
export function requestLoggerMiddleware(logger: Logger) {
  return (req: any, res: any, next: any) => {
    const requestId = Logger.generateRequestId();
    req.id = requestId;
    req.logger = logger.child({ requestId });

    const startTime = Date.now();
    req.logger.info(`${req.method} ${req.path}`, {
      method: req.method,
      path: req.path,
      query: req.query,
      ip: req.ip,
      userAgent: req.get('user-agent'),
    });

    const originalSend = res.send;
    res.send = function (data: any) {
      const duration = Date.now() - startTime;
      req.logger.info(`${req.method} ${req.path} completed`, {
        method: req.method,
        path: req.path,
        statusCode: res.statusCode,
        duration,
      });
      return originalSend.call(this, data);
    };

    next();
  };
}

/**
 * Export default logger instance
 */
export const logger = new Logger({
  serviceName: process.env.SERVICE_NAME || 'gateway-api',
  enableConsole: true,
});

export default logger;
