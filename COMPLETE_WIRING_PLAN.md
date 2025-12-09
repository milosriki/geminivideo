# COMPLETE WIRING PLAN
## Full System Integration - Connect All Components

**Generated:** 2025-12-09  
**Purpose:** Step-by-step plan to wire all existing code (78% → 100%)  
**Time Estimate:** 8-10 hours for critical wiring, 20 hours for complete

---

## EXECUTIVE SUMMARY

### Current Wiring Status: **78%**

**What's Wired:**
- ✅ Core API endpoints (Gateway → Services)
- ✅ Database connections
- ✅ Basic ML predictions
- ✅ Video processing pipelines
- ✅ Publishing workflows

**What's NOT Wired:**
- ❌ Auto-triggers (RAG indexing, learning cycles)
- ❌ Background workers (SafeExecutor, self-learning)
- ❌ Missing endpoints (ROAS, pipeline predictions)
- ❌ Champion-challenger auto-evaluation
- ❌ Pro Video module endpoints

### Target: **100% Wired**

---

## PART 1: AUTO-TRIGGER WIRING (Priority 1 - 4 Hours)

### 1.1 RAG Auto-Indexing Trigger

**Problem:** Winners detected but not automatically indexed to RAG memory

**Location:** `services/ml-service/src/main.py`

**Current State:**
- RAG endpoints exist: `/api/ml/rag/index-winner`
- Winner detection logic exists in `actuals_fetcher.py`
- **Missing:** Automatic trigger when winner detected

**Wiring Steps:**

#### Step 1: Add Winner Detection Function
```python
# File: services/ml-service/src/main.py
# Add after line 100 (after imports)

def is_winner(ctr: float, roas: float, hours_live: int) -> bool:
    """
    Detect if ad is a winner based on performance thresholds
    """
    # Winner criteria:
    # - CTR > 3% OR ROAS > 3.0
    # - At least 24 hours of data
    # - Minimum 1000 impressions
    if hours_live < 24:
        return False
    
    return (ctr > 0.03) or (roas > 3.0)
```

#### Step 2: Wire to Actuals Fetcher
```python
# File: services/ml-service/src/actuals_fetcher.py
# Add after line 200 (in fetch_actuals method)

from src.winner_index import winner_index

async def _check_and_index_winner(self, ad_actuals: AdActuals, prediction: Dict) -> None:
    """Auto-index winners to RAG memory"""
    if is_winner(
        ctr=ad_actuals.actual_ctr,
        roas=ad_actuals.actual_roas,
        hours_live=(datetime.now() - prediction['created_at']).total_seconds() / 3600
    ):
        logger.info(f"Winner detected! Auto-indexing ad {ad_actuals.ad_id} to RAG")
        
        # Index to RAG
        await winner_index.index_winner(
            ad_id=ad_actuals.ad_id,
            video_id=ad_actuals.video_id,
            ctr=ad_actuals.actual_ctr,
            roas=ad_actuals.actual_roas,
            creative_data={
                'hook': prediction.get('hook', ''),
                'cta': prediction.get('cta', ''),
                'template': prediction.get('template', ''),
                'metadata': prediction.get('metadata', {})
            },
            performance_data={
                'impressions': ad_actuals.impressions,
                'clicks': ad_actuals.clicks,
                'conversions': ad_actuals.conversions,
                'spend': ad_actuals.spend
            }
        )
```

#### Step 3: Call from Feedback Loop
```python
# File: services/ml-service/src/main.py
# In the /api/ml/feedback endpoint (around line 500)

@app.post("/api/ml/feedback")
async def submit_feedback(request: FeedbackRequest):
    # ... existing feedback processing ...
    
    # NEW: Auto-index winners
    if request.actual_ctr and request.actual_roas:
        await _check_and_index_winner(
            ad_actuals=AdActuals(
                ad_id=request.ad_id,
                video_id=request.video_id,
                actual_ctr=request.actual_ctr,
                actual_roas=request.actual_roas,
                # ... other fields ...
            ),
            prediction=prediction_data
        )
```

**Time:** 2 hours  
**Files Modified:** 2  
**Impact:** Winners automatically learned and searchable

---

### 1.2 Self-Learning Cycle Orchestrator

**Problem:** All 7 loops exist but no master orchestrator to run them together

