import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  PlayIcon,
  PauseIcon,
  ScissorsIcon,
  SlidersIcon,
  DownloadIcon,
  SparklesIcon,
  SoundWaveIcon,
  FilmIcon
} from './icons';

interface TimelineClip {
  id: string;
  type: 'video' | 'audio' | 'text' | 'image';
  name: string;
  startTime: number;
  duration: number;
  trackIndex: number;
  color: string;
  thumbnail?: string;
}

interface Track {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'text' | 'overlay';
  clips: TimelineClip[];
  muted?: boolean;
  locked?: boolean;
}

interface ProVideoEditorProps {
  projectId?: string;
  onSave?: (project: any) => void;
  onExport?: (settings: ExportSettings) => void;
}

interface ExportSettings {
  format: 'mp4' | 'webm' | 'mov';
  quality: 'draft' | 'standard' | 'high' | '4k';
  fps: 24 | 30 | 60;
}

const MOCK_TRACKS: Track[] = [
  {
    id: 'video-1',
    name: 'Video 1',
    type: 'video',
    clips: [
      { id: 'clip-1', type: 'video', name: 'Intro.mp4', startTime: 0, duration: 5, trackIndex: 0, color: '#6366f1' },
      { id: 'clip-2', type: 'video', name: 'Main.mp4', startTime: 5, duration: 15, trackIndex: 0, color: '#8b5cf6' },
      { id: 'clip-3', type: 'video', name: 'Outro.mp4', startTime: 20, duration: 5, trackIndex: 0, color: '#a855f7' },
    ],
  },
  {
    id: 'video-2',
    name: 'B-Roll',
    type: 'video',
    clips: [
      { id: 'clip-4', type: 'video', name: 'Overlay1.mp4', startTime: 8, duration: 4, trackIndex: 1, color: '#22c55e' },
      { id: 'clip-5', type: 'video', name: 'Overlay2.mp4', startTime: 15, duration: 3, trackIndex: 1, color: '#16a34a' },
    ],
  },
  {
    id: 'audio-1',
    name: 'Music',
    type: 'audio',
    clips: [
      { id: 'clip-6', type: 'audio', name: 'Background.mp3', startTime: 0, duration: 25, trackIndex: 2, color: '#f59e0b' },
    ],
  },
  {
    id: 'audio-2',
    name: 'Voiceover',
    type: 'audio',
    clips: [
      { id: 'clip-7', type: 'audio', name: 'VO_Take3.wav', startTime: 2, duration: 18, trackIndex: 3, color: '#ef4444' },
    ],
  },
  {
    id: 'text-1',
    name: 'Text/Captions',
    type: 'text',
    clips: [
      { id: 'clip-8', type: 'text', name: 'Title Card', startTime: 0, duration: 3, trackIndex: 4, color: '#0ea5e9' },
      { id: 'clip-9', type: 'text', name: 'CTA Text', startTime: 22, duration: 3, trackIndex: 4, color: '#06b6d4' },
    ],
  },
];

const TOOLS = [
  { id: 'select', name: 'Select', icon: '⬚' },
  { id: 'cut', name: 'Cut', icon: ScissorsIcon },
  { id: 'trim', name: 'Trim', icon: '⟷' },
  { id: 'text', name: 'Text', icon: 'T' },
  { id: 'effects', name: 'Effects', icon: SparklesIcon },
];

