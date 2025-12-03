import { DescriptionList, DescriptionTerm, DescriptionDetails } from '@/components/catalyst/description-list'
import { Heading } from '@/components/catalyst/heading'
import { Button } from '@/components/catalyst/button'
import { ArrowRightIcon } from '@heroicons/react/20/solid'

export function RecentActivity() {
  return (
    <div className="p-6 rounded-lg border border-zinc-950/5 bg-white shadow-sm dark:border-white/5 dark:bg-zinc-900">
      <div className="flex items-center justify-between mb-4">
        <Heading level={2}>Recent Activity</Heading>
        <Button plain className="-mr-2">
          View all
          <ArrowRightIcon />
        </Button>
      </div>
      <DescriptionList>
        <DescriptionTerm>Campaign "Summer Sale"</DescriptionTerm>
        <DescriptionDetails>Launched 2 hours ago • Budget: $500/day</DescriptionDetails>

        <DescriptionTerm>Video Generation</DescriptionTerm>
        <DescriptionDetails>Completed 5 variations for "Tech Gadget" • 15 mins ago</DescriptionDetails>

        <DescriptionTerm>Ad Spy Alert</DescriptionTerm>
        <DescriptionDetails>Competitor "BrandX" launched 3 new video ads • 1 hour ago</DescriptionDetails>

        <DescriptionTerm>Asset Upload</DescriptionTerm>
        <DescriptionDetails>Uploaded 12 new product images • 3 hours ago</DescriptionDetails>
      </DescriptionList>
    </div>
  )
}
