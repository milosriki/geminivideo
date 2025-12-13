/**
 * OpenTelemetry Tracing Configuration
 *
 * Note: This requires OpenTelemetry packages to be installed:
 * npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node
 * npm install @opentelemetry/exporter-trace-otlp-http @opentelemetry/resources @opentelemetry/semantic-conventions
 */

import { Request, Response, NextFunction } from 'express';

// Type definitions for when OpenTelemetry is installed
interface TracingConfig {
  serviceName: string;
  enabled: boolean;
  exporterUrl?: string;
}

// Simple span context for manual instrumentation
interface SpanContext {
  traceId: string;
  spanId: string;
  startTime: number;
  attributes: Record<string, any>;
}

// In-memory span storage for basic tracing without OpenTelemetry
const activeSpans = new Map<string, SpanContext>();

/**
 * Initialize OpenTelemetry tracing
 * This is a placeholder that can be enhanced when OpenTelemetry packages are installed
 */
export function initTracing(config: TracingConfig = { serviceName: 'gateway-api', enabled: false }) {
  if (!config.enabled) {
    console.log('📊 Tracing is disabled. Set TRACING_ENABLED=true to enable.');
    return;
  }

  try {
    // When OpenTelemetry packages are installed, uncomment this:
    /*
    const { NodeSDK } = require('@opentelemetry/sdk-node');
    const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
    const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
    const { Resource } = require('@opentelemetry/resources');
    const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

    const exporter = new OTLPTraceExporter({
      url: config.exporterUrl || 'http://localhost:4318/v1/traces',
    });

    const sdk = new NodeSDK({
      resource: new Resource({
        [SemanticResourceAttributes.SERVICE_NAME]: config.serviceName,
        [SemanticResourceAttributes.SERVICE_VERSION]: process.env.npm_package_version || '1.0.0',
      }),
      traceExporter: exporter,
      instrumentations: [getNodeAutoInstrumentations({
        '@opentelemetry/instrumentation-fs': {
          enabled: false, // Disable fs instrumentation to reduce noise
        },
      })],
    });

    sdk.start();
    console.log('✅ OpenTelemetry tracing initialized');

    // Graceful shutdown
    process.on('SIGTERM', () => {
      sdk.shutdown()
        .then(() => console.log('Tracing terminated'))
        .catch((error) => console.error('Error terminating tracing', error))
        .finally(() => process.exit(0));
    });
    */

    console.log('⚠️ OpenTelemetry packages not installed. Using basic tracing.');
    console.log('To enable full tracing, install: npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node');
  } catch (error: any) {
    console.warn('Failed to initialize tracing:', error.message);
  }
}

/**
 * Create a simple trace span (manual instrumentation)
 */
export function createSpan(name: string, attributes: Record<string, any> = {}): string {
  const spanId = generateId();
  const traceId = generateId();

  const span: SpanContext = {
    traceId,
    spanId,
    startTime: Date.now(),
    attributes: {
      name,
      ...attributes,
    },
  };

  activeSpans.set(spanId, span);
  return spanId;
}

/**
 * End a trace span
 */
export function endSpan(spanId: string, attributes: Record<string, any> = {}) {
  const span = activeSpans.get(spanId);
  if (!span) {
    return;
  }

  const duration = Date.now() - span.startTime;

  // Log the span (in production, this would be sent to a tracing backend)
  console.log('[TRACE]', {
    traceId: span.traceId,
    spanId: span.spanId,
    name: span.attributes.name,
    duration: `${duration}ms`,
    ...span.attributes,
    ...attributes,
  });

  activeSpans.delete(spanId);
}

/**
 * Express middleware for automatic request tracing
 */
export function tracingMiddleware(req: Request, res: Response, next: NextFunction) {
  const spanId = createSpan('http_request', {
    'http.method': req.method,
    'http.url': req.url,
    'http.route': req.route?.path || req.path,
    'http.user_agent': req.get('user-agent'),
  });

  // Store span ID in request for manual instrumentation
  (req as any).spanId = spanId;

  // Add trace ID to response headers
  const span = activeSpans.get(spanId);
  if (span) {
    res.setHeader('X-Trace-Id', span.traceId);
  }

  // End span when response finishes
  res.on('finish', () => {
    endSpan(spanId, {
      'http.status_code': res.statusCode,
      'http.status_text': res.statusMessage,
    });
  });

  next();
}

/**
 * Trace a function execution
 */
export async function traceAsync<T>(
  name: string,
  fn: () => Promise<T>,
  attributes: Record<string, any> = {}
): Promise<T> {
  const spanId = createSpan(name, attributes);

  try {
    const result = await fn();
    endSpan(spanId, { success: true });
    return result;
  } catch (error: any) {
    endSpan(spanId, {
      success: false,
      error: error.message,
    });
    throw error;
  }
}

/**
 * Get current trace context from request
 */
export function getTraceContext(req: Request): { traceId?: string; spanId?: string } {
  const spanId = (req as any).spanId;
  if (!spanId) {
    return {};
  }

  const span = activeSpans.get(spanId);
  return {
    traceId: span?.traceId,
    spanId: span?.spanId,
  };
}

/**
 * Generate a random ID for traces/spans
 */
function generateId(): string {
  return Math.random().toString(36).substring(2, 15) +
         Math.random().toString(36).substring(2, 15);
}

/**
 * Configuration helper
 */
export function getTracingConfig(): TracingConfig {
  return {
    serviceName: process.env.SERVICE_NAME || 'gateway-api',
    enabled: process.env.TRACING_ENABLED === 'true',
    exporterUrl: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
  };
}

// Export types
export type { TracingConfig, SpanContext };
