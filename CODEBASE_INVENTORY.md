# CODEBASE INVENTORY
## GeminiVideo - AI Marketing SaaS Platform
### Complete Technical Analysis

---

## EXECUTIVE SUMMARY

| Metric | Count | Connected | Orphaned |
|--------|-------|-----------|----------|
| React Components | 40 | 8 (20%) | 32 (80%) |
| API Services | 13 | ~5 | ~8 |
| State Management | 3 | 1 | 2 |
| Total Lines of Code | ~15,000+ | - | - |

**Critical Finding**: 80% of components are orphaned and not accessible in the current UI.

---

## 1. REACT COMPONENTS INVENTORY

### 1.1 CONNECTED COMPONENTS (In App.tsx)

| # | Component | File | Route/Tab | Purpose | Status |
|---|-----------|------|-----------|---------|--------|
| 1 | AssetsPanel | `components/AssetsPanel.tsx` | `/assets` | Asset upload and ingest management | ACTIVE |
| 2 | RankedClipsPanel | `components/RankedClipsPanel.tsx` | `/clips` | AI-ranked video clips display | ACTIVE |
| 3 | SemanticSearchPanel | `components/SemanticSearchPanel.tsx` | `/search` | AI-powered semantic video search | ACTIVE |
| 4 | AnalysisPanel | `components/AnalysisPanel.tsx` | `/analysis` | Video analysis and scoring | ACTIVE |
| 5 | CompliancePanel | `components/CompliancePanel.tsx` | `/compliance` | Ad policy compliance checker | ACTIVE |
| 6 | DiversificationDashboard | `components/DiversificationDashboard.tsx` | `/diversification` | Creative diversification metrics | ACTIVE |
| 7 | ReliabilityChart | `components/ReliabilityChart.tsx` | `/reliability` | System reliability monitoring | ACTIVE |
| 8 | RenderJobPanel | `components/RenderJobPanel.tsx` | `/render` | Video render job management | ACTIVE |

### 1.2 ORPHANED COMPONENTS (Not Connected)

#### Category A: Major Feature Components (HIGH PRIORITY)

| # | Component | File | Intended Purpose | Complexity | Priority |
|---|-----------|------|------------------|------------|----------|
| 1 | **ProVideoEditor** | `components/pro/ProVideoEditor.tsx` | Professional video editing suite with timeline | HIGH | CRITICAL |
| 2 | **CampaignBuilder** | `components/CampaignBuilder.tsx` | End-to-end ad campaign creation wizard | HIGH | CRITICAL |
| 3 | **AnalyticsDashboard** | `components/AnalyticsDashboard.tsx` | Performance metrics and ROAS tracking | HIGH | CRITICAL |
| 4 | **AdSpyDashboard** | `components/AdSpyDashboard.tsx` | Competitor ad intelligence and analysis | HIGH | CRITICAL |
| 5 | **AICreativeStudio** | `components/AICreativeStudio.tsx` | AI-powered creative generation hub | HIGH | CRITICAL |
| 6 | **CreatorDashboard** | `components/CreatorDashboard.tsx` | Main creator workspace and overview | HIGH | CRITICAL |

#### Category B: Studio/Editor Components (MEDIUM-HIGH PRIORITY)

| # | Component | File | Intended Purpose | Complexity |
|---|-----------|------|------------------|------------|
| 7 | **VideoStudio** | `components/VideoStudio.tsx` | Video editing workspace | HIGH |
| 8 | **StoryboardStudio** | `components/StoryboardStudio.tsx` | Visual storyboard creation | MEDIUM |
| 9 | **VideoEditor** | `components/VideoEditor.tsx` | Basic video editing | MEDIUM |
| 10 | **AdvancedEditor** | `components/AdvancedEditor.tsx` | Advanced editing features | MEDIUM |
| 11 | **TimelineCanvas** | `components/pro/TimelineCanvas.tsx` | Video timeline with tracks | HIGH |

#### Category C: Audio Components (MEDIUM PRIORITY)

| # | Component | File | Intended Purpose | Complexity |
|---|-----------|------|------------------|------------|
| 12 | **AudioSuite** | `components/AudioSuite.tsx` | Full audio editing suite | MEDIUM |
| 13 | **AudioSuitePanel** | `components/AudioSuitePanel.tsx` | Audio suite container panel | LOW |
| 14 | **AudioCutterDashboard** | `components/AudioCutterDashboard.tsx` | Audio trimming and cutting | MEDIUM |
| 15 | **AudioMixerPanel** | `components/pro/AudioMixerPanel.tsx` | Multi-track audio mixing | HIGH |

