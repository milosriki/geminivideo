import React, { useState, useCallback, useRef } from 'react';
import { WandIcon, SparklesIcon, RefreshIcon, DownloadIcon, CheckIcon, XIcon, ImageIcon, VideoIcon, CopyIcon, EyeIcon, MobileIcon, MonitorIcon } from './icons';

// ============================================================================
// TYPES & INTERFACES
// ============================================================================

interface Creative {
  id: string;
  productInfo: ProductInfo;
  targetAudience: string;
  brandVoice: BrandVoice;
  hook: GeneratedHook | null;
  copy: GeneratedCopy | null;
  image: GeneratedImage | null;
  video: GeneratedVideo | null;
  cta: GeneratedCTA | null;
  variants: CreativeVariant[];
  createdAt: Date;
}

interface ProductInfo {
  name: string;
  description: string;
  benefits: string;
  uniqueSellingPoint: string;
  painPoints: string;
  offer: string;
}

type BrandVoice = 'direct' | 'empathetic' | 'authoritative' | 'playful' | 'inspirational' | 'professional';

interface GeneratedHook {
  text: string;
  type: HookType;
  strength: number;
  suggestions: string[];
}

type HookType =
  | 'curiosity_gap'
  | 'transformation'
  | 'urgency_scarcity'
  | 'social_proof'
  | 'pattern_interrupt'
  | 'question'
  | 'negative_hook'
  | 'story_hook'
  | 'statistic_hook'
  | 'controversy_hook'
  | 'benefit_stack'
  | 'pain_agitate';

interface GeneratedCopy {
  headline: string;
  body: string;
  variants: string[];
}

interface GeneratedImage {
  url: string;
  prompt: string;
  aspectRatio: '1:1' | '16:9' | '9:16' | '4:5';
}

interface GeneratedVideo {
  url: string;
  prompt: string;
  duration: number;
  storyboard: StoryboardFrame[];
}

interface StoryboardFrame {
  timestamp: number;
  description: string;
  imagePrompt: string;
}

interface GeneratedCTA {
  text: string;
  type: 'learn_more' | 'shop_now' | 'sign_up' | 'get_started' | 'download' | 'book_call';
  urgencyLevel: number;
}

interface CreativeVariant {
  id: string;
  name: string;
  hook: string;
  copy: string;
  cta: string;
  performance?: {
    predictedCTR: number;
    predictedROI: number;
  };
}

type Platform = 'feed' | 'stories' | 'reels' | 'shorts' | 'tiktok';
type DeviceType = 'mobile' | 'desktop';

interface AICreativeStudioProps {
  onCreativeGenerated: (creative: Creative) => void;
}

// ============================================================================
// API CLIENT
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

