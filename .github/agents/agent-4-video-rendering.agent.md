# Agent 4: Video Rendering Engineer

## Your Mission
Implement real FFmpeg video rendering with MoviePy composition and transitions.

## Priority: MEDIUM (Wait for Agent 2 emotion data)

## Tasks

### 1. Install Dependencies
```bash
pip install moviepy ffmpeg-python pillow
```

### 2. Video Rendering Engine
Create `services/video-agent/src/render/engine.py`:
```python
from moviepy.editor import *
import ffmpeg
import os

class VideoRenderer:
    def __init__(self, output_dir='/outputs'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def render_from_storyboard(self, storyboard: dict, job_id: str) -> str:
        """
        Render video from storyboard
        storyboard = {
            'clips': [{'clip_id': '', 'start': 0, 'end': 5, 'transition': 'fade'}],
            'resolution': '1920x1080',
            'fps': 30,
            'audio_track': 'path/to/audio.mp3'
        }
        """
        clips = []

        for clip_spec in storyboard['clips']:
            clip = self._load_clip(clip_spec)
            clips.append(clip)

        # Concatenate with transitions
        final_video = self._concatenate_with_transitions(
            clips,
            storyboard.get('transitions', [])
        )

        # Add audio if specified
        if storyboard.get('audio_track'):
            audio = AudioFileClip(storyboard['audio_track'])
            final_video = final_video.set_audio(audio)

        # Add overlays (CTAs, text)
        if storyboard.get('overlays'):
            final_video = self._add_overlays(final_video, storyboard['overlays'])

        # Render
        output_path = f"{self.output_dir}/{job_id}.mp4"
        final_video.write_videofile(
            output_path,
            fps=storyboard.get('fps', 30),
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=4
        )

        return output_path

    def _load_clip(self, clip_spec: dict) -> VideoClip:
        """Load clip from asset with trim"""
        # Get asset path from DB
        from shared.db import SessionLocal
        from shared.models import Asset, Clip

        db = SessionLocal()
        clip = db.query(Clip).filter(Clip.clip_id == clip_spec['clip_id']).first()
        asset = db.query(Asset).filter(Asset.asset_id == clip.asset_id).first()
        db.close()

        # Load and trim
        video = VideoFileClip(asset.path)
        trimmed = video.subclip(clip.start_time, clip.end_time)

        return trimmed

    def _concatenate_with_transitions(self, clips: list, transitions: list) -> VideoClip:
        """Concatenate clips with transitions"""
        if len(clips) == 0:
            raise ValueError("No clips to concatenate")

        if len(clips) == 1:
            return clips[0]

        # Add transitions between clips
        result_clips = [clips[0]]

        for i in range(1, len(clips)):
            transition = transitions[i-1] if i-1 < len(transitions) else 'cut'

            if transition == 'fade':
                # Fade out previous, fade in next
                result_clips[-1] = result_clips[-1].fadeout(0.5)
                clips[i] = clips[i].fadein(0.5)
            elif transition == 'crossfade':
                # Overlap clips
                result_clips[-1] = result_clips[-1].crossfadeout(1.0)
                clips[i] = clips[i].crossfadein(1.0)

            result_clips.append(clips[i])

        return concatenate_videoclips(result_clips, method='compose')

    def _add_overlays(self, video: VideoClip, overlays: list) -> VideoClip:
        """Add text/CTA overlays"""
        for overlay in overlays:
            if overlay['type'] == 'text':
                txt_clip = TextClip(
                    overlay['text'],
                    fontsize=overlay.get('fontsize', 50),
                    color=overlay.get('color', 'white'),
                    font=overlay.get('font', 'Arial-Bold')
                )
                txt_clip = txt_clip.set_position(overlay.get('position', ('center', 'bottom')))
                txt_clip = txt_clip.set_start(overlay.get('start', 0))
                txt_clip = txt_clip.set_duration(overlay.get('duration', 3))

                video = CompositeVideoClip([video, txt_clip])

        return video

    def create_preview(self, storyboard: dict, job_id: str, duration: int = 5) -> str:
        """Create quick preview (first 5 seconds, lower quality)"""
        # Simplified render for preview
        clips = []
        total_duration = 0

        for clip_spec in storyboard['clips']:
            if total_duration >= duration:
                break
            clip = self._load_clip(clip_spec)
            remaining = duration - total_duration
            if clip.duration > remaining:
                clip = clip.subclip(0, remaining)
            clips.append(clip)
            total_duration += clip.duration

        video = concatenate_videoclips(clips)

        output_path = f"{self.output_dir}/{job_id}_preview.mp4"
        video.write_videofile(
            output_path,
            fps=15,  # Lower FPS
            preset='ultrafast',
            threads=2
        )

        return output_path

# Global renderer
renderer = VideoRenderer()
```

