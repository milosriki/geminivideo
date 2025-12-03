import React, { useState, useMemo } from 'react';
import { FilterBar, AdGrid, AdDetailModal } from './library';

// Mock ad data with new structure
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

const MOCK_LIBRARY_ADS: LibraryAd[] = [
  {
    id: '1',
    thumbnail: '/placeholder.jpg',
    platform: 'meta',
    brand: 'FitLife Pro',
    hook: 'Transform Your Body in 30 Days - No Gym Required!',
    views: 2500000,
    likes: 45000,
    shares: 8900,
    comments: 2300,
    date: '2024-11-15',
    style: 'ugc',
    script: 'Hey guys! So I tried this 30-day fitness program and wow... the results are insane!\n\nI was skeptical at first, but after just 2 weeks I started seeing real changes.\n\nNo gym membership needed. No fancy equipment. Just 20 minutes a day.\n\nThe best part? Over 100,000 people have already transformed their bodies with this exact program.\n\nClick the link below to start your free trial today!',
    impressions: 5000000,
    ctr: 3.2,
    engagement: 2.8,
  },
  {
    id: '2',
    thumbnail: '/placeholder.jpg',
    platform: 'tiktok',
    brand: 'GlowUp Skincare',
    hook: 'The viral serum everyone is talking about - Results in 7 days!',
    views: 3200000,
    likes: 234000,
    shares: 45000,
    comments: 12000,
    date: '2024-11-20',
    style: 'ugc',
    script: 'Okay so this vitamin C serum literally changed my skin in ONE WEEK.\n\nI know it sounds crazy but look at these before and afters.\n\nMy dark spots? GONE. My skin texture? SMOOTH AF.\n\n2 million people have already made the switch.\n\nGet yours now while it\'s still in stock!',
    impressions: 6000000,
    ctr: 4.1,
    engagement: 4.5,
  },
  {
    id: '3',
    thumbnail: '/placeholder.jpg',
    platform: 'youtube',
    brand: 'InvestSmart Academy',
    hook: 'How I Made $50K Trading From Home (Free Masterclass)',
    views: 850000,
    likes: 12000,
    shares: 2300,
    comments: 890,
    date: '2024-10-28',
    style: 'professional',
    script: 'In this free masterclass, I\'m going to reveal the exact strategy I used to make $50,000 trading from home.\n\nNo prior experience needed. No huge capital required.\n\nI\'ll walk you through my entire system step-by-step.\n\nBut spots are limited, so click below to reserve your seat now.',
    impressions: 1500000,
    ctr: 2.8,
    engagement: 1.9,
  },
  {
    id: '4',
    thumbnail: '/placeholder.jpg',
    platform: 'meta',
    brand: 'PetPals Premium',
    hook: 'Your Dog Deserves Better Food - Vet-Approved & Delivered',
    views: 1200000,
    likes: 18000,
    shares: 3400,
    comments: 1200,
    date: '2024-11-25',
    style: 'professional',
    script: 'As a pet parent, you want the best for your furry friend.\n\nThat\'s why we created PetPals Premium - human-grade ingredients, vet-approved nutrition.\n\nFree delivery on your first order, plus 20% off.\n\nYour dog will love you for it. Order now!',
    impressions: 2000000,
    ctr: 2.5,
    engagement: 2.1,
  },
  {
    id: '5',
    thumbnail: '/placeholder.jpg',
    platform: 'tiktok',
    brand: 'CodeMaster Pro',
    hook: 'Learn to Code in 30 Days - AI-Powered & Beginner-Friendly',
    views: 1800000,
    likes: 89000,
    shares: 12000,
    comments: 4500,
    date: '2024-11-10',
    style: 'ugc',
    script: 'POV: You want to learn coding but don\'t know where to start.\n\nThis AI-powered platform taught me faster than any bootcamp.\n\nNo experience needed. Start for free.\n\nLiterally changed my career in 30 days.',
    impressions: 3000000,
    ctr: 3.8,
    engagement: 3.5,
  },
  {
    id: '6',
    thumbnail: '/placeholder.jpg',
    platform: 'youtube',
    brand: 'MindfulMe Meditation',
    hook: 'Reduce Anxiety in Just 10 Minutes a Day',
    views: 920000,
    likes: 15000,
    shares: 2100,
    comments: 780,
    date: '2024-11-18',
    style: 'testimonial',
    script: 'I used to struggle with anxiety every single day.\n\nThen I discovered this 10-minute meditation technique.\n\nNow I\'m calmer, more focused, and actually enjoying life again.\n\nTry it free for 7 days and see the difference yourself.',
    impressions: 1800000,
    ctr: 2.9,
    engagement: 2.2,
  },
  {
    id: '7',
    thumbnail: '/placeholder.jpg',
    platform: 'meta',
    brand: 'HomeChef Deluxe',
    hook: 'Gourmet Meals Delivered - Save 3 Hours a Day Cooking',
    views: 1500000,
    likes: 22000,
    shares: 4200,
    comments: 1500,
    date: '2024-11-22',
    style: 'professional',
    script: 'Tired of spending hours in the kitchen every day?\n\nHomeChef Deluxe delivers restaurant-quality meals right to your door.\n\nFresh ingredients, easy recipes, ready in 15 minutes.\n\nGet 50% off your first box - no commitment required!',
    impressions: 2500000,
    ctr: 3.0,
    engagement: 2.4,
  },
  {
    id: '8',
    thumbnail: '/placeholder.jpg',
    platform: 'tiktok',
    brand: 'StyleSnap Fashion',
    hook: 'This AI Stylist Picks Your Perfect Outfit Every Time',
    views: 2100000,
    likes: 156000,
    shares: 28000,
    comments: 8900,
    date: '2024-11-28',
    style: 'ugc',
    script: 'Never know what to wear? Same.\n\nThis AI stylist literally picks the perfect outfit for any occasion.\n\nJust answer 3 questions and boom - styled.\n\nTry it free and thank me later!',
    impressions: 4000000,
    ctr: 3.9,
    engagement: 4.2,
  },
  {
    id: '9',
    thumbnail: '/placeholder.jpg',
    platform: 'youtube',
    brand: 'TechGear Pro',
    hook: 'The Laptop Every Remote Worker Needs in 2024',
    views: 680000,
    likes: 8900,
    shares: 1200,
    comments: 450,
    date: '2024-11-05',
    style: 'professional',
    script: 'Working from home? You need the right tools.\n\nThis laptop has everything: 16-hour battery, ultra-fast processor, crystal-clear display.\n\nPerfect for remote work, content creation, or gaming.\n\nLimited stock - order now before it sells out!',
    impressions: 1200000,
    ctr: 2.6,
    engagement: 1.7,
  },
  {
    id: '10',
    thumbnail: '/placeholder.jpg',
    platform: 'meta',
    brand: 'SleepWell Night',
    hook: 'Finally Sleep Through the Night - Science-Backed Formula',
    views: 1100000,
    likes: 19000,
    shares: 3800,
    comments: 1100,
    date: '2024-11-12',
    style: 'testimonial',
    script: 'I hadn\'t slept through the night in years.\n\nThen I tried this science-backed sleep formula.\n\nNow? I wake up refreshed and energized every morning.\n\n30-day guarantee - if it doesn\'t work, full refund.',
    impressions: 2200000,
    ctr: 2.7,
    engagement: 2.3,
  },
  {
    id: '11',
    thumbnail: '/placeholder.jpg',
    platform: 'tiktok',
    brand: 'CleanHome Pro',
    hook: 'This Robot Vacuum Changed My Life - No More Cleaning!',
    views: 2800000,
    likes: 198000,
    shares: 35000,
    comments: 15000,
    date: '2024-11-30',
    style: 'ugc',
    script: 'Okay hear me out... this robot vacuum is LIFE CHANGING.\n\nI literally haven\'t vacuumed in 2 months and my floors are spotless.\n\nIt maps your entire house, avoids obstacles, and empties itself.\n\nBest purchase of 2024 hands down.',
    impressions: 5000000,
    ctr: 4.3,
    engagement: 4.8,
  },
  {
    id: '12',
    thumbnail: '/placeholder.jpg',
    platform: 'youtube',
    brand: 'LearnLang Fast',
    hook: 'Speak Spanish Fluently in 90 Days - Guaranteed',
    views: 750000,
    likes: 11000,
    shares: 1800,
    comments: 620,
    date: '2024-11-08',
    style: 'professional',
    script: 'Want to speak Spanish fluently? We guarantee results in 90 days.\n\nOur proven method has helped 500,000+ students.\n\nPersonalized lessons, native speakers, real conversations.\n\nStart your free trial today and speak with confidence!',
    impressions: 1500000,
    ctr: 2.8,
    engagement: 2.0,
  },
];

