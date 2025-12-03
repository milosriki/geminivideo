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
        </div>
      </div>
    </div>
  );
};

export default CampaignBuilder;
