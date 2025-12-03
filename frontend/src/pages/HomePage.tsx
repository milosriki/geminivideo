import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  PlayCircleIcon,
  SparklesIcon,
  ChartBarIcon,
  FilmIcon,
  PlusIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
} from '@heroicons/react/24/outline'
import { Badge } from '@/components/catalyst/badge'
import { Button } from '@/components/catalyst/button'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'

// Animated number component (from Radiant pattern)
function AnimatedNumber({ value, prefix = '', suffix = '' }: { value: number; prefix?: string; suffix?: string }) {
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    const duration = 1000
    const steps = 60
    const increment = value / steps
    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= value) {
        setDisplayValue(value)
        clearInterval(timer)
      } else {
        setDisplayValue(Math.floor(current))
      }
    }, duration / steps)
    return () => clearInterval(timer)
  }, [value])

  return (
    <span>
      {prefix}{displayValue.toLocaleString()}{suffix}
    </span>
  )
}

// Metric Card Component
interface MetricCardProps {
  title: string
  value: number
  prefix?: string
  suffix?: string
  change: number
  trend: 'up' | 'down'
  icon: React.ElementType
}

function MetricCard({ title, value, prefix, suffix, change, trend, icon: Icon }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 hover:border-zinc-700 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="rounded-lg bg-zinc-800 p-2">
          <Icon className="h-5 w-5 text-zinc-400" />
        </div>
        <Badge color={trend === 'up' ? 'green' : 'red'} className="gap-1">
          {trend === 'up' ? (
            <ArrowTrendingUpIcon className="h-3 w-3" />
          ) : (
            <ArrowTrendingDownIcon className="h-3 w-3" />
          )}
          {Math.abs(change)}%
        </Badge>
      </div>
      <div className="mt-4">
        <Text className="text-zinc-400 text-sm">{title}</Text>
        <p className="text-3xl font-bold text-white mt-1">
          <AnimatedNumber value={value} prefix={prefix} suffix={suffix} />
        </p>
      </div>
    </motion.div>
  )
}

// Quick Action Card
interface QuickActionProps {
  title: string
  description: string
  icon: React.ElementType
  href: string
  color: string
}

