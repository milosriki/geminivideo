# 🏆 GEMINIVIDEO MASTER PLAN
## From Current State → Top-Grade Production Dashboard
### Rivaling Foreplay.co + Creatify.ai

---

## 📊 CURRENT STATE vs TARGET STATE

| Aspect | Current (Today) | Target (Top-Grade) |
|--------|-----------------|-------------------|
| **UI Components** | Basic, oversized | Catalyst professional |
| **Navigation** | Tab-based, broken | Sidebar + nested routes |
| **Routing** | No React Router | Full lazy-loaded routes |
| **Theme** | Inconsistent | Dark theme system |
| **Animations** | None | Framer Motion micro-interactions |
| **Data Layer** | Mock data | React Query + real APIs |
| **State** | Scattered useState | Zustand stores |
| **Forms** | Basic inputs | Catalyst forms + validation |
| **Tables** | None | Sortable, filterable, paginated |
| **Charts** | None | Recharts/Tremor dashboards |
| **Video Player** | Basic | Compass-style with PiP |
| **Mobile** | Broken | Fully responsive |

---

## 🎯 THE 8-PHASE MASTER PLAN

### PHASE 1: FOUNDATION (Days 1-2)
**Goal:** Professional app shell with Catalyst

#### Tasks:
1. ✅ Copy Catalyst components to project
2. ✅ Install dependencies (@headlessui/react, motion, clsx)
3. Create DashboardLayout with SidebarLayout
4. Setup React Router with all routes
5. Create base pages (empty shells)
6. Dark theme configuration

#### Deliverables:
- Working sidebar navigation
- All routes accessible
- Professional dark theme
- No TypeScript errors

#### Claude Code Prompt:
```
PHASE 1: Setup Catalyst Foundation

1. Verify Catalyst components in src/components/catalyst/
2. Create index.ts exporting all components
3. Create DashboardLayout.tsx using SidebarLayout:
   - Logo: GeminiVideo
   - Navigation: Home, Create, Projects, Assets, Analytics, Spy, Settings
   - User profile dropdown
   - Dark theme
4. Update App.tsx with React Router
5. Create empty page shells for all routes
6. Test navigation works

Output all files. No placeholders.
```

---

### PHASE 2: HOME DASHBOARD (Days 3-4)
**Goal:** Command Center like Foreplay/Creatify home

#### Features:
- **Welcome Header** - User name, date, quick actions
- **Metrics Row** - 4-6 KPI cards with trends
- **Performance Chart** - 7-day ROAS/views trend
- **Recent Activity** - Feed of latest actions
- **Quick Actions** - New Campaign, Generate Video, Analyze
- **AI Insights** - Recommendations panel
- **Pending Jobs** - Queue status

#### Components to Build:
```
src/components/dashboard/
├── MetricCard.tsx        # Animated count-up, trend badge
├── PerformanceChart.tsx  # Recharts line/area chart
├── RecentActivity.tsx    # Activity feed list
├── QuickActions.tsx      # Action button grid
├── AIInsights.tsx        # Recommendation cards
├── PendingJobs.tsx       # Job queue status
└── index.ts
```

#### Claude Code Prompt:
```
PHASE 2: Build Command Center Home Dashboard

Using Catalyst components, create professional home dashboard:

1. src/pages/HomePage.tsx - Main dashboard page
2. src/components/dashboard/MetricCard.tsx:
   - Props: label, value, change, trend, icon
   - Animated count-up on mount (use motion)
   - Trend arrow (green up, red down)
   - Click to drill down
   
3. src/components/dashboard/PerformanceChart.tsx:
   - 7-day line chart using Recharts
   - Dark theme styling
   - Tooltip on hover
   - Gradient fill under line
   
4. src/components/dashboard/RecentActivity.tsx:
   - Activity feed using Catalyst DescriptionList
   - Icons for each activity type
   - Relative timestamps
   - "View all" link
   
5. src/components/dashboard/QuickActions.tsx:
   - Grid of action buttons
   - Icons + labels
   - Hover effects
   - Links to create pages
   
6. Layout:
   - 4-column metric cards row
   - 2-column main (chart + activity)
   - Sidebar for insights

Install recharts: npm install recharts
Use mock data for now.
Dark theme. Animations. Production quality.
```

---

### PHASE 3: CAMPAIGN BUILDER (Days 5-7)
**Goal:** 3-Step wizard like Creatify