### 3. Update Video Agent Service
Update `services/video-agent/src/index.py`:
```python
from render.engine import renderer
from shared.db import get_db, SessionLocal
from shared.models import RenderJob
import asyncio

@app.post("/render/remix")
async def create_render_job(storyboard: dict, preview_only: bool = False):
    """Queue a render job"""
    db = SessionLocal()

    job = RenderJob(
        storyboard=storyboard,
        status='queued'
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    job_id = str(job.job_id)
    db.close()

    # Start rendering in background
    asyncio.create_task(process_render_job(job_id, preview_only))

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Render job created"
    }

async def process_render_job(job_id: str, preview_only: bool = False):
    """Background task to render video"""
    db = SessionLocal()

    try:
        job = db.query(RenderJob).filter(RenderJob.job_id == job_id).first()
        job.status = 'processing'
        db.commit()

        # Render
        if preview_only:
            output_path = renderer.create_preview(job.storyboard, job_id)
        else:
            output_path = renderer.render_from_storyboard(job.storyboard, job_id)

        # Update job
        job.status = 'completed'
        job.output_url = output_path
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        db.commit()
    finally:
        db.close()

@app.get("/render/status/{job_id}")
async def get_render_status(job_id: str, db: Session = Depends(get_db)):
    """Check render job status"""
    job = db.query(RenderJob).filter(RenderJob.job_id == job_id).first()
    if not job:
        raise HTTPException(404, "Job not found")

    return {
        "job_id": str(job.job_id),
        "status": job.status,
        "output_url": job.output_url,
        "error": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None
    }
```

### 4. Smart Storyboard Generation
Create `services/video-agent/src/storyboard/generator.py`:
```python
def generate_optimal_storyboard(clips: list, target_duration: float = 30.0) -> dict:
    """
    Generate storyboard from clips prioritizing emotion and scores
    Target: 30-60s ads with max conversion
    """
    # Sort by composite score (includes emotion)
    sorted_clips = sorted(
        clips,
        key=lambda c: c.composite_score + c.emotion_data.get('priority_score', 0),
        reverse=True
    )

    # Select clips to fit duration
    selected = []
    total_duration = 0

    for clip in sorted_clips:
        if total_duration + clip.duration <= target_duration:
            selected.append({
                'clip_id': str(clip.clip_id),
                'start': clip.start_time,
                'end': clip.end_time,
                'transition': 'fade' if len(selected) > 0 else 'cut'
            })
            total_duration += clip.duration

        if total_duration >= target_duration * 0.9:  # 90% of target
            break

    # Add CTA overlay at end
    overlays = [{
        'type': 'text',
        'text': 'Learn More',
        'position': ('center', 'bottom'),
        'start': total_duration - 3,
        'duration': 3,
        'fontsize': 60,
        'color': 'white'
    }]

    return {
        'clips': selected,
        'resolution': '1920x1080',
        'fps': 30,
        'overlays': overlays
    }
```

## Deliverables
- [ ] MoviePy rendering engine working
- [ ] Storyboard-based video generation
- [ ] Transitions (fade, crossfade)
- [ ] Text overlays/CTAs
- [ ] Preview generation (fast)
- [ ] Smart storyboard generator
- [ ] Tests for rendering

## Branch
`agent-4-video-rendering`

## Blockers
- **Agent 2** (needs emotion data for prioritization)

## Who Depends On You
- Agent 5 (frontend needs render endpoints)
- Agent 7 (Meta publisher needs rendered videos)
