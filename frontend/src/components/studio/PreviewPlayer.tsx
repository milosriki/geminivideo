import React, { useState, useRef, useEffect } from 'react';
import {
  PlayIcon,
  PauseIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ArrowsPointingOutIcon,
} from '@heroicons/react/24/outline';

interface PreviewPlayerProps {
  currentTime: number;
  duration: number;
  isPlaying: boolean;
  onPlayPause: () => void;
  onSeek: (time: number) => void;
  onVolumeChange?: (volume: number) => void;
  onSpeedChange?: (speed: number) => void;
}

const PLAYBACK_SPEEDS = [0.5, 1, 1.5, 2];

export const PreviewPlayer: React.FC<PreviewPlayerProps> = ({
  currentTime,
  duration,
  isPlaying,
  onPlayPause,
  onSeek,
  onVolumeChange,
  onSpeedChange,
}) => {
  const [showControls, setShowControls] = useState(true);
  const [volume, setVolume] = useState(100);
  const [isMuted, setIsMuted] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
  const [showSpeedMenu, setShowSpeedMenu] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const progressBarRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!progressBarRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const percent = (e.clientX - rect.left) / rect.width;
    const newTime = Math.max(0, Math.min(duration, percent * duration));
    onSeek(newTime);
  };

  const handleProgressDrag = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDragging || !progressBarRef.current) return;
    const rect = progressBarRef.current.getBoundingClientRect();
    const percent = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const newTime = percent * duration;
    onSeek(newTime);
  };

  const handleVolumeChange = (newVolume: number) => {
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
    onVolumeChange?.(newVolume);
  };

  const toggleMute = () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    onVolumeChange?.(newMuted ? 0 : volume);
  };

  const handleSpeedChange = (speed: number) => {
    setPlaybackSpeed(speed);
    onSpeedChange?.(speed);
    setShowSpeedMenu(false);
  };

  const handleFullscreen = () => {
    if (containerRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        containerRef.current.requestFullscreen();
      }
    }
  };

  const handleMouseMove = () => {
    setShowControls(true);
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
    }
    if (isPlaying) {
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false);
      }, 2000);
    }
  };

  const handleMouseLeave = () => {
    if (isPlaying && controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current);
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false);
      }, 1000);
    }
  };

  useEffect(() => {
    return () => {
      if (controlsTimeoutRef.current) {
        clearTimeout(controlsTimeoutRef.current);
      }
    };
  }, []);

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-black flex items-center justify-center group"
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {/* Video Preview Area */}
      <div className="relative w-full max-w-5xl aspect-video bg-zinc-900 rounded-lg overflow-hidden shadow-2xl">
        {/* Placeholder video content */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-zinc-800 flex items-center justify-center">
              <PlayIcon className="w-12 h-12 text-zinc-600" />
            </div>
            <p className="text-zinc-500 text-lg font-medium">Video Preview</p>
            <p className="text-zinc-600 text-sm mt-2">
              {formatTime(currentTime)} / {formatTime(duration)}
            </p>
          </div>
        </div>

        {/* Center Play/Pause Overlay */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <button
            onClick={onPlayPause}
            className={`pointer-events-auto w-20 h-20 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center
              transition-all duration-300 hover:bg-white/20 hover:scale-110 ${
                showControls ? 'opacity-100' : 'opacity-0'
              }`}
          >
            {isPlaying ? (
              <PauseIcon className="w-10 h-10 text-white" />
            ) : (
              <PlayIcon className="w-10 h-10 text-white ml-1" />
            )}
          </button>
        </div>

        {/* Bottom Controls Bar */}
        <div
          className={`absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/90 via-black/70 to-transparent
            transition-all duration-300 ${showControls ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}
        >
          {/* Progress Bar */}
          <div
            ref={progressBarRef}
            className="px-4 pt-6 pb-2 cursor-pointer group/progress"
            onClick={handleProgressClick}
            onMouseDown={() => setIsDragging(true)}
            onMouseUp={() => setIsDragging(false)}
            onMouseMove={handleProgressDrag}
          >
            <div className="relative w-full h-1.5 bg-zinc-700 rounded-full overflow-hidden">
              {/* Buffered/loaded indicator */}
              <div className="absolute inset-0 bg-zinc-600 rounded-full" style={{ width: '60%' }} />
              {/* Progress */}
              <div
                className="absolute inset-0 bg-indigo-500 rounded-full transition-all"
                style={{ width: `${progress}%` }}
              />
              {/* Hover indicator */}
              <div
                className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-lg
                  opacity-0 group-hover/progress:opacity-100 transition-opacity"
                style={{ left: `calc(${progress}% - 6px)` }}
              />
            </div>
          </div>

          {/* Control Buttons */}
          <div className="px-4 pb-3 flex items-center justify-between gap-4">
            {/* Left Controls */}
            <div className="flex items-center gap-3">
              {/* Play/Pause */}
              <button
                onClick={onPlayPause}
                className="w-9 h-9 rounded-full bg-zinc-800 hover:bg-zinc-700 flex items-center justify-center transition-colors"
              >
                {isPlaying ? (
                  <PauseIcon className="w-5 h-5 text-white" />
                ) : (
                  <PlayIcon className="w-5 h-5 text-white ml-0.5" />
                )}
              </button>

              {/* Time Display */}
              <div className="text-sm font-mono text-zinc-300">
                {formatTime(currentTime)} / {formatTime(duration)}
              </div>

              {/* Volume Control */}
              <div className="flex items-center gap-2 group/volume">
                <button
                  onClick={toggleMute}
                  className="w-8 h-8 rounded hover:bg-zinc-800 flex items-center justify-center transition-colors"
                >
                  {isMuted || volume === 0 ? (
                    <SpeakerXMarkIcon className="w-5 h-5 text-zinc-400" />
                  ) : (
                    <SpeakerWaveIcon className="w-5 h-5 text-zinc-400" />
                  )}
                </button>
                <div className="w-0 group-hover/volume:w-20 overflow-hidden transition-all duration-200">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={isMuted ? 0 : volume}
                    onChange={(e) => handleVolumeChange(Number(e.target.value))}
                    className="w-20 accent-indigo-500"
                  />
                </div>
              </div>
            </div>

            {/* Right Controls */}
            <div className="flex items-center gap-2">
              {/* Speed Selector */}
              <div className="relative">
                <button
                  onClick={() => setShowSpeedMenu(!showSpeedMenu)}
                  className="px-3 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-sm font-medium text-zinc-300
                    transition-colors min-w-[60px]"
                >
                  {playbackSpeed}x
                </button>
                {showSpeedMenu && (
                  <div className="absolute bottom-full right-0 mb-2 bg-zinc-800 rounded-lg shadow-xl border border-zinc-700 overflow-hidden">
                    {PLAYBACK_SPEEDS.map((speed) => (
                      <button
                        key={speed}
                        onClick={() => handleSpeedChange(speed)}
                        className={`w-full px-4 py-2 text-sm text-left hover:bg-zinc-700 transition-colors ${
                          speed === playbackSpeed ? 'bg-indigo-600 text-white' : 'text-zinc-300'
                        }`}
                      >
                        {speed}x
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Fullscreen */}
              <button
                onClick={handleFullscreen}
                className="w-8 h-8 rounded hover:bg-zinc-800 flex items-center justify-center transition-colors"
              >
                <ArrowsPointingOutIcon className="w-5 h-5 text-zinc-400" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreviewPlayer;
