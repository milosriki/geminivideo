/**
 * Enhanced Error Handler with Fallbacks and Recovery
 * Agent 17: Error Handling Enhancement
 * Created: 2025-12-13
 *
 * Features:
 * - Fallback to cached data on service failures
 * - Retry logic with exponential backoff
 * - Database connection failure recovery
 * - Meta API rate limit handling
 * - RAG indexing failure handling
 * - Budget update failure with rollback
 */

import { Request, Response, NextFunction } from 'express';
import { monitoring } from '../services/monitoring';
import { RedisCacheService } from '../services/redis-cache';
import { AppError, ErrorCode } from '../types/errors';

// ============================================================================
// Types
// ============================================================================

export interface FallbackConfig {
  enableCacheFallback: boolean;
  cacheKeyPrefix: string;
  cacheTtlSeconds: number;
}

export interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  retryableErrors: string[];
}

export interface RecoveryResult<T> {
  success: boolean;
  data?: T;
  source: 'primary' | 'cache' | 'fallback' | 'error';
  error?: Error;
  retries?: number;
}

// ============================================================================
// Configuration
// ============================================================================

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 1000,
  maxDelayMs: 10000,
  retryableErrors: [
    'ECONNREFUSED',
    'ECONNRESET',
    'ETIMEDOUT',
    'ENOTFOUND',
    'NETWORK_ERROR',
    'SERVICE_UNAVAILABLE'
  ]
};

const DEFAULT_FALLBACK_CONFIG: FallbackConfig = {
  enableCacheFallback: true,
  cacheKeyPrefix: 'fallback:',
  cacheTtlSeconds: 3600 // 1 hour
};

// ============================================================================
// Service-Specific Error Handlers
// ============================================================================

/**
 * Handle ML Service failures with cached prediction fallback
 */
export async function handleMLServiceFailure<T>(
  operation: () => Promise<T>,
  cacheKey: string,
  cache: RedisCacheService,
  fallbackConfig: FallbackConfig = DEFAULT_FALLBACK_CONFIG
): Promise<RecoveryResult<T>> {
  try {
    const result = await operation();

    // Cache successful result for fallback
    if (fallbackConfig.enableCacheFallback) {
      await cache.set(
        `${fallbackConfig.cacheKeyPrefix}${cacheKey}`,
        result,
        fallbackConfig.cacheTtlSeconds
      );
    }

    return { success: true, data: result, source: 'primary' };
  } catch (error) {
    monitoring.log('warn', `ML Service operation failed, attempting fallback: ${error}`);

    // Try cache fallback
    if (fallbackConfig.enableCacheFallback) {
      try {
        const cachedResult = await cache.get<T>(
          `${fallbackConfig.cacheKeyPrefix}${cacheKey}`
        );

        if (cachedResult) {
          monitoring.log('info', `Using cached fallback for ${cacheKey}`);
          return { success: true, data: cachedResult, source: 'cache' };
        }
      } catch (cacheError) {
        monitoring.log('error', `Cache fallback also failed: ${cacheError}`);
      }
    }

    return {
      success: false,
      source: 'error',
      error: error instanceof Error ? error : new Error(String(error))
    };
  }
}

/**
 * Handle Database connection failures with retry logic
 */
export async function handleDatabaseFailure<T>(
  operation: () => Promise<T>,
  retryConfig: RetryConfig = DEFAULT_RETRY_CONFIG
): Promise<RecoveryResult<T>> {
  let lastError: Error | null = null;
  let retries = 0;

  for (let attempt = 0; attempt <= retryConfig.maxRetries; attempt++) {
    try {
      const result = await operation();
      return { success: true, data: result, source: 'primary', retries };
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));
      retries = attempt;

      const isRetryable = retryConfig.retryableErrors.some(
        errType => lastError?.message.includes(errType)
      );

      if (!isRetryable || attempt === retryConfig.maxRetries) {
        break;
      }

      // Exponential backoff with jitter
      const delay = Math.min(
        retryConfig.baseDelayMs * Math.pow(2, attempt) + Math.random() * 1000,
        retryConfig.maxDelayMs
      );

      monitoring.log('warn', `Database operation failed, retrying in ${delay}ms (attempt ${attempt + 1}/${retryConfig.maxRetries})`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }

  monitoring.log('error', `Database operation failed after ${retries} retries`);
  return {
    success: false,
    source: 'error',
    error: lastError || new Error('Unknown database error'),
    retries
  };
}