#### Flow:
```
Step 1: SETUP          Step 2: AI CREATIVE      Step 3: REVIEW
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Campaign Name   │ →  │ Upload Videos   │ →  │ Preview Ads     │
│ Objective       │    │ Select Style    │    │ Edit/Regenerate │
│ Budget          │    │ Script Template │    │ Schedule/Launch │
│ Platform        │    │ Avatar Choice   │    │ A/B Test Setup  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

#### Components:
```
src/components/campaign/
├── CampaignWizard.tsx     # Main wizard container
├── WizardProgress.tsx     # Step indicator
├── SetupStep.tsx          # Step 1 form
├── CreativeStep.tsx       # Step 2 AI options
├── ReviewStep.tsx         # Step 3 preview
├── CampaignPreview.tsx    # Ad preview card
└── index.ts
```

#### Claude Code Prompt:
```
PHASE 3: Build Campaign Creation Wizard

Create 3-step campaign wizard using Catalyst forms:

1. src/pages/campaigns/NewCampaignPage.tsx - Wizard container
2. src/components/campaign/WizardProgress.tsx:
   - 3 steps with labels
   - Current step highlighted
   - Completed steps checked
   - Clickable to go back

3. src/components/campaign/SetupStep.tsx:
   Using Catalyst: Input, Select, Fieldset, Field, Label
   - Campaign name (Input)
   - Objective (Select: Conversions, Traffic, Awareness)
   - Budget (Input type=number with currency)
   - Platform (Checkbox group: Meta, TikTok, YouTube)
   - Target audience (Select)
   - Validate before next

4. src/components/campaign/CreativeStep.tsx:
   - File upload zone (drag & drop)
   - Style selector (radio cards: UGC, Professional, Mixed)
   - Script template (Select)
   - Hook style (Select)
   - Number of variants (Slider or number input)
   - AI avatar selection (grid of avatar thumbnails)

5. src/components/campaign/ReviewStep.tsx:
   - Summary of all selections
   - Preview cards of generated ads (mock)
   - Edit buttons to go back
   - Schedule date picker
   - Launch button

6. State management:
   - Zustand store for campaign data
   - Persist between steps
   - Save draft functionality

Use Catalyst components throughout.
Dark theme. Smooth step transitions with motion.
```

---

### PHASE 4: AD LIBRARY & SPY (Days 8-10)
**Goal:** Foreplay-style swipe file + competitor research

#### Features:
- **Masonry Grid** - Pinterest-style ad cards
- **Filters** - Platform, style, date, performance
- **Boards/Folders** - Organize saved ads
- **Ad Detail Modal** - Full analysis
- **Competitor Tracking** - Monitor accounts
- **Trending Ads** - Discover viral creatives

#### Components:
```
src/components/library/
├── AdCard.tsx           # Ad thumbnail with overlay
├── AdGrid.tsx           # Masonry layout
├── FilterBar.tsx        # Filter chips + search
├── AdDetailModal.tsx    # Full ad analysis
├── BoardSelector.tsx    # Save to board
├── CompetitorCard.tsx   # Tracked account
└── index.ts
```

#### Claude Code Prompt:
```
PHASE 4: Build Ad Library & Spy Dashboard

Create Foreplay-style ad library using Catalyst:

1. src/pages/AssetsPage.tsx - Main library page
2. src/pages/AdSpyPage.tsx - Competitor research

3. src/components/library/AdCard.tsx:
   - Video/image thumbnail (aspect-video)
   - Overlay on hover with:
     - Platform badge (Meta, TikTok)
     - View count
     - Save to board button
     - Quick actions (analyze, copy, edit)
   - Click opens detail modal

4. src/components/library/AdGrid.tsx:
   - Masonry layout using CSS columns
   - Responsive: 2 cols mobile, 3 tablet, 4 desktop
   - Infinite scroll or pagination
   - Loading skeletons

5. src/components/library/FilterBar.tsx:
   - Search input
   - Filter chips (Platform, Style, Date range)
   - Sort dropdown (Recent, Popular, Performance)
   - View toggle (Grid/List)
   - Using Catalyst: Input, Select, Badge, Button

6. src/components/library/AdDetailModal.tsx:
   - Using Catalyst Dialog
   - Large video preview
   - Transcript panel
   - Hook analysis
   - Performance metrics
   - Copy to campaign button
   - Save to board selector

7. src/components/library/BoardSelector.tsx:
   - Dropdown of existing boards
   - Create new board option
   - Using Catalyst Listbox

