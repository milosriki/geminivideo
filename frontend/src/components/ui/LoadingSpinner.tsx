/**
 * LoadingSpinner Component
 * Reusable loading indicator with different sizes
 */

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
  xl: 'h-16 w-16 border-4',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = '',
  text,
}) => {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <div
        className={`${sizeClasses[size]} rounded-full border-gray-700 border-t-indigo-500 animate-spin`}
      />
      {text && <p className="text-sm text-gray-400">{text}</p>}
    </div>
  );
};

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'rectangular' | 'circular';
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '', variant = 'rectangular' }) => {
  const variantClasses = {
    text: 'h-4 w-full',
    rectangular: 'h-full w-full',
    circular: 'rounded-full',
  };

  return (
    <div
      className={`animate-pulse bg-gray-800/50 ${variantClasses[variant]} ${className}`}
      aria-label="Loading..."
    />
  );
};

interface FullPageLoaderProps {
  text?: string;
}

export const FullPageLoader: React.FC<FullPageLoaderProps> = ({ text = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 bg-gray-900/95 backdrop-blur-sm flex items-center justify-center z-50">
      <LoadingSpinner size="xl" text={text} />
    </div>
  );
};
