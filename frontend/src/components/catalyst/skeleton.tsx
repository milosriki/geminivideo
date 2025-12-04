import { cn } from '@/lib/utils'

interface SkeletonProps {
  className?: string
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-zinc-800',
        className
      )}
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 space-y-4">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="h-4 w-1/2" />
    </div>
  )
}

export function SkeletonMetricCard() {
  return (
    <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-4 space-y-3">
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-8 w-3/4" />
      <Skeleton className="h-3 w-1/3" />
    </div>
  )
}

export function SkeletonTableRow() {
  return (
    <div className="flex items-center gap-4 py-4 border-b border-zinc-800">
      <Skeleton className="h-10 w-10 rounded-full" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-4 w-1/4" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <Skeleton className="h-6 w-20 rounded-full" />
    </div>
  )
}

export function SkeletonVideoCard() {
  return (
    <div className="rounded-lg bg-zinc-900 border border-zinc-800 overflow-hidden">
      <Skeleton className="aspect-video w-full" />
      <div className="p-4 space-y-2">
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    </div>
  )
}

export function SkeletonGrid({ count = 6 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonVideoCard key={i} />
      ))}
    </div>
  )
}
