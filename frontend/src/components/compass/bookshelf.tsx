import { clsx } from 'clsx'

export function Bookshelf({ children, className }: { children: React.ReactNode; className?: string }) {
    return (
        <div className={clsx('grid grid-cols-1 gap-x-8 gap-y-16 lg:grid-cols-2', className)}>
            {children}
        </div>
    )
}

export function Book({
    title,
    description,
    image,
    href,
    author,
}: {
    title: string
    description: string
    image: string
    href: string
    author?: string
}) {
    return (
        <div className="group relative flex flex-col items-start">
            <div className="relative z-10 mb-4 w-full overflow-hidden rounded-xl bg-zinc-100 dark:bg-zinc-800">
                <img
                    src={image}
                    alt=""
                    className="aspect-[3/2] w-full object-cover object-center transition duration-500 group-hover:scale-105"
                />
            </div>
            <h3 className="mt-4 text-base font-semibold text-zinc-900 dark:text-white">
                <a href={href}>
                    <span className="absolute inset-0" />
                    {title}
                </a>
            </h3>
            <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">{description}</p>
            {author && (
                <p className="mt-4 text-xs font-medium text-zinc-900 dark:text-zinc-100">
                    By {author}
                </p>
            )}
        </div>
    )
}
