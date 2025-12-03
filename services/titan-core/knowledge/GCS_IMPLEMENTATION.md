# GCS Storage Implementation

**Agent 1 of 30: Real GCS Storage Implementation**

This document describes the production-grade Google Cloud Storage (GCS) implementation for the Knowledge Base Manager.

## Overview

The GCS implementation replaces the previous `NotImplementedError` stubs with a fully functional, production-ready storage backend that provides:

- ✅ Real GCS blob storage operations
- ✅ Automatic retry logic for transient failures
- ✅ Comprehensive error handling
- ✅ Type hints and documentation
- ✅ Logging for debugging and monitoring
- ✅ Support for JSON and binary data
- ✅ Metadata operations and signed URLs
- ✅ Batch operations for efficiency

## Files Created/Modified

### New Files

1. **`gcs_store.py`** (~500 lines)
   - Core GCS implementation with `GCSKnowledgeStore` class
   - All storage operations with retry logic
   - Production-ready error handling

2. **`gcs_example.py`** (~350 lines)
   - Comprehensive usage examples
   - Multiple configuration patterns
   - Direct store usage examples

3. **`GCS_IMPLEMENTATION.md`**
   - This documentation file

### Modified Files

1. **`manager.py`**
   - Updated `GCSBackend` class (lines 122-257)
   - Replaced 5 `NotImplementedError` stubs with real implementations
   - Integrated with `GCSKnowledgeStore`

## Architecture

```
┌─────────────────────────────────────┐
│   KnowledgeBaseManager              │
│   - Version management              │
│   - Hot-reload capability           │
│   - Callback notifications          │
└────────────┬────────────────────────┘
             │
             ├─► LocalFileSystemBackend
             │
             └─► GCSBackend ───────────┐
                                       │
                 ┌─────────────────────▼──────────────────────┐
                 │   GCSKnowledgeStore                        │
                 │   - upload() / download()                  │
                 │   - upload_json() / download_json()        │
                 │   - list_blobs() / delete()                │
                 │   - exists() / get_metadata()              │
                 │   - copy() / get_signed_url()              │
                 │   - batch_delete() / get_bucket_info()     │
                 └────────────────┬───────────────────────────┘
                                  │
                    ┌─────────────▼────────────────┐
                    │   google.cloud.storage       │
                    │   (Official GCS Python SDK)  │
                    └──────────────────────────────┘
```

## Features

### 1. GCSKnowledgeStore Class

The main class providing comprehensive GCS operations:

```python
from knowledge.gcs_store import GCSKnowledgeStore

store = GCSKnowledgeStore(
    bucket_name="my-bucket",
    credentials_path="/path/to/credentials.json",  # Optional
    project_id="my-project",                        # Optional
    create_bucket=True                              # Optional
)
```

#### Upload Operations

```python
# Upload binary data
url = store.upload(
    blob_name="data/file.bin",
    data=b"binary data",
    content_type="application/octet-stream"
)

# Upload JSON data
url = store.upload_json(
    blob_name="data/config.json",
    data={"key": "value"}
)
```

#### Download Operations

```python
# Download binary data
data = store.download("data/file.bin")

# Download JSON data
config = store.download_json("data/config.json")
```

#### Listing and Existence

```python
# List all blobs with prefix
blobs = store.list_blobs(prefix="data/")

# Check if blob exists
exists = store.exists("data/file.bin")
```

#### Metadata and URLs

```python
# Get blob metadata
metadata = store.get_metadata("data/file.bin")
# Returns: size, content_type, created, updated, etc.

# Generate signed URL (temporary access)
url = store.get_signed_url(
    blob_name="data/file.bin",
    expiration_minutes=60
)
```

#### Advanced Operations

```python
# Copy blob
store.copy(
    source_blob="data/original.json",
    dest_blob="data/backup.json"
)

# Batch delete
results = store.batch_delete([
    "data/file1.json",
    "data/file2.json"
])

# Get bucket information
info = store.get_bucket_info()
```

### 2. GCSBackend Integration

The `GCSBackend` class integrates `GCSKnowledgeStore` with the `KnowledgeBaseManager`:

