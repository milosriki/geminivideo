# 🎬 VIDEO-EDIT vs GEMINIVIDEO: Comprehensive Feature Comparison

**Date:** 2025-12-02
**Purpose:** Compare the video-edit repository with geminivideo to identify missing features and advancements

---

## 📊 EXECUTIVE SUMMARY

After a comprehensive analysis of both repositories:

| Metric | video-edit | geminivideo |
|--------|------------|-------------|
| **Total Frontend Components** | 22 components | 23 components |
| **Total Backend Engines** | 15+ engines | ~8 services |
| **Video Editing Features** | Complete | Complete |
| **AI/ML Prediction System** | ✅ 8-Engine Ensemble | ❌ Missing |
| **TITAN System** | ✅ Full 4-Agent System | ❌ Missing |
| **Memory/Persistence** | ✅ Supabase + Firestore | ✅ Supabase + Firestore |
| **Smart Video Cutting** | ✅ SmartCutter | ❌ Missing |
| **VSL Pro Editing** | ✅ VSLProEditor | ❌ Missing |
| **Blueprint Generation** | ✅ BlueprintGenerator | ❌ Missing |
| **Prediction Visualization** | ✅ PredictionPanel | ❌ Missing |

### Key Finding
**video-edit is significantly more advanced** with a complete TITAN AI system for video ad optimization, while geminivideo focuses on core video editing with Gemini AI integration.

---

## 🔴 FEATURES MISSING IN GEMINIVIDEO

### 1. **TITAN Types & Data Structures**

**video-edit has these advanced types that geminivideo lacks:**

```typescript
// ❌ MISSING in geminivideo - TITAN Deep Video Analysis
export interface TitanVideoAnalysis {
  video_id: string;
  hook: {
    hook_type: string;
    hook_text?: string;
    effectiveness_score: number;
    reasoning: string;
  };
  scenes: Array<{
    timestamp: string;
    description: string;
    energy_level: string;
  }>;
  overall_energy: string;
  pacing: string;
  transformation?: {
    before_state: string;
    after_state: string;
    transformation_type: string;
    believability_score: number;
  };
  emotional_triggers: string[];
  visual_elements: string[];
  has_voiceover: boolean;
  has_music: boolean;
  transcription?: string;
  key_phrases: string[];
  cta_type?: string;
  cta_strength: number;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  similar_to_winning_patterns: string[];
}

// ❌ MISSING in geminivideo - 8-Engine ROAS Prediction
export interface TitanPrediction {
  video_id: string;
  final_score: number;
  roas_prediction: {
    predicted_roas: number;
    confidence_lower: number;
    confidence_upper: number;
    confidence_level: 'low' | 'medium' | 'high';
  };
  engine_predictions: Array<{
    engine_name: string;
    score: number;
    confidence: number;
    reasoning: string;
  }>;
  hook_score: number;
  cta_score: number;
  engagement_score: number;
  conversion_score: number;
  overall_confidence: number;
  reasoning: string;
  compared_to_avg: number;
  recommendations: string[];
}

// ❌ MISSING in geminivideo - Ad Blueprint Structure
export interface TitanBlueprint {
  id: string;
  title: string;
  hook_text: string;
  hook_type: string;
  scenes: Array<{
    scene_number: number;
    duration_seconds: number;
    visual_description: string;
    audio_description: string;
    text_overlay?: string;
    transition?: string;
  }>;
  cta_text: string;
  cta_type: string;
  caption: string;
  hashtags: string[];
  target_avatar: string;
  emotional_triggers: string[];
  predicted_roas?: number;
  confidence_score?: number;
  rank?: number;
}

// ❌ MISSING in geminivideo - Knowledge Pattern System
export interface TitanKnowledgePattern {
  id: string;
  pattern_type: 'hook' | 'trigger' | 'structure' | 'cta' | 'transformation';
  pattern_value: string;
  performance_data: {
    avg_roas?: number;
    effectiveness?: number;
    best_platform?: string;
    usage_frequency?: number;
  };
  source: 'historical' | 'campaign' | 'manual';
}
```

---

### 2. **SmartCutter Component** ❌ Missing in geminivideo

**Location in video-edit:** `components/SmartCutter.tsx` (318 lines)

