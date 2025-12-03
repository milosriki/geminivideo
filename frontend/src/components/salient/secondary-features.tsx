import { Container } from './Container'

const features = [
    {
        name: 'Reporting',
        summary: 'Stay on top of things with always up-to-date reporting features.',
        description:
            'We talked about reporting in the section above but we needed three items here, so mentioning it one more time for good measure.',
        icon: (
            <svg viewBox="0 0 32 32" aria-hidden="true" className="h-8 w-8 text-white">
                <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M16 32C7.163 32 0 24.837 0 16S7.163 0 16 0s16 7.163 16 16-7.163 16-16 16zm0-2c7.732 0 14-6.268 14-14S23.732 2 16 2 2 8.268 2 16s6.268 14 14 14zm0-26a2 2 0 100 4 2 2 0 000-4zm-6 8a2 2 0 100 4 2 2 0 000-4zm12 0a2 2 0 100 4 2 2 0 000-4zm-6 8a2 2 0 100 4 2 2 0 000-4z"
                    fill="currentColor"
                />
            </svg>
        ),
    },
    {
        name: 'Inventory',
        summary: 'Never lose track of what’s in stock with accurate inventory tracking.',
        description:
            'We don’t offer this as part of our software but that statement is inarguably true. Accurate inventory tracking is definitely a good idea.',
        icon: (
            <svg viewBox="0 0 32 32" aria-hidden="true" className="h-8 w-8 text-white">
                <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M9 0a4 4 0 00-4 4v24a4 4 0 004 4h14a4 4 0 004-4V4a4 4 0 00-4-4H9zm0 2a2 2 0 00-2 2v24a2 2 0 002 2h14a2 2 0 002-2V4a2 2 0 00-2-2H9zm2 4a1 1 0 100 2 1 1 0 000-2zm0 6a1 1 0 100 2 1 1 0 000-2zm0 6a1 1 0 100 2 1 1 0 000-2zm6-12a1 1 0 100 2 1 1 0 000-2zm0 6a1 1 0 100 2 1 1 0 000-2zm0 6a1 1 0 100 2 1 1 0 000-2z"
                    fill="currentColor"
                />
            </svg>
        ),
    },
    {
        name: 'Contacts',
        summary: 'Organize all of your contacts, service providers, and invoices in one place.',
        description:
            'This also isn’t actually a feature, it’s just some friendly advice. We definitely recommend that you do this, you’ll feel really organized.',
        icon: (
            <svg viewBox="0 0 32 32" aria-hidden="true" className="h-8 w-8 text-white">
                <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M16 32C7.163 32 0 24.837 0 16S7.163 0 16 0s16 7.163 16 16-7.163 16-16 16zm0-2c7.732 0 14-6.268 14-14S23.732 2 16 2 2 8.268 2 16s6.268 14 14 14zm-5-17a3 3 0 116 0 3 3 0 01-6 0zm3-5a5 5 0 100 10 5 5 0 000-10zm-6 17c0-2.761 2.686-5 6-5s6 2.239 6 5v1H8v-1zm-2 1v-1c0-3.866 3.582-7 8-7s8 3.134 8 7v1H6z"
                    fill="currentColor"
                />
            </svg>
        ),
    },
]

export function SecondaryFeatures() {
    return (
        <section
            id="secondary-features"
            aria-label="Features for simplifying everyday business tasks"
            className="pb-14 pt-20 sm:pb-20 sm:pt-32 lg:pb-32"
        >
            <Container>
                <div className="mx-auto max-w-2xl md:text-center">
                    <h2 className="font-display text-3xl tracking-tight text-slate-900 sm:text-4xl">
                        Simplify everyday business tasks.
                    </h2>
                    <p className="mt-4 text-lg tracking-tight text-slate-700">
                        Because you’d probably be a little confused if we suggested you complicate your everyday business tasks
                        instead.
                    </p>
                </div>
                <ul
                    role="list"
                    className="mx-auto mt-16 grid max-w-2xl grid-cols-1 gap-6 text-sm sm:mt-20 sm:grid-cols-2 md:gap-y-10 lg:max-w-none lg:grid-cols-3"
                >
                    {features.map((feature) => (
                        <li
                            key={feature.name}
                            className="rounded-2xl border border-slate-200 p-8"
                        >
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600">
                                {feature.icon}
                            </div>
                            <h3 className="mt-6 font-semibold text-slate-900">{feature.name}</h3>
                            <p className="mt-2 text-slate-700">{feature.summary}</p>
                            <p className="mt-4 text-slate-500">{feature.description}</p>
                        </li>
                    ))}
                </ul>
            </Container>
        </section>
    )
}
