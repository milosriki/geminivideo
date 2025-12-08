# 🔄 DYNAMIC QUERY SYSTEM
## Flexible Business Intelligence Query Engine

**Problem:** Hardcoded queries don't scale. Need dynamic system that adapts to any question.

**Solution:** Query parser + dynamic data aggregation + flexible response formatting

---

## 🎯 CORE CONCEPT

**Instead of hardcoded endpoints, build a query engine that:**
1. Parses natural language or structured queries
2. Dynamically determines data sources needed
3. Applies appropriate calculations
4. Formats response based on query type

---

## 📊 STEP 1: QUERY PARSER

```python
# File: services/ml-service/src/query_parser.py

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import re
from enum import Enum

class QueryType(Enum):
    """Types of queries the system can handle"""
    TOP_PERFORMERS = "top_performers"
    TREND_ANALYSIS = "trend_analysis"
    COMPARISON = "comparison"
    AGGREGATION = "aggregation"
    ATTRIBUTION = "attribution"
    PREDICTION = "prediction"

class MetricType(Enum):
    """Available metrics"""
    ROAS = "roas"
    CTR = "ctr"
    CPA = "cpa"
    REVENUE = "revenue"
    SPEND = "spend"
    CONVERSIONS = "conversions"
    IMPRESSIONS = "impressions"
    CLICKS = "clicks"
    PIPELINE_VALUE = "pipeline_value"

class TimeRange:
    """Dynamic time range parser"""
    
    PATTERNS = {
        r'last\s+(\d+)\s+days?': lambda m: timedelta(days=int(m.group(1))),
        r'last\s+(\d+)\s+weeks?': lambda m: timedelta(weeks=int(m.group(1))),
        r'last\s+(\d+)\s+months?': lambda m: timedelta(days=int(m.group(1)) * 30),
        r'last\s+quarter': lambda m: timedelta(days=90),
        r'last\s+year': lambda m: timedelta(days=365),
        r'this\s+month': lambda m: timedelta(days=datetime.now().day),
        r'this\s+quarter': lambda m: timedelta(days=(datetime.now().month - 1) % 3 * 30),
    }
    
    @classmethod
    def parse(cls, time_string: str) -> tuple[datetime, datetime]:
        """Parse time string into start and end dates"""
        time_string = time_string.lower().strip()
        
        # Try patterns
        for pattern, func in cls.PATTERNS.items():
            match = re.search(pattern, time_string)
            if match:
                delta = func(match)
                end_date = datetime.utcnow()
                start_date = end_date - delta
                return start_date, end_date
        
        # Try ISO format
        try:
            if ' to ' in time_string or ' - ' in time_string:
                parts = re.split(r'\s+(?:to|-)\s+', time_string)
                start_date = datetime.fromisoformat(parts[0].replace(' ', 'T'))
                end_date = datetime.fromisoformat(parts[1].replace(' ', 'T'))
                return start_date, end_date
        except:
            pass
        
        # Default: last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        return start_date, end_date

class QueryParser:
    """Parse business intelligence queries into structured format"""
    
    def __init__(self):
        self.metric_keywords = {
            'roas': MetricType.ROAS,
            'return on ad spend': MetricType.ROAS,
            'ctr': MetricType.CTR,
            'click through rate': MetricType.CTR,
            'cpa': MetricType.CPA,
            'cost per acquisition': MetricType.CPA,
            'revenue': MetricType.REVENUE,
            'spend': MetricType.SPEND,
            'conversions': MetricType.CONVERSIONS,
            'impressions': MetricType.IMPRESSIONS,
            'clicks': MetricType.CLICKS,
            'pipeline': MetricType.PIPELINE_VALUE,
        }
        
        self.query_type_keywords = {
            'top': QueryType.TOP_PERFORMERS,
            'best': QueryType.TOP_PERFORMERS,
            'worst': QueryType.TOP_PERFORMERS,
            'trend': QueryType.TREND_ANALYSIS,
            'compare': QueryType.COMPARISON,
            'vs': QueryType.COMPARISON,
            'total': QueryType.AGGREGATION,
            'sum': QueryType.AGGREGATION,
            'average': QueryType.AGGREGATION,
            'attribution': QueryType.ATTRIBUTION,
            'predict': QueryType.PREDICTION,
        }
    
    def parse(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse natural language or structured query.
        
        Examples:
        - "Top 5 campaigns by ROAS last quarter"
        - "Compare campaign A vs campaign B this month"
        - "What's the trend for CTR over last 30 days?"
        - "Total revenue by audience segment"
        """
        query_lower = query.lower()
        
        # Extract query type
        query_type = self._extract_query_type(query_lower)
        
        # Extract metric
        metric = self._extract_metric(query_lower)
        
        # Extract time range
        time_range = self._extract_time_range(query_lower)
        
        # Extract entity type (campaign, ad, adset, etc.)
        entity_type = self._extract_entity_type(query_lower)
        
        # Extract filters
        filters = self._extract_filters(query_lower, context)
        
        # Extract grouping/segmentation
        group_by = self._extract_group_by(query_lower)
        
        # Extract limit (top N)
        limit = self._extract_limit(query_lower)
        
        # Extract ordering
        order_by = metric  # Default to metric
        order_direction = 'desc' if 'top' in query_lower or 'best' in query_lower else 'asc'
        
        return {
            'query_type': query_type.value,
            'metric': metric.value if metric else None,
            'time_range': {
                'start': time_range[0].isoformat(),
                'end': time_range[1].isoformat()
            },
            'entity_type': entity_type,
            'filters': filters,
            'group_by': group_by,
            'limit': limit,
            'order_by': order_by.value if order_by else None,
            'order_direction': order_direction,
            'raw_query': query
        }
    
    def _extract_query_type(self, query: str) -> QueryType:
        """Extract query type from keywords"""
        for keyword, qtype in self.query_type_keywords.items():
            if keyword in query:
                return qtype
        return QueryType.AGGREGATION  # Default
    
    def _extract_metric(self, query: str) -> Optional[MetricType]:
        """Extract metric from keywords"""
        for keyword, metric in self.metric_keywords.items():
            if keyword in query:
                return metric
        return None
    
    def _extract_time_range(self, query: str) -> tuple[datetime, datetime]:
        """Extract time range"""
        return TimeRange.parse(query)
    
    def _extract_entity_type(self, query: str) -> str:
        """Extract entity type (campaign, ad, adset)"""
        if 'campaign' in query:
            return 'campaign'
        elif 'ad set' in query or 'adset' in query:
            return 'adset'
        elif 'ad ' in query and 'ad set' not in query:
            return 'ad'
        return 'campaign'  # Default
    
    def _extract_filters(self, query: str, context: Optional[Dict]) -> Dict[str, Any]:
        """Extract filters (tenant_id, status, etc.)"""
        filters = {}
        
        # Extract from context if provided
        if context:
            if 'tenant_id' in context:
                filters['tenant_id'] = context['tenant_id']
            if 'account_id' in context:
                filters['account_id'] = context['account_id']
        
        # Extract status filters
        if 'active' in query:
            filters['status'] = 'ACTIVE'
        elif 'paused' in query:
            filters['status'] = 'PAUSED'
        
        return filters
    
    def _extract_group_by(self, query: str) -> Optional[List[str]]:
        """Extract grouping dimensions"""
        group_by = []
        
        if 'by audience' in query or 'audience segment' in query:
            group_by.append('audience_segment')
        if 'by campaign' in query:
            group_by.append('campaign')
        if 'by ad' in query:
            group_by.append('ad')
        if 'by date' in query or 'daily' in query:
            group_by.append('date')
        if 'by week' in query or 'weekly' in query:
            group_by.append('week')
        if 'by month' in query or 'monthly' in query:
            group_by.append('month')
        
        return group_by if group_by else None
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract limit (top N)"""
        match = re.search(r'top\s+(\d+)', query)
        if match:
            return int(match.group(1))
        
        match = re.search(r'(\d+)\s+(?:best|worst|top)', query)
        if match:
            return int(match.group(1))
        
        return None
```

