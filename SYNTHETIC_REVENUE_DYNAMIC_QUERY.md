# 💰 SYNTHETIC REVENUE DYNAMIC QUERY SYSTEM
## Can It Handle: "Calculate synthetic revenue for deal stage change?"

**Question:** "A lead from the 'Summer Promo' campaign just moved to the 'Proposal Sent' stage in HubSpot with a deal value of $25,000. What is the calculated synthetic revenue for this event?"

**What It Checks:**
- Can calculate synthetic revenue dynamically for any stage change
- Can handle campaign attribution
- Can use deal value in calculation
- Can answer natural language questions about calculations

---

## 🔍 CURRENT IMPLEMENTATION STATUS

### ✅ What Exists

**1. Synthetic Revenue Calculator (`synthetic_revenue.py`)**
```python
# File: services/ml-service/src/synthetic_revenue.py

class SyntheticRevenueCalculator:
    """Calculate synthetic revenue from CRM pipeline stages"""
    
    def calculate_stage_change(
        self,
        tenant_id: str,
        stage_from: Optional[str],
        stage_to: str,
        deal_value: Optional[float] = None
    ) -> SyntheticRevenueResult:
        """Calculate synthetic revenue for stage change"""
        # Gets stage config from database
        # Calculates based on stage value percentage
        # Returns calculated_value
```

**2. Database Schema**
```sql
-- File: database/migrations/002_synthetic_revenue_config.sql

CREATE TABLE synthetic_revenue_config (
    tenant_id VARCHAR(255),
    stage_name VARCHAR(255),
    value_percentage NUMERIC(5, 2),  -- e.g., 0.30 = 30%
    confidence_score NUMERIC(3, 2),
    -- ...
);
```

**3. API Endpoint (Basic)**
```python
# File: services/ml-service/src/main.py

@app.post("/api/ml/synthetic-revenue/calculate")
async def calculate_synthetic_revenue(request: SyntheticRevenueRequest):
    """Calculate synthetic revenue for stage change"""
    # Basic calculation exists
```

---

## ⚠️ WHAT'S MISSING: DYNAMIC QUERY HANDLING

**Current Limitation:**
- Endpoint requires structured input (tenant_id, stage_from, stage_to)
- No natural language query parsing
- No campaign attribution in calculation
- No explanation of calculation logic

---

## 🔧 SOLUTION: DYNAMIC QUERY SYSTEM

### Step 1: Natural Language Query Parser

