// ==========================================
// CampaignsPage.tsx - List all campaigns
// ==========================================
import { useState } from 'react'
import { motion } from 'framer-motion'
import { PlusIcon, FunnelIcon } from '@heroicons/react/24/outline'
import { Button } from '@/components/catalyst/button'
import { Badge } from '@/components/catalyst/badge'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { Table, TableHead, TableBody, TableRow, TableHeader, TableCell } from '@/components/catalyst/table'
import { Dialog, DialogTitle, DialogDescription, DialogBody, DialogActions } from '@/components/catalyst/dialog'
import { Alert, AlertTitle, AlertDescription, AlertActions } from '@/components/catalyst/alert'
import { Pagination, PaginationPrevious, PaginationNext, PaginationList, PaginationPage } from '@/components/catalyst/pagination'
import { Field } from '@/components/catalyst/fieldset'
import { Label } from '@/components/catalyst/fieldset'
import { Input } from '@/components/catalyst/input'

const campaigns = [
  { id: '1', name: 'PTD Transformation Q4', status: 'active', spend: 8500, roas: 4.5, videos: 12 },
  { id: '2', name: 'Dubai Executives', status: 'active', spend: 5200, roas: 4.0, videos: 8 },
  { id: '3', name: 'Summer Body Promo', status: 'paused', spend: 3100, roas: 4.0, videos: 6 },
  { id: '4', name: 'Coach Testimonials', status: 'active', spend: 2400, roas: 4.8, videos: 15 },
]

export function CampaignsPage() {
  const [selectedCampaign, setSelectedCampaign] = useState<any>(null)
  const [campaignToDelete, setCampaignToDelete] = useState<any>(null)

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
              <TableRow key={campaign.id} className="hover:bg-zinc-800/50 cursor-pointer" onClick={() => setSelectedCampaign(campaign)}>
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
        <div className="mt-6 border-t border-zinc-800 pt-6">
          <Pagination>
            <PaginationPrevious href={null} />
            <PaginationList>
              <PaginationPage href="#" current>1</PaginationPage>
              <PaginationPage href="#">2</PaginationPage>
            </PaginationList>
            <PaginationNext href="#" />
          </Pagination>
        </div>
      </div>

      <Dialog open={selectedCampaign !== null} onClose={() => setSelectedCampaign(null)} size="lg">
        <DialogTitle>Campaign Settings</DialogTitle>
        <DialogDescription>Manage "{selectedCampaign?.name}"</DialogDescription>
        <DialogBody>
          <Field>
            <Label>Campaign Name</Label>
            <Input defaultValue={selectedCampaign?.name} />
          </Field>
        </DialogBody>
        <DialogActions>
          <Button plain onClick={() => setSelectedCampaign(null)}>Cancel</Button>
          <Button color="violet">Save Changes</Button>
        </DialogActions>
      </Dialog>

      <Alert open={campaignToDelete !== null} onClose={() => setCampaignToDelete(null)}>
        <AlertTitle>Delete Campaign</AlertTitle>
        <AlertDescription>This will permanently delete all associated data.</AlertDescription>
        <AlertActions>
          <Button plain onClick={() => setCampaignToDelete(null)}>Cancel</Button>
          <Button color="red">Delete</Button>
        </AlertActions>
      </Alert>
    </div>
  )
}

export default CampaignsPage
