# 🔧 MLOPS & VERTEX AI INTEGRATION GUIDE
## How to Use MLOps and Vertex AI in GeminiVideo

**Purpose:** Complete guide on integrating and using MLOps (Model Registry, Champion/Challenger) and Vertex AI in the system.

---

## 📊 CURRENT STATUS

### ✅ What Exists

**1. Model Registry (Database)**
```sql
-- File: database/migrations/006_model_registry.sql
CREATE TABLE model_registry (
    id UUID PRIMARY KEY,
    model_name VARCHAR(255),
    version VARCHAR(50),
    stage VARCHAR(50),  -- 'champion', 'challenger', 'archived'
    performance_metrics JSONB,
    ...
);
```

**2. Vertex AI Service (Titan-Core)**
```python
# File: services/titan-core/engines/vertex_ai.py (referenced)
# Status: Available but needs wiring
```

**3. Model Training Endpoints**
```python
# File: services/ml-service/src/main.py
@app.post("/api/ml/train")
async def train_model(...):
    """Train model"""
```

---

## 🎯 PART 1: MLOPS INTEGRATION

### Step 1: Model Registry Implementation

```python
# File: services/ml-service/src/mlops/model_registry.py

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import psycopg2
from psycopg2.extras import RealDictCursor

@dataclass
class ModelVersion:
    """Model version information"""
    model_name: str
    version: str
    stage: str  # 'champion', 'challenger', 'archived'
    performance_metrics: Dict
    model_path: str
    created_at: datetime
    metadata: Dict

class ModelRegistry:
    """
    MLOps Model Registry
    Manages model versions, champion/challenger stages, and performance tracking.
    """
    
    def __init__(self, db_connection_string: str):
        self.db_connection_string = db_connection_string
    
    def register_model(
        self,
        model_name: str,
        version: str,
        model_path: str,
        performance_metrics: Dict,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Register a new model version.
        
        Args:
            model_name: Name of the model (e.g., 'ctr_predictor')
            version: Version string (e.g., 'v1.2.3')
            model_path: Path to saved model file
            performance_metrics: Dict with metrics (rmse, mae, r2, accuracy)
            metadata: Additional metadata
        
        Returns:
            Model registry ID
        """
        conn = psycopg2.connect(self.db_connection_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Insert model version
        cursor.execute("""
            INSERT INTO model_registry (
                model_name,
                version,
                stage,
                performance_metrics,
                model_path,
                metadata,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            model_name,
            version,
            'challenger',  # New models start as challenger
            json.dumps(performance_metrics),
            model_path,
            json.dumps(metadata or {}),
            datetime.utcnow()
        ))
        
        model_id = cursor.fetchone()['id']
        conn.commit()
        cursor.close()
        conn.close()
        
        return model_id
    
    def promote_to_champion(
        self,
        model_name: str,
        version: str
    ) -> bool:
        """
        Promote challenger to champion.
        Automatically archives previous champion.
        """
        conn = psycopg2.connect(self.db_connection_string)
        cursor = conn.cursor()
        
        try:
            # Archive current champion
            cursor.execute("""
                UPDATE model_registry
                SET stage = 'archived',
                    archived_at = %s
                WHERE model_name = %s
                    AND stage = 'champion'
            """, (datetime.utcnow(), model_name))
            
            # Promote challenger to champion
            cursor.execute("""
                UPDATE model_registry
                SET stage = 'champion',
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
    
    def get_champion(self, model_name: str) -> Optional[ModelVersion]:
        """Get current champion model"""
        conn = psycopg2.connect(self.db_connection_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT *
            FROM model_registry
            WHERE model_name = %s
                AND stage = 'champion'
            ORDER BY promoted_at DESC
            LIMIT 1
        """, (model_name,))
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not row:
            return None
        
        return ModelVersion(
            model_name=row['model_name'],
            version=row['version'],
            stage=row['stage'],
            performance_metrics=json.loads(row['performance_metrics']),
            model_path=row['model_path'],
            created_at=row['created_at'],
            metadata=json.loads(row.get('metadata', '{}'))
        )
    
    def compare_models(
        self,
        model_name: str,
        champion_version: str,
        challenger_version: str
    ) -> Dict:
        """
        Compare champion vs challenger.
        Returns comparison metrics and recommendation.
        """
        conn = psycopg2.connect(self.db_connection_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get both models
        cursor.execute("""
            SELECT *
            FROM model_registry
            WHERE model_name = %s
                AND version IN (%s, %s)
        """, (model_name, champion_version, challenger_version))
        
        models = {row['version']: row for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        
        champion_metrics = json.loads(models[champion_version]['performance_metrics'])
        challenger_metrics = json.loads(models[challenger_version]['performance_metrics'])
        
        # Compare key metrics
        comparison = {
            'champion': {
                'version': champion_version,
                'metrics': champion_metrics
            },
            'challenger': {
                'version': challenger_version,
                'metrics': challenger_metrics
            },
            'improvements': {},
            'recommendation': 'keep_champion'
        }
        
        # Calculate improvements
        for metric in ['accuracy', 'r2', 'f1_score']:
            if metric in challenger_metrics and metric in champion_metrics:
                improvement = challenger_metrics[metric] - champion_metrics[metric]
                comparison['improvements'][metric] = improvement
                
                # If challenger is significantly better, recommend promotion
                if improvement > 0.05:  # 5% improvement threshold
                    comparison['recommendation'] = 'promote_challenger'
        
        return comparison
```

