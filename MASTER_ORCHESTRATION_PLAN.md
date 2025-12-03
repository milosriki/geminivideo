# GEMINI VIDEO - MASTER ORCHESTRATION PLAN

## Executive Summary

**Project Status: ~65% Complete**
- Frontend: 85% (polished, needs integration)
- Backend Services: 70% (structure complete, some stubs)
- Database Layer: 90% (async SQLAlchemy implemented)
- AI/ML Pipeline: 40% (mocks need real implementation)
- Meta Integration: 30% (stubs only)
- UI Polish: 75% (dark theme consistent, needs final touches)

---

## PART 1: WHAT'S DONE (Detailed Inventory)

### Frontend Components (24 Total)

| Component | Status | Quality | Notes |
|-----------|--------|---------|-------|
| **HomeDashboard** | ✅ Complete | ⭐⭐⭐⭐⭐ | New Command Center with metrics |
| **MetricCard** | ✅ Complete | ⭐⭐⭐⭐⭐ | Animated counters, sparklines |
| **PerformanceChart** | ✅ Complete | ⭐⭐⭐⭐⭐ | Recharts with gradient fill |
| **RecentActivity** | ✅ Complete | ⭐⭐⭐⭐⭐ | Activity feed with icons |
| **QuickActions** | ✅ Complete | ⭐⭐⭐⭐⭐ | Action grid with hover effects |
| **AIInsights** | ✅ Complete | ⭐⭐⭐⭐⭐ | AI recommendations panel |
| **CreatorDashboard** | ✅ Complete | ⭐⭐⭐⭐⭐ | Tool sidebar navigation |
| **AdWorkflow** | ✅ Complete | ⭐⭐⭐⭐⭐ | Full ad creation pipeline |
| **VideoEditor** | ✅ Complete | ⭐⭐⭐⭐ | FFmpeg-based rendering |
| **AdvancedEditor** | ✅ Complete | ⭐⭐⭐⭐⭐ | 11 edit operations + AI commands |
| **AudioCutterDashboard** | ✅ Complete | ⭐⭐⭐⭐ | Silence detection & keyword cuts |
| **VideoGenerator** | ✅ Complete | ⭐⭐⭐⭐ | Gemini Veo integration |
| **ImageSuite** | ✅ Complete | ⭐⭐⭐⭐ | Generate/Edit/Analyze |
| **AudioSuite** | ✅ Complete | ⭐⭐⭐⭐ | TTS + Transcription |
| **StoryboardStudio** | ✅ Complete | ⭐⭐⭐⭐ | Visual storyboard generation |
| **Assistant** | ✅ Complete | ⭐⭐⭐⭐⭐ | Chat + Voice with Gemini Live |
| **AnalysisPanel** | ⚠️ Mock Data | ⭐⭐⭐ | Hardcoded sample scenes |
| **CompliancePanel** | ⚠️ Stub | ⭐⭐⭐ | All data hardcoded |
| **DiversificationDashboard** | ✅ Complete | ⭐⭐⭐⭐ | Diversity metrics |
| **ReliabilityChart** | ✅ Complete | ⭐⭐⭐⭐ | Prediction accuracy |
| **RenderJobPanel** | ✅ Complete | ⭐⭐⭐⭐ | Job creation & monitoring |
| **PerformanceDashboard** | ✅ Complete | ⭐⭐⭐⭐⭐ | React Query + live data |
| **AssetsPanel** | ✅ Complete | ⭐⭐⭐ | Basic asset list |
| **ErrorBoundary** | ✅ Complete | ⭐⭐⭐⭐ | Error handling |

### Backend Services (6 Total)

| Service | Port | Status | Completeness |
|---------|------|--------|--------------|
| **gateway-api** | 8080 | ✅ Complete | 20+ endpoints, scoring engine |
| **drive-intel** | 8081 | ✅ Mostly | Scene detection, YOLO, embeddings |
| **video-agent** | 8082 | ✅ Complete | FFmpeg rendering pipeline |
| **ml-service** | 8003 | ✅ Complete | XGBoost + Thompson Sampling |
| **meta-publisher** | 8083 | ⚠️ Stub | Facebook SDK structure only |
| **titan-core** | 8084 | ⚠️ Partial | CLI only, no HTTP API |

### Database Layer

