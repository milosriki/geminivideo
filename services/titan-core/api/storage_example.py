"""
Example usage of the Video Storage Service

This demonstrates how to:
1. Upload videos via API
2. Get signed URLs
3. Delete videos
4. List stored videos
"""

import requests
import os
from pathlib import Path

# API Base URL
BASE_URL = "http://localhost:8000/storage"


def upload_video_example():
    """Example: Upload a video file"""
    video_path = "/path/to/your/video.mp4"

    if not os.path.exists(video_path):
        print("❌ Video file not found")
        return None

    # Upload with multipart/form-data
    with open(video_path, "rb") as f:
        files = {"file": (Path(video_path).name, f, "video/mp4")}
        params = {"folder": "uploads"}

        response = requests.post(
            f"{BASE_URL}/upload",
            files=files,
            params=params
        )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Upload successful!")
        print(f"   Video ID: {result['video_id']}")
        print(f"   Storage: {result['storage_path']}")
        print(f"   Size: {result['size']} bytes")
        return result['video_id']
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print(response.text)
        return None


def get_video_url_example(video_id: str):
    """Example: Get signed URL for video download"""
    params = {
        "folder": "uploads",
        "expiration": 120  # 2 hours
    }

    response = requests.get(
        f"{BASE_URL}/{video_id}/url",
        params=params
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Signed URL generated!")
        print(f"   URL: {result['url']}")
        print(f"   Expires in: {result['expires_in']} minutes")
        return result['url']
    else:
        print(f"❌ Failed to get URL: {response.status_code}")
        print(response.text)
        return None


def list_videos_example():
    """Example: List all uploaded videos"""
    params = {
        "prefix": "uploads",
        "limit": 50
    }

    response = requests.get(
        f"{BASE_URL}/list",
        params=params
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Found {result['total']} videos (Storage: {result['storage_type']})")

        for video in result['videos']:
            print(f"\n   📹 {video['filename']}")
            print(f"      ID: {video['video_id']}")
            print(f"      Size: {video['size']} bytes")
            print(f"      Uploaded: {video['upload_time']}")

        return result['videos']
    else:
        print(f"❌ Failed to list videos: {response.status_code}")
        print(response.text)
        return []


def delete_video_example(video_id: str):
    """Example: Delete a video"""
    params = {"folder": "uploads"}

    response = requests.delete(
        f"{BASE_URL}/{video_id}",
        params=params
    )

    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result['message']}")
        return True
    else:
        print(f"❌ Failed to delete: {response.status_code}")
        print(response.text)
        return False


def check_storage_health():
    """Example: Check storage service health"""
    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        result = response.json()
        print(f"✅ Storage service is {result['status']}")
        print(f"   Type: {result['storage_type']}")
        if result.get('bucket'):
            print(f"   Bucket: {result['bucket']}")
        if result.get('local_path'):
            print(f"   Local path: {result['local_path']}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False


def main():
    """Run all examples"""
    print("=" * 60)
    print("Video Storage Service - Usage Examples")
    print("=" * 60)

    # 1. Check health
    print("\n1. Checking storage health...")
    check_storage_health()

    # 2. Upload video
    print("\n2. Uploading video...")
    video_id = upload_video_example()

    if video_id:
        # 3. Get signed URL
        print(f"\n3. Getting signed URL for video: {video_id}")
        url = get_video_url_example(video_id)

        # 4. List videos
        print("\n4. Listing all videos...")
        list_videos_example()

        # 5. Delete video (optional - uncomment to test)
        # print(f"\n5. Deleting video: {video_id}")
        # delete_video_example(video_id)

    print("\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()


"""
Using with curl:

1. Upload video:
curl -X POST "http://localhost:8000/storage/upload?folder=uploads" \\
  -H "accept: application/json" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@/path/to/video.mp4"

2. Get signed URL:
curl -X GET "http://localhost:8000/storage/{video_id}/url?folder=uploads&expiration=60" \\
  -H "accept: application/json"

3. List videos:
curl -X GET "http://localhost:8000/storage/list?prefix=uploads&limit=100" \\
  -H "accept: application/json"

4. Delete video:
curl -X DELETE "http://localhost:8000/storage/{video_id}?folder=uploads" \\
  -H "accept: application/json"

5. Health check:
curl -X GET "http://localhost:8000/storage/health" \\
  -H "accept: application/json"
"""
