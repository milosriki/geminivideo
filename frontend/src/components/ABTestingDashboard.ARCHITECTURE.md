# A/B Testing Dashboard - Technical Architecture

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ABTestingDashboard                           │
│                    (Main Container)                             │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├─── State Management
             │    ├── experiments: Experiment[]
             │    ├── selectedExperiment: Experiment | null
             │    ├── statusFilter: 'all' | 'running' | 'paused' | 'completed'
             │    ├── showCreateModal: boolean
             │    ├── explorationRate: number
             │    └── autoShift: boolean
             │
             ├─── Effects
             │    ├── Initialize mock data (useEffect)
             │    └── Real-time polling (useEffect + setInterval)
             │
             └─── Child Components
                  │
                  ├─── Header Section
                  │    ├── Title
                  │    ├── Create Experiment Button
                  │    └── Export CSV Button
                  │
                  ├─── Experiments List (Left Column)
                  │    ├── Status Filter Dropdown
                  │    └── Experiments Table
                  │         ├── Row per experiment
                  │         ├── Click to select
                  │         └── Action buttons (pause/resume/delete)
                  │
                  └─── Experiment Details (Right Column)
                       │
                       ├─── Thompson Sampling Visualizer
                       │    ├── BetaDistributionChart (canvas)
                       │    ├── BarChart for arm probabilities (canvas)
                       │    └── Recommendation Panel
                       │         ├── Current winner display
                       │         ├── Confidence level
                       │         ├── Action recommendation
                       │         └── Exploration/Exploitation balance
                       │
                       ├─── Variant Comparison
                       │    ├── Metrics table
                       │    │    ├── All variant statistics
                       │    │    ├── Winner highlighting
                       │    │    └── Progress bars
                       │    └── Statistical Significance
                       │         ├── Z-test calculation
                       │         ├── P-value display
                       │         └── Significance indicator
                       │
                       └─── Budget Optimizer
                            ├── Current vs Recommended allocation
                            ├── Auto-shift toggle
                            ├── Exploration rate slider
                            └── Apply changes button
```

---

## Data Flow Diagram

```
┌──────────────┐
│ Mock Data    │
│ Generator    │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────────────────┐
│ experiments: Experiment[]                        │
│ ┌────────────────────────────────────────────┐   │
│ │ Experiment {                               │   │
│ │   id, name, status,                        │   │
│ │   variants: Variant[],                     │   │
│ │   totalBudget,                             │   │
│ │   explorationRate                          │   │
│ │ }                                          │   │
│ └────────────────────────────────────────────┘   │
└──────────────┬───────────────────────────────────┘
               │
               ├─────────────┐
               │             │
               ↓             ↓
       ┌───────────┐  ┌─────────────────┐
       │ Filter    │  │ Select          │
       │ by Status │  │ Experiment      │
       └─────┬─────┘  └────────┬────────┘
             │                 │
             ↓                 ↓
       ┌─────────────┐  ┌─────────────────────────┐
       │ Filtered    │  │ selectedExperiment      │
       │ Experiments │  └──────────┬──────────────┘
       │ Display     │             │
       └─────────────┘             │
                                   ├──────────────────┐
                                   │                  │
                                   ↓                  ↓
                          ┌─────────────────┐  ┌──────────────┐
                          │ Thompson        │  │ Metrics      │
                          │ Sampling        │  │ Calculation  │
                          │ Calculation     │  └──────────────┘
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ↓              ↓              ↓
            ┌─────────────┐ ┌────────────┐ ┌──────────────┐
            │ Beta PDF    │ │ Monte      │ │ Budget       │
            │ Charts      │ │ Carlo      │ │ Allocation   │
            │             │ │ Sampling   │ │              │
            └─────────────┘ └────────────┘ └──────────────┘
                                   │
                                   ↓
                          ┌─────────────────┐
                          │ Winner          │
                          │ Probabilities   │
                          │ [%, %, %, ...]  │
                          └────────┬────────┘
                                   │
                                   ↓
                          ┌─────────────────┐
                          │ UI Update       │
                          │ - Charts        │
                          │ - Tables        │
                          │ - Recommendations│
                          └─────────────────┘
