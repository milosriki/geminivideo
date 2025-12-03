import React, { useState, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { UploadIcon, VideoIcon, ImageIcon, CheckIcon } from '../icons';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

interface CreativeStepProps {
  data: {
    uploadedFiles?: File[];
    style?: string;
    scriptTemplate?: string;
    hookStyle?: string;
    variants?: number;
    selectedAvatar?: string;
  };
  onUpdate: (data: Partial<CreativeStepProps['data']>) => void;
  onNext: () => void;
  onBack: () => void;
}

const STYLES = [
  { value: 'ugc', label: 'UGC', description: 'User-generated content style' },
  { value: 'professional', label: 'Professional', description: 'Polished and branded' },
  { value: 'mixed', label: 'Mixed', description: 'Combination of both' },
];

const SCRIPT_TEMPLATES = [
  { value: 'problem-solution', label: 'Problem → Solution' },
  { value: 'testimonial', label: 'Customer Testimonial' },
  { value: 'how-to', label: 'How-To Guide' },
  { value: 'product-demo', label: 'Product Demo' },
  { value: 'lifestyle', label: 'Lifestyle' },
];

const HOOK_STYLES = [
  { value: 'question', label: 'Question Hook' },
  { value: 'shocking', label: 'Shocking Statement' },
  { value: 'storytelling', label: 'Story Beginning' },
  { value: 'direct', label: 'Direct Promise' },
];

interface Avatar {
  id: string;
  name: string;
  thumbnail: string;
}

export const CreativeStep: React.FC<CreativeStepProps> = ({
  data,
  onUpdate,
  onNext,
  onBack,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch avatars from API
  useEffect(() => {
    const fetchAvatars = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/avatars`);
        if (!response.ok) {
          throw new Error(response.status.toString());
        }
        const data = await response.json();
        setAvatars(data);
        setError(null);
      } catch (err) {
        setError('Data source not configured. Please configure avatars in the backend.');
        setAvatars([]);
      } finally {
        setLoading(false);
      }
    };

    fetchAvatars();
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      onUpdate({ uploadedFiles: [...(data.uploadedFiles || []), ...files] });
    },
    [data.uploadedFiles, onUpdate]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files) {
        const files = Array.from(e.target.files);
        onUpdate({ uploadedFiles: [...(data.uploadedFiles || []), ...files] });
      }
    },
    [data.uploadedFiles, onUpdate]
  );

  const removeFile = (index: number) => {
    const newFiles = [...(data.uploadedFiles || [])];
    newFiles.splice(index, 1);
    onUpdate({ uploadedFiles: newFiles });
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* File Upload */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-3">
          Upload Creative Assets
        </label>
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all ${
            isDragging
              ? 'border-indigo-500 bg-indigo-500/10'
              : 'border-zinc-700 hover:border-indigo-500/50'
          }`}
        >
          <input
            type="file"
            multiple
            accept="video/*,image/*"
            onChange={handleFileSelect}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          <UploadIcon className="w-12 h-12 mx-auto text-zinc-500 mb-4" />
          <p className="text-zinc-300 font-medium mb-1">
            Drag & drop files here
          </p>
          <p className="text-sm text-zinc-500">
            or click to browse (videos, images)
          </p>
        </div>

        {data.uploadedFiles && data.uploadedFiles.length > 0 && (
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 gap-3">
            {data.uploadedFiles.map((file, index) => (
              <div
                key={index}
                className="relative bg-zinc-800 border border-zinc-700 rounded-lg p-3"
              >
                <div className="flex items-center gap-2">
                  {file.type.startsWith('video/') ? (
                    <VideoIcon className="w-5 h-5 text-indigo-400 flex-shrink-0" />
                  ) : (
                    <ImageIcon className="w-5 h-5 text-green-400 flex-shrink-0" />
                  )}
                  <span className="text-sm text-zinc-300 truncate">
                    {file.name}
                  </span>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 hover:bg-red-600 rounded-full flex items-center justify-center transition-colors"
                >
                  <span className="text-white text-sm">&times;</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Style Selector */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-3">
          Creative Style
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {STYLES.map((style) => (
            <button
              key={style.value}
              onClick={() => onUpdate({ style: style.value })}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                data.style === style.value
                  ? 'border-indigo-500 bg-indigo-500/10'
                  : 'border-zinc-700 bg-zinc-800/60 hover:border-zinc-600'
              }`}
            >
              <div className="font-medium text-white">{style.label}</div>
              <div className="text-sm text-zinc-400 mt-1">
                {style.description}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Script Template */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">
          Script Template
        </label>
        <select
          value={data.scriptTemplate || ''}
          onChange={(e) => onUpdate({ scriptTemplate: e.target.value })}
          className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        >
          <option value="">Select a template</option>
          {SCRIPT_TEMPLATES.map((template) => (
            <option key={template.value} value={template.value}>
              {template.label}
            </option>
          ))}
        </select>
      </div>

      {/* Hook Style */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">
          Hook Style
        </label>
        <select
          value={data.hookStyle || ''}
          onChange={(e) => onUpdate({ hookStyle: e.target.value })}
          className="w-full px-4 py-3 bg-zinc-800 border border-zinc-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        >
          <option value="">Select a hook style</option>
          {HOOK_STYLES.map((hook) => (
            <option key={hook.value} value={hook.value}>
              {hook.label}
            </option>
          ))}
        </select>
      </div>

      {/* Number of Variants */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-2">
          Number of Variants: {data.variants || 1}
        </label>
        <input
          type="range"
          min="1"
          max="5"
          value={data.variants || 1}
          onChange={(e) => onUpdate({ variants: Number(e.target.value) })}
          className="w-full h-2 bg-zinc-700 rounded-lg appearance-none cursor-pointer slider"
        />
        <div className="flex justify-between text-xs text-zinc-500 mt-1">
          <span>1</span>
          <span>2</span>
          <span>3</span>
          <span>4</span>
          <span>5</span>
        </div>
      </div>

      {/* Avatar Selection */}
      <div>
        <label className="block text-sm font-medium text-zinc-300 mb-3">
          Select AI Avatar
        </label>
        {loading ? (
          <div className="text-zinc-500 text-sm py-4">Loading avatars...</div>
        ) : error ? (
          <div className="text-red-400 text-sm py-4">{error}</div>
        ) : avatars.length === 0 ? (
          <div className="text-zinc-500 text-sm py-4">No avatars available</div>
        ) : (
          <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
            {avatars.map((avatar) => (
            <button
              key={avatar.id}
              onClick={() => onUpdate({ selectedAvatar: avatar.id })}
              className={`relative aspect-square rounded-lg border-2 flex flex-col items-center justify-center transition-all ${
                data.selectedAvatar === avatar.id
                  ? 'border-indigo-500 bg-indigo-500/10'
                  : 'border-zinc-700 bg-zinc-800/60 hover:border-zinc-600'
              }`}
            >
              <div className="text-3xl mb-1">{avatar.thumbnail}</div>
              <div className="text-xs text-zinc-400">{avatar.name}</div>
              {data.selectedAvatar === avatar.id && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-indigo-500 rounded-full flex items-center justify-center">
                  <CheckIcon className="w-4 h-4 text-white" />
                </div>
              )}
            </button>
            ))}
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between pt-4">
        <button
          onClick={onBack}
          className="px-6 py-3 border border-zinc-600 text-zinc-300 rounded-lg hover:bg-zinc-800 transition-colors"
        >
          Back
        </button>
        <button
          onClick={onNext}
          className="px-8 py-3 bg-indigo-500 hover:bg-indigo-600 text-white font-medium rounded-lg transition-colors shadow-lg shadow-indigo-500/30"
        >
          Next Step
        </button>
      </div>
    </motion.div>
  );
};
