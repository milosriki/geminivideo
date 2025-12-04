# 🚀 PARALLEL EXECUTION PLAN: 10 Agents x 2 Hours

**Goal:** Transform system from 44% SMART to 95% SMART in 2 hours
**Method:** 10 specialized agents working simultaneously on isolated file sets
**No Conflicts:** Each agent owns specific files - no overlap

---

## AGENT ORCHESTRATION DIAGRAM

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PARALLEL AGENT EXECUTION (2 HOURS)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  HOUR 1: WIRE REAL SERVICES + REMOVE FAKES                                 │
│  ═══════════════════════════════════════════                               │
│                                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ AGENT 1 │ │ AGENT 2 │ │ AGENT 3 │ │ AGENT 4 │ │ AGENT 5 │              │
│  │ Drive   │ │ Video   │ │ Gateway │ │ Scoring │ │ ML      │              │
│  │ Intel   │ │ Agent   │ │ API     │ │ Engine  │ │ Service │              │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘              │
│       │          │          │          │          │                        │
│       ▼          ▼          ▼          ▼          ▼                        │
│  Wire real   Wire real   Fix fake   Replace    Connect                     │
│  scene       FFmpeg      endpoints  keywords   feedback                    │
│  detection   renderer    /analyze   with AI    loop                        │
│                                                                             │
│  HOUR 2: ADD AI INTELLIGENCE + CLOSE LOOPS                                 │
│  ═══════════════════════════════════════════                               │
│                                                                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐              │
│  │ AGENT 6 │ │ AGENT 7 │ │ AGENT 8 │ │ AGENT 9 │ │AGENT 10 │              │
│  │ Titan   │ │ Frontend│ │ RAG     │ │ Market  │ │ Test &  │              │
│  │ Core    │ │ AI      │ │ System  │ │ Intel   │ │ Deploy  │              │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘              │
│       │          │          │          │          │                        │
│       ▼          ▼          ▼          ▼          ▼                        │
│  Structured  Real AI     Winner     Real        Integration               │
│  output +    insights    memory     competitor  tests +                    │
│  CoT prompts component   FAISS      data        health                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## AGENT 1: DRIVE INTEL (Wire Real Services)

**Owner:** `services/drive-intel/`
**Time:** 60 min
**No Conflict:** Only touches drive-intel files

### Tasks:
```
1. Wire real scene detection (services/scene_detector.py → src/main.py)
2. Wire real feature extraction (services/feature_extractor.py → src/main.py)
3. Wire real Google Drive service (services/google_drive_service.py → src/main.py)
4. Remove all mock data from process_asset()
5. Connect to PostgreSQL instead of in-memory dict
```

### Files to Modify:
```
services/drive-intel/src/main.py          - REWRITE process_asset()
services/drive-intel/src/bulk_analyzer.py - Wire real services
```

### Code Change:
```python
# BEFORE (FAKE):
async def process_asset(asset_id: str):
    await asyncio.sleep(2)  # FAKE
    num_clips = 5  # HARDCODED

# AFTER (REAL):
from services.scene_detector import SceneDetector
from services.feature_extractor import FeatureExtractor

async def process_asset(asset_id: str):
    asset = assets_db[asset_id]
    video_path = asset["path"]

    # REAL scene detection
    detector = SceneDetector()
    scenes = detector.detect_scenes(video_path)

    # REAL feature extraction
    extractor = FeatureExtractor()
    for scene in scenes:
        features = extractor.extract_features(video_path, scene.start, scene.end)
        # Store real data
```

---

## AGENT 2: VIDEO AGENT (Wire FFmpeg Renderer)

**Owner:** `services/video-agent/`
**Time:** 60 min
**No Conflict:** Only touches video-agent files

### Tasks:
```
1. Wire real renderer (services/renderer.py → src/index.py)
2. Remove sleep() placeholder
3. Add real FFmpeg subprocess calls
4. Wire subtitle generator
5. Wire compliance checker
```

### Files to Modify:
```
services/video-agent/src/index.py         - REWRITE process_render_job()
services/video-agent/worker.py            - Fix Pydantic issues
```

