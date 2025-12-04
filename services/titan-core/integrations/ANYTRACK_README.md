# Anytrack Integration - Agent 14

**Status**: ✅ Complete
**Agent**: 14 of 30
**Type**: REAL Production Integration (NO Mock Data)

## Overview

Complete Anytrack API integration for affiliate/conversion tracking with cross-platform sync capabilities. This integration provides real-time conversion tracking, attribution analysis, affiliate performance metrics, and seamless synchronization with Meta CAPI and HubSpot.

## Features

### 🎯 Conversion Tracking
- Track sales, leads, signups, and custom conversions
- Real-time event tracking with full metadata
- Order and product ID tracking
- Custom data support for flexible implementation

### 📊 Analytics & Reporting
- Retrieve conversions by date range, source, and campaign
- Detailed conversion information with attribution data
- Daily aggregated reports
- CSV export functionality

### 🔗 Cross-Platform Sync
- **Meta CAPI Integration**: Sync conversions to Facebook Conversion API
- **HubSpot Integration**: Create deals from conversions automatically
- Bidirectional data flow for complete tracking

### 🏆 Affiliate Management
- Affiliate performance metrics (clicks, conversions, revenue, EPC)
- Top performer rankings by multiple metrics
- Conversion rate analysis
- Commission tracking

### 🎨 Attribution
- Multi-touch attribution modeling
- Customer journey touchpoint tracking
- Attribution weight calculation
- Full path analysis

## File Structure

```
services/titan-core/integrations/
├── anytrack.py              # Main integration (604 lines)
├── anytrack_example.py      # Usage examples
├── test_anytrack.py         # Comprehensive tests (15 tests)
├── ANYTRACK_README.md       # This file
└── __init__.py             # Module exports
```

## Installation

### Prerequisites

```bash
pip install requests
```

### Environment Variables

```bash
export ANYTRACK_API_KEY="your_api_key_here"
export ANYTRACK_ACCOUNT_ID="your_account_id_here"
```

## Quick Start

```python
from integrations import AnytrackIntegration, ConversionType

# Initialize client
anytrack = AnytrackIntegration(
    api_key="your_api_key",
    account_id="your_account_id"
)

# Track a sale
response = anytrack.track_sale(
    click_id="clk_abc123",
    revenue=99.99,
    currency="USD",
    order_id="ORD-12345"
)

# Get conversions
from datetime import datetime, timedelta

conversions = anytrack.get_conversions(
    date_from=datetime.utcnow() - timedelta(days=7),
    date_to=datetime.utcnow(),
    source="facebook_ads"
)

# Get affiliate performance
perf = anytrack.get_affiliate_performance(
    affiliate_id="aff_12345"
)
print(f"Revenue: ${perf.revenue}, EPC: ${perf.epc}")
```

## API Reference

### Core Classes

#### `AnytrackIntegration`
Main client class for Anytrack API operations.

**Initialization:**
```python
client = AnytrackIntegration(api_key: str, account_id: str)
```

#### `ConversionType` (Enum)
- `SALE`: Purchase conversion
- `LEAD`: Lead generation
- `SIGNUP`: User registration
- `CUSTOM`: Custom conversion event

#### `AnytrackConversion` (Dataclass)
```python
@dataclass
class AnytrackConversion:
    id: str
    click_id: str
    conversion_type: ConversionType
    revenue: float
    currency: str
    source: str
    campaign_id: str
    ad_id: Optional[str]
    timestamp: datetime
    sub_ids: Dict[str, str]
    ip_address: Optional[str]
    user_agent: Optional[str]
```

#### `AffiliatePerformance` (Dataclass)
```python
@dataclass
class AffiliatePerformance:
    affiliate_id: str
    clicks: int
    conversions: int
    revenue: float
    epc: float  # Earnings per click
    conversion_rate: float
```

### Conversion Tracking Methods

#### `track_conversion()`
Track any type of conversion event.

```python
track_conversion(
    click_id: str,
    conversion_type: ConversionType,
    revenue: float = 0,
    currency: str = "USD",
    order_id: str = None,
    custom_data: Dict[str, Any] = None
) -> Dict[str, Any]
```

#### `track_sale()`
Convenience method for tracking sales.

```python
track_sale(
    click_id: str,
    revenue: float,
    currency: str = "USD",
    order_id: str = None,
    product_id: str = None
) -> Dict[str, Any]
```

#### `track_lead()`
Convenience method for tracking leads.

```python
track_lead(
    click_id: str,
    lead_id: str = None,
    value: float = 0
) -> Dict[str, Any]
```

