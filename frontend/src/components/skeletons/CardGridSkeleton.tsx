import React from 'react';
import Skeleton, { SkeletonCard, SkeletonText } from '../ui/Skeleton';

export interface CardGridSkeletonProps {
  count?: number;
  columns?: 2 | 3 | 4;
  variant?: 'default' | 'compact' | 'detailed';
}

const CardGridSkeleton: React.FC<CardGridSkeletonProps> = ({
  count = 6,
  columns = 3,
  variant = 'default',
}) => {
  const gridClasses = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={`grid ${gridClasses[columns]} gap-6`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i}>
          {variant === 'default' && <DefaultCardSkeleton />}
          {variant === 'compact' && <CompactCardSkeleton />}
          {variant === 'detailed' && <DetailedCardSkeleton />}
        </div>
      ))}
    </div>
  );
};

// Default Card Skeleton
const DefaultCardSkeleton: React.FC = () => {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden">
      {/* Image/Thumbnail */}
      <Skeleton height="200px" className="rounded-none" />

      {/* Content */}
      <div className="p-6 space-y-4">
        {/* Title */}
        <SkeletonText width="80%" height="24px" />

        {/* Description */}
        <div className="space-y-2">
          <SkeletonText width="100%" height="16px" />
          <SkeletonText width="90%" height="16px" />
          <SkeletonText width="60%" height="16px" />
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-zinc-800">
          <div className="flex items-center space-x-2">
            <Skeleton width="32px" height="32px" circle />
            <SkeletonText width="100px" height="14px" />
          </div>
          <SkeletonText width="80px" height="14px" />
        </div>
      </div>
    </div>
  );
};

// Compact Card Skeleton
const CompactCardSkeleton: React.FC = () => {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-start justify-between">
        <Skeleton width="40px" height="40px" rounded />
        <SkeletonText width="60px" height="20px" />
      </div>

      {/* Title */}
      <SkeletonText width="70%" height="20px" />

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 pt-3 border-t border-zinc-800">
        <div className="space-y-1">
          <SkeletonText width="80px" height="12px" />
          <SkeletonText width="60px" height="16px" />
        </div>
        <div className="space-y-1">
          <SkeletonText width="80px" height="12px" />
          <SkeletonText width="60px" height="16px" />
        </div>
      </div>
    </div>
  );
};

// Detailed Card Skeleton (e.g., for video/asset cards)
const DetailedCardSkeleton: React.FC = () => {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg overflow-hidden hover:border-zinc-700 transition-colors">
      {/* Thumbnail with play button overlay */}
      <div className="relative">
        <Skeleton height="180px" className="rounded-none" />
        <div className="absolute inset-0 flex items-center justify-center">
          <Skeleton width="48px" height="48px" circle />
        </div>
        {/* Duration badge */}
        <div className="absolute bottom-2 right-2">
          <SkeletonText width="50px" height="20px" />
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Title and menu */}
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-2">
            <SkeletonText width="90%" height="18px" />
            <SkeletonText width="70%" height="14px" />
          </div>
          <Skeleton width="24px" height="24px" rounded />
        </div>

        {/* Meta info */}
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-2">
            <Skeleton width="20px" height="20px" circle />
            <SkeletonText width="60px" height="14px" />
          </div>
          <div className="flex items-center space-x-2">
            <Skeleton width="20px" height="20px" circle />
            <SkeletonText width="60px" height="14px" />
          </div>
        </div>

        {/* Tags */}
        <div className="flex items-center space-x-2">
          <SkeletonText width="60px" height="24px" rounded />
          <SkeletonText width="70px" height="24px" rounded />
          <SkeletonText width="50px" height="24px" rounded />
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-zinc-800">
          <div className="flex items-center space-x-2">
            <Skeleton width="32px" height="32px" rounded />
            <Skeleton width="32px" height="32px" rounded />
            <Skeleton width="32px" height="32px" rounded />
          </div>
          <SkeletonText width="80px" height="32px" rounded />
        </div>
      </div>
    </div>
  );
};

// Video Card Grid Skeleton (specialized for video thumbnails)
export const VideoCardGridSkeleton: React.FC<Omit<CardGridSkeletonProps, 'variant'>> = (props) => {
  return <CardGridSkeleton {...props} variant="detailed" />;
};

// Simple Card Grid Skeleton
export const SimpleCardGridSkeleton: React.FC<Omit<CardGridSkeletonProps, 'variant'>> = (props) => {
  return <CardGridSkeleton {...props} variant="compact" />;
};

export default CardGridSkeleton;
