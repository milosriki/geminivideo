"""
Helper functions for embeddings and text processing
"""
import re
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer


def clean_text(text: str) -> str:
    """Clean and normalize text for embedding"""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)

    return text.strip()


def prepare_ad_text(ad_data: dict) -> str:
    """Prepare ad data for embedding by combining relevant fields"""
    parts = []

    # Priority order: hook, body, cta
    if ad_data.get('hook'):
        parts.append(clean_text(ad_data['hook']))

    if ad_data.get('body'):
        parts.append(clean_text(ad_data['body']))

    if ad_data.get('cta'):
        parts.append(clean_text(ad_data['cta']))

    # Optional: include metadata if available
    if ad_data.get('theme'):
        parts.append(f"Theme: {ad_data['theme']}")

    if ad_data.get('audience'):
        parts.append(f"Audience: {ad_data['audience']}")

    return " | ".join(parts)


def batch_embed(texts: List[str], model: SentenceTransformer,
                batch_size: int = 32, normalize: bool = True) -> np.ndarray:
    """Embed a batch of texts efficiently"""
    if not texts:
        return np.array([])

    embeddings = model.encode(
        texts,
        batch_size=batch_size,
        normalize_embeddings=normalize,
        show_progress_bar=len(texts) > 100
    )

    return embeddings


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    if len(a.shape) == 1:
        a = a.reshape(1, -1)
    if len(b.shape) == 1:
        b = b.reshape(1, -1)

    return float(np.dot(a, b.T)[0, 0])


def expand_query(query: str, synonyms: Dict[str, List[str]] = None) -> List[str]:
    """Expand query with synonyms for better retrieval"""
    expanded = [query]

    if not synonyms:
        # Default marketing-related synonyms
        synonyms = {
            'sale': ['discount', 'deal', 'offer', 'promotion'],
            'new': ['latest', 'fresh', 'recent', 'modern'],
            'best': ['top', 'premium', 'excellent', 'superior'],
            'free': ['complimentary', 'no cost', 'gratis'],
            'buy': ['purchase', 'get', 'order', 'shop'],
        }

    query_lower = query.lower()
    for word, alternatives in synonyms.items():
        if word in query_lower:
            for alt in alternatives:
                expanded.append(query_lower.replace(word, alt))

    return list(set(expanded))  # Remove duplicates


def extract_ad_features(ad_data: dict) -> Dict[str, Any]:
    """Extract structured features from ad data for filtering"""
    features = {}

    # Length features
    if ad_data.get('hook'):
        features['hook_length'] = len(ad_data['hook'].split())

    if ad_data.get('body'):
        features['body_length'] = len(ad_data['body'].split())

    # Sentiment/tone indicators
    text = prepare_ad_text(ad_data).lower()

    features['has_urgency'] = any(word in text for word in
                                   ['now', 'today', 'limited', 'hurry', 'last chance'])

    features['has_discount'] = any(word in text for word in
                                    ['sale', 'discount', '%', 'off', 'save'])

    features['has_cta_action'] = any(word in text for word in
                                      ['click', 'buy', 'shop', 'get', 'order', 'try'])

    # Question detection
    features['has_question'] = '?' in text

    return features


def score_ad_quality(ad_data: dict, ctr: float) -> float:
    """Calculate composite quality score for an ad"""
    features = extract_ad_features(ad_data)

    # Base score from CTR
    score = ctr * 100

    # Bonus for good structure
    if features.get('hook_length', 0) > 0:
        score += 5

    if features.get('body_length', 0) >= 10:
        score += 5

    # Bonus for engagement elements
    if features.get('has_urgency'):
        score += 3

    if features.get('has_cta_action'):
        score += 3

    if features.get('has_question'):
        score += 2

    return min(score, 100)  # Cap at 100


def deduplicate_results(results: List[Dict[str, Any]],
                        similarity_threshold: float = 0.95) -> List[Dict[str, Any]]:
    """Remove near-duplicate results from search results"""
    if not results:
        return []

    filtered = [results[0]]  # Keep first result

    for result in results[1:]:
        is_duplicate = False

        for kept in filtered:
            # Check if too similar to already kept result
            if result.get('similarity', 0) >= similarity_threshold:
                # Compare actual content
                text1 = prepare_ad_text(result.get('data', {}))
                text2 = prepare_ad_text(kept.get('data', {}))

                if text1 == text2:
                    is_duplicate = True
                    break

        if not is_duplicate:
            filtered.append(result)

    return filtered
