import React, { useState } from 'react';
import { AnimatedCard } from '../ui/AnimatedCard';

interface AdCardProps {
  id: string;
  thumbnail: string;
  platform: 'meta' | 'tiktok' | 'youtube';
  brand: string;
  hook: string;
  views: number;
  likes?: number;
  date: string;
  style: string;
  onCardClick: (id: string) => void;
  onSaveClick: (id: string) => void;
  isSaved?: boolean;
}

const HeartIcon: React.FC<{ className?: string; filled?: boolean }> = ({ className, filled }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill={filled ? "currentColor" : "none"}
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={className}
  >
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
  </svg>
);

const EyeIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"></path>
    <circle cx="12" cy="12" r="3"></circle>
  </svg>
);

const SparklesIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
  </svg>
);

const ClipboardIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);

const EditIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path>
  </svg>
);

const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

const getPlatformBadge = (platform: string) => {
  const badges = {
    meta: { color: 'bg-blue-600', label: 'Meta' },
    tiktok: { color: 'bg-pink-500', label: 'TikTok' },
    youtube: { color: 'bg-red-600', label: 'YouTube' },
  };
  return badges[platform as keyof typeof badges] || { color: 'bg-gray-600', label: platform };
};

export const AdCard: React.FC<AdCardProps> = ({
  id,
  thumbnail,
  platform,
  brand,
  hook,
  views,
  likes,
  date,
  style,
  onCardClick,
  onSaveClick,
  isSaved = false,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const platformBadge = getPlatformBadge(platform);

  const handleSaveClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onSaveClick(id);
  };

  const handleAnalyzeClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // TODO: Implement analyze ad functionality
  };

  const handleCopyScriptClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // TODO: Implement copy script functionality
  };

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // TODO: Implement edit ad functionality
  };

  return (
    <AnimatedCard
      className="relative overflow-hidden cursor-pointer break-inside-avoid mb-4"
      scaleOnHover
      liftAmount={-8}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={() => onCardClick(id)}
    >
      {/* Thumbnail Container */}
      <div className="relative aspect-video bg-zinc-950 overflow-hidden">
        {/* Placeholder thumbnail */}
        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-zinc-800 to-zinc-900">
          <div className="text-zinc-600 text-4xl font-bold">{brand.charAt(0)}</div>
        </div>

        {/* Platform Badge - Top Left */}
        <div className="absolute top-2 left-2">
          <span className={`px-2 py-1 ${platformBadge.color} rounded text-xs font-semibold shadow-lg`}>
            {platformBadge.label}
          </span>
        </div>

        {/* Save Button - Top Right */}
        <div className="absolute top-2 right-2">
          <button
            onClick={handleSaveClick}
            className={`p-2 rounded-full transition-all duration-200 ${
              isSaved
                ? 'bg-red-500 text-white'
                : 'bg-black/60 text-white hover:bg-red-500'
            }`}
          >
            <HeartIcon className="w-4 h-4" filled={isSaved} />
          </button>
        </div>

        {/* View Count - Bottom Left */}
        <div className="absolute bottom-2 left-2 flex items-center gap-1 px-2 py-1 bg-black/70 rounded text-xs font-medium">
          <EyeIcon className="w-3 h-3" />
          <span>{formatNumber(views)}</span>
        </div>

        {/* Hover Overlay with Quick Actions */}
        <div
          className={`absolute inset-0 bg-black/80 flex flex-col items-center justify-center gap-2 transition-opacity duration-200 ${
            isHovered ? 'opacity-100' : 'opacity-0 pointer-events-none'
          }`}
        >
          <button
            onClick={handleAnalyzeClick}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <SparklesIcon className="w-4 h-4" />
            Analyze
          </button>
          <button
            onClick={handleCopyScriptClick}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <ClipboardIcon className="w-4 h-4" />
            Copy Script
          </button>
          <button
            onClick={handleEditClick}
            className="px-4 py-2 bg-zinc-700 hover:bg-zinc-600 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
          >
            <EditIcon className="w-4 h-4" />
            Edit
          </button>
        </div>
      </div>

      {/* Card Content */}
      <div className="p-3">
        {/* Brand Name */}
        <div className="text-xs text-indigo-400 font-semibold mb-1">{brand}</div>

        {/* Hook Text */}
        <h3 className="text-sm font-medium text-white line-clamp-2 mb-2">{hook}</h3>

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-zinc-500">
          <span className="truncate">{style}</span>
          {likes && (
            <span className="flex items-center gap-1">
              <HeartIcon className="w-3 h-3" />
              {formatNumber(likes)}
            </span>
          )}
        </div>
      </div>
    </AnimatedCard>
  );
};

export default AdCard;
