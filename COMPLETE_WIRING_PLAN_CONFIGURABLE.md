# COMPLETE WIRING PLAN - CONFIGURABLE VERSION
## Full System Integration with Configuration-Driven Approach

**Generated:** 2025-12-09  
**Purpose:** Step-by-step plan to wire all existing code using configuration files  
**Key Principle:** **NO HARDCODED VALUES** - Everything configurable via YAML

---

## EXECUTIVE SUMMARY

### Configuration-First Approach

**Instead of hardcoding:**
```python
# ❌ BAD - Hardcoded
if ctr > 0.03 or roas > 3.0:  # Hardcoded thresholds
    index_winner()
```

**Use configuration:**
```python
# ✅ GOOD - Configurable
config = load_learning_config()
if ctr > config['winner_detection']['ctr_threshold']:
    index_winner()
```

### Configuration File Created

**File:** `shared/config/learning_config.yaml`

**Contains:**
- Winner detection thresholds
- Learning cycle intervals
- Auto-promoter settings
- Safe executor rules
- Feature flags
- Environment overrides

---

## PART 1: CONFIGURATION LOADER

### 1.1 Create Configuration Loader

**File:** `services/ml-service/src/config_loader.py`

```python
"""
Configuration Loader for Learning & Automation
Loads settings from shared/config/learning_config.yaml
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path

_config_cache: Optional[Dict[str, Any]] = None


def get_learning_config() -> Dict[str, Any]:
    """
    Load learning configuration from YAML file
    
    Returns:
        Dict with all configuration settings
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    # Find config file
    config_path = os.getenv(
        'LEARNING_CONFIG_PATH',
        '../../shared/config/learning_config.yaml'
    )
    
    # Try multiple paths
    possible_paths = [
        config_path,
        f'shared/config/learning_config.yaml',
        f'../shared/config/learning_config.yaml',
        Path(__file__).parent.parent.parent / 'shared' / 'config' / 'learning_config.yaml'
    ]
    
    config_file = None
    for path in possible_paths:
        if os.path.exists(path):
            config_file = path
            break
    
    if not config_file:
        raise FileNotFoundError(
            f"Learning config not found. Tried: {possible_paths}"
        )
    
    # Load YAML
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply environment-specific overrides
    env = os.getenv('ENVIRONMENT', 'production')
    if env in config.get('environments', {}):
        env_config = config['environments'][env]
        # Deep merge environment overrides
        config = _deep_merge(config, env_config)
    
    _config_cache = config
    return config


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_winner_thresholds() -> Dict[str, Any]:
    """Get winner detection thresholds"""
    config = get_learning_config()
    return config.get('winner_detection', {})


def get_rag_config() -> Dict[str, Any]:
    """Get RAG indexing configuration"""
    config = get_learning_config()
    return config.get('rag_indexing', {})


def get_learning_cycle_config() -> Dict[str, Any]:
    """Get self-learning cycle configuration"""
    config = get_learning_config()
    return config.get('self_learning_cycle', {})


def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled"""
    config = get_learning_config()
    return config.get('feature_flags', {}).get(feature_name, False)
```

---

## PART 2: UPDATED AUTO-TRIGGERS (Configuration-Based)

### 2.1 RAG Auto-Indexing (Configurable)

**File:** `services/ml-service/src/main.py`

```python
# File: services/ml-service/src/main.py
# UPDATED: Use configuration instead of hardcoded values

from src.config_loader import get_winner_thresholds, get_rag_config, is_feature_enabled

def is_winner(ctr: float, roas: float, hours_live: int, impressions: int) -> bool:
    """
    Detect if ad is a winner - ALL VALUES FROM CONFIG
    """
    if not is_feature_enabled('rag_auto_indexing'):
        return False
    
    thresholds = get_winner_thresholds()
    
    # Check minimum requirements
    if hours_live < thresholds.get('min_hours_live', 24):
        return False
    
    if impressions < thresholds.get('min_impressions', 1000):
        return False
    
    # Check thresholds
    ctr_threshold = thresholds.get('ctr_threshold', 0.03)
    roas_threshold = thresholds.get('roas_threshold', 3.0)
    require_both = thresholds.get('require_both', False)
    
    if require_both:
        # Must meet BOTH thresholds
        return (ctr > ctr_threshold) and (roas > roas_threshold)
    else:
        # Must meet EITHER threshold
        return (ctr > ctr_threshold) or (roas > roas_threshold)
```

