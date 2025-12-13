import { Request, Response, NextFunction } from 'express';
import { monitoring } from '../services/monitoring';
import { AppError, ErrorCode } from '../types/errors';

export interface ErrorResponse {
  success: false;
  error: {
    code: ErrorCode;
    message: string;
    details?: Record<string, any>;
    requestId?: string;
  };
}

/**
 * Async request handler type
 */
export type AsyncRequestHandler = (
  req: Request,
  res: Response,
  next: NextFunction
) => Promise<any>;

/**
 * Regular request handler type
 */
export type RequestHandler = (
  req: Request,
  res: Response,
  next: NextFunction
) => void;

/**
 * Global error handler middleware
 * Catches all errors and sends appropriate responses
 */
export const errorHandler = (
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  // Log error
  console.error('Error:', err);

  // Default to 500 server error
  let statusCode = 500;
  let errorCode: ErrorCode = ErrorCode.INTERNAL_ERROR;
  let message = err.message || 'Internal Server Error';
  let details: Record<string, any> | undefined;

  // Extract error details
  if (err instanceof AppError) {
    statusCode = err.statusCode;
    errorCode = err.code;
    message = err.message;
    details = err.details;
  } else if (err.name === 'ValidationError') {
    statusCode = 400;
    errorCode = ErrorCode.VALIDATION_ERROR;
    message = err.message;
  } else if (err.name === 'UnauthorizedError' || err.name === 'JsonWebTokenError') {
    statusCode = 401;
    errorCode = ErrorCode.UNAUTHORIZED;
    message = 'Unauthorized';
  } else if (err.name === 'TokenExpiredError') {
    statusCode = 401;
    errorCode = ErrorCode.UNAUTHORIZED;
    message = 'Token expired';
  }

  // Log error with monitoring
  const errorContext = {
    requestId: (req as any).id || req.headers['x-request-id'],
    method: req.method,
    path: req.path,
    statusCode,
    code: errorCode,
    stack: err.stack,
  };

  if (statusCode >= 500) {
    monitoring.log('error', `Server error: ${message}`, errorContext);
    monitoring.captureException(err, errorContext);
  } else {
    monitoring.log('warn', `Client error: ${message}`, errorContext);
  }

  // Record error metric
  monitoring.recordError(err.name, req.path);

  // Build response
  const response: ErrorResponse = {
    success: false,
    error: {
      code: errorCode,
      message,
      details,
      requestId: req.headers['x-request-id'] as string,
    },
  };

  // Include stack trace in development
  if (process.env.NODE_ENV === 'development' && err.stack) {
    response.error.details = {
      ...response.error.details,
      stack: err.stack,
    };
  }

  res.status(statusCode).json(response);
};

/**
 * Not found handler for undefined routes
 */
export const notFoundHandler = (req: Request, res: Response): void => {
  const message = `Route not found: ${req.method} ${req.path}`;

  monitoring.log('warn', message, {
    requestId: (req as any).id || req.headers['x-request-id'],
    method: req.method,
    path: req.path,
  });

  const response: ErrorResponse = {
    success: false,
    error: {
      code: ErrorCode.NOT_FOUND,
      message,
      requestId: req.headers['x-request-id'] as string,
    },
  };

  res.status(404).json(response);
};

/**
 * Async handler wrapper to catch promise rejections
 */
export const asyncHandler = (fn: AsyncRequestHandler): RequestHandler => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

/**
 * Circuit breaker options
 */
export interface CircuitBreakerOptions {
  failureThreshold?: number;
  successThreshold?: number;
  timeout?: number;
  resetTimeout?: number;
  name?: string;
}

/**
 * Circuit breaker states
 */
enum CircuitState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open',
}

/**
 * Circuit Breaker implementation
 * Prevents cascading failures by stopping requests to failing services
 */
