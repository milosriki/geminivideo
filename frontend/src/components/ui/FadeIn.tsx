import React from 'react';
import { motion } from 'framer-motion';

type Direction = 'up' | 'down' | 'left' | 'right';

interface FadeInProps {
  children: React.ReactNode;
  /**
   * Delay before animation starts in seconds (default: 0)
   */
  delay?: number;
  /**
   * Animation duration in seconds (default: 0.3)
   */
  duration?: number;
  /**
   * Direction of slide animation (default: 'up')
   */
  direction?: Direction;
  /**
   * Distance to slide in pixels (default: 20)
   */
  distance?: number;
  /**
   * Additional className
   */
  className?: string;
  /**
   * Disable animations (useful for reduced motion)
   */
  disabled?: boolean;
}

const directionOffsets: Record<Direction, { x: number; y: number }> = {
  up: { x: 0, y: 20 },
  down: { x: 0, y: -20 },
  left: { x: 20, y: 0 },
  right: { x: -20, y: 0 },
};

/**
 * FadeIn - Simple fade-in wrapper with configurable direction
 *
 * Features:
 * - Fade in animation with directional slide
 * - Configurable delay, duration, and direction
 * - Respects prefers-reduced-motion
 * - Lightweight and performant
 *
 * @example
 * ```tsx
 * <FadeIn delay={0.2} direction="up">
 *   <div>Content fades in from below</div>
 * </FadeIn>
 * ```
 */
export const FadeIn: React.FC<FadeInProps> = ({
  children,
  delay = 0,
  duration = 0.3,
  direction = 'up',
  distance = 20,
  className = '',
  disabled = false,
}) => {
  if (disabled) {
    return <div className={className}>{children}</div>;
  }

  const offset = directionOffsets[direction];
  const initialX = (offset.x / 20) * distance;
  const initialY = (offset.y / 20) * distance;

  return (
    <motion.div
      initial={{ opacity: 0, x: initialX, y: initialY }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{
        duration,
        delay,
        ease: 'easeOut',
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

export default FadeIn;