**Features:**
- AI-powered video cutting with key moment detection
- Timeline with color-coded markers (hook, problem, solution, proof, transformation, CTA)
- Automatic cut suggestions for 15s, 30s, 60s versions
- Visual timeline with drag-and-seek functionality
- One-click export for optimized cuts

**Key Functionality:**
```typescript
const MARKER_COLORS: Record<string, string> = {
  hook: '#ef4444',           // Red
  problem: '#f59e0b',        // Amber
  solution: '#10b981',       // Emerald
  proof: '#3b82f6',          // Blue
  transformation: '#8b5cf6', // Purple
  cta: '#ec4899',            // Pink
};

interface CutSuggestion {
  duration: number;
  start_time: number;
  end_time: number;
  key_moments: { time: number; type: string; note: string }[];
  reasoning: string;
}
```

**Why It's Advanced:**
- Uses TITAN API to identify optimal cut points based on engagement metrics
- Provides reasoning for each suggested cut
- Supports multiple duration targets (15s for TikTok, 30s for Reels, 60s for YouTube Shorts)

---

### 3. **VSLProEditor Component** ❌ Missing in geminivideo

**Location in video-edit:** `components/VSLProEditor.tsx` (685 lines)

**Features:**
- Professional Video Sales Letter editing workflow
- VSL Section Markers (Hook, Problem, Solution, Testimonial, CTA, Custom)
- Quick Edit operations panel
- Timeline-based marker visualization
- Section-by-section organization

**Key Functionality:**
```typescript
type VSLSection = 'hook' | 'problem' | 'solution' | 'testimonial' | 'cta' | 'custom';

interface VSLMarker {
  id: string;
  type: VSLSection;
  startTime: string;
  endTime: string;
  label: string;
}

const sectionLabels: Record<VSLSection, string> = {
  hook: '🎣 Hook',
  problem: '😰 Problem',
  solution: '✨ Solution',
  testimonial: '👤 Testimonial',
  cta: '🚀 CTA',
  custom: '📌 Custom',
};
```

**Why It's Advanced:**
- Purpose-built for Video Sales Letters (VSLs) - a specific marketing video format
- Allows non-technical users to structure videos according to proven sales formulas
- Integrates with the same editing operations as AdvancedEditor

---

### 4. **8-Engine Ensemble Prediction Service** ❌ Missing in geminivideo

**Location in video-edit:** `services/predictionService.ts` (195 lines)

**Features:**
- 8 different ML models for prediction:
  - DeepFM (Deep Learning)
  - DCN - Deep & Cross Network (Deep Learning)
  - XGBoost (Gradient Boosting)
  - LightGBM (Gradient Boosting)
  - CatBoost (Gradient Boosting)
  - NeuralNet (Deep Learning)
  - RandomForest (Ensemble)
  - GradientBoost (Gradient Boosting)

**Key Functionality:**
```typescript
const ENGINE_COLORS: Record<string, string> = {
  DeepFM: '#6366f1',        // Indigo
  DCN: '#8b5cf6',           // Purple
  XGBoost: '#10b981',       // Emerald
  LightGBM: '#14b8a6',      // Teal
  CatBoost: '#f59e0b',      // Amber
  NeuralNet: '#ec4899',     // Pink
  RandomForest: '#3b82f6',  // Blue
  GradientBoost: '#84cc16', // Lime
};

export interface PredictionDisplayData {
  finalScore: number;
  predictedRoas: number;
  confidenceLevel: 'low' | 'medium' | 'high';
  confidenceRange: { lower: number; upper: number };
  hookScore: number;
  ctaScore: number;
  engagementScore: number;
  conversionScore: number;
  comparedToAvg: number;
  engines: EngineDisplayData[];
  reasoning: string;
  recommendations: string[];
  similarCampaigns: { name: string; roas: number; similarity: number }[];
}
```

**Why It's Advanced:**
- Provides quantitative ROAS predictions with confidence intervals
- Combines multiple ML model types for more accurate predictions
- Shows which engine contributed most to the prediction
- Provides actionable recommendations based on prediction gaps

---

### 5. **Memory Service with Supabase** ❌ Missing in geminivideo

**Location in video-edit:** `services/memoryService.ts` (227 lines)

**Features:**
- Historical Campaign Management
- Analyzed Videos Persistence
- Chat Memory Storage
- Knowledge Base Pattern Storage
- Blueprint Storage
- Dashboard Statistics Aggregation