| Component | Status | Notes |
|-----------|--------|-------|
| **SQLAlchemy Models** | ✅ Complete | Campaign, Video, Scene, PerformanceMetric, AuditLog |
| **Async Connection** | ✅ Complete | asyncpg driver |
| **Schema SQL** | ✅ Complete | Full DDL |
| **Config Files** | ✅ Complete | 6 YAML/JSON configs |

---

## PART 2: WHAT'S MISSING (Gap Analysis)

### Critical Gaps (Must Fix)

| Gap | Impact | Effort | Priority |
|-----|--------|--------|----------|
| **App.tsx doesn't use HomeDashboard** | Home route broken | 5 min | P0 |
| **No routing system** | Single-page only | 30 min | P0 |
| **Meta SDK not connected** | Can't publish ads | 2 hrs | P1 |
| **Google Drive API stubbed** | Can't ingest from Drive | 1 hr | P1 |
| **titan-core has no HTTP API** | AI orchestration inaccessible | 1 hr | P1 |
| **Frontend not calling real APIs** | Mock data everywhere | 2 hrs | P1 |

### UI/UX Gaps

| Gap | Impact | Effort |
|-----|--------|--------|
| **No navigation between dashboards** | User stuck on one view | 1 hr |
| **App.tsx uses old tab system** | Not using new components | 30 min |
| **No loading states in some panels** | Poor UX | 30 min |
| **Mobile responsiveness incomplete** | Bad mobile experience | 1 hr |
| **No toast notifications** | No user feedback | 30 min |

### Integration Gaps

| Gap | Current State | Target State |
|-----|---------------|--------------|
| **HomeDashboard metrics** | Mock data | Real API calls |
| **RecentActivity** | Mock activities | Real activity log |
| **AIInsights** | Mock insights | Gemini-generated insights |
| **QuickActions routes** | Console.log | React Router navigation |
| **PerformanceChart** | Mock 7-day data | Real analytics API |

---

## PART 3: ULTIMATE ORCHESTRATION PLAN

