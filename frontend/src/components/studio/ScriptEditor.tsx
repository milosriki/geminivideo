import React, { useState, useRef, useEffect } from 'react';
import { SparklesIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

interface ScriptEditorProps {
  initialScript?: string;
  onScriptChange?: (script: string) => void;
  onAISuggestion?: () => void;
}

interface SceneMarker {
  id: string;
  timestamp: number;
  text: string;
}

const PLACEHOLDER_SCRIPT = `# Video Script

[00:00 - SCENE 1: INTRO]
Welcome to our latest video! Today we're going to explore some amazing features...

[00:15 - SCENE 2: MAIN CONTENT]
Let's dive right into the details. First, we'll cover the basics...

[00:45 - SCENE 3: DEMONSTRATION]
Now, let me show you how this works in practice...

[01:30 - SCENE 4: CONCLUSION]
That wraps up our tutorial. Don't forget to like and subscribe!

[01:45 - SCENE 5: OUTRO]
Thanks for watching! See you in the next video.`;

export const ScriptEditor: React.FC<ScriptEditorProps> = ({
  initialScript = PLACEHOLDER_SCRIPT,
  onScriptChange,
  onAISuggestion,
}) => {
  const [script, setScript] = useState(initialScript);
  const [charCount, setCharCount] = useState(0);
  const [wordCount, setWordCount] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    updateCounts(script);
  }, [script]);

  const updateCounts = (text: string) => {
    setCharCount(text.length);
    const words = text.trim().split(/\s+/).filter(word => word.length > 0);
    setWordCount(words.length);
  };

  const handleScriptChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newScript = e.target.value;
    setScript(newScript);
    onScriptChange?.(newScript);
  };

  const handleAISuggestion = async () => {
    setIsGenerating(true);
    try {
      // Simulate AI generation
      await new Promise(resolve => setTimeout(resolve, 1500));
      onAISuggestion?.();
    } finally {
      setIsGenerating(false);
    }
  };

  const extractSceneMarkers = (): SceneMarker[] => {
    const markers: SceneMarker[] = [];
    const lines = script.split('\n');

    lines.forEach(line => {
      const match = line.match(/\[(\d{2}):(\d{2})\s*-\s*SCENE\s*\d+:\s*(.+?)\]/i);
      if (match) {
        const [, mins, secs, text] = match;
        const timestamp = parseInt(mins) * 60 + parseInt(secs);
        markers.push({
          id: `marker-${timestamp}`,
          timestamp,
          text: text.trim(),
        });
      }
    });

    return markers;
  };

  const formatTimestamp = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const sceneMarkers = extractSceneMarkers();

  return (
    <div className="h-full flex flex-col bg-zinc-900">
      {/* Header */}
      <div className="h-12 bg-zinc-800 border-b border-zinc-700 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <DocumentTextIcon className="w-5 h-5 text-zinc-400" />
          <span className="text-sm font-medium text-zinc-300">Script Editor</span>
        </div>
        <button
          onClick={handleAISuggestion}
          disabled={isGenerating}
          className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500
            disabled:from-zinc-700 disabled:to-zinc-700 disabled:text-zinc-500 rounded-lg text-sm font-medium
            transition-all flex items-center gap-2 shadow-lg"
        >
          <SparklesIcon className={`w-4 h-4 ${isGenerating ? 'animate-spin' : ''}`} />
          {isGenerating ? 'Generating...' : 'AI Suggest'}
        </button>
      </div>

      {/* Editor Area */}
      <div className="flex-1 overflow-hidden flex">
        {/* Main text editor */}
        <div className="flex-1 flex flex-col">
          <textarea
            ref={textareaRef}
            value={script}
            onChange={handleScriptChange}
            placeholder="Write your video script here... Use [00:00 - SCENE 1: TITLE] format for scene markers."
            className="flex-1 bg-zinc-900 text-zinc-100 p-4 resize-none focus:outline-none font-mono text-sm leading-relaxed"
            spellCheck
          />

          {/* Stats Bar */}
          <div className="h-10 bg-zinc-800 border-t border-zinc-700 flex items-center justify-between px-4">
            <div className="flex items-center gap-4 text-xs text-zinc-400">
              <span>{wordCount} words</span>
              <span className="text-zinc-600">|</span>
              <span>{charCount} characters</span>
              <span className="text-zinc-600">|</span>
              <span>{sceneMarkers.length} scenes</span>
            </div>
            <div className="text-xs text-zinc-500">
              Est. reading time: ~{Math.ceil(wordCount / 150)} min
            </div>
          </div>
        </div>

        {/* Scene Markers Panel */}
        <div className="w-56 bg-zinc-800 border-l border-zinc-700 flex flex-col">
          <div className="h-10 bg-zinc-900/50 border-b border-zinc-700 flex items-center px-3">
            <span className="text-xs font-medium text-zinc-400">Scene Markers</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-2">
            {sceneMarkers.length > 0 ? (
              sceneMarkers.map((marker) => (
                <div
                  key={marker.id}
                  className="p-2.5 bg-zinc-900 rounded-lg border border-zinc-700 hover:border-indigo-500/50
                    cursor-pointer transition-colors group"
                >
                  <div className="text-xs font-mono text-indigo-400 mb-1">
                    {formatTimestamp(marker.timestamp)}
                  </div>
                  <div className="text-xs text-zinc-300 line-clamp-2 group-hover:text-white transition-colors">
                    {marker.text}
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-xs text-zinc-500 mt-8 px-2">
                Add scene markers using the format:
                <div className="mt-2 font-mono text-zinc-600 text-[10px] leading-relaxed">
                  [MM:SS - SCENE N: TITLE]
                </div>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="p-2 border-t border-zinc-700 space-y-1">
            <button className="w-full px-3 py-2 text-xs text-left text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700
              rounded transition-colors">
              Insert Scene Marker
            </button>
            <button className="w-full px-3 py-2 text-xs text-left text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700
              rounded transition-colors">
              Auto-Generate Scenes
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScriptEditor;
