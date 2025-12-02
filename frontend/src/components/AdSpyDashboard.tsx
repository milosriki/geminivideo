import React, { useState, useMemo, useCallback } from 'react';
import { EyeIcon, TagIcon, BarChartIcon, FilmIcon, SparklesIcon, DownloadIcon } from './icons';

interface SpyAd {
  id: string;
  platform: 'meta' | 'tiktok' | 'youtube' | 'google';
  advertiser: string;
  headline: string;
  body: string;
  mediaType: 'video' | 'image' | 'carousel';
  thumbnail: string;
  cta: string;
  firstSeen: string;
  lastSeen: string;
  daysRunning: number;
  estimatedSpend: { min: number; max: number };
  engagement: {
    likes: number;
    comments: number;
    shares: number;
  };
  targeting: {
    ageRange: string;
    gender: string;
    interests: string[];
    countries: string[];
  };
  hooks: string[];
  angles: string[];
  landingPage?: string;
}

interface FilterState {
  platform: string;
  mediaType: string;
  daysRunning: string;
  search: string;
  sortBy: string;
}

const MOCK_ADS: SpyAd[] = [
  {
    id: '1',
    platform: 'meta',
    advertiser: 'FitLife Pro',
    headline: 'Transform Your Body in 30 Days',
    body: 'Join 100,000+ who have achieved their fitness goals with our proven program. No gym required!',
    mediaType: 'video',
    thumbnail: '/api/placeholder/320/180',
    cta: 'Start Free Trial',
    firstSeen: '2024-10-15',
    lastSeen: '2024-12-01',
    daysRunning: 47,
    estimatedSpend: { min: 15000, max: 35000 },
    engagement: { likes: 45000, comments: 2300, shares: 8900 },
    targeting: {
      ageRange: '25-44',
      gender: 'All',
      interests: ['Fitness', 'Weight Loss', 'Home Workouts'],
      countries: ['US', 'UK', 'CA', 'AU'],
    },
    hooks: ['Transformation Hook', 'Social Proof', 'Time-Bound Promise'],
    angles: ['Home Workout', 'Quick Results', 'No Equipment'],
  },
  {
    id: '2',
    platform: 'tiktok',
    advertiser: 'GlowUp Skincare',
    headline: 'The viral serum everyone is talking about',
    body: 'See why 2M+ people switched to our vitamin C serum. Results in just 7 days.',
    mediaType: 'video',
    thumbnail: '/api/placeholder/320/180',
    cta: 'Shop Now',
    firstSeen: '2024-11-01',
    lastSeen: '2024-12-01',
    daysRunning: 30,
    estimatedSpend: { min: 50000, max: 100000 },
    engagement: { likes: 234000, comments: 12000, shares: 45000 },
    targeting: {
      ageRange: '18-34',
      gender: 'Female',
      interests: ['Skincare', 'Beauty', 'Self Care'],
      countries: ['US', 'UK'],
    },
    hooks: ['Viral/Trending', 'Quick Results', 'FOMO'],
    angles: ['Before/After', 'User Generated', 'Tutorial Style'],
  },
  {
    id: '3',
    platform: 'youtube',
    advertiser: 'InvestSmart Academy',
    headline: 'How I Made $50K Trading From Home',
    body: 'Free masterclass reveals the exact strategy used by top traders. Limited spots available.',
    mediaType: 'video',
    thumbnail: '/api/placeholder/320/180',
    cta: 'Watch Free Class',
    firstSeen: '2024-09-20',
    lastSeen: '2024-12-01',
    daysRunning: 72,
    estimatedSpend: { min: 75000, max: 150000 },
    engagement: { likes: 12000, comments: 890, shares: 2300 },
    targeting: {
      ageRange: '25-54',
      gender: 'Male',
      interests: ['Investing', 'Finance', 'Entrepreneurship'],
      countries: ['US'],
    },
    hooks: ['Income Claim', 'Scarcity', 'Free Value'],
    angles: ['Story/Journey', 'Expert Authority', 'Results Focus'],
  },
  {
    id: '4',
    platform: 'meta',
    advertiser: 'PetPals Premium',
    headline: 'Your Dog Deserves Better Food',
    body: 'Vet-approved, human-grade ingredients. Free delivery on your first order + 20% off.',
    mediaType: 'carousel',
    thumbnail: '/api/placeholder/320/180',
    cta: 'Get 20% Off',
    firstSeen: '2024-11-10',
    lastSeen: '2024-12-01',
    daysRunning: 21,
    estimatedSpend: { min: 8000, max: 20000 },
    engagement: { likes: 18000, comments: 1200, shares: 3400 },
    targeting: {
      ageRange: '25-54',
      gender: 'All',
      interests: ['Dogs', 'Pet Care', 'Pet Food'],
      countries: ['US', 'CA'],
    },
    hooks: ['Emotional Appeal', 'Discount Offer', 'Authority'],
    angles: ['Health Focus', 'Premium Quality', 'Convenience'],
  },
  {
    id: '5',
    platform: 'tiktok',
    advertiser: 'CodeMaster Pro',
    headline: 'Learn to code in 30 days - no experience needed',
    body: 'This AI-powered platform teaches you faster than any bootcamp. Start for free.',
    mediaType: 'video',
    thumbnail: '/api/placeholder/320/180',
    cta: 'Start Learning',
    firstSeen: '2024-10-25',
    lastSeen: '2024-12-01',
    daysRunning: 37,
    estimatedSpend: { min: 25000, max: 60000 },
    engagement: { likes: 89000, comments: 4500, shares: 12000 },
    targeting: {
      ageRange: '18-34',
      gender: 'All',
      interests: ['Technology', 'Career Development', 'Education'],
      countries: ['US', 'UK', 'IN'],
    },
    hooks: ['Beginner Friendly', 'AI/Tech Appeal', 'Time Promise'],
    angles: ['Career Change', 'Side Hustle', 'Future-Proof Skills'],
  },
];

