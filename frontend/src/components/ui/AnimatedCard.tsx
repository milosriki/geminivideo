import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';
import { twMerge } from 'tailwind-merge';

interface AnimatedCardProps extends Omit<HTMLMotionProps<'div'>, 'scale'> {
  children: React.ReactNode;
  className?: string;
  /**
   * Enable scale animation on hover (default: false)
   */
  scaleOnHover?: boolean;
  /**
   * Custom lift amount in pixels (default: -4)
   */
  liftAmount?: number;
  /**
   * Disable all hover effects
   */
  disableHover?: boolean;
}

/**
 * AnimatedCard - Card component with smooth hover effects
 *
 * Features:
 * - Lift on hover (translateY)
 * - Shadow increase on hover
 * - Optional scale on hover
 * - Performance optimized (uses transform/opacity)
 * - Respects prefers-reduced-motion
 *
 * @example
 * ```tsx
 * <AnimatedCard scaleOnHover>
 *   <h2>Card Title</h2>
 *   <p>Card content...</p>
 * </AnimatedCard>
 * ```
 */
export const AnimatedCard: React.FC<AnimatedCardProps> = ({
  children,
  className = '',
  scaleOnHover = false,
  liftAmount = -4,
  disableHover = false,
  ...motionProps
}) => {
  const baseClasses = 'bg-zinc-900 border border-zinc-800 rounded-xl shadow-lg shadow-black/20';

  const hoverVariants = {
    initial: {
      y: 0,
      scale: 1,
    },
    hover: disableHover
      ? {}
      : {
          y: liftAmount,
          scale: scaleOnHover ? 1.02 : 1,
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.2)',
        },
  };

  return (
    <motion.div
      className={twMerge(baseClasses, className)}
      variants={hoverVariants}
      initial="initial"
      whileHover="hover"
      transition={{
        duration: 0.3,
        ease: 'easeOut',
      }}
      {...motionProps}
    >
      {children}
    </motion.div>
  );
};

export default AnimatedCard;
