"""
Test script demonstrating FAISS search functionality.
"""

import numpy as np
from faiss_search import FAISSEmbeddingSearch, SearchResult, IndexStats


def test_basic_functionality():
    """Test basic FAISS search operations."""
    print("=" * 60)
    print("Testing FAISS Embedding Search")
    print("=" * 60)

    # Test 1: Initialize with different index types
    print("\n1. Testing Index Initialization")
    for index_type in ["Flat", "IVF", "HNSW"]:
        try:
            search = FAISSEmbeddingSearch(
                dimension=384,
                index_type=index_type,
                use_gpu=False
            )
            print(f"  ✓ {index_type} index initialized")
            stats = search.get_stats()
            print(f"    - Dimension: {stats.dimension}")
            print(f"    - Type: {stats.index_type}")
            print(f"    - Vectors: {stats.total_vectors}")
        except Exception as e:
            print(f"  ✗ {index_type} failed: {e}")

    # Test 2: Build index with sample data
    print("\n2. Testing Index Building")
    search = FAISSEmbeddingSearch(dimension=128, index_type="Flat")

    # Create sample embeddings
    n_samples = 100
    embeddings = np.random.randn(n_samples, 128).astype(np.float32)
    ids = [f"item_{i}" for i in range(n_samples)]
    metadata = [{"category": f"cat_{i % 5}", "value": i} for i in range(n_samples)]

    search.build_index(embeddings, ids, metadata)
    stats = search.get_stats()
    print(f"  ✓ Built index with {stats.total_vectors} vectors")
    print(f"    - Memory usage: {stats.memory_usage_mb:.2f} MB")

    # Test 3: Search operations
    print("\n3. Testing Search Operations")

    # Search by embedding
    query_embedding = np.random.randn(128).astype(np.float32)
    results = search.search_similar(query_embedding, k=5)
    print(f"  ✓ Vector search returned {len(results)} results")
    if results:
        print(f"    - Top result: {results[0].id} (score: {results[0].score:.4f})")

    # Search by ID
    results = search.search_by_id("item_10", k=5, exclude_self=True)
    print(f"  ✓ Search by ID returned {len(results)} results")
    if results:
        print(f"    - Top similar: {results[0].id} (score: {results[0].score:.4f})")

    # Test 4: Text embedding and search
    print("\n4. Testing Text Embedding")
    try:
        # This requires sentence-transformers to be installed
        search_with_model = FAISSEmbeddingSearch(dimension=384, index_type="Flat")

        texts = [
            "The quick brown fox jumps over the lazy dog",
            "A journey of a thousand miles begins with a single step",
            "To be or not to be, that is the question"
        ]

        text_embeddings = search_with_model.embed_texts(texts)
        text_ids = [f"text_{i}" for i in range(len(texts))]
        search_with_model.build_index(text_embeddings, text_ids)

        results = search_with_model.search_by_text("What is the meaning of life?", k=3)
        print(f"  ✓ Text search returned {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"    {i}. {result.id} (score: {result.score:.4f})")
    except Exception as e:
        print(f"  ⚠ Text embedding skipped (requires sentence-transformers): {e}")

    # Test 5: Metadata filtering
    print("\n5. Testing Metadata Operations")

    # Filter by metadata
    filtered_ids = search.filter_by_metadata({"category": "cat_2"})
    print(f"  ✓ Metadata filter found {len(filtered_ids)} matching items")

    # Get metadata
    metadata = search.get_metadata("item_5")
    print(f"  ✓ Retrieved metadata: {metadata}")

    # Update metadata
    success = search.update_metadata("item_5", {"category": "updated", "new_field": 42})
    print(f"  ✓ Metadata updated: {success}")

    # Test 6: Batch operations
    print("\n6. Testing Batch Operations")

    # Add batch
    new_embeddings = np.random.randn(10, 128).astype(np.float32)
    new_ids = [f"new_item_{i}" for i in range(10)]
    added = search.add_batch(new_embeddings, new_ids)
    print(f"  ✓ Added {added} vectors in batch")

    # Batch search
    query_embeddings = np.random.randn(5, 128).astype(np.float32)
    batch_results = search.batch_search(query_embeddings, k=3)
    print(f"  ✓ Batch search for {len(batch_results)} queries")

    # Test 7: Persistence
    print("\n7. Testing Index Persistence")

    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = os.path.join(tmpdir, "test_index")

        # Save index
        search.save_index(save_path)
        print(f"  ✓ Index saved to {save_path}")

        # Create new search instance and load
        new_search = FAISSEmbeddingSearch(dimension=128, index_type="Flat")
        new_search.load_index(save_path)
        print(f"  ✓ Index loaded successfully")

        # Verify loaded index
        new_stats = new_search.get_stats()
        print(f"    - Loaded {new_stats.total_vectors} vectors")

        # Test search on loaded index
        results = new_search.search_similar(query_embedding, k=3)
        print(f"  ✓ Search on loaded index returned {len(results)} results")

    # Test 8: Clustering
    print("\n8. Testing Clustering")
    try:
        clusters = search.cluster_embeddings(n_clusters=5)
        print(f"  ✓ Created {len(clusters)} clusters")
        for cluster_id, items in clusters.items():
            print(f"    - Cluster {cluster_id}: {len(items)} items")
    except Exception as e:
        print(f"  ✗ Clustering failed: {e}")

    # Test 9: Index statistics
    print("\n9. Final Index Statistics")
    final_stats = search.get_stats()
    print(f"  Total vectors: {final_stats.total_vectors}")
    print(f"  Dimension: {final_stats.dimension}")
    print(f"  Index type: {final_stats.index_type}")
    print(f"  Is trained: {final_stats.is_trained}")
    print(f"  Memory usage: {final_stats.memory_usage_mb:.2f} MB")
    print(f"  Total IDs: {len(search.get_all_ids())}")

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_basic_functionality()
