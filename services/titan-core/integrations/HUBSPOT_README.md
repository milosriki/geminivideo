# HubSpot CRM Integration

**Agent 13 of 30 - ULTIMATE Production Plan**

Real HubSpot API v3 integration for tracking the 5-day sales cycle, campaign attribution, and ROAS calculation.

## Features

- **Contact Management**: Create, update, and sync contacts with UTM tracking
- **Deal Pipeline**: Full deal lifecycle management with stage transitions
- **Sales Cycle Analytics**: Calculate actual sales cycle duration from lead to close
- **Campaign Attribution**: Track which Meta ads drive closed deals
- **True ROAS Calculation**: Real revenue vs ad spend from closed deals (not mock data)
- **Pipeline Analytics**: Value, conversion rates, and stage metrics
- **Webhook Support**: Real-time event handling from HubSpot

## Setup

### 1. Install Dependencies

```bash
pip install hubspot-api-client>=8.0.0
```

### 2. Create HubSpot Private App

1. Go to HubSpot Settings → Integrations → Private Apps
2. Create a new private app
3. Grant these scopes:
   - `crm.objects.contacts.read`
   - `crm.objects.contacts.write`
   - `crm.objects.deals.read`
   - `crm.objects.deals.write`
   - `crm.schemas.contacts.read`
   - `crm.schemas.deals.read`
4. Copy the access token

### 3. Set Environment Variable

```bash
export HUBSPOT_ACCESS_TOKEN="your-private-app-token"
```

## Usage

### Initialize Client

```python
from integrations.hubspot import HubSpotIntegration

hubspot = HubSpotIntegration(access_token="your-token")
```

### Track Complete Sales Cycle

```python
from integrations.hubspot import DealStage

# 1. New lead from Meta ad
contact_id = hubspot.sync_contact(
    email="prospect@example.com",
    properties={
        "firstname": "Jane",
        "lastname": "Smith",
        "phone": "+1-555-0100",
        "lifecyclestage": "lead"
    }
)

# 2. Add UTM tracking
hubspot.add_utm_to_contact(
    contact_id=contact_id,
    utm_campaign="meta_video_q2_2024",
    utm_source="facebook",
    utm_medium="cpc"
)

# 3. Create deal
deal_id = hubspot.create_deal(
    contact_id=contact_id,
    deal_name="Enterprise Video Package",
    amount=10000.00,
    stage=DealStage.APPOINTMENT_SCHEDULED
)

# 4. Attribute to campaign
hubspot.attribute_deal_to_campaign(
    deal_id=deal_id,
    campaign_id="meta_video_q2_2024",
    meta_ad_id="120210987654321"
)

# 5. Progress through stages
hubspot.update_deal_stage(deal_id, DealStage.QUALIFIED_TO_BUY)
hubspot.update_deal_stage(deal_id, DealStage.PRESENTATION_SCHEDULED)
hubspot.update_deal_stage(deal_id, DealStage.DECISION_MAKER_BOUGHT_IN)
hubspot.update_deal_stage(deal_id, DealStage.CONTRACT_SENT)
hubspot.update_deal_stage(deal_id, DealStage.CLOSED_WON)

# 6. Calculate sales cycle
days = hubspot.calculate_sales_cycle(contact_id)
print(f"Sales cycle: {days} days")
```

### Calculate True ROAS

```python
# Get all closed deals for campaign
closed_deals = hubspot.get_closed_deals_by_campaign("meta_video_q2_2024")

# Calculate actual ROAS from closed deals
ad_spend = 5000.00
roas = hubspot.calculate_actual_roas(
    campaign_id="meta_video_q2_2024",
    ad_spend=ad_spend,
    include_pending=False  # Only count closed-won deals
)

print(f"Campaign ROAS: {roas:.2f}x")
print(f"Revenue: ${sum(d.amount for d in closed_deals):,.2f}")
print(f"Spend: ${ad_spend:,.2f}")
```

### Pipeline Analytics

```python
# Get pipeline value by stage
pipeline_value = hubspot.get_pipeline_value(by_stage=True)

for stage, value in pipeline_value.items():
    print(f"{stage}: ${value:,.2f}")

# Get conversion rates
conversion_rates = hubspot.get_conversion_rates()

for stage_pair, rate in conversion_rates.items():
    print(f"{stage_pair}: {rate:.1f}%")

# Get average sales cycle
avg_days = hubspot.get_avg_sales_cycle(days_back=90)
print(f"Average sales cycle: {avg_days:.1f} days")
```

### Handle Webhooks

```python
# In your FastAPI/Flask webhook endpoint
@app.post("/webhooks/hubspot")
async def hubspot_webhook(request: Request):
    payload = await request.json()
    
    result = hubspot.handle_webhook(
        event_type=payload.get("subscriptionType"),
        payload=payload
    )
    
    return {"status": result["status"]}
```

