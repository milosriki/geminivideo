# 🚀 10-AGENT MAXIMUM IMPACT DEPLOYMENT PLAN

**Goal:** Wire 60 existing agents, fill 3 gaps, unlock 100% of platform
**Time:** 6-8 hours with parallel execution
**Impact:** Transform 59% accessible → 100% production-ready

---

## 📊 EXECUTION OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    10-AGENT PARALLEL EXECUTION MAP                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  HOUR 0-2: FOUNDATION WAVE (4 agents parallel)                              │
│  ├── Agent 1: Error Fixer ──────────────────────────────────────→ DONE      │
│  ├── Agent 2: Router Wirer ─────────────────────────────────────→ DONE      │
│  ├── Agent 3: Worker Activator ─────────────────────────────────→ DONE      │
│  └── Agent 4: Semantic Cache Wirer ─────────────────────────────→ DONE      │
│                                                                              │
│  HOUR 2-4: INTEGRATION WAVE (3 agents parallel)                             │
│  ├── Agent 5: Cross-Learner Connector ──────────────────────────→ DONE      │
│  ├── Agent 6: Precomputer Activator ────────────────────────────→ DONE      │
│  └── Agent 7: LangGraph-Titan Bridge ───────────────────────────→ DONE      │
│                                                                              │
│  HOUR 4-6: GAP FILLER WAVE (3 agents parallel)                              │
│  ├── Agent 8: Day-Part Optimizer (NEW) ─────────────────────────→ DONE      │
│  ├── Agent 9: Circuit Breaker (NEW) ────────────────────────────→ DONE      │
│  └── Agent 10: Drift Detector (NEW) ────────────────────────────→ DONE      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 AGENT 1: THE ERROR FIXER

### Mission
Fix all 50 critical errors blocking deployment

### Files to MODIFY (not create)
```
/services/gateway-api/package.json          # Add @types/*
/services/gateway-api/src/services/*.ts     # Fix imports
/services/ml-service/src/main.py            # Fix asyncio import
/services/ml-service/src/batch_api.py       # Add logger
/frontend/.env                              # Fix VITE_API_URL
```

### Specific Tasks
```python
# Task 1: Fix TypeScript types (gateway-api/package.json)
ADD to devDependencies:
  "@types/node": "^20.0.0",
  "@types/express": "^4.17.0",
  "@types/axios": "^1.0.0",
  "@types/pg": "^8.0.0"

# Task 2: Fix Python imports (ml-service/src/main.py)
LINE 4: Add "import asyncio"
LINE 339: Fix "generate_synthetic_training_data" import

# Task 3: Fix batch_api.py
ADD at top: "import logging; logger = logging.getLogger(__name__)"

# Task 4: Fix frontend .env
CHANGE: VITE_API_BASE_URL → VITE_API_URL
```

### Success Criteria
- [ ] `npm run build` passes in gateway-api
- [ ] `python -m py_compile main.py` passes
- [ ] Frontend builds without errors

### Dependencies
None - can start immediately

### Time: 1 hour

---

## 🔧 AGENT 2: THE ROUTER WIRER

### Mission
Expose 32 hidden React components via proper routing

### Files to CREATE
```
/frontend/src/router/
├── index.tsx           # Main router setup
├── routes.ts           # Route definitions
├── guards.tsx          # Auth guards
└── layouts/
    ├── DashboardLayout.tsx
    └── AuthLayout.tsx
```

### Files to MODIFY
```
/frontend/src/App.tsx                    # Replace tabs with Router
/frontend/src/main.tsx                   # Add BrowserRouter
```

### Implementation
```typescript
// /frontend/src/router/routes.ts
export const routes = [
  // PUBLIC
  { path: '/login', component: LoginPage },
  { path: '/signup', component: SignupPage },

  // DASHBOARD (Protected)
  { path: '/', component: DashboardHome },
  { path: '/campaigns', component: CampaignBuilder },
  { path: '/campaigns/:id', component: CampaignDetail },
  { path: '/analytics', component: AnalyticsDashboard },
  { path: '/creative-studio', component: AICreativeStudio },
  { path: '/video-editor', component: ProVideoEditor },
  { path: '/assets', component: AssetLibrary },
  { path: '/settings', component: Settings },

  // AI TOOLS
  { path: '/ai/scoring', component: AIScoring },
  { path: '/ai/hooks', component: HookGenerator },
  { path: '/ai/analysis', component: VideoAnalysis },

  // ADMIN
  { path: '/admin/users', component: UserManagement },
  { path: '/admin/billing', component: BillingDashboard },
];

// /frontend/src/router/index.tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { routes } from './routes';

export const router = createBrowserRouter(
  routes.map(r => ({
    path: r.path,
    element: <ProtectedRoute><r.component /></ProtectedRoute>
  }))
);

export function AppRouter() {
  return <RouterProvider router={router} />;
}
```

### Success Criteria
- [ ] All 32 components accessible via URL
- [ ] Deep linking works (share URLs)
- [ ] Back/forward navigation works
- [ ] Auth guards protect private routes

### Dependencies
Agent 1 (errors fixed first)

