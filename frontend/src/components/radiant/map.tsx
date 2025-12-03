'use client'

import { clsx } from 'clsx'

export function Map({ className }: { className?: string }) {
    return (
        <div className={clsx('relative flex h-[500px] w-full items-center justify-center overflow-hidden rounded-3xl bg-slate-900', className)}>
            <div className="absolute inset-0 opacity-20">
                <svg className="h-full w-full text-white" fill="currentColor" viewBox="0 0 100 50" preserveAspectRatio="none">
                    {/* Simplified World Map Path Placeholder */}
                    <path d="M20,10 Q30,5 40,10 T60,10 T80,10 T90,20 T80,30 T60,30 T40,30 T20,30 T10,20 T20,10" />
                    <text x="50" y="25" textAnchor="middle" fill="currentColor" fontSize="5">World Map Visualization</text>
                </svg>
            </div>

            {/* Interactive Dots */}
            <div className="absolute top-1/3 left-1/4 h-3 w-3 rounded-full bg-blue-500 ring-4 ring-blue-500/30 animate-pulse" />
            <div className="absolute top-1/2 left-1/2 h-3 w-3 rounded-full bg-purple-500 ring-4 ring-purple-500/30 animate-pulse delay-75" />
            <div className="absolute top-1/3 right-1/4 h-3 w-3 rounded-full bg-emerald-500 ring-4 ring-emerald-500/30 animate-pulse delay-150" />

            <div className="relative z-10 text-center">
                <h3 className="text-2xl font-bold text-white">Global Reach</h3>
                <p className="mt-2 text-slate-400">Active in 3 regions</p>
            </div>
        </div>
    )
}