Dark theme. Smooth animations. Real swipe-file UX.
```

---

### PHASE 5: VIDEO STUDIO (Days 11-13)
**Goal:** Pro video editor like Creatify studio

#### Features:
- **Timeline Editor** - Clip arrangement
- **Preview Player** - Real-time preview
- **Script Editor** - AI-assisted writing
- **Avatar Gallery** - Select talking heads
- **Style Presets** - Quick looks
- **Export Options** - Quality, format

#### Components:
```
src/components/studio/
├── VideoEditor.tsx       # Main editor container
├── Timeline.tsx          # Clip timeline
├── PreviewPlayer.tsx     # Video preview
├── ScriptEditor.tsx      # Text editor
├── AvatarGallery.tsx     # Avatar selection
├── StylePresets.tsx      # Visual presets
├── ExportPanel.tsx       # Export options
└── index.ts
```

#### Claude Code Prompt:
```
PHASE 5: Build Video Studio

Create Creatify-style video studio:

1. src/pages/studio/StudioPage.tsx - Main editor layout
   Layout:
   ┌─────────────────────────────────────────┐
   │ Toolbar                                 │
   ├───────────────────┬─────────────────────┤
   │                   │ Script / Settings   │
   │   Preview         │ Panel               │
   │   Player          │                     │
   │                   │                     │
   ├───────────────────┴─────────────────────┤
   │ Timeline                                │
   └─────────────────────────────────────────┘

2. src/components/studio/PreviewPlayer.tsx:
   - Video element with custom controls
   - Play/pause, seek, volume
   - Fullscreen toggle
   - Speed control
   - Dark themed controls

3. src/components/studio/Timeline.tsx:
   - Horizontal scrollable track
   - Clip thumbnails
   - Drag to reorder (use @dnd-kit)
   - Trim handles
   - Playhead indicator

4. src/components/studio/ScriptEditor.tsx:
   - Rich text editor (use Catalyst Textarea base)
   - AI suggestion button
   - Character count
   - Variable tokens (product name, price)
   - Scene markers

5. src/components/studio/AvatarGallery.tsx:
   - Grid of avatar thumbnails
   - Category filters (Male, Female, UGC, Pro)
   - Preview on hover
   - Selection state

6. src/components/studio/ExportPanel.tsx:
   - Resolution select (1080p, 720p, 4K)
   - Format select (MP4, MOV, WebM)
   - Quality slider
   - Estimated file size
   - Export button with progress

Use Catalyst components for all UI.
Dark theme. Smooth interactions.
```

---

### PHASE 6: ANALYTICS DASHBOARD (Days 14-16)
**Goal:** Triple Whale style metrics

#### Features:
- **KPI Overview** - ROAS, Spend, Revenue, CPM
- **Performance Charts** - Multiple metrics over time
- **Campaign Breakdown** - Table with all campaigns
- **Creative Comparison** - A/B test results
- **Funnel Visualization** - Conversion flow
- **Export Reports** - PDF/CSV download

#### Components:
```
src/components/analytics/
├── KPIGrid.tsx          # Main metrics
├── PerformanceCharts.tsx # Multi-line charts
├── CampaignTable.tsx    # Data table
├── CreativeComparison.tsx # Side-by-side
├── FunnelChart.tsx      # Conversion funnel
├── DateRangePicker.tsx  # Period selector
└── index.ts
```

#### Claude Code Prompt:
```
PHASE 6: Build Analytics Dashboard

Create comprehensive analytics using Recharts + Catalyst:

1. Install: npm install recharts date-fns

2. src/pages/AnalyticsPage.tsx - Main analytics page

3. src/components/analytics/DateRangePicker.tsx:
   - Preset options (Today, 7 days, 30 days, Custom)
   - Calendar popup for custom range
   - Compare to previous period toggle

4. src/components/analytics/KPIGrid.tsx:
   - 6 KPI cards in 2 rows
   - ROAS, Revenue, Spend, Impressions, Clicks, Conversions
   - Each with sparkline trend
   - vs previous period comparison

5. src/components/analytics/PerformanceCharts.tsx:
   - Multi-metric line chart
   - Toggle metrics on/off
   - Hover tooltip with all values
   - Zoom/pan for date ranges

6. src/components/analytics/CampaignTable.tsx:
   - Using Catalyst Table
   - Columns: Campaign, Status, Spend, Revenue, ROAS, Conversions
   - Sortable columns (click header)
   - Filter by status
   - Pagination
   - Row click → detail view

7. src/components/analytics/CreativeComparison.tsx:
   - Side-by-side video previews
   - Metric comparison bars
   - Winner indicator
   - Statistical significance badge

8. src/components/analytics/FunnelChart.tsx:
   - Vertical funnel: Impressions → Clicks → Leads → Sales
   - Conversion rates between steps
   - Drop-off indicators

