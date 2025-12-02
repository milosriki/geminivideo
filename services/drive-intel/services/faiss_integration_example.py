"""
Integration example: Using FAISS search with Drive-Intel services.

Demonstrates how to integrate FAISSEmbeddingSearch with existing
feature extraction, ingestion, and search workflows.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from faiss_search import FAISSEmbeddingSearch, SearchResult

logger = logging.getLogger(__name__)


class VideoSearchEngine:
    """
    Production video search engine using FAISS.

    Combines feature extraction, embedding generation, and similarity search
    for intelligent video clip discovery.
    """

    def __init__(
        self,
        index_type: str = "HNSW",
        use_gpu: bool = False,
        persistence_path: Optional[str] = None
    ):
        """
        Initialize search engine.

        Args:
            index_type: FAISS index type (Flat, IVF, HNSW)
            use_gpu: Whether to use GPU acceleration
            persistence_path: Path to load/save index
        """
        self.search = FAISSEmbeddingSearch(
            dimension=384,  # all-MiniLM-L6-v2
            index_type=index_type,
            use_gpu=use_gpu
        )

        self.persistence_path = persistence_path

        # Load existing index if available
        if persistence_path and Path(persistence_path + ".index").exists():
            try:
                self.search.load_index(persistence_path)
                logger.info(f"Loaded existing index from {persistence_path}")
            except Exception as e:
                logger.warning(f"Failed to load index: {e}")

    def index_video_clips(
        self,
        clips: List[Any]
    ) -> int:
        """
        Index video clips with embeddings.

        Args:
            clips: List of Clip objects with features

        Returns:
            Number of clips indexed
        """
        embeddings = []
        ids = []
        metadata = []

        for clip in clips:
            # Check if clip has embedding
            if not hasattr(clip, 'features') or not clip.features.embedding:
                continue

            embeddings.append(clip.features.embedding)
            ids.append(clip.id)

            # Extract metadata
            clip_metadata = {
                'asset_id': getattr(clip, 'asset_id', None),
                'start_time': getattr(clip, 'start_time', 0),
                'end_time': getattr(clip, 'end_time', 0),
                'duration': getattr(clip, 'duration', 0),
                'scene_type': getattr(clip, 'scene_type', None),
                'motion_score': getattr(clip, 'motion_score', 0),
                'novelty_score': getattr(clip, 'novelty_score', 0),
            }

            # Add visual features if available
            if hasattr(clip.features, 'dominant_colors'):
                clip_metadata['dominant_colors'] = clip.features.dominant_colors
            if hasattr(clip.features, 'brightness'):
                clip_metadata['brightness'] = clip.features.brightness

            metadata.append(clip_metadata)

        if not embeddings:
            logger.warning("No clips with embeddings found")
            return 0

        # Build/update index
        embeddings_array = np.array(embeddings, dtype=np.float32)

        if self.search.index is None or self.search.index.ntotal == 0:
            # Build new index
            self.search.build_index(embeddings_array, ids, metadata)
        else:
            # Add to existing index
            self.search.add_batch(embeddings_array, ids, metadata)

        # Save if persistence enabled
        if self.persistence_path:
            self.search.save_index(self.persistence_path)

        logger.info(f"Indexed {len(embeddings)} clips")
        return len(embeddings)

    def search_by_description(
        self,
        description: str,
        k: int = 10,
        asset_id: Optional[str] = None,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        scene_type: Optional[str] = None
    ) -> List[SearchResult]:
        """
        Search clips by text description with optional filters.

        Args:
            description: Natural language search query
            k: Number of results
            asset_id: Filter by specific asset
            min_duration: Minimum clip duration
            max_duration: Maximum clip duration
            scene_type: Filter by scene type

        Returns:
            List of SearchResult objects
        """
        # Build filter function
        def clip_filter(id: str, metadata: Dict[str, Any]) -> bool:
            # Asset filter
            if asset_id and metadata.get('asset_id') != asset_id:
                return False

            # Duration filters
            duration = metadata.get('duration', 0)
            if min_duration and duration < min_duration:
                return False
            if max_duration and duration > max_duration:
                return False

            # Scene type filter
            if scene_type and metadata.get('scene_type') != scene_type:
                return False

            return True

        # Search
        results = self.search.search_by_text(
            text=description,
            k=k,
            filter_fn=clip_filter if any([asset_id, min_duration, max_duration, scene_type]) else None
        )

        logger.info(f"Search '{description}' returned {len(results)} results")
        return results

    def find_similar_clips(
        self,
        clip_id: str,
        k: int = 10,
        same_asset_only: bool = False
    ) -> List[SearchResult]:
        """
        Find clips similar to a given clip.

        Args:
            clip_id: ID of reference clip
            k: Number of similar clips to find
            same_asset_only: Only return clips from same asset

        Returns:
            List of SearchResult objects
        """
        if same_asset_only:
            # Get reference clip's asset_id
            ref_metadata = self.search.get_metadata(clip_id)
            ref_asset_id = ref_metadata.get('asset_id')

            if ref_asset_id:
                # Search with asset filter
                results = self.search.search_by_id(clip_id, k=k * 2, exclude_self=True)

                # Filter by asset
                filtered = [
                    r for r in results
                    if r.metadata.get('asset_id') == ref_asset_id
                ][:k]

                return filtered

        # Standard similar search
        return self.search.search_by_id(clip_id, k=k, exclude_self=True)

    def discover_novel_clips(
        self,
        k: int = 20,
        min_novelty: float = 0.7
    ) -> List[SearchResult]:
        """
        Discover novel/unique clips based on semantic diversity.

        Args:
            k: Number of clips to return
            min_novelty: Minimum novelty score threshold

        Returns:
            List of SearchResult objects sorted by novelty
        """
        # Get all IDs
        all_ids = self.search.get_all_ids()

        novel_clips = []

        for clip_id in all_ids:
            metadata = self.search.get_metadata(clip_id)
            novelty = metadata.get('novelty_score', 0)

            if novelty >= min_novelty:
                # Find similar to estimate uniqueness
                similar = self.search.search_by_id(clip_id, k=5, exclude_self=True)

                # Calculate average distance
                if similar:
                    avg_similarity = np.mean([r.score for r in similar])
                    uniqueness = 1.0 - avg_similarity
                else:
                    uniqueness = 1.0

                novel_clips.append(SearchResult(
                    id=clip_id,
                    score=uniqueness,
                    metadata=metadata
                ))

        # Sort by uniqueness
        novel_clips.sort(key=lambda x: x.score, reverse=True)

        return novel_clips[:k]

    def cluster_clips(
        self,
        n_clusters: int = 10
    ) -> Dict[int, List[str]]:
        """
        Cluster clips into semantic groups.

        Args:
            n_clusters: Number of clusters

        Returns:
            Dict mapping cluster ID to clip IDs
        """
        return self.search.cluster_embeddings(n_clusters=n_clusters)

    def get_cluster_representatives(
        self,
        n_clusters: int = 10
    ) -> Dict[int, str]:
        """
        Get representative clip for each cluster (centroid).

        Args:
            n_clusters: Number of clusters

        Returns:
            Dict mapping cluster ID to representative clip ID
        """
        clusters = self.cluster_clips(n_clusters)
        representatives = {}

        for cluster_id, clip_ids in clusters.items():
            if not clip_ids:
                continue

            # Find clip closest to centroid
            # Simple approach: find clip most similar to all others in cluster
            best_clip = None
            best_avg_similarity = -1

            for candidate_id in clip_ids:
                # Get similarities to other clips in cluster
                similarities = []
                for other_id in clip_ids:
                    if other_id == candidate_id:
                        continue

                    # Search for this clip
                    results = self.search.search_by_id(candidate_id, k=len(clip_ids))

                    # Find other_id in results
                    for r in results:
                        if r.id == other_id:
                            similarities.append(r.score)
                            break

                if similarities:
                    avg_sim = np.mean(similarities)
                    if avg_sim > best_avg_similarity:
                        best_avg_similarity = avg_sim
                        best_clip = candidate_id

            if best_clip:
                representatives[cluster_id] = best_clip

        return representatives

    def export_to_cloud(
        self,
        bucket_name: str,
        index_name: str
    ) -> str:
        """
        Export index to Google Cloud Storage.

        Args:
            bucket_name: GCS bucket
            index_name: Name for index in GCS

        Returns:
            GCS URI
        """
        return self.search.export_to_gcs(bucket_name, index_name)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get search engine statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.search.get_stats()

        return {
            'total_clips': stats.total_vectors,
            'embedding_dimension': stats.dimension,
            'index_type': stats.index_type,
            'is_trained': stats.is_trained,
            'memory_usage_mb': stats.memory_usage_mb,
            'persistence_path': self.persistence_path
        }


def example_usage():
    """Example usage of VideoSearchEngine."""

    print("=" * 60)
    print("Video Search Engine - Integration Example")
    print("=" * 60)

    # Initialize engine
    engine = VideoSearchEngine(
        index_type="HNSW",
        use_gpu=False,
        persistence_path="/tmp/video_search_index"
    )

    print("\n1. Creating sample video clips...")

    # Simulate clips (would come from FeatureExtractor in production)
    from dataclasses import dataclass
    from typing import Optional

    @dataclass
    class Features:
        embedding: np.ndarray
        dominant_colors: List[str]
        brightness: float

    @dataclass
    class Clip:
        id: str
        asset_id: str
        start_time: float
        end_time: float
        duration: float
        scene_type: str
        motion_score: float
        novelty_score: float
        features: Features

    # Create sample clips
    clips = []
    for i in range(50):
        clip = Clip(
            id=f"clip_{i}",
            asset_id=f"asset_{i % 5}",
            start_time=i * 5.0,
            end_time=(i + 1) * 5.0,
            duration=5.0,
            scene_type=["outdoor", "indoor", "action", "dialogue"][i % 4],
            motion_score=np.random.random(),
            novelty_score=np.random.random(),
            features=Features(
                embedding=np.random.randn(384).astype(np.float32),
                dominant_colors=["red", "blue", "green"],
                brightness=np.random.random()
            )
        )
        clips.append(clip)

    # Index clips
    print("\n2. Indexing clips...")
    indexed_count = engine.index_video_clips(clips)
    print(f"   Indexed {indexed_count} clips")

    # Search by description
    print("\n3. Searching by description...")
    results = engine.search_by_description(
        description="outdoor action scene",
        k=5,
        scene_type="outdoor"
    )
    print(f"   Found {len(results)} results")
    for i, result in enumerate(results[:3], 1):
        print(f"   {i}. {result.id} (score: {result.score:.4f})")

    # Find similar clips
    print("\n4. Finding similar clips...")
    similar = engine.find_similar_clips(
        clip_id="clip_10",
        k=5,
        same_asset_only=False
    )
    print(f"   Found {len(similar)} similar clips to clip_10")
    for i, result in enumerate(similar[:3], 1):
        print(f"   {i}. {result.id} (score: {result.score:.4f})")

    # Discover novel clips
    print("\n5. Discovering novel clips...")
    novel = engine.discover_novel_clips(k=5, min_novelty=0.0)
    print(f"   Found {len(novel)} novel clips")

    # Cluster clips
    print("\n6. Clustering clips...")
    clusters = engine.cluster_clips(n_clusters=5)
    print(f"   Created {len(clusters)} clusters")
    for cluster_id, clip_ids in clusters.items():
        print(f"   Cluster {cluster_id}: {len(clip_ids)} clips")

    # Get statistics
    print("\n7. Engine statistics...")
    stats = engine.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    print("Integration example completed!")
    print("=" * 60)


if __name__ == "__main__":
    example_usage()
