
export interface AdCreative {
  primarySourceFileName: string;
  variationTitle: string;
  headline: string;
  body: string;
  cta: string;
  editPlan: EditScene[];
  ranking?: CreativeRanking; // For holding ranked data on the client
  // FIX: Add properties for ranked data used by AdCreativeCard
  __roiScore?: number | null;
  __hookScore?: number | null;
  __ctaScore?: number | null;
  __reasons?: string;
}

export interface EditScene {
  timestamp: string;
  visual: string;
  edit: string;
  overlayText?: string;
  sourceFile?: string;
}

export interface VideoFile {
    file: File;
    id: string;
    thumbnail: string;
    status: 'pending' | 'processing' | 'analyzed' | 'error';
    analysisResult?: VideoAnalysisResult;
    error?: string;
    progress?: number; // For per-file progress tracking
    loadingMessage?: string; // For per-file status messages
}

export interface AudioAnalysisResult {
  summary: string;
  keyPhrases: string[];
  callsToAction: string[];
}

export interface VideoAnalysisResult {
    fileName: string;
    rank: number;
    justification: string;
    summary: string;
    sceneDescriptions: Array<{ timestamp: string; description: string; }>;
    keyObjects: string[];
    emotionalTone: string[];
    veoHookSuggestion?: string;
    audioAnalysis?: AudioAnalysisResult;
    hooks?: string[];
    angles?: string[];
    risks?: string[];
    sentiments?: string[];
    keyMoments?: Array<{ t: number; note: string }>;
}

export interface CampaignStrategy {
    primaryVideoFileName: string;
    bRollFileNames: string[];
    strategyJustification: string;
    videoAnalyses: VideoAnalysisResult[];
    summary?: string;
    keyAngles?: string[];
    risksToAvoid?: string[];
}

export interface TranscribedWord {
  word: string;
  start: number;
  end: number;
}

export type AdvancedEdit = { id: string } & (
  | { type: 'trim'; start: string; end: string }
  | { type: 'text'; text: string; start: string; end: string; position: 'top' | 'center' | 'bottom'; fontSize: number; }
  | { type: 'image'; file: File; position: 'top_left' | 'top_right' | 'bottom_left' | 'bottom_right'; scale: number; opacity: number; }
  | { type: 'speed'; factor: number }
  | { type: 'filter'; name: 'grayscale' | 'sepia' | 'negate' | 'vignette' }
  | { type: 'color'; brightness: number; contrast: number; saturation: number; }
  | { type: 'volume'; level: number; }
  | { type: 'fade'; typeIn: boolean; typeOut: boolean; duration: number; }
  | { type: 'crop'; ratio: '16:9' | '9:16' | '1:1' | '4:5'; }
  | { type: 'subtitles'; text: string; } // Simplified for now
  | { type: 'mute' }
);

export interface ChatMessage {
  role: 'user' | 'model';
  parts: { text: string }[];
}

export interface CampaignBrief {
    productName: string;
    offer: string;
    targetMarket: string;
    angle: string;
    cta: string;
    tone: 'direct'|'empathetic'|'authoritative'|'playful'|'inspirational';
    platform: 'reels'|'shorts'|'tiktok'|'feed'|'stories';
    serviceName?: string;
    idealClient?: string;
    coreBenefits?: string;
    uniqueSellingPoint?: string;
    painPoints?: string;
    emotionalResponse?: string;
    goals?: string[];
    complianceRules?: string[];
}

export interface Avatar {
    key: string;
    name: string;
    description?: string;
    pain_points?: string;
    desires?: string;
}

export interface CreativeRanking {
  index: number;
  roiScore: number;
  reasons: string;
  hookScore?: number;
  ctaScore?: number;
}

export interface StoryboardPanel {
  description: string;
  image_prompt: string;
  imageUrl?: string;
}

// Google Drive API v3 File Resource Types
// Based on: https://developers.google.com/drive/api/v3/reference/files#resource

export interface GoogleDriveFile {
  /** The ID of the file */
  id: string;
  /** The name of the file */
  name: string;
  /** The MIME type of the file */
  mimeType: string;
  /** A link to the file's thumbnail (if available) */
  thumbnailLink?: string;
  /** A link for downloading the file's content */
  webContentLink?: string;
  /** Video media metadata (if the file is a video) */
  videoMediaMetadata?: {
    /** The duration of the video in milliseconds */
    durationMillis?: string;
    /** The width of the video in pixels */
    width?: number;
    /** The height of the video in pixels */
    height?: number;
  };
  /** The size of the file in bytes */
  size?: string;
  /** The time at which the file was created (RFC 3339 date-time) */
  createdTime?: string;
  /** The last time the file was modified by anyone (RFC 3339 date-time) */
  modifiedTime?: string;
  /** Whether the file has been trashed */
  trashed?: boolean;
}