"""
FAISS-powered vector similarity search service.

Provides comprehensive vector search capabilities with multiple index types,
GPU support, persistence, and metadata filtering.
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import logging
import tempfile
import os
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Search result with ID, score, and metadata."""
    id: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class IndexStats:
    """Index statistics and information."""
    total_vectors: int
    dimension: int
    index_type: str
    is_trained: bool
    memory_usage_mb: float


class FAISSEmbeddingSearch:
    """FAISS-powered vector similarity search."""

    def __init__(
        self,
        dimension: int = 384,  # all-MiniLM-L6-v2 dimension
        index_type: str = "IVF",  # IVF, Flat, HNSW
        nlist: int = 100,  # Number of clusters for IVF
        use_gpu: bool = False
    ):
        """
        Initialize FAISS index.

        Args:
            dimension: Embedding dimension
            index_type: Type of index (IVF, Flat, HNSW)
            nlist: Number of clusters for IVF index
            use_gpu: Whether to use GPU acceleration
        """
        self.dimension = dimension
        self.index_type = index_type
        self.nlist = nlist
        self.use_gpu = use_gpu
        self.index = None
        self.id_map = {}  # internal_id -> external_id
        self.reverse_id_map = {}  # external_id -> internal_id
        self.metadata_store = {}  # external_id -> metadata
        self.embedding_model = None
        self.next_internal_id = 0
        self._init_index(index_type, nlist, use_gpu)

    def _init_index(
        self,
        index_type: str,
        nlist: int,
        use_gpu: bool
    ) -> None:
        """
        Initialize FAISS index.

        Args:
            index_type: Type of index
            nlist: Number of clusters for IVF
            use_gpu: Whether to use GPU
        """
        try:
            if index_type == "Flat":
                # Simple flat index (exhaustive search)
                self.index = faiss.IndexFlatL2(self.dimension)
            elif index_type == "IVF":
                # IVF index with quantization
                quantizer = faiss.IndexFlatL2(self.dimension)
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            elif index_type == "HNSW":
                # Hierarchical Navigable Small World graph
                self.index = faiss.IndexHNSWFlat(self.dimension, 32)
            else:
                raise ValueError(f"Unknown index type: {index_type}")

            # Move to GPU if requested
            if use_gpu and faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
                logger.info("FAISS index moved to GPU")

            logger.info(f"Initialized {index_type} index with dimension {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS index: {e}")
            raise

    def _load_embedding_model(self) -> None:
        """Load sentence transformer model."""
        if self.embedding_model is None:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Loaded embedding model: all-MiniLM-L6-v2")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise

    # Index Building
    def build_index(
        self,
        embeddings: np.ndarray,
        ids: List[str],
        metadata: List[Dict[str, Any]] = None
    ) -> None:
        """
        Build index from embeddings.

        Args:
            embeddings: Array of embeddings (N x dimension)
            ids: List of external IDs
            metadata: Optional list of metadata dicts
        """
        if len(embeddings) != len(ids):
            raise ValueError("Number of embeddings must match number of IDs")

        if metadata and len(metadata) != len(ids):
            raise ValueError("Number of metadata entries must match number of IDs")

        try:
            # Convert to float32 if needed
            embeddings = embeddings.astype(np.float32)

            # Train index if needed
            if self.index_type == "IVF" and not self.index.is_trained:
                self.train_index(embeddings)

            # Add embeddings
            self.index.add(embeddings)

            # Build ID maps
            for i, external_id in enumerate(ids):
                internal_id = self.next_internal_id + i
                self.id_map[internal_id] = external_id
                self.reverse_id_map[external_id] = internal_id

                # Store metadata if provided
                if metadata:
                    self.metadata_store[external_id] = metadata[i]

            self.next_internal_id += len(ids)
            logger.info(f"Built index with {len(ids)} vectors")
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
            raise

    def train_index(
        self,
        training_embeddings: np.ndarray
    ) -> None:
        """
        Train index (required for IVF).

        Args:
            training_embeddings: Training embeddings
        """
        if self.index_type != "IVF":
            logger.info(f"Training not required for {self.index_type} index")
            return

        try:
            training_embeddings = training_embeddings.astype(np.float32)
            self.index.train(training_embeddings)
            logger.info(f"Trained IVF index with {len(training_embeddings)} vectors")
        except Exception as e:
            logger.error(f"Failed to train index: {e}")
            raise

    # Search
    def search_similar(
        self,
        query_embedding: np.ndarray,
        k: int = 10,
        filter_fn: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ) -> List[SearchResult]:
        """
        Search for similar vectors.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_fn: Optional filter function(id, metadata) -> bool

        Returns:
            List of SearchResult objects
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        try:
            # Reshape and convert to float32
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

            # Search with extra results for filtering
            search_k = min(k * 3 if filter_fn else k, self.index.ntotal)
            distances, indices = self.index.search(query_embedding, search_k)

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0 or idx not in self.id_map:
                    continue

                external_id = self.id_map[idx]
                metadata = self.metadata_store.get(external_id, {})

                # Apply filter if provided
                if filter_fn and not filter_fn(external_id, metadata):
                    continue

                # Convert distance to similarity score (lower distance = higher similarity)
                score = float(1.0 / (1.0 + dist))

                results.append(SearchResult(
                    id=external_id,
                    score=score,
                    metadata=metadata
                ))

                if len(results) >= k:
                    break

            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_by_text(
        self,
        text: str,
        k: int = 10,
        filter_fn: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ) -> List[SearchResult]:
        """
        Search using text query.

        Args:
            text: Text query
            k: Number of results
            filter_fn: Optional filter function

        Returns:
            List of SearchResult objects
        """
        self._load_embedding_model()
        embedding = self.embed_text(text)
        return self.search_similar(embedding, k, filter_fn)

    def search_by_id(
        self,
        id: str,
        k: int = 10,
        exclude_self: bool = True
    ) -> List[SearchResult]:
        """
        Find similar items to existing item.

        Args:
            id: External ID to find similar items for
            k: Number of results
            exclude_self: Whether to exclude the query item from results

        Returns:
            List of SearchResult objects
        """
        if id not in self.reverse_id_map:
            logger.warning(f"ID not found in index: {id}")
            return []

        try:
            # Get the embedding for this ID
            internal_id = self.reverse_id_map[id]
            embedding = self.index.reconstruct(int(internal_id))

            # Search
            results = self.search_similar(embedding, k + 1 if exclude_self else k)

            # Remove self if requested
            if exclude_self:
                results = [r for r in results if r.id != id][:k]

            return results
        except Exception as e:
            logger.error(f"Search by ID failed: {e}")
            return []

    def batch_search(
        self,
        query_embeddings: np.ndarray,
        k: int = 10
    ) -> List[List[SearchResult]]:
        """
        Batch search for multiple queries.

        Args:
            query_embeddings: Array of query embeddings (N x dimension)
            k: Number of results per query

        Returns:
            List of result lists
        """
        if self.index is None or self.index.ntotal == 0:
            return [[] for _ in range(len(query_embeddings))]

        try:
            query_embeddings = query_embeddings.astype(np.float32)
            distances, indices = self.index.search(query_embeddings, k)

            all_results = []
            for query_dists, query_indices in zip(distances, indices):
                results = []
                for dist, idx in zip(query_dists, query_indices):
                    if idx < 0 or idx not in self.id_map:
                        continue

                    external_id = self.id_map[idx]
                    metadata = self.metadata_store.get(external_id, {})
                    score = float(1.0 / (1.0 + dist))

                    results.append(SearchResult(
                        id=external_id,
                        score=score,
                        metadata=metadata
                    ))

                all_results.append(results)

            return all_results
        except Exception as e:
            logger.error(f"Batch search failed: {e}")
            return [[] for _ in range(len(query_embeddings))]

    # Index Management
    def add_to_index(
        self,
        embedding: np.ndarray,
        id: str,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add single embedding to index.

        Args:
            embedding: Embedding vector
            id: External ID
            metadata: Optional metadata

        Returns:
            Success status
        """
        try:
            return self.add_batch(
                embedding.reshape(1, -1),
                [id],
                [metadata] if metadata else None
            ) == 1
        except Exception as e:
            logger.error(f"Failed to add to index: {e}")
            return False

    def add_batch(
        self,
        embeddings: np.ndarray,
        ids: List[str],
        metadata: List[Dict[str, Any]] = None
    ) -> int:
        """
        Add batch of embeddings.

        Args:
            embeddings: Array of embeddings
            ids: List of external IDs
            metadata: Optional list of metadata

        Returns:
            Number of embeddings added
        """
        if len(embeddings) != len(ids):
            raise ValueError("Number of embeddings must match number of IDs")

        try:
            embeddings = embeddings.astype(np.float32)

            # Train if needed
            if self.index_type == "IVF" and not self.index.is_trained:
                self.train_index(embeddings)

            # Add to index
            self.index.add(embeddings)

            # Update maps
            for i, external_id in enumerate(ids):
                internal_id = self.next_internal_id + i
                self.id_map[internal_id] = external_id
                self.reverse_id_map[external_id] = internal_id

                if metadata and i < len(metadata):
                    self.metadata_store[external_id] = metadata[i]

            self.next_internal_id += len(ids)
            logger.info(f"Added {len(ids)} vectors to index")
            return len(ids)
        except Exception as e:
            logger.error(f"Failed to add batch: {e}")
            return 0

    def remove_from_index(
        self,
        id: str
    ) -> bool:
        """
        Remove embedding from index.

        Note: FAISS doesn't support true deletion. This removes from metadata
        and ID maps, but the vector remains in the index.

        Args:
            id: External ID to remove

        Returns:
            Success status
        """
        if id not in self.reverse_id_map:
            logger.warning(f"ID not found: {id}")
            return False

        try:
            internal_id = self.reverse_id_map[id]

            # Remove from maps
            del self.id_map[internal_id]
            del self.reverse_id_map[id]

            # Remove metadata
            if id in self.metadata_store:
                del self.metadata_store[id]

            logger.info(f"Removed ID {id} from metadata (vector remains in index)")
            return True
        except Exception as e:
            logger.error(f"Failed to remove from index: {e}")
            return False

    def update_embedding(
        self,
        id: str,
        new_embedding: np.ndarray,
        new_metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Update existing embedding.

        Note: Implements update as remove + add since FAISS doesn't support in-place updates.

        Args:
            id: External ID
            new_embedding: New embedding vector
            new_metadata: Optional new metadata

        Returns:
            Success status
        """
        # Remove old entry
        self.remove_from_index(id)

        # Add new entry
        return self.add_to_index(new_embedding, id, new_metadata)

    # Persistence
    def save_index(
        self,
        path: str
    ) -> None:
        """
        Save index to disk.

        Args:
            path: Base path for saving (will create .index and .meta files)
        """
        try:
            path_obj = Path(path)
            path_obj.parent.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            index_path = str(path_obj.with_suffix('.index'))
            if self.use_gpu:
                # Move to CPU for saving
                cpu_index = faiss.index_gpu_to_cpu(self.index)
                faiss.write_index(cpu_index, index_path)
            else:
                faiss.write_index(self.index, index_path)

            # Save metadata
            meta_path = str(path_obj.with_suffix('.meta'))
            metadata = {
                'id_map': self.id_map,
                'reverse_id_map': self.reverse_id_map,
                'metadata_store': self.metadata_store,
                'next_internal_id': self.next_internal_id,
                'dimension': self.dimension,
                'index_type': self.index_type,
                'nlist': self.nlist
            }
            with open(meta_path, 'wb') as f:
                pickle.dump(metadata, f)

            logger.info(f"Saved index to {path}")
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            raise

    def load_index(
        self,
        path: str
    ) -> None:
        """
        Load index from disk.

        Args:
            path: Base path for loading
        """
        try:
            path_obj = Path(path)

            # Load FAISS index
            index_path = str(path_obj.with_suffix('.index'))
            self.index = faiss.read_index(index_path)

            # Move to GPU if requested
            if self.use_gpu and faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)

            # Load metadata
            meta_path = str(path_obj.with_suffix('.meta'))
            with open(meta_path, 'rb') as f:
                metadata = pickle.load(f)

            self.id_map = metadata['id_map']
            self.reverse_id_map = metadata['reverse_id_map']
            self.metadata_store = metadata['metadata_store']
            self.next_internal_id = metadata['next_internal_id']
            self.dimension = metadata['dimension']
            self.index_type = metadata['index_type']
            self.nlist = metadata.get('nlist', 100)

            logger.info(f"Loaded index from {path}")
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            raise

    def export_to_gcs(
        self,
        bucket_name: str,
        blob_name: str
    ) -> str:
        """
        Export index to Google Cloud Storage.

        Args:
            bucket_name: GCS bucket name
            blob_name: Base blob name

        Returns:
            GCS URI
        """
        try:
            from google.cloud import storage

            # Save to temp file
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = os.path.join(tmpdir, 'index')
                self.save_index(local_path)

                # Upload to GCS
                client = storage.Client()
                bucket = client.bucket(bucket_name)

                # Upload index file
                index_blob = bucket.blob(f"{blob_name}.index")
                index_blob.upload_from_filename(f"{local_path}.index")

                # Upload metadata file
                meta_blob = bucket.blob(f"{blob_name}.meta")
                meta_blob.upload_from_filename(f"{local_path}.meta")

            gcs_uri = f"gs://{bucket_name}/{blob_name}"
            logger.info(f"Exported index to {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"Failed to export to GCS: {e}")
            raise

    def import_from_gcs(
        self,
        bucket_name: str,
        blob_name: str
    ) -> None:
        """
        Import index from GCS.

        Args:
            bucket_name: GCS bucket name
            blob_name: Base blob name
        """
        try:
            from google.cloud import storage

            # Download to temp file
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = os.path.join(tmpdir, 'index')

                # Download from GCS
                client = storage.Client()
                bucket = client.bucket(bucket_name)

                # Download index file
                index_blob = bucket.blob(f"{blob_name}.index")
                index_blob.download_to_filename(f"{local_path}.index")

                # Download metadata file
                meta_blob = bucket.blob(f"{blob_name}.meta")
                meta_blob.download_to_filename(f"{local_path}.meta")

                # Load index
                self.load_index(local_path)

            logger.info(f"Imported index from gs://{bucket_name}/{blob_name}")
        except Exception as e:
            logger.error(f"Failed to import from GCS: {e}")
            raise

    # Embeddings
    def embed_text(
        self,
        text: str
    ) -> np.ndarray:
        """
        Generate embedding for text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        self._load_embedding_model()
        try:
            return self.embedding_model.encode(text, convert_to_numpy=True)
        except Exception as e:
            logger.error(f"Failed to embed text: {e}")
            raise

    def embed_texts(
        self,
        texts: List[str]
    ) -> np.ndarray:
        """
        Batch generate embeddings.

        Args:
            texts: List of input texts

        Returns:
            Array of embeddings (N x dimension)
        """
        self._load_embedding_model()
        try:
            return self.embedding_model.encode(texts, convert_to_numpy=True)
        except Exception as e:
            logger.error(f"Failed to embed texts: {e}")
            raise

    # Metadata
    def get_metadata(
        self,
        id: str
    ) -> Dict[str, Any]:
        """
        Get metadata for ID.

        Args:
            id: External ID

        Returns:
            Metadata dict (empty if not found)
        """
        return self.metadata_store.get(id, {})

    def update_metadata(
        self,
        id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update metadata for ID.

        Args:
            id: External ID
            metadata: New metadata

        Returns:
            Success status
        """
        if id not in self.reverse_id_map:
            logger.warning(f"ID not found: {id}")
            return False

        self.metadata_store[id] = metadata
        return True

    def filter_by_metadata(
        self,
        filter_dict: Dict[str, Any]
    ) -> List[str]:
        """
        Get IDs matching metadata filter.

        Args:
            filter_dict: Key-value pairs to match

        Returns:
            List of matching IDs
        """
        matching_ids = []
        for id, metadata in self.metadata_store.items():
            if all(metadata.get(k) == v for k, v in filter_dict.items()):
                matching_ids.append(id)
        return matching_ids

    # Stats
    def get_stats(self) -> IndexStats:
        """
        Get index statistics.

        Returns:
            IndexStats object
        """
        if self.index is None:
            return IndexStats(
                total_vectors=0,
                dimension=self.dimension,
                index_type=self.index_type,
                is_trained=False,
                memory_usage_mb=0.0
            )

        is_trained = True
        if self.index_type == "IVF":
            is_trained = self.index.is_trained

        # Estimate memory usage
        bytes_per_vector = self.dimension * 4  # float32
        total_bytes = self.index.ntotal * bytes_per_vector
        memory_mb = total_bytes / (1024 * 1024)

        return IndexStats(
            total_vectors=self.index.ntotal,
            dimension=self.dimension,
            index_type=self.index_type,
            is_trained=is_trained,
            memory_usage_mb=memory_mb
        )

    def get_all_ids(self) -> List[str]:
        """
        Get all indexed IDs.

        Returns:
            List of external IDs
        """
        return list(self.reverse_id_map.keys())

    # Clustering
    def cluster_embeddings(
        self,
        n_clusters: int = 10
    ) -> Dict[int, List[str]]:
        """
        Cluster indexed embeddings.

        Args:
            n_clusters: Number of clusters

        Returns:
            Dict mapping cluster ID to list of external IDs
        """
        if self.index is None or self.index.ntotal == 0:
            return {}

        try:
            # Extract all embeddings
            n_vectors = self.index.ntotal
            embeddings = np.zeros((n_vectors, self.dimension), dtype=np.float32)
            for i in range(n_vectors):
                embeddings[i] = self.index.reconstruct(i)

            # Perform k-means clustering
            n_clusters = min(n_clusters, n_vectors)
            kmeans = faiss.Kmeans(self.dimension, n_clusters, niter=20, verbose=False)
            kmeans.train(embeddings)

            # Assign clusters
            _, cluster_assignments = kmeans.index.search(embeddings, 1)

            # Build cluster map
            clusters = {}
            for internal_id, cluster_id in enumerate(cluster_assignments.flatten()):
                cluster_id = int(cluster_id)
                if cluster_id not in clusters:
                    clusters[cluster_id] = []

                if internal_id in self.id_map:
                    external_id = self.id_map[internal_id]
                    clusters[cluster_id].append(external_id)

            logger.info(f"Clustered {n_vectors} vectors into {n_clusters} clusters")
            return clusters
        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            return {}

    def find_cluster(
        self,
        id: str
    ) -> int:
        """
        Find cluster for ID.

        Args:
            id: External ID

        Returns:
            Cluster ID (-1 if not found)
        """
        if id not in self.reverse_id_map:
            return -1

        try:
            # Get embedding
            internal_id = self.reverse_id_map[id]
            embedding = self.index.reconstruct(int(internal_id)).reshape(1, -1)

            # Perform clustering with small k to find nearest cluster centroid
            clusters = self.cluster_embeddings(n_clusters=10)

            # Simple approach: search among all items and find majority cluster
            # This is a simplified implementation
            similar = self.search_by_id(id, k=20, exclude_self=True)

            # Count cluster memberships (would need to store cluster assignments)
            # For now, return -1 as this requires persistent cluster state
            logger.warning("find_cluster requires persistent cluster state")
            return -1
        except Exception as e:
            logger.error(f"Failed to find cluster: {e}")
            return -1