#### Category D: Workflow/Process Components (MEDIUM PRIORITY)

| # | Component | File | Intended Purpose | Complexity |
|---|-----------|------|------------------|------------|
| 16 | **AdWorkflow** | `components/AdWorkflow.tsx` | Ad creation workflow steps | MEDIUM |
| 17 | **HumanWorkflowDashboard** | `components/HumanWorkflowDashboard.tsx` | Human-in-loop approval workflow | MEDIUM |
| 18 | **BatchProcessingPanel** | `components/BatchProcessingPanel.tsx` | Bulk video processing | MEDIUM |
| 19 | **ABTestingDashboard** | `components/ABTestingDashboard.tsx` | A/B test management | MEDIUM |

#### Category E: Utility/Support Components (LOW PRIORITY)

| # | Component | File | Intended Purpose | Complexity |
|---|-----------|------|------------------|------------|
| 20 | **VideoGenerator** | `components/VideoGenerator.tsx` | AI video generation | MEDIUM |
| 21 | **VideoPlayer** | `components/VideoPlayer.tsx` | Video playback component | LOW |
| 22 | **PreviewPanel** | `components/PreviewPanel.tsx` | Content preview | LOW |
| 23 | **TemplateSelector** | `components/TemplateSelector.tsx` | Template selection UI | LOW |
| 24 | **AnalysisResultCard** | `components/AnalysisResultCard.tsx` | Analysis result display | LOW |
| 25 | **ColorGradingPanel** | `components/pro/ColorGradingPanel.tsx` | Color correction tools | MEDIUM |
| 26 | **ColorGradingPanelDemo** | `components/pro/ColorGradingPanelDemo.tsx` | Demo for color grading | LOW |
| 27 | **PerformanceDashboard** | `components/PerformanceDashboard.tsx` | System performance metrics | LOW |
| 28 | **ImageSuite** | `components/ImageSuite.tsx` | Image editing tools | MEDIUM |
| 29 | **Assistant** | `components/Assistant.tsx` | AI assistant chat | MEDIUM |
| 30 | **LoginPage** | `components/LoginPage.tsx` | User authentication | MEDIUM |
| 31 | **ErrorBoundary** | `components/ErrorBoundary.tsx` | Error handling wrapper | LOW |
| 32 | **icons** | `components/icons.tsx` | Icon components | LOW |

---

## 2. API SERVICES INVENTORY

### 2.1 Primary API Services

#### `dashboardAPI.ts` - Main Backend API (26 Endpoints)

| # | Function | Endpoint | Method | Purpose |
|---|----------|----------|--------|---------|
| 1 | `getStats` | `/api/stats` | GET | Dashboard statistics |
| 2 | `getRecentCampaigns` | `/api/campaigns/recent` | GET | Recent campaign list |
| 3 | `getPredictions` | `/api/predictions` | GET | ROAS predictions |
| 4 | `analyzeScript` | `/api/analyze/script` | POST | AI script analysis |
| 5 | `generateAd` | `/api/generate/ad` | POST | AI ad generation |
| 6 | `optimizeCampaign` | `/api/optimize/campaign` | POST | Campaign optimization |
| 7 | `getCompetitorAnalysis` | `/api/spy/competitors` | GET | Competitor intelligence |
| 8 | `getPerformanceMetrics` | `/api/performance` | GET | Performance data |
| 9 | `submitForReview` | `/api/review/submit` | POST | Human review submission |
| 10 | `getReviewQueue` | `/api/review/queue` | GET | Pending reviews |
| 11 | `approveReview` | `/api/review/approve` | POST | Approve content |
| 12 | `rejectReview` | `/api/review/reject` | POST | Reject content |
| 13 | `getABTests` | `/api/ab-tests` | GET | A/B test list |
| 14 | `createABTest` | `/api/ab-tests` | POST | Create A/B test |
| 15 | `getTemplates` | `/api/templates` | GET | Template library |
| 16 | `saveTemplate` | `/api/templates` | POST | Save template |
| 17 | `getBatchJobs` | `/api/batch/jobs` | GET | Batch processing jobs |
| 18 | `createBatchJob` | `/api/batch/jobs` | POST | Create batch job |
| 19 | `getAssets` | `/api/assets` | GET | Asset library |
| 20 | `uploadAsset` | `/api/assets/upload` | POST | Upload asset |
| 21 | `getRenderQueue` | `/api/render/queue` | GET | Render queue |
| 22 | `submitRender` | `/api/render/submit` | POST | Submit render job |
| 23 | `getAnalytics` | `/api/analytics` | GET | Analytics data |
| 24 | `exportData` | `/api/export` | POST | Export functionality |
| 25 | `getNotifications` | `/api/notifications` | GET | User notifications |
| 26 | `updateSettings` | `/api/settings` | PUT | User settings |