### Code Change:
```python
# BEFORE (FAKE):
async def process_render_job(job_id: str):
    await asyncio.sleep(2)  # FAKE - no work done

# AFTER (REAL):
from services.renderer import VideoRenderer

async def process_render_job(job_id: str):
    job = render_jobs[job_id]
    renderer = VideoRenderer()

    # REAL rendering
    output_path = renderer.concatenate_scenes(
        scenes=job["storyboard"],
        output_path=f"/outputs/{job_id}.mp4"
    )
    job["output_path"] = output_path
    job["status"] = "completed"
```

---

## AGENT 3: GATEWAY API (Fix Fake Endpoints)

**Owner:** `services/gateway-api/src/index.ts`
**Time:** 60 min
**No Conflict:** Only touches gateway-api index.ts

### Tasks:
```
1. Fix /api/analyze - use real Gemini Vision
2. Fix /api/metrics - connect to real Meta API
3. Remove hardcoded fallbacks (85, 8, 8)
4. Add structured output parsing
5. Connect Redis queue to workers
```

### Files to Modify:
```
services/gateway-api/src/index.ts         - Fix /api/analyze, /api/metrics
```

### Code Change:
```typescript
// BEFORE (FAKE):
app.post('/api/analyze', async (req, res) => {
    res.json({
        hook_style: "High Energy",  // ALWAYS SAME
    });
});

// AFTER (REAL):
import { GoogleGenerativeAI } from '@google/generative-ai';

app.post('/api/analyze', async (req, res) => {
    const { video_uri } = req.body;
    const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

    // REAL analysis
    const result = await model.generateContent({
        contents: [{
            role: 'user',
            parts: [
                { fileData: { fileUri: video_uri, mimeType: 'video/mp4' }},
                { text: 'Analyze this video ad: hook style, pacing, emotions...' }
            ]
        }],
        generationConfig: { responseMimeType: 'application/json' }
    });

    res.json(JSON.parse(result.response.text()));
});
```

---

## AGENT 4: SCORING ENGINE (Replace Keywords with AI)

**Owner:** `services/gateway-api/src/services/scoring-engine.ts`
**Time:** 60 min
**No Conflict:** Only touches scoring-engine.ts

### Tasks:
```
1. Replace keyword matching with Gemini API calls
2. Remove hardcoded 0.7 values
3. Add Chain-of-Thought prompting
4. Add structured output schema
5. Make scoring async
```

### Files to Modify:
```
services/gateway-api/src/services/scoring-engine.ts  - REWRITE all scoring
```

### Code Change:
```typescript
// BEFORE (FAKE):
private calculatePsychologyScore(scenes: any[]): number {
    const matches = keywordList.filter(kw =>
        allText.includes(kw.toLowerCase())  // DUMB keyword matching
    ).length;
}

// AFTER (REAL):
private async calculatePsychologyScore(scenes: any[]): Promise<number> {
    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash' });

    const result = await model.generateContent({
        contents: [{
            role: 'user',
            parts: [{ text: `
                Analyze psychological triggers step by step:

                Content: ${JSON.stringify(scenes)}

                1. PAIN POINT: What problem is addressed? (0-100)
                2. TRANSFORMATION: What result is promised? (0-100)
                3. URGENCY: Is there authentic urgency? (0-100)
                4. AUTHORITY: What credibility exists? (0-100)
                5. SOCIAL PROOF: What evidence of success? (0-100)

                Return JSON with reasoning and scores.
            `}]
        }],
        generationConfig: {
            responseMimeType: 'application/json',
            responseSchema: PSYCHOLOGY_SCHEMA
        }
    });

    return JSON.parse(result.response.text());
}
```

---

## AGENT 5: ML SERVICE (Connect Feedback Loop)

**Owner:** `services/ml-service/`
**Time:** 60 min
**No Conflict:** Only touches ml-service files

### Tasks:
```
1. Connect Meta insights to XGBoost retraining
2. Wire Thompson Sampler to variant selection
3. Add automatic retraining trigger
4. Remove synthetic data generation
5. Add real performance feedback endpoint
```

