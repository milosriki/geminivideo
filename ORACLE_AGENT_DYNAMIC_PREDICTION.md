# 🔮 ORACLE AGENT DYNAMIC PREDICTION SYSTEM
## Can It Predict Creative Performance Before Launch?

**Question:** "I'm about to launch a new video creative (ID: 'xyz-123'). Analyze its creative DNA and predict its potential performance. Should I proceed with the launch, and what is your confidence level?"

**What It Checks:**
- Can analyze creative DNA for any video
- Can predict CTR/ROAS before spending budget
- Can provide go/no-go recommendation
- Can explain confidence level
- Can handle dynamic queries (not hardcoded)

---

## 🔍 CURRENT IMPLEMENTATION STATUS

### ✅ What Exists

**1. Oracle Agent (`oracle_agent.py`)**
```python
# File: services/titan-core/ai_council/oracle_agent.py

class OracleAgent:
    """Predicts ad performance before launch"""
    
    async def predict(
        self,
        creative_dna: Dict,
        account_context: Dict
    ) -> PredictionResult:
        """Predict CTR, ROAS, and conversion probability"""
        # Uses Gemini API for prediction
        # Returns predicted metrics
```

**2. Creative DNA Extraction**
```python
# File: services/ml-service/src/creative_dna.py

def extract_creative_dna(video_path: str, ad_data: Dict) -> Dict:
    """Extract creative DNA from video"""
    return {
        'hook_type': ...,
        'hook_strength': ...,
        'visual_pacing': ...,
        # ... other DNA components
    }
```

**3. Basic Prediction Endpoint (Partial)**
```python
# File: services/ml-service/src/main.py

@app.post("/api/ml/predict-creative")
async def predict_creative_performance(...):
    """Predict creative performance"""
    # Basic endpoint exists but needs enhancement
```

---

## ⚠️ WHAT'S MISSING: DYNAMIC QUERY HANDLING

**Current Limitation:**
- Endpoint requires structured input
- No natural language query parsing
- No creative ID lookup
- No detailed explanation of prediction
- No go/no-go recommendation logic

---

## 🔧 SOLUTION: ENHANCED ORACLE AGENT WITH DYNAMIC QUERIES

### Step 1: Natural Language Query Parser

```python
# File: services/titan-core/ai_council/query_parser.py

import re
from typing import Dict, Optional, Any, List
from datetime import datetime

class OracleQueryParser:
    """Parse natural language queries about creative predictions"""
    
    def __init__(self):
        self.creative_id_patterns = [
            r"creative\s+(?:id|ID)[:\s]+['\"]?([^'\"]+)['\"]?",
            r"video\s+creative\s+['\"]?([^'\"]+)['\"]?",
            r"ID[:\s]+['\"]?([^'\"]+)['\"]?",
            r"['\"]?([a-z0-9\-]+)['\"]?\s+creative"
        ]
        
        self.action_patterns = [
            r"should\s+i\s+(?:proceed|launch|publish)",
            r"can\s+i\s+(?:proceed|launch|publish)",
            r"is\s+it\s+(?:safe|good|worth)\s+to\s+(?:launch|proceed)",
            r"recommend(?:ation)?",
            r"go\s+or\s+no\s+go"
        ]
        
        self.confidence_patterns = [
            r"confidence\s+level",
            r"how\s+confident",
            r"certainty",
            r"probability"
        ]
    
    def parse(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse natural language query about creative prediction.
        
        Examples:
        - "I'm about to launch video creative 'xyz-123'. Should I proceed?"
        - "Analyze creative ID xyz-123 and predict performance"
        - "What's the confidence level for creative xyz-123?"
        """
        query_lower = query.lower()
        
        # Extract creative ID
        creative_id = self._extract_creative_id(query, query_lower)
        
        # Extract action request
        needs_recommendation = self._needs_recommendation(query_lower)
        
        # Extract confidence request
        needs_confidence = self._needs_confidence(query_lower)
        
        # Extract account context
        account_id = self._extract_account_id(query_lower, context)
        
        return {
            'creative_id': creative_id,
            'account_id': account_id,
            'needs_recommendation': needs_recommendation,
            'needs_confidence': needs_confidence,
            'needs_analysis': 'analyze' in query_lower or 'predict' in query_lower,
            'raw_query': query
        }
    
    def _extract_creative_id(self, original_query: str, query_lower: str) -> Optional[str]:
        """Extract creative ID from query"""
        for pattern in self.creative_id_patterns:
            match = re.search(pattern, original_query, re.IGNORECASE)
            if match:
                return match.group(1).strip("'\"")
        
        return None
    
    def _needs_recommendation(self, query_lower: str) -> bool:
        """Check if query asks for go/no-go recommendation"""
        return any(re.search(pattern, query_lower) for pattern in self.action_patterns)
    
    def _needs_confidence(self, query_lower: str) -> bool:
        """Check if query asks for confidence level"""
        return any(re.search(pattern, query_lower) for pattern in self.confidence_patterns)
    
    def _extract_account_id(self, query_lower: str, context: Optional[Dict]) -> Optional[str]:
        """Extract account ID from context or query"""
        if context and 'account_id' in context:
            return context['account_id']
        
        account_match = re.search(r'account[_\s]?id[:\s]+(\w+)', query_lower)
        if account_match:
            return account_match.group(1)
        
        return None
```

