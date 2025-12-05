# Google Ads Publisher Service

**Agent 13** - Real Google Ads API integration for campaign creation, video ad publishing, and performance tracking.

## Features

- **OAuth2 Authentication** - Secure Google Ads API access
- **Campaign Management** - Create and manage Google Ads campaigns
- **Video Ad Creation** - Upload videos to YouTube and create video ads
- **Performance Metrics** - Fetch real-time campaign, ad group, and ad performance
- **Budget Control** - Update campaign budgets dynamically
- **Multi-Format Support** - Video ads, display ads, responsive ads

## API Endpoints

### Campaign Management
- `POST /api/campaigns` - Create new campaign
- `GET /api/performance/campaign/:campaignId` - Get campaign performance
- `PATCH /api/campaigns/:campaignId/budget` - Update campaign budget

### Ad Group Management
- `POST /api/ad-groups` - Create ad group
- `GET /api/performance/ad-group/:adGroupId` - Get ad group performance

### Creative Management
- `POST /api/upload-creative` - Upload video to YouTube
- `POST /api/assets/upload` - Upload image/video assets

### Ad Management
- `POST /api/video-ads` - Create video ad (complete workflow)
- `POST /api/ads` - Create ad from existing YouTube video
- `GET /api/performance/ad/:adId` - Get ad performance
- `PATCH /api/ads/:adId/status` - Update ad status (ENABLED/PAUSED)

### Publishing
- `POST /api/publish` - Complete publishing workflow (campaign + ad group + ad)

### Account
- `GET /api/account/info` - Get Google Ads account information
- `GET /health` - Health check

## Environment Variables

```bash
# Google Ads API Credentials
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_DEVELOPER_TOKEN=your_developer_token
GOOGLE_REFRESH_TOKEN=your_refresh_token
GOOGLE_ADS_CUSTOMER_ID=1234567890

# Service Configuration
PORT=8084
ALLOWED_ORIGINS=http://localhost:3000,https://geminivideo.vercel.app
```

## Google Ads API Setup

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Ads API

### 2. Create OAuth2 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Create OAuth 2.0 Client ID
3. Set authorized redirect URIs
4. Note your Client ID and Client Secret

### 3. Get Developer Token
1. Go to [Google Ads Account](https://ads.google.com/)
2. Navigate to Tools & Settings > Setup > API Center
3. Apply for developer token (may require approval)

### 4. Generate Refresh Token
```bash
# Use Google OAuth2 Playground or implement OAuth flow
# https://developers.google.com/oauthplayground/
```

### 5. Get Customer ID
- Found in your Google Ads account (top right corner)
- Format: 1234567890 (10 digits, no dashes)

## Development

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Docker

```bash
# Build image
docker build -t google-ads .

# Run container
docker run -p 8084:8084 \
  -e GOOGLE_CLIENT_ID=your_client_id \
  -e GOOGLE_CLIENT_SECRET=your_client_secret \
  -e GOOGLE_DEVELOPER_TOKEN=your_token \
  -e GOOGLE_REFRESH_TOKEN=your_refresh_token \
  -e GOOGLE_ADS_CUSTOMER_ID=1234567890 \
  google-ads
```

## Example Usage

### Create Campaign
```bash
curl -X POST http://localhost:8084/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Black Friday Campaign",
    "budget": 5000,
    "status": "PAUSED"
  }'
```

### Create Video Ad
```bash
curl -X POST http://localhost:8084/api/video-ads \
  -H "Content-Type: application/json" \
  -d '{
    "videoPath": "/path/to/video.mp4",
    "campaignId": "campaign_123",
    "adGroupId": "adgroup_456",
    "headline": "Amazing Product!",
    "description": "Get 50% off today",
    "finalUrl": "https://example.com/offer"
  }'
```

### Get Performance Metrics
```bash
curl http://localhost:8084/api/performance/campaign/campaign_123?startDate=2023-12-01&endDate=2023-12-31
```

## Integration with Gateway API

The Google Ads service is proxied through the gateway-api at:
- Base URL: `/api/google-ads/*`

## Production Considerations

1. **Video Hosting** - Videos must be uploaded to YouTube first
2. **Budget Limits** - Set daily budget caps to prevent overspending
3. **Ad Approval** - Google Ads reviews all ads before serving
4. **Rate Limits** - Google Ads API has rate limits (respect them)
5. **Error Handling** - Implement retry logic for API failures
6. **Monitoring** - Track API usage and quota limits

## Multi-Platform Strategy

For €5M investment-grade platform:
- **Meta Ads** - Facebook, Instagram (Reels focus)
- **Google Ads** - YouTube, Display Network, Search
- **Unified Dashboard** - Single pane for all platforms
- **Cross-Platform Analytics** - Compare performance across networks

## Security

- OAuth2 tokens stored securely
- Never commit credentials to Git
- Use environment variables for all secrets
- Implement rate limiting
- Audit all publishing actions

## Support

For Google Ads API issues:
- [Google Ads API Documentation](https://developers.google.com/google-ads/api/docs/start)
- [Google Ads API Forum](https://groups.google.com/g/adwords-api)