const PLATFORMS = [
  { id: 'all', name: 'All Platforms', color: 'bg-gray-600' },
  { id: 'meta', name: 'Meta', color: 'bg-blue-600' },
  { id: 'tiktok', name: 'TikTok', color: 'bg-pink-500' },
  { id: 'youtube', name: 'YouTube', color: 'bg-red-600' },
  { id: 'google', name: 'Google', color: 'bg-green-600' },
];

const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

export const AdSpyDashboard: React.FC = () => {
  const [filters, setFilters] = useState<FilterState>({
    platform: 'all',
    mediaType: 'all',
    daysRunning: 'all',
    search: '',
    sortBy: 'daysRunning',
  });
  const [selectedAd, setSelectedAd] = useState<SpyAd | null>(null);
  const [savedAds, setSavedAds] = useState<Set<string>>(new Set());

  const filteredAds = useMemo(() => {
    return MOCK_ADS
      .filter(ad => {
        if (filters.platform !== 'all' && ad.platform !== filters.platform) return false;
        if (filters.mediaType !== 'all' && ad.mediaType !== filters.mediaType) return false;
        if (filters.daysRunning === '7+' && ad.daysRunning < 7) return false;
        if (filters.daysRunning === '30+' && ad.daysRunning < 30) return false;
        if (filters.daysRunning === '60+' && ad.daysRunning < 60) return false;
        if (filters.search) {
          const search = filters.search.toLowerCase();
          return (
            ad.advertiser.toLowerCase().includes(search) ||
            ad.headline.toLowerCase().includes(search) ||
            ad.body.toLowerCase().includes(search)
          );
        }
        return true;
      })
      .sort((a, b) => {
        switch (filters.sortBy) {
          case 'daysRunning': return b.daysRunning - a.daysRunning;
          case 'spend': return b.estimatedSpend.max - a.estimatedSpend.max;
          case 'engagement': return (b.engagement.likes + b.engagement.shares) - (a.engagement.likes + a.engagement.shares);
          default: return 0;
        }
      });
  }, [filters]);

  const toggleSaveAd = useCallback((adId: string) => {
    setSavedAds(prev => {
      const next = new Set(prev);
      if (next.has(adId)) {
        next.delete(adId);
      } else {
        next.add(adId);
      }
      return next;
    });
  }, []);

  const getPlatformColor = (platform: string): string => {
    return PLATFORMS.find(p => p.id === platform)?.color || 'bg-gray-600';
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8 gap-4">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <EyeIcon className="w-6 h-6 text-indigo-400" />
              Ad Spy Dashboard
            </h1>
            <p className="text-gray-400 text-sm mt-1">
              Monitor competitor ads and discover winning creatives
            </p>
          </div>
          <div className="flex gap-2">
            <span className="px-3 py-1.5 bg-gray-800 rounded-lg text-sm">
              {filteredAds.length} ads found
            </span>
            <button className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm transition-colors">
              + New Search
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-gray-800/60 border border-gray-700 rounded-xl p-4 mb-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Search</label>
              <input
                type="text"
                placeholder="Search ads..."
                value={filters.search}
                onChange={e => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-900/60 border border-gray-700 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Platform</label>
              <select
                value={filters.platform}
                onChange={e => setFilters(prev => ({ ...prev, platform: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-900/60 border border-gray-700 rounded-lg text-sm"
              >
                {PLATFORMS.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Media Type</label>
              <select
                value={filters.mediaType}
                onChange={e => setFilters(prev => ({ ...prev, mediaType: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-900/60 border border-gray-700 rounded-lg text-sm"
              >
                <option value="all">All Types</option>
                <option value="video">Video</option>
                <option value="image">Image</option>
                <option value="carousel">Carousel</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Days Running</label>
              <select
                value={filters.daysRunning}
                onChange={e => setFilters(prev => ({ ...prev, daysRunning: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-900/60 border border-gray-700 rounded-lg text-sm"
              >
                <option value="all">Any Duration</option>
                <option value="7+">7+ Days</option>
                <option value="30+">30+ Days</option>
                <option value="60+">60+ Days</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Sort By</label>
              <select
                value={filters.sortBy}
                onChange={e => setFilters(prev => ({ ...prev, sortBy: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-900/60 border border-gray-700 rounded-lg text-sm"
              >
                <option value="daysRunning">Longest Running</option>
                <option value="spend">Highest Spend</option>
                <option value="engagement">Most Engagement</option>
              </select>
            </div>
          </div>
        </div>

        {/* Ads Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAds.map(ad => (
            <div
              key={ad.id}
              className="bg-gray-800/60 border border-gray-700 rounded-xl overflow-hidden hover:border-indigo-500/50 transition-all group"
            >
              {/* Thumbnail */}
              <div className="relative aspect-video bg-gray-900">
                <div className="absolute inset-0 flex items-center justify-center">
                  <FilmIcon className="w-12 h-12 text-gray-700" />
                </div>
                <div className="absolute top-2 left-2 flex gap-2">
                  <span className={`px-2 py-0.5 ${getPlatformColor(ad.platform)} rounded text-xs font-medium`}>
                    {ad.platform.charAt(0).toUpperCase() + ad.platform.slice(1)}
                  </span>
                  <span className="px-2 py-0.5 bg-gray-800/90 rounded text-xs">
                    {ad.mediaType}
                  </span>
                </div>
                <div className="absolute top-2 right-2">
                  <button
                    onClick={() => toggleSaveAd(ad.id)}
                    className={`p-1.5 rounded-full transition-colors ${
                      savedAds.has(ad.id) ? 'bg-indigo-600 text-white' : 'bg-gray-800/90 text-gray-400 hover:text-white'
                    }`}
                  >
                    <TagIcon className="w-4 h-4" />
                  </button>
                </div>
                <div className="absolute bottom-2 right-2 px-2 py-0.5 bg-green-900/80 text-green-400 rounded text-xs font-medium">
                  {ad.daysRunning} days
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-indigo-400">{ad.advertiser}</span>
                </div>
                <h3 className="font-semibold mb-1 line-clamp-1">{ad.headline}</h3>
                <p className="text-sm text-gray-400 line-clamp-2 mb-3">{ad.body}</p>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-2 text-center mb-3">
                  <div className="bg-gray-900/50 rounded p-2">
                    <div className="text-xs text-gray-500">Likes</div>
                    <div className="font-semibold">{formatNumber(ad.engagement.likes)}</div>
                  </div>
                  <div className="bg-gray-900/50 rounded p-2">
                    <div className="text-xs text-gray-500">Comments</div>
                    <div className="font-semibold">{formatNumber(ad.engagement.comments)}</div>
                  </div>
                  <div className="bg-gray-900/50 rounded p-2">
                    <div className="text-xs text-gray-500">Shares</div>
                    <div className="font-semibold">{formatNumber(ad.engagement.shares)}</div>
                  </div>
                </div>

                {/* Estimated Spend */}
                <div className="flex items-center justify-between text-sm mb-3">
                  <span className="text-gray-400">Est. Spend</span>
                  <span className="font-medium text-green-400">
                    ${formatNumber(ad.estimatedSpend.min)} - ${formatNumber(ad.estimatedSpend.max)}
                  </span>
                </div>

                {/* Hooks */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {ad.hooks.slice(0, 3).map(hook => (
                    <span key={hook} className="px-2 py-0.5 bg-purple-900/30 text-purple-300 rounded text-xs">
                      {hook}
                    </span>
                  ))}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedAd(ad)}
                    className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm transition-colors"
                  >
                    View Details
                  </button>
                  <button className="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg text-sm transition-colors flex items-center gap-1">
                    <SparklesIcon className="w-4 h-4" />
                    Remix
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Detail Modal */}
        {selectedAd && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-gray-900 border-b border-gray-700 p-4 flex items-center justify-between">
                <h2 className="text-xl font-bold">{selectedAd.advertiser}</h2>
                <button
                  onClick={() => setSelectedAd(null)}
                  className="text-gray-400 hover:text-white text-2xl"
                >
                  &times;
                </button>
              </div>
              <div className="p-6 space-y-6">
                {/* Ad Preview */}
                <div className="aspect-video bg-gray-800 rounded-lg flex items-center justify-center">
                  <FilmIcon className="w-16 h-16 text-gray-700" />
                </div>

                {/* Copy */}
                <div className="space-y-3">
                  <div>
                    <label className="text-xs text-gray-400">Headline</label>
                    <p className="font-semibold">{selectedAd.headline}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">Body Copy</label>
                    <p className="text-gray-300">{selectedAd.body}</p>
                  </div>
                  <div>
                    <label className="text-xs text-gray-400">CTA</label>
                    <span className="inline-block px-3 py-1 bg-indigo-600 rounded text-sm">{selectedAd.cta}</span>
                  </div>
                </div>

                {/* Targeting */}
                <div className="bg-gray-800/60 rounded-lg p-4">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    <BarChartIcon className="w-4 h-4" />
                    Targeting Insights
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-gray-400">Age Range:</span>
                      <span className="ml-2">{selectedAd.targeting.ageRange}</span>
                    </div>
                    <div>
                      <span className="text-gray-400">Gender:</span>
                      <span className="ml-2">{selectedAd.targeting.gender}</span>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-400">Interests:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedAd.targeting.interests.map(i => (
                          <span key={i} className="px-2 py-0.5 bg-gray-700 rounded text-xs">{i}</span>
                        ))}
                      </div>
                    </div>
                    <div className="col-span-2">
                      <span className="text-gray-400">Countries:</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedAd.targeting.countries.map(c => (
                          <span key={c} className="px-2 py-0.5 bg-gray-700 rounded text-xs">{c}</span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Hooks & Angles */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-800/60 rounded-lg p-4">
                    <h3 className="font-semibold mb-2">Hooks Used</h3>
                    <div className="flex flex-wrap gap-1">
                      {selectedAd.hooks.map(h => (
                        <span key={h} className="px-2 py-1 bg-purple-900/30 text-purple-300 rounded text-xs">{h}</span>
                      ))}
                    </div>
                  </div>
                  <div className="bg-gray-800/60 rounded-lg p-4">
                    <h3 className="font-semibold mb-2">Ad Angles</h3>
                    <div className="flex flex-wrap gap-1">
                      {selectedAd.angles.map(a => (
                        <span key={a} className="px-2 py-1 bg-green-900/30 text-green-300 rounded text-xs">{a}</span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                  <button className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors flex items-center justify-center gap-2">
                    <SparklesIcon className="w-5 h-5" />
                    Create Similar Ad
                  </button>
                  <button className="px-4 py-2 border border-gray-600 hover:bg-gray-800 rounded-lg transition-colors flex items-center gap-2">
                    <DownloadIcon className="w-5 h-5" />
                    Export
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdSpyDashboard;
