"""
Asset Library Manager - Comprehensive Demo
Demonstrates all features of the professional asset library system.
"""

from asset_library import (
    AssetLibrary,
    AssetType,
    AssetCategory,
    CloudStorageManager,
    MusicLibrary,
)


def demo_basic_usage():
    """Demo: Basic library setup and asset import"""
    print("=" * 60)
    print("DEMO 1: Basic Library Setup and Asset Import")
    print("=" * 60)

    # Initialize library
    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    print(f"✓ Library initialized at: {library.storage_dir}")
    print(f"✓ Database: {library.database_path}")

    # Import a video asset
    print("\nImporting video asset...")
    video_asset = library.import_asset(
        source_path="/path/to/video.mp4",
        asset_type=AssetType.VIDEO,
        name="Product Demo Video",
        category=AssetCategory.PRODUCT_SHOT,
        tags={"product", "demo", "4k"},
        description="High-quality product demonstration video",
        generate_thumbnail=True
    )

    if video_asset:
        print(f"✓ Video imported: {video_asset.name}")
        print(f"  - ID: {video_asset.id}")
        print(f"  - Type: {video_asset.asset_type.value}")
        print(f"  - Size: {video_asset.file_size / (1024*1024):.2f} MB")
        if video_asset.metadata:
            print(f"  - Resolution: {video_asset.metadata.resolution}")
            print(f"  - Duration: {video_asset.metadata.duration:.2f}s")
            print(f"  - FPS: {video_asset.metadata.fps}")
            print(f"  - Codec: {video_asset.metadata.codec.value}")

    # Import an audio asset
    print("\nImporting audio asset...")
    audio_asset = library.import_asset(
        source_path="/path/to/music.mp3",
        asset_type=AssetType.AUDIO,
        name="Upbeat Background Music",
        category=AssetCategory.MUSIC,
        tags={"upbeat", "energetic", "corporate"},
        description="Energetic background music for product videos"
    )

    if audio_asset:
        print(f"✓ Audio imported: {audio_asset.name}")
        if audio_asset.metadata:
            print(f"  - Duration: {audio_asset.metadata.duration:.2f}s")
            print(f"  - Channels: {audio_asset.metadata.channels}")
            print(f"  - Sample Rate: {audio_asset.metadata.sample_rate} Hz")


def demo_bulk_import():
    """Demo: Bulk import from folder"""
    print("\n" + "=" * 60)
    print("DEMO 2: Bulk Import from Folder")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    # Bulk import videos
    print("\nBulk importing videos...")
    video_assets = library.bulk_import(
        folder_path="/path/to/video/folder",
        asset_type=AssetType.VIDEO,
        category=AssetCategory.STOCK_FOOTAGE,
        recursive=True,
        file_extensions=['.mp4', '.mov', '.avi']
    )

    print(f"✓ Imported {len(video_assets)} video assets")

    # Bulk import audio
    print("\nBulk importing audio files...")
    audio_assets = library.bulk_import(
        folder_path="/path/to/audio/folder",
        asset_type=AssetType.AUDIO,
        category=AssetCategory.MUSIC,
        recursive=True,
        file_extensions=['.mp3', '.wav', '.flac']
    )

    print(f"✓ Imported {len(audio_assets)} audio assets")

    # Bulk import LUTs
    print("\nBulk importing LUTs...")
    lut_assets = library.bulk_import(
        folder_path="/path/to/luts/folder",
        asset_type=AssetType.LUT,
        category=AssetCategory.CINEMATIC,
        recursive=True,
        file_extensions=['.cube', '.3dl']
    )

    print(f"✓ Imported {len(lut_assets)} LUT assets")


