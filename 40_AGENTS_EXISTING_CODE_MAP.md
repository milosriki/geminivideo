# 🗺️ 40 Agents → Existing Code Mapping

## ✅ EXISTING IMPLEMENTATIONS FOUND

### **ML Service (`/services/ml-service/src/`)**

| Existing File | What It Does | 40-Agent Equivalent |
|---------------|--------------|---------------------|
| `semantic_cache.py` | Semantic caching | Agent 17: Cache Master |
| `cross_learner.py` | Cross-platform learning | Agent 21: The Learner |
| `precomputer.py` | Precomputation | Agent 45 (mentioned) |
| `self_learning.py` | Drift detection + learning | Agent 13: Sentinel + Agent 21 |
| `ctr_model.py` | CTR prediction | Agent 9: Prediction Master |
| `enhanced_ctr_model.py` | Enhanced CTR | Agent 9: Prediction Master |
| `thompson_sampler.py` | Thompson Sampling | Agent 10: Experimenter |
| `auto_scaler.py` | Auto-scaling | Agent 26: Optimizer |
| `battle_hardened_sampler.py` | Battle-hardened sampling | Agent 10: Experimenter |
| `creative_dna.py` | Creative DNA | Agent 20: DNA Analyst |
| `winner_index.py` | Winner index | Agent 24: Retriever |
| `vector_store.py` | Vector store | Agent 6: Vector Master |
| `compound_learner.py` | Compound learning | Agent 21: Learner |
| `time_optimizer.py` | Time optimization | Agent 27: Timer |
| `accuracy_tracker.py` | Accuracy tracking | Agent 15: Validator |

---

## 🔗 INTEGRATION INSTRUCTIONS

### **Agent 9: The Prediction Master**

**EXISTING:** `ctr_model.py`, `enhanced_ctr_model.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.ctr_model import ctr_predictor
from services.ml_service.src.enhanced_ctr_model import enhanced_ctr_predictor

class PredictionMasterAgent(BaseAgent):
    def __init__(self):
        # Use existing CTR models
        self.ctr_model = ctr_predictor
        self.enhanced_model = enhanced_ctr_predictor
        
    async def add_bayesian_layer(self):
        # EXTEND: Add Bayesian uncertainty to existing models
        # Don't recreate CTR prediction - enhance it
        pass
```

---

### **Agent 10: The Experimenter**

**EXISTING:** `thompson_sampler.py`, `battle_hardened_sampler.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.thompson_sampler import thompson_optimizer
from services.ml_service.src.battle_hardened_sampler import BattleHardenedSampler

class ExperimenterAgent(BaseAgent):
    def __init__(self):
        # Use existing samplers
        self.thompson = thompson_optimizer
        self.battle_hardened = BattleHardenedSampler()
        
    async def add_ucb_bandit(self):
        # EXTEND: Add UCB to existing Thompson Sampling
        # Don't recreate - enhance
        pass
```

---

### **Agent 13: The Sentinel (Drift Detection)**

**EXISTING:** `self_learning.py` (has drift detection)

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.self_learning import DriftDetector, DriftType

class SentinelAgent(BaseAgent):
    def __init__(self):
        # Use existing drift detector
        self.drift_detector = DriftDetector()
        
    async def add_ks_psi_tests(self):
        # EXTEND: Add KS/PSI tests to existing detector
        # Check self_learning.py for existing methods first
        pass
```

---

### **Agent 17: The Cache Master**

**EXISTING:** `semantic_cache.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.semantic_cache import SemanticCache

class CacheMasterAgent(BaseAgent):
    def __init__(self):
        # Use existing semantic cache
        self.cache = SemanticCache()
        
    async def enhance_cache(self):
        # EXTEND: Add embedding service, Redis vector search
        # Don't recreate semantic cache - enhance it
        pass
```

---

### **Agent 21: The Learner**

**EXISTING:** `cross_learner.py`, `compound_learner.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.cross_learner import CrossLearner
from services.ml_service.src.compound_learner import CompoundLearner

class LearnerAgent(BaseAgent):
    def __init__(self):
        # Use existing learners
        self.cross_learner = CrossLearner()
        self.compound_learner = CompoundLearner()
        
    async def add_validation_loop(self):
        # EXTEND: Add validation loop to existing learners
        # Don't recreate - enhance
        pass
```

---

### **Agent 24: The Retriever**

**EXISTING:** `winner_index.py`, `vector_store.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.winner_index import WinnerIndex
from services.ml_service.src.vector_store import VectorStore

