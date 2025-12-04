import { RedisCacheService } from './redis-cache';
import { logger } from '../utils/logger';

export interface RedisConfig {
  url: string;
  clusterNodes?: string[];
  enabled: boolean;
}

/**
 * Get Redis configuration from environment variables
 */
export function getRedisConfig(): RedisConfig {
  const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
  const clusterNodes = process.env.REDIS_CLUSTER_NODES?.split(',').filter(Boolean);
  const enabled = process.env.REDIS_ENABLED !== 'false';

  return {
    url: redisUrl,
    clusterNodes,
    enabled,
  };
}

/**
 * Singleton instance of Redis cache service
 */
let cacheServiceInstance: RedisCacheService | null = null;

/**
 * Initialize and get Redis cache service
 */
export function getRedisCacheService(): RedisCacheService | null {
  if (cacheServiceInstance) {
    return cacheServiceInstance;
  }

  const config = getRedisConfig();

  if (!config.enabled) {
    logger.warn('Redis cache is disabled');
    return null;
  }

  try {
    cacheServiceInstance = new RedisCacheService(config.url, config.clusterNodes);
    logger.info('Redis cache service initialized successfully');
    return cacheServiceInstance;
  } catch (error) {
    logger.error('Failed to initialize Redis cache service:', error);
    return null;
  }
}

/**
 * Gracefully shutdown Redis connections
 */
export async function shutdownRedis(): Promise<void> {
  if (cacheServiceInstance) {
    await cacheServiceInstance.disconnect();
    cacheServiceInstance = null;
  }
}

/**
 * Health check for Redis
 */
export async function checkRedisHealth(): Promise<{
  status: 'healthy' | 'unhealthy';
  latency?: number;
  error?: string;
}> {
  if (!cacheServiceInstance) {
    return { status: 'unhealthy', error: 'Redis not initialized' };
  }

  const startTime = Date.now();
  try {
    const isHealthy = await cacheServiceInstance.ping();
    const latency = Date.now() - startTime;

    if (isHealthy) {
      return { status: 'healthy', latency };
    } else {
      return { status: 'unhealthy', error: 'Ping failed' };
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
