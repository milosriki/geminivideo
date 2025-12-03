import React, { useState, useMemo, useEffect } from 'react';
import { FilterBar, AdGrid, AdDetailModal } from './library';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Ad data structure
interface LibraryAd {
  id: string;
  thumbnail: string;
  platform: 'meta' | 'tiktok' | 'youtube';
  brand: string;
  hook: string;
  views: number;
  likes: number;
  shares?: number;
  comments?: number;
  date: string;
  style: string;
  script?: string;
  impressions?: number;
  ctr?: number;
  engagement?: number;
}

export const AdSpyDashboard: React.FC = () => {
  // Data state
  const [libraryAds, setLibraryAds] = useState<LibraryAd[]>([]);
  const [boards, setBoards] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [platform, setPlatform] = useState('all');
  const [style, setStyle] = useState('all');
  const [dateRange, setDateRange] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // UI state
  const [selectedAd, setSelectedAd] = useState<LibraryAd | null>(null);
  const [savedAdIds, setSavedAdIds] = useState<Set<string>>(new Set());
  const [selectedBoardId, setSelectedBoardId] = useState<string | null>(null);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Fetch ads and boards from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch library ads
        const adsResponse = await fetch(`${API_BASE_URL}/adspy/library`);
        if (!adsResponse.ok) {
          throw new Error(adsResponse.status.toString());
        }
        const adsData = await adsResponse.json();
        setLibraryAds(adsData);

        // Fetch boards
        const boardsResponse = await fetch(`${API_BASE_URL}/adspy/boards`);
        if (!boardsResponse.ok) {
          throw new Error(boardsResponse.status.toString());
        }
        const boardsData = await boardsResponse.json();
        setBoards(boardsData);

        setError(null);
      } catch (err) {
        setError('Data source not configured. Please configure ad library in the backend.');
        setLibraryAds([]);
        setBoards([]);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Filter and sort ads
  const filteredAds = useMemo(() => {
    let filtered = libraryAds;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (ad) =>
          ad.brand.toLowerCase().includes(query) ||
          ad.hook.toLowerCase().includes(query) ||
          ad.style.toLowerCase().includes(query)
      );
    }

    // Platform filter
    if (platform !== 'all') {
      filtered = filtered.filter((ad) => ad.platform === platform);
    }

    // Style filter
    if (style !== 'all') {
      filtered = filtered.filter((ad) => ad.style === style);
    }

    // Date range filter
    if (dateRange !== 'all') {
      const days = parseInt(dateRange);
      const cutoffDate = new Date();
      cutoffDate.setDate(cutoffDate.getDate() - days);
      filtered = filtered.filter((ad) => new Date(ad.date) >= cutoffDate);
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'recent':
          return new Date(b.date).getTime() - new Date(a.date).getTime();
        case 'views':
          return b.views - a.views;
        case 'performance':
          return (b.engagement || 0) - (a.engagement || 0);
        default:
          return 0;
      }
    });

    return filtered;
  }, [libraryAds, searchQuery, platform, style, dateRange, sortBy]);

  const handleCardClick = (id: string) => {
    const ad = libraryAds.find((a) => a.id === id);
    if (ad) {
      setSelectedAd(ad);
    }
  };

  const handleSaveClick = (id: string) => {
    setSavedAdIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSaveToBoard = (boardId: string) => {
    setSelectedBoardId(boardId);
    // TODO: Implement save to board functionality
  };

  const handleCreateBoard = () => {
    // TODO: Implement create board functionality
  };

  const handleLoadMore = () => {
    setIsLoadingMore(true);
    // TODO: Implement pagination
    setTimeout(() => {
      setIsLoadingMore(false);
    }, 1000);
  };

  // Show loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
        <div className="text-zinc-400">Loading ad library...</div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-400 mb-2">Error loading ad library</div>
          <div className="text-zinc-500 text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Ad Spy Library</h1>
          <p className="text-zinc-400">
            Discover high-performing ads and save them to your boards
          </p>
        </div>

        {/* Filter Bar */}
        <div className="mb-6">
          <FilterBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            platform={platform}
            onPlatformChange={setPlatform}
            style={style}
            onStyleChange={setStyle}
            dateRange={dateRange}
            onDateRangeChange={setDateRange}
            sortBy={sortBy}
            onSortByChange={setSortBy}
            viewMode={viewMode}
            onViewModeChange={setViewMode}
          />
        </div>

        {/* Results Count */}
        <div className="mb-6">
          <p className="text-sm text-zinc-500">
            Showing {filteredAds.length} of {libraryAds.length} ads
          </p>
        </div>

        {/* Ad Grid */}
        <AdGrid
          ads={filteredAds}
          isLoading={isLoadingMore && filteredAds.length === 0}
          onCardClick={handleCardClick}
          onSaveClick={handleSaveClick}
          savedAdIds={savedAdIds}
          onLoadMore={handleLoadMore}
          hasMore={false} // Set to true when implementing pagination
        />

        {/* Ad Detail Modal */}
        <AdDetailModal
          ad={selectedAd}
          isOpen={selectedAd !== null}
          onClose={() => setSelectedAd(null)}
          boards={boards}
          selectedBoardId={selectedBoardId}
          onSaveToBoard={handleSaveToBoard}
          onCreateBoard={handleCreateBoard}
        />
      </div>
    </div>
  );
};

export default AdSpyDashboard;