---

### Step 2: Automated Model Retraining with MLOps

```python
# File: services/ml-service/src/mlops/auto_retrain.py

from typing import Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AutoRetrainer:
    """
    Automated model retraining with champion/challenger evaluation.
    """
    
    def __init__(self, model_registry: ModelRegistry, db_pool):
        self.model_registry = model_registry
        self.db_pool = db_pool
    
    async def should_retrain(
        self,
        model_name: str,
        accuracy_threshold: float = 0.80
    ) -> bool:
        """
        Check if model should be retrained.
        
        Criteria:
        1. Accuracy dropped below threshold
        2. New data available (last 7 days)
        3. Champion model is > 30 days old
        """
        champion = self.model_registry.get_champion(model_name)
        
        if not champion:
            return True  # No champion, need to train
        
        # Check accuracy
        accuracy = champion.performance_metrics.get('accuracy', 0)
        if accuracy < accuracy_threshold:
            logger.info(f"Model {model_name} accuracy {accuracy:.2%} below threshold {accuracy_threshold:.2%}")
            return True
        
        # Check model age
        age_days = (datetime.utcnow() - champion.created_at).days
        if age_days > 30:
            logger.info(f"Model {model_name} is {age_days} days old, retraining recommended")
            return True
        
        # Check for new data
        new_data_count = await self._count_new_data(model_name, days=7)
        if new_data_count > 1000:  # Significant new data
            logger.info(f"Model {model_name} has {new_data_count} new samples, retraining recommended")
            return True
        
        return False
    
    async def retrain_and_evaluate(
        self,
        model_name: str,
        training_data: Optional[List] = None
    ) -> Dict:
        """
        Retrain model and evaluate against champion.
        """
        # 1. Train new model
        new_model = await self._train_model(model_name, training_data)
        
        # 2. Evaluate
        test_metrics = await self._evaluate_model(new_model, model_name)
        
        # 3. Register as challenger
        version = f"v{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        model_id = self.model_registry.register_model(
            model_name=model_name,
            version=version,
            model_path=new_model['path'],
            performance_metrics=test_metrics,
            metadata={'training_samples': len(training_data) if training_data else 0}
        )
        
        # 4. Compare with champion
        champion = self.model_registry.get_champion(model_name)
        if champion:
            comparison = self.model_registry.compare_models(
                model_name=model_name,
                champion_version=champion.version,
                challenger_version=version
            )
            
            # 5. Auto-promote if better
            if comparison['recommendation'] == 'promote_challenger':
                self.model_registry.promote_to_champion(model_name, version)
                logger.info(f"Auto-promoted {model_name} {version} to champion")
            
            return {
                'model_id': model_id,
                'version': version,
                'metrics': test_metrics,
                'comparison': comparison,
                'promoted': comparison['recommendation'] == 'promote_challenger'
            }
        else:
            # No champion, promote immediately
            self.model_registry.promote_to_champion(model_name, version)
            return {
                'model_id': model_id,
                'version': version,
                'metrics': test_metrics,
                'promoted': True
            }
    
    async def _train_model(self, model_name: str, training_data: List) -> Dict:
        """Train model (delegates to existing training logic)"""
        # Use existing training endpoint logic
        # Returns: {'path': model_path, 'model': trained_model}
        pass
    
    async def _evaluate_model(self, model: Dict, model_name: str) -> Dict:
        """Evaluate model on test set"""
        # Use existing evaluation logic
        # Returns: {'accuracy': 0.85, 'rmse': 0.02, ...}
        pass
    
    async def _count_new_data(self, model_name: str, days: int) -> int:
        """Count new training data"""
        query = """
            SELECT COUNT(*)
            FROM training_data
            WHERE model_name = $1
                AND created_at >= NOW() - INTERVAL '%s days'
        """ % days
        # Execute and return count
        return count
```

