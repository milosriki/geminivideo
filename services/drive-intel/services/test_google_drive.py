"""
Test Suite for Real Google Drive API Integration - Agent 22
Demonstrates all functionality with real API calls.
"""

import os
import logging
from pathlib import Path
from google_drive import GoogleDriveService, DriveFile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_service_account_auth():
    """Test 1: Service account authentication"""
    logger.info("=" * 60)
    logger.info("TEST 1: Service Account Authentication")
    logger.info("=" * 60)

    credentials_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY', 'service-account.json')

    try:
        service = GoogleDriveService(credentials_path=credentials_path)
        logger.info("✅ Service account authentication successful")
        return service
    except Exception as e:
        logger.error(f"❌ Service account authentication failed: {e}")
        logger.info("Make sure you have a valid service account JSON file")
        return None


def test_oauth_auth():
    """Test 2: OAuth 2.0 authentication"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: OAuth 2.0 Authentication")
    logger.info("=" * 60)

    token_path = os.path.expanduser('~/.geminivideo/token.json')
    credentials_path = os.getenv('GOOGLE_OAUTH_CREDENTIALS', 'oauth_credentials.json')

    try:
        service = GoogleDriveService()
        service.authenticate_oauth(token_path, credentials_path)
        logger.info("✅ OAuth authentication successful")
        return service
    except Exception as e:
        logger.error(f"❌ OAuth authentication failed: {e}")
        return None


def test_list_folder(service: GoogleDriveService, folder_id: str):
    """Test 3: List all files in a folder"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: List Folder Contents")
    logger.info("=" * 60)

    try:
        files = service.list_folder(folder_id, page_size=20)
        logger.info(f"✅ Found {len(files)} files in folder")

        for idx, file in enumerate(files[:5], 1):
            logger.info(f"  {idx}. {file.name} ({file.size_mb():.2f} MB) - {file.mime_type}")

        return files
    except Exception as e:
        logger.error(f"❌ List folder failed: {e}")
        return []


def test_list_videos(service: GoogleDriveService, folder_id: str):
    """Test 4: List only video files"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: List Video Files")
    logger.info("=" * 60)

    try:
        videos = service.list_videos(folder_id, page_size=10)
        logger.info(f"✅ Found {len(videos)} video files")

        for idx, video in enumerate(videos, 1):
            duration_sec = video.duration_ms / 1000 if video.duration_ms else 0
            resolution = f"{video.width}x{video.height}" if video.width else "unknown"
            logger.info(
                f"  {idx}. {video.name}\n"
                f"      Size: {video.size_mb():.2f} MB | "
                f"Duration: {duration_sec:.1f}s | "
                f"Resolution: {resolution}"
            )

        return videos
    except Exception as e:
        logger.error(f"❌ List videos failed: {e}")
        return []


def test_get_metadata(service: GoogleDriveService, file_id: str):
    """Test 5: Get detailed file metadata"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Get File Metadata")
    logger.info("=" * 60)

    try:
        metadata = service.get_file_metadata(file_id)
        logger.info(f"✅ Retrieved metadata for: {metadata.name}")
        logger.info(f"  ID: {metadata.id}")
        logger.info(f"  MIME Type: {metadata.mime_type}")
        logger.info(f"  Size: {metadata.size_mb():.2f} MB")
        logger.info(f"  Created: {metadata.created_time}")
        logger.info(f"  Modified: {metadata.modified_time}")
        logger.info(f"  MD5: {metadata.md5_checksum}")
        logger.info(f"  Web Link: {metadata.web_view_link}")

        if metadata.is_video():
            logger.info(f"  Video Duration: {metadata.duration_ms / 1000:.1f}s")
            logger.info(f"  Resolution: {metadata.width}x{metadata.height}")

        return metadata
    except Exception as e:
        logger.error(f"❌ Get metadata failed: {e}")
        return None


def test_download_file(service: GoogleDriveService, file_id: str, destination: str):
    """Test 6: Download file to disk"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Download File to Disk")
    logger.info("=" * 60)

    try:
        local_path = service.download_file(file_id, destination)
        file_size = Path(local_path).stat().st_size / (1024 * 1024)
        logger.info(f"✅ Downloaded to: {local_path} ({file_size:.2f} MB)")
        return local_path
    except Exception as e:
        logger.error(f"❌ Download failed: {e}")
        return None


def test_download_to_memory(service: GoogleDriveService, file_id: str):
    """Test 7: Download file to memory"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 7: Download File to Memory")
    logger.info("=" * 60)

    try:
        content = service.download_to_memory(file_id)
        logger.info(f"✅ Downloaded {len(content) / (1024 * 1024):.2f} MB to memory")
        return content
    except Exception as e:
        logger.error(f"❌ Download to memory failed: {e}")
        return None


def test_batch_download(service: GoogleDriveService, file_ids: list, destination_dir: str):
    """Test 8: Batch download multiple files"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 8: Batch Download Files")
    logger.info("=" * 60)

    try:
        results = service.batch_download(file_ids, destination_dir)
        successful = len([v for v in results.values() if v])
        logger.info(f"✅ Batch download complete: {successful}/{len(file_ids)} succeeded")

        for file_id, local_path in results.items():
            if local_path:
                logger.info(f"  ✓ {file_id} -> {local_path}")
            else:
                logger.info(f"  ✗ {file_id} failed")

        return results
    except Exception as e:
        logger.error(f"❌ Batch download failed: {e}")
        return {}


def test_search_files(service: GoogleDriveService, query: str, folder_id: str = None):
    """Test 9: Search for files"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 9: Search Files")
    logger.info("=" * 60)

    try:
        results = service.search_files(query, folder_id=folder_id, max_results=10)
        logger.info(f"✅ Search '{query}' returned {len(results)} results")

        for idx, file in enumerate(results, 1):
            logger.info(f"  {idx}. {file.name} ({file.mime_type})")

        return results
    except Exception as e:
        logger.error(f"❌ Search failed: {e}")
        return []


