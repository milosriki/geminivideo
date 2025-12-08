"""
Stress Test: Framework & Concept Maximization
Finds where we're not using frameworks/concepts to their full potential
"""
import asyncio
import json
from typing import Dict, Any, List
import httpx
import logging

logger = logging.getLogger(__name__)


class FrameworkMaximizationAnalyzer:
    """Analyze if we're maximizing framework capabilities"""
    
    def __init__(self):
        self.base_url = "http://localhost:8003"
        self.titan_url = "http://localhost:8084"
    
    async def analyze_blending_engine_usage(self) -> Dict[str, Any]:
        """Check if using all BlendingEngine capabilities"""
        issues = []
        recommendations = []
        
        # Check if only using SIGMOID
        async with httpx.AsyncClient() as client:
            # Test different curves
            curves = ["linear", "exponential", "sigmoid", "step", "adaptive"]
            curve_usage = {}
            
            for curve in curves:
                try:
                    # Would need endpoint that accepts curve parameter
                    # For now, check if it's configurable
                    response = await client.get(
                        f"{self.base_url}/api/ml/battle-hardened/config",
                        timeout=5.0
                    )
                    # Check response for curve options
                    curve_usage[curve] = curve in response.text if response.status_code == 200 else False
                except:
                    curve_usage[curve] = False
            
            if sum(curve_usage.values()) < len(curves):
                issues.append({
                    "framework": "BlendingEngine",
                    "issue": f"Only using {sum(curve_usage.values())}/{len(curves)} curve types",
                    "missing": [c for c, used in curve_usage.items() if not used],
                    "impact": "Missing optimization opportunities - different curves work better for different sales cycles",
                    "recommendation": "Test all 5 curves per account, select best based on sales cycle length"
                })
        
        return {
            "framework": "BlendingEngine",
            "issues": issues,
            "maximization_score": sum(curve_usage.values()) / len(curves) if curve_usage else 0
        }
    
    async def analyze_thompson_sampling_usage(self) -> Dict[str, Any]:
        """Check if maximizing Thompson Sampling capabilities"""
        issues = []
        
        # Thompson Sampling should use:
        # 1. Variance-based exploration (uncertainty)
        # 2. Prior updates from feedback
        # 3. Multi-armed bandit optimization
        
        async with httpx.AsyncClient() as client:
            # Check if using variance
            try:
                response = await client.post(
                    f"{self.base_url}/api/ml/battle-hardened/select",
                    json={
                        "ad_states": [{
                            "ad_id": "test",
                            "impressions": 100,
                            "clicks": 5,
                            "spend": 100,
                            "pipeline_value": 300,
                            "age_hours": 24
                        }],
                        "total_budget": 1000
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    recs = data.get("recommendations", [])
                    
                    # Check if confidence reflects uncertainty
                    if recs:
                        confidence = recs[0].get("confidence", 0)
                        # Low impressions should = low confidence (uncertainty)
                        if confidence > 0.8:  # Too confident for new ad
                            issues.append({
                                "framework": "Thompson Sampling",
                                "issue": "Not using variance-based uncertainty quantification",
                                "impact": "Not exploring uncertain ads enough",
                                "recommendation": "Use Beta variance to prioritize exploration of uncertain ads"
                            })
            except:
                pass
        
        return {
            "framework": "Thompson Sampling",
            "issues": issues,
            "maximization_score": 0.5 if issues else 1.0
        }
    
    async def analyze_rag_usage(self) -> Dict[str, Any]:
        """Check if maximizing RAG capabilities"""
        issues = []
        
        # RAG should use:
        # 1. Hybrid search (vector + metadata)
        # 2. Multiple embedding models
        # 3. Semantic caching
        # 4. Re-ranking
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/ml/rag/search-winners",
                    json={
                        "query_embedding": [0.1] * 768,  # Dummy embedding
                        "top_k": 5,
                        "hook_type": "testimonial",
                        "min_roas": 2.0
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    matches = data.get("matches", [])
                    
                    # Check if using hybrid search
                    if not matches:
                        issues.append({
                            "framework": "RAG Winner Index",
                            "issue": "Not using hybrid search (vector + metadata filtering)",
                            "impact": "Missing relevant winners that match metadata but not vector similarity",
                            "recommendation": "Combine FAISS similarity search with metadata filters simultaneously"
                        })
                    
                    # Check if using re-ranking
                    if "rerank" not in str(data).lower() and "score" not in str(data).lower():
                        issues.append({
                            "framework": "RAG Winner Index",
                            "issue": "Not using re-ranking for better results",
                            "impact": "Suboptimal result ordering",
                            "recommendation": "Re-rank results by: similarity * ROAS * recency"
                        })
            except:
                pass
        
        return {
            "framework": "RAG Winner Index",
            "issues": issues,
            "maximization_score": 0.6 if issues else 1.0
        }
    
    async def analyze_fatigue_detector_usage(self) -> Dict[str, Any]:
        """Check if using all FatigueDetector rules"""
        issues = []
        
        # Should use all 4 rules:
        # 1. Frequency thresholds
        # 2. CTR decline
        # 3. CPM increase
        # 4. Impression decay
        
        async with httpx.AsyncClient() as client:
            try:
                # Check fatigue detection endpoint
                response = await client.post(
                    f"{self.base_url}/api/ml/fatigue/analyze",
                    json={
                        "ad_id": "test",
                        "impressions": 50000,
                        "frequency": 8.0,
                        "ctr": 0.02,
                        "historical_ctr": 0.04,
                        "cpm": 15.0,
                        "historical_cpm": 10.0
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    triggers = data.get("triggers", [])
                    
                    # Should trigger on multiple signals
                    if len(triggers) < 2:
                        issues.append({
                            "framework": "FatigueDetector",
                            "issue": "Not combining all 4 detection rules",
                            "impact": "Missing fatigue signals - ads continue past optimal point",
                            "recommendation": "Use all rules: frequency + CTR decline + CPM increase + impression decay"
                        })
            except:
                pass
        
        return {
            "framework": "FatigueDetector",
            "issues": issues,
            "maximization_score": 0.7 if issues else 1.0
        }
    
    async def analyze_synthetic_revenue_usage(self) -> Dict[str, Any]:
        """Check if maximizing Synthetic Revenue capabilities"""
        issues = []
        
        # Should use:
        # 1. Time decay
        # 2. Incremental value calculation
        # 3. Confidence scoring
        # 4. Multi-tenant configurations
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/ml/synthetic-revenue/calculate",
                    json={
                        "tenant_id": "test",
                        "stage_from": "new_lead",
                        "stage_to": "assessment_booked",
                        "deal_value": 10000,
                        "days_in_pipeline": 30
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for time decay
                    if "decay" not in str(data).lower() and "days_in_pipeline" in str(data):
                        issues.append({
                            "framework": "Synthetic Revenue",
                            "issue": "Not applying time decay for stale deals",
                            "impact": "Overvaluing old pipeline stages",
                            "recommendation": "Apply exponential decay: value * 0.5^(days/half_life)"
                        })
                    
                    # Check for incremental value
                    if "incremental" not in str(data).lower():
                        issues.append({
                            "framework": "Synthetic Revenue",
                            "issue": "Not calculating incremental value between stages",
                            "impact": "Double-counting revenue on stage transitions",
                            "recommendation": "Calculate: stage_to_value - stage_from_value"
                        })
            except:
                pass
        
        return {
            "framework": "Synthetic Revenue",
            "issues": issues,
            "maximization_score": 0.6 if issues else 1.0
        }
    
    async def analyze_safe_executor_usage(self) -> Dict[str, Any]:
        """Check if using all SafeExecutor safety features"""
        issues = []
        
        # Should use:
        # 1. Rate limiting
        # 2. Budget velocity limits
        # 3. Fuzzy budgets
        # 4. Random jitter
        # 5. Change history tracking
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/ml/safe-executor/plan",
                    json={
                        "ad_id": "test",
                        "action": "update_budget",
                        "current_budget": 100,
                        "target_budget": 150
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for fuzzing
                    fuzzed = data.get("fuzzed_budget")
                    if not fuzzed or fuzzed == 150:
                        issues.append({
                            "framework": "SafeExecutor",
                            "issue": "Not fuzzing budgets (avoiding round numbers)",
                            "impact": "Higher ban risk - Meta detects automated patterns",
                            "recommendation": "Add ±3% randomization to budgets"
                        })
                    
                    # Check for jitter
                    if "jitter" not in str(data).lower():
                        issues.append({
                            "framework": "SafeExecutor",
                            "issue": "Not using random jitter delays",
                            "impact": "Too predictable timing - looks automated",
                            "recommendation": "Add 3-18 second random delays between actions"
                        })
            except:
                pass
        
        return {
            "framework": "SafeExecutor",
            "issues": issues,
            "maximization_score": 0.5 if issues else 1.0
        }
    
    async def analyze_vertex_ai_usage(self) -> Dict[str, Any]:
        """Check if using all Vertex AI capabilities"""
        issues = []
        
        # Should use:
        # 1. Gemini 2.0 for video analysis
        # 2. Imagen for image generation
        # 3. Text embeddings for RAG
        # 4. Multimodal understanding
        
        async with httpx.AsyncClient() as client:
            capabilities_used = []
            
            # Check video analysis
            try:
                response = await client.post(
                    f"{self.titan_url}/api/titan/analyze-video",
                    json={"video_id": "test"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    capabilities_used.append("video_analysis")
            except:
                pass
            
            # Check image generation
            try:
                response = await client.post(
                    f"{self.titan_url}/api/titan/generate-image",
                    json={"prompt": "test"},
                    timeout=30.0
                )
                if response.status_code == 200:
                    capabilities_used.append("image_generation")
            except:
                pass
            
            # Check embeddings
            try:
                response = await client.post(
                    f"{self.titan_url}/api/titan/generate-embedding",
                    json={"text": "test"},
                    timeout=10.0
                )
                if response.status_code == 200:
                    capabilities_used.append("embeddings")
            except:
                pass
            
            expected = ["video_analysis", "image_generation", "embeddings"]
            missing = [c for c in expected if c not in capabilities_used]
            
            if missing:
                issues.append({
                    "framework": "Vertex AI",
                    "issue": f"Not using all capabilities: missing {missing}",
                    "impact": "Underutilizing AI - missing video analysis, image gen, or embeddings",
                    "recommendation": "Wire all Vertex AI endpoints: Gemini 2.0, Imagen, embeddings"
                })
        
        return {
            "framework": "Vertex AI",
            "issues": issues,
            "capabilities_used": len(capabilities_used),
            "capabilities_available": 3,
            "maximization_score": len(capabilities_used) / 3
        }
    
    async def analyze_life_force_8_usage(self) -> Dict[str, Any]:
        """Check if systematically using all Life-Force 8 triggers"""
        issues = []
        
        # Should test all 8 triggers:
        triggers = [
            "survival_life_extension",
            "food_beverage_enjoyment",
            "freedom_from_fear_pain",
            "sexual_companionship",
            "comfortable_living",
            "status_superiority",
            "protection_loved_ones",
            "social_approval"
        ]
        
        # Check if system uses these in creative generation
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.titan_url}/api/titan/director/create-battle-plan",
                    json={
                        "video_id": "test",
                        "framework": "training_video_framework_2025"
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    triggers_used = data.get("life_force_8_triggers", [])
                    
                    if len(triggers_used) < len(triggers):
                        issues.append({
                            "framework": "Life-Force 8",
                            "issue": f"Only using {len(triggers_used)}/{len(triggers)} triggers",
                            "impact": "Missing high-performing trigger combinations",
                            "recommendation": "Test all 8 triggers systematically in A/B tests"
                        })
            except:
                pass
        
        return {
            "framework": "Life-Force 8",
            "issues": issues,
            "maximization_score": 0.5 if issues else 1.0
        }
    
    async def analyze_all_frameworks(self) -> Dict[str, Any]:
        """Analyze all frameworks for maximization"""
        
        analyses = await asyncio.gather(
            self.analyze_blending_engine_usage(),
            self.analyze_thompson_sampling_usage(),
            self.analyze_rag_usage(),
            self.analyze_fatigue_detector_usage(),
            self.analyze_synthetic_revenue_usage(),
            self.analyze_safe_executor_usage(),
            self.analyze_vertex_ai_usage(),
            self.analyze_life_force_8_usage(),
            return_exceptions=True
        )
        
        all_issues = []
        framework_scores = {}
        
        for analysis in analyses:
            if isinstance(analysis, dict):
                framework = analysis.get("framework", "Unknown")
                issues = analysis.get("issues", [])
                score = analysis.get("maximization_score", 0)
                
                all_issues.extend(issues)
                framework_scores[framework] = score
        
        avg_score = sum(framework_scores.values()) / len(framework_scores) if framework_scores else 0
        
        return {
            "frameworks_analyzed": len(framework_scores),
            "total_issues": len(all_issues),
            "framework_scores": framework_scores,
            "average_maximization_score": avg_score,
            "all_issues": all_issues,
            "high_priority": [i for i in all_issues if "high" in i.get("impact", "").lower()],
            "medium_priority": [i for i in all_issues if "medium" in i.get("impact", "").lower()],
            "low_priority": [i for i in all_issues if "low" in i.get("impact", "").lower()]
        }


async def main():
    """Run framework maximization analysis"""
    print("=" * 80)
    print("FRAMEWORK MAXIMIZATION ANALYSIS")
    print("Finding where we're not using frameworks to full potential")
    print("=" * 80)
    
    analyzer = FrameworkMaximizationAnalyzer()
    
    results = await analyzer.analyze_all_frameworks()
    
    print(f"\nFrameworks Analyzed: {results['frameworks_analyzed']}")
    print(f"Total Issues Found: {results['total_issues']}")
    print(f"Average Maximization Score: {results['average_maximization_score']*100:.1f}%")
    
    print(f"\nFramework Scores:")
    for framework, score in results['framework_scores'].items():
        print(f"  {framework}: {score*100:.1f}%")
    
    print(f"\nHigh Priority Issues: {len(results['high_priority'])}")
    print(f"Medium Priority Issues: {len(results['medium_priority'])}")
    print(f"Low Priority Issues: {len(results['low_priority'])}")
    
    print("\n" + "=" * 80)
    print("DETAILED ISSUES")
    print("=" * 80)
    
    for issue in results['all_issues']:
        print(f"\n{issue['framework']}:")
        print(f"  Issue: {issue['issue']}")
        print(f"  Impact: {issue['impact']}")
        print(f"  Recommendation: {issue['recommendation']}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

