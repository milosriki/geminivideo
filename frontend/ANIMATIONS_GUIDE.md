# Global Animations Implementation Guide

This guide documents all the animation components and utilities implemented in the application.

## Overview

Global animations have been added to enhance the user experience with smooth, performant transitions. All animations respect `prefers-reduced-motion` for accessibility.

## Components Created

### 1. PageTransition (`src/components/ui/PageTransition.tsx`)

**Purpose**: Wrapper component for page content with fade + slide animation.

**Features**:
- Fade in from opacity 0 to 1
- Slide up from 20px below
- Exit animation when navigating away
- Duration: 300ms
- Respects prefers-reduced-motion

**Usage**:
```tsx
<PageTransition>
  <YourPageContent />
</PageTransition>
```

**Props**:
- `children: React.ReactNode` - Content to animate
- `className?: string` - Optional additional classes

---

### 2. AnimatedCard (`src/components/ui/AnimatedCard.tsx`)

**Purpose**: Card component with smooth hover effects.

**Features**:
- Lift on hover (translateY by default -4px)
- Shadow increase on hover
- Optional scale on hover
- Customizable lift amount
- Can disable hover effects
- Performance optimized (uses transform/opacity only)

**Usage**:
```tsx
<AnimatedCard scaleOnHover liftAmount={-8}>
  <h2>Card Title</h2>
  <p>Card content...</p>
</AnimatedCard>
```

**Props**:
- `children: React.ReactNode` - Card content
- `className?: string` - Additional CSS classes
- `scaleOnHover?: boolean` - Enable scale animation (default: false)
- `liftAmount?: number` - Lift distance in pixels (default: -4)
- `disableHover?: boolean` - Disable all hover effects (default: false)
- All other motion div props supported

---

### 3. FadeIn (`src/components/ui/FadeIn.tsx`)

**Purpose**: Simple fade-in wrapper with configurable direction.

**Features**:
- Fade in animation with directional slide
- Configurable delay, duration, and direction
- Four directions: up, down, left, right
- Customizable distance
- Can be disabled for reduced motion

**Usage**:
```tsx
<FadeIn delay={0.2} direction="up" duration={0.5}>
  <div>Content fades in from below</div>
</FadeIn>
```

**Props**:
- `children: React.ReactNode` - Content to animate
- `delay?: number` - Delay in seconds (default: 0)
- `duration?: number` - Duration in seconds (default: 0.3)
- `direction?: 'up' | 'down' | 'left' | 'right'` - Slide direction (default: 'up')
- `distance?: number` - Slide distance in pixels (default: 20)
- `className?: string` - Additional CSS classes
- `disabled?: boolean` - Disable animation (default: false)

---

### 4. StaggerContainer (`src/components/ui/StaggerContainer.tsx`)

**Purpose**: Container that staggers children animations.

**Features**:
- Automatically animates children with stagger delay
- Each child fades in and slides
- Configurable stagger delay and direction
- Initial delay before first child
- Performance optimized

**Usage**:
```tsx
<StaggerContainer staggerDelay={0.1} initialDelay={0.2}>
  <div>Item 1 (animates at 0.2s)</div>
  <div>Item 2 (animates at 0.3s)</div>
  <div>Item 3 (animates at 0.4s)</div>
</StaggerContainer>
```

**Props**:
- `children: React.ReactNode` - Children to animate
- `staggerDelay?: number` - Delay between children in seconds (default: 0.1)
- `initialDelay?: number` - Initial delay in seconds (default: 0)
- `duration?: number` - Animation duration in seconds (default: 0.3)
- `direction?: 'up' | 'down' | 'left' | 'right'` - Slide direction (default: 'up')
- `className?: string` - Additional CSS classes

---

## CSS Animations (`src/styles/animations.css`)

Pre-built CSS keyframe animations for common patterns:

### Animation Classes

| Class | Description |
|-------|-------------|
| `.animate-fade-in` | Simple fade in (300ms) |
| `.animate-slide-up` | Fade + slide from below (300ms) |
| `.animate-slide-down` | Fade + slide from above (300ms) |
| `.animate-slide-left` | Fade + slide from right (300ms) |
| `.animate-slide-right` | Fade + slide from left (300ms) |
| `.animate-scale-in` | Fade + scale from 95% (300ms) |
| `.animate-pulse-subtle` | Gentle pulse (2s, infinite) |
| `.animate-shimmer` | Shimmer effect for loading (2s, infinite) |
| `.animate-bounce-in` | Bounce entrance (500ms) |
| `.animate-rotate-in` | Rotate + fade entrance (400ms) |

