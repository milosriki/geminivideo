# RAG Knowledge Collection Logic
## How Our RAG System Collects All Knowledge - Best Practices

**Date:** 2025-12-09  
**Question:** How does our RAG collect all knowledge? What's the best logic?

---

## 🔍 CURRENT RAG SYSTEM ANALYSIS

### 1. Winner Index (RAG Core)

**File:** `services/rag/winner_index.py`  
**File:** `services/ml-service/src/winner_index.py`

**Current Logic:**
- Stores winning ad patterns in FAISS vector store
- Backed by GCS for persistence
- Embedding-based semantic search
- Winner detection based on performance thresholds

**What It Collects:**
- Winning ad patterns (CTR > threshold, ROAS > threshold)
- Creative DNA patterns
- Performance metrics
- Embeddings for semantic search

---

### 2. Knowledge Base System

**File:** `services/gateway-api/src/knowledge.ts`  
**File:** `services/titan-core/knowledge/`

**Current Logic:**
- Upload knowledge to GCS
- Category-based organization
- Version control
- Hot-reload capabilities

**What It Collects:**
- Brand guidelines
- Competitor analysis
- Industry benchmarks
- Hook templates
- Storyboard templates
- Winning patterns

---

### 3. Self-Learning Loops

**File:** `services/gateway-api/src/workers/self-learning-cycle.ts`

**Current Logic:**
- 7 self-learning loops
- RAG Winner Index loop
- Creative DNA extraction
- Cross-learner
- Compound learner

**What It Collects:**
- Winner patterns from campaigns
- Creative DNA from high-performers
- Cross-account learnings
- Compound improvements

---

## 🎯 BEST LOGIC FOR KNOWLEDGE COLLECTION

### 1. Multi-Source Knowledge Collection

**Like Meta's GEM - Learn from All Sources:**

```python
class ComprehensiveKnowledgeCollector:
    """
    Collects knowledge from all sources, like Meta's GEM learns from all ads.
    """
    
    def __init__(self):
        self.sources = {
            'internal': InternalKnowledgeSource(),
            'external': ExternalKnowledgeSource(),
            'competitors': CompetitorKnowledgeSource(),
            'industry': IndustryKnowledgeSource(),
            'foundation': FoundationKnowledgeSource()
        }
    
    def collect_all_knowledge(self) -> KnowledgeBase:
        """
        Collect knowledge from all sources.
        """
        knowledge = KnowledgeBase()
        
        # 1. Internal: Our own winners
        internal = self.sources['internal'].collect()
        knowledge.add(internal, source='internal', weight=1.0)
        
        # 2. External: Competitor ads (Meta Ads Library, Foreplay)
        external = self.sources['external'].collect()
        knowledge.add(external, source='external', weight=0.8)
        
        # 3. Competitors: Direct competitor analysis
        competitors = self.sources['competitors'].collect()
        knowledge.add(competitors, source='competitors', weight=0.7)
        
        # 4. Industry: Benchmarks and standards
        industry = self.sources['industry'].collect()
        knowledge.add(industry, source='industry', weight=0.6)
        
        # 5. Foundation: General marketing knowledge
        foundation = self.sources['foundation'].collect()
        knowledge.add(foundation, source='foundation', weight=0.5)
        
        return knowledge
```

---

### 2. Intelligent Winner Detection

**Not Just Thresholds - Multi-Factor Winner Detection:**

```python
class IntelligentWinnerDetection:
    """
    Detect winners using multiple factors, not just thresholds.
    """
    
    def is_winner(
        self,
        ad: Ad,
        context: CampaignContext
    ) -> Tuple[bool, float]:
        """
        Determine if ad is a winner using multiple factors.
        """
        factors = {
            'roi': self._calculate_roi_score(ad, context),
            'roas': self._calculate_roas_score(ad, context),
            'ctr': self._calculate_ctr_score(ad, context),
            'scale': self._calculate_scale_score(ad, context),
            'consistency': self._calculate_consistency_score(ad, context),
            'trend': self._calculate_trend_score(ad, context)
        }
        
        # Weighted combination (not hardcoded thresholds)
        weights = self._get_weights_for_context(context)
        
        total_score = sum(
            factors[factor] * weights[factor]
            for factor in factors
        )
        
        # Dynamic threshold based on context
        threshold = self._get_dynamic_threshold(context)
        
        is_winner = total_score >= threshold
        
        return is_winner, total_score
    
    def _get_weights_for_context(self, context: CampaignContext) -> Dict:
        """
        Get weights based on budget scale and objective.
        Not hardcoded, but from knowledge base.
        """
        # Query knowledge base for weights
        weights = self.knowledge_base.query(
            f"winner detection weights for {context.budget_scale} "
            f"with {context.objective} objective"
        )
        
        return weights
```

---

### 3. Pattern Extraction and Storage

**Extract Patterns, Not Just Store Ads:**

