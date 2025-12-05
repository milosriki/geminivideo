# Google Ads API Reference

Complete API documentation for Google Ads integration service.

## Base URLs

- **Development**: `http://localhost:8084`
- **Gateway API**: `http://localhost:8000/api/google-ads`
- **Production**: `https://gateway-api.run.app/api/google-ads`

---

## Campaign Management

### Create Campaign

Create a new Google Ads campaign.

**Endpoint**: `POST /api/campaigns`

**Request Body**:
```json
{
  "name": "Black Friday 2024",
  "budget": 5000,
  "biddingStrategy": "MAXIMIZE_CONVERSIONS",
  "startDate": "2024-11-20",
  "endDate": "2024-11-30",
  "status": "PAUSED"
}
```

**Response**:
```json
{
  "status": "success",
  "campaign_id": "campaigns/customer/123456",
  "message": "Campaign created successfully"
}
```

**Via Gateway**:
```bash
curl -X POST http://localhost:8000/api/google-ads/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Black Friday 2024",
    "budget": 5000,
    "status": "PAUSED"
  }'
```

---

### Get Campaign Performance

Fetch performance metrics for a campaign.

**Endpoint**: `GET /api/performance/campaign/:campaignId`

**Query Parameters**:
- `startDate` (optional): Start date (YYYY-MM-DD)
- `endDate` (optional): End date (YYYY-MM-DD)

**Response**:
```json
{
  "status": "success",
  "campaign_id": "campaigns/customer/123456",
  "performance": {
    "impressions": 125000,
    "clicks": 3450,
    "cost": 2850.50,
    "conversions": 245,
    "ctr": 0.0276,
    "averageCpc": 0.826,
    "conversionRate": 0.071,
    "videoViews": 8500,
    "videoViewRate": 0.068
  },
  "date_range": "last_7_days"
}
```

**Via Gateway**:
```bash
curl http://localhost:8000/api/google-ads/performance/campaign/campaigns%2Fcustomer%2F123456?startDate=2024-11-01&endDate=2024-11-30
```

---

### Update Campaign Budget

Update the daily budget for a campaign.

**Endpoint**: `PATCH /api/campaigns/:campaignId/budget`

**Request Body**:
```json
{
  "budget": 7500
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Campaign campaigns/customer/123456 budget updated to 7500"
}
```

---

## Ad Group Management

### Create Ad Group

Create a new ad group within a campaign.

**Endpoint**: `POST /api/ad-groups`

**Request Body**:
```json
{
  "name": "Fitness Enthusiasts 25-45",
  "campaignId": "campaigns/customer/123456",
  "cpcBidMicros": 1500000,
  "status": "PAUSED"
}
```

**Note**: `cpcBidMicros` is in micros (1,000,000 micros = $1.00)

**Response**:
```json
{
  "status": "success",
  "ad_group_id": "customers/customer/adGroups/789",
  "message": "Ad Group created successfully"
}
```

---

## Creative Management

### Upload Video Creative

Upload a video to YouTube (required for Google Ads video ads).

**Endpoint**: `POST /api/upload-creative`

**Request Body**:
```json
{
  "videoPath": "/path/to/video.mp4",
  "title": "Amazing Product Demo",
  "description": "See how our product transforms lives"
}
```

**Response**:
```json
{
  "status": "success",
  "video_id": "yt_1234567890_abc",
  "youtube_url": "https://www.youtube.com/watch?v=yt_1234567890_abc",
  "message": "Video uploaded to YouTube successfully"
}
```

---

## Ad Management

### Create Video Ad (Complete Workflow)

Upload video and create ad in one request.

**Endpoint**: `POST /api/video-ads`

**Request Body**:
```json
{
  "videoPath": "/path/to/video.mp4",
  "campaignId": "campaigns/customer/123456",
  "adGroupId": "customers/customer/adGroups/789",
  "headline": "Transform Your Body in 30 Days",
  "description": "Join 10,000+ success stories. Get 50% off today!",
  "finalUrl": "https://example.com/offer"
}
```