---

### Step 3: MLOps API Endpoints

```python
# File: services/ml-service/src/main.py

from src.mlops.model_registry import ModelRegistry, get_model_registry
from src.mlops.auto_retrain import AutoRetrainer

# Initialize
model_registry = get_model_registry()
auto_retrainer = AutoRetrainer(model_registry, db_pool)

@app.post("/api/mlops/register-model", tags=["MLOps"])
async def register_model(request: RegisterModelRequest):
    """Register a new model version"""
    model_id = model_registry.register_model(
        model_name=request.model_name,
        version=request.version,
        model_path=request.model_path,
        performance_metrics=request.performance_metrics,
        metadata=request.metadata
    )
    return {"model_id": model_id, "status": "registered"}

@app.post("/api/mlops/promote-champion", tags=["MLOps"])
async def promote_champion(request: PromoteChampionRequest):
    """Promote challenger to champion"""
    success = model_registry.promote_to_champion(
        model_name=request.model_name,
        version=request.version
    )
    return {"success": success, "champion_version": request.version}

@app.get("/api/mlops/champion/{model_name}", tags=["MLOps"])
async def get_champion(model_name: str):
    """Get current champion model"""
    champion = model_registry.get_champion(model_name)
    if not champion:
        raise HTTPException(404, f"No champion found for {model_name}")
    return {
        "model_name": champion.model_name,
        "version": champion.version,
        "performance_metrics": champion.performance_metrics,
        "model_path": champion.model_path
    }

@app.post("/api/mlops/auto-retrain", tags=["MLOps"])
async def auto_retrain(request: AutoRetrainRequest):
    """Automatically retrain model if needed"""
    should_retrain = await auto_retrainer.should_retrain(
        model_name=request.model_name,
        accuracy_threshold=request.accuracy_threshold
    )
    
    if not should_retrain:
        return {
            "should_retrain": False,
            "reason": "Model performance is acceptable"
        }
    
    result = await auto_retrainer.retrain_and_evaluate(
        model_name=request.model_name,
        training_data=request.training_data
    )
    
    return {
        "should_retrain": True,
        "retrained": True,
        "new_version": result['version'],
        "promoted": result.get('promoted', False),
        "metrics": result['metrics']
    }

@app.get("/api/mlops/compare-models", tags=["MLOps"])
async def compare_models(
    model_name: str,
    champion_version: str,
    challenger_version: str
):
    """Compare champion vs challenger"""
    comparison = model_registry.compare_models(
        model_name=model_name,
        champion_version=champion_version,
        challenger_version=challenger_version
    )
    return comparison
```

---

## 🎯 PART 2: VERTEX AI INTEGRATION

### Step 1: Vertex AI Service Setup

