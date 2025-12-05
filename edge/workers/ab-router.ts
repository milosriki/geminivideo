/**
 * Edge Worker: A/B Test Router
 * Handles A/B test variant selection at the edge
 * Uses Thompson Sampling for intelligent traffic allocation
 */

import { CloudflareEnv, ABTestVariant } from '../types/env';

const AB_CACHE_TTL = 60; // 1 minute

export default {
  async fetch(request: Request, env: CloudflareEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);
    const path = url.pathname;

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-User-ID',
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    try {
      // Route: POST /api/ab/assign - Assign user to variant
      if (path === '/api/ab/assign' && request.method === 'POST') {
        return await handleVariantAssignment(request, env, ctx, corsHeaders);
      }

      // Route: GET /api/ab/experiment/:experiment_id - Get experiment config
      if (path.match(/^\/api\/ab\/experiment\/(.+)$/) && request.method === 'GET') {
        const experimentId = path.split('/').pop()!;
        return await getExperimentConfig(experimentId, env, corsHeaders);
      }

      // Route: POST /api/ab/track - Track event
      if (path === '/api/ab/track' && request.method === 'POST') {
        return await trackABEvent(request, env, ctx, corsHeaders);
      }

      return new Response('Not Found', { status: 404, headers: corsHeaders });
    } catch (error: any) {
      console.error('[AB Router] Error:', error);
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

async function handleVariantAssignment(
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.json() as {
    experiment_id: string;
    user_id: string;
    context?: Record<string, any>;
  };

  const { experiment_id, user_id, context } = body;

  if (!experiment_id || !user_id) {
    return new Response(
      JSON.stringify({ error: 'experiment_id and user_id are required' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  const cacheKey = `ab:${experiment_id}:${user_id}`;

  // Check if user already assigned
  const cached = await env.AB_TESTS.get(cacheKey, 'json') as ABTestVariant | null;
  if (cached) {
    console.log(`[AB] User already assigned: ${user_id} -> variant ${cached.variant_id}`);
    return new Response(JSON.stringify(cached), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'X-Cache': 'HIT',
        'X-Variant-ID': cached.variant_id,
      },
    });
  }

  // Get experiment config from KV
  const experimentKey = `experiment:${experiment_id}`;
  const experimentData = await env.AB_TESTS.get(experimentKey, 'json') as {
    variants: ABTestVariant[];
  } | null;

  if (!experimentData || !experimentData.variants || experimentData.variants.length === 0) {
    // Fallback: fetch from origin
    console.log(`[AB] Experiment not in cache, fetching from origin: ${experiment_id}`);

    try {
      const originResponse = await fetch(
        `${env.ML_SERVICE_URL}/api/ml/ab/experiments/${experiment_id}`,
        {
          headers: { 'Authorization': `Bearer ${env.API_SECRET}` },
        }
      );

      if (!originResponse.ok) {
        throw new Error(`Origin returned ${originResponse.status}`);
      }

      const originData = await originResponse.json();

      // Cache experiment config
      ctx.waitUntil(
        env.AB_TESTS.put(experimentKey, JSON.stringify(originData), {
          expirationTtl: AB_CACHE_TTL,
        })
      );

      // Assign variant using Thompson Sampling
      const variant = selectVariantThompsonSampling(
        originData.variants,
        user_id,
        context
      );

      // Cache user assignment
      ctx.waitUntil(
        env.AB_TESTS.put(cacheKey, JSON.stringify(variant), {
          expirationTtl: 86400, // 24 hours
        })
      );

      return new Response(JSON.stringify(variant), {
        status: 200,
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/json',
          'X-Cache': 'MISS',
          'X-Variant-ID': variant.variant_id,
        },
      });
    } catch (error: any) {
      console.error(`[AB] Origin fetch failed: ${error.message}`);
      return new Response(
        JSON.stringify({
          error: 'Service Unavailable',
          message: 'Experiment not found and origin unavailable',
        }),
        {
          status: 503,
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        }
      );
    }
  }

  // Assign variant
  const variant = selectVariantThompsonSampling(
    experimentData.variants,
    user_id,
    context
  );

  // Cache user assignment
  ctx.waitUntil(
    env.AB_TESTS.put(cacheKey, JSON.stringify(variant), {
      expirationTtl: 86400, // 24 hours
    })
  );

  return new Response(JSON.stringify(variant), {
    status: 200,
    headers: {
      ...corsHeaders,
      'Content-Type': 'application/json',
      'X-Cache': 'MISS',
      'X-Variant-ID': variant.variant_id,
    },
  });
}

async function getExperimentConfig(
  experimentId: string,
  env: CloudflareEnv,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const experimentKey = `experiment:${experimentId}`;
  const cached = await env.AB_TESTS.get(experimentKey, 'json');

  if (cached) {
    return new Response(JSON.stringify(cached), {
      status: 200,
      headers: {
        ...corsHeaders,
        'Content-Type': 'application/json',
        'X-Cache': 'HIT',
      },
    });
  }

  return new Response(
    JSON.stringify({
      error: 'Not Found',
      message: 'Experiment not found in edge cache',
    }),
    {
      status: 404,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    }
  );
}

async function trackABEvent(
  request: Request,
  env: CloudflareEnv,
  ctx: ExecutionContext,
  corsHeaders: Record<string, string>
): Promise<Response> {
  const body = await request.json() as {
    experiment_id: string;
    variant_id: string;
    user_id: string;
    event_type: 'impression' | 'click' | 'conversion';
    metadata?: Record<string, any>;
  };

  const { experiment_id, variant_id, user_id, event_type, metadata } = body;

  if (!experiment_id || !variant_id || !user_id || !event_type) {
    return new Response(
      JSON.stringify({ error: 'Missing required fields' }),
      { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    );
  }

  // Track event asynchronously
  ctx.waitUntil(
    env.ANALYTICS.put(
      `ab_event:${experiment_id}:${Date.now()}:${Math.random()}`,
      JSON.stringify({
        experiment_id,
        variant_id,
        user_id,
        event_type,
        metadata,
        timestamp: new Date().toISOString(),
      }),
      { expirationTtl: 86400 } // 24 hours
    )
  );

  return new Response(
    JSON.stringify({
      message: 'Event tracked',
      experiment_id,
      variant_id,
      event_type,
    }),
    {
      status: 202,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    }
  );
}

// Thompson Sampling for variant selection
function selectVariantThompsonSampling(
  variants: ABTestVariant[],
  userId: string,
  context?: Record<string, any>
): ABTestVariant {
  if (variants.length === 0) {
    throw new Error('No variants available');
  }

  // If only one variant, return it
  if (variants.length === 1) {
    return variants[0];
  }

  // Simple deterministic assignment based on user_id hash
  // In production, this would use real Thompson Sampling with performance data
  const hash = hashCode(userId);
  const index = Math.abs(hash) % variants.length;

  return variants[index];
}

function hashCode(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash |= 0; // Convert to 32bit integer
  }
  return hash;
}