---

### Step 2: Enhanced Oracle Agent

```python
# File: services/titan-core/ai_council/oracle_agent.py

from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class PredictionResult:
    """Complete prediction result with recommendation"""
    creative_id: str
    predicted_ctr: float
    predicted_roas: float
    conversion_probability: float
    confidence_level: float
    recommendation: str  # "PROCEED", "REJECT", "MODIFY"
    reasoning: str
    risk_factors: List[str]
    strengths: List[str]
    suggested_modifications: List[str]
    account_baseline_comparison: Dict[str, Any]
    prediction_metadata: Dict[str, Any]

class EnhancedOracleAgent:
    """Enhanced Oracle Agent with dynamic query support"""
    
    def __init__(self, gemini_client, ml_service_client, db_pool):
        self.gemini_client = gemini_client
        self.ml_service_client = ml_service_client
        self.db_pool = db_pool
        self._account_baseline_cache = {}
    
    async def predict_from_query(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> PredictionResult:
        """
        Predict creative performance from natural language query.
        
        Args:
            query: Natural language query
            context: Additional context (account_id, etc.)
        
        Returns:
            PredictionResult with recommendation
        """
        from query_parser import OracleQueryParser
        
        parser = OracleQueryParser()
        parsed = parser.parse(query, context)
        
        # Validate
        if not parsed.get('creative_id'):
            raise ValueError("Creative ID not found in query")
        
        # Get creative data
        creative_data = await self._get_creative_data(parsed['creative_id'])
        
        # Extract creative DNA
        creative_dna = await self._extract_creative_dna(creative_data)
        
        # Get account context
        account_id = parsed.get('account_id') or context.get('account_id')
        account_baseline = await self._get_account_baseline(account_id)
        
        # Predict
        result = await self.predict(
            creative_dna=creative_dna,
            account_context={
                'account_id': account_id,
                'baseline_ctr': account_baseline.get('avg_ctr', 0.02),
                'baseline_roas': account_baseline.get('avg_roas', 2.0)
            }
        )
        
        # Add recommendation
        result.recommendation = self._generate_recommendation(
            result=result,
            account_baseline=account_baseline
        )
        
        # Add reasoning
        result.reasoning = self._generate_reasoning(
            result=result,
            account_baseline=account_baseline
        )
        
        return result
    
    async def predict(
        self,
        creative_dna: Dict,
        account_context: Dict
    ) -> PredictionResult:
        """
        Predict creative performance using Gemini AI.
        """
        # Build prediction prompt
        prompt = self._build_prediction_prompt(creative_dna, account_context)
        
        # Get prediction from Gemini
        response = await self.gemini_client.generate_content(prompt)
        prediction_data = self._parse_prediction_response(response.text)
        
        # Get ML model predictions (for comparison)
        ml_prediction = await self._get_ml_prediction(creative_dna)
        
        # Combine AI and ML predictions
        final_prediction = self._combine_predictions(
            ai_prediction=prediction_data,
            ml_prediction=ml_prediction,
            account_baseline=account_context
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            final_prediction,
            account_context,
            creative_dna
        )
        
        # Identify risk factors and strengths
        risk_factors = self._identify_risk_factors(creative_dna, final_prediction)
        strengths = self._identify_strengths(creative_dna, final_prediction)
        
        # Suggest modifications
        suggested_modifications = self._suggest_modifications(
            creative_dna,
            final_prediction,
            account_context
        )
        
        return PredictionResult(
            creative_id=creative_dna.get('creative_id', 'unknown'),
            predicted_ctr=final_prediction['ctr'],
            predicted_roas=final_prediction['roas'],
            conversion_probability=final_prediction['conversion_prob'],
            confidence_level=confidence,
            recommendation="",  # Set by caller
            reasoning="",  # Set by caller
            risk_factors=risk_factors,
            strengths=strengths,
            suggested_modifications=suggested_modifications,
            account_baseline_comparison={
                'baseline_ctr': account_context.get('baseline_ctr', 0.02),
                'baseline_roas': account_context.get('baseline_roas', 2.0),
                'ctr_vs_baseline': final_prediction['ctr'] / max(account_context.get('baseline_ctr', 0.02), 0.001),
                'roas_vs_baseline': final_prediction['roas'] / max(account_context.get('baseline_roas', 2.0), 0.001)
            },
            prediction_metadata={
                'prediction_method': 'hybrid_ai_ml',
                'ai_confidence': prediction_data.get('confidence', 0.7),
                'ml_confidence': ml_prediction.get('confidence', 0.8),
                'predicted_at': datetime.utcnow().isoformat()
            }
        )
    
    def _generate_recommendation(
        self,
        result: PredictionResult,
        account_baseline: Dict
    ) -> str:
        """Generate go/no-go recommendation"""
        baseline_ctr = account_baseline.get('avg_ctr', 0.02)
        baseline_roas = account_baseline.get('avg_roas', 2.0)
        
        # Decision logic
        ctr_ratio = result.predicted_ctr / max(baseline_ctr, 0.001)
        roas_ratio = result.predicted_roas / max(baseline_roas, 0.001)
        
        # High confidence + good performance = PROCEED
        if result.confidence_level >= 0.75:
            if ctr_ratio >= 0.90 and roas_ratio >= 0.90:
                return "PROCEED"
            elif ctr_ratio >= 0.70 or roas_ratio >= 0.70:
                return "MODIFY"  # Proceed with modifications
            else:
                return "REJECT"
        
        # Medium confidence
        elif result.confidence_level >= 0.60:
            if ctr_ratio >= 1.10 and roas_ratio >= 1.10:
                return "PROCEED"
            elif ctr_ratio >= 0.80 or roas_ratio >= 0.80:
                return "MODIFY"
            else:
                return "REJECT"
        
        # Low confidence = REJECT or MODIFY
        else:
            if ctr_ratio >= 1.20 and roas_ratio >= 1.20:
                return "MODIFY"  # High potential but low confidence
            else:
                return "REJECT"
    
    def _generate_reasoning(
        self,
        result: PredictionResult,
        account_baseline: Dict
    ) -> str:
        """Generate human-readable reasoning"""
        baseline_ctr = account_baseline.get('avg_ctr', 0.02)
        baseline_roas = account_baseline.get('avg_roas', 2.0)
        
        ctr_diff = result.predicted_ctr - baseline_ctr
        roas_diff = result.predicted_roas - baseline_roas
        
        reasoning_parts = []
        
        # CTR analysis
        if ctr_diff > 0:
            reasoning_parts.append(
                f"Predicted CTR ({result.predicted_ctr:.2%}) is {ctr_diff:.2%} above baseline ({baseline_ctr:.2%})"
            )
        else:
            reasoning_parts.append(
                f"Predicted CTR ({result.predicted_ctr:.2%}) is {abs(ctr_diff):.2%} below baseline ({baseline_ctr:.2%})"
            )
        
        # ROAS analysis
        if roas_diff > 0:
            reasoning_parts.append(
                f"Predicted ROAS ({result.predicted_roas:.2f}x) is {roas_diff:.2f}x above baseline ({baseline_roas:.2f}x)"
            )
        else:
            reasoning_parts.append(
                f"Predicted ROAS ({result.predicted_roas:.2f}x) is {abs(roas_diff):.2f}x below baseline ({baseline_roas:.2f}x)"
            )
        
        # Confidence
        reasoning_parts.append(
            f"Confidence level: {result.confidence_level:.0%} "
            f"({'High' if result.confidence_level >= 0.75 else 'Medium' if result.confidence_level >= 0.60 else 'Low'})"
        )
        
        # Strengths
        if result.strengths:
            reasoning_parts.append(f"Strengths: {', '.join(result.strengths)}")
        
        # Risk factors
        if result.risk_factors:
            reasoning_parts.append(f"Risk factors: {', '.join(result.risk_factors)}")
        
        return ". ".join(reasoning_parts) + "."
    
    async def _get_creative_data(self, creative_id: str) -> Dict:
        """Get creative data from database"""
        query = """
            SELECT 
                c.id,
                c.video_url,
                c.thumbnail_url,
                c.campaign_id,
                c.ad_data,
                c.created_at
            FROM creatives c
            WHERE c.id = $1
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, creative_id)
            if not row:
                raise ValueError(f"Creative {creative_id} not found")
            return dict(row)
    
    async def _extract_creative_dna(self, creative_data: Dict) -> Dict:
        """Extract creative DNA from video"""
        # Call ML service to extract DNA
        response = await self.ml_service_client.post(
            '/api/ml/creative-dna/extract',
            json={
                'video_url': creative_data['video_url'],
                'ad_data': creative_data.get('ad_data', {})
            }
        )
        return response.json()
    
    async def _get_account_baseline(self, account_id: str) -> Dict:
        """Get account performance baseline"""
        if account_id in self._account_baseline_cache:
            return self._account_baseline_cache[account_id]
        
        query = """
            SELECT 
                AVG(ctr) as avg_ctr,
                AVG(roas) as avg_roas,
                COUNT(*) as total_ads
            FROM ad_performance
            WHERE account_id = $1
                AND created_at >= NOW() - INTERVAL '90 days'
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, account_id)
            baseline = {
                'avg_ctr': float(row['avg_ctr'] or 0.02),
                'avg_roas': float(row['avg_roas'] or 2.0),
                'total_ads': int(row['total_ads'] or 0)
            }
            self._account_baseline_cache[account_id] = baseline
            return baseline
    
    def _build_prediction_prompt(self, creative_dna: Dict, account_context: Dict) -> str:
        """Build prompt for Gemini prediction"""
        return f"""
        Analyze this video creative and predict its performance:
        
        Creative DNA:
        - Hook Type: {creative_dna.get('hook_type', 'unknown')}
        - Hook Strength: {creative_dna.get('hook_strength', 0.5)}
        - Visual Pacing: {creative_dna.get('visual_pacing', 'medium')}
        - Caption Style: {creative_dna.get('caption_style', 'standard')}
        - CTA Type: {creative_dna.get('cta_type', 'learn_more')}
        
        Account Baseline:
        - Average CTR: {account_context.get('baseline_ctr', 0.02):.2%}
        - Average ROAS: {account_context.get('baseline_roas', 2.0):.2f}x
        
        Predict:
        1. Expected CTR (0-10%)
        2. Expected ROAS (0-10x)
        3. Conversion probability (0-100%)
        4. Confidence level (0-100%)
        5. Key risk factors
        6. Key strengths
        
        Format as JSON.
        """
    
    def _parse_prediction_response(self, response_text: str) -> Dict:
        """Parse Gemini response"""
        import json
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return {}
    
    async def _get_ml_prediction(self, creative_dna: Dict) -> Dict:
        """Get ML model prediction"""
        response = await self.ml_service_client.post(
            '/api/ml/predict/ctr',
            json={'clip_data': creative_dna}
        )
        return response.json()
    
    def _combine_predictions(
        self,
        ai_prediction: Dict,
        ml_prediction: Dict,
        account_baseline: Dict
    ) -> Dict:
        """Combine AI and ML predictions"""
        # Weighted average: 60% AI, 40% ML
        ctr = (ai_prediction.get('ctr', 0) * 0.6) + (ml_prediction.get('predicted_ctr', 0) * 0.4)
        roas = (ai_prediction.get('roas', 0) * 0.6) + (ml_prediction.get('predicted_roas', 0) * 0.4)
        
        return {
            'ctr': max(0, min(ctr, 0.10)),  # Cap at 10%
            'roas': max(0, min(roas, 10.0)),  # Cap at 10x
            'conversion_prob': ai_prediction.get('conversion_prob', 0.5)
        }
    
    def _calculate_confidence(
        self,
        prediction: Dict,
        account_context: Dict,
        creative_dna: Dict
    ) -> float:
        """Calculate confidence level"""
        # Factors:
        # 1. Data quality (completeness of creative DNA)
        # 2. Account history (more data = higher confidence)
        # 3. Prediction agreement (AI vs ML)
        
        dna_completeness = sum([
            1 if creative_dna.get('hook_type') else 0,
            1 if creative_dna.get('hook_strength') else 0,
            1 if creative_dna.get('visual_pacing') else 0,
            1 if creative_dna.get('caption_style') else 0,
        ]) / 4.0
        
        account_history = min(account_context.get('total_ads', 0) / 100, 1.0)
        
        # Base confidence
        confidence = (dna_completeness * 0.4) + (account_history * 0.3) + 0.3
        
        return min(confidence, 0.95)  # Cap at 95%
    
    def _identify_risk_factors(self, creative_dna: Dict, prediction: Dict) -> List[str]:
        """Identify risk factors"""
        risks = []
        
        if creative_dna.get('hook_strength', 0) < 0.5:
            risks.append("Weak hook (strength < 0.5)")
        
        if prediction['ctr'] < 0.02:
            risks.append("Low predicted CTR (< 2%)")
        
        if prediction['roas'] < 2.0:
            risks.append("Low predicted ROAS (< 2.0x)")
        
        if not creative_dna.get('caption_style'):
            risks.append("Missing captions")
        
        return risks
    
    def _identify_strengths(self, creative_dna: Dict, prediction: Dict) -> List[str]:
        """Identify strengths"""
        strengths = []
        
        if creative_dna.get('hook_strength', 0) >= 0.8:
            strengths.append("Strong hook")
        
        if prediction['ctr'] >= 0.03:
            strengths.append("High predicted CTR (≥ 3%)")
        
        if prediction['roas'] >= 3.0:
            strengths.append("High predicted ROAS (≥ 3.0x)")
        
        if creative_dna.get('visual_pacing') == 'fast':
            strengths.append("Fast-paced visuals (good for attention)")
        
        return strengths
    
    def _suggest_modifications(
        self,
        creative_dna: Dict,
        prediction: Dict,
        account_context: Dict
    ) -> List[str]:
        """Suggest modifications to improve performance"""
        suggestions = []
        
        if creative_dna.get('hook_strength', 0) < 0.6:
            suggestions.append("Strengthen hook in first 3 seconds")
        
        if prediction['ctr'] < account_context.get('baseline_ctr', 0.02):
            suggestions.append("Add text overlay to improve CTR")
        
        if not creative_dna.get('caption_style'):
            suggestions.append("Add captions for better engagement")
        
        if creative_dna.get('cta_type') == 'learn_more':
            suggestions.append("Consider more specific CTA (e.g., 'Start Free Trial')")
        
        return suggestions
```

