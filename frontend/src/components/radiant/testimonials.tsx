'use client'

import { clsx } from 'clsx'
import { Container } from './container'

export function Testimonials({
    children,
    className,
}: {
    children: React.ReactNode
    className?: string
}) {
    return (
        <div className={clsx('py-24 sm:py-32', className)}>
            <Container>
                <div className="mx-auto max-w-2xl lg:max-w-none">
                    <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
                        {children}
                    </div>
                </div>
            </Container>
        </div>
    )
}

export function Testimonial({
    author,
    children,
    className,
}: {
    author: { name: string; role: string; image?: string }
    children: React.ReactNode
    className?: string
}) {
    return (
        <figure className={clsx('rounded-2xl bg-white p-6 shadow-lg ring-1 ring-gray-900/5', className)}>
            <blockquote className="text-gray-900">
                <p>{`“${children}”`}</p>
            </blockquote>
            <figcaption className="mt-6 flex items-center gap-x-4">
                {author.image && (
                    <img
                        className="h-10 w-10 rounded-full bg-gray-50"
                        src={author.image}
                        alt=""
                    />
                )}
                <div>
                    <div className="font-semibold">{author.name}</div>
                    <div className="text-gray-600">{author.role}</div>
                </div>
            </figcaption>
        </figure>
    )
}
