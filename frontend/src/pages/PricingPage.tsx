import { useState } from 'react'
import { Button } from '@/components/radiant/button'
import { Container } from '@/components/radiant/container'
import { Gradient, GradientBackground } from '@/components/radiant/gradient'
import { Heading, Lead, Subheading } from '@/components/radiant/text'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import {
  CheckIcon,
  ChevronUpDownIcon,
  MinusIcon,
} from '@heroicons/react/16/solid'
import { clsx } from 'clsx'

interface TierFeature {
  description: string
  disabled?: boolean
}

interface TierDetailedFeature {
  section: string
  name: string
  value: string | number | boolean
}

interface Tier {
  name: 'Free' | 'Pro' | 'Enterprise'
  slug: string
  description: string
  priceMonthly: number
  priceAnnual: number
  href: string
  popular?: boolean
  highlights: TierFeature[]
  features: TierDetailedFeature[]
}

const tiers: Tier[] = [
  {
    name: 'Free',
    slug: 'free',
    description: 'Perfect for trying out AI video creation.',
    priceMonthly: 0,
    priceAnnual: 0,
    href: '/register',
    highlights: [
      { description: '5 videos per month' },
      { description: '720p video quality' },
      { description: 'Basic templates library' },
      { description: 'AI voice generation', disabled: true },
      { description: 'Priority processing', disabled: true },
    ],
    features: [
      { section: 'Video Creation', name: 'Monthly videos', value: 5 },
      { section: 'Video Creation', name: 'Max video length', value: '30 seconds' },
      { section: 'Video Creation', name: 'Video quality', value: '720p' },
      { section: 'Video Creation', name: 'Templates', value: 'Basic' },
      { section: 'Video Creation', name: 'Custom branding', value: false },
      { section: 'AI Features', name: 'AI voice generation', value: false },
      { section: 'AI Features', name: 'AI script writing', value: false },
      { section: 'AI Features', name: 'Auto-captions', value: false },
      { section: 'AI Features', name: 'Smart b-roll', value: false },
      { section: 'Support', name: 'Community support', value: true },
      { section: 'Support', name: 'Email support', value: false },
      { section: 'Support', name: 'Priority support', value: false },
    ],
  },
  {
    name: 'Pro',
    slug: 'pro',
    description: 'Everything you need for professional content.',
    priceMonthly: 29,
    priceAnnual: 290,
    href: '/register',
    popular: true,
    highlights: [
      { description: '100 videos per month' },
      { description: '4K video quality' },
      { description: 'Premium templates & assets' },
      { description: 'AI voice generation' },
      { description: 'Priority processing & support' },
    ],
    features: [
      { section: 'Video Creation', name: 'Monthly videos', value: 100 },
      { section: 'Video Creation', name: 'Max video length', value: '10 minutes' },
      { section: 'Video Creation', name: 'Video quality', value: '4K' },
      { section: 'Video Creation', name: 'Templates', value: 'Premium' },
      { section: 'Video Creation', name: 'Custom branding', value: true },
      { section: 'AI Features', name: 'AI voice generation', value: true },
      { section: 'AI Features', name: 'AI script writing', value: true },
      { section: 'AI Features', name: 'Auto-captions', value: true },
      { section: 'AI Features', name: 'Smart b-roll', value: '50 / month' },
      { section: 'Support', name: 'Community support', value: true },
      { section: 'Support', name: 'Email support', value: true },
      { section: 'Support', name: 'Priority support', value: false },
    ],
  },
  {
    name: 'Enterprise',
    slug: 'enterprise',
    description: 'Advanced features for teams and agencies.',
    priceMonthly: 99,
    priceAnnual: 990,
    href: '/contact',
    highlights: [
      { description: 'Unlimited videos' },
      { description: '4K video quality' },
      { description: 'All premium features' },
      { description: 'Team collaboration' },
      { description: 'Dedicated account manager' },
    ],
    features: [
      { section: 'Video Creation', name: 'Monthly videos', value: 'Unlimited' },
      { section: 'Video Creation', name: 'Max video length', value: 'Unlimited' },
      { section: 'Video Creation', name: 'Video quality', value: '4K' },
      { section: 'Video Creation', name: 'Templates', value: 'Premium' },
      { section: 'Video Creation', name: 'Custom branding', value: true },
      { section: 'AI Features', name: 'AI voice generation', value: true },
      { section: 'AI Features', name: 'AI script writing', value: true },
      { section: 'AI Features', name: 'Auto-captions', value: true },
      { section: 'AI Features', name: 'Smart b-roll', value: 'Unlimited' },
      { section: 'Support', name: 'Community support', value: true },
      { section: 'Support', name: 'Email support', value: true },
      { section: 'Support', name: 'Priority support', value: true },
    ],
  },
]

