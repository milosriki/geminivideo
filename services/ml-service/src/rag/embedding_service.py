from typing import List, Dict, Any
import os

class VertexAIService:
    """Mock wrapper for Vertex AI to avoid dependency issues if not installed."""
    async def generate_text_embedding(self, text: str) -> List[float]:
        # In production, this would call Vertex AI
        # For now, return a dummy embedding
        return [0.1] * 384

class EmbeddingService:
    def __init__(self):
        self.vertex_service = VertexAIService()

    async def generate_creative_dna_embedding(self, creative_dna: Dict[str, Any]) -> List[float]:
        """
        Generates an embedding vector from a Creative DNA dictionary.
        """
        # Convert Creative DNA to a rich text representation
        text_representation = (
            f"Hook: {creative_dna.get('hook_type', 'unknown')}. "
            f"Visual: {creative_dna.get('visual_style', 'unknown')}. "
            f"Audio: {creative_dna.get('audio_style', 'unknown')}. "
            f"Pacing: {creative_dna.get('pacing', 'unknown')}."
        )
        
        # Generate embedding using Vertex AI
        embedding = await self.vertex_service.generate_text_embedding(text_representation)
        return embedding