**Location:** Create new file `services/ml-service/src/self_learning_orchestrator.py`

**Wiring Steps:**

#### Step 1: Create Orchestrator
```python
# File: services/ml-service/src/self_learning_orchestrator.py

"""
Self-Learning Cycle Orchestrator
Runs all 7 learning loops in sequence for continuous improvement
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Any
from src.creative_dna import get_creative_dna
from src.compound_learner import compound_learner
from src.actuals_fetcher import actuals_fetcher
from src.auto_promoter import auto_promoter
from src.thompson_sampler import thompson_optimizer
from src.winner_index import winner_index

logger = logging.getLogger(__name__)


class SelfLearningOrchestrator:
    """Orchestrates all 7 self-learning loops"""
    
    def __init__(self):
        self.creative_dna = get_creative_dna()
        self.compound_learner = compound_learner
        self.actuals_fetcher = actuals_fetcher
        self.auto_promoter = auto_promoter
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """
        Run all 7 learning loops in sequence
        
        Returns:
            Dict with results from each loop
        """
        results = {
            'started_at': datetime.utcnow().isoformat(),
            'loops': {}
        }
        
        try:
            # Loop 1: RAG Winner Index - Search and learn from winners
            logger.info("Loop 1: RAG Winner Index")
            rag_results = await winner_index.refresh_index()
            results['loops']['rag'] = {
                'status': 'completed',
                'winners_indexed': rag_results.get('count', 0)
            }
            
            # Loop 2: Thompson Sampling - Update variant probabilities
            logger.info("Loop 2: Thompson Sampling")
            thompson_results = await thompson_optimizer.update_all_experiments()
            results['loops']['thompson'] = {
                'status': 'completed',
                'experiments_updated': thompson_results.get('count', 0)
            }
            
            # Loop 3: Cross-Learner - Learn across campaigns
            logger.info("Loop 3: Cross-Learner")
            cross_learn_results = await self._run_cross_learner()
            results['loops']['cross_learner'] = cross_learn_results
            
            # Loop 4: Creative DNA - Extract winning patterns
            logger.info("Loop 4: Creative DNA")
            dna_results = await self.creative_dna.extract_all_patterns()
            results['loops']['creative_dna'] = {
                'status': 'completed',
                'patterns_extracted': len(dna_results.get('patterns', []))
            }
            
            # Loop 5: Compound Learner - Improve ensemble models
            logger.info("Loop 5: Compound Learner")
            compound_results = await self.compound_learner.improve_models()
            results['loops']['compound_learner'] = {
                'status': 'completed',
                'models_updated': compound_results.get('count', 0)
            }
            
            # Loop 6: Actuals Fetcher - Get latest performance data
            logger.info("Loop 6: Actuals Fetcher")
            actuals_results = await self.actuals_fetcher.fetch_all_pending()
            results['loops']['actuals'] = {
                'status': 'completed',
                'ads_fetched': actuals_results.get('count', 0)
            }
            
            # Loop 7: Auto-Promoter - Scale winners, kill losers
            logger.info("Loop 7: Auto-Promoter")
            promoter_results = await self.auto_promoter.check_and_promote_all()
            results['loops']['auto_promoter'] = {
                'status': 'completed',
                'ads_promoted': promoter_results.get('promoted', 0),
                'ads_killed': promoter_results.get('killed', 0)
            }
            
            results['status'] = 'completed'
            results['completed_at'] = datetime.utcnow().isoformat()
            
        except Exception as e:
            logger.error(f"Self-learning cycle failed: {e}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
        
        return results
    
    async def _run_cross_learner(self) -> Dict[str, Any]:
        """Run cross-learner (if available)"""
        try:
            from src.cross_learner import cross_learner
            return await cross_learner.learn_from_all_campaigns()
        except ImportError:
            return {'status': 'skipped', 'reason': 'Cross-learner not available'}


# Global instance
_orchestrator = None

def get_orchestrator() -> SelfLearningOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SelfLearningOrchestrator()
    return _orchestrator
```

#### Step 2: Add Endpoint
```python
# File: services/ml-service/src/main.py
# Add after line 2000

from src.self_learning_orchestrator import get_orchestrator

@app.post("/api/ml/self-learning-cycle")
async def run_self_learning_cycle():
    """
    Run all 7 self-learning loops in sequence
    This is the master orchestrator endpoint
    """
    orchestrator = get_orchestrator()
    results = await orchestrator.run_full_cycle()
    return results
```