/**
 * Handle Meta API rate limits with queue and retry
 */
export async function handleMetaAPIRateLimit<T>(
  operation: () => Promise<T>,
  retryAfterSeconds: number = 60
): Promise<RecoveryResult<T>> {
  try {
    const result = await operation();
    return { success: true, data: result, source: 'primary' };
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);

    // Check if it's a rate limit error
    if (
      errorMessage.includes('rate limit') ||
      errorMessage.includes('429') ||
      errorMessage.includes('too many requests')
    ) {
      monitoring.log('warn', `Meta API rate limited, will retry after ${retryAfterSeconds}s`);

      // Wait and retry once
      await new Promise(resolve => setTimeout(resolve, retryAfterSeconds * 1000));

      try {
        const retryResult = await operation();
        return { success: true, data: retryResult, source: 'primary', retries: 1 };
      } catch (retryError) {
        return {
          success: false,
          source: 'error',
          error: retryError instanceof Error ? retryError : new Error(String(retryError)),
          retries: 1
        };
      }
    }

    return {
      success: false,
      source: 'error',
      error: error instanceof Error ? error : new Error(String(error))
    };
  }
}

/**
 * Handle RAG indexing failures (log and continue)
 */
export async function handleRAGIndexingFailure<T>(
  operation: () => Promise<T>,
  context: { adId?: string; action?: string }
): Promise<RecoveryResult<T>> {
  try {
    const result = await operation();
    return { success: true, data: result, source: 'primary' };
  } catch (error) {
    // Log error but don't fail the main operation
    monitoring.log('error', `RAG indexing failed for ${context.adId || 'unknown'}: ${error}`);

    // Record for later retry
    try {
      // Queue for background retry
      await queueForRetry('rag_indexing', {
        ...context,
        error: error instanceof Error ? error.message : String(error),
        timestamp: new Date().toISOString()
      });
    } catch (queueError) {
      monitoring.log('error', `Failed to queue RAG retry: ${queueError}`);
    }

    // Return success with fallback status - operation continues
    return {
      success: true,
      data: undefined,
      source: 'fallback'
    };
  }
}

/**
 * Handle budget update failures with rollback
 */
