"""
Example Usage of GCS Knowledge Store
Agent 1 of 30: GCS Storage Implementation

Demonstrates how to use the real GCS implementation for knowledge persistence.
"""

import os
import logging
from pathlib import Path

from manager import KnowledgeBaseManager, GCSBackend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_local_storage():
    """Example: Using local file system storage (default)"""
    logger.info("=== Example: Local File System Storage ===")

    # Initialize with default local storage
    manager = KnowledgeBaseManager()

    # Upload brand guidelines
    brand_data = {
        "brand_name": "FitPro",
        "voice": "energetic and motivational",
        "values": ["authenticity", "results-driven", "community"],
        "tone": "direct but empathetic",
        "keywords": ["transformation", "proven", "science-backed"],
        "avoid": ["gimmicks", "quick fixes", "unrealistic promises"]
    }

    version_id = manager.upload_knowledge(
        category="brand_guidelines",
        data=brand_data,
        description="Initial brand guidelines",
        author="marketing_team"
    )
    logger.info(f"Uploaded version: {version_id}")

    # Download and verify
    downloaded = manager.download_knowledge("brand_guidelines")
    logger.info(f"Downloaded brand: {downloaded.get('brand_name')}")


def example_gcs_storage():
    """Example: Using Google Cloud Storage"""
    logger.info("=== Example: Google Cloud Storage ===")

    # Configuration
    BUCKET_NAME = "geminivideo-knowledge-base"
    PROJECT_ID = "your-gcp-project-id"  # Replace with your project ID

    # Option 1: Using service account credentials
    CREDENTIALS_PATH = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    try:
        # Initialize GCS backend
        gcs_backend = GCSBackend(
            bucket_name=BUCKET_NAME,
            credentials_path=CREDENTIALS_PATH,
            project_id=PROJECT_ID,
            create_bucket=True  # Creates bucket if it doesn't exist
        )

        # Initialize manager with GCS backend
        manager = KnowledgeBaseManager(storage_backend=gcs_backend)

        # Upload hook templates to GCS
        hook_templates = {
            "templates": [
                {
                    "id": "hook_001",
                    "name": "Problem-Solution Hook",
                    "template": "Struggling with {problem}? Here's how {solution} changed everything.",
                    "use_cases": ["tutorials", "product demos"],
                    "avg_retention": 0.85
                },
                {
                    "id": "hook_002",
                    "name": "Curiosity Gap",
                    "template": "You won't believe what happened when {scenario}...",
                    "use_cases": ["storytelling", "viral content"],
                    "avg_retention": 0.92
                },
                {
                    "id": "hook_003",
                    "name": "Social Proof",
                    "template": "{number} people are already using this {technique} to {benefit}",
                    "use_cases": ["testimonials", "case studies"],
                    "avg_retention": 0.78
                }
            ],
            "metadata": {
                "total_templates": 3,
                "last_updated": "2025-12-01",
                "performance_threshold": 0.75
            }
        }

        version_id = manager.upload_knowledge(
            category="hook_templates",
            data=hook_templates,
            description="Initial hook templates collection",
            author="content_team"
        )
        logger.info(f"Uploaded to GCS - version: {version_id}")

        # Download from GCS
        downloaded = manager.download_knowledge("hook_templates")
        logger.info(f"Downloaded {downloaded['metadata']['total_templates']} templates from GCS")

        # List all versions
        versions = manager.list_versions("hook_templates")
        logger.info(f"Total versions in GCS: {len(versions)}")
        for v in versions:
            logger.info(f"  - {v.version_id} by {v.author} ({v.size_bytes} bytes)")

        # Subscribe to updates
        def on_knowledge_update(category, new_version, old_version):
            logger.info(f"Knowledge updated: {category} {old_version} -> {new_version}")

        subscription_id = manager.subscribe_to_updates(on_knowledge_update)
        logger.info(f"Subscribed to updates: {subscription_id}")

        # Upload winning patterns
        winning_patterns = {
            "patterns": [
                {
                    "pattern_id": "pattern_001",
                    "name": "Fast-Cut Montage",
                    "description": "Quick cuts every 2-3 seconds with energetic music",
                    "success_rate": 0.87,
                    "best_for": ["fitness", "lifestyle", "product reveals"]
                },
                {
                    "pattern_id": "pattern_002",
                    "name": "Before-After Transition",
                    "description": "Dramatic transformation reveal with swipe transition",
                    "success_rate": 0.91,
                    "best_for": ["fitness", "home improvement", "makeovers"]
                }
            ],
            "analysis": {
                "total_analyzed": 10000,
                "confidence": 0.95,
                "updated": "2025-12-01"
            }
        }

        version_id = manager.upload_knowledge(
            category="winning_patterns",
            data=winning_patterns,
            description="Top performing video patterns",
            author="analytics_team"
        )
        logger.info(f"Uploaded winning patterns to GCS - version: {version_id}")

        # Get overall status
        status = manager.get_all_status()
        logger.info("\nKnowledge Base Status:")
        for category, info in status.items():
            if info['total_versions'] > 0:
                logger.info(
                    f"  {category}: {info['total_versions']} versions, "
                    f"active: {info['active_version']}, "
                    f"cached: {info['cached']}"
                )

    except Exception as e:
        logger.error(f"GCS example failed: {e}")
        raise