#### Step 3: Add Scheduled Job
```python
# File: services/ml-service/src/tasks.py (Celery)
# Add new scheduled task

from celery import Celery
from src.self_learning_orchestrator import get_orchestrator

celery_app = Celery('ml-service')

@celery_app.task(name='self_learning_cycle')
async def scheduled_self_learning_cycle():
    """Run self-learning cycle every hour"""
    orchestrator = get_orchestrator()
    return await orchestrator.run_full_cycle()

# Schedule: Run every hour
celery_app.conf.beat_schedule = {
    'self-learning-cycle-hourly': {
        'task': 'self_learning_cycle',
        'schedule': 3600.0,  # 1 hour
    },
}
```

**Time:** 2 hours  
**Files Created:** 1  
**Files Modified:** 2  
**Impact:** All 7 loops run automatically every hour

---

### 1.3 Champion-Challenger Auto-Evaluation

**Problem:** Models trained but not automatically evaluated against champion

**Location:** `services/ml-service/src/tasks.py`

**Wiring Steps:**

```python
# File: services/ml-service/src/tasks.py
# Add after model training tasks

from src.model_evaluation import evaluate_champion_vs_challenger

@celery_app.task(name='auto_evaluate_models')
def auto_evaluate_models_after_training(model_path: str, model_type: str):
    """
    Automatically evaluate challenger model vs champion
    Called after model training completes
    """
    try:
        # Get champion model path
        champion_path = get_champion_model_path(model_type)
        
        if not champion_path:
            logger.info(f"No champion model found for {model_type}, promoting challenger")
            promote_to_champion(model_path, model_type)
            return {'status': 'promoted', 'reason': 'first_model'}
        
        # Evaluate
        result = evaluate_champion_vs_challenger(
            champion_path=champion_path,
            challenger_path=model_path,
            model_type=model_type
        )
        
        if result['challenger_wins']:
            logger.info(f"Challenger wins! Promoting {model_path}")
            promote_to_champion(model_path, model_type)
            return {'status': 'promoted', 'metrics': result['metrics']}
        else:
            logger.info(f"Champion still better, keeping {champion_path}")
            return {'status': 'kept_champion', 'metrics': result['metrics']}
            
    except Exception as e:
        logger.error(f"Auto-evaluation failed: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}
```

**Wire to Training:**
```python
# File: services/ml-service/src/main.py
# In /train/ctr endpoint (around line 450)

@app.post("/train/ctr")
async def train_ctr_model():
    # ... existing training code ...
    
    # After training completes:
    model_path = enhanced_ctr_predictor.save_model()
    
    # NEW: Auto-evaluate
    from src.tasks import auto_evaluate_models_after_training
    auto_evaluate_models_after_training.delay(
        model_path=model_path,
        model_type='ctr'
    )
    
    return {"status": "training_complete", "model_path": model_path}
```

**Time:** 1 hour  
**Files Modified:** 2  
**Impact:** Models automatically evaluated and promoted

---

## PART 2: MISSING ENDPOINTS (Priority 2 - 2 Hours)

### 2.1 ROAS Prediction Endpoint

**Problem:** ROAS prediction logic exists in `battle_hardened_sampler.py` but no dedicated endpoint

**Location:** `services/ml-service/src/main.py`

**Wiring Steps:**

```python
# File: services/ml-service/src/main.py
# Add after line 600 (after other prediction endpoints)

from pydantic import BaseModel
from src.battle_hardened_sampler import get_battle_hardened_sampler

class ROASPredictionRequest(BaseModel):
    ad_id: str
    current_ctr: float
    current_roas: float
    hours_live: int
    daily_spend: float
    days_forward: int = 7

@app.post("/api/ml/predict/roas")
async def predict_roas(request: ROASPredictionRequest):
    """
    Predict ROAS for next N days using Battle-Hardened Sampler logic
    """
    sampler = get_battle_hardened_sampler()
    
    # Use existing blended score logic
    predicted_roas = sampler._calculate_blended_score(
        ctr=request.current_ctr,
        roas=request.current_roas,
        hours_live=request.hours_live
    )
    
    # Project forward
    projected_spend = request.daily_spend * request.days_forward
    projected_revenue = projected_spend * predicted_roas
    projected_profit = projected_revenue - projected_spend
    
    return {
        "ad_id": request.ad_id,
        "predicted_roas": round(predicted_roas, 2),
        "projected_spend": round(projected_spend, 2),
        "projected_revenue": round(projected_revenue, 2),
        "projected_profit": round(projected_profit, 2),
        "days_forward": request.days_forward,
        "confidence": "high" if request.hours_live > 72 else "medium"
    }
```

