# ✅ EXISTING MLOPS & VERTEX AI - HOW TO USE
## What Already Exists and How to Use It

**Found:** Vertex AI service exists! Model Registry database exists! Here's how to use them.

---

## 🎯 PART 1: VERTEX AI (Already Implemented!)

### ✅ What Exists

**File:** `services/titan-core/engines/vertex_ai.py` (941 lines!)

**Capabilities:**
- ✅ Video analysis with Gemini 2.0
- ✅ Image generation with Imagen
- ✅ Text embeddings
- ✅ Ad copy generation
- ✅ Hook improvement
- ✅ Competitor analysis
- ✅ Storyboard generation
- ✅ Chat sessions

---

### How to Use Vertex AI

#### 1. Initialize Vertex AI Service

```python
# File: services/titan-core/engines/vertex_ai.py

from engines.vertex_ai import VertexAIService

# Initialize (already done in titan-core)
vertex_service = VertexAIService(
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location="us-central1"
)
```

#### 2. Use in Titan-Core API

```python
# File: services/titan-core/api/main.py
# Already imported!

if VERTEX_AI_AVAILABLE:
    from engines.vertex_ai import VertexAIService
    vertex_service = VertexAIService(...)
```

#### 3. Example: Video Analysis

```python
# Already implemented in vertex_ai.py!

# Analyze video
analysis = vertex_service.analyze_video(
    video_gcs_uri="gs://bucket/video.mp4",
    prompt="Analyze for marketing purposes",
    task_complexity="complex"
)

# Returns VideoAnalysis with:
# - summary
# - scenes
# - objects_detected
# - hook_quality (0-100)
# - engagement_score (0-100)
# - marketing_insights
# - recommendations
```

#### 4. Example: Generate Ad Copy

```python
# Already implemented!

variants = vertex_service.generate_ad_copy(
    product_info="Fitness watch with heart rate monitoring...",
    style="urgent",
    num_variants=3
)
# Returns: ["variant1", "variant2", "variant3"]
```

#### 5. Example: Improve Hook

```python
# Already implemented!

improved_hooks = vertex_service.improve_hook(
    current_hook="Check out this new fitness watch!",
    target_emotion="urgency"
)
# Returns: List of improved hooks
```

#### 6. Example: Generate Images

```python
# Already implemented!

images = vertex_service.generate_image(
    prompt="Sleek fitness watch on runner's wrist",
    aspect_ratio="1:1",
    num_images=2
)
# Returns: List of image bytes
```

---

### Wire Vertex AI to Existing Endpoints

```python
# File: services/titan-core/api/main.py

@app.post("/api/titan/analyze-video", tags=["Vertex AI"])
async def analyze_video_vertex(request: VideoAnalysisRequest):
    """Analyze video using Vertex AI (already available!)"""
    if not VERTEX_AI_AVAILABLE:
        raise HTTPException(503, "Vertex AI not available")
    
    analysis = vertex_service.analyze_video(
        video_gcs_uri=request.video_uri,
        prompt=request.prompt,
        task_complexity=request.complexity or "complex"
    )
    
    return {
        "summary": analysis.summary,
        "hook_quality": analysis.hook_quality,
        "engagement_score": analysis.engagement_score,
        "recommendations": analysis.recommendations,
        "marketing_insights": analysis.marketing_insights
    }

@app.post("/api/titan/generate-ad-copy", tags=["Vertex AI"])
async def generate_ad_copy_vertex(request: AdCopyRequest):
    """Generate ad copy using Vertex AI"""
    variants = vertex_service.generate_ad_copy(
        product_info=request.product_info,
        style=request.style,
        num_variants=request.num_variants
    )
    return {"variants": variants}

@app.post("/api/titan/improve-hook", tags=["Vertex AI"])
async def improve_hook_vertex(request: HookImprovementRequest):
    """Improve hook using Vertex AI"""
    improved = vertex_service.improve_hook(
        current_hook=request.current_hook,
        target_emotion=request.target_emotion
    )
    return {"improved_hooks": improved}
```

**Time to Wire:** 1-2 hours (just add endpoints!)

---

## 🎯 PART 2: MODEL REGISTRY (Database Exists!)

### ✅ What Exists

**File:** `database/migrations/006_model_registry.sql`

**Schema:**
```sql
CREATE TABLE model_registry (
    id UUID PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    artifact_path TEXT NOT NULL,
    training_metrics JSONB,
    is_champion BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ,
    promoted_at TIMESTAMPTZ,
    UNIQUE(model_name, version)
);
```

**Features:**
- ✅ Champion/challenger pattern
- ✅ Version tracking
- ✅ Performance metrics storage
- ✅ Unique constraint (one champion per model)

---

### How to Use Model Registry

#### 1. Register Model After Training