### 2.2 Self-Learning Cycle (Configurable)

**File:** `services/ml-service/src/self_learning_orchestrator.py`

```python
# File: services/ml-service/src/self_learning_orchestrator.py
# UPDATED: Use configuration for intervals and loop settings

from src.config_loader import get_learning_cycle_config, is_feature_enabled

class SelfLearningOrchestrator:
    """Orchestrates all 7 self-learning loops - CONFIGURABLE"""
    
    def __init__(self):
        self.config = get_learning_cycle_config()
        self.creative_dna = get_creative_dna()
        self.compound_learner = compound_learner
        self.actuals_fetcher = actuals_fetcher
        self.auto_promoter = auto_promoter
    
    async def run_full_cycle(self) -> Dict[str, Any]:
        """Run all 7 learning loops - ORDER AND TIMEOUTS FROM CONFIG"""
        
        if not is_feature_enabled('self_learning_cycle'):
            return {'status': 'disabled', 'reason': 'Feature flag disabled'}
        
        results = {
            'started_at': datetime.utcnow().isoformat(),
            'loops': {}
        }
        
        # Get loop configuration
        loops_config = self.config.get('loops', {})
        continue_on_error = self.config.get('continue_on_error', True)
        max_retries = self.config.get('max_retries', 3)
        
        # Sort loops by priority
        sorted_loops = sorted(
            loops_config.items(),
            key=lambda x: x[1].get('priority', 999)
        )
        
        for loop_name, loop_config in sorted_loops:
            if not loop_config.get('enabled', True):
                logger.info(f"Skipping disabled loop: {loop_name}")
                continue
            
            timeout = loop_config.get('timeout_seconds', 300)
            
            try:
                # Run loop with timeout
                result = await asyncio.wait_for(
                    self._run_loop(loop_name),
                    timeout=timeout
                )
                results['loops'][loop_name] = result
                
            except asyncio.TimeoutError:
                logger.error(f"Loop {loop_name} timed out after {timeout}s")
                results['loops'][loop_name] = {'status': 'timeout'}
                if not continue_on_error:
                    break
                    
            except Exception as e:
                logger.error(f"Loop {loop_name} failed: {e}", exc_info=True)
                results['loops'][loop_name] = {'status': 'failed', 'error': str(e)}
                if not continue_on_error:
                    break
        
        results['status'] = 'completed'
        results['completed_at'] = datetime.utcnow().isoformat()
        return results
```

### 2.3 Champion-Challenger (Configurable)

**File:** `services/ml-service/src/tasks.py`

```python
# File: services/ml-service/src/tasks.py
# UPDATED: Use configuration for evaluation criteria

from src.config_loader import get_learning_config, is_feature_enabled

@celery_app.task(name='auto_evaluate_models')
def auto_evaluate_models_after_training(model_path: str, model_type: str):
    """Auto-evaluate models - CRITERIA FROM CONFIG"""
    
    if not is_feature_enabled('champion_challenger'):
        return {'status': 'disabled'}
    
    config = get_learning_config()
    eval_config = config.get('model_evaluation', {})
    
    # Get thresholds from config
    min_improvement_pct = eval_config.get('min_improvement_pct', 2.0)
    min_samples = eval_config.get('min_samples', 1000)
    confidence_level = eval_config.get('confidence_level', 0.95)
    min_accuracy_delta = eval_config.get('min_accuracy_delta', 0.01)
    
    # Evaluate with configurable criteria
    result = evaluate_champion_vs_challenger(
        champion_path=champion_path,
        challenger_path=model_path,
        model_type=model_type,
        min_improvement_pct=min_improvement_pct,
        min_samples=min_samples,
        confidence_level=confidence_level,
        min_accuracy_delta=min_accuracy_delta
    )
    
    # Auto-promote if enabled and challenger wins
    if eval_config.get('auto_promote', True) and result['challenger_wins']:
        promote_to_champion(model_path, model_type)
        return {'status': 'promoted', 'metrics': result['metrics']}
    
    return result
```

---

## PART 3: CONFIGURABLE WORKERS

### 3.1 SafeExecutor Worker (Configurable)

**File:** `services/gateway-api/src/jobs/safe-executor.ts`

