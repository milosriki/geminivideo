# 🗺️ EXTENDED COMPLETE ROADMAP TO PRODUCTION
## Every Detail: Wiring, Frontend, Backend, Supabase, Cloud Run

**Generated:** 2024-12-08  
**Current Status:** 85% Complete  
**Target:** 100% Production-Ready  
**Timeline:** 6 weeks (or 2 weeks intensive)

---

## 📊 EXECUTIVE SUMMARY

### What's Done (85%)
- ✅ Core ML intelligence (BattleHardenedSampler, RAG, Synthetic Revenue)
- ✅ Database migrations (6/6 complete)
- ✅ Backend services (ML, Gateway, Titan-Core, Video-Agent)
- ✅ Safety systems (SafeExecutor, job queue)
- ✅ Self-learning loops (7/7 wired)
- ✅ Frontend exists (React + TypeScript)

### What's Left (15%)
- ⚠️ Final wiring (RAG → Creative Generation)
- ⚠️ Frontend integration (expose all features)
- ⚠️ Deployment automation (Cloud Run, Supabase)
- ⚠️ Monitoring & alerting (production observability)
- ⚠️ Testing & validation (end-to-end tests)

---

## 🎯 PHASE 1: CRITICAL WIRING (Week 1) - 13 hours

### Step 1.1: Wire RAG to Creative Generation (4 hours)

**Files to Modify:**
1. `services/titan-core/ai_council/director_agent.py`
2. `services/ml-service/src/main.py` (feedback endpoint)
3. `services/titan-core/api/main.py` (if needed)

**Code Changes:**

```python
# File: services/titan-core/ai_council/director_agent.py

async def create_battle_plan(self, video_id: str, creative_dna: dict):
    """
    Create battle plan with RAG context from similar winners.
    """
    # STEP 1: Search for similar winners
    ml_service_url = os.getenv('ML_SERVICE_URL', 'http://ml-service:8003')
    
    similar_winners = await httpx.post(
        f"{ml_service_url}/api/ml/rag/search-winners",
        json={
            "query": json.dumps(creative_dna),  # Use creative DNA as query
            "top_k": 5
        },
        timeout=10.0
    )
    
    winners_data = similar_winners.json()
    
    # STEP 2: Use winners in prompt
    prompt = f"""
    Here are 5 winning ads similar to this video:
    {json.dumps(winners_data['winners'], indent=2)}
    
    Create a battle plan that applies their proven patterns:
    - Hook style: {winners_data['winners'][0]['metadata'].get('hook_type')}
    - Pacing: {winners_data['winners'][0]['metadata'].get('visual_pacing')}
    - CTA style: {winners_data['winners'][0]['metadata'].get('cta_type')}
    
    Video Creative DNA:
    {json.dumps(creative_dna, indent=2)}
    """
    
    # STEP 3: Generate plan with Gemini
    plan = await self.gemini_client.generate_content(prompt)
    
    return plan
```

```python
# File: services/ml-service/src/main.py
# Modify: battle_hardened_feedback endpoint

@app.post("/api/ml/battle-hardened/feedback", tags=["Battle-Hardened Sampler"])
async def battle_hardened_feedback(request: BattleHardenedFeedbackRequest):
    """Register actual performance feedback for model improvement"""
    try:
        sampler = get_battle_hardened_sampler()
        result = sampler.register_feedback(
            ad_id=request.ad_id,
            actual_pipeline_value=request.actual_pipeline_value,
            actual_spend=request.actual_spend,
        )
        
        # NEW: Auto-index winners
        if request.actual_pipeline_value / max(request.actual_spend, 1) > 3.0:
            # This is a winner! Index it
            winner_index = get_winner_index()
            
            # Get creative DNA for this ad
            creative_dna = await get_creative_dna_for_ad(request.ad_id)
            
            # Create embedding from creative DNA
            embedding = create_embedding(creative_dna)
            
            # Add to index
            await winner_index.add_winner(
                ad_id=request.ad_id,
                embedding=embedding,
                metadata={
                    'creative_dna': creative_dna,
                    'pipeline_roas': request.actual_pipeline_value / max(request.actual_spend, 1),
                    'ctr': request.actual_clicks / max(request.actual_impressions, 1)
                }
            )
        
        return {
            "status": "feedback_registered",
            "ad_id": result["ad_id"],
            "actual_roas": result["actual_roas"],
            "timestamp": result["timestamp"],
        }
    except Exception as e:
        logger.error(f"Error registering feedback: {e}", exc_info=True)
        raise HTTPException(500, str(e))
```

**Test:**
```bash
# 1. Upload test video
curl -X POST http://localhost:8080/api/videos/upload

# 2. Verify RAG search in logs
docker-compose logs titan-core | grep "similar winners"

# 3. Verify winner auto-indexing
curl http://localhost:8003/api/ml/rag/memory-stats
```

---

### Step 1.2: Wire HubSpot to Celery Queue (3 hours)

**Files to Create/Modify:**
1. `services/ml-service/src/tasks.py` (CREATE)
2. `services/gateway-api/src/webhooks/hubspot.ts` (MODIFY)
3. `docker-compose.yml` (ADD worker)

