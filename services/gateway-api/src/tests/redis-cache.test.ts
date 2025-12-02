/**
 * Redis Cache Service Tests
 *
 * Run with: npm test -- redis-cache.test.ts
 */

import { RedisCacheService, SessionData } from '../services/redis-cache';

describe('RedisCacheService', () => {
  let cacheService: RedisCacheService;
  const testRedisUrl = process.env.REDIS_URL || 'redis://localhost:6379';

  beforeAll(() => {
    cacheService = new RedisCacheService(testRedisUrl);
  });

  afterAll(async () => {
    await cacheService.disconnect();
  });

  afterEach(async () => {
    // Clean up test keys
    await cacheService.invalidatePattern('test:*');
  });

  describe('Basic Cache Operations', () => {
    test('should set and get a value', async () => {
      const key = 'test:basic:set-get';
      const value = { name: 'John Doe', age: 30 };

      await cacheService.set(key, value, 60);
      const retrieved = await cacheService.get<typeof value>(key);

      expect(retrieved).toEqual(value);
    });

    test('should return null for non-existent key', async () => {
      const result = await cacheService.get('test:non-existent');
      expect(result).toBeNull();
    });

    test('should delete a key', async () => {
      const key = 'test:basic:delete';
      await cacheService.set(key, 'value', 60);

      await cacheService.delete(key);
      const result = await cacheService.get(key);

      expect(result).toBeNull();
    });

    test('should check key existence', async () => {
      const key = 'test:basic:exists';

      await cacheService.set(key, 'value', 60);
      expect(await cacheService.exists(key)).toBe(true);

      await cacheService.delete(key);
      expect(await cacheService.exists(key)).toBe(false);
    });

    test('should respect TTL', async () => {
      const key = 'test:basic:ttl';
      await cacheService.set(key, 'value', 1); // 1 second TTL

      expect(await cacheService.exists(key)).toBe(true);

      // Wait for expiration
      await new Promise(resolve => setTimeout(resolve, 1500));

      expect(await cacheService.exists(key)).toBe(false);
    }, 10000);
  });

  describe('Session Management', () => {
    test('should set and get session', async () => {
      const sessionId = 'test-session-123';
      const sessionData: SessionData = {
        userId: 'user-456',
        email: 'test@example.com',
        roles: ['user', 'admin'],
        metadata: { loginTime: Date.now() },
        createdAt: Date.now(),
        lastAccessedAt: Date.now(),
      };

      await cacheService.setSession(sessionId, sessionData, 3600);
      const retrieved = await cacheService.getSession(sessionId);

      expect(retrieved).toBeDefined();
      expect(retrieved?.userId).toBe(sessionData.userId);
      expect(retrieved?.email).toBe(sessionData.email);
      expect(retrieved?.roles).toEqual(sessionData.roles);
    });

    test('should update lastAccessedAt on get', async () => {
      const sessionId = 'test-session-456';
      const sessionData: SessionData = {
        userId: 'user-789',
        email: 'test2@example.com',
        createdAt: Date.now(),
        lastAccessedAt: Date.now(),
      };

      await cacheService.setSession(sessionId, sessionData, 3600);
      await new Promise(resolve => setTimeout(resolve, 100));

      const retrieved = await cacheService.getSession(sessionId);
      expect(retrieved?.lastAccessedAt).toBeGreaterThan(sessionData.lastAccessedAt);
    });

    test('should delete session', async () => {
      const sessionId = 'test-session-789';
      const sessionData: SessionData = {
        userId: 'user-101',
        email: 'test3@example.com',
        createdAt: Date.now(),
        lastAccessedAt: Date.now(),
      };

      await cacheService.setSession(sessionId, sessionData, 3600);
      await cacheService.deleteSession(sessionId);

      const retrieved = await cacheService.getSession(sessionId);
      expect(retrieved).toBeNull();
    });
  });

  describe('Rate Limiting', () => {
    test('should allow requests within limit', async () => {
      const key = 'test:ratelimit:allow';
      const limit = 5;
      const windowSeconds = 60;

      for (let i = 0; i < limit; i++) {
        const result = await cacheService.checkRateLimit(key, limit, windowSeconds);
        expect(result.allowed).toBe(true);
        expect(result.remaining).toBe(limit - i - 1);
      }
    });

    test('should block requests exceeding limit', async () => {
      const key = 'test:ratelimit:block';
      const limit = 3;
      const windowSeconds = 60;

      // Make limit requests
      for (let i = 0; i < limit; i++) {
        await cacheService.checkRateLimit(key, limit, windowSeconds);
      }

      // Next request should be blocked
      const result = await cacheService.checkRateLimit(key, limit, windowSeconds);
      expect(result.allowed).toBe(false);
      expect(result.remaining).toBe(0);
    });

    test('should reset after window expires', async () => {
      const key = 'test:ratelimit:reset';
      const limit = 2;
      const windowSeconds = 1; // 1 second window

      // Exhaust limit
      await cacheService.checkRateLimit(key, limit, windowSeconds);
      await cacheService.checkRateLimit(key, limit, windowSeconds);

      // Should be blocked
      let result = await cacheService.checkRateLimit(key, limit, windowSeconds);
      expect(result.allowed).toBe(false);

      // Wait for window to expire
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Should be allowed again
      result = await cacheService.checkRateLimit(key, limit, windowSeconds);
      expect(result.allowed).toBe(true);
    }, 10000);
  });

  describe('Cache Patterns', () => {
    test('getOrSet should return cached value', async () => {
      const key = 'test:pattern:cached';
      let factoryCalls = 0;

      const factory = async () => {
        factoryCalls++;
        return { data: 'test' };
      };

      // First call should execute factory
      const result1 = await cacheService.getOrSet(key, factory, 60);
      expect(result1).toEqual({ data: 'test' });
      expect(factoryCalls).toBe(1);

      // Second call should use cache
      const result2 = await cacheService.getOrSet(key, factory, 60);
      expect(result2).toEqual({ data: 'test' });
      expect(factoryCalls).toBe(1); // Factory not called again
    });

    test('should invalidate pattern', async () => {
      // Create multiple keys with same pattern
      await cacheService.set('test:pattern:invalidate:1', 'value1', 60);
      await cacheService.set('test:pattern:invalidate:2', 'value2', 60);
      await cacheService.set('test:pattern:invalidate:3', 'value3', 60);

      // Invalidate all
      const count = await cacheService.invalidatePattern('test:pattern:invalidate:*');
      expect(count).toBe(3);

      // Verify deletion
      expect(await cacheService.exists('test:pattern:invalidate:1')).toBe(false);
      expect(await cacheService.exists('test:pattern:invalidate:2')).toBe(false);
      expect(await cacheService.exists('test:pattern:invalidate:3')).toBe(false);
    });
  });

  describe('Job Queue', () => {
    test('should enqueue and dequeue jobs', async () => {
      const queueName = 'test-queue';
      const job = {
        type: 'email',
        to: 'test@example.com',
        subject: 'Test',
      };

      const jobId = await cacheService.enqueue(queueName, job);
      expect(jobId).toBeDefined();

      const dequeuedJob = await cacheService.dequeue(queueName);
      expect(dequeuedJob).toBeDefined();
      expect(dequeuedJob?.payload).toEqual(job);
    });

    test('should return null when queue is empty', async () => {
      const queueName = 'empty-queue';
      const result = await cacheService.dequeue(queueName);
      expect(result).toBeNull();
    });

    test('should maintain FIFO order', async () => {
      const queueName = 'test-fifo-queue';

      await cacheService.enqueue(queueName, { order: 1 });
      await cacheService.enqueue(queueName, { order: 2 });
      await cacheService.enqueue(queueName, { order: 3 });

      const job1 = await cacheService.dequeue(queueName);
      const job2 = await cacheService.dequeue(queueName);
      const job3 = await cacheService.dequeue(queueName);

      expect(job1?.payload.order).toBe(1);
      expect(job2?.payload.order).toBe(2);
      expect(job3?.payload.order).toBe(3);
    });
  });

  describe('Distributed Locks', () => {
    test('should acquire and release lock', async () => {
      const lockKey = 'test:lock:basic';

      const lockId = await cacheService.acquireLock(lockKey, 10);
      expect(lockId).toBeDefined();

      const released = await cacheService.releaseLock(lockKey, lockId!);
      expect(released).toBe(true);
    });

    test('should prevent concurrent lock acquisition', async () => {
      const lockKey = 'test:lock:concurrent';

      const lockId1 = await cacheService.acquireLock(lockKey, 10);
      expect(lockId1).toBeDefined();

      // Second attempt should fail
      const lockId2 = await cacheService.acquireLock(lockKey, 10);
      expect(lockId2).toBeNull();

      // Release first lock
      await cacheService.releaseLock(lockKey, lockId1!);

      // Now should be able to acquire
      const lockId3 = await cacheService.acquireLock(lockKey, 10);
      expect(lockId3).toBeDefined();
    });

    test('should not release lock with wrong identifier', async () => {
      const lockKey = 'test:lock:wrong-id';

      const lockId = await cacheService.acquireLock(lockKey, 10);
      expect(lockId).toBeDefined();

      // Try to release with wrong ID
      const released = await cacheService.releaseLock(lockKey, 'wrong-id');
      expect(released).toBe(false);

      // Lock should still exist
      const lockId2 = await cacheService.acquireLock(lockKey, 10);
      expect(lockId2).toBeNull();
    });

    test('should auto-expire lock after TTL', async () => {
      const lockKey = 'test:lock:expire';

      const lockId = await cacheService.acquireLock(lockKey, 1); // 1 second TTL
      expect(lockId).toBeDefined();

      // Wait for lock to expire
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Should be able to acquire new lock
      const lockId2 = await cacheService.acquireLock(lockKey, 10);
      expect(lockId2).toBeDefined();
    }, 10000);
  });

  describe('Health Check', () => {
    test('should ping successfully', async () => {
      const result = await cacheService.ping();
      expect(result).toBe(true);
    });
  });

  describe('Pub/Sub', () => {
    test('should publish and receive messages', async () => {
      const channel = 'test:pubsub:basic';
      const testMessage = { event: 'test', data: 'hello' };

      let receivedMessage: any = null;

      // Subscribe
      await cacheService.subscribe(channel, (message) => {
        receivedMessage = message;
      });

      // Wait a bit for subscription to be ready
      await new Promise(resolve => setTimeout(resolve, 100));

      // Publish
      await cacheService.publish(channel, testMessage);

      // Wait for message to be received
      await new Promise(resolve => setTimeout(resolve, 200));

      expect(receivedMessage).toEqual(testMessage);
    }, 10000);
  });
});
