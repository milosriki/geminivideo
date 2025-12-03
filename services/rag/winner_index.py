import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
from pathlib import Path

class WinnerIndex:
    def __init__(self, index_path: str = "/tmp/winners.index"):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = faiss.IndexFlatIP(self.dimension)
        self.winners: List[Dict[str, Any]] = []
        self.index_path = index_path
        self._load_if_exists()

    def add_winner(self, ad_data: dict, ctr: float, min_ctr: float = 0.03):
        """Add winning ad to index if CTR exceeds threshold"""
        if ctr < min_ctr:
            return False

        # Create embedding from ad content
        text = f"{ad_data.get('hook', '')} {ad_data.get('body', '')} {ad_data.get('cta', '')}"
        embedding = self.model.encode(text, normalize_embeddings=True)

        # Add to FAISS
        self.index.add(np.array([embedding], dtype=np.float32))
        self.winners.append({"data": ad_data, "ctr": ctr})

        self._save()
        return True

    def find_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Find similar winning ads"""
        if self.index.ntotal == 0:
            return []

        query_emb = self.model.encode(query, normalize_embeddings=True)
        distances, indices = self.index.search(
            np.array([query_emb], dtype=np.float32),
            min(k, self.index.ntotal)
        )

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and idx < len(self.winners):
                results.append({
                    **self.winners[idx],
                    "similarity": float(dist)
                })
        return results

    def _save(self):
        faiss.write_index(self.index, f"{self.index_path}.faiss")
        with open(f"{self.index_path}.json", 'w') as f:
            json.dump(self.winners, f)

    def _load_if_exists(self):
        if Path(f"{self.index_path}.faiss").exists():
            self.index = faiss.read_index(f"{self.index_path}.faiss")
            with open(f"{self.index_path}.json", 'r') as f:
                self.winners = json.load(f)

# Singleton instance
winner_index = WinnerIndex()
