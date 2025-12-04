import { useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '../components/radiant/button'
import { Container } from '../components/radiant/container'
import { Footer } from '../components/radiant/footer'
import { GradientBackground } from '../components/radiant/gradient'
import { Link } from '../components/radiant/link'
import { Navbar } from '../components/radiant/navbar'
import { Heading, Lead, Subheading } from '../components/radiant/text'
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react'
import {
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ChevronUpDownIcon,
  MagnifyingGlassIcon,
  RssIcon,
} from '@heroicons/react/16/solid'
import { clsx } from 'clsx'

// Types
interface Author {
  name: string
  image: string
}

interface BlogPost {
  slug: string
  title: string
  excerpt: string
  publishedAt: string
  author: Author
  mainImage: string
  categories: string[]
  featured?: boolean
}

interface Category {
  slug: string
  title: string
}

// Sample data
const sampleAuthors: Author[] = [
  {
    name: 'Sarah Chen',
    image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80',
  },
  {
    name: 'Marcus Rodriguez',
    image: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80',
  },
  {
    name: 'Emily Taylor',
    image: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?ixlib=rb-1.2.1&auto=format&fit=facearea&facepad=2&w=256&h=256&q=80',
  },
]

const samplePosts: BlogPost[] = [
  {
    slug: 'ai-powered-video-marketing-2024',
    title: 'AI-Powered Video Marketing: The Future is Here',
    excerpt:
      'Discover how artificial intelligence is revolutionizing video marketing strategies and helping brands create more engaging content at scale.',
    publishedAt: '2024-11-28',
    author: sampleAuthors[0],
    mainImage: 'https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=1200&q=80',
    categories: ['ai', 'video-marketing'],
    featured: true,
  },
  {
    slug: 'maximizing-ad-roi-video-campaigns',
    title: 'Maximizing ROI with Data-Driven Video Ad Campaigns',
    excerpt:
      'Learn proven strategies to optimize your video advertising budget and achieve better returns through smart analytics and targeting.',
    publishedAt: '2024-11-25',
    author: sampleAuthors[1],
    mainImage: 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=1200&q=80',
    categories: ['advertising', 'analytics'],
    featured: true,
  },
  {
    slug: 'generative-ai-video-production',
    title: 'Generative AI in Video Production: A Game Changer',
    excerpt:
      'Explore how generative AI tools are transforming video production workflows, reducing costs, and opening new creative possibilities.',
    publishedAt: '2024-11-22',
    author: sampleAuthors[2],
    mainImage: 'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=1200&q=80',
    categories: ['ai', 'production'],
    featured: true,
  },
  {
    slug: 'social-media-video-trends-2024',
    title: 'Top Social Media Video Trends to Watch in 2024',
    excerpt:
      'Stay ahead of the curve with insights into the latest video content trends dominating platforms like TikTok, Instagram, and YouTube.',
    publishedAt: '2024-11-18',
    author: sampleAuthors[0],
    mainImage: 'https://images.unsplash.com/photo-1611162617474-5b21e879e113?auto=format&fit=crop&w=1200&q=80',
    categories: ['video-marketing', 'social-media'],
  },
  {
    slug: 'video-analytics-metrics-matter',
    title: 'Video Analytics: Which Metrics Actually Matter?',
    excerpt:
      'Cut through the noise and focus on the video analytics metrics that truly impact your business goals and marketing success.',
    publishedAt: '2024-11-15',
    author: sampleAuthors[1],
    mainImage: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1200&q=80',
    categories: ['analytics', 'video-marketing'],
  },
  {
    slug: 'programmatic-video-advertising-guide',
    title: 'Complete Guide to Programmatic Video Advertising',
    excerpt:
      'Master programmatic video advertising with this comprehensive guide covering everything from DSPs to real-time bidding strategies.',
    publishedAt: '2024-11-12',
    author: sampleAuthors[2],
    mainImage: 'https://images.unsplash.com/photo-1557804506-669a67965ba0?auto=format&fit=crop&w=1200&q=80',
    categories: ['advertising', 'technology'],
  },
]

const categories: Category[] = [
  { slug: 'ai', title: 'Artificial Intelligence' },
  { slug: 'video-marketing', title: 'Video Marketing' },
  { slug: 'advertising', title: 'Advertising' },
  { slug: 'analytics', title: 'Analytics' },
  { slug: 'production', title: 'Production' },
  { slug: 'social-media', title: 'Social Media' },
  { slug: 'technology', title: 'Technology' },
]

const postsPerPage = 5

// Featured Posts Component
function FeaturedPosts() {
  const featuredPosts = samplePosts.filter((post) => post.featured)

  if (featuredPosts.length === 0) {
    return null
  }

  return (
    <div className="mt-16 bg-gradient-to-t from-zinc-900/50 pb-14">
      <Container>
        <h2 className="text-2xl font-medium tracking-tight text-zinc-100">Featured</h2>
        <div className="mt-6 grid grid-cols-1 gap-8 lg:grid-cols-3">
          {featuredPosts.map((post) => (
            <div
              key={post.slug}
              className="group relative flex flex-col rounded-3xl bg-zinc-900 p-2 shadow-md ring-1 shadow-black/5 ring-zinc-800/50 transition-all hover:ring-purple-500/50"
            >
              {post.mainImage && (
                <img
                  alt=""
                  src={post.mainImage}
                  className="aspect-[3/2] w-full rounded-2xl object-cover"
                />
              )}
              <div className="flex flex-1 flex-col p-8">
                <div className="text-sm/5 text-zinc-400">
                  {new Date(post.publishedAt).toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </div>
                <div className="mt-2 text-base/7 font-medium text-zinc-100">
                  <Link href={`/blog/${post.slug}`}>
                    <span className="absolute inset-0" />
                    {post.title}
                  </Link>
                </div>
                <div className="mt-2 flex-1 text-sm/6 text-zinc-400">
                  {post.excerpt}
                </div>
                {post.author && (
                  <div className="mt-6 flex items-center gap-3">
                    {post.author.image && (
                      <img
                        alt=""
                        src={post.author.image}
                        className="aspect-square size-6 rounded-full object-cover ring-1 ring-zinc-700"
                      />
                    )}
                    <div className="text-sm/5 text-zinc-300">{post.author.name}</div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </Container>
    </div>
  )
}

// Categories Component
function Categories({
  selected,
  onCategoryChange,
}: {
  selected?: string
  onCategoryChange: (category: string | undefined) => void
}) {
  if (categories.length === 0) {
    return null
  }

  return (
    <div className="flex flex-wrap items-center justify-between gap-2">
      <Menu>
        <MenuButton className="flex items-center justify-between gap-2 font-medium text-zinc-100 hover:text-purple-400 transition-colors">
          {categories.find(({ slug }) => slug === selected)?.title || 'All categories'}
          <ChevronUpDownIcon className="size-4 fill-zinc-400" />
        </MenuButton>
        <MenuItems
          anchor="bottom start"
          className="min-w-40 rounded-lg bg-zinc-900 p-1 shadow-lg ring-1 ring-zinc-800 [--anchor-gap:6px] [--anchor-offset:-4px] [--anchor-padding:10px]"
        >
          <MenuItem>
            <button
              onClick={() => onCategoryChange(undefined)}
              data-selected={selected === undefined ? true : undefined}
              className="group grid w-full grid-cols-[1rem_1fr] items-center gap-2 rounded-md px-2 py-1 text-left text-zinc-100 data-focus:bg-zinc-800"
            >
              <CheckIcon className="hidden size-4 group-data-selected:block text-purple-400" />
              <p className="col-start-2 text-sm/6">All categories</p>
            </button>
          </MenuItem>
          {categories.map((category) => (
            <MenuItem key={category.slug}>
              <button
                onClick={() => onCategoryChange(category.slug)}
                data-selected={category.slug === selected ? true : undefined}
                className="group grid w-full grid-cols-[16px_1fr] items-center gap-2 rounded-md px-2 py-1 text-left text-zinc-100 data-focus:bg-zinc-800"
              >
                <CheckIcon className="hidden size-4 group-data-selected:block text-purple-400" />
                <p className="col-start-2 text-sm/6">{category.title}</p>
              </button>
            </MenuItem>
          ))}
        </MenuItems>
      </Menu>
      <Button variant="outline" href="/blog/feed.xml" className="gap-1 bg-zinc-900 text-zinc-100 ring-zinc-800 hover:bg-zinc-800">
        <RssIcon className="size-4" />
        RSS Feed
      </Button>
    </div>
  )
}

// Search Component
function SearchBar({
  searchQuery,
  onSearchChange,
}: {
  searchQuery: string
  onSearchChange: (query: string) => void
}) {
  return (
    <div className="relative mt-6">
      <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
        <MagnifyingGlassIcon className="h-5 w-5 text-zinc-500" />
      </div>
      <input
        type="text"
        placeholder="Search articles..."
        value={searchQuery}
        onChange={(e) => onSearchChange(e.target.value)}
        className="block w-full rounded-lg border-0 bg-zinc-900 py-2 pl-10 pr-3 text-zinc-100 placeholder:text-zinc-500 ring-1 ring-zinc-800 focus:ring-2 focus:ring-purple-500 sm:text-sm sm:leading-6"
      />
    </div>
  )
}

// Posts Component
function Posts({
  posts,
  page,
}: {
  posts: BlogPost[]
  page: number
}) {
  if (posts.length === 0) {
    return (
      <p className="mt-6 text-center text-lg text-zinc-500">
        No posts found. Try adjusting your search or filters.
      </p>
    )
  }

  return (
    <div className="mt-6">
      {posts.map((post) => (
        <div
          key={post.slug}
          className="group relative grid grid-cols-1 border-b border-b-zinc-800 py-10 first:border-t first:border-t-zinc-800 max-sm:gap-3 sm:grid-cols-3 transition-colors hover:border-purple-500/30"
        >
          <div>
            <div className="text-sm/5 max-sm:text-zinc-400 sm:font-medium text-zinc-300">
              {new Date(post.publishedAt).toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </div>
            {post.author && (
              <div className="mt-2.5 flex items-center gap-3">
                {post.author.image && (
                  <img
                    alt=""
                    src={post.author.image}
                    className="aspect-square size-6 rounded-full object-cover ring-1 ring-zinc-700"
                  />
                )}
                <div className="text-sm/5 text-zinc-400">{post.author.name}</div>
              </div>
            )}
          </div>
          <div className="sm:col-span-2 sm:max-w-2xl">
            <h2 className="text-sm/5 font-medium text-zinc-100 group-hover:text-purple-400 transition-colors">
              {post.title}
            </h2>
            <p className="mt-3 text-sm/6 text-zinc-400">{post.excerpt}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {post.categories.map((catSlug) => {
                const category = categories.find((c) => c.slug === catSlug)
                return category ? (
                  <span
                    key={catSlug}
                    className="rounded-full border border-dotted border-zinc-700 bg-zinc-900/50 px-2 text-xs/6 font-medium text-zinc-500"
                  >
                    {category.title}
                  </span>
                ) : null
              })}
            </div>
            <div className="mt-4">
              <Link
                href={`/blog/${post.slug}`}
                className="flex items-center gap-1 text-sm/5 font-medium text-zinc-100 hover:text-purple-400 transition-colors"
              >
                <span className="absolute inset-0" />
                Read more
                <ChevronRightIcon className="size-4 fill-zinc-400 group-hover:fill-purple-400" />
              </Link>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// Pagination Component
function Pagination({
  page,
  totalPages,
  onPageChange,
}: {
  page: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  if (totalPages < 2) {
    return null
  }

  const hasPreviousPage = page > 1
  const hasNextPage = page < totalPages

  return (
    <div className="mt-6 flex items-center justify-between gap-2">
      <Button
        variant="outline"
        onClick={() => hasPreviousPage && onPageChange(page - 1)}
        disabled={!hasPreviousPage}
        className="bg-zinc-900 text-zinc-100 ring-zinc-800 hover:bg-zinc-800 disabled:opacity-40"
      >
        <ChevronLeftIcon className="size-4" />
        Previous
      </Button>
      <div className="flex gap-2 max-sm:hidden">
        {Array.from({ length: totalPages }, (_, i) => (
          <button
            key={i + 1}
            onClick={() => onPageChange(i + 1)}
            data-active={i + 1 === page ? true : undefined}
            className={clsx(
              'size-7 rounded-lg text-center text-sm/7 font-medium transition-colors',
              'hover:bg-zinc-800',
              'data-active:bg-purple-600 data-active:text-white data-active:shadow-sm',
              'data-active:hover:bg-purple-500',
              i + 1 === page ? 'text-white' : 'text-zinc-300'
            )}
          >
            {i + 1}
          </button>
        ))}
      </div>
      <Button
        variant="outline"
        onClick={() => hasNextPage && onPageChange(page + 1)}
        disabled={!hasNextPage}
        className="bg-zinc-900 text-zinc-100 ring-zinc-800 hover:bg-zinc-800 disabled:opacity-40"
      >
        Next
        <ChevronRightIcon className="size-4" />
      </Button>
    </div>
  )
}

// Main Blog Page Component
export default function BlogPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()

  const pageParam = searchParams.get('page')
  const categoryParam = searchParams.get('category')

  const [page, setPage] = useState(pageParam ? parseInt(pageParam) : 1)
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(
    categoryParam || undefined
  )
  const [searchQuery, setSearchQuery] = useState('')

  // Filter and search posts
  const filteredPosts = useMemo(() => {
    return samplePosts.filter((post) => {
      // Category filter
      if (selectedCategory && !post.categories.includes(selectedCategory)) {
        return false
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          post.title.toLowerCase().includes(query) ||
          post.excerpt.toLowerCase().includes(query) ||
          post.categories.some((cat) =>
            categories.find((c) => c.slug === cat)?.title.toLowerCase().includes(query)
          )
        )
      }

      return true
    })
  }, [selectedCategory, searchQuery])

  // Paginate posts
  const paginatedPosts = useMemo(() => {
    const startIndex = (page - 1) * postsPerPage
    return filteredPosts.slice(startIndex, startIndex + postsPerPage)
  }, [filteredPosts, page])

  const totalPages = Math.ceil(filteredPosts.length / postsPerPage)

  // Update URL when category changes
  const handleCategoryChange = (category: string | undefined) => {
    setSelectedCategory(category)
    setPage(1)
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    setSearchParams(params)
  }

  // Update URL when page changes
  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    const params = new URLSearchParams()
    if (selectedCategory) params.set('category', selectedCategory)
    if (newPage > 1) params.set('page', newPage.toString())
    setSearchParams(params)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const showFeaturedPosts = page === 1 && !selectedCategory && !searchQuery

  return (
    <main className="overflow-hidden bg-zinc-950">
      <GradientBackground />
      <Container>
        <Navbar />
        <Subheading className="mt-16 text-purple-400">Blog</Subheading>
        <Heading as="h1" className="mt-2" dark>
          Insights on video marketing and AI.
        </Heading>
        <Lead className="mt-6 max-w-3xl text-zinc-400">
          Stay informed with the latest trends, strategies, and insights on video marketing,
          AI-powered advertising, and data-driven content creation.
        </Lead>
      </Container>
      {showFeaturedPosts && <FeaturedPosts />}
      <Container className="mt-16 pb-24">
        <Categories selected={selectedCategory} onCategoryChange={handleCategoryChange} />
        <SearchBar searchQuery={searchQuery} onSearchChange={setSearchQuery} />
        <Posts posts={paginatedPosts} page={page} />
        {!searchQuery && <Pagination page={page} totalPages={totalPages} onPageChange={handlePageChange} />}
        {searchQuery && filteredPosts.length > postsPerPage && (
          <p className="mt-6 text-center text-sm text-zinc-500">
            Showing {filteredPosts.length} results. Clear search to see pagination.
          </p>
        )}
      </Container>
      <Footer />
    </main>
  )
}
