import { Pool } from 'pg';

interface CircuitBreakerConfig {
  failureThreshold: number;
  resetTimeout: number;
  halfOpenRequests: number;
}

enum CircuitState {
  CLOSED = 'closed',
  OPEN = 'open',
  HALF_OPEN = 'half_open'
}

export class SafeExecutor {
  private pgPool: Pool;
  private circuitState: CircuitState = CircuitState.CLOSED;
  private failureCount: number = 0;
  private lastFailureTime: number = 0;
  private config: CircuitBreakerConfig;

  constructor(pgPool: Pool, config?: Partial<CircuitBreakerConfig>) {
    this.pgPool = pgPool;
    this.config = {
      failureThreshold: config?.failureThreshold || 5,
      resetTimeout: config?.resetTimeout || 30000,
      halfOpenRequests: config?.halfOpenRequests || 3
    };
  }

  async execute<T>(
    operation: () => Promise<T>,
    operationName: string,
    fallback?: () => T
  ): Promise<T> {
    // Check circuit state
    if (this.circuitState === CircuitState.OPEN) {
      if (Date.now() - this.lastFailureTime > this.config.resetTimeout) {
        this.circuitState = CircuitState.HALF_OPEN;
        console.log(`Circuit breaker for ${operationName}: transitioning to HALF_OPEN`);
      } else {
        console.warn(`Circuit breaker OPEN for ${operationName}, using fallback`);
        if (fallback) return fallback();
        throw new Error(`Circuit breaker open for ${operationName}`);
      }
    }

    try {
      const result = await operation();
      this.onSuccess(operationName);
      return result;
    } catch (error: any) {
      this.onFailure(operationName, error);
      if (fallback) return fallback();
      throw error;
    }
  }

  private onSuccess(operationName: string): void {
    if (this.circuitState === CircuitState.HALF_OPEN) {
      this.circuitState = CircuitState.CLOSED;
      console.log(`Circuit breaker for ${operationName}: transitioning to CLOSED`);
    }
    this.failureCount = 0;
  }

  private onFailure(operationName: string, error: Error): void {
    this.failureCount++;
    this.lastFailureTime = Date.now();

    console.error(`SafeExecutor failure in ${operationName}: ${error.message}`);

    if (this.failureCount >= this.config.failureThreshold) {
      this.circuitState = CircuitState.OPEN;
      console.warn(`Circuit breaker for ${operationName}: transitioning to OPEN after ${this.failureCount} failures`);
    }

    // Log to database for monitoring
    this.logFailure(operationName, error);
  }

  private async logFailure(operationName: string, error: Error): Promise<void> {
    try {
      await this.pgPool.query(
        `INSERT INTO execution_failures (operation_name, error_message, circuit_state, created_at)
         VALUES ($1, $2, $3, NOW())`,
        [operationName, error.message, this.circuitState]
      );
    } catch (logError) {
      console.error('Failed to log execution failure:', logError);
    }
  }

  getCircuitState(): CircuitState {
    return this.circuitState;
  }

  resetCircuit(): void {
    this.circuitState = CircuitState.CLOSED;
    this.failureCount = 0;
    console.log('Circuit breaker manually reset');
  }
}

// Singleton instance for the application
let safeExecutorInstance: SafeExecutor | null = null;

export function initializeSafeExecutor(pgPool: Pool): SafeExecutor {
  if (!safeExecutorInstance) {
    safeExecutorInstance = new SafeExecutor(pgPool);
    console.log('SafeExecutor initialized with circuit breaker');
  }
  return safeExecutorInstance;
}

export function getSafeExecutor(): SafeExecutor | null {
  return safeExecutorInstance;
}