function QuickAction({ title, description, icon: Icon, href, color }: QuickActionProps) {
  return (
    <Link to={href}>
      <motion.div
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="rounded-xl bg-zinc-900 border border-zinc-800 p-6 hover:border-violet-500/50 transition-all cursor-pointer group"
      >
        <div className={`rounded-lg ${color} p-3 w-fit`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <h3 className="text-white font-semibold mt-4 group-hover:text-violet-400 transition-colors">
          {title}
        </h3>
        <p className="text-zinc-400 text-sm mt-1">{description}</p>
      </motion.div>
    </Link>
  )
}

// Job Status Item
interface JobProps {
  id: string
  name: string
  status: 'queued' | 'processing' | 'completed' | 'failed'
  progress?: number
}

function JobItem({ job }: { job: JobProps }) {
  const statusConfig = {
    queued: { color: 'yellow', icon: ClockIcon, text: 'Queued' },
    processing: { color: 'blue', icon: SparklesIcon, text: 'Processing' },
    completed: { color: 'green', icon: CheckCircleIcon, text: 'Completed' },
    failed: { color: 'red', icon: ExclamationCircleIcon, text: 'Failed' },
  }

  const config = statusConfig[job.status]
  const StatusIcon = config.icon

  return (
    <div className="flex items-center justify-between py-3 border-b border-zinc-800 last:border-0">
      <div className="flex items-center gap-3">
        <StatusIcon className={`h-5 w-5 text-${config.color}-500`} />
        <div>
          <p className="text-white text-sm font-medium">{job.name}</p>
          <p className="text-zinc-500 text-xs">Job #{job.id}</p>
        </div>
      </div>
      <Badge color={config.color as any}>{config.text}</Badge>
    </div>
  )
}

// Activity Item
interface ActivityProps {
  id: string
  action: string
  target: string
  time: string
}

function ActivityItem({ activity }: { activity: ActivityProps }) {
  return (
    <div className="flex items-start gap-3 py-3 border-b border-zinc-800 last:border-0">
      <div className="rounded-full bg-violet-500/20 p-1.5 mt-0.5">
        <SparklesIcon className="h-3 w-3 text-violet-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-white text-sm">
          {activity.action} <span className="text-violet-400">{activity.target}</span>
        </p>
        <p className="text-zinc-500 text-xs mt-0.5">{activity.time}</p>
      </div>
    </div>
  )
}

// Main HomePage Component
export function HomePage() {
  // Mock data - replace with real API calls
  const metrics = [
    { title: 'Total Spend', value: 45230, prefix: '$', change: 12, trend: 'up' as const, icon: ChartBarIcon },
    { title: 'ROAS', value: 4.2, suffix: 'x', change: 8, trend: 'up' as const, icon: ArrowTrendingUpIcon },
    { title: 'Videos Generated', value: 156, change: 24, trend: 'up' as const, icon: FilmIcon },
    { title: 'Active Campaigns', value: 12, change: -5, trend: 'down' as const, icon: PlayCircleIcon },
  ]

  const quickActions = [
    { title: 'New Campaign', description: 'Create AI-powered video ads', icon: PlusIcon, href: '/create', color: 'bg-violet-600' },
    { title: 'Generate Video', description: 'Turn scripts into videos', icon: SparklesIcon, href: '/studio', color: 'bg-fuchsia-600' },
    { title: 'Analyze Competitor', description: 'Spy on winning ads', icon: ChartBarIcon, href: '/spy', color: 'bg-blue-600' },
    { title: 'View Analytics', description: 'Track campaign performance', icon: ChartBarIcon, href: '/analytics', color: 'bg-emerald-600' },
  ]

  const recentJobs: JobProps[] = [
    { id: '1234', name: 'PTD Transformation Ad', status: 'processing', progress: 65 },
    { id: '1233', name: 'Summer Promo Video', status: 'completed' },
    { id: '1232', name: 'Client Testimonial', status: 'queued' },
    { id: '1231', name: 'Coach Intro Reel', status: 'completed' },
  ]

  const recentActivity: ActivityProps[] = [
    { id: '1', action: 'Campaign launched:', target: 'Dubai Fitness Q4', time: '2 hours ago' },
    { id: '2', action: 'Video generated:', target: 'transformation-v3.mp4', time: '4 hours ago' },
    { id: '3', action: 'Ad published to:', target: 'Meta Ads', time: '6 hours ago' },
    { id: '4', action: 'Analysis completed:', target: 'Competitor Study', time: '1 day ago' },
  ]

  return (
    <div className="p-6 lg:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Heading level={1} className="text-white">Welcome back, Milos 👋</Heading>
          <Text className="text-zinc-400 mt-1">Here's what's happening with your campaigns today.</Text>
        </div>
        <Button color="violet" href="/create" className="gap-2">
          <PlusIcon className="h-4 w-4" />
          New Campaign
        </Button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric, index) => (
          <motion.div
            key={metric.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <MetricCard {...metric} />
          </motion.div>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <Heading level={2} className="text-white mb-4">Quick Actions</Heading>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <motion.div
              key={action.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 + index * 0.1 }}
            >
              <QuickAction {...action} />
            </motion.div>
          ))}
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Job Queue */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <Heading level={3} className="text-white">Generation Queue</Heading>
            <Badge color="violet">{recentJobs.filter(j => j.status === 'processing').length} Active</Badge>
          </div>
          <div className="space-y-1">
            {recentJobs.map((job) => (
              <JobItem key={job.id} job={job} />
            ))}
          </div>
          <Button plain className="w-full mt-4 text-zinc-400 hover:text-white">
            View All Jobs
          </Button>
        </motion.div>

        {/* Recent Activity */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-4">
            <Heading level={3} className="text-white">Recent Activity</Heading>
            <Link to="/activity" className="text-violet-400 text-sm hover:text-violet-300">
              View All
            </Link>
          </div>
          <div className="space-y-1">
            {recentActivity.map((activity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))}
          </div>
        </motion.div>
      </div>

      {/* AI Insights Panel */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 1 }}
        className="rounded-xl bg-gradient-to-r from-violet-900/50 to-fuchsia-900/50 border border-violet-500/30 p-6"
      >
        <div className="flex items-start gap-4">
          <div className="rounded-lg bg-violet-500/20 p-3">
            <SparklesIcon className="h-6 w-6 text-violet-400" />
          </div>
          <div className="flex-1">
            <Heading level={3} className="text-white">AI Insights</Heading>
            <Text className="text-zinc-300 mt-2">
              Your "Transformation Stories" campaign is outperforming by 34%. Consider increasing budget 
              and creating 3 more variants using the same hook style. Top-performing time: 6-9 PM Dubai time.
            </Text>
            <div className="flex gap-3 mt-4">
              <Button color="violet" className="gap-2">
                <SparklesIcon className="h-4 w-4" />
                Generate Variants
              </Button>
              <Button plain className="text-zinc-300">
                View Analysis
              </Button>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

export default HomePage