**Key Functionality:**
```typescript
export interface HistoricalCampaign {
  id: string;
  campaign_name: string;
  spend: number;
  revenue: number;
  roas: number;
  ctr: number;
  cvr: number;
  hook_text?: string;
  hook_type?: string;
  cta_text?: string;
  emotional_triggers?: string[];
  target_avatar?: string;
  platform?: string;
  features?: Record<string, any>;
  created_at: string;
}

// Key methods:
// - getHistoricalCampaigns()
// - getTopPerformers()
// - getAnalyzedVideos()
// - saveVideoAnalysis()
// - getChatHistory()
// - saveConversation()
// - getPatterns()
// - addPattern()
// - getBlueprints()
// - saveBlueprint()
// - getDashboardStats()
```

**Why It's Advanced:**
- Full persistence layer for learning from past campaigns
- Enables AI to reference historical winners when generating new content
- Tracks what patterns worked best over time

---

### 6. **TITAN API Service** ❌ Missing in geminivideo

**Location in video-edit:** `services/titanApi.ts` (375 lines)

**Features - 4 Agent System:**

1. **ANALYST Agent** - Video Analysis
   - `analyzeVideo(videoUri, filename)` - Deep video analysis
   - `compareToHistorical(videoId)` - Compare with winners

2. **ORACLE Agent** - Prediction
   - `predict(features, videoId)` - 8-engine ensemble prediction
   - `explainPrediction(videoId)` - Explain why score is what it is
   - `getEngineInfo()` - Get engine weights and baselines

3. **DIRECTOR Agent** - Blueprint Generation
   - `generateBlueprints(params)` - Generate 50 ad variations
   - `generateHooks(baseHook, targetAvatar, numVariations)` - Generate hook variations
   - `generateCuts(videoId, targetDurations)` - AI-powered cut suggestions

4. **CHAT Agent** - Conversational AI
   - `chat(message, conversationId, videoId)` - Natural language interaction
   - `getProactiveInsights(userId)` - AI-initiated recommendations
   - `getChatSummary(conversationId)` - Summarize conversation

**Why It's Advanced:**
- Multi-agent architecture for specialized tasks
- Full API for backend integration
- Proactive insights - AI reaches out to users with recommendations

---

### 7. **BlueprintGenerator Component** ❌ Missing in geminivideo

**Location in video-edit:** `components/BlueprintGenerator.tsx` (361 lines)

**Features:**
- Generate 5, 10, 25, or 50 ad variations
- Rank by predicted ROAS
- Visual blueprint cards with hook, scenes, CTA
- Copy-to-clipboard functionality
- Platform-specific generation (Reels, Shorts, TikTok, Feed)
- Tone selection (Direct, Empathetic, Authoritative, Playful, Inspirational)

**Why It's Advanced:**
- Automates the creative process
- Uses historical data to predict which variations will perform best
- Provides ready-to-use captions and hashtags

---

### 8. **PredictionPanel Component** ❌ Missing in geminivideo

**Location in video-edit:** `components/PredictionPanel.tsx` (192 lines)

**Features:**
- Visual display of 8-engine ensemble predictions
- Score bars for Hook, CTA, Engagement, Conversion
- Engine-by-engine breakdown with confidence
- AI reasoning text
- Similar campaign comparison
- Status badges (Excellent, Good, Average, Poor)

**Why It's Advanced:**
- Makes complex ML predictions understandable
- Shows confidence intervals for predictions
- Compares to historical baselines

---

### 9. **Backend Engines** ❌ Missing in geminivideo

**Location in video-edit:** `backend_core/engines/`

**15 specialized engines:**
| Engine | Purpose | File |
|--------|---------|------|
| `deep_ctr.py` | Deep CTR prediction (DeepFM, DCN) | 7,206 lines |
| `deep_video_intelligence.py` | Advanced video understanding | 4,431 lines |
| `ensemble.py` | 8-engine ensemble orchestration | 8,687 lines |
| `meta_ads.py` | Meta Ads API integration | 7,475 lines |
| `claude.py` | Claude AI integration | 1,091 lines |
| `gpt.py` | GPT integration | 827 lines |
| `llama.py` | Llama integration | 878 lines |
| `vertex_vision.py` | Google Vertex AI Vision | 1,370 lines |
| `video_agent.py` | Video agent core | 1,202 lines |
| `transformation.py` | Transformation detection | 774 lines |
| `roas.py` | ROAS calculation | 704 lines |
| `google_ads.py` | Google Ads integration | 696 lines |
| `ga4.py` | GA4 analytics integration | 1,004 lines |
| `fitness_form.py` | Fitness form analysis | 1,095 lines |
| `base.py` | Base engine class | 549 lines |