const creativeAPI = {
  // Agent 17: Hook Detection & Generation
  async generateHooks(productInfo: ProductInfo, targetAudience: string, count: number = 5): Promise<GeneratedHook[]> {
    const response = await fetch(`${API_BASE_URL}/hooks/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: productInfo.name,
        product_description: productInfo.description,
        target_audience: targetAudience,
        pain_points: productInfo.painPoints,
        unique_selling_point: productInfo.uniqueSellingPoint,
        count
      })
    });

    if (!response.ok) {
      throw new Error(`Hook generation failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.hooks.map((h: any) => ({
      text: h.text,
      type: h.type,
      strength: h.strength,
      suggestions: h.suggestions || []
    }));
  },

  async analyzeHook(text: string): Promise<{ type: HookType; strength: number; suggestions: string[] }> {
    const response = await fetch(`${API_BASE_URL}/hooks/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (!response.ok) {
      throw new Error(`Hook analysis failed: ${response.statusText}`);
    }

    return response.json();
  },

  // Agent 23: Vertex AI - Ad Copy Generation
  async generateAdCopy(
    productInfo: ProductInfo,
    targetAudience: string,
    brandVoice: BrandVoice,
    hook: string
  ): Promise<GeneratedCopy> {
    const response = await fetch(`${API_BASE_URL}/vertex/generate-copy`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: productInfo.name,
        product_description: productInfo.description,
        benefits: productInfo.benefits,
        target_audience: targetAudience,
        brand_voice: brandVoice,
        hook,
        offer: productInfo.offer
      })
    });

    if (!response.ok) {
      throw new Error(`Copy generation failed: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      headline: data.headline,
      body: data.body,
      variants: data.variants || []
    };
  },

  // Agent 23: Vertex AI - Image Generation (Imagen)
  async generateImage(
    prompt: string,
    aspectRatio: '1:1' | '16:9' | '9:16' | '4:5',
    productInfo: ProductInfo
  ): Promise<GeneratedImage> {
    const response = await fetch(`${API_BASE_URL}/vertex/generate-image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        aspect_ratio: aspectRatio,
        product_context: {
          name: productInfo.name,
          description: productInfo.description
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Image generation failed: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      url: data.image_url,
      prompt: data.refined_prompt || prompt,
      aspectRatio
    };
  },

  // Agent 23: Vertex AI - Video Generation (Veo)
  async generateVideo(
    prompt: string,
    duration: number,
    productInfo: ProductInfo
  ): Promise<GeneratedVideo> {
    const response = await fetch(`${API_BASE_URL}/vertex/generate-video`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        prompt,
        duration,
        product_context: {
          name: productInfo.name,
          description: productInfo.description
        }
      })
    });

    if (!response.ok) {
      throw new Error(`Video generation failed: ${response.statusText}`);
    }

    const data = await response.json();
    return {
      url: data.video_url,
      prompt: data.refined_prompt || prompt,
      duration,
      storyboard: data.storyboard || []
    };
  },

  // Generate storyboard for video planning
  async generateStoryboard(
    productInfo: ProductInfo,
    hook: string,
    targetAudience: string
  ): Promise<StoryboardFrame[]> {
    const response = await fetch(`${API_BASE_URL}/vertex/generate-storyboard`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: productInfo.name,
        product_description: productInfo.description,
        hook,
        target_audience: targetAudience
      })
    });

    if (!response.ok) {
      throw new Error(`Storyboard generation failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.frames;
  },

  // Generate CTAs
  async generateCTAs(
    productInfo: ProductInfo,
    hook: string,
    offer: string
  ): Promise<GeneratedCTA[]> {
    const response = await fetch(`${API_BASE_URL}/vertex/generate-cta`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_name: productInfo.name,
        hook,
        offer
      })
    });

    if (!response.ok) {
      throw new Error(`CTA generation failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.ctas;
  }
};

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

const ProductInfoForm: React.FC<{
  productInfo: ProductInfo;
  onChange: (info: ProductInfo) => void;
}> = ({ productInfo, onChange }) => {
  const handleChange = (field: keyof ProductInfo, value: string) => {
    onChange({ ...productInfo, [field]: value });
  };

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-semibold text-gray-300 mb-2">Product/Service Name</label>
        <input
          type="text"
          value={productInfo.name}
          onChange={(e) => handleChange('name', e.target.value)}
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
          placeholder="e.g., Ultimate Productivity App"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-300 mb-2">Description</label>
        <textarea
          value={productInfo.description}
          onChange={(e) => handleChange('description', e.target.value)}
          rows={3}
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
          placeholder="What does your product do?"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-300 mb-2">Key Benefits</label>
        <textarea
          value={productInfo.benefits}
          onChange={(e) => handleChange('benefits', e.target.value)}
          rows={2}
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
          placeholder="List the main benefits..."
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-300 mb-2">Unique Selling Point</label>
        <input
          type="text"
          value={productInfo.uniqueSellingPoint}
          onChange={(e) => handleChange('uniqueSellingPoint', e.target.value)}
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
          placeholder="What makes you different?"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-300 mb-2">Pain Points You Solve</label>
        <textarea
          value={productInfo.painPoints}
          onChange={(e) => handleChange('painPoints', e.target.value)}
          rows={2}
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
          placeholder="What problems does this solve?"
        />
      </div>

      <div>
        <label className="block text-sm font-semibold text-gray-300 mb-2">Current Offer</label>
        <input
          type="text"
          value={productInfo.offer}
          onChange={(e) => handleChange('offer', e.target.value)}
          className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
          placeholder="e.g., 50% off first month"
        />
      </div>
    </div>
  );
};

const HookGenerator: React.FC<{
  productInfo: ProductInfo;
  targetAudience: string;
  onHookSelected: (hook: GeneratedHook) => void;
  isGenerating: boolean;
  setIsGenerating: (val: boolean) => void;
}> = ({ productInfo, targetAudience, onHookSelected, isGenerating, setIsGenerating }) => {
  const [generatedHooks, setGeneratedHooks] = useState<GeneratedHook[]>([]);
  const [selectedHook, setSelectedHook] = useState<GeneratedHook | null>(null);
  const [customHook, setCustomHook] = useState('');

  const generateHooks = async () => {
    if (!productInfo.name || !targetAudience) {
      alert('Please fill in product name and target audience first');
      return;
    }

    setIsGenerating(true);
    try {
      const hooks = await creativeAPI.generateHooks(productInfo, targetAudience, 8);
      setGeneratedHooks(hooks);
    } catch (error) {
      console.error('Hook generation error:', error);
      alert(`Failed to generate hooks: ${error}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const analyzeCustomHook = async () => {
    if (!customHook.trim()) return;

    try {
      const analysis = await creativeAPI.analyzeHook(customHook);
      const hook: GeneratedHook = {
        text: customHook,
        ...analysis
      };
      setSelectedHook(hook);
      onHookSelected(hook);
    } catch (error) {
      console.error('Hook analysis error:', error);
      alert(`Failed to analyze hook: ${error}`);
    }
  };

  const selectHook = (hook: GeneratedHook) => {
    setSelectedHook(hook);
    onHookSelected(hook);
  };

  const hookTypeColors: Record<HookType, string> = {
    curiosity_gap: 'bg-purple-900/50 text-purple-300',
    transformation: 'bg-green-900/50 text-green-300',
    urgency_scarcity: 'bg-red-900/50 text-red-300',
    social_proof: 'bg-blue-900/50 text-blue-300',
    pattern_interrupt: 'bg-yellow-900/50 text-yellow-300',
    question: 'bg-indigo-900/50 text-indigo-300',
    negative_hook: 'bg-orange-900/50 text-orange-300',
    story_hook: 'bg-pink-900/50 text-pink-300',
    statistic_hook: 'bg-cyan-900/50 text-cyan-300',
    controversy_hook: 'bg-red-900/50 text-red-300',
    benefit_stack: 'bg-teal-900/50 text-teal-300',
    pain_agitate: 'bg-amber-900/50 text-amber-300'
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-white">Hook Generator</h3>
        <button
          onClick={generateHooks}
          disabled={isGenerating}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? (
            <>
              <RefreshIcon className="w-4 h-4 animate-spin" />
              Generating...
            </>
          ) : (
            <>
              <SparklesIcon className="w-4 h-4" />
              Generate Hooks
            </>
          )}
        </button>
      </div>

      {generatedHooks.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {generatedHooks.map((hook, idx) => (
            <div
              key={idx}
              onClick={() => selectHook(hook)}
              className={`p-4 bg-gray-800 border rounded-lg cursor-pointer hover:border-indigo-500 transition-all ${
                selectedHook?.text === hook.text ? 'border-indigo-500 bg-indigo-900/20' : 'border-gray-700'
              }`}
            >
              <div className="flex items-start justify-between mb-2">
                <span className={`text-xs px-2 py-1 rounded-full font-semibold ${hookTypeColors[hook.type]}`}>
                  {hook.type.replace('_', ' ')}
                </span>
                <span className="text-xs font-bold text-green-400">{hook.strength}/10</span>
              </div>
              <p className="text-white font-medium">{hook.text}</p>
            </div>
          ))}
        </div>
      )}

      <div className="border-t border-gray-700 pt-4">
        <label className="block text-sm font-semibold text-gray-300 mb-2">Or write your own hook:</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={customHook}
            onChange={(e) => setCustomHook(e.target.value)}
            className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
            placeholder="Type your custom hook..."
          />
          <button
            onClick={analyzeCustomHook}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-semibold"
          >
            Analyze
          </button>
        </div>
      </div>
    </div>
  );
};