**Code Changes:**

```python
# File: services/ml-service/src/tasks.py (CREATE NEW FILE)

from celery import Celery
import os
import httpx
import logging

logger = logging.getLogger(__name__)

# Celery app
celery_app = Celery('ml_service')
celery_app.conf.broker_url = os.getenv('REDIS_URL', 'redis://redis:6379')
celery_app.conf.result_backend = os.getenv('REDIS_URL', 'redis://redis:6379')

ML_SERVICE_URL = os.getenv('ML_SERVICE_URL', 'http://localhost:8003')

@celery_app.task(name='process_hubspot_webhook', bind=True, max_retries=3)
def process_hubspot_webhook(self, webhook_payload: dict):
    """
    Process HubSpot webhook asynchronously.
    
    Flow:
    1. Calculate synthetic revenue
    2. Attribute to ad click
    3. Send feedback to BattleHardenedSampler
    """
    try:
        # Import here to avoid circular dependencies
        from src.synthetic_revenue import SyntheticRevenueCalculator
        from src.hubspot_attribution import HubSpotAttribution
        
        calculator = SyntheticRevenueCalculator()
        attribution = HubSpotAttribution()
        
        # 1. Calculate synthetic revenue
        deal_id = webhook_payload.get('dealId')
        stage_to = webhook_payload.get('stageTo')
        tenant_id = webhook_payload.get('tenantId')
        
        synthetic_result = calculator.calculate_stage_change(
            tenant_id=tenant_id,
            stage_from=webhook_payload.get('stageFrom'),
            stage_to=stage_to
        )
        
        # 2. Attribute to ad
        attribution_result = attribution.attribute_conversion(
            contact_email=webhook_payload.get('contactEmail'),
            deal_value=synthetic_result.calculated_value
        )
        
        if attribution_result.ad_id:
            # 3. Send feedback to BattleHardenedSampler
            httpx.post(
                f"{ML_SERVICE_URL}/api/ml/battle-hardened/feedback",
                json={
                    "ad_id": attribution_result.ad_id,
                    "actual_pipeline_value": synthetic_result.calculated_value,
                    "actual_spend": attribution_result.attributed_spend or 0,
                },
                timeout=10.0
            )
            
            logger.info(f"Feedback sent for ad {attribution_result.ad_id}")
        
        return {"status": "processed", "ad_id": attribution_result.ad_id}
        
    except Exception as e:
        logger.error(f"Error processing HubSpot webhook: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

```typescript
// File: services/gateway-api/src/webhooks/hubspot.ts
// MODIFY: Queue to Celery instead of direct processing

import { createClient } from 'redis';

const redisClient = createClient({ url: process.env.REDIS_URL });

router.post('/webhooks/hubspot', async (req: Request, res: Response) => {
  try {
    // 1. Verify HubSpot signature
    const signature = req.headers['x-hubspot-signature-v3'];
    if (!verifyHubSpotSignature(req.body, signature)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }
    
    // 2. Queue to Celery (via Redis)
    await redisClient.lPush(
      'celery',
      JSON.stringify({
        task: 'process_hubspot_webhook',
        args: [req.body],
        id: uuidv4()
      })
    );
    
    // 3. Return immediately
    res.status(200).json({ status: 'queued' });
    
  } catch (error) {
    logger.error('HubSpot webhook error:', error);
    res.status(500).json({ error: 'Internal error' });
  }
});
```

```yaml
# File: docker-compose.yml
# ADD: Celery worker

hubspot-worker:
  build:
    context: ./services/ml-service
    dockerfile: Dockerfile
  container_name: geminivideo-hubspot-worker
  environment:
    DATABASE_URL: postgresql://geminivideo:geminivideo@postgres:5432/geminivideo
    REDIS_URL: redis://redis:6379
    ML_SERVICE_URL: http://ml-service:8003
  depends_on:
    - redis
    - postgres
    - ml-service
  command: celery -A src.tasks worker --loglevel=info -Q hubspot-webhook-events
  restart: unless-stopped
  networks:
    - geminivideo-network
```

**Test:**
```bash
# 1. Send test webhook
curl -X POST http://localhost:8080/webhooks/hubspot \
  -H "Content-Type: application/json" \
  -d '{"dealId": "123", "stageTo": "appointment_scheduled", "tenantId": "test"}'

# 2. Check Celery logs
docker-compose logs hubspot-worker

# 3. Verify feedback sent
docker-compose logs ml-service | grep "Feedback registered"
```

---

### Step 1.3: Wire Pre-Spend Prediction (3 hours)

**Files to Create/Modify:**
1. `services/ml-service/src/main.py` (ADD endpoint)
2. `services/titan-core/ai_council/director_agent.py` (MODIFY)

**Code Changes:**

```python
# File: services/ml-service/src/main.py
# ADD: New endpoint after line 3600

class CreativePredictionRequest(BaseModel):
    """Request for pre-spend creative performance prediction"""
    creative_dna: Dict[str, Any]
    account_id: str
    rag_context: Optional[Dict[str, Any]] = None

