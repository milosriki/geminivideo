import { createLogger, format, transports, Logger as WinstonLogger } from 'winston';
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
 * Structured logger using Winston
 * Provides JSON logging in production, pretty printing in development
 */
export class Logger {
  private logger: WinstonLogger;
  private serviceName: string;
  private defaultContext: LogContext;

  constructor(config: LoggerConfig = {}) {
    this.serviceName = config.serviceName || 'gateway-api';
    this.defaultContext = {};

    const isDevelopment = process.env.NODE_ENV !== 'production';
    const logLevel = config.level || process.env.LOG_LEVEL || (isDevelopment ? 'debug' : 'info');

    // Define custom format
    const customFormat = format.combine(
      format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
      format.errors({ stack: true }),
      format.metadata({ fillExcept: ['message', 'level', 'timestamp'] }),
      isDevelopment ? this.developmentFormat() : this.productionFormat()
    );

    // Configure transports
    const logTransports: any[] = [];

    if (config.enableConsole !== false) {
      logTransports.push(
        new transports.Console({
          level: logLevel,
        })
      );
    }

    if (config.enableFile) {
      logTransports.push(
        new transports.File({
          filename: config.filename || 'logs/error.log',
          level: 'error',
        }),
        new transports.File({
          filename: 'logs/combined.log',
        })
      );
    }

    this.logger = createLogger({
      level: logLevel,
      format: customFormat,
      defaultMeta: { service: this.serviceName },
      transports: logTransports,
    });
  }

  /**
   * Production format - JSON output
   */
  private productionFormat() {
    return format.combine(
      format.json(),
      format.printf((info) => {
        const { timestamp, level, message, metadata, ...rest } = info;
        return JSON.stringify({
          timestamp,
          level,
          service: this.serviceName,
          message,
          ...metadata,
          ...rest,
        });
      })
    );
  }

  /**
   * Development format - Pretty colored output
   */
  private developmentFormat() {
    return format.combine(
      format.colorize(),
      format.printf((info) => {
        const { timestamp, level, message, metadata } = info;
        const metaStr = metadata && Object.keys(metadata).length > 0
          ? `\n${JSON.stringify(metadata, null, 2)}`
          : '';
        return `${timestamp} [${level}]: ${message}${metaStr}`;
      })
    );
  }

  /**
   * Set default context for all logs
   */
  setDefaultContext(context: LogContext): void {
    this.defaultContext = { ...this.defaultContext, ...context };
  }

  /**
   * Clear default context
   */
  clearDefaultContext(): void {
    this.defaultContext = {};
  }

  /**
   * Debug level log
   */
  debug(message: string, context?: LogContext): void {
    this.logger.debug(message, this.mergeContext(context));
  }

  /**
   * Info level log
   */
  info(message: string, context?: LogContext): void {
    this.logger.info(message, this.mergeContext(context));
  }

  /**
   * Warning level log
   */
  warn(message: string, context?: LogContext): void {
    this.logger.warn(message, this.mergeContext(context));
  }

  /**
   * Error level log
   */
  error(message: string, error?: Error | unknown, context?: LogContext): void {
    const errorContext: any = this.mergeContext(context);

    if (error instanceof Error) {
      errorContext.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    } else if (error) {
      errorContext.error = error;
    }

    this.logger.error(message, errorContext);
  }

  /**
   * Fatal level log
   */
  fatal(message: string, error?: Error | unknown, context?: LogContext): void {
    const errorContext: any = this.mergeContext(context);

    if (error instanceof Error) {
      errorContext.error = {
        name: error.name,
        message: error.message,
        stack: error.stack,
      };
    } else if (error) {
      errorContext.error = error;
    }

    this.logger.log('fatal', message, errorContext);
  }

  /**
   * Merge context with default context
   */
  private mergeContext(context?: LogContext): any {
    return { ...this.defaultContext, ...context };
  }

  /**
   * Create a child logger with pre-set context
   */
  child(context: LogContext): Logger {
    const childLogger = new Logger({
      serviceName: this.serviceName,
    });
    childLogger.setDefaultContext({ ...this.defaultContext, ...context });
    return childLogger;
  }

  /**
   * Generate a unique request ID
   */
  static generateRequestId(): string {
    return uuidv4();
  }
}

/**
 * Request logger middleware
 * Adds request ID and logs all HTTP requests
 */
export function requestLoggerMiddleware(logger: Logger) {
  return (req: any, res: any, next: any) => {
    // Generate request ID
    const requestId = Logger.generateRequestId();
    req.id = requestId;

    // Create request-scoped logger
    req.logger = logger.child({ requestId });

    // Log request start
    const startTime = Date.now();
    req.logger.info(`${req.method} ${req.path}`, {
      method: req.method,
      path: req.path,
      query: req.query,
      ip: req.ip,
      userAgent: req.get('user-agent'),
    });

    // Log response
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
  enableFile: process.env.NODE_ENV === 'production',
});

export default logger;
