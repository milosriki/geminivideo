import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SparklesIcon, RocketLaunchIcon } from '@heroicons/react/24/outline'
import { ProgressIndicator } from '@/components/onboarding/ProgressIndicator'
import { Tooltip } from '@/components/onboarding/Tooltip'
import { LiveChatWidget } from '@/components/onboarding/LiveChatWidget'

const ONBOARDING_STEPS = [
  { id: 'welcome', name: 'Welcome', description: 'Get started' },
  { id: 'meta', name: 'Meta', description: 'Connect account' },
  { id: 'google', name: 'Google', description: 'Connect ads' },
  { id: 'configure', name: 'Configure', description: 'Set preferences' },
  { id: 'campaign', name: 'Campaign', description: 'Create first ad' },
  { id: 'complete', name: 'Complete', description: 'You\'re ready!' },
]

const CAMPAIGN_TEMPLATES = [
  {
    id: 'ecommerce',
    name: 'E-commerce Product Launch',
    description: 'Perfect for launching new products with high-converting video ads',
    objective: 'Conversions',
    icon: '🛍️',
  },
  {
    id: 'lead-gen',
    name: 'Lead Generation',
    description: 'Generate qualified leads for your B2B or high-ticket offers',
    objective: 'Lead Generation',
    icon: '📈',
  },
  {
    id: 'brand-awareness',
    name: 'Brand Awareness',
    description: 'Build brand recognition and reach new audiences at scale',
    objective: 'Awareness',
    icon: '🎯',
  },
  {
    id: 'retargeting',
    name: 'Retargeting Campaign',
    description: 'Re-engage warm audiences with personalized video ads',
    objective: 'Conversions',
    icon: '🔄',
  },
]

export default function FirstCampaignPage() {
  const navigate = useNavigate()
  const [creating, setCreating] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [campaignName, setCampaignName] = useState('')

  const handleCreate = async () => {
    if (!selectedTemplate || !campaignName) {
      return
    }

    setCreating(true)

    try {
      // Create campaign (mock)
      await new Promise(resolve => setTimeout(resolve, 2000))
      const mockCampaignId = 'CAMP-' + Math.random().toString(36).substr(2, 9)

      // Mark step complete
      const userId = 'demo-user-id'
      await fetch('/api/onboarding/step/first-campaign', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          data: { campaign_id: mockCampaignId },
        }),
      })

      navigate('/onboarding/complete')
    } catch (error) {
      console.error('Error creating campaign:', error)
      setCreating(false)
    }
  }

  const handleSkip = () => {
    navigate('/onboarding/complete')
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
              onClick={() => navigate('/onboarding/configure')}
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
          currentStep={5}
          completedSteps={new Set(['welcome', 'meta', 'google', 'configure'])}
        />
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-violet-500/10 rounded-full mb-4">
              <RocketLaunchIcon className="h-8 w-8 text-violet-400" />
            </div>
            <h1 className="text-4xl font-bold mb-4">Create Your First Campaign</h1>
            <p className="text-lg text-zinc-400">
              Choose a template to get started. You can customize everything later.
            </p>
          </div>

          <div className="space-y-8">
            {/* Campaign Name */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8">
              <label className="block text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                Campaign Name
                <Tooltip content="Give your campaign a descriptive name" />
              </label>
              <input
                type="text"
                value={campaignName}
                onChange={(e) => setCampaignName(e.target.value)}
                placeholder="e.g., Holiday Sale 2024"
                className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
              />
            </div>

            {/* Template Selection */}
            <div>
              <h3 className="text-lg font-semibold mb-4">Choose a Template</h3>
              <div className="grid md:grid-cols-2 gap-4">
                {CAMPAIGN_TEMPLATES.map((template) => (
                  <motion.button
                    key={template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`text-left bg-zinc-900 border-2 rounded-xl p-6 transition-all duration-300 ${
                      selectedTemplate === template.id
                        ? 'border-violet-500 bg-violet-500/5'
                        : 'border-zinc-800 hover:border-zinc-700'
                    }`}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <div className="text-3xl mb-3">{template.icon}</div>
                    <h4 className="font-semibold text-white mb-2">{template.name}</h4>
                    <p className="text-sm text-zinc-400 mb-3">{template.description}</p>
                    <div className="inline-block px-3 py-1 bg-zinc-800 rounded-full text-xs text-zinc-400">
                      {template.objective}
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>

            {/* AI Preview */}
            {selectedTemplate && campaignName && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 border border-violet-500/30 rounded-xl p-6"
              >
                <h4 className="font-semibold text-violet-300 mb-3 flex items-center gap-2">
                  <SparklesIcon className="h-5 w-5" />
                  AI Recommendation
                </h4>
                <p className="text-sm text-zinc-300 mb-4">
                  Based on your selection, we recommend:
                </p>
                <ul className="space-y-2 text-sm text-zinc-400">
                  <li>• Generate 50-100 video variations</li>
                  <li>• Target 5-7 audience segments</li>
                  <li>• Run A/B tests on hooks and CTAs</li>
                  <li>• Estimated ROAS: 3.2x - 4.8x</li>
                </ul>
              </motion.div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end gap-4">
              <button
                onClick={handleSkip}
                className="bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 font-medium px-6 py-3 rounded-xl transition-all duration-300"
              >
                Skip for now
              </button>
              <button
                onClick={handleCreate}
                disabled={!selectedTemplate || !campaignName || creating}
                className="bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 disabled:from-zinc-700 disabled:to-zinc-700 text-white font-semibold px-8 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:cursor-not-allowed"
              >
                {creating ? (
                  <span className="flex items-center gap-2">
                    <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating...
                  </span>
                ) : (
                  <>
                    Create Campaign
                    <RocketLaunchIcon className="inline h-5 w-5 ml-2" />
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