### Time: 2 hours

---

## 🔧 AGENT 3: THE WORKER ACTIVATOR

### Mission
Start all background workers that exist but aren't running

### Files to CREATE
```
/scripts/start-workers.sh                    # Worker startup script
/docker-compose.workers.yml                  # Worker containers
/services/ml-service/src/worker_manager.py   # Worker orchestration
```

### Files to MODIFY
```
/services/ml-service/src/celery_app.py       # Ensure configured
/services/ml-service/src/celery_tasks.py     # Ensure tasks registered
```

### Implementation
```bash
#!/bin/bash
# /scripts/start-workers.sh

echo "🚀 Starting GeminiVideo Workers..."

# 1. Start Celery Worker
celery -A services.ml-service.src.celery_app worker \
  --loglevel=info \
  --concurrency=4 \
  -Q default,high_priority,low_priority &

# 2. Start Celery Beat (Scheduler)
celery -A services.ml-service.src.celery_app beat \
  --loglevel=info &

# 3. Start Learning Cycle Worker
python -m services.ml-service.src.compound_learner --daemon &

# 4. Start Auto-Scaler Worker
python -m services.ml-service.src.auto_scaler --daemon &

# 5. Start Fatigue Monitor
python -m services.ml-service.src.fatigue_monitor --daemon &

echo "✅ All workers started!"
```

```yaml
# /docker-compose.workers.yml
version: '3.8'
services:
  celery-worker:
    build: ./services/ml-service
    command: celery -A src.celery_app worker -l info
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - redis
      - postgres

  celery-beat:
    build: ./services/ml-service
    command: celery -A src.celery_app beat -l info
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  learning-worker:
    build: ./services/ml-service
    command: python -m src.compound_learner --daemon
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - postgres
```

### Success Criteria
- [ ] Celery worker processes tasks
- [ ] Beat scheduler runs periodic tasks
- [ ] Learning cycle runs daily
- [ ] Auto-scaler runs hourly
- [ ] Fatigue monitor runs every 6 hours

### Dependencies
None - can start immediately

### Time: 1.5 hours

---

## 🔧 AGENT 4: THE SEMANTIC CACHE WIRER

### Mission
Connect built semantic cache to reduce API costs 80%

### Files to CREATE
```
/services/ml-service/src/cache/
├── __init__.py
├── semantic_cache_manager.py    # Cache orchestration
└── cache_keys.py                # Key generation
```

### Files to MODIFY
```
/services/ml-service/src/battle_hardened_sampler.py   # Add cache layer
/services/titan-core/ai_council/council_of_titans.py  # Add cache layer
/services/gateway-api/src/services/scoring-engine.ts  # Add cache layer
```

### Implementation
```python
# /services/ml-service/src/cache/semantic_cache_manager.py
import hashlib
import json
import redis
from typing import Any, Optional
import numpy as np

class SemanticCacheManager:
    """
    Semantic caching for ML predictions and AI evaluations.
    Reduces API costs by 80% through intelligent caching.
    """

    def __init__(self, redis_url: str = None):
        self.redis = redis.from_url(redis_url or os.getenv('REDIS_URL'))
        self.ttl_seconds = {
            'budget_allocation': 1800,    # 30 min
            'ctr_prediction': 3600,       # 1 hour
            'creative_score': 7200,       # 2 hours
            'council_evaluation': 86400,  # 24 hours (expensive!)
        }

    def get(self, key: str, query_type: str) -> Optional[Any]:
        """Get cached value if exists and not expired."""
        cached = self.redis.get(f"cache:{query_type}:{key}")
        if cached:
            return json.loads(cached)
        return None

    def set(self, key: str, value: Any, query_type: str, ttl: int = None):
        """Cache a value with appropriate TTL."""
        ttl = ttl or self.ttl_seconds.get(query_type, 3600)
        self.redis.setex(
            f"cache:{query_type}:{key}",
            ttl,
            json.dumps(value, default=str)
        )

    def generate_key(self, data: dict) -> str:
        """Generate deterministic cache key from input data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def get_or_compute(self, key: str, query_type: str, compute_fn):
        """Get from cache or compute and cache."""
        cached = self.get(key, query_type)
        if cached:
            return cached, True  # cache hit

        result = compute_fn()
        self.set(key, result, query_type)
        return result, False  # cache miss


# Singleton
_cache_manager = None

def get_semantic_cache() -> SemanticCacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = SemanticCacheManager()
    return _cache_manager
```

```python
# MODIFY: /services/ml-service/src/battle_hardened_sampler.py
# Add at top:
from src.cache.semantic_cache_manager import get_semantic_cache

# In select_budget_allocation method, wrap computation:
def select_budget_allocation(self, ad_states, total_budget, ...):
    cache = get_semantic_cache()
    cache_key = cache.generate_key({
        'ad_ids': [s.ad_id for s in ad_states],
        'total_budget': total_budget,
        'strategy': self.strategy
    })

    # Check cache first
    cached, hit = cache.get(cache_key, 'budget_allocation'), False
    if cached:
        logger.info(f"Cache HIT for budget allocation")
        return cached

    # Compute (existing logic)
    recommendations = self._compute_recommendations(ad_states, total_budget)

    # Cache result
    cache.set(cache_key, recommendations, 'budget_allocation')
    return recommendations
```

