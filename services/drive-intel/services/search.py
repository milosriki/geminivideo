"""
Semantic search service using FAISS
"""
import numpy as np
from typing import List, Dict, Any, Optional
import faiss


class SearchService:
    """
    FAISS-based semantic search for video clips
    """
    
    def __init__(self):
        self.index = None
        self.clip_id_map = []  # Maps index position to clip ID
        self.embedding_model = None
        self._init_embedding_model()
    
    def _init_embedding_model(self):
        """Initialize sentence transformer for query encoding"""
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Warning: Could not load embedding model: {e}")
    
    def add_clips(self, clips: List[Any]):
        """
        Add clips to the search index
        
        Args:
            clips: List of Clip objects with embeddings
        """
        # Collect clips with embeddings
        valid_clips = [c for c in clips if c.features.embedding is not None]
        
        if not valid_clips:
            return
        
        embeddings = [np.array(c.features.embedding, dtype='float32') for c in valid_clips]
        embeddings_matrix = np.vstack(embeddings)
        
        # Initialize or update FAISS index
        if self.index is None:
            dimension = embeddings_matrix.shape[1]
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            # Normalize vectors for cosine similarity
            faiss.normalize_L2(embeddings_matrix)
            self.index.add(embeddings_matrix)
            self.clip_id_map = [c.id for c in valid_clips]
        else:
            # Normalize and add new embeddings
            faiss.normalize_L2(embeddings_matrix)
            self.index.add(embeddings_matrix)
            self.clip_id_map.extend([c.id for c in valid_clips])
    
    def search(
        self, 
        query: str, 
        top_k: int = 10,
        filter_asset_id: Optional[str] = None,
        persistence = None
    ) -> List[Dict[str, Any]]:
        """
        Search for clips matching the query
        
        Args:
            query: Text query
            top_k: Number of results to return
            filter_asset_id: Optional asset ID filter
            persistence: Persistence layer to fetch clip details
            
        Returns:
            List of search results with clip info and similarity scores
        """
        if self.index is None or self.embedding_model is None:
            return []
        
        try:
            # Encode query
            query_embedding = self.embedding_model.encode(query)
            query_vector = np.array([query_embedding], dtype='float32')
            faiss.normalize_L2(query_vector)
            
            # Search in FAISS index
            k = min(top_k * 2, len(self.clip_id_map))  # Get more to account for filtering
            distances, indices = self.index.search(query_vector, k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx >= len(self.clip_id_map):
                    continue
                
                clip_id = self.clip_id_map[idx]
                
                # Apply filter if specified
                if filter_asset_id and persistence:
                    clip = persistence.get_clip(clip_id)
                    if clip and clip.asset_id != filter_asset_id:
                        continue
                
                results.append({
                    "clip_id": clip_id,
                    "similarity": float(dist),
                    "score": float(dist)
                })
                
                if len(results) >= top_k:
                    break
            
            return results
        except Exception as e:
            print(f"Error in search: {e}")
            return []
    
    def calculate_novelty_scores(self, clips: List[Any]):
        """
        Calculate novelty scores for clips based on semantic diversity
        Higher novelty = more unique/different from other clips
        
        Args:
            clips: List of Clip objects with embeddings
        """
        if self.index is None or len(self.clip_id_map) < 2:
            # Not enough data for novelty calculation
            for clip in clips:
                clip.novelty_score = 0.5
            return
        
        for clip in clips:
            if clip.features.embedding is None:
                clip.novelty_score = 0.5
                continue
            
            try:
                # Search for similar clips
                query_vector = np.array([clip.features.embedding], dtype='float32')
                faiss.normalize_L2(query_vector)
                
                k = min(5, len(self.clip_id_map))
                distances, indices = self.index.search(query_vector, k)
                
                # Average distance to nearest neighbors (excluding self)
                similarities = distances[0]
                
                # Find self in results and exclude
                valid_similarities = []
                for sim, idx in zip(similarities, indices[0]):
                    if idx >= 0 and idx < len(self.clip_id_map):
                        if self.clip_id_map[idx] != clip.id:
                            valid_similarities.append(sim)
                
                if valid_similarities:
                    # Lower average similarity = higher novelty
                    avg_similarity = np.mean(valid_similarities)
                    novelty = 1.0 - avg_similarity
                    clip.novelty_score = max(0.0, min(1.0, novelty))
                else:
                    clip.novelty_score = 0.5
            except Exception as e:
                print(f"Error calculating novelty: {e}")
                clip.novelty_score = 0.5