### Files to Modify:
```
services/ml-service/src/main.py           - Add feedback endpoint
services/ml-service/src/ctr_model.py      - Real training pipeline
services/ml-service/src/thompson_sampler.py - Connect to variants
```

### Code Change:
```python
# ADD: Feedback loop endpoint
@app.post("/api/ml/feedback")
async def record_feedback(data: FeedbackData):
    """Record real performance and trigger retraining"""
    # Store performance
    db.insert({
        "ad_id": data.ad_id,
        "impressions": data.impressions,
        "clicks": data.clicks,
        "ctr": data.clicks / data.impressions
    })

    # Update Thompson Sampler
    thompson_sampler.update(data.variant_id, reward=data.ctr)

    # Check if retraining needed
    samples = db.count_since(hours=24)
    if samples >= 100:
        await trigger_retrain()

    return {"status": "recorded", "retrain_triggered": samples >= 100}
```

---

## AGENT 6: TITAN CORE (Structured Output + CoT)

**Owner:** `services/titan-core/`
**Time:** 60 min
**No Conflict:** Only touches titan-core files

### Tasks:
```
1. Add structured output to ensemble.py (no more string parsing)
2. Add Chain-of-Thought to all prompts
3. Make verdict threshold dynamic per niche
4. Add RAG context to orchestrator
5. Fix brittle JSON parsing
```

### Files to Modify:
```
services/titan-core/engines/ensemble.py            - Structured output
services/titan-core/orchestrator.py                - Add RAG
services/titan-core/engines/andromeda_prompts.py   - CoT prompts
```

### Code Change:
```python
# BEFORE (BRITTLE):
text = response.text
if "SCORE:" in text:
    score_text = text.split("SCORE:")[1].split("\n")[0]  # BREAKS EASILY

# AFTER (ROBUST):
response = await model.generate_content(
    prompt,
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema={
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "score": {"type": "number", "minimum": 0, "maximum": 100}
            },
            "required": ["reasoning", "score"]
        }
    )
)
result = json.loads(response.text)  # GUARANTEED valid JSON
```

---

## AGENT 7: FRONTEND AI (Real Insights)

**Owner:** `frontend/src/components/` + `frontend/src/pages/`
**Time:** 60 min
**No Conflict:** Only touches frontend files

### Tasks:
```
1. Replace mock insights with real API call
2. Connect AdSpyPage to backend
3. Add real-time refresh
4. Remove hardcoded competitor data
5. Add loading states
```

### Files to Modify:
```
frontend/src/components/dashboard/AIInsights.tsx   - Real API
frontend/src/pages/AdSpyPage.tsx                   - Real competitors
frontend/src/services/apiClient.ts                 - New endpoints
```

### Code Change:
```typescript
// BEFORE (FAKE):
const mockInsights = [
    { description: "23% better than average" }  // HARDCODED
];

// AFTER (REAL):
const [insights, setInsights] = useState<Insight[]>([]);

useEffect(() => {
    const fetchInsights = async () => {
        const response = await fetch('/api/insights/ai');
        const data = await response.json();
        setInsights(data.insights);
    };
    fetchInsights();
}, []);
```

---

## AGENT 8: RAG SYSTEM (Winner Memory)

**Owner:** NEW files + `services/drive-intel/services/search.py`
**Time:** 60 min
**No Conflict:** Creates new files

### Tasks:
```
1. Create FAISS index for winning ads
2. Add embedding generation for new content
3. Create RAG retrieval function
4. Inject winners into generation prompts
5. Add similarity search endpoint
```

### Files to Create/Modify:
```
services/rag/winner_index.py              - NEW: FAISS index
services/rag/embeddings.py                - NEW: Embedding generation
services/titan-core/orchestrator.py       - Inject RAG context
```

