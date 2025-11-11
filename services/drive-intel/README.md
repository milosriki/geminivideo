# Drive Intel Service

Video intelligence service for ingesting, analyzing, and extracting features from video content.

## Features

- **Video Ingestion**: Ingest from local folders or Google Drive
- **Scene Detection**: Automatic scene boundary detection using PySceneDetect
- **Feature Extraction**: 
  - Motion energy analysis
  - Face detection
  - Object detection (YOLO stub)
  - OCR text extraction (Tesseract stub)
  - Embedding generation for similarity search
- **FAISS Indexing**: In-memory vector search for content similarity
- **Clip Ranking**: Score and rank clips by engagement potential

## Endpoints

### Health Check
```
GET /health
```

### Ingestion
```
POST /ingest/local/folder    - Ingest from local filesystem
POST /ingest/drive/folder    - Ingest from Google Drive
```

### Asset Management
```
GET /assets                   - List all assets
GET /assets/{id}/clips        - Get clips for an asset (supports ?ranked=true&top=10)
```

## Configuration

Environment variables:
- `PORT` - Server port (default: 8081)
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `FAISS_INDEX_PATH` - Path for FAISS index storage

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn src.main:app --reload --port 8081
```

## Docker

```bash
# Build image
docker build -t drive-intel .

# Run container
docker run -p 8081:8081 drive-intel
```

## Feature Extraction Pipeline

1. **Scene Detection**: Uses PySceneDetect to identify scene boundaries
2. **Motion Analysis**: OpenCV optical flow for motion energy
3. **Object Detection**: YOLO for object/person detection
4. **OCR**: Tesseract for text overlay extraction
5. **Face Detection**: OpenCV cascade classifier
6. **Embeddings**: Vision transformer for semantic similarity
7. **FAISS Indexing**: Fast similarity search across clips