**Total: ~37,000 lines of backend engine code**

---

### 10. **KnowledgeBase Component** ❌ Missing in geminivideo

**Location in video-edit:** `components/KnowledgeBase.tsx` (280 lines)

**Features:**
- Display winning patterns (hooks, triggers, CTAs, structures)
- Add custom insights from campaigns
- Performance data visualization
- Pattern categorization

---

### 11. **ProactiveInsights Component** ❌ Missing in geminivideo

**Location in video-edit:** `components/ProactiveInsights.tsx` (158 lines)

**Features:**
- AI-initiated recommendations
- Priority-based insight cards
- Action suggestions
- Related video links

---

## ✅ FEATURES PRESENT IN BOTH REPOSITORIES

| Feature | video-edit | geminivideo |
|---------|------------|-------------|
| **Video Processing** |
| FFmpeg.wasm processing | ✅ | ✅ |
| Trim/Cut | ✅ | ✅ |
| Text Overlays | ✅ | ✅ |
| Image Overlays | ✅ | ✅ |
| Speed Adjustment | ✅ | ✅ |
| Visual Filters | ✅ | ✅ |
| Color Grading | ✅ | ✅ |
| Volume Control | ✅ | ✅ |
| Fade Effects | ✅ | ✅ |
| Aspect Ratio Crop | ✅ | ✅ |
| Subtitles | ✅ | ✅ |
| Mute Audio | ✅ | ✅ |
| **Components** |
| AdvancedEditor | ✅ | ✅ |
| VideoEditor | ✅ | ✅ |
| VideoGenerator | ✅ | ✅ |
| VideoPlayer | ✅ | ✅ |
| AdWorkflow | ✅ | ✅ |
| AudioSuite | ✅ | ✅ |
| AudioCutterDashboard | ✅ | ✅ |
| ImageSuite | ✅ | ✅ |
| StoryboardStudio | ✅ | ✅ |
| PerformanceDashboard | ✅ | ✅ |
| Assistant | ✅ | ✅ |
| CreatorDashboard | ✅ | ✅ |
| AnalysisResultCard | ✅ | ✅ |
| ErrorBoundary | ✅ | ✅ |
| **Services** |
| geminiService | ✅ | ✅ |
| googleDriveService | ✅ | ✅ |
| firestoreService | ✅ | ✅ |
| supabaseClient | ✅ | ✅ |
| apiClient | ✅ | ✅ |
| videoProcessor | ✅ | ✅ |
| **Utilities** |
| audio.ts | ✅ | ✅ |
| video.ts | ✅ | ✅ |
| error.ts | ✅ | ✅ |
| files.ts | ✅ | ✅ |
| supabase.ts | ✅ | ✅ |

---

## 📈 ADVANCEMENT ANALYSIS

### How video-edit is MORE Advanced:

1. **Full TITAN AI System** (4 agents: Analyst, Oracle, Director, Chat)
   - geminivideo has basic Gemini integration
   - video-edit has a complete multi-agent system

2. **8-Engine ML Prediction**
   - geminivideo has no ROAS prediction
   - video-edit predicts performance before publishing

3. **Historical Learning**
   - geminivideo doesn't learn from past campaigns
   - video-edit tracks what works and improves over time

4. **Smart Video Cutting**
   - geminivideo has manual cutting only
   - video-edit suggests optimal cuts based on AI analysis

5. **VSL-Specific Workflow**
   - geminivideo is general-purpose
   - video-edit has purpose-built tools for sales videos

6. **Blueprint Generation**
   - geminivideo generates one ad at a time
   - video-edit generates 50 variations ranked by predicted ROAS

7. **Knowledge Base**
   - geminivideo doesn't store winning patterns
   - video-edit builds a library of what works

8. **Proactive AI**
   - geminivideo AI is reactive (responds to requests)
   - video-edit AI is proactive (suggests optimizations)

### Areas Where geminivideo is Equal:

1. **Core Video Editing** - Same 11 editing operations
2. **Frontend Components** - Similar component architecture
3. **Video Processing** - Same FFmpeg.wasm implementation
4. **Gemini Integration** - Both use Google Gemini AI
5. **Google Drive Integration** - Both can fetch videos from Drive