```typescript
// File: services/gateway-api/src/jobs/safe-executor.ts
// UPDATED: Load configuration from YAML or environment

import * as yaml from 'js-yaml';
import * as fs from 'fs';
import * as path from 'path';

interface SafeExecutorConfig {
  enabled: boolean;
  poll_interval_ms: number;
  rate_limiting: {
    max_actions_per_hour: number;
    max_actions_per_day: number;
  };
  budget_velocity: {
    max_change_pct: number;
    velocity_window_hours: number;
  };
  jitter: {
    enabled: boolean;
    min_ms: number;
    max_ms: number;
  };
  fuzzy_budgets: {
    enabled: boolean;
    variance_pct: number;
  };
}

function loadSafeExecutorConfig(): SafeExecutorConfig {
  // Try to load from YAML
  const configPath = process.env.SAFE_EXECUTOR_CONFIG_PATH || 
    path.join(__dirname, '../../../shared/config/learning_config.yaml');
  
  try {
    if (fs.existsSync(configPath)) {
      const config = yaml.load(fs.readFileSync(configPath, 'utf8'));
      return config.safe_executor;
    }
  } catch (error) {
    console.warn('Could not load config from YAML, using defaults');
  }
  
  // Fallback to environment variables or defaults
  return {
    enabled: process.env.SAFE_EXECUTOR_ENABLED !== 'false',
    poll_interval_ms: parseInt(process.env.POLL_INTERVAL_MS || '5000', 10),
    rate_limiting: {
      max_actions_per_hour: parseInt(process.env.MAX_ACTIONS_PER_HOUR || '15', 10),
      max_actions_per_day: parseInt(process.env.MAX_ACTIONS_PER_DAY || '100', 10),
    },
    budget_velocity: {
      max_change_pct: parseFloat(process.env.MAX_BUDGET_CHANGE_PCT || '20.0'),
      velocity_window_hours: parseInt(process.env.VELOCITY_WINDOW_HOURS || '6', 10),
    },
    jitter: {
      enabled: process.env.JITTER_ENABLED !== 'false',
      min_ms: parseInt(process.env.JITTER_MIN_MS || '3000', 10),
      max_ms: parseInt(process.env.JITTER_MAX_MS || '18000', 10),
    },
    fuzzy_budgets: {
      enabled: process.env.FUZZY_BUDGETS_ENABLED !== 'false',
      variance_pct: parseFloat(process.env.FUZZY_BUDGET_VARIANCE_PCT || '3.0'),
    },
  };
}

// Use config throughout
const config = loadSafeExecutorConfig();

if (!config.enabled) {
  console.log('SafeExecutor disabled by configuration');
  process.exit(0);
}

// Use config values
const POLL_INTERVAL_MS = config.poll_interval_ms;
const MAX_ACTIONS_PER_HOUR = config.rate_limiting.max_actions_per_hour;
const MAX_BUDGET_CHANGE_PCT = config.budget_velocity.max_change_pct;
// ... etc
```

### 3.2 Self-Learning Worker (Configurable)

**File:** `services/ml-service/src/workers/self_learning_worker.py`

```python
# File: services/ml-service/src/workers/self_learning_worker.py
# UPDATED: Use configuration for interval

from src.config_loader import get_learning_cycle_config, is_feature_enabled

async def main():
    """Main worker loop - INTERVAL FROM CONFIG"""
    
    if not is_feature_enabled('self_learning_cycle'):
        logger.info("Self-learning cycle disabled by configuration")
        return
    
    config = get_learning_cycle_config()
    interval_seconds = config.get('interval_seconds', 3600)
    
    logger.info(f"Starting self-learning worker (interval: {interval_seconds}s)")
    
    while True:
        try:
            await run_cycle()
        except Exception as e:
            logger.error(f"Cycle failed: {e}", exc_info=True)
        
        # Wait for configured interval
        logger.info(f"Waiting {interval_seconds} seconds before next cycle...")
        await asyncio.sleep(interval_seconds)
```

---

## PART 4: CONFIGURABLE DATABASE TRIGGERS

### 4.1 Database Trigger (Configurable)

**File:** `database/migrations/007_auto_triggers.sql`