---

### Step 3: Enhanced API Endpoint

```python
# File: services/titan-core/api/main.py

from pydantic import BaseModel
from typing import Optional, Dict, Any

class OracleQueryRequest(BaseModel):
    """Request for Oracle prediction (natural language or structured)"""
    query: Optional[str] = None  # Natural language query
    creative_id: Optional[str] = None
    account_id: Optional[str] = None
    creative_dna: Optional[Dict] = None
    include_recommendation: bool = True
    include_confidence: bool = True

@app.post("/api/titan/oracle/predict", tags=["Oracle Agent"])
async def oracle_predict(request: OracleQueryRequest):
    """
    Predict creative performance with go/no-go recommendation.
    
    Examples:
    1. Natural Language:
       {
         "query": "I'm about to launch video creative 'xyz-123'. Should I proceed?",
         "account_id": "account_123"
       }
    
    2. Structured:
       {
         "creative_id": "xyz-123",
         "account_id": "account_123",
         "include_recommendation": true,
         "include_confidence": true
       }
    """
    try:
        oracle = get_oracle_agent()
        
        if request.query:
            # Natural language query
            result = await oracle.predict_from_query(
                query=request.query,
                context={'account_id': request.account_id}
            )
        else:
            # Structured query
            if not request.creative_id:
                raise ValueError("creative_id is required if query is not provided")
            
            # Get creative DNA
            if request.creative_dna:
                creative_dna = request.creative_dna
            else:
                creative_data = await get_creative_data(request.creative_id)
                creative_dna = await extract_creative_dna(creative_data)
            
            # Get account baseline
            account_baseline = await get_account_baseline(request.account_id)
            
            # Predict
            result = await oracle.predict(
                creative_dna=creative_dna,
                account_context={
                    'account_id': request.account_id,
                    'baseline_ctr': account_baseline.get('avg_ctr', 0.02),
                    'baseline_roas': account_baseline.get('avg_roas', 2.0)
                }
            )
            
            # Add recommendation
            result.recommendation = oracle._generate_recommendation(
                result=result,
                account_baseline=account_baseline
            )
            
            result.reasoning = oracle._generate_reasoning(
                result=result,
                account_baseline=account_baseline
            )
        
        response = {
            'creative_id': result.creative_id,
            'predicted_ctr': result.predicted_ctr,
            'predicted_roas': result.predicted_roas,
            'conversion_probability': result.conversion_probability,
        }
        
        if request.include_confidence:
            response['confidence_level'] = result.confidence_level
        
        if request.include_recommendation:
            response['recommendation'] = result.recommendation
            response['reasoning'] = result.reasoning
            response['risk_factors'] = result.risk_factors
            response['strengths'] = result.strengths
            response['suggested_modifications'] = result.suggested_modifications
        
        response['account_baseline_comparison'] = result.account_baseline_comparison
        response['prediction_metadata'] = result.prediction_metadata
        
        return response
        
    except Exception as e:
        logger.error(f"Error in Oracle prediction: {e}", exc_info=True)
        raise HTTPException(500, str(e))
```

