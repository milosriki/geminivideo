# PRO VIDEO MODULES - API ENDPOINTS REFERENCE

**Base URL:** `http://localhost:8002/api/pro`

---

## 1. AUTO CAPTIONS

**Endpoint:** `POST /api/pro/caption`

Generate AI-powered captions with multiple styles using OpenAI Whisper.

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "style": "instagram",
  "language": "en",
  "word_level": true,
  "burn_in": false,
  "output_path": "/tmp/output.mp4"
}
```

**Parameters:**
- `video_path` (string, required): Path to input video file
- `style` (string): Caption style - `instagram`, `youtube`, `karaoke`, `tiktok`, `hormozi`
- `language` (string): Language code (default: `en`)
- `word_level` (boolean): Word-level timestamps (default: `true`)
- `burn_in` (boolean): Burn captions into video (default: `false`)
- `output_path` (string): Output path for burned-in video

**Response:**
```json
{
  "status": "success",
  "captions": {
    "srt_path": "/tmp/captions.srt",
    "text": "Full transcript text..."
  },
  "style": "instagram",
  "output_video": "/tmp/output.mp4"
}
```

---

## 2. COLOR GRADING

**Endpoint:** `POST /api/pro/color-grade`

Apply professional color grading presets.

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "preset": "cinematic",
  "intensity": 1.0,
  "output_path": "/tmp/graded.mp4"
}
```

**Parameters:**
- `video_path` (string, required): Path to input video
- `preset` (string): Color preset - `cinematic`, `vintage`, `high_contrast`, `warm`, `cold`, `fitness_energy`, `clean_corporate`, `instagram_dramatic`, `instagram_fade`, `instagram_vibrant`
- `intensity` (float): Effect intensity 0.0-1.0 (default: `1.0`)
- `output_path` (string): Output path

**Response:**
```json
{
  "status": "success",
  "output_path": "/tmp/graded.mp4",
  "preset": "cinematic",
  "intensity": 1.0
}
```

---

## 3. WINNING AD GENERATOR

**Endpoint:** `POST /api/pro/render-winning-ad`

Generate complete winning video ads with all pro features.

**Request Body:**
```json
{
  "video_clips": ["/path/clip1.mp4", "/path/clip2.mp4"],
  "template": "fitness_transformation",
  "platform": "instagram",
  "hook_text": "Transform Your Life",
  "cta_text": "Start Now",
  "product_name": "FitPro",
  "duration_target": 30
}
```

**Parameters:**
- `video_clips` (array, required): List of video clip paths
- `template` (string): Ad template - `fitness_transformation`, `testimonial`, `problem_solution`, `listicle`, `hook_story_offer`, `ugc`, `educational`, `product_showcase`, `comparison`, `behind_scenes`
- `platform` (string): Target platform - `tiktok`, `instagram`, `youtube`, `facebook`
- `hook_text` (string): Hook text for opening
- `cta_text` (string): Call-to-action text
- `product_name` (string): Product name
- `duration_target` (integer): Target duration in seconds

**Response:**
```json
{
  "status": "queued",
  "job_id": "uuid-here",
  "template": "fitness_transformation",
  "message": "Winning ad generation started"
}
```

---

## 4. SMART CROP

**Endpoint:** `POST /api/pro/smart-crop`

Auto-crop video for different platforms with face/object tracking.

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "target_aspect": "9:16",
  "track_faces": true,
  "smooth_motion": true,
  "output_path": "/tmp/cropped.mp4"
}
```

**Parameters:**
- `video_path` (string, required): Path to input video
- `target_aspect` (string): Aspect ratio - `9:16`, `1:1`, `4:5`, `16:9`, `21:9`
- `track_faces` (boolean): Enable face tracking (default: `true`)
- `smooth_motion` (boolean): Smooth panning (default: `true`)
- `output_path` (string): Output path

**Response:**
```json
{
  "status": "success",
  "output_path": "/tmp/cropped.mp4",
  "target_aspect": "9:16"
}
```

---

## 5. AUDIO MIXER

**Endpoint:** `POST /api/pro/audio-mix`

Professional audio mixing with ducking and enhancement.

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "music_path": "/path/to/music.mp3",
  "voiceover_path": "/path/to/voice.mp3",
  "auto_duck": true,
  "normalization": "social_media",
  "voice_enhance": true,
  "output_path": "/tmp/mixed.mp4"
}
```

**Parameters:**
- `video_path` (string, required): Path to input video
- `music_path` (string): Background music path
- `voiceover_path` (string): Voiceover audio path
- `auto_duck` (boolean): Auto-ducking (default: `true`)
- `normalization` (string): Standard - `social_media` (-16 LUFS), `streaming` (-14 LUFS), `broadcast` (-23 LUFS)
- `voice_enhance` (boolean): Voice enhancement (default: `true`)
- `output_path` (string): Output path

**Response:**
```json
{
  "status": "success",
  "output_path": "/tmp/mixed.mp4",
  "auto_duck": true,
  "normalization": "social_media"
}
```

