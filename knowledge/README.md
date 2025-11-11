# Knowledge Base & Hot-Reload System

This directory contains the knowledge base for the AI Ad Intelligence system, including brand guidelines, competitor analysis, and industry best practices.

## GCS Bucket Layout

The knowledge base is stored in Google Cloud Storage with the following structure:

```
gs://ai-studio-bucket-208288753973-us-west1/
├── knowledge/
│   ├── brand_guidelines/
│   │   ├── voice_tone.md
│   │   ├── visual_style.json
│   │   └── prohibited_content.json
│   ├── competitor_analysis/
│   │   ├── successful_campaigns/
│   │   └── trending_patterns.json
│   ├── industry_benchmarks/
│   │   ├── ctr_baselines.json
│   │   └── engagement_metrics.json
│   └── templates/
│       ├── hooks/
│       └── storyboards/
├── config/
│   ├── weights.yaml
│   ├── scene_ranking.yaml
│   └── personas/
└── models/
    ├── embeddings/
    └── classifiers/
```

## Hot-Reload Endpoints

The Gateway API provides endpoints for dynamically updating the knowledge base without service restarts:

### Upload Knowledge Content

```bash
POST /knowledge/upload
Content-Type: multipart/form-data

{
  "file": <file>,
  "category": "brand_guidelines|competitor_analysis|industry_benchmarks|templates",
  "subcategory": "string",
  "metadata": {
    "version": "string",
    "author": "string",
    "tags": ["string"]
  }
}
```

**Response:**
```json
{
  "upload_id": "uuid",
  "gcs_path": "gs://bucket/path/to/file",
  "status": "uploaded",
  "timestamp": "ISO-8601"
}
```

### Activate Knowledge Version

```bash
POST /knowledge/activate
Content-Type: application/json

{
  "upload_id": "uuid",
  "category": "string"
}
```

Activates a previously uploaded knowledge file, making it available to all services. Triggers a hot-reload notification to dependent services.

**Response:**
```json
{
  "status": "active",
  "version": "1.2.3",
  "activated_at": "ISO-8601",
  "affected_services": ["drive-intel", "video-agent", "meta-publisher"]
}
```

### Check Knowledge Status

```bash
GET /knowledge/status?category=brand_guidelines
```

Returns the current active version and metadata for knowledge categories.

**Response:**
```json
{
  "category": "brand_guidelines",
  "active_version": "1.2.3",
  "last_updated": "ISO-8601",
  "files": [
    {
      "name": "voice_tone.md",
      "gcs_path": "gs://...",
      "size_bytes": 1024,
      "checksum": "sha256:..."
    }
  ]
}
```

## Hot-Reload Mechanism

Services subscribe to knowledge updates via Pub/Sub:

1. Gateway uploads new knowledge to GCS
2. Gateway publishes message to `knowledge-updates` topic
3. Services receive notification and refresh their in-memory caches
4. Services log reload events for audit trail

## Local Development

For local development, mock the GCS bucket with local files:

```bash
export KNOWLEDGE_BASE_PATH=./knowledge
export GCS_MOCK_MODE=true
```

## Versioning

Knowledge files use semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes to schema or structure
- MINOR: New content or non-breaking additions
- PATCH: Corrections or minor updates

## Access Control

Knowledge bucket access is controlled via Service Account with roles:
- `storage.objectViewer` - Read access for services
- `storage.objectCreator` - Upload access for gateway
- `storage.objectAdmin` - Admin access for maintenance
