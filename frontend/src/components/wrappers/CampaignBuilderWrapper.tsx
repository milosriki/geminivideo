import React, { Suspense } from 'react';
import { ErrorBoundary } from '../layout/ErrorBoundary';
import { PageWrapper } from '../layout/PageWrapper';
import CampaignBuilder from '../CampaignBuilder';

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
  const handleComplete = (campaign: any) => {
    // TODO: Implement actual publish logic with API
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
