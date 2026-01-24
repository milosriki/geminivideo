/**
 * CampaignBuilderWrapper Component
 * Wraps CampaignBuilder with React Query hooks for proper API integration
 */

import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import CampaignBuilder, { Campaign as BuilderCampaign } from '../CampaignBuilder';
import { Campaign } from '../../lib/api';
import {
  useCreateCampaign,
  useSaveCampaignDraft,
  useLaunchCampaign,
  useUploadCreative,
} from '../../hooks/useCampaigns';
import { useToastStore } from '../../stores/toastStore';

interface CampaignBuilderWrapperProps {
  initialCampaign?: Partial<BuilderCampaign>;
  campaignId?: string;
}

export const CampaignBuilderWrapper: React.FC<CampaignBuilderWrapperProps> = ({
  initialCampaign,
  campaignId,
}) => {
  const navigate = useNavigate();
  const { addToast } = useToastStore();

  const createCampaign = useCreateCampaign();
  const saveDraft = useSaveCampaignDraft();
  const launchCampaign = useLaunchCampaign();
  const uploadCreative = useUploadCreative();

  const handleComplete = useCallback(
    async (campaign: BuilderCampaign) => {
      try {
        if (campaignId) {
          // Launching existing campaign
          await launchCampaign.mutateAsync(campaignId);
          addToast({
            title: 'Campaign Launched!',
            message: `${campaign.name} has been successfully launched.`,
            variant: 'success',
          });
        } else {
          // Creating and launching new campaign - cast to any for structural compatibility
          const created = await createCampaign.mutateAsync(campaign as any);
          await launchCampaign.mutateAsync(created.id!);
          addToast({
            title: 'Campaign Created and Launched!',
            message: `${campaign.name} is now live.`,
            variant: 'success',
          });
        }
        navigate('/campaigns');
      } catch (error: any) {
        addToast({
          title: 'Launch Failed',
          message: error.message || 'Failed to launch campaign',
          variant: 'error',
        });
      }
    },
    [campaignId, createCampaign, launchCampaign, navigate, addToast]
  );

  return (
    <CampaignBuilder
      onComplete={handleComplete}
      initialCampaign={initialCampaign}
    />
  );
};

export default CampaignBuilderWrapper;