export async function handleBudgetUpdateFailure<T>(
  updateOperation: () => Promise<T>,
  rollbackOperation: () => Promise<void>,
  context: { accountId: string; fromAds: string[]; toAds: string[] }
): Promise<RecoveryResult<T>> {
  try {
    const result = await updateOperation();
    monitoring.log('info', `Budget update successful for account ${context.accountId}`);
    return { success: true, data: result, source: 'primary' };
  } catch (error) {
    monitoring.log('error', `Budget update failed, initiating rollback: ${error}`);

    // Attempt rollback
    try {
      await rollbackOperation();
      monitoring.log('info', `Budget rollback successful for account ${context.accountId}`);

      // Send alert
      monitoring.recordError('budget_update_rollback', context.accountId);
    } catch (rollbackError) {
      monitoring.log('error', `Budget rollback FAILED: ${rollbackError}`);
      monitoring.recordError('budget_rollback_failed', context.accountId);

      // This is critical - alert immediately
      await sendCriticalAlert({
        type: 'BUDGET_ROLLBACK_FAILED',
        accountId: context.accountId,
        error: rollbackError instanceof Error ? rollbackError.message : String(rollbackError),
        timestamp: new Date().toISOString()
      });
    }

    return {
      success: false,
      source: 'error',
      error: error instanceof Error ? error : new Error(String(error))
    };
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Queue failed operation for background retry
 */
async function queueForRetry(
  operationType: string,
  context: Record<string, any>
): Promise<void> {
  // In production, this would use a proper job queue like BullMQ
  monitoring.log('info', `Queued ${operationType} for retry: ${JSON.stringify(context)}`);
}

/**
 * Send critical alert for system failures
 */
async function sendCriticalAlert(alert: {
  type: string;
  accountId: string;
  error: string;
  timestamp: string;
}): Promise<void> {
  // In production, this would send to PagerDuty/Slack/etc.
  monitoring.log('error', `🚨 CRITICAL ALERT: ${JSON.stringify(alert)}`);
}

// ============================================================================
// Express Middleware
// ============================================================================

/**
 * Enhanced error handler middleware with recovery options
 */
export function enhancedErrorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const requestId = req.headers['x-request-id'] as string || 'unknown';
  const path = req.path;
  const method = req.method;

  // Categorize error
  let statusCode = 500;
  let errorCode: ErrorCode = ErrorCode.INTERNAL_ERROR;
  let message = 'An unexpected error occurred';
  let recoverable = false;

  if (err instanceof AppError) {
    statusCode = err.statusCode;
    errorCode = err.code;
    message = err.message;
  } else if (err.message.includes('rate limit')) {
    statusCode = 429;
    errorCode = ErrorCode.FORBIDDEN;
    message = 'Rate limit exceeded. Please try again later.';
    recoverable = true;
  } else if (err.message.includes('ECONNREFUSED') || err.message.includes('ETIMEDOUT')) {
    statusCode = 503;
    errorCode = ErrorCode.INTERNAL_ERROR;
    message = 'Service temporarily unavailable. Please retry.';
    recoverable = true;
  } else if (err.message.includes('circuit')) {
    statusCode = 503;
    errorCode = ErrorCode.INTERNAL_ERROR;
    message = 'Service is experiencing issues. Please try again in a few minutes.';
    recoverable = true;
  }

  // Log with context
  monitoring.log('error', `Error in ${method} ${path}: ${err.message}`, {
    requestId,
    statusCode,
    errorCode,
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined
  });

  // Record metric
  monitoring.recordError(err.name || 'Error', path);

  // Build response
  const response = {
    success: false,
    error: {
      code: errorCode,
      message,
      requestId,
      recoverable,
      retryAfter: recoverable ? 30 : undefined // Suggest retry after 30s
    }
  };

  // Include stack in development
  if (process.env.NODE_ENV === 'development' && err.stack) {
    (response.error as any).stack = err.stack;
  }

  res.status(statusCode).json(response);
}

/**
 * Async handler wrapper with automatic error recovery
 */
export function asyncHandlerWithRecovery(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<any>,
  options: {
    cache?: RedisCacheService;
    cacheKeyGenerator?: (req: Request) => string;
    fallbackResponse?: any;
  } = {}
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      await fn(req, res, next);
    } catch (error) {
      // Try cache fallback if available
      if (options.cache && options.cacheKeyGenerator) {
        const cacheKey = options.cacheKeyGenerator(req);
        const cached = await options.cache.get(cacheKey);

        if (cached) {
          monitoring.log('info', `Serving cached response for ${req.path}`);
          return res.json({
            ...(cached as Record<string, any>),
            _meta: {
              source: 'cache',
              warning: 'This response was served from cache due to a service issue'
            }
          });
        }
      }

      // Use fallback response if provided
      if (options.fallbackResponse) {
        monitoring.log('info', `Serving fallback response for ${req.path}`);
        return res.json({
          ...options.fallbackResponse,
          _meta: {
            source: 'fallback',
            warning: 'This is a default response due to a service issue'
          }
        });
      }

      next(error);
    }
  };
}

export default {
  enhancedErrorHandler,
  asyncHandlerWithRecovery,
  handleMLServiceFailure,
  handleDatabaseFailure,
  handleMetaAPIRateLimit,
  handleRAGIndexingFailure,
  handleBudgetUpdateFailure
};