const MOCK_BOARDS = [
  { id: '1', name: 'My Boards', count: 24 },
  { id: '2', name: 'Competitor Ads', count: 18 },
  { id: '3', name: 'Inspiration', count: 42 },
  { id: '4', name: 'UGC Collection', count: 31 },
  { id: '5', name: 'High Performers', count: 15 },
];

export const AdSpyDashboard: React.FC = () => {
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [platform, setPlatform] = useState('all');
  const [style, setStyle] = useState('all');
  const [dateRange, setDateRange] = useState('all');
  const [sortBy, setSortBy] = useState('recent');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');

  // UI state
  const [selectedAd, setSelectedAd] = useState<LibraryAd | null>(null);
  const [savedAdIds, setSavedAdIds] = useState<Set<string>>(new Set(['1', '3', '7']));
  const [selectedBoardId, setSelectedBoardId] = useState<string | null>('1');
  const [isLoading, setIsLoading] = useState(false);

  // Filter and sort ads
  const filteredAds = useMemo(() => {
    let filtered = MOCK_LIBRARY_ADS;

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
  }, [searchQuery, platform, style, dateRange, sortBy]);

  const handleCardClick = (id: string) => {
    const ad = MOCK_LIBRARY_ADS.find((a) => a.id === id);
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
    setIsLoading(true);
    // Simulate loading more ads
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };

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
            Showing {filteredAds.length} of {MOCK_LIBRARY_ADS.length} ads
          </p>
        </div>

        {/* Ad Grid */}
        <AdGrid
          ads={filteredAds}
          isLoading={isLoading && filteredAds.length === 0}
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
          boards={MOCK_BOARDS}
          selectedBoardId={selectedBoardId}
          onSaveToBoard={handleSaveToBoard}
          onCreateBoard={handleCreateBoard}
        />
      </div>
    </div>
  );
};

export default AdSpyDashboard;
