# Redis Cache Service Usage Guide

## Overview

The Redis cache service provides production-grade caching capabilities including:
- Basic cache operations
- Session management
- Rate limiting
- Pub/Sub messaging
- Job queue support
- Distributed locking
- Cluster support
- Automatic reconnection

## Setup

### Environment Variables

```bash
# Single Redis instance
REDIS_URL=redis://localhost:6379

# Redis Cluster (optional)
REDIS_CLUSTER_NODES=redis1:6379,redis2:6379,redis3:6379

# Enable/disable cache
REDIS_ENABLED=true
```

### Initialize Redis Cache

```typescript
import { getRedisCacheService } from './services/redis-config';

// Get singleton instance
const cache = getRedisCacheService();
```

## Basic Cache Operations

### Get/Set/Delete

```typescript
// Set with TTL
await cache.set('user:123', { name: 'John Doe' }, 3600); // 1 hour

// Get
const user = await cache.get<User>('user:123');

// Delete
await cache.delete('user:123');

// Check existence
const exists = await cache.exists('user:123');
```

### Cache-Aside Pattern

```typescript
// Get from cache or fetch from database
const user = await cache.getOrSet(
  `user:${userId}`,
  async () => {
    return await database.findUser(userId);
  },
  3600 // TTL: 1 hour
);
```

### Pattern-Based Invalidation

```typescript
// Invalidate all user caches
const count = await cache.invalidatePattern('user:*');
console.log(`Invalidated ${count} keys`);

// Invalidate specific pattern
await cache.invalidatePattern('cache:api:products:*');
```

## Session Management

```typescript
import { SessionData } from './services/redis-cache';

// Create session
const sessionData: SessionData = {
  userId: '123',
  email: 'user@example.com',
  roles: ['admin'],
  metadata: { loginTime: Date.now() },
  createdAt: Date.now(),
  lastAccessedAt: Date.now(),
};

await cache.setSession('session-id-123', sessionData, 86400); // 24 hours

// Get session (automatically updates lastAccessedAt)
const session = await cache.getSession('session-id-123');

// Delete session (logout)
await cache.deleteSession('session-id-123');
```

## Rate Limiting

```typescript
// Check rate limit (100 requests per minute)
const result = await cache.checkRateLimit(
  `api:user:${userId}`,
  100, // limit
  60   // window in seconds
);

if (!result.allowed) {
  throw new Error(`Rate limit exceeded. Try again in ${result.resetAt - Date.now()}ms`);
}

console.log(`Remaining requests: ${result.remaining}`);
```

## Pub/Sub Messaging

```typescript
// Subscribe to channel
await cache.subscribe('notifications', (message) => {
  console.log('Received notification:', message);
});

// Publish to channel
await cache.publish('notifications', {
  type: 'new_order',
  orderId: '12345',
  timestamp: Date.now(),
});
```

## Job Queue

```typescript
// Enqueue job
const jobId = await cache.enqueue('email-queue', {
  to: 'user@example.com',
  subject: 'Welcome',
  body: 'Welcome to our platform!',
});

// Dequeue and process job
const job = await cache.dequeue('email-queue');
if (job) {
  console.log(`Processing job ${job.id}:`, job.payload);
  // Process the job...
}
```

## Distributed Locking

```typescript
// Acquire lock
const lockId = await cache.acquireLock('process:report', 30); // 30 seconds TTL

if (lockId) {
  try {
    // Critical section - only one process will execute this
    await generateReport();
  } finally {
    // Release lock
    await cache.releaseLock('process:report', lockId);
  }
} else {
  console.log('Could not acquire lock - another process is running');
}
```

## Route-Level Caching Middleware

### Basic Usage

```typescript
import express from 'express';
import { CacheMiddleware } from './middleware/cache';
import { getRedisCacheService } from './services/redis-config';

const app = express();
const cache = getRedisCacheService();
const cacheMiddleware = new CacheMiddleware(cache!);

// Cache GET requests for 5 minutes
app.get(
  '/api/products',
  cacheMiddleware.cache({
    ttlSeconds: 300,
    keyPrefix: 'api:products',
    includeQueryParams: true,
  }),
  async (req, res) => {
    const products = await database.getProducts();
    res.json(products);
  }
);
```

