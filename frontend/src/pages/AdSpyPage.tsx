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

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  MagnifyingGlassIcon,
  GlobeAltIcon,
  PlayIcon,
  BookmarkIcon,
  ArrowTrendingUpIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Input } from '@/components/catalyst/input'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

interface TrendingAd {
  id: string;
  brand: string;
  title: string;
  views: string;
  engagement: string;
  platform: string;
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

export function AdSpyPage() {
  const [search, setSearch] = useState('')
  const [trendingAds, setTrendingAds] = useState<TrendingAd[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div>
        <Heading level={1} className="text-white">Ad Spy</Heading>
        <Text className="text-zinc-400 mt-1">Research competitor ads and discover winning creatives.</Text>
      </div>

      {/* Search Bar */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by brand, keyword, or URL..."
            className="pl-10"
          />
        </div>
        <Button color="violet">Search</Button>
      </div>

      {/* Trending Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <Heading level={2} className="text-white">Trending in Fitness</Heading>
          {trendingAds.length > 0 && (
            <Button plain className="text-violet-400">View All</Button>
          )}
        </div>

        {loading && (
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

        {!loading && !error && trendingAds.length === 0 && (
          <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-8 text-center">
            <GlobeAltIcon className="h-12 w-12 text-zinc-700 mx-auto" />
            <p className="text-white mt-4 font-medium">No trending ads available</p>
            <p className="text-zinc-400 text-sm mt-2">Connect a data source to start tracking competitor ads.</p>
            <Button color="violet" className="mt-4">Connect Data Source</Button>
          </div>
        )}

        {!loading && !error && trendingAds.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {trendingAds.map((ad, index) => (
              <motion.div
                key={ad.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
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
