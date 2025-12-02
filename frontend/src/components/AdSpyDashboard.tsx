import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  SearchIcon,
  FilterIcon,
  BookmarkIcon,
  DownloadIcon,
  GridIcon,
  ListIcon,
  PlayIcon,
  TrendingUpIcon,
  BarChartIcon,
  GlobeIcon,
  CalendarIcon,
  VideoIcon,
  ImageIcon,
  RefreshIcon,
  SparklesIcon,
  EyeIcon,
  TargetIcon,
} from './icons';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface AdLibraryAd {
  id: string;
  ad_archive_id: string;
  page_id: string;
  page_name: string;
  ad_creative_bodies: string[];
  ad_creative_link_captions: string[];
  ad_creative_link_descriptions: string[];
  ad_creative_link_titles: string[];
  ad_delivery_start_time: string;
  ad_delivery_stop_time?: string;
  ad_snapshot_url: string;
  currency: string;
  funding_entity: string;
  impressions?: { lower_bound: number; upper_bound: number };
  spend?: { lower_bound: number; upper_bound: number };
  bylines?: string;
  languages: string[];
  publisher_platforms: string[];
  estimated_audience_size?: { lower_bound: number; upper_bound: number };
}

interface SearchFilters {
  searchTerm: string;
  countries: string[];
  platforms: string[];
  mediaType: 'ALL' | 'VIDEO' | 'IMAGE';
  activeStatus: 'ACTIVE' | 'INACTIVE' | 'ALL';
  dateRange: 'all' | '7d' | '30d' | '90d' | 'custom';
  customStartDate?: string;
  customEndDate?: string;
}

interface SavedCollection {
  id: string;
  name: string;
  ads: AdLibraryAd[];
  createdAt: string;
  updatedAt: string;
}

interface PatternAnalysis {
  total_ads: number;
  common_hooks: Array<[string, number]>;
  cta_distribution: Record<string, number>;
  platform_distribution: Record<string, number>;
  avg_copy_length_words: number;
  avg_active_duration_days?: number;
  languages_used: string[];
}

interface CompetitorPage {
  page_id: string;
  page_name: string;
  tracked_since: string;
  total_ads: number;
  active_ads: number;
  last_updated: string;
}

interface AdSpyDashboardProps {
  onSaveAd?: (ad: AdLibraryAd) => void;
  onRemixAd?: (ad: AdLibraryAd) => void;
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function searchAdsLibrary(filters: SearchFilters): Promise<AdLibraryAd[]> {
  const response = await fetch(`${API_BASE_URL}/meta/ads-library/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      search_terms: filters.searchTerm,
      countries: filters.countries,
      platforms: filters.platforms,
      media_type: filters.mediaType,
      active_status: filters.activeStatus,
      limit: 100,
    }),
  });

  if (!response.ok) {
    throw new Error(`Search failed: ${response.statusText}`);
  }

  return response.json();
}

async function getPageAds(pageId: string): Promise<AdLibraryAd[]> {
  const response = await fetch(`${API_BASE_URL}/meta/ads-library/page/${pageId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch page ads: ${response.statusText}`);
  }
  return response.json();
}

async function analyzePatterns(ads: AdLibraryAd[]): Promise<PatternAnalysis> {
  const response = await fetch(`${API_BASE_URL}/meta/ads-library/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ads }),
  });

  if (!response.ok) {
    throw new Error(`Analysis failed: ${response.statusText}`);
  }

  return response.json();
}

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function formatDateRange(ad: AdLibraryAd): string {
  const start = new Date(ad.ad_delivery_start_time);
  const end = ad.ad_delivery_stop_time ? new Date(ad.ad_delivery_stop_time) : null;

  const startStr = start.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  if (end) {
    const endStr = end.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    return `${startStr} - ${endStr}`;
  }

  return `${startStr} - Active`;
}

function extractHooks(ad: AdLibraryAd): string[] {
  const hooks: string[] = [];

  ad.ad_creative_bodies.forEach(body => {
    const sentences = body.split(/[.!?]/);
    if (sentences.length > 0) {
      const hook = sentences[0].trim();
      if (hook.length > 10) {
        hooks.push(hook);
      }
    }
  });

  return hooks;
}

