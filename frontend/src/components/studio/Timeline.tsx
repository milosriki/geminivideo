import React, { useRef } from 'react';
import {
  FilmIcon,
  MusicalNoteIcon,
  LockClosedIcon,
  LockOpenIcon,
  EyeIcon,
  EyeSlashIcon,
} from '@heroicons/react/24/outline';

export interface TimelineClip {
  id: string;
  type: 'video' | 'audio' | 'text' | 'image';
  name: string;
  startTime: number;
  duration: number;
  trackIndex: number;
  color: string;
  thumbnail?: string;
}

export interface TimelineTrack {
  id: string;
  name: string;
  type: 'video' | 'audio' | 'text' | 'overlay';
  clips: TimelineClip[];
  muted?: boolean;
  locked?: boolean;
  visible?: boolean;
}

interface TimelineProps {
  tracks: TimelineTrack[];
  currentTime: number;
  duration: number;
  zoom: number;
  selectedClip: string | null;
  onTrackUpdate?: (tracks: TimelineTrack[]) => void;
  onClipSelect?: (clipId: string | null) => void;
  onSeek?: (time: number) => void;
  onZoomChange?: (zoom: number) => void;
}

// Mock clips for demonstration
const MOCK_CLIPS: TimelineClip[] = [
  { id: 'clip-1', type: 'video', name: 'Intro Scene', startTime: 0, duration: 5, trackIndex: 0, color: '#6366f1' },
  { id: 'clip-2', type: 'video', name: 'Main Content', startTime: 5, duration: 15, trackIndex: 0, color: '#8b5cf6' },
  { id: 'clip-3', type: 'video', name: 'Outro', startTime: 20, duration: 5, trackIndex: 0, color: '#a855f7' },
  { id: 'clip-4', type: 'video', name: 'B-Roll 1', startTime: 8, duration: 4, trackIndex: 1, color: '#22c55e' },
  { id: 'clip-5', type: 'video', name: 'B-Roll 2', startTime: 15, duration: 3, trackIndex: 1, color: '#16a34a' },
  { id: 'clip-6', type: 'audio', name: 'Background Music', startTime: 0, duration: 25, trackIndex: 2, color: '#f59e0b' },
  { id: 'clip-7', type: 'audio', name: 'Voiceover', startTime: 2, duration: 18, trackIndex: 3, color: '#ef4444' },
  { id: 'clip-8', type: 'text', name: 'Title Card', startTime: 0, duration: 3, trackIndex: 4, color: '#0ea5e9' },
  { id: 'clip-9', type: 'text', name: 'Lower Third', startTime: 10, duration: 5, trackIndex: 4, color: '#06b6d4' },
  { id: 'clip-10', type: 'text', name: 'CTA', startTime: 22, duration: 3, trackIndex: 4, color: '#0284c7' },
];

