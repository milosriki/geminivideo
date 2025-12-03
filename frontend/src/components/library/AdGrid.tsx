import React from 'react';

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

const AdCard: React.FC<{
  id: string;
  thumbnail: string;
  platform: string;
  brand: string;
  hook: string;
  views: number;
  likes?: number;
  date: string;
  style: string;
  onCardClick: (id: string) => void;
  onSaveClick: (id: string) => void;
  isSaved: boolean;
}> = ({
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
  isSaved,
}) => {
    return (
      <div
        onClick={() => onCardClick(id)}
        className="group relative bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden cursor-pointer hover:border-zinc-700 transition-all mb-4 break-inside-avoid"
      >
        {/* Thumbnail */}
        <div className="aspect-[9/16] relative bg-zinc-800">
          <img
            src={thumbnail}
            alt={hook}
            className="w-full h-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60" />

          {/* Platform Badge */}
          <div className="absolute top-3 left-3 bg-black/50 backdrop-blur-sm px-2 py-1 rounded-md text-xs font-medium text-white capitalize">
            {platform}
          </div>

          {/* Save Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSaveClick(id);
            }}
            className={`absolute top-3 right-3 p-2 rounded-full backdrop-blur-sm transition-colors ${isSaved ? 'bg-violet-500 text-white' : 'bg-black/50 text-white hover:bg-black/70'
              }`}
          >
            <svg className="w-4 h-4" fill={isSaved ? "currentColor" : "none"} stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </button>

          {/* Stats Overlay */}
          <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-xs text-white/90">
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
              {(views / 1000).toFixed(1)}k
            </div>
            {likes && (
              <div className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                {(likes / 1000).toFixed(1)}k
              </div>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-5 h-5 rounded-full bg-zinc-800 flex-shrink-0" />
            <span className="text-xs text-zinc-400 font-medium truncate">{brand}</span>
          </div>
          <h3 className="text-sm font-medium text-white line-clamp-2 mb-3 group-hover:text-violet-400 transition-colors">
            {hook}
          </h3>
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-zinc-800 text-zinc-400 capitalize">
              {style}
            </span>
            <span className="text-[10px] text-zinc-500">
              {new Date(date).toLocaleDateString()}
            </span>
          </div>
        </div>
      </div>
    );
  };

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