@app.post("/api/ml/predict-creative", tags=["Prediction"])
async def predict_creative_performance(request: CreativePredictionRequest):
    """
    Predict CTR/ROAS BEFORE spending budget.
    Decision gate: REJECT if < 70% of account average.
    """
    try:
        # 1. Get Oracle prediction from Titan-Core
        titan_core_url = os.getenv('TITAN_CORE_URL', 'http://titan-core:8084')
        
        oracle_response = await httpx.post(
            f"{titan_core_url}/api/titan/oracle/predict",
            json={
                "creative_dna": request.creative_dna,
                "rag_context": request.rag_context
            },
            timeout=15.0
        )
        
        oracle_data = oracle_response.json()
        predicted_ctr = oracle_data.get('predicted_ctr', 0)
        predicted_roas = oracle_data.get('predicted_roas', 0)
        confidence = oracle_data.get('confidence', 0)
        
        # 2. Get account baseline
        account_baseline = await get_account_baseline(request.account_id)
        
        # 3. Decision gate
        if predicted_ctr < account_baseline * 0.70:
            return {
                "decision": "REJECT",
                "reason": f"Predicted CTR {predicted_ctr:.2%} below 70% of account average ({account_baseline:.2%})",
                "recommendation": "Fix hook pacing or increase text contrast",
                "predicted_ctr": predicted_ctr,
                "confidence": confidence
            }
        
        return {
            "decision": "PROCEED",
            "predicted_ctr": predicted_ctr,
            "predicted_roas": predicted_roas,
            "confidence": confidence,
            "recommendation": "High potential creative. Proceed with variations."
        }
        
    except Exception as e:
        logger.error(f"Error in creative prediction: {e}", exc_info=True)
        raise HTTPException(500, str(e))
```

```python
# File: services/titan-core/ai_council/director_agent.py
# MODIFY: create_battle_plan method

async def create_battle_plan(self, video_id: str, creative_dna: dict):
    """
    Create battle plan with pre-spend prediction gate.
    """
    # STEP 1: Get prediction BEFORE creating plan
    ml_service_url = os.getenv('ML_SERVICE_URL', 'http://ml-service:8003')
    
    prediction = await httpx.post(
        f"{ml_service_url}/api/ml/predict-creative",
        json={
            "creative_dna": creative_dna,
            "account_id": self.account_id
        },
        timeout=15.0
    )
    
    prediction_data = prediction.json()
    
    # STEP 2: Decision gate
    if prediction_data['decision'] == 'REJECT':
        # Focus plan on fixing identified weaknesses
        return self.create_fix_plan(
            video_id=video_id,
            issues=prediction_data['recommendation']
        )
    
    # STEP 3: Proceed with normal plan creation
    # (existing code continues...)
```

**Test:**
```bash
# 1. Test with low-potential creative
curl -X POST http://localhost:8003/api/ml/predict-creative \
  -d '{"creative_dna": {"hook_strength": 0.3}, "account_id": "test"}'
# Expected: REJECT

# 2. Test with high-potential creative
curl -X POST http://localhost:8003/api/ml/predict-creative \
  -d '{"creative_dna": {"hook_strength": 0.9}, "account_id": "test"}'
# Expected: PROCEED
```

---

### Step 1.4: Wire Real-Time Fatigue Monitoring (3 hours)

**Files to Create/Modify:**
1. `services/ml-service/src/tasks.py` (ADD periodic task)
2. `docker-compose.yml` (ADD celery-beat)

**Code Changes:**

```python
# File: services/ml-service/src/tasks.py
# ADD: After existing tasks

from celery.schedules import crontab
from src.fatigue_detector import detect_fatigue

@celery_app.task(name='monitor_fatigue')
def monitor_all_ads():
    """
    Monitor all active ads for fatigue.
    Runs every 2 hours.
    """
    from db.models import Ad, PerformanceMetric
    from db.session import get_db
    
    db = next(get_db())
    
    # Get all active ads
    active_ads = db.query(Ad).filter(Ad.status == 'ACTIVE').all()
    
    for ad in active_ads:
        # Get metrics history (last 7 days)
        metrics = db.query(PerformanceMetric).filter(
            PerformanceMetric.ad_id == ad.id,
            PerformanceMetric.created_at >= datetime.utcnow() - timedelta(days=7)
        ).order_by(PerformanceMetric.created_at).all()
        
        # Convert to list of dicts
        metrics_history = [
            {
                'ctr': m.ctr,
                'frequency': m.frequency,
                'cpm': m.cpm,
                'impressions': m.impressions
            }
            for m in metrics
        ]
        
        # Detect fatigue
        result = detect_fatigue(ad.id, metrics_history)
        
        if result.status in ['FATIGUING', 'SATURATED', 'AUDIENCE_EXHAUSTED']:
            # Auto-remediate
            auto_remediate_fatigue(ad.id, result)

