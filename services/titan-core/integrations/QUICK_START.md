# HubSpot Integration - Quick Start Guide

**Get up and running in 5 minutes**

## 1. Install Dependencies

```bash
cd /home/user/geminivideo/services/titan-core
pip install hubspot-api-client>=8.0.0
```

## 2. Get HubSpot Access Token

1. Go to: https://app.hubspot.com/settings
2. Navigate to: Integrations → Private Apps
3. Click: "Create a private app"
4. Name it: "Titan Core Integration"
5. Grant these scopes:
   - ✅ `crm.objects.contacts.read`
   - ✅ `crm.objects.contacts.write`
   - ✅ `crm.objects.deals.read`
   - ✅ `crm.objects.deals.write`
6. Copy the access token

## 3. Set Environment Variable

```bash
export HUBSPOT_ACCESS_TOKEN="pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

## 4. Basic Usage

```python
from integrations.hubspot import HubSpotIntegration, DealStage

# Initialize
hubspot = HubSpotIntegration(access_token="your-token-here")

# Create/sync contact
contact_id = hubspot.sync_contact(
    email="customer@example.com",
    properties={
        "firstname": "John",
        "lastname": "Doe",
        "phone": "+1-555-0100"
    }
)

# Create deal
deal_id = hubspot.create_deal(
    contact_id=contact_id,
    deal_name="Video Production Package",
    amount=5000.00,
    stage=DealStage.APPOINTMENT_SCHEDULED
)

# Progress through pipeline
hubspot.update_deal_stage(deal_id, DealStage.QUALIFIED_TO_BUY)
hubspot.update_deal_stage(deal_id, DealStage.CLOSED_WON)

# Calculate sales cycle
days = hubspot.calculate_sales_cycle(contact_id)
print(f"Sales cycle: {days} days")
```

## 5. Track Ad Campaign ROAS

```python
# Attribute deal to Meta campaign
hubspot.attribute_deal_to_campaign(
    deal_id=deal_id,
    campaign_id="meta_video_q2_2024",
    meta_ad_id="120210987654321"
)

# Calculate true ROAS
roas = hubspot.calculate_actual_roas(
    campaign_id="meta_video_q2_2024",
    ad_spend=2500.00,
    include_pending=False  # Only closed-won deals
)

print(f"Campaign ROAS: {roas:.2f}x")
```

## 6. Run Example Code

```bash
export HUBSPOT_ACCESS_TOKEN="your-token"
python integrations/hubspot_example.py
```

## 7. Run Tests

```bash
export HUBSPOT_ACCESS_TOKEN="your-token"
python integrations/test_hubspot.py
```

## Common Use Cases

### Track Lead from Meta Ad to Close

```python
# 1. New lead from ad
contact_id = hubspot.sync_contact(
    email="lead@example.com",
    properties={"firstname": "Jane", "lastname": "Smith"}
)

# 2. Add UTM tracking
hubspot.add_utm_to_contact(
    contact_id,
    utm_campaign="meta_video_q2",
    utm_source="facebook",
    utm_medium="cpc"
)

# 3. Create deal
deal_id = hubspot.create_deal(
    contact_id=contact_id,
    deal_name="Enterprise Package",
    amount=10000.00
)

# 4. Link to Meta campaign
hubspot.attribute_deal_to_campaign(
    deal_id,
    campaign_id="meta_video_q2",
    meta_ad_id="120210123456789"
)

# 5. Close deal
hubspot.update_deal_stage(deal_id, DealStage.CLOSED_WON)
```

### Get Pipeline Insights

```python
# Total pipeline value
pipeline = hubspot.get_pipeline_value(by_stage=True)
for stage, value in pipeline.items():
    print(f"{stage}: ${value:,.2f}")

# Conversion rates
rates = hubspot.get_conversion_rates()
for stage_pair, rate in rates.items():
    print(f"{stage_pair}: {rate:.1f}%")

# Average sales cycle
avg = hubspot.get_avg_sales_cycle(days_back=90)
print(f"Avg cycle: {avg:.1f} days")
```

### Calculate Campaign Performance

```python
# Get all closed deals for campaign
deals = hubspot.get_closed_deals_by_campaign("meta_video_q2")

total_revenue = sum(d.amount for d in deals)
ad_spend = 5000.00

print(f"Deals closed: {len(deals)}")
print(f"Revenue: ${total_revenue:,.2f}")
print(f"Spend: ${ad_spend:,.2f}")
print(f"ROAS: {total_revenue / ad_spend:.2f}x")
```

## Troubleshooting

### Error: "Invalid access token"
- Verify token is correct
- Check token hasn't expired
- Ensure private app has required scopes

### Error: "Contact not found"
- Use `get_contact_by_email()` to search first
- Check email address is correct
- Verify contact exists in HubSpot

### Error: "Deal creation failed"
- Ensure contact_id exists
- Check amount is valid number
- Verify pipeline exists

## Next Steps

- Read full documentation: `HUBSPOT_README.md`
- Review examples: `hubspot_example.py`
- Run test suite: `test_hubspot.py`
- Check implementation summary: `AGENT_13_SUMMARY.md`

## Support

- HubSpot API Docs: https://developers.hubspot.com/docs/api/overview
- API Explorer: https://developers.hubspot.com/docs/api/overview#api-explorer
- SDK GitHub: https://github.com/HubSpot/hubspot-api-python

---

**Ready to track your 5-day sales cycle!** 🚀