### Code:
```python
# NEW FILE: services/rag/winner_index.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class WinnerIndex:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index = faiss.IndexFlatIP(384)  # Inner product
        self.winners = []

    def add_winner(self, ad_data: dict, ctr: float):
        """Add winning ad to index"""
        if ctr < 0.05:  # Only winners
            return
        embedding = self.model.encode(str(ad_data))
        self.index.add(np.array([embedding]))
        self.winners.append(ad_data)

    def find_similar(self, query: str, k: int = 5) -> list:
        """Find similar winning ads"""
        query_emb = self.model.encode(query)
        distances, indices = self.index.search(np.array([query_emb]), k)
        return [self.winners[i] for i in indices[0] if i < len(self.winners)]
```

---

## AGENT 9: MARKET INTEL (Real Competitor Data)

**Owner:** `scripts/` + new market intel service
**Time:** 60 min
**No Conflict:** Creates new files, modifies scripts/

### Tasks:
```
1. Add CSV upload endpoint for competitor data
2. Create Apify integration (optional)
3. Replace hardcoded patterns with real data
4. Add competitor tracking database table
5. Create trending analysis from real data
```

### Files to Create/Modify:
```
scripts/meta_ads_library_pattern_miner.py  - Real data source
services/market-intel/competitor_tracker.py - NEW: Tracking
services/gateway-api/src/index.ts          - CSV upload endpoint
```

### Code:
```python
# NEW FILE: services/market-intel/competitor_tracker.py
import pandas as pd
from datetime import datetime

class CompetitorTracker:
    def __init__(self, db):
        self.db = db

    async def import_from_csv(self, csv_path: str):
        """Import competitor ads from CSV"""
        df = pd.read_csv(csv_path)
        for _, row in df.iterrows():
            await self.db.insert("competitor_ads", {
                "brand": row["brand"],
                "hook_text": row["hook"],
                "engagement": row["engagement"],
                "platform": row["platform"],
                "imported_at": datetime.utcnow()
            })

    async def get_winning_patterns(self, niche: str):
        """Get real patterns from tracked competitors"""
        ads = await self.db.query(
            "SELECT * FROM competitor_ads WHERE niche = $1 ORDER BY engagement DESC LIMIT 100",
            [niche]
        )
        # Analyze REAL patterns
        return self._analyze_patterns(ads)
```

---

## AGENT 10: TEST & DEPLOY (Integration + Health)

**Owner:** Tests + deployment configs
**Time:** 60 min
**No Conflict:** Only touches test files and configs

### Tasks:
```
1. Create integration tests for all fixed endpoints
2. Add health checks for all services
3. Update docker-compose with proper env vars
4. Create deployment verification script
5. Test full pipeline end-to-end
```

### Files to Create/Modify:
```
tests/integration/test_pipeline.py        - NEW: Full pipeline test
tests/integration/test_ai_endpoints.py    - NEW: AI endpoint tests
docker-compose.yml                        - Add missing env vars
scripts/verify_deployment.py              - NEW: Deployment check
```

### Code:
```python
# NEW FILE: tests/integration/test_pipeline.py
import pytest
import asyncio

class TestFullPipeline:
    """Test the entire pipeline with real services"""

    async def test_analyze_endpoint_returns_real_data(self):
        """Verify /api/analyze no longer returns hardcoded data"""
        response = await client.post('/api/analyze', json={
            'video_uri': 'gs://test/video.mp4'
        })
        data = response.json()

        # Should NOT always be "High Energy"
        assert data['hook_style'] != "High Energy" or data.get('confidence')
        assert 'reasoning' in data  # AI should explain

    async def test_feedback_loop_works(self):
        """Verify feedback updates models"""
        # Record feedback
        await client.post('/api/ml/feedback', json={
            'ad_id': 'test-123',
            'impressions': 1000,
            'clicks': 50
        })

        # Verify Thompson Sampler updated
        stats = await client.get('/api/ml/stats')
        assert stats.json()['total_feedback'] > 0
```

---

## EXECUTION TIMELINE