### Success Criteria
- [ ] Cache hit rate > 70% after warmup
- [ ] API costs reduced measurably
- [ ] Response times < 50ms for cached requests
- [ ] No stale data (proper TTLs)

### Dependencies
None - can start immediately

### Time: 1.5 hours

---

## 🔧 AGENT 5: THE CROSS-LEARNER CONNECTOR

### Mission
Activate cross-account learning for network effects (100x more data)

### Files to CREATE
```
/services/ml-service/src/learning/
├── __init__.py
├── cross_learner_scheduler.py    # Scheduling logic
├── network_boost.py              # Apply cross-account insights
└── pattern_aggregator.py         # Aggregate patterns across accounts
```

### Files to MODIFY
```
/services/ml-service/src/cross_learner.py        # Add scheduler hook
/services/ml-service/src/battle_hardened_sampler.py  # Apply boost
/services/ml-service/src/compound_learner.py     # Inject insights
```

### Implementation
```python
# /services/ml-service/src/learning/cross_learner_scheduler.py
import asyncio
from datetime import datetime, timedelta
from src.cross_learner import CrossAccountLearner
from src.compound_learner import compound_learner
import logging

logger = logging.getLogger(__name__)

class CrossLearnerScheduler:
    """
    Schedules and orchestrates cross-account learning.
    Runs daily to extract patterns that work across 3+ accounts.
    """

    def __init__(self):
        self.cross_learner = CrossAccountLearner()
        self.last_run = None
        self.run_interval = timedelta(hours=24)

    async def run_learning_cycle(self):
        """
        Daily cross-account learning cycle:
        1. Extract patterns from all accounts
        2. Find patterns working in 3+ accounts
        3. Inject into compound learner
        4. Update network boost factors
        """
        logger.info("🌐 Starting cross-account learning cycle...")

        # 1. Get all account IDs
        accounts = await self._get_active_accounts()
        logger.info(f"Found {len(accounts)} active accounts")

        # 2. Extract patterns per account
        all_patterns = []
        for account_id in accounts:
            patterns = await self.cross_learner.extract_account_patterns(account_id)
            all_patterns.extend(patterns)

        # 3. Find cross-account winners (work in 3+ accounts)
        network_patterns = self._find_network_patterns(all_patterns, min_accounts=3)
        logger.info(f"Found {len(network_patterns)} network-wide winning patterns")

        # 4. Inject into compound learner
        for pattern in network_patterns:
            await compound_learner.inject_network_pattern(pattern)

        # 5. Update boost factors
        await self._update_boost_factors(network_patterns)

        self.last_run = datetime.utcnow()
        logger.info("✅ Cross-account learning cycle complete")

        return {
            'accounts_processed': len(accounts),
            'patterns_found': len(network_patterns),
            'timestamp': self.last_run.isoformat()
        }

    def _find_network_patterns(self, patterns, min_accounts=3):
        """Find patterns that work across multiple accounts."""
        from collections import Counter

        pattern_counts = Counter()
        pattern_data = {}

        for p in patterns:
            key = f"{p['type']}:{p['name']}"
            pattern_counts[key] += 1
            if key not in pattern_data:
                pattern_data[key] = p
            else:
                # Aggregate performance
                pattern_data[key]['avg_roas'] = (
                    pattern_data[key].get('avg_roas', 0) + p.get('avg_roas', 0)
                ) / 2

        # Filter to patterns in 3+ accounts
        network_patterns = [
            pattern_data[key]
            for key, count in pattern_counts.items()
            if count >= min_accounts
        ]

        return sorted(network_patterns, key=lambda x: x.get('avg_roas', 0), reverse=True)


# Celery task
@celery_app.task
def run_cross_learning():
    scheduler = CrossLearnerScheduler()
    return asyncio.run(scheduler.run_learning_cycle())
```

### Success Criteria
- [ ] Daily learning cycle runs automatically
- [ ] Network patterns extracted from 3+ accounts
- [ ] Boost factors applied to predictions
- [ ] Measurable improvement in new account performance

### Dependencies
Agent 3 (workers running)

### Time: 1.5 hours

---

## 🔧 AGENT 6: THE PRECOMPUTER ACTIVATOR

### Mission
Activate batch prediction for zero-latency decisions

### Files to CREATE
```
/services/ml-service/src/precompute/
├── __init__.py
├── precompute_scheduler.py      # Scheduling
├── batch_predictor.py           # Batch predictions
└── prediction_store.py          # Store precomputed results
```

### Files to MODIFY
```
/services/ml-service/src/precomputer.py     # Wire to scheduler
/services/ml-service/src/main.py            # Add precompute endpoints
```

