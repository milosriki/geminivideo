import React, { useRef, useEffect, useState, useCallback } from 'react';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface Point {
  x: number;
  y: number;
}

interface Rect {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Clip {
  id: string;
  trackId: string;
  startTime: number;
  duration: number;
  trimStart: number;
  trimEnd: number;
  name: string;
  type: 'video' | 'audio' | 'text' | 'image';
  thumbnailUrl?: string;
  waveformData?: number[];
  effects: Effect[];
  keyframes: Keyframe[];
  transition?: Transition;
}

interface Keyframe {
  time: number;
  property: string;
  value: any;
}

interface Effect {
  id: string;
  name: string;
  enabled: boolean;
}

interface Transition {
  type: 'crossfade' | 'wipe' | 'slide';
  duration: number;
}

interface Track {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'text';
  height: number;
  locked: boolean;
  muted: boolean;
  solo: boolean;
  collapsed: boolean;
}

interface TimelineState {
  tracks: Track[];
  clips: Clip[];
  currentTime: number;
  duration: number;
  zoom: number;
  scrollX: number;
  scrollY: number;
  selectedClipIds: string[];
  inPoint: number | null;
  outPoint: number | null;
  rippleMode: boolean;
  snapEnabled: boolean;
}

interface DragState {
  isDragging: boolean;
  dragType: 'move' | 'trim-start' | 'trim-end' | 'playhead' | 'select' | null;
  startPos: Point;
  currentPos: Point;
  originalClipData: Map<string, { startTime: number; duration: number; trimStart: number; trimEnd: number }>;
  dragClipId: string | null;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const TRACK_HEADER_WIDTH = 200;
const TIMELINE_RULER_HEIGHT = 40;
const DEFAULT_TRACK_HEIGHT = 80;
const CLIP_PADDING = 4;
const RESIZE_HANDLE_WIDTH = 8;
const PLAYHEAD_WIDTH = 2;
const SNAP_THRESHOLD = 10;
const MIN_CLIP_WIDTH = 20;
const ZOOM_LEVELS = [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 20];

// Colors
const COLORS = {
  background: '#1e1e1e',
  trackBg: '#252525',
  trackAlt: '#2a2a2a',
  trackHeader: '#1a1a1a',
  clipVideo: '#4a90e2',
  clipAudio: '#50c878',
  clipText: '#e28b4a',
  clipImage: '#9b59b6',
  clipSelected: '#6ab0ff',
  clipHover: 'rgba(255, 255, 255, 0.1)',
  playhead: '#ff3b3b',
  inOutPoint: '#ffa500',
  ruler: '#333333',
  rulerText: '#999999',
  waveform: '#50c878',
  keyframe: '#ffd700',
  effectBadge: '#9b59b6',
  snapLine: '#ff00ff',
  selection: 'rgba(106, 176, 255, 0.3)',
  border: '#404040',
  text: '#ffffff',
  textSecondary: '#999999',
  transition: '#ff69b4',
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function timeToPixels(time: number, zoom: number): number {
  return time * zoom * 100; // 100 pixels per second at 1x zoom
}

function pixelsToTime(pixels: number, zoom: number): number {
  return pixels / (zoom * 100);
}

function formatTime(seconds: number, zoomLevel: number): string {
  if (zoomLevel > 5) {
    // Show frames
    const fps = 30;
    const frames = Math.floor(seconds * fps);
    const secs = Math.floor(seconds);
    const frame = frames % fps;
    return `${secs}:${frame.toString().padStart(2, '0')}`;
  } else if (zoomLevel > 1) {
    // Show seconds
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  } else {
    // Show minutes:seconds
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }
}

function getClipColor(type: string, selected: boolean): string {
  const baseColor = {
    video: COLORS.clipVideo,
    audio: COLORS.clipAudio,
    text: COLORS.clipText,
    image: COLORS.clipImage,
  }[type] || COLORS.clipVideo;

  return selected ? COLORS.clipSelected : baseColor;
}

function pointInRect(point: Point, rect: Rect): boolean {
  return (
    point.x >= rect.x &&
    point.x <= rect.x + rect.width &&
    point.y >= rect.y &&
    point.y <= rect.y + rect.height
  );
}

function snapToValue(value: number, snapPoints: number[], threshold: number, zoom: number): number {
  const pixelThreshold = threshold / zoom;
  for (const point of snapPoints) {
    if (Math.abs(value - point) < pixelThreshold) {
      return point;
    }
  }
  return value;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

interface TimelineCanvasProps {
  timeline: TimelineState;
  onTimelineChange: (timeline: TimelineState) => void;
  onClipSelect: (clipIds: string[]) => void;
  onTimeChange: (time: number) => void;
  onContextMenu?: (clipId: string | null, position: Point) => void;
}

const TimelineCanvas: React.FC<TimelineCanvasProps> = ({
  timeline,
  onTimelineChange,
  onClipSelect,
  onTimeChange,
  onContextMenu,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animationFrameRef = useRef<number>();
  const thumbnailCacheRef = useRef<Map<string, HTMLImageElement>>(new Map());

  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [dragState, setDragState] = useState<DragState>({
    isDragging: false,
    dragType: null,
    startPos: { x: 0, y: 0 },
    currentPos: { x: 0, y: 0 },
    originalClipData: new Map(),
    dragClipId: null,
  });
  const [hoveredClipId, setHoveredClipId] = useState<string | null>(null);
  const [hoveredHandle, setHoveredHandle] = useState<'start' | 'end' | null>(null);
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPos, setContextMenuPos] = useState<Point>({ x: 0, y: 0 });

  // ============================================================================
  // RESIZE HANDLER
  // ============================================================================

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // ============================================================================
  // THUMBNAIL LOADING
  // ============================================================================

  useEffect(() => {
    timeline.clips.forEach((clip) => {
      if (clip.thumbnailUrl && !thumbnailCacheRef.current.has(clip.id)) {
        const img = new Image();
        img.src = clip.thumbnailUrl;
        img.onload = () => {
          thumbnailCacheRef.current.set(clip.id, img);
        };
      }
    });
  }, [timeline.clips]);

  // ============================================================================
  // CLIP POSITION CALCULATIONS
  // ============================================================================

  const getClipRect = useCallback((clip: Clip): Rect => {
    const trackIndex = timeline.tracks.findIndex((t) => t.id === clip.trackId);
    if (trackIndex === -1) return { x: 0, y: 0, width: 0, height: 0 };

    const track = timeline.tracks[trackIndex];
    const x = TRACK_HEADER_WIDTH + timeToPixels(clip.startTime, timeline.zoom) - timeline.scrollX;
    const y = TIMELINE_RULER_HEIGHT +
              timeline.tracks.slice(0, trackIndex).reduce((sum, t) => sum + t.height, 0) -
              timeline.scrollY;
    const width = timeToPixels(clip.duration, timeline.zoom);
    const height = track.height - CLIP_PADDING * 2;

    return { x, y: y + CLIP_PADDING, width, height };
  }, [timeline.tracks, timeline.zoom, timeline.scrollX, timeline.scrollY]);

  const getTrackAtY = useCallback((y: number): Track | null => {
    let currentY = TIMELINE_RULER_HEIGHT - timeline.scrollY;
    for (const track of timeline.tracks) {
      if (y >= currentY && y < currentY + track.height) {
        return track;
      }
      currentY += track.height;
    }
    return null;
  }, [timeline.tracks, timeline.scrollY]);

  const getClipAtPoint = useCallback((point: Point): Clip | null => {
    for (let i = timeline.clips.length - 1; i >= 0; i--) {
      const clip = timeline.clips[i];
      const rect = getClipRect(clip);
      if (pointInRect(point, rect)) {
        return clip;
      }
    }
    return null;
  }, [timeline.clips, getClipRect]);

  // ============================================================================
  // SNAP CALCULATIONS
  // ============================================================================

  const getSnapPoints = useCallback((): number[] => {
    const points: number[] = [0, timeline.duration];

    if (timeline.inPoint !== null) points.push(timeline.inPoint);
    if (timeline.outPoint !== null) points.push(timeline.outPoint);

    timeline.clips.forEach((clip) => {
      if (!timeline.selectedClipIds.includes(clip.id)) {
        points.push(clip.startTime);
        points.push(clip.startTime + clip.duration);
      }
    });

    return points.sort((a, b) => a - b);
  }, [timeline.clips, timeline.selectedClipIds, timeline.duration, timeline.inPoint, timeline.outPoint]);

  // ============================================================================
  // DRAWING FUNCTIONS
  // ============================================================================

  const drawTimeRuler = useCallback((ctx: CanvasRenderingContext2D, width: number) => {
    ctx.fillStyle = COLORS.ruler;
    ctx.fillRect(TRACK_HEADER_WIDTH, 0, width - TRACK_HEADER_WIDTH, TIMELINE_RULER_HEIGHT);

    ctx.strokeStyle = COLORS.border;
    ctx.beginPath();
    ctx.moveTo(TRACK_HEADER_WIDTH, TIMELINE_RULER_HEIGHT);
    ctx.lineTo(width, TIMELINE_RULER_HEIGHT);
    ctx.stroke();

    // Draw time markers
    const visibleStartTime = pixelsToTime(timeline.scrollX, timeline.zoom);
    const visibleEndTime = pixelsToTime(timeline.scrollX + width - TRACK_HEADER_WIDTH, timeline.zoom);

    let interval = 1; // seconds
    if (timeline.zoom < 0.1) interval = 60;
    else if (timeline.zoom < 0.5) interval = 10;
    else if (timeline.zoom < 1) interval = 5;
    else if (timeline.zoom > 5) interval = 1 / 30; // frames

    const startMarker = Math.floor(visibleStartTime / interval) * interval;

    ctx.fillStyle = COLORS.rulerText;
    ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    for (let time = startMarker; time <= visibleEndTime; time += interval) {
      const x = TRACK_HEADER_WIDTH + timeToPixels(time, timeline.zoom) - timeline.scrollX;

      ctx.strokeStyle = COLORS.border;
      ctx.beginPath();
      ctx.moveTo(x, TIMELINE_RULER_HEIGHT - 10);
      ctx.lineTo(x, TIMELINE_RULER_HEIGHT);
      ctx.stroke();

      ctx.fillText(formatTime(time, timeline.zoom), x, TIMELINE_RULER_HEIGHT / 2);
    }

    // Draw in/out points
    if (timeline.inPoint !== null) {
      const x = TRACK_HEADER_WIDTH + timeToPixels(timeline.inPoint, timeline.zoom) - timeline.scrollX;
      ctx.fillStyle = COLORS.inOutPoint;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x + 8, 0);
      ctx.lineTo(x, 8);
      ctx.closePath();
      ctx.fill();
    }

    if (timeline.outPoint !== null) {
      const x = TRACK_HEADER_WIDTH + timeToPixels(timeline.outPoint, timeline.zoom) - timeline.scrollX;
      ctx.fillStyle = COLORS.inOutPoint;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x - 8, 0);
      ctx.lineTo(x, 8);
      ctx.closePath();
      ctx.fill();
    }
  }, [timeline.zoom, timeline.scrollX, timeline.inPoint, timeline.outPoint]);

  const drawTrackHeaders = useCallback((ctx: CanvasRenderingContext2D, height: number) => {
    let y = TIMELINE_RULER_HEIGHT - timeline.scrollY;

    timeline.tracks.forEach((track, index) => {
      // Background
      ctx.fillStyle = COLORS.trackHeader;
      ctx.fillRect(0, y, TRACK_HEADER_WIDTH, track.height);

      // Border
      ctx.strokeStyle = COLORS.border;
      ctx.beginPath();
      ctx.moveTo(TRACK_HEADER_WIDTH, y);
      ctx.lineTo(TRACK_HEADER_WIDTH, y + track.height);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(0, y + track.height);
      ctx.lineTo(TRACK_HEADER_WIDTH, y + track.height);
      ctx.stroke();

      // Track name
      ctx.fillStyle = COLORS.text;
      ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText(track.name, 10, y + 10);

      // Track type badge
      ctx.fillStyle = track.type === 'video' ? COLORS.clipVideo :
                     track.type === 'audio' ? COLORS.clipAudio : COLORS.clipText;
      ctx.font = '9px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(track.type.toUpperCase(), 10, y + 28);

      // Status indicators
      const indicators: string[] = [];
      if (track.locked) indicators.push('L');
      if (track.muted) indicators.push('M');
      if (track.solo) indicators.push('S');

      if (indicators.length > 0) {
        ctx.fillStyle = COLORS.textSecondary;
        ctx.font = '10px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.fillText(indicators.join(' '), 10, y + track.height - 20);
      }

      y += track.height;
    });

    // Fill remaining space
    if (y < height) {
      ctx.fillStyle = COLORS.trackHeader;
      ctx.fillRect(0, y, TRACK_HEADER_WIDTH, height - y);
    }
  }, [timeline.tracks, timeline.scrollY]);

  const drawTracks = useCallback((ctx: CanvasRenderingContext2D, width: number, height: number) => {
    let y = TIMELINE_RULER_HEIGHT - timeline.scrollY;

    timeline.tracks.forEach((track, index) => {
      // Background
      ctx.fillStyle = index % 2 === 0 ? COLORS.trackBg : COLORS.trackAlt;
      ctx.fillRect(TRACK_HEADER_WIDTH, y, width - TRACK_HEADER_WIDTH, track.height);

      // Border
      ctx.strokeStyle = COLORS.border;
      ctx.beginPath();
      ctx.moveTo(TRACK_HEADER_WIDTH, y + track.height);
      ctx.lineTo(width, y + track.height);
      ctx.stroke();

      y += track.height;
    });

    // Fill remaining space
    if (y < height) {
      ctx.fillStyle = COLORS.background;
      ctx.fillRect(TRACK_HEADER_WIDTH, y, width - TRACK_HEADER_WIDTH, height - y);
    }
  }, [timeline.tracks, timeline.scrollY]);

  const drawWaveform = useCallback((
    ctx: CanvasRenderingContext2D,
    waveformData: number[],
    rect: Rect
  ) => {
    if (!waveformData || waveformData.length === 0) return;

    ctx.save();
    ctx.beginPath();
    ctx.rect(rect.x, rect.y, rect.width, rect.height);
    ctx.clip();

    ctx.strokeStyle = COLORS.waveform;
    ctx.lineWidth = 1;
    ctx.globalAlpha = 0.6;

    const centerY = rect.y + rect.height / 2;
    const samplesPerPixel = Math.max(1, Math.floor(waveformData.length / rect.width));

    ctx.beginPath();
    for (let x = 0; x < rect.width; x++) {
      const sampleIndex = Math.floor((x / rect.width) * waveformData.length);
      let maxSample = 0;

      for (let i = 0; i < samplesPerPixel && sampleIndex + i < waveformData.length; i++) {
        maxSample = Math.max(maxSample, Math.abs(waveformData[sampleIndex + i]));
      }

      const waveHeight = maxSample * (rect.height / 2);
      ctx.moveTo(rect.x + x, centerY - waveHeight);
      ctx.lineTo(rect.x + x, centerY + waveHeight);
    }
    ctx.stroke();

    ctx.restore();
  }, []);

  const drawClip = useCallback((
    ctx: CanvasRenderingContext2D,
    clip: Clip,
    rect: Rect,
    isSelected: boolean,
    isHovered: boolean
  ) => {
    if (rect.width < 1) return;

    ctx.save();

    // Clip boundary
    ctx.beginPath();
    ctx.rect(rect.x, rect.y, rect.width, rect.height);
    ctx.clip();

    // Background
    const color = getClipColor(clip.type, isSelected);
    ctx.fillStyle = color;
    ctx.fillRect(rect.x, rect.y, rect.width, rect.height);

    // Thumbnail for video/image clips
    if ((clip.type === 'video' || clip.type === 'image') && clip.thumbnailUrl) {
      const img = thumbnailCacheRef.current.get(clip.id);
      if (img && img.complete) {
        ctx.globalAlpha = 0.4;
        ctx.drawImage(img, rect.x, rect.y, rect.width, rect.height);
        ctx.globalAlpha = 1;
      }
    }

    // Waveform for audio clips
    if (clip.type === 'audio' && clip.waveformData) {
      drawWaveform(ctx, clip.waveformData, rect);
    }

    // Hover overlay
    if (isHovered && !isSelected) {
      ctx.fillStyle = COLORS.clipHover;
      ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
    }

    // Border
    ctx.strokeStyle = isSelected ? COLORS.text : 'rgba(0, 0, 0, 0.3)';
    ctx.lineWidth = isSelected ? 2 : 1;
    ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);

    // Clip name
    ctx.fillStyle = COLORS.text;
    ctx.font = '11px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText(clip.name, rect.x + 6, rect.y + 6);

    // Effect badges
    if (clip.effects.length > 0) {
      const enabledEffects = clip.effects.filter(e => e.enabled);
      if (enabledEffects.length > 0) {
        const badgeText = `${enabledEffects.length} FX`;
        ctx.fillStyle = COLORS.effectBadge;
        ctx.font = 'bold 9px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(badgeText, rect.x + rect.width - 6, rect.y + 6);
      }
    }

    // Keyframe diamonds
    if (clip.keyframes.length > 0) {
      clip.keyframes.forEach((keyframe) => {
        const keyframeTime = clip.startTime + keyframe.time;
        if (keyframeTime >= clip.startTime && keyframeTime <= clip.startTime + clip.duration) {
          const kfX = rect.x + timeToPixels(keyframe.time, timeline.zoom);
          const kfY = rect.y + rect.height - 10;

          ctx.fillStyle = COLORS.keyframe;
          ctx.beginPath();
          ctx.moveTo(kfX, kfY - 4);
          ctx.lineTo(kfX + 4, kfY);
          ctx.lineTo(kfX, kfY + 4);
          ctx.lineTo(kfX - 4, kfY);
          ctx.closePath();
          ctx.fill();
        }
      });
    }

    // Transition indicator
    if (clip.transition) {
      const transitionWidth = timeToPixels(clip.transition.duration, timeline.zoom);
      ctx.fillStyle = COLORS.transition;
      ctx.globalAlpha = 0.5;
      ctx.fillRect(rect.x, rect.y, Math.min(transitionWidth, rect.width), 3);
      ctx.globalAlpha = 1;
    }

    // Resize handles
    if (isSelected && rect.width > MIN_CLIP_WIDTH * 2) {
      ctx.fillStyle = COLORS.text;

      // Left handle
      ctx.fillRect(rect.x, rect.y, RESIZE_HANDLE_WIDTH, rect.height);

      // Right handle
      ctx.fillRect(rect.x + rect.width - RESIZE_HANDLE_WIDTH, rect.y, RESIZE_HANDLE_WIDTH, rect.height);
    }

    ctx.restore();
  }, [timeline.zoom, drawWaveform]);