```python
# File: services/ml-service/src/query_parser.py

import re
from typing import Dict, Optional, Any
from datetime import datetime

class SyntheticRevenueQueryParser:
    """Parse natural language queries about synthetic revenue"""
    
    def __init__(self):
        self.stage_patterns = {
            r'proposal\s+sent': 'proposal_sent',
            r'appointment\s+scheduled': 'appointment_scheduled',
            r'qualified\s+lead': 'qualified_lead',
            r'closed\s+won': 'closed_won',
            r'closed\s+lost': 'closed_lost',
            r'negotiation': 'negotiation',
            r'decision\s+maker': 'decision_maker',
        }
        
        self.campaign_patterns = [
            r"from\s+(?:the\s+)?['\"]?([^'\"]+)['\"]?\s+campaign",
            r"campaign\s+['\"]?([^'\"]+)['\"]?",
            r"('.*?'|[\"'].*?[\"'])\s+campaign"
        ]
        
        self.deal_value_patterns = [
            r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+)\s*(?:thousand|k|K)',
            r'deal\s+value\s+of\s+\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
    
    def parse(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse natural language query about synthetic revenue.
        
        Examples:
        - "A lead from 'Summer Promo' campaign moved to 'Proposal Sent' with $25,000. Calculate synthetic revenue."
        - "What's the synthetic revenue for a $30k deal moving to Proposal Sent?"
        - "Calculate synthetic revenue: Proposal Sent stage, deal value $25,000"
        """
        query_lower = query.lower()
        
        # Extract stage
        stage_to = self._extract_stage(query_lower, query)
        
        # Extract deal value
        deal_value = self._extract_deal_value(query_lower, query)
        
        # Extract campaign
        campaign_name = self._extract_campaign(query_lower, query)
        
        # Extract tenant_id from context or query
        tenant_id = self._extract_tenant_id(query_lower, context)
        
        # Extract stage_from (if mentioned)
        stage_from = self._extract_stage_from(query_lower, query)
        
        return {
            'tenant_id': tenant_id,
            'campaign_name': campaign_name,
            'stage_from': stage_from,
            'stage_to': stage_to,
            'deal_value': deal_value,
            'raw_query': query
        }
    
    def _extract_stage(self, query_lower: str, original_query: str) -> Optional[str]:
        """Extract stage name from query"""
        # Try exact matches first
        for pattern, stage_name in self.stage_patterns.items():
            if re.search(pattern, query_lower):
                return stage_name
        
        # Try quoted strings
        quoted = re.search(r"['\"]([^'\"]+)['\"]", original_query)
        if quoted:
            stage_text = quoted.group(1).lower()
            for pattern, stage_name in self.stage_patterns.items():
                if re.search(pattern, stage_text):
                    return stage_name
        
        return None
    
    def _extract_deal_value(self, query_lower: str, original_query: str) -> Optional[float]:
        """Extract deal value from query"""
        # Try explicit deal value patterns
        for pattern in self.deal_value_patterns:
            match = re.search(pattern, original_query, re.IGNORECASE)
            if match:
                value_str = match.group(1).replace(',', '')
                
                # Handle "thousand" or "k"
                if 'thousand' in query_lower or ' k' in query_lower or 'k' in query_lower:
                    return float(value_str) * 1000
                
                return float(value_str)
        
        return None
    
    def _extract_campaign(self, query_lower: str, original_query: str) -> Optional[str]:
        """Extract campaign name from query"""
        for pattern in self.campaign_patterns:
            match = re.search(pattern, original_query, re.IGNORECASE)
            if match:
                campaign = match.group(1).strip("'\"")
                return campaign
        
        return None
    
    def _extract_tenant_id(self, query_lower: str, context: Optional[Dict]) -> Optional[str]:
        """Extract tenant_id from context or query"""
        if context and 'tenant_id' in context:
            return context['tenant_id']
        
        # Try to extract from query (if mentioned)
        tenant_match = re.search(r'tenant[_\s]?id[:\s]+(\w+)', query_lower)
        if tenant_match:
            return tenant_match.group(1)
        
        return None
    
    def _extract_stage_from(self, query_lower: str, original_query: str) -> Optional[str]:
        """Extract previous stage if mentioned"""
        # Look for "moved from X to Y" or "changed from X to Y"
        from_match = re.search(r'(?:moved|changed)\s+from\s+['\"]?([^'\"]+)['\"]?', query_lower)
        if from_match:
            stage_text = from_match.group(1).lower()
            for pattern, stage_name in self.stage_patterns.items():
                if re.search(pattern, stage_text):
                    return stage_name
        
        return None
```

---

### Step 2: Enhanced Synthetic Revenue Calculator

