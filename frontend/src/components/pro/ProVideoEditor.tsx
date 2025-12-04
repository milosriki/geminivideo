import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { create } from 'zustand';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface TimelineClip {
  id: string;
  trackId: string;
  startTime: number; // seconds
  duration: number; // seconds
  offset: number; // trim start offset
  source: MediaSource;
  effects: Effect[];
  volume: number;
  locked: boolean;
}

interface MediaSource {
  id: string;
  type: 'video' | 'audio' | 'image';
  url: string;
  name: string;
  duration: number;
  thumbnail?: string;
  waveform?: number[]; // Audio waveform data
}

interface Track {
  id: string;
  type: 'video' | 'audio';
  name: string;
  locked: boolean;
  muted: boolean;
  solo: boolean;
  height: number;
  volume: number;
}

interface Effect {
  id: string;
  type: 'transition' | 'filter' | 'colorGrade';
  name: string;
  params: Record<string, any>;
  startTime?: number;
  duration?: number;
}

interface Marker {
  id: string;
  time: number;
  label: string;
  color: string;
  comment?: string;
}

interface HistoryState {
  clips: TimelineClip[];
  tracks: Track[];
  markers: Marker[];
  timestamp: number;
}

interface ExportSettings {
  format: 'mp4' | 'mov' | 'webm';
  quality: 'low' | 'medium' | 'high' | 'ultra';
  resolution: '720p' | '1080p' | '4k';
  fps: 24 | 30 | 60;
  platform: 'youtube' | 'instagram' | 'tiktok' | 'facebook' | 'custom';
}

interface ColorGrading {
  exposure: number;
  contrast: number;
  highlights: number;
  shadows: number;
  whites: number;
  blacks: number;
  temperature: number;
  tint: number;
  saturation: number;
  vibrance: number;
}

interface Caption {
  id: string;
  startTime: number;
  endTime: number;
  text: string;
  style: CaptionStyle;
}

interface CaptionStyle {
  fontFamily: string;
  fontSize: number;
  color: string;
  backgroundColor: string;
  position: 'top' | 'center' | 'bottom';
  alignment: 'left' | 'center' | 'right';
}

type Tool = 'selection' | 'razor' | 'hand';

// ============================================================================
// ZUSTAND STORE
// ============================================================================

interface EditorStore {
  // Project state
  projectName: string;
  clips: TimelineClip[];
  tracks: Track[];
  markers: Marker[];
  captions: Caption[];

  // Playback state
  currentTime: number;
  isPlaying: boolean;
  playbackRate: number;
  duration: number;

  // Timeline state
  zoom: number;
  scrollPosition: number;
  snapToGrid: boolean;
  gridSize: number;

  // Selection state
  selectedClipIds: string[];
  selectedTool: Tool;

  // In/Out points
  inPoint: number | null;
  outPoint: number | null;

  // History (undo/redo)
  history: HistoryState[];
  historyIndex: number;
  maxHistory: number;

  // Clipboard
  clipboard: TimelineClip[];

  // Panels
  showEffects: boolean;
  showColorGrading: boolean;
  showAudioMixer: boolean;
  showCaptions: boolean;
  showExport: boolean;

  // Color grading
  colorGrading: ColorGrading;

  // Export settings
  exportSettings: ExportSettings;

  // Media library
  mediaLibrary: MediaSource[];

  // Actions
  setProjectName: (name: string) => void;
  setCurrentTime: (time: number) => void;
  setIsPlaying: (playing: boolean) => void;
  setPlaybackRate: (rate: number) => void;
  setZoom: (zoom: number) => void;
  setScrollPosition: (pos: number) => void;
  setSnapToGrid: (snap: boolean) => void;
  setSelectedTool: (tool: Tool) => void;

  // Clip actions
  addClip: (clip: TimelineClip) => void;
  updateClip: (id: string, updates: Partial<TimelineClip>) => void;
  deleteClip: (id: string) => void;
  splitClipAtTime: (clipId: string, time: number) => void;

  // Track actions
  addTrack: (type: 'video' | 'audio') => void;
  updateTrack: (id: string, updates: Partial<Track>) => void;
  deleteTrack: (id: string) => void;

  // Selection
  selectClip: (id: string, addToSelection?: boolean) => void;
  clearSelection: () => void;

  // In/Out points
  setInPoint: (time: number | null) => void;
  setOutPoint: (time: number | null) => void;

  // Clipboard
  copySelectedClips: () => void;
  pasteClips: () => void;
  cutSelectedClips: () => void;

  // History
  undo: () => void;
  redo: () => void;
  saveHistory: () => void;

  // Markers
  addMarker: (marker: Marker) => void;
  updateMarker: (id: string, updates: Partial<Marker>) => void;
  deleteMarker: (id: string) => void;

  // Captions
  addCaption: (caption: Caption) => void;
  updateCaption: (id: string, updates: Partial<Caption>) => void;
  deleteCaption: (id: string) => void;

  // Panels
  togglePanel: (panel: 'effects' | 'colorGrading' | 'audioMixer' | 'captions' | 'export') => void;

  // Color grading
  updateColorGrading: (updates: Partial<ColorGrading>) => void;

  // Export
  updateExportSettings: (updates: Partial<ExportSettings>) => void;

  // Media
  addMedia: (media: MediaSource) => void;

  // Project
  loadProject: (data: any) => void;
  saveProject: () => any;
}

