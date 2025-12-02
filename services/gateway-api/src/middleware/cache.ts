import { Request, Response, NextFunction } from 'express';
import { RedisCacheService } from '../services/redis-cache';
import { logger } from '../logger';
import crypto from 'crypto';

export interface CacheOptions {
  ttlSeconds: number;
  keyPrefix?: string;
  includeQueryParams?: boolean;
  includeHeaders?: string[];
  excludeParams?: string[];
  statusCodesToCache?: number[];
  varyByUser?: boolean;
  skipCache?: (req: Request) => boolean;
}

export interface CacheStats {
  hits: number;
  misses: number;
  errors: number;
  lastReset: number;
}

export class CacheMiddleware {
  private cacheService: RedisCacheService;
  private stats: CacheStats = {
    hits: 0,
    misses: 0,
    errors: 0,
    lastReset: Date.now(),
  };

  constructor(cacheService: RedisCacheService) {
    this.cacheService = cacheService;
  }

  /**
   * Creates a cache middleware with the specified options
   */
  cache(options: CacheOptions) {
    return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
      try {
        // Skip cache if specified
        if (options.skipCache && options.skipCache(req)) {
          return next();
        }

        // Only cache GET and HEAD requests
        if (req.method !== 'GET' && req.method !== 'HEAD') {
          return next();
        }

        // Generate cache key
        const cacheKey = this.generateCacheKey(req, options);

        // Try to get from cache
        const cachedResponse = await this.cacheService.get<CachedResponse>(cacheKey);

        if (cachedResponse) {
          // Cache hit
          this.stats.hits++;
          logger.debug(`Cache HIT for key: ${cacheKey}`);

          // Set cache headers
          res.set('X-Cache', 'HIT');
          res.set('X-Cache-Key', cacheKey);

          // Set original headers
          if (cachedResponse.headers) {
            Object.entries(cachedResponse.headers).forEach(([key, value]) => {
              res.set(key, value);
            });
          }

          // Send cached response
          res.status(cachedResponse.statusCode).send(cachedResponse.body);
          return;
        }

        // Cache miss
        this.stats.misses++;
        logger.debug(`Cache MISS for key: ${cacheKey}`);

        // Intercept response
        const originalSend = res.send.bind(res);
        const originalJson = res.json.bind(res);

        res.send = (body: any): Response => {
          this.cacheResponse(cacheKey, res, body, options);
          return originalSend(body);
        };

        res.json = (body: any): Response => {
          this.cacheResponse(cacheKey, res, body, options);
          return originalJson(body);
        };

        res.set('X-Cache', 'MISS');
        res.set('X-Cache-Key', cacheKey);

        next();
      } catch (error) {
        this.stats.errors++;
        logger.error('Cache middleware error:', error);
        // Continue without cache on error
        next();
      }
    };
  }

  /**
   * Generates a cache key based on request parameters
   */
  private generateCacheKey(req: Request, options: CacheOptions): string {
    const parts: string[] = [];

    // Add prefix
    if (options.keyPrefix) {
      parts.push(options.keyPrefix);
    }

    // Add path
    parts.push(req.path);

    // Add query parameters
    if (options.includeQueryParams && Object.keys(req.query).length > 0) {
      const filteredQuery = { ...req.query };

      // Exclude specified params
      if (options.excludeParams) {
        options.excludeParams.forEach(param => {
          delete filteredQuery[param];
        });
      }

      // Sort for consistency
      const sortedQuery = Object.keys(filteredQuery)
        .sort()
        .reduce((acc, key) => {
          acc[key] = filteredQuery[key];
          return acc;
        }, {} as Record<string, any>);

      if (Object.keys(sortedQuery).length > 0) {
        parts.push(JSON.stringify(sortedQuery));
      }
    }

    // Add headers
    if (options.includeHeaders && options.includeHeaders.length > 0) {
      const headers = options.includeHeaders
        .map(header => `${header}:${req.get(header) || ''}`)
        .join(',');
      parts.push(headers);
    }

    // Add user identifier if needed
    if (options.varyByUser) {
      const userId = this.extractUserId(req);
      if (userId) {
        parts.push(`user:${userId}`);
      }
    }

    // Generate hash for long keys
    const keyString = parts.join(':');
    if (keyString.length > 200) {
      const hash = crypto.createHash('sha256').update(keyString).digest('hex');
      return `cache:${options.keyPrefix || 'default'}:${hash}`;
    }

    return `cache:${keyString}`;
  }

  /**
   * Caches the response
   */
  private async cacheResponse(
    cacheKey: string,
    res: Response,
    body: any,
    options: CacheOptions
  ): Promise<void> {
    try {
      // Check if status code should be cached
      const statusCodesToCache = options.statusCodesToCache || [200];
      if (!statusCodesToCache.includes(res.statusCode)) {
        logger.debug(`Not caching response with status ${res.statusCode}`);
        return;
      }

      // Prepare cached response
      const cachedResponse: CachedResponse = {
        statusCode: res.statusCode,
        body,
        headers: this.extractCacheableHeaders(res),
        cachedAt: Date.now(),
      };

      // Store in cache
      await this.cacheService.set(cacheKey, cachedResponse, options.ttlSeconds);
      logger.debug(`Cached response for key: ${cacheKey} (TTL: ${options.ttlSeconds}s)`);
    } catch (error) {
      logger.error('Error caching response:', error);
    }
  }

  /**
   * Extracts headers that should be cached
   */
  private extractCacheableHeaders(res: Response): Record<string, string> {
    const cacheableHeaders = [
      'content-type',
      'content-length',
      'etag',
      'last-modified',
      'cache-control',
    ];

    const headers: Record<string, string> = {};

    cacheableHeaders.forEach(header => {
      const value = res.get(header);
      if (value) {
        headers[header] = value;
      }
    });

    return headers;
  }

  /**
   * Extracts user ID from request (customize based on your auth)
   */
  private extractUserId(req: Request): string | null {
    // Check common auth patterns
    const authHeader = req.get('Authorization');
    if (authHeader) {
      // Extract from Bearer token, session, etc.
      // This is a placeholder - implement based on your auth strategy
      return crypto.createHash('md5').update(authHeader).digest('hex');
    }

    // Check session
    const session = (req as any).session;
    if (session?.userId) {
      return session.userId;
    }

    return null;
  }

  /**
   * Invalidates cache by key
   */
  async invalidate(key: string): Promise<void> {
    try {
      await this.cacheService.delete(key);
      logger.info(`Invalidated cache key: ${key}`);
    } catch (error) {
      logger.error(`Error invalidating cache key ${key}:`, error);
    }
  }

  /**
   * Invalidates cache by pattern
   */
  async invalidatePattern(pattern: string): Promise<number> {
    try {
      const count = await this.cacheService.invalidatePattern(pattern);
      logger.info(`Invalidated ${count} cache keys matching pattern: ${pattern}`);
      return count;
    } catch (error) {
      logger.error(`Error invalidating cache pattern ${pattern}:`, error);
      return 0;
    }
  }

  /**
   * Invalidates cache for a specific route
   */
  async invalidateRoute(route: string): Promise<number> {
    const pattern = `cache:*:${route}*`;
    return this.invalidatePattern(pattern);
  }

  /**
   * Warms cache with predefined data
   */
  async warmCache(
    key: string,
    data: any,
    ttlSeconds: number,
    statusCode: number = 200
  ): Promise<void> {
    try {
      const cachedResponse: CachedResponse = {
        statusCode,
        body: data,
        headers: { 'content-type': 'application/json' },
        cachedAt: Date.now(),
      };

      await this.cacheService.set(key, cachedResponse, ttlSeconds);
      logger.info(`Warmed cache for key: ${key}`);
    } catch (error) {
      logger.error(`Error warming cache for key ${key}:`, error);
    }
  }

  /**
   * Gets cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Resets cache statistics
   */
  resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      errors: 0,
      lastReset: Date.now(),
    };
  }

  /**
   * Gets cache hit rate
   */
  getHitRate(): number {
    const total = this.stats.hits + this.stats.misses;
    if (total === 0) return 0;
    return (this.stats.hits / total) * 100;
  }
}

interface CachedResponse {
  statusCode: number;
  body: any;
  headers: Record<string, string>;
  cachedAt: number;
}

/**
 * Middleware to set cache control headers
 */
export function setCacheHeaders(maxAge: number, options?: {
  public?: boolean;
  mustRevalidate?: boolean;
  noStore?: boolean;
  noCache?: boolean;
}) {
  return (req: Request, res: Response, next: NextFunction): void => {
    const directives: string[] = [];

    if (options?.noStore) {
      directives.push('no-store');
    } else if (options?.noCache) {
      directives.push('no-cache');
    } else {
      directives.push(options?.public ? 'public' : 'private');
      directives.push(`max-age=${maxAge}`);
    }

    if (options?.mustRevalidate) {
      directives.push('must-revalidate');
    }

    res.set('Cache-Control', directives.join(', '));
    next();
  };
}

/**
 * Middleware to disable caching
 */
export function noCache() {
  return (req: Request, res: Response, next: NextFunction): void => {
    res.set({
      'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0',
      'Surrogate-Control': 'no-store',
    });
    next();
  };
}

/**
 * Creates a cache key for manual cache operations
 */
export function createCacheKey(...parts: (string | number)[]): string {
  return `cache:${parts.join(':')}`;
}
