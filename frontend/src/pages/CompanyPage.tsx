import { Container } from '../components/radiant/container'
import { Footer } from '../components/radiant/footer'
import { GradientBackground } from '../components/radiant/gradient'
import { Navbar } from '../components/radiant/navbar'
import { Heading, Lead, Subheading } from '../components/radiant/text'
import { Button } from '../components/radiant/button'
import { AnimatedNumber } from '../components/radiant/animated-number'
import { CheckIcon, SparklesIcon, RocketLaunchIcon, UserGroupIcon, LightBulbIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'

interface PersonProps {
  name: string
  description: string
  img: string
}

function Person({ name, description, img }: PersonProps) {
  return (
    <li className="flex items-center gap-4">
      <img alt="" src={img} className="size-12 rounded-full ring-2 ring-purple-500/20" />
      <div className="text-sm/6">
        <h3 className="font-medium text-white">{name}</h3>
        <p className="text-zinc-400">{description}</p>
      </div>
    </li>
  )
}

interface ValueCardProps {
  icon: React.ElementType
  title: string
  description: string
}

function ValueCard({ icon: Icon, title, description }: ValueCardProps) {
  return (
    <div className="relative rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-sm transition-all hover:bg-white/10 hover:border-purple-500/30">
      <div className="mb-4 inline-flex rounded-lg bg-purple-500/10 p-3 ring-1 ring-purple-500/20">
        <Icon className="h-6 w-6 text-purple-400" />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-sm/6 text-zinc-400">{description}</p>
    </div>
  )
}

interface MilestoneProps {
  year: string
  title: string
  description: string
}

function Milestone({ year, title, description }: MilestoneProps) {
  return (
    <div className="relative pl-8 pb-12 last:pb-0 border-l border-purple-500/30">
      <div className="absolute left-0 -translate-x-1/2 w-3 h-3 rounded-full bg-purple-500 ring-4 ring-zinc-900" />
      <div className="space-y-2">
        <div className="text-sm font-mono font-semibold text-purple-400">{year}</div>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="text-sm/6 text-zinc-400">{description}</p>
      </div>
    </div>
  )
}

function Header() {
  return (
    <Container className="mt-16">
      <Heading as="h1" dark>
        Building the future of AI-powered video creation.
      </Heading>
      <Lead className="mt-6 max-w-3xl text-zinc-300">
        We're on a mission to democratize professional video production by harnessing the power of cutting-edge AI technology and making it accessible to everyone.
      </Lead>
      <section className="mt-16 grid grid-cols-1 lg:grid-cols-2 lg:gap-12">
        <div className="max-w-lg">
          <h2 className="text-2xl font-medium tracking-tight text-white">Our mission</h2>
          <p className="mt-6 text-sm/6 text-zinc-400">
            At GeminiVideo, we are dedicated to transforming the way creators produce video content. Our mission is to provide our customers with powerful AI tools that turn ideas into stunning videos in seconds, not hours.
          </p>
          <p className="mt-8 text-sm/6 text-zinc-400">
            We believe that everyone should have access to professional-grade video production tools. By combining Google's Gemini AI with advanced video processing, we're breaking down the barriers that have traditionally kept high-quality video creation out of reach for most people.
          </p>
          <p className="mt-8 text-sm/6 text-zinc-400">
            Our platform is built on the principles of innovation, accessibility, and quality. We're constantly pushing the boundaries of what's possible with AI-generated video while keeping our tools intuitive and easy to use.
          </p>
        </div>
        <div className="pt-20 lg:row-span-2 lg:-mr-16 xl:mr-auto">
          <div className="-mx-8 grid grid-cols-2 gap-4 sm:-mx-16 sm:grid-cols-4 lg:mx-0 lg:grid-cols-2 lg:gap-4 xl:gap-8">
            <div className="aspect-square overflow-hidden rounded-xl shadow-xl outline-1 -outline-offset-1 outline-white/10 bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center">
              <SparklesIcon className="w-20 h-20 text-white/80" />
            </div>
            <div className="-mt-8 aspect-square overflow-hidden rounded-xl shadow-xl outline-1 -outline-offset-1 outline-white/10 bg-gradient-to-br from-blue-600 to-cyan-600 flex items-center justify-center lg:-mt-32">
              <RocketLaunchIcon className="w-20 h-20 text-white/80" />
            </div>
            <div className="aspect-square overflow-hidden rounded-xl shadow-xl outline-1 -outline-offset-1 outline-white/10 bg-gradient-to-br from-cyan-600 to-teal-600 flex items-center justify-center">
              <LightBulbIcon className="w-20 h-20 text-white/80" />
            </div>
            <div className="-mt-8 aspect-square overflow-hidden rounded-xl shadow-xl outline-1 -outline-offset-1 outline-white/10 bg-gradient-to-br from-teal-600 to-purple-600 flex items-center justify-center lg:-mt-32">
              <ShieldCheckIcon className="w-20 h-20 text-white/80" />
            </div>
          </div>
        </div>
        <div className="max-lg:mt-16 lg:col-span-1">
          <Subheading dark>The Numbers</Subheading>
          <hr className="mt-6 border-t border-white/10" />
          <dl className="mt-6 grid grid-cols-1 gap-x-8 gap-y-4 sm:grid-cols-2">
            <div className="flex flex-col gap-y-2 border-b border-dotted border-white/10 pb-4">
              <dt className="text-sm/6 text-zinc-400">Videos Generated</dt>
              <dd className="order-first text-6xl font-medium tracking-tight text-white">
                <AnimatedNumber value={250} />K
              </dd>
            </div>
            <div className="flex flex-col gap-y-2 border-b border-dotted border-white/10 pb-4">
              <dt className="text-sm/6 text-zinc-400">Active Users</dt>
              <dd className="order-first text-6xl font-medium tracking-tight text-white">
                <AnimatedNumber value={50} />K+
              </dd>
            </div>
            <div className="flex flex-col gap-y-2 max-sm:border-b max-sm:border-dotted max-sm:border-white/10 max-sm:pb-4">
              <dt className="text-sm/6 text-zinc-400">Hours Saved</dt>
              <dd className="order-first text-6xl font-medium tracking-tight text-white">
                <AnimatedNumber value={1.2} decimals={1} />M
              </dd>
            </div>
            <div className="flex flex-col gap-y-2">
              <dt className="text-sm/6 text-zinc-400">AI Models Trained</dt>
              <dd className="order-first text-6xl font-medium tracking-tight text-white">
                <AnimatedNumber value={15} />+
              </dd>
            </div>
          </dl>
        </div>
      </section>
    </Container>
  )
}

function Values() {
  return (
    <Container className="mt-32">
      <Subheading dark>Our Values</Subheading>
      <Heading as="h3" className="mt-2" dark>
        What drives us forward.
      </Heading>
      <Lead className="mt-6 max-w-3xl text-zinc-300">
        Our core values guide every decision we make and every feature we build.
      </Lead>
      <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
        <ValueCard
          icon={SparklesIcon}
          title="Innovation First"
          description="We're constantly exploring new AI capabilities and pushing the boundaries of what's possible in video generation."
        />
        <ValueCard
          icon={UserGroupIcon}
          title="User-Centric Design"
          description="Every feature is designed with our users in mind, ensuring an intuitive and powerful experience for creators of all skill levels."
        />
        <ValueCard
          icon={LightBulbIcon}
          title="Creative Freedom"
          description="We believe in empowering creators with tools that enhance their vision rather than constraining it."
        />
        <ValueCard
          icon={ShieldCheckIcon}
          title="Trust & Transparency"
          description="We're committed to ethical AI practices and transparent communication about how our technology works."
        />
        <ValueCard
          icon={RocketLaunchIcon}
          title="Speed & Quality"
          description="We never compromise on quality, even as we deliver lightning-fast video generation capabilities."
        />
        <ValueCard
          icon={CheckIcon}
          title="Continuous Improvement"
          description="We iterate quickly, learn from our users, and constantly refine our platform to serve you better."
        />
      </div>
    </Container>
  )
}

function Team() {
  return (
    <Container className="mt-32">
      <Subheading dark>Meet the team</Subheading>
      <Heading as="h3" className="mt-2" dark>
        Built by passionate creators and engineers.
      </Heading>
      <Lead className="mt-6 max-w-3xl text-zinc-300">
        Our team combines deep expertise in AI, video production, and software engineering to create the best video generation platform.
      </Lead>
      <div className="mt-12 grid grid-cols-1 gap-12 lg:grid-cols-2">
        <div className="max-w-lg">
          <p className="text-sm/6 text-zinc-400">
            Founded by a team of AI researchers and video production experts, GeminiVideo emerged from a simple observation: creating professional video content was too time-consuming and expensive for most creators.
          </p>
          <p className="mt-8 text-sm/6 text-zinc-400">
            We started with a vision to leverage the latest advances in generative AI to make video creation as simple as writing a prompt. Today, our platform serves thousands of creators worldwide, from individual content creators to marketing teams at Fortune 500 companies.
          </p>
          <div className="mt-6">
            <Button className="w-full sm:w-auto" href="/contact">
              Join our team
            </Button>
          </div>
        </div>
        <div className="max-lg:order-first max-lg:max-w-lg">
          <div className="aspect-3/2 overflow-hidden rounded-xl shadow-xl outline-1 -outline-offset-1 outline-white/10 bg-gradient-to-br from-purple-600 via-blue-600 to-cyan-600 flex items-center justify-center">
            <UserGroupIcon className="w-40 h-40 text-white/40" />
          </div>
        </div>
      </div>
      <Subheading as="h3" className="mt-24" dark>
        Leadership Team
      </Subheading>
      <hr className="mt-6 border-t border-white/10" />
      <ul
        role="list"
        className="mx-auto mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3"
      >
        <Person
          name="Alex Chen"
          description="Co-Founder & CEO"
          img="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop"
        />
        <Person
          name="Sarah Mitchell"
          description="Co-Founder & CTO"
          img="https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop"
        />
        <Person
          name="Marcus Johnson"
          description="Head of AI Research"
          img="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop"
        />
        <Person
          name="Emily Rodriguez"
          description="VP of Product"
          img="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop"
        />
        <Person
          name="David Kim"
          description="Head of Engineering"
          img="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop"
        />
        <Person
          name="Lisa Thompson"
          description="VP of Design"
          img="https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=100&h=100&fit=crop"
        />
      </ul>
    </Container>
  )
}

function Timeline() {
  return (
    <Container className="mt-32">
      <Subheading dark>Our Journey</Subheading>
      <Heading as="h3" className="mt-2" dark>
        Milestones that shaped us.
      </Heading>
      <Lead className="mt-6 max-w-3xl text-zinc-300">
        From a small research project to a platform serving thousands of creators worldwide.
      </Lead>
      <div className="mt-16 max-w-3xl">
        <Milestone
          year="2023"
          title="The Beginning"
          description="GeminiVideo was founded with a vision to democratize video creation through AI. Our first prototype could generate simple animations from text prompts."
        />
        <Milestone
          year="Early 2024"
          title="Gemini Integration"
          description="We became one of the first platforms to integrate Google's Gemini AI, unlocking unprecedented capabilities in understanding complex video requirements."
        />
        <Milestone
          year="Mid 2024"
          title="Beta Launch"
          description="Launched our private beta with 100 hand-picked creators. The response was overwhelming, with users reporting 80% time savings in their video production workflow."
        />
        <Milestone
          year="Late 2024"
          title="Public Launch & Gemini 2.0"
          description="Opened to the public and upgraded to Gemini 2.0 Flash Experimental, bringing real-time video generation and advanced editing capabilities to all users."
        />
        <Milestone
          year="2025"
          title="Enterprise Solutions"
          description="Launched enterprise tier with custom model training, brand safety controls, and dedicated support for teams and businesses."
        />
      </div>
    </Container>
  )
}

function CTA() {
  return (
    <Container className="mt-32 mb-32">
      <div className="relative rounded-3xl border border-white/10 bg-gradient-to-br from-purple-600/20 via-blue-600/20 to-cyan-600/20 p-12 backdrop-blur-sm">
        <div className="relative z-10 mx-auto max-w-2xl text-center">
          <Heading as="h2" dark className="text-3xl sm:text-5xl">
            Ready to transform your video creation?
          </Heading>
          <Lead className="mt-6 text-zinc-300">
            Join thousands of creators who are already using GeminiVideo to bring their ideas to life.
          </Lead>
          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Button href="/signup" className="sm:w-auto">
              Get started for free
            </Button>
            <Button href="/contact" variant="outline" className="sm:w-auto bg-white/10 text-white hover:bg-white/20 border-white/20">
              Contact sales
            </Button>
          </div>
          <p className="mt-6 text-sm text-zinc-400">
            No credit card required. Start creating in seconds.
          </p>
        </div>
      </div>
    </Container>
  )
}

export default function CompanyPage() {
  return (
    <main className="overflow-hidden bg-zinc-950">
      <GradientBackground />
      <Container>
        <Navbar />
      </Container>
      <Header />
      <Values />
      <Team />
      <Timeline />
      <CTA />
      <Footer />
    </main>
  )
}
