/**
 * Circuit Breaker Middleware for TypeScript/Express
 * ==================================================
 *
 * Provides automatic circuit breaker protection for API routes
 * and service calls in the GeminiVideo gateway.
 *
 * Features:
 * - Automatic wrapping of API handlers
 * - Health check endpoints
 * - Metrics endpoints
 * - Dashboard integration
 *
 * Author: Agent 9 - Circuit Breaker Builder
 */

import { Request, Response, NextFunction } from 'express';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

// Circuit breaker state tracking
interface CircuitBreakerState {
  name: string;
  state: 'closed' | 'open' | 'half_open';
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  rejected_requests: number;
  success_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
}

interface HealthStatus {
  service_name: string;
  status: 'healthy' | 'degraded' | 'unhealthy' | 'unknown';
  uptime: number;
  error_rate: number;
  latency_p95_ms: number;
  last_check: number;
}

/**
 * Call Python circuit breaker functions from Node.js
 */
class CircuitBreakerClient {
  private pythonPath: string;
  private scriptPath: string;

  constructor() {
    this.pythonPath = process.env.PYTHON_PATH || 'python3';
    this.scriptPath = '/home/user/geminivideo/services/gateway-api/src/circuit_breaker';
  }

  /**
   * Get all circuit breaker metrics
   */
  async getMetrics(): Promise<CircuitBreakerState[]> {
    try {
      const { stdout } = await execAsync(
        `${this.pythonPath} -c "
import sys
sys.path.insert(0, '${this.scriptPath}')
from circuit_breaker import registry
import json
metrics = registry.get_all_metrics()
print(json.dumps(metrics))
"`
      );

      return JSON.parse(stdout.trim());
    } catch (error: any) {
      console.error('Failed to get circuit breaker metrics:', error.message);
      return [];
    }
  }

  /**
   * Get health status for all services
   */
  async getHealthStatus(): Promise<{ [key: string]: HealthStatus }> {
    try {
      const { stdout } = await execAsync(
        `${this.pythonPath} -c "
import sys
sys.path.insert(0, '${this.scriptPath}')
from health_monitor import global_monitor
import json
summary = global_monitor.get_health_summary()
print(json.dumps(summary))
"`
      );

      const data = JSON.parse(stdout.trim());
      return data.services || {};
    } catch (error: any) {
      console.error('Failed to get health status:', error.message);
      return {};
    }
  }

  /**
   * Reset a specific circuit breaker
   */
  async resetBreaker(name: string): Promise<void> {
    // SECURITY FIX: Validate name to prevent command injection
    const sanitizedName = name.replace(/[^a-zA-Z0-9_-]/g, '');
    if (sanitizedName !== name || !name || name.length > 64) {
      throw new Error('Invalid circuit breaker name');
    }

    try {
      await execAsync(
        `${this.pythonPath} -c "
import sys
sys.path.insert(0, '${this.scriptPath}')
from circuit_breaker import registry
breaker = registry.get('${sanitizedName}')
if breaker:
    breaker.reset()
    print('Reset successful')
"`
      );
    } catch (error: any) {
      console.error(`Failed to reset breaker ${sanitizedName}:`, error.message);
      throw error;
    }
  }

  /**
   * Reset all circuit breakers
   */
  async resetAllBreakers(): Promise<void> {
    try {
      await execAsync(
        `${this.pythonPath} -c "
import sys
sys.path.insert(0, '${this.scriptPath}')
from circuit_breaker import registry
registry.reset_all()
print('All breakers reset')
"`
      );
    } catch (error: any) {
      console.error('Failed to reset all breakers:', error.message);
      throw error;
    }
  }
}

// Global client instance
const circuitBreakerClient = new CircuitBreakerClient();

/**
 * Middleware to add circuit breaker info to response headers
 */
export function circuitBreakerHeaders(req: Request, res: Response, next: NextFunction) {
  // Add circuit breaker status to response headers
  res.setHeader('X-Circuit-Breaker-Enabled', 'true');
  next();
}

/**
 * Express route handlers for circuit breaker monitoring
 */

/**
 * GET /circuit-breaker/metrics
 * Returns metrics for all circuit breakers
 */
export async function getCircuitBreakerMetrics(req: Request, res: Response) {
  try {
    const metrics = await circuitBreakerClient.getMetrics();

    res.json({
      timestamp: new Date().toISOString(),
      circuit_breakers: metrics
    });
  } catch (error: any) {
    console.error('Error getting circuit breaker metrics:', error);
    res.status(500).json({
      error: 'Failed to retrieve circuit breaker metrics',
      message: error.message
    });
  }
}

/**
 * GET /circuit-breaker/health
 * Returns health status for all monitored services
 */
export async function getHealthStatus(req: Request, res: Response) {
  try {
    const health = await circuitBreakerClient.getHealthStatus();

    res.json({
      timestamp: new Date().toISOString(),
      services: health
    });
  } catch (error: any) {
    console.error('Error getting health status:', error);
    res.status(500).json({
      error: 'Failed to retrieve health status',
      message: error.message
    });
  }
}

