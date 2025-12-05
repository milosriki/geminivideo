# Key Code Snippets - Agent 10 Retraining Loop

## 1. CTRPredictor.check_and_retrain() Method

```python
# File: /home/user/geminivideo/services/ml-service/src/ctr_model.py

async def check_and_retrain(self) -> Dict:
    """
    Check if model needs retraining based on prediction accuracy
    
    Returns:
        Dictionary with retraining status and metrics
    """
    if not self.accuracy_tracker:
        logger.warning("AccuracyTracker not available - cannot check accuracy")
        return {'status': 'error', 'error': 'AccuracyTracker not available'}
    
    try:
        # Get recent predictions with actuals
        accuracy = await self.accuracy_tracker.calculate_accuracy_metrics(days_back=7)
        
        total_predictions = accuracy.get('total_predictions', 0)
        ctr_mae = accuracy.get('ctr_mae', 0.0)
        
        logger.info(f"Current accuracy check: MAE={ctr_mae:.4f}, samples={total_predictions}")
        
        # If accuracy dropped below threshold, retrain
        if ctr_mae > 0.02:  # 2% error threshold
            logger.warning(f"Accuracy dropped (MAE={ctr_mae:.4f} > 0.02) - triggering retrain")
            return await self.retrain_on_real_data()
        
        return {
            'status': 'no_retrain_needed',
            'current_accuracy': accuracy,
            'threshold': 0.02,
            'message': f"Model accuracy acceptable (MAE={ctr_mae:.4f} <= 0.02)"
        }
    
    except Exception as e:
        logger.error(f"Error during check_and_retrain: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}
```

## 2. CTRPredictor.retrain_on_real_data() Method

```python
# File: /home/user/geminivideo/services/ml-service/src/ctr_model.py

async def retrain_on_real_data(self) -> Dict:
    """
    Retrain model using actual performance data from database
    
    Returns:
        Dictionary with retraining status and metrics
    """
    try:
        # Load predictions with actuals
        training_data = await self.load_real_training_data()
        
        if len(training_data) < 50:
            logger.warning(f"Insufficient training data: {len(training_data)} samples (need 50+)")
            return {
                'status': 'insufficient_data',
                'count': len(training_data),
                'message': f"Need at least 50 samples for retraining, got {len(training_data)}"
            }
        
        # Extract features and targets
        X = self.extract_features(training_data)
        y = np.array([d['actual_ctr'] for d in training_data])
        
        logger.info(f"Retraining model with {len(training_data)} real performance samples...")
        
        # Store old metrics for comparison
        old_metrics = self.training_metrics.copy() if self.training_metrics else {}
        
        # Retrain
        from src.feature_engineering import feature_extractor
        metrics = self.train(X, y, feature_names=feature_extractor.feature_names)
        
        # Log improvement
        improvement = {}
        if old_metrics:
            improvement = {
                'r2_improvement': metrics['test_r2'] - old_metrics.get('test_r2', 0),
                'mae_improvement': old_metrics.get('test_mae', 1) - metrics['test_mae']
            }
            logger.info(f"Model retrained. New R²: {metrics['test_r2']:.4f} (improvement: {improvement['r2_improvement']:+.4f})")
        else:
            logger.info(f"Model retrained. New R²: {metrics['test_r2']:.4f}")
        
        return {
            'status': 'retrained',
            'samples': len(training_data),
            'metrics': metrics,
            'old_metrics': old_metrics,
            'improvement': improvement,
            'retrained_at': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error during retraining: {e}", exc_info=True)
        return {'status': 'error', 'error': str(e)}
```

## 3. API Endpoint: POST /api/ml/check-retrain

```python
# File: /home/user/geminivideo/services/ml-service/src/main.py

@app.post("/api/ml/check-retrain")
async def check_and_retrain_model():
    """
    Check model accuracy and retrain if needed (Agent 10)
    
    This endpoint should be called daily via cron to:
    1. Check prediction accuracy against actual performance
    2. Trigger retraining if accuracy drops below threshold (MAE > 2%)
    3. Return detailed metrics and status
    
    Investment-grade implementation for €5M validation
    """
    try:
        logger.info("🔄 CRON: Starting scheduled accuracy check and potential retrain...")
        
        # Check if retraining is needed
        result = await ctr_predictor.check_and_retrain()
        
        # Add timestamp
        result['checked_at'] = datetime.utcnow().isoformat()
        
        # Log result
        if result['status'] == 'retrained':
            logger.info(f"✅ CRON: Model retrained successfully with {result['samples']} samples")
            logger.info(f"   New R²: {result['metrics']['test_r2']:.4f}")
            logger.info(f"   New MAE: {result['metrics']['test_mae']:.4f}")
            if result.get('improvement'):
                logger.info(f"   R² improvement: {result['improvement']['r2_improvement']:+.4f}")
        elif result['status'] == 'no_retrain_needed':
            logger.info(f"✅ CRON: Model accuracy acceptable - no retrain needed")
            logger.info(f"   Current MAE: {result['current_accuracy']['ctr_mae']:.4f}")
        elif result['status'] == 'insufficient_data':
            logger.warning(f"⚠️  CRON: Insufficient training data ({result['count']} samples)")
        else:
            logger.error(f"❌ CRON: Error during check/retrain - {result.get('error', 'unknown')}")
        
        return result
    
    except Exception as e:
        logger.error(f"❌ CRON: Error in check_and_retrain endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## 4. Learning Loop Integration

```python
# File: /home/user/geminivideo/services/titan-core/ai_council/learning_loop.py

