import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  Squares2X2Icon,
  ListBulletIcon,
  HeartIcon,
  PlayIcon,
  EllipsisHorizontalIcon,
} from '@heroicons/react/24/outline'
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid'
import { Button } from '@/components/catalyst/button'
import { Input } from '@/components/catalyst/input'
import { Select } from '@/components/catalyst/select'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import {
  Dropdown,
  DropdownButton,
  DropdownMenu,
  DropdownItem,
} from '@/components/catalyst/dropdown'

// Mock ad data
const ads = [
  { id: '1', title: 'Transformation Story', platform: 'Meta', type: 'video', duration: 30, likes: 24, saved: true },
  { id: '2', title: 'Coach Introduction', platform: 'TikTok', type: 'video', duration: 15, likes: 18, saved: false },
  { id: '3', title: 'Client Testimonial', platform: 'Meta', type: 'video', duration: 45, likes: 32, saved: true },
  { id: '4', title: 'Before/After', platform: 'Meta', type: 'image', duration: 0, likes: 56, saved: false },
  { id: '5', title: 'Workout Motivation', platform: 'TikTok', type: 'video', duration: 20, likes: 12, saved: false },
  { id: '6', title: 'Nutrition Tips', platform: 'YouTube', type: 'video', duration: 60, likes: 8, saved: true },
]

// Ad Card Component
interface AdCardProps {
  ad: typeof ads[0]
  onSave: () => void
}

function AdCard({ ad, onSave }: AdCardProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ y: -4 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="relative rounded-xl overflow-hidden bg-zinc-900 border border-zinc-800 group cursor-pointer"
    >
      {/* Thumbnail */}
      <div className="aspect-[9/16] bg-gradient-to-br from-zinc-800 to-zinc-900 relative">
        {/* Play button overlay */}
        {ad.type === 'video' && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur flex items-center justify-center">
              <PlayIcon className="h-6 w-6 text-white ml-0.5" />
            </div>
          </div>
        )}

        {/* Hover overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          className="absolute inset-0 bg-black/60 flex flex-col justify-between p-3"
        >
          {/* Top actions */}
          <div className="flex justify-between">
            <Badge color={ad.platform === 'Meta' ? 'blue' : ad.platform === 'TikTok' ? 'pink' : 'red'}>
              {ad.platform}
            </Badge>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onSave()
              }}
              className="p-1.5 rounded-full bg-white/20 hover:bg-white/30 transition-colors"
            >
              {ad.saved ? (
                <HeartSolidIcon className="h-4 w-4 text-red-500" />
              ) : (
                <HeartIcon className="h-4 w-4 text-white" />
              )}
            </button>
          </div>

          {/* Bottom actions */}
          <div className="flex gap-2">
            <Button color="violet" className="flex-1 text-sm">
              Analyze
            </Button>
            <Button outline className="text-sm">
              Copy
            </Button>
          </div>
        </motion.div>

        {/* Duration badge */}
        {ad.type === 'video' && (
          <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/60 text-white text-xs">
            {Math.floor(ad.duration / 60)}:{(ad.duration % 60).toString().padStart(2, '0')}
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-white font-medium text-sm truncate">{ad.title}</h3>
            <p className="text-zinc-500 text-xs mt-0.5">{ad.likes} saves</p>
          </div>
          <Dropdown>
            <DropdownButton plain className="p-1">
              <EllipsisHorizontalIcon className="h-4 w-4 text-zinc-400" />
            </DropdownButton>
            <DropdownMenu anchor="bottom end">
              <DropdownItem>Edit</DropdownItem>
              <DropdownItem>Duplicate</DropdownItem>
              <DropdownItem>Download</DropdownItem>
              <DropdownItem className="text-red-400">Delete</DropdownItem>
            </DropdownMenu>
          </Dropdown>
        </div>
      </div>
    </motion.div>
  )
}

export function AssetsPage() {
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [search, setSearch] = useState('')

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Heading level={1} className="text-white">Ad Library</Heading>
          <Text className="text-zinc-400 mt-1">Browse and manage your video assets.</Text>
        </div>
        <Button color="violet" href="/studio" className="gap-2">
          <PlayIcon className="h-4 w-4" />
          Create Video
        </Button>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-zinc-500" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search assets..."
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          <Select className="w-32">
            <option value="all">All Platforms</option>
            <option value="meta">Meta</option>
            <option value="tiktok">TikTok</option>
            <option value="youtube">YouTube</option>
          </Select>
          <Select className="w-32">
            <option value="all">All Types</option>
            <option value="video">Video</option>
            <option value="image">Image</option>
          </Select>
          <Button outline className="gap-2">
            <FunnelIcon className="h-4 w-4" />
            More Filters
          </Button>
          <div className="flex border border-zinc-800 rounded-lg overflow-hidden">
            <button
              onClick={() => setView('grid')}
              className={`p-2 ${view === 'grid' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              <Squares2X2Icon className="h-5 w-5" />
            </button>
            <button
              onClick={() => setView('list')}
              className={`p-2 ${view === 'list' ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white'}`}
            >
              <ListBulletIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Masonry Grid */}
      <div className="columns-2 sm:columns-3 lg:columns-4 xl:columns-5 gap-4 space-y-4">
        {ads.map((ad, index) => (
          <motion.div
            key={ad.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="break-inside-avoid"
          >
            <AdCard ad={ad} onSave={() => console.log('Save', ad.id)} />
          </motion.div>
        ))}
      </div>
    </div>
  )
}

export default AssetsPage