  const drawPlayhead = useCallback((ctx: CanvasRenderingContext2D, height: number) => {
    const x = TRACK_HEADER_WIDTH + timeToPixels(timeline.currentTime, timeline.zoom) - timeline.scrollX;

    if (x < TRACK_HEADER_WIDTH || x > dimensions.width) return;

    ctx.strokeStyle = COLORS.playhead;
    ctx.lineWidth = PLAYHEAD_WIDTH;
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();

    // Playhead top indicator
    ctx.fillStyle = COLORS.playhead;
    ctx.beginPath();
    ctx.moveTo(x - 6, 0);
    ctx.lineTo(x + 6, 0);
    ctx.lineTo(x, 8);
    ctx.closePath();
    ctx.fill();

    // Time display
    const timeText = formatTime(timeline.currentTime, timeline.zoom);
    ctx.font = 'bold 11px monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(x - 30, 10, 60, 16);
    ctx.fillStyle = COLORS.playhead;
    ctx.fillText(timeText, x, 12);
  }, [timeline.currentTime, timeline.zoom, timeline.scrollX, dimensions.width]);

  const drawSnapLines = useCallback((ctx: CanvasRenderingContext2D, height: number) => {
    if (!dragState.isDragging || !timeline.snapEnabled) return;

    const snapPoints = getSnapPoints();

    timeline.selectedClipIds.forEach((clipId) => {
      const clip = timeline.clips.find((c) => c.id === clipId);
      if (!clip) return;

      const clipStart = clip.startTime;
      const clipEnd = clip.startTime + clip.duration;

      snapPoints.forEach((point) => {
        if (Math.abs(clipStart - point) < 0.1 || Math.abs(clipEnd - point) < 0.1) {
          const x = TRACK_HEADER_WIDTH + timeToPixels(point, timeline.zoom) - timeline.scrollX;

          ctx.strokeStyle = COLORS.snapLine;
          ctx.lineWidth = 1;
          ctx.setLineDash([4, 4]);
          ctx.beginPath();
          ctx.moveTo(x, TIMELINE_RULER_HEIGHT);
          ctx.lineTo(x, height);
          ctx.stroke();
          ctx.setLineDash([]);
        }
      });
    });
  }, [dragState.isDragging, timeline.snapEnabled, timeline.selectedClipIds, timeline.clips, timeline.zoom, timeline.scrollX, getSnapPoints]);

