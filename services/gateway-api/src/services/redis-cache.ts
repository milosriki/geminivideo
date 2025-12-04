import Redis, { RedisOptions, Cluster } from 'ioredis';
import { logger } from '../logger';

export interface SessionData {
  userId: string;
  email?: string;
  roles?: string[];
  metadata?: Record<string, any>;
  createdAt: number;
  lastAccessedAt: number;
}

export interface RateLimitResult {
  allowed: boolean;
  remaining: number;
  resetAt: number;
}

export interface JobData {
  id: string;
  type: string;
  payload: any;
  createdAt: number;
  retries?: number;
}

export class RedisCacheService {
  private client: Redis | Cluster;
  private subscriber: Redis | Cluster;
  private isCluster: boolean;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;
  private reconnectDelay: number = 1000;

  constructor(redisUrl: string, clusterNodes?: string[]) {
    this.isCluster = !!clusterNodes && clusterNodes.length > 0;

    const baseOptions: RedisOptions = {
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      enableOfflineQueue: true,
      retryStrategy: (times: number) => {
        if (times > this.maxReconnectAttempts) {
          logger.error('Redis max reconnection attempts reached');
          return null;
        }
        const delay = Math.min(times * this.reconnectDelay, 10000);
        logger.warn(`Redis reconnecting in ${delay}ms (attempt ${times})`);
        return delay;
      },
      reconnectOnError: (err: Error) => {
        const targetErrors = ['READONLY', 'ECONNREFUSED', 'ETIMEDOUT'];
        if (targetErrors.some(targetError => err.message.includes(targetError))) {
          logger.warn('Redis reconnecting due to error:', err.message);
          return true;
        }
        return false;
      },
    };

    if (this.isCluster) {
      // Cluster mode with connection pooling
      this.client = new Redis.Cluster(
        clusterNodes!.map(node => {
          const [host, port] = node.split(':');
          return { host, port: parseInt(port, 10) };
        }),
        {
          redisOptions: baseOptions,
          clusterRetryStrategy: (times: number) => {
            return Math.min(times * 100, 2000);
          },
          enableOfflineQueue: true,
          scaleReads: 'slave',
        }
      );

      this.subscriber = new Redis.Cluster(
        clusterNodes!.map(node => {
          const [host, port] = node.split(':');
          return { host, port: parseInt(port, 10) };
        }),
        {
          redisOptions: baseOptions,
        }
      );
    } else {
      // Single instance with connection pooling
      this.client = new Redis(redisUrl, baseOptions);
      this.subscriber = new Redis(redisUrl, baseOptions);
    }

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.client.on('connect', () => {
      logger.info('Redis client connected');
      this.reconnectAttempts = 0;
    });

    this.client.on('ready', () => {
      logger.info('Redis client ready');
    });

    this.client.on('error', (err: Error) => {
      logger.error('Redis client error:', err);
      this.reconnectAttempts++;
    });

    this.client.on('close', () => {
      logger.warn('Redis client connection closed');
    });

    this.client.on('reconnecting', () => {
      logger.info('Redis client reconnecting...');
    });

    this.subscriber.on('error', (err: Error) => {
      logger.error('Redis subscriber error:', err);
    });

    this.subscriber.on('message', (channel: string, message: string) => {
      logger.debug(`Received message from channel ${channel}`);
    });
  }

  // Basic cache operations
  async get<T>(key: string): Promise<T | null> {
    try {
      const value = await this.client.get(key);
      if (!value) return null;
      return JSON.parse(value) as T;
    } catch (error) {
      logger.error(`Error getting key ${key}:`, error);
      return null;
    }
  }

  async set(key: string, value: any, ttlSeconds?: number): Promise<void> {
    try {
      const serialized = JSON.stringify(value);
      if (ttlSeconds) {
        await this.client.setex(key, ttlSeconds, serialized);
      } else {
        await this.client.set(key, serialized);
      }
    } catch (error) {
      logger.error(`Error setting key ${key}:`, error);
      throw error;
    }
  }

  async delete(key: string): Promise<void> {
    try {
      await this.client.del(key);
    } catch (error) {
      logger.error(`Error deleting key ${key}:`, error);
      throw error;
    }
  }

