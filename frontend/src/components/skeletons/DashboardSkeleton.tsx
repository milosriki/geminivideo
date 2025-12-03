import React from 'react';
import Skeleton, { SkeletonCard, SkeletonChart, SkeletonText } from '../ui/Skeleton';

const DashboardSkeleton: React.FC = () => {
  return (
    <div className="space-y-8 p-6">
      {/* Header */}
      <div className="space-y-2">
        <SkeletonText width="300px" height="32px" />
        <SkeletonText width="500px" height="20px" />
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 space-y-3">
            {/* Icon */}
            <div className="flex items-center justify-between">
              <Skeleton width="40px" height="40px" rounded circle />
              <SkeletonText width="60px" height="20px" />
            </div>

            {/* Value */}
            <SkeletonText width="120px" height="36px" />

            {/* Label */}
            <SkeletonText width="150px" height="16px" />

            {/* Change indicator */}
            <SkeletonText width="100px" height="16px" />
          </div>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Main Chart */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <SkeletonText width="200px" height="24px" />
            <SkeletonText width="100px" height="32px" />
          </div>
          <SkeletonChart height="300px" />
        </div>

        {/* Secondary Chart */}
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <SkeletonText width="180px" height="24px" />
            <SkeletonText width="80px" height="32px" />
          </div>
          <SkeletonChart height="300px" />
        </div>
      </div>

      {/* Activity/Table Section */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-6 space-y-4">
        <div className="flex items-center justify-between">
          <SkeletonText width="200px" height="24px" />
          <SkeletonText width="120px" height="36px" />
        </div>

        {/* Activity List */}
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex items-center space-x-4 py-3 border-b border-zinc-800 last:border-0">
              <Skeleton width="48px" height="48px" rounded circle />
              <div className="flex-1 space-y-2">
                <SkeletonText width="70%" height="16px" />
                <SkeletonText width="40%" height="14px" />
              </div>
              <div className="space-y-2">
                <SkeletonText width="80px" height="16px" />
                <SkeletonText width="60px" height="14px" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardSkeleton;