function Header() {
  return (
    <Container className="mt-16">
      <Heading as="h1" dark>
        Pricing that scales with your creativity.
      </Heading>
      <Lead className="mt-6 max-w-3xl text-zinc-400">
        Create stunning AI-powered videos at any scale. Start free and upgrade
        as your needs grow.
      </Lead>
    </Container>
  )
}

function BillingToggle({
  billingPeriod,
  setBillingPeriod,
}: {
  billingPeriod: 'monthly' | 'annual'
  setBillingPeriod: (period: 'monthly' | 'annual') => void
}) {
  return (
    <div className="flex items-center justify-center gap-3">
      <span
        className={clsx(
          'text-sm font-medium transition-colors',
          billingPeriod === 'monthly' ? 'text-white' : 'text-zinc-500'
        )}
      >
        Monthly
      </span>
      <button
        onClick={() =>
          setBillingPeriod(billingPeriod === 'monthly' ? 'annual' : 'monthly')
        }
        className="relative inline-flex h-6 w-11 items-center rounded-full bg-zinc-800 transition-colors hover:bg-zinc-700"
        aria-label="Toggle billing period"
      >
        <span
          className={clsx(
            'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
            billingPeriod === 'annual' ? 'translate-x-6' : 'translate-x-1'
          )}
        />
      </button>
      <span
        className={clsx(
          'text-sm font-medium transition-colors',
          billingPeriod === 'annual' ? 'text-white' : 'text-zinc-500'
        )}
      >
        Annual
        <span className="ml-1.5 rounded-full bg-purple-500/20 px-2 py-0.5 text-xs text-purple-300">
          Save 17%
        </span>
      </span>
    </div>
  )
}

function PricingCards({ billingPeriod }: { billingPeriod: 'monthly' | 'annual' }) {
  return (
    <div className="relative py-24">
      <Gradient className="absolute inset-x-2 top-48 bottom-0 rounded-4xl opacity-10 ring-1 ring-white/10 ring-inset" />
      <Container className="relative">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {tiers.map((tier, tierIndex) => (
            <PricingCard
              key={tierIndex}
              tier={tier}
              billingPeriod={billingPeriod}
            />
          ))}
        </div>
      </Container>
    </div>
  )
}

