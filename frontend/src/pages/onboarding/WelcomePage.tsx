import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SparklesIcon, RocketLaunchIcon, ChartBarIcon, BoltIcon } from '@heroicons/react/24/outline'
import { ProgressIndicator } from '@/components/onboarding/ProgressIndicator'
import { VideoTutorial } from '@/components/onboarding/VideoTutorial'
import { LiveChatWidget } from '@/components/onboarding/LiveChatWidget'

const ONBOARDING_STEPS = [
  { id: 'welcome', name: 'Welcome', description: 'Get started' },
  { id: 'meta', name: 'Meta', description: 'Connect account' },
  { id: 'google', name: 'Google', description: 'Connect ads' },
  { id: 'configure', name: 'Configure', description: 'Set preferences' },
  { id: 'campaign', name: 'Campaign', description: 'Create first ad' },
  { id: 'complete', name: 'Complete', description: 'You\'re ready!' },
]

const FEATURES = [
  {
    icon: SparklesIcon,
    title: 'AI-Powered Creative Generation',
    description: 'Generate thousands of video ads in minutes with our AI engine',
  },
  {
    icon: ChartBarIcon,
    title: 'Real-Time Performance Analytics',
    description: 'Track ROAS, conversions, and optimize campaigns on the fly',
  },
  {
    icon: BoltIcon,
    title: 'Automated A/B Testing',
    description: 'Let AI test variations and find winning combinations automatically',
  },
  {
    icon: RocketLaunchIcon,
    title: 'Scale to $100k+/day',
    description: 'Infrastructure built for elite marketers spending serious budgets',
  },
]

export default function WelcomePage() {
  const navigate = useNavigate()

  const handleContinue = async () => {
    // Initialize onboarding session
    try {
      const userId = 'demo-user-id' // TODO: Get from auth context
      await fetch('/api/onboarding/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId }),
      })

      // Mark welcome step as complete
      await fetch('/api/onboarding/step/welcome', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId }),
      })

      navigate('/onboarding/connect-meta')
    } catch (error) {
      console.error('Error starting onboarding:', error)
      // Continue anyway for demo
      navigate('/onboarding/connect-meta')
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <LiveChatWidget />

      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <SparklesIcon className="h-8 w-8 text-violet-500" />
              <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-fuchsia-500 bg-clip-text text-transparent">
                GeminiVideo
              </span>
            </div>
            <div className="text-sm text-zinc-400">
              Elite Marketer Onboarding
            </div>
          </div>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <ProgressIndicator
          steps={ONBOARDING_STEPS}
          currentStep={1}
          completedSteps={new Set()}
        />
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white via-violet-200 to-white bg-clip-text text-transparent mb-6">
            Welcome to the Future of Ad Creation
          </h1>
          <p className="text-xl text-zinc-400 max-w-3xl mx-auto mb-12">
            You're joining an elite group of marketers spending <span className="text-violet-400 font-semibold">$20k+/day</span> on ads.
            Let's get you set up to scale faster than ever before.
          </p>

          {/* Features Grid */}
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            {FEATURES.map((feature, idx) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: idx * 0.1 }}
                className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-left hover:border-violet-500/50 transition-all duration-300"
              >
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 bg-violet-500/10 rounded-lg p-3">
                    <feature.icon className="h-6 w-6 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white mb-2">{feature.title}</h3>
                    <p className="text-sm text-zinc-400">{feature.description}</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Video Tutorial */}
          <div className="mb-12">
            <h3 className="text-lg font-semibold mb-4">Quick Start Video</h3>
            <div className="max-w-2xl mx-auto">
              <VideoTutorial
                title="Getting Started with GeminiVideo"
                description="Watch this 3-minute overview to learn how elite marketers are scaling with our platform"
                videoUrl="https://www.youtube.com/watch?v=demo"
                duration="3:24"
              />
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="flex items-center justify-center gap-4">
            <motion.button
              onClick={handleContinue}
              className="bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white font-semibold px-8 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Continue to Setup
              <span className="ml-2">→</span>
            </motion.button>

            <motion.button
              onClick={() => navigate('/onboarding/connect-meta')}
              className="bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 font-medium px-8 py-4 rounded-xl transition-all duration-300"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              Skip intro
            </motion.button>
          </div>

          {/* Trust Indicators */}
          <div className="mt-16 pt-8 border-t border-zinc-800">
            <p className="text-sm text-zinc-500 mb-6">Trusted by elite marketers at:</p>
            <div className="flex items-center justify-center gap-12 opacity-50">
              {['Company A', 'Company B', 'Company C', 'Company D'].map((company) => (
                <div key={company} className="text-zinc-600 font-semibold">
                  {company}
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