  const drawSelectionBox = useCallback((ctx: CanvasRenderingContext2D) => {
    if (!dragState.isDragging || dragState.dragType !== 'select') return;

    const startX = Math.min(dragState.startPos.x, dragState.currentPos.x);
    const startY = Math.min(dragState.startPos.y, dragState.currentPos.y);
    const width = Math.abs(dragState.currentPos.x - dragState.startPos.x);
    const height = Math.abs(dragState.currentPos.y - dragState.startPos.y);

    ctx.fillStyle = COLORS.selection;
    ctx.fillRect(startX, startY, width, height);

    ctx.strokeStyle = COLORS.clipSelected;
    ctx.lineWidth = 1;
    ctx.strokeRect(startX, startY, width, height);
  }, [dragState]);

  const drawRippleModeIndicator = useCallback((ctx: CanvasRenderingContext2D) => {
    if (!timeline.rippleMode) return;

    ctx.fillStyle = COLORS.playhead;
    ctx.font = 'bold 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'top';
    ctx.fillText('RIPPLE', 10, 10);
  }, [timeline.rippleMode]);

  // ============================================================================
  // MAIN RENDER LOOP
  // ============================================================================

  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) return;

    const { width, height } = dimensions;

    // Clear canvas
    ctx.fillStyle = COLORS.background;
    ctx.fillRect(0, 0, width, height);