def _trigger_ml_retraining(self):
    """
    Trigger ML model retraining via API call
    Agent 10 - Investment-grade implementation
    """
    try:
        logger.info("🔄 LEARNING LOOP: Triggering ML model retraining...")
        
        # Call the ML service check-retrain endpoint
        url = f"{self.ml_service_url}/api/ml/check-retrain"
        
        response = requests.post(url, timeout=300)  # 5 min timeout for training
        
        if response.status_code == 200:
            result = response.json()
            
            if result['status'] == 'retrained':
                logger.info(f"✅ LEARNING LOOP: Model retrained successfully!")
                logger.info(f"   Samples used: {result.get('samples', 0)}")
                logger.info(f"   New R²: {result.get('metrics', {}).get('test_r2', 0):.4f}")
            elif result['status'] == 'no_retrain_needed':
                logger.info(f"✅ LEARNING LOOP: Model accuracy acceptable - no retrain needed")
                logger.info(f"   Current MAE: {result.get('current_accuracy', {}).get('ctr_mae', 0):.4f}")
            elif result['status'] == 'insufficient_data':
                logger.warning(f"⚠️  LEARNING LOOP: Insufficient data for retraining ({result.get('count', 0)} samples)")
            else:
                logger.warning(f"⚠️  LEARNING LOOP: Retraining status: {result['status']}")
        else:
            logger.error(f"❌ LEARNING LOOP: ML service returned error {response.status_code}")
    
    except requests.RequestException as e:
        logger.error(f"❌ LEARNING LOOP: Failed to connect to ML service: {e}")
    except Exception as e:
        logger.error(f"❌ LEARNING LOOP: Error triggering retraining: {e}", exc_info=True)
```

## 5. Cron Script

```bash
#!/bin/bash
# File: /home/user/geminivideo/services/ml-service/cron_retrain.sh

# Configuration
ML_SERVICE_URL="${ML_SERVICE_URL:-http://localhost:8003}"
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"

echo "========================================="
echo "ML Model Retraining Check - $(date)"
echo "========================================="

# Call the check-retrain endpoint
response=$(curl -s -w "\n%{http_code}" -X POST "${ML_SERVICE_URL}/api/ml/check-retrain")
http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

echo "HTTP Status: $http_code"
echo "Response: $body"

# Parse the response
status=$(echo "$body" | jq -r '.status' 2>/dev/null || echo "unknown")

if [ "$http_code" -eq 200 ]; then
    echo "✅ Check completed successfully"
    
    case "$status" in
        "retrained")
            samples=$(echo "$body" | jq -r '.samples' 2>/dev/null || echo "unknown")
            test_r2=$(echo "$body" | jq -r '.metrics.test_r2' 2>/dev/null || echo "unknown")
            echo "✅ Model retrained with $samples samples (R²: $test_r2)"
            
            # Send success notification to Slack if configured
            if [ -n "$SLACK_WEBHOOK_URL" ]; then
                curl -X POST "$SLACK_WEBHOOK_URL" \
                    -H 'Content-Type: application/json' \
                    -d "{\"text\":\"✅ ML Model Retrained: $samples samples, R²: $test_r2\"}"
            fi
            ;;
        "no_retrain_needed")
            mae=$(echo "$body" | jq -r '.current_accuracy.ctr_mae' 2>/dev/null || echo "unknown")
            echo "✅ Model accuracy acceptable (MAE: $mae)"
            ;;
        "insufficient_data")
            count=$(echo "$body" | jq -r '.count' 2>/dev/null || echo "unknown")
            echo "⚠️  Insufficient training data: $count samples"
            ;;
    esac
else
    echo "❌ Error: HTTP $http_code"
    exit 1
fi
```

## 6. Usage Examples

### Manual API Call
```bash
# Check and retrain if needed
curl -X POST http://localhost:8003/api/ml/check-retrain

# With pretty formatting
curl -X POST http://localhost:8003/api/ml/check-retrain | jq
```

### Cron Job Setup
```bash
# Edit crontab
crontab -e

# Add daily run at 2 AM
0 2 * * * /home/user/geminivideo/services/ml-service/cron_retrain.sh >> /var/log/ml-retrain.log 2>&1
```

### Python Testing
```python
import asyncio
from src.ctr_model import ctr_predictor

# Test retraining
async def test():
    result = await ctr_predictor.check_and_retrain()
    print(f"Status: {result['status']}")
    print(f"Details: {result}")

asyncio.run(test())
```

## 7. Response Examples

### No Retrain Needed
```json
{
  "status": "no_retrain_needed",
  "current_accuracy": {
    "ctr_mae": 0.0145,
    "ctr_rmse": 0.0189,
    "ctr_accuracy": 87.5,
    "total_predictions": 156
  },
  "threshold": 0.02,
  "message": "Model accuracy acceptable (MAE=0.0145 <= 0.02)",
  "checked_at": "2025-12-05T10:30:00Z"
}
```

### Retrained Successfully
```json
{
  "status": "retrained",
  "samples": 245,
  "metrics": {
    "test_r2": 0.8956,
    "test_mae": 0.0167,
    "test_rmse": 0.0212,
    "test_accuracy": 0.92,
    "trained_at": "2025-12-05T10:30:15Z"
  },
  "old_metrics": {
    "test_r2": 0.8723,
    "test_mae": 0.0234
  },
  "improvement": {
    "r2_improvement": 0.0233,
    "mae_improvement": 0.0067
  },
  "retrained_at": "2025-12-05T10:30:15Z",
  "checked_at": "2025-12-05T10:30:00Z"
}
```

### Insufficient Data
```json
{
  "status": "insufficient_data",
  "count": 42,
  "message": "Need at least 50 samples for retraining, got 42",
  "checked_at": "2025-12-05T10:30:00Z"
}
```

---

**These snippets demonstrate the complete retraining loop implementation for €5M investment validation.**
