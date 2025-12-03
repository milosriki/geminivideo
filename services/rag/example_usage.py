"""
Example usage of the Winner RAG system

This demonstrates how to:
1. Add winning ads to the index
2. Search for similar winners
3. Use helper functions for better results
"""

from winner_index import winner_index
from embeddings import (
    prepare_ad_text,
    extract_ad_features,
    score_ad_quality,
    deduplicate_results,
    expand_query
)


def example_add_winners():
    """Example: Adding winning ads to the index"""

    # Example winning ad 1
    ad1 = {
        "hook": "Transform Your Kitchen in 24 Hours",
        "body": "Professional cabinet refinishing. No mess, no stress. 5-star rated service.",
        "cta": "Book Free Consultation",
        "theme": "home improvement",
        "audience": "homeowners 35-55"
    }
    winner_index.add_winner(ad1, ctr=0.045)

    # Example winning ad 2
    ad2 = {
        "hook": "Ready for Your Dream Kitchen?",
        "body": "Custom cabinets installed in just one day. Lifetime warranty included.",
        "cta": "Get Instant Quote",
        "theme": "home improvement",
        "audience": "homeowners 30-50"
    }
    winner_index.add_winner(ad2, ctr=0.038)

    # Example winning ad 3 - different niche
    ad3 = {
        "hook": "Lose 10 Pounds in 30 Days",
        "body": "Science-backed meal plans. No gym required. Join 50,000+ success stories.",
        "cta": "Start Free Trial",
        "theme": "health & fitness",
        "audience": "adults 25-45"
    }
    winner_index.add_winner(ad3, ctr=0.052)

    print("Added 3 winning ads to the index!")


def example_search():
    """Example: Searching for similar winning ads"""

    # Simple search
    query = "kitchen renovation services"
    results = winner_index.find_similar(query, k=3)

    print(f"\n=== Search Results for: '{query}' ===")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Similarity: {result['similarity']:.3f} | CTR: {result['ctr']:.3f}")
        print(f"   Hook: {result['data']['hook']}")
        print(f"   Body: {result['data']['body']}")

    # Advanced search with query expansion
    expanded = expand_query("best weight loss")
    print(f"\n=== Expanded Queries: {expanded[:3]} ===")


def example_features():
    """Example: Analyzing ad features"""

    ad = {
        "hook": "LAST CHANCE: 50% Off Today Only!",
        "body": "Premium quality at half price. Limited stock available.",
        "cta": "Shop Now"
    }

    features = extract_ad_features(ad)
    quality_score = score_ad_quality(ad, ctr=0.042)

    print("\n=== Ad Feature Analysis ===")
    print(f"Features: {features}")
    print(f"Quality Score: {quality_score:.1f}/100")


def example_deduplication():
    """Example: Removing duplicate results"""

    # Simulate search results with duplicates
    results = [
        {"data": {"hook": "Save 50% Today", "body": "Limited offer"}, "similarity": 0.98, "ctr": 0.04},
        {"data": {"hook": "Save 50% Today", "body": "Limited offer"}, "similarity": 0.97, "ctr": 0.04},
        {"data": {"hook": "Get 50% Off Now", "body": "Flash sale"}, "similarity": 0.85, "ctr": 0.03},
    ]

    filtered = deduplicate_results(results, similarity_threshold=0.96)
    print(f"\n=== Deduplication ===")
    print(f"Original: {len(results)} results")
    print(f"After dedup: {len(filtered)} results")


if __name__ == "__main__":
    print("RAG System Usage Examples\n" + "=" * 50)

    # Run examples
    example_add_winners()
    example_search()
    example_features()
    example_deduplication()

    print("\n" + "=" * 50)
    print("RAG system is ready! Index persists at /tmp/winners.index.*")