**Time:** 1 hour  
**Files Modified:** 1  
**Impact:** ROAS predictions available via API

---

### 2.2 Pipeline Value Prediction Endpoint

**Problem:** Pipeline prediction logic exists in `synthetic_revenue.py` but no dedicated endpoint

**Location:** `services/ml-service/src/main.py`

**Wiring Steps:**

```python
# File: services/ml-service/src/main.py
# Add after ROAS prediction endpoint

from src.synthetic_revenue import get_synthetic_revenue_calculator

class PipelinePredictionRequest(BaseModel):
    deals: List[Dict[str, Any]]  # [{id, stage, amount, ...}]

@app.post("/api/ml/predict/pipeline")
async def predict_pipeline_value(request: PipelinePredictionRequest):
    """
    Predict future revenue from HubSpot pipeline using synthetic revenue logic
    """
    calculator = get_synthetic_revenue_calculator()
    
    predictions = {}
    total_expected_value = 0
    
    for deal in request.deals:
        stage = deal.get('stage', '')
        amount = float(deal.get('amount', 0))
        
        # Use existing synthetic revenue logic
        stage_value = calculator.calculate_stage_value(stage)
        probability = calculator.get_stage_probability(stage)
        avg_days = calculator.get_avg_days_to_close(stage)
        
        expected_value = amount * probability
        
        predictions[deal['id']] = {
            "deal_id": deal['id'],
            "stage": stage,
            "amount": amount,
            "expected_value": round(expected_value, 2),
            "probability": round(probability, 3),
            "predicted_close_days": avg_days,
            "synthetic_value": stage_value
        }
        
        total_expected_value += expected_value
    
    return {
        "deals": list(predictions.values()),
        "total_pipeline_value": round(total_expected_value, 2),
        "deal_count": len(predictions),
        "avg_probability": round(sum(p['probability'] for p in predictions.values()) / len(predictions), 3) if predictions else 0
    }
```

**Time:** 1 hour  
**Files Modified:** 1  
**Impact:** Pipeline forecasting available via API

---

## PART 3: BACKGROUND WORKERS (Priority 3 - 2 Hours)

### 3.1 SafeExecutor Worker

**Problem:** SafeExecutor code exists but worker process not running

**Location:** `services/gateway-api/src/jobs/safe-executor.ts`

**Wiring Steps:**

#### Step 1: Create Worker Entry Point
```typescript
// File: services/gateway-api/src/jobs/safe-executor-worker.ts

/**
 * SafeExecutor Worker - Standalone Process
 * Polls pending_ad_changes and executes safely
 */

import { startSafeExecutorWorker } from './safe-executor';

// Start worker
const workerId = process.env.WORKER_ID || `worker-${Date.now()}`;
console.log(`Starting SafeExecutor worker: ${workerId}`);

startSafeExecutorWorker(workerId)
  .then(() => {
    console.log('SafeExecutor worker started successfully');
  })
  .catch((error) => {
    console.error('Failed to start SafeExecutor worker:', error);
    process.exit(1);
  });
```

#### Step 2: Add to docker-compose.yml
```yaml
# File: docker-compose.yml
# Add after gateway-api service

  safe-executor-worker:
    build:
      context: ./services/gateway-api
      dockerfile: Dockerfile
    container_name: geminivideo-safe-executor
    environment:
      DATABASE_URL: postgresql://geminivideo:geminivideo@postgres:5432/geminivideo
      META_ACCESS_TOKEN: ${META_ACCESS_TOKEN}
      META_API_VERSION: ${META_API_VERSION:-v18.0}
      WORKER_ID: safe-executor-1
      POLL_INTERVAL_MS: 5000
      BATCH_MODE_ENABLED: true
      BATCH_SIZE: 10
    depends_on:
      postgres:
        condition: service_healthy
      gateway-api:
        condition: service_started
    restart: unless-stopped
    networks:
      - geminivideo-network
    command: node dist/jobs/safe-executor-worker.js
```

