// ==========================================
// AdSpyPage.tsx - Competitor Research
// ==========================================
//
// ============================================================================
// 🔴 CRITICAL ANALYSIS FINDINGS (December 2024)
// ============================================================================
//
// STATUS: 100% FAKE UI - No real competitor tracking!
//
// WHAT'S FAKE:
// - trendingAds array (line 19-24): HARDCODED mock data
//   "Competitor A/B/C/D" - these are not real competitors
//   Views (2.4M, 1.8M) - completely made up
//   Engagement (8.2%, 6.5%) - fabricated percentages
// - Search button: Does NOTHING (no backend route)
// - "Add Competitor" button: Does NOTHING (no tracking system)
// - "View All" button: Does NOTHING (no more data)
//
// WHAT IT SHOULD DO:
// 1. Connect to Meta Ads Library API for real competitor ads
// 2. Use Apify/PhantomBuster to scrape competitor ad creatives
// 3. Store tracked competitors in database
// 4. Show real engagement metrics from actual ads
//
// BACKEND REQUIREMENT:
// - /api/competitors/track - Add competitor to watch list
// - /api/competitors/ads - Fetch competitor's ads
// - /api/ads/trending - Get trending ads by category
//
// FAST FIX: Use Apify's Meta Ads Library scraper actor
// Or: Allow manual CSV upload of competitor ad data
// ============================================================================

import { useState, useEffect, useCallback } from 'react'
import { motion } from 'framer-motion'
import {
  MagnifyingGlassIcon,
  GlobeAltIcon,
  PlayIcon,
  BookmarkIcon,
  ArrowTrendingUpIcon,
  FunnelIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Input } from '@/components/catalyst/input'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'

import { API_BASE_URL } from '../config/api';

interface TrendingAd {
  id: string;
  brand: string;
  title: string;
  views: string;
  engagement: string;
  platform: string;
  thumbnail?: string;
  videoUrl?: string;
  datePublished?: string;
  category?: string;
}

interface SearchFilters {
  platform: string;
  category: string;
  minEngagement: string;
  dateRange: string;
  sortBy: string;
}

