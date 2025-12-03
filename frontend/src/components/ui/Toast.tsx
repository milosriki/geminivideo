import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { Toast as ToastType, ToastVariant } from '../../stores/toastStore';

interface ToastProps {
  toast: ToastType;
  onClose: () => void;
}

const variantConfig = {
  success: {
    icon: CheckCircleIcon,
    accentColor: 'rgb(34, 197, 94)', // green-500
    borderColor: 'border-green-500/20',
    iconBg: 'bg-green-500/10',
  },
  error: {
    icon: XCircleIcon,
    accentColor: 'rgb(239, 68, 68)', // red-500
    borderColor: 'border-red-500/20',
    iconBg: 'bg-red-500/10',
  },
  warning: {
    icon: ExclamationTriangleIcon,
    accentColor: 'rgb(245, 158, 11)', // amber-500
    borderColor: 'border-amber-500/20',
    iconBg: 'bg-amber-500/10',
  },
  info: {
    icon: InformationCircleIcon,
    accentColor: 'rgb(59, 130, 246)', // blue-500
    borderColor: 'border-blue-500/20',
    iconBg: 'bg-blue-500/10',
  },
};

export const Toast: React.FC<ToastProps> = ({ toast, onClose }) => {
  const [progress, setProgress] = useState(100);
  const duration = toast.duration || 5000;
  const config = variantConfig[toast.variant];
  const Icon = config.icon;

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);

      if (remaining === 0) {
        clearInterval(interval);
      }
    }, 10);

    return () => clearInterval(interval);
  }, [duration]);

  return (
    <motion.div
      initial={{ opacity: 0, x: 100, scale: 0.95 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.95 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className={`
        relative w-96 bg-zinc-800 border ${config.borderColor} rounded-lg shadow-xl overflow-hidden
      `}
    >
      {/* Content */}
      <div className="p-4 flex items-start gap-3">
        {/* Icon */}
        <div className={`flex-shrink-0 ${config.iconBg} rounded-lg p-2`}>
          <Icon className="h-5 w-5" style={{ color: config.accentColor }} />
        </div>

        {/* Text Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white mb-0.5">
            {toast.title}
          </h3>
          {toast.message && (
            <p className="text-sm text-zinc-400 break-words">
              {toast.message}
            </p>
          )}
        </div>

        {/* Close Button */}
        <button
          onClick={onClose}
          className="flex-shrink-0 text-zinc-400 hover:text-white transition-colors"
          aria-label="Close notification"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-zinc-700/50">
        <motion.div
          className="h-full"
          style={{
            backgroundColor: config.accentColor,
            width: `${progress}%`,
          }}
          initial={{ width: '100%' }}
          animate={{ width: '0%' }}
          transition={{ duration: duration / 1000, ease: 'linear' }}
        />
      </div>
    </motion.div>
  );
};
