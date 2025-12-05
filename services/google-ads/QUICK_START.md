# Google Ads Integration - Quick Start Guide

**5-Minute Setup for Elite Marketers**

---

## Prerequisites

- [ ] Google Cloud project with Google Ads API enabled
- [ ] OAuth2 credentials (Client ID + Secret)
- [ ] Developer Token (approved)
- [ ] Refresh Token
- [ ] Customer ID (10 digits)

---

## Installation

### 1. Configure Environment

```bash
cd /services/google-ads
cp .env.example .env
nano .env  # Fill in your credentials
```

**Required variables**:
```bash
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxx
GOOGLE_DEVELOPER_TOKEN=xxxxx
GOOGLE_REFRESH_TOKEN=xxxxx
GOOGLE_ADS_CUSTOMER_ID=1234567890
```

### 2. Install & Run

```bash
# Install dependencies
npm install

# Development mode
npm run dev

# Production mode
npm run build && npm start

# Docker
docker build -t google-ads .
docker run -p 8084:8084 --env-file .env google-ads
```

### 3. Test

```bash
# Health check
curl http://localhost:8084/health

# Account info
curl http://localhost:8084/api/account/info

# Integration test
./test-integration.sh
```

---

## Common Operations

### Create Campaign

```bash
curl -X POST http://localhost:8084/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Black Friday 2024",
    "budget": 5000,
    "status": "PAUSED"
  }'
```

### Upload Video & Create Ad

```bash
curl -X POST http://localhost:8084/api/video-ads \
  -H "Content-Type: application/json" \
  -d '{
    "videoPath": "/path/to/video.mp4",
    "campaignId": "campaigns/customer/123456",
    "adGroupId": "customers/customer/adGroups/789",
    "headline": "Transform Your Body",
    "finalUrl": "https://example.com/offer"
  }'
```

### Get Performance

```bash
curl "http://localhost:8084/api/performance/campaign/campaigns%2Fcustomer%2F123456"
```

### Complete Workflow (All-in-One)

```bash
curl -X POST http://localhost:8084/api/publish \
  -H "Content-Type: application/json" \
  -d '{
    "videoPath": "/path/to/video.mp4",
    "campaignName": "My Campaign",
    "budget": 5000,
    "adGroupName": "My Ad Group",
    "cpcBidMicros": 1500000,
    "headline": "Amazing Offer",
    "finalUrl": "https://example.com"
  }'
```

---

## Via Gateway API

All endpoints also available through gateway:

```bash
# Create campaign
curl -X POST http://localhost:8000/api/google-ads/campaigns \
  -H "Content-Type: application/json" \
  -d '{"name": "Campaign", "budget": 5000}'

# Get performance
curl http://localhost:8000/api/google-ads/performance/ad/test_123

# Publish
curl -X POST http://localhost:8000/api/google-ads/publish \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## Multi-Platform Publishing

### Publish to Both Meta + Google Ads

```javascript
// 1. Meta (Facebook/Instagram)
await fetch('http://localhost:8000/api/publish/meta', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    ad_id: 'uuid-here',
    video_path: '/video.mp4',
    // ...
  })
});

// 2. Google Ads (YouTube/Display)
await fetch('http://localhost:8000/api/google-ads/publish', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    videoPath: '/video.mp4',
    campaignName: 'My Campaign',
    budget: 5000,
    // ...
  })
});

// 3. Compare Performance
const [metaData, googleData] = await Promise.all([
  fetch('http://localhost:8000/api/insights?ad_id=meta_123'),
  fetch('http://localhost:8000/api/google-ads/performance/ad/google_456')
]);

console.log('Meta CTR:', metaData.ctr);
console.log('Google CTR:', googleData.performance.ctr);
```

---

## Troubleshooting

### Issue: "Google Ads SDK not configured"

**Solution**: Check environment variables
```bash
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_ADS_CUSTOMER_ID
# Should output your credentials, not empty
```

### Issue: "Invalid refresh token"

**Solution**: Regenerate refresh token
1. Go to https://developers.google.com/oauthplayground/
2. Select Google Ads API scope
3. Authorize and exchange authorization code
4. Copy refresh token to .env

### Issue: "Developer token not approved"

**Solution**: Apply for production access
1. Go to Google Ads account
2. Tools & Settings > API Center
3. Apply for developer token
4. May take 2-3 business days

### Issue: Port 8084 already in use

**Solution**: Change port
```bash
PORT=8085 npm start
```

### Issue: Video upload fails

**Solution**: Videos must be hosted on YouTube first
- Google Ads requires YouTube hosting
- Use `/api/upload-creative` endpoint first
- Then create ad with returned video_id

---

## Cost Units (Important!)

Google Ads uses **micros** for currency:

```
1,000,000 micros = $1.00
1,500,000 micros = $1.50
10,000,000 micros = $10.00
```

**Examples**:
- Daily budget of $100: `"budget": 100` (in API)
- CPC bid of $1.50: `"cpcBidMicros": 1500000`
- Total spend of $2,850.50: `"cost_micros": 2850500000`

**Conversions**:
```javascript
// Dollars to micros
const micros = dollars * 1_000_000;

// Micros to dollars
const dollars = micros / 1_000_000;
```

---

## File Structure

```
google-ads/
├── src/
│   ├── google/
│   │   └── google-ads-manager.ts    # Core client
│   └── index.ts                      # API server
├── .env.example                      # Config template
├── API_REFERENCE.md                  # Full API docs
├── IMPLEMENTATION_SUMMARY.md         # Technical details
├── QUICK_START.md                    # This file
└── test-integration.sh               # Test script
```

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/campaigns` | POST | Create campaign |
| `/api/ad-groups` | POST | Create ad group |
| `/api/upload-creative` | POST | Upload video to YouTube |
| `/api/video-ads` | POST | Create video ad |
| `/api/ads` | POST | Create ad from existing video |
| `/api/publish` | POST | Complete workflow |
| `/api/performance/campaign/:id` | GET | Campaign metrics |
| `/api/performance/ad/:id` | GET | Ad metrics |
| `/api/ads/:id/status` | PATCH | Update ad status |
| `/api/campaigns/:id/budget` | PATCH | Update budget |
| `/api/account/info` | GET | Account details |

---

## Production Checklist

- [ ] Google Ads credentials configured
- [ ] Developer token approved
- [ ] Service deployed (Cloud Run, etc.)
- [ ] Gateway API updated with service URL
- [ ] Health checks passing
- [ ] Test campaign created
- [ ] Test video uploaded
- [ ] Performance metrics verified
- [ ] Monitoring configured
- [ ] Budget alerts set up

---

## Next Steps

1. **Configure credentials** (see .env.example)
2. **Deploy service** (Docker or Cloud Run)
3. **Update gateway** (set GOOGLE_ADS_URL)
4. **Test integration** (run test-integration.sh)
5. **Create first campaign**
6. **Monitor performance**
7. **Scale to production**

---

## Support

- **Full API Docs**: See `API_REFERENCE.md`
- **Technical Details**: See `IMPLEMENTATION_SUMMARY.md`
- **Google Ads API**: https://developers.google.com/google-ads/api
- **OAuth2 Setup**: https://developers.google.com/oauthplayground/

---

**Ready to publish to Google Ads!** 🚀
