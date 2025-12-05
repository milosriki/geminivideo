// ==========================================
// CampaignsPage.tsx - List all campaigns
// ==========================================
import { useState } from 'react'
import { PlusIcon } from '@heroicons/react/24/outline'
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
import { NoCampaignsEmpty } from '@/components/catalyst/empty-state'
import { useCampaignsList, useDeleteCampaign, usePauseCampaign, useResumeCampaign } from '@/hooks/useCampaigns'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'
import { useToastStore } from '@/stores/toastStore'

export function CampaignsPage() {
  const [selectedCampaign, setSelectedCampaign] = useState<any>(null)
  const [campaignToDelete, setCampaignToDelete] = useState<any>(null)

  // Fetch campaigns using React Query
  const { data: campaigns = [], isLoading, isError, error } = useCampaignsList()
  const deleteCampaign = useDeleteCampaign()
  const pauseCampaign = usePauseCampaign()
  const resumeCampaign = useResumeCampaign()
  const { addToast } = useToastStore()

  const handleDelete = async () => {
    if (!campaignToDelete) return

    try {
      await deleteCampaign.mutateAsync(campaignToDelete.id)
      addToast({
        title: 'Campaign Deleted',
        message: `${campaignToDelete.name} has been deleted.`,
        variant: 'success',
      })
      setCampaignToDelete(null)
    } catch (err: any) {
      addToast({
        title: 'Delete Failed',
        message: err.message || 'Failed to delete campaign',
        variant: 'error',
      })
    }
  }

  const handleToggleStatus = async (campaign: any) => {
    try {
      if (campaign.status === 'active') {
        await pauseCampaign.mutateAsync(campaign.id)
        addToast({
          title: 'Campaign Paused',
          message: `${campaign.name} has been paused.`,
          variant: 'success',
        })
      } else {
        await resumeCampaign.mutateAsync(campaign.id)
        addToast({
          title: 'Campaign Resumed',
          message: `${campaign.name} is now active.`,
          variant: 'success',
        })
      }
    } catch (err: any) {
      addToast({
        title: 'Update Failed',
        message: err.message || 'Failed to update campaign status',
        variant: 'error',
      })
    }
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Heading level={1} className="text-white">Campaigns</Heading>
          <Text className="text-zinc-400 mt-1">Manage your video ad campaigns.</Text>
        </div>
        <Button color="violet" href="/campaigns/create" className="gap-2">
          <PlusIcon className="h-4 w-4" />
          New Campaign
        </Button>
      </div>

      <div className="rounded-xl bg-zinc-900 border border-zinc-800 p-6">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" text="Loading campaigns..." />
          </div>
        ) : isError ? (
          <div className="text-center py-12">
            <p className="text-red-400">Failed to load campaigns</p>
            <p className="text-sm text-gray-400 mt-2">{(error as any)?.message}</p>
          </div>
        ) : campaigns.length === 0 ? (
          <NoCampaignsEmpty />
        ) : (
          <>
            <Table>
              <TableHead>
                <TableRow>
                  <TableHeader>Campaign</TableHeader>
                  <TableHeader>Status</TableHeader>
                  <TableHeader>Objective</TableHeader>
                  <TableHeader className="text-right">Budget</TableHeader>
                  <TableHeader className="text-right">Creatives</TableHeader>
                  <TableHeader>Actions</TableHeader>
                </TableRow>
              </TableHead>
              <TableBody>
                {campaigns.map((campaign) => (
                  <TableRow key={campaign.id} className="hover:bg-zinc-800/50">
                    <TableCell
                      className="font-medium text-white cursor-pointer"
                      onClick={() => setSelectedCampaign(campaign)}
                    >
                      {campaign.name}
                    </TableCell>
                    <TableCell>
                      <Badge color={
                        campaign.status === 'active' ? 'green' :
                        campaign.status === 'paused' ? 'yellow' :
                        campaign.status === 'draft' ? 'gray' : 'blue'
                      }>
                        {campaign.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="capitalize">{campaign.objective?.replace('_', ' ')}</TableCell>
                    <TableCell className="text-right">
                      ${campaign.budget?.amount} {campaign.budget?.type === 'daily' ? '/day' : 'total'}
                    </TableCell>
                    <TableCell className="text-right">{campaign.creatives?.length || 0}</TableCell>
                    <TableCell>
                      <div className="flex gap-2">
                        <Button
                          plain
                          onClick={(e) => {
                            e.stopPropagation()
                            handleToggleStatus(campaign)
                          }}
                        >
                          {campaign.status === 'active' ? 'Pause' : 'Resume'}
                        </Button>
                        <Button
                          plain
                          color="red"
                          onClick={(e) => {
                            e.stopPropagation()
                            setCampaignToDelete(campaign)
                          }}
                        >
                          Delete
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </>
        )}
      </div>

      <Dialog open={selectedCampaign !== null} onClose={() => setSelectedCampaign(null)} size="lg">
        <DialogTitle>Campaign Details</DialogTitle>
        <DialogDescription>"{selectedCampaign?.name}"</DialogDescription>
        <DialogBody>
          <div className="space-y-4">
            <Field>
              <Label>Campaign Name</Label>
              <Input defaultValue={selectedCampaign?.name} readOnly />
            </Field>
            <Field>
              <Label>Objective</Label>
              <Input defaultValue={selectedCampaign?.objective} readOnly className="capitalize" />
            </Field>
            <Field>
              <Label>Status</Label>
              <Input defaultValue={selectedCampaign?.status} readOnly className="capitalize" />
            </Field>
          </div>
        </DialogBody>
        <DialogActions>
          <Button plain onClick={() => setSelectedCampaign(null)}>Close</Button>
          <Button color="violet" href={`/campaigns/${selectedCampaign?.id}/edit`}>Edit Campaign</Button>
        </DialogActions>
      </Dialog>

      <Alert open={campaignToDelete !== null} onClose={() => setCampaignToDelete(null)}>
        <AlertTitle>Delete Campaign</AlertTitle>
        <AlertDescription>
          Are you sure you want to delete "{campaignToDelete?.name}"? This will permanently delete all associated data.
        </AlertDescription>
        <AlertActions>
          <Button plain onClick={() => setCampaignToDelete(null)}>Cancel</Button>
          <Button color="red" onClick={handleDelete} disabled={deleteCampaign.isPending}>
            {deleteCampaign.isPending ? 'Deleting...' : 'Delete'}
          </Button>
        </AlertActions>
      </Alert>
    </div>
  )
}

export default CampaignsPage
