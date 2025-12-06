/**
 * AdIntel Discovery Dashboard - Foreplay-style ad discovery
 *
 * Features:
 * - Faceted search (industry, emotion, hook type)
 * - Winner filtering (30+ days running)
 * - Brand tracking (Spyder)
 * - AI enrichment panel
 * - Boards/Collections
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useAdIntel, AdIntelAd, SearchFilters, TrackedBrand } from '../hooks/useAdIntel';
import {
  SearchIcon,
  FilterIcon,
  BookmarkIcon,
  TrendingUpIcon,
  BarChartIcon,
  SparklesIcon,
  EyeIcon,
  PlayIcon,
  GridIcon,
  ListIcon,
  RefreshIcon,
  TargetIcon,
  GlobeIcon,
} from './icons';

// =============================================================================
// Sub-Components
// =============================================================================

// Facet Filter Component
const FacetFilter: React.FC<{
  title: string;
  options: Array<{ value: string; count: number }>;
  selected: string | null;
  onChange: (value: string | null) => void;
}> = ({ title, options, selected, onChange }) => (
  <div className="mb-4">
    <h4 className="text-sm font-medium text-gray-700 mb-2">{title}</h4>
    <div className="space-y-1 max-h-48 overflow-y-auto">
      <button
        onClick={() => onChange(null)}
        className={`w-full text-left px-2 py-1 text-sm rounded ${
          selected === null ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
        }`}
      >
        All
      </button>
      {options.map(({ value, count }) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          className={`w-full text-left px-2 py-1 text-sm rounded flex justify-between ${
            selected === value ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'
          }`}
        >
          <span className="capitalize">{value}</span>
          <span className="text-gray-400">{count}</span>
        </button>
      ))}
    </div>
  </div>
);

// Winner Badge
const WinnerBadge: React.FC<{ score: number; days: number }> = ({ score, days }) => (
  <div className="flex items-center gap-2">
    {days >= 30 && (
      <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs font-medium rounded-full">
        Winner ({days}d)
      </span>
    )}
    {score > 0 && (
      <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs font-medium rounded-full">
        Score: {score}
      </span>
    )}
  </div>
);

// Ad Card Component
const AdCard: React.FC<{
  ad: AdIntelAd;
  onSave: () => void;
  onEnrich: () => void;
  onViewSimilar: () => void;
  isSaved: boolean;
}> = ({ ad, onSave, onEnrich, onViewSimilar, isSaved }) => (
  <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
    {/* Header */}
    <div className="p-3 border-b border-gray-100 flex justify-between items-start">
      <div>
        <h3 className="font-medium text-gray-900 text-sm">{ad.brand_name}</h3>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500 capitalize">{ad.platform}</span>
          <span className="text-xs text-gray-300">|</span>
          <span className="text-xs text-gray-500 capitalize">{ad.format}</span>
        </div>
      </div>
      <WinnerBadge score={ad.winner_score || 0} days={ad.running_duration_days} />
    </div>

    {/* Thumbnail */}
    <div className="relative aspect-video bg-gray-100">
      {ad.thumbnail_url ? (
        <img
          src={ad.thumbnail_url}
          alt={ad.headline || 'Ad thumbnail'}
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="flex items-center justify-center h-full">
          <PlayIcon className="w-12 h-12 text-gray-300" />
        </div>
      )}
      {ad.format === 'video' && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 hover:opacity-100 transition-opacity">
          <button className="bg-white/90 rounded-full p-3">
            <PlayIcon className="w-6 h-6 text-gray-700" />
          </button>
        </div>
      )}
    </div>

    {/* Content */}
    <div className="p-3 space-y-2">
      {/* Headline */}
      {ad.headline && (
        <p className="text-sm text-gray-900 font-medium line-clamp-2">{ad.headline}</p>
      )}

      {/* Hook */}
      {ad.hook_text && (
        <div className="bg-blue-50 p-2 rounded">
          <p className="text-xs text-blue-600 font-medium">Hook ({ad.hook_type})</p>
          <p className="text-sm text-blue-800 italic">"{ad.hook_text}"</p>
        </div>
      )}

      {/* Emotion */}
      {ad.primary_emotion && (
        <div className="flex flex-wrap gap-1">
          <span className="px-2 py-0.5 bg-pink-100 text-pink-700 text-xs rounded-full">
            {ad.primary_emotion}
          </span>
          {ad.emotional_drivers.slice(0, 2).map((driver, i) => (
            <span key={i} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded-full">
              {driver}
            </span>
          ))}
        </div>
      )}

      {/* Patterns */}
      {ad.winning_patterns.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {ad.winning_patterns.slice(0, 3).map((pattern, i) => (
            <span key={i} className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full">
              {pattern}
            </span>
          ))}
        </div>
      )}
    </div>

    {/* Actions */}
    <div className="px-3 py-2 border-t border-gray-100 flex justify-between">
      <div className="flex gap-2">
        <button
          onClick={onSave}
          className={`p-1.5 rounded ${isSaved ? 'bg-yellow-100 text-yellow-600' : 'hover:bg-gray-100 text-gray-500'}`}
          title="Save to board"
        >
          <BookmarkIcon className="w-4 h-4" />
        </button>
        <button
          onClick={onEnrich}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
          title="AI enrich"
        >
          <SparklesIcon className="w-4 h-4" />
        </button>
        <button
          onClick={onViewSimilar}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-500"
          title="Find similar"
        >
          <TargetIcon className="w-4 h-4" />
        </button>
      </div>
      <span className="text-xs text-gray-400">
        {ad.running_duration_days}d running
      </span>
    </div>
  </div>
);

