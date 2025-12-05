import { useState } from 'react'
import { ChatBubbleLeftRightIcon, XMarkIcon } from '@heroicons/react/24/outline'
import { motion, AnimatePresence } from 'framer-motion'

export function LiveChatWidget() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      {/* Chat Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full p-4 shadow-lg hover:shadow-xl transition-shadow"
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
      >
        {isOpen ? (
          <XMarkIcon className="h-6 w-6 text-white" />
        ) : (
          <ChatBubbleLeftRightIcon className="h-6 w-6 text-white" />
        )}
      </motion.button>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="fixed bottom-24 right-6 z-50 w-96 h-[500px] bg-zinc-900 border border-zinc-800 rounded-2xl shadow-2xl overflow-hidden"
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-violet-500 to-fuchsia-500 px-6 py-4">
              <h3 className="font-semibold text-white">Live Support</h3>
              <p className="text-sm text-white/80">We typically reply in under 2 minutes</p>
            </div>

            {/* Chat Content */}
            <div className="h-[calc(100%-140px)] p-6 overflow-y-auto">
              <div className="space-y-4">
                {/* Welcome Message */}
                <div className="flex gap-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-violet-500 rounded-full flex items-center justify-center text-white text-sm font-medium">
                    GV
                  </div>
                  <div className="flex-1">
                    <div className="bg-zinc-800 rounded-lg px-4 py-3">
                      <p className="text-sm text-zinc-300">
                        Hey! Welcome to GeminiVideo. I'm here to help you get started.
                        What brings you here today?
                      </p>
                    </div>
                    <p className="text-xs text-zinc-500 mt-1">Just now</p>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-2">
                  <p className="text-xs text-zinc-500 font-medium">QUICK ACTIONS</p>
                  <div className="space-y-2">
                    {[
                      'Help connecting Meta Business Manager',
                      'Troubleshoot Google Ads connection',
                      'Setup my first campaign',
                      'Speak with a specialist'
                    ].map((action, idx) => (
                      <button
                        key={idx}
                        className="w-full text-left px-4 py-3 bg-zinc-800 hover:bg-zinc-750 border border-zinc-700 hover:border-violet-500/50 rounded-lg text-sm text-zinc-300 transition-colors"
                      >
                        {action}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Input */}
            <div className="absolute bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-800 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Type your message..."
                  className="flex-1 bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                />
                <button className="bg-violet-500 hover:bg-violet-600 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors">
                  Send
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
