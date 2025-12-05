/**
 * Edge Worker: Analytics Collector
 * Collects performance metrics and user events at the edge
 * Aggregates and sends to origin asynchronously
 */

import { CloudflareEnv, EdgeAnalyticsEvent, RegionPerformance } from '../types/env';

export default {
  async fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route: POST /api/analytics/track - Track event
      if (path === '/api/analytics/track' && request.method === 'POST') {
        return await handleTrackEvent(request, env, ctx, corsHeaders);
      }

      // Route: POST /api/analytics/batch - Batch track events
      if (path === '/api/analytics/batch' && request.method === 'POST') {
        return await handleBatchTrack(request, env, ctx, corsHeaders);
      }

      // Route: GET /api/analytics/performance - Get edge performance metrics
      if (path === '/api/analytics/performance' && request.method === 'GET') {
        return await getPerformanceMetrics(env, corsHeaders);
      }

      // Route: GET /api/analytics/regions - Get regional statistics
      if (path === '/api/analytics/regions' && request.method === 'GET') {
        return await getRegionalStats(env, corsHeaders);
      }

      return new Response('Not Found', { status: 404, headers: corsHeaders });
    } catch (error: any) {
      console.error('[Edge Analytics] Error:', error);
      return new Response(
        JSON.stringify({ error: 'Internal Server Error', message: error.message }),
        {
          status: 500,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      );
    }
  },
};

async function handleTrackEvent(
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const event = await request.json() as EdgeAnalyticsEvent;

  // Validate event
  if (!event.event_type) {
    return new Response(
      JSON.stringify({ error: 'event_type is required' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // Enrich with request metadata
  const cf = (request as any).cf;
  const enrichedEvent: EdgeAnalyticsEvent = {
    ...event,
    timestamp: event.timestamp || new Date().toISOString(),
    country: cf?.country || event.country,
    city: cf?.city || event.city,
    user_agent: request.headers.get('User-Agent') || event.user_agent,
    referer: request.headers.get('Referer') || event.referer,
  };

  // Store in KV for batch processing
  const eventKey = `analytics:${Date.now()}:${Math.random().toString(36).slice(2)}`;

  ctx.waitUntil(
    env.ANALYTICS.put(eventKey, JSON.stringify(enrichedEvent), {
      expirationTtl: 86400, // 24 hours
    })
  );

  // Also increment counters in real-time
  ctx.waitUntil(incrementCounters(env, enrichedEvent));

  return new Response(
    JSON.stringify({
      message: 'Event tracked',
      event_id: eventKey,
      timestamp: enrichedEvent.timestamp,
    }),
    {
      status: 202, // Accepted
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    }
  );
}

async function handleBatchTrack(
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.json() as { events: EdgeAnalyticsEvent[] };
  const events = body.events;

  if (!events || !Array.isArray(events) || events.length === 0) {
    return new Response(
      JSON.stringify({ error: 'events array is required' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // Limit batch size
  if (events.length > 100) {
    return new Response(
      JSON.stringify({ error: 'Batch size limited to 100 events' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // Track each event asynchronously
  const cf = (request as any).cf;
  const trackPromises = events.map(async (event) => {
    const enrichedEvent: EdgeAnalyticsEvent = {
      ...event,
      timestamp: event.timestamp || new Date().toISOString(),
      country: cf?.country || event.country,
    };

    const eventKey = `analytics:${Date.now()}:${Math.random().toString(36).slice(2)}`;
    await env.ANALYTICS.put(eventKey, JSON.stringify(enrichedEvent), {
      expirationTtl: 86400,
    });

    return eventKey;
  });

  ctx.waitUntil(Promise.all(trackPromises));

  return new Response(
    JSON.stringify({
      message: 'Batch tracked',
      event_count: events.length,
    }),
    {
      status: 202,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    }
  );
}

async function incrementCounters(
  env: CloudflareEnv,
  event: EdgeAnalyticsEvent
): Promise<void> {
  // Increment event type counter
  const counterKey = `counter:${event.event_type}:${event.country || 'unknown'}`;
  const current = await env.ANALYTICS.get(counterKey);
  const count = current ? parseInt(current) + 1 : 1;

  await env.ANALYTICS.put(counterKey, String(count), {
    expirationTtl: 3600, // 1 hour
  });

  // Increment creative-specific counter if available
  if (event.creative_id) {
    const creativeKey = `counter:creative:${event.creative_id}:${event.event_type}`;
    const creativeCount = await env.ANALYTICS.get(creativeKey);
    const count = creativeCount ? parseInt(creativeCount) + 1 : 1;

    await env.ANALYTICS.put(creativeKey, String(count), {
      expirationTtl: 3600,
    });
  }
}

async function getPerformanceMetrics(
  env: CloudflareEnv,
  corsHeaders: Record<string, string>
): Promise<Response> {
  // In production, this would query Durable Objects or KV for aggregated metrics
  // For now, return placeholder data

  const metrics = {
    global: {
      total_requests: 0,
      cache_hit_rate: 0,
      avg_latency_ms: 0,
      error_rate: 0,
    },
    regions: [] as RegionPerformance[],
    timestamp: new Date().toISOString(),
  };

  // Try to get cached metrics
  const cached = await env.ANALYTICS.get('metrics:global', 'json');
  if (cached) {
    return new Response(JSON.stringify(cached), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=60',
      },
    });
  }

  return new Response(JSON.stringify(metrics), {
    status: 200,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json',
    },
  });
}

async function getRegionalStats(
  env: CloudflareEnv,
  corsHeaders: Record<string, string>
): Promise<Response> {
  // Get regional performance statistics
  const regions: RegionPerformance[] = [];

  // Try to get from cache
  const cached = await env.ANALYTICS.get('metrics:regions', 'json') as RegionPerformance[] | null;
  if (cached) {
    return new Response(JSON.stringify({ regions: cached }), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'Cache-Control': 'public, max-age=60',
      },
    });
  }

  return new Response(
    JSON.stringify({
      regions,
      message: 'Regional stats will be available after analytics data collection',
    }),
    {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
      },
    }
  );
}