### Phase 1: Foundation (4 Agents in Parallel) - 30 min

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: FOUNDATION                               │
│                    (Run ALL 4 in Parallel)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  AGENT 1                    AGENT 2                                 │
│  ┌─────────────┐           ┌─────────────┐                         │
│  │ ROUTER      │           │ APP LAYOUT  │                         │
│  │ SETUP       │           │ INTEGRATION │                         │
│  ├─────────────┤           ├─────────────┤                         │
│  │ • Install   │           │ • Update    │                         │
│  │   react-    │           │   App.tsx   │                         │
│  │   router-dom│           │ • Add       │                         │
│  │ • Create    │           │   sidebar   │                         │
│  │   routes.tsx│           │ • Integrate │                         │
│  │ • Define    │           │   Home      │                         │
│  │   all paths │           │   Dashboard │                         │
│  └─────────────┘           └─────────────┘                         │
│                                                                      │
│  AGENT 3                    AGENT 4                                 │
│  ┌─────────────┐           ┌─────────────┐                         │
│  │ API CLIENT  │           │ SHARED      │                         │
│  │ ENHANCEMENT │           │ STATE       │                         │
│  ├─────────────┤           ├─────────────┤                         │
│  │ • Expand    │           │ • Create    │                         │
│  │   titan_    │           │   context/  │                         │
│  │   client.ts │           │   store     │                         │
│  │ • Add all   │           │ • User      │                         │
│  │   endpoints │           │   session   │                         │
│  │ • Error     │           │ • Global    │                         │
│  │   handling  │           │   settings  │                         │
│  └─────────────┘           └─────────────┘                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 2: Backend Integration (6 Agents in Parallel) - 45 min

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 2: BACKEND INTEGRATION                      │
│                    (Run ALL 6 in Parallel)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  AGENT 5              AGENT 6              AGENT 7                  │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐              │
│  │ TITAN    │        │ META     │        │ GOOGLE   │              │
│  │ CORE API │        │ PUBLISHER│        │ DRIVE    │              │
│  ├──────────┤        ├──────────┤        ├──────────┤              │
│  │ • Add    │        │ • Real   │        │ • OAuth  │              │
│  │   FastAPI│        │   FB SDK │        │   2.0    │              │
│  │   routes │        │   calls  │        │ • File   │              │
│  │ • Expose │        │ • Campaign│        │   picker │              │
│  │   orches-│        │   create │        │ • Folder │              │
│  │   trator │        │ • Publish│        │   sync   │              │
│  └──────────┘        └──────────┘        └──────────┘              │
│                                                                      │
│  AGENT 8              AGENT 9              AGENT 10                 │
│  ┌──────────┐        ┌──────────┐        ┌──────────┐              │
│  │ METRICS  │        │ ACTIVITY │        │ INSIGHTS │              │
│  │ API      │        │ LOGGER   │        │ ENGINE   │              │
│  ├──────────┤        ├──────────┤        ├──────────┤              │
│  │ • Real   │        │ • Event  │        │ • Gemini │              │
│  │   metrics│        │   sourcing│        │   analyze│              │
│  │   from DB│        │ • Audit  │        │ • Pattern│              │
│  │ • ROAS   │        │   log    │        │   detect │              │
│  │   calc   │        │   query  │        │ • Suggest│              │
│  └──────────┘        └──────────┘        └──────────┘              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 3: Frontend Polish (8 Agents in Parallel) - 45 min

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 3: FRONTEND POLISH                          │
│                    (Run ALL 8 in Parallel)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  AGENT 11       AGENT 12       AGENT 13       AGENT 14              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐             │
│  │ HOME    │   │ CAMPAIGN│   │ VIDEO   │   │ ANALYTICS│             │
│  │ CONNECT │   │ PAGE    │   │ LIBRARY │   │ ENHANCE │             │
│  ├─────────┤   ├─────────┤   ├─────────┤   ├─────────┤             │
│  │ • Wire  │   │ • New   │   │ • Grid  │   │ • More  │             │
│  │   real  │   │   campaign│   │   view  │   │   charts│             │
│  │   APIs  │   │   wizard │   │ • Filters│   │ • Export│             │
│  │ • Live  │   │ • Budget │   │ • Search│   │   reports│             │
│  │   refresh│   │   setup │   │ • Tags  │   │ • Date  │             │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘             │
│                                                                      │
│  AGENT 15       AGENT 16       AGENT 17       AGENT 18              │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐             │
│  │ TOAST   │   │ LOADING │   │ MOBILE  │   │ THEME   │             │
│  │ SYSTEM  │   │ STATES  │   │ OPTIMIZE│   │ POLISH  │             │
│  ├─────────┤   ├─────────┤   ├─────────┤   ├─────────┤             │
│  │ • Toast │   │ • Skeleton│   │ • Touch │   │ • Color │             │
│  │   provider│   │   loaders│   │   targets│   │   consistency│             │
│  │ • Success│   │ • Suspense│   │ • Bottom│   │ • Hover │             │
│  │   /error │   │   fallback│   │   nav   │   │   states│             │
│  │ • Queue │   │ • Progress│   │ • Swipe │   │ • Focus │             │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 4: Final Integration (4 Agents in Parallel) - 30 min

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PHASE 4: FINAL INTEGRATION                        │
│                    (Run ALL 4 in Parallel)                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  AGENT 19              AGENT 20                                     │
│  ┌─────────────┐      ┌─────────────┐                              │
│  │ E2E TESTING │      │ DOCKER      │                              │
│  │             │      │ COMPOSE     │                              │
│  ├─────────────┤      ├─────────────┤                              │
│  │ • API tests │      │ • Update    │                              │
│  │ • UI tests  │      │   services  │                              │
│  │ • Flow tests│      │ • Health    │                              │
│  │ • Fix bugs  │      │   checks    │                              │
│  └─────────────┘      └─────────────┘                              │
│                                                                      │
│  AGENT 21              AGENT 22                                     │
│  ┌─────────────┐      ┌─────────────┐                              │
│  │ DOCS UPDATE │      │ CLEANUP     │                              │
│  │             │      │ & LINT      │                              │
│  ├─────────────┤      ├─────────────┤                              │
│  │ • README    │      │ • Remove    │                              │
│  │ • API docs  │      │   dead code │                              │
│  │ • Setup     │      │ • Fix lint  │                              │
│  │   guide     │      │ • Types     │                              │
│  └─────────────┘      └─────────────┘                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART 4: UI SYNCHRONIZATION STRATEGY