const PreviewPanel: React.FC<{
  creative: Partial<Creative>;
  platform: Platform;
  deviceType: DeviceType;
}> = ({ creative, platform, deviceType }) => {
  const getPreviewDimensions = () => {
    if (deviceType === 'mobile') {
      if (platform === 'stories' || platform === 'reels' || platform === 'shorts' || platform === 'tiktok') {
        return { width: '300px', height: '533px', aspectRatio: '9/16' };
      }
      return { width: '375px', height: '667px', aspectRatio: '9/16' };
    }
    return { width: '500px', height: '281px', aspectRatio: '16/9' };
  };

  const dimensions = getPreviewDimensions();

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm font-semibold text-gray-400">
          {platform.toUpperCase()} Preview ({deviceType})
        </span>
      </div>

      <div
        className="mx-auto bg-gray-800 rounded-lg overflow-hidden border border-gray-700 relative"
        style={{ width: dimensions.width, aspectRatio: dimensions.aspectRatio }}
      >
        {creative.image?.url ? (
          <img src={creative.image.url} alt="Preview" className="w-full h-full object-cover" />
        ) : creative.video?.url ? (
          <video src={creative.video.url} className="w-full h-full object-cover" controls />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500">
            <ImageIcon className="w-16 h-16" />
          </div>
        )}

        {/* Overlay text */}
        {creative.hook && (
          <div className="absolute top-0 left-0 right-0 p-4 bg-gradient-to-b from-black/80 to-transparent">
            <p className="text-white font-bold text-sm">{creative.hook.text}</p>
          </div>
        )}

        {creative.copy && (
          <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/90 to-transparent">
            <p className="text-white font-semibold text-xs mb-1">{creative.copy.headline}</p>
            <p className="text-gray-300 text-xs line-clamp-2">{creative.copy.body}</p>
            {creative.cta && (
              <button className="mt-2 px-4 py-1 bg-indigo-600 text-white text-xs font-bold rounded-full">
                {creative.cta.text}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

const VariantManager: React.FC<{
  creative: Partial<Creative>;
  onCreateVariant: () => void;
}> = ({ creative, onCreateVariant }) => {
  const variants = creative.variants || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-white">A/B Test Variants</h3>
        <button
          onClick={onCreateVariant}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-semibold flex items-center gap-2"
        >
          <CopyIcon className="w-4 h-4" />
          Create Variant
        </button>
      </div>

      {variants.length === 0 ? (
        <p className="text-gray-400 text-sm">No variants created yet. Create one to test different versions.</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {variants.map((variant) => (
            <div key={variant.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4">
              <h4 className="font-bold text-white mb-2">{variant.name}</h4>
              <div className="space-y-2 text-sm">
                <p className="text-gray-400">
                  <span className="font-semibold">Hook:</span> {variant.hook}
                </p>
                <p className="text-gray-400">
                  <span className="font-semibold">CTA:</span> {variant.cta}
                </p>
                {variant.performance && (
                  <div className="flex gap-2 mt-2">
                    <span className="px-2 py-1 bg-blue-900/50 text-blue-300 rounded text-xs">
                      CTR: {variant.performance.predictedCTR}%
                    </span>
                    <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">
                      ROI: {variant.performance.predictedROI}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const AICreativeStudio: React.FC<AICreativeStudioProps> = ({ onCreativeGenerated }) => {
  // State
  const [productInfo, setProductInfo] = useState<ProductInfo>({
    name: '',
    description: '',
    benefits: '',
    uniqueSellingPoint: '',
    painPoints: '',
    offer: ''
  });
  const [targetAudience, setTargetAudience] = useState('');
  const [brandVoice, setBrandVoice] = useState<BrandVoice>('professional');
  const [currentCreative, setCurrentCreative] = useState<Partial<Creative>>({});

  const [isGeneratingHook, setIsGeneratingHook] = useState(false);
  const [isGeneratingCopy, setIsGeneratingCopy] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [isGeneratingVideo, setIsGeneratingVideo] = useState(false);
  const [isGeneratingCTA, setIsGeneratingCTA] = useState(false);

  const [platform, setPlatform] = useState<Platform>('feed');
  const [deviceType, setDeviceType] = useState<DeviceType>('mobile');
  const [imageAspectRatio, setImageAspectRatio] = useState<'1:1' | '16:9' | '9:16' | '4:5'>('1:1');

  // Handlers
  const handleHookSelected = (hook: GeneratedHook) => {
    setCurrentCreative((prev) => ({ ...prev, hook }));
  };

  const generateCopy = async () => {
    if (!currentCreative.hook) {
      alert('Please generate or select a hook first');
      return;
    }

    setIsGeneratingCopy(true);
    try {
      const copy = await creativeAPI.generateAdCopy(
        productInfo,
        targetAudience,
        brandVoice,
        currentCreative.hook.text
      );
      setCurrentCreative((prev) => ({ ...prev, copy }));
    } catch (error) {
      console.error('Copy generation error:', error);
      alert(`Failed to generate copy: ${error}`);
    } finally {
      setIsGeneratingCopy(false);
    }
  };

  const generateImage = async () => {
    if (!currentCreative.hook) {
      alert('Please generate a hook first');
      return;
    }

    setIsGeneratingImage(true);
    try {
      const prompt = `Create a compelling ad image for ${productInfo.name}. ${productInfo.description}. Hook: ${currentCreative.hook.text}. Style: ${brandVoice}.`;
      const image = await creativeAPI.generateImage(prompt, imageAspectRatio, productInfo);
      setCurrentCreative((prev) => ({ ...prev, image }));
    } catch (error) {
      console.error('Image generation error:', error);
      alert(`Failed to generate image: ${error}`);
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const generateVideo = async () => {
    if (!currentCreative.hook) {
      alert('Please generate a hook first');
      return;
    }

    setIsGeneratingVideo(true);
    try {
      // First, generate storyboard
      const storyboard = await creativeAPI.generateStoryboard(
        productInfo,
        currentCreative.hook.text,
        targetAudience
      );

      // Then generate video
      const prompt = `Create an engaging ${platform} video ad for ${productInfo.name}. ${productInfo.description}. Hook: ${currentCreative.hook.text}`;
      const video = await creativeAPI.generateVideo(prompt, 15, productInfo);
      video.storyboard = storyboard;

      setCurrentCreative((prev) => ({ ...prev, video }));
    } catch (error) {
      console.error('Video generation error:', error);
      alert(`Failed to generate video: ${error}`);
    } finally {
      setIsGeneratingVideo(false);
    }
  };

  const generateCTA = async () => {
    if (!currentCreative.hook) {
      alert('Please generate a hook first');
      return;
    }

    setIsGeneratingCTA(true);
    try {
      const ctas = await creativeAPI.generateCTAs(
        productInfo,
        currentCreative.hook.text,
        productInfo.offer
      );
      if (ctas.length > 0) {
        setCurrentCreative((prev) => ({ ...prev, cta: ctas[0] }));
      }
    } catch (error) {
      console.error('CTA generation error:', error);
      alert(`Failed to generate CTA: ${error}`);
    } finally {
      setIsGeneratingCTA(false);
    }
  };

  const createVariant = () => {
    if (!currentCreative.hook || !currentCreative.copy || !currentCreative.cta) {
      alert('Please generate hook, copy, and CTA first');
      return;
    }

    const variant: CreativeVariant = {
      id: `variant-${Date.now()}`,
      name: `Variant ${(currentCreative.variants?.length || 0) + 1}`,
      hook: currentCreative.hook.text,
      copy: currentCreative.copy.body,
      cta: currentCreative.cta.text,
      performance: {
        predictedCTR: Math.random() * 5 + 2,
        predictedROI: Math.random() * 3 + 1
      }
    };

    setCurrentCreative((prev) => ({
      ...prev,
      variants: [...(prev.variants || []), variant]
    }));
  };

  const exportCreative = () => {
    if (!currentCreative.hook || !currentCreative.copy) {
      alert('Please generate at least a hook and copy before exporting');
      return;
    }

    const creative: Creative = {
      id: `creative-${Date.now()}`,
      productInfo,
      targetAudience,
      brandVoice,
      hook: currentCreative.hook!,
      copy: currentCreative.copy!,
      image: currentCreative.image || null,
      video: currentCreative.video || null,
      cta: currentCreative.cta || null,
      variants: currentCreative.variants || [],
      createdAt: new Date()
    };

    onCreativeGenerated(creative);
    alert('Creative exported successfully!');
  };

  const downloadAssets = () => {
    // Download generated assets
    const data = JSON.stringify(currentCreative, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `creative-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
            <WandIcon className="w-10 h-10 text-indigo-400" />
            AI Creative Studio
          </h1>
          <p className="text-gray-400">One-click AI-powered ad creation with Vertex AI</p>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Input */}
          <div className="lg:col-span-1 space-y-6">
            {/* Product Info */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-2xl font-bold text-white mb-4">Product Info</h2>
              <ProductInfoForm productInfo={productInfo} onChange={setProductInfo} />
            </div>

            {/* Target Audience */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-2xl font-bold text-white mb-4">Target Audience</h2>
              <textarea
                value={targetAudience}
                onChange={(e) => setTargetAudience(e.target.value)}
                rows={4}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
                placeholder="Describe your ideal customer..."
              />
            </div>

            {/* Brand Voice */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h2 className="text-2xl font-bold text-white mb-4">Brand Voice</h2>
              <select
                value={brandVoice}
                onChange={(e) => setBrandVoice(e.target.value as BrandVoice)}
                className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
              >
                <option value="professional">Professional</option>
                <option value="direct">Direct</option>
                <option value="empathetic">Empathetic</option>
                <option value="authoritative">Authoritative</option>
                <option value="playful">Playful</option>
                <option value="inspirational">Inspirational</option>
              </select>
            </div>
          </div>

          {/* Middle Column - Generation */}
          <div className="lg:col-span-1 space-y-6">
            {/* Hook Generator */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <HookGenerator
                productInfo={productInfo}
                targetAudience={targetAudience}
                onHookSelected={handleHookSelected}
                isGenerating={isGeneratingHook}
                setIsGenerating={setIsGeneratingHook}
              />
            </div>

            {/* Copy Generator */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white">Ad Copy</h3>
                <button
                  onClick={generateCopy}
                  disabled={isGeneratingCopy || !currentCreative.hook}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGeneratingCopy ? (
                    <>
                      <RefreshIcon className="w-4 h-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="w-4 h-4" />
                      Generate Copy
                    </>
                  )}
                </button>
              </div>

              {currentCreative.copy && (
                <div className="space-y-3">
                  <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                    <label className="text-xs font-semibold text-gray-400">HEADLINE</label>
                    <input
                      type="text"
                      value={currentCreative.copy.headline}
                      onChange={(e) =>
                        setCurrentCreative((prev) => ({
                          ...prev,
                          copy: prev.copy ? { ...prev.copy, headline: e.target.value } : prev.copy
                        }))
                      }
                      className="w-full mt-1 px-0 py-1 bg-transparent border-none text-white font-semibold focus:outline-none"
                    />
                  </div>

                  <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                    <label className="text-xs font-semibold text-gray-400">BODY</label>
                    <textarea
                      value={currentCreative.copy.body}
                      onChange={(e) =>
                        setCurrentCreative((prev) => ({
                          ...prev,
                          copy: prev.copy ? { ...prev.copy, body: e.target.value } : prev.copy
                        }))
                      }
                      rows={4}
                      className="w-full mt-1 px-0 py-1 bg-transparent border-none text-white focus:outline-none resize-none"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* CTA Generator */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-white">Call-to-Action</h3>
                <button
                  onClick={generateCTA}
                  disabled={isGeneratingCTA || !currentCreative.hook}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGeneratingCTA ? (
                    <>
                      <RefreshIcon className="w-4 h-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <SparklesIcon className="w-4 h-4" />
                      Generate CTA
                    </>
                  )}
                </button>
              </div>

              {currentCreative.cta && (
                <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                  <input
                    type="text"
                    value={currentCreative.cta.text}
                    onChange={(e) =>
                      setCurrentCreative((prev) => ({
                        ...prev,
                        cta: prev.cta ? { ...prev.cta, text: e.target.value } : prev.cta
                      }))
                    }
                    className="w-full px-0 py-1 bg-transparent border-none text-white font-bold focus:outline-none"
                  />
                  <div className="flex gap-2 mt-2">
                    <span className="px-2 py-1 bg-indigo-900/50 text-indigo-300 rounded text-xs">
                      {currentCreative.cta.type.replace('_', ' ')}
                    </span>
                    <span className="px-2 py-1 bg-orange-900/50 text-orange-300 rounded text-xs">
                      Urgency: {currentCreative.cta.urgencyLevel}/10
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Visual Generation */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-4">Visuals</h3>

              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-300 mb-2">Aspect Ratio</label>
                <select
                  value={imageAspectRatio}
                  onChange={(e) => setImageAspectRatio(e.target.value as any)}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white focus:border-indigo-500 focus:outline-none"
                >
                  <option value="1:1">1:1 (Square)</option>
                  <option value="16:9">16:9 (Landscape)</option>
                  <option value="9:16">9:16 (Portrait)</option>
                  <option value="4:5">4:5 (Instagram)</option>
                </select>
              </div>

              <div className="space-y-2">
                <button
                  onClick={generateImage}
                  disabled={isGeneratingImage || !currentCreative.hook}
                  className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGeneratingImage ? (
                    <>
                      <RefreshIcon className="w-4 h-4 animate-spin" />
                      Generating Image...
                    </>
                  ) : (
                    <>
                      <ImageIcon className="w-4 h-4" />
                      Generate Image (Imagen)
                    </>
                  )}
                </button>

                <button
                  onClick={generateVideo}
                  disabled={isGeneratingVideo || !currentCreative.hook}
                  className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isGeneratingVideo ? (
                    <>
                      <RefreshIcon className="w-4 h-4 animate-spin" />
                      Generating Video...
                    </>
                  ) : (
                    <>
                      <VideoIcon className="w-4 h-4" />
                      Generate Video (Veo)
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Right Column - Preview & Export */}
          <div className="lg:col-span-1 space-y-6">
            {/* Platform & Device Toggle */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-4">Preview Settings</h3>

              <div className="mb-4">
                <label className="block text-sm font-semibold text-gray-300 mb-2">Platform</label>
                <div className="grid grid-cols-3 gap-2">
                  {(['feed', 'stories', 'reels'] as Platform[]).map((p) => (
                    <button
                      key={p}
                      onClick={() => setPlatform(p)}
                      className={`px-3 py-2 rounded-lg font-semibold text-sm ${
                        platform === p
                          ? 'bg-indigo-600 text-white'
                          : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                      }`}
                    >
                      {p}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-300 mb-2">Device</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setDeviceType('mobile')}
                    className={`px-3 py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 ${
                      deviceType === 'mobile'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    <MobileIcon className="w-4 h-4" />
                    Mobile
                  </button>
                  <button
                    onClick={() => setDeviceType('desktop')}
                    className={`px-3 py-2 rounded-lg font-semibold text-sm flex items-center justify-center gap-2 ${
                      deviceType === 'desktop'
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    <MonitorIcon className="w-4 h-4" />
                    Desktop
                  </button>
                </div>
              </div>
            </div>

            {/* Preview */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <EyeIcon className="w-5 h-5" />
                Live Preview
              </h3>
              <PreviewPanel creative={currentCreative} platform={platform} deviceType={deviceType} />
            </div>

            {/* Variant Manager */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <VariantManager creative={currentCreative} onCreateVariant={createVariant} />
            </div>

            {/* Export Actions */}
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-xl font-bold text-white mb-4">Export</h3>
              <div className="space-y-2">
                <button
                  onClick={exportCreative}
                  className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold flex items-center justify-center gap-2"
                >
                  <CheckIcon className="w-5 h-5" />
                  Send to Campaign Builder
                </button>

                <button
                  onClick={downloadAssets}
                  className="w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-bold flex items-center justify-center gap-2"
                >
                  <DownloadIcon className="w-5 h-5" />
                  Download Assets
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AICreativeStudio;