### Implementation
```python
# /services/ml-service/src/precompute/precompute_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.precomputer import Precomputer
import logging

logger = logging.getLogger(__name__)

class PrecomputeScheduler:
    """
    Schedules batch predictions for all active ads.
    Runs every 15 minutes to ensure fresh predictions.
    """

    def __init__(self):
        self.precomputer = Precomputer()
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # Run every 15 minutes
        self.scheduler.add_job(
            self.run_batch_predictions,
            'interval',
            minutes=15,
            id='precompute_predictions'
        )

        # Run immediately on startup
        self.scheduler.add_job(
            self.run_batch_predictions,
            'date',
            id='precompute_startup'
        )

        self.scheduler.start()
        logger.info("📊 Precompute scheduler started (every 15 min)")

    async def run_batch_predictions(self):
        """
        Precompute predictions for all active ads.
        Results stored in Redis for instant access.
        """
        logger.info("🔮 Running batch predictions...")

        # Get all active ads
        active_ads = await self._get_active_ads()
        logger.info(f"Precomputing for {len(active_ads)} active ads")

        # Batch predict
        results = await self.precomputer.predict_batch(active_ads)

        # Store in Redis
        await self._store_predictions(results)

        logger.info(f"✅ Precomputed {len(results)} predictions")
        return len(results)

    async def _store_predictions(self, results):
        """Store predictions in Redis for instant access."""
        import redis
        r = redis.from_url(os.getenv('REDIS_URL'))

        pipe = r.pipeline()
        for ad_id, prediction in results.items():
            pipe.setex(
                f"precomputed:ctr:{ad_id}",
                900,  # 15 min TTL
                json.dumps(prediction)
            )
        pipe.execute()
```

### Success Criteria
- [ ] Predictions precomputed every 15 minutes
- [ ] Zero-latency access to predictions
- [ ] Coverage > 95% of active ads
- [ ] Fallback to real-time if precomputed missing

### Dependencies
Agent 3 (workers running)

### Time: 1 hour

---

## 🔧 AGENT 7: THE LANGGRAPH-TITAN BRIDGE

### Mission
Create adapter to use Titan-Core as tools in LangGraph CEO Agent

### Files to CREATE
```
/services/langgraph-app/src/adapters/
├── __init__.py
├── titan_adapter.py             # Bridge to Titan-Core
├── council_tool.py              # Council as LangGraph tool
├── oracle_tool.py               # Oracle as LangGraph tool
└── director_tool.py             # Director as LangGraph tool
```

### Files to MODIFY
```
/services/langgraph-app/src/agent/tools.py    # Register new tools
/services/langgraph-app/src/agent/graph.py    # Add new nodes
```

### Implementation
```python
# /services/langgraph-app/src/adapters/titan_adapter.py
import httpx
from typing import Dict, Any
import os

TITAN_CORE_URL = os.getenv('TITAN_CORE_URL', 'http://localhost:8084')

class TitanAdapter:
    """
    Adapter to call Titan-Core services from LangGraph.
    Enables CEO Agent to use Council, Oracle, and Director.
    """

    def __init__(self):
        self.client = httpx.AsyncClient(base_url=TITAN_CORE_URL, timeout=60.0)

    async def evaluate_script(self, script: str, visual_features: dict = None) -> Dict[str, Any]:
        """Call Council of Titans to evaluate a script."""
        response = await self.client.post('/api/council/evaluate', json={
            'script': script,
            'visual_features': visual_features
        })
        return response.json()

    async def predict_roas(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Call Oracle Agent for ROAS prediction."""
        response = await self.client.post('/api/oracle/predict', json=features)
        return response.json()

    async def generate_blueprint(self, context: str, niche: str = 'fitness') -> Dict[str, Any]:
        """Call Director Agent to generate ad blueprint."""
        response = await self.client.post('/api/director/generate', json={
            'context': context,
            'niche': niche
        })
        return response.json()

    async def run_antigravity_loop(self, video_context: str) -> Dict[str, Any]:
        """Run full Antigravity loop (Director → Council → Approve)."""
        response = await self.client.post('/api/antigravity/run', json={
            'video_context': video_context
        })
        return response.json()


# /services/langgraph-app/src/adapters/council_tool.py
from langchain.tools import tool
from .titan_adapter import TitanAdapter

adapter = TitanAdapter()

@tool
async def evaluate_ad_script(script: str) -> str:
    """
    Evaluate an ad script using the Council of Titans (Gemini 2.0 + GPT-4o + Claude).
    Returns score (0-100) and detailed feedback.

    Use this when you need to evaluate ad creative quality.
    """
    result = await adapter.evaluate_script(script)
    return f"""
    Score: {result['final_score']}/100
    Verdict: {result['verdict']}
    Breakdown:
    - Gemini 2.0: {result['breakdown']['gemini_2_0_thinking']}
    - GPT-4o: {result['breakdown']['gpt_4o']}
    - Claude: {result['breakdown']['claude_3_5']}
    - DeepCTR: {result['breakdown']['deep_ctr']}

    Feedback: {result.get('feedback', 'N/A')}
    """

@tool
async def predict_ad_roas(ad_features: str) -> str:
    """
    Predict ROAS for an ad using the 8-engine Oracle Agent.
    Returns predicted ROAS with confidence interval.

    Use this when you need to predict ad performance.
    """
    import json
    features = json.loads(ad_features)
    result = await adapter.predict_roas(features)
    return f"""
    Predicted ROAS: {result['roas_prediction']['predicted_roas']:.2f}x
    Confidence: {result['roas_prediction']['confidence_level']*100:.0f}%
    Range: {result['roas_prediction']['confidence_lower']:.2f}x - {result['roas_prediction']['confidence_upper']:.2f}x

    Hook Score: {result['hook_score']}/10
    CTA Score: {result['cta_score']}/10
    Engagement Score: {result['engagement_score']}/10

    Recommendations: {', '.join(result['recommendations'][:3])}
    """

@tool
async def generate_ad_blueprint(video_context: str) -> str:
    """
    Generate an ad blueprint using the Director Agent with Gemini 3 Pro.
    Returns a complete ad script with hook, body, and CTA.

    Use this when you need to create new ad content.
    """
    result = await adapter.generate_blueprint(video_context)
    return f"""
    Status: {result['status']}
    Model: {result['model_used']}
    Turns Taken: {result['turns_taken']}

    Blueprint:
    {result['blueprint']}

    Council Score: {result['council_review'].get('final_score', 'N/A')}
    """
```