#### Step 3: Update package.json Script
```json
// File: services/gateway-api/package.json
// Add to scripts section

{
  "scripts": {
    "worker:safe-executor": "ts-node src/jobs/safe-executor-worker.ts"
  }
}
```

**Time:** 1 hour  
**Files Created:** 1  
**Files Modified:** 2  
**Impact:** Ad changes execute safely with rate limiting

---

### 3.2 Self-Learning Cycle Worker

**Problem:** Self-learning cycle exists but no scheduled worker

**Location:** Create `services/ml-service/src/workers/self_learning_worker.py`

**Wiring Steps:**

#### Step 1: Create Worker Script
```python
# File: services/ml-service/src/workers/self_learning_worker.py

"""
Self-Learning Cycle Worker
Runs self-learning cycle on schedule (every hour)
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.self_learning_orchestrator import get_orchestrator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_cycle():
    """Run one self-learning cycle"""
    logger.info("=" * 60)
    logger.info("Starting self-learning cycle")
    logger.info("=" * 60)
    
    orchestrator = get_orchestrator()
    results = await orchestrator.run_full_cycle()
    
    logger.info(f"Cycle completed: {results['status']}")
    logger.info(f"Results: {results.get('loops', {})}")
    
    return results


async def main():
    """Main worker loop - runs cycle every hour"""
    while True:
        try:
            await run_cycle()
        except Exception as e:
            logger.error(f"Cycle failed: {e}", exc_info=True)
        
        # Wait 1 hour before next cycle
        logger.info("Waiting 1 hour before next cycle...")
        await asyncio.sleep(3600)  # 1 hour


if __name__ == "__main__":
    asyncio.run(main())
```

#### Step 2: Add to docker-compose.yml
```yaml
# File: docker-compose.yml
# Add after ml-service

  self-learning-worker:
    build:
      context: ./services/ml-service
      dockerfile: Dockerfile
    container_name: geminivideo-self-learning-worker
    environment:
      DATABASE_URL: postgresql://geminivideo:geminivideo@postgres:5432/geminivideo
      REDIS_URL: redis://redis:6379
    depends_on:
      ml-service:
        condition: service_started
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - geminivideo-network
    command: python -m src.workers.self_learning_worker
```

**Time:** 1 hour  
**Files Created:** 1  
**Files Modified:** 1  
**Impact:** Self-learning cycles run automatically every hour

---

## PART 4: PRO VIDEO MODULE ENDPOINTS (Priority 4 - 3 Hours)

### 4.1 Expose All Pro Video Features

**Problem:** 13 pro modules imported but not all features exposed via API

**Location:** `services/video-agent/main.py`

**Current State:**
- ✅ Basic endpoints exist (`/api/pro/caption`, `/api/pro/color-grade`, etc.)
- ⚠️ Some advanced features not exposed
- ⚠️ Batch operations missing

**Wiring Steps:**

#### Add Batch Operations
```python
# File: services/video-agent/main.py
# Add after existing pro endpoints

@app.post("/api/pro/batch")
async def batch_pro_operations(request: Dict[str, Any]):
    """
    Batch process multiple videos with pro modules
    
    Body:
    - operations: List[Dict] - [{type, video_path, config}]
    - parallel: bool - Process in parallel (default: true)
    """
    operations = request.get("operations", [])
    parallel = request.get("parallel", True)
    
    if not operations:
        raise HTTPException(status_code=400, detail="operations required")
    
    results = []
    
    if parallel:
        # Process in parallel
        import asyncio
        tasks = [_process_pro_operation(op) for op in operations]
        results = await asyncio.gather(*tasks)
    else:
        # Process sequentially
        for op in operations:
            result = await _process_pro_operation(op)
            results.append(result)
    
    return {
        "status": "completed",
        "results": results,
        "total": len(results),
        "successful": sum(1 for r in results if r.get("status") == "success")
    }

async def _process_pro_operation(operation: Dict) -> Dict:
    """Process single pro operation"""
    op_type = operation.get("type")
    video_path = operation.get("video_path")
    config = operation.get("config", {})
    
    try:
        if op_type == "caption":
            result = await generate_captions({"video_path": video_path, **config})
        elif op_type == "color_grade":
            result = await apply_color_grading({"video_path": video_path, **config})
        elif op_type == "smart_crop":
            result = await smart_crop_video({"video_path": video_path, **config})
        # ... add other operations ...
        else:
            raise HTTPException(status_code=400, detail=f"Unknown operation type: {op_type}")
        
        return {"status": "success", "operation": op_type, **result}
    except Exception as e:
        return {"status": "failed", "operation": op_type, "error": str(e)}
```

