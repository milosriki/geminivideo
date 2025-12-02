import React, { useState, useCallback } from 'react';
import {
  SparklesIcon,
  WandIcon,
  ImageIcon,
  VideoIcon,
  FilmIcon,
  DownloadIcon,
  CheckIcon
} from './icons';

interface GeneratedAsset {
  id: string;
  type: 'image' | 'video' | 'text' | 'audio';
  name: string;
  url: string;
  thumbnail?: string;
  status: 'generating' | 'ready' | 'error';
  prompt?: string;
  createdAt: string;
}

interface AITemplate {
  id: string;
  name: string;
  description: string;
  category: 'ad' | 'social' | 'thumbnail' | 'logo' | 'video';
  preview: string;
  aspectRatio: string;
}

interface AICreativeStudioProps {
  projectId?: string;
  onAssetGenerated?: (asset: GeneratedAsset) => void;
}

const TEMPLATES: AITemplate[] = [
  {
    id: 't1',
    name: 'Product Showcase',
    description: 'Clean product-focused ad with dynamic background',
    category: 'ad',
    preview: '/api/placeholder/200/200',
    aspectRatio: '1:1',
  },
  {
    id: 't2',
    name: 'Testimonial Video',
    description: 'Customer testimonial with animated text overlays',
    category: 'video',
    preview: '/api/placeholder/200/112',
    aspectRatio: '16:9',
  },
  {
    id: 't3',
    name: 'Story Ad',
    description: 'Vertical format for Instagram/TikTok stories',
    category: 'social',
    preview: '/api/placeholder/112/200',
    aspectRatio: '9:16',
  },
  {
    id: 't4',
    name: 'YouTube Thumbnail',
    description: 'Eye-catching thumbnail with bold text',
    category: 'thumbnail',
    preview: '/api/placeholder/200/112',
    aspectRatio: '16:9',
  },
  {
    id: 't5',
    name: 'Carousel Post',
    description: 'Multi-slide format for educational content',
    category: 'social',
    preview: '/api/placeholder/200/200',
    aspectRatio: '1:1',
  },
  {
    id: 't6',
    name: 'Promo Banner',
    description: 'Wide format banner for sales and promotions',
    category: 'ad',
    preview: '/api/placeholder/300/100',
    aspectRatio: '3:1',
  },
];

const GENERATED_ASSETS: GeneratedAsset[] = [
  {
    id: 'g1',
    type: 'image',
    name: 'Product Ad - Version A',
    url: '/generated/ad-1.png',
    status: 'ready',
    prompt: 'Modern fitness product on gradient background',
    createdAt: '2024-12-01T10:30:00Z',
  },
  {
    id: 'g2',
    type: 'image',
    name: 'Story Background',
    url: '/generated/story-bg.png',
    status: 'ready',
    prompt: 'Abstract gradient with geometric shapes',
    createdAt: '2024-12-01T09:15:00Z',
  },
  {
    id: 'g3',
    type: 'video',
    name: 'Product Demo',
    url: '/generated/demo.mp4',
    status: 'ready',
    prompt: 'Product rotation animation with particles',
    createdAt: '2024-11-30T16:45:00Z',
  },
];

const STYLES = [
  'Photorealistic',
  'Digital Art',
  'Minimalist',
  '3D Render',
  'Cinematic',
  'Vibrant Pop',
  'Professional',
  'Vintage',
];

