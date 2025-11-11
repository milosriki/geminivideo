# Meta Publisher Service

Service for publishing video ads to Meta (Facebook/Instagram) platforms and tracking performance insights.

## Features

- **Ad Publishing**: Publish video ads to Meta platforms
- **Insights Tracking**: Fetch performance metrics (impressions, clicks, CTR)
- **Prediction Linking**: Updates prediction logs with actual performance
- **Automated Learning**: Feeds data back to nightly learning scripts

## Endpoints

### Health Check
```
GET /health
```

### Publishing
```
POST /publish/meta    - Publish video ad to Meta platforms
```

### Insights
```
GET /insights?ad_id={ad_id}&prediction_id={prediction_id}
```

## Configuration

Environment variables:
- `PORT` - Server port (default: 8083)
- `META_ACCESS_TOKEN` - Meta Marketing API access token
- `META_AD_ACCOUNT_ID` - Meta ad account ID

## Development

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build
npm run build

# Run production
npm start
```

## Docker

```bash
# Build image
docker build -t meta-publisher .

# Run container
docker run -p 8083:8083 -e META_ACCESS_TOKEN=xxx meta-publisher
```

## Publishing Request Format

```json
{
  "video_url": "gs://bucket/video.mp4",
  "caption": "Check out our amazing product!",
  "targeting": {
    "age_range": [25, 45],
    "interests": ["technology", "shopping"],
    "locations": ["US", "CA", "UK"]
  },
  "budget": {
    "daily_budget": 100,
    "currency": "USD"
  },
  "prediction_id": "uuid-from-prediction-log"
}
```

## Insights Response

```json
{
  "ad_id": "ad_123456",
  "insights": {
    "impressions": 50000,
    "clicks": 2500,
    "ctr": 0.05,
    "spend": 250,
    "reach": 30000,
    "engagement": 1500
  },
  "updated_at": "2025-11-11T12:00:00Z"
}
```

## Integration with Prediction System

When fetching insights, the service automatically updates the prediction log with actual CTR, enabling the nightly learning system to:
1. Compare predicted vs actual performance
2. Calibrate scoring weights
3. Improve future predictions