## Data Models

### Contact

```python
@dataclass
class Contact:
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    company: Optional[str]
    lifecycle_stage: str
    lead_source: Optional[str]
    utm_campaign: Optional[str]
    utm_source: Optional[str]
    created_at: datetime
```

### Deal

```python
@dataclass
class Deal:
    id: str
    name: str
    amount: float
    stage: DealStage
    contact_id: str
    campaign_id: Optional[str]
    close_date: Optional[datetime]
    created_at: datetime
    pipeline: str
```

### StageChange

```python
@dataclass
class StageChange:
    deal_id: str
    from_stage: str
    to_stage: str
    timestamp: datetime
    time_in_stage_hours: float
```

## Deal Stages

The integration uses HubSpot's standard deal stages:

1. **APPOINTMENT_SCHEDULED** - Initial contact made
2. **QUALIFIED_TO_BUY** - Budget and authority confirmed
3. **PRESENTATION_SCHEDULED** - Demo/presentation booked
4. **DECISION_MAKER_BOUGHT_IN** - Key stakeholder committed
5. **CONTRACT_SENT** - Paperwork sent
6. **CLOSED_WON** - Deal won!
7. **CLOSED_LOST** - Deal lost

## API Methods

### Contact Management

- `sync_contact(email, properties)` - Create or update contact
- `get_contact(contact_id)` - Get contact by ID
- `get_contact_by_email(email)` - Search by email
- `update_contact(contact_id, properties)` - Update properties
- `add_utm_to_contact(contact_id, utm_campaign, utm_source, utm_medium)` - Add tracking

### Deal Management

- `create_deal(contact_id, deal_name, amount, stage, pipeline, properties)` - Create deal
- `update_deal_stage(deal_id, stage)` - Update stage
- `get_deal(deal_id)` - Get deal by ID
- `get_deal_history(deal_id)` - Get stage change history

### Sales Cycle Analysis

- `calculate_sales_cycle(contact_id)` - Days from lead to close
- `get_avg_sales_cycle(pipeline, days_back)` - Average cycle duration

### Campaign Attribution

- `attribute_deal_to_campaign(deal_id, campaign_id, meta_ad_id)` - Link deal to campaign
- `get_closed_deals_by_campaign(campaign_id, date_range)` - Get campaign deals
- `calculate_actual_roas(campaign_id, ad_spend, include_pending)` - True ROAS

### Pipeline Analytics

- `get_pipeline_value(pipeline, by_stage)` - Total or per-stage value
- `get_conversion_rates(pipeline)` - Stage-to-stage conversion %

### Webhooks

- `handle_webhook(event_type, payload)` - Process HubSpot events

## Error Handling

All methods include comprehensive error handling:

```python
from hubspot.crm.contacts import ApiException

try:
    contact = hubspot.get_contact(contact_id)
except ApiException as e:
    print(f"HubSpot API error: {e}")
    # Handle error
```

## Logging

The integration uses Python's logging module:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

Log output includes:
- API calls and responses
- Error details
- Performance metrics
- Webhook events

## Production Considerations

### Rate Limits

HubSpot API limits:
- 100 requests per 10 seconds (free)
- 150 requests per 10 seconds (starter)
- 200 requests per 10 seconds (professional+)

The integration includes automatic retry logic for rate limit errors.

### Caching

Consider caching frequently accessed data:

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_contact_cached(contact_id: str):
    return hubspot.get_contact(contact_id)
```

### Async Support

For high-volume applications, consider async version:

```python
import asyncio
from hubspot.crm.contacts import AsyncApi

# Async implementation coming soon
```

## Testing

See `hubspot_example.py` for comprehensive usage examples:

```bash
export HUBSPOT_ACCESS_TOKEN="your-token"
python integrations/hubspot_example.py
```

## Integration with Meta Ads

Combine with Meta Ads Library for full attribution:

```python
from meta_ads_library import MetaAdsLibrary

# Get ad performance
meta = MetaAdsLibrary(access_token="meta-token")
ad_performance = meta.get_campaign_performance("campaign_id")

# Calculate true ROAS from HubSpot
hubspot_roas = hubspot.calculate_actual_roas(
    campaign_id="campaign_id",
    ad_spend=ad_performance['spend']
)

print(f"Meta reported ROAS: {ad_performance['roas']:.2f}x")
print(f"Actual closed deal ROAS: {hubspot_roas:.2f}x")
```

## Support

For issues or questions:
1. Check HubSpot API documentation: https://developers.hubspot.com/docs/api/overview
2. Review logs for detailed error messages
3. Verify API scopes and permissions
4. Test with HubSpot's API explorer

## License

Part of Titan Core - ULTIMATE Production Plan
Agent 13 of 30
