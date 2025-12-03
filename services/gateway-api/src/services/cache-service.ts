/**
 * Semantic Cache Service - Redis-backed caching for AI evaluations and pattern searches
 *
 * ============================================================================
 * ✅ REDIS CACHING LAYER (December 2024)
 * ============================================================================
 *
 * PURPOSE:
 * - Cache expensive AI operations (Gemini analysis, scoring)
 * - Cache pattern searches across ad intelligence sources
 * - Reduce latency and API costs
 * - Track cache performance metrics
 *
 * FEATURES:
 * - TTL-based expiration
 * - Cache-aside pattern with getOrCompute()
 * - Semantic query hashing for consistent keys
 * - Hit rate and performance tracking
 * - Automatic JSON serialization
 *
 * CACHE STRATEGY:
 * - Analysis results: 1 hour TTL (stable video content)
 * - Scoring results: 1 hour TTL (deterministic calculations)
 * - Search results: 15 min TTL (dynamic data sources)
 *
 * ============================================================================
 */

import { createClient, RedisClientType } from 'redis';
import * as crypto from 'crypto';

interface CacheStats {
  hits: number;
  misses: number;
  hit_rate: number;
  total_requests: number;
  keys_count: number;
  memory_usage?: string;
  uptime_seconds: number;
}

interface CacheOptions {
  ttl?: number; // Time to live in seconds
  prefix?: string; // Key prefix for namespacing
}

export class SemanticCache {
  private client: RedisClientType;
  private hits: number = 0;
  private misses: number = 0;
  private startTime: number;
  private keyPrefix: string;

  constructor(redisClient: RedisClientType, options: CacheOptions = {}) {
    this.client = redisClient;
    this.keyPrefix = options.prefix || 'cache';
    this.startTime = Date.now();
  }

  /**
   * Store a value in cache with TTL
   * @param key - Cache key
   * @param value - Value to cache (will be JSON serialized)
   * @param ttl - Time to live in seconds (default: 3600 = 1 hour)
   */
  async set(key: string, value: any, ttl: number = 3600): Promise<void> {
    try {
      const fullKey = this.buildKey(key);
      const serialized = JSON.stringify(value);

      await this.client.setEx(fullKey, ttl, serialized);

      console.log(`[Cache] SET ${fullKey} (TTL: ${ttl}s)`);
    } catch (error: any) {
      console.error(`[Cache] SET failed for ${key}:`, error.message);
      // Don't throw - cache failures shouldn't break the application
    }
  }

  /**
   * Retrieve a value from cache
   * @param key - Cache key
   * @returns Cached value or null if not found
   */
  async get(key: string): Promise<any | null> {
    try {
      const fullKey = this.buildKey(key);
      const cached = await this.client.get(fullKey);

      if (cached) {
        this.hits++;
        console.log(`[Cache] HIT ${fullKey}`);
        return JSON.parse(cached);
      } else {
        this.misses++;
        console.log(`[Cache] MISS ${fullKey}`);
        return null;
      }
    } catch (error: any) {
      console.error(`[Cache] GET failed for ${key}:`, error.message);
      this.misses++;
      return null;
    }
  }

  /**
   * Cache-aside pattern: Get from cache or compute and store
   * @param key - Cache key
   * @param computeFn - Async function to compute value if not cached
   * @param ttl - Time to live in seconds
   * @returns Cached or computed value
   */
  async getOrCompute<T>(
    key: string,
    computeFn: () => Promise<T>,
    ttl: number = 3600
  ): Promise<T> {
    // Try to get from cache first
    const cached = await this.get(key);

    if (cached !== null) {
      return cached as T;
    }

    // Cache miss - compute the value
    console.log(`[Cache] Computing value for ${key}`);
    const computed = await computeFn();

    // Store in cache for next time
    await this.set(key, computed, ttl);

    return computed;
  }

  /**
   * Create a consistent cache key from a query object
   * Uses SHA256 hash of sorted JSON to ensure same queries produce same keys
   * @param query - Query object or string
   * @returns Hashed cache key
   */
  hashQuery(query: any): string {
    try {
      // Convert to string and sort keys for consistency
      const normalized = typeof query === 'string'
        ? query
        : JSON.stringify(this.sortObject(query));

      // Create SHA256 hash
      const hash = crypto
        .createHash('sha256')
        .update(normalized)
        .digest('hex')
        .substring(0, 16); // Use first 16 chars for readability

      return hash;
    } catch (error: any) {
      console.error('[Cache] Hash generation failed:', error.message);
      // Fallback to simple string conversion
      return String(query).substring(0, 32);
    }
  }

  /**
   * Get cache statistics
   * @returns Cache performance metrics
   */
  async getCacheStats(): Promise<CacheStats> {
    const totalRequests = this.hits + this.misses;
    const hitRate = totalRequests > 0 ? this.hits / totalRequests : 0;

    const stats: CacheStats = {
      hits: this.hits,
      misses: this.misses,
      hit_rate: Math.round(hitRate * 100) / 100,
      total_requests: totalRequests,
      keys_count: 0,
      uptime_seconds: Math.floor((Date.now() - this.startTime) / 1000)
    };

    try {
      // Get Redis info
      const info = await this.client.info('stats');

      // Count keys with our prefix
      const keys = await this.client.keys(`${this.keyPrefix}:*`);
      stats.keys_count = keys.length;

      // Extract memory usage if available
      const memoryInfo = await this.client.info('memory');
      const memoryMatch = memoryInfo.match(/used_memory_human:(\S+)/);
      if (memoryMatch) {
        stats.memory_usage = memoryMatch[1];
      }
    } catch (error: any) {
      console.warn('[Cache] Could not fetch Redis stats:', error.message);
    }

    return stats;
  }

  /**
   * Invalidate a specific cache key
   * @param key - Cache key to invalidate
   */
  async invalidate(key: string): Promise<void> {
    try {
      const fullKey = this.buildKey(key);
      await this.client.del(fullKey);
      console.log(`[Cache] INVALIDATED ${fullKey}`);
    } catch (error: any) {
      console.error(`[Cache] Invalidation failed for ${key}:`, error.message);
    }
  }

  /**
   * Clear all cache keys with this service's prefix
   */
  async clear(): Promise<void> {
    try {
      const keys = await this.client.keys(`${this.keyPrefix}:*`);
      if (keys.length > 0) {
        await this.client.del(keys);
        console.log(`[Cache] CLEARED ${keys.length} keys`);
      }
    } catch (error: any) {
      console.error('[Cache] Clear failed:', error.message);
    }
  }

  /**
   * Build full cache key with prefix
   */
  private buildKey(key: string): string {
    return `${this.keyPrefix}:${key}`;
  }

  /**
   * Sort object keys recursively for consistent hashing
   */
  private sortObject(obj: any): any {
    if (typeof obj !== 'object' || obj === null) {
      return obj;
    }

    if (Array.isArray(obj)) {
      return obj.map(item => this.sortObject(item));
    }

    const sorted: any = {};
    Object.keys(obj)
      .sort()
      .forEach(key => {
        sorted[key] = this.sortObject(obj[key]);
      });

    return sorted;
  }

  /**
   * Reset statistics (useful for testing)
   */
  resetStats(): void {
    this.hits = 0;
    this.misses = 0;
    this.startTime = Date.now();
  }
}

/**
 * Factory function to create a cache service with standard configuration
 */
export function createCacheService(
  redisClient: RedisClientType,
  options: CacheOptions = {}
): SemanticCache {
  return new SemanticCache(redisClient, {
    prefix: options.prefix || 'geminivideo',
    ...options
  });
}