```python
# File: services/ml-service/src/synthetic_revenue.py

from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class SyntheticRevenueResult:
    """Result of synthetic revenue calculation"""
    tenant_id: str
    stage_from: Optional[str]
    stage_to: str
    deal_value: Optional[float]
    calculated_value: float
    calculation_method: str
    stage_value_percentage: float
    confidence_score: float
    explanation: str
    campaign_name: Optional[str] = None
    attribution_details: Optional[Dict] = None

class EnhancedSyntheticRevenueCalculator:
    """Enhanced calculator with campaign attribution and explanations"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
        self._stage_config_cache = {}
    
    async def calculate_with_query(
        self,
        query: str,
        context: Optional[Dict] = None
    ) -> SyntheticRevenueResult:
        """
        Calculate synthetic revenue from natural language query.
        
        Args:
            query: Natural language query
            context: Additional context (tenant_id, etc.)
        
        Returns:
            SyntheticRevenueResult with calculation and explanation
        """
        from query_parser import SyntheticRevenueQueryParser
        
        parser = SyntheticRevenueQueryParser()
        parsed = parser.parse(query, context)
        
        # Validate required fields
        if not parsed.get('tenant_id'):
            raise ValueError("tenant_id is required (provide in context or query)")
        
        if not parsed.get('stage_to'):
            raise ValueError("Could not extract stage from query")
        
        # Calculate synthetic revenue
        result = await self.calculate_stage_change(
            tenant_id=parsed['tenant_id'],
            stage_from=parsed.get('stage_from'),
            stage_to=parsed['stage_to'],
            deal_value=parsed.get('deal_value'),
            campaign_name=parsed.get('campaign_name')
        )
        
        # Add query context
        result.raw_query = query
        result.parsed_query = parsed
        
        return result
    
    async def calculate_stage_change(
        self,
        tenant_id: str,
        stage_from: Optional[str],
        stage_to: str,
        deal_value: Optional[float] = None,
        campaign_name: Optional[str] = None
    ) -> SyntheticRevenueResult:
        """
        Calculate synthetic revenue for stage change with campaign attribution.
        """
        # Get stage configuration
        stage_config = await self._get_stage_config(tenant_id, stage_to)
        
        if not stage_config:
            raise ValueError(f"Stage '{stage_to}' not configured for tenant {tenant_id}")
        
        # Calculate based on method
        if deal_value:
            # Method 1: Use deal value * stage percentage
            calculated_value = deal_value * (stage_config['value_percentage'] / 100)
            calculation_method = "deal_value_percentage"
            explanation = (
                f"Deal value ${deal_value:,.2f} × {stage_config['value_percentage']}% "
                f"(stage value percentage) = ${calculated_value:,.2f}"
            )
        else:
            # Method 2: Use average deal value for tenant
            avg_deal_value = await self._get_average_deal_value(tenant_id)
            calculated_value = avg_deal_value * (stage_config['value_percentage'] / 100)
            calculation_method = "average_deal_value_percentage"
            explanation = (
                f"Average deal value ${avg_deal_value:,.2f} × {stage_config['value_percentage']}% "
                f"(stage value percentage) = ${calculated_value:,.2f}"
            )
        
        # Get campaign attribution if campaign_name provided
        attribution_details = None
        if campaign_name:
            attribution_details = await self._get_campaign_attribution(
                tenant_id=tenant_id,
                campaign_name=campaign_name
            )
        
        return SyntheticRevenueResult(
            tenant_id=tenant_id,
            stage_from=stage_from,
            stage_to=stage_to,
            deal_value=deal_value,
            calculated_value=calculated_value,
            calculation_method=calculation_method,
            stage_value_percentage=stage_config['value_percentage'],
            confidence_score=stage_config.get('confidence_score', 0.8),
            explanation=explanation,
            campaign_name=campaign_name,
            attribution_details=attribution_details
        )
    
    async def _get_stage_config(self, tenant_id: str, stage_name: str) -> Optional[Dict]:
        """Get stage configuration from database"""
        # Check cache first
        cache_key = f"{tenant_id}:{stage_name}"
        if cache_key in self._stage_config_cache:
            return self._stage_config_cache[cache_key]
        
        # Query database
        query = """
            SELECT 
                stage_name,
                value_percentage,
                confidence_score,
                description
            FROM synthetic_revenue_config
            WHERE tenant_id = $1 AND stage_name = $2
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, tenant_id, stage_name)
            
            if row:
                config = dict(row)
                self._stage_config_cache[cache_key] = config
                return config
        
        return None
    
    async def _get_average_deal_value(self, tenant_id: str) -> float:
        """Get average deal value for tenant"""
        query = """
            SELECT AVG(deal_value) as avg_value
            FROM hubspot_deals
            WHERE tenant_id = $1
                AND deal_value IS NOT NULL
                AND deal_value > 0
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, tenant_id)
            return float(row['avg_value']) if row and row['avg_value'] else 10000.0  # Default
    
    async def _get_campaign_attribution(
        self,
        tenant_id: str,
        campaign_name: str
    ) -> Dict[str, Any]:
        """Get campaign attribution details"""
        query = """
            SELECT 
                c.id as campaign_id,
                c.name as campaign_name,
                SUM(ach.spend) as total_spend,
                COUNT(DISTINCT at.contact_email) as attributed_leads
            FROM campaigns c
            LEFT JOIN ad_change_history ach ON c.id = ach.campaign_id
            LEFT JOIN attribution_tracking at ON ach.ad_id = at.ad_id
            WHERE c.tenant_id = $1
                AND c.name ILIKE $2
            GROUP BY c.id, c.name
        """
        
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(query, tenant_id, f"%{campaign_name}%")
            
            if row:
                return {
                    'campaign_id': row['campaign_id'],
                    'campaign_name': row['campaign_name'],
                    'total_spend': float(row['total_spend'] or 0),
                    'attributed_leads': int(row['attributed_leads'] or 0)
                }
        
        return None
    
    async def explain_calculation(
        self,
        tenant_id: str,
        stage_to: str,
        deal_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Explain how synthetic revenue is calculated for a stage.
        Useful for answering "how" questions.
        """
        stage_config = await self._get_stage_config(tenant_id, stage_to)
        
        if not stage_config:
            return {
                'error': f"Stage '{stage_to}' not configured"
            }
        
        explanation = {
            'stage_name': stage_to,
            'stage_value_percentage': stage_config['value_percentage'],
            'confidence_score': stage_config.get('confidence_score', 0.8),
            'description': stage_config.get('description', ''),
            'calculation_methods': []
        }
        
        if deal_value:
            calculated = deal_value * (stage_config['value_percentage'] / 100)
            explanation['calculation_methods'].append({
                'method': 'deal_value_percentage',
                'formula': f'Deal Value × Stage Percentage',
                'example': f'${deal_value:,.2f} × {stage_config["value_percentage"]}% = ${calculated:,.2f}',
                'when_to_use': 'When deal value is known'
            })
        else:
            avg_deal = await self._get_average_deal_value(tenant_id)
            calculated = avg_deal * (stage_config['value_percentage'] / 100)
            explanation['calculation_methods'].append({
                'method': 'average_deal_value_percentage',
                'formula': f'Average Deal Value × Stage Percentage',
                'example': f'${avg_deal:,.2f} × {stage_config["value_percentage"]}% = ${calculated:,.2f}',
                'when_to_use': 'When deal value is not specified'
            })
        
        return explanation
```

