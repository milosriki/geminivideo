// ==========================================
// CampaignsPage.tsx - List all campaigns
// ==========================================
import { motion } from 'framer-motion'
import { PlusIcon, FunnelIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { Table, TableHead, TableBody, TableRow, TableHeader, TableCell } from '@/components/catalyst/table'

const campaigns = [
  { id: '1', name: 'PTD Transformation Q4', status: 'active', spend: 8500, roas: 4.5, videos: 12 },
  { id: '2', name: 'Dubai Executives', status: 'active', spend: 5200, roas: 4.0, videos: 8 },
  { id: '3', name: 'Summer Body Promo', status: 'paused', spend: 3100, roas: 4.0, videos: 6 },
  { id: '4', name: 'Coach Testimonials', status: 'active', spend: 2400, roas: 4.8, videos: 15 },
]

export function CampaignsPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Heading level={1} className="text-white">Campaigns</Heading>
          <Text className="text-zinc-400 mt-1">Manage your video ad campaigns.</Text>
        </div>
        <Button color="violet" href="/create" className="gap-2">
          <PlusIcon className="h-4 w-4" />
          New Campaign
        </Button>
      </div>

      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
        <Table>
          <TableHead>
            <TableRow>
              <TableHeader>Campaign</TableHeader>
              <TableHeader>Status</TableHeader>
              <TableHeader className="text-right">Spend</TableHeader>
              <TableHeader className="text-right">ROAS</TableHeader>
              <TableHeader className="text-right">Videos</TableHeader>
            </TableRow>
          </TableHead>
          <TableBody>
            {campaigns.map((campaign) => (
              <TableRow key={campaign.id} className="hover:bg-zinc-800/50 cursor-pointer">
                <TableCell className="font-medium text-white">{campaign.name}</TableCell>
                <TableCell>
                  <Badge color={campaign.status === 'active' ? 'green' : 'yellow'}>
                    {campaign.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">AED {campaign.spend.toLocaleString()}</TableCell>
                <TableCell className="text-right">{campaign.roas}x</TableCell>
                <TableCell className="text-right">{campaign.videos}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

export default CampaignsPage