### Areas Where geminivideo is Different (not necessarily worse):

1. **Simpler Architecture** - Easier to understand and maintain
2. **More Focused** - Does video editing without complex ML
3. **Lower Infrastructure Cost** - No 8-engine ensemble to run

---

## 🎯 RECOMMENDATIONS

### To Match video-edit Capabilities, geminivideo Needs:

1. **Add TITAN Types** (Priority: HIGH)
   - Add TitanVideoAnalysis, TitanPrediction, TitanBlueprint, TitanKnowledgePattern to types.ts

2. **Add SmartCutter Component** (Priority: HIGH)
   - AI-powered video cutting with key moment detection

3. **Add Prediction Service** (Priority: MEDIUM)
   - Start with 2-3 engines (XGBoost, NeuralNet)
   - Add more engines later

4. **Add Memory Service** (Priority: MEDIUM)
   - Track historical campaign performance
   - Store analyzed videos persistently

5. **Add Blueprint Generator** (Priority: MEDIUM)
   - Generate multiple ad variations
   - Rank by predicted ROAS

6. **Add TITAN API** (Priority: HIGH)
   - Backend API for the 4-agent system

7. **Add VSLProEditor** (Priority: LOW)
   - Only if targeting VSL market

8. **Add Knowledge Base** (Priority: LOW)
   - Start storing winning patterns

---

## 📋 MISSING FEATURES SUMMARY

| Feature | Lines of Code | Complexity | Priority |
|---------|---------------|------------|----------|
| TitanTypes in types.ts | ~100 | Low | HIGH |
| SmartCutter.tsx | 318 | Medium | HIGH |
| predictionService.ts | 195 | Medium | HIGH |
| memoryService.ts | 227 | Medium | MEDIUM |
| titanApi.ts | 375 | High | HIGH |
| BlueprintGenerator.tsx | 361 | Medium | MEDIUM |
| PredictionPanel.tsx | 192 | Low | MEDIUM |
| VSLProEditor.tsx | 685 | High | LOW |
| KnowledgeBase.tsx | 280 | Low | LOW |
| ProactiveInsights.tsx | 158 | Low | LOW |
| Backend Engines | ~37,000 | Very High | HIGH |

**Total Missing Code: ~40,000+ lines**

---

## ✅ CONCLUSION

**video-edit is significantly more advanced** than geminivideo in terms of:
- AI/ML prediction capabilities
- Historical learning and optimization
- Smart video cutting
- Blueprint generation
- Multi-agent architecture

**geminivideo is simpler and more focused**, which may be appropriate depending on use case.

**To achieve feature parity**, geminivideo would need:
- ~40,000 lines of new code
- 8-engine ML infrastructure
- Supabase schema for memory
- TITAN API backend

**Recommended approach**: Incrementally add the highest-value features (SmartCutter, Prediction, TITAN API) rather than trying to port everything at once.

---

## 🔬 DETAILED BACKEND FUNCTIONS ANALYSIS

### TITAN 4-Agent System (Backend Core)

The video-edit repository has a complete AI agent architecture in `backend_core/agents/`:

---

### 1. **AnalystAgent** (`analyst_agent.py` - 11,511 bytes)

**Purpose:** Deep video intelligence - extract actionable insights from video content

**Key Classes & Functions:**

```python
class SceneAnalysis:
    timestamp: str           # MM:SS format
    description: str         # Scene description
    energy_level: str        # low, medium, high
    key_objects: List[str]   # Detected objects

class HookAnalysis:
    hook_type: str           # Visual Shock, Question, Story, Statistic, etc.
    hook_text: Optional[str] # Text in hook
    effectiveness_score: int # 1-10 rating
    reasoning: str           # Why it works/doesn't

class TransformationAnalysis:
    before_state: str        # Before description
    after_state: str         # After description
    transformation_type: str # physical, emotional, lifestyle, financial
    believability_score: int # 1-10 rating

class VideoDeepAnalysis:
    video_id: str
    duration_seconds: float
    hook: HookAnalysis
    scenes: List[SceneAnalysis]
    overall_energy: str      # low, medium, high, dynamic
    pacing: str              # slow, moderate, fast, variable
    transformation: Optional[TransformationAnalysis]
    emotional_triggers: List[str]
    visual_elements: List[str]
    has_voiceover: bool
    has_music: bool
    transcription: Optional[str]
    key_phrases: List[str]
    cta_type: Optional[str]
    cta_strength: int
    summary: str
    strengths: List[str]
    weaknesses: List[str]
    similar_to_winning_patterns: List[str]

class AnalystAgent:
    def analyze_video(video_uri, historical_patterns) -> VideoDeepAnalysis
    def extract_features_for_prediction(analysis) -> Dict[str, Any]
    def compare_to_historical(analysis, top_performers) -> Dict[str, Any]
```