---

### Step 3: Enhanced API Endpoint

```python
# File: services/ml-service/src/main.py

from pydantic import BaseModel
from typing import Optional, Dict, Any

class SyntheticRevenueQueryRequest(BaseModel):
    """Request for synthetic revenue calculation (natural language or structured)"""
    query: Optional[str] = None  # Natural language query
    tenant_id: Optional[str] = None
    campaign_name: Optional[str] = None
    stage_from: Optional[str] = None
    stage_to: Optional[str] = None
    deal_value: Optional[float] = None
    include_explanation: bool = True

@app.post("/api/ml/synthetic-revenue/calculate", tags=["Synthetic Revenue"])
async def calculate_synthetic_revenue(request: SyntheticRevenueQueryRequest):
    """
    Calculate synthetic revenue from natural language or structured query.
    
    Examples:
    1. Natural Language:
       {
         "query": "A lead from 'Summer Promo' campaign moved to 'Proposal Sent' with $25,000. Calculate synthetic revenue.",
         "tenant_id": "tenant_123"
       }
    
    2. Structured:
       {
         "tenant_id": "tenant_123",
         "campaign_name": "Summer Promo",
         "stage_to": "proposal_sent",
         "deal_value": 25000
       }
    
    3. Explain Calculation:
       {
         "query": "How is synthetic revenue calculated for Proposal Sent stage?",
         "tenant_id": "tenant_123"
       }
    """
    try:
        calculator = get_synthetic_revenue_calculator()
        
        # Check if it's an explanation query
        if request.query and any(word in request.query.lower() for word in ['how', 'explain', 'calculate', 'method']):
            # Return explanation
            parsed = calculator.parser.parse(request.query, {'tenant_id': request.tenant_id})
            explanation = await calculator.explain_calculation(
                tenant_id=request.tenant_id or parsed.get('tenant_id'),
                stage_to=parsed.get('stage_to') or request.stage_to,
                deal_value=parsed.get('deal_value') or request.deal_value
            )
            return explanation
        
        # Calculate synthetic revenue
        if request.query:
            # Natural language query
            result = await calculator.calculate_with_query(
                query=request.query,
                context={'tenant_id': request.tenant_id}
            )
        else:
            # Structured query
            result = await calculator.calculate_stage_change(
                tenant_id=request.tenant_id,
                stage_from=request.stage_from,
                stage_to=request.stage_to,
                deal_value=request.deal_value,
                campaign_name=request.campaign_name
            )
        
        response = {
            'calculated_value': result.calculated_value,
            'calculation_method': result.calculation_method,
            'stage_to': result.stage_to,
            'stage_value_percentage': result.stage_value_percentage,
            'confidence_score': result.confidence_score,
            'deal_value_used': result.deal_value,
            'campaign_name': result.campaign_name
        }
        
        if request.include_explanation:
            response['explanation'] = result.explanation
        
        if result.attribution_details:
            response['campaign_attribution'] = result.attribution_details
        
        return response
        
    except Exception as e:
        logger.error(f"Error calculating synthetic revenue: {e}", exc_info=True)
        raise HTTPException(500, str(e))
```

