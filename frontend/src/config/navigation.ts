import {
  LucideIcon,
  Home,
  Rocket,
  Film,
  BarChart3,
  Search,
  Folder,
  Settings,
  Palette,
  Music,
  Clock,
  Target,
  LineChart,
  FlaskConical,
  TrendingUp,
  Bookmark,
  FolderOpen,
  LayoutTemplate,
  Video,
  Sparkles,
  Wand2,
  Zap,
  Cpu
} from 'lucide-react';

export interface NavItem {
  label: string;
  icon?: LucideIcon;
  href?: string;
  children?: NavItem[];
}

export const navigation: NavItem[] = [
  {
    label: 'Home',
    icon: Home,
    href: '/'
  },
  {
    label: 'Create',
    icon: Rocket,
    children: [
      { label: 'Campaign Builder', icon: Target, href: '/campaigns' },
      { label: 'AI Creative Studio', icon: Sparkles, href: '/studio/ai' },
      { label: 'Video Generator', icon: Wand2, href: '/generator' }
    ]
  },
  {
    label: 'Studio',
    icon: Film,
    children: [
      { label: 'Pro Video Editor', icon: Video, href: '/studio' },
      { label: 'Timeline Editor', icon: Clock, href: '/studio/timeline' },
      { label: 'Color Grading', icon: Palette, href: '/studio/color' },
      { label: 'Audio Mixer', icon: Music, href: '/studio/audio' }
    ]
  },
  {
    label: 'Analytics',
    icon: BarChart3,
    children: [
      { label: 'Dashboard', icon: BarChart3, href: '/analytics' },
      { label: 'ROAS Tracking', icon: LineChart, href: '/analytics/roas' },
      { label: 'Predictions', icon: TrendingUp, href: '/analytics/predictions' },
      { label: 'A/B Testing', icon: FlaskConical, href: '/testing' }
    ]
  },
  {
    label: 'Ad Spy',
    icon: Search,
    children: [
      { label: 'Competitor Research', icon: Search, href: '/spy' },
      { label: 'Trending Ads', icon: TrendingUp, href: '/spy/trending' },
      { label: 'Swipe File', icon: Bookmark, href: '/spy/swipe' }
    ]
  },
  {
    label: 'Library',
    icon: Folder,
    children: [
      { label: 'Assets', icon: FolderOpen, href: '/library' },
      { label: 'Campaigns', icon: Target, href: '/library/campaigns' },
      { label: 'Templates', icon: LayoutTemplate, href: '/library/templates' }
    ]
  },
  {
    label: 'Antigravity',
    icon: Zap,
    children: [
      { label: 'Skills Constellation', icon: Cpu, href: '/skills' },
      { label: 'Agent Status', icon: Sparkles, href: '/skills/status' }
    ]
  },
  {
    label: 'Settings',
    icon: Settings,
    href: '/settings'
  }
];