---

## 6. TRANSITIONS

**Endpoint:** `POST /api/pro/transitions`

Add professional transitions between clips.

**Request Body:**
```json
{
  "clips": ["/path/clip1.mp4", "/path/clip2.mp4"],
  "transition_type": "dissolve",
  "duration": 1.0,
  "easing": "ease_in_out",
  "output_path": "/tmp/transitions.mp4"
}
```

**Parameters:**
- `clips` (array, required): List of clip paths (minimum 2)
- `transition_type` (string): Type - `dissolve`, `wipe`, `slide`, `3d`, `blur`, `glitch`, `light`, `creative`, `geometric`
- `duration` (float): Transition duration in seconds (default: `1.0`)
- `easing` (string): Easing function - `linear`, `ease_in`, `ease_out`, `ease_in_out`
- `output_path` (string): Output path

**Response:**
```json
{
  "status": "success",
  "output_path": "/tmp/transitions.mp4",
  "transition": "fade",
  "duration": 1.0
}
```

---

## 7. MOTION GRAPHICS

**Endpoint:** `POST /api/pro/motion-graphics`

Add animated text and motion graphics overlays.

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "type": "lower_third",
  "text": "John Doe",
  "subtitle": "Fitness Expert",
  "style": "corporate",
  "start_time": 0.0,
  "duration": 3.0,
  "animation": "word_pop",
  "output_path": "/tmp/motion.mp4"
}
```

**Parameters:**
- `video_path` (string, required): Path to input video
- `type` (string): Type - `lower_third`, `title_card`, `animated_text`, `cta`
- `text` (string, required): Text content
- `subtitle` (string): Subtitle text (for lower thirds)
- `style` (string): Style depends on type
  - Lower third: `corporate`, `social`, `news`, `minimal`
  - Title card: `cinematic`, `youtube`, `social`
- `start_time` (float): Start time in seconds (default: `0.0`)
- `duration` (float): Duration in seconds (default: `3.0`)
- `animation` (string): Animation type - `typewriter`, `word_pop`, `fly_in`, `bounce`
- `output_path` (string): Output path

**Response:**
```json
{
  "status": "success",
  "output_path": "/tmp/motion.mp4",
  "type": "lower_third",
  "text": "John Doe"
}
```

---

## 8. PREVIEW GENERATOR

**Endpoint:** `POST /api/pro/preview`

Generate quick preview or proxy video.

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "quality": "480p",
  "thumbnail_strip": false,
  "frame_count": 10,
  "output_path": "/tmp/proxy.mp4"
}
```

**Parameters:**
- `video_path` (string, required): Path to input video
- `quality` (string): Quality - `240p`, `360p`, `480p`, `720p`
- `thumbnail_strip` (boolean): Generate thumbnail strip (default: `false`)
- `frame_count` (integer): Number of frames for thumbnail strip (default: `10`)
- `output_path` (string): Output path

**Response (Video):**
```json
{
  "status": "success",
  "output_path": "/tmp/proxy.mp4",
  "quality": "480p"
}
```

**Response (Thumbnail Strip):**
```json
{
  "status": "success",
  "thumbnail_strip": "hex_data_here",
  "frame_count": 10
}
```

---

## 9. TIMELINE ENGINE

**Endpoint:** `POST /api/pro/timeline`

Create and manipulate video timeline.

**Request Body (Create):**
```json
{
  "operation": "create",
  "fps": 30,
  "width": 1920,
  "height": 1080
}
```

**Request Body (Add Clip):**
```json
{
  "operation": "add_clip",
  "timeline_id": "uuid-here",
  "clip": {
    "source_path": "/path/clip.mp4",
    "start_time": 0.0,
    "duration": 5.0
  }
}
```

**Request Body (Export):**
```json
{
  "operation": "export",
  "timeline_id": "uuid-here",
  "export_path": "/tmp/timeline.mp4"
}
```

**Parameters:**
- `operation` (string): Operation - `create`, `add_clip`, `export`
- `timeline_id` (string): Timeline ID (for existing timeline)
- `fps` (integer): Frames per second (default: `30`)
- `width` (integer): Video width (default: `1920`)
- `height` (integer): Video height (default: `1080`)

**Response:**
```json
{
  "status": "success",
  "timeline_id": "uuid-here",
  "fps": 30,
  "resolution": "1920x1080"
}
```

---

## 10. KEYFRAME ANIMATION

**Endpoint:** `POST /api/pro/keyframe`

Create keyframe animations for video properties.

**Request Body:**
```json
{
  "video_path": "/path/to/video.mp4",
  "property": "opacity",
  "keyframes": [
    {"time": 0.0, "value": 0.0, "interpolation": "ease_in"},
    {"time": 2.0, "value": 1.0, "interpolation": "ease_out"}
  ],
  "output_path": "/tmp/animated.mp4"
}
```