**Response**:
```json
{
  "status": "success",
  "ad_id": "customers/customer/adGroupAds/101112",
  "video_id": "yt_1234567890_abc",
  "youtube_url": "https://www.youtube.com/watch?v=yt_1234567890_abc",
  "message": "Video ad created successfully"
}
```

---

### Create Ad from Existing Video

Create an ad using an already-uploaded YouTube video.

**Endpoint**: `POST /api/ads`

**Request Body**:
```json
{
  "name": "Product Demo Ad - Variant A",
  "adGroupId": "customers/customer/adGroups/789",
  "videoId": "yt_1234567890_abc",
  "headline": "Limited Time Offer",
  "description": "50% off for new customers",
  "callToAction": "SHOP_NOW",
  "finalUrl": "https://example.com/offer"
}
```

**Response**:
```json
{
  "status": "success",
  "ad_id": "customers/customer/adGroupAds/101112",
  "message": "Ad created successfully"
}
```

---

### Get Ad Performance

Fetch performance metrics for a specific ad.

**Endpoint**: `GET /api/performance/ad/:adId`

**Query Parameters**:
- `startDate` (optional): Start date (YYYY-MM-DD)
- `endDate` (optional): End date (YYYY-MM-DD)

**Response**:
```json
{
  "status": "success",
  "ad_id": "customers/customer/adGroupAds/101112",
  "performance": {
    "impressions": 45000,
    "clicks": 1250,
    "cost": 980.50,
    "conversions": 85,
    "ctr": 0.0278,
    "averageCpc": 0.784,
    "conversionRate": 0.068,
    "videoViews": 3200,
    "videoViewRate": 0.071
  },
  "date_range": "last_7_days"
}
```

---

### Update Ad Status

Enable or pause an ad.

**Endpoint**: `PATCH /api/ads/:adId/status`

**Request Body**:
```json
{
  "status": "ENABLED"
}
```

**Valid status values**: `ENABLED`, `PAUSED`

**Response**:
```json
{
  "status": "success",
  "message": "Ad customers/customer/adGroupAds/101112 status updated to ENABLED"
}
```

---

## Publishing Workflows

### Complete Publishing Workflow

Create campaign, ad group, and ad in one request.

**Endpoint**: `POST /api/publish`

**Request Body**:
```json
{
  "videoPath": "/path/to/video.mp4",
  "campaignName": "Black Friday Campaign",
  "budget": 5000,
  "adGroupName": "Fitness Enthusiasts",
  "cpcBidMicros": 1500000,
  "headline": "Transform Your Body",
  "description": "Join 10,000+ success stories",
  "finalUrl": "https://example.com/offer"
}
```

**Response**:
```json
{
  "status": "success",
  "campaign_id": "campaigns/customer/123456",
  "ad_group_id": "customers/customer/adGroups/789",
  "ad_id": "customers/customer/adGroupAds/101112",
  "video_id": "yt_1234567890_abc",
  "youtube_url": "https://www.youtube.com/watch?v=yt_1234567890_abc",
  "ad_status": "PAUSED",
  "message": "Ad created successfully (PAUSED)"
}
```

**Via Gateway**:
```bash
curl -X POST http://localhost:8000/api/google-ads/publish \
  -H "Content-Type: application/json" \
  -d '{
    "videoPath": "/path/to/video.mp4",
    "campaignName": "Black Friday Campaign",
    "budget": 5000,
    "adGroupName": "Fitness Enthusiasts",
    "cpcBidMicros": 1500000,
    "headline": "Transform Your Body",
    "description": "Join 10000+ success stories",
    "finalUrl": "https://example.com/offer"
  }'
```

---

## Account Management

### Get Account Info

Retrieve Google Ads account information.

**Endpoint**: `GET /api/account/info`