def example_direct_gcs_store():
    """Example: Using GCSKnowledgeStore directly (advanced)"""
    logger.info("=== Example: Direct GCS Store Usage ===")

    from gcs_store import GCSKnowledgeStore

    BUCKET_NAME = "geminivideo-knowledge-base"
    PROJECT_ID = "your-gcp-project-id"

    try:
        # Initialize store
        store = GCSKnowledgeStore(
            bucket_name=BUCKET_NAME,
            project_id=PROJECT_ID,
            create_bucket=True
        )

        # Upload JSON data
        test_data = {
            "message": "Hello from GCS!",
            "timestamp": "2025-12-01T00:00:00Z",
            "test": True
        }

        url = store.upload_json(
            blob_name="test/hello.json",
            data=test_data
        )
        logger.info(f"Uploaded JSON to: {url}")

        # Download JSON data
        downloaded = store.download_json("test/hello.json")
        logger.info(f"Downloaded: {downloaded}")

        # List blobs
        blobs = store.list_blobs(prefix="test/")
        logger.info(f"Blobs in test/: {blobs}")

        # Get metadata
        metadata = store.get_metadata("test/hello.json")
        logger.info(f"Blob metadata: size={metadata['size_bytes']}, type={metadata['content_type']}")

        # Generate signed URL
        signed_url = store.get_signed_url(
            blob_name="test/hello.json",
            expiration_minutes=60
        )
        logger.info(f"Signed URL (valid for 60 min): {signed_url[:100]}...")

        # Copy blob
        new_url = store.copy(
            source_blob="test/hello.json",
            dest_blob="test/hello_backup.json"
        )
        logger.info(f"Copied to: {new_url}")

        # Batch operations
        to_delete = ["test/hello.json", "test/hello_backup.json"]
        results = store.batch_delete(to_delete)
        logger.info(f"Batch delete results: {results}")

        # Bucket info
        bucket_info = store.get_bucket_info()
        logger.info(f"Bucket: {bucket_info['name']} in {bucket_info['location']}")

    except Exception as e:
        logger.error(f"Direct GCS store example failed: {e}")
        raise


def example_environment_variables():
    """Example: Configuration using environment variables"""
    logger.info("=== Example: Environment Variable Configuration ===")

    # Set these environment variables:
    # export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
    # export GCS_BUCKET_NAME=your-bucket-name
    # export GCP_PROJECT_ID=your-project-id

    bucket_name = os.environ.get("GCS_BUCKET_NAME", "geminivideo-knowledge-base")
    project_id = os.environ.get("GCP_PROJECT_ID")
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    logger.info(f"Using bucket: {bucket_name}")
    logger.info(f"Project ID: {project_id or 'default'}")
    logger.info(f"Credentials: {credentials_path or 'default credentials'}")

    try:
        gcs_backend = GCSBackend(
            bucket_name=bucket_name,
            credentials_path=credentials_path,
            project_id=project_id,
            create_bucket=True
        )

        manager = KnowledgeBaseManager(storage_backend=gcs_backend)
        logger.info("Successfully initialized with environment variables")

    except Exception as e:
        logger.error(f"Environment variable configuration failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    examples = {
        "local": example_local_storage,
        "gcs": example_gcs_storage,
        "direct": example_direct_gcs_store,
        "env": example_environment_variables
    }

    if len(sys.argv) > 1 and sys.argv[1] in examples:
        examples[sys.argv[1]]()
    else:
        logger.info("Available examples:")
        logger.info("  python gcs_example.py local   - Local file system storage")
        logger.info("  python gcs_example.py gcs     - Google Cloud Storage")
        logger.info("  python gcs_example.py direct  - Direct GCS store usage")
        logger.info("  python gcs_example.py env     - Environment variable config")
        logger.info("\nRunning local example by default...\n")
        example_local_storage()