All charts dark themed. Responsive. Animated on load.
```

---

### PHASE 7: REAL-TIME & NOTIFICATIONS (Days 17-18)
**Goal:** Live updates + progress tracking

#### Features:
- **Job Queue** - Real-time generation status
- **Toast Notifications** - Success/error alerts
- **Live Metrics** - Auto-updating numbers
- **WebSocket Connection** - Real-time data
- **Push Notifications** - Browser alerts

#### Components:
```
src/components/realtime/
├── JobQueue.tsx          # Generation queue
├── JobProgress.tsx       # Individual job progress
├── ToastProvider.tsx     # Notification system
├── LiveMetric.tsx        # Auto-updating number
├── ConnectionStatus.tsx  # Online/offline indicator
└── index.ts
```

#### Claude Code Prompt:
```
PHASE 7: Build Real-Time Features

Create real-time updates and notifications:

1. src/components/realtime/ToastProvider.tsx:
   - Global toast context
   - Toast types: success, error, warning, info
   - Auto-dismiss with progress bar
   - Stack multiple toasts
   - Close button

2. src/components/realtime/JobQueue.tsx:
   - List of pending/active jobs
   - Job types: Generate, Analyze, Render, Publish
   - Status badges using Catalyst Badge
   - Cancel button
   - Estimated time remaining

3. src/components/realtime/JobProgress.tsx:
   - Current step name
   - Progress percentage bar
   - Step breakdown (1/5, 2/5, etc.)
   - Elapsed time
   - Animated progress fill

4. src/components/realtime/LiveMetric.tsx:
   - Number that updates in real-time
   - Flash animation on change
   - Up/down indicator
   - Configurable update interval

5. src/components/realtime/ConnectionStatus.tsx:
   - Green dot when connected
   - Red dot with "Reconnecting..." when offline
   - Tooltip with last sync time

6. src/stores/realtimeStore.ts:
   - Zustand store for job queue
   - WebSocket connection state
   - Active jobs array
   - Add/update/remove job actions

Use Catalyst Badge, Dialog components.
Smooth animations for all state changes.
```

---

### PHASE 8: POLISH & PRODUCTION (Days 19-21)
**Goal:** Final touches for launch

#### Tasks:
1. **Loading States** - Skeleton screens everywhere
2. **Empty States** - Helpful messages + CTAs
3. **Error Handling** - Error boundaries + recovery
4. **Animations** - Page transitions, micro-interactions
5. **Mobile Responsive** - Test all breakpoints
6. **Accessibility** - Keyboard nav, ARIA labels
7. **Performance** - Code splitting, lazy loading
8. **SEO/Meta** - Page titles, descriptions

#### Claude Code Prompt:
```
PHASE 8: Production Polish

Final touches for top-grade quality:

1. LOADING STATES:
   - Create skeleton variants for all components
   - Full page loader for route changes
   - Button loading states
   - Table skeleton rows
   - Chart loading placeholder

2. EMPTY STATES:
   - No campaigns: "Create your first campaign"
   - No assets: "Upload videos to get started"
   - No analytics: "Launch a campaign to see data"
   - No search results: "Try different keywords"
   - Each with illustration + CTA button

3. ERROR HANDLING:
   - ErrorBoundary wrapper for all pages
   - Network error component with retry
   - 404 page with navigation
   - Form validation errors inline
   - API error toasts

4. ANIMATIONS:
   - Page fade-in transitions
   - Sidebar collapse/expand smooth
   - Card hover lift effect
   - Button press feedback
   - Modal open/close
   - Dropdown reveal
   - Number count-up on load

5. RESPONSIVE:
   - Mobile sidebar as drawer
   - Stack layouts on mobile
   - Touch-friendly tap targets
   - Bottom nav for mobile?

6. ACCESSIBILITY:
   - Focus visible outlines
   - Keyboard navigation
   - Screen reader labels
   - Color contrast check
   - Reduced motion support

7. PERFORMANCE:
   - Lazy load all routes
   - Image optimization
   - Virtualize long lists
   - Debounce search inputs
   - Memoize expensive renders

