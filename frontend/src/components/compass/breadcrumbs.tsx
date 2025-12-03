import { ChevronRightIcon } from '@heroicons/react/20/solid'
import { Link } from 'react-router-dom'

export function Breadcrumbs({
    pages,
}: {
    pages: Array<{ name: string; href: string; current: boolean }>
}) {
    return (
        <nav className="flex" aria-label="Breadcrumb">
            <ol role="list" className="flex items-center space-x-4">
                <li>
                    <div>
                        <Link to="/" className="text-zinc-400 hover:text-zinc-500">
                            <span className="sr-only">Home</span>
                            <svg className="h-5 w-5 flex-shrink-0" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                                <path
                                    fillRule="evenodd"
                                    d="M9.293 2.293a1 1 0 011.414 0l7 7A1 1 0 0117 11h-1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-3a1 1 0 00-1-1H9a1 1 0 00-1 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-6H3a1 1 0 01-.707-1.707l7-7z"
                                    clipRule="evenodd"
                                />
                            </svg>
                        </Link>
                    </div>
                </li>
                {pages.map((page) => (
                    <li key={page.name}>
                        <div className="flex items-center">
                            <ChevronRightIcon className="h-5 w-5 flex-shrink-0 text-zinc-400" aria-hidden="true" />
                            <Link
                                to={page.href}
                                className={`ml-4 text-sm font-medium ${page.current ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'
                                    }`}
                                aria-current={page.current ? 'page' : undefined}
                            >
                                {page.name}
                            </Link>
                        </div>
                    </li>
                ))}
            </ol>
        </nav>
    )
}