```python
from knowledge.manager import KnowledgeBaseManager, GCSBackend

# Create GCS backend
gcs_backend = GCSBackend(
    bucket_name="geminivideo-knowledge",
    credentials_path="/path/to/credentials.json",
    project_id="my-project",
    create_bucket=True
)

# Initialize manager with GCS storage
manager = KnowledgeBaseManager(storage_backend=gcs_backend)

# Now all operations use GCS
version_id = manager.upload_knowledge(
    category="brand_guidelines",
    data={"brand_name": "FitPro", ...}
)
```

## Configuration

### Option 1: Service Account Credentials

```python
gcs_backend = GCSBackend(
    bucket_name="my-bucket",
    credentials_path="/path/to/service-account.json",
    project_id="my-gcp-project"
)
```

### Option 2: Application Default Credentials (ADC)

```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"

# Or use gcloud
gcloud auth application-default login
```

```python
# No credentials_path needed
gcs_backend = GCSBackend(
    bucket_name="my-bucket",
    project_id="my-gcp-project"
)
```

### Option 3: Environment Variables

```bash
export GCS_BUCKET_NAME="geminivideo-knowledge"
export GCP_PROJECT_ID="my-gcp-project"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

```python
import os

gcs_backend = GCSBackend(
    bucket_name=os.environ["GCS_BUCKET_NAME"],
    credentials_path=os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"),
    project_id=os.environ["GCP_PROJECT_ID"]
)
```

## Error Handling

The implementation includes comprehensive error handling:

### Automatic Retries

Transient failures are automatically retried with exponential backoff:

- `ServiceUnavailable` (503)
- `InternalServerError` (500)
- `TooManyRequests` (429)
- `DeadlineExceeded`

```python
# Retry configuration
DEFAULT_RETRY = retry.Retry(
    initial=1.0,      # Start with 1 second
    maximum=10.0,     # Max 10 seconds between retries
    multiplier=2.0,   # Exponential backoff
    deadline=60.0     # Total timeout
)
```

### Error Types

```python
from google.cloud.exceptions import NotFound, GoogleCloudError

try:
    data = store.download("nonexistent.json")
except NotFound:
    print("Blob not found")
except GoogleCloudError as e:
    print(f"GCS error: {e}")
```

### Logging

All operations are logged for debugging:

```python
import logging

logging.basicConfig(level=logging.INFO)

# Example logs:
# INFO - GCS backend initialized for bucket: my-bucket
# INFO - Uploaded 1234 bytes to data/file.json
# INFO - Downloaded 5678 bytes from data/file.json
# WARNING - Blob not found: data/missing.json
# ERROR - Failed to upload data/file.json: Permission denied
```

## Performance Considerations

### Caching

The `KnowledgeBaseManager` includes built-in caching:

```python
# First download - fetches from GCS
data1 = manager.download_knowledge("brand_guidelines")

# Second download - uses cache
data2 = manager.download_knowledge("brand_guidelines")
```

### Batch Operations

Use batch operations for efficiency:

```python
# Instead of multiple deletes
for blob in blobs:
    store.delete(blob)

# Use batch delete
results = store.batch_delete(blobs)
```

### Listing Optimization

Use prefixes to limit results:

```python
# Get all blobs (slow for large buckets)
all_blobs = store.list_blobs()

# Get specific category (faster)
category_blobs = store.list_blobs(prefix="brand_guidelines/")
```

## Security Best Practices

### 1. Use Service Accounts

Create dedicated service accounts with minimal permissions:

```bash
gcloud iam service-accounts create geminivideo-storage \
    --display-name="GeminiVideo Storage Service Account"

gcloud projects add-iam-policy-binding my-project \
    --member="serviceAccount:geminivideo-storage@my-project.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

gcloud iam service-accounts keys create credentials.json \
    --iam-account=geminivideo-storage@my-project.iam.gserviceaccount.com
```

### 2. Secure Credentials

```python
# ✅ Good - use environment variables
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

