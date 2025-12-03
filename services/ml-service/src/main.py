"""
ML Service - XGBoost CTR Prediction & Vowpal Wabbit A/B Testing
Agent 1-3 - Main FastAPI Service with XGBoost
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import os
import logging
import numpy as np
from datetime import datetime

# Import ML components
from src.feature_engineering import feature_extractor
from src.ctr_model import ctr_predictor
from src.thompson_sampler import thompson_optimizer
from src.data_loader import get_data_loader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feedback store for retraining (in-memory, but could be persisted)
feedback_store: List[Dict[str, Any]] = []

app = FastAPI(
    title="ML Service",
    description="XGBoost CTR Prediction & Vowpal Wabbit A/B Testing",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CTRPredictionRequest(BaseModel):
    """Request model for CTR prediction"""
    clip_data: Dict[str, Any]
    include_confidence: bool = False


class CTRPredictionResponse(BaseModel):
    """Response model for CTR prediction"""
    predicted_ctr: float
    confidence: Optional[float] = None
    features_used: int


class BatchCTRPredictionRequest(BaseModel):
    """Request model for batch CTR prediction"""
    clips_data: List[Dict[str, Any]]
    include_confidence: bool = False


class TrainingRequest(BaseModel):
    """Request model for model training"""
    use_synthetic_data: bool = True
    n_samples: Optional[int] = 1000


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ml-service",
        "xgboost_loaded": ctr_predictor.is_trained,
        "vowpal_wabbit_loaded": True,
        "thompson_sampling_active": len(thompson_optimizer.variants) > 0,
        "active_variants": len(thompson_optimizer.variants),
        "model_metrics": ctr_predictor.training_metrics if ctr_predictor.is_trained else {}
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ML Service",
        "version": "1.0.0",
        "learning_mode": "real_data",
        "endpoints": {
            "health": "/health",
            "predict_ctr": "/api/ml/predict-ctr",
            "predict_ctr_batch": "/api/ml/predict-ctr/batch",
            "train_model": "/api/ml/train",
            "model_info": "/api/ml/model-info",
            "feature_importance": "/api/ml/feature-importance",
            "feedback": "/api/ml/feedback",
            "stats": "/api/ml/stats",
            "ab_testing": {
                "register_variant": "/api/ml/ab/register-variant",
                "select_variant": "/api/ml/ab/select-variant",
                "update_variant": "/api/ml/ab/update-variant",
                "variant_stats": "/api/ml/ab/variant-stats/{variant_id}",
                "all_variants": "/api/ml/ab/all-variants",
                "best_variant": "/api/ml/ab/best-variant",
                "reallocate_budget": "/api/ml/ab/reallocate-budget"
            }
        }
    }

# XGBoost CTR Prediction Endpoints (Agent 3)

@app.post("/api/ml/predict-ctr", response_model=CTRPredictionResponse)
async def predict_ctr(request: CTRPredictionRequest):
    """
    Predict CTR for a single clip/storyboard

    Agent 3 - XGBoost CTR Prediction
    """
    try:
        if not ctr_predictor.is_trained:
            raise HTTPException(status_code=400, detail="Model not trained. Call /api/ml/train first.")

        # Extract features
        features = feature_extractor.extract_features(request.clip_data)

        # Predict CTR
        if request.include_confidence:
            predictions, confidence = ctr_predictor.predict_with_confidence(features.reshape(1, -1))
            predicted_ctr = predictions[0]
            conf_score = confidence[0]
        else:
            predicted_ctr = ctr_predictor.predict_single(features)
            conf_score = None

        return CTRPredictionResponse(
            predicted_ctr=float(predicted_ctr),
            confidence=float(conf_score) if conf_score is not None else None,
            features_used=feature_extractor.get_feature_count()
        )

    except Exception as e:
        logger.error(f"Error predicting CTR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/predict-ctr/batch")
async def predict_ctr_batch(request: BatchCTRPredictionRequest):
    """
    Predict CTR for multiple clips/storyboards at once

    Agent 3 - Batch XGBoost CTR Prediction
    """
    try:
        if not ctr_predictor.is_trained:
            raise HTTPException(status_code=400, detail="Model not trained. Call /api/ml/train first.")

        # Extract features for all clips
        features = feature_extractor.extract_batch_features(request.clips_data)

        # Predict CTR
        if request.include_confidence:
            predictions, confidence = ctr_predictor.predict_with_confidence(features)
            results = [
                {
                    "predicted_ctr": float(pred),
                    "confidence": float(conf)
                }
                for pred, conf in zip(predictions, confidence)
            ]
        else:
            predictions = ctr_predictor.predict(features)
            results = [
                {"predicted_ctr": float(pred)}
                for pred in predictions
            ]

        return {
            "predictions": results,
            "count": len(results),
            "features_used": feature_extractor.get_feature_count()
        }

    except Exception as e:
        logger.error(f"Error predicting CTR batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/train")
async def train_model(request: TrainingRequest):
    """
    Train XGBoost CTR model

    Agent 3 - Model Training
    """
    try:
        if request.use_synthetic_data:
            logger.info(f"Generating {request.n_samples} synthetic training samples...")
            X, y = generate_synthetic_training_data(n_samples=request.n_samples)
            feature_names = feature_extractor.feature_names
        else:
            # Load real data from database
            logger.info("Loading real training data from database...")
            data_loader = get_data_loader()
            
            if data_loader is None:
                raise HTTPException(status_code=500, detail="Database connection not available")
            
            X, y = data_loader.fetch_training_data(min_impressions=100)
            
            if X is None or len(X) == 0:
                raise HTTPException(
                    status_code=400, 
                    detail="No training data found. Ensure videos table has performance data."
                )
            
            feature_names = feature_extractor.feature_names

        # Train model
        logger.info("Training XGBoost model...")
        metrics = ctr_predictor.train(X, y, feature_names=feature_names)

        return {
            "status": "success",
            "message": "Model trained successfully",
            "metrics": metrics
        }

    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/model-info")
async def get_model_info():
    """Get information about the trained model"""
    try:
        info = ctr_predictor.get_model_info()
        return info
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/feature-importance")
async def get_feature_importance():
    """Get feature importance from trained XGBoost model"""
    try:
        if not ctr_predictor.is_trained:
            raise HTTPException(status_code=400, detail="Model not trained")

        importance_df = ctr_predictor.get_feature_importance()

        return {
            "feature_importance": importance_df.to_dict(orient='records')
        }

    except Exception as e:
        logger.error(f"Error getting feature importance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Thompson Sampling A/B Testing Endpoints (Agent 7-8)

class VariantRegistration(BaseModel):
    """Request model for registering a new variant"""
    variant_id: str
    metadata: Optional[Dict[str, Any]] = None


class VariantSelection(BaseModel):
    """Request model for selecting a variant"""
    context: Optional[Dict[str, Any]] = None
    available_variants: Optional[List[str]] = None


class VariantUpdate(BaseModel):
    """Request model for updating variant performance"""
    variant_id: str
    reward: float
    cost: float = 0.0
    context: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, float]] = None


class BudgetAllocation(BaseModel):
    """Request model for budget reallocation"""
    total_budget: float
    min_budget_per_variant: float = 0.0


@app.post("/api/ml/ab/register-variant")
async def register_variant(request: VariantRegistration):
    """Register a new A/B test variant (Agent 7)"""
    try:
        thompson_optimizer.register_variant(
            variant_id=request.variant_id,
            metadata=request.metadata
        )
        return {
            "status": "success",
            "variant_id": request.variant_id,
            "message": "Variant registered successfully"
        }
    except Exception as e:
        logger.error(f"Error registering variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/ab/select-variant")
async def select_variant(request: VariantSelection):
    """Select best variant using Thompson Sampling (Agent 7)"""
    try:
        selection = thompson_optimizer.select_variant(
            context=request.context,
            available_variants=request.available_variants
        )
        return selection
    except Exception as e:
        logger.error(f"Error selecting variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/ab/update-variant")
async def update_variant(request: VariantUpdate):
    """Update variant with observed performance (Agent 7)"""
    try:
        thompson_optimizer.update(
            variant_id=request.variant_id,
            reward=request.reward,
            cost=request.cost,
            context=request.context,
            metrics=request.metrics
        )
        return {
            "status": "success",
            "variant_id": request.variant_id,
            "message": "Variant updated successfully"
        }
    except Exception as e:
        logger.error(f"Error updating variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/ab/variant-stats/{variant_id}")
async def get_variant_stats(variant_id: str):
    """Get statistics for a specific variant (Agent 7)"""
    try:
        stats = thompson_optimizer.get_variant_stats(variant_id)
        return stats
    except Exception as e:
        logger.error(f"Error getting variant stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/ab/all-variants")
async def get_all_variants():
    """Get statistics for all variants (Agent 7)"""
    try:
        stats = thompson_optimizer.get_all_variants_stats()
        return {"variants": stats}
    except Exception as e:
        logger.error(f"Error getting all variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/ab/best-variant")
async def get_best_variant():
    """Get the best performing variant (Agent 7)"""
    try:
        best = thompson_optimizer.get_best_variant()
        return best
    except Exception as e:
        logger.error(f"Error getting best variant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/ab/reallocate-budget")
async def reallocate_budget(request: BudgetAllocation):
    """Reallocate budget based on variant performance (Agent 8)"""
    try:
        allocations = thompson_optimizer.reallocate_budget(
            total_budget=request.total_budget,
            min_budget_per_variant=request.min_budget_per_variant
        )
        return {
            "status": "success",
            "allocations": allocations,
            "total_budget": request.total_budget
        }
    except Exception as e:
        logger.error(f"Error reallocating budget: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Feedback Loop Endpoints (Agent 5)

class FeedbackData(BaseModel):
    """Request model for performance feedback"""
    ad_id: str
    variant_id: str
    impressions: int
    clicks: int
    conversions: int = 0


async def trigger_retrain():
    """Trigger model retraining with accumulated feedback data"""
    global feedback_store

    logger.info(f"Triggering retraining with {len(feedback_store)} feedback samples...")

    try:
        # Load real data from database
        data_loader = get_data_loader()

        if data_loader is None:
            logger.warning("Database connection not available, skipping retrain")
            return False

        X, y = data_loader.fetch_training_data(min_impressions=10)

        if X is None or len(X) < 50:
            logger.warning(f"Not enough training data ({len(X) if X is not None else 0} samples). Need at least 50.")
            return False

        # Train model
        metrics = ctr_predictor.train(X, y, feature_names=feature_extractor.feature_names)

        logger.info(f"Model retrained: Test Accuracy = {metrics['test_accuracy']:.2%}, Test R² = {metrics['test_r2']:.4f}")

        # Clear feedback store after successful training
        feedback_store.clear()

        return True

    except Exception as e:
        logger.error(f"Error during retraining: {e}")
        return False


@app.post("/api/ml/feedback")
async def record_feedback(data: FeedbackData):
    """
    Record real performance and trigger learning (Agent 5)

    This endpoint receives performance data from the ad system and:
    1. Updates Thompson Sampler with the reward
    2. Stores feedback for XGBoost retraining
    3. Triggers retraining when enough samples accumulated
    """
    try:
        # Calculate CTR from actual performance
        ctr = data.clicks / data.impressions if data.impressions > 0 else 0.0
        cvr = data.conversions / data.clicks if data.clicks > 0 else 0.0

        # Update Thompson Sampler with reward (CTR as reward signal)
        thompson_optimizer.update(
            variant_id=data.variant_id,
            reward=ctr,
            metrics={
                'impressions': data.impressions,
                'clicks': data.clicks,
                'conversions': data.conversions
            }
        )

        # Store for retraining
        feedback_entry = {
            "ad_id": data.ad_id,
            "variant_id": data.variant_id,
            "ctr": ctr,
            "cvr": cvr,
            "impressions": data.impressions,
            "clicks": data.clicks,
            "conversions": data.conversions,
            "timestamp": datetime.utcnow().isoformat()
        }
        feedback_store.append(feedback_entry)

        logger.info(f"Feedback recorded for variant {data.variant_id}: CTR={ctr:.4f}, CVR={cvr:.4f}")

        # Check if retraining needed (every 100 samples)
        retrain_triggered = False
        if len(feedback_store) >= 100:
            logger.info("Feedback threshold reached (100 samples), triggering retrain...")
            retrain_triggered = await trigger_retrain()

        return {
            "status": "recorded",
            "ctr": ctr,
            "cvr": cvr,
            "feedback_count": len(feedback_store),
            "retrain_triggered": retrain_triggered
        }

    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/stats")
async def get_feedback_stats():
    """
    Get feedback loop status and statistics (Agent 5)

    Returns information about:
    - Feedback samples collected
    - Thompson Sampler variant performance
    - XGBoost model training status
    - System health metrics
    """
    try:
        # Get Thompson Sampler stats
        all_variants = thompson_optimizer.get_all_variants_stats()

        # Calculate aggregate stats
        total_impressions = sum(v['impressions'] for v in all_variants)
        total_clicks = sum(v['clicks'] for v in all_variants)
        total_conversions = sum(v['conversions'] for v in all_variants)

        overall_ctr = total_clicks / total_impressions if total_impressions > 0 else 0.0
        overall_cvr = total_conversions / total_clicks if total_clicks > 0 else 0.0

        # Get best performing variant
        best_variant = thompson_optimizer.get_best_variant() if all_variants else None

        return {
            "feedback_loop": {
                "samples_collected": len(feedback_store),
                "next_retrain_at": 100,
                "samples_until_retrain": max(0, 100 - len(feedback_store))
            },
            "thompson_sampler": {
                "active_variants": len(all_variants),
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "overall_ctr": overall_ctr,
                "overall_cvr": overall_cvr,
                "best_variant": best_variant
            },
            "xgboost_model": {
                "is_trained": ctr_predictor.is_trained,
                "training_metrics": ctr_predictor.training_metrics,
                "feature_count": len(ctr_predictor.feature_names)
            },
            "system_health": {
                "ml_service": "healthy",
                "feedback_loop": "active",
                "learning_mode": "real_data"
            }
        }

    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("ML Service starting up...")
    logger.info("Feedback loop enabled - system will learn from real data")

    # Try to load existing model or train with real data from database
    if not ctr_predictor.is_trained:
        logger.info("No trained model found. Attempting to train with real data from database...")
        try:
            data_loader = get_data_loader()

            if data_loader is not None:
                X, y = data_loader.fetch_training_data(min_impressions=10)

                if X is not None and len(X) >= 50:
                    metrics = ctr_predictor.train(X, y, feature_names=feature_extractor.feature_names)
                    logger.info(f"Model trained on startup with real data: Test Accuracy = {metrics['test_accuracy']:.2%}")
                else:
                    logger.warning(f"Not enough real training data ({len(X) if X is not None else 0} samples). Model will train once feedback is collected.")
            else:
                logger.warning("Database connection not available. Model will train once feedback is collected.")
        except Exception as e:
            logger.warning(f"Failed to train model on startup: {e}. Model will train once feedback is collected.")
    else:
        logger.info("Model loaded successfully from disk")

    # Start automated retraining scheduler
    try:
        from src.training_scheduler import training_scheduler
        training_scheduler.start()
        logger.info("Training scheduler started")
    except ImportError:
        logger.warning("Training scheduler not available")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
