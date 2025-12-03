<<<<<<< HEAD
import React, { useState, useCallback } from 'react';
import { AnimatePresence } from 'framer-motion';
import { useCampaignStore } from '../stores/campaignStore';
import { WizardProgress, SetupStep, CreativeStep, ReviewStep } from './campaign';

interface CampaignBuilderProps {
  campaignId?: string;
  onSave?: () => void;
  onPublish?: () => void;
}

export const CampaignBuilder: React.FC<CampaignBuilderProps> = ({
  campaignId,
  onSave,
  onPublish,
}) => {
  const {
    wizardStep,
    wizardData,
    setWizardStep,
    updateWizardData,
    resetWizard,
    addCampaign,
  } = useCampaignStore();

  const [isLaunching, setIsLaunching] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Setup step data
  const [setupData, setSetupData] = useState({
    name: wizardData.name || '',
    objective: wizardData.objective || '',
    budget: wizardData.budget || 0,
    platforms: wizardData.platforms || [],
    targetAudience: '',
  });

  // Creative step data
  const [creativeData, setCreativeData] = useState({
    uploadedFiles: [] as File[],
    style: wizardData.creativeSettings?.style || '',
    scriptTemplate: '',
    hookStyle: '',
    variants: 1,
    selectedAvatar: '',
  });

  const handleSetupUpdate = useCallback(
    (data: Partial<typeof setupData>) => {
      setSetupData((prev) => ({ ...prev, ...data }));
      updateWizardData({
        name: data.name !== undefined ? data.name : setupData.name,
        objective:
          data.objective !== undefined ? data.objective : setupData.objective,
        budget: data.budget !== undefined ? data.budget : setupData.budget,
        platforms:
          data.platforms !== undefined ? data.platforms : setupData.platforms,
      });
    },
    [setupData, updateWizardData]
  );

  const handleCreativeUpdate = useCallback(
    (data: Partial<typeof creativeData>) => {
      setCreativeData((prev) => ({ ...prev, ...data }));
      updateWizardData({
        creativeSettings: {
          style: data.style || creativeData.style,
          tone: data.hookStyle || creativeData.hookStyle,
        },
      });
    },
    [creativeData, updateWizardData]
  );

  const handleStepChange = useCallback(
    (step: number) => {
      // Only allow going back, not forward
      if (step < wizardStep) {
        setWizardStep(step);
      }
    },
    [wizardStep, setWizardStep]
  );

  const handleNext = useCallback(() => {
    if (wizardStep < 3) {
      setWizardStep(wizardStep + 1);
    }
  }, [wizardStep, setWizardStep]);

  const handleBack = useCallback(() => {
    if (wizardStep > 1) {
      setWizardStep(wizardStep - 1);
    }
  }, [wizardStep, setWizardStep]);

  const handleSaveDraft = useCallback(async () => {
    setIsSaving(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const draftCampaign = {
        id: campaignId || `draft_${Date.now()}`,
        name: setupData.name || 'Untitled Campaign',
        status: 'draft' as const,
        objective: setupData.objective,
        budget: setupData.budget,
        platforms: setupData.platforms,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      addCampaign(draftCampaign);
      onSave?.();

      // TODO: Show success toast notification
    } catch (error) {
      console.error('Failed to save draft:', error);
    } finally {
      setIsSaving(false);
    }
  }, [setupData, campaignId, addCampaign, onSave]);

  const handleLaunch = useCallback(async () => {
    setIsLaunching(true);
    try {
      // Simulate API call for campaign launch
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const newCampaign = {
        id: campaignId || `campaign_${Date.now()}`,
        name: setupData.name || 'Untitled Campaign',
        status: 'active' as const,
        objective: setupData.objective,
        budget: setupData.budget,
        platforms: setupData.platforms,
        createdAt: new Date(),
        updatedAt: new Date(),
        metrics: {
          impressions: 0,
          clicks: 0,
          conversions: 0,
          spend: 0,
          roas: 0,
        },
      };

      addCampaign(newCampaign);
      resetWizard();
      onPublish?.();

      // TODO: Show success toast notification
    } catch (error) {
      console.error('Failed to launch campaign:', error);
    } finally {
      setIsLaunching(false);
    }
  }, [setupData, campaignId, addCampaign, resetWizard, onPublish]);

  return (
    <div className="min-h-screen bg-zinc-900 text-white">
      <div className="max-w-5xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">
              {campaignId ? 'Edit Campaign' : 'Create New Campaign'}
            </h1>
            <p className="text-zinc-400 mt-1">
              {wizardStep === 1
                ? 'Set up your campaign basics'
                : wizardStep === 2
                ? 'Configure your creative settings'
                : 'Review and launch your campaign'}
            </p>
          </div>
          <button
            onClick={handleSaveDraft}
            disabled={isSaving || !setupData.name}
            className="px-4 py-2 border border-zinc-600 text-zinc-300 rounded-lg hover:bg-zinc-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Save Draft'}
          </button>
        </div>

        {/* Wizard Progress */}
        <WizardProgress currentStep={wizardStep} onStepClick={handleStepChange} />

        {/* Step Content */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 sm:p-8 mb-6">
          <AnimatePresence mode="wait">
            {wizardStep === 1 && (
              <SetupStep
                key="setup"
                data={setupData}
                onUpdate={handleSetupUpdate}
                onNext={handleNext}
              />
            )}

            {wizardStep === 2 && (
              <CreativeStep
                key="creative"
                data={creativeData}
                onUpdate={handleCreativeUpdate}
                onNext={handleNext}
                onBack={handleBack}
              />
            )}

            {wizardStep === 3 && (
              <ReviewStep
                key="review"
                setupData={setupData}
                creativeData={creativeData}
                onEdit={handleStepChange}
                onBack={handleBack}
                onLaunch={handleLaunch}
                isLaunching={isLaunching}
              />
            )}
          </AnimatePresence>
        </div>

        {/* Progress Indicator */}
        <div className="text-center text-sm text-zinc-500">
          Step {wizardStep} of 3
=======
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  SparklesIcon,
  VideoIcon,
  ImageIcon,
  CheckIcon,
  UploadIcon,
  CalendarIcon,
  TargetIcon,
  DollarSignIcon,
  BarChartIcon,
  SendIcon,
  SaveIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  TemplateIcon,
  XIcon,
  TrendingUpIcon,
  UsersIcon,
  EyeIcon,
} from './icons';
import api from '../services/api';
import { formatErrorMessage } from '../utils/error';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface Campaign {
  id?: string;
  name: string;
  objective: CampaignObjective;
  creatives: CampaignCreative[];
  targeting: TargetingConfig;
  budget: BudgetConfig;
  schedule: ScheduleConfig;
  status: 'draft' | 'pending' | 'active' | 'paused' | 'completed';
  predictions?: CampaignPredictions;
  abTestConfig?: ABTestConfig;
  createdAt?: Date;
  updatedAt?: Date;
}

type CampaignObjective =
  | 'traffic'
  | 'leads'
  | 'sales'
  | 'brand_awareness'
  | 'engagement'
  | 'app_installs'
  | 'video_views';

interface CampaignCreative {
  id: string;
  type: 'video' | 'image';
  url?: string;
  file?: File;
  thumbnail?: string;
  headline: string;
  body: string;
  cta: string;
  assetId?: string;
}

interface TargetingConfig {
  locations: string[];
  ageMin: number;
  ageMax: number;
  genders: ('male' | 'female' | 'all')[];
  interests: string[];
  behaviors: string[];
  customAudiences: string[];
  lookalikes: string[];
  detailedTargeting: DetailedTargeting;
}

interface DetailedTargeting {
  demographics: string[];
  interests: string[];
  behaviors: string[];
}

interface BudgetConfig {
  type: 'daily' | 'lifetime';
  amount: number;
  bidStrategy: 'lowest_cost' | 'cost_cap' | 'bid_cap';
  bidAmount?: number;
  spendingLimit?: number;
}

interface ScheduleConfig {
  startDate: string;
  endDate?: string;
  timeZone: string;
  dayParting?: DayPartingConfig[];
}

interface DayPartingConfig {
  days: number[];
  hours: number[];
}

interface CampaignPredictions {
  estimatedReach: number;
  estimatedImpressions: number;
  estimatedClicks: number;
  estimatedCTR: number;
  estimatedCPA: number;
  estimatedROAS: number;
  confidence: number;
  audienceSize: number;
  competitionLevel: 'low' | 'medium' | 'high';
  recommendations: string[];
}

interface ABTestConfig {
  enabled: boolean;
  splitPercentage: number;
  metric: 'ctr' | 'cpa' | 'roas' | 'engagement';
  duration: number;
  minimumSampleSize: number;
}

interface CampaignTemplate {
  id: string;
  name: string;
  objective: CampaignObjective;
  targeting: Partial<TargetingConfig>;
  budget: Partial<BudgetConfig>;
  description: string;
}

interface ValidationError {
  step: number;
  field: string;
  message: string;
}

interface CampaignBuilderProps {
  onComplete: (campaign: Campaign) => void;
  initialCampaign?: Partial<Campaign>;
}

// ============================================================================
// CAMPAIGN BUILDER COMPONENT
// ============================================================================

const CampaignBuilder: React.FC<CampaignBuilderProps> = ({
  onComplete,
  initialCampaign
}) => {
  // Step management
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  // Campaign state
  const [campaign, setCampaign] = useState<Campaign>({
    name: '',
    objective: 'traffic',
    creatives: [],
    targeting: {
      locations: ['United States'],
      ageMin: 18,
      ageMax: 65,
      genders: ['all'],
      interests: [],
      behaviors: [],
      customAudiences: [],
      lookalikes: [],
      detailedTargeting: {
        demographics: [],
        interests: [],
        behaviors: [],
      },
    },
    budget: {
      type: 'daily',
      amount: 50,
      bidStrategy: 'lowest_cost',
    },
    schedule: {
      startDate: new Date().toISOString().split('T')[0],
      timeZone: 'America/New_York',
    },
    status: 'draft',
    ...initialCampaign,
  });

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [predictions, setPredictions] = useState<CampaignPredictions | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [selectedPlacement, setSelectedPlacement] = useState<'feed' | 'stories' | 'reels'>('feed');
  const [availableAssets, setAvailableAssets] = useState<any[]>([]);
  const [showAssetLibrary, setShowAssetLibrary] = useState(false);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const predictionTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Templates
  const templates: CampaignTemplate[] = [
    {
      id: 'ecom-sales',
      name: 'E-commerce Sales',
      objective: 'sales',
      targeting: {
        interests: ['Online shopping', 'E-commerce'],
        ageMin: 25,
        ageMax: 54,
      },
      budget: {
        type: 'daily',
        amount: 100,
        bidStrategy: 'lowest_cost',
      },
      description: 'Optimized for driving sales in e-commerce stores',
    },
    {
      id: 'lead-gen',
      name: 'Lead Generation',
      objective: 'leads',
      targeting: {
        interests: ['Business', 'Entrepreneurship'],
        ageMin: 30,
        ageMax: 60,
      },
      budget: {
        type: 'daily',
        amount: 75,
        bidStrategy: 'cost_cap',
      },
      description: 'Generate high-quality leads for B2B services',
    },
    {
      id: 'brand-awareness',
      name: 'Brand Awareness',
      objective: 'brand_awareness',
      targeting: {
        ageMin: 18,
        ageMax: 45,
      },
      budget: {
        type: 'daily',
        amount: 150,
        bidStrategy: 'lowest_cost',
      },
      description: 'Maximize reach and brand visibility',
    },
    {
      id: 'video-views',
      name: 'Video Engagement',
      objective: 'video_views',
      targeting: {
        interests: ['Entertainment', 'Video content'],
        ageMin: 18,
        ageMax: 35,
      },
      budget: {
        type: 'daily',
        amount: 60,
        bidStrategy: 'lowest_cost',
      },
      description: 'Maximize video views and engagement',
    },
  ];

  // ============================================================================
  // EFFECTS
  // ============================================================================

  useEffect(() => {
    loadAvailableAssets();
  }, []);

  // Real-time predictions when targeting or budget changes
  useEffect(() => {
    if (currentStep >= 3) {
      if (predictionTimerRef.current) {
        clearTimeout(predictionTimerRef.current);
      }
      predictionTimerRef.current = setTimeout(() => {
        fetchPredictions();
      }, 1000);
    }
    return () => {
      if (predictionTimerRef.current) {
        clearTimeout(predictionTimerRef.current);
      }
    };
  }, [campaign.targeting, campaign.budget, currentStep]);

  // ============================================================================
  // API CALLS
  // ============================================================================

  const loadAvailableAssets = async () => {
    try {
      const response = await api.get('/assets', { params: { limit: 50 } });
      setAvailableAssets(response.data || []);
    } catch (err) {
      console.error('Failed to load assets:', err);
    }
  };

  const fetchPredictions = async () => {
    try {
      setIsLoading(true);
      const response = await api.post('/campaigns/predict', {
        objective: campaign.objective,
        targeting: campaign.targeting,
        budget: campaign.budget,
        schedule: campaign.schedule,
      });
      setPredictions(response.data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch predictions:', err);
      setError('Unable to fetch predictions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const saveCampaignDraft = async () => {
    try {
      setIsLoading(true);
      const response = await api.post('/campaigns/draft', {
        ...campaign,
        status: 'draft',
      });
      setError(null);
      return response.data;
    } catch (err) {
      const errorMsg = formatErrorMessage(err);
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const launchCampaign = async () => {
    try {
      setIsLoading(true);

      // Upload creatives first
      const uploadedCreatives = await Promise.all(
        campaign.creatives.map(async (creative) => {
          if (creative.file) {
            const formData = new FormData();
            formData.append('file', creative.file);
            formData.append('headline', creative.headline);
            formData.append('body', creative.body);
            formData.append('cta', creative.cta);

            const response = await api.post('/creatives/upload', formData, {
              headers: { 'Content-Type': 'multipart/form-data' },
            });
            return { ...creative, url: response.data.url, assetId: response.data.id };
          }
          return creative;
        })
      );

      // Create campaign with uploaded creatives
      const response = await api.post('/campaigns/launch', {
        ...campaign,
        creatives: uploadedCreatives,
        status: 'pending',
      });

      setError(null);
      onComplete(response.data);
    } catch (err) {
      const errorMsg = formatErrorMessage(err);
      setError(errorMsg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  // ============================================================================
  // VALIDATION
  // ============================================================================

  const validateStep = (step: number): boolean => {
    const errors: ValidationError[] = [];

    switch (step) {
      case 0: // Objective
        if (!campaign.name.trim()) {
          errors.push({ step, field: 'name', message: 'Campaign name is required' });
        }
        if (campaign.name.length < 3) {
          errors.push({ step, field: 'name', message: 'Campaign name must be at least 3 characters' });
        }
        break;

      case 1: // Creatives
        if (campaign.creatives.length === 0) {
          errors.push({ step, field: 'creatives', message: 'At least one creative is required' });
        }
        campaign.creatives.forEach((creative, idx) => {
          if (!creative.headline.trim()) {
            errors.push({ step, field: `creative-${idx}-headline`, message: `Creative ${idx + 1} headline is required` });
          }
          if (!creative.body.trim()) {
            errors.push({ step, field: `creative-${idx}-body`, message: `Creative ${idx + 1} body is required` });
          }
          if (!creative.cta.trim()) {
            errors.push({ step, field: `creative-${idx}-cta`, message: `Creative ${idx + 1} CTA is required` });
          }
        });
        break;

      case 2: // Targeting
        if (campaign.targeting.locations.length === 0) {
          errors.push({ step, field: 'locations', message: 'At least one location is required' });
        }
        if (campaign.targeting.ageMin < 13 || campaign.targeting.ageMin > campaign.targeting.ageMax) {
          errors.push({ step, field: 'age', message: 'Invalid age range' });
        }
        if (
          campaign.targeting.interests.length === 0 &&
          campaign.targeting.behaviors.length === 0 &&
          campaign.targeting.customAudiences.length === 0
        ) {
          errors.push({ step, field: 'targeting', message: 'Add at least one targeting parameter' });
        }
        break;

      case 3: // Budget
        if (campaign.budget.amount < 1) {
          errors.push({ step, field: 'budget', message: 'Budget must be at least $1' });
        }
        if (campaign.budget.type === 'daily' && campaign.budget.amount < 5) {
          errors.push({ step, field: 'budget', message: 'Daily budget must be at least $5' });
        }
        if (campaign.budget.bidStrategy !== 'lowest_cost' && !campaign.budget.bidAmount) {
          errors.push({ step, field: 'bidAmount', message: 'Bid amount is required for this strategy' });
        }
        if (!campaign.schedule.startDate) {
          errors.push({ step, field: 'startDate', message: 'Start date is required' });
        }
        break;

      case 4: // Review
        // No additional validation needed
        break;
    }

    setValidationErrors(errors);
    return errors.length === 0;
  };

  // ============================================================================
  // HANDLERS
  // ============================================================================

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCompletedSteps([...new Set([...completedSteps, currentStep])]);
      setCurrentStep(currentStep + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    setCurrentStep(currentStep - 1);
    setError(null);
  };

  const handleStepClick = (step: number) => {
    if (completedSteps.includes(step - 1) || step <= Math.max(...completedSteps, 0)) {
      setCurrentStep(step);
    }
  };

  const handleTemplateSelect = (template: CampaignTemplate) => {
    setCampaign({
      ...campaign,
      name: template.name,
      objective: template.objective,
      targeting: { ...campaign.targeting, ...template.targeting },
      budget: { ...campaign.budget, ...template.budget },
    });
    setShowTemplates(false);
  };

  const handleFileSelect = async (files: FileList | null) => {
    if (!files || files.length === 0) return;

    const newCreatives: CampaignCreative[] = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const type = file.type.startsWith('video/') ? 'video' : 'image';

      // Create thumbnail
      const thumbnail = await createThumbnail(file);

      newCreatives.push({
        id: `creative-${Date.now()}-${i}`,
        type,
        file,
        thumbnail,
        headline: '',
        body: '',
        cta: 'Learn More',
      });
    }

    setCampaign({
      ...campaign,
      creatives: [...campaign.creatives, ...newCreatives],
    });
  };

  const createThumbnail = (file: File): Promise<string> => {
    return new Promise((resolve) => {
      if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target?.result as string);
        reader.readAsDataURL(file);
      } else if (file.type.startsWith('video/')) {
        const video = document.createElement('video');
        video.preload = 'metadata';
        video.onloadedmetadata = () => {
          video.currentTime = 1;
        };
        video.onseeked = () => {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.getContext('2d')?.drawImage(video, 0, 0);
          resolve(canvas.toDataURL());
        };
        video.src = URL.createObjectURL(file);
      }
    });
  };

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    handleFileSelect(e.dataTransfer.files);
  }, [campaign.creatives]);

  const handleRemoveCreative = (id: string) => {
    setCampaign({
      ...campaign,
      creatives: campaign.creatives.filter(c => c.id !== id),
    });
  };

  const handleUpdateCreative = (id: string, updates: Partial<CampaignCreative>) => {
    setCampaign({
      ...campaign,
      creatives: campaign.creatives.map(c =>
        c.id === id ? { ...c, ...updates } : c
      ),
    });
  };

  const handleAddAssetFromLibrary = (asset: any) => {
    const creative: CampaignCreative = {
      id: `asset-${asset.id}`,
      type: asset.type || 'video',
      assetId: asset.id,
      url: asset.url,
      thumbnail: asset.thumbnail,
      headline: '',
      body: '',
      cta: 'Learn More',
    };
    setCampaign({
      ...campaign,
      creatives: [...campaign.creatives, creative],
    });
    setShowAssetLibrary(false);
  };

  const handleSaveDraft = async () => {
    try {
      await saveCampaignDraft();
      alert('Draft saved successfully!');
    } catch (err) {
      // Error already handled in saveCampaignDraft
    }
  };

  const handleLaunch = async () => {
    if (!validateStep(currentStep)) return;

    const confirmed = window.confirm(
      'Are you sure you want to launch this campaign? This will publish it to Meta.'
    );

    if (confirmed) {
      try {
        await launchCampaign();
      } catch (err) {
        // Error already handled in launchCampaign
      }
    }
  };

  // ============================================================================
  // STEP COMPONENTS
  // ============================================================================

  const renderStepIndicator = () => {
    const steps = [
      { label: 'Objective', icon: TargetIcon },
      { label: 'Creative', icon: VideoIcon },
      { label: 'Targeting', icon: UsersIcon },
      { label: 'Budget & Schedule', icon: DollarSignIcon },
      { label: 'Predictions', icon: TrendingUpIcon },
      { label: 'Review & Launch', icon: SendIcon },
    ];

    return (
      <div className="flex items-center justify-between mb-8">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isActive = idx === currentStep;
          const isCompleted = completedSteps.includes(idx);
          const isAccessible = idx === 0 || completedSteps.includes(idx - 1);

          return (
            <React.Fragment key={idx}>
              <div
                className={`flex flex-col items-center cursor-pointer transition-all ${
                  isAccessible ? 'opacity-100' : 'opacity-40 cursor-not-allowed'
                }`}
                onClick={() => isAccessible && handleStepClick(idx)}
              >
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                    isActive
                      ? 'bg-indigo-600 text-white scale-110'
                      : isCompleted
                      ? 'bg-green-600 text-white'
                      : 'bg-gray-700 text-gray-400'
                  }`}
                >
                  {isCompleted ? (
                    <CheckIcon className="w-6 h-6" />
                  ) : (
                    <Icon className="w-6 h-6" />
                  )}
                </div>
                <span
                  className={`text-xs mt-2 font-medium ${
                    isActive ? 'text-indigo-400' : isCompleted ? 'text-green-400' : 'text-gray-500'
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <div
                  className={`flex-1 h-1 mx-2 rounded transition-all ${
                    isCompleted ? 'bg-green-600' : 'bg-gray-700'
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    );
  };

  const renderStep0 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Choose Campaign Objective</h2>
        <p className="text-gray-400">What's your main goal for this campaign?</p>
      </div>

      <div className="flex justify-end mb-4">
        <button
          onClick={() => setShowTemplates(!showTemplates)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <TemplateIcon className="w-5 h-5" />
          Use Template
        </button>
      </div>

      {showTemplates && (
        <div className="grid md:grid-cols-2 gap-4 mb-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          {templates.map(template => (
            <div
              key={template.id}
              onClick={() => handleTemplateSelect(template)}
              className="p-4 bg-gray-900/50 rounded-lg border border-gray-700 hover:border-indigo-500 cursor-pointer transition-all"
            >
              <h3 className="font-bold text-lg mb-2">{template.name}</h3>
              <p className="text-sm text-gray-400 mb-3">{template.description}</p>
              <div className="flex gap-2 text-xs">
                <span className="px-2 py-1 bg-indigo-900/50 text-indigo-300 rounded">
                  {template.objective}
                </span>
                <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded">
                  ${template.budget?.amount}/day
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div>
        <label className="block text-sm font-semibold mb-2">Campaign Name</label>
        <input
          type="text"
          value={campaign.name}
          onChange={(e) => setCampaign({ ...campaign, name: e.target.value })}
          placeholder="e.g., Holiday Sale 2024"
          className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { value: 'traffic', label: 'Website Traffic', icon: '🌐' },
          { value: 'leads', label: 'Lead Generation', icon: '📋' },
          { value: 'sales', label: 'Sales/Conversions', icon: '💰' },
          { value: 'brand_awareness', label: 'Brand Awareness', icon: '📢' },
          { value: 'engagement', label: 'Engagement', icon: '❤️' },
          { value: 'app_installs', label: 'App Installs', icon: '📱' },
          { value: 'video_views', label: 'Video Views', icon: '🎥' },
        ].map(objective => (
          <button
            key={objective.value}
            onClick={() => setCampaign({ ...campaign, objective: objective.value as CampaignObjective })}
            className={`p-4 rounded-lg border-2 transition-all ${
              campaign.objective === objective.value
                ? 'border-indigo-500 bg-indigo-900/30'
                : 'border-gray-700 bg-gray-800/50 hover:border-gray-600'
            }`}
          >
            <div className="text-3xl mb-2">{objective.icon}</div>
            <div className="text-sm font-semibold">{objective.label}</div>
          </button>
        ))}
      </div>
    </div>
  );

  const renderStep1 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Select or Upload Creative</h2>
        <p className="text-gray-400">Add videos or images for your ad campaign</p>
      </div>

      <div className="flex gap-4 mb-4">
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
        >
          <UploadIcon className="w-5 h-5" />
          Upload Files
        </button>
        <button
          onClick={() => setShowAssetLibrary(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <VideoIcon className="w-5 h-5" />
          Select from Library
        </button>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="video/*,image/*"
        onChange={(e) => handleFileSelect(e.target.files)}
        className="hidden"
      />

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all ${
          isDragging
            ? 'border-indigo-500 bg-indigo-900/20'
            : 'border-gray-700 bg-gray-900/30'
        }`}
      >
        <UploadIcon className="w-12 h-12 mx-auto mb-4 text-gray-500" />
        <p className="text-lg font-semibold mb-2">Drag & drop files here</p>
        <p className="text-sm text-gray-400">or click "Upload Files" button above</p>
      </div>

      {campaign.creatives.length > 0 && (
        <div className="space-y-4">
          {campaign.creatives.map(creative => (
            <div
              key={creative.id}
              className="bg-gray-800/50 border border-gray-700 rounded-lg p-4"
            >
              <div className="flex gap-4">
                <div className="w-32 h-32 bg-gray-900 rounded-lg overflow-hidden flex-shrink-0">
                  {creative.thumbnail ? (
                    <img
                      src={creative.thumbnail}
                      alt="Thumbnail"
                      className="w-full h-full object-cover"
                    />
                  ) : creative.url ? (
                    <img
                      src={creative.url}
                      alt="Asset"
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <VideoIcon className="w-12 h-12 text-gray-600" />
                    </div>
                  )}
                </div>
                <div className="flex-1 space-y-3">
                  <div>
                    <label className="text-xs font-semibold text-gray-400">Headline</label>
                    <input
                      type="text"
                      value={creative.headline}
                      onChange={(e) => handleUpdateCreative(creative.id, { headline: e.target.value })}
                      placeholder="Enter headline..."
                      className="w-full mt-1 p-2 bg-gray-900 border border-gray-600 rounded focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-gray-400">Body Text</label>
                    <textarea
                      value={creative.body}
                      onChange={(e) => handleUpdateCreative(creative.id, { body: e.target.value })}
                      placeholder="Enter body text..."
                      rows={2}
                      className="w-full mt-1 p-2 bg-gray-900 border border-gray-600 rounded focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <label className="text-xs font-semibold text-gray-400">Call-to-Action</label>
                      <select
                        value={creative.cta}
                        onChange={(e) => handleUpdateCreative(creative.id, { cta: e.target.value })}
                        className="w-full mt-1 p-2 bg-gray-900 border border-gray-600 rounded focus:outline-none focus:border-indigo-500"
                      >
                        <option>Learn More</option>
                        <option>Shop Now</option>
                        <option>Sign Up</option>
                        <option>Download</option>
                        <option>Get Quote</option>
                        <option>Contact Us</option>
                        <option>Apply Now</option>
                      </select>
                    </div>
                    <button
                      onClick={() => handleRemoveCreative(creative.id)}
                      className="mt-6 px-4 py-2 bg-red-900/50 hover:bg-red-800/50 rounded transition-colors"
                    >
                      <XIcon className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showAssetLibrary && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-lg w-full max-w-4xl max-h-[80vh] flex flex-col">
            <div className="p-4 border-b border-gray-700 flex justify-between items-center">
              <h3 className="text-xl font-bold">Asset Library</h3>
              <button
                onClick={() => setShowAssetLibrary(false)}
                className="text-gray-400 hover:text-white"
              >
                <XIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto">
              <div className="grid grid-cols-3 gap-4">
                {availableAssets.map(asset => (
                  <div
                    key={asset.id}
                    onClick={() => handleAddAssetFromLibrary(asset)}
                    className="cursor-pointer bg-gray-900/50 rounded-lg overflow-hidden hover:ring-2 hover:ring-indigo-500 transition-all"
                  >
                    <div className="aspect-video bg-gray-700">
                      {asset.thumbnail && (
                        <img
                          src={asset.thumbnail}
                          alt={asset.name}
                          className="w-full h-full object-cover"
                        />
                      )}
                    </div>
                    <div className="p-2">
                      <p className="text-sm font-semibold truncate">{asset.name || 'Untitled'}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Define Targeting</h2>
        <p className="text-gray-400">Who should see your ads?</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold mb-2">Locations</label>
          <input
            type="text"
            value={campaign.targeting.locations.join(', ')}
            onChange={(e) => setCampaign({
              ...campaign,
              targeting: {
                ...campaign.targeting,
                locations: e.target.value.split(',').map(l => l.trim()),
              },
            })}
            placeholder="e.g., United States, Canada"
            className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">Age Range</label>
          <div className="flex gap-2 items-center">
            <input
              type="number"
              min="13"
              max="65"
              value={campaign.targeting.ageMin}
              onChange={(e) => setCampaign({
                ...campaign,
                targeting: { ...campaign.targeting, ageMin: parseInt(e.target.value) },
              })}
              className="w-20 p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
            />
            <span className="text-gray-400">to</span>
            <input
              type="number"
              min="13"
              max="65"
              value={campaign.targeting.ageMax}
              onChange={(e) => setCampaign({
                ...campaign,
                targeting: { ...campaign.targeting, ageMax: parseInt(e.target.value) },
              })}
              className="w-20 p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">Gender</label>
          <div className="flex gap-2">
            {['all', 'male', 'female'].map(gender => (
              <button
                key={gender}
                onClick={() => setCampaign({
                  ...campaign,
                  targeting: { ...campaign.targeting, genders: [gender as any] },
                })}
                className={`flex-1 p-3 rounded-lg border-2 transition-all capitalize ${
                  campaign.targeting.genders.includes(gender as any)
                    ? 'border-indigo-500 bg-indigo-900/30'
                    : 'border-gray-700 bg-gray-800/50'
                }`}
              >
                {gender}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">Interests</label>
          <input
            type="text"
            value={campaign.targeting.interests.join(', ')}
            onChange={(e) => setCampaign({
              ...campaign,
              targeting: {
                ...campaign.targeting,
                interests: e.target.value.split(',').map(i => i.trim()).filter(Boolean),
              },
            })}
            placeholder="e.g., Fitness, Technology, Travel"
            className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">Behaviors</label>
          <input
            type="text"
            value={campaign.targeting.behaviors.join(', ')}
            onChange={(e) => setCampaign({
              ...campaign,
              targeting: {
                ...campaign.targeting,
                behaviors: e.target.value.split(',').map(b => b.trim()).filter(Boolean),
              },
            })}
            placeholder="e.g., Frequent shoppers, Early adopters"
            className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">Custom Audiences</label>
          <input
            type="text"
            value={campaign.targeting.customAudiences.join(', ')}
            onChange={(e) => setCampaign({
              ...campaign,
              targeting: {
                ...campaign.targeting,
                customAudiences: e.target.value.split(',').map(a => a.trim()).filter(Boolean),
              },
            })}
            placeholder="e.g., Website visitors, Email subscribers"
            className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Set Budget & Schedule</h2>
        <p className="text-gray-400">How much do you want to spend and when?</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-semibold mb-2">Budget Type</label>
          <div className="flex gap-2">
            {['daily', 'lifetime'].map(type => (
              <button
                key={type}
                onClick={() => setCampaign({
                  ...campaign,
                  budget: { ...campaign.budget, type: type as any },
                })}
                className={`flex-1 p-3 rounded-lg border-2 transition-all capitalize ${
                  campaign.budget.type === type
                    ? 'border-indigo-500 bg-indigo-900/30'
                    : 'border-gray-700 bg-gray-800/50'
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">
            {campaign.budget.type === 'daily' ? 'Daily Budget' : 'Lifetime Budget'}
          </label>
          <div className="relative">
            <span className="absolute left-3 top-3 text-gray-400">$</span>
            <input
              type="number"
              min="1"
              step="1"
              value={campaign.budget.amount}
              onChange={(e) => setCampaign({
                ...campaign,
                budget: { ...campaign.budget, amount: parseFloat(e.target.value) },
              })}
              className="w-full pl-8 p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="md:col-span-2">
          <label className="block text-sm font-semibold mb-2">Bid Strategy</label>
          <select
            value={campaign.budget.bidStrategy}
            onChange={(e) => setCampaign({
              ...campaign,
              budget: { ...campaign.budget, bidStrategy: e.target.value as any },
            })}
            className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
          >
            <option value="lowest_cost">Lowest Cost (Recommended)</option>
            <option value="cost_cap">Cost Cap</option>
            <option value="bid_cap">Bid Cap</option>
          </select>
        </div>

        {campaign.budget.bidStrategy !== 'lowest_cost' && (
          <div>
            <label className="block text-sm font-semibold mb-2">
              {campaign.budget.bidStrategy === 'cost_cap' ? 'Cost Cap' : 'Bid Cap'}
            </label>
            <div className="relative">
              <span className="absolute left-3 top-3 text-gray-400">$</span>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={campaign.budget.bidAmount || ''}
                onChange={(e) => setCampaign({
                  ...campaign,
                  budget: { ...campaign.budget, bidAmount: parseFloat(e.target.value) },
                })}
                className="w-full pl-8 p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-semibold mb-2">Start Date</label>
          <input
            type="date"
            value={campaign.schedule.startDate}
            onChange={(e) => setCampaign({
              ...campaign,
              schedule: { ...campaign.schedule, startDate: e.target.value },
            })}
            className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold mb-2">End Date (Optional)</label>
          <input
            type="date"
            value={campaign.schedule.endDate || ''}
            onChange={(e) => setCampaign({
              ...campaign,
              schedule: { ...campaign.schedule, endDate: e.target.value || undefined },
            })}
            className="w-full p-3 bg-gray-900/70 border border-gray-600 rounded-lg focus:outline-none focus:border-indigo-500"
          />
        </div>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">AI Predictions</h2>
        <p className="text-gray-400">See how your campaign is expected to perform</p>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500"></div>
        </div>
      ) : predictions ? (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <UsersIcon className="w-5 h-5 text-indigo-400" />
                <span className="text-sm text-gray-400">Estimated Reach</span>
              </div>
              <p className="text-2xl font-bold">{predictions.estimatedReach.toLocaleString()}</p>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <EyeIcon className="w-5 h-5 text-blue-400" />
                <span className="text-sm text-gray-400">Impressions</span>
              </div>
              <p className="text-2xl font-bold">{predictions.estimatedImpressions.toLocaleString()}</p>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <BarChartIcon className="w-5 h-5 text-green-400" />
                <span className="text-sm text-gray-400">CTR</span>
              </div>
              <p className="text-2xl font-bold">{(predictions.estimatedCTR * 100).toFixed(2)}%</p>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUpIcon className="w-5 h-5 text-purple-400" />
                <span className="text-sm text-gray-400">ROAS</span>
              </div>
              <p className="text-2xl font-bold">{predictions.estimatedROAS.toFixed(2)}x</p>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <DollarSignIcon className="w-5 h-5 text-yellow-400" />
                <span className="text-sm text-gray-400">CPA</span>
              </div>
              <p className="text-2xl font-bold">${predictions.estimatedCPA.toFixed(2)}</p>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <UsersIcon className="w-5 h-5 text-pink-400" />
                <span className="text-sm text-gray-400">Audience Size</span>
              </div>
              <p className="text-2xl font-bold">{predictions.audienceSize.toLocaleString()}</p>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <SparklesIcon className="w-5 h-5 text-orange-400" />
                <span className="text-sm text-gray-400">Competition</span>
              </div>
              <p className="text-2xl font-bold capitalize">{predictions.competitionLevel}</p>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <div className="flex items-center gap-2 mb-2">
                <CheckIcon className="w-5 h-5 text-cyan-400" />
                <span className="text-sm text-gray-400">Confidence</span>
              </div>
              <p className="text-2xl font-bold">{(predictions.confidence * 100).toFixed(0)}%</p>
            </div>
          </div>

          {predictions.recommendations && predictions.recommendations.length > 0 && (
            <div className="bg-indigo-900/20 border border-indigo-500/50 rounded-lg p-4">
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-indigo-400" />
                AI Recommendations
              </h3>
              <ul className="space-y-2">
                {predictions.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-sm">
                    <CheckIcon className="w-4 h-4 text-indigo-400 mt-0.5 flex-shrink-0" />
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
            <h3 className="font-bold mb-3">Preview on Different Placements</h3>
            <div className="flex gap-2 mb-4">
              {['feed', 'stories', 'reels'].map(placement => (
                <button
                  key={placement}
                  onClick={() => setSelectedPlacement(placement as any)}
                  className={`px-4 py-2 rounded-lg capitalize transition-all ${
                    selectedPlacement === placement
                      ? 'bg-indigo-600'
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                >
                  {placement}
                </button>
              ))}
            </div>
            <div className={`bg-gray-900 rounded-lg p-4 ${
              selectedPlacement === 'stories' || selectedPlacement === 'reels'
                ? 'aspect-[9/16] max-w-sm mx-auto'
                : 'aspect-video'
            }`}>
              <div className="w-full h-full flex items-center justify-center text-gray-500">
                Preview for {selectedPlacement} placement
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-gray-400">Click "Fetch Predictions" to see AI-powered insights</p>
          <button
            onClick={fetchPredictions}
            className="mt-4 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
          >
            Fetch Predictions
          </button>
        </div>
      )}
    </div>
  );

  const renderStep5 = () => (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold mb-2">Review & Launch</h2>
        <p className="text-gray-400">Review your campaign before launching</p>
      </div>

      <div className="space-y-4">
        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <h3 className="font-bold mb-3">Campaign Details</h3>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div><span className="text-gray-400">Name:</span> {campaign.name}</div>
            <div><span className="text-gray-400">Objective:</span> {campaign.objective}</div>
            <div><span className="text-gray-400">Budget:</span> ${campaign.budget.amount} {campaign.budget.type}</div>
            <div><span className="text-gray-400">Start Date:</span> {campaign.schedule.startDate}</div>
          </div>
        </div>

        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <h3 className="font-bold mb-3">Creatives ({campaign.creatives.length})</h3>
          <div className="grid grid-cols-3 gap-2">
            {campaign.creatives.map(creative => (
              <div key={creative.id} className="aspect-video bg-gray-900 rounded overflow-hidden">
                {creative.thumbnail && (
                  <img src={creative.thumbnail} alt="Creative" className="w-full h-full object-cover" />
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
          <h3 className="font-bold mb-3">Targeting</h3>
          <div className="space-y-2 text-sm">
            <div><span className="text-gray-400">Locations:</span> {campaign.targeting.locations.join(', ')}</div>
            <div><span className="text-gray-400">Age:</span> {campaign.targeting.ageMin}-{campaign.targeting.ageMax}</div>
            <div><span className="text-gray-400">Gender:</span> {campaign.targeting.genders.join(', ')}</div>
            {campaign.targeting.interests.length > 0 && (
              <div><span className="text-gray-400">Interests:</span> {campaign.targeting.interests.join(', ')}</div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-yellow-900/20 border border-yellow-500/50 rounded-lg p-4">
        <p className="text-sm">
          <strong>Note:</strong> Once launched, this campaign will be published to Meta and will start spending your budget.
          Make sure all details are correct before proceeding.
        </p>
      </div>
    </div>
  );

  // ============================================================================
  // MAIN RENDER
  // ============================================================================

  return (
    <div className="max-w-6xl mx-auto p-6">
      {renderStepIndicator()}

      {error && (
        <div className="bg-red-900/50 border border-red-700 text-red-300 p-4 rounded-lg mb-6 flex justify-between items-center">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-xl px-2">&times;</button>
        </div>
      )}

      {validationErrors.length > 0 && (
        <div className="bg-orange-900/50 border border-orange-700 text-orange-300 p-4 rounded-lg mb-6">
          <p className="font-bold mb-2">Please fix the following errors:</p>
          <ul className="list-disc list-inside space-y-1 text-sm">
            {validationErrors.map((err, idx) => (
              <li key={idx}>{err.message}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-gray-800/30 rounded-lg p-6 min-h-[500px]">
        {currentStep === 0 && renderStep0()}
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
        {currentStep === 4 && renderStep4()}
        {currentStep === 5 && renderStep5()}
      </div>

      <div className="flex justify-between mt-6">
        <div>
          {currentStep > 0 && (
            <button
              onClick={handleBack}
              className="flex items-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
            >
              <ChevronLeftIcon className="w-5 h-5" />
              Back
            </button>
          )}
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleSaveDraft}
            disabled={isLoading}
            className="flex items-center gap-2 px-6 py-3 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <SaveIcon className="w-5 h-5" />
            Save Draft
          </button>
          {currentStep < 5 ? (
            <button
              onClick={handleNext}
              className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
            >
              Next
              <ChevronRightIcon className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleLaunch}
              disabled={isLoading}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <SendIcon className="w-5 h-5" />
              {isLoading ? 'Launching...' : 'Launch Campaign'}
            </button>
          )}
>>>>>>> origin/claude/plan-video-editing-solution-01K1NVwMYwFHsZECx5H2RVTT
        </div>
      </div>
    </div>
  );
};

export default CampaignBuilder;