---

### Step 4: Usage Examples

#### Example 1: Natural Language Query
```bash
POST /api/titan/oracle/predict
{
  "query": "I'm about to launch a new video creative (ID: 'xyz-123'). Analyze its creative DNA and predict its potential performance. Should I proceed with the launch, and what is your confidence level?",
  "account_id": "account_123"
}
```

**Response:**
```json
{
  "creative_id": "xyz-123",
  "predicted_ctr": 0.034,
  "predicted_roas": 3.5,
  "conversion_probability": 0.72,
  "confidence_level": 0.82,
  "recommendation": "PROCEED",
  "reasoning": "Predicted CTR (3.40%) is 1.40% above baseline (2.00%). Predicted ROAS (3.50x) is 1.50x above baseline (2.00x). Confidence level: 82% (High). Strengths: Strong hook, High predicted CTR (≥ 3%), Fast-paced visuals (good for attention).",
  "risk_factors": [],
  "strengths": [
    "Strong hook",
    "High predicted CTR (≥ 3%)",
    "Fast-paced visuals (good for attention)"
  ],
  "suggested_modifications": [],
  "account_baseline_comparison": {
    "baseline_ctr": 0.02,
    "baseline_roas": 2.0,
    "ctr_vs_baseline": 1.7,
    "roas_vs_baseline": 1.75
  },
  "prediction_metadata": {
    "prediction_method": "hybrid_ai_ml",
    "ai_confidence": 0.75,
    "ml_confidence": 0.85,
    "predicted_at": "2024-12-08T10:00:00Z"
  }
}
```