```sql
-- File: database/migrations/007_auto_triggers.sql
-- UPDATED: Read thresholds from config table

-- Create config table if it doesn't exist
CREATE TABLE IF NOT EXISTS learning_config (
    key VARCHAR(255) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert default thresholds (can be updated via API)
INSERT INTO learning_config (key, value) VALUES
('winner_detection', '{"ctr_threshold": 0.03, "roas_threshold": 3.0, "min_impressions": 1000, "min_hours_live": 24}'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- Function to get threshold from config
CREATE OR REPLACE FUNCTION get_winner_threshold(threshold_name TEXT)
RETURNS NUMERIC AS $$
DECLARE
    config_value JSONB;
    threshold_value NUMERIC;
BEGIN
    SELECT value INTO config_value
    FROM learning_config
    WHERE key = 'winner_detection';
    
    threshold_value := (config_value->>threshold_name)::NUMERIC;
    RETURN COALESCE(threshold_value, 0);
END;
$$ LANGUAGE plpgsql;

-- Updated trigger function using config
CREATE OR REPLACE FUNCTION check_winner_and_index()
RETURNS TRIGGER AS $$
DECLARE
    v_ctr FLOAT;
    v_roas FLOAT;
    v_hours_live INT;
    v_ctr_threshold FLOAT;
    v_roas_threshold FLOAT;
    v_min_impressions INT;
    v_min_hours INT;
BEGIN
    -- Get thresholds from config
    v_ctr_threshold := get_winner_threshold('ctr_threshold');
    v_roas_threshold := get_winner_threshold('roas_threshold');
    v_min_impressions := get_winner_threshold('min_impressions')::INT;
    v_min_hours := get_winner_threshold('min_hours_live')::INT;
    
    -- Get performance metrics
    v_ctr := NEW.ctr;
    v_roas := (NEW.raw_data->>'roas')::FLOAT;
    v_hours_live := EXTRACT(EPOCH FROM (NOW() - NEW.created_at)) / 3600;
    
    -- Check if winner using CONFIGURABLE thresholds
    IF v_hours_live >= v_min_hours 
       AND NEW.impressions >= v_min_impressions 
       AND (v_ctr > v_ctr_threshold OR v_roas > v_roas_threshold) THEN
        
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
```

---

## PART 5: CONFIGURATION API

### 5.1 Configuration Management Endpoints

**File:** `services/ml-service/src/main.py`

```python
# File: services/ml-service/src/main.py
# Add configuration management endpoints

from src.config_loader import get_learning_config, reload_config

@app.get("/api/config/learning")
async def get_learning_config_endpoint():
    """Get current learning configuration"""
    return get_learning_config()

@app.put("/api/config/learning")
async def update_learning_config(request: Dict[str, Any]):
    """
    Update learning configuration (requires admin)
    Updates the YAML file and reloads cache
    """
    # TODO: Add admin authentication
    
    config_path = os.getenv(
        'LEARNING_CONFIG_PATH',
        '../../shared/config/learning_config.yaml'
    )
    
    # Load existing config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Update with new values
    config = _deep_merge(config, request)
    
    # Save back to file
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    # Reload cache
    reload_config()
    
    return {"status": "updated", "config": config}

@app.post("/api/config/learning/reload")
async def reload_learning_config():
    """Reload configuration from file (without restart)"""
    reload_config()
    return {"status": "reloaded", "config": get_learning_config()}
```

---

## PART 6: ENVIRONMENT VARIABLES (Fallback)

### 6.1 Environment Variable Support

**For Docker/Kubernetes deployments, support environment variables:**

```yaml
# docker-compose.yml
services:
  ml-service:
    environment:
      # Override config via environment variables
      - WINNER_CTR_THRESHOLD=0.03
      - WINNER_ROAS_THRESHOLD=3.0
      - LEARNING_CYCLE_INTERVAL_SECONDS=3600
      - SAFE_EXECUTOR_POLL_INTERVAL_MS=5000
      - RAG_AUTO_INDEXING_ENABLED=true
```

**Code to support this:**

```python
# File: services/ml-service/src/config_loader.py
# Add environment variable support

def get_winner_thresholds() -> Dict[str, Any]:
    """Get winner detection thresholds with env var override"""
    config = get_learning_config()
    thresholds = config.get('winner_detection', {})
    
    # Override with environment variables if set
    if os.getenv('WINNER_CTR_THRESHOLD'):
        thresholds['ctr_threshold'] = float(os.getenv('WINNER_CTR_THRESHOLD'))
    
    if os.getenv('WINNER_ROAS_THRESHOLD'):
        thresholds['roas_threshold'] = float(os.getenv('WINNER_ROAS_THRESHOLD'))
    
    if os.getenv('WINNER_MIN_IMPRESSIONS'):
        thresholds['min_impressions'] = int(os.getenv('WINNER_MIN_IMPRESSIONS'))
    
    return thresholds
```

