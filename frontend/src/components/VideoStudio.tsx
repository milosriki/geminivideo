import React, { useState, useRef, useEffect } from 'react';
import { AdvancedEdit, AdCreative, EditScene } from '../types';
import { processVideoWithAdvancedEdits, processVideoWithCreative } from '../services/videoProcessor';
import {
  DownloadIcon,
  SlidersIcon,
  WandIcon,
  FilmIcon,
  SparklesIcon,
  SendIcon,
  GridIcon,
  PlayIcon
} from './icons';
import { formatErrorMessage } from '../utils/error';
import VideoPlayer from './VideoPlayer';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface EditSuggestion {
  id: string;
  type: 'operation' | 'blueprint';
  description: string;
  confidence: number;
  edit?: AdvancedEdit;
  blueprint?: AdCreative;
}

interface VideoStudioProps {
  sourceVideos?: File[];
  sourceVideo?: File;
  adCreative?: AdCreative;
  mode?: 'manual' | 'ai-blueprint' | 'hybrid';
  onClose: () => void;
}

type StudioMode = 'manual' | 'ai-blueprint' | 'hybrid';

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const VideoStudio: React.FC<VideoStudioProps> = ({
  sourceVideos: initialSourceVideos,
  sourceVideo,
  adCreative: initialAdCreative,
  mode: initialMode = 'manual',
  onClose
}) => {
  // ---------------------------------------------------------------------------
  // STATE MANAGEMENT
  // ---------------------------------------------------------------------------

  // Core state
  const [mode, setMode] = useState<StudioMode>(initialMode);
  const [sourceVideos, setSourceVideos] = useState<File[]>(
    initialSourceVideos || (sourceVideo ? [sourceVideo] : [])
  );
  const [edits, setEdits] = useState<AdvancedEdit[]>([]);
  const [aiBlueprint, setAiBlueprint] = useState<AdCreative | null>(initialAdCreative || null);
  const [aiSuggestions, setAiSuggestions] = useState<EditSuggestion[]>([]);

  // Processing state
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [outputUrl, setOutputUrl] = useState<string | null>(null);

  // UI state
  const [aiPrompt, setAiPrompt] = useState('');
  const [showLogs, setShowLogs] = useState(false);
  const [selectedEditId, setSelectedEditId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'edits' | 'blueprint' | 'suggestions'>('edits');

  // Refs
  const sourceVideoUrls = useRef<string[]>([]);

  // ---------------------------------------------------------------------------
  // EFFECTS
  // ---------------------------------------------------------------------------

  useEffect(() => {
    // Create object URLs for source videos
    sourceVideoUrls.current = sourceVideos.map(v => URL.createObjectURL(v));

    return () => {
      if (outputUrl) URL.revokeObjectURL(outputUrl);
      sourceVideoUrls.current.forEach(url => URL.revokeObjectURL(url));
    };
  }, [sourceVideos, outputUrl]);

  // ---------------------------------------------------------------------------
  // EDIT MANAGEMENT
  // ---------------------------------------------------------------------------

  const addEdit = (type: AdvancedEdit['type']) => {
    setEdits((prev): AdvancedEdit[] => {
      const id = Date.now().toString();
      switch (type) {
        case 'trim': {
          const newTrimEdit: AdvancedEdit = { id, type: 'trim', start: '0.00', end: '5.00' };
          return [newTrimEdit, ...prev.filter((e) => e.type !== 'trim')];
        }
        case 'text': {
          const newTextEdit: AdvancedEdit = {
            id, type: 'text', text: 'Hello World', start: '0.00', end: '3.00',
            position: 'center', fontSize: 48
          };
          return [...prev, newTextEdit];
        }
        case 'image': {
          const placeholderFile = new File([], 'placeholder.png', { type: 'image/png' });
          const newImageEdit: AdvancedEdit = {
            id, type: 'image', file: placeholderFile, position: 'top_right',
            scale: 0.2, opacity: 1.0
          };
          return [...prev, newImageEdit];
        }
        case 'speed': {
          const newSpeedEdit: AdvancedEdit = { id, type: 'speed', factor: 2.0 };
          return [...prev, newSpeedEdit];
        }
        case 'filter': {
          const newFilterEdit: AdvancedEdit = { id, type: 'filter', name: 'grayscale' };
          return [...prev, newFilterEdit];
        }
        case 'color': {
          const newColorEdit: AdvancedEdit = {
            id, type: 'color', brightness: 0, contrast: 1, saturation: 1
          };
          return [...prev, newColorEdit];
        }
        case 'volume': {
          const newVolumeEdit: AdvancedEdit = { id, type: 'volume', level: 1.0 };
          return [...prev, newVolumeEdit];
        }
        case 'fade': {
          const newFadeEdit: AdvancedEdit = {
            id, type: 'fade', typeIn: true, typeOut: true, duration: 1.0
          };
          return [...prev, newFadeEdit];
        }
        case 'crop': {
          const newCropEdit: AdvancedEdit = { id, type: 'crop', ratio: '9:16' };
          return [...prev, newCropEdit];
        }
        case 'subtitles': {
          const newSubtitlesEdit: AdvancedEdit = {
            id, type: 'subtitles', text: 'Sample Subtitle Text'
          };
          return [...prev, newSubtitlesEdit];
        }
        case 'mute': {
          const newMuteEdit: AdvancedEdit = { id, type: 'mute' };
          return [...prev, newMuteEdit];
        }
        default:
          return prev;
      }
    });
  };

  const updateEdit = (id: string, newValues: Partial<AdvancedEdit>) => {
    setEdits(prev => prev.map(e => e.id === id ? { ...e, ...newValues } : e) as any);
  };

  const removeEdit = (id: string) => {
    setEdits(prev => prev.filter(e => e.id !== id));
  };

  // ---------------------------------------------------------------------------
  // AI COMMAND PROCESSING
  // ---------------------------------------------------------------------------

  const handleAICommand = () => {
    const prompt = aiPrompt.toLowerCase();
    const suggestions: EditSuggestion[] = [];

    // Pattern matching for common commands
    if (prompt.includes('faster') || prompt.includes('speed up')) {
      const suggestion: EditSuggestion = {
        id: Date.now().toString(),
        type: 'operation',
        description: 'Speed up video by 2x',
        confidence: 0.9,
        edit: { id: Date.now().toString(), type: 'speed', factor: 2.0 }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('slow') || prompt.includes('slo-mo') || prompt.includes('slow motion')) {
      const suggestion: EditSuggestion = {
        id: Date.now().toString(),
        type: 'operation',
        description: 'Apply slow motion effect (0.5x speed)',
        confidence: 0.85,
        edit: { id: Date.now().toString(), type: 'speed', factor: 0.5 }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('mute') || prompt.includes('silent') || prompt.includes('no audio')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 1).toString(),
        type: 'operation',
        description: 'Mute audio completely',
        confidence: 0.95,
        edit: { id: (Date.now() + 1).toString(), type: 'mute' }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('black and white') || prompt.includes('grayscale') || prompt.includes('b&w')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 2).toString(),
        type: 'operation',
        description: 'Apply black and white filter',
        confidence: 0.9,
        edit: { id: (Date.now() + 2).toString(), type: 'filter', name: 'grayscale' }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('vertical') || prompt.includes('reel') || prompt.includes('tiktok') || prompt.includes('9:16')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 3).toString(),
        type: 'operation',
        description: 'Crop to vertical 9:16 format (Reels/TikTok)',
        confidence: 0.92,
        edit: { id: (Date.now() + 3).toString(), type: 'crop', ratio: '9:16' }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('square') || prompt.includes('1:1') || prompt.includes('instagram feed')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 4).toString(),
        type: 'operation',
        description: 'Crop to square 1:1 format (Instagram feed)',
        confidence: 0.88,
        edit: { id: (Date.now() + 4).toString(), type: 'crop', ratio: '1:1' }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('caption') || prompt.includes('subtitle') || prompt.includes('text')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 5).toString(),
        type: 'operation',
        description: 'Add subtitles/captions',
        confidence: 0.8,
        edit: { id: (Date.now() + 5).toString(), type: 'subtitles', text: 'Enter your caption text' }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('fade') || prompt.includes('transition')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 6).toString(),
        type: 'operation',
        description: 'Add fade in/out transitions',
        confidence: 0.85,
        edit: { id: (Date.now() + 6).toString(), type: 'fade', typeIn: true, typeOut: true, duration: 1.0 }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('bright') || prompt.includes('lighter')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 7).toString(),
        type: 'operation',
        description: 'Increase brightness',
        confidence: 0.82,
        edit: { id: (Date.now() + 7).toString(), type: 'color', brightness: 0.3, contrast: 1, saturation: 1 }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('dark') || prompt.includes('dimmer')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 8).toString(),
        type: 'operation',
        description: 'Decrease brightness',
        confidence: 0.82,
        edit: { id: (Date.now() + 8).toString(), type: 'color', brightness: -0.3, contrast: 1, saturation: 1 }
      };
      suggestions.push(suggestion);
    }

    if (prompt.includes('vibrant') || prompt.includes('saturate') || prompt.includes('colorful')) {
      const suggestion: EditSuggestion = {
        id: (Date.now() + 9).toString(),
        type: 'operation',
        description: 'Increase color saturation',
        confidence: 0.78,
        edit: { id: (Date.now() + 9).toString(), type: 'color', brightness: 0, contrast: 1, saturation: 1.5 }
      };
      suggestions.push(suggestion);
    }

    if (mode === 'manual' && suggestions.length > 0) {
      // In manual mode, apply the first suggestion directly
      if (suggestions[0].edit) {
        setEdits(prev => [...prev, suggestions[0].edit!]);
      }
    } else if (mode === 'hybrid') {
      // In hybrid mode, add to suggestions for user approval
      setAiSuggestions(prev => [...suggestions, ...prev].slice(0, 10));
      setActiveTab('suggestions');
    }

    if (suggestions.length === 0) {
      alert("I didn't understand that command. Try: 'make it vertical', 'add captions', 'speed up', 'black and white', etc.");
    }

    setAiPrompt('');
  };

  const applySuggestion = (suggestion: EditSuggestion) => {
    if (suggestion.edit) {
      setEdits(prev => [...prev, suggestion.edit!]);
    }
    setAiSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
  };

  const dismissSuggestion = (suggestionId: string) => {
    setAiSuggestions(prev => prev.filter(s => s.id !== suggestionId));
  };

  // ---------------------------------------------------------------------------
  // VIDEO PROCESSING
  // ---------------------------------------------------------------------------

  const handleRenderVideo = async () => {
    setError(null);

    // Validation for manual mode
    if (mode === 'manual' || mode === 'hybrid') {
      const trimEdit = edits.find(e => e.type === 'trim');
      if (trimEdit && trimEdit.type === 'trim') {
        const start = parseFloat(trimEdit.start);
        const end = parseFloat(trimEdit.end);
        if (isNaN(start) || isNaN(end) || start < 0 || end <= 0) {
          setError("Trim 'start' and 'end' times must be valid, positive numbers.");
          return;
        }
        if (start >= end) {
          setError("Trim 'start' time must be less than 'end' time.");
          return;
        }
      }

      const imageEdits = edits.filter(e => e.type === 'image') as Extract<AdvancedEdit, { type: 'image' }>[];
      if (imageEdits.some(edit => edit.file.size === 0)) {
        setError("Please select an image file for all 'Image Overlay' edits before rendering.");
        return;
      }
    }

    setIsProcessing(true);
    setLogs([]);
    setProgress(0);
    setProgressMessage('Initializing...');
    if (outputUrl) URL.revokeObjectURL(outputUrl);
    setOutputUrl(null);

    try {
      let outputBlob: Blob;

      if (mode === 'ai-blueprint' && aiBlueprint) {
        // Use AI blueprint processing
        outputBlob = await processVideoWithCreative(
          sourceVideos,
          aiBlueprint,
          (p) => {
            setProgress(p.progress * 100);
            setProgressMessage(p.message);
          },
          (log) => setLogs(prev => [...prev, log].slice(-100))
        );
      } else {
        // Use manual edits processing (for manual and hybrid modes)
        if (sourceVideos.length === 0) {
          throw new Error('No source video selected');
        }
        outputBlob = await processVideoWithAdvancedEdits(
          sourceVideos[0], // Use first video for now
          edits,
          (p) => {
            setProgress(p.progress * 100);
            setProgressMessage(p.message);
          },
          (log) => setLogs(prev => [...prev, log].slice(-100))
        );
      }

      const url = URL.createObjectURL(outputBlob);
      setOutputUrl(url);
    } catch (err) {
      setError(formatErrorMessage(err));
    } finally {
      setIsProcessing(false);
      setProgressMessage('');
    }
  };

  const handleDownload = () => {
    if (!outputUrl) return;
    const a = document.createElement('a');
    a.href = outputUrl;
    const fileName = mode === 'ai-blueprint' && aiBlueprint
      ? `AI_${aiBlueprint.variationTitle.replace(/\s+/g, '_')}.mp4`
      : `VideoStudio_${sourceVideos[0]?.name || 'output'}.mp4`;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // ---------------------------------------------------------------------------
  // RENDER HELPERS
  // ---------------------------------------------------------------------------

  const renderEditControl = (edit: AdvancedEdit) => {
    switch (edit.type) {
      case 'trim': return (
        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            value={edit.start}
            onChange={e => updateEdit(edit.id, { start: e.target.value })}
            className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full"
            placeholder="Start (s)"
          />
          <input
            type="text"
            value={edit.end}
            onChange={e => updateEdit(edit.id, { end: e.target.value })}
            className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full"
            placeholder="End (s)"
          />
        </div>
      );

      case 'text': return (
        <div className="space-y-2">
          <input
            type="text"
            value={edit.text}
            onChange={e => updateEdit(edit.id, { text: e.target.value })}
            className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full"
            placeholder="Overlay Text"
          />
          <div className="grid grid-cols-2 gap-2">
            <input
              type="text"
              value={edit.start}
              onChange={e => updateEdit(edit.id, { start: e.target.value })}
              className="bg-gray-900 border border-gray-600 rounded p-1 text-sm"
              placeholder="Start (s)"
            />
            <input
              type="text"
              value={edit.end}
              onChange={e => updateEdit(edit.id, { end: e.target.value })}
              className="bg-gray-900 border border-gray-600 rounded p-1 text-sm"
              placeholder="End (s)"
            />
          </div>
          <select
            value={edit.position}
            onChange={e => updateEdit(edit.id, { position: e.target.value as 'top' | 'center' | 'bottom' })}
            className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full"
          >
            <option value="top">Top</option>
            <option value="center">Center</option>
            <option value="bottom">Bottom</option>
          </select>
          <div>
            <label className="text-xs text-gray-400">Font Size: {edit.fontSize}px</label>
            <input
              type="range"
              min="12"
              max="96"
              step="4"
              value={edit.fontSize}
              onChange={e => updateEdit(edit.id, { fontSize: parseInt(e.target.value) })}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
            />
          </div>
        </div>
      );

      case 'image': return (
        <div className="space-y-2">
          <input
            type="file"
            accept="image/*"
            onChange={e => e.target.files && updateEdit(edit.id, { file: e.target.files[0] })}
            className="text-xs file:mr-2 file:py-1 file:px-2 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 w-full"
          />
          <select
            value={edit.position}
            onChange={e => updateEdit(edit.id, { position: e.target.value as 'top_left' | 'top_right' | 'bottom_left' | 'bottom_right' })}
            className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full"
          >
            <option value="top_left">Top Left</option>
            <option value="top_right">Top Right</option>
            <option value="bottom_left">Bottom Left</option>
            <option value="bottom_right">Bottom Right</option>
          </select>
          <label className="text-xs text-gray-400">Scale: {edit.scale.toFixed(2)}</label>
          <input
            type="range"
            min="0.05"
            max="1"
            step="0.05"
            value={edit.scale}
            onChange={e => updateEdit(edit.id, { scale: parseFloat(e.target.value) })}
            className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
          />
          <label className="text-xs text-gray-400">Opacity: {edit.opacity.toFixed(2)}</label>
          <input
            type="range"
            min="0.1"
            max="1"
            step="0.05"
            value={edit.opacity}
            onChange={e => updateEdit(edit.id, { opacity: parseFloat(e.target.value) })}
            className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
          />
        </div>
      );

      case 'speed': return (
        <div className="flex items-center gap-2">
          <input
            type="range"
            min="0.25"
            max="4"
            step="0.25"
            value={edit.factor}
            onChange={e => updateEdit(edit.id, { factor: parseFloat(e.target.value) })}
            className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer"
          />
          <span className="font-mono text-sm whitespace-nowrap">{edit.factor.toFixed(2)}x</span>
        </div>
      );

      case 'filter': return (
        <select
          value={edit.name}
          onChange={e => updateEdit(edit.id, { name: e.target.value as 'grayscale' | 'sepia' | 'negate' | 'vignette' })}
          className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full"
        >
          <option value="grayscale">Grayscale</option>
          <option value="sepia">Sepia</option>
          <option value="negate">Negate</option>
          <option value="vignette">Vignette</option>
        </select>
      );

      case 'color': return (
        <div className="space-y-2">
          <div>
            <label className="text-xs text-gray-400 flex justify-between">
              <span>Brightness</span>
              <span>{edit.brightness.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min="-1"
              max="1"
              step="0.1"
              value={edit.brightness}
              onChange={e => updateEdit(edit.id, { brightness: parseFloat(e.target.value) })}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 flex justify-between">
              <span>Contrast</span>
              <span>{edit.contrast.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min="-2"
              max="2"
              step="0.1"
              value={edit.contrast}
              onChange={e => updateEdit(edit.id, { contrast: parseFloat(e.target.value) })}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 flex justify-between">
              <span>Saturation</span>
              <span>{edit.saturation.toFixed(2)}</span>
            </label>
            <input
              type="range"
              min="0"
              max="3"
              step="0.1"
              value={edit.saturation}
              onChange={e => updateEdit(edit.id, { saturation: parseFloat(e.target.value) })}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
            />
          </div>
        </div>
      );

      case 'volume': return (
        <div className="space-y-2">
          <label className="text-xs text-gray-400 flex justify-between">
            <span>Volume Level</span>
            <span>{(edit.level * 100).toFixed(0)}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="2"
            step="0.1"
            value={edit.level}
            onChange={e => updateEdit(edit.id, { level: parseFloat(e.target.value) })}
            className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
          />
        </div>
      );

      case 'fade': return (
        <div className="space-y-2">
          <div className="flex gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={edit.typeIn}
                onChange={e => updateEdit(edit.id, { typeIn: e.target.checked })}
                className="rounded bg-gray-700 border-gray-600 text-indigo-600"
              />
              Fade In
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-300">
              <input
                type="checkbox"
                checked={edit.typeOut}
                onChange={e => updateEdit(edit.id, { typeOut: e.target.checked })}
                className="rounded bg-gray-700 border-gray-600 text-indigo-600"
              />
              Fade Out
            </label>
          </div>
          <div>
            <label className="text-xs text-gray-400 flex justify-between">
              <span>Duration (s)</span>
              <span>{edit.duration.toFixed(1)}s</span>
            </label>
            <input
              type="range"
              min="0.5"
              max="5"
              step="0.5"
              value={edit.duration}
              onChange={e => updateEdit(edit.id, { duration: parseFloat(e.target.value) })}
              className="w-full h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer range-sm"
            />
          </div>
        </div>
      );

      case 'crop': return (
        <div className="space-y-2">
          <label className="text-xs text-gray-400">Aspect Ratio</label>
          <select
            value={edit.ratio}
            onChange={e => updateEdit(edit.id, { ratio: e.target.value as '16:9' | '9:16' | '1:1' | '4:5' })}
            className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full"
          >
            <option value="16:9">16:9 (Landscape)</option>
            <option value="9:16">9:16 (Vertical/Reels)</option>
            <option value="1:1">1:1 (Square/Feed)</option>
            <option value="4:5">4:5 (Portrait)</option>
          </select>
        </div>
      );

      case 'subtitles': return (
        <div className="space-y-2">
          <label className="text-xs text-gray-400">Subtitle Text</label>
          <textarea
            value={edit.text}
            onChange={e => updateEdit(edit.id, { text: e.target.value })}
            className="bg-gray-900 border border-gray-600 rounded p-1 text-sm w-full h-20"
            placeholder="Enter text to burn as subtitles..."
          />
        </div>
      );

      case 'mute': return (
        <p className="text-xs text-gray-400 italic">Audio will be completely muted</p>
      );

      default:
        return null;
    }
  };

  const renderBlueprintTimeline = () => {
    if (!aiBlueprint || !aiBlueprint.editPlan) return null;

    return (
      <div className="space-y-3 text-xs max-h-96 overflow-y-auto pr-2">
        {aiBlueprint.editPlan.map((scene, sceneIndex) => (
          <div key={sceneIndex} className="bg-gray-800 rounded p-3 border border-gray-700">
            <div className="flex gap-3">
              <div className="font-mono text-indigo-400 whitespace-nowrap pt-px font-bold">
                {scene.timestamp}
              </div>
              <div className="flex-1 space-y-1">
                <p className="text-gray-300">
                  <strong className="text-gray-400">Source:</strong> {scene.sourceFile || aiBlueprint.primarySourceFileName}
                </p>
                <p className="text-gray-300">
                  <strong className="text-gray-400">Visual:</strong> {scene.visual}
                </p>
                <p className="text-gray-300">
                  <strong className="text-gray-400">Edit:</strong> {scene.edit}
                </p>
                {scene.overlayText && scene.overlayText !== 'N/A' && (
                  <p className="text-gray-300">
                    <strong className="text-gray-400">Text:</strong> "{scene.overlayText}"
                  </p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // ---------------------------------------------------------------------------
  // MAIN RENDER
  // ---------------------------------------------------------------------------

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-gray-800 rounded-2xl shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col border border-gray-700/50">

        {/* Header */}
        <header className="p-4 border-b border-gray-700 flex justify-between items-center flex-shrink-0">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-bold text-indigo-400 flex items-center gap-2">
              <FilmIcon className="w-6 h-6" />
              VideoStudio
            </h2>

            {/* Mode Selector */}
            <div className="flex gap-1 bg-gray-900/50 rounded-lg p-1">
              <button
                onClick={() => setMode('manual')}
                className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                  mode === 'manual'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <SlidersIcon className="w-4 h-4 inline mr-1" />
                Manual
              </button>
              <button
                onClick={() => setMode('ai-blueprint')}
                className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                  mode === 'ai-blueprint'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <WandIcon className="w-4 h-4 inline mr-1" />
                AI Blueprint
              </button>
              <button
                onClick={() => setMode('hybrid')}
                className={`px-3 py-1 rounded text-sm font-medium transition-all ${
                  mode === 'hybrid'
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                <SparklesIcon className="w-4 h-4 inline mr-1" />
                Hybrid
              </button>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            &times;
          </button>
        </header>

        {/* Main Content */}
        <div className="flex-grow p-6 overflow-hidden grid md:grid-cols-12 gap-6">

          {/* Left Panel: Tools & Edits */}
          <div className="md:col-span-4 flex flex-col gap-4 overflow-y-auto">

            {/* AI Assistant Input */}
            {(mode === 'manual' || mode === 'hybrid') && (
              <div className="bg-indigo-900/30 p-3 rounded-lg border border-indigo-500/30">
                <label className="text-xs font-bold text-indigo-300 mb-1 block flex items-center gap-2">
                  <SparklesIcon className="w-4 h-4" />
                  AI Assistant {mode === 'hybrid' ? '(Suggests)' : '(Direct Apply)'}
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={aiPrompt}
                    onChange={e => setAiPrompt(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleAICommand()}
                    placeholder="e.g., 'Make it vertical', 'Add captions', 'Speed up'..."
                    className="bg-gray-900 border border-gray-600 rounded p-2 text-sm w-full text-white placeholder-gray-500"
                  />
                  <button
                    onClick={handleAICommand}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 rounded text-sm flex items-center gap-1"
                  >
                    <SendIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Source Videos Info */}
            <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700/50">
              <h4 className="text-sm font-bold text-gray-300 mb-2">Source Videos ({sourceVideos.length})</h4>
              <div className="space-y-1">
                {sourceVideos.map((video, idx) => (
                  <div key={idx} className="text-xs text-gray-400 truncate">
                    {idx + 1}. {video.name}
                  </div>
                ))}
              </div>
            </div>

            {/* Tabs for different panels */}
            {mode !== 'ai-blueprint' && (
              <div className="flex gap-1 bg-gray-900/50 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('edits')}
                  className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-all ${
                    activeTab === 'edits'
                      ? 'bg-gray-700 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Edits ({edits.length})
                </button>
                {aiBlueprint && (
                  <button
                    onClick={() => setActiveTab('blueprint')}
                    className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-all ${
                      activeTab === 'blueprint'
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    Blueprint
                  </button>
                )}
                {mode === 'hybrid' && (
                  <button
                    onClick={() => setActiveTab('suggestions')}
                    className={`flex-1 px-2 py-1 rounded text-xs font-medium transition-all ${
                      activeTab === 'suggestions'
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-400 hover:text-white'
                    }`}
                  >
                    AI Suggestions ({aiSuggestions.length})
                  </button>
                )}
              </div>
            )}

            {/* Edit Queue */}
            {(mode === 'manual' || mode === 'hybrid') && activeTab === 'edits' && (
              <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 flex-grow overflow-hidden flex flex-col">
                <h4 className="text-base font-bold text-gray-300 mb-3">Edit Queue</h4>
                <div className="space-y-2 text-xs flex-grow overflow-y-auto">
                  {edits.length === 0 && (
                    <p className="text-center text-gray-500 py-4">
                      Add an edit operation to get started
                    </p>
                  )}
                  {edits.map(edit => (
                    <div
                      key={edit.id}
                      className={`bg-gray-800 p-2 rounded border transition-all ${
                        selectedEditId === edit.id
                          ? 'border-indigo-500'
                          : 'border-gray-700'
                      }`}
                      onClick={() => setSelectedEditId(edit.id)}
                    >
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-indigo-400 capitalize">
                          {edit.type}
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            removeEdit(edit.id);
                          }}
                          className="text-red-400 hover:text-red-300 font-bold text-lg"
                        >
                          &times;
                        </button>
                      </div>
                      {renderEditControl(edit)}
                    </div>
                  ))}
                </div>

                {/* Add Edit Dropdown */}
                <div className="relative mt-3">
                  <select
                    defaultValue=""
                    onChange={e => {
                      if (e.target.value) {
                        addEdit(e.target.value as AdvancedEdit['type']);
                        e.target.value = '';
                      }
                    }}
                    className="w-full bg-gray-700 hover:bg-gray-600 text-white font-bold py-2 px-3 rounded-lg appearance-none text-center cursor-pointer"
                  >
                    <option value="" disabled>+ Add Edit Operation</option>
                    <option value="trim">Trim</option>
                    <option value="text">Text Overlay</option>
                    <option value="image">Image Overlay</option>
                    <option value="speed">Speed Change</option>
                    <option value="filter">Filter</option>
                    <option value="color">Color Correction</option>
                    <option value="volume">Volume Control</option>
                    <option value="fade">Fade In/Out</option>
                    <option value="crop">Crop / Resize</option>
                    <option value="subtitles">Add Subtitles</option>
                    <option value="mute">Mute Audio</option>
                  </select>
                </div>
              </div>
            )}

            {/* AI Blueprint Panel */}
            {activeTab === 'blueprint' && aiBlueprint && (
              <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 flex-grow overflow-hidden flex flex-col">
                <h4 className="text-base font-bold text-gray-300 mb-3 flex items-center gap-2">
                  <WandIcon className="w-5 h-5 text-indigo-400" />
                  AI Blueprint
                </h4>
                <div className="mb-3">
                  <h5 className="text-sm font-semibold text-white">{aiBlueprint.variationTitle}</h5>
                  <p className="text-xs text-gray-400">{aiBlueprint.headline}</p>
                </div>
                <div className="flex-grow overflow-y-auto">
                  {renderBlueprintTimeline()}
                </div>
              </div>
            )}

            {/* AI Suggestions Panel */}
            {mode === 'hybrid' && activeTab === 'suggestions' && (
              <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 flex-grow overflow-hidden flex flex-col">
                <h4 className="text-base font-bold text-gray-300 mb-3 flex items-center gap-2">
                  <SparklesIcon className="w-5 h-5 text-indigo-400" />
                  AI Suggestions
                </h4>
                <div className="space-y-2 text-xs flex-grow overflow-y-auto">
                  {aiSuggestions.length === 0 && (
                    <p className="text-center text-gray-500 py-4">
                      Use the AI Assistant above to get suggestions
                    </p>
                  )}
                  {aiSuggestions.map(suggestion => (
                    <div
                      key={suggestion.id}
                      className="bg-gray-800 p-3 rounded border border-gray-700"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <p className="text-gray-300 font-medium mb-1">
                            {suggestion.description}
                          </p>
                          <p className="text-gray-500 text-xs">
                            Confidence: {(suggestion.confidence * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => applySuggestion(suggestion)}
                          className="flex-1 bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs font-medium"
                        >
                          Apply
                        </button>
                        <button
                          onClick={() => dismissSuggestion(suggestion.id)}
                          className="flex-1 bg-gray-700 hover:bg-gray-600 text-white px-2 py-1 rounded text-xs font-medium"
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Blueprint View (when in blueprint mode) */}
            {mode === 'ai-blueprint' && aiBlueprint && (
              <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700/50 flex-grow overflow-hidden flex flex-col">
                <h4 className="text-base font-bold text-gray-300 mb-3 flex items-center gap-2">
                  <WandIcon className="w-5 h-5 text-indigo-400" />
                  AI Edit Blueprint
                </h4>
                <div className="mb-3">
                  <h5 className="text-sm font-semibold text-white">{aiBlueprint.variationTitle}</h5>
                  <p className="text-xs text-gray-400 mt-1">{aiBlueprint.headline}</p>
                  <p className="text-xs text-gray-500 mt-1">{aiBlueprint.body}</p>
                  <p className="text-xs text-indigo-400 mt-2 font-semibold">{aiBlueprint.cta}</p>
                </div>
                <div className="flex-grow overflow-y-auto">
                  {renderBlueprintTimeline()}
                </div>
              </div>
            )}

            {/* Render Button */}
            <button
              onClick={handleRenderVideo}
              disabled={isProcessing || sourceVideos.length === 0}
              className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white font-bold py-3 px-4 rounded-lg flex items-center justify-center gap-2 transition-all text-lg"
            >
              <PlayIcon className="w-5 h-5" />
              {isProcessing ? 'Rendering...' : 'Render Video'}
            </button>
          </div>

          {/* Right Panel: Preview & Output */}
          <div className="md:col-span-8 bg-gray-900/50 rounded-lg p-4 flex flex-col overflow-hidden">

            {/* Source Preview (when not processing or done) */}
            {!isProcessing && !outputUrl && sourceVideos.length > 0 && (
              <div className="w-full mb-4">
                <h4 className="font-bold text-gray-300 mb-2">Source Preview</h4>
                <VideoPlayer src={sourceVideoUrls.current[0]} />
              </div>
            )}

            {/* Processing State */}
            {isProcessing && (
              <div className="flex-grow flex flex-col justify-center">
                <div className="text-center p-4 bg-gray-900/50 rounded-lg mb-4">
                  <p className="font-semibold text-indigo-400 mb-2">{progressMessage}</p>
                  <div className="w-full bg-gray-700 rounded-full h-2.5 mt-2">
                    <div
                      className="bg-indigo-500 h-2.5 rounded-full transition-all"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Processing happens in your browser. This can take several minutes.
                  </p>
                </div>

                {/* FFmpeg Logs */}
                <div className="flex-grow flex flex-col">
                  <div className="flex justify-between items-center mb-2">
                    <h4 className="font-bold text-gray-300 text-sm">Processing Logs</h4>
                    <button
                      onClick={() => setShowLogs(!showLogs)}
                      className="text-xs text-indigo-400 hover:text-indigo-300"
                    >
                      {showLogs ? 'Hide' : 'Show'}
                    </button>
                  </div>
                  {showLogs && (
                    <div className="flex-grow bg-black rounded-md p-2 overflow-y-scroll font-mono text-xs text-gray-500 border border-gray-700">
                      {logs.length > 0 ? (
                        logs.map((log, i) => (
                          <p key={i} className="whitespace-pre-wrap leading-tight">
                            {log}
                          </p>
                        ))
                      ) : (
                        <p>Waiting for FFmpeg logs...</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Error State */}
            {error && !isProcessing && (
              <div className="flex items-center justify-center flex-grow">
                <p className="text-red-400 text-center p-4 bg-red-900/30 rounded-lg max-w-2xl">
                  {error}
                </p>
              </div>
            )}

            {/* Output Video */}
            {outputUrl && !isProcessing && (
              <div className="flex-grow flex flex-col">
                <h4 className="font-bold text-gray-300 mb-2">Rendered Output</h4>
                <div className="flex-grow flex items-center justify-center">
                  <video
                    src={outputUrl}
                    controls
                    className="w-full max-h-full rounded-md aspect-video"
                  ></video>
                </div>
                <button
                  onClick={handleDownload}
                  className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-all mt-4"
                >
                  <DownloadIcon className="w-5 h-5" />
                  Download Video
                </button>
              </div>
            )}

            {/* Empty State */}
            {!isProcessing && !outputUrl && !error && sourceVideos.length === 0 && (
              <div className="flex items-center justify-center flex-grow text-gray-500">
                <p>No source videos loaded</p>
              </div>
            )}

            {!isProcessing && !outputUrl && !error && sourceVideos.length > 0 && (
              <div className="flex items-center justify-center flex-grow text-gray-500">
                <p>Configure your edits and click "Render Video" to start</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoStudio;
