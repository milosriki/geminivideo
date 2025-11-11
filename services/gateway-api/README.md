# Gateway API

Gateway API service for the AI Ad Intelligence & Creation Suite. Provides unified access to knowledge management, scoring, and routing to backend services.

## Features

- **Knowledge Management**: Upload, activate, and manage knowledge base files
- **Scoring Engine**: Psychology, hook strength, and novelty scoring for ad clips
- **Service Routing**: Routes requests to appropriate backend services
- **Prediction Logging**: Tracks predictions and actual performance for learning

## Endpoints

### Health Check
```
GET /health
```

### Knowledge Management
```
POST /knowledge/upload      - Upload knowledge content
POST /knowledge/activate    - Activate knowledge version
GET  /knowledge/status      - Check knowledge status
```

### Scoring
```
POST /score/clip           - Score a video clip
```

## Configuration

Environment variables:
- `PORT` - Server port (default: 8080)
- `PROJECT_ID` - GCP project ID
- `GCS_BUCKET` - GCS bucket name
- `GCS_MOCK_MODE` - Enable mock mode for local development (true/false)

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
docker build -t gateway-api .

# Run container
docker run -p 8080:8080 -e PORT=8080 gateway-api
```
