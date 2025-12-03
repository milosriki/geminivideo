import React, { Suspense } from 'react';
import { ErrorBoundary } from '../layout/ErrorBoundary';
import ProVideoEditor from '../ProVideoEditor';

const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-950">
    <div className="text-center">
      <svg className="animate-spin h-10 w-10 text-indigo-500 mx-auto mb-4" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <p className="text-gray-400">Loading Video Editor...</p>
    </div>
  </div>
);

interface ProVideoEditorWrapperProps {
  projectId?: string;
}

export const ProVideoEditorWrapper: React.FC<ProVideoEditorWrapperProps> = ({ projectId }) => {
  const handleSave = async (project: any) => {
    // TODO: Implement actual save logic with API
  };

  const handleExport = async (settings: any) => {
    // TODO: Implement actual export logic with video processing service
  };

  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingFallback />}>
        <ProVideoEditor
          projectId={projectId}
          onSave={handleSave}
          onExport={handleExport}
        />
      </Suspense>
    </ErrorBoundary>
  );
};

export default ProVideoEditorWrapper;