def auto_remediate_fatigue(ad_id: str, fatigue_result):
    """
    Auto-remediate fatiguing ad:
    1. Gradually reduce budget
    2. Trigger replacement creative generation
    """
    from db.models import Ad
    from db.session import get_db
    import httpx
    
    db = next(get_db())
    ad = db.query(Ad).filter(Ad.id == ad_id).first()
    
    if not ad:
        return
    
    # 1. Reduce budget by 20%
    current_budget = ad.daily_budget
    new_budget = current_budget * 0.8
    
    # Queue budget reduction
    gateway_url = os.getenv('GATEWAY_API_URL', 'http://gateway-api:8080')
    httpx.post(
        f"{gateway_url}/api/ml/battle-hardened/select",
        json={
            "ad_states": [{
                "ad_id": ad_id,
                "impressions": ad.impressions,
                "clicks": ad.clicks,
                "spend": ad.spend,
                "pipeline_value": ad.pipeline_value,
                "cash_revenue": ad.revenue,
                "age_hours": (datetime.utcnow() - ad.created_at).total_seconds() / 3600
            }],
            "total_budget": new_budget
        }
    )
    
    # 2. Trigger creative refresh
    titan_core_url = os.getenv('TITAN_CORE_URL', 'http://titan-core:8084')
    httpx.post(
        f"{titan_core_url}/api/titan/director/refresh-creative",
        json={
            "ad_id": ad_id,
            "reason": f"Fatigue detected: {fatigue_result.reason}"
        }
    )
    
    logger.info(f"Auto-remediated ad {ad_id}: {fatigue_result.reason}")

# Schedule periodic task
celery_app.conf.beat_schedule = {
    'monitor-fatigue-every-2-hours': {
        'task': 'monitor_fatigue',
        'schedule': crontab(minute=0, hour='*/2'),  # Every 2 hours
    },
}
```

```yaml
# File: docker-compose.yml
# ADD: Celery Beat

celery-beat:
  build:
    context: ./services/ml-service
    dockerfile: Dockerfile
  container_name: geminivideo-celery-beat
  environment:
    DATABASE_URL: postgresql://geminivideo:geminivideo@postgres:5432/geminivideo
    REDIS_URL: redis://redis:6379
  depends_on:
    - redis
    - postgres
  command: celery -A src.tasks beat --loglevel=info
  restart: unless-stopped
  networks:
    - geminivideo-network
```

**Test:**
```bash
# 1. Check Celery Beat is running
docker-compose logs celery-beat

# 2. Manually trigger task
docker-compose exec ml-service celery -A src.tasks call monitor_fatigue

# 3. Verify fatigue detection
docker-compose logs ml-service | grep "FATIGUING"
```

---

## 🎯 PHASE 2: FRONTEND INTEGRATION (Week 2) - 11 hours

### Step 2.1: Wire BattleHardenedSampler to Frontend (4 hours)

**Files to Create/Modify:**
1. `frontend/src/services/mlApi.ts` (CREATE)
2. `frontend/src/components/BudgetOptimizer.tsx` (CREATE)
3. `frontend/src/pages/CampaignsPage.tsx` (MODIFY)

**Code Changes:**

```typescript
// File: frontend/src/services/mlApi.ts (CREATE NEW FILE)

import { apiClient } from './api';

export interface AdState {
  ad_id: string;
  impressions: number;
  clicks: number;
  spend: number;
  pipeline_value?: number;
  cash_revenue?: number;
  age_hours: number;
}

export interface BudgetRecommendation {
  ad_id: string;
  current_budget: number;
  recommended_budget: number;
  change_percentage: number;
  confidence: number;
  reason: string;
  metrics: {
    impressions: number;
    clicks: number;
    ctr: number;
    pipeline_roas: number;
    ctr_weight: number;
    roas_weight: number;
    blended_score: number;
    decay_factor: number;
    age_hours: number;
  };
}

export interface BudgetOptimizationRequest {
  ad_states: AdState[];
  total_budget: number;
  creative_dna_scores?: Record<string, number>;
}

export interface BudgetOptimizationResponse {
  total_budget: number;
  recommendations: BudgetRecommendation[];
  num_ads: number;
}

export const mlApi = {
  /**
   * Optimize budget allocation across ads using BattleHardenedSampler
   */
  optimizeBudget: async (
    request: BudgetOptimizationRequest
  ): Promise<BudgetOptimizationResponse> => {
    const response = await apiClient.post<BudgetOptimizationResponse>(
      '/api/ml/battle-hardened/select',
      request
    );
    return response.data;
  },

  /**
   * Register performance feedback
   */
  registerFeedback: async (
    adId: string,
    actualPipelineValue: number,
    actualSpend: number
  ): Promise<void> => {
    await apiClient.post('/api/ml/battle-hardened/feedback', {
      ad_id: adId,
      actual_pipeline_value: actualPipelineValue,
      actual_spend: actualSpend,
    });
  },
};
```

```typescript
// File: frontend/src/components/BudgetOptimizer.tsx (CREATE NEW FILE)

import React, { useState } from 'react';
import { mlApi, BudgetRecommendation } from '../services/mlApi';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface BudgetOptimizerProps {
  campaignId: string;
  adStates: mlApi.AdState[];
  totalBudget: number;
  onOptimizationComplete?: (recommendations: BudgetRecommendation[]) => void;
}

