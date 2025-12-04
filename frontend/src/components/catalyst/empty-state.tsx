import clsx from 'clsx'
import { Button } from './button'

interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description: string
  action?: {
    label: string
    href?: string
    onClick?: () => void
  }
  className?: string
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  className
}: EmptyStateProps) {
  return (
    <div className={clsx(
      'flex flex-col items-center justify-center py-16 px-4 text-center',
      className
    )}>
      {icon && (
        <div className="mb-4 text-zinc-600">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold text-white mb-2">
        {title}
      </h3>
      <p className="text-zinc-400 text-sm max-w-sm mb-6">
        {description}
      </p>
      {action && (
        <Button
          color="violet"
          href={action.href}
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
    </div>
  )
}

// Pre-built empty states for common scenarios
export function NoVideosEmpty() {
  return (
    <EmptyState
      icon={
        <svg className="h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      }
      title="No videos yet"
      description="Upload your first video to get started with AI-powered editing and analysis."
      action={{ label: 'Upload Video', href: '/assets' }}
    />
  )
}

export function NoCampaignsEmpty() {
  return (
    <EmptyState
      icon={
        <svg className="h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      }
      title="No campaigns yet"
      description="Create your first campaign to start generating AI-powered video ads."
      action={{ label: 'Create Campaign', href: '/create' }}
    />
  )
}

export function NoResultsEmpty({ query }: { query?: string }) {
  return (
    <EmptyState
      icon={
        <svg className="h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      }
      title="No results found"
      description={query ? `No results for "${query}". Try adjusting your search.` : 'Try adjusting your filters or search terms.'}
    />
  )
}
