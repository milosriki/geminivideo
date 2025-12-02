/**
 * Type definitions for the Pro-Grade Color Grading Panel
 * These types can be imported separately for better modularity
 */

/**
 * Represents a point on a curve with x and y coordinates (0-1 range)
 */
export interface CurvePoint {
  x: number; // 0 to 1
  y: number; // 0 to 1
}

/**
 * RGB color offset for color wheels (-1 to 1 range)
 */
export interface RGBOffset {
  r: number; // -1 to 1
  g: number; // -1 to 1
  b: number; // -1 to 1
}

/**
 * HSL adjustment values for a specific color range
 */
export interface HSLAdjustment {
  h: number; // Hue: -180 to 180
  s: number; // Saturation: -100 to 100
  l: number; // Luminance: -100 to 100
}

/**
 * Complete color grading configuration
 */
export interface ColorGrade {
  // Color Wheels - Control shadows, midtones, and highlights
  lift: RGBOffset;  // Shadows
  gamma: RGBOffset; // Midtones
  gain: RGBOffset;  // Highlights

  // RGB Curves - Per-channel tone curves
  curves: {
    red: CurvePoint[];
    green: CurvePoint[];
    blue: CurvePoint[];
    master: CurvePoint[]; // Affects all channels
  };

  // HSL - Per-color adjustments
  hsl: {
    red: HSLAdjustment;
    orange: HSLAdjustment;
    yellow: HSLAdjustment;
    green: HSLAdjustment;
    cyan: HSLAdjustment;
    blue: HSLAdjustment;
    purple: HSLAdjustment;
    magenta: HSLAdjustment;
  };

  // Basic Adjustments
  exposure: number;    // -5 to 5
  contrast: number;    // 0 to 200
  highlights: number;  // -100 to 100
  shadows: number;     // -100 to 100
  whites: number;      // -100 to 100
  blacks: number;      // -100 to 100

  // Color Temperature and Tint
  temperature: number; // -100 (cool) to 100 (warm)
  tint: number;       // -100 (green) to 100 (magenta)

  // Saturation Controls
  vibrance: number;   // -100 to 100 (smart saturation)
  saturation: number; // -100 to 100 (global saturation)

  // LUT Selection
  selectedLUT: string | null; // LUT preset ID or null
}

/**
 * LUT (Look-Up Table) preset definition
 */
export interface LUTPreset {
  id: string;          // Unique identifier
  name: string;        // Display name
  category: string;    // Category (e.g., "Cinematic", "Vintage")
  thumbnail: string;   // Emoji or image URL
  description: string; // Brief description
  lutData?: number[][][]; // Optional: actual LUT data (3D array)
}

/**
 * Props for the main ColorGradingPanel component
 */
export interface ColorGradingPanelProps {
  /**
   * Callback fired whenever any color grade parameter changes
   * @param grade - The updated color grade configuration
   */
  onGradeChange?: (grade: ColorGrade) => void;

  /**
   * Initial color grade values (partial is allowed)
   * Missing values will be filled with defaults
   */
  initialGrade?: Partial<ColorGrade>;

  /**
   * Optional custom LUT presets to display
   */
  customLUTs?: LUTPreset[];

  /**
   * Whether to show the vectorscope visualization
   * @default false
   */
  showVectorscope?: boolean;

  /**
   * Whether to enable real-time preview updates
   * @default true
   */
  realtimePreview?: boolean;

  /**
   * Maximum number of control points allowed per curve
   * @default 10
   */
  maxCurvePoints?: number;
}

/**
 * Props for the ColorWheel component
 */
export interface ColorWheelProps {
  value: RGBOffset;
  onChange: (value: RGBOffset) => void;
  label: string;
  size?: number;
  disabled?: boolean;
}

/**
 * Props for the CurveEditor component
 */
export interface CurveEditorProps {
  points: CurvePoint[];
  onChange: (points: CurvePoint[]) => void;
  color: string;
  label: string;
  maxPoints?: number;
  disabled?: boolean;
}

/**
 * Saved preset with name and grade
 */
export interface SavedPreset {
  id: string;
  name: string;
  grade: ColorGrade;
  createdAt: Date;
  thumbnail?: string;
}

/**
 * Collapsible section state
 */
export interface CollapsibleSections {
  colorWheels: boolean;
  curves: boolean;
  hsl: boolean;
  basic: boolean;
  tempTint: boolean;
  vibrance: boolean;
  lut: boolean;
  vectorscope: boolean;
}

/**
 * Color grading history entry for undo/redo
 */
export interface HistoryEntry {
  timestamp: Date;
  grade: ColorGrade;
  action: string; // Description of the action
}

