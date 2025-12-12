/**
 * Route Definitions for GeminiVideo
 * Complete routing configuration exposing all 32 hidden components
 * React Router v6 format
 */

export interface RouteConfig {
  path: string
  name: string
  description?: string
  category: 'dashboard' | 'campaign' | 'analytics' | 'studio' | 'assets' | 'tools' | 'workflow' | 'auth' | 'onboarding' | 'marketing' | 'demo'
}

/**
 * All application routes organized by category
 */
export const routes: RouteConfig[] = [
  // ============================================================================
  // DASHBOARD ROUTES
  // ============================================================================
  {
    path: '/',
    name: 'Home Dashboard',
    description: 'Main dashboard overview',
    category: 'dashboard',
  },
  {
    path: '/dashboard/creator',
    name: 'Creator Dashboard',
    description: 'Alternative creator-focused dashboard',
    category: 'dashboard',
  },

  // ============================================================================
  // CAMPAIGN MANAGEMENT ROUTES
  // ============================================================================
  {
    path: '/campaigns',
    name: 'Campaigns List',
    description: 'View all campaigns',
    category: 'campaign',
  },
  {
    path: '/campaigns/:id',
    name: 'Campaign Details',
    description: 'View campaign details',
    category: 'campaign',
  },
  {
    path: '/create',
    name: 'Create Campaign',
    description: 'Create new campaign (quick flow)',
    category: 'campaign',
  },
  {
    path: '/campaigns/builder',
    name: 'Campaign Builder',
    description: 'Advanced campaign builder',
    category: 'campaign',
  },
  {
    path: '/campaigns/new',
    name: 'New Campaign',
    description: 'Start new campaign',
    category: 'campaign',
  },

  // ============================================================================
  // ANALYTICS & REPORTING ROUTES
  // ============================================================================
  {
    path: '/analytics',
    name: 'Analytics Page',
    description: 'Main analytics view',
    category: 'analytics',
  },
  {
    path: '/analytics/dashboard',
    name: 'Analytics Dashboard',
    description: 'Comprehensive analytics dashboard',
    category: 'analytics',
  },
  {
    path: '/analytics/performance',
    name: 'Performance Dashboard',
    description: 'Campaign performance metrics',
    category: 'analytics',
  },
  {
    path: '/analytics/reliability',
    name: 'Reliability Chart',
    description: 'System reliability metrics',
    category: 'analytics',
  },
  {
    path: '/analytics/diversification',
    name: 'Diversification Dashboard',
    description: 'Portfolio diversification analysis',
    category: 'analytics',
  },
  {
    path: '/analytics/roas',
    name: 'ROAS Dashboard',
    description: 'Return on ad spend tracking',
    category: 'analytics',
  },
  {
    path: '/reports',
    name: 'Reports Generator',
    description: 'Generate PDF/Excel reports',
    category: 'analytics',
  },

  // ============================================================================
  // STUDIO & CREATIVE ROUTES
  // ============================================================================
  {
    path: '/studio',
    name: 'Studio Page',
    description: 'Main studio landing',
    category: 'studio',
  },
  {
    path: '/studio/:projectId',
    name: 'Studio Project',
    description: 'Studio with project loaded',
    category: 'studio',
  },
  {
    path: '/studio/pro',
    name: 'Pro Video Editor',
    description: 'Professional video editing suite',
    category: 'studio',
  },
  {
    path: '/studio/pro/:projectId',
    name: 'Pro Editor Project',
    description: 'Pro editor with project',
    category: 'studio',
  },
  {
    path: '/studio/storyboard',
    name: 'Storyboard Studio',
    description: 'Visual storyboard creator',
    category: 'studio',
  },
  {
    path: '/studio/video',
    name: 'Video Studio',
    description: 'Video editing and generation',
    category: 'studio',
  },
  {
    path: '/studio/ai',
    name: 'AI Creative Studio',
    description: 'AI-powered creative generation',
    category: 'studio',
  },
  {
    path: '/studio/generate',
    name: 'Video Generator',
    description: 'Quick video generation',
    category: 'studio',
  },
  {
    path: '/studio/audio-mixer',
    name: 'Audio Mixer',
    description: 'Professional audio mixing panel',
    category: 'studio',
  },
  {
    path: '/studio/color-grading',
    name: 'Color Grading',
    description: 'Advanced color grading panel',
    category: 'studio',
  },
  {
    path: '/studio/color-grading-demo',
    name: 'Color Grading Demo',
    description: 'Color grading demo mode',
    category: 'studio',
  },

  // ============================================================================
  // ASSETS & LIBRARY ROUTES
  // ============================================================================
  {
    path: '/assets',
    name: 'Assets Page',
    description: 'Main assets view',
    category: 'assets',
  },
  {
    path: '/library',
    name: 'Asset Library',
    description: 'Complete asset library',
    category: 'assets',
  },
  {
    path: '/library/assets',
    name: 'Assets Panel',
    description: 'Asset management panel',
    category: 'assets',
  },
  {
    path: '/library/clips',
    name: 'Ranked Clips',
    description: 'AI-ranked video clips',
    category: 'assets',
  },
  {
    path: '/library/search',
    name: 'Semantic Search',
    description: 'AI-powered asset search',
    category: 'assets',
  },

  // ============================================================================
  // TOOLS & UTILITIES ROUTES
  // ============================================================================
  {
    path: '/spy',
    name: 'Ad Spy Page',
    description: 'Competitor ad intelligence',
    category: 'tools',
  },
  {
    path: '/spy/dashboard',
    name: 'Ad Spy Dashboard',
    description: 'Full ad spy dashboard',
    category: 'tools',
  },
  {
    path: '/analysis',
    name: 'Analysis Panel',
    description: 'Video and creative analysis',
    category: 'tools',
  },
  {
    path: '/compliance',
    name: 'Compliance Panel',
    description: 'Ad compliance checking',
    category: 'tools',
  },
  {
    path: '/audio',
    name: 'Audio Suite',
    description: 'Audio tools suite',
    category: 'tools',
  },
  {
    path: '/audio/suite',
    name: 'Audio Suite Panel',
    description: 'Advanced audio tools',
    category: 'tools',
  },
  {
    path: '/image',
    name: 'Image Suite',
    description: 'Image editing and generation',
    category: 'tools',
  },
  {
    path: '/assistant',
    name: 'AI Assistant',
    description: 'AI strategy assistant',
    category: 'tools',
  },
  {
    path: '/resources',
    name: 'Resources & Tutorials',
    description: 'Learning resources',
    category: 'tools',
  },

  // ============================================================================
  // WORKFLOW & TESTING ROUTES
  // ============================================================================
  {
    path: '/testing',
    name: 'A/B Testing Dashboard',
    description: 'Bayesian A/B testing',
    category: 'workflow',
  },
  {
    path: '/workflow',
    name: 'Human Workflow',
    description: 'Human-in-the-loop workflow',
    category: 'workflow',
  },
  {
    path: '/workflow/approvals',
    name: 'Approval Workflow',
    description: 'Content approval system',
    category: 'workflow',
  },
  {
    path: '/batch',
    name: 'Batch Processing',
    description: 'Batch video processing',
    category: 'workflow',
  },
  {
    path: '/render',
    name: 'Render Jobs',
    description: 'Video render queue',
    category: 'workflow',
  },

  // ============================================================================
  // PROJECTS ROUTES
  // ============================================================================
  {
    path: '/projects',
    name: 'Projects',
    description: 'Manage projects',
    category: 'dashboard',
  },

  // ============================================================================
  // SETTINGS & HELP ROUTES
  // ============================================================================
  {
    path: '/settings',
    name: 'Settings',
    description: 'Application settings',
    category: 'dashboard',
  },
  {
    path: '/help',
    name: 'Help & Support',
    description: 'Get help and support',
    category: 'dashboard',
  },

  // ============================================================================
  // AUTH ROUTES (Standalone - No Dashboard Layout)
  // ============================================================================
  {
    path: '/login',
    name: 'Login',
    description: 'User login',
    category: 'auth',
  },
  {
    path: '/register',
    name: 'Register',
    description: 'User registration',
    category: 'auth',
  },
  {
    path: '/verify',
    name: 'OTP Verification',
    description: 'Email verification',
    category: 'auth',
  },

  // ============================================================================
  // ONBOARDING ROUTES (Standalone)
  // ============================================================================
  {
    path: '/onboarding/welcome',
    name: 'Welcome',
    description: 'Onboarding welcome',
    category: 'onboarding',
  },
  {
    path: '/onboarding/connect-meta',
    name: 'Connect Meta',
    description: 'Connect Meta Ads',
    category: 'onboarding',
  },
  {
    path: '/onboarding/connect-google',
    name: 'Connect Google',
    description: 'Connect Google Ads',
    category: 'onboarding',
  },
  {
    path: '/onboarding/configure',
    name: 'Configure',
    description: 'Configure settings',
    category: 'onboarding',
  },
  {
    path: '/onboarding/first-campaign',
    name: 'First Campaign',
    description: 'Create first campaign',
    category: 'onboarding',
  },
  {
    path: '/onboarding/complete',
    name: 'Onboarding Complete',
    description: 'Onboarding completion',
    category: 'onboarding',
  },

  // ============================================================================
  // MARKETING PAGES (Standalone)
  // ============================================================================
  {
    path: '/landing',
    name: 'Landing Page',
    description: 'Public landing page',
    category: 'marketing',
  },
  {
    path: '/blog',
    name: 'Blog',
    description: 'Blog articles',
    category: 'marketing',
  },
  {
    path: '/company',
    name: 'Company',
    description: 'About company',
    category: 'marketing',
  },
  {
    path: '/pricing',
    name: 'Pricing',
    description: 'Pricing plans',
    category: 'marketing',
  },

  // ============================================================================
  // DEMO ROUTES (Standalone)
  // ============================================================================
  {
    path: '/demo/presentation',
    name: 'Investor Presentation',
    description: 'Investor pitch deck',
    category: 'demo',
  },
]