export const Timeline: React.FC<TimelineProps> = ({
  tracks: initialTracks,
  currentTime,
  duration,
  zoom,
  selectedClip,
  onTrackUpdate,
  onClipSelect,
  onSeek,
  onZoomChange,
}) => {
  const timelineRef = useRef<HTMLDivElement>(null);
  const pixelsPerSecond = 40 * zoom;
  const totalWidth = duration * pixelsPerSecond;

  // Use mock tracks with demo clips
  const tracks: TimelineTrack[] = [
    {
      id: 'video-1',
      name: 'Video Track 1',
      type: 'video',
      clips: MOCK_CLIPS.filter(c => c.trackIndex === 0),
      visible: true,
      locked: false,
    },
    {
      id: 'video-2',
      name: 'Video Track 2',
      type: 'video',
      clips: MOCK_CLIPS.filter(c => c.trackIndex === 1),
      visible: true,
      locked: false,
    },
    {
      id: 'audio-1',
      name: 'Music',
      type: 'audio',
      clips: MOCK_CLIPS.filter(c => c.trackIndex === 2),
      muted: false,
      locked: false,
    },
    {
      id: 'audio-2',
      name: 'Voiceover',
      type: 'audio',
      clips: MOCK_CLIPS.filter(c => c.trackIndex === 3),
      muted: false,
      locked: false,
    },
    {
      id: 'text-1',
      name: 'Text / Captions',
      type: 'text',
      clips: MOCK_CLIPS.filter(c => c.trackIndex === 4),
      visible: true,
      locked: false,
    },
  ];

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleTimelineClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!timelineRef.current || !onSeek) return;
    const rect = timelineRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left + timelineRef.current.scrollLeft;
    const newTime = Math.max(0, Math.min(duration, x / pixelsPerSecond));
    onSeek(newTime);
  };

  const handleClipClick = (clipId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onClipSelect?.(clipId);
  };

  const getTrackIcon = (type: string) => {
    switch (type) {
      case 'audio':
        return <MusicalNoteIcon className="w-4 h-4 text-orange-400" />;
      case 'video':
        return <FilmIcon className="w-4 h-4 text-indigo-400" />;
      case 'text':
        return <span className="text-cyan-400 font-bold text-sm">T</span>;
      default:
        return <FilmIcon className="w-4 h-4 text-zinc-400" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-zinc-900">
      {/* Timeline Header */}
      <div className="h-10 bg-zinc-800 border-b border-zinc-700 flex items-center justify-between px-4">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-zinc-300">Timeline</span>
          <span className="text-xs text-zinc-500 font-mono">{formatTime(currentTime)}</span>
        </div>
        <div className="flex items-center gap-3">
          {/* Zoom Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onZoomChange?.(Math.max(0.5, zoom - 0.25))}
              className="w-6 h-6 rounded bg-zinc-700 hover:bg-zinc-600 flex items-center justify-center text-zinc-300 transition-colors"
            >
              -
            </button>
            <span className="text-xs text-zinc-400 w-12 text-center">{Math.round(zoom * 100)}%</span>
            <button
              onClick={() => onZoomChange?.(Math.min(3, zoom + 0.25))}
              className="w-6 h-6 rounded bg-zinc-700 hover:bg-zinc-600 flex items-center justify-center text-zinc-300 transition-colors"
            >
              +
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Track Headers */}
        <div className="w-44 flex-shrink-0 bg-zinc-800 border-r border-zinc-700 overflow-y-auto">
          {/* Time ruler header space */}
          <div className="h-8 bg-zinc-900/50 border-b border-zinc-700 flex items-center px-3">
            <span className="text-xs text-zinc-500 font-medium">Tracks</span>
          </div>

          {/* Track Headers */}
          {tracks.map((track) => (
            <div
              key={track.id}
              className="h-16 border-b border-zinc-700 flex items-center px-3 gap-2 hover:bg-zinc-700/30 transition-colors"
            >
              {getTrackIcon(track.type)}
              <span className="text-sm text-zinc-300 truncate flex-1">{track.name}</span>
              <div className="flex gap-1">
                {track.type === 'audio' && (
                  <button className="w-6 h-6 rounded hover:bg-zinc-600 flex items-center justify-center transition-colors">
                    {track.muted ? (
                      <SpeakerXMarkIcon className="w-4 h-4 text-zinc-500" />
                    ) : (
                      <SpeakerWaveIcon className="w-4 h-4 text-zinc-400" />
                    )}
                  </button>
                )}
                {(track.type === 'video' || track.type === 'text') && (
                  <button className="w-6 h-6 rounded hover:bg-zinc-600 flex items-center justify-center transition-colors">
                    {track.visible ? (
                      <EyeIcon className="w-4 h-4 text-zinc-400" />
                    ) : (
                      <EyeSlashIcon className="w-4 h-4 text-zinc-500" />
                    )}
                  </button>
                )}
                <button className="w-6 h-6 rounded hover:bg-zinc-600 flex items-center justify-center transition-colors">
                  {track.locked ? (
                    <LockClosedIcon className="w-4 h-4 text-zinc-500" />
                  ) : (
                    <LockOpenIcon className="w-4 h-4 text-zinc-400" />
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Timeline Content */}
        <div className="flex-1 overflow-auto" ref={timelineRef}>
          <div style={{ width: Math.max(totalWidth, 1000) }}>
            {/* Time Ruler */}
            <div
              className="h-8 bg-zinc-900/50 border-b border-zinc-700 relative cursor-pointer select-none"
              onClick={handleTimelineClick}
            >
              {/* Time markers */}
              {Array.from({ length: Math.ceil(duration / 5) + 1 }).map((_, i) => {
                const time = i * 5;
                return (
                  <div
                    key={i}
                    className="absolute top-0 h-full border-l border-zinc-700"
                    style={{ left: time * pixelsPerSecond }}
                  >
                    <span className="absolute top-1 left-1 text-xs text-zinc-500 font-mono">
                      {formatTime(time)}
                    </span>
                  </div>
                );
              })}

              {/* Playhead */}
              <div
                className="absolute top-0 w-0.5 h-full bg-red-500 z-20 pointer-events-none"
                style={{ left: currentTime * pixelsPerSecond }}
              >
                <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 bg-red-500 rounded-sm rotate-45" />
              </div>
            </div>

            {/* Tracks */}
            {tracks.map((track) => (
              <div key={track.id} className="h-16 border-b border-zinc-700 relative bg-zinc-950/50">
                {/* Grid lines */}
                {Array.from({ length: Math.ceil(duration / 5) + 1 }).map((_, i) => (
                  <div
                    key={i}
                    className="absolute top-0 h-full border-l border-zinc-800/50"
                    style={{ left: i * 5 * pixelsPerSecond }}
                  />
                ))}

                {/* Clips */}
                {track.clips.map((clip) => (
                  <div
                    key={clip.id}
                    onClick={(e) => handleClipClick(clip.id, e)}
                    className={`absolute top-2 h-12 rounded-md cursor-pointer transition-all shadow-lg overflow-hidden
                      ${selectedClip === clip.id ? 'ring-2 ring-white ring-offset-2 ring-offset-zinc-900' : 'hover:brightness-110'}`}
                    style={{
                      left: clip.startTime * pixelsPerSecond,
                      width: clip.duration * pixelsPerSecond,
                      backgroundColor: clip.color,
                    }}
                  >
                    {/* Clip thumbnail/pattern */}
                    <div className="absolute inset-0 opacity-10">
                      <div
                        className="w-full h-full"
                        style={{
                          backgroundImage: clip.type === 'audio'
                            ? 'repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 4px)'
                            : 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,255,255,0.05) 10px, rgba(255,255,255,0.05) 20px)',
                        }}
                      />
                    </div>

                    {/* Clip content */}
                    <div className="relative h-full px-2 py-1 flex flex-col justify-center">
                      <div className="text-xs font-medium text-white truncate drop-shadow-md">
                        {clip.name}
                      </div>
                      <div className="text-xs text-white/70 truncate mt-0.5">
                        {formatTime(clip.duration)}
                      </div>
                    </div>

                    {/* Resize handles */}
                    <div className="absolute left-0 top-0 bottom-0 w-1 bg-white/20 cursor-ew-resize hover:bg-white/40" />
                    <div className="absolute right-0 top-0 bottom-0 w-1 bg-white/20 cursor-ew-resize hover:bg-white/40" />
                  </div>
                ))}

                {/* Playhead line */}
                <div
                  className="absolute top-0 w-0.5 h-full bg-red-500/30 pointer-events-none z-10"
                  style={{ left: currentTime * pixelsPerSecond }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Icon placeholders for missing icons
const SpeakerWaveIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
  </svg>
);

const SpeakerXMarkIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
  </svg>
);

export default Timeline;