**Key Features:**
- First 3-second hook analysis
- Scene-by-scene energy detection
- Before/after transformation detection
- Emotional trigger identification
- Audio analysis (voiceover, music, transcription)
- Pattern matching against historical winners

---

### 2. **DirectorAgent** (`director_agent.py` - 19,407 bytes)

**Purpose:** Create winning ad scripts using Gemini 2.0 Flash with Reflexion Loop

**Key Classes & Functions:**

```python
class SceneBlueprint:
    scene_number: int
    duration_seconds: float
    visual_description: str
    audio_description: str
    text_overlay: Optional[str]
    transition: Optional[str]

class AdBlueprint:
    id: str
    title: str
    hook_text: str
    hook_type: str           # pattern_interrupt, question, statistic, story, transformation
    scenes: List[SceneBlueprint]
    cta_text: str
    cta_type: str            # book_call, download, buy_now, learn_more
    caption: str             # Social media caption
    hashtags: List[str]
    target_avatar: str
    emotional_triggers: List[str]
    predicted_roas: Optional[float]
    confidence_score: Optional[float]
    rank: Optional[int]
    source_video_id: Optional[str]
    based_on_pattern: Optional[str]

class DirectorAgentV2:
    # 12 Hook Templates built-in:
    hook_templates = [
        {"type": "pattern_interrupt", "template": "STOP scrolling if you {pain_point}"},
        {"type": "question", "template": "What if you could {desire} in just {timeframe}?"},
        {"type": "statistic", "template": "{stat_number}% of {avatar} struggle with {pain_point}"},
        {"type": "story", "template": "I used to {pain_point}. Then I discovered..."},
        {"type": "transformation", "template": "From {before} to {after} in {timeframe}"},
        # + 7 more templates
    ]
    
    async def generate_blueprints(request) -> List[AdBlueprint]
    async def _generate_initial_variations(request) -> List[AdBlueprint]
    async def _reflexion_loop(blueprints, request) -> List[AdBlueprint]  # Self-critique
    def _rank_blueprints(blueprints) -> List[AdBlueprint]
    async def generate_hook_variations(base_hook, target_avatar, num=50) -> List[Dict]
```

**Key Features:**
- Generate 10-50 ad blueprint variations
- Reflexion Loop: AI self-critiques and improves
- RAG integration with historical winners
- Scene-by-scene script generation
- Platform-specific optimization (Reels, TikTok, Shorts)
- Hook variation generation (50+ from single base)

---

### 3. **OracleAgent** (`oracle_agent.py` - 19,202 bytes)

**Purpose:** 8-Engine Ensemble Prediction for ROAS before spending money

**Key Classes & Functions:**

```python
class EnginePrediction:
    engine_name: str
    score: float             # 0-1 prediction
    confidence: float        # 0-1 confidence
    reasoning: str

class ROASPrediction:
    predicted_roas: float
    confidence_lower: float  # 95% CI lower
    confidence_upper: float  # 95% CI upper
    confidence_level: str    # low, medium, high

class EnsemblePredictionResult:
    video_id: str
    final_score: float       # 0-100 virality score
    roas_prediction: ROASPrediction
    engine_predictions: List[EnginePrediction]
    hook_score: float        # 0-10
    cta_score: float         # 0-10
    engagement_score: float  # 0-10
    conversion_score: float  # 0-10
    overall_confidence: float
    reasoning: str
    compared_to_avg: float   # % above/below historical average
    similar_campaigns: List[Dict]
    recommendations: List[str]

class OracleAgent:
    # Engine weights from historical $2M data
    engine_weights = {
        "DeepFM": 0.15,
        "DCN": 0.15,
        "XGBoost": 0.15,
        "LightGBM": 0.12,
        "CatBoost": 0.12,
        "NeuralNet": 0.12,
        "RandomForest": 0.10,
        "GradientBoost": 0.09
    }
    
    # Historical baselines
    historical_avg_roas = 2.4
    historical_avg_ctr = 0.024
    historical_avg_cvr = 0.031
    
    async def predict(features, video_id) -> EnsemblePredictionResult
    async def _run_all_engines(features) -> List[EnginePrediction]
    def _predict_roas(final_score, features) -> ROASPrediction
    def _generate_recommendations(hook, cta, engagement, features) -> List[str]
    def _find_similar_campaigns(features) -> List[Dict]
```