```

---

## Algorithm Flow: Thompson Sampling

```
For each experiment:

1. Data Input
   ┌────────────────────────────┐
   │ Variant Data               │
   │ - Impressions              │
   │ - Clicks                   │
   │ - Conversions              │
   └──────────┬─────────────────┘
              ↓
2. Beta Distribution Parameters
   ┌────────────────────────────┐
   │ alpha = clicks + 1         │
   │ beta = (impr - clicks) + 1 │
   └──────────┬─────────────────┘
              ↓
3. Monte Carlo Simulation (10,000 samples)
   ┌────────────────────────────┐
   │ FOR i = 1 to 10,000:       │
   │   FOR each variant:        │
   │     sample ~ Beta(α, β)    │
   │   winner = argmax(samples) │
   │   wins[winner]++           │
   └──────────┬─────────────────┘
              ↓
4. Winner Probabilities
   ┌────────────────────────────┐
   │ prob[i] = wins[i] / 10,000 │
   │ × 100 (percentage)         │
   └──────────┬─────────────────┘
              ↓
5. Budget Allocation
   ┌────────────────────────────┐
   │ allocation[i] =            │
   │   prob[i] × (1 - explore)  │
   │   + (explore / n_variants) │
   └──────────┬─────────────────┘
              ↓
6. Recommendation
   ┌────────────────────────────┐
   │ IF max(prob) > 95%:        │
   │   → "Roll out winner"      │
   │ ELIF max(prob) > 80%:      │
   │   → "Increase leader budget"│
   │ ELSE:                      │
   │   → "Continue exploring"   │
   └────────────────────────────┘
```

---

## Chart Rendering Pipeline

```
┌─────────────────────────────────────────────────────┐
│              BetaDistributionChart                  │
└───────────────────┬─────────────────────────────────┘
                    │
                    ├─── 1. Canvas Setup
                    │    ├── Get context
                    │    ├── Clear canvas
                    │    └── Set dimensions
                    │
                    ├─── 2. Calculate Bounds
                    │    ├── Find max density
                    │    ├── Calculate padding
                    │    └── Set scale factors
                    │
                    ├─── 3. Draw Axes
                    │    ├── X-axis (0 to 1)
                    │    ├── Y-axis (0 to max density)
                    │    ├── Grid lines
                    │    └── Labels
                    │
                    ├─── 4. Plot Beta Distributions
                    │    ├── FOR each variant:
                    │    │   ├── Set color
                    │    │   ├── Calculate PDF points
                    │    │   │   (x from 0.01 to 0.99, step 0.005)
                    │    │   ├── Draw curve
                    │    │   └── Add to legend
                    │    └── Next variant
                    │
                    └─── 5. Render to DOM
                         └── Canvas displays in UI
```

---

## State Update Cycle

```
┌─────────────────────────────────────────────────────┐
│              Real-time Update Loop                  │
│              (Every 5 seconds)                      │
└───────────────────┬─────────────────────────────────┘
                    │
                    ↓
            ┌───────────────┐
            │ setInterval   │
            │ (5000ms)      │
            └───────┬───────┘
                    │
                    ↓
        ┌───────────────────────┐
        │ FOR each experiment:  │
        │   IF status = running │
        └───────┬───────────────┘
                │
                ↓
        ┌───────────────────────────┐
        │ Generate new data:        │
        │ - Random impressions (1-10)│
        │ - Random clicks (0-3)     │
        │ - Random conversions (0-1)│
        └───────┬───────────────────┘
                │
                ↓
        ┌───────────────────────────┐
        │ Update variant metrics:   │
        │ - impressions += new      │
        │ - clicks += new           │
        │ - conversions += new      │
        │ - alpha = clicks + 1      │
        │ - beta = (impr-clicks) + 1│
        │ - spend += new × 0.1      │
        │ - revenue += conv × 15    │
        └───────┬───────────────────┘
                │
                ↓
        ┌───────────────────────────┐
        │ setExperiments(updated)   │
        └───────┬───────────────────┘
                │
                ↓
        ┌───────────────────────────┐
        │ React re-renders:         │
        │ - Charts update           │
        │ - Tables refresh          │
        │ - Probabilities recalc    │
        └───────────────────────────┘
