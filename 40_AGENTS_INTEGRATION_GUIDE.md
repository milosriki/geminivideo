# 🔗 40 Agents Integration Guide - EXTEND EXISTING CODE

## ⚠️ CRITICAL: DO NOT DUPLICATE

**All agents must CHECK for existing code FIRST, then EXTEND it.**

---

## 📋 EXISTING CODE LOCATIONS

### **ML Service (`/services/ml-service/src/`)**

| File | Purpose | Import Path |
|------|---------|-------------|
| `semantic_cache.py` | Semantic caching | `from src.semantic_cache import SemanticCache` |
| `cross_learner.py` | Cross-platform learning | `from src.cross_learner import CrossLearner` |
| `precomputer.py` | Precomputation | `from src.precomputer import get_precomputer` |
| `ctr_model.py` | CTR prediction | `from src.ctr_model import ctr_predictor` |
| `enhanced_ctr_model.py` | Enhanced CTR | `from src.enhanced_ctr_model import enhanced_ctr_predictor` |
| `thompson_sampler.py` | Thompson Sampling | `from src.thompson_sampler import thompson_optimizer` |
| `battle_hardened_sampler.py` | Battle-hardened sampling | `from src.battle_hardened_sampler import BattleHardenedSampler` |
| `auto_scaler.py` | Auto-scaling | `from src.auto_scaler import AutoScaler` |
| `creative_dna.py` | Creative DNA | `from src.creative_dna import CreativeDNA` |
| `winner_index.py` | Winner index | `from src.winner_index import WinnerIndex` |
| `vector_store.py` | Vector store | `from src.vector_store import VectorStore` |
| `compound_learner.py` | Compound learning | `from src.compound_learner import CompoundLearner` |
| `time_optimizer.py` | Time optimization | `from src.time_optimizer import TimeOptimizer` |
| `accuracy_tracker.py` | Accuracy tracking | `from src.accuracy_tracker import accuracy_tracker` |

### **Gateway API (`/services/gateway-api/src/`)**

| File | Purpose | Import Path |
|------|---------|-------------|
| `middleware/error-handler.ts` | Circuit breaker | `import { CircuitBreaker } from './middleware/error-handler'` |

---

## 🔧 AGENT-BY-AGENT INTEGRATION

### **Agent 9: The Prediction Master**

**EXISTING:** `ctr_model.py`, `enhanced_ctr_model.py`

**ACTION:** EXTEND - Add Bayesian uncertainty layer

```python
# ✅ CORRECT
from services.ml_service.src.ctr_model import ctr_predictor
from services.ml_service.src.enhanced_ctr_model import enhanced_ctr_predictor

class PredictionMasterAgent(BaseAgent):
    def __init__(self):
        # Use existing models
        self.ctr_model = ctr_predictor
        self.enhanced_model = enhanced_ctr_predictor
        # ADD: Bayesian layer
        self.bayesian_model = None  # Create new
        
    async def add_bayesian_uncertainty(self):
        # EXTEND existing models with uncertainty
        pass
```

**❌ WRONG:** Creating new CTR model from scratch

---

### **Agent 10: The Experimenter**

**EXISTING:** `thompson_sampler.py`, `battle_hardened_sampler.py`

**ACTION:** EXTEND - Add UCB bandit

```python
# ✅ CORRECT
from services.ml_service.src.thompson_sampler import thompson_optimizer
from services.ml_service.src.battle_hardened_sampler import BattleHardenedSampler

class ExperimenterAgent(BaseAgent):
    def __init__(self):
        # Use existing samplers
        self.thompson = thompson_optimizer
        self.battle_hardened = BattleHardenedSampler()
        # ADD: UCB bandit
        self.ucb_bandit = None  # Create new
        
    async def add_ucb_bandit(self):
        # EXTEND existing with UCB
        pass
```

**❌ WRONG:** Creating new Thompson Sampling from scratch

---

### **Agent 13: The Sentinel (Drift Detection)**

**EXISTING:** Check `self_learning.py` or create if missing

**ACTION:** CHECK FIRST, then CREATE or EXTEND

```python
# ✅ CORRECT - Check first
try:
    from services.ml_service.src.self_learning import DriftDetector
    # EXTEND existing
    class SentinelAgent(BaseAgent):
        def __init__(self):
            self.drift_detector = DriftDetector()
            
        async def add_ks_psi_tests(self):
            # Add KS/PSI to existing detector
            pass
except ImportError:
    # CREATE new if doesn't exist
    class SentinelAgent(BaseAgent):
        def __init__(self):
            self.drift_detector = DriftDetector()  # Create new
```

---

### **Agent 17: The Cache Master**

**EXISTING:** `semantic_cache.py` (716+ lines, fully implemented)

**ACTION:** EXTEND - Add Redis vector search, metrics

```python
# ✅ CORRECT
from services.ml_service.src.semantic_cache import SemanticCache

class CacheMasterAgent(BaseAgent):
    def __init__(self):
        # Use existing semantic cache
        self.cache = SemanticCache()
        
    async def enhance_cache(self):
        # EXTEND: Add Redis vector search
        # EXTEND: Add embedding service integration
        # EXTEND: Add cache metrics
        # DON'T recreate semantic cache - it's already done!
        pass
```

**❌ WRONG:** Creating new semantic cache

---

### **Agent 21: The Learner**

**EXISTING:** `cross_learner.py`, `compound_learner.py`

**ACTION:** EXTEND - Add validation loop

```python
# ✅ CORRECT
from services.ml_service.src.cross_learner import CrossLearner
from services.ml_service.src.compound_learner import CompoundLearner

class LearnerAgent(BaseAgent):
    def __init__(self):
        # Use existing learners
        self.cross_learner = CrossLearner()
        self.compound_learner = CompoundLearner()
        
    async def add_validation_loop(self):
        # EXTEND: Add validation loop to existing
        pass
```