    // Draw tracks background
    drawTracks(ctx, width, height);

    // Draw clips
    timeline.clips.forEach((clip) => {
      const rect = getClipRect(clip);
      const isSelected = timeline.selectedClipIds.includes(clip.id);
      const isHovered = hoveredClipId === clip.id;
      drawClip(ctx, clip, rect, isSelected, isHovered);
    });

    // Draw snap lines
    drawSnapLines(ctx, height);

    // Draw selection box
    drawSelectionBox(ctx);

    // Draw playhead
    drawPlayhead(ctx, height);

    // Draw time ruler (on top of tracks)
    drawTimeRuler(ctx, width);

    // Draw track headers (on top of everything)
    drawTrackHeaders(ctx, height);

    // Draw ripple mode indicator
    drawRippleModeIndicator(ctx);

  }, [
    dimensions,
    timeline,
    hoveredClipId,
    dragState,
    drawTracks,
    drawClip,
    drawSnapLines,
    drawSelectionBox,
    drawPlayhead,
    drawTimeRuler,
    drawTrackHeaders,
    drawRippleModeIndicator,
    getClipRect,
  ]);

  // ============================================================================
  // ANIMATION LOOP
  // ============================================================================

  useEffect(() => {
    const animate = () => {
      render();
      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [render]);

  // ============================================================================
  // MOUSE EVENT HANDLERS
  // ============================================================================

  const getMousePos = (e: React.MouseEvent): Point => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const getResizeHandle = (clip: Clip, point: Point): 'start' | 'end' | null => {
    const rect = getClipRect(clip);

    if (point.x >= rect.x && point.x <= rect.x + RESIZE_HANDLE_WIDTH &&
        point.y >= rect.y && point.y <= rect.y + rect.height) {
      return 'start';
    }

    if (point.x >= rect.x + rect.width - RESIZE_HANDLE_WIDTH && point.x <= rect.x + rect.width &&
        point.y >= rect.y && point.y <= rect.y + rect.height) {
      return 'end';
    }

    return null;
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    const pos = getMousePos(e);

    // Check if clicking on playhead
    const playheadX = TRACK_HEADER_WIDTH + timeToPixels(timeline.currentTime, timeline.zoom) - timeline.scrollX;
    if (Math.abs(pos.x - playheadX) < 10 && pos.y < TIMELINE_RULER_HEIGHT) {
      setDragState({
        isDragging: true,
        dragType: 'playhead',
        startPos: pos,
        currentPos: pos,
        originalClipData: new Map(),
        dragClipId: null,
      });
      return;
    }

    // Check if clicking on timeline ruler (to set playhead)
    if (pos.y < TIMELINE_RULER_HEIGHT && pos.x >= TRACK_HEADER_WIDTH) {
      const time = pixelsToTime(pos.x - TRACK_HEADER_WIDTH + timeline.scrollX, timeline.zoom);
      onTimeChange(Math.max(0, Math.min(time, timeline.duration)));
      return;
    }

    // Check if clicking on a clip
    const clickedClip = getClipAtPoint(pos);

    if (clickedClip) {
      const handle = getResizeHandle(clickedClip, pos);

      if (handle) {
        // Start resizing
        const originalData = new Map();
        timeline.selectedClipIds.forEach((clipId) => {
          const clip = timeline.clips.find((c) => c.id === clipId);
          if (clip) {
            originalData.set(clipId, {
              startTime: clip.startTime,
              duration: clip.duration,
              trimStart: clip.trimStart,
              trimEnd: clip.trimEnd,
            });
          }
        });

        setDragState({
          isDragging: true,
          dragType: handle === 'start' ? 'trim-start' : 'trim-end',
          startPos: pos,
          currentPos: pos,
          originalClipData: originalData,
          dragClipId: clickedClip.id,
        });
      } else {
        // Select and potentially start moving
        let newSelection: string[];

        if (e.shiftKey || e.metaKey || e.ctrlKey) {
          // Multi-select
          if (timeline.selectedClipIds.includes(clickedClip.id)) {
            newSelection = timeline.selectedClipIds.filter((id) => id !== clickedClip.id);
          } else {
            newSelection = [...timeline.selectedClipIds, clickedClip.id];
          }
        } else {
          // Single select
          if (!timeline.selectedClipIds.includes(clickedClip.id)) {
            newSelection = [clickedClip.id];
          } else {
            newSelection = timeline.selectedClipIds;
          }
        }

        onClipSelect(newSelection);

        // Start move operation
        const originalData = new Map();
        newSelection.forEach((clipId) => {
          const clip = timeline.clips.find((c) => c.id === clipId);
          if (clip) {
            originalData.set(clipId, {
              startTime: clip.startTime,
              duration: clip.duration,
              trimStart: clip.trimStart,
              trimEnd: clip.trimEnd,
            });
          }
        });

        setDragState({
          isDragging: true,
          dragType: 'move',
          startPos: pos,
          currentPos: pos,
          originalClipData: originalData,
          dragClipId: clickedClip.id,
        });
      }
    } else {
      // Start selection box
      if (!(e.shiftKey || e.metaKey || e.ctrlKey)) {
        onClipSelect([]);
      }

      setDragState({
        isDragging: true,
        dragType: 'select',
        startPos: pos,
        currentPos: pos,
        originalClipData: new Map(),
        dragClipId: null,
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    const pos = getMousePos(e);

    if (!dragState.isDragging) {
      // Update hover state
      const hoveredClip = getClipAtPoint(pos);
      setHoveredClipId(hoveredClip?.id || null);

      if (hoveredClip) {
        const handle = getResizeHandle(hoveredClip, pos);
        setHoveredHandle(handle);

        // Update cursor
        if (handle) {
          document.body.style.cursor = 'ew-resize';
        } else {
          document.body.style.cursor = 'move';
        }
      } else {
        setHoveredHandle(null);
        document.body.style.cursor = 'default';
      }

      return;
    }

    // Handle dragging
    setDragState((prev) => ({ ...prev, currentPos: pos }));

    const deltaX = pos.x - dragState.startPos.x;
    const deltaTime = pixelsToTime(deltaX, timeline.zoom);

    if (dragState.dragType === 'playhead') {
      const time = pixelsToTime(pos.x - TRACK_HEADER_WIDTH + timeline.scrollX, timeline.zoom);
      onTimeChange(Math.max(0, Math.min(time, timeline.duration)));
    } else if (dragState.dragType === 'move') {
      // Move selected clips
      const updatedClips = timeline.clips.map((clip) => {
        if (timeline.selectedClipIds.includes(clip.id)) {
          const original = dragState.originalClipData.get(clip.id);
          if (original) {
            let newStartTime = original.startTime + deltaTime;

            // Snap if enabled
            if (timeline.snapEnabled) {
              const snapPoints = getSnapPoints();
              newStartTime = snapToValue(newStartTime, snapPoints, SNAP_THRESHOLD, timeline.zoom);
            }

            // Clamp to valid range
            newStartTime = Math.max(0, newStartTime);

            return { ...clip, startTime: newStartTime };
          }
        }
        return clip;
      });

      onTimelineChange({ ...timeline, clips: updatedClips });
    } else if (dragState.dragType === 'trim-start') {
      // Trim start of clips
      const updatedClips = timeline.clips.map((clip) => {
        if (timeline.selectedClipIds.includes(clip.id)) {
          const original = dragState.originalClipData.get(clip.id);
          if (original) {
            const newStartTime = original.startTime + deltaTime;
            const newDuration = original.duration - deltaTime;
            const newTrimStart = original.trimStart + deltaTime;

            if (newDuration >= pixelsToTime(MIN_CLIP_WIDTH, timeline.zoom)) {
              return {
                ...clip,
                startTime: Math.max(0, newStartTime),
                duration: newDuration,
                trimStart: newTrimStart,
              };
            }
          }
        }
        return clip;
      });

      onTimelineChange({ ...timeline, clips: updatedClips });
    } else if (dragState.dragType === 'trim-end') {
      // Trim end of clips
      const updatedClips = timeline.clips.map((clip) => {
        if (timeline.selectedClipIds.includes(clip.id)) {
          const original = dragState.originalClipData.get(clip.id);
          if (original) {
            const newDuration = original.duration + deltaTime;
            const newTrimEnd = original.trimEnd - deltaTime;

            if (newDuration >= pixelsToTime(MIN_CLIP_WIDTH, timeline.zoom)) {
              return {
                ...clip,
                duration: newDuration,
                trimEnd: newTrimEnd,
              };
            }
          }
        }
        return clip;
      });

      onTimelineChange({ ...timeline, clips: updatedClips });
    } else if (dragState.dragType === 'select') {
      // Update selection based on selection box
      const selectionRect: Rect = {
        x: Math.min(dragState.startPos.x, pos.x),
        y: Math.min(dragState.startPos.y, pos.y),
        width: Math.abs(pos.x - dragState.startPos.x),
        height: Math.abs(pos.y - dragState.startPos.y),
      };

      const selectedClips = timeline.clips.filter((clip) => {
        const clipRect = getClipRect(clip);
        return (
          clipRect.x + clipRect.width >= selectionRect.x &&
          clipRect.x <= selectionRect.x + selectionRect.width &&
          clipRect.y + clipRect.height >= selectionRect.y &&
          clipRect.y <= selectionRect.y + selectionRect.height
        );
      });

      onClipSelect(selectedClips.map((c) => c.id));
    }
  };

  const handleMouseUp = (e: React.MouseEvent) => {
    setDragState({
      isDragging: false,
      dragType: null,
      startPos: { x: 0, y: 0 },
      currentPos: { x: 0, y: 0 },
      originalClipData: new Map(),
      dragClipId: null,
    });

    document.body.style.cursor = 'default';
  };

  const handleMouseLeave = () => {
    setHoveredClipId(null);
    setHoveredHandle(null);
    document.body.style.cursor = 'default';
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    const pos = getMousePos(e);
    const clickedClip = getClipAtPoint(pos);

    setContextMenuPos(pos);
    setShowContextMenu(true);

    if (onContextMenu) {
      onContextMenu(clickedClip?.id || null, pos);
    }
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();

    if (e.ctrlKey || e.metaKey) {
      // Zoom
      const zoomIndex = ZOOM_LEVELS.indexOf(timeline.zoom);
      const newZoomIndex = e.deltaY > 0
        ? Math.max(0, zoomIndex - 1)
        : Math.min(ZOOM_LEVELS.length - 1, zoomIndex + 1);

      const newZoom = ZOOM_LEVELS[newZoomIndex];

      // Zoom towards mouse position
      const mouseTime = pixelsToTime(e.clientX - TRACK_HEADER_WIDTH + timeline.scrollX, timeline.zoom);
      const newScrollX = timeToPixels(mouseTime, newZoom) - (e.clientX - TRACK_HEADER_WIDTH);

      onTimelineChange({
        ...timeline,
        zoom: newZoom,
        scrollX: Math.max(0, newScrollX),
      });
    } else if (e.shiftKey) {
      // Horizontal scroll
      const newScrollX = Math.max(0, timeline.scrollX + e.deltaY);
      onTimelineChange({ ...timeline, scrollX: newScrollX });
    } else {
      // Vertical scroll
      const maxScrollY = Math.max(0,
        timeline.tracks.reduce((sum, t) => sum + t.height, 0) -
        (dimensions.height - TIMELINE_RULER_HEIGHT)
      );
      const newScrollY = Math.max(0, Math.min(maxScrollY, timeline.scrollY + e.deltaY));
      onTimelineChange({ ...timeline, scrollY: newScrollY });
    }
  };

  // ============================================================================
  // KEYBOARD EVENT HANDLERS
  // ============================================================================

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Delete selected clips
    if ((e.key === 'Delete' || e.key === 'Backspace') && timeline.selectedClipIds.length > 0) {
      const updatedClips = timeline.clips.filter(
        (clip) => !timeline.selectedClipIds.includes(clip.id)
      );
      onTimelineChange({ ...timeline, clips: updatedClips });
      onClipSelect([]);
    }

    // Select all
    if ((e.metaKey || e.ctrlKey) && e.key === 'a') {
      e.preventDefault();
      onClipSelect(timeline.clips.map((c) => c.id));
    }

    // Deselect all
    if (e.key === 'Escape') {
      onClipSelect([]);
    }

    // Set in point
    if (e.key === 'i') {
      onTimelineChange({ ...timeline, inPoint: timeline.currentTime });
    }

    // Set out point
    if (e.key === 'o') {
      onTimelineChange({ ...timeline, outPoint: timeline.currentTime });
    }

    // Clear in/out points
    if ((e.metaKey || e.ctrlKey) && e.key === 'x') {
      onTimelineChange({ ...timeline, inPoint: null, outPoint: null });
    }

    // Toggle ripple mode
    if (e.key === 'r') {
      onTimelineChange({ ...timeline, rippleMode: !timeline.rippleMode });
    }

    // Toggle snap
    if (e.key === 's') {
      onTimelineChange({ ...timeline, snapEnabled: !timeline.snapEnabled });
    }

    // Zoom in
    if ((e.metaKey || e.ctrlKey) && e.key === '=') {
      e.preventDefault();
      const zoomIndex = ZOOM_LEVELS.indexOf(timeline.zoom);
      const newZoomIndex = Math.min(ZOOM_LEVELS.length - 1, zoomIndex + 1);
      onTimelineChange({ ...timeline, zoom: ZOOM_LEVELS[newZoomIndex] });
    }

    // Zoom out
    if ((e.metaKey || e.ctrlKey) && e.key === '-') {
      e.preventDefault();
      const zoomIndex = ZOOM_LEVELS.indexOf(timeline.zoom);
      const newZoomIndex = Math.max(0, zoomIndex - 1);
      onTimelineChange({ ...timeline, zoom: ZOOM_LEVELS[newZoomIndex] });
    }

    // Frame forward
    if (e.key === 'ArrowRight') {
      const frameDuration = 1 / 30;
      onTimeChange(Math.min(timeline.duration, timeline.currentTime + frameDuration));
    }

    // Frame backward
    if (e.key === 'ArrowLeft') {
      const frameDuration = 1 / 30;
      onTimeChange(Math.max(0, timeline.currentTime - frameDuration));
    }
  }, [timeline, onTimelineChange, onClipSelect, onTimeChange]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        position: 'relative',
        backgroundColor: COLORS.background,
      }}
    >
      <canvas
        ref={canvasRef}
        width={dimensions.width}
        height={dimensions.height}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onContextMenu={handleContextMenu}
        onWheel={handleWheel}
        style={{
          display: 'block',
          width: '100%',
          height: '100%',
        }}
      />
    </div>
  );
};

export default TimelineCanvas;