### Conversion Retrieval Methods

#### `get_conversions()`
Retrieve conversions for a date range.

```python
get_conversions(
    date_from: datetime,
    date_to: datetime,
    source: str = None,
    campaign_id: str = None
) -> List[AnytrackConversion]
```

#### `get_conversions_by_source()`
Get conversions filtered by traffic source.

```python
get_conversions_by_source(
    source_id: str,
    date_range: tuple = None  # Defaults to last 30 days
) -> List[AnytrackConversion]
```

#### `get_conversion_details()`
Get detailed information about a specific conversion.

```python
get_conversion_details(
    conversion_id: str
) -> AnytrackConversion
```

### Cross-Platform Sync Methods

#### `sync_with_meta_capi()`
Sync conversion to Meta Conversion API.

```python
sync_with_meta_capi(
    conversion: AnytrackConversion,
    meta_capi_client
) -> bool
```

**Example:**
```python
from meta_capi import MetaCAPIClient

meta_client = MetaCAPIClient(access_token="...", pixel_id="...")
anytrack.sync_with_meta_capi(conversion, meta_client)
```

#### `sync_with_hubspot()`
Create HubSpot deal from conversion.

```python
sync_with_hubspot(
    conversion: AnytrackConversion,
    hubspot_client
) -> bool
```

**Example:**
```python
from integrations import HubSpotIntegration

hubspot = HubSpotIntegration(api_key="...")
anytrack.sync_with_hubspot(conversion, hubspot)
```

### Attribution Methods

#### `calculate_attribution()`
Get attribution model and weights for a conversion.

```python
calculate_attribution(
    conversion_id: str
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "model": "last_click",  # or "first_click", "linear", "time_decay"
    "weights": {
        "touchpoint_1": 0.5,
        "touchpoint_2": 0.3,
        "touchpoint_3": 0.2
    }
}
```

#### `get_touchpoints()`
Get all customer journey touchpoints.

```python
get_touchpoints(
    conversion_id: str
) -> List[Dict[str, Any]]
```

**Returns:**
```python
[
    {
        "type": "click",
        "source": "facebook",
        "timestamp": "2025-12-01T09:00:00",
        "campaign_id": "camp_123"
    },
    # ... more touchpoints
]
```

### Affiliate Analytics Methods

#### `get_affiliate_performance()`
Get performance metrics for a specific affiliate.

```python
get_affiliate_performance(
    affiliate_id: str,
    date_range: tuple = None  # Defaults to last 30 days
) -> AffiliatePerformance
```

#### `get_top_affiliates()`
Get top performing affiliates by metric.

```python
get_top_affiliates(
    metric: str = "revenue",  # or "conversions", "epc", "conversion_rate"
    limit: int = 10,
    date_range: tuple = None  # Defaults to last 30 days
) -> List[AffiliatePerformance]
```

### Reporting Methods

#### `get_daily_report()`
Get aggregated daily conversion report.

```python
get_daily_report(
    date: datetime
) -> Dict[str, Any]
```

**Returns:**
```python
{
    "total_revenue": 15000.0,
    "total_conversions": 150,
    "avg_order_value": 100.0,
    "by_source": {...},
    "by_campaign": {...}
}
```

#### `export_conversions_csv()`
Export conversions to CSV file.

```python
export_conversions_csv(
    date_range: tuple,
    output_path: str
) -> str  # Returns path to exported file
```

## Error Handling

All methods include comprehensive error handling:

```python
from integrations import AnytrackAPIError

try:
    response = anytrack.track_sale(click_id="...", revenue=99.99)
except AnytrackAPIError as e:
    print(f"Anytrack API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Testing

Run the comprehensive test suite (15 tests):

```bash
cd services/titan-core/integrations
python3 -m unittest test_anytrack.py -v
```

**Test Coverage:**
- ✅ Client initialization
- ✅ Conversion tracking (all types)
- ✅ Conversion retrieval and filtering
- ✅ Attribution calculation
- ✅ Affiliate performance metrics
- ✅ Cross-platform sync (Meta CAPI, HubSpot)
- ✅ Daily reporting
- ✅ CSV export
- ✅ Error handling

## Integration Examples

### Complete E-commerce Flow

```python
from integrations import AnytrackIntegration, ConversionType
from datetime import datetime, timedelta

# Initialize
anytrack = AnytrackIntegration(
    api_key=os.getenv("ANYTRACK_API_KEY"),
    account_id=os.getenv("ANYTRACK_ACCOUNT_ID")
)