def test_storage_quota(service: GoogleDriveService):
    """Test 10: Get storage quota information"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 10: Storage Quota")
    logger.info("=" * 60)

    try:
        quota = service.get_storage_quota()
        logger.info("✅ Storage quota retrieved")
        logger.info(f"  Total: {quota['limit'] / 1024**3:.2f} GB")
        logger.info(f"  Used: {quota['usage'] / 1024**3:.2f} GB")
        logger.info(f"  Drive: {quota['usage_in_drive'] / 1024**3:.2f} GB")
        logger.info(f"  Trash: {quota['usage_in_drive_trash'] / 1024**3:.2f} GB")
        logger.info(f"  Usage: {quota['usage_percent']:.1f}%")

        return quota
    except Exception as e:
        logger.error(f"❌ Get storage quota failed: {e}")
        return {}


def test_create_folder(service: GoogleDriveService, name: str, parent_id: str = None):
    """Test 11: Create a new folder"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 11: Create Folder")
    logger.info("=" * 60)

    try:
        folder_id = service.create_folder(name, parent_id)
        logger.info(f"✅ Created folder '{name}' with ID: {folder_id}")
        return folder_id
    except Exception as e:
        logger.error(f"❌ Create folder failed: {e}")
        return None


def test_move_file(service: GoogleDriveService, file_id: str, new_parent_id: str):
    """Test 12: Move file to different folder"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 12: Move File")
    logger.info("=" * 60)

    try:
        success = service.move_file(file_id, new_parent_id)
        if success:
            logger.info(f"✅ Moved file {file_id} to folder {new_parent_id}")
        else:
            logger.error(f"❌ Failed to move file {file_id}")
        return success
    except Exception as e:
        logger.error(f"❌ Move file failed: {e}")
        return False


def test_watch_folder(service: GoogleDriveService, folder_id: str, webhook_url: str):
    """Test 13: Watch folder for changes"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 13: Watch Folder (Webhooks)")
    logger.info("=" * 60)

    try:
        channel_info = service.watch_folder(folder_id, webhook_url, expiration_hours=24)
        logger.info(f"✅ Started watching folder {folder_id}")
        logger.info(f"  Channel ID: {channel_info['channel_id']}")
        logger.info(f"  Resource ID: {channel_info['resource_id']}")
        logger.info(f"  Webhook: {channel_info['webhook_url']}")
        logger.info(f"  Expires: {channel_info.get('expiration', 'N/A')}")

        return channel_info
    except Exception as e:
        logger.error(f"❌ Watch folder failed: {e}")
        return None


def test_stop_watch(service: GoogleDriveService, channel_id: str, resource_id: str):
    """Test 14: Stop watching folder"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 14: Stop Watch")
    logger.info("=" * 60)

    try:
        success = service.stop_watch(channel_id, resource_id)
        if success:
            logger.info(f"✅ Stopped watching channel {channel_id}")
        else:
            logger.error(f"❌ Failed to stop channel {channel_id}")
        return success
    except Exception as e:
        logger.error(f"❌ Stop watch failed: {e}")
        return False


def run_comprehensive_test():
    """Run comprehensive test suite"""
    logger.info("\n" + "=" * 80)
    logger.info("GOOGLE DRIVE API INTEGRATION - COMPREHENSIVE TEST SUITE")
    logger.info("Agent 22 - Real API Integration (NO MOCK DATA)")
    logger.info("=" * 80)

    # Configuration
    TEST_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'your-folder-id-here')
    TEST_FILE_ID = os.getenv('GOOGLE_DRIVE_FILE_ID', 'your-file-id-here')
    WEBHOOK_URL = os.getenv('WEBHOOK_URL', 'https://your-domain.com/webhook')

    # Authenticate
    service = test_service_account_auth()
    if not service:
        logger.warning("Trying OAuth authentication instead...")
        service = test_oauth_auth()

    if not service:
        logger.error("❌ All authentication methods failed. Exiting.")
        return

    # Run tests
    test_storage_quota(service)
    files = test_list_folder(service, TEST_FOLDER_ID)
    videos = test_list_videos(service, TEST_FOLDER_ID)

    if videos:
        test_file_id = videos[0].id
        test_get_metadata(service, test_file_id)

    test_search_files(service, "video", folder_id=TEST_FOLDER_ID)

    # Note: Download tests commented out to avoid large file transfers
    # Uncomment to test downloads
    # test_download_file(service, TEST_FILE_ID, "/tmp/test_video.mp4")
    # test_download_to_memory(service, TEST_FILE_ID)
    # test_batch_download(service, [TEST_FILE_ID], "/tmp/batch_downloads")

    # Note: Folder creation/modification commented out to avoid changes
    # Uncomment to test folder operations
    # new_folder_id = test_create_folder(service, "Test Folder", TEST_FOLDER_ID)
    # test_move_file(service, TEST_FILE_ID, new_folder_id)

    # Note: Webhook tests require a public HTTPS endpoint
    # Uncomment if you have a webhook endpoint
    # channel_info = test_watch_folder(service, TEST_FOLDER_ID, WEBHOOK_URL)
    # if channel_info:
    #     test_stop_watch(service, channel_info['channel_id'], channel_info['resource_id'])

    logger.info("\n" + "=" * 80)
    logger.info("TEST SUITE COMPLETE")
    logger.info("=" * 80)


if __name__ == '__main__':
    run_comprehensive_test()
