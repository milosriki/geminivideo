# AI STRATEGY: Making GeminiVideo Actually Intelligent

**Date:** December 2024
**Timeline:** 30 days @ 15 hours/day = 450 hours
**Goal:** Transform from "AI in name only" to "AI-powered decisions"

---

## CURRENT STATE: THE BRUTAL TRUTH

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION INTELLIGENCE MAP                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   36 TOTAL DECISIONS ANALYZED                                   │
│                                                                 │
│   ████████████████░░░░░░░░░░░░░░░░  44% SMART (16)             │
│   ████████████████░░░░░░░░░░░░░░░░  44% DUMB  (16)             │
│   ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  12% FAKE  (4)              │
│                                                                 │
│   SMART = Real AI/ML making decisions                          │
│   DUMB  = Keyword matching, hardcoded rules (looks smart)      │
│   FAKE  = Returns same value every time (mock data)            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## THE 16 DUMB DECISIONS THAT MUST BECOME SMART

| # | Decision | Current Method | Should Be | File:Line |
|---|----------|----------------|-----------|-----------|
| 1 | Psychology Score | `text.includes(keyword)` | Gemini analysis | scoring-engine.ts:107 |
| 2 | Hook Strength | Regex (has number?) | Claude psychology | scoring-engine.ts:156 |
| 3 | Demographic Match | Hardcoded 0.7 always | Vision + persona AI | scoring-engine.ts:239 |
| 4 | Clip Selection | SQL ORDER BY score | AI ranking with context | index.ts:433 |
| 5 | Clip Ranking | Static weights (25%, 20%) | Learned weights | ranking.py:19 |
| 6 | Verdict Threshold | if score >= 85 | Dynamic per niche | ensemble.py:144 |
| 7 | Hook Variants | random.shuffle() | AI-generated variations | variant_generator.py:61 |
| 8 | Audience Selection | Pass-through string | AI persona matching | index.ts:315 |
| 9 | Scene Detection | Formula (i * 6.0) | Real PySceneDetect | main.py:261 |
| 10 | Motion Energy | Formula (0.5 + i*0.1) | OpenCV analysis | main.py:271 |
| 11 | Object Detection | Fake ["person"] | Real YOLO (exists!) | main.py:277 |
| 12 | Text Detection | Fake "Scene text" | Real PaddleOCR (exists!) | main.py:279 |
| 13 | Embeddings | Fake [0.1] * 512 | Real SentenceTransformer | main.py:281 |
| 14 | Council Weights | Fixed 40/30/20/10 | Learned from performance | ensemble.py:132 |
| 15 | Composite Score | Hardcoded formula | ML regression | scoring.ts:145 |
| 16 | Budget Allocation | Static percentages | Thompson Sampling (exists!) | thompson_sampler.py:331 |

---

## THE 4 FAKE DECISIONS THAT MUST BECOME REAL

| # | Decision | Current Output | Should Be | File:Line |
|---|----------|----------------|-----------|-----------|
| 1 | Video Analysis | Always "High Energy, Fast" | Real Gemini Vision | index.ts:387 |
| 2 | Metrics Dashboard | Hardcoded 15000 impressions | Real Meta API | index.ts:560 |
| 3 | Market Patterns | Fabricated 345, 289 counts | Real competitor data | pattern_miner.py:56 |
| 4 | AI Insights | "23% better" invented | Real performance analysis | AIInsights.tsx:48 |

---

## MISSING AI PATTERNS (MUST IMPLEMENT)

### 1. RAG (Retrieval Augmented Generation)
**Status:** NOT IMPLEMENTED
**Impact:** AI can't learn from past successes

```python
# CURRENT: AI generates blindly
response = gemini.generate("Create a fitness ad hook")

# SHOULD BE: AI uses past winners
winners = faiss_search("fitness hooks that converted > 5%")
response = gemini.generate(f"""
Create a fitness ad hook.

Here are hooks that performed well in the past:
{winners}

Generate a new hook that follows these winning patterns.
""")
```

### 2. Chain-of-Thought Prompting
**Status:** NOT IMPLEMENTED
**Impact:** AI gives shallow answers

