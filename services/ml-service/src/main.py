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

# Import ML components
from src.feature_engineering import feature_extractor
from src.ctr_model import ctr_predictor, generate_synthetic_training_data
from src.thompson_sampler import thompson_optimizer
from src.data_loader import get_data_loader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        "endpoints": {
            "health": "/health",
            "predict_ctr": "/api/ml/predict-ctr",
            "predict_ctr_batch": "/api/ml/predict-ctr/batch",
            "train_model": "/api/ml/train",
            "model_info": "/api/ml/model-info",
            "feature_importance": "/api/ml/feature-importance"
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


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("ML Service starting up...")

    # Try to load existing model or train with synthetic data
    if not ctr_predictor.is_trained:
        logger.info("No trained model found. Training with synthetic data...")
        try:
            X, y = generate_synthetic_training_data(n_samples=1000)
            metrics = ctr_predictor.train(X, y, feature_names=feature_extractor.feature_names)
            logger.info(f"Model trained on startup: Test Accuracy = {metrics['test_accuracy']:.2%}")
        except Exception as e:
            logger.warning(f"Failed to train model on startup: {e}")
    else:
        logger.info("Model loaded successfully from disk")
    
    # Start automated retraining scheduler
    from src.training_scheduler import training_scheduler
    training_scheduler.start()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
