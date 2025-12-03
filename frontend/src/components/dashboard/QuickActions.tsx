import { Button } from '@/components/catalyst/button'
import { Heading } from '@/components/catalyst/heading'
import { PlusIcon, SparklesIcon, MagnifyingGlassIcon, VideoCameraIcon } from '@heroicons/react/20/solid'

export function QuickActions() {
  return (
    <div className="p-6 rounded-lg border border-zinc-950/5 bg-white shadow-sm dark:border-white/5 dark:bg-zinc-900">
      <Heading level={2} className="mb-4">Quick Actions</Heading>
      <div className="grid grid-cols-2 gap-3">
        <Button className="w-full justify-start" href="/create">
          <PlusIcon />
          New Campaign
        </Button>
        <Button className="w-full justify-start" href="/studio" color="indigo">
          <SparklesIcon />
          Generate Video
        </Button>
        <Button className="w-full justify-start" href="/spy" plain>
          <MagnifyingGlassIcon />
          Spy Ads
        </Button>
        <Button className="w-full justify-start" href="/assets" plain>
          <VideoCameraIcon />
          Ad Library
        </Button>
      </div>
    </div>
  )
}