// Brand Tracker Card
const BrandTrackerCard: React.FC<{
  brand: TrackedBrand;
  onViewAds: () => void;
  onUntrack: () => void;
}> = ({ brand, onViewAds, onUntrack }) => (
  <div className="bg-white rounded-lg border border-gray-200 p-4">
    <div className="flex justify-between items-start mb-3">
      <div>
        <h4 className="font-medium text-gray-900">{brand.brand_name}</h4>
        <span className={`text-xs px-2 py-0.5 rounded-full ${
          brand.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
        }`}>
          {brand.status}
        </span>
      </div>
      <button onClick={onUntrack} className="text-gray-400 hover:text-red-500">
        &times;
      </button>
    </div>
    <div className="grid grid-cols-2 gap-4 text-sm">
      <div>
        <p className="text-gray-500">Total Ads</p>
        <p className="font-semibold">{brand.ad_count}</p>
      </div>
      <div>
        <p className="text-gray-500">Winners</p>
        <p className="font-semibold text-green-600">{brand.winner_count}</p>
      </div>
    </div>
    <button
      onClick={onViewAds}
      className="mt-3 w-full py-2 bg-blue-50 text-blue-600 rounded text-sm font-medium hover:bg-blue-100"
    >
      View Ads
    </button>
  </div>
);

// =============================================================================
// Main Discovery Dashboard
// =============================================================================

