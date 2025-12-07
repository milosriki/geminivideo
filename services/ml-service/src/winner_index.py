"""
FAISS-based RAG index for winning ad patterns.
Learn from winners, find similar patterns, scale what works.
"""
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import json
import os
import threading

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("⚠️ FAISS not available. Install with: pip install faiss-cpu")

@dataclass
class WinnerMatch:
    ad_id: str
    similarity: float
    metadata: Dict

class WinnerIndex:
    """FAISS-based RAG index for winning ad patterns."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, dimension: int = 768, index_path: str = "/data/winner_index"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, dimension: int = 768, index_path: str = "/data/winner_index"):
        if self._initialized:
            return

        if not FAISS_AVAILABLE:
            print("⚠️ WinnerIndex initialized but FAISS not available")
            self._initialized = True
            return

        self.dimension = dimension
        self.index_path = index_path
        self.metadata_path = f"{index_path}_metadata.json"

        # Try to load existing index
        if os.path.exists(f"{index_path}.faiss"):
            self.index = faiss.read_index(f"{index_path}.faiss")
            with open(self.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            print(f"✅ Loaded existing winner index with {self.index.ntotal} winners")
        else:
            self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
            self.metadata = {}
            print(f"✅ Created new winner index (dimension={dimension})")

        self._initialized = True

    def add_winner(self, ad_id: str, embedding: np.ndarray, metadata: Dict) -> bool:
        """Add a winning ad pattern to the index."""
        if not FAISS_AVAILABLE:
            return False

        if embedding.shape[0] != self.dimension:
            raise ValueError(f"Expected {self.dimension} dimensions, got {embedding.shape[0]}")

        # Normalize for cosine similarity
        embedding = embedding / np.linalg.norm(embedding)
        embedding = embedding.reshape(1, -1).astype('float32')

        idx = self.index.ntotal
        self.index.add(embedding)
        self.metadata[str(idx)] = {"ad_id": ad_id, **metadata}

        print(f"✅ Added winner {ad_id} to index (total: {self.index.ntotal})")
        return True

    def find_similar(self, embedding: np.ndarray, k: int = 5) -> List[WinnerMatch]:
        """Find k most similar winning ads."""
        if not FAISS_AVAILABLE or self.index.ntotal == 0:
            return []

        embedding = embedding / np.linalg.norm(embedding)
        embedding = embedding.reshape(1, -1).astype('float32')

        distances, indices = self.index.search(embedding, min(k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            meta = self.metadata.get(str(idx), {})
            results.append(WinnerMatch(
                ad_id=meta.get("ad_id", "unknown"),
                similarity=float(dist),
                metadata=meta
            ))

        return results

    def persist(self) -> bool:
        """Save index to disk."""
        if not FAISS_AVAILABLE:
            return False

        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        faiss.write_index(self.index, f"{self.index_path}.faiss")
        with open(self.metadata_path, 'w') as f:
            json.dump(self.metadata, f)
        print(f"✅ Persisted winner index to {self.index_path}")
        return True

    def stats(self) -> Dict:
        """Get index statistics."""
        return {
            "total_winners": self.index.ntotal if FAISS_AVAILABLE else 0,
            "dimension": self.dimension,
            "index_path": self.index_path,
            "faiss_available": FAISS_AVAILABLE
        }

# Singleton getter
def get_winner_index() -> WinnerIndex:
    return WinnerIndex()