```python
# MODIFY: /services/langgraph-app/src/agent/tools.py
# Add at end:
from src.adapters.council_tool import evaluate_ad_script, predict_ad_roas, generate_ad_blueprint

# Update ALL_TOOLS
ALL_TOOLS = [
    search_winning_ads,
    check_model_status,
    check_ad_fatigue,
    get_account_config,
    search_crm_contacts,
    # NEW: Titan-Core integration
    evaluate_ad_script,
    predict_ad_roas,
    generate_ad_blueprint,
]
```

### Success Criteria
- [ ] CEO Agent can call Council evaluation
- [ ] CEO Agent can call Oracle prediction
- [ ] CEO Agent can call Director generation
- [ ] All tools return structured results
- [ ] Error handling for Titan-Core failures

### Dependencies
None - can start immediately

### Time: 2 hours

---

## 🔧 AGENT 8: THE DAY-PART OPTIMIZER (NEW)

### Mission
Build time-based budget optimization (TRUE GAP)

### Files to CREATE
```
/services/ml-service/src/optimization/
├── __init__.py
├── daypart_optimizer.py         # Core optimizer
├── hour_profiles.py             # Hour-based profiles
└── budget_scheduler.py          # Apply optimizations
```

### Implementation
```python
# /services/ml-service/src/optimization/daypart_optimizer.py
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
from sqlalchemy import func
from src.database import get_db
from src.models import CampaignPerformanceSnapshot
import logging

logger = logging.getLogger(__name__)

@dataclass
class HourProfile:
    hour: int
    avg_ctr: float
    avg_cpm: float
    avg_roas: float
    sample_count: int
    multiplier: float  # Budget multiplier for this hour

@dataclass
class DayPartSchedule:
    account_id: str
    campaign_id: str
    hour_profiles: List[HourProfile]
    peak_hours: List[int]      # Hours with 30%+ boost
    valley_hours: List[int]    # Hours with 30%- reduction
    optimal_daily_pattern: Dict[int, float]  # hour -> multiplier

class DayPartOptimizer:
    """
    Optimizes ad budget allocation by hour of day.
    Learns when ads perform best and allocates accordingly.
    """

    def __init__(self):
        self.min_samples_per_hour = 10
        self.boost_threshold = 1.3      # 30% above average
        self.reduction_threshold = 0.7  # 30% below average

    async def learn_hour_profiles(
        self,
        campaign_id: str,
        lookback_days: int = 30
    ) -> List[HourProfile]:
        """
        Learn performance by hour from historical data.
        """
        async with get_db() as db:
            # Get hourly performance data
            cutoff = datetime.utcnow() - timedelta(days=lookback_days)

            results = await db.execute(
                select(
                    func.extract('hour', CampaignPerformanceSnapshot.timestamp).label('hour'),
                    func.avg(CampaignPerformanceSnapshot.ctr).label('avg_ctr'),
                    func.avg(CampaignPerformanceSnapshot.cpm).label('avg_cpm'),
                    func.avg(CampaignPerformanceSnapshot.roas).label('avg_roas'),
                    func.count().label('count')
                )
                .where(CampaignPerformanceSnapshot.campaign_id == campaign_id)
                .where(CampaignPerformanceSnapshot.timestamp >= cutoff)
                .group_by(func.extract('hour', CampaignPerformanceSnapshot.timestamp))
            )

            hour_data = {row.hour: row for row in results}

        # Calculate overall average
        if not hour_data:
            return self._default_profiles()

        avg_roas = np.mean([h.avg_roas for h in hour_data.values()])

        # Create profiles with multipliers
        profiles = []
        for hour in range(24):
            if hour in hour_data:
                h = hour_data[hour]
                multiplier = h.avg_roas / avg_roas if avg_roas > 0 else 1.0
                profiles.append(HourProfile(
                    hour=hour,
                    avg_ctr=h.avg_ctr,
                    avg_cpm=h.avg_cpm,
                    avg_roas=h.avg_roas,
                    sample_count=h.count,
                    multiplier=min(max(multiplier, 0.3), 2.0)  # Clamp 0.3-2.0
                ))
            else:
                profiles.append(HourProfile(
                    hour=hour,
                    avg_ctr=0,
                    avg_cpm=0,
                    avg_roas=0,
                    sample_count=0,
                    multiplier=1.0
                ))

        return profiles

    async def create_schedule(
        self,
        account_id: str,
        campaign_id: str
    ) -> DayPartSchedule:
        """
        Create optimized day-part schedule for a campaign.
        """
        profiles = await self.learn_hour_profiles(campaign_id)

        peak_hours = [p.hour for p in profiles if p.multiplier >= self.boost_threshold]
        valley_hours = [p.hour for p in profiles if p.multiplier <= self.reduction_threshold]

        optimal_pattern = {p.hour: p.multiplier for p in profiles}

        logger.info(f"Created day-part schedule: peaks={peak_hours}, valleys={valley_hours}")

        return DayPartSchedule(
            account_id=account_id,
            campaign_id=campaign_id,
            hour_profiles=profiles,
            peak_hours=peak_hours,
            valley_hours=valley_hours,
            optimal_daily_pattern=optimal_pattern
        )

    def get_current_multiplier(self, schedule: DayPartSchedule) -> float:
        """Get budget multiplier for current hour."""
        current_hour = datetime.utcnow().hour
        return schedule.optimal_daily_pattern.get(current_hour, 1.0)

    def _default_profiles(self) -> List[HourProfile]:
        """Default profiles when no data available."""
        # Based on general social media patterns
        default_multipliers = {
            0: 0.5, 1: 0.4, 2: 0.3, 3: 0.3, 4: 0.4, 5: 0.6,
            6: 0.8, 7: 1.0, 8: 1.1, 9: 1.2, 10: 1.1, 11: 1.0,
            12: 1.2, 13: 1.1, 14: 1.0, 15: 1.0, 16: 1.1, 17: 1.2,
            18: 1.3, 19: 1.4, 20: 1.5, 21: 1.4, 22: 1.2, 23: 0.8
        }
        return [
            HourProfile(hour=h, avg_ctr=0, avg_cpm=0, avg_roas=0,
                       sample_count=0, multiplier=m)
            for h, m in default_multipliers.items()
        ]


# Integration with auto-scaler
async def apply_daypart_optimization(campaign_id: str, base_budget: float) -> float:
    """Apply day-part optimization to budget."""
    optimizer = DayPartOptimizer()
    schedule = await optimizer.create_schedule(None, campaign_id)
    multiplier = optimizer.get_current_multiplier(schedule)

    optimized_budget = base_budget * multiplier
    logger.info(f"Day-part optimization: {base_budget} -> {optimized_budget} (x{multiplier:.2f})")

    return optimized_budget
```

