import { useState, useEffect } from 'react'
import { getAssets } from '@/services/api'
import { googleDriveService } from '@/services/googleDriveService'
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
import { VideoCard } from '@/components/compass/video-card'
import { Dialog, DialogTitle, DialogDescription, DialogBody, DialogActions } from '@/components/catalyst/dialog'
import { Alert, AlertTitle, AlertDescription, AlertActions } from '@/components/catalyst/alert'
import { Pagination, PaginationPrevious, PaginationNext, PaginationList, PaginationPage, PaginationGap } from '@/components/catalyst/pagination'
import { NoVideosEmpty } from '@/components/catalyst/empty-state'





export function AssetsPage() {
  const [view, setView] = useState<'grid' | 'list'>('grid')
  const [search, setSearch] = useState('')
  const [assets, setAssets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedAsset, setSelectedAsset] = useState<any>(null)
  const [isDetailOpen, setIsDetailOpen] = useState(false)
  const [assetToDelete, setAssetToDelete] = useState<any>(null)
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const data = await getAssets()
        // Handle both array response or object with items
        const items = Array.isArray(data) ? data : (data.items || [])
        setAssets(items)
      } catch (error) {
        console.error('Failed to fetch assets:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchAssets()
  }, [])

  // Google Drive Integration
  const handleDriveImport = async () => {
    try {
      setLoading(true)
      await googleDriveService.signIn()
      const files = await googleDriveService.listFiles()

      // Transform Drive files to Asset format
      const driveAssets = files.map(f => ({
        asset_id: f.id,
        filename: f.name,
        url: f.webContentLink || f.thumbnailLink || '',
        format: f.mimeType.split('/')[1] || 'video',
        size_bytes: parseInt(f.size || '0', 10),
        duration_seconds: f.videoMediaMetadata?.durationMillis ? parseInt(f.videoMediaMetadata.durationMillis, 10) / 1000 : 0,
        source: 'google_drive'
      }))

      setAssets(prev => [...driveAssets, ...prev])
      alert(`Successfully imported ${files.length} videos from Google Drive!`)
    } catch (error: any) {
      console.error('Drive import failed:', error)
      alert('Failed to import from Drive: ' + error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Heading level={1} className="text-white">Ad Library</Heading>
          <Text className="text-zinc-400 mt-1">Browse and manage your video assets.</Text>
        </div>
        <div className="flex gap-2">
          <Button outline onClick={handleDriveImport} className="gap-2">
            <img src="https://upload.wikimedia.org/wikipedia/commons/1/12/Google_Drive_icon_%282020%29.svg" className="h-4 w-4" alt="Drive" />
            Import from Drive
          </Button>
          <Button color="violet" href="/studio" className="gap-2">
            <PlayIcon className="h-4 w-4" />
            Create Video
          </Button>
        </div>
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
          <div className="flex gap-1">
            <button
              onClick={() => setView('grid')}
              className={`p-2 rounded-lg transition-colors ${view === 'grid'
                ? 'bg-violet-500 text-white'
                : 'bg-transparent text-zinc-400 hover:text-white hover:bg-zinc-800'
                }`}
              aria-label="Grid view"
            >
              <Squares2X2Icon className="h-5 w-5" />
            </button>
            <button
              onClick={() => setView('list')}
              className={`p-2 rounded-lg transition-colors ${view === 'list'
                ? 'bg-violet-500 text-white'
                : 'bg-transparent text-zinc-400 hover:text-white hover:bg-zinc-800'
                }`}
              aria-label="List view"
            >
              <ListBulletIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Masonry Grid */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]" role="status">
            <span className="!absolute !-m-px !h-px !w-px !overflow-hidden !whitespace-nowrap !border-0 !p-0 ![clip:rect(0,0,0,0)]">Loading...</span>
          </div>
        </div>
      ) : !loading && assets.length === 0 ? (
        <NoVideosEmpty />
      ) : (
        <div className="columns-2 sm:columns-3 lg:columns-4 xl:columns-5 gap-4 space-y-4">
          {assets.map((asset, index) => (
            <motion.div
              key={asset.asset_id || index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
              className="break-inside-avoid"
            >
              <VideoCard
                url={`/assets/${asset.asset_id}`}
                title={asset.filename || 'Untitled'}
                subtitle={`${asset.format || 'Video'} • ${(asset.size_bytes / 1024 / 1024).toFixed(1)} MB`}
                thumbnailUrl={asset.source === 'google_drive' ? asset.url : "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?ixlib=rb-1.2.1&auto=format&fit=crop&w=1000&q=80"}
                duration={asset.duration_seconds || 0}
              />
            </motion.div>
          ))}
        </div>
      )}

      {/* Pagination */}
      <Pagination className="mt-8">
        <PaginationPrevious href={currentPage > 1 ? '#' : null} />
        <PaginationList>
          <PaginationPage href="#" current={currentPage === 1}>1</PaginationPage>
          <PaginationPage href="#">2</PaginationPage>
          <PaginationPage href="#">3</PaginationPage>
        </PaginationList>
        <PaginationNext href="#" />
      </Pagination>

      {/* Asset Detail Dialog */}
      <Dialog open={isDetailOpen} onClose={() => setIsDetailOpen(false)} size="2xl">
        <DialogTitle>{selectedAsset?.filename || 'Asset Details'}</DialogTitle>
        <DialogDescription>View and manage this video asset.</DialogDescription>
        <DialogBody>
          <div className="aspect-video bg-black rounded-lg">
            <video src={selectedAsset?.url} controls className="w-full h-full" />
          </div>
        </DialogBody>
        <DialogActions>
          <Button plain onClick={() => setIsDetailOpen(false)}>Close</Button>
          <Button color="violet">Edit in Studio</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Alert */}
      <Alert open={assetToDelete !== null} onClose={() => setAssetToDelete(null)}>
        <AlertTitle>Delete Asset</AlertTitle>
        <AlertDescription>Are you sure? This cannot be undone.</AlertDescription>
        <AlertActions>
          <Button plain onClick={() => setAssetToDelete(null)}>Cancel</Button>
          <Button color="red">Delete</Button>
        </AlertActions>
      </Alert>
    </div>
  )
}


export default AssetsPage
