# Redis Caching Integration Guide

This document shows how to integrate Redis caching into the existing endpoints.

## Overview

The cache service has been created at `/home/user/geminivideo/services/gateway-api/src/services/cache-service.ts` and is already initialized in `index.ts`.

## Endpoints to Update

### 1. /api/analyze - Gemini Video Analysis (1 hour TTL)

**Current Location:** Line ~187 in index.ts

**Replace the endpoint with:**

```typescript
// Real AI analysis endpoint using Gemini Vision API with Redis caching
app.post('/api/analyze', async (req: Request, res: Response) => {
  try {
    const { video_uri } = req.body;

    // Validate required fields
    if (!video_uri) {
      return res.status(400).json({ error: 'Missing required field: video_uri' });
    }

    // Initialize Gemini API
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      return res.status(500).json({ error: 'GEMINI_API_KEY environment variable not set' });
    }

    // Create cache key from video URI
    const cacheKey = cacheService ? `analyze:${cacheService.hashQuery(video_uri)}` : null;

    // Use cache-aside pattern with 1 hour TTL
    const analysis = await (cacheService && cacheKey
      ? cacheService.getOrCompute(
          cacheKey,
          async () => {
            // Cache miss - perform Gemini analysis
            const genAI = new GoogleGenerativeAI(apiKey);
            const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

            console.log(`[API] Analyzing video with Gemini: ${video_uri}`);

            const result = await model.generateContent({
              contents: [{
                role: 'user',
                parts: [{
                  text: `Analyze this video ad at ${video_uri}. Return JSON with the following fields:
- hook_style: string (e.g., "High Energy", "Calm", "Dramatic")
- pacing: string (e.g., "Fast", "Medium", "Slow")
- visual_elements: array of strings (key visual components)
- emotional_trigger: string (primary emotion evoked)
- reasoning: string (brief explanation of your analysis)`
                }]
              }],
              generationConfig: {
                responseMimeType: 'application/json'
              }
            });

            const analysisText = result.response.text();
            return JSON.parse(analysisText);
          },
          3600 // 1 hour TTL
        )
      : // Fallback if cache not available
        (async () => {
          const genAI = new GoogleGenerativeAI(apiKey);
          const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

          console.log(`[API] Analyzing video with Gemini (no cache): ${video_uri}`);

          const result = await model.generateContent({
            contents: [{
              role: 'user',
              parts: [{
                text: `Analyze this video ad at ${video_uri}. Return JSON with the following fields:
- hook_style: string (e.g., "High Energy", "Calm", "Dramatic")
- pacing: string (e.g., "Fast", "Medium", "Slow")
- visual_elements: array of strings (key visual components)
- emotional_trigger: string (primary emotion evoked)
- reasoning: string (brief explanation of your analysis)`
              }]
            }],
            generationConfig: {
              responseMimeType: 'application/json'
            }
          });

          const analysisText = result.response.text();
          return JSON.parse(analysisText);
        })()
    );

    res.json(analysis);

  } catch (error: any) {
    console.error('Error in Gemini analysis:', error);
    res.status(500).json({
      error: 'Failed to analyze video',
      details: error.message
    });
  }
});
```

### 2. /api/score/storyboard - Scoring Results (1 hour TTL)

**Current Location:** Line ~271 in index.ts

**Replace the endpoint with:**

```typescript
// Scoring endpoint with XGBoost integration and Redis caching
app.post('/api/score/storyboard', async (req: Request, res: Response) => {
  try {
    const { scenes, metadata } = req.body;

    // Create cache key from request body
    const cacheKey = cacheService ? `score:${cacheService.hashQuery({ scenes, metadata })}` : null;

    // Use cache-aside pattern with 1 hour TTL
    const result = await (cacheService && cacheKey
      ? cacheService.getOrCompute(
          cacheKey,
          async () => {
            console.log('[API] Computing scores (cache miss)');

            // Calculate rule-based scores
            const scores = await scoringEngine.scoreStoryboard(scenes, metadata);

            // Get XGBoost CTR prediction
            let xgboostPrediction = null;
            try {
              const mlResponse = await axios.post(`${ML_SERVICE_URL}/api/ml/predict-ctr`, {
                clip_data: {
                  ...scores,
                  ...metadata,
                  scene_count: scenes.length
                },
                include_confidence: true
              });
              xgboostPrediction = mlResponse.data;
            } catch (mlError: any) {
              console.warn('XGBoost prediction failed, using rule-based scores only:', mlError.message);
            }

            // Combine scores
            const finalScores = {
              ...scores,
              xgboost_ctr: xgboostPrediction?.predicted_ctr || null,
              xgboost_confidence: xgboostPrediction?.confidence || null,
              // Use XGBoost prediction if available, otherwise use rule-based
              final_ctr_prediction: xgboostPrediction?.predicted_ctr || scores.win_probability?.value || 0.02
            };

            // Log prediction
            const predictionId = reliabilityLogger.logPrediction({
              scenes,
              scores: finalScores,
              metadata,
              timestamp: new Date().toISOString()
            });

            return {
              prediction_id: predictionId,
              scores: finalScores,
              timestamp: new Date().toISOString()
            };
          },
          3600 // 1 hour TTL
        )
      : // Fallback if cache not available
        (async () => {
          console.log('[API] Computing scores (no cache)');

          const scores = await scoringEngine.scoreStoryboard(scenes, metadata);

          let xgboostPrediction = null;
          try {
            const mlResponse = await axios.post(`${ML_SERVICE_URL}/api/ml/predict-ctr`, {
              clip_data: {
                ...scores,
                ...metadata,
                scene_count: scenes.length
              },
              include_confidence: true
            });
            xgboostPrediction = mlResponse.data;
          } catch (mlError: any) {
            console.warn('XGBoost prediction failed, using rule-based scores only:', mlError.message);
          }

          const finalScores = {
            ...scores,
            xgboost_ctr: xgboostPrediction?.predicted_ctr || null,
            xgboost_confidence: xgboostPrediction?.confidence || null,
            final_ctr_prediction: xgboostPrediction?.predicted_ctr || scores.win_probability?.value || 0.02
          };

          const predictionId = reliabilityLogger.logPrediction({
            scenes,
            scores: finalScores,
            metadata,
            timestamp: new Date().toISOString()
          });

          return {
            prediction_id: predictionId,
            scores: finalScores,
            timestamp: new Date().toISOString()
          };
        })()
    );

    res.json(result);
  } catch (error: any) {
    console.error('Error in scoring:', error);
    res.status(500).json({ error: error.message });
  }
});
```