**Response**:
```json
{
  "status": "success",
  "account": {
    "id": "1234567890",
    "descriptive_name": "My Business Account",
    "currency_code": "USD",
    "time_zone": "America/New_York",
    "status": "ENABLED"
  }
}
```

---

## Health Check

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-05T10:30:00.000Z",
  "google_ads_configured": true
}
```

---

## Error Handling

All endpoints return errors in this format:

```json
{
  "error": "Failed to create campaign: Invalid budget value",
  "details": {
    "code": "INVALID_ARGUMENT",
    "message": "Budget must be positive"
  }
}
```

**Common HTTP Status Codes**:
- `200 OK` - Request successful
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limits

Google Ads API has the following rate limits:

- **Developer Token (test)**: 15,000 operations/day
- **Developer Token (production)**: Unlimited (fair use)
- **Per-customer limits**: 10,000 operations/day

**Best Practices**:
- Batch operations when possible
- Cache performance data
- Use webhooks for real-time updates
- Implement exponential backoff for retries

---

## Cost Units

Google Ads uses **micros** for monetary values:
- 1,000,000 micros = $1.00
- 1,500,000 micros = $1.50
- 10,000,000 micros = $10.00

**Example conversions**:
```javascript
// Dollars to micros
const budgetMicros = budgetDollars * 1_000_000;

// Micros to dollars
const budgetDollars = budgetMicros / 1_000_000;
```

---

## Multi-Platform Integration

### Meta + Google Ads Unified Publishing

```bash
# 1. Publish to Meta
curl -X POST http://localhost:8000/api/publish/meta \
  -H "Content-Type: application/json" \
  -d '{"ad_id": "uuid", "video_path": "/video.mp4", ...}'

# 2. Publish to Google Ads
curl -X POST http://localhost:8000/api/google-ads/publish \
  -H "Content-Type: application/json" \
  -d '{"videoPath": "/video.mp4", "campaignName": "Campaign", ...}'

# 3. Compare performance
curl http://localhost:8000/api/insights?ad_id=meta_ad_123
curl http://localhost:8000/api/google-ads/performance/ad/google_ad_456
```

---

## Testing

### Dry-Run Mode

The service runs in dry-run mode when credentials are not configured:

```bash
# Without credentials
PORT=8084 npm start

# Service returns mock responses
curl -X POST http://localhost:8084/api/publish \
  -H "Content-Type: application/json" \
  -d '{"videoPath": "/test.mp4", ...}'

# Response:
{
  "status": "dry_run",
  "message": "No Google Ads credentials provided - dry run mode",
  "would_create": {
    "campaign_id": "dry_run_campaign_123",
    "ad_group_id": "dry_run_ad_group_456",
    "ad_id": "dry_run_ad_789",
    "status": "PAUSED"
  }
}
```

---

## Production Checklist

- [ ] Set up Google Cloud project
- [ ] Enable Google Ads API
- [ ] Create OAuth2 credentials
- [ ] Get developer token (approved)
- [ ] Generate refresh token
- [ ] Configure environment variables
- [ ] Test campaign creation
- [ ] Test video upload to YouTube
- [ ] Test ad creation
- [ ] Verify performance metrics
- [ ] Set up monitoring and alerts
- [ ] Configure rate limit handling
- [ ] Implement retry logic
- [ ] Set up budget alerts
- [ ] Review ad policies compliance

---

## Support & Resources

- **Google Ads API Docs**: https://developers.google.com/google-ads/api/docs/start
- **Node.js Client Library**: https://github.com/Opteo/google-ads-api
- **Google Ads Forum**: https://groups.google.com/g/adwords-api
- **OAuth2 Playground**: https://developers.google.com/oauthplayground/
- **Status Dashboard**: https://ads.google.com/status/

---

## Related Services

- **Meta Publisher**: `/api/publish/meta`
- **Campaign Analytics**: `/api/metrics/diversification`
- **ML Predictions**: `/api/ml/predict-ctr`
- **Video Rendering**: `/api/render/remix`