**Key Features:**
- 8 ML models for prediction
- Weighted ensemble scoring
- ROAS prediction with confidence intervals
- Comparison to $2M historical data
- Automatic recommendation generation

---

### 4. **ChatAgent** (`chat_agent.py` - 13,873 bytes)

**Purpose:** Proactive conversational AI with persistent memory

**Key Classes & Functions:**

```python
class ChatMessage:
    role: str                # user or assistant
    content: str
    timestamp: datetime
    metadata: Optional[Dict]

class ProactiveInsight:
    insight_type: str        # performance, optimization, trend, warning
    title: str
    description: str
    action: Optional[str]    # Suggested action
    priority: str            # low, medium, high, urgent
    related_video_id: Optional[str]

class ConversationContext:
    conversation_id: str
    video_id: Optional[str]
    video_analysis: Optional[Dict]
    user_preferences: Dict
    historical_context: Dict
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: datetime

class ChatAgentV2:
    active_conversations: Dict[str, ConversationContext]  # Memory cache
    
    async def chat(message, conversation_id, video_id, video_analysis, user_context) -> ChatResponse
    async def get_proactive_insights(user_id, historical_data) -> List[ProactiveInsight]
    async def learn_preferences(conversation_id, preference_type, value) -> bool
    async def get_conversation_history(conversation_id, limit=50) -> List[ChatMessage]
    async def summarize_conversation(conversation_id) -> Optional[str]
```

**Key Features:**
- Persistent conversation memory
- Proactive insights generation
- User preference learning
- Video-aware context
- Conversation summarization

---

### Council of Titans (Ensemble System)

**Location:** `backend_core/engines/ensemble.py` (8,687 bytes)

```python
class CouncilOfTitans:
    """
    The Ultimate Ensemble (4 AI Models):
    1. Gemini 2.0 Flash (with extended reasoning) - 40%
    2. GPT-4o (Logic/Structure) - 20%
    3. Claude 3.5 Sonnet (Nuance/Psychology) - 30%
    4. DeepCTR (Data/Math) - 10%
    """
    
    async def get_gemini_critique(script) -> Dict  # 40% weight
    async def get_gpt4_critique(script) -> Dict    # 20% weight
    async def get_claude_critique(script) -> Dict  # 30% weight
    async def evaluate_script(script, visual_features) -> Dict
        # Returns weighted score + breakdown + APPROVE/REJECT verdict
```

---

### DeepCTR Engine (Real ML Model)

**Location:** `backend_core/engines/deep_ctr.py` (7,206 bytes)

```python
class DeepCTREngine:
    """
    Real DeepFM model trained on $2M ad data
    Features: has_transformation, has_urgency, has_offer, is_video
    """
    
    def __init__(model_path):
        # Loads trained PyTorch DeepFM model
        
    def predict_sync(video_data) -> float:
        # Returns 0-100 ROAS probability
        # Falls back to Gemini Zero-Shot if model unavailable
```

---

### Video Intelligence Service

**Location:** `backend_core/services/video_intelligence.py` (6,689 bytes)

```python
class VideoIntelligenceService:
    """
    Google Cloud Video Intelligence API integration
    """
    
    def analyze_faces(video_uri) -> List[Dict]:
        # Detects faces, emotions, bounding boxes
        # Returns: start_time, end_time, attributes, confidence
        
    def transcribe_video(video_uri, language="en-US") -> List[Dict]:
        # Full speech-to-text with word timestamps
        # Returns: transcript, confidence, words[]
        
    def detect_labels(video_uri) -> List[Dict]:
        # Objects, locations, activities
        # Returns: entity, category, timestamps, confidence
```

---

### Learning Loop (Continuous Improvement)

**Location:** `backend_core/services/learning_loop.py` (2,759 bytes)