---

## 🔄 STEP 2: DYNAMIC DATA AGGREGATOR

```python
# File: services/ml-service/src/dynamic_aggregator.py

from typing import Dict, List, Any, Optional
from datetime import datetime
from query_parser import QueryParser, MetricType, QueryType
import httpx
import asyncio

class DataSource:
    """Abstract data source"""
    
    async def fetch(self, query_params: Dict) -> List[Dict]:
        """Fetch data from source"""
        raise NotImplementedError

class MetaInsightsSource(DataSource):
    """Meta Insights API data source"""
    
    def __init__(self, api_url: str, access_token: str):
        self.api_url = api_url
        self.access_token = access_token
    
    async def fetch(self, query_params: Dict) -> List[Dict]:
        """Fetch from Meta Insights API"""
        level = query_params.get('entity_type', 'campaign')
        start_date = query_params['time_range']['start']
        end_date = query_params['time_range']['end']
        
        # Build Meta API request
        fields = self._get_fields_for_metric(query_params.get('metric'))
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.api_url}/insights",
                params={
                    'level': level,
                    'time_range': {
                        'since': start_date,
                        'until': end_date
                    },
                    'fields': ','.join(fields),
                    'access_token': self.access_token
                }
            )
            return response.json().get('data', [])
    
    def _get_fields_for_metric(self, metric: Optional[MetricType]) -> List[str]:
        """Determine which Meta API fields to fetch based on metric"""
        base_fields = ['campaign_id', 'campaign_name', 'spend', 'impressions', 'clicks']
        
        if metric == MetricType.ROAS:
            return base_fields + ['actions', 'action_values']
        elif metric == MetricType.CTR:
            return base_fields
        elif metric == MetricType.CPA:
            return base_fields + ['actions']
        elif metric == MetricType.REVENUE:
            return base_fields + ['action_values']
        else:
            return base_fields

class HubSpotPipelineSource(DataSource):
    """HubSpot pipeline data source"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def fetch(self, query_params: Dict) -> Dict[str, float]:
        """Fetch pipeline values from HubSpot attribution"""
        start_date = query_params['time_range']['start']
        end_date = query_params['time_range']['end']
        tenant_id = query_params.get('filters', {}).get('tenant_id')
        
        # Query attribution_tracking table
        query = """
            SELECT 
                at.ad_id,
                SUM(sr.calculated_value) as pipeline_value
            FROM attribution_tracking at
            JOIN hubspot_deals hd ON at.contact_email = hd.contact_email
            JOIN synthetic_revenue_calculations sr ON hd.deal_id = sr.deal_id
            WHERE at.tenant_id = $1
                AND at.clicked_at >= $2
                AND at.clicked_at <= $3
            GROUP BY at.ad_id
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query, tenant_id, start_date, end_date)
            return {row['ad_id']: row['pipeline_value'] for row in rows}

class DatabaseSource(DataSource):
    """Database data source"""
    
    def __init__(self, db_pool):
        self.db_pool = db_pool
    
    async def fetch(self, query_params: Dict) -> List[Dict]:
        """Fetch from database"""
        # Build dynamic SQL query based on query_params
        query = self._build_query(query_params)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    
    def _build_query(self, query_params: Dict) -> str:
        """Build SQL query dynamically"""
        entity_type = query_params.get('entity_type', 'campaign')
        time_range = query_params['time_range']
        filters = query_params.get('filters', {})
        group_by = query_params.get('group_by')
        
        # Base query
        if entity_type == 'campaign':
            base = "SELECT c.id, c.name, SUM(ach.spend) as spend"
        elif entity_type == 'ad':
            base = "SELECT a.id, a.name, SUM(ach.spend) as spend"
        else:
            base = "SELECT * FROM ad_change_history"
        
        # Add WHERE clause
        where_clauses = [
            f"ach.created_at >= '{time_range['start']}'",
            f"ach.created_at <= '{time_range['end']}'"
        ]
        
        if 'tenant_id' in filters:
            where_clauses.append(f"c.tenant_id = '{filters['tenant_id']}'")
        
        where_clause = " AND ".join(where_clauses)
        
        # Add GROUP BY
        group_by_clause = ""
        if group_by:
            group_by_clause = f"GROUP BY {', '.join(group_by)}"
        
        return f"{base} WHERE {where_clause} {group_by_clause}"

class DynamicAggregator:
    """Dynamically aggregate data from multiple sources"""
    
    def __init__(self, meta_source: MetaInsightsSource, 
                 hubspot_source: HubSpotPipelineSource,
                 db_source: DatabaseSource):
        self.meta_source = meta_source
        self.hubspot_source = hubspot_source
        self.db_source = db_source
    
    async def aggregate(self, parsed_query: Dict) -> List[Dict]:
        """
        Aggregate data from all relevant sources based on query.
        """
        # Determine which sources are needed
        sources_needed = self._determine_sources(parsed_query)
        
        # Fetch from all sources in parallel
        tasks = []
        if 'meta' in sources_needed:
            tasks.append(self.meta_source.fetch(parsed_query))
        if 'hubspot' in sources_needed:
            tasks.append(self.hubspot_source.fetch(parsed_query))
        if 'database' in sources_needed:
            tasks.append(self.db_source.fetch(parsed_query))
        
        results = await asyncio.gather(*tasks)
        
        # Combine results
        combined_data = self._combine_results(results, parsed_query)
        
        # Calculate metrics
        calculated_data = self._calculate_metrics(combined_data, parsed_query)
        
        # Apply filters
        filtered_data = self._apply_filters(calculated_data, parsed_query)
        
        # Group if needed
        if parsed_query.get('group_by'):
            grouped_data = self._group_data(filtered_data, parsed_query)
        else:
            grouped_data = filtered_data
        
        # Sort
        sorted_data = self._sort_data(grouped_data, parsed_query)
        
        # Limit
        if parsed_query.get('limit'):
            sorted_data = sorted_data[:parsed_query['limit']]
        
        return sorted_data
    
    def _determine_sources(self, query: Dict) -> List[str]:
        """Determine which data sources are needed"""
        sources = ['meta']  # Always need Meta for base metrics
        
        metric = query.get('metric')
        if metric in [MetricType.ROAS, MetricType.PIPELINE_VALUE]:
            sources.append('hubspot')  # Need pipeline data for service businesses
        
        if query.get('group_by') or query.get('filters'):
            sources.append('database')  # Need DB for complex queries
        
        return sources
    
    def _combine_results(self, results: List, query: Dict) -> List[Dict]:
        """Combine data from multiple sources"""
        meta_data = results[0] if results else []
        hubspot_data = results[1] if len(results) > 1 else {}
        
        # Combine Meta data with HubSpot pipeline values
        combined = []
        for item in meta_data:
            ad_id = item.get('ad_id') or item.get('id')
            pipeline_value = hubspot_data.get(ad_id, 0)
            
            combined_item = {
                **item,
                'pipeline_value': pipeline_value,
                'direct_revenue': item.get('revenue', 0),
                'total_revenue': item.get('revenue', 0) + pipeline_value
            }
            combined.append(combined_item)
        
        return combined
    
    def _calculate_metrics(self, data: List[Dict], query: Dict) -> List[Dict]:
        """Calculate requested metrics"""
        metric = query.get('metric')
        
        for item in data:
            if metric == MetricType.ROAS:
                spend = item.get('spend', 0)
                revenue = item.get('total_revenue', 0)
                item['roas'] = revenue / max(spend, 1)
            
            elif metric == MetricType.CTR:
                impressions = item.get('impressions', 0)
                clicks = item.get('clicks', 0)
                item['ctr'] = clicks / max(impressions, 1)
            
            elif metric == MetricType.CPA:
                spend = item.get('spend', 0)
                conversions = item.get('conversions', 0)
                item['cpa'] = spend / max(conversions, 1)
        
        return data
    
    def _apply_filters(self, data: List[Dict], query: Dict) -> List[Dict]:
        """Apply filters"""
        filters = query.get('filters', {})
        
        filtered = data
        for key, value in filters.items():
            filtered = [item for item in filtered if item.get(key) == value]
        
        return filtered
    
    def _group_data(self, data: List[Dict], query: Dict) -> List[Dict]:
        """Group data by specified dimensions"""
        group_by = query.get('group_by', [])
        
        if not group_by:
            return data
        
        # Group by dimensions
        grouped = {}
        for item in data:
            key = tuple(item.get(dim) for dim in group_by)
            if key not in grouped:
                grouped[key] = {
                    **{dim: item.get(dim) for dim in group_by},
                    'count': 0,
                    'spend': 0,
                    'revenue': 0
                }
            
            grouped[key]['count'] += 1
            grouped[key]['spend'] += item.get('spend', 0)
            grouped[key]['revenue'] += item.get('total_revenue', 0)
        
        return list(grouped.values())
    
    def _sort_data(self, data: List[Dict], query: Dict) -> List[Dict]:
        """Sort data"""
        order_by = query.get('order_by')
        order_direction = query.get('order_direction', 'desc')
        
        if not order_by:
            return data
        
        reverse = order_direction == 'desc'
        return sorted(data, key=lambda x: x.get(order_by, 0), reverse=reverse)
```

