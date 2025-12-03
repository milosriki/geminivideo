import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  CalendarIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Select } from '@/components/catalyst/select'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { Table, TableHead, TableBody, TableRow, TableHeader, TableCell } from '@/components/catalyst/table'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080'

interface ChartDataPoint {
  date: string
  spend: number
  revenue: number
  roas: number
  impressions: number
  clicks: number
}

interface CampaignData {
  id: string
  name: string
  status: string
  spend: number
  revenue: number
  roas: number
  conversions: number
}

// KPI Card Component
interface KPICardProps {
  title: string
  value: string
  change: number
  trend: 'up' | 'down'
  sparklineData?: number[]
}

function KPICard({ title, value, change, trend }: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
    >
      <div className="flex items-center justify-between">
        <Text className="text-zinc-400 text-sm">{title}</Text>
        <Badge color={trend === 'up' ? 'green' : 'red'} className="gap-1">
          {trend === 'up' ? (
            <ArrowTrendingUpIcon className="h-3 w-3" />
          ) : (
            <ArrowTrendingDownIcon className="h-3 w-3" />
          )}
          {Math.abs(change)}%
        </Badge>
      </div>
      <p className="text-3xl font-bold text-white mt-2">{value}</p>
      <div className="h-10 mt-4">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData.slice(-7)}>
            <Area
              type="monotone"
              dataKey="roas"
              stroke="#8b5cf6"
              fill="#8b5cf6"
              fillOpacity={0.2}
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </motion.div>
  )
}

// Custom Tooltip
function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    return (
      <div className="bg-zinc-800 border border-zinc-700 rounded-lg p-3 shadow-xl">
        <p className="text-zinc-400 text-xs mb-2">{label}</p>
        {payload.map((item: any, index: number) => (
          <p key={index} className="text-sm" style={{ color: item.color }}>
            {item.name}: {typeof item.value === 'number' && item.name.includes('AED')
              ? `AED ${item.value.toLocaleString()}`
              : item.value.toLocaleString()}
          </p>
        ))}
      </div>
    )
  }
  return null
}

export function AnalyticsPage() {
  const [dateRange, setDateRange] = useState('7d')
  const [metric, setMetric] = useState('all')
  const [chartData, setChartData] = useState<ChartDataPoint[]>([])
  const [campaignData, setCampaignData] = useState<CampaignData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [chartRes, campaignRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/analytics/chart?range=${dateRange}`),
          fetch(`${API_BASE_URL}/api/campaigns`)
        ])

        if (chartRes.ok) {
          const data = await chartRes.json()
          setChartData(data.chart || [])
        }

        if (campaignRes.ok) {
          const data = await campaignRes.json()
          setCampaignData(data.campaigns || [])
        }
      } catch (err) {
        console.error('Failed to fetch analytics:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [dateRange])

  const kpis = [
    { title: 'Total Revenue', value: 'AED 38,250', change: 12, trend: 'up' as const },
    { title: 'Total Spend', value: 'AED 8,500', change: 8, trend: 'up' as const },
    { title: 'ROAS', value: '4.5x', change: 15, trend: 'up' as const },
    { title: 'Conversions', value: '127', change: 22, trend: 'up' as const },
    { title: 'CTR', value: '2.1%', change: -3, trend: 'down' as const },
    { title: 'CPA', value: 'AED 67', change: -8, trend: 'up' as const },
  ]

  return (
    <div className="p-6 lg:p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Heading level={1} className="text-white">Analytics</Heading>
          <Text className="text-zinc-400 mt-1">Track your campaign performance and ROI.</Text>
        </div>
        <div className="flex items-center gap-3">
          <Select value={dateRange} onChange={(e) => setDateRange(e.target.value)}>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="90d">Last 90 days</option>
          </Select>
          <Button outline className="gap-2">
            <CalendarIcon className="h-4 w-4" />
            Custom
          </Button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi, index) => (
          <motion.div
            key={kpi.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <KPICard {...kpi} />
          </motion.div>
        ))}
      </div>

      {/* Main Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue vs Spend */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <Heading level={3} className="text-white">Revenue vs Spend</Heading>
            <Select value={metric} onChange={(e) => setMetric(e.target.value)} className="w-32">
              <option value="all">All</option>
              <option value="revenue">Revenue</option>
              <option value="spend">Spend</option>
            </Select>
          </div>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="date" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="revenue"
                  name="Revenue (AED)"
                  stroke="#10b981"
                  fill="url(#colorRevenue)"
                  strokeWidth={2}
                />
                <Area
                  type="monotone"
                  dataKey="spend"
                  name="Spend (AED)"
                  stroke="#8b5cf6"
                  fill="url(#colorSpend)"
                  strokeWidth={2}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        {/* ROAS Trend */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
          className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <Heading level={3} className="text-white">ROAS Trend</Heading>
            <Badge color="green">+15% vs last period</Badge>
          </div>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="date" stroke="#71717a" fontSize={12} />
                <YAxis stroke="#71717a" fontSize={12} domain={[0, 6]} />
                <Tooltip content={<CustomTooltip />} />
                <Line
                  type="monotone"
                  dataKey="roas"
                  name="ROAS"
                  stroke="#f59e0b"
                  strokeWidth={3}
                  dot={{ fill: '#f59e0b', strokeWidth: 2 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      {/* Campaign Performance Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="rounded-xl bg-zinc-900 border border-zinc-800 p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <Heading level={3} className="text-white">Campaign Performance</Heading>
          <Button outline className="gap-2">
            <FunnelIcon className="h-4 w-4" />
            Filter
          </Button>
        </div>
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Campaign</TableHeader>
              <TableHeader>Status</TableHeader>
              <TableHeader className="text-right">Spend</TableHeader>
              <TableHeader className="text-right">Revenue</TableHeader>
              <TableHeader className="text-right">ROAS</TableHeader>
              <TableHeader className="text-right">Conversions</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {campaignData.map((campaign) => (
              <TableRow key={campaign.id} className="hover:bg-zinc-800/50 cursor-pointer">
                <TableCell className="font-medium text-white">{campaign.name}</TableCell>
                <TableCell>
                  <Badge
                    color={
                      campaign.status === 'active'
                        ? 'green'
                        : campaign.status === 'paused'
                        ? 'yellow'
                        : 'zinc'
                    }
                  >
                    {campaign.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">AED {campaign.spend.toLocaleString()}</TableCell>
                <TableCell className="text-right text-emerald-400">
                  AED {campaign.revenue.toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  {campaign.roas > 0 ? `${campaign.roas}x` : '-'}
                </TableCell>
                <TableCell className="text-right">{campaign.conversions || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </motion.div>
    </div>
  )
}

export default AnalyticsPage
