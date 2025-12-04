import { cn } from '@/utils/cn'

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * The variant of skeleton to display
   * - 'default': Standard shimmer skeleton
   * - 'card': Card-shaped skeleton with rounded corners
   * - 'avatar': Circular skeleton for avatars
   * - 'text': Thin skeleton for text content
   */
  variant?: 'default' | 'card' | 'avatar' | 'text'
}

/**
 * Skeleton component for loading states
 * Uses animated pulse effect for visual feedback
 * Implements WCAG guidelines with aria-busy attribute
 */
export function Skeleton({
  className,
  variant = 'default',
  ...props
}: SkeletonProps) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading content"
      className={cn(
        'animate-pulse bg-zinc-200 dark:bg-zinc-800',
        {
          'rounded-md': variant === 'default',
          'rounded-xl': variant === 'card',
          'rounded-full': variant === 'avatar',
          'h-4 rounded': variant === 'text',
        },
        className
      )}
      {...props}
    />
  )
}

/**
 * Pre-composed skeleton for card loading states
 */
export function SkeletonCard({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading card"
      className={cn('space-y-4 rounded-xl border border-zinc-200 p-4 dark:border-zinc-800', className)}
    >
      <Skeleton variant="default" className="h-32 w-full" />
      <div className="space-y-2">
        <Skeleton variant="text" className="h-4 w-3/4" />
        <Skeleton variant="text" className="h-4 w-1/2" />
      </div>
    </div>
  )
}

/**
 * Pre-composed skeleton for table row loading states
 */
export function SkeletonTableRow({ columns = 4 }: { columns?: number }) {
  return (
    <tr role="status" aria-busy="true" aria-label="Loading table row">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <Skeleton variant="text" className="h-4 w-full" />
        </td>
      ))}
    </tr>
  )
}

/**
 * Pre-composed skeleton for avatar with text
 */
export function SkeletonAvatar({ className }: { className?: string }) {
  return (
    <div
      role="status"
      aria-busy="true"
      aria-label="Loading avatar"
      className={cn('flex items-center gap-3', className)}
    >
      <Skeleton variant="avatar" className="h-10 w-10" />
      <div className="space-y-2">
        <Skeleton variant="text" className="h-4 w-24" />
        <Skeleton variant="text" className="h-3 w-16" />
      </div>
    </div>
  )
}