---

## 🎯 STEP 3: DYNAMIC API ENDPOINT

```python
# File: services/ml-service/src/main.py

from query_parser import QueryParser
from dynamic_aggregator import DynamicAggregator, MetaInsightsSource, HubSpotPipelineSource, DatabaseSource

# Initialize components
query_parser = QueryParser()
meta_source = MetaInsightsSource(
    api_url=os.getenv('META_API_URL'),
    access_token=os.getenv('META_ACCESS_TOKEN')
)
hubspot_source = HubSpotPipelineSource(db_pool)
db_source = DatabaseSource(db_pool)
aggregator = DynamicAggregator(meta_source, hubspot_source, db_source)

@app.post("/api/analytics/query", tags=["Analytics"])
async def dynamic_query(request: DynamicQueryRequest):
    """
    Dynamic business intelligence query endpoint.
    
    Accepts:
    - Natural language queries: "Top 5 campaigns by ROAS last quarter"
    - Structured queries: {"metric": "roas", "limit": 5, "time_range": "last_quarter"}
    """
    try:
        # Parse query (handles both natural language and structured)
        if isinstance(request.query, str):
            # Natural language
            parsed_query = query_parser.parse(
                request.query,
                context={'tenant_id': request.tenant_id}
            )
        else:
            # Structured query
            parsed_query = request.query
            parsed_query['filters'] = parsed_query.get('filters', {})
            parsed_query['filters']['tenant_id'] = request.tenant_id
        
        # Aggregate data dynamically
        results = await aggregator.aggregate(parsed_query)
        
        # Format response based on query type
        response = format_response(results, parsed_query)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in dynamic query: {e}", exc_info=True)
        raise HTTPException(500, str(e))

class DynamicQueryRequest(BaseModel):
    """Request for dynamic query"""
    query: Union[str, Dict[str, Any]]  # Natural language or structured
    tenant_id: str
    include_metadata: bool = False

def format_response(results: List[Dict], query: Dict) -> Dict:
    """Format response based on query type"""
    query_type = query.get('query_type')
    
    if query_type == 'top_performers':
        return {
            'query': query.get('raw_query'),
            'results': [
                {
                    'rank': i + 1,
                    **result
                }
                for i, result in enumerate(results)
            ],
            'summary': calculate_summary(results, query)
        }
    
    elif query_type == 'trend_analysis':
        return {
            'query': query.get('raw_query'),
            'trend': results,
            'summary': calculate_trend_summary(results)
        }
    
    elif query_type == 'comparison':
        return {
            'query': query.get('raw_query'),
            'comparison': results,
            'summary': calculate_comparison_summary(results)
        }
    
    else:
        return {
            'query': query.get('raw_query'),
            'results': results
        }

def calculate_summary(results: List[Dict], query: Dict) -> Dict:
    """Calculate summary statistics"""
    metric = query.get('metric')
    
    if not results:
        return {}
    
    values = [r.get(metric, 0) for r in results if metric in r]
    
    return {
        'count': len(results),
        'average': sum(values) / len(values) if values else 0,
        'total': sum(r.get('spend', 0) for r in results),
        'total_revenue': sum(r.get('total_revenue', 0) for r in results)
    }
```

