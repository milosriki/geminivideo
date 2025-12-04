
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Switch } from '@headlessui/react'
import {
  PlayIcon,
  PauseIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ArrowsPointingOutIcon,
  ScissorsIcon,
  SparklesIcon,
  ArrowDownTrayIcon,
  PlusIcon,
  TrashIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Select } from '@/components/catalyst/select'
import { Textarea } from '@/components/catalyst/textarea'
import { Input } from '@/components/catalyst/input'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { Field, Label } from '@/components/catalyst/fieldset'
import { Dialog, DialogTitle, DialogDescription, DialogBody, DialogActions } from '@/components/catalyst/dialog'
import { Listbox, ListboxOption, ListboxLabel, ListboxDescription } from '@/components/catalyst/listbox'
import { Button as CompassButton } from '@/components/compass/button'
import { IconButton } from '@/components/compass/icon-button'
import { Video as VideoPlayer } from '@/components/compass/video-player'
import { Breadcrumbs } from '@/components/compass/breadcrumbs'
import { apiClient } from '@/services/apiClient'
import { Avatar } from '@/types'

// Timeline Clip Component
interface TimelineClipProps {
  id: string
  name: string
  duration: number
  thumbnail: string
  isSelected: boolean
  onClick: () => void
}

function TimelineClip({ name, duration, isSelected, onClick }: TimelineClipProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        flex-shrink-0 w-32 h-20 rounded-lg overflow-hidden cursor-pointer
        border-2 transition-all
        ${isSelected ? 'border-violet-500 ring-2 ring-violet-500/30' : 'border-zinc-700 hover:border-zinc-600'}
      `}
    >
      <div className="bg-gradient-to-br from-zinc-700 to-zinc-800 h-full flex flex-col justify-end p-2">
        <p className="text-white text-xs font-medium truncate">{name}</p>
        <p className="text-zinc-400 text-xs">{duration}s</p>
      </div>
    </motion.div>
  )
}

// Avatar Selection Card
interface AvatarProps {
  id: string
  name: string
  image: string
  isSelected: boolean
  onClick: () => void
}

function AvatarCard({ name, isSelected, onClick }: AvatarProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={onClick}
      className={`
        p-3 rounded-xl border transition-all text-center
        ${isSelected ? 'border-violet-500 bg-violet-500/10' : 'border-zinc-800 hover:border-zinc-700'}
      `}
    >
      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 mx-auto" />
      <p className="text-white text-sm mt-2">{name}</p>
    </motion.button>
  )
}

export function StudioPage() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration] = useState(30)
  const [selectedClip, setSelectedClip] = useState<string | null>('clip-1')
  const [selectedAvatar, setSelectedAvatar] = useState<string | null>('avatar-1')
  const [script, setScript] = useState(
    'Transform your body in 90 days with Dubai\'s #1 personal training company. Our certified coaches have helped 12,000+ clients achieve their fitness goals...'
  )
  const videoRef = useRef<HTMLVideoElement>(null)
  const [isExportOpen, setIsExportOpen] = useState(false)
  const [exportFormat, setExportFormat] = useState('1080p')
  const [selectedVoice, setSelectedVoice] = useState('natural-female')

  const voiceOptions = [
    { value: 'natural-female', name: 'Natural Female', description: 'Sarah - Warm and engaging' },
    { value: 'natural-male', name: 'Natural Male', description: 'James - Professional and clear' },
    { value: 'professional', name: 'Professional', description: 'Corporate and authoritative' },
    { value: 'energetic', name: 'Energetic', description: 'Dynamic and exciting' },
  ]

  const clips = [
    { id: 'clip-1', name: 'Intro Hook', duration: 5, thumbnail: '' },
    { id: 'clip-2', name: 'Problem', duration: 8, thumbnail: '' },
    { id: 'clip-3', name: 'Solution', duration: 10, thumbnail: '' },
    { id: 'clip-4', name: 'Testimonial', duration: 7, thumbnail: '' },
  ]

  const [avatars, setAvatars] = useState<Avatar[]>([])
  const [loadingAvatars, setLoadingAvatars] = useState(true)

  useEffect(() => {
    const loadAvatars = async () => {
      try {
        const data = await apiClient.fetchAvatars()
        setAvatars(data)
        if (data.length > 0) setSelectedAvatar(data[0].key)
      } catch (error) {
        console.error('Failed to load avatars:', error)
      } finally {
        setLoadingAvatars(false)
      }
    }
    loadAvatars()
  }, [])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const handleGenerate = async () => {
    if (!selectedAvatar) return

    // console.log('Generating video with script:', script)
    try {
      // Mock brief and strategy for now as StudioPage doesn't have full campaign context yet
      const mockBrief = {
        productName: 'Fitness App',
        targetMarket: 'Fitness Enthusiasts',
        offer: '90 Day Transformation',
        cta: 'Sign Up Now',
        angle: 'Transformation',
        tone: 'inspirational' as const,
        platform: 'reels' as const,
        painPoints: '',
        competitors: []
      }
      const mockStrategy = {
        primaryVideoFileName: 'studio_generated.mp4',
        bRollFileNames: [],
        strategyJustification: '',
        videoAnalyses: []
      }

      await apiClient.generateCreatives(mockBrief, selectedAvatar, mockStrategy)
      alert('Generation started! Check the Jobs queue.')
    } catch (error) {
      console.error('Generation failed:', error)
      alert('Generation failed. See console.')
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-6 py-3 border-b border-zinc-800 bg-zinc-900">
        <div className="flex flex-col gap-1">
          <Breadcrumbs
            pages={[
              { name: 'Assets', href: '/assets', current: false },
              { name: 'Studio', href: '/studio', current: true },
            ]}
          />
          <div className="flex items-center gap-4 mt-2">
            <Heading level={2} className="text-white">Video Studio</Heading>
            <Badge color="violet">Draft</Badge>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Button outline className="gap-2">
            <SparklesIcon className="h-4 w-4" />
            AI Enhance
          </Button>
          <Button color="violet" className="gap-2" onClick={() => setIsExportOpen(true)}>
            <ArrowDownTrayIcon className="h-4 w-4" />
            Export
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Preview + Timeline */}
        <div className="flex-1 flex flex-col">
          {/* Video Preview */}
          <div className="flex-1 flex items-center justify-center bg-black p-8">
            <div className="relative w-full max-w-2xl">
              <VideoPlayer
                src="https://assets.mixkit.co/videos/preview/mixkit-going-down-a-curved-highway-through-a-mountain-range-41576-large.mp4"
                poster="https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?ixlib=rb-1.2.1&auto=format&fit=crop&w=1000&q=80"
              />
            </div>
          </div>

          {/* Timeline */}
          <div className="h-40 border-t border-zinc-800 bg-zinc-900 p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <ScissorsIcon className="h-4 w-4 text-zinc-400" />
                <Text className="text-zinc-400 text-sm">Timeline</Text>
                <div className="flex items-center gap-1 ml-4">
                  <IconButton
                    icon={isPlaying ? PauseIcon : PlayIcon}
                    onClick={() => setIsPlaying(!isPlaying)}
                    aria-label={isPlaying ? 'Pause' : 'Play'}
                  />
                  <IconButton
                    icon={isMuted ? SpeakerXMarkIcon : SpeakerWaveIcon}
                    onClick={() => setIsMuted(!isMuted)}
                    aria-label={isMuted ? 'Unmute' : 'Mute'}
                  />
                </div>
              </div>
              <Button plain className="gap-1 text-sm">
                <PlusIcon className="h-4 w-4" />
                Add Clip
              </Button>
            </div>

            {/* Clips Track */}
            <div className="flex items-center gap-2 overflow-x-auto pb-2">
              {clips.map((clip) => (
                <TimelineClip
                  key={clip.id}
                  {...clip}
                  isSelected={selectedClip === clip.id}
                  onClick={() => setSelectedClip(clip.id)}
                />
              ))}

              {/* Add Clip Button */}
              <button className="flex-shrink-0 w-32 h-20 rounded-lg border-2 border-dashed border-zinc-700 hover:border-zinc-600 flex items-center justify-center transition-colors">
                <PlusIcon className="h-6 w-6 text-zinc-500" />
              </button>
            </div>

            {/* Playhead indicator */}
            <div className="relative h-2 mt-2">
              <div className="absolute inset-x-0 h-0.5 bg-zinc-700 top-1/2 -translate-y-1/2" />
              <div
                className="absolute w-3 h-3 bg-violet-500 rounded-full top-1/2 -translate-y-1/2 -translate-x-1/2"
                style={{ left: `${(currentTime / duration) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Right Panel - Script & Settings */}
        <div className="w-96 border-l border-zinc-800 bg-zinc-900 flex flex-col overflow-hidden">
          {/* Panel Tabs */}
          <div className="flex border-b border-zinc-800">
            <button className="flex-1 px-4 py-3 text-sm font-medium text-violet-400 border-b-2 border-violet-500">
              Script
            </button>
            <button className="flex-1 px-4 py-3 text-sm font-medium text-zinc-400 hover:text-white">
              Settings
            </button>
            <button className="flex-1 px-4 py-3 text-sm font-medium text-zinc-400 hover:text-white">
              Export
            </button>
          </div>

          {/* Panel Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {/* AI Script Editor */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <Text className="text-white font-medium">Script</Text>
                <Button plain className="gap-1 text-xs">
                  <SparklesIcon className="h-3 w-3" />
                  AI Rewrite
                </Button>
              </div>
              <Textarea
                value={script}
                onChange={(e) => setScript(e.target.value)}
                rows={6}
                placeholder="Enter your video script..."
              />
              <div className="flex items-center justify-between mt-2">
                <Text className="text-zinc-500 text-xs">{script.length} characters</Text>
                <Text className="text-zinc-500 text-xs">~{Math.ceil(script.length / 15)}s read time</Text>
              </div>
            </div>

            {/* Voice Selection */}
            <div>
              <Text className="text-white font-medium mb-2">Voice</Text>
              <Listbox value={selectedVoice} onChange={setSelectedVoice}>
                {voiceOptions.map((voice) => (
                  <ListboxOption key={voice.value} value={voice.value}>
                    <ListboxLabel>{voice.name}</ListboxLabel>
                    <ListboxDescription>{voice.description}</ListboxDescription>
                  </ListboxOption>
                ))}
              </Listbox>
            </div>

            {/* Avatar Selection */}
            <div>
              <Text className="text-white font-medium mb-3">AI Avatar</Text>
              <div className="grid grid-cols-4 gap-2">
                {loadingAvatars ? (
                  <div className="col-span-4 text-center text-zinc-500 text-sm">Loading avatars...</div>
                ) : (
                  avatars.map((avatar) => (
                    <AvatarCard
                      key={avatar.key}
                      id={avatar.key}
                      name={avatar.name}
                      image={`https://api.dicebear.com/7.x/avataaars/svg?seed=${avatar.key}`}
                      isSelected={selectedAvatar === avatar.key}
                      onClick={() => setSelectedAvatar(avatar.key)}
                    />
                  ))
                )}
              </div>
            </div>

            {/* Style Options */}
            <div>
              <Text className="text-white font-medium mb-2">Style</Text>
              <div className="grid grid-cols-2 gap-2">
                {['Modern', 'Classic', 'Bold', 'Minimal'].map((style) => (
                  <button
                    key={style}
                    className="px-4 py-2 rounded-lg border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-white text-sm transition-all"
                  >
                    {style}
                  </button>
                ))}
              </div>
            </div>

            {/* Export Settings */}
            <div>
              <Text className="text-white font-medium mb-2">Resolution</Text>
              <Select>
                <option value="1080p">1080p (Full HD)</option>
                <option value="720p">720p (HD)</option>
                <option value="4k">4K (Ultra HD)</option>
                <option value="9:16">9:16 Vertical (Stories/Reels)</option>
              </Select>
            </div>
          </div>

          {/* Generate Button */}
          <div className="p-4 border-t border-zinc-800">
            <Button color="violet" className="w-full gap-2" onClick={handleGenerate}>
              <SparklesIcon className="h-4 w-4" />
              Generate Video
            </Button>
          </div>
        </div>
      </div>

      {/* Export Dialog */}
      <Dialog open={isExportOpen} onClose={() => setIsExportOpen(false)} size="md">
        <DialogTitle>Export Video</DialogTitle>
        <DialogDescription>Configure export settings.</DialogDescription>
        <DialogBody>
          <Field>
            <Label>Resolution</Label>
            <Select value={exportFormat} onChange={(e) => setExportFormat(e.target.value)}>
              <option value="720p">720p (HD)</option>
              <option value="1080p">1080p (Full HD)</option>
              <option value="4k">4K (Ultra HD)</option>
            </Select>
          </Field>
        </DialogBody>
        <DialogActions>
          <Button plain onClick={() => setIsExportOpen(false)}>Cancel</Button>
          <Button color="violet">Export Video</Button>
        </DialogActions>
      </Dialog>
    </div>
  )
}

export default StudioPage
