import { cn } from '@/utils/cn'
import { motion } from 'framer-motion'

interface EmptyStateProps {
  /**
   * Icon to display in the empty state
   */
  icon?: React.ReactNode
  /**
   * Title text for the empty state
   */
  title: string
  /**
   * Description text explaining what the user can do
   */
  description?: string
  /**
   * Optional action button/link
   */
  action?: React.ReactNode
  /**
   * Additional CSS classes
   */
  className?: string
}

/**
 * EmptyState component for displaying when no data is available
 * Features smooth animation entrance and accessible structure
 */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      role="status"
      aria-label={title}
      className={cn(
        'flex flex-col items-center justify-center rounded-xl border border-dashed border-zinc-300 bg-zinc-50 px-6 py-12 text-center dark:border-zinc-700 dark:bg-zinc-900/50',
        className
      )}
    >
      {icon && (
        <motion.div
          initial={{ scale: 0.8 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1, duration: 0.3 }}
          className="mb-4 text-zinc-400 dark:text-zinc-500"
          aria-hidden="true"
        >
          {icon}
        </motion.div>
      )}
      <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        {title}
      </h3>
      {description && (
        <p className="mt-2 max-w-sm text-sm text-zinc-600 dark:text-zinc-400">
          {description}
        </p>
      )}
      {action && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.3 }}
          className="mt-6"
        >
          {action}
        </motion.div>
      )}
    </motion.div>
  )
}

/**
 * Preset empty state for no search results
 */
export function NoSearchResults({
  searchTerm,
  onClear,
}: {
  searchTerm: string
  onClear?: () => void
}) {
  return (
    <EmptyState
      icon={
        <svg
          className="h-12 w-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
          />
        </svg>
      }
      title="No results found"
      description={`We couldn't find anything matching "${searchTerm}". Try adjusting your search.`}
      action={
        onClear && (
          <button
            onClick={onClear}
            className="rounded-lg bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 focus:outline-none focus:ring-2 focus:ring-zinc-500 focus:ring-offset-2 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
          >
            Clear search
          </button>
        )
      }
    />
  )
}

/**
 * Preset empty state for no data available
 */
export function NoDataAvailable({
  entityName = 'items',
  onCreate,
  createLabel = 'Create new',
}: {
  entityName?: string
  onCreate?: () => void
  createLabel?: string
}) {
  return (
    <EmptyState
      icon={
        <svg
          className="h-12 w-12"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
          />
        </svg>
      }
      title={`No ${entityName} yet`}
      description={`Get started by creating your first ${entityName.replace(/s$/, '')}.`}
      action={
        onCreate && (
          <button
            onClick={onCreate}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            <svg
              className="h-4 w-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            {createLabel}
          </button>
        )
      }
    />
  )
}