### Success Criteria
- [ ] Learn hour profiles from historical data
- [ ] Identify peak and valley hours
- [ ] Apply budget multipliers automatically
- [ ] Integration with auto-scaler

### Dependencies
Agent 3 (workers), Agent 4 (cache)

### Time: 2 hours

---

## 🔧 AGENT 9: THE CIRCUIT BREAKER (NEW)

### Mission
Build safety limits for budget and API calls (TRUE GAP)

### Files to CREATE
```
/services/ml-service/src/safety/
├── __init__.py
├── circuit_breaker.py           # Core circuit breaker
├── budget_limits.py             # Budget safety limits
├── api_throttle.py              # API rate limiting
└── stop_loss.py                 # Emergency stop logic
```

### Implementation
```python
# /services/ml-service/src/safety/circuit_breaker.py
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5      # Failures before opening
    success_threshold: int = 3      # Successes to close
    timeout_seconds: int = 60       # Time before half-open
    half_open_max_calls: int = 3    # Calls allowed in half-open

class CircuitBreaker:
    """
    Circuit breaker pattern for protecting against cascading failures.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_try_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info(f"Circuit {self.name}: OPEN -> HALF_OPEN")
            else:
                raise CircuitOpenError(f"Circuit {self.name} is OPEN")

        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.config.half_open_max_calls:
                raise CircuitOpenError(f"Circuit {self.name} half-open limit reached")
            self.half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info(f"Circuit {self.name}: HALF_OPEN -> CLOSED")
        else:
            self.failure_count = 0

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit {self.name}: HALF_OPEN -> OPEN (failure)")
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit {self.name}: CLOSED -> OPEN ({self.failure_count} failures)")

    def _should_try_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_seconds

class CircuitOpenError(Exception):
    pass


# /services/ml-service/src/safety/stop_loss.py
@dataclass
class StopLossConfig:
    max_daily_spend: float = 10000.0      # Max spend per day
    max_hourly_spend: float = 1000.0      # Max spend per hour
    min_roas_threshold: float = 0.5       # Pause if ROAS below this
    max_cpm_threshold: float = 100.0      # Pause if CPM above this
    cooldown_hours: int = 2               # Hours to wait after stop

class StopLossManager:
    """
    Emergency stop-loss for protecting ad spend.
    """

    def __init__(self, config: StopLossConfig = None):
        self.config = config or StopLossConfig()
        self.stopped_campaigns = {}  # campaign_id -> stop_time

    async def check_campaign(self, campaign_id: str, metrics: dict) -> dict:
        """
        Check if campaign should be stopped.
        Returns action and reason.
        """
        # Check if in cooldown
        if campaign_id in self.stopped_campaigns:
            stop_time = self.stopped_campaigns[campaign_id]
            if datetime.utcnow() - stop_time < timedelta(hours=self.config.cooldown_hours):
                return {'action': 'BLOCKED', 'reason': 'In cooldown period'}

        spend = metrics.get('spend', 0)
        roas = metrics.get('roas', 0)
        cpm = metrics.get('cpm', 0)

        # Check stop conditions
        if spend > self.config.max_daily_spend:
            return await self._stop_campaign(campaign_id, 'Daily spend limit exceeded')

        if roas < self.config.min_roas_threshold and spend > 100:
            return await self._stop_campaign(campaign_id, f'ROAS too low: {roas:.2f}')

        if cpm > self.config.max_cpm_threshold:
            return await self._stop_campaign(campaign_id, f'CPM too high: ${cpm:.2f}')

        return {'action': 'CONTINUE', 'reason': 'All metrics within limits'}

    async def _stop_campaign(self, campaign_id: str, reason: str) -> dict:
        """Stop campaign and record."""
        self.stopped_campaigns[campaign_id] = datetime.utcnow()
        logger.warning(f"🛑 STOP LOSS: Campaign {campaign_id} - {reason}")

        # Actually pause in Meta (implementation in meta_publisher)
        # await meta_publisher.pause_campaign(campaign_id)

        return {'action': 'STOPPED', 'reason': reason}
```

