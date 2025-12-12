# GeminiVideo Router Documentation

Complete routing configuration for the GeminiVideo application, exposing all 32 previously hidden components.

## Architecture

The router is organized into three main files:

1. **`index.tsx`** - Main router component with all route definitions
2. **`routes.ts`** - Route metadata and configuration
3. **`README.md`** - This documentation file

## Previously Hidden Components (32 Total)

### Dashboard & Home (1 component)
1. **Creator Dashboard** - `/dashboard/creator` - Alternative creator-focused dashboard

### Campaign Management (1 component)
2. **Campaign Builder** - `/campaigns/builder` - Advanced campaign builder with full features

### Analytics & Reporting (6 components)
3. **Analytics Dashboard** - `/analytics/dashboard` - Comprehensive analytics with charts
4. **Performance Dashboard** - `/analytics/performance` - Detailed performance metrics
5. **Reliability Chart** - `/analytics/reliability` - System reliability tracking
6. **Diversification Dashboard** - `/analytics/diversification` - Portfolio analysis
7. **ROAS Dashboard** - `/analytics/roas` - Return on ad spend tracking
8. **Reports Generator** - `/reports` - Generate PDF/Excel reports

### Studio & Creative Tools (8 components)
9. **Pro Video Editor** - `/studio/pro` - Professional video editing suite
10. **Storyboard Studio** - `/studio/storyboard` - Visual storyboard creator
11. **Video Studio** - `/studio/video` - Advanced video editing
12. **AI Creative Studio** - `/studio/ai` - AI-powered creative generation
13. **Video Generator** - `/studio/generate` - Quick video generation
14. **Audio Mixer Panel** - `/studio/audio-mixer` - Professional audio mixing
15. **Color Grading Panel** - `/studio/color-grading` - Advanced color grading
16. **Color Grading Demo** - `/studio/color-grading-demo` - Color grading demo mode

### Asset Management (3 components)
17. **Assets Panel** - `/library/assets` - Advanced asset management
18. **Ranked Clips Panel** - `/library/clips` - AI-ranked video clips
19. **Semantic Search Panel** - `/library/search` - AI-powered asset search

### Tools & Intelligence (8 components)
20. **Ad Spy Dashboard** - `/spy/dashboard` - Full competitor intelligence dashboard
21. **Analysis Panel** - `/analysis` - Video and creative analysis
22. **Compliance Panel** - `/compliance` - Ad compliance checking
23. **Audio Suite** - `/audio` - Audio tools collection
24. **Audio Suite Panel** - `/audio/suite` - Advanced audio tools
25. **Image Suite** - `/image` - Image editing and generation
26. **AI Assistant** - `/assistant` - AI strategy assistant
27. **Resources Page** - `/resources` - Tutorials and learning resources

### Workflow & Testing (4 components)
28. **A/B Testing Dashboard** - `/testing` - Bayesian A/B testing with statistics
29. **Human Workflow Dashboard** - `/workflow` - Human-in-the-loop approvals
30. **Batch Processing Panel** - `/batch` - Batch video processing
31. **Render Jobs Panel** - `/render` - Video render queue management

### Marketing (1 component)
32. **Landing Page** - `/landing` - Public marketing landing page

## Route Categories

### Dashboard Routes
Routes wrapped in the main dashboard layout with sidebar and navigation.

- `/` - Home Dashboard
- `/dashboard/creator` - Creator Dashboard
- `/projects` - Projects Management
- `/settings` - Settings
- `/help` - Help & Support

### Campaign Routes
Campaign creation and management.

- `/campaigns` - Campaigns List
- `/campaigns/:id` - Campaign Details
- `/create` - Quick Campaign Create
- `/campaigns/builder` - Advanced Campaign Builder
- `/campaigns/new` - New Campaign Flow

### Analytics Routes
Performance tracking and reporting.

- `/analytics` - Main Analytics
- `/analytics/dashboard` - Full Analytics Dashboard
- `/analytics/performance` - Performance Metrics
- `/analytics/reliability` - Reliability Tracking
- `/analytics/diversification` - Portfolio Analysis
- `/analytics/roas` - ROAS Tracking
- `/reports` - Report Generator

### Studio Routes
Video editing and creative tools.

- `/studio` - Studio Landing
- `/studio/:projectId` - Studio with Project
- `/studio/pro` - Pro Video Editor
- `/studio/pro/:projectId` - Pro Editor with Project
- `/studio/storyboard` - Storyboard Creator
- `/studio/video` - Video Studio
- `/studio/ai` - AI Creative Studio
- `/studio/generate` - Video Generator
- `/studio/audio-mixer` - Audio Mixer
- `/studio/color-grading` - Color Grading
- `/studio/color-grading-demo` - Color Grading Demo

