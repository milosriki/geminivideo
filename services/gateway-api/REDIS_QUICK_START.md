# Redis Cache - Quick Start Guide

## Installation

```bash
cd /home/user/geminivideo/services/gateway-api
npm install
```

Dependencies already added to `package.json`:
- `ioredis@^5.3.2`
- `@types/ioredis@^5.0.0`

## Setup

1. **Start Redis** (for local development):
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

2. **Configure Environment** (`.env`):
```bash
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=true
```

## Basic Usage

### Initialize Redis Cache

```typescript
import { getRedisCacheService } from './services/redis-config';

const cache = getRedisCacheService();
```

### Simple Cache Operations

```typescript
// Set with TTL
await cache.set('user:123', { name: 'John' }, 3600); // 1 hour

// Get
const user = await cache.get('user:123');

// Delete
await cache.delete('user:123');
```

### Route Caching (Most Common Use Case)

```typescript
import { CacheMiddleware } from './middleware/cache';

const cacheMiddleware = new CacheMiddleware(cache!);

// Cache GET requests for 5 minutes
app.get('/api/products',
  cacheMiddleware.cache({
    ttlSeconds: 300,
    includeQueryParams: true,
  }),
  async (req, res) => {
    const products = await db.getProducts();
    res.json(products);
  }
);
```

### Rate Limiting

```typescript
const result = await cache.checkRateLimit(
  `api:user:${userId}`,
  100, // 100 requests
  60   // per minute
);

if (!result.allowed) {
  return res.status(429).json({ error: 'Too many requests' });
}
```

### Session Management

```typescript
// Login
await cache.setSession(sessionId, {
  userId: user.id,
  email: user.email,
  roles: user.roles,
  createdAt: Date.now(),
  lastAccessedAt: Date.now(),
}, 86400); // 24 hours

// Get session
const session = await cache.getSession(sessionId);

// Logout
await cache.deleteSession(sessionId);
```

## Integration with Existing App

Add to your main `src/index.ts`:

```typescript
import { getRedisCacheService, checkRedisHealth } from './services/redis-config';
import { CacheMiddleware } from './middleware/cache';

// Initialize Redis
const cache = getRedisCacheService();
const cacheMiddleware = cache ? new CacheMiddleware(cache) : null;

// Health check endpoint
app.get('/health/redis', async (req, res) => {
  const health = await checkRedisHealth();
  res.status(health.status === 'healthy' ? 200 : 503).json(health);
});

// Apply caching to routes
app.get('/api/expensive-data',
  cacheMiddleware?.cache({ ttlSeconds: 600 }) || ((req, res, next) => next()),
  expensiveHandler
);
```

## Cache Invalidation

```typescript
// After updating data
await updateProduct(id, data);

// Invalidate cache
await cacheMiddleware.invalidatePattern('cache:api:products*');
```

## Monitoring

```typescript
// Get cache statistics
app.get('/api/admin/cache/stats', (req, res) => {
  const stats = cacheMiddleware.getStats();
  res.json({
    hitRate: `${cacheMiddleware.getHitRate()}%`,
    ...stats,
  });
});
```

## Testing

```bash
npm test -- redis-cache.test.ts
```

## Production Deployment

1. Use managed Redis (AWS ElastiCache, Google Cloud Memorystore, etc.)
2. Enable Redis authentication:
   ```
   REDIS_URL=redis://:password@hostname:6379
   ```
3. Use SSL/TLS:
   ```
   REDIS_URL=rediss://username:password@hostname:6380
   ```
4. For high availability, use Redis Cluster:
   ```
   REDIS_CLUSTER_NODES=redis1:6379,redis2:6379,redis3:6379
   ```

## Troubleshooting

**Redis connection failed:**
```bash
# Check if Redis is running
redis-cli ping

# Check connection
telnet localhost 6379
```

**High memory usage:**
```bash
# Check memory
redis-cli info memory

# Find large keys
redis-cli --bigkeys
```

**Cache not working:**
- Check `REDIS_ENABLED=true` in `.env`
- Verify Redis is running
- Check logs for connection errors

## Files Reference

- **Core Service**: `src/services/redis-cache.ts`
- **Configuration**: `src/services/redis-config.ts`
- **Middleware**: `src/middleware/cache.ts`
- **Examples**: `src/examples/redis-integration-example.ts`
- **Tests**: `src/tests/redis-cache.test.ts`
- **Full Documentation**: `src/services/REDIS_USAGE.md`

## Next Steps

1. ✅ Redis cache implementation complete
2. 🔄 Integrate into existing routes
3. 🔄 Add health monitoring
4. 🔄 Configure production Redis
5. 🔄 Run tests and verify

---

For complete documentation, see:
- `REDIS_USAGE.md` - Comprehensive usage guide
- `REDIS_IMPLEMENTATION.md` - Implementation details
- `redis-integration-example.ts` - 12 real-world examples
