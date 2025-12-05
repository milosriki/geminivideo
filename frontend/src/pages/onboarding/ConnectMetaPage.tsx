import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SparklesIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'
import { ProgressIndicator } from '@/components/onboarding/ProgressIndicator'
import { Tooltip } from '@/components/onboarding/Tooltip'
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

export default function ConnectMetaPage() {
  const navigate = useNavigate()
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [businessId, setBusinessId] = useState('')
  const [adAccountId, setAdAccountId] = useState('')

  const handleConnect = async () => {
    setIsConnecting(true)
    setError(null)

    try {
      // Simulate OAuth flow
      await new Promise(resolve => setTimeout(resolve, 2000))

      // Mock successful connection
      const mockBusinessId = 'BM-' + Math.random().toString(36).substr(2, 9)
      const mockAdAccountId = 'ACT-' + Math.random().toString(36).substr(2, 9)

      setBusinessId(mockBusinessId)
      setAdAccountId(mockAdAccountId)
      setIsConnected(true)

      // Save to backend
      const userId = 'demo-user-id'
      await fetch('/api/onboarding/step/connect-meta', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          data: {
            meta_business_id: mockBusinessId,
            meta_ad_account_id: mockAdAccountId,
          },
        }),
      })

      // Auto-redirect after success
      setTimeout(() => {
        navigate('/onboarding/connect-google')
      }, 1500)
    } catch (err: any) {
      setError(err.message || 'Failed to connect to Meta')
      setIsConnecting(false)
    }
  }

  const handleSkip = async () => {
    const userId = 'demo-user-id'
    await fetch('/api/onboarding/skip', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        userId,
        step: 'connect-meta',
        reason: 'User chose to skip',
      }),
    })
    navigate('/onboarding/connect-google')
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
            <button
              onClick={() => navigate('/onboarding/welcome')}
              className="text-sm text-zinc-400 hover:text-white transition-colors"
            >
              ← Back
            </button>
          </div>
        </div>
      </div>

      {/* Progress Indicator */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        <ProgressIndicator
          steps={ONBOARDING_STEPS}
          currentStep={2}
          completedSteps={new Set(['welcome'])}
        />
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">Connect Meta Business Manager</h1>
            <p className="text-lg text-zinc-400">
              Connect your Meta account to publish ads directly to Facebook and Instagram
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Left Column - Connection Form */}
            <div>
              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8">
                {!isConnected ? (
                  <>
                    <h3 className="text-xl font-semibold mb-6">Requirements</h3>
                    <ul className="space-y-4 mb-8">
                      {[
                        'Meta Business Manager account',
                        'Admin access to Ad Accounts',
                        'Active payment method',
                        'Business verification (recommended)',
                      ].map((req, idx) => (
                        <li key={idx} className="flex items-start gap-3">
                          <CheckCircleIcon className="h-5 w-5 text-violet-400 mt-0.5 flex-shrink-0" />
                          <span className="text-zinc-300">{req}</span>
                        </li>
                      ))}
                    </ul>

                    {error && (
                      <div className="mb-6 bg-red-500/10 border border-red-500/50 rounded-lg p-4 flex items-start gap-3">
                        <ExclamationCircleIcon className="h-5 w-5 text-red-400 mt-0.5 flex-shrink-0" />
                        <div>
                          <p className="text-sm font-medium text-red-400">Connection failed</p>
                          <p className="text-sm text-red-300 mt-1">{error}</p>
                        </div>
                      </div>
                    )}

                    <button
                      onClick={handleConnect}
                      disabled={isConnecting}
                      className="w-full bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 disabled:from-zinc-700 disabled:to-zinc-700 text-white font-semibold px-6 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:cursor-not-allowed"
                    >
                      {isConnecting ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                          Connecting...
                        </span>
                      ) : (
                        'Connect Meta Account'
                      )}
                    </button>

                    <button
                      onClick={handleSkip}
                      disabled={isConnecting}
                      className="w-full mt-3 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 font-medium px-6 py-3 rounded-xl transition-all duration-300"
                    >
                      Skip for now
                    </button>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: 'spring', duration: 0.5 }}
                      className="inline-flex items-center justify-center w-16 h-16 bg-emerald-500/10 rounded-full mb-4"
                    >
                      <CheckCircleIcon className="h-10 w-10 text-emerald-400" />
                    </motion.div>
                    <h3 className="text-xl font-semibold text-white mb-2">
                      Successfully Connected!
                    </h3>
                    <p className="text-zinc-400 mb-6">
                      Your Meta Business Manager is now connected
                    </p>
                    <div className="bg-zinc-800 rounded-lg p-4 text-left space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="text-zinc-500">Business ID</span>
                        <span className="text-zinc-300 font-mono">{businessId}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-zinc-500">Ad Account</span>
                        <span className="text-zinc-300 font-mono">{adAccountId}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column - Help & Tutorial */}
            <div className="space-y-6">
              <VideoTutorial
                title="How to Connect Meta Business Manager"
                description="Step-by-step guide to connecting your Meta account"
                videoUrl="https://www.youtube.com/watch?v=demo"
                duration="2:15"
              />

              <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6">
                <h4 className="font-semibold mb-4 flex items-center gap-2">
                  Need Help?
                  <Tooltip content="We're here to assist you with the connection process" />
                </h4>
                <ul className="space-y-3 text-sm text-zinc-400">
                  <li>• Don't have a Business Manager? <a href="#" className="text-violet-400 hover:text-violet-300">Create one here</a></li>
                  <li>• Need admin access? <a href="#" className="text-violet-400 hover:text-violet-300">Request from your team</a></li>
                  <li>• Having issues? <a href="#" className="text-violet-400 hover:text-violet-300">Contact support</a></li>
                </ul>
              </div>

              <div className="bg-violet-500/10 border border-violet-500/30 rounded-xl p-6">
                <h4 className="font-semibold text-violet-300 mb-2">Pro Tip</h4>
                <p className="text-sm text-zinc-300">
                  Connect multiple ad accounts now to switch between them easily later.
                  You can manage all your accounts from one dashboard.
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
