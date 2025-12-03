import React from 'react';
import { PageTransition } from './PageTransition';
import { AnimatedCard } from './AnimatedCard';
import { FadeIn } from './FadeIn';
import { StaggerContainer } from './StaggerContainer';

/**
 * AnimationExamples - Demonstrations of all animation components
 *
 * This file shows examples of how to use each animation component.
 * Use this as a reference when implementing animations in your pages.
 */

export const AnimationExamples: React.FC = () => {
  return (
    <PageTransition>
      <div className="p-8 space-y-12 bg-zinc-950 min-h-screen">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <FadeIn direction="down">
            <h1 className="text-4xl font-bold text-white mb-2">
              Animation Components
            </h1>
            <p className="text-zinc-400">
              Examples of all available animation components and how to use them
            </p>
          </FadeIn>

          {/* PageTransition Example */}
          <section className="mt-12">
            <FadeIn delay={0.1}>
              <h2 className="text-2xl font-bold text-white mb-4">
                1. PageTransition
              </h2>
              <p className="text-zinc-400 mb-4">
                Wrap your page content for smooth entrance/exit animations when
                navigating between routes.
              </p>
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                <code className="text-sm text-green-400">
                  {`<PageTransition>
  <YourPageContent />
</PageTransition>`}
                </code>
              </div>
            </FadeIn>
          </section>

          {/* AnimatedCard Example */}
          <section className="mt-12">
            <FadeIn delay={0.2}>
              <h2 className="text-2xl font-bold text-white mb-4">
                2. AnimatedCard
              </h2>
              <p className="text-zinc-400 mb-4">
                Cards with smooth hover effects (lift, shadow, optional scale)
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <AnimatedCard className="p-6">
                  <h3 className="text-white font-semibold mb-2">
                    Default Card
                  </h3>
                  <p className="text-zinc-400 text-sm">
                    Hover to see lift and shadow effects
                  </p>
                </AnimatedCard>

                <AnimatedCard className="p-6" scaleOnHover>
                  <h3 className="text-white font-semibold mb-2">
                    Scale on Hover
                  </h3>
                  <p className="text-zinc-400 text-sm">
                    This card also scales slightly on hover
                  </p>
                </AnimatedCard>

                <AnimatedCard className="p-6" liftAmount={-8}>
                  <h3 className="text-white font-semibold mb-2">
                    Custom Lift
                  </h3>
                  <p className="text-zinc-400 text-sm">
                    Lifts 8px instead of default 4px
                  </p>
                </AnimatedCard>

                <AnimatedCard className="p-6" disableHover>
                  <h3 className="text-white font-semibold mb-2">
                    Hover Disabled
                  </h3>
                  <p className="text-zinc-400 text-sm">
                    No hover effects on this card
                  </p>
                </AnimatedCard>
              </div>
            </FadeIn>
          </section>

          {/* FadeIn Example */}
          <section className="mt-12">
            <FadeIn delay={0.3}>
              <h2 className="text-2xl font-bold text-white mb-4">3. FadeIn</h2>
              <p className="text-zinc-400 mb-4">
                Simple fade-in wrapper with configurable direction and timing
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FadeIn direction="up" delay={0.4}>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                    <p className="text-white text-sm">Fades in from below</p>
                  </div>
                </FadeIn>

                <FadeIn direction="down" delay={0.5}>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                    <p className="text-white text-sm">Fades in from above</p>
                  </div>
                </FadeIn>

                <FadeIn direction="left" delay={0.6}>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                    <p className="text-white text-sm">Fades in from right</p>
                  </div>
                </FadeIn>

                <FadeIn direction="right" delay={0.7}>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                    <p className="text-white text-sm">Fades in from left</p>
                  </div>
                </FadeIn>
              </div>
            </FadeIn>
          </section>

          {/* StaggerContainer Example */}
          <section className="mt-12">
            <FadeIn delay={0.4}>
              <h2 className="text-2xl font-bold text-white mb-4">
                4. StaggerContainer
              </h2>
              <p className="text-zinc-400 mb-4">
                Automatically staggers animation of child elements
              </p>
              <StaggerContainer staggerDelay={0.1} initialDelay={0.5}>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-3">
                  <p className="text-white text-sm">First item (0s delay)</p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-3">
                  <p className="text-white text-sm">Second item (0.1s delay)</p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-3">
                  <p className="text-white text-sm">Third item (0.2s delay)</p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 mb-3">
                  <p className="text-white text-sm">Fourth item (0.3s delay)</p>
                </div>
              </StaggerContainer>
            </FadeIn>
          </section>

          {/* CSS Animations Example */}
          <section className="mt-12">
            <FadeIn delay={0.5}>
              <h2 className="text-2xl font-bold text-white mb-4">
                5. CSS Animation Classes
              </h2>
              <p className="text-zinc-400 mb-4">
                Available utility classes from animations.css
              </p>
              <div className="space-y-3">
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 animate-fade-in">
                  <p className="text-white text-sm">
                    .animate-fade-in - Simple fade in
                  </p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 animate-slide-up animation-delay-100">
                  <p className="text-white text-sm">
                    .animate-slide-up - Slide from below
                  </p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 animate-scale-in animation-delay-200">
                  <p className="text-white text-sm">
                    .animate-scale-in - Scale from center
                  </p>
                </div>
                <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 animate-pulse-subtle animation-delay-300">
                  <p className="text-white text-sm">
                    .animate-pulse-subtle - Gentle pulse (infinite)
                  </p>
                </div>
              </div>
            </FadeIn>
          </section>

          {/* Best Practices */}
          <section className="mt-12">
            <FadeIn delay={0.6}>
              <h2 className="text-2xl font-bold text-white mb-4">
                Best Practices
              </h2>
              <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
                <ul className="space-y-3 text-zinc-300 text-sm">
                  <li className="flex items-start gap-3">
                    <span className="text-green-400 font-bold">✓</span>
                    <span>
                      Keep animations short (300ms default) for responsive feel
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-400 font-bold">✓</span>
                    <span>
                      Use only transform and opacity for best performance
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-400 font-bold">✓</span>
                    <span>
                      All animations respect prefers-reduced-motion
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-green-400 font-bold">✓</span>
                    <span>
                      Stagger delays for multiple items (0.1s between items)
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-red-400 font-bold">✗</span>
                    <span>
                      Avoid animating width, height, or layout properties
                    </span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="text-red-400 font-bold">✗</span>
                    <span>Don't overuse animations - they should enhance UX</span>
                  </li>
                </ul>
              </div>
            </FadeIn>
          </section>
        </div>
      </div>
    </PageTransition>
  );
};

export default AnimationExamples;