### Success Criteria
- [ ] Circuit breaker protects all external API calls
- [ ] Stop-loss triggers on budget limits
- [ ] Stop-loss triggers on poor ROAS
- [ ] Proper cooldown periods
- [ ] Alert notifications on stops

### Dependencies
None - can start immediately

### Time: 2 hours

---

## 🔧 AGENT 10: THE DRIFT DETECTOR (NEW)

### Mission
Monitor model drift and trigger retraining (TRUE GAP)

### Files to CREATE
```
/services/ml-service/src/monitoring/
├── __init__.py
├── drift_detector.py            # Core drift detection
├── statistical_tests.py         # KS, PSI tests
├── retrain_trigger.py           # Auto-retrain logic
└── alerting.py                  # Drift alerts
```

### Implementation
```python
# /services/ml-service/src/monitoring/drift_detector.py
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

@dataclass
class DriftResult:
    feature_name: str
    drift_score: float
    is_drifted: bool
    test_used: str
    p_value: float
    recommendation: str

@dataclass
class ModelDriftReport:
    model_name: str
    timestamp: datetime
    overall_drift_score: float
    is_significant_drift: bool
    feature_drifts: List[DriftResult]
    accuracy_delta: float
    recommendation: str

class DriftDetector:
    """
    Detects data drift and concept drift in ML models.
    Uses KS test for continuous features, PSI for distributions.
    """

    def __init__(self):
        self.ks_threshold = 0.1        # KS statistic threshold
        self.psi_threshold = 0.2       # PSI threshold (>0.2 = significant)
        self.accuracy_threshold = 0.05  # 5% accuracy drop = drift

    def detect_feature_drift(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        feature_name: str
    ) -> DriftResult:
        """
        Detect drift in a single feature using KS test.
        """
        # Kolmogorov-Smirnov test
        ks_stat, p_value = stats.ks_2samp(reference, current)

        is_drifted = ks_stat > self.ks_threshold

        recommendation = "No action needed"
        if is_drifted:
            if ks_stat > 0.3:
                recommendation = "CRITICAL: Immediate retraining required"
            elif ks_stat > 0.2:
                recommendation = "HIGH: Schedule retraining soon"
            else:
                recommendation = "MEDIUM: Monitor closely"

        return DriftResult(
            feature_name=feature_name,
            drift_score=ks_stat,
            is_drifted=is_drifted,
            test_used="Kolmogorov-Smirnov",
            p_value=p_value,
            recommendation=recommendation
        )

    def calculate_psi(
        self,
        reference: np.ndarray,
        current: np.ndarray,
        bins: int = 10
    ) -> float:
        """
        Calculate Population Stability Index (PSI).
        PSI < 0.1: No drift
        0.1 <= PSI < 0.2: Slight drift
        PSI >= 0.2: Significant drift
        """
        # Create bins from reference distribution
        _, bin_edges = np.histogram(reference, bins=bins)

        # Calculate proportions
        ref_counts, _ = np.histogram(reference, bins=bin_edges)
        cur_counts, _ = np.histogram(current, bins=bin_edges)

        ref_props = ref_counts / len(reference)
        cur_props = cur_counts / len(current)

        # Avoid division by zero
        ref_props = np.where(ref_props == 0, 0.0001, ref_props)
        cur_props = np.where(cur_props == 0, 0.0001, cur_props)

        # PSI formula
        psi = np.sum((cur_props - ref_props) * np.log(cur_props / ref_props))

        return psi

    async def analyze_model(
        self,
        model_name: str,
        reference_data: Dict[str, np.ndarray],
        current_data: Dict[str, np.ndarray],
        reference_accuracy: float,
        current_accuracy: float
    ) -> ModelDriftReport:
        """
        Comprehensive drift analysis for a model.
        """
        feature_drifts = []
        drift_scores = []

        for feature_name in reference_data.keys():
            if feature_name in current_data:
                result = self.detect_feature_drift(
                    reference_data[feature_name],
                    current_data[feature_name],
                    feature_name
                )
                feature_drifts.append(result)
                drift_scores.append(result.drift_score)

        overall_drift = np.mean(drift_scores) if drift_scores else 0
        accuracy_delta = reference_accuracy - current_accuracy

        is_significant = (
            overall_drift > self.ks_threshold or
            accuracy_delta > self.accuracy_threshold
        )

        if is_significant:
            if accuracy_delta > 0.1:
                recommendation = "CRITICAL: Retrain immediately - accuracy dropped significantly"
            elif overall_drift > 0.2:
                recommendation = "HIGH: Retrain soon - major feature drift detected"
            else:
                recommendation = "MEDIUM: Schedule retraining - drift accumulating"
        else:
            recommendation = "OK: Model performing within acceptable range"

        return ModelDriftReport(
            model_name=model_name,
            timestamp=datetime.utcnow(),
            overall_drift_score=overall_drift,
            is_significant_drift=is_significant,
            feature_drifts=feature_drifts,
            accuracy_delta=accuracy_delta,
            recommendation=recommendation
        )


# Celery task for periodic drift checking
@celery_app.task
def check_model_drift():
    """Run drift detection for all models."""
    detector = DriftDetector()

    models_to_check = ['ctr_model', 'enhanced_ctr_model', 'roas_predictor']

    for model_name in models_to_check:
        # Get reference data (from training)
        reference = load_reference_data(model_name)

        # Get current data (last 7 days)
        current = load_current_data(model_name, days=7)

        # Get accuracy metrics
        ref_accuracy = get_reference_accuracy(model_name)
        cur_accuracy = get_current_accuracy(model_name)

        # Analyze
        report = asyncio.run(detector.analyze_model(
            model_name, reference, current, ref_accuracy, cur_accuracy
        ))

        # Store report
        save_drift_report(report)

        # Trigger action if needed
        if report.is_significant_drift:
            logger.warning(f"🚨 Drift detected in {model_name}: {report.recommendation}")
            if "CRITICAL" in report.recommendation:
                trigger_model_retrain(model_name)
```

