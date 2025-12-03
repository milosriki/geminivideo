import React from 'react';
import { motion } from 'framer-motion';
import { CheckIcon, TagIcon, WandIcon, EyeIcon } from '../icons';

interface Step {
  id: number;
  name: string;
  icon: React.FC<{ className?: string }>;
}

interface WizardProgressProps {
  currentStep: number;
  onStepClick: (step: number) => void;
}

const STEPS: Step[] = [
  { id: 1, name: 'Setup', icon: TagIcon },
  { id: 2, name: 'Creative', icon: WandIcon },
  { id: 3, name: 'Review', icon: EyeIcon },
];

export const WizardProgress: React.FC<WizardProgressProps> = ({
  currentStep,
  onStepClick,
}) => {
  return (
    <div className="flex items-center justify-between mb-8 px-4">
      {STEPS.map((step, index) => {
        const isCompleted = currentStep > step.id;
        const isCurrent = currentStep === step.id;
        const canClick = currentStep >= step.id;

        return (
          <React.Fragment key={step.id}>
            <button
              onClick={() => canClick && onStepClick(step.id)}
              disabled={!canClick}
              className={`flex flex-col items-center group transition-all ${
                canClick ? 'cursor-pointer' : 'cursor-not-allowed opacity-50'
              }`}
            >
              <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                className={`relative w-12 h-12 rounded-full flex items-center justify-center mb-2 transition-all ${
                  isCompleted
                    ? 'bg-indigo-500 shadow-lg shadow-indigo-500/50'
                    : isCurrent
                    ? 'bg-indigo-500 shadow-lg shadow-indigo-500/50 ring-4 ring-indigo-500/20'
                    : 'bg-zinc-800 border-2 border-zinc-700'
                } ${canClick ? 'group-hover:scale-110' : ''}`}
              >
                {isCompleted ? (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  >
                    <CheckIcon className="w-6 h-6 text-white" />
                  </motion.div>
                ) : (
                  <step.icon
                    className={`w-6 h-6 ${
                      isCurrent ? 'text-white' : 'text-zinc-400'
                    }`}
                  />
                )}
              </motion.div>
              <span
                className={`text-sm font-medium transition-colors ${
                  isCurrent
                    ? 'text-indigo-400'
                    : isCompleted
                    ? 'text-zinc-300'
                    : 'text-zinc-500'
                }`}
              >
                {step.name}
              </span>
            </button>

            {index < STEPS.length - 1 && (
              <div className="flex-1 h-0.5 mx-4 relative">
                <div className="absolute inset-0 bg-zinc-800" />
                <motion.div
                  initial={{ scaleX: 0 }}
                  animate={{
                    scaleX: currentStep > step.id ? 1 : 0,
                  }}
                  transition={{ duration: 0.3 }}
                  className="absolute inset-0 bg-indigo-500 origin-left"
                />
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