```python
# CURRENT: Direct question
prompt = "Score this ad 0-100"

# SHOULD BE: Reasoning first
prompt = """
Analyze this ad step by step:

1. HOOK ANALYSIS: What technique is used? Is it effective?
2. PAIN POINT: What problem does it address? How clearly?
3. TRANSFORMATION: What result is promised? Is it believable?
4. URGENCY: What drives action? Is it authentic or forced?
5. CTA: Is the next step clear and compelling?

Based on your analysis above, provide:
- REASONING: Why this score?
- SCORE: 0-100
"""
```

### 3. Feedback Loops
**Status:** INFRASTRUCTURE EXISTS, NOT CONNECTED
**Impact:** System never improves

```
CURRENT FLOW:
Create Ad → Publish → [Results go nowhere]

SHOULD BE:
Create Ad → Publish → Track CTR → Update weights → Create better ad
                              ↓
                    Thompson Sampler (exists!)
                              ↓
                    XGBoost retrain (exists!)
```

### 4. Multi-Agent with Dynamic Routing
**Status:** HARDCODED AGENT SELECTION
**Impact:** Same process for every ad type

```python
# CURRENT: Always same 4 agents in same order
council = [Gemini, Claude, GPT, DeepCTR]
for agent in council:
    agent.evaluate(script)

# SHOULD BE: AI decides which agents needed
router = gemini.generate(f"""
Given this ad brief: {brief}

Which specialists should evaluate this?
- Psychology Expert (Claude): For emotional triggers
- Logic Verifier (GPT): For claim verification
- Trend Analyzer (Gemini): For market fit
- CTR Predictor (XGBoost): For performance estimate

Select 2-3 most relevant for this specific ad.
""")
```

---

## 30-DAY IMPLEMENTATION PLAN

### WEEK 1: Fix the Fakes (Days 1-7)
**Goal:** Remove all mock data, wire real services

| Day | Hours | Task | Files |
|-----|-------|------|-------|
| 1 | 15 | Wire real scene detection in main.py | drive-intel/src/main.py |
| 2 | 15 | Wire real feature extraction (YOLO, OCR) | feature_extractor.py |
| 3 | 15 | Fix /api/analyze to use real Gemini Vision | gateway-api/index.ts |
| 4 | 15 | Fix /api/metrics to use real Meta API | gateway-api/index.ts |
| 5 | 15 | Add real market data source (Apify/CSV) | pattern_miner.py |
| 6 | 15 | Connect AIInsights to real analysis | AIInsights.tsx |
| 7 | 15 | Test all wired services, fix bugs | All |

**Deliverable:** No more mock data in production paths

---

### WEEK 2: Make Decisions Smart (Days 8-14)
**Goal:** Replace keyword matching with AI calls

| Day | Hours | Task | Before → After |
|-----|-------|------|----------------|
| 8 | 15 | Replace psychology scoring | includes() → Gemini |
| 9 | 15 | Replace hook strength | Regex → Claude |
| 10 | 15 | Replace demographic match | 0.7 → Vision AI |
| 11 | 15 | Replace clip ranking | Static → Learned |
| 12 | 15 | Add RAG to all generation | Blind → Context-aware |
| 13 | 15 | Add Chain-of-Thought prompts | Direct → Reasoning |
| 14 | 15 | Test decision quality, tune | All |

**Deliverable:** All 16 DUMB decisions become SMART

---

### WEEK 3: Close the Loops (Days 15-21)
**Goal:** Connect feedback for continuous improvement

| Day | Hours | Task | Loop |
|-----|-------|------|------|
| 15 | 15 | Connect Meta insights to database | Performance → DB |
| 16 | 15 | Build retraining pipeline | DB → XGBoost |
| 17 | 15 | Connect Thompson Sampler to variants | Results → Selection |
| 18 | 15 | Add weight calibration trigger | Performance → Weights |
| 19 | 15 | Build A/B test result processor | Test → Learn |
| 20 | 15 | Add automated winner detection | Stats → Flag |
| 21 | 15 | Test full feedback loop | End-to-end |

**Deliverable:** System improves from every ad it runs

---

### WEEK 4: Scale Intelligence (Days 22-30)
**Goal:** Advanced AI patterns, production hardening

| Day | Hours | Task | Capability |
|-----|-------|------|------------|
| 22 | 15 | Add dynamic agent routing | Smart orchestration |
| 23 | 15 | Add structured output (Gemini) | Reliable parsing |
| 24 | 15 | Add structured output (Claude) | Reliable parsing |
| 25 | 15 | Build niche-specific models | Domain expertise |
| 26 | 15 | Add real-time trend detection | Market following |
| 27 | 15 | Add competitor response system | Competitive intel |
| 28 | 15 | Production hardening, error handling | Reliability |
| 29 | 15 | Load testing, optimization | Performance |
| 30 | 15 | Documentation, deployment | Launch ready |