#### `api.ts` - Legacy API Layer (20 Endpoints)

| # | Function | Purpose | Status |
|---|----------|---------|--------|
| 1 | `fetchVideos` | Get video list | ACTIVE |
| 2 | `uploadVideo` | Upload video | ACTIVE |
| 3 | `analyzeVideo` | AI video analysis | ACTIVE |
| 4 | `getVideoDetails` | Video metadata | ACTIVE |
| 5 | `deleteVideo` | Remove video | ACTIVE |
| 6 | `getClips` | Get video clips | ACTIVE |
| 7 | `rankClips` | AI clip ranking | ACTIVE |
| 8 | `searchVideos` | Semantic search | ACTIVE |
| 9 | `getComplianceReport` | Compliance check | ACTIVE |
| 10 | `getDiversificationScore` | Creative diversity | ACTIVE |
| 11 | `getReliabilityMetrics` | System health | ACTIVE |
| 12 | `submitRenderJob` | Render video | ACTIVE |
| 13 | `getRenderStatus` | Render progress | ACTIVE |
| 14 | `getAssetLibrary` | Asset management | ACTIVE |
| 15 | `processAsset` | Asset processing | ACTIVE |
| 16 | `getAnalysisResults` | Analysis data | ACTIVE |
| 17 | `saveAnalysis` | Store analysis | ACTIVE |
| 18 | `getSceneData` | Scene enrichment | ACTIVE |
| 19 | `getPredictiveScore` | ROAS prediction | ACTIVE |
| 20 | `getAudienceInsights` | Audience data | ACTIVE |

### 2.2 External Integration Services

#### `geminiService.ts` - Google Gemini AI

| Function | Model | Purpose |
|----------|-------|---------|
| `analyzeScript` | gemini-1.5-pro | Script analysis |
| `generateCreative` | gemini-1.5-pro | Creative generation |
| `extractScenes` | gemini-1.5-flash | Scene extraction |
| `predictPerformance` | gemini-1.5-pro | Performance prediction |
| `generateVariations` | gemini-1.5-flash | Creative variations |

#### `supabaseClient.ts` - Supabase Database

| Function | Table | Purpose |
|----------|-------|---------|
| `signIn` | auth | User authentication |
| `signUp` | auth | User registration |
| `signOut` | auth | Logout |
| `getUser` | auth | Get current user |
| `saveCampaign` | campaigns | Store campaign |
| `getCampaigns` | campaigns | List campaigns |
| `saveAsset` | assets | Store asset |
| `getAssets` | assets | List assets |
| `saveAnalysis` | analyses | Store analysis |
| `getAnalyses` | analyses | List analyses |

#### `googleDriveService.ts` - Google Drive Integration

| Function | Scope | Purpose |
|----------|-------|---------|
| `authenticate` | drive.file | OAuth flow |
| `uploadFile` | drive.file | Upload to Drive |
| `listFiles` | drive.readonly | List Drive files |
| `downloadFile` | drive.file | Download from Drive |
| `shareFile` | drive.file | Share file |

#### `metaPixel.ts` - Meta/Facebook Tracking

| Function | Event | Purpose |
|----------|-------|---------|
| `trackPageView` | PageView | Track page visits |
| `trackPurchase` | Purchase | Track conversions |
| `trackLead` | Lead | Track leads |
| `trackCustom` | Custom | Custom events |

### 2.3 Processing Services

#### `videoProcessor.ts` - Video Processing

| Function | Purpose | FFmpeg |
|----------|---------|--------|
| `extractFrames` | Frame extraction | Yes |
| `trimVideo` | Video trimming | Yes |
| `concatenateClips` | Merge videos | Yes |
| `addOverlay` | Text/image overlay | Yes |
| `adjustSpeed` | Speed changes | Yes |
| `extractAudio` | Audio extraction | Yes |

#### `audioProcessor.ts` - Audio Processing

| Function | Purpose |
|----------|---------|
| `trimAudio` | Trim audio file |
| `mergeAudio` | Merge audio tracks |
| `adjustVolume` | Volume control |
| `fadeInOut` | Fade effects |
| `addBackgroundMusic` | Background track |

#### `batchProcessor.ts` - Batch Operations

| Function | Purpose |
|----------|---------|
| `processQueue` | Process batch queue |
| `addToQueue` | Add job to queue |
| `getQueueStatus` | Queue status |
| `cancelJob` | Cancel batch job |
| `retryJob` | Retry failed job |