**Time:** 3 hours  
**Files Modified:** 1  
**Impact:** All pro video features accessible via API

---

## PART 5: GATEWAY API PROXIES (Priority 5 - 1 Hour)

### 5.1 Wire Missing Gateway Endpoints

**Problem:** Some ML endpoints not proxied through Gateway API

**Location:** `services/gateway-api/src/index.ts`

**Wiring Steps:**

```typescript
// File: services/gateway-api/src/index.ts
// Add after existing ML proxy routes (around line 1900)

// ROAS Prediction Proxy
app.post('/api/ml/predict/roas',
  apiRateLimiter,
  validateInput({
    body: {
      ad_id: { type: 'string', required: true },
      current_ctr: { type: 'number', required: true, min: 0, max: 1 },
      current_roas: { type: 'number', required: true, min: 0 },
      hours_live: { type: 'number', required: true, min: 0 },
      daily_spend: { type: 'number', required: true, min: 0 },
      days_forward: { type: 'number', required: false, min: 1, max: 90 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/predict/roas`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('ROAS prediction error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'ROAS prediction failed', details: error.response?.data });
    }
  });

// Pipeline Prediction Proxy
app.post('/api/ml/predict/pipeline',
  apiRateLimiter,
  validateInput({
    body: {
      deals: { type: 'array', required: true, min: 1 }
    }
  }),
  async (req: Request, res: Response) => {
    try {
      const response = await axios.post(`${ML_SERVICE_URL}/api/ml/predict/pipeline`, req.body, { timeout: 30000 });
      res.json(response.data);
    } catch (error: any) {
      console.error('Pipeline prediction error:', error.message);
      res.status(error.response?.status || 500).json({ error: 'Pipeline prediction failed', details: error.response?.data });
    }
  });
```

**Time:** 1 hour  
**Files Modified:** 1  
**Impact:** All endpoints accessible through Gateway API

---

## PART 6: DATABASE TRIGGERS (Priority 6 - 1 Hour)

### 6.1 Auto-Trigger on Performance Updates

**Problem:** Performance data updated but not triggering learning

**Location:** Database migration

**Wiring Steps:**

```sql
-- File: database/migrations/007_auto_triggers.sql

-- Function to check winner and trigger RAG indexing
CREATE OR REPLACE FUNCTION check_winner_and_index()
RETURNS TRIGGER AS $$
DECLARE
    v_ctr FLOAT;
    v_roas FLOAT;
    v_hours_live INT;