---

## PART 7: UPDATED WIRING CHECKLIST

### Phase 1: Configuration System (2 hours)
- [ ] 1.1 Create `learning_config.yaml` (✅ DONE)
- [ ] 1.2 Create `config_loader.py` (1h)
- [ ] 1.3 Add configuration API endpoints (1h)

### Phase 2: Update Auto-Triggers (3 hours)
- [ ] 2.1 RAG Auto-Indexing (use config) (1h)
- [ ] 2.2 Self-Learning Cycle (use config) (1h)
- [ ] 2.3 Champion-Challenger (use config) (1h)

### Phase 3: Update Workers (2 hours)
- [ ] 3.1 SafeExecutor (use config) (1h)
- [ ] 3.2 Self-Learning Worker (use config) (1h)

### Phase 4: Database Triggers (1 hour)
- [ ] 4.1 Configurable triggers (1h)

### Phase 5: Testing (2 hours)
- [ ] 5.1 Test configuration loading (1h)
- [ ] 5.2 Test environment overrides (1h)

**Total Time:** 10 hours  
**Benefit:** Fully configurable, no hardcoded values

---

## PART 8: CONFIGURATION EXAMPLES

### Example 1: Stricter Winner Criteria

```yaml
# shared/config/learning_config.yaml
winner_detection:
  ctr_threshold: 0.05          # 5% instead of 3%
  roas_threshold: 4.0          # 4.0 instead of 3.0
  require_both: true            # Must meet BOTH
  min_impressions: 5000         # More data required
```

### Example 2: Faster Learning Cycles (Development)

```yaml
# shared/config/learning_config.yaml
environments:
  development:
    self_learning_cycle:
      interval_seconds: 60     # Every minute
    safe_executor:
      poll_interval_ms: 1000   # Every second
```

### Example 3: Disable Features

```yaml
# shared/config/learning_config.yaml
feature_flags:
  rag_auto_indexing: false     # Disable auto-indexing
  auto_promoter: false          # Disable auto-promotion
  # But keep learning cycles running
  self_learning_cycle: true
```

---

## PART 9: MIGRATION FROM HARDCODED

### Step-by-Step Migration:

1. **Create config file** (✅ DONE)
2. **Create config loader** (1h)
3. **Update one function at a time:**
   - Start with `is_winner()` function
   - Test thoroughly
   - Move to next function
4. **Add configuration API** (1h)
5. **Update database triggers** (1h)
6. **Test all scenarios** (2h)

### Testing Strategy:

```python
# Test configuration loading
def test_config_loading():
    config = get_learning_config()
    assert config['winner_detection']['ctr_threshold'] == 0.03

# Test environment override
def test_env_override():
    os.environ['WINNER_CTR_THRESHOLD'] = '0.05'
    thresholds = get_winner_thresholds()
    assert thresholds['ctr_threshold'] == 0.05

# Test feature flags
def test_feature_flags():
    assert is_feature_enabled('rag_auto_indexing') == True
```

---

## CONCLUSION

### Benefits of Configuration Approach:

1. **No Hardcoded Values** ✅
   - All thresholds configurable
   - Easy to adjust without code changes
   - Environment-specific settings

2. **Feature Flags** ✅
   - Enable/disable features
   - Gradual rollout
   - A/B testing

3. **Environment Overrides** ✅
   - Different settings for dev/staging/prod
   - Easy testing
   - Safe defaults

4. **Runtime Updates** ✅
   - Change config without restart
   - API to update settings
   - Immediate effect

5. **Better Testing** ✅
   - Test with different configs
   - Easy to mock
   - Isolated tests

### Next Steps:

1. ✅ Create `learning_config.yaml` (DONE)
2. Create `config_loader.py`
3. Update all functions to use config
4. Add configuration API
5. Test thoroughly
6. Deploy with confidence

---

**Document Generated:** 2025-12-09  
**Approach:** Configuration-First, No Hardcoding  
**Status:** Ready for implementation

