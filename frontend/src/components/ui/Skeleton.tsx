import React from 'react';
import { clsx } from 'clsx';

export interface SkeletonProps {
  variant?: 'text' | 'avatar' | 'card' | 'chart' | 'table-row';
  width?: string | number;
  height?: string | number;
  className?: string;
  rounded?: boolean;
  circle?: boolean;
}

const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width,
  height,
  className,
  rounded = false,
  circle = false,
}) => {
  const baseClasses = 'relative overflow-hidden bg-zinc-800/50 animate-pulse';

  const shimmerClasses = 'before:absolute before:inset-0 before:-translate-x-full before:animate-[shimmer_2s_infinite] before:bg-gradient-to-r before:from-transparent before:via-zinc-700/50 before:to-transparent';

  const variantClasses = {
    text: 'h-4 rounded',
    avatar: 'w-12 h-12 rounded-full',
    card: 'w-full h-48 rounded-lg',
    chart: 'w-full h-64 rounded-lg',
    'table-row': 'w-full h-12 rounded',
  };

  const roundedClass = rounded ? 'rounded-lg' : '';
  const circleClass = circle ? 'rounded-full' : '';

  const style: React.CSSProperties = {};
  if (width) {
    style.width = typeof width === 'number' ? `${width}px` : width;
  }
  if (height) {
    style.height = typeof height === 'number' ? `${height}px` : height;
  }

  return (
    <div
      className={clsx(
        baseClasses,
        shimmerClasses,
        variantClasses[variant],
        roundedClass,
        circleClass,
        className
      )}
      style={style}
    />
  );
};

// Compound component patterns for convenience
export const SkeletonText: React.FC<Omit<SkeletonProps, 'variant'>> = (props) => (
  <Skeleton variant="text" {...props} />
);

export const SkeletonAvatar: React.FC<Omit<SkeletonProps, 'variant'>> = (props) => (
  <Skeleton variant="avatar" circle {...props} />
);

export const SkeletonCard: React.FC<Omit<SkeletonProps, 'variant'>> = (props) => (
  <Skeleton variant="card" {...props} />
);

export const SkeletonChart: React.FC<Omit<SkeletonProps, 'variant'>> = (props) => (
  <Skeleton variant="chart" {...props} />
);

export const SkeletonTableRow: React.FC<Omit<SkeletonProps, 'variant'>> = (props) => (
  <Skeleton variant="table-row" {...props} />
);

// Add shimmer animation to global CSS via style tag
const shimmerStyles = `
  @keyframes shimmer {
    100% {
      transform: translateX(100%);
    }
  }
`;

// Inject styles on component mount
if (typeof document !== 'undefined') {
  const styleId = 'skeleton-shimmer-styles';
  if (!document.getElementById(styleId)) {
    const style = document.createElement('style');
    style.id = styleId;
    style.innerHTML = shimmerStyles;
    document.head.appendChild(style);
  }
}

export default Skeleton;