export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private successCount: number = 0;
  private nextAttempt: number = Date.now();
  private readonly failureThreshold: number;
  private readonly successThreshold: number;
  private readonly timeout: number;
  private readonly resetTimeout: number;
  private readonly name: string;

  constructor(options: CircuitBreakerOptions = {}) {
    this.failureThreshold = options.failureThreshold || 5;
    this.successThreshold = options.successThreshold || 2;
    this.timeout = options.timeout || 60000; // 1 minute
    this.resetTimeout = options.resetTimeout || 30000; // 30 seconds
    this.name = options.name || 'default';

    // Update monitoring
    this.updateMonitoring();
  }

  /**
   * Execute a function with circuit breaker protection
   */
  async call<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() < this.nextAttempt) {
        throw new AppError(
          ErrorCode.INTERNAL_ERROR,
          `Circuit breaker is OPEN for ${this.name}`,
          503,
          { circuitBreaker: this.name }
        );
      }
      // Try to recover
      this.state = CircuitState.HALF_OPEN;
      this.updateMonitoring();
      monitoring.log('info', `Circuit breaker ${this.name} entering HALF_OPEN state`);
    }

    try {
      const result = await this.executeWithTimeout(fn);
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  /**
   * Execute function with timeout
   */
  private async executeWithTimeout<T>(fn: () => Promise<T>): Promise<T> {
    return Promise.race([
      fn(),
      new Promise<T>((_, reject) =>
        setTimeout(
          () => reject(new Error('Circuit breaker timeout')),
          this.timeout
        )
      ),
    ]);
  }

  /**
   * Handle successful execution
   */
  private onSuccess(): void {
    this.failureCount = 0;

    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.successThreshold) {
        this.state = CircuitState.CLOSED;
        this.successCount = 0;
        this.updateMonitoring();
        monitoring.log('info', `Circuit breaker ${this.name} recovered to CLOSED state`);
      }
    }
  }

  /**
   * Handle failed execution
   */
  private onFailure(): void {
    this.failureCount++;
    this.successCount = 0;

    if (this.failureCount >= this.failureThreshold) {
      this.state = CircuitState.OPEN;
      this.nextAttempt = Date.now() + this.resetTimeout;
      this.updateMonitoring();
      monitoring.log('error', `Circuit breaker ${this.name} opened due to failures`);
    }
  }

  /**
   * Update monitoring metrics
   */
  private updateMonitoring(): void {
    monitoring.updateCircuitBreakerState(this.name, this.state as any);
  }

  /**
   * Get current state
   */
  getState(): CircuitState {
    return this.state;
  }

  /**
   * Manually reset circuit breaker
   */
  reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    this.nextAttempt = Date.now();
    this.updateMonitoring();
    monitoring.log('info', `Circuit breaker ${this.name} manually reset`);
  }
}

/**
 * Retry with exponential backoff
 * Retries a function with increasing delays between attempts
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000,
  maxDelay: number = 10000
): Promise<T> {
  let lastError: Error | undefined;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      if (attempt === maxRetries) {
        monitoring.log('error', `Retry failed after ${maxRetries} attempts`, {
          error: lastError.message,
        });
        throw lastError;
      }

      // Calculate delay with exponential backoff and jitter
      const exponentialDelay = Math.min(baseDelay * Math.pow(2, attempt), maxDelay);
      const jitter = Math.random() * 0.3 * exponentialDelay;
      const delay = exponentialDelay + jitter;

      monitoring.log('warn', `Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`, {
        error: lastError.message,
      });

      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
}

/**
 * Rate limiter options
 */
export interface RateLimiterOptions {
  windowMs?: number;
  maxRequests?: number;
  message?: string;
}

/**
 * Simple in-memory rate limiter
 * For production, use Redis-backed rate limiting
 */
export class RateLimiter {
  private requests: Map<string, number[]> = new Map();
  private readonly windowMs: number;
  private readonly maxRequests: number;
  private readonly message: string;

  constructor(options: RateLimiterOptions = {}) {
    this.windowMs = options.windowMs || 60000; // 1 minute
    this.maxRequests = options.maxRequests || 100;
    this.message = options.message || 'Too many requests';
  }

  /**
   * Check if request is allowed
   */
  check(key: string): boolean {
    const now = Date.now();
    const windowStart = now - this.windowMs;

    // Get existing requests for this key
    let timestamps = this.requests.get(key) || [];

    // Remove old requests outside the window
    timestamps = timestamps.filter((t) => t > windowStart);

    // Check if limit exceeded
    if (timestamps.length >= this.maxRequests) {
      return false;
    }

    // Add current request
    timestamps.push(now);
    this.requests.set(key, timestamps);

    return true;
  }

  /**
   * Middleware function
   */
  middleware() {
    return (req: Request, res: Response, next: NextFunction): void => {
      const key = req.ip || 'unknown';

      if (!this.check(key)) {
        const response: ErrorResponse = {
          success: false,
          error: {
            code: ErrorCode.FORBIDDEN,
            message: this.message,
            requestId: req.headers['x-request-id'] as string,
          },
        };
        res.status(429).json(response);
        return;
      }

      next();
    };
  }
}
