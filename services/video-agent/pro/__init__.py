"""
Pro-grade video editing features
"""

from .motion_graphics import (
    MotionGraphicsEngine,
    AnimationType,
    LowerThirdStyle,
    TitleCardStyle,
    CTAType,
    AnimatedText,
    LowerThird,
    TitleCard,
    CTAOverlay,
    ProgressBar,
    Timer,
    SocialMediaElement,
    LottieAnimation,
    create_lower_third,
    create_title_card,
    create_animated_text,
)

from .asset_library import (
    AssetLibrary,
    Asset,
    AssetType,
    AssetCategory,
    AssetSearch,
    VideoMetadata,
    AudioMetadata,
    ImageMetadata,
    FontMetadata,
    LUTMetadata,
    TemplateMetadata,
    CloudStorageManager,
    FFProbeExtractor,
    ThumbnailGenerator,
    StockFootageProvider,
    MusicLibrary,
    VideoCodec,
    AudioCodec,
)

from .motion_moment_sdk import (
    MotionMomentSDK,
    MotionMoment,
    TemporalWindow,
)

__all__ = [
    # Motion Graphics
    'MotionGraphicsEngine',
    'AnimationType',
    'LowerThirdStyle',
    'TitleCardStyle',
    'CTAType',
    'AnimatedText',
    'LowerThird',
    'TitleCard',
    'CTAOverlay',
    'ProgressBar',
    'Timer',
    'SocialMediaElement',
    'LottieAnimation',
    'create_lower_third',
    'create_title_card',
    'create_animated_text',
    # Asset Library
    'AssetLibrary',
    'Asset',
    'AssetType',
    'AssetCategory',
    'AssetSearch',
    'VideoMetadata',
    'AudioMetadata',
    'ImageMetadata',
    'FontMetadata',
    'LUTMetadata',
    'TemplateMetadata',
    'CloudStorageManager',
    'FFProbeExtractor',
    'ThumbnailGenerator',
    'StockFootageProvider',
    'MusicLibrary',
    'VideoCodec',
    'AudioCodec',
    # Motion Moment SDK
    'MotionMomentSDK',
    'MotionMoment',
    'TemporalWindow',
]