---

## 🎨 STEP 4: USAGE EXAMPLES

### Example 1: Natural Language Query
```python
POST /api/analytics/query
{
  "query": "Top 5 campaigns by ROAS last quarter",
  "tenant_id": "tenant_123"
}
```

### Example 2: Structured Query
```python
POST /api/analytics/query
{
  "query": {
    "metric": "roas",
    "entity_type": "campaign",
    "time_range": "last_quarter",
    "limit": 5,
    "order_by": "roas",
    "order_direction": "desc"
  },
  "tenant_id": "tenant_123"
}
```

### Example 3: Complex Query with Grouping
```python
POST /api/analytics/query
{
  "query": "Total revenue by audience segment this month",
  "tenant_id": "tenant_123"
}
```

### Example 4: Trend Analysis
```python
POST /api/analytics/query
{
  "query": "CTR trend over last 30 days by campaign",
  "tenant_id": "tenant_123"
}
```

---

## 🔧 STEP 5: FRONTEND INTEGRATION

```typescript
// File: frontend/src/services/analyticsApi.ts

export interface DynamicQueryRequest {
  query: string | {
    metric?: string;
    entity_type?: string;
    time_range?: string;
    limit?: number;
    group_by?: string[];
    filters?: Record<string, any>;
  };
  tenant_id: string;
}

export const analyticsApi = {
  /**
   * Execute dynamic business intelligence query
   */
  query: async (request: DynamicQueryRequest) => {
    const response = await apiClient.post('/api/analytics/query', request);
    return response.data;
  },
};
```