export const AICreativeStudio: React.FC<AICreativeStudioProps> = ({
  projectId,
  onAssetGenerated
}) => {
  const [activeTab, setActiveTab] = useState<'generate' | 'templates' | 'library'>('generate');
  const [generationType, setGenerationType] = useState<'image' | 'video' | 'text'>('image');
  const [prompt, setPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('Photorealistic');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAssets, setGeneratedAssets] = useState<GeneratedAsset[]>(GENERATED_ASSETS);
  const [selectedAssets, setSelectedAssets] = useState<Set<string>>(new Set());

  const handleGenerate = useCallback(async () => {
    if (!prompt.trim()) return;

    setIsGenerating(true);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 3000));

    const newAsset: GeneratedAsset = {
      id: `gen-${Date.now()}`,
      type: generationType,
      name: `Generated ${generationType} - ${Date.now()}`,
      url: `/generated/new-${Date.now()}.${generationType === 'video' ? 'mp4' : 'png'}`,
      status: 'ready',
      prompt,
      createdAt: new Date().toISOString(),
    };

    setGeneratedAssets(prev => [newAsset, ...prev]);
    onAssetGenerated?.(newAsset);
    setIsGenerating(false);
    setPrompt('');
  }, [prompt, generationType, onAssetGenerated]);

  const toggleAssetSelection = (assetId: string) => {
    setSelectedAssets(prev => {
      const next = new Set(prev);
      if (next.has(assetId)) {
        next.delete(assetId);
      } else {
        next.add(assetId);
      }
      return next;
    });
  };

  const renderGenerateTab = () => (
    <div className="space-y-6">
      {/* Generation Type */}
      <div className="flex gap-2">
        {[
          { id: 'image' as const, label: 'Image', icon: ImageIcon },
          { id: 'video' as const, label: 'Video', icon: VideoIcon },
          { id: 'text' as const, label: 'Copy', icon: 'T' },
        ].map(type => (
          <button
            key={type.id}
            onClick={() => setGenerationType(type.id)}
            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-all ${
              generationType === type.id
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
            }`}
          >
            {typeof type.icon === 'string' ? (
              <span className="text-lg font-bold">{type.icon}</span>
            ) : (
              <type.icon className="w-5 h-5" />
            )}
            {type.label}
          </button>
        ))}
      </div>

      {/* Prompt Input */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Describe what you want to create
        </label>
        <textarea
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          placeholder={
            generationType === 'image'
              ? 'A modern fitness product on a clean gradient background with soft lighting...'
              : generationType === 'video'
              ? 'A 15-second product showcase video with smooth camera movement...'
              : 'Write a compelling ad headline for a fitness app targeting busy professionals...'
          }
          rows={4}
          className="w-full p-4 bg-gray-800/60 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Style Selection */}
      {generationType !== 'text' && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Style
          </label>
          <div className="flex flex-wrap gap-2">
            {STYLES.map(style => (
              <button
                key={style}
                onClick={() => setSelectedStyle(style)}
                className={`px-4 py-2 rounded-lg text-sm transition-all ${
                  selectedStyle === style
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                {style}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Aspect Ratio */}
      {generationType !== 'text' && (
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Aspect Ratio
          </label>
          <div className="flex gap-3">
            {['1:1', '16:9', '9:16', '4:5'].map(ratio => (
              <button
                key={ratio}
                onClick={() => setAspectRatio(ratio)}
                className={`flex flex-col items-center gap-1 p-3 rounded-lg transition-all ${
                  aspectRatio === ratio
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                }`}
              >
                <div
                  className={`bg-current opacity-50 rounded ${
                    ratio === '1:1' ? 'w-6 h-6' :
                    ratio === '16:9' ? 'w-8 h-4' :
                    ratio === '9:16' ? 'w-4 h-8' :
                    'w-5 h-6'
                  }`}
                />
                <span className="text-xs">{ratio}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerate}
        disabled={!prompt.trim() || isGenerating}
        className={`w-full py-4 rounded-lg font-bold text-lg flex items-center justify-center gap-2 transition-all ${
          isGenerating
            ? 'bg-indigo-800 text-indigo-300 cursor-wait'
            : prompt.trim()
            ? 'bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white'
            : 'bg-gray-700 text-gray-500 cursor-not-allowed'
        }`}
      >
        {isGenerating ? (
          <>
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Generating...
          </>
        ) : (
          <>
            <SparklesIcon className="w-5 h-5" />
            Generate {generationType === 'text' ? 'Copy' : generationType.charAt(0).toUpperCase() + generationType.slice(1)}
          </>
        )}
      </button>

      {/* Quick Prompts */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">
          Quick Prompts
        </label>
        <div className="flex flex-wrap gap-2">
          {[
            'Product showcase with gradient',
            'Testimonial style UGC',
            'Before/after comparison',
            'Bold sale announcement',
          ].map(quickPrompt => (
            <button
              key={quickPrompt}
              onClick={() => setPrompt(quickPrompt)}
              className="px-3 py-1.5 bg-gray-800/60 border border-gray-700 rounded-full text-xs text-gray-400 hover:text-white hover:border-gray-600 transition-colors"
            >
              {quickPrompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  const renderTemplatesTab = () => (
    <div className="space-y-6">
      <div className="flex gap-2 overflow-x-auto pb-2">
        {['all', 'ad', 'video', 'social', 'thumbnail'].map(cat => (
          <button
            key={cat}
            className="px-4 py-2 bg-gray-800 rounded-lg text-sm whitespace-nowrap hover:bg-gray-700 transition-colors"
          >
            {cat === 'all' ? 'All Templates' : cat.charAt(0).toUpperCase() + cat.slice(1)}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {TEMPLATES.map(template => (
          <div
            key={template.id}
            className="bg-gray-800/60 border border-gray-700 rounded-lg overflow-hidden hover:border-indigo-500/50 transition-all cursor-pointer group"
          >
            <div className="aspect-video bg-gray-900 flex items-center justify-center relative">
              <FilmIcon className="w-8 h-8 text-gray-700" />
              <div className="absolute inset-0 bg-indigo-600/0 group-hover:bg-indigo-600/20 transition-colors flex items-center justify-center">
                <WandIcon className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
            <div className="p-3">
              <h3 className="font-medium text-sm">{template.name}</h3>
              <p className="text-xs text-gray-500 mt-1">{template.description}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="px-2 py-0.5 bg-gray-700 rounded text-xs">{template.category}</span>
                <span className="text-xs text-gray-500">{template.aspectRatio}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderLibraryTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400">
          {selectedAssets.size > 0 ? `${selectedAssets.size} selected` : `${generatedAssets.length} assets`}
        </span>
        {selectedAssets.size > 0 && (
          <div className="flex gap-2">
            <button className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm transition-colors">
              Export Selected
            </button>
            <button className="px-3 py-1.5 bg-red-600/20 text-red-400 hover:bg-red-600/30 rounded text-sm transition-colors">
              Delete
            </button>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {generatedAssets.map(asset => (
          <div
            key={asset.id}
            onClick={() => toggleAssetSelection(asset.id)}
            className={`bg-gray-800/60 border rounded-lg overflow-hidden cursor-pointer transition-all ${
              selectedAssets.has(asset.id)
                ? 'border-indigo-500 ring-2 ring-indigo-500/20'
                : 'border-gray-700 hover:border-gray-600'
            }`}
          >
            <div className="aspect-square bg-gray-900 flex items-center justify-center relative">
              {asset.type === 'image' ? (
                <ImageIcon className="w-8 h-8 text-gray-700" />
              ) : asset.type === 'video' ? (
                <VideoIcon className="w-8 h-8 text-gray-700" />
              ) : (
                <span className="text-2xl font-bold text-gray-700">T</span>
              )}
              {selectedAssets.has(asset.id) && (
                <div className="absolute top-2 right-2 w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center">
                  <CheckIcon className="w-4 h-4" />
                </div>
              )}
            </div>
            <div className="p-3">
              <h3 className="font-medium text-sm truncate">{asset.name}</h3>
              <p className="text-xs text-gray-500 truncate mt-1">{asset.prompt}</p>
              <div className="flex items-center justify-between mt-2">
                <span className="text-xs text-gray-500">
                  {new Date(asset.createdAt).toLocaleDateString()}
                </span>
                <button
                  onClick={e => {
                    e.stopPropagation();
                    // Download logic
                  }}
                  className="p-1 hover:bg-gray-700 rounded transition-colors"
                >
                  <DownloadIcon className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center">
            <SparklesIcon className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">AI Creative Studio</h1>
            <p className="text-gray-400 text-sm">Generate images, videos, and copy with AI</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-gray-800/60 p-1 rounded-lg mb-6 w-fit">
          {[
            { id: 'generate' as const, label: 'Generate' },
            { id: 'templates' as const, label: 'Templates' },
            { id: 'library' as const, label: 'My Library' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-gray-700 text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="bg-gray-800/40 border border-gray-700 rounded-xl p-6">
          {activeTab === 'generate' && renderGenerateTab()}
          {activeTab === 'templates' && renderTemplatesTab()}
          {activeTab === 'library' && renderLibraryTab()}
        </div>
      </div>
    </div>
  );
};

export default AICreativeStudio;