/**
 * Get routes by category
 */
export function getRoutesByCategory(category: RouteConfig['category']): RouteConfig[] {
  return routes.filter(route => route.category === category)
}

/**
 * Get all dashboard routes
 */
export function getDashboardRoutes(): RouteConfig[] {
  return routes.filter(route =>
    ['dashboard', 'campaign', 'analytics', 'studio', 'assets', 'tools', 'workflow'].includes(route.category)
  )
}

/**
 * Get all standalone routes (no dashboard layout)
 */
export function getStandaloneRoutes(): RouteConfig[] {
  return routes.filter(route =>
    ['auth', 'onboarding', 'marketing', 'demo'].includes(route.category)
  )
}

/**
 * Route path constants for type-safe navigation
 */
export const ROUTES = {
  // Dashboard
  HOME: '/',
  CREATOR_DASHBOARD: '/dashboard/creator',

  // Campaigns
  CAMPAIGNS: '/campaigns',
  CREATE_CAMPAIGN: '/create',
  CAMPAIGN_BUILDER: '/campaigns/builder',

  // Analytics
  ANALYTICS: '/analytics',
  ANALYTICS_DASHBOARD: '/analytics/dashboard',
  PERFORMANCE: '/analytics/performance',
  ROAS: '/analytics/roas',
  REPORTS: '/reports',

  // Studio
  STUDIO: '/studio',
  PRO_EDITOR: '/studio/pro',
  STORYBOARD: '/studio/storyboard',
  VIDEO_STUDIO: '/studio/video',
  AI_CREATIVE: '/studio/ai',
  VIDEO_GENERATOR: '/studio/generate',

  // Assets
  ASSETS: '/assets',
  LIBRARY: '/library',

  // Tools
  AD_SPY: '/spy',
  ASSISTANT: '/assistant',
  RESOURCES: '/resources',

  // Workflow
  AB_TESTING: '/testing',
  WORKFLOW: '/workflow',
  BATCH: '/batch',
  RENDER: '/render',

  // Other
  PROJECTS: '/projects',
  SETTINGS: '/settings',
  HELP: '/help',

  // Auth
  LOGIN: '/login',
  REGISTER: '/register',

  // Marketing
  LANDING: '/landing',
  PRICING: '/pricing',
} as const

export type RoutePath = typeof ROUTES[keyof typeof ROUTES]