```python
class PatternExtractor:
    """
    Extract patterns from winners, not just store the ads.
    Like Meta's GEM extracts general patterns.
    """
    
    def extract_patterns(self, winners: List[Ad]) -> List[Pattern]:
        """
        Extract general patterns from winners.
        """
        patterns = []
        
        # 1. Hook patterns
        hook_patterns = self._extract_hook_patterns(winners)
        patterns.extend(hook_patterns)
        
        # 2. Visual patterns
        visual_patterns = self._extract_visual_patterns(winners)
        patterns.extend(visual_patterns)
        
        # 3. Audio patterns
        audio_patterns = self._extract_audio_patterns(winners)
        patterns.extend(audio_patterns)
        
        # 4. Pacing patterns
        pacing_patterns = self._extract_pacing_patterns(winners)
        patterns.extend(pacing_patterns)
        
        # 5. Copy patterns
        copy_patterns = self._extract_copy_patterns(winners)
        patterns.extend(copy_patterns)
        
        # 6. CTA patterns
        cta_patterns = self._extract_cta_patterns(winners)
        patterns.extend(cta_patterns)
        
        # 7. ROI optimization patterns
        roi_patterns = self._extract_roi_patterns(winners)
        patterns.extend(roi_patterns)
        
        return patterns
    
    def _extract_roi_patterns(self, winners: List[Ad]) -> List[ROIPattern]:
        """
        Extract ROI optimization patterns from winners.
        """
        patterns = []
        
        # Group winners by ROI characteristics
        high_roi_winners = [w for w in winners if w.roi > 200]
        medium_roi_winners = [w for w in winners if 100 <= w.roi <= 200]
        
        # Extract patterns from each group
        for group_name, group_winners in [
            ('high_roi', high_roi_winners),
            ('medium_roi', medium_roi_winners)
        ]:
            # Extract common characteristics
            common_features = self._find_common_features(group_winners)
            
            # Create pattern
            pattern = ROIPattern(
                name=f"{group_name}_pattern",
                features=common_features,
                avg_roi=sum(w.roi for w in group_winners) / len(group_winners),
                sample_count=len(group_winners),
                confidence=self._calculate_confidence(group_winners)
            )
            
            patterns.append(pattern)
        
        return patterns
```

---

### 4. Semantic Search and Retrieval

**Intelligent Retrieval Based on Context:**

```python
class IntelligentRAGRetrieval:
    """
    Retrieve knowledge based on context, not just similarity.
    """
    
    def retrieve(
        self,
        query: str,
        context: CampaignContext
    ) -> List[Pattern]:
        """
        Retrieve relevant patterns based on query and context.
        """
        # 1. Semantic search (embedding-based)
        semantic_results = self.vector_store.search(
            query=query,
            top_k=50
        )
        
        # 2. Filter by context
        context_filtered = self._filter_by_context(
            semantic_results,
            context
        )
        
        # 3. Rank by relevance + performance
        ranked = self._rank_by_relevance_and_performance(
            context_filtered,
            context
        )
        
        # 4. Return top patterns
        return ranked[:10]
    
    def _filter_by_context(
        self,
        patterns: List[Pattern],
        context: CampaignContext
    ) -> List[Pattern]:
        """
        Filter patterns by budget scale and objective.
        """
        filtered = []
        
        for pattern in patterns:
            # Check if pattern is relevant for this context
            if self._is_relevant_for_context(pattern, context):
                filtered.append(pattern)
        
        return filtered
    
    def _is_relevant_for_context(
        self,
        pattern: Pattern,
        context: CampaignContext
    ) -> bool:
        """
        Check if pattern is relevant for this context.
        """
        # Check budget scale match
        if pattern.budget_scale and pattern.budget_scale != context.budget_scale:
            return False
        
        # Check objective match
        if pattern.objective and pattern.objective != context.objective:
            return False
        
        # Check industry match (if specified)
        if pattern.industry and pattern.industry != context.industry:
            return False
        
        return True
```

---

### 5. Continuous Learning Loop

**Learn from All Campaigns, Not Just Winners:**

```python
class ContinuousLearningLoop:
    """
    Continuous learning from all campaigns, not just winners.
    Like Meta's GEM learns from all ads.
    """
    
    def learn_from_campaign(self, campaign: Campaign):
        """
        Learn from campaign, whether winner or loser.
        """
        # 1. Extract patterns (winners and losers)
        winner_patterns = self._extract_winner_patterns(campaign)
        loser_patterns = self._extract_loser_patterns(campaign)
        
        # 2. Store winner patterns
        for pattern in winner_patterns:
            self.rag_index.add_pattern(pattern, label='winner')
        
        # 3. Store loser patterns (to avoid)
        for pattern in loser_patterns:
            self.rag_index.add_pattern(pattern, label='loser')
        
        # 4. Learn ROI optimization patterns
        roi_patterns = self._extract_roi_patterns(campaign)
        for pattern in roi_patterns:
            self.rag_index.add_pattern(pattern, label='roi_optimization')
        
        # 5. Update foundation model
        self.foundation_model.update(campaign)
    
    def _extract_loser_patterns(self, campaign: Campaign) -> List[Pattern]:
        """
        Extract patterns from losers (to avoid).
        """
        losers = [ad for ad in campaign.ads if ad.roi < 50]
        
        # Extract common characteristics of losers
        common_features = self._find_common_features(losers)
        
        # Create anti-patterns
        anti_patterns = [
            AntiPattern(
                name=f"loser_pattern_{i}",
                features=features,
                avg_roi=sum(ad.roi for ad in losers) / len(losers),
                avoid=True
            )
            for i, features in enumerate(common_features)
        ]
        
        return anti_patterns
```

