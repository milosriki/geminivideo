// ==========================================
// AdSpyPage.tsx - Competitor Research
// ==========================================
import { useState } from 'react'
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
import { Combobox, ComboboxOption, ComboboxLabel, ComboboxDescription } from '@/components/catalyst/combobox'
import { Link } from '@/components/catalyst/link'

const brands = [
  { id: '1', name: 'Competitor A', industry: 'Fitness & Wellness', adsCount: 247 },
  { id: '2', name: 'Competitor B', industry: 'Personal Training', adsCount: 189 },
  { id: '3', name: 'Competitor C', industry: 'Health & Nutrition', adsCount: 342 },
  { id: '4', name: 'Competitor D', industry: 'Fitness Equipment', adsCount: 156 },
  { id: '5', name: 'Competitor E', industry: 'Weight Loss Programs', adsCount: 428 },
]

const trendingAds = [
  { id: '1', brand: 'Competitor A', title: 'Weight Loss Success', views: '2.4M', engagement: '8.2%', platform: 'Meta' },
  { id: '2', brand: 'Competitor B', title: 'Personal Training Ad', views: '1.8M', engagement: '6.5%', platform: 'TikTok' },
  { id: '3', brand: 'Competitor C', title: 'Transformation Story', views: '3.1M', engagement: '9.1%', platform: 'Meta' },
  { id: '4', brand: 'Competitor D', title: 'Fitness Challenge', views: '950K', engagement: '7.8%', platform: 'YouTube' },
]

function TrendingAdCard({ ad }: { ad: typeof trendingAds[0] }) {
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
  const [selectedBrand, setSelectedBrand] = useState<typeof brands[0] | null>(null)

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div>
        <Heading level={1} className="text-white">Ad Spy</Heading>
        <Text className="text-zinc-400 mt-1">Research competitor ads and discover winning creatives.</Text>
      </div>

      {/* Search Bar */}
      <div className="flex gap-4">
        <div className="flex-1">
          <Combobox
            value={selectedBrand}
            onChange={setSelectedBrand}
            placeholder="Search brands, keywords..."
          >
            {brands.map((brand) => (
              <ComboboxOption key={brand.id} value={brand}>
                <ComboboxLabel>{brand.name}</ComboboxLabel>
                <ComboboxDescription>{brand.industry} - {brand.adsCount} ads</ComboboxDescription>
              </ComboboxOption>
            ))}
          </Combobox>
        </div>
        <Button color="violet">Search</Button>
      </div>

      {/* Trending Section */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <Heading level={2} className="text-white">Trending in Fitness</Heading>
          <Link href="#" className="text-violet-400">View All</Link>
        </div>
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