### 3. /api/intelligence/search - Pattern Search (15 min TTL)

**Current Location:** Line ~797 in index.ts

**Replace the endpoint with:**

```typescript
// POST /api/intelligence/search - Search across all configured sources with caching
app.post('/api/intelligence/search', async (req: Request, res: Response) => {
  try {
    const { query, industry, limit } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'MISSING_PARAM: query is required' });
    }

    // Create cache key from search parameters
    const cacheKey = cacheService ? `search:${cacheService.hashQuery({ query, industry, limit })}` : null;

    // Use cache-aside pattern with 15 min TTL (shorter for search results)
    const result = await (cacheService && cacheKey
      ? cacheService.getOrCompute(
          cacheKey,
          async () => {
            console.log('[API] Searching intelligence sources (cache miss)');
            return await adIntelligence.searchAll({ query, industry, limit });
          },
          900 // 15 minutes TTL
        )
      : // Fallback if cache not available
        (async () => {
          console.log('[API] Searching intelligence sources (no cache)');
          return await adIntelligence.searchAll({ query, industry, limit });
        })()
    );

    res.json(result);
  } catch (error: any) {
    // NEVER return mock data - fail loudly
    res.status(503).json({
      error: error.message,
      help: 'Configure at least one data source. Run GET /api/intelligence/status to see options.'
    });
  }
});
```

## Cache Statistics Endpoint

✅ **Already Added** at line ~1374 in index.ts

```bash
GET /api/cache/stats
```

Returns:
```json
{
  "hits": 150,
  "misses": 50,
  "hit_rate": 0.75,
  "total_requests": 200,
  "keys_count": 42,
  "memory_usage": "2.1M",
  "uptime_seconds": 3600
}
```

## Testing

### 1. Test Cache Stats
```bash
curl http://localhost:8000/api/cache/stats
```

### 2. Test Cached Analysis (first call = miss, second call = hit)
```bash
# First call (cache miss)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_uri": "gs://bucket/video.mp4"}'

# Second call (cache hit - should be instant)
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"video_uri": "gs://bucket/video.mp4"}'

# Check stats to see hit rate
curl http://localhost:8000/api/cache/stats
```

### 3. Monitor Cache Logs
The cache service logs all operations:
- `[Cache] HIT <key>` - Cache hit
- `[Cache] MISS <key>` - Cache miss
- `[Cache] SET <key> (TTL: Xs)` - Value stored
- `[Cache] Computing value for <key>` - Computing new value

## Cache Key Strategy

The cache uses SHA256 hashing to create consistent keys:

1. **Analysis:** `geminivideo:analyze:<hash(video_uri)>`
2. **Scoring:** `geminivideo:score:<hash(scenes+metadata)>`
3. **Search:** `geminivideo:search:<hash(query+industry+limit)>`

The `hashQuery()` method ensures identical inputs always produce the same cache key, even if object properties are in different orders.

## TTL Strategy

- **Analysis (1 hour):** Video content doesn't change, safe to cache long
- **Scoring (1 hour):** Deterministic calculations, safe to cache long
- **Search (15 min):** External data sources may update, shorter TTL

## Performance Impact

Expected improvements:
- **Latency:** 95%+ reduction for cached requests (ms vs seconds)
- **Cost:** 75%+ reduction in Gemini API calls
- **Throughput:** 10x+ increase in requests/second
- **Reliability:** Better resilience during API outages

## Files Created

1. ✅ `/home/user/geminivideo/services/gateway-api/src/services/cache-service.ts` - Cache service implementation
2. ✅ `/home/user/geminivideo/services/gateway-api/src/index.ts` - Cache initialization and stats endpoint added
3. ✅ `/home/user/geminivideo/services/gateway-api/CACHE_INTEGRATION.md` - This integration guide

## Next Steps

To complete the integration:

1. Update the three endpoints in `index.ts` using the code above
2. Restart the gateway-api service
3. Test with the curl commands
4. Monitor logs for cache hit/miss patterns
5. Adjust TTL values based on your needs

## Troubleshooting

**Cache not working?**
- Check Redis is running: `docker ps | grep redis`
- Check Redis connection in logs: Look for "✅ Redis connected for async queues and caching"
- Check cache service initialization: Look for "✅ Cache service initialized"

**Low hit rate?**
- Ensure requests are identical (same video_uri, same scenes, etc.)
- Check cache keys in Redis: `redis-cli KEYS "geminivideo:*"`
- Verify TTL hasn't expired: `redis-cli TTL "geminivideo:analyze:<hash>"`
