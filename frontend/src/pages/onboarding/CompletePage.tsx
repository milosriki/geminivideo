import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SparklesIcon, CheckCircleIcon, RocketLaunchIcon, ChartBarIcon, VideoCameraIcon } from '@heroicons/react/24/outline'
import { ProgressIndicator } from '@/components/onboarding/ProgressIndicator'
import { LiveChatWidget } from '@/components/onboarding/LiveChatWidget'

const ONBOARDING_STEPS = [
  { id: 'welcome', name: 'Welcome', description: 'Get started' },
  { id: 'meta', name: 'Meta', description: 'Connect account' },
  { id: 'google', name: 'Google', description: 'Connect ads' },
  { id: 'configure', name: 'Configure', description: 'Set preferences' },
  { id: 'campaign', name: 'Campaign', description: 'Create first ad' },
  { id: 'complete', name: 'Complete', description: 'You\'re ready!' },
]

const NEXT_STEPS = [
  {
    icon: VideoCameraIcon,
    title: 'Create Your First Video',
    description: 'Use AI to generate hundreds of video variations',
    link: '/create',
    color: 'from-violet-500 to-fuchsia-500',
  },
  {
    icon: ChartBarIcon,
    title: 'View Analytics',
    description: 'Track your campaigns and optimize for ROAS',
    link: '/analytics',
    color: 'from-blue-500 to-cyan-500',
  },
  {
    icon: RocketLaunchIcon,
    title: 'Launch Campaign',
    description: 'Set up and launch your first campaign',
    link: '/campaigns',
    color: 'from-emerald-500 to-teal-500',
  },
]

export default function CompletePage() {
  const navigate = useNavigate()

  useEffect(() => {
    // Mark onboarding as complete
    const completeOnboarding = async () => {
      try {
        const userId = 'demo-user-id'
        await fetch('/api/onboarding/step/complete', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ userId }),
        })
      } catch (error) {
        console.error('Error completing onboarding:', error)
      }
    }

    completeOnboarding()
  }, [])

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <LiveChatWidget />

      {/* Header */}
      <div className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-3">
              <SparklesIcon className="h-8 w-8 text-violet-500" />
              <span className="text-xl font-bold bg-gradient-to-r from-violet-500 to-fuchsia-500 bg-clip-text text-transparent">
                GeminiVideo
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <ProgressIndicator
          steps={ONBOARDING_STEPS}
          currentStep={6}
          completedSteps={new Set(['welcome', 'meta', 'google', 'configure', 'campaign', 'complete'])}
        />
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="text-center"
        >
          {/* Success Animation */}
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', duration: 0.8, delay: 0.2 }}
            className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-full mb-8 shadow-lg shadow-emerald-500/50"
          >
            <CheckCircleIcon className="h-14 w-14 text-white" />
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="text-5xl font-bold bg-gradient-to-r from-white via-emerald-200 to-white bg-clip-text text-transparent mb-6"
          >
            You're All Set!
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
            className="text-xl text-zinc-400 max-w-2xl mx-auto mb-12"
          >
            Welcome to the elite marketer's toolkit. You're ready to scale your ad campaigns
            to <span className="text-emerald-400 font-semibold">$100k+/day</span> with AI-powered video generation.
          </motion.p>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8 }}
            className="grid grid-cols-3 gap-6 mb-16"
          >
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="text-3xl font-bold text-violet-400 mb-2">2.5 min</div>
              <div className="text-sm text-zinc-500">Setup Time</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="text-3xl font-bold text-emerald-400 mb-2">100%</div>
              <div className="text-sm text-zinc-500">Ready to Scale</div>
            </div>
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
              <div className="text-3xl font-bold text-blue-400 mb-2">∞</div>
              <div className="text-sm text-zinc-500">Possibilities</div>
            </div>
          </motion.div>

          {/* Next Steps */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.0 }}
          >
            <h2 className="text-2xl font-bold mb-6">What's Next?</h2>
            <div className="grid md:grid-cols-3 gap-6 mb-12">
              {NEXT_STEPS.map((step, idx) => (
                <motion.button
                  key={step.title}
                  onClick={() => navigate(step.link)}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 1.2 + idx * 0.1 }}
                  className="group bg-zinc-900 border border-zinc-800 rounded-xl p-6 text-left hover:border-violet-500/50 transition-all duration-300"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <div className={`inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br ${step.color} rounded-lg mb-4`}>
                    <step.icon className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="font-semibold text-white mb-2 group-hover:text-violet-400 transition-colors">
                    {step.title}
                  </h3>
                  <p className="text-sm text-zinc-400">{step.description}</p>
                </motion.button>
              ))}
            </div>

            {/* Primary CTA */}
            <motion.button
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 1.5 }}
              onClick={() => navigate('/')}
              className="bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 text-white font-semibold px-12 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Go to Dashboard
              <span className="ml-2">→</span>
            </motion.button>
          </motion.div>

          {/* Support Section */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.8 }}
            className="mt-16 pt-8 border-t border-zinc-800"
          >
            <p className="text-sm text-zinc-500 mb-4">
              Need help getting started? Our team is here 24/7
            </p>
            <div className="flex items-center justify-center gap-6">
              <a href="#" className="text-sm text-violet-400 hover:text-violet-300 transition-colors">
                View Documentation
              </a>
              <span className="text-zinc-700">•</span>
              <a href="#" className="text-sm text-violet-400 hover:text-violet-300 transition-colors">
                Watch Tutorials
              </a>
              <span className="text-zinc-700">•</span>
              <a href="#" className="text-sm text-violet-400 hover:text-violet-300 transition-colors">
                Contact Support
              </a>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}
