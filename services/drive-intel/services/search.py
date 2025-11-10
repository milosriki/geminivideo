"""
Semantic search service using FAISS.
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)

class SearchService:
    """Service for semantic search of clips."""
    
    def __init__(self):
        self.sentence_model = None
        self.faiss_index = None
        self.clip_mapping = []  # Maps index positions to clips
        
        self._init_models()
        logger.info("Search service initialized")
    
    def _init_models(self):
        """Initialize search models."""
        try:
            from sentence_transformers import SentenceTransformer
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence transformer loaded for search")
        except Exception as e:
            logger.warning(f"Failed to load sentence transformer: {e}")
        
        try:
            import faiss
            # Initialize FAISS index (will be populated as clips are added)
            self.faiss_index = None  # Created when first clip is added
            logger.info("FAISS ready")
        except Exception as e:
            logger.warning(f"FAISS initialization skipped: {e}")
    
    async def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search for clips using semantic similarity."""
        if not self.sentence_model:
            logger.warning("Search model not available")
            return []
        
        if not self.clip_mapping:
            logger.warning("No clips indexed yet")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.sentence_model.encode(query)
            
            # If FAISS is available and initialized, use it
            if self.faiss_index is not None:
                return self._search_faiss(query_embedding, top_k)
            else:
                # Fallback to simple similarity search
                return self._search_simple(query, top_k)
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return []
    
    def _search_faiss(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Search using FAISS index."""
        try:
            import faiss
            
            # Reshape for FAISS
            query_vec = query_embedding.reshape(1, -1).astype('float32')
            
            # Search
            distances, indices = self.faiss_index.search(query_vec, min(top_k, len(self.clip_mapping)))
            
            # Get clips
            results = []
            for idx in indices[0]:
                if idx < len(self.clip_mapping):
                    results.append(self.clip_mapping[idx])
            
            return results
        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []
    
    def _search_simple(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Simple keyword-based search fallback."""
        query_lower = query.lower()
        results = []
        
        for clip in self.clip_mapping:
            # Check if query matches any OCR tokens or objects
            ocr_tokens = clip.get("ocr_tokens", [])
            objects = clip.get("objects", [])
            
            # Calculate simple match score
            score = 0
            for token in ocr_tokens:
                if query_lower in token.lower():
                    score += 1
            for obj in objects:
                if query_lower in obj.lower():
                    score += 1
            
            if score > 0:
                results.append((score, clip))
        
        # Sort by score and return top k
        results.sort(key=lambda x: x[0], reverse=True)
        return [clip for score, clip in results[:top_k]]
    
    def index_clips(self, clips: List[Dict[str, Any]]):
        """Index clips for search."""
        if not self.sentence_model:
            return
        
        try:
            import faiss
            
            # Generate embeddings for all clips
            embeddings = []
            indexed_clips = []
            
            for clip in clips:
                # Create text representation
                text_parts = []
                text_parts.extend(clip.get("ocr_tokens", []))
                text_parts.extend(clip.get("objects", []))
                if clip.get("transcript_excerpt"):
                    text_parts.append(clip["transcript_excerpt"])
                
                text = " ".join(text_parts)
                if text:
                    embedding = self.sentence_model.encode(text)
                    embeddings.append(embedding)
                    indexed_clips.append(clip)
            
            if embeddings:
                # Create FAISS index
                embeddings_array = np.array(embeddings).astype('float32')
                dimension = embeddings_array.shape[1]
                
                self.faiss_index = faiss.IndexFlatL2(dimension)
                self.faiss_index.add(embeddings_array)
                self.clip_mapping = indexed_clips
                
                logger.info(f"Indexed {len(indexed_clips)} clips in FAISS")
        except Exception as e:
            logger.error(f"Indexing failed: {e}")
