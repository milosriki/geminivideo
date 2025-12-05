import { CheckCircleIcon } from '@heroicons/react/24/solid'
import { motion } from 'framer-motion'

interface Step {
  id: string
  name: string
  description: string
}

interface ProgressIndicatorProps {
  steps: Step[]
  currentStep: number
  completedSteps: Set<string>
}

export function ProgressIndicator({ steps, currentStep, completedSteps }: ProgressIndicatorProps) {
  return (
    <nav aria-label="Progress" className="w-full">
      <ol role="list" className="flex items-center justify-between w-full">
        {steps.map((step, stepIdx) => {
          const isCompleted = completedSteps.has(step.id)
          const isCurrent = stepIdx + 1 === currentStep
          const isUpcoming = stepIdx + 1 > currentStep

          return (
            <li key={step.id} className={`relative ${stepIdx !== steps.length - 1 ? 'flex-1' : ''}`}>
              {/* Connector Line */}
              {stepIdx !== steps.length - 1 && (
                <div className="absolute left-full top-5 -ml-px h-0.5 w-full">
                  <motion.div
                    className={`h-full ${isCompleted ? 'bg-violet-500' : 'bg-zinc-800'}`}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: isCompleted ? 1 : 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                  />
                </div>
              )}

              <div className="group relative flex flex-col items-center">
                {/* Step Circle */}
                <motion.div
                  className={`relative flex h-10 w-10 items-center justify-center rounded-full border-2 ${
                    isCompleted
                      ? 'border-violet-500 bg-violet-500'
                      : isCurrent
                      ? 'border-violet-500 bg-zinc-900'
                      : 'border-zinc-700 bg-zinc-900'
                  }`}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ duration: 0.3, delay: stepIdx * 0.1 }}
                >
                  {isCompleted ? (
                    <CheckCircleIcon className="h-6 w-6 text-white" />
                  ) : (
                    <span
                      className={`text-sm font-semibold ${
                        isCurrent ? 'text-violet-400' : 'text-zinc-500'
                      }`}
                    >
                      {stepIdx + 1}
                    </span>
                  )}
                </motion.div>

                {/* Step Label */}
                <div className="mt-3 text-center">
                  <span
                    className={`block text-sm font-medium ${
                      isCurrent
                        ? 'text-violet-400'
                        : isCompleted
                        ? 'text-violet-300'
                        : 'text-zinc-500'
                    }`}
                  >
                    {step.name}
                  </span>
                  <span className="block text-xs text-zinc-600 mt-1 max-w-24">
                    {step.description}
                  </span>
                </div>

                {/* Current Step Indicator */}
                {isCurrent && (
                  <motion.div
                    className="absolute -bottom-2 h-1 w-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500"
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ duration: 0.5 }}
                  />
                )}
              </div>
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