```python
# File: services/titan-core/engines/vertex_ai.py

from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aip
from typing import Dict, List, Optional, Any
import os
import logging

logger = logging.getLogger(__name__)

class VertexAIService:
    """
    Vertex AI Integration for Advanced ML Operations
    
    Uses:
    - Vertex AI Training (distributed training)
    - Vertex AI Prediction (scalable inference)
    - Vertex AI Model Registry (centralized model management)
    - Vertex AI Pipelines (ML workflows)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        location: str = "us-central1",
        staging_bucket: Optional[str] = None
    ):
        """
        Initialize Vertex AI service.
        
        Args:
            project_id: GCP project ID (defaults to env var)
            location: GCP region
            staging_bucket: GCS bucket for staging
        """
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.location = location
        self.staging_bucket = staging_bucket or os.getenv("GCS_STAGING_BUCKET")
        
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID must be set")
        
        # Initialize Vertex AI
        aiplatform.init(
            project=self.project_id,
            location=self.location,
            staging_bucket=self.staging_bucket
        )
        
        logger.info(f"✅ Vertex AI initialized: project={self.project_id}, location={self.location}")
    
    def train_model_vertex(
        self,
        model_name: str,
        training_data_path: str,
        training_config: Dict
    ) -> str:
        """
        Train model on Vertex AI.
        
        Args:
            model_name: Name of model
            training_data_path: GCS path to training data
            training_config: Training configuration
        
        Returns:
            Model resource name
        """
        from google.cloud.aiplatform import training_jobs
        
        # Create custom training job
        job = training_jobs.CustomTrainingJob(
            display_name=f"{model_name}_training",
            script_path="training_script.py",
            container_uri="gcr.io/cloud-aiplatform/training/tf-cpu.2-8:latest",
            requirements=["tensorflow==2.8.0", "scikit-learn==1.0.2"],
            model_serving_container_image_uri="gcr.io/cloud-aiplatform/prediction/tf2-cpu.2-8:latest"
        )
        
        # Run training
        model = job.run(
            dataset=training_data_path,
            replica_count=1,
            machine_type="n1-standard-4",
            args=[
                f"--model_name={model_name}",
                f"--epochs={training_config.get('epochs', 100)}",
                f"--batch_size={training_config.get('batch_size', 32)}"
            ]
        )
        
        logger.info(f"✅ Model trained on Vertex AI: {model.resource_name}")
        return model.resource_name
    
    def deploy_model(
        self,
        model_resource_name: str,
        endpoint_name: str,
        machine_type: str = "n1-standard-2",
        min_replicas: int = 1,
        max_replicas: int = 10
    ) -> str:
        """
        Deploy model to Vertex AI endpoint for prediction.
        
        Args:
            model_resource_name: Resource name of trained model
            endpoint_name: Name for the endpoint
            machine_type: Machine type for serving
            min_replicas: Minimum number of replicas
            max_replicas: Maximum number of replicas
        
        Returns:
            Endpoint resource name
        """
        from google.cloud.aiplatform import models
        
        # Get model
        model = models.Model(model_resource_name)
        
        # Create endpoint
        endpoint = model.deploy(
            endpoint=endpoint_name,
            machine_type=machine_type,
            min_replica_count=min_replicas,
            max_replica_count=max_replicas,
            traffic_percentage=100
        )
        
        logger.info(f"✅ Model deployed to endpoint: {endpoint.resource_name}")
        return endpoint.resource_name
    
    def predict(
        self,
        endpoint_name: str,
        instances: List[Dict]
    ) -> List[Dict]:
        """
        Make predictions using Vertex AI endpoint.
        
        Args:
            endpoint_name: Endpoint resource name
            instances: List of prediction instances
        
        Returns:
            List of predictions
        """
        from google.cloud.aiplatform import endpoints
        
        endpoint = endpoints.Endpoint(endpoint_name)
        predictions = endpoint.predict(instances=instances)
        
        return predictions.predictions
    
    def register_model_vertex(
        self,
        model_resource_name: str,
        model_name: str,
        version: str,
        metadata: Dict
    ) -> str:
        """
        Register model in Vertex AI Model Registry.
        
        Args:
            model_resource_name: Resource name of model
            model_name: Display name
            version: Version string
            metadata: Model metadata
        
        Returns:
            Model registry ID
        """
        from google.cloud.aiplatform import models
        
        model = models.Model(model_resource_name)
        
        # Add labels for versioning
        model.labels = {
            "model_name": model_name,
            "version": version,
            **metadata
        }
        
        logger.info(f"✅ Model registered in Vertex AI: {model.resource_name}")
        return model.resource_name
```

---

### Step 2: Vertex AI Integration in ML Service

