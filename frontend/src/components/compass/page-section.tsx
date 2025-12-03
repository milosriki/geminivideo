import { clsx } from 'clsx'

export function PageSection({
    title,
    description,
    children,
    className,
}: {
    title: string
    description?: string
    children: React.ReactNode
    className?: string
}) {
    return (
        <section className={clsx('py-12', className)}>
            <div className="mb-8">
                <h2 className="text-2xl font-bold tracking-tight text-zinc-900 dark:text-white">
                    {title}
                </h2>
                {description && (
                    <p className="mt-2 text-base text-zinc-500 dark:text-zinc-400">
                        {description}
                    </p>
                )}
            </div>
            {children}
        </section>
    )
}