export const BudgetOptimizer: React.FC<BudgetOptimizerProps> = ({
  campaignId,
  adStates,
  totalBudget,
  onOptimizationComplete,
}) => {
  const [recommendations, setRecommendations] = useState<BudgetRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleOptimize = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await mlApi.optimizeBudget({
        ad_states: adStates,
        total_budget: totalBudget,
      });

      setRecommendations(result.recommendations);
      onOptimizationComplete?.(result.recommendations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="text-2xl font-bold mb-4">Budget Optimization</h2>
      
      <div className="mb-4">
        <p className="text-gray-600 mb-2">
          Total Budget: ${totalBudget.toLocaleString()}
        </p>
        <p className="text-gray-600 mb-4">
          Number of Ads: {adStates.length}
        </p>
      </div>

      <Button
        onClick={handleOptimize}
        disabled={loading || adStates.length === 0}
        className="mb-4"
      >
        {loading ? 'Optimizing...' : 'Optimize Budget'}
      </Button>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {recommendations.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">Recommendations</h3>
          {recommendations.map((rec) => (
            <BudgetRecommendationCard
              key={rec.ad_id}
              recommendation={rec}
            />
          ))}
        </div>
      )}
    </Card>
  );
};

const BudgetRecommendationCard: React.FC<{
  recommendation: BudgetRecommendation;
}> = ({ recommendation }) => {
  const changeColor =
    recommendation.change_percentage > 0
      ? 'text-green-600'
      : recommendation.change_percentage < 0
      ? 'text-red-600'
      : 'text-gray-600';

  return (
    <Card className="p-4">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-semibold">Ad ID: {recommendation.ad_id}</h4>
          <p className="text-sm text-gray-600">{recommendation.reason}</p>
        </div>
        <div className="text-right">
          <p className={`font-bold ${changeColor}`}>
            {recommendation.change_percentage > 0 ? '+' : ''}
            {recommendation.change_percentage.toFixed(1)}%
          </p>
          <p className="text-sm text-gray-500">
            Confidence: {(recommendation.confidence * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
        <div>
          <p className="text-gray-600">Current Budget</p>
          <p className="font-semibold">${recommendation.current_budget.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-gray-600">Recommended Budget</p>
          <p className="font-semibold">${recommendation.recommended_budget.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-gray-600">CTR</p>
          <p className="font-semibold">{recommendation.metrics.ctr.toFixed(2)}%</p>
        </div>
        <div>
          <p className="text-gray-600">Pipeline ROAS</p>
          <p className="font-semibold">{recommendation.metrics.pipeline_roas.toFixed(2)}x</p>
        </div>
      </div>
    </Card>
  );
};
```

```typescript
// File: frontend/src/pages/CampaignsPage.tsx
// MODIFY: Add BudgetOptimizer component

import { BudgetOptimizer } from '../components/BudgetOptimizer';

// In CampaignDetails component:
<BudgetOptimizer
  campaignId={campaign.id}
  adStates={campaign.ads.map(ad => ({
    ad_id: ad.id,
    impressions: ad.impressions,
    clicks: ad.clicks,
    spend: ad.spend,
    pipeline_value: ad.pipeline_value,
    cash_revenue: ad.revenue,
    age_hours: (Date.now() - new Date(ad.created_at).getTime()) / (1000 * 60 * 60)
  }))}
  totalBudget={campaign.total_budget}
  onOptimizationComplete={(recommendations) => {
    // Show success message
    toast.success(`Optimized ${recommendations.length} ads`);
  }}
/>
```

**Test:**
```bash
# 1. Start frontend
cd frontend && npm run dev

# 2. Navigate to Campaigns page
# 3. Click "Optimize Budget"
# 4. Verify recommendations appear
```

---

### Step 2.2: Wire RAG Winner Index to Frontend (3 hours)

**Files to Create:**
1. `frontend/src/components/WinnerSearch.tsx` (CREATE)
2. `frontend/src/services/mlApi.ts` (ADD methods)

**Code Changes:**

```typescript
// File: frontend/src/services/mlApi.ts
// ADD: RAG methods

export interface WinnerMatch {
  ad_id: string;
  similarity: number;
  metadata: {
    creative_dna?: any;
    pipeline_roas?: number;
    ctr?: number;
  };
}

export interface WinnerSearchRequest {
  query: string;
  top_k?: number;
}

export interface WinnerSearchResponse {
  query: string;
  total_in_memory: number;
  results_found: number;
  winners: WinnerMatch[];
  memory_backend: string;
}

export const mlApi = {
  // ... existing methods ...

  /**
   * Search for similar winning ads
   */
  searchWinners: async (
    request: WinnerSearchRequest
  ): Promise<WinnerSearchResponse> => {
    const response = await apiClient.post<WinnerSearchResponse>(
      '/api/ml/rag/search-winners',
      request
    );
    return response.data;
  },

  /**
   * Get RAG memory stats
   */
  getRAGStats: async (): Promise<any> => {
    const response = await apiClient.get('/api/ml/rag/memory-stats');
    return response.data;
  },
};
```

```typescript
// File: frontend/src/components/WinnerSearch.tsx (CREATE NEW FILE)

import React, { useState, useEffect } from 'react';
import { mlApi, WinnerMatch } from '../services/mlApi';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface WinnerSearchProps {
  videoId?: string;
  creativeDNA?: any;
  onWinnerSelected?: (winner: WinnerMatch) => void;
}

export const WinnerSearch: React.FC<WinnerSearchProps> = ({
  videoId,
  creativeDNA,
  onWinnerSelected,
}) => {
  const [winners, setWinners] = useState<WinnerMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);

  useEffect(() => {
    // Load stats on mount
    mlApi.getRAGStats().then(setStats);
  }, []);

  const handleSearch = async () => {
    if (!creativeDNA) return;

    setLoading(true);
    try {
      const result = await mlApi.searchWinners({
        query: JSON.stringify(creativeDNA),
        top_k: 5,
      });
      setWinners(result.winners);
    } catch (err) {
      console.error('Winner search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="text-2xl font-bold mb-4">Find Similar Winners</h2>

      {stats && (
        <div className="mb-4 p-3 bg-gray-50 rounded">
          <p className="text-sm text-gray-600">
            Total Winners in Memory: {stats.total_winners_in_memory}
          </p>
          <p className="text-sm text-gray-600">
            FAISS Index Size: {stats.faiss_index_size}
          </p>
        </div>
      )}

      <Button
        onClick={handleSearch}
        disabled={loading || !creativeDNA}
        className="mb-4"
      >
        {loading ? 'Searching...' : 'Find Similar Winners'}
      </Button>

      {winners.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-xl font-semibold">
            Found {winners.length} Similar Winners
          </h3>
          {winners.map((winner) => (
            <WinnerCard
              key={winner.ad_id}
              winner={winner}
              onSelect={() => onWinnerSelected?.(winner)}
            />
          ))}
        </div>
      )}
    </Card>
  );
};

const WinnerCard: React.FC<{
  winner: WinnerMatch;
  onSelect: () => void;
}> = ({ winner, onSelect }) => {
  const similarityPercent = (winner.similarity * 100).toFixed(1);

  return (
    <Card className="p-4 cursor-pointer hover:bg-gray-50" onClick={onSelect}>
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-semibold">Ad ID: {winner.ad_id}</h4>
          <p className="text-sm text-gray-600">
            Similarity: {similarityPercent}%
          </p>
        </div>
        <div className="text-right">
          {winner.metadata.pipeline_roas && (
            <p className="text-sm">
              ROAS: {winner.metadata.pipeline_roas.toFixed(2)}x
            </p>
          )}
          {winner.metadata.ctr && (
            <p className="text-sm">CTR: {(winner.metadata.ctr * 100).toFixed(2)}%</p>
          )}
        </div>
      </div>

      {winner.metadata.creative_dna && (
        <div className="mt-2 text-xs text-gray-500">
          <p>Hook: {winner.metadata.creative_dna.hook_type}</p>
          <p>Pacing: {winner.metadata.creative_dna.visual_pacing}</p>
        </div>
      )}
    </Card>
  );
};
```

**Test:**
```bash
# 1. Navigate to video analysis page
# 2. Click "Find Similar Winners"
# 3. Verify results appear with similarity scores
```

---

### Step 2.3: Wire Self-Learning Cycle to Frontend (2 hours)

**Files to Create:**
1. `frontend/src/components/LearningDashboard.tsx` (CREATE)

**Code Changes:**

```typescript
// File: frontend/src/components/LearningDashboard.tsx (CREATE NEW FILE)

import React, { useState } from 'react';
import { mlApi } from '../services/mlApi';
import { Button } from './ui/button';
import { Card } from './ui/card';

interface LearningStep {
  step: number;
  name: string;
  status?: string;
  successful?: number;
  failed?: number;
  accuracy?: number;
  triggered?: boolean;
  new_patterns?: number;
  promoted?: number;
}

interface LearningCycleResult {
  cycle_started_at: string;
  cycle_completed_at?: string;
  duration_seconds?: number;
  status: string;
  steps: LearningStep[];
}

export const LearningDashboard: React.FC<{ accountId: string }> = ({
  accountId,
}) => {
  const [cycleStatus, setCycleStatus] = useState<LearningCycleResult | null>(null);
  const [loading, setLoading] = useState(false);

  const triggerCycle = async () => {
    setLoading(true);
    try {
      const result = await mlApi.triggerSelfLearningCycle({
        account_id: accountId,
        trigger_retrain: true,
        accuracy_threshold: 0.80,
      });
      setCycleStatus(result);
    } catch (err) {
      console.error('Learning cycle failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="p-6">
      <h2 className="text-2xl font-bold mb-4">Self-Learning System</h2>

      <Button onClick={triggerCycle} disabled={loading} className="mb-4">
        {loading ? 'Running...' : 'Run Learning Cycle'}
      </Button>

      {cycleStatus && (
        <div className="space-y-4">
          <div className="flex justify-between text-sm">
            <span>Status: {cycleStatus.status}</span>
            {cycleStatus.duration_seconds && (
              <span>Duration: {cycleStatus.duration_seconds.toFixed(1)}s</span>
            )}
          </div>

          <div className="space-y-2">
            <h3 className="font-semibold">Learning Steps:</h3>
            {cycleStatus.steps.map((step) => (
              <LearningStepCard key={step.step} step={step} />
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};

const LearningStepCard: React.FC<{ step: LearningStep }> = ({ step }) => {
  const getStatusColor = () => {
    if (step.status === 'completed') return 'bg-green-100';
    if (step.status === 'active') return 'bg-blue-100';
    return 'bg-gray-100';
  };

  return (
    <Card className={`p-3 ${getStatusColor()}`}>
      <div className="flex justify-between items-center">
        <div>
          <p className="font-semibold">
            Step {step.step}: {step.name}
          </p>
          {step.accuracy && (
            <p className="text-sm">Accuracy: {(step.accuracy * 100).toFixed(1)}%</p>
          )}
          {step.new_patterns !== undefined && (
            <p className="text-sm">New Patterns: {step.new_patterns}</p>
          )}
          {step.promoted !== undefined && (
            <p className="text-sm">Promoted: {step.promoted}</p>
          )}
        </div>
        <div className="text-right">
          {step.status && (
            <span className="text-xs px-2 py-1 bg-white rounded">
              {step.status}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
};
```

---

### Step 2.4: Wire Synthetic Revenue to Frontend (2 hours)

**Files to Create:**
1. `frontend/src/components/PipelineValueDashboard.tsx` (CREATE)

**Code Changes:**

```typescript
// File: frontend/src/components/PipelineValueDashboard.tsx (CREATE NEW FILE)

import React, { useState, useEffect } from 'react';
import { mlApi } from '../services/mlApi';
import { Card } from './ui/card';
import { Button } from './ui/button';

interface StageValue {
  stage_name: string;
  value: number;
  confidence: number;
  description?: string;
}

export const PipelineValueDashboard: React.FC<{ tenantId: string }> = ({
  tenantId,
}) => {
  const [stages, setStages] = useState<StageValue[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<number>(0);

  useEffect(() => {
    loadStages();
  }, [tenantId]);

  const loadStages = async () => {
    try {
      const result = await mlApi.getPipelineStages(tenantId);
      setStages(result.stages);
    } catch (err) {
      console.error('Failed to load stages:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (stageName: string) => {
    try {
      await mlApi.updateStageValue(tenantId, stageName, editValue);
      await loadStages();
      setEditing(null);
    } catch (err) {
      console.error('Failed to update stage:', err);
    }
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <Card className="p-6">
      <h2 className="text-2xl font-bold mb-4">Pipeline Stage Values</h2>
      <p className="text-gray-600 mb-4">
        Configure synthetic revenue values for each CRM stage
      </p>

      <div className="space-y-4">
        {stages.map((stage) => (
          <Card key={stage.stage_name} className="p-4">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">{stage.stage_name}</h3>
                {stage.description && (
                  <p className="text-sm text-gray-600">{stage.description}</p>
                )}
                <p className="text-xs text-gray-500">
                  Confidence: {(stage.confidence * 100).toFixed(0)}%
                </p>
              </div>
              <div className="text-right">
                {editing === stage.stage_name ? (
                  <div className="flex gap-2">
                    <input
                      type="number"
                      value={editValue}
                      onChange={(e) => setEditValue(parseFloat(e.target.value))}
                      className="w-24 px-2 py-1 border rounded"
                    />
                    <Button
                      size="sm"
                      onClick={() => handleSave(stage.stage_name)}
                    >
                      Save
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditing(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <div>
                    <p className="text-2xl font-bold">
                      ${stage.value.toLocaleString()}
                    </p>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setEditing(stage.stage_name);
                        setEditValue(stage.value);
                      }}
                    >
                      Edit
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </Card>
  );
};
```

---

## 🎯 PHASE 3: SUPABASE SETUP (Week 3) - 4 hours

### Step 3.1: Create Supabase Project (1 hour)

**Actions:**
1. Go to supabase.com
2. Create new project
3. Note connection details:
   - Database URL
   - API URL
   - Anon Key
   - Service Role Key

### Step 3.2: Run Migrations (1 hour)

```bash
# Connect to Supabase
export SUPABASE_DB_URL="postgresql://postgres:[password]@db.[project].supabase.co:5432/postgres"

# Run migrations
psql $SUPABASE_DB_URL < database/migrations/001_ad_change_history.sql
psql $SUPABASE_DB_URL < database/migrations/002_synthetic_revenue_config.sql
psql $SUPABASE_DB_URL < database/migrations/003_attribution_tracking.sql
psql $SUPABASE_DB_URL < database/migrations/004_pgboss_extension.sql
psql $SUPABASE_DB_URL < database/migrations/005_pending_ad_changes.sql
psql $SUPABASE_DB_URL < database/migrations/006_model_registry.sql

# Enable pgvector extension
psql $SUPABASE_DB_URL -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Step 3.3: Update Environment Variables (1 hour)

```bash
# .env files for all services
DATABASE_URL=$SUPABASE_DB_URL
SUPABASE_URL=https://[project].supabase.co
SUPABASE_ANON_KEY=[anon key]
SUPABASE_SERVICE_ROLE_KEY=[service role key]
```

### Step 3.4: Test Connection (1 hour)

```bash
# Test from each service
docker-compose exec ml-service python -c "from db.session import get_db; next(get_db())"
docker-compose exec gateway-api node -e "require('pg').Pool({connectionString: process.env.DATABASE_URL}).query('SELECT 1')"
```

---

## 🎯 PHASE 4: CLOUD RUN DEPLOYMENT (Week 3) - 6 hours

### Step 4.1: Create Service Definitions (2 hours)

```yaml
# cloud-run/ml-service.yaml

apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ml-service
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      serviceAccountName: ml-service-sa
      containers:
      - image: gcr.io/[PROJECT_ID]/ml-service:latest
        ports:
        - containerPort: 8003
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        resources:
          limits:
            cpu: "2"
            memory: 4Gi
          requests:
            cpu: "1"
            memory: 2Gi
```

### Step 4.2: Create GitHub Actions Workflow (2 hours)

```yaml
# .github/workflows/deploy.yml

name: Deploy to Cloud Run

on:
  push:
    branches: [main]

env:
  PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
  GCP_SA_KEY: ${{ secrets.GCP_SA_KEY }}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Build and Push ML Service
        run: |
          docker build -t gcr.io/$PROJECT_ID/ml-service ./services/ml-service
          docker push gcr.io/$PROJECT_ID/ml-service
      
      - name: Deploy ML Service
        run: |
          gcloud run deploy ml-service \
            --image gcr.io/$PROJECT_ID/ml-service \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated \
            --set-env-vars DATABASE_URL=${{ secrets.DATABASE_URL }}
```

### Step 4.3: Configure Secrets (1 hour)

```bash
# Store secrets in Secret Manager
gcloud secrets create database-url --data-file=- <<< "$DATABASE_URL"
gcloud secrets create redis-url --data-file=- <<< "$REDIS_URL"
gcloud secrets create gemini-api-key --data-file=- <<< "$GEMINI_API_KEY"

# Grant access to Cloud Run service account
gcloud secrets add-iam-policy-binding database-url \
  --member="serviceAccount:ml-service-sa@[PROJECT].iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Step 4.4: Deploy All Services (1 hour)

```bash
# Deploy each service
./deploy-cloud-run.sh ml-service
./deploy-cloud-run.sh gateway-api
./deploy-cloud-run.sh titan-core
./deploy-cloud-run.sh video-agent
```

---

## 🎯 PHASE 5: MONITORING (Week 4) - 7 hours

### Step 5.1: Prometheus & Grafana (4 hours)

**Deploy Prometheus:**
```yaml
# prometheus/prometheus.yml

global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ml-service'
    static_configs:
      - targets: ['ml-service:8003']
  - job_name: 'gateway-api'
    static_configs:
      - targets: ['gateway-api:8080']
```

**Add Metrics:**
```python
# services/ml-service/src/main.py

from prometheus_client import Counter, Histogram, Gauge

prediction_requests = Counter('prediction_requests_total', 'Total predictions')
prediction_duration = Histogram('prediction_duration_seconds', 'Prediction time')
active_samplers = Gauge('active_samplers', 'Active BattleHardenedSampler instances')

@app.post("/api/ml/predict/ctr")
async def predict_ctr(...):
    with prediction_duration.time():
        prediction_requests.inc()
        # ... prediction logic ...
```

### Step 5.2: Error Tracking (3 hours)

**Setup Sentry:**
```python
# services/ml-service/src/main.py

import sentry_sdk
sentry_sdk.init(
    dsn="[SENTRY_DSN]",
    traces_sample_rate=0.1,
    environment="production"
)
```

---

## 📋 COMPLETE CHECKLIST

### Week 1: Critical Wiring (13h)
- [ ] Wire RAG to Creative Generation (4h)
- [ ] Wire HubSpot to Celery (3h)
- [ ] Wire Pre-Spend Prediction (3h)
- [ ] Wire Fatigue Monitoring (3h)

### Week 2: Frontend (11h)
- [ ] Budget Optimizer UI (4h)
- [ ] Winner Search UI (3h)
- [ ] Learning Dashboard (2h)
- [ ] Pipeline Value Dashboard (2h)

### Week 3: Infrastructure (13h)
- [ ] Supabase Setup (4h)
- [ ] Cloud Run Deployment (6h)
- [ ] Redis & Celery (3h)

### Week 4: Monitoring (7h)
- [ ] Prometheus & Grafana (4h)
- [ ] Error Tracking (3h)

### Week 5: Testing (12h)
- [ ] E2E Tests (8h)
- [ ] Load Tests (4h)

### Week 6: Security (6h)
- [ ] Security Hardening (4h)
- [ ] Secrets Management (2h)

**Total: 62 hours over 6 weeks**

---

## 🚀 THIS WEEK (Quick Start)

### Today (4 hours)
1. Wire RAG to Director Agent (2h)
2. Auto-index winners (1h)
3. Test integration (1h)

### Tomorrow (3 hours)
1. Create Celery task (1h)
2. Modify webhook (1h)
3. Test async (1h)

**Week 1 Goal: Core intelligence fully wired**

---

**This extended roadmap covers every detail from wiring to deployment.**