const DiscoveryDashboard: React.FC = () => {
  // AdIntel Hook
  const {
    searchAds,
    getWinners,
    findSimilar,
    trackBrand,
    getTrackedBrands,
    untrackBrand,
    enrichAd,
    getTrends,
    loading,
    error,
    results,
    trends,
    trackedBrands,
  } = useAdIntel();

  // Local state
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({});
  const [selectedIndustry, setSelectedIndustry] = useState<string | null>(null);
  const [selectedEmotion, setSelectedEmotion] = useState<string | null>(null);
  const [selectedHookType, setSelectedHookType] = useState<string | null>(null);
  const [winnersOnly, setWinnersOnly] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(true);
  const [activeTab, setActiveTab] = useState<'discovery' | 'spyder' | 'trends'>('discovery');
  const [savedAdIds, setSavedAdIds] = useState<Set<string>>(new Set());
  const [newBrandName, setNewBrandName] = useState('');

  // Load initial data
  useEffect(() => {
    getTrends();
    getTrackedBrands();
  }, []);

  // Search handler
  const handleSearch = useCallback(async () => {
    await searchAds({
      query: query || '*',
      industry: selectedIndustry || undefined,
      emotion: selectedEmotion || undefined,
      hook_type: selectedHookType || undefined,
      winners_only: winnersOnly,
      page: 1,
      per_page: 20,
    });
  }, [query, selectedIndustry, selectedEmotion, selectedHookType, winnersOnly, searchAds]);

  // Handle filter changes
  useEffect(() => {
    if (activeTab === 'discovery') {
      handleSearch();
    }
  }, [selectedIndustry, selectedEmotion, selectedHookType, winnersOnly]);

  // Track new brand
  const handleTrackBrand = async () => {
    if (newBrandName.trim()) {
      await trackBrand(newBrandName.trim());
      setNewBrandName('');
    }
  };

  // Save ad
  const handleSaveAd = (adId: string) => {
    setSavedAdIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(adId)) {
        newSet.delete(adId);
      } else {
        newSet.add(adId);
      }
      return newSet;
    });
  };

  // Enrich ad
  const handleEnrichAd = async (ad: AdIntelAd) => {
    await enrichAd(ad.ad_id, ad.video_url || undefined);
    handleSearch(); // Refresh to show enriched data
  };

  // Find similar
  const handleFindSimilar = async (adId: string) => {
    const similar = await findSimilar(adId);
    // Could open a modal with similar ads
    console.log('Similar ads:', similar);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold">AdIntel Discovery</h1>
          <p className="text-indigo-200 mt-1">
            Find winning ads, track competitors, discover patterns
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto">
          <nav className="flex gap-8 px-6">
            {[
              { id: 'discovery', label: 'Discovery', icon: SearchIcon },
              { id: 'spyder', label: 'Brand Tracker', icon: TargetIcon },
              { id: 'trends', label: 'Trends', icon: TrendingUpIcon },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`flex items-center gap-2 py-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-indigo-600 text-indigo-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                <tab.icon className="w-5 h-5" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Discovery Tab */}
        {activeTab === 'discovery' && (
          <div className="flex gap-6">
            {/* Filters Sidebar */}
            {showFilters && (
              <div className="w-64 flex-shrink-0">
                <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="font-semibold">Filters</h3>
                    <button
                      onClick={() => {
                        setSelectedIndustry(null);
                        setSelectedEmotion(null);
                        setSelectedHookType(null);
                        setWinnersOnly(false);
                      }}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Clear all
                    </button>
                  </div>

                  {/* Winners Toggle */}
                  <label className="flex items-center gap-2 mb-4 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={winnersOnly}
                      onChange={(e) => setWinnersOnly(e.target.checked)}
                      className="rounded border-gray-300 text-indigo-600"
                    />
                    <span className="text-sm">Winners only (30+ days)</span>
                  </label>

                  {/* Industry Facet */}
                  {results?.facets.industry && (
                    <FacetFilter
                      title="Industry"
                      options={results.facets.industry}
                      selected={selectedIndustry}
                      onChange={setSelectedIndustry}
                    />
                  )}

                  {/* Emotion Facet */}
                  {results?.facets.primary_emotion && (
                    <FacetFilter
                      title="Emotion"
                      options={results.facets.primary_emotion}
                      selected={selectedEmotion}
                      onChange={setSelectedEmotion}
                    />
                  )}

                  {/* Hook Type Facet */}
                  {results?.facets.hook_type && (
                    <FacetFilter
                      title="Hook Type"
                      options={results.facets.hook_type}
                      selected={selectedHookType}
                      onChange={setSelectedHookType}
                    />
                  )}
                </div>
              </div>
            )}

            {/* Main Content */}
            <div className="flex-1">
              {/* Search Bar */}
              <div className="flex gap-2 mb-6">
                <div className="relative flex-1">
                  <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    placeholder="Search ads by keyword, brand, or industry..."
                    className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className={`p-3 rounded-lg border ${showFilters ? 'bg-indigo-100 border-indigo-300' : 'border-gray-300'}`}
                >
                  <FilterIcon className="w-5 h-5" />
                </button>
                <div className="flex border border-gray-300 rounded-lg overflow-hidden">
                  <button
                    onClick={() => setViewMode('grid')}
                    className={`p-3 ${viewMode === 'grid' ? 'bg-gray-100' : ''}`}
                  >
                    <GridIcon className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setViewMode('list')}
                    className={`p-3 ${viewMode === 'list' ? 'bg-gray-100' : ''}`}
                  >
                    <ListIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-red-700">
                  {error}
                </div>
              )}

              {/* Results */}
              {results && (
                <>
                  <div className="flex justify-between items-center mb-4">
                    <p className="text-sm text-gray-600">
                      Found <span className="font-semibold">{results.total}</span> ads
                      {results.remaining_credits !== undefined && (
                        <span className="ml-2 text-gray-400">
                          ({results.remaining_credits} credits remaining)
                        </span>
                      )}
                    </p>
                  </div>

                  <div className={viewMode === 'grid'
                    ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                    : 'space-y-4'
                  }>
                    {results.hits.map(ad => (
                      <AdCard
                        key={ad.ad_id}
                        ad={ad}
                        onSave={() => handleSaveAd(ad.ad_id)}
                        onEnrich={() => handleEnrichAd(ad)}
                        onViewSimilar={() => handleFindSimilar(ad.ad_id)}
                        isSaved={savedAdIds.has(ad.ad_id)}
                      />
                    ))}
                  </div>

                  {results.hits.length === 0 && (
                    <div className="text-center py-12">
                      <SearchIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                      <p className="text-gray-500">No ads found. Try different filters.</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {/* Brand Tracker Tab */}
        {activeTab === 'spyder' && (
          <div>
            {/* Add Brand */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
              <h3 className="font-semibold mb-4">Track a Competitor</h3>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newBrandName}
                  onChange={(e) => setNewBrandName(e.target.value)}
                  placeholder="Enter brand name (e.g., Nike, Gymshark)"
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={handleTrackBrand}
                  disabled={loading || !newBrandName.trim()}
                  className="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50"
                >
                  Start Tracking
                </button>
              </div>
            </div>

            {/* Tracked Brands */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {trackedBrands.map(brand => (
                <BrandTrackerCard
                  key={brand.brand_id}
                  brand={brand}
                  onViewAds={() => {
                    setQuery(brand.brand_name);
                    setActiveTab('discovery');
                    searchAds({ brand_name: brand.brand_name });
                  }}
                  onUntrack={() => untrackBrand(brand.brand_id)}
                />
              ))}
            </div>

            {trackedBrands.length === 0 && (
              <div className="text-center py-12">
                <TargetIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No brands tracked yet. Add one above!</p>
              </div>
            )}
          </div>
        )}

        {/* Trends Tab */}
        {activeTab === 'trends' && trends && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* By Industry */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <GlobeIcon className="w-5 h-5 text-indigo-600" />
                Winners by Industry
              </h3>
              <div className="space-y-2">
                {trends.by_industry.slice(0, 10).map(({ value, count }) => (
                  <div key={value} className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-indigo-500 h-2 rounded-full"
                        style={{ width: `${(count / trends.total_winners) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-600 w-24 capitalize">{value}</span>
                    <span className="text-sm font-medium w-12 text-right">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* By Emotion */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <SparklesIcon className="w-5 h-5 text-pink-600" />
                Top Emotions
              </h3>
              <div className="flex flex-wrap gap-2">
                {trends.by_emotion.slice(0, 10).map(({ value, count }) => (
                  <span
                    key={value}
                    className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full text-sm"
                  >
                    {value} ({count})
                  </span>
                ))}
              </div>
            </div>

            {/* By Hook Type */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <BarChartIcon className="w-5 h-5 text-green-600" />
                Top Hook Types
              </h3>
              <div className="flex flex-wrap gap-2">
                {trends.by_hook_type.slice(0, 10).map(({ value, count }) => (
                  <span
                    key={value}
                    className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm capitalize"
                  >
                    {value} ({count})
                  </span>
                ))}
              </div>
            </div>

            {/* Winning Patterns */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold mb-4 flex items-center gap-2">
                <TrendingUpIcon className="w-5 h-5 text-purple-600" />
                Winning Patterns
              </h3>
              <div className="flex flex-wrap gap-2">
                {trends.top_patterns.slice(0, 10).map(({ value, count }) => (
                  <span
                    key={value}
                    className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm"
                  >
                    {value} ({count})
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DiscoveryDashboard;
