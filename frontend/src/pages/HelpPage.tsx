import { TableOfContents } from '@/components/compass/table-of-contents'
import { Heading } from '@/components/catalyst/heading'
import { Text } from '@/components/catalyst/text'
import { Faqs } from '@/components/salient/faqs'

const helpFaqs = [
    {
        question: 'How do I reset my password?',
        answer: 'Go to Settings > Security and click on "Reset Password". You will receive an email with instructions.',
    },
    {
        question: 'Can I export videos in 4K?',
        answer: 'Yes, 4K export is available on the Pro and Enterprise plans.',
    },
    {
        question: 'Where can I find my invoices?',
        answer: 'Invoices are available in the Settings > Billing section.',
    },
]

export function HelpPage() {
    return (
        <div className="p-6 lg:p-8 max-w-7xl mx-auto flex gap-12">
            {/* Main Content */}
            <div className="flex-1 min-w-0" id="help-content">
                <Heading level={1} className="text-white mb-8">Help & Documentation</Heading>

                <section id="getting-started" className="mb-12">
                    <h2 id="getting-started" className="text-2xl font-bold text-white mb-4">Getting Started</h2>
                    <Text className="text-zinc-400 mb-4">
                        Welcome to GeminiVideo! This guide will help you get up and running with your first video campaign.
                        Our platform leverages advanced AI to generate high-converting video ads in minutes.
                    </Text>
                    <h3 id="account-setup" className="text-xl font-semibold text-white mb-2 mt-6">Account Setup</h3>
                    <Text className="text-zinc-400">
                        Before you begin, ensure your profile is complete in the Settings page. Connect your ad platforms
                        (Meta, TikTok, YouTube) to enable direct publishing.
                    </Text>
                </section>

                <section id="creating-campaigns" className="mb-12">
                    <h2 id="creating-campaigns" className="text-2xl font-bold text-white mb-4">Creating Campaigns</h2>
                    <Text className="text-zinc-400 mb-4">
                        The Campaign Wizard is your central hub for creating new video ads. It guides you through a simple 3-step process.
                    </Text>
                    <h3 id="step-1-setup" className="text-xl font-semibold text-white mb-2 mt-6">Step 1: Setup</h3>
                    <Text className="text-zinc-400">
                        Define your campaign objective, budget, and target audience. This information helps our AI tailor the content.
                    </Text>
                    <h3 id="step-2-creative" className="text-xl font-semibold text-white mb-2 mt-6">Step 2: Creative</h3>
                    <Text className="text-zinc-400">
                        Upload your source assets or choose from our stock library. Select your preferred style (UGC, Professional) and let the AI generate scripts.
                    </Text>
                </section>

                <section id="video-studio" className="mb-12">
                    <h2 id="video-studio" className="text-2xl font-bold text-white mb-4">Video Studio</h2>
                    <Text className="text-zinc-400 mb-4">
                        For more granular control, use the Video Studio to edit your generated videos.
                    </Text>
                    <h3 id="timeline-editing" className="text-xl font-semibold text-white mb-2 mt-6">Timeline Editing</h3>
                    <Text className="text-zinc-400">
                        Trim clips, add transitions, and adjust timing using the intuitive timeline editor.
                    </Text>
                </section>

                <section id="faq" className="mb-12">
                    <Heading level={2} className="text-white mb-4">Frequently Asked Questions</Heading>
                    <Faqs faqs={helpFaqs} />
                </section>
            </div>

            {/* Table of Contents Sidebar */}
            <div className="hidden xl:block w-64 shrink-0">
                <TableOfContents contentId="help-content" />
            </div>
        </div>
    )
}

export default HelpPage
