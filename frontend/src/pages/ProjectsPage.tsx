// ==========================================
// ProjectsPage.tsx
// ==========================================
import { FolderIcon, PlusIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'

export function ProjectsPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Heading level={1} className="text-white">Projects</Heading>
          <Text className="text-zinc-400 mt-1">Organize your video projects.</Text>
        </div>
        <Button color="violet" className="gap-2">
          <PlusIcon className="h-4 w-4" />
          New Project
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {['Q4 Campaign Videos', 'Testimonials', 'Product Demos', 'Social Content'].map((project) => (
          <div
            key={project}
            className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 hover:border-zinc-700 transition-colors cursor-pointer"
          >
            <FolderIcon className="h-8 w-8 text-violet-500 mb-4" />
            <h3 className="text-white font-medium">{project}</h3>
            <p className="text-zinc-400 text-sm mt-1">12 videos</p>
          </div>
        ))}
      </div>
    </div>
  )
}

export default ProjectsPage
