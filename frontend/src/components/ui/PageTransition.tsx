import React from 'react';
import { motion } from 'framer-motion';

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
}

/**
 * PageTransition - Wrapper component for page content with fade + slide animation
 *
 * Provides smooth entrance animation for page content with:
 * - Fade in from opacity 0 to 1
 * - Slide up from 20px below
 * - Respects prefers-reduced-motion
 *
 * @example
 * ```tsx
 * <PageTransition>
 *   <h1>Page Content</h1>
 * </PageTransition>
 * ```
 */
export const PageTransition: React.FC<PageTransitionProps> = ({
  children,
  className = '',
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{
        duration: 0.3,
        ease: 'easeOut',
      }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

export default PageTransition;