```

---

## Event Handler Flow

```
User Action                  Handler                   Effect
────────────────────────────────────────────────────────────────

Click "Create Experiment"
    │
    └──→ handleCreateExperiment()
             │
             └──→ setShowCreateModal(true)
                      │
                      └──→ Modal displays


Click Experiment Row
    │
    └──→ setSelectedExperiment(exp)
             │
             ├──→ Row highlights
             ├──→ Details panel updates
             ├──→ Charts recalculate
             └──→ Recommendations update


Click "Pause" button
    │
    └──→ handlePauseResume(id)
             │
             └──→ Update experiment.status
                      │
                      ├──→ Badge color changes
                      └──→ Icon changes ⏸ ↔ ▶


Adjust Exploration Slider
    │
    └──→ setExplorationRate(value)
             │
             ├──→ Slider value updates
             ├──→ Balance bar adjusts
             └──→ Allocation recalculates


Click "Apply Budget Changes"
    │
    └──→ handleApplyBudgetChanges()
             │
             ├──→ Update experiment config
             ├──→ Recalculate allocations
             └──→ Show success alert


Click "Export to CSV"
    │
    └──→ handleExportCSV()
             │
             ├──→ Generate CSV string
             ├──→ Create Blob
             ├──→ Create download link
             └──→ Trigger download


Click "Delete" button
    │
    └──→ handleDelete(id)
             │
             ├──→ Show confirmation dialog
             │
             └──→ IF confirmed:
                      │
                      ├──→ Remove from experiments
                      └──→ Update selection
```

---

## Mathematical Operations

### 1. Beta Distribution PDF

```
Input: x ∈ (0, 1), α > 0, β > 0

Step 1: Calculate Beta function
   B(α, β) = Γ(α) × Γ(β) / Γ(α + β)

Step 2: Calculate PDF
   f(x; α, β) = x^(α-1) × (1-x)^(β-1) / B(α, β)

Output: Probability density at x
```

### 2. Gamma Function (Stirling's Approximation)

```
Input: z > 0

For z < 0.5:
   Γ(z) = π / (sin(πz) × Γ(1-z))

For z ≥ 0.5:
   Use series expansion with coefficients C[]

Output: Γ(z)
```

### 3. Statistical Significance (Z-test)

```
Input: variant1, variant2

Step 1: Calculate proportions
   p₁ = clicks₁ / impressions₁
   p₂ = clicks₂ / impressions₂

Step 2: Pooled proportion
   p_pool = (clicks₁ + clicks₂) / (n₁ + n₂)

Step 3: Standard error
   SE = √(p_pool × (1 - p_pool) × (1/n₁ + 1/n₂))

Step 4: Z-statistic
   z = (p₁ - p₂) / SE

Step 5: P-value
   p-value = 2 × (1 - Φ(|z|))
   where Φ is the standard normal CDF

Output: { pValue, significant: pValue < 0.05 }
```

### 4. Budget Allocation

```
Input: variants[], explorationRate

Step 1: Get winner probabilities
   probs[] = thompsonSampling(variants, 10000)

Step 2: Calculate allocation
   FOR each variant i:
      exploit = probs[i] × (1 - explorationRate)
      explore = explorationRate / n_variants
      allocation[i] = exploit + explore

Step 3: Normalize to 100%
   total = sum(allocation)
   allocation[i] = (allocation[i] / total) × 100

