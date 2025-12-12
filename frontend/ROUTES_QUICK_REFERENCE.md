# Quick Reference: All Available Routes

## Analytics & Business Intelligence
| Route | Component | Description |
|-------|-----------|-------------|
| `/analytics/dashboard` | Analytics Dashboard | Comprehensive analytics with charts |
| `/analytics/performance` | Performance Dashboard | Detailed performance metrics |
| `/analytics/reliability` | Reliability Chart | System reliability tracking |
| `/analytics/diversification` | Diversification Dashboard | Portfolio analysis |
| `/analytics/roas` | ROAS Dashboard | Return on ad spend tracking |
| `/reports` | Reports Generator | Generate PDF/Excel reports |

## Studio & Creative Tools
| Route | Component | Description |
|-------|-----------|-------------|
| `/studio/pro` | Pro Video Editor | Professional video editing suite |
| `/studio/storyboard` | Storyboard Studio | Visual storyboard creator |
| `/studio/video` | Video Studio | Advanced video editing |
| `/studio/ai` | AI Creative Studio | AI-powered creative generation |
| `/studio/generate` | Video Generator | Quick video generation |
| `/studio/audio-mixer` | Audio Mixer Panel | Professional audio mixing |
| `/studio/color-grading` | Color Grading Panel | Advanced color grading |
| `/studio/color-grading-demo` | Color Grading Demo | Color grading demo mode |

## Asset Management
| Route | Component | Description |
|-------|-----------|-------------|
| `/library/assets` | Assets Panel | Advanced asset management |
| `/library/clips` | Ranked Clips Panel | AI-ranked video clips |
| `/library/search` | Semantic Search Panel | AI-powered asset search |

## Intelligence & Analysis
| Route | Component | Description |
|-------|-----------|-------------|
| `/spy/dashboard` | Ad Spy Dashboard | Full competitor intelligence |
| `/analysis` | Analysis Panel | Video and creative analysis |
| `/compliance` | Compliance Panel | Ad compliance checking |
| `/audio` | Audio Suite | Audio tools collection |
| `/audio/suite` | Audio Suite Panel | Advanced audio tools |
| `/image` | Image Suite | Image editing and generation |
| `/assistant` | AI Assistant | AI strategy assistant |
| `/resources` | Resources Page | Tutorials and learning resources |

## Workflow & Testing
| Route | Component | Description |
|-------|-----------|-------------|
| `/testing` | A/B Testing Dashboard | Bayesian A/B testing |
| `/workflow` | Human Workflow Dashboard | Human-in-the-loop approvals |
| `/batch` | Batch Processing Panel | Batch video processing |
| `/render` | Render Jobs Panel | Video render queue |

## Campaign Management
| Route | Component | Description |
|-------|-----------|-------------|
| `/campaigns/builder` | Campaign Builder | Advanced campaign builder |
| `/dashboard/creator` | Creator Dashboard | Creator-focused dashboard |

## Marketing (Public)
| Route | Component | Description |
|-------|-----------|-------------|
| `/landing` | Landing Page | Public marketing landing |

---

## Import Examples

```typescript
// Import route constants
import { ROUTES } from '@/router/routes'

// Navigate to routes
navigate(ROUTES.ROAS)
navigate(ROUTES.PRO_EDITOR)
navigate(ROUTES.AB_TESTING)

// Get routes by category
import { getRoutesByCategory } from '@/router/routes'
const studioRoutes = getRoutesByCategory('studio')
```

## Total Routes: 80+
- **32 Previously Hidden Components** (now accessible)
- **20+ Existing Routes** (from original App.tsx)
- **28 Additional Routes** (auth, onboarding, marketing, variations)

## Categories
- 📊 **Analytics** (6 routes)
- 🎬 **Studio** (8 routes)
- 📦 **Assets** (3 routes)
- 🔍 **Intelligence** (8 routes)
- ⚙️ **Workflow** (4 routes)
- 📢 **Campaigns** (2 routes)
- 🌐 **Marketing** (1 route)
- 🔐 **Auth** (3 routes)
- 👋 **Onboarding** (6 routes)