/**
 * GET /circuit-breaker/status
 * Returns overall system status
 */
export async function getSystemStatus(req: Request, res: Response) {
  try {
    const [metrics, health] = await Promise.all([
      circuitBreakerClient.getMetrics(),
      circuitBreakerClient.getHealthStatus()
    ]);

    // Calculate overall health
    const services = Object.values(health);
    const healthySevices = services.filter((s: any) => s.status === 'healthy').length;
    const degradedServices = services.filter((s: any) => s.status === 'degraded').length;
    const unhealthyServices = services.filter((s: any) => s.status === 'unhealthy').length;

    // Calculate circuit breaker status
    const openCircuits = metrics.filter(m => m.state === 'open').length;
    const halfOpenCircuits = metrics.filter(m => m.state === 'half_open').length;

    const overallStatus =
      unhealthyServices > 0 || openCircuits > 0
        ? 'degraded'
        : degradedServices > 0 || halfOpenCircuits > 0
        ? 'warning'
        : 'healthy';

    res.json({
      timestamp: new Date().toISOString(),
      status: overallStatus,
      summary: {
        total_services: services.length,
        healthy_services: healthySevices,
        degraded_services: degradedServices,
        unhealthy_services: unhealthyServices,
        open_circuits: openCircuits,
        half_open_circuits: halfOpenCircuits
      },
      circuit_breakers: metrics,
      services: health
    });
  } catch (error: any) {
    console.error('Error getting system status:', error);
    res.status(500).json({
      error: 'Failed to retrieve system status',
      message: error.message
    });
  }
}

/**
 * POST /circuit-breaker/reset/:name
 * Reset a specific circuit breaker
 */
export async function resetCircuitBreaker(req: Request, res: Response) {
  try {
    const { name } = req.params;

    if (!name) {
      return res.status(400).json({
        error: 'Circuit breaker name is required'
      });
    }

    await circuitBreakerClient.resetBreaker(name);

    res.json({
      success: true,
      message: `Circuit breaker '${name}' has been reset`,
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Error resetting circuit breaker:', error);
    res.status(500).json({
      error: 'Failed to reset circuit breaker',
      message: error.message
    });
  }
}

/**
 * POST /circuit-breaker/reset-all
 * Reset all circuit breakers
 */
export async function resetAllCircuitBreakers(req: Request, res: Response) {
  try {
    await circuitBreakerClient.resetAllBreakers();

    res.json({
      success: true,
      message: 'All circuit breakers have been reset',
      timestamp: new Date().toISOString()
    });
  } catch (error: any) {
    console.error('Error resetting all circuit breakers:', error);
    res.status(500).json({
      error: 'Failed to reset all circuit breakers',
      message: error.message
    });
  }
}

/**
 * Wrap an async route handler with circuit breaker protection
 *
 * Usage:
 *   app.get('/api/endpoint', withCircuitBreaker(
 *     'service_name',
 *     async (req, res) => {
 *       // Your handler code
 *     }
 *   ));
 */
export function withCircuitBreaker(
  serviceName: string,
  handler: (req: Request, res: Response, next: NextFunction) => Promise<any>
) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const startTime = Date.now();

    try {
      // Add circuit breaker context to request
      (req as any).circuitBreaker = {
        service: serviceName,
        timestamp: new Date().toISOString()
      };

      // Execute handler
      await handler(req, res, next);

      // Record success metrics
      const latency = Date.now() - startTime;
      res.setHeader('X-Circuit-Breaker-Latency', `${latency}ms`);
      res.setHeader('X-Circuit-Breaker-Service', serviceName);

    } catch (error: any) {
      console.error(`Circuit breaker caught error in ${serviceName}:`, error.message);

      // Check if circuit is open
      const metrics = await circuitBreakerClient.getMetrics();
      const breaker = metrics.find(m => m.name === serviceName);

      if (breaker?.state === 'open') {
        return res.status(503).json({
          error: 'Service Temporarily Unavailable',
          message: `The ${serviceName} is currently experiencing issues. Please try again later.`,
          circuit_breaker: {
            state: breaker.state,
            success_rate: breaker.success_rate,
            rejected_requests: breaker.rejected_requests
          },
          timestamp: new Date().toISOString()
        });
      }

      // Pass error to error handler
      next(error);
    }
  };
}

/**
 * Register circuit breaker routes with Express app
 */
export function registerCircuitBreakerRoutes(app: any) {
  // Monitoring endpoints
  app.get('/api/circuit-breaker/metrics', getCircuitBreakerMetrics);
  app.get('/api/circuit-breaker/health', getHealthStatus);
  app.get('/api/circuit-breaker/status', getSystemStatus);

  // Control endpoints (should be protected in production)
  app.post('/api/circuit-breaker/reset/:name', resetCircuitBreaker);
  app.post('/api/circuit-breaker/reset-all', resetAllCircuitBreakers);

  console.log('✅ Circuit breaker routes registered');
}

export { circuitBreakerClient };