```python
class LearningLoop:
    """
    Closes the feedback loop: When purchases happen,
    boost winning patterns in Vector Store
    """
    
    def process_purchase_signal(transaction_data):
        # Updates Vector Store embeddings with HIGH_CONVERSION tag
        # Makes future predictions smarter
```

---

### Knowledge Base (Federated Knowledge)

**Location:** `backend_core/knowledge/core.py` (2,232 bytes)

```python
class FederatedKnowledge:
    """
    Aggregates Hardcoded Rules + Live User Research
    """
    
    domains = {
        "fitness": {
            "hormozi_rules": [
                "0-3s: Pattern Interrupt (Visual Shock)",
                "3-10s: Agitate the Pain",
                "10-40s: The New Mechanism",
                "40-60s: Explicit CTA"
            ],
            "psychology": ["Status", "Sloth", "Fear"],
            "pain_points": [...]
        }
    }
    
    def inject_spy_data(data)       # Add competitor intelligence
    def add_user_research(niche, insight)  # Add user research
    def get_context_block(niche) -> str    # Build prompt context
```

---

## 🎯 PRIORITIZED FUNCTIONS TO PORT TO GEMINIVIDEO

### Tier 1: High Impact (Port First)

| Function | From File | Purpose | Effort |
|----------|-----------|---------|--------|
| `AnalystAgent.analyze_video()` | analyst_agent.py | Deep video analysis | Medium |
| `OracleAgent.predict()` | oracle_agent.py | ROAS prediction | High |
| `CouncilOfTitans.evaluate_script()` | ensemble.py | Multi-LLM scoring | Medium |
| `DirectorAgent.generate_blueprints()` | director_agent.py | Ad variation generation | High |

### Tier 2: Medium Impact

| Function | From File | Purpose | Effort |
|----------|-----------|---------|--------|
| `ChatAgentV2.get_proactive_insights()` | chat_agent.py | AI suggestions | Medium |
| `VideoIntelligenceService.*` | video_intelligence.py | GCP video analysis | Low |
| `DeepCTREngine.predict_sync()` | deep_ctr.py | ML prediction | High |
| `FederatedKnowledge.get_context_block()` | core.py | Context building | Low |

### Tier 3: Nice to Have

| Function | From File | Purpose | Effort |
|----------|-----------|---------|--------|
| `LearningLoop.process_purchase_signal()` | learning_loop.py | Continuous learning | Medium |
| `DirectorAgent.generate_hook_variations()` | director_agent.py | Hook diversification | Low |
| `ChatAgentV2.summarize_conversation()` | chat_agent.py | Chat summary | Low |

---

## 📋 FUNCTION-BY-FUNCTION PORTING CHECKLIST

```
Backend Agents:
[ ] AnalystAgent - VideoDeepAnalysis type + analyze_video()
[ ] OracleAgent - EnsemblePredictionResult + 8-engine predict()
[ ] DirectorAgent - AdBlueprint + generate_blueprints() + hook_templates
[ ] ChatAgent - ConversationContext + persistent memory

Backend Engines:
[ ] CouncilOfTitans - Multi-LLM evaluation (Gemini + GPT-4 + Claude + DeepCTR)
[ ] DeepCTREngine - Real ML model with Gemini fallback
[ ] EnsemblePredictor - 8-engine prediction system

Backend Services:
[ ] VideoIntelligenceService - GCP Video API
[ ] LearningLoop - Purchase signal processing
[ ] FederatedKnowledge - Context building

Frontend Components:
[ ] SmartCutter - AI video cutting
[ ] VSLProEditor - VSL section markers
[ ] BlueprintGenerator - Ad variation UI
[ ] PredictionPanel - 8-engine visualization
[ ] AIAssistant - Enhanced chat with memory
[ ] ProactiveInsights - AI suggestions panel
```

---

## 💡 QUICK WINS TO START

1. **Copy Types** - Add TitanVideoAnalysis, TitanPrediction, TitanBlueprint to `frontend/src/types.ts`

2. **Port SmartCutter** - Copy `SmartCutter.tsx` to geminivideo components (works standalone)

3. **Add Prediction Service** - Port `predictionService.ts` for score visualization

4. **Deploy TITAN API** - Set up `backend_core/` as separate Python service

5. **Connect Memory** - Extend Supabase schema with `analyzed_videos`, `ad_blueprints` tables