### Utility Classes

**Delays**:
- `.animation-delay-100` - 100ms delay
- `.animation-delay-200` - 200ms delay
- `.animation-delay-300` - 300ms delay
- `.animation-delay-400` - 400ms delay
- `.animation-delay-500` - 500ms delay

**Durations**:
- `.animation-duration-100` - 100ms
- `.animation-duration-200` - 200ms
- `.animation-duration-300` - 300ms
- `.animation-duration-500` - 500ms
- `.animation-duration-700` - 700ms
- `.animation-duration-1000` - 1000ms

**Usage**:
```html
<div class="animate-slide-up animation-delay-200">
  Content slides up after 200ms
</div>
```

---

## Updated Components

### MainLayout.tsx
- Added `AnimatePresence` for route transitions
- Wraps `<Outlet />` with `PageTransition` component
- Keyed by `location.pathname` for smooth page changes

### App.tsx
- Updated placeholder pages (Assets, Settings) to use `FadeIn`

### AnalyticsDashboard.tsx
- Replaced individual motion divs with `FadeIn` and `StaggerContainer`
- Header uses `FadeIn` with "down" direction
- Main sections use `StaggerContainer` for sequential animation

### AdCard.tsx (library)
- Replaced standard div with `AnimatedCard`
- Enabled `scaleOnHover` prop
- Custom `liftAmount` of -8px for more pronounced effect

### AIInsights.tsx (dashboard)
- Wrapped insight cards with `StaggerContainer`
- Stagger delay of 0.1s between cards
- Added hover effect to cards

---

## Integration

### Import in index.css
```css
@import './styles/animations.css';
```

### Export in ui/index.ts
```typescript
export { PageTransition } from './PageTransition';
export { AnimatedCard } from './AnimatedCard';
export { FadeIn } from './FadeIn';
export { StaggerContainer } from './StaggerContainer';
```

---

## Best Practices

### ✅ DO:
- Keep animations short (300ms default) for responsive feel
- Use only `transform` and `opacity` for best performance
- Stagger delays for multiple items (0.1s between items)
- Test with `prefers-reduced-motion` enabled
- Use `PageTransition` for all page-level components
- Use `AnimatedCard` for interactive card components
- Use `StaggerContainer` for lists of items

### ❌ DON'T:
- Animate width, height, or layout properties
- Use animations longer than 500ms unless absolutely necessary
- Overuse animations - they should enhance, not distract
- Forget about accessibility (all components respect reduced motion)
- Chain too many animations - keep it simple
- Animate on scroll without throttling/debouncing

---

## Performance Considerations

All animations are optimized for performance:

1. **GPU Acceleration**: Using `transform` and `opacity` triggers GPU acceleration
2. **No Layout Thrashing**: Animations don't trigger reflow/repaint
3. **Framer Motion**: Uses optimized animation engine
4. **Reduced Motion**: Automatically disabled when user prefers reduced motion
5. **Cubic Bezier Easing**: Smooth, natural-feeling animations

---

## Example Component

See `src/components/ui/AnimationExamples.tsx` for a comprehensive demo of all animation components and patterns.

---

## Testing Animations

### Test Reduced Motion
In Chrome DevTools:
1. Open DevTools (F12)
2. Press Cmd/Ctrl + Shift + P
3. Type "Show Rendering"
4. Check "Emulate CSS prefers-reduced-motion"

### Performance Testing
1. Open DevTools Performance tab
2. Start recording
3. Navigate between pages
4. Check for frame drops (should maintain 60fps)

---

## Future Enhancements

Potential additions:
- Page transition variants (slide, scale, etc.)
- Scroll-triggered animations
- Loading state animations
- Micro-interactions (button press, input focus, etc.)
- Custom spring configurations
- Gesture-based animations

---

## Questions or Issues?

If you encounter issues with animations:
1. Check browser console for errors
2. Verify framer-motion version (should be ^12.23.25)
3. Test with animations disabled (reduced motion)
4. Check for conflicting CSS transitions
5. Verify component imports are correct
