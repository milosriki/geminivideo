import React, { Suspense, useState } from 'react';
import { ErrorBoundary } from '../layout/ErrorBoundary';
import { PageWrapper } from '../layout/PageWrapper';
import AICreativeStudio from '../AICreativeStudio';
import { useAuth } from '@/contexts/AuthContext';
import { apiUrl } from '@/config/api';

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="text-center">
      <svg className="animate-spin h-10 w-10 text-indigo-500 mx-auto mb-4" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p className="text-gray-400">Loading AI Creative Studio...</p>
    </div>
  </div>
);

interface AICreativeStudioWrapperProps {
  projectId?: string;
}

export const AICreativeStudioWrapper: React.FC<AICreativeStudioWrapperProps> = ({ projectId }) => {
  const { currentUser, getIdToken } = useAuth();
  const [isSaving, setIsSaving] = useState(false);

  const handleCreativeGenerated = async (creative: any) => {
    if (!currentUser) {
      console.warn('User not authenticated, cannot save creative to asset library');
      return;
    }

    setIsSaving(true);
    try {
      const token = await getIdToken();
      const response = await fetch(apiUrl('/assets'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        },
        body: JSON.stringify({
          userId: currentUser.uid,
          projectId,
          creative: {
            type: creative.type || 'image',
            url: creative.url,
            thumbnail: creative.thumbnail,
            prompt: creative.prompt,
            metadata: {
              style: creative.style,
              platform: creative.platform,
              dimensions: creative.dimensions,
              generatedAt: new Date().toISOString(),
              ...creative.metadata
            }
          }
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to save creative to asset library');
      }

      const savedAsset = await response.json();
      console.log('Creative saved to asset library:', savedAsset);

      // Show success notification
      if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('asset-saved', {
          detail: { asset: savedAsset, message: 'Creative saved to asset library' }
        }));
      }
    } catch (error) {
      console.error('Failed to save creative to asset library:', error);
      // Show error notification
      if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('asset-save-error', {
          detail: { error, message: error instanceof Error ? error.message : 'Failed to save creative' }
        }));
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <AICreativeStudio
          onCreativeGenerated={handleCreativeGenerated}
        />
      </Suspense>
    </ErrorBoundary>
  );
};

export default AICreativeStudioWrapper;
