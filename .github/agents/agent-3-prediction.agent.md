# Agent 3: ML Engineer - Prediction Models

## Your Mission
Implement XGBoost CTR prediction and Vowpal Wabbit A/B optimization.

## Priority: MEDIUM (Wait for Agent 1 DB)

## Tasks

### 1. Install Dependencies
```bash
pip install xgboost vowpalwabbit scikit-learn pandas
```

### 2. XGBoost CTR Prediction
Create `services/gateway-api/src/prediction.py`:
```python
import xgboost as xgb
import pandas as pd
import numpy as np
from shared.db import get_db
from shared.models import Prediction, Clip

class CTRPredictor:
    def __init__(self):
        self.model = None
        self.feature_names = [
            'psychology_composite',
            'hook_strength',
            'novelty_score',
            'emotion_priority',
            'duration',
            'has_face'
        ]

    def extract_features(self, clip) -> np.ndarray:
        """Extract features from clip for prediction"""
        psych = clip.psychology_score or {}
        hook = clip.hook_strength or {}
        novelty = clip.novelty_score or {}
        emotion = clip.emotion_data or {}

        features = [
            psych.get('composite', 0.5),
            hook.get('strength', 0.5),
            novelty.get('composite', 0.5),
            emotion.get('priority_score', 0.0),
            clip.duration,
            1.0 if emotion.get('has_face') else 0.0
        ]
        return np.array(features)

    def train(self, db_session):
        """Train on historical predictions with actual CTR"""
        # Load training data
        predictions = db_session.query(Prediction).filter(
            Prediction.actual_ctr.isnot(None)
        ).all()

        if len(predictions) < 10:
            print("Not enough data to train (need 10+)")
            return False

        X = []
        y = []
        for pred in predictions:
            clip = db_session.query(Clip).filter(
                Clip.clip_id == pred.clip_id
            ).first()
            if clip:
                X.append(self.extract_features(clip))
                y.append(pred.actual_ctr)

        X = np.array(X)
        y = np.array(y)

        # Train XGBoost
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1
        )
        self.model.fit(X, y)

        # Save model
        self.model.save_model('models/ctr_predictor.json')
        return True

    def predict(self, clip) -> dict:
        """Predict CTR for a clip"""
        if self.model is None:
            # Load or use defaults
            try:
                self.model = xgb.XGBRegressor()
                self.model.load_model('models/ctr_predictor.json')
            except:
                return self._default_prediction(clip)

        features = self.extract_features(clip).reshape(1, -1)
        predicted_ctr = float(self.model.predict(features)[0])

        # Determine band
        if predicted_ctr >= 0.08:
            band = 'viral'
        elif predicted_ctr >= 0.05:
            band = 'high'
        elif predicted_ctr >= 0.03:
            band = 'medium'
        else:
            band = 'low'

        return {
            'predicted_ctr': predicted_ctr,
            'predicted_band': band,
            'confidence': 0.85  # Could calculate based on model uncertainty
        }

    def _default_prediction(self, clip) -> dict:
        """Fallback prediction using heuristics"""
        emotion = clip.emotion_data or {}
        composite = clip.composite_score or 0.5

        base_ctr = composite * 0.05
        emotion_boost = emotion.get('priority_score', 0) * 0.02
        predicted_ctr = base_ctr + emotion_boost

        return {
            'predicted_ctr': predicted_ctr,
            'predicted_band': 'medium',
            'confidence': 0.5
        }

# Global predictor
predictor = CTRPredictor()
```

### 3. Vowpal Wabbit A/B Optimization
Create `services/meta-publisher/src/optimization.py`:
```python
import vowpalwabbit as vw
import json

class ThompsonSampling:
    def __init__(self, num_variants=3):
        self.num_variants = num_variants
        # Create VW instance with contextual bandit
        self.vw_model = vw.Workspace(
            '--cb_explore_adf --epsilon 0.2 --quiet'
        )
        self.variant_stats = [{'wins': 0, 'trials': 0} for _ in range(num_variants)]

    def select_variant(self, context: dict) -> int:
        """Select best variant using Thompson Sampling"""
        # Format context for VW
        context_str = self._format_context(context)

        # Create examples for each variant
        examples = []
        for i in range(self.num_variants):
            examples.append(f"| variant_{i} emotion={context.get('emotion', 0):.2f}")

        # Get prediction from VW
        vw_input = "shared |s " + context_str + "\n" + "\n".join(examples)
        prediction = self.vw_model.predict(vw_input)

        # Select variant (VW returns probabilities)
        selected = int(prediction)
        return selected

    def update(self, variant: int, reward: float, context: dict):
        """Update model with reward (CTR)"""
        # Format as VW example
        context_str = self._format_context(context)
        cost = -reward  # VW minimizes cost

        example = f"shared |s {context_str}\n"
        example += f"0:{cost}:{1/self.num_variants} | variant_{variant}\n"

        # Update model
        self.vw_model.learn(example)

        # Update stats
        self.variant_stats[variant]['trials'] += 1
        if reward > 0.03:  # Success threshold
            self.variant_stats[variant]['wins'] += 1

    def _format_context(self, context: dict) -> str:
        """Format context features for VW"""
        features = []
        for key, value in context.items():
            if isinstance(value, (int, float)):
                features.append(f"{key}={value:.3f}")
        return " ".join(features)

    def get_stats(self) -> dict:
        """Get current performance stats"""
        return {
            'variants': self.variant_stats,
            'best_variant': max(
                range(self.num_variants),
                key=lambda i: self.variant_stats[i]['wins'] / max(1, self.variant_stats[i]['trials'])
            )
        }

# Global optimizer
optimizer = ThompsonSampling(num_variants=3)
```

### 4. Add Endpoints
Update `services/gateway-api/src/index.ts`:
```python
from prediction import predictor

@app.post("/predict/ctr")
async def predict_ctr(clip_id: str, db: Session = Depends(get_db)):
    """Predict CTR for a clip"""
    clip = db.query(Clip).filter(Clip.clip_id == clip_id).first()
    if not clip:
        raise HTTPException(404, "Clip not found")

    prediction = predictor.predict(clip)

    # Save prediction
    pred_record = Prediction(
        clip_id=clip_id,
        predicted_ctr=prediction['predicted_ctr'],
        predicted_band=prediction['predicted_band']
    )
    db.add(pred_record)
    db.commit()

    return prediction

@app.post("/train/ctr-model")
async def train_ctr_model(db: Session = Depends(get_db)):
    """Train CTR prediction model on historical data"""
    success = predictor.train(db)
    return {"success": success, "message": "Model trained" if success else "Not enough data"}
```

### 5. Nightly Training
Update `scripts/nightly_learning.py`:
```python
from services.gateway_api.src.prediction import predictor
from shared.db import SessionLocal

def train_models():
    db = SessionLocal()
    try:
        # Train XGBoost
        success = predictor.train(db)
        print(f"CTR model training: {'success' if success else 'insufficient data'}")

        # Update weights (existing code)
        # ...
    finally:
        db.close()

if __name__ == '__main__':
    train_models()
```

## Deliverables
- [ ] XGBoost CTR prediction working
- [ ] Vowpal Wabbit Thompson Sampling
- [ ] Training endpoint
- [ ] Prediction endpoint
- [ ] Nightly training integrated
- [ ] Tests for predictions

## Branch
`agent-3-prediction-models`

## Blockers
- **Agent 1** (needs DB with Predictions table)

## Who Depends On You
- Agent 7 (needs optimization for Meta A/B)
- Agent 5 (needs prediction API for frontend)
