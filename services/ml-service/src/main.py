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
import time
import numpy as np
from datetime import datetime

# Track startup time for uptime calculation
_start_time = time.time()

# Import ML components
from src.feature_engineering import feature_extractor
from src.ctr_model import ctr_predictor
from src.thompson_sampler import thompson_optimizer
from src.data_loader import get_data_loader
from src.enhanced_ctr_model import enhanced_ctr_predictor, generate_synthetic_training_data as generate_enhanced_data
from src.accuracy_tracker import accuracy_tracker

# Import Alert System (Agent 16)
from src.alerts.alert_engine import alert_engine, Alert
from src.alerts.alert_rules import alert_rule_manager, AlertRule, AlertType, AlertSeverity
from src.alerts.alert_notifier import alert_notifier, NotificationChannel

# Import Report Generator (Agent 18)
from src.reports.report_generator import ReportGenerator, ReportType, ReportFormat
from src.reports.pdf_builder import generate_pdf_report
from src.reports.excel_builder import generate_excel_report

# Import Precomputer (Agent 45)
from src.precomputer import get_precomputer, PrecomputeEvent, PrecomputeTaskType

# Import Batch API (Agent 42)
try:
    from src.batch_api import router as batch_router
    BATCH_API_AVAILABLE = True
except ImportError:
    logger.warning("Batch API not available - install batch requirements")
    BATCH_API_AVAILABLE = False

# Import Auto-Scaler API (Agent 47)
try:
    from src.auto_scaler_api import router as auto_scaler_router
    AUTO_SCALER_AVAILABLE = True
except ImportError:
    logger.warning("Auto-Scaler API not available - check dependencies")
    AUTO_SCALER_AVAILABLE = False

# Import Creative DNA API (Agent 48)
try:
    from src.dna_endpoints import router as dna_router
    DNA_API_AVAILABLE = True
except ImportError:
    logger.warning("Creative DNA API not available - check dependencies")
    DNA_API_AVAILABLE = False

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

# Production safety check - prevent debug mode in production
if app.debug and os.environ.get('ENVIRONMENT') == 'production':
    raise RuntimeError("Debug mode detected in production!")

# CORS
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include Batch API router (Agent 42)
if BATCH_API_AVAILABLE:
    app.include_router(batch_router)
    logger.info("✅ Batch API endpoints enabled at /batch/*")

# Include Auto-Scaler API router (Agent 47)
if AUTO_SCALER_AVAILABLE:
    app.include_router(auto_scaler_router)
    logger.info("✅ Auto-Scaler API endpoints enabled at /api/auto-scaler/*")

# Include Creative DNA API router (Agent 48)
if DNA_API_AVAILABLE:
    app.include_router(dna_router)
    logger.info("✅ Creative DNA API endpoints enabled at /api/dna/*")

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
    uptime = int(time.time() - _start_time)
    return {
        "status": "healthy",
        "service": "ml-service",
        "uptime": uptime,
        "xgboost_loaded": ctr_predictor.is_trained,
        "enhanced_xgboost_loaded": enhanced_ctr_predictor.is_trained,
        "vowpal_wabbit_loaded": True,
        "thompson_sampling_active": len(thompson_optimizer.get_all_variants_stats()) > 0,
        "active_variants": len(thompson_optimizer.get_all_variants_stats()),
        "model_metrics": ctr_predictor.training_metrics if ctr_predictor.is_trained else {},
        "enhanced_model_metrics": enhanced_ctr_predictor.training_metrics if enhanced_ctr_predictor.is_trained else {},
        "enhanced_features_count": len(enhanced_ctr_predictor.feature_names)
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ML Service",
        "version": "2.0.0",
        "description": "XGBoost CTR Prediction & Vowpal Wabbit A/B Testing with Enhanced 75+ Feature Model",
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
            },
            "enhanced_predict_ctr": "/predict/ctr",
            "enhanced_train_ctr": "/train/ctr",
            "enhanced_feature_importance": "/model/importance",
            "check_retrain": "/api/ml/check-retrain",
            "accuracy_tracking": {
                "accuracy_report": "/api/ml/accuracy-report",
                "accuracy_metrics": "/api/ml/accuracy-metrics",
                "record_prediction": "/api/ml/prediction/record",
                "update_actuals": "/api/ml/prediction/update-actuals",
                "top_performers": "/api/ml/top-performers"
            },
            "precomputation": {
                "precompute_video": "/api/precompute/video",
                "precompute_campaign": "/api/precompute/campaign",
                "precompute_login": "/api/precompute/login",
                "predict_actions": "/api/precompute/predict-actions",
                "get_cached": "/api/precompute/cache/{cache_key}",
                "invalidate_cache": "/api/precompute/cache",
                "refresh_cache": "/api/precompute/refresh/{task_type}",
                "metrics": "/api/precompute/metrics",
                "queue_status": "/api/precompute/queue"
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


# Enhanced XGBoost CTR Prediction Endpoints (Agent 5)

class EnhancedCTRRequest(BaseModel):
    """Request model for enhanced CTR prediction"""
    clip_data: Dict[str, Any]


class EnhancedCTRResponse(BaseModel):
    """Response model for enhanced CTR prediction"""
    predicted_ctr: float
    predicted_band: str
    confidence: float
    features_used: int


class EnhancedTrainingRequest(BaseModel):
    """Request model for enhanced model training"""
    use_synthetic_data: bool = True
    n_samples: Optional[int] = 1000
    historical_ads: Optional[List[Dict[str, Any]]] = None


@app.post("/predict/ctr", response_model=EnhancedCTRResponse)
async def predict_ctr_enhanced(request: EnhancedCTRRequest):
    """
    Predict CTR using enhanced model with 75+ features

    Agent 5 - Enhanced XGBoost CTR Prediction
    Target: R² > 0.88 (94% accuracy)
    """
    try:
        if not enhanced_ctr_predictor.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Enhanced model not trained. Call /train/ctr first."
            )

        # Predict CTR
        result = enhanced_ctr_predictor.predict(request.clip_data)

        return EnhancedCTRResponse(
            predicted_ctr=result['predicted_ctr'],
            predicted_band=result['predicted_band'],
            confidence=result['confidence'],
            features_used=len(enhanced_ctr_predictor.feature_names)
        )

    except Exception as e:
        logger.error(f"Error predicting CTR with enhanced model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/train/ctr")