**Deliverable:** Production-ready AI system

---

## CODE TRANSFORMATIONS REQUIRED

### Transform #1: Psychology Scoring
```typescript
// ❌ CURRENT (scoring-engine.ts:107)
private calculatePsychologyScore(scenes: any[]): number {
    const allText = this.extractAllText(scenes).toLowerCase();
    for (const [category, keywordList] of Object.entries(keywords)) {
        const matches = keywordList.filter(kw =>
            allText.includes(kw.toLowerCase())  // Just word counting!
        ).length;
    }
}

// ✅ SHOULD BE
private async calculatePsychologyScore(scenes: any[]): Promise<number> {
    const analysis = await this.gemini.generateContent({
        contents: [{
            role: 'user',
            parts: [{
                text: `Analyze the psychological triggers in this content:

                ${JSON.stringify(scenes)}

                Rate each dimension 0-100:
                1. Pain Point Clarity: How clearly is the problem stated?
                2. Transformation Promise: How compelling is the result?
                3. Urgency Authenticity: Is the urgency real or forced?
                4. Authority Signals: What credibility markers exist?
                5. Social Proof: What evidence of others' success?

                Think step by step, then provide scores.`
            }]
        }],
        generationConfig: {
            responseMimeType: "application/json",
            responseSchema: PSYCHOLOGY_SCHEMA
        }
    });
    return analysis.response.compositeScore;
}
```

### Transform #2: Video Analysis Endpoint
```typescript
// ❌ CURRENT (index.ts:387)
app.post('/api/analyze', async (req, res) => {
    res.json({
        hook_style: "High Energy",      // ALWAYS THE SAME
        pacing: "Fast",                  // ALWAYS THE SAME
        emotional_trigger: "Excitement"  // ALWAYS THE SAME
    });
});

// ✅ SHOULD BE
app.post('/api/analyze', async (req, res) => {
    const { video_uri } = req.body;

    // Get video frames
    const frames = await extractKeyFrames(video_uri, 10);

    // Use Gemini Vision for real analysis
    const analysis = await gemini.generateContent({
        contents: [{
            role: 'user',
            parts: [
                ...frames.map(f => ({ inlineData: { mimeType: 'image/jpeg', data: f } })),
                { text: `Analyze this video ad:

                1. Hook Style: What technique opens the video?
                2. Pacing: How does energy flow through scenes?
                3. Visual Elements: What objects/people appear?
                4. Emotional Arc: What feelings does it evoke?
                5. CTR Prediction: Based on patterns, estimate performance.

                Be specific to THIS video, not generic.` }
            ]
        }],
        generationConfig: {
            responseMimeType: "application/json",
            responseSchema: VIDEO_ANALYSIS_SCHEMA
        }
    });

    res.json(analysis.response);
});
```

### Transform #3: Add RAG to Generation
```python
# ❌ CURRENT (orchestrator.py)
def generate_script(brief):
    return gemini.generate(f"Create an ad for {brief}")

# ✅ SHOULD BE
async def generate_script(brief):
    # 1. Find similar winning ads
    winners = await faiss_index.search(
        query=embed(brief),
        filter={"ctr": {"$gt": 0.05}},  # Only winners
        limit=5
    )

    # 2. Extract patterns from winners
    patterns = await gemini.generate(f"""
    Analyze these high-performing ads:
    {json.dumps(winners)}

    What patterns make them successful?
    - Hook techniques
    - Pain point framing
    - Transformation promises
    - CTA styles
    """)

    # 3. Generate with context
    script = await gemini.generate(f"""
    Create an ad for: {brief}

    Use these proven patterns:
    {patterns}

    Generate a script that:
    1. Opens with a hook matching the winning pattern
    2. Addresses pain points in the proven style
    3. Promises transformation like the winners
    4. Ends with a CTA style that converts
    """)

    return script
```