/**
 * Vectorscope data for color analysis
 */
export interface VectorscopeData {
  points: { x: number; y: number; intensity: number }[];
  skinToneIndicator?: { x: number; y: number };
}

/**
 * Export format for color grades
 */
export interface ColorGradeExport {
  version: string; // Format version for compatibility
  name?: string;
  description?: string;
  grade: ColorGrade;
  metadata?: {
    createdAt: string;
    software: string;
    author?: string;
  };
}

/**
 * Curve types for the RGB curve editor
 */
export type CurveType = 'master' | 'red' | 'green' | 'blue';

/**
 * Color ranges for HSL adjustments
 */
export type ColorRange = 'red' | 'orange' | 'yellow' | 'green' | 'cyan' | 'blue' | 'purple' | 'magenta';

/**
 * LUT categories for organization
 */
export type LUTCategory = 'Cinematic' | 'Vintage' | 'Natural' | 'Creative' | 'Custom' | 'Technical';

/**
 * Color wheel types
 */
export type ColorWheelType = 'lift' | 'gamma' | 'gain';

/**
 * Utility type for partial updates
 */
export type ColorGradeUpdate = Partial<ColorGrade>;

/**
 * Comparison mode for before/after
 */
export type ComparisonMode = 'off' | 'split' | 'toggle' | 'side-by-side';

/**
 * Scope types for video analysis
 */
export type ScopeType = 'vectorscope' | 'waveform' | 'histogram' | 'parade';

/**
 * Default color grade values
 */
export const DEFAULT_COLOR_GRADE: ColorGrade = {
  lift: { r: 0, g: 0, b: 0 },
  gamma: { r: 0, g: 0, b: 0 },
  gain: { r: 0, g: 0, b: 0 },
  curves: {
    red: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
    green: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
    blue: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
    master: [{ x: 0, y: 0 }, { x: 1, y: 1 }],
  },
  hsl: {
    red: { h: 0, s: 0, l: 0 },
    orange: { h: 0, s: 0, l: 0 },
    yellow: { h: 0, s: 0, l: 0 },
    green: { h: 0, s: 0, l: 0 },
    cyan: { h: 0, s: 0, l: 0 },
    blue: { h: 0, s: 0, l: 0 },
    purple: { h: 0, s: 0, l: 0 },
    magenta: { h: 0, s: 0, l: 0 },
  },
  exposure: 0,
  contrast: 100,
  highlights: 0,
  shadows: 0,
  whites: 0,
  blacks: 0,
  temperature: 0,
  tint: 0,
  vibrance: 0,
  saturation: 0,
  selectedLUT: null,
};

/**
 * Utility function to validate color grade values
 */
export const validateColorGrade = (grade: Partial<ColorGrade>): boolean => {
  try {
    // Validate exposure
    if (grade.exposure !== undefined && (grade.exposure < -5 || grade.exposure > 5)) {
      return false;
    }

    // Validate contrast
    if (grade.contrast !== undefined && (grade.contrast < 0 || grade.contrast > 200)) {
      return false;
    }

    // Validate RGB offsets
    const validateRGB = (rgb?: RGBOffset) => {
      if (!rgb) return true;
      return rgb.r >= -1 && rgb.r <= 1 &&
             rgb.g >= -1 && rgb.g <= 1 &&
             rgb.b >= -1 && rgb.b <= 1;
    };

    if (!validateRGB(grade.lift) || !validateRGB(grade.gamma) || !validateRGB(grade.gain)) {
      return false;
    }

    return true;
  } catch {
    return false;
  }
};

/**
 * Utility function to merge partial grade with defaults
 */
export const mergeColorGrade = (partial: Partial<ColorGrade>): ColorGrade => {
  return {
    ...DEFAULT_COLOR_GRADE,
    ...partial,
    curves: {
      ...DEFAULT_COLOR_GRADE.curves,
      ...partial.curves,
    },
    hsl: {
      ...DEFAULT_COLOR_GRADE.hsl,
      ...partial.hsl,
    },
  };
};

/**
 * Utility function to clone a color grade
 */
export const cloneColorGrade = (grade: ColorGrade): ColorGrade => {
  return JSON.parse(JSON.stringify(grade));
};

/**
 * Utility function to compare two color grades
 */
export const areColorGradesEqual = (a: ColorGrade, b: ColorGrade): boolean => {
  return JSON.stringify(a) === JSON.stringify(b);
};

/**
 * Export types for external use
 */
export type {
  // Re-export for convenience
  ColorGrade as ColorGradeConfig,
  LUTPreset as LookUpTablePreset,
};