```typescript
// File: frontend/src/components/DynamicQueryBuilder.tsx

const DynamicQueryBuilder = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  
  const executeQuery = async () => {
    const response = await analyticsApi.query({
      query: query,
      tenant_id: getTenantId()
    });
    setResults(response);
  };
  
  return (
    <div>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="e.g., Top 5 campaigns by ROAS last quarter"
      />
      <button onClick={executeQuery}>Execute Query</button>
      {results && <QueryResults data={results} />}
    </div>
  );
};
```

---

## ✅ BENEFITS OF DYNAMIC SYSTEM

1. **No Hardcoding:** Handles any query without code changes
2. **Flexible:** Supports natural language and structured queries
3. **Extensible:** Easy to add new metrics, data sources, or query types
4. **Efficient:** Only fetches data from sources needed
5. **Maintainable:** Single endpoint handles all queries

---

## 📋 IMPLEMENTATION CHECKLIST

- [ ] Create QueryParser class
- [ ] Create DynamicAggregator class
- [ ] Implement data sources (Meta, HubSpot, Database)
- [ ] Create `/api/analytics/query` endpoint
- [ ] Add response formatting logic
- [ ] Create frontend query builder
- [ ] Add query caching (Redis)
- [ ] Add query validation
- [ ] Add error handling
- [ ] Add query logging/auditing

---

**This dynamic system can handle any business intelligence question without hardcoding!**

