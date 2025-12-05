"""
Embedding Pipeline - Generate embeddings for text and images.

Agent 39: Vector Database Upgrade
Provides unified interface for generating embeddings using:
- OpenAI text-embedding-3-large (3072 dims) for text
- CLIP (512 dims) for images

Usage:
    embedder = EmbeddingPipeline(openai_api_key="...")

    # Text embedding
    text_emb = await embedder.embed_text("Your hook text here")

    # Image embedding
    image_emb = await embedder.embed_image("/path/to/image.jpg")

    # Batch embedding
    embeddings = await embedder.embed_texts(["text1", "text2", "text3"])
"""

import os
import logging
from typing import List, Union, Optional
import asyncio
from pathlib import Path

import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from openai import AsyncOpenAI
import tiktoken

logger = logging.getLogger(__name__)


class EmbeddingPipeline:
    """
    Unified embedding pipeline for text and images.

    Features:
    - Text embeddings via OpenAI text-embedding-3-large (3072 dims)
    - Image embeddings via CLIP (512 dims)
    - Batch processing support
    - Automatic caching and optimization
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        clip_model_name: str = "openai/clip-vit-base-patch32",
        max_tokens: int = 8191,
        batch_size: int = 100
    ):
        """
        Initialize embedding pipeline.

        Args:
            openai_api_key: OpenAI API key (uses env var if not provided)
            clip_model_name: HuggingFace CLIP model name
            max_tokens: Maximum tokens for text embedding
            batch_size: Batch size for processing
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set - text embeddings will fail")

        self.clip_model_name = clip_model_name
        self.max_tokens = max_tokens
        self.batch_size = batch_size

        # Initialize OpenAI client
        self.openai_client = AsyncOpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"Failed to load tokenizer: {e}")
            self.tokenizer = None

        # CLIP model (lazy loaded)
        self.clip_model = None
        self.clip_processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        logger.info(f"Initialized EmbeddingPipeline (device: {self.device})")

    def _load_clip_model(self):
        """Lazy load CLIP model."""
        if self.clip_model is None:
            try:
                logger.info(f"Loading CLIP model: {self.clip_model_name}")
                self.clip_model = CLIPModel.from_pretrained(self.clip_model_name).to(self.device)
                self.clip_processor = CLIPProcessor.from_pretrained(self.clip_model_name)
                self.clip_model.eval()  # Set to evaluation mode
                logger.info("CLIP model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load CLIP model: {e}")
                raise

    # ========================================================================
    # TEXT EMBEDDINGS (OpenAI)
    # ========================================================================

    async def embed_text(
        self,
        text: str,
        model: str = "text-embedding-3-large",
        dimensions: int = 3072
    ) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Input text
            model: OpenAI embedding model
            dimensions: Embedding dimensions (3072 for text-embedding-3-large)

        Returns:
            Embedding vector (list of floats)
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        try:
            # Truncate if too long
            if self.tokenizer:
                tokens = self.tokenizer.encode(text)
                if len(tokens) > self.max_tokens:
                    logger.warning(f"Text too long ({len(tokens)} tokens), truncating to {self.max_tokens}")
                    tokens = tokens[:self.max_tokens]
                    text = self.tokenizer.decode(tokens)

            # Generate embedding
            response = await self.openai_client.embeddings.create(
                input=text,
                model=model,
                dimensions=dimensions
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated text embedding: {len(embedding)} dims")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            raise

    async def embed_texts(
        self,
        texts: List[str],
        model: str = "text-embedding-3-large",
        dimensions: int = 3072
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched).

        Args:
            texts: List of input texts
            model: OpenAI embedding model
            dimensions: Embedding dimensions

        Returns:
            List of embedding vectors
        """
        if not self.openai_client:
            raise ValueError("OpenAI API key not configured")

        if not texts:
            return []

        try:
            # Process in batches
            all_embeddings = []

            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]

                # Truncate texts if needed
                if self.tokenizer:
                    truncated_batch = []
                    for text in batch:
                        tokens = self.tokenizer.encode(text)
                        if len(tokens) > self.max_tokens:
                            tokens = tokens[:self.max_tokens]
                            text = self.tokenizer.decode(tokens)
                        truncated_batch.append(text)
                    batch = truncated_batch

                # Generate embeddings for batch
                response = await self.openai_client.embeddings.create(
                    input=batch,
                    model=model,
                    dimensions=dimensions
                )

                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Generated embeddings for batch {i // self.batch_size + 1}: {len(batch)} texts")

            logger.info(f"Generated embeddings for {len(texts)} texts")
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate text embeddings: {e}")
            raise

    # ========================================================================
    # IMAGE EMBEDDINGS (CLIP)
    # ========================================================================

    def embed_image(
        self,
        image_path: Union[str, Path, Image.Image]
    ) -> List[float]:
        """
        Generate embedding for single image using CLIP.

        Args:
            image_path: Path to image or PIL Image object

        Returns:
            Embedding vector (512 dims)
        """
        self._load_clip_model()

        try:
            # Load image
            if isinstance(image_path, (str, Path)):
                image = Image.open(image_path).convert("RGB")
            else:
                image = image_path

            # Process image
            inputs = self.clip_processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate embedding
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                # Normalize
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Convert to list
            embedding = image_features.cpu().numpy()[0].tolist()
            logger.debug(f"Generated image embedding: {len(embedding)} dims")
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate image embedding: {e}")
            raise

    def embed_images(
        self,
        image_paths: List[Union[str, Path, Image.Image]]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple images (batched).

        Args:
            image_paths: List of image paths or PIL Image objects

        Returns:
            List of embedding vectors
        """
        self._load_clip_model()

        if not image_paths:
            return []

        try:
            all_embeddings = []

            # Process in batches
            for i in range(0, len(image_paths), self.batch_size):
                batch = image_paths[i:i + self.batch_size]

                # Load images
                images = []
                for img_path in batch:
                    if isinstance(img_path, (str, Path)):
                        img = Image.open(img_path).convert("RGB")
                    else:
                        img = img_path
                    images.append(img)

                # Process batch
                inputs = self.clip_processor(images=images, return_tensors="pt")
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Generate embeddings
                with torch.no_grad():
                    image_features = self.clip_model.get_image_features(**inputs)
                    # Normalize
                    image_features = image_features / image_features.norm(dim=-1, keepdim=True)

                # Convert to list
                batch_embeddings = image_features.cpu().numpy().tolist()
                all_embeddings.extend(batch_embeddings)

                logger.debug(f"Generated embeddings for batch {i // self.batch_size + 1}: {len(batch)} images")

            logger.info(f"Generated embeddings for {len(image_paths)} images")
            return all_embeddings

        except Exception as e:
            logger.error(f"Failed to generate image embeddings: {e}")
            raise

    # ========================================================================
    # HYBRID EMBEDDINGS
    # ========================================================================

    async def embed_creative(
        self,
        text: Optional[str] = None,
        image_path: Optional[Union[str, Path, Image.Image]] = None
    ) -> dict:
        """
        Generate embeddings for creative with both text and image.

        Args:
            text: Creative text (hook, script, etc.)
            image_path: Creative image/thumbnail

        Returns:
            Dict with 'text_embedding' and 'visual_embedding'
        """
        result = {}

        try:
            # Generate text embedding
            if text:
                result['text_embedding'] = await self.embed_text(text)

            # Generate image embedding
            if image_path:
                result['visual_embedding'] = self.embed_image(image_path)

            logger.info(f"Generated creative embeddings: text={bool(text)}, image={bool(image_path)}")
            return result

        except Exception as e:
            logger.error(f"Failed to generate creative embeddings: {e}")
            raise

    # ========================================================================
    # SEMANTIC SEARCH HELPERS
    # ========================================================================

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        if not self.tokenizer:
            # Rough approximation
            return len(text.split()) * 1.3

        return len(self.tokenizer.encode(text))

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def get_info(self) -> dict:
        """
        Get embedding pipeline information.

        Returns:
            Dict with configuration and status
        """
        return {
            'text_embedding': {
                'provider': 'OpenAI',
                'model': 'text-embedding-3-large',
                'dimensions': 3072,
                'max_tokens': self.max_tokens,
                'configured': self.openai_client is not None
            },
            'image_embedding': {
                'provider': 'HuggingFace',
                'model': self.clip_model_name,
                'dimensions': 512,
                'device': self.device,
                'loaded': self.clip_model is not None
            },
            'batch_size': self.batch_size
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Global instance (lazy initialized)
_global_embedder: Optional[EmbeddingPipeline] = None


def get_embedder(
    openai_api_key: Optional[str] = None,
    clip_model_name: str = "openai/clip-vit-base-patch32"
) -> EmbeddingPipeline:
    """
    Get or create global embedding pipeline instance.

    Args:
        openai_api_key: OpenAI API key
        clip_model_name: CLIP model name

    Returns:
        EmbeddingPipeline instance
    """
    global _global_embedder

    if _global_embedder is None:
        _global_embedder = EmbeddingPipeline(
            openai_api_key=openai_api_key,
            clip_model_name=clip_model_name
        )

    return _global_embedder


async def quick_embed_text(text: str) -> List[float]:
    """
    Quick text embedding using global embedder.

    Args:
        text: Input text

    Returns:
        Embedding vector
    """
    embedder = get_embedder()
    return await embedder.embed_text(text)


def quick_embed_image(image_path: Union[str, Path, Image.Image]) -> List[float]:
    """
    Quick image embedding using global embedder.

    Args:
        image_path: Image path or PIL Image

    Returns:
        Embedding vector
    """
    embedder = get_embedder()
    return embedder.embed_image(image_path)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    async def example():
        # Initialize pipeline
        embedder = EmbeddingPipeline(openai_api_key=os.getenv("OPENAI_API_KEY"))

        # Text embedding
        print("Generating text embedding...")
        text = "Stop wasting money on gym memberships you never use..."
        text_emb = await embedder.embed_text(text)
        print(f"Text embedding dimensions: {len(text_emb)}")

        # Batch text embeddings
        print("\nGenerating batch text embeddings...")
        texts = [
            "Transform your body in 30 days",
            "Get fit without leaving your home",
            "Professional trainer in your pocket"
        ]
        embeddings = await embedder.embed_texts(texts)
        print(f"Generated {len(embeddings)} embeddings")

        # Calculate similarity
        sim = embedder.cosine_similarity(embeddings[0], embeddings[1])
        print(f"Similarity between first two texts: {sim:.4f}")

        # Pipeline info
        info = embedder.get_info()
        print("\nPipeline info:")
        import json
        print(json.dumps(info, indent=2))

    # Run example
    asyncio.run(example())