### Navigation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         APP SHELL                                    │
├─────────────┬───────────────────────────────────────────────────────┤
│             │                                                        │
│  SIDEBAR    │              MAIN CONTENT AREA                        │
│             │                                                        │
│  ┌───────┐  │  ┌─────────────────────────────────────────────────┐ │
│  │ 🏠    │  │  │                                                  │ │
│  │ Home  │──┼──│►  HomeDashboard (/)                             │ │
│  └───────┘  │  │   • Metrics • Chart • Activity • Insights       │ │
│             │  └─────────────────────────────────────────────────┘ │
│  ┌───────┐  │                                                        │
│  │ 📊    │  │  ┌─────────────────────────────────────────────────┐ │
│  │Campaign│──┼──│►  CampaignDashboard (/campaigns)               │ │
│  └───────┘  │  │   • List • Create • Edit • Analytics            │ │
│             │  └─────────────────────────────────────────────────┘ │
│  ┌───────┐  │                                                        │
│  │ 🎬    │  │  ┌─────────────────────────────────────────────────┐ │
│  │ Create│──┼──│►  CreatorDashboard (/create)                    │ │
│  └───────┘  │  │   • AdWorkflow • Video • Image • Audio          │ │
│             │  └─────────────────────────────────────────────────┘ │
│  ┌───────┐  │                                                        │
│  │ 📁    │  │  ┌─────────────────────────────────────────────────┐ │
│  │ Assets│──┼──│►  AssetsPage (/assets)                          │ │
│  └───────┘  │  │   • Upload • Browse • Search • Tags             │ │
│             │  └─────────────────────────────────────────────────┘ │
│  ┌───────┐  │                                                        │
│  │ 📈    │  │  ┌─────────────────────────────────────────────────┐ │
│  │Analytics──┼──│►  AnalyticsPage (/analytics)                   │ │
│  └───────┘  │  │   • Performance • Reliability • Diversification │ │
│             │  └─────────────────────────────────────────────────┘ │
│  ┌───────┐  │                                                        │
│  │ ⚙️    │  │  ┌─────────────────────────────────────────────────┐ │
│  │Settings│──┼──│►  SettingsPage (/settings)                     │ │
│  └───────┘  │  │   • API Keys • Integrations • Preferences       │ │
│             │  └─────────────────────────────────────────────────┘ │
└─────────────┴───────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
App
├── AppShell (Layout)
│   ├── Sidebar
│   │   ├── Logo
│   │   ├── NavItems
│   │   └── UserMenu
│   ├── TopBar
│   │   ├── Breadcrumbs
│   │   ├── SearchBar
│   │   └── QuickActions
│   └── MainContent
│       └── <Outlet /> (React Router)
│
├── Routes
│   ├── / → HomeDashboard
│   │   ├── MetricCards (4x)
│   │   ├── PerformanceChart
│   │   ├── RecentActivity
│   │   ├── QuickActions
│   │   └── AIInsights
│   │
│   ├── /campaigns → CampaignDashboard
│   │   ├── CampaignList
│   │   ├── CampaignCard
│   │   └── CampaignFilters
│   │
│   ├── /create → CreatorDashboard
│   │   ├── ToolSidebar
│   │   └── ActiveTool
│   │       ├── AdWorkflow
│   │       ├── VideoGenerator
│   │       ├── ImageSuite
│   │       ├── AudioSuite
│   │       ├── StoryboardStudio
│   │       └── Assistant
│   │
│   ├── /assets → AssetsPage
│   │   ├── AssetGrid
│   │   ├── AssetFilters
│   │   └── AssetUploader
│   │
│   ├── /analytics → AnalyticsPage
│   │   ├── PerformanceDashboard
│   │   ├── ReliabilityChart
│   │   ├── DiversificationDashboard
│   │   └── CompliancePanel
│   │
│   └── /settings → SettingsPage
│       ├── APIKeyManager
│       ├── IntegrationSettings
│       └── PreferencesForm
│
└── Global
    ├── ToastProvider
    ├── QueryClientProvider
    ├── ErrorBoundary
    └── LoadingOverlay