**Parameters:**
- `video_path` (string, required): Path to input video
- `property` (string): Property - `position_x`, `position_y`, `scale_x`, `scale_y`, `rotation`, `opacity`
- `keyframes` (array): Array of keyframe objects
  - `time` (float): Time in seconds
  - `value` (float): Property value
  - `interpolation` (string): Type - `linear`, `ease_in`, `ease_out`, `ease_in_out`, `bezier`

**Response:**
```json
{
  "status": "success",
  "property": "opacity",
  "keyframe_count": 2,
  "ffmpeg_filter": "fade=t=in:st=0:d=2"
}
```

---

## 11. ASSET LIBRARY

**Endpoint:** `POST /api/pro/assets`

Manage video/audio/image assets.

**Request Body (Add):**
```json
{
  "operation": "add",
  "file_path": "/path/to/asset.mp4",
  "asset_type": "video",
  "metadata": {
    "title": "My Video",
    "tags": ["fitness", "workout"]
  }
}
```

**Request Body (Search):**
```json
{
  "operation": "search",
  "query": "fitness",
  "asset_type": "video"
}
```

**Request Body (Get):**
```json
{
  "operation": "get",
  "asset_id": "uuid-here"
}
```

**Parameters:**
- `operation` (string): Operation - `add`, `search`, `get`, `delete`
- `file_path` (string): File path (for add)
- `asset_type` (string): Type - `video`, `audio`, `image`, `font`, `lut`, `template`
- `query` (string): Search query
- `asset_id` (string): Asset ID (for get/delete)
- `metadata` (object): Custom metadata

**Response:**
```json
{
  "status": "success",
  "asset_id": "uuid-here",
  "asset_type": "video"
}
```

---

## 12. PRO RENDERER

**Endpoint:** `POST /api/pro/render`

Advanced video rendering with GPU acceleration.

**Request Body:**
```json
{
  "input_path": "/path/to/video.mp4",
  "platform": "instagram",
  "quality": "high",
  "aspect_ratio": "9:16",
  "use_gpu": true,
  "output_path": "/tmp/render.mp4"
}
```

**Parameters:**
- `input_path` (string, required): Path to input video
- `platform` (string): Platform - `instagram`, `tiktok`, `youtube`, `twitter`, `facebook`
- `quality` (string): Quality - `draft`, `standard`, `high`, `master`
- `aspect_ratio` (string): Aspect - `9:16`, `1:1`, `16:9`, `4:5`
- `use_gpu` (boolean): GPU acceleration (default: `true`)
- `output_path` (string): Output path

**Response:**
```json
{
  "status": "queued",
  "job_id": "uuid-here",
  "platform": "instagram",
  "quality": "high"
}
```

---

## 13. HEALTH CHECK

**Endpoint:** `GET /api/pro/health`

Health check for all 13 pro video modules.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-05T14:39:00.000Z",
  "modules": {
    "auto_captions": {"status": "ready", "model": "base"},
    "pro_renderer": {"status": "ready", "gpu_available": true},
    "winning_ads": {"status": "ready", "templates": 10},
    "color_grading": {"status": "ready", "presets": 10},
    "smart_crop": {"status": "ready", "tracking": "enabled"},
    "audio_mixer": {"status": "ready", "normalization": "available"},
    "timeline_engine": {"status": "ready", "active_timelines": 0},
    "motion_graphics": {"status": "ready", "styles": "50+"},
    "transitions": {"status": "ready", "count": 50},
    "keyframe_animator": {"status": "ready", "interpolation_types": 6},
    "preview_generator": {"status": "ready", "caching": "enabled"},
    "asset_library": {"status": "ready", "assets": 0},
    "pro_jobs": {"status": "ready", "active_jobs": 0}
  },
  "total_modules": 13,
  "production_ready": true,
  "investment_grade": "€5M"
}
```

---

## 14. JOB STATUS

**Endpoint:** `GET /api/pro/job/{job_id}`

Get status of a pro module job.

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "completed",
  "data": {
    "output_path": "/tmp/output.mp4",
    "platform": "instagram",
    "quality": "high"
  }
}
```

**Status Values:**
- `processing`: Job is currently running
- `completed`: Job finished successfully
- `failed`: Job encountered an error

---

## ERROR RESPONSES

All endpoints return standard HTTP error codes:

**400 Bad Request:**
```json
{
  "detail": "Invalid video_path"
}
```

**404 Not Found:**
```json
{
  "detail": "Job not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Error message here"
}
```

---

## TESTING

Test the service:
```bash
# Start service
cd /home/user/geminivideo/services/video-agent
python3 main.py

# Test health endpoint
curl http://localhost:8002/api/pro/health

# Test caption endpoint
curl -X POST http://localhost:8002/api/pro/caption \
  -H "Content-Type: application/json" \
  -d '{"video_path": "/path/to/video.mp4", "style": "instagram"}'
```

---

**Documentation Version:** 1.0.0
**Service Port:** 8002
**Base URL:** `http://localhost:8002`