```python
# File: services/ml-service/src/vertex_integration.py

from typing import Dict, Optional
import os

class VertexMLOps:
    """
    MLOps using Vertex AI for scalable training and deployment.
    """
    
    def __init__(self):
        vertex_available = os.getenv("VERTEX_AI_ENABLED", "false").lower() == "true"
        
        if vertex_available:
            from services.titan_core.engines.vertex_ai import VertexAIService
            self.vertex = VertexAIService()
            self.enabled = True
        else:
            self.vertex = None
            self.enabled = False
    
    async def train_with_vertex(
        self,
        model_name: str,
        training_data_path: str,
        config: Dict
    ) -> Dict:
        """
        Train model on Vertex AI (distributed, scalable).
        """
        if not self.enabled:
            raise ValueError("Vertex AI not enabled")
        
        # Upload training data to GCS if needed
        gcs_path = await self._upload_to_gcs(training_data_path)
        
        # Train on Vertex AI
        model_resource = self.vertex.train_model_vertex(
            model_name=model_name,
            training_data_path=gcs_path,
            training_config=config
        )
        
        # Register in Vertex AI Model Registry
        vertex_model_id = self.vertex.register_model_vertex(
            model_resource_name=model_resource,
            model_name=model_name,
            version=config.get('version', 'v1'),
            metadata=config.get('metadata', {})
        )
        
        return {
            'model_resource': model_resource,
            'vertex_model_id': vertex_model_id,
            'training_completed': True
        }
    
    async def deploy_to_vertex(
        self,
        model_resource_name: str,
        endpoint_name: str
    ) -> Dict:
        """
        Deploy model to Vertex AI endpoint.
        """
        if not self.enabled:
            raise ValueError("Vertex AI not enabled")
        
        endpoint = self.vertex.deploy_model(
            model_resource_name=model_resource_name,
            endpoint_name=endpoint_name,
            min_replicas=1,
            max_replicas=10
        )
        
        return {
            'endpoint_name': endpoint,
            'deployed': True
        }
    
    async def predict_with_vertex(
        self,
        endpoint_name: str,
        features: List[Dict]
    ) -> List[Dict]:
        """
        Make predictions using Vertex AI endpoint.
        """
        if not self.enabled:
            raise ValueError("Vertex AI not enabled")
        
        predictions = self.vertex.predict(
            endpoint_name=endpoint_name,
            instances=features
        )
        
        return predictions
```

---

### Step 3: Hybrid Approach (Local + Vertex AI)

```python
# File: services/ml-service/src/main.py

from src.vertex_integration import VertexMLOps

vertex_mlops = VertexMLOps()

@app.post("/api/ml/train", tags=["ML Training"])
async def train_model(request: TrainingRequest):
    """
    Train model (local or Vertex AI based on config).
    """
    if request.use_vertex_ai and vertex_mlops.enabled:
        # Use Vertex AI for distributed training
        result = await vertex_mlops.train_with_vertex(
            model_name=request.model_name,
            training_data_path=request.training_data_path,
            config=request.config
        )
        return {
            "training_method": "vertex_ai",
            "model_resource": result['model_resource'],
            "vertex_model_id": result['vertex_model_id']
        }
    else:
        # Use local training (existing logic)
        model = await train_model_local(request)
        return {
            "training_method": "local",
            "model_path": model['path']
        }

@app.post("/api/ml/deploy", tags=["ML Deployment"])
async def deploy_model(request: DeployRequest):
    """
    Deploy model to Vertex AI endpoint.
    """
    if not vertex_mlops.enabled:
        raise HTTPException(400, "Vertex AI not enabled")
    
    result = await vertex_mlops.deploy_to_vertex(
        model_resource_name=request.model_resource_name,
        endpoint_name=request.endpoint_name
    )
    
    return result

@app.post("/api/ml/predict/vertex", tags=["ML Prediction"])
async def predict_vertex(request: VertexPredictRequest):
    """
    Make predictions using Vertex AI endpoint.
    """
    predictions = await vertex_mlops.predict_with_vertex(
        endpoint_name=request.endpoint_name,
        features=request.features
    )
    
    return {"predictions": predictions}
```

---

## 🎯 PART 3: USAGE EXAMPLES

### Example 1: Register Model After Training