def demo_import_from_url():
    """Demo: Import assets from URL"""
    print("\n" + "=" * 60)
    print("DEMO 3: Import Assets from URL")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    # Import stock video from URL
    print("\nImporting stock footage from URL...")
    stock_video = library.import_from_url(
        url="https://example.com/stock-footage/video.mp4",
        asset_type=AssetType.VIDEO,
        name="Stock Ocean Waves",
        category=AssetCategory.STOCK_FOOTAGE,
        tags={"ocean", "nature", "b-roll"},
        description="Beautiful ocean waves stock footage"
    )

    if stock_video:
        print(f"✓ Stock video downloaded and imported: {stock_video.name}")
        print(f"  - Source URL: {stock_video.source_url}")

    # Import music from URL
    print("\nImporting music from URL...")
    music_track = library.import_from_url(
        url="https://example.com/music/track.mp3",
        asset_type=AssetType.AUDIO,
        name="Cinematic Epic Music",
        category=AssetCategory.MUSIC,
        tags={"cinematic", "epic", "dramatic"}
    )

    if music_track:
        print(f"✓ Music track downloaded and imported: {music_track.name}")


def demo_search_and_filter():
    """Demo: Search and filter assets"""
    print("\n" + "=" * 60)
    print("DEMO 4: Search and Filter Assets")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    # Search by query
    print("\nSearching for 'product' assets...")
    results = library.search_assets(query="product")
    print(f"✓ Found {len(results)} assets matching 'product'")
    for asset in results[:3]:
        print(f"  - {asset.name} ({asset.asset_type.value})")

    # Filter by type
    print("\nGetting all video assets...")
    videos = library.search_assets(asset_type=AssetType.VIDEO)
    print(f"✓ Found {len(videos)} video assets")

    # Filter by category
    print("\nGetting all music assets...")
    music = library.search_assets(
        asset_type=AssetType.AUDIO,
        category=AssetCategory.MUSIC
    )
    print(f"✓ Found {len(music)} music assets")

    # Filter by tags
    print("\nSearching for assets tagged 'cinematic' and '4k'...")
    cinematic_4k = library.search_assets(tags={"cinematic", "4k"})
    print(f"✓ Found {len(cinematic_4k)} assets with both tags")

    # Filter by duration
    print("\nSearching for videos under 30 seconds...")
    short_videos = library.search_assets(
        asset_type=AssetType.VIDEO,
        max_duration=30.0
    )
    print(f"✓ Found {len(short_videos)} short videos")

    # Filter by resolution
    print("\nSearching for 4K videos...")
    uhd_videos = library.search_assets(
        asset_type=AssetType.VIDEO,
        min_resolution=(3840, 2160)
    )
    print(f"✓ Found {len(uhd_videos)} 4K videos")

    # Filter videos with audio
    print("\nSearching for videos with audio...")
    videos_with_audio = library.search_assets(
        asset_type=AssetType.VIDEO,
        has_audio=True
    )
    print(f"✓ Found {len(videos_with_audio)} videos with audio tracks")


def demo_favorites_and_usage():
    """Demo: Favorites and usage tracking"""
    print("\n" + "=" * 60)
    print("DEMO 5: Favorites and Usage Tracking")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    # Get first asset
    assets = list(library.assets.values())
    if not assets:
        print("No assets in library")
        return

    asset = assets[0]

    # Mark as favorite
    print(f"\nMarking '{asset.name}' as favorite...")
    library.set_favorite(asset.id, True)
    print("✓ Asset marked as favorite")

    # Mark as used
    print("\nTracking asset usage...")
    for i in range(5):
        library.mark_used(asset.id)
    print(f"✓ Asset used 5 times")
    print(f"  - Use count: {asset.use_count}")
    print(f"  - Last used: {asset.last_used}")

    # Get favorites
    print("\nGetting all favorites...")
    favorites = library.get_favorites()
    print(f"✓ Found {len(favorites)} favorite assets")
    for fav in favorites[:5]:
        print(f"  - {fav.name}")

    # Get recently used
    print("\nGetting recently used assets...")
    recent = library.get_recently_used(limit=10)
    print(f"✓ {len(recent)} recently used assets")
    for asset in recent:
        print(f"  - {asset.name} (used {asset.use_count} times)")