const useEditorStore = create<EditorStore>((set, get) => ({
  // Initial state
  projectName: 'Untitled Project',
  clips: [],
  tracks: [
    { id: 'track-v1', type: 'video', name: 'Video 1', locked: false, muted: false, solo: false, height: 80, volume: 1 },
    { id: 'track-a1', type: 'audio', name: 'Audio 1', locked: false, muted: false, solo: false, height: 60, volume: 1 },
  ],
  markers: [],
  captions: [],

  currentTime: 0,
  isPlaying: false,
  playbackRate: 1,
  duration: 300,

  zoom: 1,
  scrollPosition: 0,
  snapToGrid: true,
  gridSize: 1,

  selectedClipIds: [],
  selectedTool: 'selection',

  inPoint: null,
  outPoint: null,

  history: [],
  historyIndex: -1,
  maxHistory: 50,

  clipboard: [],

  showEffects: false,
  showColorGrading: false,
  showAudioMixer: false,
  showCaptions: false,
  showExport: false,

  colorGrading: {
    exposure: 0,
    contrast: 0,
    highlights: 0,
    shadows: 0,
    whites: 0,
    blacks: 0,
    temperature: 0,
    tint: 0,
    saturation: 0,
    vibrance: 0,
  },

  exportSettings: {
    format: 'mp4',
    quality: 'high',
    resolution: '1080p',
    fps: 30,
    platform: 'youtube',
  },

  mediaLibrary: [],

  // Actions
  setProjectName: (name) => set({ projectName: name }),
  setCurrentTime: (time) => set({ currentTime: Math.max(0, Math.min(time, get().duration)) }),
  setIsPlaying: (playing) => set({ isPlaying: playing }),
  setPlaybackRate: (rate) => set({ playbackRate: rate }),
  setZoom: (zoom) => set({ zoom: Math.max(0.1, Math.min(zoom, 10)) }),
  setScrollPosition: (pos) => set({ scrollPosition: pos }),
  setSnapToGrid: (snap) => set({ snapToGrid: snap }),
  setSelectedTool: (tool) => set({ selectedTool: tool }),

  addClip: (clip) => {
    get().saveHistory();
    set((state) => ({ clips: [...state.clips, clip] }));
  },

  updateClip: (id, updates) => {
    get().saveHistory();
    set((state) => ({
      clips: state.clips.map(clip => clip.id === id ? { ...clip, ...updates } : clip)
    }));
  },

  deleteClip: (id) => {
    get().saveHistory();
    set((state) => ({
      clips: state.clips.filter(clip => clip.id !== id),
      selectedClipIds: state.selectedClipIds.filter(cid => cid !== id)
    }));
  },

  splitClipAtTime: (clipId, time) => {
    const state = get();
    const clip = state.clips.find(c => c.id === clipId);
    if (!clip || time <= clip.startTime || time >= clip.startTime + clip.duration) return;

    get().saveHistory();

    const relativeTime = time - clip.startTime;
    const clip1: TimelineClip = {
      ...clip,
      id: `${clip.id}-split1-${Date.now()}`,
      duration: relativeTime,
    };

    const clip2: TimelineClip = {
      ...clip,
      id: `${clip.id}-split2-${Date.now()}`,
      startTime: time,
      duration: clip.duration - relativeTime,
      offset: clip.offset + relativeTime,
    };

    set((state) => ({
      clips: [...state.clips.filter(c => c.id !== clipId), clip1, clip2]
    }));
  },

  addTrack: (type) => {
    get().saveHistory();
    const state = get();
    const trackNumber = state.tracks.filter(t => t.type === type).length + 1;
    const newTrack: Track = {
      id: `track-${type[0]}${trackNumber}-${Date.now()}`,
      type,
      name: `${type === 'video' ? 'Video' : 'Audio'} ${trackNumber}`,
      locked: false,
      muted: false,
      solo: false,
      height: type === 'video' ? 80 : 60,
      volume: 1,
    };
    set((state) => ({ tracks: [...state.tracks, newTrack] }));
  },

  updateTrack: (id, updates) => {
    set((state) => ({
      tracks: state.tracks.map(track => track.id === id ? { ...track, ...updates } : track)
    }));
  },

  deleteTrack: (id) => {
    get().saveHistory();
    set((state) => ({
      tracks: state.tracks.filter(track => track.id !== id),
      clips: state.clips.filter(clip => clip.trackId !== id)
    }));
  },

  selectClip: (id, addToSelection = false) => {
    set((state) => ({
      selectedClipIds: addToSelection
        ? state.selectedClipIds.includes(id)
          ? state.selectedClipIds.filter(cid => cid !== id)
          : [...state.selectedClipIds, id]
        : [id]
    }));
  },

  clearSelection: () => set({ selectedClipIds: [] }),

  setInPoint: (time) => set({ inPoint: time }),
  setOutPoint: (time) => set({ outPoint: time }),

  copySelectedClips: () => {
    const state = get();
    const selectedClips = state.clips.filter(c => state.selectedClipIds.includes(c.id));
    set({ clipboard: selectedClips.map(c => ({ ...c, id: `${c.id}-copy` })) });
  },

  pasteClips: () => {
    const state = get();
    if (state.clipboard.length === 0) return;

    get().saveHistory();
    const minStartTime = Math.min(...state.clipboard.map(c => c.startTime));
    const offset = state.currentTime - minStartTime;

    const pastedClips = state.clipboard.map(c => ({
      ...c,
      id: `clip-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      startTime: c.startTime + offset,
    }));

    set((state) => ({ clips: [...state.clips, ...pastedClips] }));
  },

  cutSelectedClips: () => {
    get().copySelectedClips();
    const state = get();
    get().saveHistory();
    set((state) => ({
      clips: state.clips.filter(c => !state.selectedClipIds.includes(c.id)),
      selectedClipIds: []
    }));
  },

  saveHistory: () => {
    const state = get();
    const historyState: HistoryState = {
      clips: JSON.parse(JSON.stringify(state.clips)),
      tracks: JSON.parse(JSON.stringify(state.tracks)),
      markers: JSON.parse(JSON.stringify(state.markers)),
      timestamp: Date.now(),
    };

    const newHistory = state.history.slice(0, state.historyIndex + 1);
    newHistory.push(historyState);

    if (newHistory.length > state.maxHistory) {
      newHistory.shift();
    }

    set({
      history: newHistory,
      historyIndex: newHistory.length - 1,
    });
  },

  undo: () => {
    const state = get();
    if (state.historyIndex <= 0) return;

    const newIndex = state.historyIndex - 1;
    const historyState = state.history[newIndex];

    set({
      clips: JSON.parse(JSON.stringify(historyState.clips)),
      tracks: JSON.parse(JSON.stringify(historyState.tracks)),
      markers: JSON.parse(JSON.stringify(historyState.markers)),
      historyIndex: newIndex,
    });
  },

  redo: () => {
    const state = get();
    if (state.historyIndex >= state.history.length - 1) return;

    const newIndex = state.historyIndex + 1;
    const historyState = state.history[newIndex];

    set({
      clips: JSON.parse(JSON.stringify(historyState.clips)),
      tracks: JSON.parse(JSON.stringify(historyState.tracks)),
      markers: JSON.parse(JSON.stringify(historyState.markers)),
      historyIndex: newIndex,
    });
  },

  addMarker: (marker) => {
    get().saveHistory();
    set((state) => ({ markers: [...state.markers, marker] }));
  },

  updateMarker: (id, updates) => {
    set((state) => ({
      markers: state.markers.map(m => m.id === id ? { ...m, ...updates } : m)
    }));
  },

  deleteMarker: (id) => {
    get().saveHistory();
    set((state) => ({ markers: state.markers.filter(m => m.id !== id) }));
  },

  addCaption: (caption) => {
    get().saveHistory();
    set((state) => ({ captions: [...state.captions, caption] }));
  },

  updateCaption: (id, updates) => {
    set((state) => ({
      captions: state.captions.map(c => c.id === id ? { ...c, ...updates } : c)
    }));
  },

  deleteCaption: (id) => {
    get().saveHistory();
    set((state) => ({ captions: state.captions.filter(c => c.id !== id) }));
  },

  togglePanel: (panel) => {
    set((state) => ({
      showEffects: panel === 'effects' ? !state.showEffects : state.showEffects,
      showColorGrading: panel === 'colorGrading' ? !state.showColorGrading : state.showColorGrading,
      showAudioMixer: panel === 'audioMixer' ? !state.showAudioMixer : state.showAudioMixer,
      showCaptions: panel === 'captions' ? !state.showCaptions : state.showCaptions,
      showExport: panel === 'export' ? !state.showExport : state.showExport,
    }));
  },

  updateColorGrading: (updates) => {
    set((state) => ({
      colorGrading: { ...state.colorGrading, ...updates }
    }));
  },

  updateExportSettings: (updates) => {
    set((state) => ({
      exportSettings: { ...state.exportSettings, ...updates }
    }));
  },

  addMedia: (media) => {
    set((state) => ({ mediaLibrary: [...state.mediaLibrary, media] }));
  },

  loadProject: (data) => {
    set({
      projectName: data.projectName || 'Untitled Project',
      clips: data.clips || [],
      tracks: data.tracks || [],
      markers: data.markers || [],
      captions: data.captions || [],
      colorGrading: data.colorGrading || get().colorGrading,
      exportSettings: data.exportSettings || get().exportSettings,
    });
  },

  saveProject: () => {
    const state = get();
    return {
      projectName: state.projectName,
      clips: state.clips,
      tracks: state.tracks,
      markers: state.markers,
      captions: state.captions,
      colorGrading: state.colorGrading,
      exportSettings: state.exportSettings,
      version: '1.0.0',
      timestamp: Date.now(),
    };
  },
}));

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

const formatTime = (seconds: number): string => {
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const frames = Math.floor((seconds % 1) * 30);

  return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
};

const snapToGridValue = (value: number, gridSize: number, enabled: boolean): number => {
  if (!enabled) return value;
  return Math.round(value / gridSize) * gridSize;
};

const generateWaveform = (audioBuffer: AudioBuffer): number[] => {
  const rawData = audioBuffer.getChannelData(0);
  const samples = 200;
  const blockSize = Math.floor(rawData.length / samples);
  const waveform: number[] = [];

  for (let i = 0; i < samples; i++) {
    let sum = 0;
    for (let j = 0; j < blockSize; j++) {
      sum += Math.abs(rawData[i * blockSize + j]);
    }
    waveform.push(sum / blockSize);
  }

  return waveform;
};

// ============================================================================
// COMPONENTS
// ============================================================================

// Timeline Ruler Component
const TimelineRuler: React.FC<{ zoom: number; duration: number; width: number }> = ({ zoom, duration, width }) => {
  const pixelsPerSecond = zoom * 20;
  const numTicks = Math.ceil(duration);

  return (
    <div className="timeline-ruler" style={{ height: 30, background: '#2a2a2a', position: 'relative', borderBottom: '1px solid #444' }}>
      {Array.from({ length: numTicks + 1 }).map((_, i) => {
        const x = i * pixelsPerSecond;
        if (x > width) return null;

        return (
          <div key={i} style={{ position: 'absolute', left: x, top: 0, height: '100%', borderLeft: '1px solid #666' }}>
            <span style={{ fontSize: 10, color: '#999', marginLeft: 4 }}>{formatTime(i)}</span>
          </div>
        );
      })}
    </div>
  );
};

// Playhead Component
const Playhead: React.FC<{ currentTime: number; zoom: number; onSeek: (time: number) => void }> = ({ currentTime, zoom, onSeek }) => {
  const pixelsPerSecond = zoom * 20;
  const x = currentTime * pixelsPerSecond;

  const handleDrag = (e: React.MouseEvent) => {
    const startX = e.clientX;
    const startTime = currentTime;

    const onMouseMove = (me: MouseEvent) => {
      const deltaX = me.clientX - startX;
      const deltaTime = deltaX / pixelsPerSecond;
      onSeek(startTime + deltaTime);
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  return (
    <div
      className="playhead"
      onMouseDown={handleDrag}
      style={{
        position: 'absolute',
        left: x,
        top: 0,
        bottom: 0,
        width: 2,
        background: '#ff4444',
        cursor: 'ew-resize',
        zIndex: 100,
        pointerEvents: 'auto',
      }}
    >
      <div style={{
        position: 'absolute',
        top: -8,
        left: -6,
        width: 14,
        height: 14,
        background: '#ff4444',
        clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)'
      }} />
    </div>
  );
};

// Timeline Clip Component
const TimelineClipComponent: React.FC<{
  clip: TimelineClip;
  zoom: number;
  isSelected: boolean;
  onSelect: () => void;
  onUpdate: (updates: Partial<TimelineClip>) => void;
}> = ({ clip, zoom, isSelected, onSelect, onUpdate }) => {
  const pixelsPerSecond = zoom * 20;
  const width = clip.duration * pixelsPerSecond;
  const left = clip.startTime * pixelsPerSecond;

  const handleDragMove = (e: React.MouseEvent) => {
    if (clip.locked) return;
    e.stopPropagation();

    const startX = e.clientX;
    const startTime = clip.startTime;

    const onMouseMove = (me: MouseEvent) => {
      const deltaX = me.clientX - startX;
      const deltaTime = deltaX / pixelsPerSecond;
      onUpdate({ startTime: Math.max(0, startTime + deltaTime) });
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const handleResizeLeft = (e: React.MouseEvent) => {
    if (clip.locked) return;
    e.stopPropagation();

    const startX = e.clientX;
    const startTime = clip.startTime;
    const startDuration = clip.duration;
    const startOffset = clip.offset;

    const onMouseMove = (me: MouseEvent) => {
      const deltaX = me.clientX - startX;
      const deltaTime = deltaX / pixelsPerSecond;
      const newStartTime = Math.max(0, startTime + deltaTime);
      const newDuration = startDuration - (newStartTime - startTime);
      const newOffset = startOffset + (newStartTime - startTime);

      if (newDuration > 0.1) {
        onUpdate({ startTime: newStartTime, duration: newDuration, offset: newOffset });
      }
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const handleResizeRight = (e: React.MouseEvent) => {
    if (clip.locked) return;
    e.stopPropagation();

    const startX = e.clientX;
    const startDuration = clip.duration;

    const onMouseMove = (me: MouseEvent) => {
      const deltaX = me.clientX - startX;
      const deltaTime = deltaX / pixelsPerSecond;
      const newDuration = Math.max(0.1, startDuration + deltaTime);
      onUpdate({ duration: newDuration });
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  return (
    <div
      className={`timeline-clip ${isSelected ? 'selected' : ''}`}
      onClick={onSelect}
      onMouseDown={handleDragMove}
      style={{
        position: 'absolute',
        left,
        width,
        height: '100%',
        background: clip.source.type === 'video' ? '#4a9eff' : '#9b59b6',
        border: isSelected ? '2px solid #fff' : '1px solid #333',
        borderRadius: 4,
        cursor: clip.locked ? 'not-allowed' : 'move',
        overflow: 'hidden',
        opacity: clip.locked ? 0.6 : 1,
      }}
    >
      <div style={{ padding: '4px 8px', fontSize: 11, color: '#fff', fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {clip.source.name}
      </div>

      {clip.source.waveform && (
        <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '50%', display: 'flex', alignItems: 'flex-end', padding: '0 4px' }}>
          {clip.source.waveform.map((value, i) => (
            <div key={i} style={{ flex: 1, background: 'rgba(255,255,255,0.3)', height: `${value * 100}%`, margin: '0 0.5px' }} />
          ))}
        </div>
      )}

      {!clip.locked && (
        <>
          <div
            className="resize-handle-left"
            onMouseDown={handleResizeLeft}
            style={{
              position: 'absolute',
              left: 0,
              top: 0,
              bottom: 0,
              width: 8,
              cursor: 'ew-resize',
              background: 'rgba(255,255,255,0.1)',
            }}
          />
          <div
            className="resize-handle-right"
            onMouseDown={handleResizeRight}
            style={{
              position: 'absolute',
              right: 0,
              top: 0,
              bottom: 0,
              width: 8,
              cursor: 'ew-resize',
              background: 'rgba(255,255,255,0.1)',
            }}
          />
        </>
      )}
    </div>
  );
};

// Track Component
const TrackComponent: React.FC<{ track: Track }> = ({ track }) => {
  const { clips, selectedClipIds, selectClip, updateClip, updateTrack } = useEditorStore();
  const zoom = useEditorStore(state => state.zoom);
  const trackClips = clips.filter(c => c.trackId === track.id);

  return (
    <div className="track" style={{ display: 'flex', borderBottom: '1px solid #333' }}>
      <div className="track-header" style={{
        width: 200,
        background: '#252525',
        padding: 8,
        borderRight: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        gap: 4,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input
            type="text"
            value={track.name}
            onChange={(e) => updateTrack(track.id, { name: e.target.value })}
            style={{
              flex: 1,
              background: '#1a1a1a',
              border: '1px solid #444',
              color: '#fff',
              padding: '4px 8px',
              borderRadius: 4,
              fontSize: 12,
            }}
          />
        </div>

        <div style={{ display: 'flex', gap: 4 }}>
          <button
            onClick={() => updateTrack(track.id, { locked: !track.locked })}
            style={{
              flex: 1,
              padding: '4px 8px',
              background: track.locked ? '#ff4444' : '#333',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: 11,
            }}
            title="Lock/Unlock Track"
          >
            {track.locked ? '🔒' : '🔓'}
          </button>

          <button
            onClick={() => updateTrack(track.id, { muted: !track.muted })}
            style={{
              flex: 1,
              padding: '4px 8px',
              background: track.muted ? '#ff4444' : '#333',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: 11,
            }}
            title="Mute/Unmute"
          >
            {track.muted ? '🔇' : '🔊'}
          </button>

          <button
            onClick={() => updateTrack(track.id, { solo: !track.solo })}
            style={{
              flex: 1,
              padding: '4px 8px',
              background: track.solo ? '#ffaa00' : '#333',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: 11,
            }}
            title="Solo"
          >
            S
          </button>
        </div>
      </div>

      <div className="track-content" style={{
        flex: 1,
        height: track.height,
        background: '#1a1a1a',
        position: 'relative',
      }}>
        {trackClips.map(clip => (
          <TimelineClipComponent
            key={clip.id}
            clip={clip}
            zoom={zoom}
            isSelected={selectedClipIds.includes(clip.id)}
            onSelect={() => selectClip(clip.id)}
            onUpdate={(updates) => updateClip(clip.id, updates)}
          />
        ))}
      </div>
    </div>
  );
};

// Timeline Component
const Timeline: React.FC = () => {
  const { tracks, currentTime, setCurrentTime, zoom, addTrack, duration } = useEditorStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver(entries => {
      setContainerWidth(entries[0].contentRect.width);
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - 200; // Subtract track header width
    const pixelsPerSecond = zoom * 20;
    const time = x / pixelsPerSecond;
    setCurrentTime(Math.max(0, time));
  };

  return (
    <div className="timeline-container" ref={containerRef} style={{ flex: 1, overflow: 'auto', background: '#1a1a1a' }}>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex' }}>
          <div style={{ width: 200, background: '#252525', borderRight: '1px solid #333', height: 30 }} />
          <div style={{ flex: 1, position: 'relative' }} onClick={handleTimelineClick}>
            <TimelineRuler zoom={zoom} duration={duration} width={containerWidth - 200} />
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          <div style={{ position: 'relative' }}>
            {tracks.map(track => (
              <TrackComponent key={track.id} track={track} />
            ))}
          </div>

          <Playhead currentTime={currentTime} zoom={zoom} onSeek={setCurrentTime} />
        </div>

        <div style={{ display: 'flex', gap: 8, padding: 8, background: '#252525', borderTop: '1px solid #333' }}>
          <button
            onClick={() => addTrack('video')}
            style={{
              padding: '8px 16px',
              background: '#4a9eff',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 500,
            }}
          >
            + Video Track
          </button>
          <button
            onClick={() => addTrack('audio')}
            style={{
              padding: '8px 16px',
              background: '#9b59b6',
              color: '#fff',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 500,
            }}
          >
            + Audio Track
          </button>
        </div>
      </div>
    </div>
  );
};

// Preview Panel Component
const PreviewPanel: React.FC = () => {
  const { currentTime, isPlaying, setIsPlaying, colorGrading, captions } = useEditorStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;
    const gl = canvas.getContext('webgl2');

    if (!gl) {
      console.error('WebGL2 not supported');
      return;
    }

    // WebGL rendering would go here
    // For now, just clear to black
    gl.clearColor(0, 0, 0, 1);
    gl.clear(gl.COLOR_BUFFER_BIT);
  }, [currentTime, colorGrading]);

  const activeCaptions = captions.filter(c => currentTime >= c.startTime && currentTime <= c.endTime);

  return (
    <div className="preview-panel" style={{
      background: '#000',
      position: 'relative',
      aspectRatio: '16/9',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
    }}>
      <canvas
        ref={canvasRef}
        width={1920}
        height={1080}
        style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }}
      />

      {activeCaptions.map(caption => (
        <div
          key={caption.id}
          style={{
            position: 'absolute',
            [caption.style.position]: 20,
            left: 0,
            right: 0,
            textAlign: caption.style.alignment,
            fontFamily: caption.style.fontFamily,
            fontSize: caption.style.fontSize,
            color: caption.style.color,
            backgroundColor: caption.style.backgroundColor,
            padding: '8px 16px',
          }}
        >
          {caption.text}
        </div>
      ))}
    </div>
  );
};

// Transport Controls Component
const TransportControls: React.FC = () => {
  const {
    isPlaying,
    setIsPlaying,
    currentTime,
    setCurrentTime,
    playbackRate,
    setPlaybackRate,
    setInPoint,
    setOutPoint,
    inPoint,
    outPoint,
  } = useEditorStore();

  return (
    <div className="transport-controls" style={{
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      padding: '12px 16px',
      background: '#252525',
      borderTop: '1px solid #333',
    }}>
      <button
        onClick={() => setCurrentTime(0)}
        style={{ padding: '8px 12px', background: '#333', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        title="Go to Start"
      >
        ⏮
      </button>

      <button
        onClick={() => setPlaybackRate(Math.max(0.1, playbackRate - 0.5))}
        style={{ padding: '8px 12px', background: '#333', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        title="Slower (J)"
      >
        J
      </button>

      <button
        onClick={() => setIsPlaying(!isPlaying)}
        style={{
          padding: '12px 20px',
          background: '#4a9eff',
          color: '#fff',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer',
          fontSize: 16,
        }}
        title="Play/Pause (K)"
      >
        {isPlaying ? '⏸' : '▶'}
      </button>

      <button
        onClick={() => setPlaybackRate(Math.min(4, playbackRate + 0.5))}
        style={{ padding: '8px 12px', background: '#333', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer' }}
        title="Faster (L)"
      >
        L
      </button>

      <div style={{ color: '#999', fontSize: 14, fontFamily: 'monospace', minWidth: 120 }}>
        {formatTime(currentTime)}
      </div>

      <div style={{ flex: 1 }} />

      <button
        onClick={() => setInPoint(currentTime)}
        style={{
          padding: '8px 12px',
          background: inPoint !== null ? '#4a9eff' : '#333',
          color: '#fff',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer'
        }}
        title="Set In Point (I)"
      >
        [ In
      </button>

      <button
        onClick={() => setOutPoint(currentTime)}
        style={{
          padding: '8px 12px',
          background: outPoint !== null ? '#4a9eff' : '#333',
          color: '#fff',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer'
        }}
        title="Set Out Point (O)"
      >
        Out ]
      </button>

      <div style={{ color: '#999', fontSize: 12 }}>
        Speed: {playbackRate.toFixed(1)}x
      </div>
    </div>
  );
};

// Toolbar Component
const Toolbar: React.FC = () => {
  const {
    selectedTool,
    setSelectedTool,
    undo,
    redo,
    history,
    historyIndex,
    zoom,
    setZoom,
    snapToGrid,
    setSnapToGrid,
    togglePanel,
    showEffects,
    showColorGrading,
    showAudioMixer,
    showCaptions,
    showExport,
    saveProject,
    loadProject,
  } = useEditorStore();

  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;

  const handleSaveProject = () => {
    const projectData = saveProject();
    const blob = new Blob([JSON.stringify(projectData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${projectData.projectName}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleLoadProject = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target?.result as string);
          loadProject(data);
        } catch (error) {
          console.error('Failed to load project:', error);
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };

  return (
    <div className="toolbar" style={{
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      padding: '8px 16px',
      background: '#2a2a2a',
      borderBottom: '1px solid #444',
      flexWrap: 'wrap',
    }}>
      <div style={{ display: 'flex', gap: 4 }}>
        <button
          onClick={handleSaveProject}
          style={{ padding: '8px 12px', background: '#333', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12 }}
          title="Save Project"
        >
          💾 Save
        </button>

        <button
          onClick={handleLoadProject}
          style={{ padding: '8px 12px', background: '#333', color: '#fff', border: 'none', borderRadius: 4, cursor: 'pointer', fontSize: 12 }}
          title="Load Project"
        >
          📂 Load
        </button>
      </div>

      <div style={{ width: 1, height: 24, background: '#444' }} />

      <div style={{ display: 'flex', gap: 4 }}>
        <button
          onClick={undo}
          disabled={!canUndo}
          style={{
            padding: '8px 12px',
            background: canUndo ? '#333' : '#1a1a1a',
            color: canUndo ? '#fff' : '#666',
            border: 'none',
            borderRadius: 4,
            cursor: canUndo ? 'pointer' : 'not-allowed',
            fontSize: 12,
          }}
          title="Undo (Cmd+Z)"
        >
          ↶ Undo
        </button>

        <button
          onClick={redo}
          disabled={!canRedo}
          style={{
            padding: '8px 12px',
            background: canRedo ? '#333' : '#1a1a1a',
            color: canRedo ? '#fff' : '#666',
            border: 'none',
            borderRadius: 4,
            cursor: canRedo ? 'pointer' : 'not-allowed',
            fontSize: 12,
          }}
          title="Redo (Cmd+Shift+Z)"
        >
          ↷ Redo
        </button>
      </div>

      <div style={{ width: 1, height: 24, background: '#444' }} />

      <div style={{ display: 'flex', gap: 4 }}>
        <button
          onClick={() => setSelectedTool('selection')}
          style={{
            padding: '8px 12px',
            background: selectedTool === 'selection' ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
          title="Selection Tool (V)"
        >
          ↖ Select
        </button>

        <button
          onClick={() => setSelectedTool('razor')}
          style={{
            padding: '8px 12px',
            background: selectedTool === 'razor' ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
          title="Razor Tool (C)"
        >
          ✂ Razor
        </button>

        <button
          onClick={() => setSelectedTool('hand')}
          style={{
            padding: '8px 12px',
            background: selectedTool === 'hand' ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
          title="Hand Tool (H)"
        >
          ✋ Hand
        </button>
      </div>

      <div style={{ width: 1, height: 24, background: '#444' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <span style={{ color: '#999', fontSize: 12 }}>Zoom:</span>
        <input
          type="range"
          min="0.1"
          max="5"
          step="0.1"
          value={zoom}
          onChange={(e) => setZoom(parseFloat(e.target.value))}
          style={{ width: 100 }}
        />
        <span style={{ color: '#fff', fontSize: 12, minWidth: 40 }}>{Math.round(zoom * 100)}%</span>
      </div>

      <label style={{ display: 'flex', alignItems: 'center', gap: 4, color: '#fff', fontSize: 12, cursor: 'pointer' }}>
        <input
          type="checkbox"
          checked={snapToGrid}
          onChange={(e) => setSnapToGrid(e.target.checked)}
        />
        Snap
      </label>

      <div style={{ flex: 1 }} />

      <div style={{ display: 'flex', gap: 4 }}>
        <button
          onClick={() => togglePanel('effects')}
          style={{
            padding: '8px 12px',
            background: showEffects ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
        >
          ✨ Effects
        </button>

        <button
          onClick={() => togglePanel('colorGrading')}
          style={{
            padding: '8px 12px',
            background: showColorGrading ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
        >
          🎨 Color
        </button>

        <button
          onClick={() => togglePanel('audioMixer')}
          style={{
            padding: '8px 12px',
            background: showAudioMixer ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
        >
          🎚 Audio
        </button>

        <button
          onClick={() => togglePanel('captions')}
          style={{
            padding: '8px 12px',
            background: showCaptions ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
        >
          💬 Captions
        </button>

        <button
          onClick={() => togglePanel('export')}
          style={{
            padding: '8px 12px',
            background: showExport ? '#4a9eff' : '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
          }}
        >
          📤 Export
        </button>
      </div>
    </div>
  );
};

// Effects Panel Component
const EffectsPanel: React.FC = () => {
  const transitions = [
    { name: 'Cross Dissolve', type: 'transition' },
    { name: 'Fade to Black', type: 'transition' },
    { name: 'Fade to White', type: 'transition' },
    { name: 'Wipe Left', type: 'transition' },
    { name: 'Wipe Right', type: 'transition' },
    { name: 'Zoom In', type: 'transition' },
    { name: 'Zoom Out', type: 'transition' },
  ];

  const filters = [
    { name: 'Blur', type: 'filter' },
    { name: 'Sharpen', type: 'filter' },
    { name: 'Glow', type: 'filter' },
    { name: 'Vignette', type: 'filter' },
    { name: 'Film Grain', type: 'filter' },
    { name: 'Chromatic Aberration', type: 'filter' },
  ];

  return (
    <div className="effects-panel" style={{
      width: 280,
      background: '#252525',
      borderLeft: '1px solid #333',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'auto',
    }}>
      <div style={{ padding: 16, borderBottom: '1px solid #333' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: 14, fontWeight: 600 }}>Effects</h3>
      </div>

      <div style={{ padding: 16 }}>
        <h4 style={{ margin: '0 0 12px 0', color: '#999', fontSize: 12, fontWeight: 500, textTransform: 'uppercase' }}>Transitions</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {transitions.map(effect => (
            <div
              key={effect.name}
              draggable
              style={{
                padding: '8px 12px',
                background: '#333',
                borderRadius: 4,
                color: '#fff',
                fontSize: 12,
                cursor: 'grab',
              }}
            >
              {effect.name}
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: 16 }}>
        <h4 style={{ margin: '0 0 12px 0', color: '#999', fontSize: 12, fontWeight: 500, textTransform: 'uppercase' }}>Filters</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filters.map(effect => (
            <div
              key={effect.name}
              draggable
              style={{
                padding: '8px 12px',
                background: '#333',
                borderRadius: 4,
                color: '#fff',
                fontSize: 12,
                cursor: 'grab',
              }}
            >
              {effect.name}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Color Grading Panel Component
const ColorGradingPanel: React.FC = () => {
  const { colorGrading, updateColorGrading } = useEditorStore();

  const Slider: React.FC<{ label: string; value: number; onChange: (value: number) => void; min?: number; max?: number; step?: number }> = ({
    label,
    value,
    onChange,
    min = -100,
    max = 100,
    step = 1,
  }) => (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <label style={{ color: '#999', fontSize: 12 }}>{label}</label>
        <span style={{ color: '#fff', fontSize: 12 }}>{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        style={{ width: '100%' }}
      />
    </div>
  );

  return (
    <div className="color-grading-panel" style={{
      width: 280,
      background: '#252525',
      borderLeft: '1px solid #333',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'auto',
    }}>
      <div style={{ padding: 16, borderBottom: '1px solid #333' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: 14, fontWeight: 600 }}>Color Grading</h3>
      </div>

      <div style={{ padding: 16 }}>
        <Slider
          label="Exposure"
          value={colorGrading.exposure}
          onChange={(value) => updateColorGrading({ exposure: value })}
        />

        <Slider
          label="Contrast"
          value={colorGrading.contrast}
          onChange={(value) => updateColorGrading({ contrast: value })}
        />

        <Slider
          label="Highlights"
          value={colorGrading.highlights}
          onChange={(value) => updateColorGrading({ highlights: value })}
        />

        <Slider
          label="Shadows"
          value={colorGrading.shadows}
          onChange={(value) => updateColorGrading({ shadows: value })}
        />

        <Slider
          label="Whites"
          value={colorGrading.whites}
          onChange={(value) => updateColorGrading({ whites: value })}
        />

        <Slider
          label="Blacks"
          value={colorGrading.blacks}
          onChange={(value) => updateColorGrading({ blacks: value })}
        />

        <Slider
          label="Temperature"
          value={colorGrading.temperature}
          onChange={(value) => updateColorGrading({ temperature: value })}
        />

        <Slider
          label="Tint"
          value={colorGrading.tint}
          onChange={(value) => updateColorGrading({ tint: value })}
        />

        <Slider
          label="Saturation"
          value={colorGrading.saturation}
          onChange={(value) => updateColorGrading({ saturation: value })}
        />

        <Slider
          label="Vibrance"
          value={colorGrading.vibrance}
          onChange={(value) => updateColorGrading({ vibrance: value })}
        />

        <button
          onClick={() => updateColorGrading({
            exposure: 0,
            contrast: 0,
            highlights: 0,
            shadows: 0,
            whites: 0,
            blacks: 0,
            temperature: 0,
            tint: 0,
            saturation: 0,
            vibrance: 0,
          })}
          style={{
            width: '100%',
            padding: '8px 12px',
            background: '#333',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 12,
            marginTop: 8,
          }}
        >
          Reset All
        </button>
      </div>
    </div>
  );
};

// Audio Mixer Panel Component
const AudioMixerPanel: React.FC = () => {
  const { tracks, updateTrack } = useEditorStore();
  const audioTracks = tracks.filter(t => t.type === 'audio');

  return (
    <div className="audio-mixer-panel" style={{
      width: 280,
      background: '#252525',
      borderLeft: '1px solid #333',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'auto',
    }}>
      <div style={{ padding: 16, borderBottom: '1px solid #333' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: 14, fontWeight: 600 }}>Audio Mixer</h3>
      </div>

      <div style={{ padding: 16 }}>
        {audioTracks.map(track => (
          <div key={track.id} style={{ marginBottom: 24 }}>
            <div style={{ marginBottom: 8 }}>
              <span style={{ color: '#fff', fontSize: 12, fontWeight: 500 }}>{track.name}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ flex: 1 }}>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="0.01"
                  value={track.volume}
                  onChange={(e) => updateTrack(track.id, { volume: parseFloat(e.target.value) })}
                  style={{ width: '100%' }}
                />
              </div>
              <span style={{ color: '#999', fontSize: 11, minWidth: 40 }}>{Math.round(track.volume * 100)}%</span>
            </div>

            <div style={{ display: 'flex', gap: 4, marginTop: 8 }}>
              <button
                onClick={() => updateTrack(track.id, { muted: !track.muted })}
                style={{
                  flex: 1,
                  padding: '6px',
                  background: track.muted ? '#ff4444' : '#333',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontSize: 11,
                }}
              >
                {track.muted ? 'Unmute' : 'Mute'}
              </button>

              <button
                onClick={() => updateTrack(track.id, { solo: !track.solo })}
                style={{
                  flex: 1,
                  padding: '6px',
                  background: track.solo ? '#ffaa00' : '#333',
                  color: '#fff',
                  border: 'none',
                  borderRadius: 4,
                  cursor: 'pointer',
                  fontSize: 11,
                }}
              >
                {track.solo ? 'Unsolo' : 'Solo'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Caption Editor Panel Component
const CaptionEditorPanel: React.FC = () => {
  const { captions, addCaption, updateCaption, deleteCaption, currentTime } = useEditorStore();

  const handleAddCaption = () => {
    const newCaption: Caption = {
      id: `caption-${Date.now()}`,
      startTime: currentTime,
      endTime: currentTime + 3,
      text: 'New Caption',
      style: {
        fontFamily: 'Arial',
        fontSize: 32,
        color: '#ffffff',
        backgroundColor: 'rgba(0,0,0,0.7)',
        position: 'bottom',
        alignment: 'center',
      },
    };
    addCaption(newCaption);
  };

  return (
    <div className="caption-editor-panel" style={{
      width: 320,
      background: '#252525',
      borderLeft: '1px solid #333',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'auto',
    }}>
      <div style={{ padding: 16, borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: 14, fontWeight: 600 }}>Captions</h3>
        <button
          onClick={handleAddCaption}
          style={{
            padding: '6px 12px',
            background: '#4a9eff',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 11,
          }}
        >
          + Add
        </button>
      </div>

      <div style={{ flex: 1, overflow: 'auto' }}>
        {captions.map(caption => (
          <div key={caption.id} style={{ padding: 16, borderBottom: '1px solid #333' }}>
            <div style={{ marginBottom: 8 }}>
              <textarea
                value={caption.text}
                onChange={(e) => updateCaption(caption.id, { text: e.target.value })}
                style={{
                  width: '100%',
                  minHeight: 60,
                  background: '#1a1a1a',
                  border: '1px solid #444',
                  color: '#fff',
                  padding: 8,
                  borderRadius: 4,
                  fontSize: 12,
                  resize: 'vertical',
                }}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
              <div>
                <label style={{ color: '#999', fontSize: 11, display: 'block', marginBottom: 4 }}>Start</label>
                <input
                  type="number"
                  value={caption.startTime}
                  onChange={(e) => updateCaption(caption.id, { startTime: parseFloat(e.target.value) })}
                  style={{
                    width: '100%',
                    background: '#1a1a1a',
                    border: '1px solid #444',
                    color: '#fff',
                    padding: '4px 8px',
                    borderRadius: 4,
                    fontSize: 11,
                  }}
                  step="0.1"
                />
              </div>

              <div>
                <label style={{ color: '#999', fontSize: 11, display: 'block', marginBottom: 4 }}>End</label>
                <input
                  type="number"
                  value={caption.endTime}
                  onChange={(e) => updateCaption(caption.id, { endTime: parseFloat(e.target.value) })}
                  style={{
                    width: '100%',
                    background: '#1a1a1a',
                    border: '1px solid #444',
                    color: '#fff',
                    padding: '4px 8px',
                    borderRadius: 4,
                    fontSize: 11,
                  }}
                  step="0.1"
                />
              </div>
            </div>

            <div style={{ marginBottom: 8 }}>
              <label style={{ color: '#999', fontSize: 11, display: 'block', marginBottom: 4 }}>Position</label>
              <select
                value={caption.style.position}
                onChange={(e) => updateCaption(caption.id, {
                  style: { ...caption.style, position: e.target.value as 'top' | 'center' | 'bottom' }
                })}
                style={{
                  width: '100%',
                  background: '#1a1a1a',
                  border: '1px solid #444',
                  color: '#fff',
                  padding: '4px 8px',
                  borderRadius: 4,
                  fontSize: 11,
                }}
              >
                <option value="top">Top</option>
                <option value="center">Center</option>
                <option value="bottom">Bottom</option>
              </select>
            </div>

            <button
              onClick={() => deleteCaption(caption.id)}
              style={{
                width: '100%',
                padding: '6px',
                background: '#ff4444',
                color: '#fff',
                border: 'none',
                borderRadius: 4,
                cursor: 'pointer',
                fontSize: 11,
              }}
            >
              Delete
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

// Export Settings Panel Component
const ExportSettingsPanel: React.FC = () => {
  const { exportSettings, updateExportSettings } = useEditorStore();

  const platformPresets = {
    youtube: { resolution: '1080p' as const, fps: 30 as const, format: 'mp4' as const },
    instagram: { resolution: '1080p' as const, fps: 30 as const, format: 'mp4' as const },
    tiktok: { resolution: '1080p' as const, fps: 30 as const, format: 'mp4' as const },
    facebook: { resolution: '1080p' as const, fps: 30 as const, format: 'mp4' as const },
  };

  const handlePlatformChange = (platform: keyof typeof platformPresets | 'custom') => {
    if (platform === 'custom') {
      updateExportSettings({ platform });
    } else {
      updateExportSettings({
        platform,
        ...platformPresets[platform],
      });
    }
  };

  const handleExport = () => {
    // console.log('Exporting with settings:', exportSettings);
    alert('Export started! This would trigger the rendering process.');
  };

  return (
    <div className="export-settings-panel" style={{
      width: 320,
      background: '#252525',
      borderLeft: '1px solid #333',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'auto',
    }}>
      <div style={{ padding: 16, borderBottom: '1px solid #333' }}>
        <h3 style={{ margin: 0, color: '#fff', fontSize: 14, fontWeight: 600 }}>Export Settings</h3>
      </div>

      <div style={{ padding: 16, flex: 1 }}>
        <div style={{ marginBottom: 16 }}>
          <label style={{ color: '#999', fontSize: 12, display: 'block', marginBottom: 8 }}>Platform Preset</label>
          <select
            value={exportSettings.platform}
            onChange={(e) => handlePlatformChange(e.target.value as any)}
            style={{
              width: '100%',
              background: '#1a1a1a',
              border: '1px solid #444',
              color: '#fff',
              padding: '8px 12px',
              borderRadius: 4,
              fontSize: 12,
            }}
          >
            <option value="youtube">YouTube</option>
            <option value="instagram">Instagram</option>
            <option value="tiktok">TikTok</option>
            <option value="facebook">Facebook</option>
            <option value="custom">Custom</option>
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ color: '#999', fontSize: 12, display: 'block', marginBottom: 8 }}>Format</label>
          <select
            value={exportSettings.format}
            onChange={(e) => updateExportSettings({ format: e.target.value as any })}
            style={{
              width: '100%',
              background: '#1a1a1a',
              border: '1px solid #444',
              color: '#fff',
              padding: '8px 12px',
              borderRadius: 4,
              fontSize: 12,
            }}
          >
            <option value="mp4">MP4</option>
            <option value="mov">MOV</option>
            <option value="webm">WebM</option>
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ color: '#999', fontSize: 12, display: 'block', marginBottom: 8 }}>Resolution</label>
          <select
            value={exportSettings.resolution}
            onChange={(e) => updateExportSettings({ resolution: e.target.value as any })}
            style={{
              width: '100%',
              background: '#1a1a1a',
              border: '1px solid #444',
              color: '#fff',
              padding: '8px 12px',
              borderRadius: 4,
              fontSize: 12,
            }}
          >
            <option value="720p">720p (HD)</option>
            <option value="1080p">1080p (Full HD)</option>
            <option value="4k">4K (Ultra HD)</option>
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ color: '#999', fontSize: 12, display: 'block', marginBottom: 8 }}>Frame Rate</label>
          <select
            value={exportSettings.fps}
            onChange={(e) => updateExportSettings({ fps: parseInt(e.target.value) as any })}
            style={{
              width: '100%',
              background: '#1a1a1a',
              border: '1px solid #444',
              color: '#fff',
              padding: '8px 12px',
              borderRadius: 4,
              fontSize: 12,
            }}
          >
            <option value="24">24 fps</option>
            <option value="30">30 fps</option>
            <option value="60">60 fps</option>
          </select>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ color: '#999', fontSize: 12, display: 'block', marginBottom: 8 }}>Quality</label>
          <select
            value={exportSettings.quality}
            onChange={(e) => updateExportSettings({ quality: e.target.value as any })}
            style={{
              width: '100%',
              background: '#1a1a1a',
              border: '1px solid #444',
              color: '#fff',
              padding: '8px 12px',
              borderRadius: 4,
              fontSize: 12,
            }}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="ultra">Ultra</option>
          </select>
        </div>

        <button
          onClick={handleExport}
          style={{
            width: '100%',
            padding: '12px',
            background: '#4a9eff',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 14,
            fontWeight: 600,
            marginTop: 16,
          }}
        >
          Export Video
        </button>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const ProVideoEditor: React.FC = () => {
  const {
    isPlaying,
    setIsPlaying,
    currentTime,
    setCurrentTime,
    playbackRate,
    selectedTool,
    setSelectedTool,
    showEffects,
    showColorGrading,
    showAudioMixer,
    showCaptions,
    showExport,
    undo,
    redo,
    setInPoint,
    setOutPoint,
    splitClipAtTime,
    selectedClipIds,
    clips,
    copySelectedClips,
    pasteClips,
    cutSelectedClips,
    zoom,
    setZoom,
  } = useEditorStore();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent defaults for editor shortcuts
      const editorShortcuts = ['j', 'k', 'l', 'i', 'o', 'c', 'v', 'h', 'z'];
      if (editorShortcuts.includes(e.key.toLowerCase()) && !e.metaKey && !e.ctrlKey) {
        // Only prevent if not focused on input
        const target = e.target as HTMLElement;
        if (target.tagName !== 'INPUT' && target.tagName !== 'TEXTAREA') {
          e.preventDefault();
        }
      }

      // Playback controls
      if (e.key === ' ') {
        e.preventDefault();
        setIsPlaying(!isPlaying);
      } else if (e.key === 'j' || e.key === 'J') {
        // Slower playback
      } else if (e.key === 'k' || e.key === 'K') {
        setIsPlaying(false);
      } else if (e.key === 'l' || e.key === 'L') {
        // Faster playback
      }

      // In/Out points
      else if (e.key === 'i' || e.key === 'I') {
        setInPoint(currentTime);
      } else if (e.key === 'o' || e.key === 'O') {
        setOutPoint(currentTime);
      }

      // Tools
      else if (e.key === 'v' || e.key === 'V') {
        setSelectedTool('selection');
      } else if (e.key === 'c' || e.key === 'C') {
        setSelectedTool('razor');
      } else if (e.key === 'h' || e.key === 'H') {
        setSelectedTool('hand');
      }

      // Edit operations
      else if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault();
        if (e.shiftKey) {
          redo();
        } else {
          undo();
        }
      } else if ((e.metaKey || e.ctrlKey) && e.key === 'c') {
        e.preventDefault();
        copySelectedClips();
      } else if ((e.metaKey || e.ctrlKey) && e.key === 'v') {
        e.preventDefault();
        pasteClips();
      } else if ((e.metaKey || e.ctrlKey) && e.key === 'x') {
        e.preventDefault();
        cutSelectedClips();
      }

      // Split clip
      else if (e.key === 's' || e.key === 'S') {
        if (selectedClipIds.length === 1) {
          const clip = clips.find(c => c.id === selectedClipIds[0]);
          if (clip && currentTime > clip.startTime && currentTime < clip.startTime + clip.duration) {
            splitClipAtTime(clip.id, currentTime);
          }
        }
      }

      // Zoom
      else if ((e.metaKey || e.ctrlKey) && (e.key === '=' || e.key === '+')) {
        e.preventDefault();
        setZoom(zoom + 0.2);
      } else if ((e.metaKey || e.ctrlKey) && e.key === '-') {
        e.preventDefault();
        setZoom(zoom - 0.2);
      }
    };

    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        setZoom(zoom + delta);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('wheel', handleWheel);
    };
  }, [isPlaying, currentTime, selectedTool, selectedClipIds, zoom]);

  // Playback loop
  useEffect(() => {
    if (!isPlaying) return;

    const intervalId = setInterval(() => {
      setCurrentTime(currentTime + (1 / 30) * playbackRate);
    }, 1000 / 30);

    return () => clearInterval(intervalId);
  }, [isPlaying, currentTime, playbackRate]);

  return (
    <div className="pro-video-editor" style={{
      width: '100vw',
      height: '100vh',
      display: 'flex',
      flexDirection: 'column',
      background: '#1a1a1a',
      color: '#fff',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      overflow: 'hidden',
    }}>
      <Toolbar />

      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: 16, background: '#252525' }}>
            <PreviewPanel />
          </div>

          <TransportControls />

          <Timeline />
        </div>

        {showEffects && <EffectsPanel />}
        {showColorGrading && <ColorGradingPanel />}
        {showAudioMixer && <AudioMixerPanel />}
        {showCaptions && <CaptionEditorPanel />}
        {showExport && <ExportSettingsPanel />}
      </div>

      <style>{`
        .pro-video-editor * {
          box-sizing: border-box;
        }

        .pro-video-editor input[type="range"] {
          -webkit-appearance: none;
          appearance: none;
          background: transparent;
          cursor: pointer;
        }

        .pro-video-editor input[type="range"]::-webkit-slider-track {
          background: #444;
          height: 4px;
          border-radius: 2px;
        }

        .pro-video-editor input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          background: #4a9eff;
          height: 14px;
          width: 14px;
          border-radius: 7px;
          margin-top: -5px;
        }

        .pro-video-editor input[type="range"]::-moz-range-track {
          background: #444;
          height: 4px;
          border-radius: 2px;
        }

        .pro-video-editor input[type="range"]::-moz-range-thumb {
          background: #4a9eff;
          height: 14px;
          width: 14px;
          border-radius: 7px;
          border: none;
        }

        .pro-video-editor ::-webkit-scrollbar {
          width: 10px;
          height: 10px;
        }

        .pro-video-editor ::-webkit-scrollbar-track {
          background: #1a1a1a;
        }

        .pro-video-editor ::-webkit-scrollbar-thumb {
          background: #444;
          border-radius: 5px;
        }

        .pro-video-editor ::-webkit-scrollbar-thumb:hover {
          background: #555;
        }

        .timeline-clip:hover .resize-handle-left,
        .timeline-clip:hover .resize-handle-right {
          background: rgba(255,255,255,0.3);
        }

        .timeline-clip.selected {
          box-shadow: 0 0 0 2px #fff;
        }
      `}</style>
    </div>
  );
};

export default ProVideoEditor;