  async exists(key: string): Promise<boolean> {
    try {
      const result = await this.client.exists(key);
      return result === 1;
    } catch (error) {
      logger.error(`Error checking existence of key ${key}:`, error);
      return false;
    }
  }

  // Session management
  async setSession(sessionId: string, data: SessionData, ttlSeconds: number): Promise<void> {
    try {
      const key = `session:${sessionId}`;
      const sessionData = {
        ...data,
        lastAccessedAt: Date.now(),
      };
      await this.set(key, sessionData, ttlSeconds);
    } catch (error) {
      logger.error(`Error setting session ${sessionId}:`, error);
      throw error;
    }
  }

  async getSession(sessionId: string): Promise<SessionData | null> {
    try {
      const key = `session:${sessionId}`;
      const session = await this.get<SessionData>(key);
      if (session) {
        // Update last accessed time
        session.lastAccessedAt = Date.now();
        const ttl = await this.client.ttl(key);
        if (ttl > 0) {
          await this.set(key, session, ttl);
        }
      }
      return session;
    } catch (error) {
      logger.error(`Error getting session ${sessionId}:`, error);
      return null;
    }
  }

  async deleteSession(sessionId: string): Promise<void> {
    try {
      const key = `session:${sessionId}`;
      await this.delete(key);
    } catch (error) {
      logger.error(`Error deleting session ${sessionId}:`, error);
      throw error;
    }
  }

