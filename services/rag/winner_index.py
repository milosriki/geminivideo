import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
import tempfile
import os
from pathlib import Path
import logging
from .gcs_storage import gcs_store

logger = logging.getLogger(__name__)

class WinnerIndex:
    def __init__(
        self,
        index_path: str = "/tmp/winners.index",
        namespace: str = "winners",
        use_gcs: bool = True
    ):
        """
        Initialize WinnerIndex with GCS-backed persistent storage.

        Args:
            index_path: Local path for temporary files (used as fallback)
            namespace: GCS namespace for organizing patterns
            use_gcs: Whether to use GCS storage (falls back to local if unavailable)
        """
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = 384
        self.index = faiss.IndexFlatIP(self.dimension)
        self.winners: List[Dict[str, Any]] = []
        self.index_path = index_path
        self.namespace = namespace
        self.use_gcs = use_gcs and gcs_store.use_gcs

        # Create temp directory for FAISS index operations
        self.temp_dir = Path(tempfile.mkdtemp(prefix="winner_index_"))

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
        """Save index and patterns to GCS or local fallback."""
        if self.use_gcs:
            self._save_to_gcs()
        else:
            self._save_to_local()

    def _save_to_gcs(self):
        """Save to GCS with local temp files."""
        try:
            # Save FAISS index to temp file
            temp_faiss = self.temp_dir / "winners.faiss"
            faiss.write_index(self.index, str(temp_faiss))

            # Upload FAISS index to GCS
            gcs_store.store_binary(
                str(temp_faiss),
                self.namespace,
                "winners.faiss"
            )

            # Upload patterns metadata to GCS
            gcs_store.store_patterns(
                self.winners,
                self.namespace,
                metadata={"total_count": len(self.winners)}
            )

            logger.info(f"Saved {len(self.winners)} winners to GCS: {self.namespace}")
        except Exception as e:
            logger.error(f"Failed to save to GCS, falling back to local: {e}")
            self._save_to_local()

    def _save_to_local(self):
        """Save to local filesystem (fallback)."""
        try:
            faiss.write_index(self.index, f"{self.index_path}.faiss")
            with open(f"{self.index_path}.json", 'w') as f:
                json.dump(self.winners, f)
            logger.info(f"Saved {len(self.winners)} winners locally: {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to save locally: {e}")

    def _load_if_exists(self):
        """Load index and patterns from GCS or local fallback."""
        if self.use_gcs:
            self._load_from_gcs()
        else:
            self._load_from_local()

    def _load_from_gcs(self):
        """Load from GCS with local temp files."""
        try:
            # Check if patterns exist in GCS
            if not gcs_store.exists(self.namespace):
                logger.info(f"No existing patterns in GCS: {self.namespace}")
                return

            # Download FAISS index to temp file
            temp_faiss = self.temp_dir / "winners.faiss"
            if gcs_store.load_binary(self.namespace, "winners.faiss", str(temp_faiss)):
                self.index = faiss.read_index(str(temp_faiss))

                # Load patterns metadata from GCS
                self.winners = gcs_store.load_patterns(self.namespace)

                logger.info(f"Loaded {len(self.winners)} winners from GCS: {self.namespace}")
            else:
                logger.warning(f"FAISS index not found in GCS, trying local fallback")
                self._load_from_local()
        except Exception as e:
            logger.error(f"Failed to load from GCS, trying local fallback: {e}")
            self._load_from_local()

    def _load_from_local(self):
        """Load from local filesystem (fallback)."""
        try:
            if Path(f"{self.index_path}.faiss").exists():
                self.index = faiss.read_index(f"{self.index_path}.faiss")
                with open(f"{self.index_path}.json", 'r') as f:
                    self.winners = json.load(f)
                logger.info(f"Loaded {len(self.winners)} winners locally: {self.index_path}")
            else:
                logger.info(f"No existing local patterns: {self.index_path}")
        except Exception as e:
            logger.error(f"Failed to load locally: {e}")

# Singleton instance
winner_index = WinnerIndex()