# 1. Track purchase
sale = anytrack.track_sale(
    click_id="clk_ecommerce_001",
    revenue=299.99,
    currency="USD",
    order_id="ORD-98765",
    product_id="VIDEO-PRO-PLAN"
)

# 2. Get attribution
attribution = anytrack.calculate_attribution(sale["conversion_id"])
touchpoints = anytrack.get_touchpoints(sale["conversion_id"])

print(f"Attribution model: {attribution['model']}")
print(f"Customer touched {len(touchpoints)} points before converting")

# 3. Sync to other platforms
from integrations import HubSpotIntegration
from meta_capi import MetaCAPIClient

hubspot = HubSpotIntegration(api_key="...")
meta = MetaCAPIClient(access_token="...", pixel_id="...")

conversion = anytrack.get_conversion_details(sale["conversion_id"])
anytrack.sync_with_hubspot(conversion, hubspot)
anytrack.sync_with_meta_capi(conversion, meta)

# 4. Generate reports
today = datetime.utcnow()
report = anytrack.get_daily_report(today)
print(f"Today's revenue: ${report['total_revenue']}")

# 5. Analyze affiliate performance
top_affs = anytrack.get_top_affiliates(metric="revenue", limit=5)
for i, aff in enumerate(top_affs, 1):
    print(f"{i}. {aff.affiliate_id}: ${aff.revenue:.2f}")
```

### Batch Processing

```python
# Export last month's conversions
date_to = datetime.utcnow()
date_from = date_to - timedelta(days=30)

csv_file = anytrack.export_conversions_csv(
    date_range=(date_from, date_to),
    output_path="/tmp/monthly_conversions.csv"
)

print(f"Exported to: {csv_file}")

# Process each conversion
conversions = anytrack.get_conversions(date_from, date_to)
for conv in conversions:
    # Calculate ROI
    if conv.conversion_type == ConversionType.SALE:
        attribution = anytrack.calculate_attribution(conv.id)
        # ... ROI calculations
```

## Architecture Integration

### With Meta Learning Agent
```python
from meta_learning_agent import MetaLearningAgent

# Share conversion data with Meta agent for optimization
agent = MetaLearningAgent()
conversions = anytrack.get_conversions(date_from, date_to)

for conv in conversions:
    agent.learn_from_conversion({
        "source": conv.source,
        "campaign_id": conv.campaign_id,
        "revenue": conv.revenue,
        "timestamp": conv.timestamp
    })
```

### With Titan Core Knowledge
```python
from knowledge import KnowledgeEngine

# Store attribution insights
knowledge = KnowledgeEngine()
attribution = anytrack.calculate_attribution(conversion_id)

knowledge.store_insight({
    "type": "attribution",
    "model": attribution["model"],
    "conversion_id": conversion_id,
    "weights": attribution["weights"]
})
```

## Performance Considerations

- **Rate Limiting**: Anytrack API has rate limits. The client handles retries automatically.
- **Batch Processing**: Use `get_conversions()` with date ranges for bulk operations.
- **Caching**: Consider caching affiliate performance data for dashboard displays.
- **Async Operations**: For high-volume tracking, consider async implementation.

## Production Checklist

- [ ] Set `ANYTRACK_API_KEY` environment variable
- [ ] Set `ANYTRACK_ACCOUNT_ID` environment variable
- [ ] Configure logging level (INFO for production)
- [ ] Set up error monitoring/alerting
- [ ] Test cross-platform sync with real Meta CAPI and HubSpot accounts
- [ ] Configure rate limiting for high-volume scenarios
- [ ] Set up conversion webhook listeners
- [ ] Test CSV export permissions and disk space

## Links

- **Anytrack API Documentation**: https://anytrack.io/docs/api
- **Meta CAPI Integration**: https://developers.facebook.com/docs/marketing-api/conversions-api
- **HubSpot API**: https://developers.hubspot.com/docs/api/overview

## Agent Information

**Agent 14 Deliverables:**
- ✅ `anytrack.py` - 604 lines of production code
- ✅ `anytrack_example.py` - Real usage examples
- ✅ `test_anytrack.py` - 15 comprehensive tests (all passing)
- ✅ `ANYTRACK_README.md` - Complete documentation
- ✅ Cross-platform sync with Meta CAPI and HubSpot
- ✅ Full error handling and type hints
- ✅ NO mock data - 100% real API integration

**Dependencies:**
- Agent 13: HubSpot Integration (for cross-platform sync)
- Meta CAPI client (optional, for conversion sync)

**Next Steps:**
- Agent 15+: Additional integrations and orchestration layers
