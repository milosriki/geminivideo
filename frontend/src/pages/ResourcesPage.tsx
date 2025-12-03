import { Book, Bookshelf } from '@/components/compass/bookshelf'
import { PageSection } from '@/components/compass/page-section'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'

export default function ResourcesPage() {
    return (
        <div className="p-6 lg:p-8 max-w-7xl mx-auto">
            <div className="mb-12">
                <Heading level={1} className="text-white">Resources & Tutorials</Heading>
                <Text className="text-zinc-400 mt-1">
                    Learn how to get the most out of GeminiVideo with our curated guides.
                </Text>
            </div>

            <PageSection title="Getting Started" description="Essential guides for new users.">
                <Bookshelf>
                    <Book
                        title="Campaign Basics"
                        description="Learn how to set up your first video ad campaign in 3 easy steps."
                        image="https://images.unsplash.com/photo-1460925895917-afdab827c52f?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                        href="#"
                        author="Gemini Team"
                    />
                    <Book
                        title="Understanding AI Credits"
                        description="How our credit system works and how to optimize your usage."
                        image="https://images.unsplash.com/photo-1554224155-6726b3ff858f?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                        href="#"
                        author="Billing Dept"
                    />
                </Bookshelf>
            </PageSection>

            <PageSection title="Advanced Techniques" description="Take your video marketing to the next level.">
                <Bookshelf>
                    <Book
                        title="Viral Hooks Masterclass"
                        description="The science behind stopping the scroll on TikTok and Reels."
                        image="https://images.unsplash.com/photo-1611162617474-5b21e879e113?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                        href="#"
                        author="Marketing Pro"
                    />
                    <Book
                        title="A/B Testing Strategies"
                        description="How to scientifically test creatives to find winners."
                        image="https://images.unsplash.com/photo-1551288049-bebda4e38f71?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                        href="#"
                        author="Data Science Team"
                    />
                    <Book
                        title="Studio Pro Tips"
                        description="Hidden features in the Video Studio you might not know about."
                        image="https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
                        href="#"
                        author="Product Team"
                    />
                </Bookshelf>
            </PageSection>
        </div>
    )
}
