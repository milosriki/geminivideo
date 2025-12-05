"""
Banana.dev GPU Inference Wrapper
Handles ML model loading and inference for serverless GPU deployment

Supports:
- XGBoost CTR prediction
- PyTorch CLIP embeddings
- Batch processing
- Model caching and optimization
"""

import os
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
import asyncio

import numpy as np
import xgboost as xgb
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import joblib
import base64
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BananaMLModel:
    """
    Unified ML model wrapper for Banana.dev GPU inference.

    Handles:
    - XGBoost CTR prediction
    - CLIP image embeddings
    - Batch processing
    - Model warming
    """

    def __init__(self):
        """Initialize models and configure GPU."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing BananaMLModel on device: {self.device}")

        # Model paths
        self.xgboost_model_path = os.getenv("XGBOOST_MODEL_PATH", "/models/ctr_model.pkl")
        self.clip_model_name = os.getenv("CLIP_MODEL_NAME", "openai/clip-vit-base-patch32")

        # Models (lazy loaded)
        self.xgboost_model = None
        self.clip_model = None
        self.clip_processor = None

        # Performance metrics
        self.inference_count = 0
        self.total_inference_time = 0.0

        # Warm up models on initialization
        self._warm_up_models()

    def _warm_up_models(self):
        """Pre-load and warm up models to reduce cold start time."""
        logger.info("Warming up models...")

        # Load XGBoost model
        if os.path.exists(self.xgboost_model_path):
            try:
                self.xgboost_model = joblib.load(self.xgboost_model_path)
                logger.info(f"XGBoost model loaded from {self.xgboost_model_path}")

                # Warm up with dummy prediction
                dummy_features = np.random.rand(1, 10)
                _ = self.xgboost_model.predict(dummy_features)
                logger.info("XGBoost model warmed up")
            except Exception as e:
                logger.error(f"Failed to load XGBoost model: {e}")
        else:
            logger.warning(f"XGBoost model not found at {self.xgboost_model_path}")

        # Load CLIP model
        try:
            logger.info(f"Loading CLIP model: {self.clip_model_name}")
            self.clip_model = CLIPModel.from_pretrained(self.clip_model_name).to(self.device)
            self.clip_processor = CLIPProcessor.from_pretrained(self.clip_model_name)
            self.clip_model.eval()

            # Warm up with dummy image
            dummy_image = Image.new('RGB', (224, 224), color='white')
            inputs = self.clip_processor(images=dummy_image, return_tensors="pt").to(self.device)
            with torch.no_grad():
                _ = self.clip_model.get_image_features(**inputs)
            logger.info("CLIP model warmed up")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")

        logger.info("Model warm-up complete")

    def predict_ctr(
        self,
        features: Union[List[float], List[List[float]]],
        batch: bool = False
    ) -> Union[float, List[float]]:
        """
        Predict CTR using XGBoost model.

        Args:
            features: Feature vector(s) for prediction
            batch: Whether input is a batch of features

        Returns:
            Predicted CTR value(s)
        """
        if self.xgboost_model is None:
            raise RuntimeError("XGBoost model not loaded")

        start_time = time.time()

        # Convert to numpy array
        X = np.array(features)
        if not batch and X.ndim == 1:
            X = X.reshape(1, -1)

        # Predict
        predictions = self.xgboost_model.predict(X)

        # Update metrics
        inference_time = time.time() - start_time
        self.inference_count += len(X) if batch else 1
        self.total_inference_time += inference_time

        logger.info(f"CTR prediction completed in {inference_time:.3f}s for {len(X)} samples")

        # Return single value or list
        if batch or len(predictions) > 1:
            return predictions.tolist()
        return float(predictions[0])

    def embed_image(
        self,
        image_data: Union[str, List[str]],
        batch: bool = False
    ) -> Union[List[float], List[List[float]]]:
        """
        Generate CLIP embeddings for image(s).

        Args:
            image_data: Base64-encoded image string(s) or file path(s)
            batch: Whether input is a batch of images

        Returns:
            Image embedding(s) as list of floats
        """
        if self.clip_model is None or self.clip_processor is None:
            raise RuntimeError("CLIP model not loaded")

        start_time = time.time()

        # Handle single vs batch
        if not batch:
            image_data = [image_data]

        # Load images
        images = []
        for img_data in image_data:
            if img_data.startswith('data:image') or img_data.startswith('/9j/'):
                # Base64 encoded image
                if ',' in img_data:
                    img_data = img_data.split(',', 1)[1]
                img_bytes = base64.b64decode(img_data)
                image = Image.open(BytesIO(img_bytes)).convert('RGB')
            else:
                # File path
                image = Image.open(img_data).convert('RGB')
            images.append(image)

        # Process images
        inputs = self.clip_processor(images=images, return_tensors="pt").to(self.device)

        # Generate embeddings
        with torch.no_grad():
            embeddings = self.clip_model.get_image_features(**inputs)
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)  # Normalize

        # Convert to list
        embeddings_list = embeddings.cpu().numpy().tolist()

        # Update metrics
        inference_time = time.time() - start_time
        self.inference_count += len(images)
        self.total_inference_time += inference_time

        logger.info(f"Image embedding completed in {inference_time:.3f}s for {len(images)} images")

        # Return single embedding or list
        if not batch and len(embeddings_list) == 1:
            return embeddings_list[0]
        return embeddings_list

    def get_metrics(self) -> Dict[str, Any]:
        """Get model performance metrics."""
        avg_inference_time = (
            self.total_inference_time / self.inference_count
            if self.inference_count > 0
            else 0
        )

        return {
            "inference_count": self.inference_count,
            "total_inference_time": self.total_inference_time,
            "avg_inference_time": avg_inference_time,
            "device": self.device,
            "models_loaded": {
                "xgboost": self.xgboost_model is not None,
                "clip": self.clip_model is not None
            }
        }


# Global model instance (Banana keeps this warm)
model = None


def init():
    """
    Initialize the model. Called once on cold start.
    This is the Banana.dev standard initialization function.
    """
    global model
    logger.info("Initializing Banana ML Model...")
    model = BananaMLModel()
    logger.info("Banana ML Model initialized successfully")
    return model


def inference(model_inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run inference on the model.
    This is the Banana.dev standard inference function.

    Args:
        model_inputs: Dictionary with the following structure:
            {
                "task": "ctr_prediction" | "image_embedding",
                "data": <task-specific data>,
                "batch": bool (optional, default False)
            }

            For CTR prediction:
                data: List[float] or List[List[float]]

            For image embedding:
                data: str (base64 image) or List[str]

    Returns:
        Dictionary with prediction results and metadata
    """
    global model

    if model is None:
        model = init()

    start_time = time.time()

    try:
        task = model_inputs.get("task")
        data = model_inputs.get("data")
        batch = model_inputs.get("batch", False)

        if not task or data is None:
            return {
                "error": "Missing required fields: 'task' and 'data'",
                "success": False
            }

        # Route to appropriate model
        if task == "ctr_prediction":
            result = model.predict_ctr(data, batch=batch)
            output = {
                "predictions": result,
                "task": "ctr_prediction"
            }

        elif task == "image_embedding":
            result = model.embed_image(data, batch=batch)
            output = {
                "embeddings": result,
                "task": "image_embedding",
                "dimension": len(result[0]) if batch else len(result)
            }

        else:
            return {
                "error": f"Unknown task: {task}. Supported tasks: ctr_prediction, image_embedding",
                "success": False
            }

        # Add metadata
        inference_time = time.time() - start_time
        output.update({
            "success": True,
            "inference_time": inference_time,
            "batch_size": len(data) if batch else 1
        })

        return output

    except Exception as e:
        logger.error(f"Inference error: {e}", exc_info=True)
        return {
            "error": str(e),
            "success": False,
            "inference_time": time.time() - start_time
        }


# Health check endpoint
def health_check() -> Dict[str, Any]:
    """Check if model is ready and healthy."""
    global model

    if model is None:
        return {
            "status": "not_initialized",
            "healthy": False
        }

    metrics = model.get_metrics()
    return {
        "status": "healthy",
        "healthy": True,
        "metrics": metrics
    }


if __name__ == "__main__":
    # Test the model locally
    print("Testing Banana ML Model...")

    # Initialize
    test_model = init()

    # Test CTR prediction
    print("\n1. Testing CTR prediction...")
    test_features = [0.5, 0.3, 0.8, 0.2, 0.6, 0.1, 0.9, 0.4, 0.7, 0.3]
    result = inference({
        "task": "ctr_prediction",
        "data": test_features,
        "batch": False
    })
    print(f"Result: {result}")

    # Test batch CTR prediction
    print("\n2. Testing batch CTR prediction...")
    batch_features = [test_features, test_features, test_features]
    result = inference({
        "task": "ctr_prediction",
        "data": batch_features,
        "batch": True
    })
    print(f"Result: {result}")

    # Test health check
    print("\n3. Testing health check...")
    health = health_check()
    print(f"Health: {health}")

    print("\nAll tests completed!")