---

## 🎯 BEST PRACTICES FOR OUR RAG SYSTEM

### 1. Multi-Source Collection

**Collect from:**
- ✅ Internal winners (our campaigns)
- ✅ External sources (Meta Ads Library, Foreplay, TikTok)
- ✅ Competitor analysis
- ✅ Industry benchmarks
- ✅ Foundation knowledge (general marketing)

**Weight by Source:**
- Internal: 1.0 (highest weight - our own data)
- External: 0.8 (competitor ads)
- Competitors: 0.7 (direct competitors)
- Industry: 0.6 (benchmarks)
- Foundation: 0.5 (general knowledge)

---

### 2. Intelligent Winner Detection

**Not Just Thresholds:**
- ✅ Multi-factor scoring (ROI, ROAS, CTR, scale, consistency, trend)
- ✅ Dynamic thresholds (based on context, not hardcoded)
- ✅ Weighted combination (from knowledge base, not hardcoded)
- ✅ Context-aware (budget scale, objective, industry)

---

### 3. Pattern Extraction

**Extract Patterns, Not Just Store:**
- ✅ Hook patterns
- ✅ Visual patterns
- ✅ Audio patterns
- ✅ Pacing patterns
- ✅ Copy patterns
- ✅ CTA patterns
- ✅ **ROI optimization patterns** (NEW - most important!)

---

### 4. Context-Aware Retrieval

**Retrieve Based on Context:**
- ✅ Semantic search (embedding-based)
- ✅ Context filtering (budget scale, objective, industry)
- ✅ Relevance + performance ranking
- ✅ Not just similarity, but context match

---

### 5. Continuous Learning

**Learn from All Campaigns:**
- ✅ Winner patterns (what to replicate)
- ✅ Loser patterns (what to avoid)
- ✅ ROI optimization patterns (how to optimize)
- ✅ Foundation model updates (general patterns)

---

## 🚀 IMPLEMENTATION PLAN

### Phase 1: Enhance Winner Detection
```python
# Current: Simple threshold
if ad.roi > 200:
    add_to_rag(ad)

# Better: Multi-factor intelligent detection
winner_score = calculate_winner_score(ad, context)
if winner_score > dynamic_threshold(context):
    extract_patterns(ad)
    add_to_rag(patterns)
```

### Phase 2: Multi-Source Collection
```python
# Current: Only internal winners
winners = get_internal_winners()

# Better: Multi-source collection
knowledge = collect_from_all_sources([
    'internal',
    'external',
    'competitors',
    'industry',
    'foundation'
])
```

### Phase 3: Pattern Extraction
```python
# Current: Store whole ads
rag_index.add(ad)

# Better: Extract patterns
patterns = extract_patterns(ad)
rag_index.add_patterns(patterns)
```

### Phase 4: Context-Aware Retrieval
```python
# Current: Simple similarity search
results = vector_store.search(query)

# Better: Context-aware retrieval
results = intelligent_retrieval(
    query=query,
    context=campaign_context,
    filters={
        'budget_scale': 'growth',
        'objective': 'roi'
    }
)
```

---

## ✅ RECOMMENDED LOGIC

### Best RAG Knowledge Collection Logic:

1. **Multi-Source Collection:**
   - Internal winners (weight: 1.0)
   - External sources (weight: 0.8)
   - Competitors (weight: 0.7)
   - Industry (weight: 0.6)
   - Foundation (weight: 0.5)

2. **Intelligent Winner Detection:**
   - Multi-factor scoring (not just thresholds)
   - Dynamic thresholds (from knowledge base)
   - Context-aware (budget scale, objective)

3. **Pattern Extraction:**
   - Extract patterns, not just store ads
   - ROI optimization patterns (most important)
   - Anti-patterns (what to avoid)

4. **Context-Aware Retrieval:**
   - Semantic search + context filtering
   - Rank by relevance + performance
   - Match budget scale and objective

5. **Continuous Learning:**
   - Learn from winners and losers
   - Update foundation model
   - Extract ROI optimization patterns

---

**This logic makes our RAG system like Meta's GEM - learns from all sources, extracts general patterns, works at all scales!** 🚀