### Advanced Caching Options

```typescript
// Cache with custom options
app.get(
  '/api/user/profile',
  cacheMiddleware.cache({
    ttlSeconds: 600,
    keyPrefix: 'api:user:profile',
    includeQueryParams: true,
    excludeParams: ['_', 'timestamp'], // Exclude cache-busting params
    statusCodesToCache: [200, 304],
    varyByUser: true, // Different cache per user
    includeHeaders: ['Accept-Language'], // Vary by language
    skipCache: (req) => {
      // Skip cache for admin users
      return req.get('X-Admin') === 'true';
    },
  }),
  async (req, res) => {
    const profile = await getUserProfile(req.userId);
    res.json(profile);
  }
);
```

### Cache Invalidation

```typescript
// Invalidate specific route
await cacheMiddleware.invalidateRoute('/api/products');

// Invalidate by pattern
await cacheMiddleware.invalidatePattern('cache:api:user:*');

// Invalidate specific key
await cacheMiddleware.invalidate('cache:api:products:123');
```

### Cache Warming

```typescript
// Pre-populate cache
await cacheMiddleware.warmCache(
  'cache:api:featured-products',
  await database.getFeaturedProducts(),
  3600 // 1 hour
);
```

### Cache Statistics

```typescript
// Get cache stats
const stats = cacheMiddleware.getStats();
console.log(`Hit rate: ${cacheMiddleware.getHitRate()}%`);
console.log(`Hits: ${stats.hits}, Misses: ${stats.misses}`);

// Reset stats
cacheMiddleware.resetStats();
```

## Cache Control Headers

```typescript
import { setCacheHeaders, noCache } from './middleware/cache';

// Set cache headers (1 hour, public)
app.get('/api/public-data',
  setCacheHeaders(3600, { public: true }),
  handler
);

// Disable caching completely
app.get('/api/sensitive-data',
  noCache(),
  handler
);

// Must revalidate
app.get('/api/important-data',
  setCacheHeaders(300, { mustRevalidate: true }),
  handler
);
```

## Health Check

```typescript
import { checkRedisHealth } from './services/redis-config';

app.get('/health/redis', async (req, res) => {
  const health = await checkRedisHealth();
  res.status(health.status === 'healthy' ? 200 : 503).json(health);
});
```

## Graceful Shutdown

```typescript
import { shutdownRedis } from './services/redis-config';

process.on('SIGTERM', async () => {
  console.log('Shutting down gracefully...');
  await shutdownRedis();
  process.exit(0);
});
```

## Best Practices

1. **TTL Selection**: Choose appropriate TTL based on data freshness requirements
2. **Cache Invalidation**: Always invalidate cache when data changes
3. **Error Handling**: The cache fails gracefully - application continues if Redis is down
4. **Key Naming**: Use consistent, hierarchical key patterns (e.g., `resource:id:field`)
5. **Memory Management**: Monitor Redis memory usage and set maxmemory-policy
6. **Rate Limiting**: Use sliding window for accurate rate limiting
7. **Distributed Locks**: Always use try-finally to release locks
8. **Monitoring**: Track cache hit rates and adjust TTLs accordingly

## Performance Tips

1. **Pipeline Operations**: Use Redis pipelining for bulk operations
2. **Cluster Mode**: Use Redis Cluster for horizontal scaling
3. **Connection Pooling**: ioredis handles connection pooling automatically
4. **Compression**: Consider compressing large cached values
5. **Cache Warming**: Pre-populate cache for frequently accessed data
6. **Selective Caching**: Only cache expensive operations

## Troubleshooting

### Cache Not Working

```bash
# Check Redis connection
redis-cli ping

# Check Redis logs
docker logs redis

# Check environment variables
echo $REDIS_URL
```

### High Memory Usage

```bash
# Check memory usage
redis-cli info memory

# Check keys count
redis-cli dbsize

# Find large keys
redis-cli --bigkeys
```

### Connection Issues

- Check network connectivity
- Verify Redis is running
- Check firewall rules
- Verify cluster node addresses
