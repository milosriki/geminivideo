import React from 'react';

interface PageWrapperProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

export const PageWrapper: React.FC<PageWrapperProps> = ({
  title,
  description,
  children,
  actions
}) => {
  return (
    <div className="min-h-screen bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white">{title}</h1>
            {description && (
              <p className="mt-1 text-sm text-gray-400">{description}</p>
            )}
          </div>
          {actions && (
            <div className="mt-4 sm:mt-0 flex gap-3">
              {actions}
            </div>
          )}
        </div>
        <div className="space-y-6">
          {children}
        </div>
      </div>
    </div>
  );
};

export default PageWrapper;