function PricingCard({
  tier,
  billingPeriod,
}: {
  tier: Tier
  billingPeriod: 'monthly' | 'annual'
}) {
  const price = billingPeriod === 'monthly' ? tier.priceMonthly : tier.priceAnnual
  const monthlyEquivalent = billingPeriod === 'annual' ? Math.floor(price / 12) : price

  return (
    <div
      className={clsx(
        '-m-2 grid grid-cols-1 rounded-4xl ring-1 max-lg:mx-auto max-lg:w-full max-lg:max-w-md',
        tier.popular
          ? 'bg-purple-500/10 ring-purple-500/50 shadow-[inset_0_0_2px_1px_rgba(168,85,247,0.4)]'
          : 'ring-white/10 shadow-[inset_0_0_2px_1px_rgba(255,255,255,0.1)]'
      )}
    >
      <div className="grid grid-cols-1 rounded-4xl p-2 shadow-md shadow-black/20">
        <div className="relative rounded-3xl bg-zinc-900 p-10 pb-9 shadow-2xl ring-1 ring-white/10">
          {tier.popular && (
            <div className="absolute -top-5 left-0 right-0 mx-auto w-fit rounded-full bg-gradient-to-r from-purple-500 to-pink-500 px-4 py-1 text-xs font-semibold text-white shadow-lg">
              Most Popular
            </div>
          )}
          <Subheading dark>{tier.name}</Subheading>
          <p className="mt-2 text-sm/6 text-zinc-400">{tier.description}</p>
          <div className="mt-8 flex items-baseline gap-2">
            <div className="text-5xl font-medium text-white">
              ${monthlyEquivalent}
            </div>
            <div className="text-sm/5 text-zinc-400">
              <p>USD</p>
              <p>per month</p>
            </div>
          </div>
          {billingPeriod === 'annual' && tier.priceAnnual > 0 && (
            <p className="mt-2 text-sm text-zinc-500">
              ${tier.priceAnnual} billed annually
            </p>
          )}
          <div className="mt-8">
            <Button
              href={tier.href}
              variant={tier.popular ? 'secondary' : 'outline'}
              className="w-full"
            >
              {tier.name === 'Free' ? 'Get started free' : 'Start free trial'}
            </Button>
          </div>
          <div className="mt-8">
            <h3 className="text-sm/6 font-medium text-white">
              What's included:
            </h3>
            <ul className="mt-3 space-y-3">
              {tier.highlights.map((props, featureIndex) => (
                <FeatureItem key={featureIndex} {...props} />
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

function PricingTable({ selectedTier }: { selectedTier: Tier }) {
  return (
    <Container className="py-24">
      <Subheading dark className="text-center">
        Compare features
      </Subheading>
      <Heading as="div" dark className="mt-2 text-center">
        Find the perfect plan for you.
      </Heading>
      <table className="mt-16 w-full text-left">
        <caption className="sr-only">Pricing plan comparison</caption>
        <colgroup>
          <col className="w-3/5 sm:w-2/5" />
          <col
            data-selected={selectedTier === tiers[0] ? true : undefined}
            className="w-2/5 data-selected:table-column max-sm:hidden sm:w-1/5"
          />
          <col
            data-selected={selectedTier === tiers[1] ? true : undefined}
            className="w-2/5 data-selected:table-column max-sm:hidden sm:w-1/5"
          />
          <col
            data-selected={selectedTier === tiers[2] ? true : undefined}
            className="w-2/5 data-selected:table-column max-sm:hidden sm:w-1/5"
          />
        </colgroup>
        <thead>
          <tr className="max-sm:hidden">
            <td className="p-0" />
            {tiers.map((tier) => (
              <th
                key={tier.slug}
                scope="col"
                data-selected={selectedTier === tier ? true : undefined}
                className="p-0 data-selected:table-cell max-sm:hidden"
              >
                <Subheading as="div" dark>
                  {tier.name}
                </Subheading>
              </th>
            ))}
          </tr>
          <tr className="sm:hidden">
            <td className="p-0">
              <div className="relative inline-block">
                <Menu>
                  <MenuButton className="flex items-center justify-between gap-2 font-medium text-white">
                    {selectedTier.name}
                    <ChevronUpDownIcon className="size-4 fill-zinc-400" />
                  </MenuButton>
                  <MenuItems
                    anchor="bottom start"
                    className="min-w-[var(--button-width)] rounded-lg bg-zinc-800 p-1 shadow-lg ring-1 ring-white/10 [--anchor-gap:6px] [--anchor-offset:-4px] [--anchor-padding:10px]"
                  >
                    {tiers.map((tier) => (
                      <MenuItem key={tier.slug}>
                        <button
                          onClick={() => {
                            // In a real implementation, this would update the selected tier
                          }}
                          data-selected={tier === selectedTier ? true : undefined}
                          className="group flex w-full items-center gap-2 rounded-md px-2 py-1 text-white data-focus:bg-zinc-700"
                        >
                          {tier.name}
                          <CheckIcon className="hidden size-4 group-data-selected:block" />
                        </button>
                      </MenuItem>
                    ))}
                  </MenuItems>
                </Menu>
              </div>
            </td>
            <td colSpan={3} className="p-0 text-right">
              <Button variant="outline" href={selectedTier.href}>
                Get started
              </Button>
            </td>
          </tr>
          <tr className="max-sm:hidden">
            <th className="p-0" scope="row">
              <span className="sr-only">Get started</span>
            </th>
            {tiers.map((tier) => (
              <td
                key={tier.slug}
                data-selected={selectedTier === tier ? true : undefined}
                className="px-0 pt-4 pb-0 data-selected:table-cell max-sm:hidden"
              >
                <Button variant="outline" href={tier.href}>
                  Get started
                </Button>
              </td>
            ))}
          </tr>
        </thead>
        {[...new Set(tiers[0].features.map(({ section }) => section))].map(
          (section) => (
            <tbody key={section} className="group">
              <tr>
                <th
                  scope="colgroup"
                  colSpan={4}
                  className="px-0 pt-10 pb-0 group-first-of-type:pt-5"
                >
                  <div className="-mx-4 rounded-lg bg-zinc-800/50 px-4 py-3 text-sm/6 font-semibold text-white">
                    {section}
                  </div>
                </th>
              </tr>
              {tiers[0].features
                .filter((feature) => feature.section === section)
                .map(({ name }) => (
                  <tr
                    key={name}
                    className="border-b border-zinc-800 last:border-none"
                  >
                    <th
                      scope="row"
                      className="px-0 py-4 text-sm/6 font-normal text-zinc-400"
                    >
                      {name}
                    </th>
                    {tiers.map((tier) => {
                      let value = tier.features.find(
                        (feature) =>
                          feature.section === section && feature.name === name
                      )?.value

                      return (
                        <td
                          key={tier.slug}
                          data-selected={selectedTier === tier ? true : undefined}
                          className="p-4 data-selected:table-cell max-sm:hidden"
                        >
                          {value === true ? (
                            <>
                              <CheckIcon className="size-4 fill-green-500" />
                              <span className="sr-only">
                                Included in {tier.name}
                              </span>
                            </>
                          ) : value === false || value === undefined ? (
                            <>
                              <MinusIcon className="size-4 fill-zinc-600" />
                              <span className="sr-only">
                                Not included in {tier.name}
                              </span>
                            </>
                          ) : (
                            <div className="text-sm/6 text-white">{value}</div>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
            </tbody>
          )
        )}
      </table>
    </Container>
  )
}

function FeatureItem({
  description,
  disabled = false,
}: {
  description: string
  disabled?: boolean
}) {
  return (
    <li
      data-disabled={disabled ? true : undefined}
      className="flex items-start gap-4 text-sm/6 text-zinc-300 data-disabled:text-zinc-600"
    >
      <span className="inline-flex h-6 items-center">
        <PlusIcon
          className={clsx(
            'size-3.75 shrink-0',
            disabled ? 'fill-zinc-600' : 'fill-purple-400'
          )}
        />
      </span>
      {disabled && <span className="sr-only">Not included:</span>}
      {description}
    </li>
  )
}

function PlusIcon(props: React.ComponentPropsWithoutRef<'svg'>) {
  return (
    <svg viewBox="0 0 15 15" aria-hidden="true" {...props}>
      <path clipRule="evenodd" d="M8 0H7v7H0v1h7v7h1V8h7V7H8V0z" />
    </svg>
  )
}

function FrequentlyAskedQuestions() {
  const faqs = [
    {
      question: 'Can I change my plan later?',
      answer:
        'Absolutely! You can upgrade or downgrade your plan at any time. Changes to your plan will be reflected in your next billing cycle, and we\'ll prorate any differences.',
    },
    {
      question: 'What payment methods do you accept?',
      answer:
        'We accept all major credit cards (Visa, Mastercard, American Express, Discover) and PayPal. For Enterprise plans, we also offer invoice-based billing with NET 30 terms.',
    },
    {
      question: 'Is there a free trial available?',
      answer:
        'Yes! All paid plans come with a 14-day free trial. No credit card required to start. You can explore all features and create videos to see if it\'s the right fit for you.',
    },
    {
      question: 'What happens if I exceed my video limit?',
      answer:
        'If you reach your monthly video limit, you can either wait until the next billing cycle or upgrade to a higher plan. We\'ll notify you when you\'re approaching your limit so you can plan accordingly.',
    },
    {
      question: 'Do you offer refunds?',
      answer:
        'We offer a 30-day money-back guarantee on all paid plans. If you\'re not satisfied with GeminiVideo for any reason, contact our support team within 30 days of your purchase for a full refund.',
    },
    {
      question: 'Can I cancel my subscription anytime?',
      answer:
        'Yes, you can cancel your subscription at any time from your account settings. Your access will continue until the end of your current billing period, and you won\'t be charged again.',
    },
  ]

  return (
    <Container className="pb-24">
      <section id="faqs" className="scroll-mt-8">
        <Subheading dark className="text-center">
          Frequently asked questions
        </Subheading>
        <Heading as="div" dark className="mt-2 text-center">
          Everything you need to know.
        </Heading>
        <div className="mx-auto mt-16 mb-16 max-w-3xl space-y-12">
          {faqs.map((faq, index) => (
            <dl key={index}>
              <dt className="text-base font-semibold text-white">{faq.question}</dt>
              <dd className="mt-4 text-base/7 text-zinc-400">{faq.answer}</dd>
            </dl>
          ))}
        </div>
        <div className="mt-16 text-center">
          <p className="text-base text-zinc-400">
            Still have questions?{' '}
            <a
              href="/contact"
              className="font-semibold text-purple-400 hover:text-purple-300"
            >
              Contact our team
            </a>
          </p>
        </div>
      </section>
    </Container>
  )
}

export default function PricingPage() {
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'annual'>('monthly')
  const [selectedTier, setSelectedTier] = useState<Tier>(tiers[1]) // Default to Pro

  return (
    <main className="overflow-hidden bg-zinc-950">
      <GradientBackground />
      <Header />
      <div className="mt-12 flex justify-center">
        <BillingToggle
          billingPeriod={billingPeriod}
          setBillingPeriod={setBillingPeriod}
        />
      </div>
      <PricingCards billingPeriod={billingPeriod} />
      <PricingTable selectedTier={selectedTier} />
      <FrequentlyAskedQuestions />
    </main>
  )
}