def demo_tagging():
    """Demo: Tag management"""
    print("\n" + "=" * 60)
    print("DEMO 6: Tag Management")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    assets = list(library.assets.values())
    if not assets:
        print("No assets in library")
        return

    asset = assets[0]

    # Add tags
    print(f"\nAdding tags to '{asset.name}'...")
    library.add_tag(asset.id, "premium")
    library.add_tag(asset.id, "featured")
    library.add_tag(asset.id, "trending")
    print(f"✓ Tags added: {asset.tags}")

    # Remove tag
    print("\nRemoving 'trending' tag...")
    library.remove_tag(asset.id, "trending")
    print(f"✓ Current tags: {asset.tags}")

    # Search by tags
    print("\nSearching for assets with 'premium' tag...")
    premium_assets = library.search_assets(tags={"premium"})
    print(f"✓ Found {len(premium_assets)} premium assets")


def demo_cloud_storage():
    """Demo: Cloud storage integration"""
    print("\n" + "=" * 60)
    print("DEMO 7: Cloud Storage Integration")
    print("=" * 60)

    # Initialize cloud storage
    try:
        cloud = CloudStorageManager(
            bucket_name="my-video-assets",
            credentials_path="/path/to/gcs-credentials.json"
        )

        library = AssetLibrary(
            storage_dir="/tmp/pro_asset_library",
            cloud_storage=cloud
        )

        print("✓ Cloud storage configured")

        assets = list(library.assets.values())
        if not assets:
            print("No assets in library")
            return

        asset = assets[0]

        # Upload to cloud
        print(f"\nUploading '{asset.name}' to cloud...")
        success = library.upload_to_cloud(asset.id, include_thumbnail=True)

        if success:
            print("✓ Asset uploaded to cloud storage")
            print(f"  - Cloud path: {asset.cloud_path}")
            if asset.thumbnail_cloud_path:
                print(f"  - Thumbnail: {asset.thumbnail_cloud_path}")
            print(f"  - Public URL: {cloud.get_public_url(asset.cloud_path.split('/')[-1])}")

    except ImportError:
        print("⚠ google-cloud-storage not installed")
        print("  Install with: pip install google-cloud-storage")
    except Exception as e:
        print(f"⚠ Cloud storage error: {e}")


def demo_versioning():
    """Demo: Asset versioning"""
    print("\n" + "=" * 60)
    print("DEMO 8: Asset Versioning")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    assets = list(library.assets.values())
    if not assets:
        print("No assets in library")
        return

    original = assets[0]

    # Create new version
    print(f"\nCreating new version of '{original.name}'...")
    new_version = library.create_version(
        asset_id=original.id,
        new_file_path="/path/to/updated/version.mp4"
    )

    if new_version:
        print(f"✓ New version created")
        print(f"  - Version: {new_version.version}")
        print(f"  - Parent ID: {new_version.parent_id}")

        # Get all versions
        print("\nGetting all versions...")
        versions = library.get_asset_versions(original.id)
        print(f"✓ Found {len(versions)} versions")
        for v in versions:
            print(f"  - v{v.version}: {v.name}")


def demo_organization():
    """Demo: Asset organization"""
    print("\n" + "=" * 60)
    print("DEMO 9: Asset Organization")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    # Organize by type
    print("\nOrganizing assets by type...")
    by_type = library.organize_by_type()
    print("✓ Assets organized by type:")
    for asset_type, assets in by_type.items():
        if assets:
            print(f"  - {asset_type.value}: {len(assets)} assets")

    # Organize by category
    print("\nOrganizing assets by category...")
    by_category = library.organize_by_category()
    print("✓ Assets organized by category:")
    for category, assets in by_category.items():
        if category:
            print(f"  - {category.value}: {len(assets)} assets")

    # Music library organization
    print("\nOrganizing music by mood...")
    audio_assets = library.search_assets(asset_type=AssetType.AUDIO)
    by_mood = MusicLibrary.categorize_by_mood(audio_assets)
    print("✓ Music organized by mood:")
    for mood, tracks in by_mood.items():
        if tracks:
            print(f"  - {mood}: {len(tracks)} tracks")

    print("\nOrganizing music by genre...")
    by_genre = MusicLibrary.categorize_by_genre(audio_assets)
    print("✓ Music organized by genre:")
    for genre, tracks in by_genre.items():
        if tracks:
            print(f"  - {genre}: {len(tracks)} tracks")


