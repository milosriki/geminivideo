/**
 * Pro-Grade Color Grading Panel - Export Module
 * Complete color grading solution for professional video editing
 */

// Main component
export { ColorGradingPanel } from './ColorGradingPanel';
export { default as ColorGradingPanelDefault } from './ColorGradingPanel';

// Demo component
export { ColorGradingPanelDemo } from './ColorGradingPanelDemo';
export { default as ColorGradingPanelDemoDefault } from './ColorGradingPanelDemo';

// Type definitions
export type {
  ColorGrade,
  ColorGradeConfig,
  CurvePoint,
  RGBOffset,
  HSLAdjustment,
  LUTPreset,
  LookUpTablePreset,
  ColorGradingPanelProps,
  ColorWheelProps,
  CurveEditorProps,
  SavedPreset,
  CollapsibleSections,
  HistoryEntry,
  VectorscopeData,
  ColorGradeExport,
  CurveType,
  ColorRange,
  LUTCategory,
  ColorWheelType,
  ColorGradeUpdate,
  ComparisonMode,
  ScopeType,
} from './ColorGradingPanel.types';

// Constants
export { DEFAULT_COLOR_GRADE } from './ColorGradingPanel.types';

// Utility functions
export {
  validateColorGrade,
  mergeColorGrade,
  cloneColorGrade,
  areColorGradesEqual,
} from './ColorGradingPanel.types';

// Color grading utilities
export {
  applyColorGradeToImageData,
  generateCSSFilters,
  generateWebGLShader,
  applyColorGradeToVideo,
  exportColorGrade,
  importColorGrade,
  interpolateColorGrades,
} from './ColorGradingUtils';

// Default export (main component)
export { ColorGradingPanel as default } from './ColorGradingPanel';

/**
 * Quick Start Usage:
 *
 * ```tsx
 * import { ColorGradingPanel } from './components/pro';
 * import './components/pro/ColorGradingPanel.css';
 *
 * function MyEditor() {
 *   const handleGradeChange = (grade) => {
 *     console.log('Grade changed:', grade);
 *   };
 *
 *   return <ColorGradingPanel onGradeChange={handleGradeChange} />;
 * }
 * ```
 */
