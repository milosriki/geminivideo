import React from 'react';
import { motion } from 'framer-motion';

interface PageLoaderProps {
  message?: string;
}

const PageLoader: React.FC<PageLoaderProps> = ({ message = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 bg-zinc-950 flex items-center justify-center z-50">
      <div className="flex flex-col items-center space-y-6">
        {/* Logo Animation */}
        <motion.div
          className="relative"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{
            duration: 0.5,
            ease: "easeOut"
          }}
        >
          {/* Outer Ring */}
          <motion.div
            className="w-24 h-24 rounded-full border-4 border-zinc-800"
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 3,
              repeat: Infinity,
              ease: "linear"
            }}
          >
            {/* Gradient Spinner */}
            <motion.div
              className="absolute inset-0 rounded-full"
              style={{
                background: 'linear-gradient(90deg, transparent 50%, #10b981 50%)',
              }}
              animate={{
                rotate: 360,
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: "linear"
              }}
            />
          </motion.div>

          {/* GeminiVideo Logo/Icon */}
          <motion.div
            className="absolute inset-0 flex items-center justify-center"
            animate={{
              scale: [1, 1.1, 1],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          >
            <svg
              className="w-12 h-12 text-brand-500"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4zM14 13h-3v3H9v-3H6v-2h3V8h2v3h3v2z" />
            </svg>
          </motion.div>
        </motion.div>

        {/* Loading Text */}
        <motion.div
          className="flex flex-col items-center space-y-2"
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: 0.2,
            duration: 0.5,
          }}
        >
          <h3 className="text-xl font-semibold text-white">
            {message}
          </h3>

          {/* Animated Dots */}
          <div className="flex space-x-1">
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                className="w-2 h-2 bg-brand-500 rounded-full"
                animate={{
                  scale: [1, 1.5, 1],
                  opacity: [0.5, 1, 0.5],
                }}
                transition={{
                  duration: 1,
                  repeat: Infinity,
                  delay: i * 0.15,
                  ease: "easeInOut"
                }}
              />
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
};

// Minimal loader variant
export const MiniLoader: React.FC = () => {
  return (
    <div className="flex items-center justify-center p-8">
      <motion.div
        className="w-8 h-8 border-4 border-zinc-700 border-t-brand-500 rounded-full"
        animate={{ rotate: 360 }}
        transition={{
          duration: 1,
          repeat: Infinity,
          ease: "linear"
        }}
      />
    </div>
  );
};

// Inline spinner
export const Spinner: React.FC<{ size?: 'sm' | 'md' | 'lg'; className?: string }> = ({
  size = 'md',
  className = ''
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-3',
    lg: 'w-8 h-8 border-4',
  };

  return (
    <motion.div
      className={`${sizeClasses[size]} border-zinc-700 border-t-brand-500 rounded-full ${className}`}
      animate={{ rotate: 360 }}
      transition={{
        duration: 1,
        repeat: Infinity,
        ease: "linear"
      }}
    />
  );
};

export default PageLoader;