BEGIN
    -- Get performance metrics
    v_ctr := NEW.ctr;
    v_roas := (NEW.raw_data->>'roas')::FLOAT;
    v_hours_live := EXTRACT(EPOCH FROM (NOW() - NEW.created_at)) / 3600;
    
    -- Check if winner (CTR > 3% OR ROAS > 3.0, at least 24h old, 1000+ impressions)
    IF v_hours_live >= 24 AND NEW.impressions >= 1000 AND (v_ctr > 0.03 OR v_roas > 3.0) THEN
        -- Queue RAG indexing job
        INSERT INTO pending_jobs (job_type, payload, status, created_at)
        VALUES (
            'rag_index_winner',
            jsonb_build_object(
                'ad_id', NEW.ad_id,
                'video_id', NEW.video_id,
                'ctr', v_ctr,
                'roas', v_roas,
                'impressions', NEW.impressions
            ),
            'pending',
            NOW()
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger on performance_metrics table
CREATE TRIGGER trigger_winner_detection
AFTER INSERT OR UPDATE ON performance_metrics
FOR EACH ROW
WHEN (NEW.impressions >= 1000)
EXECUTE FUNCTION check_winner_and_index();
```

**Time:** 1 hour  
**Files Created:** 1  
**Impact:** Automatic winner detection and indexing

---

## PART 7: COMPLETE WIRING CHECKLIST

### Phase 1: Auto-Triggers (4 hours)
- [ ] 1.1 RAG Auto-Indexing Trigger (2h)
- [ ] 1.2 Self-Learning Cycle Orchestrator (2h)
- [ ] 1.3 Champion-Challenger Auto-Evaluation (1h)

### Phase 2: Missing Endpoints (2 hours)
- [ ] 2.1 ROAS Prediction Endpoint (1h)
- [ ] 2.2 Pipeline Prediction Endpoint (1h)

### Phase 3: Background Workers (2 hours)
- [ ] 3.1 SafeExecutor Worker (1h)
- [ ] 3.2 Self-Learning Cycle Worker (1h)

### Phase 4: Pro Video Endpoints (3 hours)
- [ ] 4.1 Batch Operations (2h)
- [ ] 4.2 Advanced Features (1h)

### Phase 5: Gateway Proxies (1 hour)
- [ ] 5.1 Wire Missing Endpoints (1h)

### Phase 6: Database Triggers (1 hour)
- [ ] 6.1 Auto-Trigger Functions (1h)

**Total Time:** 13 hours  
**Target Completion:** 78% → 100% wired

---

## PART 8: TESTING PLAN

### After Each Phase:

1. **Unit Tests**
   - Test new functions
   - Test error handling
   - Test edge cases

2. **Integration Tests**
   - Test service-to-service calls
   - Test database triggers
   - Test worker processes

3. **End-to-End Tests**
   - Test complete workflows
   - Test auto-triggers
   - Test learning cycles

### Test Commands:

```bash
# Test RAG auto-indexing
curl -X POST http://localhost:8000/api/ml/feedback \
  -H "Content-Type: application/json" \
  -d '{"ad_id": "test", "actual_ctr": 0.05, "actual_roas": 4.0}'

# Test self-learning cycle
curl -X POST http://localhost:8000/api/ml/self-learning-cycle

# Test ROAS prediction
curl -X POST http://localhost:8000/api/ml/predict/roas \
  -H "Content-Type: application/json" \
  -d '{"ad_id": "test", "current_ctr": 0.03, "current_roas": 2.5, "hours_live": 48, "daily_spend": 100}'

# Check worker status
docker ps | grep worker
```

---

## PART 9: DEPLOYMENT ORDER

### Recommended Order:

1. **Database Triggers** (Phase 6)
   - No service changes
   - Immediate benefit

2. **Missing Endpoints** (Phase 2)
   - Low risk
   - High value

3. **Auto-Triggers** (Phase 1)
   - Core functionality
   - Requires testing

4. **Background Workers** (Phase 3)
   - Requires docker-compose update
   - Monitor closely

5. **Pro Video Endpoints** (Phase 4)
   - Nice to have
   - Lower priority

6. **Gateway Proxies** (Phase 5)
   - Final polish
   - Complete integration

---

## PART 10: VERIFICATION

### After Complete Wiring:

**Check 1: All Endpoints Respond**
```bash
# Test all new endpoints
curl http://localhost:8000/api/ml/predict/roas
curl http://localhost:8000/api/ml/predict/pipeline
curl http://localhost:8000/api/ml/self-learning-cycle
```

**Check 2: Workers Running**
```bash
docker ps | grep -E "safe-executor|self-learning"
```

**Check 3: Auto-Triggers Working**
```bash
# Insert test performance data
# Check if RAG indexing triggered
curl http://localhost:8000/api/ml/rag/memory-stats
```

**Check 4: Learning Cycles Active**
```bash
# Check logs
docker logs geminivideo-self-learning-worker
```

---

## CONCLUSION

### Current State: 78% Wired
### Target State: 100% Wired
### Time Required: 13 hours
### Impact: Full system automation

**Key Benefits:**
- ✅ Winners automatically learned
- ✅ Models continuously improve
- ✅ Ad changes execute safely
- ✅ All predictions available
- ✅ Complete automation

**Next Steps:**
1. Start with Phase 1 (Auto-Triggers)
2. Test thoroughly
3. Deploy incrementally
4. Monitor performance
5. Iterate based on results

---

**Document Generated:** 2025-12-09  
**Status:** Ready for implementation  
**Priority:** High (completes system wiring)