function extractCTAs(ad: AdLibraryAd): string[] {
  const ctaKeywords = [
    'learn more', 'shop now', 'sign up', 'get started', 'download',
    'buy now', 'order now', 'book now', 'subscribe', 'register',
    'try free', 'claim offer', 'get quote', 'contact us', 'apply now'
  ];

  const ctas = new Set<string>();

  ad.ad_creative_bodies.forEach(body => {
    const lowerBody = body.toLowerCase();
    ctaKeywords.forEach(cta => {
      if (lowerBody.includes(cta)) {
        ctas.add(cta);
      }
    });
  });

  ad.ad_creative_link_titles.forEach(title => {
    const lowerTitle = title.toLowerCase();
    ctaKeywords.forEach(cta => {
      if (lowerTitle.includes(cta)) {
        ctas.add(cta);
      }
    });
  });

  return Array.from(ctas);
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

const SearchBar: React.FC<{
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void;
  isSearching: boolean;
}> = ({ value, onChange, onSearch, isSearching }) => {
  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && onSearch()}
          placeholder="Search for ads (e.g., 'weight loss', 'SaaS', 'DTC brands')..."
          className="w-full pl-10 pr-4 py-3 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          disabled={isSearching}
        />
      </div>
      <button
        onClick={onSearch}
        disabled={isSearching}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {isSearching ? 'Searching...' : 'Search'}
      </button>
    </div>
  );
};

