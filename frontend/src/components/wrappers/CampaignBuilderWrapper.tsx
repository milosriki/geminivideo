import React, { Suspense, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ErrorBoundary } from '../layout/ErrorBoundary';
import { PageWrapper } from '../layout/PageWrapper';
import CampaignBuilder from '../CampaignBuilder';
import { useAuth } from '@/contexts/AuthContext';
import { apiUrl } from '@/config/api';

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="text-center">
      <svg className="animate-spin h-10 w-10 text-indigo-500 mx-auto mb-4" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p className="text-gray-400">Loading Campaign Builder...</p>
    </div>
  </div>
);

interface CampaignBuilderWrapperProps {
  campaignId?: string;
}

export const CampaignBuilderWrapper: React.FC<CampaignBuilderWrapperProps> = ({ campaignId }) => {
  const { currentUser, getIdToken } = useAuth();
  const navigate = useNavigate();
  const [isPublishing, setIsPublishing] = useState(false);

  const handleComplete = async (campaign: any) => {
    if (!currentUser) {
      console.error('User not authenticated, cannot publish campaign');
      window.dispatchEvent(new CustomEvent('campaign-publish-error', {
        detail: { message: 'You must be logged in to publish campaigns' }
      }));
      return;
    }

    setIsPublishing(true);
    try {
      const token = await getIdToken();

      // Step 1: Create or update the campaign
      const campaignEndpoint = campaignId
        ? apiUrl(`/campaigns/${campaignId}`)
        : apiUrl('/campaigns');

      const campaignMethod = campaignId ? 'PUT' : 'POST';

      const campaignResponse = await fetch(campaignEndpoint, {
        method: campaignMethod,
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          userId: currentUser.uid,
          name: campaign.name,
          budget_daily: campaign.dailyBudget,
          target_audience: campaign.targetAudience,
          platforms: campaign.platforms || ['meta'],
          status: 'draft',
          metadata: {
            ...campaign.metadata,
            createdBy: currentUser.uid,
            createdAt: new Date().toISOString()
          }
        })
      });

      if (!campaignResponse.ok) {
        const errorData = await campaignResponse.json();
        throw new Error(errorData.message || 'Failed to save campaign');
      }

      const savedCampaign = await campaignResponse.json();
      const finalCampaignId = savedCampaign.id || savedCampaign.campaign_id;

      console.log('Campaign saved:', savedCampaign);

      // Step 2: If user wants to publish immediately, launch the campaign
      if (campaign.publishImmediately) {
        const launchResponse = await fetch(apiUrl(`/campaigns/${finalCampaignId}/launch`), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
          },
          body: JSON.stringify({
            platforms: campaign.platforms || ['meta'],
            startDate: campaign.startDate || new Date().toISOString(),
            endDate: campaign.endDate
          })
        });

        if (!launchResponse.ok) {
          const errorData = await launchResponse.json();
          throw new Error(errorData.message || 'Failed to launch campaign');
        }

        const launchResult = await launchResponse.json();
        console.log('Campaign launched:', launchResult);

        // Show success notification
        window.dispatchEvent(new CustomEvent('campaign-published', {
          detail: {
            campaign: savedCampaign,
            launched: true,
            message: `Campaign "${campaign.name}" published and launched successfully!`
          }
        }));

        // Navigate to campaign analytics
        navigate(`/analytics/campaign/${finalCampaignId}`);
      } else {
        // Campaign saved as draft
        window.dispatchEvent(new CustomEvent('campaign-saved', {
          detail: {
            campaign: savedCampaign,
            message: `Campaign "${campaign.name}" saved as draft`
          }
        }));

        // Navigate to campaigns list
        navigate('/campaigns');
      }
    } catch (error) {
      console.error('Failed to publish campaign:', error);
      window.dispatchEvent(new CustomEvent('campaign-publish-error', {
        detail: {
          error,
          message: error instanceof Error ? error.message : 'Failed to publish campaign'
        }
      }));
    } finally {
      setIsPublishing(false);
    }
  };

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <CampaignBuilder
          onComplete={handleComplete}
        />
      </Suspense>
    </ErrorBoundary>
  );
};

export default CampaignBuilderWrapper;