```python
# After training a model
from src.mlops.model_registry import get_model_registry

registry = get_model_registry()

# Register new version
model_id = registry.register_model(
    model_name="ctr_predictor",
    version="v2.1.0",
    model_path="/models/ctr_predictor_v2.1.0.pkl",
    performance_metrics={
        "accuracy": 0.87,
        "rmse": 0.015,
        "r2": 0.92,
        "f1_score": 0.85
    },
    metadata={
        "training_samples": 50000,
        "features": 76,
        "training_time_seconds": 1200
    }
)

# Auto-promote if better than champion
champion = registry.get_champion("ctr_predictor")
if champion:
    comparison = registry.compare_models(
        model_name="ctr_predictor",
        champion_version=champion.version,
        challenger_version="v2.1.0"
    )
    
    if comparison['recommendation'] == 'promote_challenger':
        registry.promote_to_champion("ctr_predictor", "v2.1.0")
```

### Example 2: Automated Retraining

```python
# Scheduled task (Celery)
@celery_app.task(name='auto_retrain_models')
def auto_retrain_all_models():
    """Auto-retrain all models if needed"""
    from src.mlops.auto_retrain import AutoRetrainer
    
    retrainer = AutoRetrainer(model_registry, db_pool)
    
    models = ["ctr_predictor", "roas_predictor", "pipeline_predictor"]
    
    for model_name in models:
        should_retrain = await retrainer.should_retrain(model_name)
        
        if should_retrain:
            result = await retrainer.retrain_and_evaluate(model_name)
            logger.info(f"Retrained {model_name}: {result}")
```

### Example 3: Vertex AI Training

```python
# Train large model on Vertex AI
from services.titan_core.engines.vertex_ai import VertexAIService

vertex = VertexAIService(
    project_id="geminivideo-prod",
    location="us-central1"
)

# Train on Vertex AI (distributed, scalable)
model_resource = vertex.train_model_vertex(
    model_name="enhanced_ctr_predictor",
    training_data_path="gs://geminivideo-data/training/ctr_data.csv",
    training_config={
        "epochs": 200,
        "batch_size": 64,
        "version": "v3.0.0"
    }
)

# Deploy to endpoint
endpoint = vertex.deploy_model(
    model_resource_name=model_resource,
    endpoint_name="ctr-predictor-endpoint",
    min_replicas=2,
    max_replicas=20
)

# Use for predictions
predictions = vertex.predict(
    endpoint_name=endpoint,
    instances=[{"features": [...]}]
)
```

---

## 📋 IMPLEMENTATION CHECKLIST

### MLOps
- [ ] Implement ModelRegistry class
- [ ] Add register_model endpoint
- [ ] Add promote_champion endpoint
- [ ] Add compare_models endpoint
- [ ] Implement AutoRetrainer
- [ ] Add auto-retrain scheduled task
- [ ] Test champion/challenger workflow

### Vertex AI
- [ ] Setup Vertex AI service
- [ ] Add train_model_vertex method
- [ ] Add deploy_model method
- [ ] Add predict method
- [ ] Add register_model_vertex method
- [ ] Create training script for Vertex AI
- [ ] Test Vertex AI training
- [ ] Test Vertex AI deployment
- [ ] Test Vertex AI predictions

### Integration
- [ ] Wire MLOps to model training
- [ ] Wire Vertex AI to training endpoint
- [ ] Add environment variables
- [ ] Add GCP authentication
- [ ] Test end-to-end workflow

---

## 🔧 ENVIRONMENT VARIABLES

```bash
# MLOps
MLOPS_ENABLED=true
MODEL_REGISTRY_DB_URL=postgresql://...

# Vertex AI
VERTEX_AI_ENABLED=true
GCP_PROJECT_ID=geminivideo-prod
GCP_REGION=us-central1
GCS_STAGING_BUCKET=gs://geminivideo-mlops
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

---

## 📊 SUMMARY

**MLOps:**
- Model Registry: Track versions, champion/challenger
- Auto-Retrain: Automatically retrain when needed
- Model Comparison: Compare versions before promotion

**Vertex AI:**
- Distributed Training: Scale training to multiple machines
- Model Deployment: Deploy to scalable endpoints
- Centralized Registry: Manage models in GCP

**Usage:**
- Local training for small models
- Vertex AI for large-scale training
- Hybrid approach based on model size

**Time to Implement:** 8-12 hours

---

**This integration enables production-grade MLOps with Vertex AI scalability!**