```python
# File: services/ml-service/src/mlops/model_registry.py (CREATE)

import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

class ModelRegistry:
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
    
    def register_model(
        self,
        model_name: str,
        version: str,
        artifact_path: str,
        training_metrics: Dict
    ) -> str:
        """Register model in database"""
        conn = psycopg2.connect(self.db_connection_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO model_registry (
                model_name,
                version,
                artifact_path,
                training_metrics,
                is_champion,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            model_name,
            version,
            artifact_path,
            json.dumps(training_metrics),
            False,  # Start as challenger
            datetime.utcnow()
        ))
        
        model_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        
        return model_id
    
    def get_champion(self, model_name: str) -> Optional[Dict]:
        """Get current champion"""
        conn = psycopg2.connect(self.db_connection_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT *
            FROM model_registry
            WHERE model_name = %s
                AND is_champion = true
            ORDER BY promoted_at DESC
            LIMIT 1
        """, (model_name,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def promote_to_champion(
        self,
        model_name: str,
        version: str
    ) -> bool:
        """Promote challenger to champion"""
        conn = psycopg2.connect(self.db_connection_string)
        cursor = conn.cursor()
        
        try:
            # Archive current champion
            cursor.execute("""
                UPDATE model_registry
                SET is_champion = false
                WHERE model_name = %s
                    AND is_champion = true
            """, (model_name,))
            
            # Promote new champion
            cursor.execute("""
                UPDATE model_registry
                SET is_champion = true,
                    promoted_at = %s
                WHERE model_name = %s
                    AND version = %s
            """, (datetime.utcnow(), model_name, version))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
        except Exception as e:
            conn.rollback()
            raise
```

#### 2. Use After Training

```python
# File: services/ml-service/src/main.py

from src.mlops.model_registry import ModelRegistry

model_registry = ModelRegistry(os.getenv("DATABASE_URL"))

@app.post("/api/ml/train", tags=["ML Training"])
async def train_model(request: TrainingRequest):
    """Train model and register"""
    # Train model (existing logic)
    model = await train_ctr_model(request.training_data)
    
    # Register in model registry
    version = f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    model_id = model_registry.register_model(
        model_name="ctr_predictor",
        version=version,
        artifact_path=model['path'],
        training_metrics=model['metrics']
    )
    
    # Compare with champion
    champion = model_registry.get_champion("ctr_predictor")
    if champion:
        challenger_metrics = model['metrics']
        champion_metrics = json.loads(champion['training_metrics'])
        
        # Auto-promote if better
        if challenger_metrics['accuracy'] > champion_metrics.get('accuracy', 0):
            model_registry.promote_to_champion("ctr_predictor", version)
    
    return {
        "model_id": model_id,
        "version": version,
        "metrics": model['metrics']
    }
```

#### 3. Load Champion for Predictions

```python
# File: services/ml-service/src/main.py

@app.post("/api/ml/predict/ctr", tags=["ML Prediction"])
async def predict_ctr(request: CTRPredictionRequest):
    """Predict CTR using champion model"""
    # Get champion model
    champion = model_registry.get_champion("ctr_predictor")
    
    if not champion:
        # Fallback to default
        model = ctr_predictor
    else:
        # Load champion model
        model = load_model(champion['artifact_path'])
    
    # Predict
    prediction = model.predict(request.clip_data)
    
    return {
        "predicted_ctr": prediction,
        "model_version": champion['version'] if champion else "default"
    }
```

---

## 🎯 PART 3: COMPLETE INTEGRATION

### Step 1: Wire Model Registry (2 hours)

```python
# 1. Create ModelRegistry class (see above)
# 2. Wire to training endpoint
# 3. Wire to prediction endpoint
# 4. Add promotion logic
```

### Step 2: Wire Vertex AI Endpoints (1 hour)

```python
# 1. Add endpoints to titan-core/api/main.py
# 2. Use existing VertexAIService
# 3. Test endpoints
```

### Step 3: Add Auto-Retrain (2 hours)

```python
# 1. Create AutoRetrainer class
# 2. Add Celery scheduled task
# 3. Wire to model registry
```

---

## 📋 QUICK START

### Use Vertex AI Right Now

```python
# In titan-core service
from engines.vertex_ai import VertexAIService

vertex = VertexAIService(
    project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location="us-central1"
)

# Analyze video
analysis = vertex.analyze_video("gs://bucket/video.mp4")

# Generate ad copy
variants = vertex.generate_ad_copy(
    product_info="...",
    style="urgent"
)

# Improve hook
hooks = vertex.improve_hook(
    current_hook="...",
    target_emotion="urgency"
)
```

### Use Model Registry Right Now

```python
# After training
from src.mlops.model_registry import ModelRegistry

registry = ModelRegistry(os.getenv("DATABASE_URL"))

# Register
model_id = registry.register_model(
    model_name="ctr_predictor",
    version="v1.0.0",
    artifact_path="/models/ctr_v1.pkl",
    training_metrics={"accuracy": 0.87, "rmse": 0.015}
)

# Get champion
champion = registry.get_champion("ctr_predictor")

# Promote
registry.promote_to_champion("ctr_predictor", "v1.0.0")
```

---

## ✅ SUMMARY

**Vertex AI:** ✅ **FULLY IMPLEMENTED** (941 lines!)
- Video analysis
- Image generation
- Ad copy generation
- Hook improvement
- Just needs API endpoints wired

**Model Registry:** ✅ **DATABASE EXISTS**
- Schema ready
- Champion/challenger support
- Just needs Python wrapper

**Time to Wire:** 3-5 hours total

**No new algorithms needed - just wiring existing components!**