Output: allocation[] (percentages)
```

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Render experiments list | O(n) | n = number of experiments |
| Filter experiments | O(n) | Linear scan |
| Thompson Sampling | O(s × v) | s = samples (10k), v = variants |
| Beta PDF calculation | O(1) | Constant per point |
| Chart rendering | O(p × v) | p = points (200), v = variants |
| Statistical test | O(1) | Fixed calculation |

### Space Complexity

| Component | Size | Notes |
|-----------|------|-------|
| Experiment data | O(n × v) | n experiments, v variants each |
| Chart canvas | O(w × h) | Canvas pixel buffer |
| Monte Carlo samples | O(s × v) | Temporary, GC'd after |
| Component state | O(n × v) | React state |

### Optimization Opportunities

1. **Memoization**
   - Winner probabilities (useMemo)
   - Budget allocations (useMemo)
   - Chart components (React.memo)

2. **Web Workers**
   - Thompson Sampling calculation
   - Statistical tests
   - CSV generation

3. **Virtual Scrolling**
   - Experiments list (for 100+ experiments)

4. **Debouncing**
   - Slider changes
   - Filter updates

---

## Error Handling

```
┌─────────────────────────────────────────────────────┐
│                Error Boundaries                     │
└───────────────────┬─────────────────────────────────┘
                    │
                    ├─── Division by Zero
                    │    └──→ Check impressions > 0
                    │
                    ├─── Invalid Beta Parameters
                    │    └──→ Ensure α, β > 0
                    │
                    ├─── Empty Variants Array
                    │    └──→ Check length before operations
                    │
                    ├─── Canvas Not Supported
                    │    └──→ Fallback message
                    │
                    └─── Real-time Update Failure
                         └──→ Continue with stale data
```

---

## Testing Strategy

```
Unit Tests
    ├── Mathematical Functions
    │   ├── betaPDF()
    │   ├── gamma()
    │   ├── calculateSignificance()
    │   └── calculateLift()
    │
    ├── Thompson Sampling
    │   ├── sampleBeta()
    │   ├── calculateWinnerProbability()
    │   └── calculateBudgetAllocation()
    │
    └── Utilities
        ├── exportToCSV()
        └── normalCDF()

Integration Tests
    ├── User Workflows
    │   ├── Create → Pause → Resume → Delete
    │   ├── Select → Adjust Budget → Export
    │   └── Filter → Select → View Details
    │
    └── State Management
        ├── Real-time updates
        ├── Filter updates
        └── Selection updates

Component Tests
    ├── Rendering
    │   ├── Header
    │   ├── Experiments list
    │   ├── Charts
    │   └── Tables
    │
    └── Interactions
        ├── Click handlers
        ├── Form inputs
        └── Modal operations

Performance Tests
    ├── Render time < 1s
    ├── Thompson Sampling < 100ms
    └── Chart drawing < 100ms

Accessibility Tests
    ├── Keyboard navigation
    ├── Screen reader compatibility
    └── ARIA labels
```

---

## Deployment Checklist

- [ ] TypeScript compilation passes
- [ ] All tests pass
- [ ] No console errors
- [ ] Charts render correctly
- [ ] Real-time updates work
- [ ] CSV export functions
- [ ] Modal opens/closes
- [ ] Responsive on mobile
- [ ] Accessible via keyboard
- [ ] Cross-browser tested
- [ ] Performance benchmarks met
- [ ] Documentation complete

---

## Monitoring & Analytics

### Key Metrics to Track

1. **Usage Metrics**
   - Number of experiments created
   - Average experiment duration
   - Most common variant counts
   - Feature usage (export, pause, etc.)

2. **Performance Metrics**
   - Component render time
   - Thompson Sampling calculation time
   - Chart rendering time
   - Memory usage

3. **User Behavior**
   - Time spent on dashboard
   - Experiments per user
   - Export frequency
   - Budget adjustment frequency

4. **Business Metrics**
   - Experiment success rate
   - Average lift achieved
   - ROI improvement
   - Time to statistical significance

---

## Architecture Principles

1. **Separation of Concerns**
   - Charts as separate components
   - Utilities as pure functions
   - State management centralized

2. **Type Safety**
   - Full TypeScript coverage
   - Interface definitions
   - No `any` types

3. **Performance**
   - Efficient algorithms
   - Minimal re-renders
   - Optimized canvas usage

4. **Maintainability**
   - Clear naming conventions
   - Comprehensive comments
   - Modular structure

5. **Extensibility**
   - Easy to add new charts
   - Pluggable algorithms
   - Configurable parameters

---

**Document Version:** 1.0
**Last Updated:** December 1, 2025
**Maintained by:** Agent 13 - A/B Testing Dashboard Engineer
