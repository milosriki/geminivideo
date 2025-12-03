#!/usr/bin/env python3
"""
QUICKSTART EXAMPLE - Google Drive API Integration
Agent 22 | Minimal working example to get started quickly
"""

from google_drive import GoogleDriveService, DriveFile
import os
from pathlib import Path


def example_service_account():
    """Example 1: Service Account Authentication (recommended for servers)"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Service Account Authentication")
    print("="*60)

    # Initialize with service account
    service = GoogleDriveService(
        credentials_path='path/to/service-account.json'
    )

    # Get storage quota
    quota = service.get_storage_quota()
    print(f"\n📊 Storage: {quota['usage_percent']:.1f}% used")
    print(f"   {quota['usage']/1024**3:.2f} GB / {quota['limit']/1024**3:.2f} GB")

    return service


def example_oauth():
    """Example 2: OAuth 2.0 Authentication (for user access)"""
    print("\n" + "="*60)
    print("EXAMPLE 2: OAuth 2.0 Authentication")
    print("="*60)

    # Initialize and authenticate with OAuth
    service = GoogleDriveService()
    service.authenticate_oauth(
        token_path=os.path.expanduser('~/.geminivideo/token.json'),
        credentials_path='path/to/oauth_credentials.json'
    )

    print("✅ OAuth authentication successful")
    return service


def example_list_videos(service: GoogleDriveService, folder_id: str):
    """Example 3: List all videos in a folder"""
    print("\n" + "="*60)
    print("EXAMPLE 3: List Videos")
    print("="*60)

    # Get all videos from folder
    videos = service.list_videos(folder_id, page_size=20)

    print(f"\n📹 Found {len(videos)} videos:\n")

    for i, video in enumerate(videos[:5], 1):
        duration = video.duration_ms / 1000 if video.duration_ms else 0
        resolution = f"{video.width}x{video.height}" if video.width else "unknown"

        print(f"{i}. {video.name}")
        print(f"   Size: {video.size_mb():.2f} MB")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Resolution: {resolution}")
        print()

    return videos


def example_download(service: GoogleDriveService, file_id: str):
    """Example 4: Download a video file"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Download Video")
    print("="*60)

    # Get file metadata first
    metadata = service.get_file_metadata(file_id)
    print(f"\n📥 Downloading: {metadata.name}")
    print(f"   Size: {metadata.size_mb():.2f} MB")

    # Download to local directory
    download_dir = Path('/tmp/geminivideo/downloads')
    download_dir.mkdir(parents=True, exist_ok=True)

    local_path = service.download_file(
        file_id,
        str(download_dir / metadata.name)
    )

    print(f"✅ Saved to: {local_path}")
    return local_path


def example_batch_download(service: GoogleDriveService, videos: list):
    """Example 5: Batch download multiple videos"""
    print("\n" + "="*60)
    print("EXAMPLE 5: Batch Download")
    print("="*60)

    # Select first 3 videos
    video_ids = [v.id for v in videos[:3]]

    print(f"\n📦 Downloading {len(video_ids)} videos...\n")

    # Batch download
    results = service.batch_download(
        file_ids=video_ids,
        destination_dir='/tmp/geminivideo/batch'
    )

    # Check results
    successful = [fid for fid, path in results.items() if path]
    failed = [fid for fid, path in results.items() if not path]

    print(f"\n✅ Successful: {len(successful)}/{len(video_ids)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")

    return results


def example_search(service: GoogleDriveService, folder_id: str):
    """Example 6: Search for specific videos"""
    print("\n" + "="*60)
    print("EXAMPLE 6: Search Videos")
    print("="*60)

    # Search for videos with "interview" in name
    results = service.search_files(
        query='interview',
        folder_id=folder_id,
        max_results=10
    )

    print(f"\n🔍 Search 'interview': {len(results)} results\n")

    for i, file in enumerate(results, 1):
        print(f"{i}. {file.name}")
        if file.is_video():
            print(f"   Video: {file.size_mb():.2f} MB")
        print()


def example_folder_management(service: GoogleDriveService, parent_id: str):
    """Example 7: Create and organize folders"""
    print("\n" + "="*60)
    print("EXAMPLE 7: Folder Management")
    print("="*60)

    # Create folders
    processed_id = service.create_folder('Processed Videos', parent_id)
    pending_id = service.create_folder('Pending Videos', parent_id)

    print(f"✅ Created folders:")
    print(f"   Processed: {processed_id}")
    print(f"   Pending: {pending_id}")

    return processed_id, pending_id


def example_webhooks(service: GoogleDriveService, folder_id: str):
    """Example 8: Set up folder watching with webhooks"""
    print("\n" + "="*60)
    print("EXAMPLE 8: Folder Webhooks")
    print("="*60)

    # Your webhook endpoint (must be HTTPS and publicly accessible)
    webhook_url = 'https://yourapp.com/api/webhook/drive'

    # Start watching folder
    channel_info = service.watch_folder(
        folder_id=folder_id,
        webhook_url=webhook_url,
        expiration_hours=24
    )

    print(f"\n🔔 Watching folder for changes:")
    print(f"   Channel ID: {channel_info['channel_id']}")
    print(f"   Resource ID: {channel_info['resource_id']}")
    print(f"   Webhook: {channel_info['webhook_url']}")

    # Stop watching (when done)
    # service.stop_watch(
    #     channel_id=channel_info['channel_id'],
    #     resource_id=channel_info['resource_id']
    # )

    return channel_info


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("GOOGLE DRIVE API - QUICKSTART EXAMPLES")
    print("Agent 22 | Real API Integration (NO MOCK DATA)")
    print("="*80)

    # Configuration - UPDATE THESE VALUES
    FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'your-folder-id-here')
    SERVICE_ACCOUNT_PATH = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY', 'service-account.json')

    print("\n📝 Configuration:")
    print(f"   Folder ID: {FOLDER_ID}")
    print(f"   Credentials: {SERVICE_ACCOUNT_PATH}")

    try:
        # Example 1: Authenticate
        service = GoogleDriveService(credentials_path=SERVICE_ACCOUNT_PATH)

        # Example 2: List videos
        videos = example_list_videos(service, FOLDER_ID)

        # Example 3: Search
        example_search(service, FOLDER_ID)

        # Example 4: Download single file (if videos available)
        if videos:
            # Uncomment to download
            # example_download(service, videos[0].id)
            pass

        # Example 5: Batch download (if videos available)
        if len(videos) >= 3:
            # Uncomment to batch download
            # example_batch_download(service, videos)
            pass

        # Example 6: Folder management
        # Uncomment to create folders
        # example_folder_management(service, FOLDER_ID)

        # Example 7: Webhooks
        # Uncomment if you have a webhook endpoint
        # example_webhooks(service, FOLDER_ID)

        print("\n" + "="*80)
        print("✅ QUICKSTART COMPLETE")
        print("="*80)
        print("\nNext steps:")
        print("1. Update FOLDER_ID and SERVICE_ACCOUNT_PATH")
        print("2. Uncomment examples you want to run")
        print("3. Integrate with your video processing pipeline")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check credentials file exists and is valid JSON")
        print("2. Ensure folder is shared with service account email")
        print("3. Verify Google Drive API is enabled in Cloud Console")
        print("4. Check folder ID is correct (from Drive URL)")


if __name__ == '__main__':
    main()