const FilterPanel: React.FC<{
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  isOpen: boolean;
}> = ({ filters, onChange, isOpen }) => {
  if (!isOpen) return null;

  const countries = [
    { code: 'US', name: 'United States' },
    { code: 'GB', name: 'United Kingdom' },
    { code: 'CA', name: 'Canada' },
    { code: 'AU', name: 'Australia' },
    { code: 'DE', name: 'Germany' },
    { code: 'FR', name: 'France' },
    { code: 'ES', name: 'Spain' },
    { code: 'IT', name: 'Italy' },
  ];

  const platforms = ['facebook', 'instagram', 'audience_network', 'messenger'];

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
      <h3 className="font-semibold text-lg">Filters</h3>

      {/* Countries */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <GlobeIcon className="inline w-4 h-4 mr-1" />
          Countries
        </label>
        <div className="space-y-2 max-h-48 overflow-y-auto">
          {countries.map(country => (
            <label key={country.code} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
              <input
                type="checkbox"
                checked={filters.countries.includes(country.code)}
                onChange={(e) => {
                  const newCountries = e.target.checked
                    ? [...filters.countries, country.code]
                    : filters.countries.filter(c => c !== country.code);
                  onChange({ ...filters, countries: newCountries });
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm">{country.name}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Platforms */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Platforms
        </label>
        <div className="space-y-2">
          {platforms.map(platform => (
            <label key={platform} className="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded">
              <input
                type="checkbox"
                checked={filters.platforms.includes(platform)}
                onChange={(e) => {
                  const newPlatforms = e.target.checked
                    ? [...filters.platforms, platform]
                    : filters.platforms.filter(p => p !== platform);
                  onChange({ ...filters, platforms: newPlatforms });
                }}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm capitalize">{platform.replace('_', ' ')}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Media Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Media Type
        </label>
        <select
          value={filters.mediaType}
          onChange={(e) => onChange({ ...filters, mediaType: e.target.value as any })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="ALL">All Types</option>
          <option value="VIDEO">Video Only</option>
          <option value="IMAGE">Image Only</option>
        </select>
      </div>

      {/* Active Status */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Ad Status
        </label>
        <select
          value={filters.activeStatus}
          onChange={(e) => onChange({ ...filters, activeStatus: e.target.value as any })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="ALL">All Ads</option>
          <option value="ACTIVE">Active Only</option>
          <option value="INACTIVE">Inactive Only</option>
        </select>
      </div>

      {/* Date Range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          <CalendarIcon className="inline w-4 h-4 mr-1" />
          Date Range
        </label>
        <select
          value={filters.dateRange}
          onChange={(e) => onChange({ ...filters, dateRange: e.target.value as any })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="all">All Time</option>
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
          <option value="custom">Custom Range</option>
        </select>
      </div>
    </div>
  );
};

const AdCard: React.FC<{
  ad: AdLibraryAd;
  onSave: () => void;
  onRemix: () => void;
  onViewSnapshot: () => void;
  isSaved: boolean;
}> = ({ ad, onSave, onRemix, onViewSnapshot, isSaved }) => {
  const impressions = ad.impressions
    ? `${formatNumber(ad.impressions.lower_bound)} - ${formatNumber(ad.impressions.upper_bound)}`
    : 'N/A';

  const spend = ad.spend
    ? `${ad.currency} ${ad.spend.lower_bound.toLocaleString()} - ${ad.spend.upper_bound.toLocaleString()}`
    : 'N/A';

  const hooks = extractHooks(ad);
  const ctas = extractCTAs(ad);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">{ad.page_name}</h3>
            <p className="text-sm text-gray-500 mt-1">{formatDateRange(ad)}</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onSave}
              className={`p-2 rounded-lg transition-colors ${
                isSaved
                  ? 'bg-yellow-100 text-yellow-600 hover:bg-yellow-200'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
              title={isSaved ? 'Saved' : 'Save to collection'}
            >
              <BookmarkIcon className="w-5 h-5" />
            </button>
            <button
              onClick={onRemix}
              className="p-2 bg-blue-100 text-blue-600 rounded-lg hover:bg-blue-200 transition-colors"
              title="Remix this ad"
            >
              <SparklesIcon className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Preview */}
      <div className="relative bg-gray-100 aspect-[9/16] sm:aspect-video flex items-center justify-center cursor-pointer" onClick={onViewSnapshot}>
        <div className="absolute inset-0 flex items-center justify-center">
          {ad.publisher_platforms.includes('instagram') ? (
            <ImageIcon className="w-16 h-16 text-gray-400" />
          ) : (
            <VideoIcon className="w-16 h-16 text-gray-400" />
          )}
        </div>
        <button className="relative z-10 bg-white/90 hover:bg-white rounded-full p-4 shadow-lg transition-all">
          <EyeIcon className="w-6 h-6 text-gray-700" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        {/* Primary Text */}
        {ad.ad_creative_bodies.length > 0 && (
          <div>
            <p className="text-sm text-gray-700 line-clamp-3">{ad.ad_creative_bodies[0]}</p>
          </div>
        )}

        {/* Hooks */}
        {hooks.length > 0 && (
          <div>
            <p className="text-xs font-medium text-gray-500 mb-1">Hook:</p>
            <p className="text-sm text-blue-600 italic">"{hooks[0]}"</p>
          </div>
        )}

        {/* CTAs */}
        {ctas.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {ctas.map((cta, idx) => (
              <span key={idx} className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full capitalize">
                {cta}
              </span>
            ))}
          </div>
        )}

        {/* Platforms */}
        <div className="flex flex-wrap gap-2">
          {ad.publisher_platforms.map((platform, idx) => (
            <span key={idx} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded capitalize">
              {platform}
            </span>
          ))}
        </div>

        {/* Metrics */}
        <div className="pt-3 border-t border-gray-200 grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-gray-500">Impressions</p>
            <p className="text-sm font-semibold text-gray-900">{impressions}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Spend</p>
            <p className="text-sm font-semibold text-gray-900">{spend}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

const PatternAnalysisView: React.FC<{
  analysis: PatternAnalysis | null;
  isLoading: boolean;
}> = ({ analysis, isLoading }) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 space-y-6">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <BarChartIcon className="w-5 h-5 text-blue-600" />
        Pattern Analysis
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Summary Stats */}
        <div className="space-y-4">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600 font-medium">Total Ads</p>
            <p className="text-3xl font-bold text-blue-700">{analysis.total_ads}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-green-600 font-medium">Avg. Copy Length</p>
            <p className="text-3xl font-bold text-green-700">{analysis.avg_copy_length_words} words</p>
          </div>
          {analysis.avg_active_duration_days && (
            <div className="bg-purple-50 rounded-lg p-4">
              <p className="text-sm text-purple-600 font-medium">Avg. Duration</p>
              <p className="text-3xl font-bold text-purple-700">{analysis.avg_active_duration_days} days</p>
            </div>
          )}
        </div>

        {/* Common Hooks */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Top Hooks</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {analysis.common_hooks.slice(0, 10).map(([hook, count], idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm">
                <span className="text-blue-600 font-medium">{idx + 1}.</span>
                <span className="flex-1 text-gray-700">"{hook}"</span>
                <span className="text-gray-500">({count})</span>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Distribution */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">CTA Distribution</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {Object.entries(analysis.cta_distribution)
              .sort(([, a], [, b]) => b - a)
              .map(([cta, count]) => (
                <div key={cta} className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(count / analysis.total_ads) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-600 capitalize w-24 text-right">{cta}</span>
                  <span className="text-xs font-medium text-gray-900 w-8 text-right">{count}</span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Platform & Language Distribution */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-gray-200">
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Platform Distribution</h4>
          <div className="space-y-2">
            {Object.entries(analysis.platform_distribution).map(([platform, count]) => (
              <div key={platform} className="flex items-center gap-3">
                <span className="text-sm capitalize flex-1">{platform}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${(count / analysis.total_ads) * 100}%` }}
                  ></div>
                </div>
                <span className="text-sm font-medium w-12 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <h4 className="font-medium text-gray-900 mb-3">Languages</h4>
          <div className="flex flex-wrap gap-2">
            {analysis.languages_used.map((lang, idx) => (
              <span key={idx} className="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">
                {lang}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const AdSpyDashboard: React.FC<AdSpyDashboardProps> = ({ onSaveAd, onRemixAd }) => {
  const [filters, setFilters] = useState<SearchFilters>({
    searchTerm: '',
    countries: ['US'],
    platforms: ['facebook', 'instagram'],
    mediaType: 'ALL',
    activeStatus: 'ACTIVE',
    dateRange: '30d',
  });

  const [ads, setAds] = useState<AdLibraryAd[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [savedAdIds, setSavedAdIds] = useState<Set<string>>(new Set());
  const [collections, setCollections] = useState<SavedCollection[]>([]);
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [patternAnalysis, setPatternAnalysis] = useState<PatternAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [competitorPages, setCompetitorPages] = useState<CompetitorPage[]>([]);
  const [showPatterns, setShowPatterns] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load saved collections from localStorage
  useEffect(() => {
    const savedCollections = localStorage.getItem('adSpyCollections');
    if (savedCollections) {
      const parsed = JSON.parse(savedCollections);
      setCollections(parsed);

      const allSavedIds = new Set<string>();
      parsed.forEach((col: SavedCollection) => {
        col.ads.forEach(ad => allSavedIds.add(ad.ad_archive_id));
      });
      setSavedAdIds(allSavedIds);
    }
  }, []);

  // Save collections to localStorage
  const saveCollectionsToStorage = useCallback((cols: SavedCollection[]) => {
    localStorage.setItem('adSpyCollections', JSON.stringify(cols));
  }, []);

  // Handle search
  const handleSearch = useCallback(async () => {
    if (!filters.searchTerm.trim()) {
      setError('Please enter a search term');
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const results = await searchAdsLibrary(filters);
      setAds(results);

      if (results.length === 0) {
        setError('No ads found. Try adjusting your filters.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  }, [filters]);

  // Analyze patterns
  const handleAnalyzePatterns = useCallback(async () => {
    if (ads.length === 0) {
      setError('No ads to analyze. Search for ads first.');
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const analysis = await analyzePatterns(ads);
      setPatternAnalysis(analysis);
      setShowPatterns(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  }, [ads]);

  // Save ad to collection
  const handleSaveAd = useCallback((ad: AdLibraryAd) => {
    const defaultCollectionId = 'default';
    let updatedCollections = [...collections];

    let defaultCollection = updatedCollections.find(c => c.id === defaultCollectionId);

    if (!defaultCollection) {
      defaultCollection = {
        id: defaultCollectionId,
        name: 'Saved Ads',
        ads: [],
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
      };
      updatedCollections.push(defaultCollection);
    }

    const isAlreadySaved = defaultCollection.ads.some(a => a.ad_archive_id === ad.ad_archive_id);

    if (isAlreadySaved) {
      defaultCollection.ads = defaultCollection.ads.filter(a => a.ad_archive_id !== ad.ad_archive_id);
      setSavedAdIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(ad.ad_archive_id);
        return newSet;
      });
    } else {
      defaultCollection.ads.push(ad);
      defaultCollection.updatedAt = new Date().toISOString();
      setSavedAdIds(prev => new Set(prev).add(ad.ad_archive_id));
    }

    setCollections(updatedCollections);
    saveCollectionsToStorage(updatedCollections);

    if (onSaveAd) {
      onSaveAd(ad);
    }
  }, [collections, saveCollectionsToStorage, onSaveAd]);

  // Remix ad
  const handleRemixAd = useCallback((ad: AdLibraryAd) => {
    if (onRemixAd) {
      onRemixAd(ad);
    }
  }, [onRemixAd]);

  // View ad snapshot
  const handleViewSnapshot = useCallback((ad: AdLibraryAd) => {
    window.open(ad.ad_snapshot_url, '_blank');
  }, []);

  // Export to CSV
  const handleExportCSV = useCallback(() => {
    if (ads.length === 0) {
      setError('No ads to export');
      return;
    }

    const headers = ['Page Name', 'Ad Text', 'Start Date', 'End Date', 'Platforms', 'Impressions', 'Spend'];
    const rows = ads.map(ad => [
      ad.page_name,
      ad.ad_creative_bodies[0] || '',
      ad.ad_delivery_start_time,
      ad.ad_delivery_stop_time || 'Active',
      ad.publisher_platforms.join('; '),
      ad.impressions ? `${ad.impressions.lower_bound}-${ad.impressions.upper_bound}` : 'N/A',
      ad.spend ? `${ad.spend.lower_bound}-${ad.spend.upper_bound}` : 'N/A',
    ]);

    const csv = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ad-spy-export-${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [ads]);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto mb-6">
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg p-6 text-white">
          <h1 className="text-3xl font-bold mb-2">Ad Spy & Competitor Intelligence</h1>
          <p className="text-purple-100">Search, analyze, and remix competitor ads from Meta Ads Library</p>
        </div>
      </div>

      {/* Search & Controls */}
      <div className="max-w-7xl mx-auto mb-6 space-y-4">
        <SearchBar
          value={filters.searchTerm}
          onChange={(value) => setFilters({ ...filters, searchTerm: value })}
          onSearch={handleSearch}
          isSearching={isSearching}
        />

        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                showFilters
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              <FilterIcon className="inline w-4 h-4 mr-2" />
              Filters
            </button>

            {ads.length > 0 && (
              <>
                <button
                  onClick={handleAnalyzePatterns}
                  disabled={isAnalyzing}
                  className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 disabled:opacity-50"
                >
                  <BarChartIcon className="inline w-4 h-4 mr-2" />
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Patterns'}
                </button>

                <button
                  onClick={handleExportCSV}
                  className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg font-medium hover:bg-gray-50"
                >
                  <DownloadIcon className="inline w-4 h-4 mr-2" />
                  Export CSV
                </button>
              </>
            )}
          </div>

          {ads.length > 0 && (
            <div className="flex gap-2 bg-white rounded-lg border border-gray-300 p-1">
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded ${viewMode === 'grid' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
              >
                <GridIcon className="w-5 h-5" />
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-200' : 'hover:bg-gray-100'}`}
              >
                <ListIcon className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto mb-6">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
            {error}
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filter Panel */}
          {showFilters && (
            <div className="lg:col-span-1">
              <FilterPanel filters={filters} onChange={setFilters} isOpen={showFilters} />
            </div>
          )}

          {/* Ads Grid/List */}
          <div className={showFilters ? 'lg:col-span-3' : 'lg:col-span-4'}>
            {/* Pattern Analysis */}
            {showPatterns && (
              <div className="mb-6">
                <PatternAnalysisView analysis={patternAnalysis} isLoading={isAnalyzing} />
              </div>
            )}

            {/* Results */}
            {ads.length > 0 ? (
              <>
                <div className="mb-4 text-sm text-gray-600">
                  Found {ads.length} ads
                </div>
                <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6' : 'space-y-4'}>
                  {ads.map(ad => (
                    <AdCard
                      key={ad.ad_archive_id}
                      ad={ad}
                      onSave={() => handleSaveAd(ad)}
                      onRemix={() => handleRemixAd(ad)}
                      onViewSnapshot={() => handleViewSnapshot(ad)}
                      isSaved={savedAdIds.has(ad.ad_archive_id)}
                    />
                  ))}
                </div>
              </>
            ) : !isSearching ? (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <SearchIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-900 mb-2">Start Searching</h3>
                <p className="text-gray-500 max-w-md mx-auto">
                  Enter keywords to search Meta Ads Library for competitor ads. Analyze patterns, save favorites, and remix winning creatives.
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-gray-600">Searching Meta Ads Library...</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdSpyDashboard;