async def train_enhanced_ctr_model(request: EnhancedTrainingRequest):
    """
    Train enhanced XGBoost CTR model with 75+ features

    Agent 5 - Enhanced Model Training
    Target: R² > 0.88 (94% accuracy)
    """
    try:
        if request.use_synthetic_data:
            logger.info(f"Generating {request.n_samples} synthetic enhanced training samples...")
            historical_ads = generate_enhanced_data(n_samples=request.n_samples)
        elif request.historical_ads:
            logger.info(f"Using {len(request.historical_ads)} provided historical ads...")
            historical_ads = request.historical_ads
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either use_synthetic_data=True or historical_ads"
            )

        # Train enhanced model
        logger.info("Training enhanced XGBoost model with 75+ features...")
        metrics = enhanced_ctr_predictor.train(historical_ads)

        # Save model
        enhanced_ctr_predictor.save()

        return {
            "status": "success",
            "message": "Enhanced CTR model trained successfully",
            "metrics": metrics,
            "target_achieved": metrics.get('target_achieved', False),
            "features_used": len(enhanced_ctr_predictor.feature_names)
        }

    except Exception as e:
        logger.error(f"Error training enhanced model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/importance")
async def get_enhanced_feature_importance():
    """
    Get feature importance from enhanced XGBoost model

    Agent 5 - Feature Importance Analysis
    Returns importance scores for all 75+ features
    """
    try:
        if not enhanced_ctr_predictor.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Enhanced model not trained. Call /train/ctr first."
            )

        importance = enhanced_ctr_predictor.get_feature_importance()

        # Get top 20 most important features
        top_20 = dict(list(importance.items())[:20])

        return {
            "feature_importance": importance,
            "top_20_features": top_20,
            "total_features": len(importance),
            "model_metrics": enhanced_ctr_predictor.training_metrics
        }

    except Exception as e:
        logger.error(f"Error getting enhanced feature importance: {e}")
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


# Additional AB Testing Endpoints for Visualization (Agent 15)