#### `templateSystem.ts` - Template Engine

| Function | Purpose |
|----------|---------|
| `loadTemplate` | Load template |
| `applyTemplate` | Apply to video |
| `saveAsTemplate` | Save as template |
| `listTemplates` | Get templates |
| `deleteTemplate` | Remove template |

#### `realtimePreview.ts` - Live Preview

| Function | Purpose |
|----------|---------|
| `startPreview` | Start live preview |
| `updatePreview` | Update preview |
| `stopPreview` | Stop preview |
| `captureFrame` | Capture frame |

### 2.4 Vercel Serverless API Functions

| File | Endpoint | Model | Purpose |
|------|----------|-------|---------|
| `api/council.py` | POST /api/council | Multi-model | AI Council (4 models) |
| `api/generate.py` | POST /api/generate | Gemini | Blueprint generation |
| `api/quick-score.py` | POST /api/quick-score | Gemini Flash | Fast scoring |

---

## 3. STATE MANAGEMENT INVENTORY

### 3.1 React Contexts

#### `AuthContext.tsx` - Authentication State

```typescript
interface AuthContextType {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
}
```

| Provider | Used In | Status |
|----------|---------|--------|
| AuthProvider | LoginPage | ORPHANED |

#### `DashboardContext.tsx` - Dashboard State

```typescript
interface DashboardContextType {
  stats: DashboardStats | null;
  campaigns: Campaign[];
  assets: Asset[];
  notifications: Notification[];
  loading: boolean;
  refreshStats: () => Promise<void>;
  refreshCampaigns: () => Promise<void>;
}
```

| Provider | Used In | Status |
|----------|---------|--------|
| DashboardProvider | CreatorDashboard | ORPHANED |

### 3.2 Zustand Store (ProVideoEditor)

```typescript
// Located in: components/pro/ProVideoEditor.tsx
interface EditorStore {
  // Timeline State
  tracks: Track[];
  currentTime: number;
  duration: number;
  zoom: number;

  // Playback State
  isPlaying: boolean;
  volume: number;

  // Selection State
  selectedClip: Clip | null;
  selectedTrack: number;

  // Actions
  addTrack: (type: TrackType) => void;
  removeTrack: (id: string) => void;
  addClip: (trackId: string, clip: Clip) => void;
  moveClip: (clipId: string, newStart: number) => void;
  splitClip: (clipId: string, time: number) => void;
  setCurrentTime: (time: number) => void;
  play: () => void;
  pause: () => void;
}
```

| Store | Used In | Status |
|-------|---------|--------|
| useEditorStore | ProVideoEditor | ORPHANED |

---

## 4. COMPLETE CONNECTION STATUS TABLE

| # | Component | Connected | Route | Parent | Status |
|---|-----------|-----------|-------|--------|--------|
| 1 | AssetsPanel | YES | /assets | App.tsx | ACTIVE |
| 2 | RankedClipsPanel | YES | /clips | App.tsx | ACTIVE |
| 3 | SemanticSearchPanel | YES | /search | App.tsx | ACTIVE |
| 4 | AnalysisPanel | YES | /analysis | App.tsx | ACTIVE |
| 5 | CompliancePanel | YES | /compliance | App.tsx | ACTIVE |
| 6 | DiversificationDashboard | YES | /diversification | App.tsx | ACTIVE |
| 7 | ReliabilityChart | YES | /reliability | App.tsx | ACTIVE |
| 8 | RenderJobPanel | YES | /render | App.tsx | ACTIVE |
| 9 | ProVideoEditor | NO | - | None | ORPHANED |
| 10 | CampaignBuilder | NO | - | None | ORPHANED |
| 11 | AnalyticsDashboard | NO | - | None | ORPHANED |
| 12 | AdSpyDashboard | NO | - | None | ORPHANED |
| 13 | AICreativeStudio | NO | - | None | ORPHANED |
| 14 | CreatorDashboard | NO | - | None | ORPHANED |
| 15 | VideoStudio | NO | - | None | ORPHANED |
| 16 | StoryboardStudio | NO | - | None | ORPHANED |
| 17 | VideoEditor | NO | - | None | ORPHANED |
| 18 | AdvancedEditor | NO | - | None | ORPHANED |
| 19 | TimelineCanvas | NO | - | ProVideoEditor | ORPHANED |
| 20 | AudioSuite | NO | - | None | ORPHANED |
| 21 | AudioSuitePanel | NO | - | None | ORPHANED |
| 22 | AudioCutterDashboard | NO | - | None | ORPHANED |
| 23 | AudioMixerPanel | NO | - | ProVideoEditor | ORPHANED |
| 24 | AdWorkflow | NO | - | None | ORPHANED |
| 25 | HumanWorkflowDashboard | NO | - | None | ORPHANED |
| 26 | BatchProcessingPanel | NO | - | None | ORPHANED |
| 27 | ABTestingDashboard | NO | - | None | ORPHANED |
| 28 | VideoGenerator | NO | - | None | ORPHANED |
| 29 | VideoPlayer | NO | - | Multiple | ORPHANED |
| 30 | PreviewPanel | NO | - | None | ORPHANED |
| 31 | TemplateSelector | NO | - | None | ORPHANED |
| 32 | AnalysisResultCard | NO | - | AnalysisPanel | ACTIVE* |
| 33 | ColorGradingPanel | NO | - | ProVideoEditor | ORPHANED |
| 34 | ColorGradingPanelDemo | NO | - | None | ORPHANED |
| 35 | PerformanceDashboard | NO | - | None | ORPHANED |
| 36 | ImageSuite | NO | - | None | ORPHANED |
| 37 | Assistant | NO | - | None | ORPHANED |
| 38 | LoginPage | NO | - | None | ORPHANED |
| 39 | ErrorBoundary | NO | - | None | ORPHANED |
| 40 | icons | NO | - | Multiple | UTILITY |

