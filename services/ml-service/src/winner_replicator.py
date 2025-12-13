"""
Winner Replication Service
Automatically replicates winning ad patterns with creative variations.

Features:
- Replicate top N winners automatically
- Clone winners with hook/visual/audio variations
- Track source winner for performance comparison
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import numpy as np
import asyncio
import uuid

try:
    from src.winner_index import get_winner_index, WinnerMatch
    WINNER_INDEX_AVAILABLE = True
except ImportError:
    WINNER_INDEX_AVAILABLE = False

try:
    from src.creative_dna import CreativeDNA
    CREATIVE_DNA_AVAILABLE = True
except ImportError:
    CREATIVE_DNA_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ReplicatedAd:
    """A replicated ad variation."""
    replica_id: str
    source_winner_id: str
    source_ctr: float
    source_roas: float
    variation_type: str  # 'hook', 'visual', 'audience', 'copy', 'cta'
    variation_description: str
    creative_dna: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str


class WinnerReplicator:
    """
    Replicate winning ad patterns automatically.

    Uses the Winner Index (FAISS) to find top performers and
    generates variations using Creative DNA patterns.
    """

    def __init__(self):
        self.winner_index = get_winner_index() if WINNER_INDEX_AVAILABLE else None
        self._creative_dna_extractor = None

    @property
    def creative_dna(self):
        """Lazy load Creative DNA extractor."""
        if self._creative_dna_extractor is None and CREATIVE_DNA_AVAILABLE:
            self._creative_dna_extractor = CreativeDNA()
        return self._creative_dna_extractor

    async def replicate_top_winners(
        self,
        limit: int = 5,
        min_ctr: float = 0.03,
        min_roas: float = 3.0,
        variations_per_winner: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Replicate top N winners.

        Args:
            limit: Number of top winners to replicate
            min_ctr: Minimum CTR threshold (default 3%)
            min_roas: Minimum ROAS threshold (default 3x)
            variations_per_winner: Number of variations per winner

        Returns:
            List of replicated ad variations
        """
        try:
            if not self.winner_index:
                logger.warning("Winner index not available, using fallback")
                return await self._get_fallback_winners(limit, min_ctr, min_roas, variations_per_winner)

            # Get all winners from index
            all_winners = self._get_top_winners(limit, min_ctr, min_roas)

            if not all_winners:
                logger.info(f"No winners found matching criteria: min_ctr={min_ctr}, min_roas={min_roas}")
                return []

            replicated = []
            for winner in all_winners:
                # Clone winner with variations
                cloned = await self._clone_with_variations(winner, variations=variations_per_winner)
                replicated.extend(cloned)

            logger.info(f"Replicated {len(replicated)} variations from {len(all_winners)} winners")
            return replicated

        except Exception as e:
            logger.error(f"Error replicating winners: {e}")
            raise

    def _get_top_winners(
        self,
        limit: int,
        min_ctr: float,
        min_roas: float
    ) -> List[Dict[str, Any]]:
        """Get top winners from index filtered by criteria."""
        if not self.winner_index or not hasattr(self.winner_index, 'metadata'):
            return []

        # Filter winners by criteria
        winners = []
        for idx, meta in self.winner_index.metadata.items():
            ctr = meta.get('actual_ctr', meta.get('ctr', 0))
            roas = meta.get('actual_roas', meta.get('roas', 0))

            if ctr >= min_ctr and roas >= min_roas:
                winners.append({
                    'index': idx,
                    'ad_id': meta.get('ad_id', f'winner_{idx}'),
                    'ctr': ctr,
                    'roas': roas,
                    'metadata': meta
                })

        # Sort by ROAS descending, then CTR
        winners.sort(key=lambda x: (x['roas'], x['ctr']), reverse=True)

        return winners[:limit]

    async def _get_fallback_winners(
        self,
        limit: int,
        min_ctr: float,
        min_roas: float,
        variations_per_winner: int
    ) -> List[Dict[str, Any]]:
        """Fallback when winner index is not available."""
        logger.warning("Using fallback winner data")

        # Return empty list - in production, this would query the database
        return []

    async def _clone_with_variations(
        self,
        winner: Dict[str, Any],
        variations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Clone winner with creative variations.

        Args:
            winner: Winner ad data
            variations: Number of variations to create

        Returns:
            List of cloned ad variations
        """
        try:
            ad_id = winner.get('ad_id', 'unknown')
            metadata = winner.get('metadata', {})

            # Define variation types
            variation_types = [
                ('hook', 'Modified opening hook with urgency'),
                ('audience', 'Expanded lookalike audience'),
                ('copy', 'Refined ad copy with social proof'),
                ('visual', 'Enhanced visual style'),
                ('cta', 'Alternative call-to-action'),
            ]

            variations_list = []
            for i in range(min(variations, len(variation_types))):
                variation_type, description = variation_types[i]

                # Generate creative DNA for this variation
                creative_dna = self._generate_variation_dna(
                    winner,
                    variation_type
                )

                replica = ReplicatedAd(
                    replica_id=str(uuid.uuid4()),
                    source_winner_id=ad_id,
                    source_ctr=winner.get('ctr', 0),
                    source_roas=winner.get('roas', 0),
                    variation_type=variation_type,
                    variation_description=description,
                    creative_dna=creative_dna,
                    metadata={
                        **metadata,
                        'is_replica': True,
                        'variation_index': i + 1
                    },
                    created_at=datetime.utcnow().isoformat()
                )

                variations_list.append(asdict(replica))

            logger.info(f"Created {len(variations_list)} variations for winner {ad_id}")
            return variations_list

        except Exception as e:
            logger.error(f"Error cloning winner {winner.get('ad_id', 'unknown')}: {e}")
            return []

    def _generate_variation_dna(
        self,
        winner: Dict[str, Any],
        variation_type: str
    ) -> Dict[str, Any]:
        """Generate Creative DNA for a specific variation type."""
        base_dna = winner.get('metadata', {}).get('creative_dna', {})

        # Clone base DNA
        variation_dna = dict(base_dna) if base_dna else {}

        # Apply variation-specific modifications
        if variation_type == 'hook':
            variation_dna['hook_modified'] = True
            variation_dna['hook_type'] = 'urgency_scarcity'
            variation_dna['hook_strength'] = min(1.0, variation_dna.get('hook_strength', 0.7) * 1.2)

        elif variation_type == 'audience':
            variation_dna['audience_expanded'] = True
            variation_dna['targeting'] = {
                'type': 'lookalike',
                'seed_audience': 'top_converters',
                'expansion_level': 2
            }

        elif variation_type == 'copy':
            variation_dna['copy_modified'] = True
            variation_dna['social_proof_added'] = True
            variation_dna['cta_urgency_increased'] = True

        elif variation_type == 'visual':
            variation_dna['visual_enhanced'] = True
            variation_dna['color_saturation'] = 1.1
            variation_dna['contrast_boost'] = 1.05

        elif variation_type == 'cta':
            variation_dna['cta_modified'] = True
            variation_dna['cta_type'] = 'shop_now' if variation_dna.get('cta_type') != 'shop_now' else 'learn_more'

        variation_dna['variation_type'] = variation_type
        variation_dna['source_roas'] = winner.get('roas', 0)

        return variation_dna

    async def replicate_similar_to_winner(
        self,
        winner_id: str,
        variations: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Replicate variations similar to a specific winner.

        Args:
            winner_id: ID of the winner ad
            variations: Number of variations to create

        Returns:
            List of replicated ad variations
        """
        try:
            if not self.winner_index:
                logger.warning("Winner index not available")
                return []

            # Find the winner in metadata
            winner = None
            for idx, meta in self.winner_index.metadata.items():
                if meta.get('ad_id') == winner_id:
                    winner = {
                        'index': idx,
                        'ad_id': winner_id,
                        'ctr': meta.get('actual_ctr', meta.get('ctr', 0)),
                        'roas': meta.get('actual_roas', meta.get('roas', 0)),
                        'metadata': meta
                    }
                    break

            if not winner:
                logger.warning(f"Winner {winner_id} not found in index")
                return []

            return await self._clone_with_variations(winner, variations=variations)

        except Exception as e:
            logger.error(f"Error replicating winner {winner_id}: {e}")
            return []

    async def get_replication_stats(self) -> Dict[str, Any]:
        """Get statistics about winner replication potential."""
        if not self.winner_index:
            return {'error': 'Winner index not available'}

        stats = self.winner_index.stats()

        # Count winners by performance tier
        tiers = {
            'excellent': 0,  # ROAS >= 5
            'good': 0,       # ROAS >= 3
            'average': 0,    # ROAS >= 2
            'below_average': 0
        }

        for idx, meta in self.winner_index.metadata.items():
            roas = meta.get('actual_roas', meta.get('roas', 0))
            if roas >= 5:
                tiers['excellent'] += 1
            elif roas >= 3:
                tiers['good'] += 1
            elif roas >= 2:
                tiers['average'] += 1
            else:
                tiers['below_average'] += 1

        return {
            'total_winners': stats.get('total_winners', 0),
            'performance_tiers': tiers,
            'replication_potential': tiers['excellent'] + tiers['good'],
            'index_ready': stats.get('faiss_available', False)
        }


# Singleton instance
_replicator_instance = None

def get_winner_replicator() -> WinnerReplicator:
    """Get singleton WinnerReplicator instance."""
    global _replicator_instance
    if _replicator_instance is None:
        _replicator_instance = WinnerReplicator()
    return _replicator_instance