### Transform #4: Close the Feedback Loop
```python
# ❌ CURRENT: Data collected but never used
def track_performance(ad_id, impressions, clicks):
    db.insert({"ad_id": ad_id, "impressions": impressions, "clicks": clicks})
    # That's it. Data sits unused.

# ✅ SHOULD BE
async def track_performance(ad_id, impressions, clicks):
    ctr = clicks / impressions if impressions > 0 else 0

    # 1. Store performance
    db.insert({"ad_id": ad_id, "ctr": ctr, "timestamp": now()})

    # 2. Update Thompson Sampler
    variant_id = db.get_variant(ad_id)
    thompson_sampler.update(variant_id, reward=ctr)

    # 3. Check if retraining needed
    recent_samples = db.count_since(hours=24)
    if recent_samples >= 100:
        await trigger_xgboost_retrain()

    # 4. Update weights if significant change
    calibration = await calculate_calibration()
    if calibration.error > 0.1:
        await learning_service.update_weights()

    # 5. Flag winners for RAG index
    if ctr > 0.05:
        await faiss_index.add(ad_id, embed(ad_content))
```

---

## BEST PRACTICES CHECKLIST

### Prompting
- [ ] Every prompt includes "Think step by step"
- [ ] Every prompt uses structured output (JSON schema)
- [ ] Every prompt includes relevant examples (few-shot)
- [ ] Every prompt has a persona ("Act as a Meta Ads expert")

### AI Calls
- [ ] Use function calling for tool use
- [ ] Use streaming for long responses
- [ ] Cache repeated queries (5-min TTL)
- [ ] Fallback to simpler model on failure

### Decision Making
- [ ] No hardcoded thresholds (learn them)
- [ ] No keyword matching (use embeddings)
- [ ] No static weights (update from performance)
- [ ] Always explain reasoning (not just score)

### Feedback
- [ ] Every prediction is logged
- [ ] Every result is tracked back
- [ ] Models retrain on new data
- [ ] Weights calibrate continuously

---

## SUCCESS METRICS

| Metric | Current | Week 1 | Week 2 | Week 3 | Week 4 |
|--------|---------|--------|--------|--------|--------|
| SMART decisions | 44% | 55% | 85% | 90% | 95% |
| DUMB decisions | 44% | 35% | 10% | 5% | 0% |
| FAKE decisions | 12% | 0% | 0% | 0% | 0% |
| Feedback loops | 0 | 0 | 2 | 5 | 5 |
| RAG queries | 0 | 0 | 50% | 90% | 100% |
| Structured output | 0% | 20% | 80% | 100% | 100% |

---

## PRIORITY ORDER (If Time Limited)

If you can't do everything, do these in order:

1. **Day 1-2:** Wire real services (remove ALL mock data)
2. **Day 3-4:** Replace keyword matching with Gemini calls
3. **Day 5-6:** Add structured output to all AI calls
4. **Day 7-8:** Add RAG to generation
5. **Day 9-10:** Close one feedback loop (Meta → XGBoost)

**These 10 days transform the system from "fake AI" to "real AI"**

The remaining 20 days are optimization and scaling.

---

## FILES TO MODIFY (Priority Order)

```
WEEK 1 (Remove Fakes):
1. services/drive-intel/src/main.py           - Wire real scene detection
2. services/gateway-api/src/index.ts          - Fix /api/analyze, /api/metrics
3. scripts/meta_ads_library_pattern_miner.py  - Real market data
4. frontend/src/components/dashboard/AIInsights.tsx - Real insights

WEEK 2 (Make Smart):
5. services/gateway-api/src/services/scoring-engine.ts - AI scoring
6. services/titan-core/engines/ensemble.py    - Structured output
7. services/titan-core/orchestrator.py        - RAG integration
8. services/drive-intel/services/ranking.py   - Learned weights

WEEK 3 (Close Loops):
9. services/ml-service/src/ctr_model.py       - Retraining pipeline
10. services/ml-service/src/thompson_sampler.py - Connect to variants
11. services/gateway-api/src/services/learning-service.ts - Weight updates

WEEK 4 (Scale):
12. services/titan-core/engines/deep_video_intelligence.py - Full video analysis
13. services/meta-publisher/src/index.ts      - Real publishing
14. All services                              - Production hardening
```

---

## THE BOTTOM LINE

**Current System:** Makes videos, doesn't make decisions
**Target System:** AI decides what to create based on what works

**The difference:**
- Current: "Create a fitness ad" → Generic output
- Target: "Create a fitness ad" → Finds winning patterns → Generates variation → Tests → Learns → Improves

**In 30 days with 15 hours/day (450 hours), this is achievable.**
