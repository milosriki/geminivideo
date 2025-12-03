import React from 'react';
import { AdCard } from './AdCard';

interface Ad {
  id: string;
  thumbnail: string;
  platform: 'meta' | 'tiktok' | 'youtube';
  brand: string;
  hook: string;
  views: number;
  likes?: number;
  date: string;
  style: string;
}

interface AdGridProps {
  ads: Ad[];
  isLoading?: boolean;
  onCardClick: (id: string) => void;
  onSaveClick: (id: string) => void;
  savedAdIds?: Set<string>;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

const SkeletonCard: React.FC = () => (
  <div className="bg-zinc-900 border border-zinc-800 rounded-lg overflow-hidden break-inside-avoid mb-4 animate-pulse">
    <div className="aspect-video bg-zinc-800" />
    <div className="p-3 space-y-2">
      <div className="h-3 bg-zinc-800 rounded w-1/3" />
      <div className="h-4 bg-zinc-800 rounded w-full" />
      <div className="h-3 bg-zinc-800 rounded w-2/3" />
    </div>
  </div>
);

export const AdGrid: React.FC<AdGridProps> = ({
  ads,
  isLoading = false,
  onCardClick,
  onSaveClick,
  savedAdIds = new Set(),
  onLoadMore,
  hasMore = false,
}) => {
  if (isLoading && ads.length === 0) {
    return (
      <div
        className="grid gap-4"
        style={{
          columnCount: 1,
          columnGap: '1rem',
        }}
      >
        {Array.from({ length: 8 }).map((_, index) => (
          <SkeletonCard key={index} />
        ))}
      </div>
    );
  }

  if (!isLoading && ads.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="w-16 h-16 mb-4 rounded-full bg-zinc-800 flex items-center justify-center">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="32"
            height="32"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="text-zinc-600"
          >
            <circle cx="11" cy="11" r="8"></circle>
            <path d="m21 21-4.35-4.35"></path>
          </svg>
        </div>
        <h3 className="text-lg font-semibold text-white mb-1">No ads found</h3>
        <p className="text-sm text-zinc-500">Try adjusting your filters or search query</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Masonry Grid using CSS columns */}
      <div
        className="masonry-grid"
        style={{
          columnCount: 1,
          columnGap: '1rem',
        }}
      >
        <style>{`
          @media (min-width: 640px) {
            .masonry-grid {
              column-count: 2 !important;
            }
          }
          @media (min-width: 1024px) {
            .masonry-grid {
              column-count: 3 !important;
            }
          }
          @media (min-width: 1280px) {
            .masonry-grid {
              column-count: 4 !important;
            }
          }
        `}</style>

        {ads.map((ad) => (
          <AdCard
            key={ad.id}
            id={ad.id}
            thumbnail={ad.thumbnail}
            platform={ad.platform}
            brand={ad.brand}
            hook={ad.hook}
            views={ad.views}
            likes={ad.likes}
            date={ad.date}
            style={ad.style}
            onCardClick={onCardClick}
            onSaveClick={onSaveClick}
            isSaved={savedAdIds.has(ad.id)}
          />
        ))}
      </div>

      {/* Load More Button */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={onLoadMore}
            disabled={isLoading}
            className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 disabled:bg-zinc-900 border border-zinc-700 rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Loading...
              </span>
            ) : (
              'Load More'
            )}
          </button>
        </div>
      )}
    </div>
  );
};

export default AdGrid;