*ACTIVE* = Used as child component within connected parent

---

## 5. DEPENDENCY MAP

```
App.tsx (ROOT)
├── AssetsPanel
├── RankedClipsPanel
├── SemanticSearchPanel
├── AnalysisPanel
│   └── AnalysisResultCard
├── CompliancePanel
├── DiversificationDashboard
├── ReliabilityChart
└── RenderJobPanel

ORPHANED TREES:
├── ProVideoEditor (MAJOR)
│   ├── TimelineCanvas
│   ├── AudioMixerPanel
│   └── ColorGradingPanel
│
├── CreatorDashboard (MAJOR)
│   └── DashboardContext
│
├── CampaignBuilder (MAJOR)
│   └── AdWorkflow
│
├── AnalyticsDashboard (MAJOR)
│
├── AdSpyDashboard (MAJOR)
│
├── AICreativeStudio (MAJOR)
│   ├── VideoGenerator
│   └── TemplateSelector
│
├── LoginPage (AUTH)
│   └── AuthContext
│
└── Supporting Components
    ├── VideoStudio
    ├── StoryboardStudio
    ├── AudioSuite
    ├── BatchProcessingPanel
    ├── ABTestingDashboard
    ├── HumanWorkflowDashboard
    └── ...
```

---

## 6. RECOMMENDED INTEGRATION PRIORITY

### Phase 1: Core Experience (CRITICAL)
1. **LoginPage** + **AuthContext** - Enable authentication
2. **CreatorDashboard** + **DashboardContext** - Main landing page
3. **AnalyticsDashboard** - ROAS and performance tracking

### Phase 2: Creation Tools (HIGH)
4. **AICreativeStudio** - AI-powered creative generation
5. **CampaignBuilder** + **AdWorkflow** - End-to-end campaign creation
6. **ProVideoEditor** with Timeline, Audio, Color grading

### Phase 3: Intelligence (MEDIUM)
7. **AdSpyDashboard** - Competitor analysis
8. **ABTestingDashboard** - A/B testing
9. **HumanWorkflowDashboard** - Approval workflow

### Phase 4: Advanced Features (LOWER)
10. **BatchProcessingPanel** - Bulk operations
11. **VideoStudio** / **StoryboardStudio** - Alternative editors
12. **AudioSuite** - Dedicated audio editing

---

## 7. TECHNICAL DEBT SUMMARY

| Issue | Severity | Impact |
|-------|----------|--------|
| 80% components orphaned | CRITICAL | Most features inaccessible |
| No router implemented | HIGH | Single-page limitation |
| Auth flow not connected | HIGH | No user management |
| Dashboard context unused | MEDIUM | State management fragmented |
| Duplicate editor components | LOW | Code maintainability |

---

## 8. FILE SIZE ANALYSIS

| Category | Files | Est. Lines |
|----------|-------|------------|
| Components | 40 | ~8,000 |
| Services | 13 | ~3,000 |
| Contexts | 3 | ~500 |
| API Functions | 3 | ~400 |
| Config/Types | ~10 | ~500 |
| **TOTAL** | **~69** | **~12,400** |

---

*Generated: 2025-12-02*
*Platform: GeminiVideo AI Marketing SaaS*
*Version: 1.0.0*