#### Example 2: Structured Query
```bash
POST /api/titan/oracle/predict
{
  "creative_id": "xyz-123",
  "account_id": "account_123",
  "include_recommendation": true,
  "include_confidence": true
}
```

#### Example 3: Low Performance (REJECT)
```json
{
  "creative_id": "xyz-456",
  "predicted_ctr": 0.015,
  "predicted_roas": 1.5,
  "recommendation": "REJECT",
  "reasoning": "Predicted CTR (1.50%) is 0.50% below baseline (2.00%). Predicted ROAS (1.50x) is 0.50x below baseline (2.00x). Confidence level: 65% (Medium). Risk factors: Weak hook (strength < 0.5), Low predicted CTR (< 2%), Low predicted ROAS (< 2.0x).",
  "suggested_modifications": [
    "Strengthen hook in first 3 seconds",
    "Add text overlay to improve CTR",
    "Add captions for better engagement"
  ]
}
```

---

## 🧪 TESTING

### Test 1: Natural Language Query
```bash
curl -X POST http://localhost:8084/api/titan/oracle/predict \
  -H "Content-Type: application/json" \
  -d '{
    "query": "I'm about to launch video creative xyz-123. Should I proceed?",
    "account_id": "account_123"
  }'
```

### Test 2: With Confidence Request
```bash
curl -X POST http://localhost:8084/api/titan/oracle/predict \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze creative ID xyz-123 and predict performance. What is your confidence level?",
    "account_id": "account_123"
  }'
```

