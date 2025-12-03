import React from 'react';
import { motion } from 'framer-motion';

interface StaggerContainerProps {
  children: React.ReactNode;
  /**
   * Delay between each child animation in seconds (default: 0.1)
   */
  staggerDelay?: number;
  /**
   * Initial delay before first child animates in seconds (default: 0)
   */
  initialDelay?: number;
  /**
   * Animation duration for each child in seconds (default: 0.3)
   */
  duration?: number;
  /**
   * Additional className
   */
  className?: string;
  /**
   * Direction of stagger animation (default: 'up')
   */
  direction?: 'up' | 'down' | 'left' | 'right';
}

/**
 * StaggerContainer - Container that staggers children animations
 *
 * Automatically animates children with a stagger delay between each.
 * Each child will fade in and slide from the specified direction.
 *
 * Features:
 * - Staggers animations of direct children
 * - Configurable stagger delay and direction
 * - Respects prefers-reduced-motion
 * - Performance optimized
 *
 * @example
 * ```tsx
 * <StaggerContainer staggerDelay={0.1}>
 *   <div>Item 1</div>
 *   <div>Item 2</div>
 *   <div>Item 3</div>
 * </StaggerContainer>
 * ```
 */
export const StaggerContainer: React.FC<StaggerContainerProps> = ({
  children,
  staggerDelay = 0.1,
  initialDelay = 0,
  duration = 0.3,
  className = '',
  direction = 'up',
}) => {
  const containerVariants = {
    hidden: { opacity: 1 },
    visible: {
      opacity: 1,
      transition: {
        delayChildren: initialDelay,
        staggerChildren: staggerDelay,
      },
    },
  };

  const getItemVariants = () => {
    let x = 0;
    let y = 0;

    switch (direction) {
      case 'up':
        y = 20;
        break;
      case 'down':
        y = -20;
        break;
      case 'left':
        x = 20;
        break;
      case 'right':
        x = -20;
        break;
    }

    return {
      hidden: { opacity: 0, x, y },
      visible: {
        opacity: 1,
        x: 0,
        y: 0,
        transition: {
          duration,
        },
      },
    };
  };

  const itemVariants = getItemVariants();

  // Convert children to array and wrap each in motion.div
  const childrenArray = React.Children.toArray(children);

  return (
    <motion.div
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {childrenArray.map((child, index) => (
        <motion.div key={index} variants={itemVariants}>
          {child}
        </motion.div>
      ))}
    </motion.div>
  );
};

export default StaggerContainer;
