import React, { useState, useRef, useCallback, useEffect } from 'react';
import {
  FilmIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { PreviewPlayer, Timeline, ScriptEditor, ExportPanel, TimelineTrack } from './studio';

interface ProVideoEditorProps {
  projectId?: string;
  onSave?: (project: any) => void;
  onExport?: (settings: any) => void;
}

export const ProVideoEditor: React.FC<ProVideoEditorProps> = ({ projectId, onSave, onExport }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration] = useState(25);
  const [zoom, setZoom] = useState(1);
  const [selectedClip, setSelectedClip] = useState<string | null>(null);
  const [tracks, setTracks] = useState<TimelineTrack[]>([]);
  const [activeTab, setActiveTab] = useState<'script' | 'export' | 'settings'>('script');

  const playbackInterval = useRef<NodeJS.Timeout | null>(null);

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

  const handleSeek = (time: number) => {
    setCurrentTime(time);
  };

  const handleSave = () => {
    onSave?.({ tracks, currentTime, duration });
  };

  const handleExport = (settings: any) => {
    onExport?.(settings);
  };

  return (
    <div className="h-screen bg-zinc-950 text-white flex flex-col overflow-hidden">
      {/* Top Toolbar */}
      <div className="h-14 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between px-6 shadow-lg flex-shrink-0">
        <div className="flex items-center gap-4">
          <FilmIcon className="w-6 h-6 text-indigo-400" />
          <span className="font-semibold text-lg">Pro Video Studio</span>
          <span className="text-zinc-600">|</span>
          <span className="text-zinc-400 text-sm">{projectId || 'Untitled Project'}</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            className="px-4 py-2 text-sm bg-zinc-800 hover:bg-zinc-700 rounded-lg transition-colors font-medium"
          >
            Save Project
          </button>
          <button
            onClick={() => setActiveTab('export')}
            className="px-4 py-2 text-sm bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 rounded-lg transition-all font-medium shadow-lg"
          >
            Export Video
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left - Preview Player */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 min-h-0">
            <PreviewPlayer
              currentTime={currentTime}
              duration={duration}
              isPlaying={isPlaying}
              onPlayPause={togglePlayback}
              onSeek={handleSeek}
            />
          </div>
        </div>

        {/* Right Panel - Tabs */}
        <div className="w-96 bg-zinc-900 border-l border-zinc-800 flex flex-col flex-shrink-0">
          {/* Tab Headers */}
          <div className="h-12 bg-zinc-800 border-b border-zinc-700 flex items-center px-2 gap-1 flex-shrink-0">
            <button
              onClick={() => setActiveTab('script')}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                activeTab === 'script'
                  ? 'bg-zinc-700 text-white shadow-md'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/50'
              }`}
            >
              <DocumentTextIcon className="w-4 h-4" />
              Script
            </button>
            <button
              onClick={() => setActiveTab('export')}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                activeTab === 'export'
                  ? 'bg-zinc-700 text-white shadow-md'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/50'
              }`}
            >
              <FilmIcon className="w-4 h-4" />
              Export
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center justify-center gap-2 ${
                activeTab === 'settings'
                  ? 'bg-zinc-700 text-white shadow-md'
                  : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/50'
              }`}
            >
              <Cog6ToothIcon className="w-4 h-4" />
              Settings
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-hidden">
            {activeTab === 'script' && <ScriptEditor />}
            {activeTab === 'export' && <ExportPanel duration={duration} onExport={handleExport} />}
            {activeTab === 'settings' && (
              <div className="h-full bg-zinc-900 p-6">
                <h3 className="text-lg font-semibold mb-4">Project Settings</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Project Name</label>
                    <input
                      type="text"
                      value={projectId || 'Untitled Project'}
                      className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Frame Rate</label>
                    <select className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm">
                      <option value="24">24 fps</option>
                      <option value="30">30 fps</option>
                      <option value="60">60 fps</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-2">Resolution</label>
                    <select className="w-full px-3 py-2 bg-zinc-800 border border-zinc-700 rounded-lg text-sm">
                      <option value="1080p">1920x1080 (1080p)</option>
                      <option value="4k">3840x2160 (4K)</option>
                      <option value="720p">1280x720 (720p)</option>
                    </select>
                  </div>
                  <div className="pt-4 border-t border-zinc-700">
                    <label className="flex items-center gap-3 cursor-pointer group">
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded border-zinc-600 bg-zinc-800 text-indigo-600"
                        defaultChecked
                      />
                      <span className="text-sm text-zinc-400 group-hover:text-zinc-300">
                        Auto-save enabled
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Timeline */}
      <div className="h-72 border-t border-zinc-800 flex-shrink-0">
        <Timeline
          tracks={tracks}
          currentTime={currentTime}
          duration={duration}
          zoom={zoom}
          selectedClip={selectedClip}
          onClipSelect={setSelectedClip}
          onSeek={handleSeek}
          onZoomChange={setZoom}
        />
      </div>
    </div>
  );
};

export default ProVideoEditor;
