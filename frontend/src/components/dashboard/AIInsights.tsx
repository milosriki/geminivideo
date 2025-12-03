import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { SparklesIcon } from '@heroicons/react/20/solid'

export function AIInsights() {
  return (
    <div className="p-6 rounded-lg border border-zinc-950/5 bg-gradient-to-br from-indigo-50 to-white dark:from-indigo-950/30 dark:to-zinc-900 shadow-sm dark:border-white/5">
      <div className="flex items-center gap-2 mb-4 text-indigo-600 dark:text-indigo-400">
        <SparklesIcon className="size-5" />
        <Heading level={2}>AI Insights</Heading>
      </div>
      <div className="space-y-4">
        <div className="p-3 rounded-md bg-white/50 dark:bg-white/5 border border-indigo-100 dark:border-white/5">
          <Text className="font-medium text-zinc-900 dark:text-white">Opportunity Detected</Text>
          <Text className="mt-1 text-sm">Your "Tech Gadget" video has a 25% higher CTR than average. Consider increasing budget.</Text>
        </div>
        <div className="p-3 rounded-md bg-white/50 dark:bg-white/5 border border-indigo-100 dark:border-white/5">
          <Text className="font-medium text-zinc-900 dark:text-white">Trend Alert</Text>
          <Text className="mt-1 text-sm">UGC-style videos are trending in your niche. Generate 3 new variations?</Text>
        </div>
      </div>
    </div>
  )
}
