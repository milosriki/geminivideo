/**
 * Redis Cache Integration Example
 *
 * This file demonstrates how to integrate the Redis cache service
 * into the gateway API.
 */

import express, { Request, Response } from 'express';
import { getRedisCacheService, checkRedisHealth, shutdownRedis } from '../services/redis-config';
import { CacheMiddleware, setCacheHeaders, noCache } from '../middleware/cache';

const app = express();
app.use(express.json());

// Initialize Redis cache service
const cacheService = getRedisCacheService();
const cacheMiddleware = cacheService ? new CacheMiddleware(cacheService) : null;

/**
 * Example 1: Basic Route Caching
 * Cache product list for 5 minutes
 */
app.get('/api/products',
  cacheMiddleware?.cache({
    ttlSeconds: 300,
    keyPrefix: 'api:products',
    includeQueryParams: true,
    excludeParams: ['_', 'nocache'],
  }) || ((req, res, next) => next()),
  async (req: Request, res: Response) => {
    try {
      // Simulated database query
      const products = await fetchProductsFromDatabase();
      res.json(products);
    } catch (error) {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

/**
 * Example 2: User-Specific Caching
 * Cache user profile with different cache per user
 */
app.get('/api/user/profile',
  cacheMiddleware?.cache({
    ttlSeconds: 600,
    keyPrefix: 'api:user:profile',
    varyByUser: true,
    statusCodesToCache: [200],
  }) || ((req, res, next) => next()),
  async (req: Request, res: Response) => {
    try {
      const userId = req.headers['x-user-id'] as string;
      const profile = await fetchUserProfile(userId);
      res.json(profile);
    } catch (error) {
      res.status(500).json({ error: 'Internal server error' });
    }
  }
);

/**
 * Example 3: Manual Cache Usage with getOrSet
 */
app.get('/api/statistics', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      const stats = await calculateStatistics();
      return res.json(stats);
    }

    const stats = await cacheService.getOrSet(
      'stats:daily',
      async () => {
        console.log('Cache miss - calculating statistics...');
        return await calculateStatistics();
      },
      3600 // Cache for 1 hour
    );

    res.json(stats);
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 4: Rate Limiting
 */
app.post('/api/expensive-operation', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      return res.status(503).json({ error: 'Cache service unavailable' });
    }

    const clientId = req.ip || 'unknown';
    const rateLimitKey = `ratelimit:expensive:${clientId}`;

    // Allow 10 requests per minute
    const result = await cacheService.checkRateLimit(rateLimitKey, 10, 60);

    // Set rate limit headers
    res.set({
      'X-RateLimit-Limit': '10',
      'X-RateLimit-Remaining': result.remaining.toString(),
      'X-RateLimit-Reset': new Date(result.resetAt).toISOString(),
    });

    if (!result.allowed) {
      return res.status(429).json({
        error: 'Too many requests',
        retryAfter: Math.ceil((result.resetAt - Date.now()) / 1000),
      });
    }

    // Process expensive operation
    const result_data = await performExpensiveOperation();
    res.json(result_data);
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 5: Session Management
 */
app.post('/api/auth/login', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      return res.status(503).json({ error: 'Cache service unavailable' });
    }

    const { email, password } = req.body;

    // Authenticate user (placeholder)
    const user = await authenticateUser(email, password);
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Create session
    const sessionId = generateSessionId();
    await cacheService.setSession(
      sessionId,
      {
        userId: user.id,
        email: user.email,
        roles: user.roles,
        metadata: { loginTime: Date.now() },
        createdAt: Date.now(),
        lastAccessedAt: Date.now(),
      },
      86400 // 24 hours
    );

    res.json({ sessionId, user });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/auth/logout', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      return res.status(503).json({ error: 'Cache service unavailable' });
    }

    const sessionId = req.headers['x-session-id'] as string;
    if (sessionId) {
      await cacheService.deleteSession(sessionId);
    }

    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 6: Pub/Sub for Real-time Updates
 */
if (cacheService) {
  // Subscribe to order updates
  cacheService.subscribe('orders:new', (message) => {
    console.log('New order received:', message);
    // Broadcast to connected clients via WebSocket, etc.
  });
}

app.post('/api/orders', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      return res.status(503).json({ error: 'Cache service unavailable' });
    }

    const order = await createOrder(req.body);

    // Publish order creation event
    await cacheService.publish('orders:new', {
      orderId: order.id,
      userId: order.userId,
      total: order.total,
      timestamp: Date.now(),
    });

    res.json(order);
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 7: Cache Invalidation
 */
app.post('/api/products/:id', async (req: Request, res: Response) => {
  try {
    const productId = req.params.id;

    // Update product
    const product = await updateProduct(productId, req.body);

    // Invalidate related caches
    if (cacheMiddleware) {
      await cacheMiddleware.invalidatePattern(`cache:api:products*`);
      await cacheMiddleware.invalidate(`cache:api:products:${productId}`);
    }

    res.json(product);
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 8: Job Queue
 */
app.post('/api/reports/generate', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      return res.status(503).json({ error: 'Cache service unavailable' });
    }

    // Enqueue report generation job
    const jobId = await cacheService.enqueue('reports', {
      type: 'sales_report',
      userId: req.body.userId,
      startDate: req.body.startDate,
      endDate: req.body.endDate,
    });

    res.json({ jobId, status: 'queued' });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 9: Distributed Lock
 */
app.post('/api/inventory/reserve', async (req: Request, res: Response) => {
  try {
    if (!cacheService) {
      return res.status(503).json({ error: 'Cache service unavailable' });
    }

    const productId = req.body.productId;
    const lockKey = `inventory:${productId}`;

    // Acquire lock to prevent race conditions
    const lockId = await cacheService.acquireLock(lockKey, 10);

    if (!lockId) {
      return res.status(409).json({ error: 'Product reservation in progress' });
    }

    try {
      // Critical section - reserve inventory
      const reservation = await reserveInventory(productId, req.body.quantity);
      res.json(reservation);
    } finally {
      // Always release lock
      await cacheService.releaseLock(lockKey, lockId);
    }
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 10: Cache Statistics
 */
app.get('/api/admin/cache/stats', async (req: Request, res: Response) => {
  try {
    if (!cacheMiddleware) {
      return res.status(503).json({ error: 'Cache service unavailable' });
    }

    const stats = cacheMiddleware.getStats();
    const hitRate = cacheMiddleware.getHitRate();

    res.json({
      stats,
      hitRate: `${hitRate.toFixed(2)}%`,
      uptime: Date.now() - stats.lastReset,
    });
  } catch (error) {
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * Example 11: Health Check
 */
app.get('/health/redis', async (req: Request, res: Response) => {
  const health = await checkRedisHealth();
  res.status(health.status === 'healthy' ? 200 : 503).json(health);
});

/**
 * Example 12: Cache Control Headers
 */
app.get('/api/public/announcements',
  setCacheHeaders(1800, { public: true }), // 30 minutes, public
  async (req: Request, res: Response) => {
    const announcements = await getAnnouncements();
    res.json(announcements);
  }
);

app.get('/api/user/transactions',
  noCache(), // Never cache sensitive data
  async (req: Request, res: Response) => {
    const transactions = await getUserTransactions(req.headers['x-user-id'] as string);
    res.json(transactions);
  }
);

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('SIGTERM signal received: closing Redis connections');
  await shutdownRedis();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('SIGINT signal received: closing Redis connections');
  await shutdownRedis();
  process.exit(0);
});

// Placeholder functions (implement based on your actual database/services)
async function fetchProductsFromDatabase() {
  return [{ id: 1, name: 'Product 1' }, { id: 2, name: 'Product 2' }];
}

async function fetchUserProfile(userId: string) {
  return { id: userId, name: 'John Doe', email: 'john@example.com' };
}

async function calculateStatistics() {
  return { totalOrders: 1000, totalRevenue: 50000 };
}

async function performExpensiveOperation() {
  return { result: 'completed' };
}

async function authenticateUser(email: string, password: string) {
  return { id: '123', email, roles: ['user'] };
}

function generateSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

async function createOrder(data: any) {
  return { id: '123', userId: data.userId, total: data.total };
}

async function updateProduct(id: string, data: any) {
  return { id, ...data };
}

async function reserveInventory(productId: string, quantity: number) {
  return { productId, quantity, reserved: true };
}

async function getAnnouncements() {
  return [{ id: 1, title: 'Welcome!', content: 'Welcome to our platform' }];
}

async function getUserTransactions(userId: string) {
  return [{ id: 1, userId, amount: 100, date: new Date() }];
}

export default app;