  // Rate limiting using sliding window
  async checkRateLimit(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<RateLimitResult> {
    try {
      const now = Date.now();
      const windowStart = now - windowSeconds * 1000;
      const rateLimitKey = `ratelimit:${key}`;

      // Use Redis transaction for atomic operations
      const pipeline = this.client.pipeline();

      // Remove old entries outside the window
      pipeline.zremrangebyscore(rateLimitKey, '-inf', windowStart);

      // Count entries in current window
      pipeline.zcard(rateLimitKey);

      // Add current request
      pipeline.zadd(rateLimitKey, now, `${now}-${Math.random()}`);

      // Set expiry
      pipeline.expire(rateLimitKey, windowSeconds);

      const results = await pipeline.exec();

      if (!results) {
        throw new Error('Pipeline execution failed');
      }

      const count = (results[1][1] as number) || 0;
      const allowed = count < limit;
      const remaining = Math.max(0, limit - count - 1);
      const resetAt = now + windowSeconds * 1000;

      return { allowed, remaining, resetAt };
    } catch (error) {
      logger.error(`Error checking rate limit for ${key}:`, error);
      // Fail open - allow the request if Redis is down
      return { allowed: true, remaining: limit, resetAt: Date.now() };
    }
  }

  // Pub/Sub for real-time updates
  async publish(channel: string, message: any): Promise<void> {
    try {
      const serialized = JSON.stringify(message);
      await this.client.publish(channel, serialized);
    } catch (error) {
      logger.error(`Error publishing to channel ${channel}:`, error);
      throw error;
    }
  }

  async subscribe(channel: string, callback: (message: any) => void): Promise<void> {
    try {
      await this.subscriber.subscribe(channel);

      this.subscriber.on('message', (ch: string, msg: string) => {
        if (ch === channel) {
          try {
            const parsed = JSON.parse(msg);
            callback(parsed);
          } catch (error) {
            logger.error(`Error parsing message from channel ${channel}:`, error);
          }
        }
      });
    } catch (error) {
      logger.error(`Error subscribing to channel ${channel}:`, error);
      throw error;
    }
  }

  // Cache patterns
  async getOrSet<T>(
    key: string,
    factory: () => Promise<T>,
    ttlSeconds: number
  ): Promise<T> {
    try {
      // Try to get from cache first
      const cached = await this.get<T>(key);
      if (cached !== null) {
        return cached;
      }

      // Cache miss - execute factory function
      const value = await factory();

      // Store in cache
      await this.set(key, value, ttlSeconds);

      return value;
    } catch (error) {
      logger.error(`Error in getOrSet for key ${key}:`, error);
      throw error;
    }
  }

  async invalidatePattern(pattern: string): Promise<number> {
    try {
      let deleted = 0;

      if (this.isCluster) {
        // For cluster, we need to scan each node
        const nodes = (this.client as Cluster).nodes('master');

        for (const node of nodes) {
          let cursor = '0';
          do {
            const [newCursor, keys] = await node.scan(
              cursor,
              'MATCH',
              pattern,
              'COUNT',
              100
            );
            cursor = newCursor;

            if (keys.length > 0) {
              const result = await node.del(...keys);
              deleted += result;
            }
          } while (cursor !== '0');
        }
      } else {
        // For single instance
        let cursor = '0';
        do {
          const [newCursor, keys] = await (this.client as Redis).scan(
            cursor,
            'MATCH',
            pattern,
            'COUNT',
            100
          );
          cursor = newCursor;

          if (keys.length > 0) {
            const result = await this.client.del(...keys);
            deleted += result;
          }
        } while (cursor !== '0');
      }

      logger.info(`Invalidated ${deleted} keys matching pattern ${pattern}`);
      return deleted;
    } catch (error) {
      logger.error(`Error invalidating pattern ${pattern}:`, error);
      throw error;
    }
  }

  // Job queue support (simple implementation)
  async enqueue(queueName: string, job: any): Promise<string> {
    try {
      const jobId = `job:${Date.now()}:${Math.random().toString(36).substr(2, 9)}`;
      const jobData: JobData = {
        id: jobId,
        type: queueName,
        payload: job,
        createdAt: Date.now(),
        retries: 0,
      };

      const queueKey = `queue:${queueName}`;
      await this.client.rpush(queueKey, JSON.stringify(jobData));

      logger.debug(`Enqueued job ${jobId} to queue ${queueName}`);
      return jobId;
    } catch (error) {
      logger.error(`Error enqueuing job to ${queueName}:`, error);
      throw error;
    }
  }

  async dequeue(queueName: string): Promise<JobData | null> {
    try {
      const queueKey = `queue:${queueName}`;
      const result = await this.client.lpop(queueKey);

      if (!result) {
        return null;
      }

      const jobData = JSON.parse(result) as JobData;
      logger.debug(`Dequeued job ${jobData.id} from queue ${queueName}`);

      return jobData;
    } catch (error) {
      logger.error(`Error dequeuing from ${queueName}:`, error);
      return null;
    }
  }

  // Health check
  async ping(): Promise<boolean> {
    try {
      const result = await this.client.ping();
      return result === 'PONG';
    } catch (error) {
      logger.error('Redis ping failed:', error);
      return false;
    }
  }

  // Graceful shutdown
  async disconnect(): Promise<void> {
    try {
      await this.client.quit();
      await this.subscriber.quit();
      logger.info('Redis connections closed gracefully');
    } catch (error) {
      logger.error('Error disconnecting from Redis:', error);
      // Force disconnect
      this.client.disconnect();
      this.subscriber.disconnect();
    }
  }

  // Advanced: Distributed lock
  async acquireLock(
    lockKey: string,
    ttlSeconds: number,
    identifier?: string
  ): Promise<string | null> {
    try {
      const lockId = identifier || `${Date.now()}-${Math.random()}`;
      const key = `lock:${lockKey}`;

      const result = await this.client.set(key, lockId, 'EX', ttlSeconds, 'NX');

      if (result === 'OK') {
        return lockId;
      }
      return null;
    } catch (error) {
      logger.error(`Error acquiring lock ${lockKey}:`, error);
      return null;
    }
  }

  async releaseLock(lockKey: string, identifier: string): Promise<boolean> {
    try {
      const key = `lock:${lockKey}`;

      // Use Lua script to ensure atomic check and delete
      const script = `
        if redis.call("get", KEYS[1]) == ARGV[1] then
          return redis.call("del", KEYS[1])
        else
          return 0
        end
      `;

      const result = await this.client.eval(script, 1, key, identifier);
      return result === 1;
    } catch (error) {
      logger.error(`Error releasing lock ${lockKey}:`, error);
      return false;
    }
  }
}