---

### Step 4: Usage Examples

#### Example 1: Natural Language Query
```bash
POST /api/ml/synthetic-revenue/calculate
{
  "query": "A lead from the 'Summer Promo' campaign just moved to the 'Proposal Sent' stage in HubSpot with a deal value of $25,000. What is the calculated synthetic revenue for this event?",
  "tenant_id": "tenant_123"
}
```

**Response:**
```json
{
  "calculated_value": 7500.00,
  "calculation_method": "deal_value_percentage",
  "stage_to": "proposal_sent",
  "stage_value_percentage": 30.0,
  "confidence_score": 0.85,
  "deal_value_used": 25000.00,
  "campaign_name": "Summer Promo",
  "explanation": "Deal value $25,000.00 × 30% (stage value percentage) = $7,500.00",
  "campaign_attribution": {
    "campaign_id": "campaign_456",
    "campaign_name": "Summer Promo",
    "total_spend": 50000.00,
    "attributed_leads": 15
  }
}
```

#### Example 2: Structured Query
```bash
POST /api/ml/synthetic-revenue/calculate
{
  "tenant_id": "tenant_123",
  "campaign_name": "Summer Promo",
  "stage_to": "proposal_sent",
  "deal_value": 25000,
  "include_explanation": true
}
```

#### Example 3: Explanation Query
```bash
POST /api/ml/synthetic-revenue/calculate
{
  "query": "How is synthetic revenue calculated for Proposal Sent stage?",
  "tenant_id": "tenant_123",
  "deal_value": 25000
}
```

**Response:**
```json
{
  "stage_name": "proposal_sent",
  "stage_value_percentage": 30.0,
  "confidence_score": 0.85,
  "description": "Proposal sent to client - 30% of deal value",
  "calculation_methods": [
    {
      "method": "deal_value_percentage",
      "formula": "Deal Value × Stage Percentage",
      "example": "$25,000.00 × 30% = $7,500.00",
      "when_to_use": "When deal value is known"
    }
  ]
}
```

---

## 🧪 TESTING

### Test 1: Natural Language Query
```bash
curl -X POST http://localhost:8003/api/ml/synthetic-revenue/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "A lead from Summer Promo campaign moved to Proposal Sent with $25,000. Calculate synthetic revenue.",
    "tenant_id": "tenant_123"
  }'
```

### Test 2: Different Deal Values
```bash
curl -X POST http://localhost:8003/api/ml/synthetic-revenue/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is synthetic revenue for a $50k deal moving to Proposal Sent?",
    "tenant_id": "tenant_123"
  }'
```

### Test 3: Without Deal Value
```bash
curl -X POST http://localhost:8003/api/ml/synthetic-revenue/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Calculate synthetic revenue for Proposal Sent stage",
    "tenant_id": "tenant_123"
  }'
```

### Test 4: Explanation Query
```bash
curl -X POST http://localhost:8003/api/ml/synthetic-revenue/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How is synthetic revenue calculated for Proposal Sent?",
    "tenant_id": "tenant_123"
  }'
```

---

## ✅ IMPLEMENTATION CHECKLIST

- [ ] Create SyntheticRevenueQueryParser
- [ ] Enhance SyntheticRevenueCalculator with query parsing
- [ ] Add campaign attribution lookup
- [ ] Add explanation generation
- [ ] Update API endpoint to accept natural language queries
- [ ] Add explanation endpoint
- [ ] Test with various query formats
- [ ] Add error handling for missing data
- [ ] Add caching for stage configs
- [ ] Document query patterns

---

## 📊 SUMMARY

**Question:** "A lead from the 'Summer Promo' campaign just moved to the 'Proposal Sent' stage in HubSpot with a deal value of $25,000. What is the calculated synthetic revenue for this event?"

**Current Status:** ⚠️ **PARTIALLY IMPLEMENTED**

**What Exists:**
- ✅ Synthetic revenue calculation logic
- ✅ Stage configuration system
- ✅ Basic API endpoint

**What's Missing:**
- ⚠️ Natural language query parsing
- ⚠️ Campaign name extraction and attribution
- ⚠️ Explanation generation
- ⚠️ Dynamic query handling

**Estimated Time to Complete:** 4-6 hours

**This enhancement will enable the system to answer any synthetic revenue question dynamically!**