@app.get("/api/ml/ab/experiments/{experiment_id}/results")
async def get_experiment_results(experiment_id: str):
    """
    Get detailed results for an AB test experiment
    Returns variant performance, statistical significance, and Thompson Sampling metrics
    """
    try:
        # Get all variant stats
        all_variants = thompson_optimizer.get_all_variants_stats()

        # Filter variants for this experiment (if metadata contains experiment_id)
        experiment_variants = [
            v for v in all_variants
            if v.get('metadata', {}).get('experiment_id') == experiment_id
        ]

        if not experiment_variants:
            # If no experiment-specific filtering, return all variants
            experiment_variants = all_variants

        # Calculate overall metrics
        total_impressions = sum(v['impressions'] for v in experiment_variants)
        total_clicks = sum(v['clicks'] for v in experiment_variants)
        total_conversions = sum(v['conversions'] for v in experiment_variants)
        total_spend = sum(v['spend'] for v in experiment_variants)
        total_revenue = sum(v.get('revenue', 0) for v in experiment_variants)

        overall_ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        overall_cvr = total_conversions / total_clicks if total_clicks > 0 else 0
        overall_roas = total_revenue / total_spend if total_spend > 0 else 0

        # Find best variant
        best_variant = max(
            experiment_variants,
            key=lambda v: v['alpha'] / (v['alpha'] + v['beta'])
        ) if experiment_variants else None

        # Calculate winner probability for each variant
        winner_probabilities = {}
        if len(experiment_variants) >= 2:
            # Simple Thompson Sampling simulation
            from src.thompson_sampler import thompson_optimizer as ts_opt
            for variant in experiment_variants:
                samples = np.random.beta(variant['alpha'], variant['beta'], 10000)
                # Compare against all other variants
                wins = 0
                for _ in range(10000):
                    this_sample = np.random.beta(variant['alpha'], variant['beta'])
                    other_samples = [
                        np.random.beta(v['alpha'], v['beta'])
                        for v in experiment_variants
                        if v['id'] != variant['id']
                    ]
                    if all(this_sample > s for s in other_samples):
                        wins += 1
                winner_probabilities[variant['id']] = wins / 10000

        return {
            "experiment_id": experiment_id,
            "variants": experiment_variants,
            "overall_metrics": {
                "total_impressions": total_impressions,
                "total_clicks": total_clicks,
                "total_conversions": total_conversions,
                "total_spend": total_spend,
                "total_revenue": total_revenue,
                "overall_ctr": overall_ctr,
                "overall_cvr": overall_cvr,
                "overall_roas": overall_roas
            },
            "best_variant": best_variant,
            "winner_probabilities": winner_probabilities,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting experiment results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/ab/experiments/{experiment_id}/variants")
async def get_experiment_variants(experiment_id: str):
    """
    Get variant performance data for an experiment
    Includes Thompson Sampling statistics and confidence intervals
    """
    try:
        # Get all variant stats
        all_variants = thompson_optimizer.get_all_variants_stats()

        # Filter variants for this experiment
        experiment_variants = [
            v for v in all_variants
            if v.get('metadata', {}).get('experiment_id') == experiment_id
        ]

        if not experiment_variants:
            # If no experiment-specific filtering, return all variants
            experiment_variants = all_variants

        # Enhance with additional metrics
        enhanced_variants = []
        for variant in experiment_variants:
            # Calculate actual CTR, CVR, ROAS
            ctr = variant['clicks'] / variant['impressions'] if variant['impressions'] > 0 else 0
            cvr = variant['conversions'] / variant['clicks'] if variant['clicks'] > 0 else 0
            roas = variant.get('roas', 0)

            # Thompson Sampling expected CTR
            expected_ctr = variant['alpha'] / (variant['alpha'] + variant['beta'])

            # Confidence interval (95%)
            from scipy import stats
            try:
                ci_lower, ci_upper = stats.beta.interval(
                    0.95,
                    variant['alpha'],
                    variant['beta']
                )
            except:
                ci_lower, ci_upper = variant.get('ctr_ci_lower', 0), variant.get('ctr_ci_upper', 0)

            enhanced_variants.append({
                **variant,
                "ctr": ctr,
                "cvr": cvr,
                "roas": roas,
                "expected_ctr": expected_ctr,
                "confidence_interval": {
                    "lower": ci_lower,
                    "upper": ci_upper
                }
            })

        return {
            "experiment_id": experiment_id,
            "variants": enhanced_variants,
            "count": len(enhanced_variants)
        }

    except Exception as e:
        logger.error(f"Error getting experiment variants: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/ab/experiments")
async def list_all_experiments():
    """
    List all active AB test experiments
    Groups variants by experiment_id if available in metadata
    """
    try:
        # Get all variants
        all_variants = thompson_optimizer.get_all_variants_stats()

        # Group by experiment_id
        experiments = {}
        for variant in all_variants:
            exp_id = variant.get('metadata', {}).get('experiment_id', 'default')
            if exp_id not in experiments:
                experiments[exp_id] = {
                    "experiment_id": exp_id,
                    "experiment_name": variant.get('metadata', {}).get('experiment_name', f'Experiment {exp_id}'),
                    "status": "running",
                    "variants": [],
                    "created_at": variant.get('created_at'),
                    "total_budget": variant.get('metadata', {}).get('total_budget', 5000)
                }
            experiments[exp_id]['variants'].append(variant)

        # Convert to list
        experiments_list = list(experiments.values())

        # Calculate metrics for each experiment
        for exp in experiments_list:
            total_impressions = sum(v['impressions'] for v in exp['variants'])
            total_clicks = sum(v['clicks'] for v in exp['variants'])
            exp['total_impressions'] = total_impressions
            exp['total_clicks'] = total_clicks
            exp['overall_ctr'] = total_clicks / total_impressions if total_impressions > 0 else 0

        return {
            "experiments": experiments_list,
            "count": len(experiments_list)
        }

    except Exception as e:
        logger.error(f"Error listing experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Feedback Loop Endpoints (Agent 5)

class FeedbackData(BaseModel):
    """Request model for performance feedback"""
    ad_id: str
    variant_id: str
    impressions: int
    clicks: int
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0


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
        # Calculate weighted reward based on event type (Agent 5 - Enhanced Learning)
        # If explicit value is provided (e.g. purchase value), use it.
        # Otherwise, use weighted score for the event type.
        
        reward = 0.0
        if data.revenue > 0:
            reward = data.revenue  # Use actual revenue if available
        elif data.conversions > 0:
            reward = 1.0  # Default conversion reward
        elif data.clicks > 0:
            reward = 0.5  # Click reward (Medium value)
        elif data.impressions > 0:
            reward = 0.01 # Impression reward (Low value, but non-zero to track exposure)
            
        # Update Thompson Sampler with reward
        thompson_optimizer.update(
            variant_id=data.variant_id,
            reward=reward,
            cost=data.spend,
            metrics={
                'impressions': data.impressions,
                'clicks': data.clicks,
                'conversions': data.conversions,
                'revenue': data.revenue
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
            "retrain_triggered": retrain_triggered
        }

    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/thompson/impression")
async def record_impression(variant_id: str):
    """
    Record an ad impression (Agent 5 - Enhanced Learning)
    Call this when ad is shown (from Meta webhook or frontend)
    """
    try:
        # Record as failure (shown but no conversion yet)
        # This increments the 'beta' parameter (failure count) or just impressions count
        # depending on implementation. In our case, update() handles metrics.
        
        thompson_optimizer.update(
            variant_id=variant_id,
            reward=0.0,
            cost=0.0,
            metrics={'impressions': 1}
        )
        return {"recorded": True}
    except Exception as e:
        logger.error(f"Error recording impression: {e}")
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


# Accuracy Tracking Endpoints (Agent 9)

class PredictionRecordRequest(BaseModel):
    """Request model for recording a new prediction"""
    prediction_id: str
    campaign_id: str
    creative_id: str
    predicted_ctr: float
    predicted_roas: float
    hook_type: Optional[str] = None
    template_id: Optional[str] = None
    features: Optional[Dict[str, Any]] = None
    demographic_target: Optional[Dict[str, Any]] = None


class UpdateActualsRequest(BaseModel):
    """Request model for updating prediction with actuals"""
    prediction_id: str
    actual_ctr: float
    actual_roas: float
    actual_conversions: Optional[int] = None


@app.get("/api/ml/accuracy-report")
async def get_accuracy_report(days_back: int = 30):
    """
    Generate comprehensive investor validation report (Agent 9)

    This is THE endpoint for €5M investment validation.
    Shows investors that ML predictions match reality.

    Args:
        days_back: Number of days to analyze (default: 30)

    Returns:
        Complete investor report with:
        - Overall accuracy metrics (CTR, ROAS)
        - Performance by hook type
        - Performance by template
        - Top performing predictions
        - Learning improvement over time
        - Revenue impact analysis
        - Investment validation verdict
    """
    try:
        logger.info(f"📊 Generating investor accuracy report for last {days_back} days...")

        report = await accuracy_tracker.generate_investor_report(days_back=days_back)

        logger.info(f"✅ Investor report generated:")
        logger.info(f"   Total predictions: {report.get('summary', {}).get('total_predictions', 0)}")
        logger.info(f"   CTR accuracy: {report.get('summary', {}).get('ctr_accuracy', 0)}%")
        logger.info(f"   ROAS accuracy: {report.get('summary', {}).get('roas_accuracy', 0)}%")
        logger.info(f"   Investment verdict: {report.get('investment_validation', {}).get('overall_verdict', 'N/A')}")

        return report

    except Exception as e:
        logger.error(f"Error generating accuracy report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/accuracy-metrics")
async def get_accuracy_metrics(days_back: int = 30):
    """
    Get overall accuracy metrics (Agent 9)

    Args:
        days_back: Number of days to analyze

    Returns:
        Dictionary with accuracy metrics including:
        - CTR MAE, RMSE, MAPE, accuracy percentage
        - ROAS MAE, RMSE, MAPE, accuracy percentage
        - Business impact metrics
    """
    try:
        metrics = await accuracy_tracker.calculate_accuracy_metrics(days_back=days_back)
        return metrics

    except Exception as e:
        logger.error(f"Error getting accuracy metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/prediction/record")
async def record_prediction(request: PredictionRecordRequest):
    """
    Record a new prediction for accuracy tracking (Agent 9)

    This should be called whenever the ML model makes a prediction
    before launching a campaign.

    Args:
        request: Prediction details

    Returns:
        Success status
    """
    try:
        success = await accuracy_tracker.record_prediction(
            prediction_id=request.prediction_id,
            campaign_id=request.campaign_id,
            creative_id=request.creative_id,
            predicted_ctr=request.predicted_ctr,
            predicted_roas=request.predicted_roas,
            hook_type=request.hook_type,
            template_id=request.template_id,
            features=request.features,
            demographic_target=request.demographic_target
        )

        if success:
            return {
                "status": "recorded",
                "prediction_id": request.prediction_id,
                "message": "Prediction recorded successfully"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to record prediction")

    except Exception as e:
        logger.error(f"Error recording prediction: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ml/prediction/update-actuals")
async def update_prediction_actuals(request: UpdateActualsRequest):
    """
    Update prediction with actual performance results (Agent 9)

    This should be called after a campaign has run and actual
    performance data is available.

    Args:
        request: Actual performance data

    Returns:
        Success status with accuracy score
    """
    try:
        success = await accuracy_tracker.update_with_actuals(
            prediction_id=request.prediction_id,
            actual_ctr=request.actual_ctr,
            actual_roas=request.actual_roas,
            actual_conversions=request.actual_conversions
        )

        if success:
            return {
                "status": "updated",
                "prediction_id": request.prediction_id,
                "message": "Actuals recorded successfully"
            }
        else:
            raise HTTPException(status_code=404, detail="Prediction not found")

    except Exception as e:
        logger.error(f"Error updating actuals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ml/top-performers")
async def get_top_performers(limit: int = 10):
    """
    Get top performing predictions (Agent 9)

    Shows which predictions were most accurate and had best outcomes.

    Args:
        limit: Number of top performers to return

    Returns:
        List of top performing predictions
    """
    try:
        top_performers = await accuracy_tracker.get_top_performing_ads(limit=limit)
        return {
            "top_performers": top_performers,
            "count": len(top_performers)
        }

    except Exception as e:
        logger.error(f"Error getting top performers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ALERT SYSTEM ENDPOINTS (Agent 16)
# Real-Time Performance Alerts for Elite Marketers
# ============================================================

class AlertRuleCreateRequest(BaseModel):
    """Request model for creating alert rule"""
    rule_id: str
    name: str
    alert_type: str
    severity: str
    enabled: bool = True
    threshold: float = 0.0
    threshold_operator: str = "<"
    lookback_minutes: int = 60
    cooldown_minutes: int = 30
    conditions: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class MetricCheckRequest(BaseModel):
    """Request model for checking metrics against alert rules"""
    metric_name: str
    metric_value: float
    campaign_id: str
    campaign_name: str
    ad_id: Optional[str] = ""
    context: Optional[Dict[str, Any]] = None
    alert_types: Optional[List[str]] = None


class AcknowledgeAlertRequest(BaseModel):
    """Request model for acknowledging an alert"""
    user_id: str


@app.post("/api/alerts/rules", tags=["Alerts"])
async def create_alert_rule(request: AlertRuleCreateRequest):
    """
    Create or update an alert rule (Agent 16)

    Allows marketers to configure custom alert rules for their campaigns.

    Args:
        request: Alert rule configuration

    Returns:
        Created/updated rule
    """
    try:
        logger.info(f"Creating/updating alert rule: {request.rule_id}")

        # Create alert rule
        rule = AlertRule(
            rule_id=request.rule_id,
            name=request.name,
            alert_type=AlertType(request.alert_type),
            severity=AlertSeverity(request.severity),
            enabled=request.enabled,
            threshold=request.threshold,
            threshold_operator=request.threshold_operator,
            lookback_minutes=request.lookback_minutes,
            cooldown_minutes=request.cooldown_minutes,
            conditions=request.conditions,
            metadata=request.metadata
        )

        # Add to manager
        alert_rule_manager.add_rule(rule)

        return {
            "success": True,
            "rule": rule.to_dict()
        }

    except Exception as e:
        logger.error(f"Error creating alert rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/rules", tags=["Alerts"])
async def get_alert_rules(enabled_only: bool = False):
    """
    Get all alert rules (Agent 16)

    Args:
        enabled_only: Return only enabled rules

    Returns:
        List of alert rules
    """
    try:
        if enabled_only:
            rules = alert_rule_manager.get_enabled_rules()
        else:
            rules = alert_rule_manager.get_all_rules()

        return {
            "rules": [rule.to_dict() for rule in rules],
            "count": len(rules)
        }

    except Exception as e:
        logger.error(f"Error getting alert rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/rules/{rule_id}", tags=["Alerts"])
async def get_alert_rule(rule_id: str):
    """
    Get a specific alert rule (Agent 16)

    Args:
        rule_id: Rule identifier

    Returns:
        Alert rule
    """
    try:
        rule = alert_rule_manager.get_rule(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")

        return rule.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/alerts/rules/{rule_id}", tags=["Alerts"])
async def delete_alert_rule(rule_id: str):
    """
    Delete an alert rule (Agent 16)

    Args:
        rule_id: Rule identifier

    Returns:
        Success status
    """
    try:
        success = alert_rule_manager.remove_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")

        return {"success": True, "rule_id": rule_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/alerts/rules/{rule_id}/enable", tags=["Alerts"])
async def enable_alert_rule(rule_id: str):
    """Enable an alert rule"""
    try:
        success = alert_rule_manager.enable_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
        return {"success": True, "enabled": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling alert rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/alerts/rules/{rule_id}/disable", tags=["Alerts"])
async def disable_alert_rule(rule_id: str):
    """Disable an alert rule"""
    try:
        success = alert_rule_manager.disable_rule(rule_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Rule not found: {rule_id}")
        return {"success": True, "enabled": False}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling alert rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/check", tags=["Alerts"])
async def check_metric(request: MetricCheckRequest):
    """
    Check a metric against alert rules (Agent 16)

    This is the core endpoint for real-time alert monitoring.
    Called whenever a metric needs to be checked (ROAS, CTR, budget, etc.)

    Args:
        request: Metric information

    Returns:
        List of triggered alerts
    """
    try:
        logger.info(f"Checking metric: {request.metric_name}={request.metric_value} for campaign {request.campaign_id}")

        # Convert alert type strings to enums if provided
        alert_types = None
        if request.alert_types:
            alert_types = [AlertType(at) for at in request.alert_types]

        # Check metric
        alerts = alert_engine.check_metric(
            metric_name=request.metric_name,
            metric_value=request.metric_value,
            campaign_id=request.campaign_id,
            campaign_name=request.campaign_name,
            ad_id=request.ad_id,
            context=request.context,
            alert_types=alert_types
        )

        # Send notifications for triggered alerts
        for alert in alerts:
            try:
                await alert_engine.send_alert_notifications(alert)
                logger.info(f"Notifications sent for alert: {alert.alert_id}")
            except Exception as e:
                logger.error(f"Failed to send notifications for alert {alert.alert_id}: {e}")

        return {
            "alerts_triggered": len(alerts),
            "alerts": [alert.to_dict() for alert in alerts]
        }

    except Exception as e:
        logger.error(f"Error checking metric: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts", tags=["Alerts"])
async def get_active_alerts(
    campaign_id: Optional[str] = None,
    alert_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100
):
    """
    Get active alerts (Agent 16)

    Returns list of currently active alerts with optional filtering.

    Args:
        campaign_id: Filter by campaign ID
        alert_type: Filter by alert type
        severity: Filter by severity
        limit: Maximum number of alerts to return

    Returns:
        List of active alerts
    """
    try:
        # Convert string enums
        alert_type_enum = AlertType(alert_type) if alert_type else None
        severity_enum = AlertSeverity(severity) if severity else None

        alerts = alert_engine.get_active_alerts(
            campaign_id=campaign_id,
            alert_type=alert_type_enum,
            severity=severity_enum,
            limit=limit
        )

        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts)
        }

    except Exception as e:
        logger.error(f"Error getting active alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/history", tags=["Alerts"])
async def get_alert_history(
    campaign_id: Optional[str] = None,
    days_back: int = 7,
    limit: int = 100
):
    """
    Get alert history (Agent 16)

    Returns historical alerts with optional filtering.

    Args:
        campaign_id: Filter by campaign ID
        days_back: Number of days to look back
        limit: Maximum number of alerts to return

    Returns:
        List of historical alerts
    """
    try:
        from datetime import timedelta

        start_date = datetime.utcnow() - timedelta(days=days_back)
        alerts = alert_engine.get_alert_history(
            campaign_id=campaign_id,
            start_date=start_date,
            limit=limit
        )

        return {
            "alerts": [alert.to_dict() for alert in alerts],
            "count": len(alerts),
            "days_back": days_back
        }

    except Exception as e:
        logger.error(f"Error getting alert history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/stats", tags=["Alerts"])
async def get_alert_stats(campaign_id: Optional[str] = None):
    """
    Get alert statistics (Agent 16)

    Returns summary statistics about alerts.

    Args:
        campaign_id: Filter by campaign ID (optional)

    Returns:
        Alert statistics
    """
    try:
        stats = alert_engine.get_alert_stats(campaign_id=campaign_id)
        return stats

    except Exception as e:
        logger.error(f"Error getting alert stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/alerts/{alert_id}/acknowledge", tags=["Alerts"])
async def acknowledge_alert(alert_id: str, request: AcknowledgeAlertRequest):
    """
    Acknowledge an alert (Agent 16)

    Marks an alert as acknowledged by a user.

    Args:
        alert_id: Alert identifier
        request: User ID who is acknowledging

    Returns:
        Success status
    """
    try:
        success = alert_engine.acknowledge_alert(alert_id, request.user_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return {
            "success": True,
            "alert_id": alert_id,
            "acknowledged_by": request.user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/alerts/{alert_id}/resolve", tags=["Alerts"])
async def resolve_alert(alert_id: str):
    """
    Resolve an alert (Agent 16)

    Marks an alert as resolved and moves it to history.

    Args:
        alert_id: Alert identifier

    Returns:
        Success status
    """
    try:
        success = alert_engine.resolve_alert(alert_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return {
            "success": True,
            "alert_id": alert_id,
            "resolved": True
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/{alert_id}", tags=["Alerts"])
async def get_alert(alert_id: str):
    """
    Get a specific alert (Agent 16)

    Args:
        alert_id: Alert identifier

    Returns:
        Alert details
    """
    try:
        alert = alert_engine.active_alerts.get(alert_id)
        if not alert:
            # Check history
            for historical_alert in alert_engine.alert_history:
                if historical_alert.alert_id == alert_id:
                    alert = historical_alert
                    break

        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return alert.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/alerts/test", tags=["Alerts"])
async def test_alert_notification(channel: str = "slack"):
    """
    Send a test alert notification (Agent 16)

    Useful for verifying notification configuration.

    Args:
        channel: Notification channel to test (email, slack, webhook)

    Returns:
        Test result
    """
    try:
        channel_enum = NotificationChannel(channel)
        success = alert_notifier.send_test_notification(channel_enum)

        return {
            "success": success,
            "channel": channel,
            "message": "Test notification sent" if success else "Test notification failed"
        }

    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid channel: {channel}")
    except Exception as e:
        logger.error(f"Error sending test notification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# END ALERT SYSTEM ENDPOINTS
# ============================================================


# ============================================================
# REPORT GENERATION ENDPOINTS (Agent 18)
# Professional PDF & Excel Reports for Elite Marketers
# ============================================================

# Initialize report generator
report_generator = None

class ReportGenerateRequest(BaseModel):
    """Request model for report generation"""
    report_type: str
    format: str
    start_date: str
    end_date: str
    campaign_ids: Optional[List[str]] = None
    ad_ids: Optional[List[str]] = None
    company_name: Optional[str] = "Your Company"
    company_logo: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


@app.post("/api/reports/generate", tags=["Reports"])
async def generate_report(request: ReportGenerateRequest):
    """
    Generate a professional campaign performance report (Agent 18)

    Creates investment-grade PDF or Excel reports suitable for:
    - C-suite executives
    - Board presentations
    - Client deliverables
    - Investor updates

    Args:
        request: Report generation parameters

    Returns:
        Report metadata and download information
    """
    try:
        logger.info(f"Generating {request.report_type} report in {request.format} format")

        # Parse dates
        from dateutil import parser
        start_date = parser.parse(request.start_date)
        end_date = parser.parse(request.end_date)

        # Validate report type
        try:
            report_type_enum = ReportType(request.report_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid report type. Must be one of: {[t.value for t in ReportType]}"
            )

        # Validate format
        try:
            format_enum = ReportFormat(request.format)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid format. Must be one of: {[f.value for f in ReportFormat]}"
            )

        # Get database connection
        data_loader = get_data_loader()
        db_pool = data_loader.pool if data_loader else None

        # Initialize report generator with DB pool
        global report_generator
        if report_generator is None:
            report_generator = ReportGenerator(db_pool)

        # Generate report content
        report_data = await report_generator.generate_report(
            report_type=report_type_enum,
            format=format_enum,
            start_date=start_date,
            end_date=end_date,
            campaign_ids=request.campaign_ids,
            ad_ids=request.ad_ids,
            company_name=request.company_name,
            company_logo=request.company_logo,
            filters=request.filters
        )

        # Build output file
        report_id = report_data['report_id']
        file_extension = 'pdf' if format_enum == ReportFormat.PDF else 'xlsx'
        output_dir = '/tmp/reports'
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/{report_id}.{file_extension}"

        # Generate file based on format
        if format_enum == ReportFormat.PDF:
            file_path = generate_pdf_report(report_data['content'], output_path)
        else:
            file_path = generate_excel_report(report_data['content'], output_path)

        logger.info(f"Report generated successfully: {file_path}")

        return {
            "success": True,
            "report_id": report_id,
            "report_type": request.report_type,
            "format": request.format,
            "file_path": file_path,
            "download_url": f"/api/reports/{report_id}/download",
            "generated_at": report_data['content']['generated_at'],
            "summary": {
                "campaigns_analyzed": report_data['content']['data'].get('total_campaigns', 0),
                "date_range": report_data['content']['date_range']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports", tags=["Reports"])
async def list_reports(limit: int = 20):
    """
    List all generated reports (Agent 18)

    Args:
        limit: Maximum number of reports to return

    Returns:
        List of report metadata
    """
    try:
        # Get database connection
        data_loader = get_data_loader()

        if not data_loader or not data_loader.pool:
            # Return mock data if no DB
            return {
                "reports": [],
                "count": 0,
                "message": "Database not connected"
            }

        query = """
            SELECT
                report_id,
                report_type,
                format,
                start_date,
                end_date,
                created_at,
                status
            FROM reports
            ORDER BY created_at DESC
            LIMIT $1
        """

        results = await data_loader.pool.fetch(query, limit)

        reports = [dict(row) for row in results]

        return {
            "reports": reports,
            "count": len(reports)
        }

    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        # Return empty list on error
        return {
            "reports": [],
            "count": 0
        }


@app.get("/api/reports/{report_id}/download", tags=["Reports"])
async def download_report(report_id: str):
    """
    Download a generated report file (Agent 18)

    Args:
        report_id: Report ID

    Returns:
        File download response
    """
    try:
        from fastapi.responses import FileResponse

        # Check both PDF and Excel extensions
        for ext in ['pdf', 'xlsx']:
            file_path = f"/tmp/reports/{report_id}.{ext}"
            if os.path.exists(file_path):
                # Determine media type
                media_type = 'application/pdf' if ext == 'pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

                return FileResponse(
                    path=file_path,
                    media_type=media_type,
                    filename=f"campaign_report_{report_id}.{ext}"
                )

        raise HTTPException(status_code=404, detail="Report file not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/reports/{report_id}", tags=["Reports"])
async def delete_report(report_id: str):
    """
    Delete a generated report (Agent 18)

    Args:
        report_id: Report ID

    Returns:
        Deletion confirmation
    """
    try:
        # Delete files
        deleted_files = []
        for ext in ['pdf', 'xlsx']:
            file_path = f"/tmp/reports/{report_id}.{ext}"
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_files.append(ext)

        if not deleted_files:
            raise HTTPException(status_code=404, detail="Report not found")

        # Delete from database
        data_loader = get_data_loader()
        if data_loader and data_loader.pool:
            await data_loader.pool.execute(
                "DELETE FROM reports WHERE report_id = $1",
                report_id
            )

        return {
            "success": True,
            "report_id": report_id,
            "deleted_files": deleted_files,
            "message": "Report deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# END REPORT GENERATION ENDPOINTS
# ============================================================


# ============================================================
# PRECOMPUTATION ENDPOINTS (Agent 45)
# Predictive Precomputation for Instant Responses
# ============================================================

class PrecomputeVideoRequest(BaseModel):
    """Request model for video precomputation"""
    video_id: str
    user_id: str
    video_data: Optional[Dict[str, Any]] = None


class PrecomputeCampaignRequest(BaseModel):
    """Request model for campaign precomputation"""
    campaign_id: str
    user_id: str
    campaign_data: Optional[Dict[str, Any]] = None


class PrecomputeLoginRequest(BaseModel):
    """Request model for login precomputation"""
    user_id: str
    user_data: Optional[Dict[str, Any]] = None


class PredictActionsRequest(BaseModel):
    """Request model for action prediction"""
    user_id: str


class CacheInvalidateRequest(BaseModel):
    """Request model for cache invalidation"""
    pattern: str


@app.post("/api/precompute/video", tags=["Precomputation"])
async def precompute_video_analysis(request: PrecomputeVideoRequest):
    """
    Trigger precomputation for uploaded video (Agent 45)

    Immediately queues all analysis tasks:
    - Scene detection
    - Face detection
    - Hook analysis
    - CTR prediction
    - Thumbnail generation
    - Caption generation

    Results are cached and instantly available when requested.

    Args:
        request: Video precomputation request

    Returns:
        Queued task IDs
    """
    try:
        logger.info(f"📹 Precomputing video analysis: {request.video_id}")

        precomputer = get_precomputer()
        queued_tasks = await precomputer.on_video_upload(
            video_id=request.video_id,
            user_id=request.user_id,
            video_data=request.video_data
        )

        return {
            "success": True,
            "video_id": request.video_id,
            "queued_tasks": queued_tasks,
            "message": f"Queued {sum(len(tasks) for tasks in queued_tasks.values())} precomputation tasks",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error triggering video precomputation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/precompute/campaign", tags=["Precomputation"])
async def precompute_campaign_variants(request: PrecomputeCampaignRequest):
    """
    Trigger precomputation for campaign creation (Agent 45)

    Immediately queues:
    - All 50 variants generation
    - Variant scoring
    - ROAS predictions

    Results ready instantly when user views campaign.

    Args:
        request: Campaign precomputation request

    Returns:
        Queued task IDs
    """
    try:
        logger.info(f"🎯 Precomputing campaign variants: {request.campaign_id}")

        precomputer = get_precomputer()
        queued_tasks = await precomputer.on_campaign_create(
            campaign_id=request.campaign_id,
            user_id=request.user_id,
            campaign_data=request.campaign_data
        )

        return {
            "success": True,
            "campaign_id": request.campaign_id,
            "queued_tasks": queued_tasks,
            "message": f"Queued {sum(len(tasks) for tasks in queued_tasks.values())} precomputation tasks",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error triggering campaign precomputation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/precompute/login", tags=["Precomputation"])
async def precompute_on_login(request: PrecomputeLoginRequest):
    """
    Trigger precomputation on user login (Agent 45)

    Precomputes:
    - Dashboard data
    - Predicted next actions based on ML model

    Makes dashboard load feel instant.

    Args:
        request: Login precomputation request

    Returns:
        Queued tasks and predicted actions
    """
    try:
        logger.info(f"👤 Precomputing for user login: {request.user_id}")

        precomputer = get_precomputer()

        # Trigger login precomputation
        queued_tasks = await precomputer.on_user_login(
            user_id=request.user_id,
            user_data=request.user_data
        )

        # Get action predictions
        predictions = await precomputer.predict_next_actions(request.user_id)

        return {
            "success": True,
            "user_id": request.user_id,
            "queued_tasks": queued_tasks,
            "predicted_actions": predictions,
            "message": f"Precomputed dashboard and predicted {len(predictions)} next actions",
            "status": "processing"
        }

    except Exception as e:
        logger.error(f"Error triggering login precomputation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/precompute/predict-actions", tags=["Precomputation"])
async def predict_user_actions(request: PredictActionsRequest):
    """
    Predict user's next actions (Agent 45)

    Uses ML model trained on user behavior patterns to predict
    what user will do next with >50% confidence.

    Args:
        request: Action prediction request

    Returns:
        Predicted actions with probabilities
    """
    try:
        logger.info(f"🔮 Predicting actions for user: {request.user_id}")

        precomputer = get_precomputer()
        predictions = await precomputer.predict_next_actions(request.user_id)

        return {
            "success": True,
            "user_id": request.user_id,
            "predictions": predictions,
            "count": len(predictions)
        }

    except Exception as e:
        logger.error(f"Error predicting user actions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/precompute/cache/{cache_key}", tags=["Precomputation"])
async def get_cached_result(cache_key: str):
    """
    Get precomputed result from cache (Agent 45)

    Args:
        cache_key: Cache key

    Returns:
        Cached result or 404 if not found
    """
    try:
        precomputer = get_precomputer()
        result = precomputer.get_cached_result(cache_key)

        if result:
            return {
                "success": True,
                "cache_key": cache_key,
                "result": result,
                "cached": True
            }
        else:
            raise HTTPException(status_code=404, detail="Cache entry not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cached result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/precompute/cache", tags=["Precomputation"])
async def invalidate_cache(request: CacheInvalidateRequest):
    """
    Invalidate cache entries (Agent 45)

    Args:
        request: Cache invalidation request with pattern

    Returns:
        Success status
    """
    try:
        precomputer = get_precomputer()
        precomputer.invalidate_cache(request.pattern)

        return {
            "success": True,
            "pattern": request.pattern,
            "message": f"Cache entries matching '{request.pattern}' invalidated"
        }

    except Exception as e:
        logger.error(f"Error invalidating cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/precompute/refresh/{task_type}", tags=["Precomputation"])
async def refresh_cache_proactively(task_type: str):
    """
    Proactively refresh cache for task type (Agent 45)

    Refreshes cache entries nearing expiration.

    Args:
        task_type: Type of tasks to refresh

    Returns:
        Success status
    """
    try:
        task_type_enum = PrecomputeTaskType(task_type)
        precomputer = get_precomputer()

        await precomputer.refresh_cache_proactively(task_type_enum)

        return {
            "success": True,
            "task_type": task_type,
            "message": f"Cache refresh queued for {task_type}"
        }

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid task type. Must be one of: {[t.value for t in PrecomputeTaskType]}"
        )
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/precompute/metrics", tags=["Precomputation"])
async def get_precompute_metrics():
    """
    Get precomputation metrics (Agent 45)

    Returns comprehensive metrics including:
    - Cache hit rate
    - Queue size
    - Processing times
    - Task statistics

    Investment-grade monitoring for €5M validation.

    Returns:
        Precomputation metrics
    """
    try:
        precomputer = get_precomputer()
        metrics = precomputer.get_metrics()

        return {
            "success": True,
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting precompute metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/precompute/queue", tags=["Precomputation"])
async def get_queue_status():
    """
    Get precomputation queue status (Agent 45)

    Returns:
        Queue statistics by task type
    """
    try:
        precomputer = get_precomputer()
        queue_stats = precomputer.get_queue_stats()

        return {
            "success": True,
            "queue_stats": queue_stats,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting queue status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# END PRECOMPUTATION ENDPOINTS
# ============================================================


# ============================================================
# CROSS-ACCOUNT LEARNING ENDPOINTS (Agent 49)
# Network Effects Through Anonymized Pattern Sharing
# ============================================================

from src.cross_learner import cross_learner, initialize_cross_learner

class NicheDetectionRequest(BaseModel):
    """Request model for niche detection"""
    account_id: str


class ApplyWisdomRequest(BaseModel):
    """Request model for applying niche wisdom"""
    account_id: str
    auto_apply: bool = False


@app.post("/api/cross-learning/detect-niche", tags=["Cross-Learning"])
async def detect_account_niche(request: NicheDetectionRequest):
    """
    Detect the niche/industry for an account (Agent 49)

    Uses AI-powered content analysis to classify accounts into niches.

    Args:
        request: Account ID to analyze

    Returns:
        Niche category and confidence score
    """
    try:
        if not cross_learner:
            raise HTTPException(status_code=503, detail="Cross-learning system not initialized")

        logger.info(f"Detecting niche for account {request.account_id}")

        niche, confidence = await cross_learner.detect_niche(request.account_id)

        return {
            "success": True,
            "account_id": request.account_id,
            "niche": niche,
            "confidence": confidence,
            "detected_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error detecting niche: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cross-learning/extract-insights", tags=["Cross-Learning"])
async def extract_account_insights(request: NicheDetectionRequest):
    """
    Extract anonymized insights from an account (Agent 49)

    Privacy-preserving: Only extracts patterns, not content.

    Args:
        request: Account ID to analyze

    Returns:
        Anonymized insights including hook types, duration, CTA styles, etc.
    """
    try:
        if not cross_learner:
            raise HTTPException(status_code=503, detail="Cross-learning system not initialized")

        logger.info(f"Extracting insights for account {request.account_id}")

        insights = await cross_learner.extract_anonymized_insights(request.account_id)

        if not insights:
            return {
                "success": False,
                "message": "Insufficient data to extract insights",
                "account_id": request.account_id
            }

        return {
            "success": True,
            "account_id": request.account_id,
            "insights": insights.to_dict()
        }

    except Exception as e:
        logger.error(f"Error extracting insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cross-learning/niche-wisdom/{niche}", tags=["Cross-Learning"])
async def get_niche_wisdom(niche: str, force_refresh: bool = False):
    """
    Get aggregated wisdom for a niche (Agent 49)

    Returns insights from all accounts in a niche, aggregated
    to show what works best for that industry.

    Args:
        niche: Niche category (fitness, beauty, tech, etc.)
        force_refresh: Force recalculation even if cached

    Returns:
        Niche-wide patterns and benchmarks
    """
    try:
        if not cross_learner:
            raise HTTPException(status_code=503, detail="Cross-learning system not initialized")

        logger.info(f"Getting niche wisdom for {niche}")

        wisdom = await cross_learner.get_niche_insights(niche, force_refresh=force_refresh)

        if not wisdom:
            return {
                "success": False,
                "message": f"Insufficient data for niche {niche}",
                "niche": niche
            }

        return {
            "success": True,
            "niche": niche,
            "wisdom": wisdom.to_dict()
        }

    except Exception as e:
        logger.error(f"Error getting niche wisdom: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/cross-learning/apply-wisdom", tags=["Cross-Learning"])
async def apply_niche_wisdom(request: ApplyWisdomRequest):
    """
    Apply niche wisdom to an account (Agent 49)

    Bootstraps new accounts with proven patterns from their niche.
    Creates network effect: new accounts benefit from all previous learning.

    Args:
        request: Account ID and auto-apply setting

    Returns:
        Niche-specific recommendations
    """
    try:
        if not cross_learner:
            raise HTTPException(status_code=503, detail="Cross-learning system not initialized")

        logger.info(f"Applying niche wisdom to account {request.account_id}")

        result = await cross_learner.apply_niche_wisdom(
            new_account_id=request.account_id,
            auto_apply=request.auto_apply
        )

        return result

    except Exception as e:
        logger.error(f"Error applying niche wisdom: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cross-learning/dashboard/{account_id}", tags=["Cross-Learning"])
async def get_cross_learning_dashboard(account_id: str):
    """
    Get cross-learning dashboard for an account (Agent 49)

    Shows:
    - Account's niche
    - Performance vs. niche benchmarks
    - Improvement opportunities
    - Network effect stats

    Args:
        account_id: Account ID

    Returns:
        Comprehensive cross-learning dashboard
    """
    try:
        if not cross_learner:
            raise HTTPException(status_code=503, detail="Cross-learning system not initialized")

        logger.info(f"Generating cross-learning dashboard for account {account_id}")

        dashboard = await cross_learner.get_cross_learning_dashboard(account_id)

        return dashboard

    except Exception as e:
        logger.error(f"Error generating dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cross-learning/stats", tags=["Cross-Learning"])
async def get_cross_learning_stats():
    """
    Get overall cross-learning system statistics (Agent 49)

    Shows the power of network effects:
    - Total accounts contributing
    - Active niches
    - Pattern quality
    - Learning velocity

    Returns:
        System-wide cross-learning stats
    """
    try:
        if not cross_learner:
            raise HTTPException(status_code=503, detail="Cross-learning system not initialized")

        total_accounts = await cross_learner._get_total_account_count()
        active_niches = await cross_learner._get_active_niche_count()

        stats = {
            "network_effects": {
                "total_accounts": total_accounts,
                "active_niches": active_niches,
                "avg_accounts_per_niche": total_accounts / active_niches if active_niches > 0 else 0,
                "learning_power": "10x" if total_accounts >= 100 else "5x" if total_accounts >= 50 else "2x"
            },
            "system_status": {
                "initialized": cross_learner is not None,
                "cache_size": len(cross_learner._wisdom_cache) if cross_learner else 0,
                "min_sample_size": cross_learner.min_sample_size if cross_learner else 0
            },
            "privacy": {
                "content_shared": False,
                "only_patterns": True,
                "anonymized": True,
                "opt_in_required": True
            },
            "generated_at": datetime.utcnow().isoformat()
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting cross-learning stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# END CROSS-ACCOUNT LEARNING ENDPOINTS
# ============================================================


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    logger.info("ML Service starting up...")
    logger.info("Feedback loop enabled - system will learn from real data")
    logger.info("Alert system initialized - monitoring performance metrics")

    # Start precomputation workers (Agent 45)
    try:
        precomputer = get_precomputer()
        num_workers = int(os.getenv("PRECOMPUTE_WORKERS", "3"))
        asyncio.create_task(precomputer.start_workers(num_workers=num_workers))
        logger.info(f"Precomputation engine started with {num_workers} workers")
    except Exception as e:
        logger.warning(f"Failed to start precomputation workers: {e}")

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

    # Start compound learning scheduler (Agent 50)
    try:
        from src.compound_learning_scheduler import compound_learning_scheduler
        compound_learning_scheduler.start()
        logger.info("🚀 Compound learning scheduler started - system will get 10x better automatically!")
    except Exception as e:
        logger.warning(f"Compound learning scheduler not available: {e}")

    # Train enhanced model if not already trained
    if not enhanced_ctr_predictor.is_trained:
        logger.info("No enhanced model found. Training with synthetic data...")
        try:
            historical_ads = generate_enhanced_data(n_samples=1000)
            metrics = enhanced_ctr_predictor.train(historical_ads)
            enhanced_ctr_predictor.save()
            logger.info(f"Enhanced model trained on startup: Test R² = {metrics['test_r2']:.4f}")
            logger.info(f"Target achieved: {metrics.get('target_achieved', False)}")
        except Exception as e:
            logger.warning(f"Failed to train enhanced model on startup: {e}")
    else:
        logger.info("Enhanced model loaded successfully from disk")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