export const ProVideoEditor: React.FC<ProVideoEditorProps> = ({ projectId, onSave, onExport }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration] = useState(25);
  const [zoom, setZoom] = useState(1);
  const [selectedClip, setSelectedClip] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState('select');
  const [tracks, setTracks] = useState<Track[]>(MOCK_TRACKS);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportSettings, setExportSettings] = useState<ExportSettings>({
    format: 'mp4',
    quality: 'high',
    fps: 30,
  });

  const timelineRef = useRef<HTMLDivElement>(null);
  const playbackInterval = useRef<NodeJS.Timeout | null>(null);

  const pixelsPerSecond = 40 * zoom;
  const totalWidth = duration * pixelsPerSecond;

  useEffect(() => {
    return () => {
      if (playbackInterval.current) {
        clearInterval(playbackInterval.current);
      }
    };
  }, []);

  const togglePlayback = useCallback(() => {
    if (isPlaying) {
      if (playbackInterval.current) {
        clearInterval(playbackInterval.current);
      }
    } else {
      playbackInterval.current = setInterval(() => {
        setCurrentTime(prev => {
          if (prev >= duration) {
            if (playbackInterval.current) clearInterval(playbackInterval.current);
            setIsPlaying(false);
            return 0;
          }
          return prev + 0.1;
        });
      }, 100);
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying, duration]);

  const handleTimelineClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left + timelineRef.current.scrollLeft;
    const newTime = Math.max(0, Math.min(duration, x / pixelsPerSecond));
    setCurrentTime(newTime);
  }, [duration, pixelsPerSecond]);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const frames = Math.floor((seconds % 1) * 30);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`;
  };

  const handleExport = () => {
    onExport?.(exportSettings);
    setShowExportModal(false);
  };

  return (
    <div className="h-screen bg-gray-950 text-white flex flex-col">
      {/* Top Toolbar */}
      <div className="h-12 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <FilmIcon className="w-6 h-6 text-indigo-400" />
          <span className="font-semibold">Pro Video Editor</span>
          <span className="text-gray-500">|</span>
          <span className="text-gray-400 text-sm">{projectId || 'Untitled Project'}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onSave?.(tracks)}
            className="px-3 py-1.5 text-sm bg-gray-800 hover:bg-gray-700 rounded transition-colors"
          >
            Save
          </button>
          <button
            onClick={() => setShowExportModal(true)}
            className="px-3 py-1.5 text-sm bg-indigo-600 hover:bg-indigo-700 rounded transition-colors flex items-center gap-2"
          >
            <DownloadIcon className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Tools */}
        <div className="w-14 bg-gray-900 border-r border-gray-800 flex flex-col items-center py-2 gap-1">
          {TOOLS.map(tool => (
            <button
              key={tool.id}
              onClick={() => setSelectedTool(tool.id)}
              className={`w-10 h-10 rounded flex items-center justify-center transition-colors ${
                selectedTool === tool.id
                  ? 'bg-indigo-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
              title={tool.name}
            >
              {typeof tool.icon === 'string' ? (
                <span className="text-lg">{tool.icon}</span>
              ) : (
                <tool.icon className="w-5 h-5" />
              )}
            </button>
          ))}
        </div>

        {/* Center - Preview */}
        <div className="flex-1 flex flex-col">
          {/* Video Preview */}
          <div className="flex-1 bg-black flex items-center justify-center">
            <div className="relative w-full max-w-3xl aspect-video bg-gray-900 rounded-lg overflow-hidden">
              {/* Placeholder video preview */}
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <FilmIcon className="w-16 h-16 text-gray-700 mx-auto mb-4" />
                  <p className="text-gray-500">Video Preview</p>
                  <p className="text-gray-600 text-sm mt-1">{formatTime(currentTime)}</p>
                </div>
              </div>

              {/* Playback Controls Overlay */}
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 bg-black/60 backdrop-blur px-4 py-2 rounded-full">
                <button
                  onClick={() => setCurrentTime(0)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  ⏮
                </button>
                <button
                  onClick={togglePlayback}
                  className="w-10 h-10 rounded-full bg-white text-black flex items-center justify-center hover:scale-105 transition-transform"
                >
                  {isPlaying ? <PauseIcon className="w-5 h-5" /> : <PlayIcon className="w-5 h-5" />}
                </button>
                <button
                  onClick={() => setCurrentTime(duration)}
                  className="text-gray-400 hover:text-white transition-colors"
                >
                  ⏭
                </button>
              </div>
            </div>
          </div>

          {/* Timeline Controls */}
          <div className="h-10 bg-gray-900 border-t border-gray-800 flex items-center justify-between px-4">
            <div className="flex items-center gap-4">
              <span className="text-sm font-mono">{formatTime(currentTime)}</span>
              <span className="text-gray-600">/</span>
              <span className="text-sm font-mono text-gray-400">{formatTime(duration)}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Zoom:</span>
              <input
                type="range"
                min="0.5"
                max="3"
                step="0.1"
                value={zoom}
                onChange={e => setZoom(Number(e.target.value))}
                className="w-24 accent-indigo-600"
              />
              <span className="text-xs text-gray-400 w-8">{Math.round(zoom * 100)}%</span>
            </div>
          </div>

          {/* Timeline */}
          <div className="h-64 bg-gray-900 border-t border-gray-800 overflow-hidden">
            {/* Time Ruler */}
            <div
              ref={timelineRef}
              className="h-6 bg-gray-800/50 border-b border-gray-700 overflow-x-auto cursor-pointer relative"
              onClick={handleTimelineClick}
            >
              <div style={{ width: totalWidth }} className="h-full relative">
                {Array.from({ length: Math.ceil(duration) + 1 }).map((_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 h-full border-l border-gray-700 text-xs text-gray-500 pl-1"
                    style={{ left: i * pixelsPerSecond }}
                  >
                    {i}s
                  </div>
                ))}
                {/* Playhead */}
                <div
                  className="absolute top-0 w-0.5 h-full bg-red-500 z-10"
                  style={{ left: currentTime * pixelsPerSecond }}
                >
                  <div className="absolute -top-0 left-1/2 -translate-x-1/2 w-3 h-3 bg-red-500 rotate-45" />
                </div>
              </div>
            </div>

            {/* Tracks */}
            <div className="flex-1 overflow-y-auto overflow-x-auto">
              {tracks.map((track, trackIndex) => (
                <div key={track.id} className="flex h-12 border-b border-gray-800">
                  {/* Track Header */}
                  <div className="w-32 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex items-center px-2 gap-2">
                    {track.type === 'audio' ? (
                      <SoundWaveIcon className="w-4 h-4 text-orange-400" />
                    ) : track.type === 'video' ? (
                      <FilmIcon className="w-4 h-4 text-indigo-400" />
                    ) : (
                      <span className="text-blue-400 font-bold text-xs">T</span>
                    )}
                    <span className="text-xs text-gray-400 truncate">{track.name}</span>
                  </div>

                  {/* Track Content */}
                  <div className="flex-1 relative bg-gray-950/50" style={{ width: totalWidth }}>
                    {track.clips.map(clip => (
                      <div
                        key={clip.id}
                        onClick={() => setSelectedClip(clip.id)}
                        className={`absolute top-1 h-10 rounded cursor-pointer transition-all ${
                          selectedClip === clip.id ? 'ring-2 ring-white' : ''
                        }`}
                        style={{
                          left: clip.startTime * pixelsPerSecond,
                          width: clip.duration * pixelsPerSecond,
                          backgroundColor: clip.color,
                        }}
                      >
                        <div className="px-2 py-1 text-xs truncate font-medium">
                          {clip.name}
                        </div>
                      </div>
                    ))}
                    {/* Playhead line through track */}
                    <div
                      className="absolute top-0 w-0.5 h-full bg-red-500/50 pointer-events-none"
                      style={{ left: currentTime * pixelsPerSecond }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Panel - Properties */}
        <div className="w-64 bg-gray-900 border-l border-gray-800 p-4 overflow-y-auto">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <SlidersIcon className="w-4 h-4" />
            Properties
          </h3>
          {selectedClip ? (
            <div className="space-y-4">
              {tracks.flatMap(t => t.clips).filter(c => c.id === selectedClip).map(clip => (
                <div key={clip.id} className="space-y-3">
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Name</label>
                    <input
                      type="text"
                      value={clip.name}
                      readOnly
                      className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Start</label>
                      <input
                        type="text"
                        value={formatTime(clip.startTime)}
                        readOnly
                        className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-400 mb-1">Duration</label>
                      <input
                        type="text"
                        value={formatTime(clip.duration)}
                        readOnly
                        className="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-sm font-mono"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-400 mb-1">Type</label>
                    <span className="px-2 py-1 bg-gray-800 rounded text-xs capitalize">{clip.type}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">Select a clip to edit properties</p>
          )}
        </div>
      </div>

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">Export Video</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Format</label>
                <select
                  value={exportSettings.format}
                  onChange={e => setExportSettings(prev => ({ ...prev, format: e.target.value as ExportSettings['format'] }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                >
                  <option value="mp4">MP4 (H.264)</option>
                  <option value="webm">WebM (VP9)</option>
                  <option value="mov">MOV (ProRes)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Quality</label>
                <select
                  value={exportSettings.quality}
                  onChange={e => setExportSettings(prev => ({ ...prev, quality: e.target.value as ExportSettings['quality'] }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                >
                  <option value="draft">Draft (720p)</option>
                  <option value="standard">Standard (1080p)</option>
                  <option value="high">High (1080p, high bitrate)</option>
                  <option value="4k">4K UHD</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-400 mb-2">Frame Rate</label>
                <select
                  value={exportSettings.fps}
                  onChange={e => setExportSettings(prev => ({ ...prev, fps: Number(e.target.value) as ExportSettings['fps'] }))}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg"
                >
                  <option value="24">24 fps (Film)</option>
                  <option value="30">30 fps (Standard)</option>
                  <option value="60">60 fps (Smooth)</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowExportModal(false)}
                className="flex-1 px-4 py-2 border border-gray-600 rounded-lg hover:bg-gray-800 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleExport}
                className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
              >
                Export
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProVideoEditor;