# ❌ Bad - hardcoded paths
credentials_path = "/home/user/secret-key.json"
```

### 3. Signed URLs for Temporary Access

```python
# Generate time-limited URL instead of making blob public
signed_url = store.get_signed_url(
    blob_name="sensitive-data.json",
    expiration_minutes=60
)
```

## Testing

### Unit Tests

```python
import unittest
from knowledge.gcs_store import GCSKnowledgeStore

class TestGCSStore(unittest.TestCase):
    def setUp(self):
        self.store = GCSKnowledgeStore(
            bucket_name="test-bucket",
            create_bucket=True
        )

    def test_upload_download(self):
        data = b"test data"
        self.store.upload("test.bin", data)
        downloaded = self.store.download("test.bin")
        self.assertEqual(data, downloaded)

    def test_json_operations(self):
        data = {"key": "value"}
        self.store.upload_json("test.json", data)
        downloaded = self.store.download_json("test.json")
        self.assertEqual(data, downloaded)
```

### Integration Tests

Run the example file:

```bash
# Test local storage
python services/titan-core/knowledge/gcs_example.py local

# Test GCS storage
python services/titan-core/knowledge/gcs_example.py gcs

# Test direct GCS store
python services/titan-core/knowledge/gcs_example.py direct
```

## Monitoring

### Log Analysis

Monitor for errors and performance:

```bash
# Find upload errors
grep "Failed to upload" logs/titan-core.log

# Find slow operations
grep "Downloaded.*bytes" logs/titan-core.log | awk '{print $NF}'
```

### GCS Metrics

Monitor bucket metrics in GCP Console:

- Total storage
- Request count
- Bandwidth
- Error rate

## Migration Guide

### From Local to GCS

```python
# 1. Backup local data
local_manager = KnowledgeBaseManager()  # Uses local storage
for category in local_manager.CATEGORIES:
    data = local_manager.download_knowledge(category)
    if data:
        # Save backup
        with open(f"backup/{category}.json", "w") as f:
            json.dump(data, f)

# 2. Initialize GCS
gcs_backend = GCSBackend(bucket_name="my-bucket", create_bucket=True)
gcs_manager = KnowledgeBaseManager(storage_backend=gcs_backend)

# 3. Migrate data
for category in local_manager.CATEGORIES:
    data = local_manager.download_knowledge(category)
    if data:
        gcs_manager.upload_knowledge(
            category=category,
            data=data,
            description=f"Migrated from local storage"
        )
```

## Troubleshooting

### Issue: "Bucket does not exist"

**Solution**: Set `create_bucket=True` or create bucket manually:

```bash
gsutil mb -l US gs://my-bucket-name
```

### Issue: "Permission denied"

**Solution**: Check service account permissions:

```bash
gcloud projects get-iam-policy my-project \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:*"
```

### Issue: "Import error: google.cloud.storage"

**Solution**: Install dependencies:

```bash
pip install google-cloud-storage
```

### Issue: "Credentials not found"

**Solution**: Set up authentication:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
# Or
gcloud auth application-default login
```

## API Reference

### GCSKnowledgeStore Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `upload(blob_name, data, content_type)` | Upload binary data | Public URL |
| `upload_json(blob_name, data)` | Upload JSON data | Public URL |
| `download(blob_name)` | Download binary data | bytes |
| `download_json(blob_name)` | Download JSON data | dict |
| `list_blobs(prefix)` | List blobs with prefix | List[str] |
| `delete(blob_name)` | Delete blob | bool |
| `exists(blob_name)` | Check existence | bool |
| `get_metadata(blob_name)` | Get blob metadata | dict |
| `copy(source, dest)` | Copy blob | Public URL |
| `get_signed_url(blob_name, minutes)` | Generate signed URL | str |
| `batch_delete(blob_names)` | Delete multiple blobs | dict |
| `get_bucket_info()` | Get bucket info | dict |

## Support

For issues or questions:

1. Check logs: `services/titan-core/logs/`
2. Review examples: `services/titan-core/knowledge/gcs_example.py`
3. GCS documentation: https://cloud.google.com/storage/docs
4. Python client docs: https://googleapis.dev/python/storage/latest/

## License

Part of the GeminiVideo project.
