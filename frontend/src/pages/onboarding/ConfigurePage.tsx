import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SparklesIcon, CheckCircleIcon } from '@heroicons/react/24/outline'
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

const CURRENCIES = ['USD', 'EUR', 'GBP', 'CAD', 'AUD']
const TIMEZONES = [
  'America/New_York',
  'America/Los_Angeles',
  'America/Chicago',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Singapore',
  'Australia/Sydney',
]

export default function ConfigurePage() {
  const navigate = useNavigate()
  const [saving, setSaving] = useState(false)

  const [config, setConfig] = useState({
    currency: 'USD',
    timezone: 'America/New_York',
    dailyBudget: '20000',
    emailNotifications: true,
    slackNotifications: false,
    pushNotifications: true,
  })

  const handleSave = async () => {
    setSaving(true)

    try {
      const userId = 'demo-user-id'
      await fetch('/api/onboarding/step/configure', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          data: {
            default_currency: config.currency,
            default_timezone: config.timezone,
            daily_budget_limit: parseFloat(config.dailyBudget),
            email_notifications: config.emailNotifications,
            slack_notifications: config.slackNotifications,
            push_notifications: config.pushNotifications,
          },
        }),
      })

      setTimeout(() => {
        navigate('/onboarding/first-campaign')
      }, 500)
    } catch (error) {
      console.error('Error saving config:', error)
      setSaving(false)
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
            <button
              onClick={() => navigate('/onboarding/connect-google')}
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
          currentStep={4}
          completedSteps={new Set(['welcome', 'meta', 'google'])}
        />
      </div>

      {/* Main Content */}
      <div className="max-w-3xl mx-auto px-6 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold mb-4">Configure Your Settings</h1>
            <p className="text-lg text-zinc-400">
              Set your default preferences for campaigns and notifications
            </p>
          </div>

          <div className="space-y-8">
            {/* Campaign Settings */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                Campaign Settings
                <Tooltip content="These will be your default settings for new campaigns" />
              </h3>

              <div className="space-y-6">
                {/* Currency */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Default Currency
                  </label>
                  <select
                    value={config.currency}
                    onChange={(e) => setConfig({ ...config, currency: e.target.value })}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    {CURRENCIES.map((currency) => (
                      <option key={currency} value={currency}>
                        {currency}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Timezone */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2">
                    Timezone
                  </label>
                  <select
                    value={config.timezone}
                    onChange={(e) => setConfig({ ...config, timezone: e.target.value })}
                    className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Daily Budget */}
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-2 flex items-center gap-2">
                    Daily Budget Limit
                    <Tooltip content="Maximum daily spend across all campaigns" />
                  </label>
                  <div className="relative">
                    <span className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500">
                      $
                    </span>
                    <input
                      type="number"
                      value={config.dailyBudget}
                      onChange={(e) => setConfig({ ...config, dailyBudget: e.target.value })}
                      className="w-full bg-zinc-800 border border-zinc-700 rounded-lg pl-8 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-violet-500"
                      placeholder="20000"
                    />
                  </div>
                  <p className="text-xs text-zinc-500 mt-2">
                    Recommended: $20,000+/day for elite marketers
                  </p>
                </div>
              </div>
            </div>

            {/* Notification Preferences */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8">
              <h3 className="text-xl font-semibold mb-6 flex items-center gap-2">
                Notification Preferences
                <Tooltip content="Choose how you want to receive updates" />
              </h3>

              <div className="space-y-4">
                {/* Email Notifications */}
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.emailNotifications}
                    onChange={(e) => setConfig({ ...config, emailNotifications: e.target.checked })}
                    className="w-5 h-5 rounded border-zinc-700 bg-zinc-800 text-violet-500 focus:ring-2 focus:ring-violet-500 focus:ring-offset-0"
                  />
                  <div className="flex-1">
                    <span className="font-medium text-white group-hover:text-violet-400 transition-colors">
                      Email Notifications
                    </span>
                    <p className="text-sm text-zinc-500">
                      Campaign alerts, performance reports, and important updates
                    </p>
                  </div>
                </label>

                {/* Slack Notifications */}
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.slackNotifications}
                    onChange={(e) => setConfig({ ...config, slackNotifications: e.target.checked })}
                    className="w-5 h-5 rounded border-zinc-700 bg-zinc-800 text-violet-500 focus:ring-2 focus:ring-violet-500 focus:ring-offset-0"
                  />
                  <div className="flex-1">
                    <span className="font-medium text-white group-hover:text-violet-400 transition-colors">
                      Slack Notifications
                    </span>
                    <p className="text-sm text-zinc-500">
                      Real-time alerts sent to your Slack workspace
                    </p>
                  </div>
                </label>

                {/* Push Notifications */}
                <label className="flex items-center gap-3 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={config.pushNotifications}
                    onChange={(e) => setConfig({ ...config, pushNotifications: e.target.checked })}
                    className="w-5 h-5 rounded border-zinc-700 bg-zinc-800 text-violet-500 focus:ring-2 focus:ring-violet-500 focus:ring-offset-0"
                  />
                  <div className="flex-1">
                    <span className="font-medium text-white group-hover:text-violet-400 transition-colors">
                      Push Notifications
                    </span>
                    <p className="text-sm text-zinc-500">
                      Browser notifications for urgent alerts
                    </p>
                  </div>
                </label>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-4">
              <button
                onClick={() => navigate('/onboarding/first-campaign')}
                className="bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 font-medium px-6 py-3 rounded-xl transition-all duration-300"
              >
                Skip
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="bg-gradient-to-r from-violet-500 to-fuchsia-500 hover:from-violet-600 hover:to-fuchsia-600 disabled:from-zinc-700 disabled:to-zinc-700 text-white font-semibold px-8 py-3 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <span className="flex items-center gap-2">
                    <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Saving...
                  </span>
                ) : (
                  <>
                    Save & Continue
                    <span className="ml-2">→</span>
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