Test everything. Fix all TypeScript errors. No console warnings.
```

---

## 📅 COMPLETE TIMELINE

| Phase | Days | Deliverables |
|-------|------|--------------|
| 1. Foundation | 1-2 | Catalyst setup, routing, sidebar |
| 2. Home Dashboard | 3-4 | Metrics, charts, activity feed |
| 3. Campaign Builder | 5-7 | 3-step wizard, forms |
| 4. Ad Library/Spy | 8-10 | Masonry grid, filters, boards |
| 5. Video Studio | 11-13 | Editor, timeline, preview |
| 6. Analytics | 14-16 | Charts, tables, comparisons |
| 7. Real-Time | 17-18 | Jobs, notifications, live data |
| 8. Polish | 19-21 | Loading, errors, animations |

**TOTAL: 21 Days / 3 Weeks to Production-Ready**

---

## 🛠️ TECH STACK SUMMARY

```
FRONTEND:
├── React 18 + TypeScript
├── Vite (build tool)
├── React Router v6 (routing)
├── Tailwind CSS v4 (styling)
├── Catalyst UI Kit (components)
├── Headless UI v2 (accessibility)
├── Framer Motion (animations)
├── Recharts (charts)
├── Zustand (state)
├── React Query (data fetching)
├── React Hook Form + Zod (forms)
└── @dnd-kit (drag & drop)

BACKEND (existing):
├── Python Titan Engine (Port 8080)
├── GeminiVideo AI Services
├── Meta Ads MCP
└── PostgreSQL/Supabase
```

---

## 📁 FINAL FOLDER STRUCTURE

```
frontend/src/
├── components/
│   ├── catalyst/           # Catalyst UI components
│   │   ├── button.tsx
│   │   ├── sidebar.tsx
│   │   ├── table.tsx
│   │   └── ... (all 25+ components)
│   ├── dashboard/          # Home dashboard
│   │   ├── MetricCard.tsx
│   │   ├── PerformanceChart.tsx
│   │   └── ...
│   ├── campaign/           # Campaign builder
│   │   ├── CampaignWizard.tsx
│   │   ├── SetupStep.tsx
│   │   └── ...
│   ├── library/            # Ad library
│   │   ├── AdCard.tsx
│   │   ├── AdGrid.tsx
│   │   └── ...
│   ├── studio/             # Video editor
│   │   ├── VideoEditor.tsx
│   │   ├── Timeline.tsx
│   │   └── ...
│   ├── analytics/          # Analytics
│   │   ├── KPIGrid.tsx
│   │   ├── CampaignTable.tsx
│   │   └── ...
│   └── realtime/           # Real-time features
│       ├── JobQueue.tsx
│       ├── ToastProvider.tsx
│       └── ...
├── layouts/
│   ├── DashboardLayout.tsx
│   └── AuthLayout.tsx
├── pages/
│   ├── HomePage.tsx
│   ├── campaigns/
│   ├── studio/
│   ├── analytics/
│   └── settings/
├── stores/
│   ├── uiStore.ts
│   ├── campaignStore.ts
│   ├── analyticsStore.ts
│   └── realtimeStore.ts
├── hooks/
│   ├── useAuth.ts
│   ├── useCampaigns.ts
│   └── useAnalytics.ts
├── lib/
│   ├── api.ts
│   └── utils.ts
├── App.tsx
└── main.tsx
```

---

## ⚡ PARALLEL AGENT STRATEGY

For maximum speed, use multiple Claude Code agents:

### Week 1 (Phases 1-3):
| Agent | Task |
|-------|------|
| Agent 1 | Foundation + Layout |
| Agent 2 | Home Dashboard |
| Agent 3 | Campaign Wizard |

### Week 2 (Phases 4-5):
| Agent | Task |
|-------|------|
| Agent 1 | Ad Library |
| Agent 2 | Ad Spy |
| Agent 3 | Video Studio |

### Week 3 (Phases 6-8):
| Agent | Task |
|-------|------|
| Agent 1 | Analytics |
| Agent 2 | Real-Time |
| Agent 3 | Polish |

**With 3 parallel agents: 21 days → 7-10 days**

---

## 🎯 SUCCESS CRITERIA

Your dashboard is TOP-GRADE when:

✅ Professional dark theme throughout
✅ Smooth animations on all interactions
✅ < 3 second initial load time
✅ All routes lazy-loaded
✅ Zero TypeScript errors
✅ Zero console warnings
✅ Mobile responsive (all breakpoints)
✅ Keyboard navigable
✅ Loading states for all async
✅ Error handling for all failures
✅ Real-time updates working
✅ Forms validate before submit
✅ Tables sort and filter
✅ Charts animate on load
✅ Notifications appear for actions
✅ Users say "This looks better than Foreplay"

---

## 🚀 START NOW

**Step 1:** Copy Catalyst files (Terminal commands above)
**Step 2:** Run Phase 1 Claude Code prompt
**Step 3:** Continue with Phase 2, 3, etc.

Each phase builds on the previous. Don't skip ahead.

**You have everything you need. Let's build! 🔥**
