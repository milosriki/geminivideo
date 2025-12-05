import { PlayCircleIcon } from '@heroicons/react/24/solid'
import { motion } from 'framer-motion'

interface VideoTutorialProps {
  title: string
  description: string
  thumbnailUrl?: string
  videoUrl: string
  duration: string
}

export function VideoTutorial({ title, description, thumbnailUrl, videoUrl, duration }: VideoTutorialProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-violet-500/50 transition-all duration-300"
    >
      <a href={videoUrl} target="_blank" rel="noopener noreferrer" className="block">
        {/* Thumbnail */}
        <div className="relative aspect-video bg-zinc-800">
          {thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt={title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <PlayCircleIcon className="h-16 w-16 text-zinc-700" />
            </div>
          )}

          {/* Play Button Overlay */}
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
            <div className="bg-violet-500 rounded-full p-3">
              <PlayCircleIcon className="h-10 w-10 text-white" />
            </div>
          </div>

          {/* Duration Badge */}
          <div className="absolute bottom-3 right-3 bg-black/80 px-2 py-1 rounded text-xs font-medium text-white">
            {duration}
          </div>
        </div>

        {/* Content */}
        <div className="p-4">
          <h4 className="font-semibold text-white group-hover:text-violet-400 transition-colors">
            {title}
          </h4>
          <p className="text-sm text-zinc-400 mt-1 line-clamp-2">{description}</p>
        </div>
      </a>
    </motion.div>
  )
}