### Asset Routes
Asset management and search.

- `/assets` - Assets Overview
- `/library` - Asset Library
- `/library/assets` - Asset Management
- `/library/clips` - Ranked Clips
- `/library/search` - Semantic Search

### Tool Routes
Additional tools and utilities.

- `/spy` - Ad Spy Overview
- `/spy/dashboard` - Full Ad Spy Dashboard
- `/analysis` - Analysis Tools
- `/compliance` - Compliance Checker
- `/audio` - Audio Suite
- `/audio/suite` - Advanced Audio Tools
- `/image` - Image Suite
- `/assistant` - AI Assistant
- `/resources` - Resources & Tutorials

### Workflow Routes
Testing and workflow management.

- `/testing` - A/B Testing
- `/workflow` - Human Workflow
- `/workflow/approvals` - Approval Queue
- `/batch` - Batch Processing
- `/render` - Render Jobs

### Auth Routes (Standalone)
Authentication pages without dashboard layout.

- `/login` - Login
- `/register` - Register
- `/verify` - Email Verification (OTP)

### Onboarding Routes (Standalone)
Onboarding flow without dashboard layout.

- `/onboarding/welcome` - Welcome
- `/onboarding/connect-meta` - Connect Meta Ads
- `/onboarding/connect-google` - Connect Google Ads
- `/onboarding/configure` - Configure Settings
- `/onboarding/first-campaign` - First Campaign Setup
- `/onboarding/complete` - Onboarding Complete

### Marketing Routes (Standalone)
Public marketing pages.

- `/landing` - Landing Page
- `/blog` - Blog
- `/company` - Company Info
- `/pricing` - Pricing Plans

### Demo Routes (Standalone)
Demo and presentation pages.

- `/demo/presentation` - Investor Presentation

## Usage

### Importing Routes

```typescript
import { AppRouter } from '@/router'
import { routes, ROUTES, getRoutesByCategory } from '@/router/routes'
```

### Navigating to Routes

```typescript
import { useNavigate } from 'react-router-dom'
import { ROUTES } from '@/router/routes'

function MyComponent() {
  const navigate = useNavigate()

  // Type-safe navigation
  navigate(ROUTES.ROAS)
  navigate(ROUTES.PRO_EDITOR)
  navigate(ROUTES.AB_TESTING)
}
```

### Getting Routes by Category

```typescript
import { getRoutesByCategory } from '@/router/routes'

const studioRoutes = getRoutesByCategory('studio')
const analyticsRoutes = getRoutesByCategory('analytics')
```

## Features

- **Lazy Loading** - All components are lazy-loaded for optimal performance
- **Code Splitting** - Automatic code splitting per route
- **TypeScript Support** - Full type safety with route definitions
- **Categorized Routes** - Routes organized by feature category
- **Suspense Boundaries** - Loading states for all routes
- **Error Boundaries** - Error handling wrapped around all routes
- **Dashboard Layout** - Automatic layout wrapping for dashboard routes
- **Standalone Routes** - Auth, onboarding, and marketing routes without layout

## Layout Structure

### Dashboard Layout Routes
Routes wrapped in `<DashboardLayout>` include:
- Sidebar navigation
- Header with user menu
- Breadcrumbs
- Toast notifications

### Standalone Routes
Routes without dashboard layout include:
- Auth pages (login, register, verify)
- Onboarding flow
- Marketing pages
- Demo presentations

## Route Params

Some routes accept dynamic parameters:

- `/campaigns/:id` - Campaign ID
- `/studio/:projectId` - Studio project ID
- `/studio/pro/:projectId` - Pro editor project ID

## Protected Routes

All dashboard routes should be protected by authentication. The `DashboardLayout` component handles auth checking.

## Next Steps

To add a new route:

1. Create your component in the appropriate directory
2. Add the route definition to `routes.ts`
3. Import and add the lazy-loaded component to `index.tsx`
4. Add the route to the appropriate section in `<Routes>`

## Testing Routes

You can test all routes by navigating to them in your browser:

```bash
# Dashboard routes
http://localhost:5173/
http://localhost:5173/dashboard/creator

# Analytics routes
http://localhost:5173/analytics/roas
http://localhost:5173/reports

# Studio routes
http://localhost:5173/studio/pro
http://localhost:5173/studio/ai

# Tool routes
http://localhost:5173/spy/dashboard
http://localhost:5173/assistant

# Workflow routes
http://localhost:5173/testing
http://localhost:5173/workflow
```

## Notes

- All 32 previously hidden components are now accessible
- Routes use React Router v6 syntax
- Proper TypeScript types for all route configurations
- Lazy loading ensures optimal bundle size
- Organized route structure for maintainability