function TrendingAdCard({ ad }: { ad: TrendingAd }) {
  return (
    <motion.div
      whileHover={{ y: -4 }}
      className="rounded-xl bg-zinc-900 border border-zinc-800 overflow-hidden cursor-pointer group"
    >
      <div className="aspect-video bg-gradient-to-br from-zinc-800 to-zinc-900 relative">
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/40">
          <PlayIcon className="h-12 w-12 text-white" />
        </div>
        <Badge color="violet" className="absolute top-3 left-3">{ad.platform}</Badge>
      </div>
      <div className="p-4">
        <p className="text-zinc-400 text-xs">{ad.brand}</p>
        <h3 className="text-white font-medium mt-1">{ad.title}</h3>
        <div className="flex items-center gap-4 mt-3">
          <div className="flex items-center gap-1 text-zinc-400 text-sm">
            <GlobeAltIcon className="h-4 w-4" />
            {ad.views}
          </div>
          <div className="flex items-center gap-1 text-emerald-400 text-sm">
            <ArrowTrendingUpIcon className="h-4 w-4" />
            {ad.engagement}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

const DEFAULT_FILTERS: SearchFilters = {
  platform: 'all',
  category: 'all',
  minEngagement: '0',
  dateRange: '30',
  sortBy: 'engagement',
};

export function AdSpyPage() {
  const [search, setSearch] = useState('')
  const [trendingAds, setTrendingAds] = useState<TrendingAd[]>([])
  const [searchResults, setSearchResults] = useState<TrendingAd[]>([])
  const [loading, setLoading] = useState(true)
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS)
  const [hasSearched, setHasSearched] = useState(false)

  // Fetch trending ads on mount
  useEffect(() => {
    const fetchTrendingAds = async () => {
      try {
        setError(null)
        const response = await fetch(`${API_BASE_URL}/api/ads/trending`)
        if (response.ok) {
          const data = await response.json()
          setTrendingAds(data.ads || [])
        } else {
          throw new Error(`API returned ${response.status}`)
        }
      } catch (err) {
        console.error('Failed to fetch trending ads:', err)
        setError('Unable to load trending ads')
      } finally {
        setLoading(false)
      }
    }

    fetchTrendingAds()
  }, [])

  // Search ads with filters
  const handleSearch = useCallback(async () => {
    if (!search.trim() && filters.platform === 'all' && filters.category === 'all') {
      setSearchResults([])
      setHasSearched(false)
      return
    }

    setSearching(true)
    setError(null)
    setHasSearched(true)

    try {
      const queryParams = new URLSearchParams({
        q: search.trim(),
        platform: filters.platform,
        category: filters.category,
        minEngagement: filters.minEngagement,
        dateRange: filters.dateRange,
        sortBy: filters.sortBy,
      })

      const response = await fetch(`${API_BASE_URL}/api/ads/search?${queryParams}`)

      if (response.ok) {
        const data = await response.json()
        setSearchResults(data.ads || [])
      } else if (response.status === 404) {
        // No results found
        setSearchResults([])
      } else {
        throw new Error(`Search failed with status ${response.status}`)
      }
    } catch (err: any) {
      console.error('Search failed:', err)
      setError(`Search failed: ${err.message}`)
      setSearchResults([])
    } finally {
      setSearching(false)
    }
  }, [search, filters])

  // Handle Enter key in search input
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  // Clear search and reset
  const clearSearch = () => {
    setSearch('')
    setSearchResults([])
    setHasSearched(false)
    setFilters(DEFAULT_FILTERS)
  }

  // Update filter
  const updateFilter = (key: keyof SearchFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  // Determine which ads to display
  const displayedAds = hasSearched ? searchResults : trendingAds

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div>
        <Heading level={1} className="text-white">Ad Spy</Heading>
        <Text className="text-zinc-400 mt-1">Research competitor ads and discover winning creatives.</Text>
      </div>

      {/* Search Bar */}
      <div className="space-y-4">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Search by brand, keyword, or URL..."
              className="pl-10"
            />
            {search && (
              <button
                onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-white"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            )}
          </div>
          <Button
            color="violet"
            onClick={handleSearch}
            disabled={searching}
          >
            {searching ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                Searching...
              </div>
            ) : (
              'Search'
            )}
          </Button>
          <Button
            outline
            onClick={() => setShowFilters(!showFilters)}
            className={showFilters ? 'border-violet-500 text-violet-400' : ''}
          >
            <FunnelIcon className="h-5 w-5" />
          </Button>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="rounded-xl bg-zinc-900 border border-zinc-800 p-4"
          >
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm text-zinc-400 mb-1">Platform</label>
                <select
                  value={filters.platform}
                  onChange={(e) => updateFilter('platform', e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="all">All Platforms</option>
                  <option value="meta">Meta (FB/IG)</option>
                  <option value="tiktok">TikTok</option>
                  <option value="youtube">YouTube</option>
                  <option value="google">Google Ads</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => updateFilter('category', e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="all">All Categories</option>
                  <option value="fitness">Fitness</option>
                  <option value="ecommerce">E-commerce</option>
                  <option value="saas">SaaS</option>
                  <option value="finance">Finance</option>
                  <option value="education">Education</option>
                  <option value="health">Health</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">Min Engagement</label>
                <select
                  value={filters.minEngagement}
                  onChange={(e) => updateFilter('minEngagement', e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="0">Any</option>
                  <option value="1">1%+</option>
                  <option value="3">3%+</option>
                  <option value="5">5%+</option>
                  <option value="10">10%+</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">Date Range</label>
                <select
                  value={filters.dateRange}
                  onChange={(e) => updateFilter('dateRange', e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="7">Last 7 days</option>
                  <option value="30">Last 30 days</option>
                  <option value="90">Last 90 days</option>
                  <option value="365">Last year</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-zinc-400 mb-1">Sort By</label>
                <select
                  value={filters.sortBy}
                  onChange={(e) => updateFilter('sortBy', e.target.value)}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-white text-sm"
                >
                  <option value="engagement">Engagement</option>
                  <option value="views">Views</option>
                  <option value="recent">Most Recent</option>
                  <option value="relevance">Relevance</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end mt-4 gap-2">
              <Button plain onClick={() => setFilters(DEFAULT_FILTERS)} className="text-zinc-400">
                Reset Filters
              </Button>
              <Button color="violet" onClick={handleSearch}>
                Apply Filters
              </Button>
            </div>
          </motion.div>
        )}

        {/* Search results info */}
        {hasSearched && (
          <div className="flex items-center justify-between">
            <Text className="text-zinc-400">
              {searching ? 'Searching...' : `Found ${searchResults.length} result${searchResults.length !== 1 ? 's' : ''}`}
              {search && ` for "${search}"`}
            </Text>
            <Button plain onClick={clearSearch} className="text-zinc-400 hover:text-white">
              Clear Search
            </Button>
          </div>
        )}
      </div>

      {/* Results Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <Heading level={2} className="text-white">
            {hasSearched ? 'Search Results' : 'Trending in Fitness'}
          </Heading>
          {displayedAds.length > 0 && !hasSearched && (
            <Button plain className="text-violet-400">View All</Button>
          )}
        </div>

        {(loading || searching) && (
          <div className="flex items-center justify-center py-16 rounded-xl bg-zinc-900 border border-zinc-800">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-violet-500"></div>
          </div>
        )}

        {error && (
          <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-8 text-center">
            <div className="w-12 h-12 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-white font-medium">{error}</p>
            <p className="text-zinc-400 text-sm mt-2">Check your connection or try again later.</p>
          </div>
        )}

        {!loading && !searching && !error && displayedAds.length === 0 && (
          <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-8 text-center">
            <GlobeAltIcon className="h-12 w-12 text-zinc-700 mx-auto" />
            <p className="text-white mt-4 font-medium">
              {hasSearched ? 'No ads found matching your search' : 'No trending ads available'}
            </p>
            <p className="text-zinc-400 text-sm mt-2">
              {hasSearched
                ? 'Try different keywords or adjust your filters.'
                : 'Connect a data source to start tracking competitor ads.'}
            </p>
            {hasSearched ? (
              <Button color="violet" className="mt-4" onClick={clearSearch}>
                Clear Search
              </Button>
            ) : (
              <Button color="violet" className="mt-4">Connect Data Source</Button>
            )}
          </div>
        )}

        {!loading && !searching && !error && displayedAds.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {displayedAds.map((ad, index) => (
              <motion.div
                key={ad.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <TrendingAdCard ad={ad} />
              </motion.div>
            ))}
          </div>
        )}
      </div>

      {/* Tracked Competitors */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <Heading level={2} className="text-white">Tracked Competitors</Heading>
          <Button outline className="gap-2">
            <BookmarkIcon className="h-4 w-4" />
            Add Competitor
          </Button>
        </div>
        <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-8 text-center">
          <BookmarkIcon className="h-12 w-12 text-zinc-700 mx-auto" />
          <p className="text-white mt-4">No competitors tracked yet</p>
          <p className="text-zinc-400 text-sm mt-1">Start tracking competitor ad accounts to monitor their creatives.</p>
          <Button color="violet" className="mt-4">Add First Competitor</Button>
        </div>
      </div>
    </div>
  )
}

export default AdSpyPage