```

### State Management Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│                      STATE ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    REACT QUERY (Server State)                │   │
│  │                                                               │   │
│  │  • Campaigns List      useQuery('campaigns')                 │   │
│  │  • Metrics             useQuery('metrics', { days })         │   │
│  │  • Activity Feed       useQuery('activity', { limit })       │   │
│  │  • AI Insights         useQuery('insights')                  │   │
│  │  • Assets              useQuery('assets')                    │   │
│  │  • Analytics           useQuery('analytics', { range })      │   │
│  │                                                               │   │
│  │  Auto-refetch: 30s for metrics, 60s for others               │   │
│  │  Stale time: 10s                                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    REACT CONTEXT (UI State)                  │   │
│  │                                                               │   │
│  │  • ThemeContext        { theme, setTheme }                   │   │
│  │  • SidebarContext      { collapsed, toggle }                 │   │
│  │  • ToastContext        { toasts, addToast, removeToast }     │   │
│  │  • UserContext         { user, apiKeys, settings }           │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    LOCAL STATE (Component)                   │   │
│  │                                                               │   │
│  │  • Form inputs         useState()                            │   │
│  │  • Modal open/close    useState()                            │   │
│  │  • Tab selection       useState()                            │   │
│  │  • Dropdown menus      useState()                            │   │
│  │                                                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART 5: IMMEDIATE ACTION ITEMS

### Quick Wins (Can Do Now)

1. **Update App.tsx** to use HomeDashboard as default route
2. **Add react-router-dom** for proper navigation
3. **Wire QuickActions** to actual routes
4. **Connect HomeDashboard metrics** to titan_client API
5. **Add toast notifications** for user feedback

### Agent Assignment Matrix

| Agent | Task | Dependencies | Output |
|-------|------|--------------|--------|
| 1 | Router Setup | None | routes.tsx |
| 2 | App Layout | Agent 1 | Updated App.tsx |
| 3 | API Client | None | titan_client.ts |
| 4 | State Management | None | contexts/*.tsx |
| 5 | Titan Core HTTP | None | FastAPI routes |
| 6 | Meta Publisher | None | Real SDK calls |
| 7 | Google Drive | None | OAuth flow |
| 8 | Metrics API | Agent 5 | Real data endpoints |
| 9 | Activity Logger | Agent 5 | Event sourcing |
| 10 | Insights Engine | Agent 5 | AI analysis |
| 11 | Home Connect | Agents 3,8,9,10 | Wired HomeDashboard |
| 12 | Campaign Page | Agents 1,3,6 | New campaign wizard |
| 13 | Video Library | Agents 1,3 | Asset management |
| 14 | Analytics Enhance | Agents 3,8 | Full analytics |
| 15 | Toast System | None | Toast provider |
| 16 | Loading States | None | Skeleton loaders |
| 17 | Mobile Optimize | Agent 2 | Responsive fixes |
| 18 | Theme Polish | None | Visual consistency |
| 19 | E2E Testing | All above | Test suite |
| 20 | Docker Update | All services | docker-compose.yml |
| 21 | Documentation | All above | Updated docs |
| 22 | Cleanup | All above | Linted code |

---

## PART 6: ESTIMATED TIMELINE

```
TIME        PHASE           AGENTS    STATUS
────────────────────────────────────────────────
0:00        Start           -         Begin
0:00-0:30   Foundation      1-4       Parallel
0:30-1:15   Backend         5-10      Parallel
1:15-2:00   Frontend        11-18     Parallel
2:00-2:30   Integration     19-22     Parallel
────────────────────────────────────────────────
TOTAL: 2.5 hours to 100% completion
```

---

## PART 7: SUCCESS CRITERIA

### Functional Requirements
- [ ] Home dashboard shows real metrics from API
- [ ] Navigation works between all pages
- [ ] Campaigns can be created and published to Meta
- [ ] Videos can be ingested from Google Drive
- [ ] AI insights are generated dynamically
- [ ] Activity feed shows real events
- [ ] All editors (Video, Image, Audio) functional
- [ ] Toast notifications for all actions

### Quality Requirements
- [ ] No TypeScript errors
- [ ] ESLint passes
- [ ] All components responsive (mobile + desktop)
- [ ] Loading states for all async operations
- [ ] Error boundaries catch failures gracefully
- [ ] Consistent dark theme across all pages

### Performance Requirements
- [ ] Initial load < 3 seconds
- [ ] Route transitions < 200ms
- [ ] API calls cached appropriately
- [ ] No layout shift on data load

---

## CONCLUSION

The GeminiVideo project has a **solid foundation** with 65% completion. The frontend components are well-built and styled. The main gaps are:

1. **Integration** - Components exist but aren't connected
2. **Routing** - No navigation between features
3. **Real APIs** - Mock data instead of live data
4. **Meta/Drive** - Stubs instead of real SDKs

With **22 parallel agents** working in **4 phases**, the project can reach **100% completion in ~2.5 hours**.

The key is **parallel execution** - most tasks have no dependencies and can run simultaneously.
