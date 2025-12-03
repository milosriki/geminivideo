import { Badge } from '@/components/catalyst/badge'
import { Text } from '@/components/catalyst/text'
import { motion } from 'motion/react'
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/20/solid'

interface MetricCardProps {
  label: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
  icon?: React.ElementType
}

export function MetricCard({ label, value, change, trend, icon: Icon }: MetricCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-6 rounded-lg border border-zinc-950/5 bg-white shadow-sm dark:border-white/5 dark:bg-zinc-900"
    >
      <div className="flex items-center justify-between">
        <Text>{label}</Text>
        {Icon && <Icon className="size-5 text-zinc-400" />}
      </div>
      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-3xl font-semibold text-zinc-950 dark:text-white">{value}</span>
        <Badge color={trend === 'up' ? 'emerald' : trend === 'down' ? 'red' : 'zinc'}>
          {trend === 'up' && <ArrowUpIcon className="size-3 mr-1" />}
          {trend === 'down' && <ArrowDownIcon className="size-3 mr-1" />}
          {trend === 'neutral' && <MinusIcon className="size-3 mr-1" />}
          {change}
        </Badge>
      </div>
    </motion.div>
  )
}