**❌ WRONG:** Creating new learning system

---

### **Agent 24: The Retriever**

**EXISTING:** `winner_index.py`, `vector_store.py`

**ACTION:** EXTEND - Build RAG on top

```python
# ✅ CORRECT
from services.ml_service.src.winner_index import WinnerIndex
from services.ml_service.src.vector_store import VectorStore

class RetrieverAgent(BaseAgent):
    def __init__(self):
        # Use existing systems
        self.winner_index = WinnerIndex()
        self.vector_store = VectorStore()
        
    async def build_rag_system(self):
        # EXTEND: Build RAG on top of existing
        pass
```

---

### **Agent 26: The Optimizer**

**EXISTING:** `auto_scaler.py`

**ACTION:** EXTEND - Add RL layer

```python
# ✅ CORRECT
from services.ml_service.src.auto_scaler import AutoScaler

class OptimizerAgent(BaseAgent):
    def __init__(self):
        # Use existing auto-scaler
        self.auto_scaler = AutoScaler()
        # ADD: RL optimizer
        self.rl_optimizer = None  # Create new
        
    async def add_rl_optimization(self):
        # EXTEND: Add RL to existing auto-scaler
        pass
```

---

### **Agent 27: The Timer**

**EXISTING:** `time_optimizer.py`

**ACTION:** EXTEND - Add day-part optimization

```python
# ✅ CORRECT
from services.ml_service.src.time_optimizer import TimeOptimizer

class TimerAgent(BaseAgent):
    def __init__(self):
        # Use existing time optimizer
        self.time_optimizer = TimeOptimizer()
        
    async def add_daypart_optimization(self):
        # EXTEND: Add day-part to existing
        pass
```

---

### **Agent 30: The Guardian (Circuit Breaker)**

**EXISTING:** `services/gateway-api/src/middleware/error-handler.ts`

**ACTION:** EXTEND - Add stop-loss, campaign-level breakers

```typescript
// ✅ CORRECT
import { CircuitBreaker } from './middleware/error-handler';

class GuardianAgent {
    private circuitBreaker: CircuitBreaker;
    
    constructor() {
        // Use existing circuit breaker
        this.circuitBreaker = new CircuitBreaker({
            name: 'campaign-safety',
            failureThreshold: 5,
            timeout: 30000
        });
    }
    
    async addStopLoss() {
        // EXTEND: Add stop-loss limits
    }
}
```

---

### **Agent 20: The DNA Analyst**

**EXISTING:** `creative_dna.py`

**ACTION:** EXTEND - Add temporal decay

```python
# ✅ CORRECT
from services.ml_service.src.creative_dna import CreativeDNA

class DNAAnalystAgent(BaseAgent):
    def __init__(self):
        # Use existing Creative DNA
        self.creative_dna = CreativeDNA()
        
    async def add_temporal_decay(self):
        # EXTEND: Add temporal decay to existing
        pass
```

---

### **Agent 6: The Vector Master**

**EXISTING:** `vector_store.py`

**ACTION:** EXTEND - Add FAISS enhancements

```python
# ✅ CORRECT
from services.ml_service.src.vector_store import VectorStore

class VectorMasterAgent(BaseAgent):
    def __init__(self):
        # Use existing vector store
        self.vector_store = VectorStore()
        
    async def add_faiss_enhancements(self):
        # EXTEND: Add FAISS to existing
        pass
```

---

### **Agent 15: The Validator**

**EXISTING:** `accuracy_tracker.py`

**ACTION:** EXTEND - Add confidence intervals

```python
# ✅ CORRECT
from services.ml_service.src.accuracy_tracker import accuracy_tracker

class ValidatorAgent(BaseAgent):
    def __init__(self):
        # Use existing accuracy tracker
        self.tracker = accuracy_tracker
        
    async def add_confidence_intervals(self):
        # EXTEND: Add confidence intervals
        pass
```

---

## 📝 MODIFIED AGENT INSTRUCTION TEMPLATE

For each agent instruction file, add this section:

```markdown
## EXISTING CODE CHECK

**BEFORE writing code, check these locations:**

1. `/services/ml-service/src/` - ML models and services
2. `/services/gateway-api/src/` - API services
3. `/services/langgraph-app/src/` - Agent system

**If system exists:**
- Import from existing module
- Extend with new features
- Don't recreate

**If system doesn't exist:**
- Create new implementation
- Follow existing patterns
```

---

## ✅ INTEGRATION WORKFLOW

### **For Each Agent:**

1. **Search for existing code:**
   ```bash
   grep -r "semantic.*cache\|cache.*semantic" services/ml-service/src/
   ```

2. **Read existing implementation:**
   ```python
   # Read the file to understand structure
   from services.ml_service.src.semantic_cache import SemanticCache
   ```

3. **Extend, don't replace:**
   ```python
   class EnhancedAgent(BaseAgent):
       def __init__(self):
           self.existing = ExistingClass()  # Use existing
           
       async def new_feature(self):
           # Add new functionality
           pass
   ```

4. **Test integration:**
   ```python
   # Ensure existing code still works
   # New features work with existing
   ```

---

## 🎯 SUMMARY

**40 Agents Breakdown:**
- **~15 agents:** CREATE NEW (foundation, contracts, new features)
- **~20 agents:** EXTEND EXISTING (most ML/learning features)
- **~5 agents:** WIRE TO EXISTING (use as-is)

**Key Principle:** Every agent checks for existing code FIRST, then extends or creates.

**Next Step:** Update each agent instruction file with import statements and extension patterns.