### Success Criteria
- [ ] Detect feature drift using KS test
- [ ] Calculate PSI for distribution shift
- [ ] Track accuracy degradation
- [ ] Auto-trigger retraining when critical
- [ ] Alert on significant drift

### Dependencies
Agent 3 (workers)

### Time: 2 hours

---

## 📊 EXPECTED RESULTS

| Metric | Before | After 10 Agents | Improvement |
|--------|--------|-----------------|-------------|
| **Platform Accessible** | 59% | 100% | +41% |
| **Build Errors** | 50 critical | 0 | -100% |
| **Background Jobs** | 0 running | 6 running | ∞ |
| **API Cache Hit Rate** | 0% | 70%+ | ∞ |
| **Response Time** | 2000ms | <100ms | -95% |
| **Budget Optimization** | Static | Dynamic (24h) | New capability |
| **Safety Limits** | None | Circuit breaker | New capability |
| **Model Monitoring** | None | Auto-drift detection | New capability |
| **LangGraph-Titan** | Separate | Integrated | New capability |

---

## 🚀 DEPLOYMENT COMMAND

```bash
# Deploy all 10 agents in waves

# WAVE 1: Foundation (parallel)
claude-code --agent=1 --task="error-fixer" &
claude-code --agent=2 --task="router-wirer" &
claude-code --agent=3 --task="worker-activator" &
claude-code --agent=4 --task="semantic-cache" &
wait

# WAVE 2: Integration (parallel)
claude-code --agent=5 --task="cross-learner" &
claude-code --agent=6 --task="precomputer" &
claude-code --agent=7 --task="langgraph-titan" &
wait

# WAVE 3: Gap Fillers (parallel)
claude-code --agent=8 --task="daypart-optimizer" &
claude-code --agent=9 --task="circuit-breaker" &
claude-code --agent=10 --task="drift-detector" &
wait

echo "✅ All 10 agents complete!"
```

---

## ✅ SUCCESS CHECKLIST

- [ ] All 50 errors fixed
- [ ] All 32 components routed
- [ ] All 6 workers running
- [ ] Semantic cache active (70%+ hit rate)
- [ ] Cross-learner running daily
- [ ] Precomputer running every 15 min
- [ ] LangGraph-Titan bridge working
- [ ] Day-part optimization active
- [ ] Circuit breaker protecting APIs
- [ ] Drift detector monitoring models

---

**TOTAL TIME: 6-8 hours with parallel execution**
**TOTAL IMPACT: 59% → 100% platform accessibility**
