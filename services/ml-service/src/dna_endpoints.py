"""
Creative DNA API Endpoints - Agent 48
Provides DNA extraction, formula building, and creative optimization APIs
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from src.creative_dna import get_creative_dna, DNASuggestion
from src.data_loader import get_data_loader

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/dna", tags=["Creative DNA"])

# Global DNA analyzer instance
creative_dna_analyzer = None


# Request Models
class ExtractDNARequest(BaseModel):
    """Request model for DNA extraction"""
    creative_id: str


class BuildFormulaRequest(BaseModel):
    """Request model for building winning formula"""
    account_id: str
    min_roas: float = 3.0
    min_samples: int = 10
    lookback_days: int = 90


class ApplyDNARequest(BaseModel):
    """Request model for applying DNA to creative"""
    creative_id: str
    account_id: str


class ScoreCreativeRequest(BaseModel):
    """Request model for scoring creative"""
    creative_id: str
    account_id: str


# Endpoints

@router.post("/extract")
async def extract_creative_dna(request: ExtractDNARequest):
    """
    Extract DNA from a creative (Agent 48)

    Analyzes a creative and extracts all DNA components:
    - Hook DNA
    - Visual DNA
    - Audio DNA
    - Pacing DNA
    - Copy DNA
    - CTA DNA

    Args:
        request: Creative ID to extract DNA from

    Returns:
        Complete DNA profile
    """
    try:
        logger.info(f"🧬 Extracting DNA from creative {request.creative_id}")

        # Get database connection
        data_loader = get_data_loader()

        # Initialize DNA analyzer
        global creative_dna_analyzer
        if creative_dna_analyzer is None:
            creative_dna_analyzer = get_creative_dna(data_loader.pool if data_loader else None)

        # Extract DNA
        dna = await creative_dna_analyzer.extract_dna(request.creative_id)

        if not dna:
            raise HTTPException(status_code=404, detail="Creative not found or DNA extraction failed")

        logger.info(f"✅ DNA extracted successfully for creative {request.creative_id}")

        return {
            "success": True,
            "creative_id": request.creative_id,
            "dna": dna,
            "extracted_at": dna.get("extracted_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting creative DNA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/formula/build")
async def build_winning_formula(request: BuildFormulaRequest):
    """
    Build winning formula from top-performing creatives (Agent 48)

    Analyzes all winning creatives to extract common patterns and build
    a "winning formula" that can be applied to future creatives.

    This is the core of 10X LEVERAGE - each winner makes future creatives better.

    Args:
        request: Formula parameters

    Returns:
        Winning formula with all patterns
    """
    try:
        logger.info(f"🧬 Building winning formula for account {request.account_id}")

        # Get database connection
        data_loader = get_data_loader()

        # Initialize DNA analyzer
        global creative_dna_analyzer
        if creative_dna_analyzer is None:
            creative_dna_analyzer = get_creative_dna(data_loader.pool if data_loader else None)

        # Build formula
        formula = await creative_dna_analyzer.build_winning_formula(
            account_id=request.account_id,
            min_roas=request.min_roas,
            min_samples=request.min_samples,
            lookback_days=request.lookback_days
        )

        if "error" in formula:
            if formula["error"] == "insufficient_data":
                return {
                    "success": False,
                    "error": formula["error"],
                    "message": formula["message"],
                    "winners_count": formula.get("winners_count", 0),
                    "min_samples_needed": request.min_samples
                }
            else:
                raise HTTPException(status_code=500, detail=formula.get("message", "Failed to build formula"))

        logger.info(f"✅ Winning formula built with {formula['sample_size']} winners")

        return {
            "success": True,
            "formula": formula,
            "summary": {
                "account_id": formula["account_id"],
                "sample_size": formula["sample_size"],
                "formula_score": formula.get("formula_score", 0),
                "avg_roas": formula["performance_benchmarks"]["avg_roas"],
                "best_hook_types": [h["item"] for h in formula["best_hooks"][:3]],
                "optimal_duration": formula["optimal_duration"],
                "created_at": formula["created_at"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building winning formula: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formula/{account_id}")
async def get_winning_formula(account_id: str):
    """
    Get winning formula for an account (Agent 48)

    Returns the cached winning formula or builds a new one if not available.

    Args:
        account_id: Account ID

    Returns:
        Winning formula
    """
    try:
        logger.info(f"📊 Getting winning formula for account {account_id}")

        # Get database connection
        data_loader = get_data_loader()

        # Initialize DNA analyzer
        global creative_dna_analyzer
        if creative_dna_analyzer is None:
            creative_dna_analyzer = get_creative_dna(data_loader.pool if data_loader else None)

        # Get formula
        formula = await creative_dna_analyzer.get_winning_formula(account_id)

        if "error" in formula:
            return {
                "success": False,
                "error": formula["error"],
                "message": "No winning formula available. Build one first."
            }

        return {
            "success": True,
            "formula": formula,
            "cached": True
        }

    except Exception as e:
        logger.error(f"Error getting winning formula: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/apply")
async def apply_dna_to_creative(request: ApplyDNARequest):
    """
    Apply winning DNA to a new creative (Agent 48)

    Analyzes a creative and suggests improvements based on the winning formula.
    This is DNA INHERITANCE - new creatives inherit winning traits.

    Args:
        request: Creative and account IDs

    Returns:
        List of DNA-based suggestions
    """
    try:
        logger.info(f"🧬 Applying DNA to creative {request.creative_id}")

        # Get database connection
        data_loader = get_data_loader()

        # Initialize DNA analyzer
        global creative_dna_analyzer
        if creative_dna_analyzer is None:
            creative_dna_analyzer = get_creative_dna(data_loader.pool if data_loader else None)

        # Apply DNA
        suggestions = await creative_dna_analyzer.apply_dna_to_new_creative(
            creative_id=request.creative_id,
            account_id=request.account_id
        )

        logger.info(f"✅ Generated {len(suggestions)} DNA suggestions")

        return {
            "success": True,
            "creative_id": request.creative_id,
            "suggestions_count": len(suggestions),
            "suggestions": [
                {
                    "category": s.category,
                    "type": s.suggestion_type,
                    "current": s.current_value,
                    "recommended": s.recommended_value,
                    "impact": s.expected_impact,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning
                }
                for s in suggestions
            ]
        }

    except Exception as e:
        logger.error(f"Error applying DNA: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score")
async def score_creative(request: ScoreCreativeRequest):
    """
    Score a creative against the winning formula (Agent 48)

    Returns an alignment score showing how well the creative matches
    the winning pattern.

    Args:
        request: Creative and account IDs

    Returns:
        Score and breakdown
    """
    try:
        logger.info(f"📊 Scoring creative {request.creative_id}")

        # Get database connection
        data_loader = get_data_loader()

        # Initialize DNA analyzer
        global creative_dna_analyzer
        if creative_dna_analyzer is None:
            creative_dna_analyzer = get_creative_dna(data_loader.pool if data_loader else None)

        # Score creative
        score_data = await creative_dna_analyzer.score_creative_against_formula(
            creative_id=request.creative_id,
            account_id=request.account_id
        )

        if "error" in score_data:
            raise HTTPException(status_code=400, detail=score_data["error"])

        logger.info(f"✅ Creative scored: {score_data['overall_score']:.2%} alignment")

        return {
            "success": True,
            "creative_id": request.creative_id,
            "score": score_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scoring creative: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/{account_id}")
async def get_dna_dashboard(account_id: str):
    """
    Get DNA dashboard for an account (Agent 48)

    Shows:
    - Winning formula summary
    - Top performing patterns
    - DNA effectiveness metrics
    - Recent DNA applications

    Args:
        account_id: Account ID

    Returns:
        Complete DNA dashboard data
    """
    try:
        logger.info(f"📊 Getting DNA dashboard for account {account_id}")

        # Get database connection
        data_loader = get_data_loader()

        # Initialize DNA analyzer
        global creative_dna_analyzer
        if creative_dna_analyzer is None:
            creative_dna_analyzer = get_creative_dna(data_loader.pool if data_loader else None)

        # Get winning formula
        formula = await creative_dna_analyzer.get_winning_formula(account_id)

        if "error" in formula:
            return {
                "success": False,
                "error": "no_formula",
                "message": "No winning formula available yet. Build one first."
            }

        # Get top performers
        top_performers = await creative_dna_analyzer.get_top_performers(
            account_id=account_id,
            min_roas=3.0,
            limit=10
        )

        # Build dashboard
        dashboard = {
            "account_id": account_id,
            "formula_summary": {
                "sample_size": formula["sample_size"],
                "avg_roas": formula["performance_benchmarks"]["avg_roas"],
                "avg_ctr": formula["performance_benchmarks"]["avg_ctr"],
                "created_at": formula["created_at"],
                "updated_at": formula["updated_at"]
            },
            "winning_patterns": {
                "best_hooks": [h["item"] for h in formula["best_hooks"][:5]],
                "best_visuals": [v["item"] for v in formula.get("best_visual_patterns", [])[:5]],
                "best_ctas": [c["item"] for c in formula["best_ctas"][:5]],
                "optimal_duration": formula["optimal_duration"]
            },
            "hook_dna": formula["hook_patterns"],
            "visual_dna": formula["visual_patterns"],
            "pacing_dna": formula["pacing_patterns"],
            "cta_dna": formula["cta_patterns"],
            "top_performers": top_performers,
            "dna_effectiveness": {
                "formula_age_hours": (datetime.utcnow() - datetime.fromisoformat(formula["created_at"].replace("Z", "+00:00"))).total_seconds() / 3600,
                "winners_analyzed": formula["sample_size"],
                "expected_roas": formula["performance_benchmarks"]["avg_roas"]
            }
        }

        return {
            "success": True,
            "dashboard": dashboard
        }

    except Exception as e:
        logger.error(f"Error getting DNA dashboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-performers/{account_id}")
async def get_top_performers(account_id: str, min_roas: float = 3.0, limit: int = 20):
    """
    Get top performing creatives for DNA extraction (Agent 48)

    Args:
        account_id: Account ID
        min_roas: Minimum ROAS threshold
        limit: Maximum number to return

    Returns:
        List of top performers
    """
    try:
        logger.info(f"🏆 Getting top performers for account {account_id}")

        # Get database connection
        data_loader = get_data_loader()

        # Initialize DNA analyzer
        global creative_dna_analyzer
        if creative_dna_analyzer is None:
            creative_dna_analyzer = get_creative_dna(data_loader.pool if data_loader else None)

        # Get top performers
        performers = await creative_dna_analyzer.get_top_performers(
            account_id=account_id,
            min_roas=min_roas,
            limit=limit
        )

        return {
            "success": True,
            "account_id": account_id,
            "count": len(performers),
            "min_roas": min_roas,
            "performers": performers
        }

    except Exception as e:
        logger.error(f"Error getting top performers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