class RetrieverAgent(BaseAgent):
    def __init__(self):
        # Use existing systems
        self.winner_index = WinnerIndex()
        self.vector_store = VectorStore()
        
    async def build_rag_system(self):
        # EXTEND: Build RAG on top of existing winner index
        # Don't recreate - enhance
        pass
```

---

### **Agent 26: The Optimizer**

**EXISTING:** `auto_scaler.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.auto_scaler import AutoScaler

class OptimizerAgent(BaseAgent):
    def __init__(self):
        # Use existing auto-scaler
        self.auto_scaler = AutoScaler()
        
    async def add_rl_optimization(self):
        # EXTEND: Add RL layer to existing auto-scaler
        # Don't recreate - enhance
        pass
```

---

### **Agent 27: The Timer**

**EXISTING:** `time_optimizer.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.time_optimizer import TimeOptimizer

class TimerAgent(BaseAgent):
    def __init__(self):
        # Use existing time optimizer
        self.time_optimizer = TimeOptimizer()
        
    async def add_daypart_optimization(self):
        # EXTEND: Add day-part optimization to existing
        # Don't recreate - enhance
        pass
```

---

### **Agent 20: The DNA Analyst**

**EXISTING:** `creative_dna.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.creative_dna import CreativeDNA

class DNAAnalystAgent(BaseAgent):
    def __init__(self):
        # Use existing Creative DNA
        self.creative_dna = CreativeDNA()
        
    async def add_temporal_decay(self):
        # EXTEND: Add temporal decay to existing DNA
        # Don't recreate - enhance
        pass
```

---

### **Agent 6: The Vector Master**

**EXISTING:** `vector_store.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.vector_store import VectorStore

class VectorMasterAgent(BaseAgent):
    def __init__(self):
        # Use existing vector store
        self.vector_store = VectorStore()
        
    async def add_faiss_enhancements(self):
        # EXTEND: Add FAISS enhancements to existing
        # Don't recreate - enhance
        pass
```

---

### **Agent 15: The Validator**

**EXISTING:** `accuracy_tracker.py`

**INTEGRATION:**
```python
# ✅ CORRECT: Import existing
from services.ml_service.src.accuracy_tracker import accuracy_tracker

class ValidatorAgent(BaseAgent):
    def __init__(self):
        # Use existing accuracy tracker
        self.tracker = accuracy_tracker
        
    async def add_confidence_intervals(self):
        # EXTEND: Add confidence intervals to existing tracker
        # Don't recreate - enhance
        pass
```

---

## 📋 MODIFIED AGENT INSTRUCTIONS TEMPLATE

For each agent, update instructions to:

1. **Check Existing Code First:**
   ```python
   # BEFORE writing code, check:
   # - services/ml-service/src/
   # - services/gateway-api/src/
   # - services/langgraph-app/src/
   ```

2. **Import Existing:**
   ```python
   # If system exists, import it
   from services.ml_service.src.existing_module import ExistingClass
   ```

3. **Extend, Don't Replace:**
   ```python
   # Add new methods to existing class
   # Or create wrapper that uses existing
   class EnhancedAgent(BaseAgent):
       def __init__(self):
           self.existing = ExistingClass()  # Use existing
           
       async def new_feature(self):
           # Add new functionality
           pass
   ```

---

## ✅ INTEGRATION CHECKLIST

Before implementing each agent:

- [ ] Search for existing implementation in `/services/ml-service/src/`
- [ ] Search for existing implementation in `/services/gateway-api/src/`
- [ ] Search for existing implementation in `/services/langgraph-app/src/`
- [ ] If found → Import and extend
- [ ] If not found → Create new
- [ ] Update agent instruction file with import statements
- [ ] Test integration with existing code

---

## 🎯 SUMMARY

**Out of 40 Agents:**
- **~15 agents** need to CREATE NEW (foundation, contracts, new features)
- **~20 agents** need to EXTEND EXISTING (most ML/learning features exist)
- **~5 agents** need to WIRE TO EXISTING (use as-is, no changes)

**Key Files to Import From:**
- `semantic_cache.py` → Agent 17
- `cross_learner.py` → Agent 21
- `self_learning.py` → Agent 13
- `ctr_model.py` → Agent 9
- `thompson_sampler.py` → Agent 10
- `auto_scaler.py` → Agent 26
- `creative_dna.py` → Agent 20
- `winner_index.py` → Agent 24
- `vector_store.py` → Agent 6
- `time_optimizer.py` → Agent 27

**Next Step:** I'll create modified agent instruction files that import from existing code.