---

## ✅ IMPLEMENTATION CHECKLIST

- [ ] Create OracleQueryParser
- [ ] Enhance OracleAgent with query parsing
- [ ] Add creative ID lookup
- [ ] Add recommendation logic (PROCEED/REJECT/MODIFY)
- [ ] Add confidence calculation
- [ ] Add reasoning generation
- [ ] Add risk factors identification
- [ ] Add strengths identification
- [ ] Add modification suggestions
- [ ] Update API endpoint
- [ ] Test with various queries

---

## 📊 SUMMARY

**Question:** "I'm about to launch a new video creative (ID: 'xyz-123'). Analyze its creative DNA and predict its potential performance. Should I proceed with the launch, and what is your confidence level?"

**Current Status:** ⚠️ **PARTIALLY IMPLEMENTED**

**What Exists:**
- ✅ Oracle Agent (basic prediction)
- ✅ Creative DNA extraction
- ✅ Basic prediction endpoint

**What's Missing:**
- ⚠️ Natural language query parsing
- ⚠️ Creative ID lookup
- ⚠️ Go/no-go recommendation logic
- ⚠️ Confidence level explanation
- ⚠️ Reasoning generation

**Estimated Time to Complete:** 6-8 hours

**This enhancement will enable the system to answer any creative prediction question dynamically!**