def demo_library_stats():
    """Demo: Library statistics"""
    print("\n" + "=" * 60)
    print("DEMO 10: Library Statistics")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    stats = library.get_library_stats()

    print("\nLibrary Statistics:")
    print(f"  Total assets: {stats['total_assets']}")
    print(f"  Total size: {stats['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"  Favorites: {stats['favorites_count']}")
    print(f"  With thumbnails: {stats['with_thumbnails']}")

    print("\nAssets by type:")
    for asset_type, count in stats['by_type'].items():
        print(f"  - {asset_type}: {count}")

    print("\nAssets by category:")
    for category, count in stats['by_category'].items():
        print(f"  - {category}: {count}")


def demo_thumbnail_generation():
    """Demo: Thumbnail generation"""
    print("\n" + "=" * 60)
    print("DEMO 11: Thumbnail Generation")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    assets = list(library.assets.values())
    if not assets:
        print("No assets in library")
        return

    for asset in assets[:3]:
        print(f"\nGenerating thumbnail for '{asset.name}'...")
        success = library.generate_asset_thumbnail(asset)

        if success:
            print(f"✓ Thumbnail generated")
            print(f"  - Path: {asset.thumbnail_path}")
        else:
            print(f"⚠ Thumbnail generation failed or not supported")


def demo_advanced_search():
    """Demo: Advanced search scenarios"""
    print("\n" + "=" * 60)
    print("DEMO 12: Advanced Search Scenarios")
    print("=" * 60)

    library = AssetLibrary(storage_dir="/tmp/pro_asset_library")

    # Find 4K videos under 60 seconds
    print("\nSearching for 4K videos under 60 seconds...")
    results = library.search_assets(
        asset_type=AssetType.VIDEO,
        min_resolution=(3840, 2160),
        max_duration=60.0
    )
    print(f"✓ Found {len(results)} matching videos")

    # Find cinematic LUTs
    print("\nSearching for cinematic LUTs...")
    results = library.search_assets(
        asset_type=AssetType.LUT,
        category=AssetCategory.CINEMATIC
    )
    print(f"✓ Found {len(results)} cinematic LUTs")

    # Find upbeat music between 2-4 minutes
    print("\nSearching for upbeat music (2-4 minutes)...")
    results = library.search_assets(
        asset_type=AssetType.AUDIO,
        tags={"upbeat"},
        min_duration=120.0,
        max_duration=240.0
    )
    print(f"✓ Found {len(results)} matching tracks")

    # Find lower third templates
    print("\nSearching for lower third templates...")
    results = library.search_assets(
        asset_type=AssetType.TEMPLATE,
        category=AssetCategory.LOWER_THIRD
    )
    print(f"✓ Found {len(results)} lower third templates")

    # Find HD videos without audio (for B-roll)
    print("\nSearching for HD B-roll (no audio)...")
    results = library.search_assets(
        asset_type=AssetType.VIDEO,
        category=AssetCategory.B_ROLL,
        min_resolution=(1920, 1080),
        has_audio=False
    )
    print(f"✓ Found {len(results)} B-roll clips")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("PROFESSIONAL ASSET LIBRARY MANAGER - COMPREHENSIVE DEMO")
    print("=" * 60)

    demos = [
        demo_basic_usage,
        demo_bulk_import,
        demo_import_from_url,
        demo_search_and_filter,
        demo_favorites_and_usage,
        demo_tagging,
        demo_cloud_storage,
        demo_versioning,
        demo_organization,
        demo_library_stats,
        demo_thumbnail_generation,
        demo_advanced_search,
    ]

    for i, demo in enumerate(demos, 1):
        try:
            demo()
        except Exception as e:
            print(f"\n⚠ Demo {i} error: {e}")

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
