# 📦 Extracted UI Kits - Reference Guide

This document describes the UI kits that have been extracted from the uploaded zip files and how to use them.

---

## 🗂️ What Was Extracted

From your uploaded files, the following UI kits are available:

### 1. Catalyst UI Kit
**Location:** `frontend/reference/catalyst/`

Professional TypeScript components from Tailwind Labs (28 components):
- `alert.tsx` - Alert banners
- `avatar.tsx` - User avatars
- `badge.tsx` - Status badges
- `button.tsx` - Buttons with variants
- `checkbox.tsx` - Checkboxes
- `combobox.tsx` - Searchable dropdowns
- `description-list.tsx` - Key-value lists
- `dialog.tsx` - Modal dialogs
- `divider.tsx` - Horizontal dividers
- `dropdown.tsx` - Dropdown menus
- `fieldset.tsx` - Form fieldsets
- `heading.tsx` - Typography headings
- `input.tsx` - Form inputs
- `link.tsx` - Styled links
- `listbox.tsx` - Select listboxes
- `navbar.tsx` - Navigation bars
- `pagination.tsx` - Pagination controls
- `radio.tsx` - Radio buttons
- `select.tsx` - Select dropdowns
- `sidebar-layout.tsx` - Sidebar layouts
- `sidebar.tsx` - Sidebar navigation
- `stacked-layout.tsx` - Stacked layouts
- `switch.tsx` - Toggle switches
- `table.tsx` - Data tables
- `text.tsx` - Text components
- `textarea.tsx` - Text areas

### 2. Radiant Template ✨ NEW
**Location:** `frontend/reference/radiant/`

Modern animated components (20 components):
- `animated-number.tsx` - Animated number counters
- `bento-card.tsx` - Bento grid cards
- `button.tsx` - Styled buttons
- `container.tsx` - Layout containers
- `footer.tsx` - Footer component
- `gradient.tsx` - Gradient backgrounds
- `keyboard.tsx` - Keyboard visualizations
- `link.tsx` - Styled links
- `linked-avatars.tsx` - Linked avatar groups
- `logo-cloud.tsx` - Logo cloud displays
- `logo-cluster.tsx` - Clustered logo layouts
- `logo-timeline.tsx` - Timeline with logos
- `logo.tsx` - Logo component
- `map.tsx` - Map visualizations
- `navbar.tsx` - Navigation bar
- `plus-grid.tsx` - Plus grid layouts
- `screenshot.tsx` - Screenshot displays
- `testimonials.tsx` - Testimonials carousel
- `text.tsx` - Typography components

### 3. Compass Template
**Location:** `frontend/reference/compass/`

Video-focused components:
- `video-player.jsx` - Custom video player
- `video-card.jsx` - Video thumbnails
- `sidebar-layout.jsx` - Sidebar layouts
- `navbar.jsx` - Navigation
- `table-of-contents.jsx` - TOC component
- And more...

### 4. Salient Template
**Location:** `frontend/reference/salient/`

Marketing/landing components:
- `Hero.jsx` - Hero sections
- `Features.jsx` - Feature grids
- `Pricing.jsx` - Pricing tables
- `Testimonials.jsx` - Testimonials
- `CallToAction.jsx` - CTAs
- And more...

---

## ⚠️ Current Status

The Catalyst components are placed in `frontend/reference/` because they need TypeScript fixes:

1. **Motion import issue:** Components import from `motion/react` but should use `framer-motion` ✅ Fixed
2. **Type compatibility:** Some type definitions need adjustment for Headless UI v2 + React 18
3. **Tailwind CSS v4 syntax:** Uses new Tailwind v4 CSS variable syntax

These are **reference components** - copy individual files to `src/components/` and fix as needed.

### To Use a Component:
1. Copy from `reference/catalyst/` to `src/components/catalyst/`
2. Fix any TypeScript errors
3. Add `// @ts-nocheck` at top if needed temporarily

---

## 🛠️ How to Use These Components

### Using Catalyst Components:
```tsx
import { Button, Input, Badge } from '@/components/catalyst'

function MyComponent() {
  return (
    <div>
      <Button color="indigo">Click me</Button>
      <Input placeholder="Enter text..." />
      <Badge color="green">Active</Badge>
    </div>
  )
}
```

### Using Compass Video Player:
```tsx
// Reference the compass video player for inspiration
// Copy and adapt to TypeScript as needed
import VideoPlayer from '@/templates/compass/video-player'
```

### Using Salient Components:
```tsx
// Reference the salient components for marketing pages
// Copy and adapt to TypeScript as needed
import { Hero, Features } from '@/templates/salient'
```

---

## 📁 Final Structure

```
frontend/
├── src/                    # Active source code (builds)
│   ├── components/
│   │   ├── dashboard/      # Your dashboard components
│   │   ├── layout/         # Layout components
│   │   └── ...
│   └── ...
└── reference/              # UI kit reference files (not built)
    ├── catalyst/           # Catalyst UI Kit (28 TypeScript components)
    │   ├── button.tsx
    │   ├── input.tsx
    │   └── ...
    ├── radiant/            # Radiant Template (20 TypeScript components)
    │   ├── bento-card.tsx
    │   ├── animated-number.tsx
    │   └── ...
    ├── compass/            # Compass Template (JSX)
    │   ├── video-player.jsx
    │   └── ...
    └── salient/            # Salient Template (JSX)
        ├── Hero.jsx
        └── ...
```

---

## 🚀 Next Steps

1. **Phase 1:** Fix Catalyst component imports and integrate with layout
2. **Phase 2:** Build dashboard using Catalyst components
3. **Phase 3:** Create campaign wizard with forms
4. **Phase 4-8:** Follow the Master Plan

See `GEMINIVIDEO_MASTER_PLAN.md` for the complete development roadmap.
