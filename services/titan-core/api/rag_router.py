from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

# Import from the moved location
from services.titan_core.knowledge.rag.winner_index import winner_index
from services.titan_core.knowledge.rag.embeddings import (
    extract_ad_features,
    score_ad_quality,
    expand_query
)

router = APIRouter(
    prefix="/rag",
    tags=["RAG Knowledge Base"]
)

# Pydantic models
class AdData(BaseModel):
    hook: str
    body: str
    cta: str
    theme: Optional[str] = None
    audience: Optional[str] = None

class AddWinnerRequest(BaseModel):
    ad: AdData
    ctr: float

class SearchResult(BaseModel):
    data: Dict[str, Any]
    similarity: float
    ctr: float

class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    expanded_queries: Optional[List[str]] = None

class FeatureExtractionRequest(BaseModel):
    ad: AdData
    ctr: Optional[float] = None

class FeatureResponse(BaseModel):
    features: Dict[str, Any]
    quality_score: Optional[float] = None

@router.post("/winners", status_code=201)
async def add_winner(request: AddWinnerRequest):
    """Add a winning ad to the RAG index"""
    try:
        winner_index.add_winner(request.ad.dict(), ctr=request.ctr)
        return {"message": "Ad added to index", "ad": request.ad}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchResponse)
async def search_winners(
    query: str = Query(..., min_length=3),
    k: int = Query(5, ge=1, le=20),
    expand: bool = Query(False)
):
    """Search for similar winning ads"""
    try:
        results = winner_index.find_similar(query, k=k)
        
        expanded_queries = None
        if expand:
            expanded_queries = expand_query(query)
            
        return {
            "query": query,
            "results": results,
            "expanded_queries": expanded_queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/features", response_model=FeatureResponse)
async def extract_features(request: FeatureExtractionRequest):
    """Extract features and score quality of an ad"""
    try:
        ad_dict = request.ad.dict()
        features = extract_ad_features(ad_dict)
        
        quality_score = None
        if request.ctr is not None:
            quality_score = score_ad_quality(ad_dict, ctr=request.ctr)
            
        return {
            "features": features,
            "quality_score": quality_score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