```
TIME        AGENT 1     AGENT 2     AGENT 3     AGENT 4     AGENT 5
────────────────────────────────────────────────────────────────────
0:00        Start       Start       Start       Start       Start
            Drive       Video       Gateway     Scoring     ML
            Intel       Agent       API         Engine      Service

0:30        Scene       FFmpeg      /analyze    Psychology  Feedback
            Detection   Wired       Fixed       AI Call     Loop
            Wired

1:00        Features    Renderer    /metrics    Demographics Thompson
            Extracted   Complete    Fixed       AI Call     Connected


TIME        AGENT 6     AGENT 7     AGENT 8     AGENT 9     AGENT 10
────────────────────────────────────────────────────────────────────
0:00        Start       Start       Start       Start       Start
            Titan       Frontend    RAG         Market      Test
            Core        AI          System      Intel       Deploy

0:30        Structured  Insights    FAISS       CSV         Integration
            Output      Real        Index       Upload      Tests

1:00        CoT         AdSpy       RAG         Patterns    E2E
            Prompts     Real        Integrated  Real        Verified

1:30        ALL AGENTS COMPLETE - MERGE & DEPLOY

2:00        PRODUCTION READY ✅
```

---

## NO-CONFLICT FILE MATRIX

| Agent | Exclusive Files | No Overlap |
|-------|-----------------|------------|
| 1 | `services/drive-intel/src/main.py`, `bulk_analyzer.py` | ✅ |
| 2 | `services/video-agent/src/index.py`, `worker.py` | ✅ |
| 3 | `services/gateway-api/src/index.ts` | ✅ |
| 4 | `services/gateway-api/src/services/scoring-engine.ts` | ✅ |
| 5 | `services/ml-service/src/*` | ✅ |
| 6 | `services/titan-core/engines/*`, `orchestrator.py` | ✅ |
| 7 | `frontend/src/components/`, `frontend/src/pages/` | ✅ |
| 8 | `services/rag/*` (NEW) | ✅ |
| 9 | `scripts/*`, `services/market-intel/*` (NEW) | ✅ |
| 10 | `tests/*`, `docker-compose.yml` | ✅ |

---

## EXPECTED OUTCOME

| Metric | Before | After 2 Hours |
|--------|--------|---------------|
| SMART decisions | 44% | 95% |
| DUMB decisions | 44% | 5% |
| FAKE decisions | 12% | 0% |
| Feedback loops | 0 | 3 |
| RAG queries | 0% | 100% |
| Structured output | 0% | 100% |
| Real market data | 0% | 100% |

---

## COMMAND TO LAUNCH ALL AGENTS

```bash
# Launch all 10 agents in parallel
claude-code --parallel \
  --agent-1 "Wire real services in drive-intel/src/main.py" \
  --agent-2 "Wire FFmpeg in video-agent/src/index.py" \
  --agent-3 "Fix fake endpoints in gateway-api/src/index.ts" \
  --agent-4 "Replace keywords with AI in scoring-engine.ts" \
  --agent-5 "Connect feedback loop in ml-service" \
  --agent-6 "Add structured output in titan-core" \
  --agent-7 "Fix frontend AI components" \
  --agent-8 "Create RAG system in services/rag/" \
  --agent-9 "Add real market data in scripts/" \
  --agent-10 "Create integration tests"
```

---

## SUCCESS CRITERIA

After 2 hours, run this verification:

```bash
# 1. No more hardcoded responses
curl -X POST localhost:8000/api/analyze -d '{"video_uri":"test.mp4"}'
# Should NOT return "High Energy" every time

# 2. Real scene detection
curl localhost:8001/assets/test-123/clips
# Should return REAL scenes, not always 5

# 3. Feedback loop works
curl -X POST localhost:8003/api/ml/feedback -d '{"ad_id":"x","ctr":0.05}'
# Should update Thompson Sampler

# 4. RAG retrieval works
curl localhost:8000/api/rag/similar -d '{"query":"fitness ad"}'
# Should return similar winners
```

---

## THE BOTTOM LINE

**10 agents, 2 hours, zero conflicts.**

Each agent owns specific files and completes specific transformations.
At the end: System goes from "AI in name only" to "AI-powered decisions."
