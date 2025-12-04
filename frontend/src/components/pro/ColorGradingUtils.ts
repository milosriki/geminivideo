/**
 * Utility functions for applying color grades to video/image data
 * These functions help integrate the ColorGradingPanel with actual video processing
 */

import { ColorGrade, CurvePoint, RGBOffset } from './ColorGradingPanel.types';

/**
 * Apply color grade to canvas ImageData
 * This is useful for canvas-based video processing
 */
export const applyColorGradeToImageData = (
  imageData: ImageData,
  grade: ColorGrade
): ImageData => {
  const data = imageData.data;
  const width = imageData.width;
  const height = imageData.height;

  // Create curve lookup tables for performance
  const masterLUT = createCurveLUT(grade.curves.master);
  const redLUT = createCurveLUT(grade.curves.red);
  const greenLUT = createCurveLUT(grade.curves.green);
  const blueLUT = createCurveLUT(grade.curves.blue);

  for (let i = 0; i < data.length; i += 4) {
    let r = data[i] / 255;
    let g = data[i + 1] / 255;
    let b = data[i + 2] / 255;

    // Apply color wheels (lift, gamma, gain)
    ({ r, g, b } = applyColorWheels(r, g, b, grade));

    // Apply exposure
    const exposureMult = Math.pow(2, grade.exposure);
    r *= exposureMult;
    g *= exposureMult;
    b *= exposureMult;

    // Apply curves
    r = applyCurveLUT(r, masterLUT);
    g = applyCurveLUT(g, masterLUT);
    b = applyCurveLUT(b, masterLUT);

    r = applyCurveLUT(r, redLUT);
    g = applyCurveLUT(g, greenLUT);
    b = applyCurveLUT(b, blueLUT);

    // Apply contrast
    const contrastFactor = grade.contrast / 100;
    r = (r - 0.5) * contrastFactor + 0.5;
    g = (g - 0.5) * contrastFactor + 0.5;
    b = (b - 0.5) * contrastFactor + 0.5;

    // Apply highlights and shadows
    const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
    const highlightsFactor = grade.highlights / 100;
    const shadowsFactor = grade.shadows / 100;

    if (luminance > 0.5) {
      // Highlights
      const factor = (luminance - 0.5) * 2 * highlightsFactor;
      r += factor;
      g += factor;
      b += factor;
    } else {
      // Shadows
      const factor = (0.5 - luminance) * 2 * shadowsFactor;
      r += factor;
      g += factor;
      b += factor;
    }

    // Apply whites and blacks
    r = applyWhitesBlacks(r, grade.whites, grade.blacks);
    g = applyWhitesBlacks(g, grade.whites, grade.blacks);
    b = applyWhitesBlacks(b, grade.whites, grade.blacks);

    // Apply temperature and tint
    ({ r, g, b } = applyTemperatureAndTint(r, g, b, grade.temperature, grade.tint));

    // Apply saturation and vibrance
    ({ r, g, b } = applySaturation(r, g, b, grade.saturation, grade.vibrance));

    // Apply HSL per color
    ({ r, g, b } = applyHSLAdjustments(r, g, b, grade));

    // Clamp values
    data[i] = Math.max(0, Math.min(255, r * 255));
    data[i + 1] = Math.max(0, Math.min(255, g * 255));
    data[i + 2] = Math.max(0, Math.min(255, b * 255));
  }

  return imageData;
};

/**
 * Apply color wheels (lift, gamma, gain) to RGB values
 */
const applyColorWheels = (
  r: number,
  g: number,
  b: number,
  grade: ColorGrade
): { r: number; g: number; b: number } => {
  const { lift, gamma, gain } = grade;

  // Lift (shadows) - affects darker areas more
  r += lift.r * (1 - r) * 0.5;
  g += lift.g * (1 - g) * 0.5;
  b += lift.b * (1 - b) * 0.5;

  // Gamma (midtones) - power function
  const gammaR = 1 + gamma.r;
  const gammaG = 1 + gamma.g;
  const gammaB = 1 + gamma.b;
  r = Math.pow(r, 1 / gammaR);
  g = Math.pow(g, 1 / gammaG);
  b = Math.pow(b, 1 / gammaB);

  // Gain (highlights) - affects brighter areas more
  r += gain.r * r * 0.5;
  g += gain.g * g * 0.5;
  b += gain.b * b * 0.5;

  return { r, g, b };
};

/**
 * Create a lookup table from curve points for performance
 */
const createCurveLUT = (points: CurvePoint[]): number[] => {
  const lut: number[] = new Array(256);
  const sortedPoints = [...points].sort((a, b) => a.x - b.x);

  for (let i = 0; i < 256; i++) {
    const x = i / 255;
    lut[i] = evaluateCurve(x, sortedPoints);
  }

  return lut;
};

/**
 * Evaluate a bezier curve at a given x position
 */
const evaluateCurve = (x: number, points: CurvePoint[]): number => {
  if (points.length < 2) return x;

  // Find the two points that x falls between
  let i = 0;
  while (i < points.length - 1 && points[i + 1].x < x) {
    i++;
  }

  if (i >= points.length - 1) return points[points.length - 1].y;

  const p0 = points[i];
  const p1 = points[i + 1];

  // Linear interpolation between points
  const t = (x - p0.x) / (p1.x - p0.x);

  // Cubic bezier interpolation for smoother curves
  const t2 = t * t;
  const t3 = t2 * t;
  const mt = 1 - t;
  const mt2 = mt * mt;
  const mt3 = mt2 * mt;

  return mt3 * p0.y + 3 * mt2 * t * p0.y + 3 * mt * t2 * p1.y + t3 * p1.y;
};

/**
 * Apply curve LUT to a normalized value
 */
const applyCurveLUT = (value: number, lut: number[]): number => {
  const index = Math.max(0, Math.min(255, Math.floor(value * 255)));
  return lut[index];
};

/**
 * Apply whites and blacks adjustments
 */
const applyWhitesBlacks = (
  value: number,
  whites: number,
  blacks: number
): number => {
  // Whites affect bright areas
  if (value > 0.7) {
    value += (whites / 100) * (value - 0.7) * 0.5;
  }

  // Blacks affect dark areas
  if (value < 0.3) {
    value += (blacks / 100) * (0.3 - value) * 0.5;
  }

  return value;
};

/**
 * Apply temperature and tint adjustments
 */
const applyTemperatureAndTint = (
  r: number,
  g: number,
  b: number,
  temperature: number,
  tint: number
): { r: number; g: number; b: number } => {
  // Temperature (cool to warm)
  const tempFactor = temperature / 100;
  r += tempFactor * 0.3;
  b -= tempFactor * 0.3;

  // Tint (green to magenta)
  const tintFactor = tint / 100;
  r += tintFactor * 0.2;
  g -= tintFactor * 0.2;
  b += tintFactor * 0.2;

  return { r, g, b };
};

/**
 * Apply saturation and vibrance
 */
const applySaturation = (
  r: number,
  g: number,
  b: number,
  saturation: number,
  vibrance: number
): { r: number; g: number; b: number } => {
  const gray = 0.299 * r + 0.587 * g + 0.114 * b;

  // Global saturation
  if (saturation !== 0) {
    const satFactor = (saturation + 100) / 100;
    r = gray + (r - gray) * satFactor;
    g = gray + (g - gray) * satFactor;
    b = gray + (b - gray) * satFactor;
  }

  // Vibrance (smart saturation that protects skin tones)
  if (vibrance !== 0) {
    const maxRGB = Math.max(r, g, b);
    const minRGB = Math.min(r, g, b);
    const currentSat = maxRGB - minRGB;

    // Vibrance affects less saturated colors more
    const vibFactor = (vibrance / 100) * (1 - currentSat);

    r = gray + (r - gray) * (1 + vibFactor);
    g = gray + (g - gray) * (1 + vibFactor);
    b = gray + (b - gray) * (1 + vibFactor);
  }

  return { r, g, b };
};

/**
 * Apply HSL adjustments per color range
 */
const applyHSLAdjustments = (
  r: number,
  g: number,
  b: number,
  grade: ColorGrade
): { r: number; g: number; b: number } => {
  // Convert RGB to HSL
  const hsl = rgbToHsl(r, g, b);

  // Determine which color range this pixel belongs to
  const colorRange = getColorRange(hsl.h);

  if (colorRange && grade.hsl[colorRange]) {
    const adjustment = grade.hsl[colorRange];

    // Apply adjustments
    hsl.h += adjustment.h;
    hsl.s += adjustment.s / 100;
    hsl.l += adjustment.l / 100;

    // Clamp values
    hsl.h = ((hsl.h % 360) + 360) % 360;
    hsl.s = Math.max(0, Math.min(1, hsl.s));
    hsl.l = Math.max(0, Math.min(1, hsl.l));

    // Convert back to RGB
    return hslToRgb(hsl.h, hsl.s, hsl.l);
  }

  return { r, g, b };
};

/**
 * Convert RGB to HSL
 */
const rgbToHsl = (
  r: number,
  g: number,
  b: number
): { h: number; s: number; l: number } => {
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const l = (max + min) / 2;

  if (max === min) {
    return { h: 0, s: 0, l };
  }

  const d = max - min;
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

  let h = 0;
  switch (max) {
    case r:
      h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
      break;
    case g:
      h = ((b - r) / d + 2) / 6;
      break;
    case b:
      h = ((r - g) / d + 4) / 6;
      break;
  }

  return { h: h * 360, s, l };
};

/**
 * Convert HSL to RGB
 */
const hslToRgb = (h: number, s: number, l: number): { r: number; g: number; b: number } => {
  h = h / 360;

  if (s === 0) {
    return { r: l, g: l, b: l };
  }

  const hue2rgb = (p: number, q: number, t: number): number => {
    if (t < 0) t += 1;
    if (t > 1) t -= 1;
    if (t < 1 / 6) return p + (q - p) * 6 * t;
    if (t < 1 / 2) return q;
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
    return p;
  };

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
  const p = 2 * l - q;

  return {
    r: hue2rgb(p, q, h + 1 / 3),
    g: hue2rgb(p, q, h),
    b: hue2rgb(p, q, h - 1 / 3),
  };
};

/**
 * Get color range from hue value
 */
const getColorRange = (
  hue: number
): 'red' | 'orange' | 'yellow' | 'green' | 'cyan' | 'blue' | 'purple' | 'magenta' | null => {
  if (hue >= 345 || hue < 15) return 'red';
  if (hue >= 15 && hue < 45) return 'orange';
  if (hue >= 45 && hue < 75) return 'yellow';
  if (hue >= 75 && hue < 155) return 'green';
  if (hue >= 155 && hue < 195) return 'cyan';
  if (hue >= 195 && hue < 255) return 'blue';
  if (hue >= 255 && hue < 295) return 'purple';
  if (hue >= 295 && hue < 345) return 'magenta';
  return null;
};

/**
 * Generate CSS filter string from color grade (limited functionality)
 * This is a fallback for browsers that don't support canvas/WebGL
 */
export const generateCSSFilters = (grade: ColorGrade): string => {
  const filters: string[] = [];

  // Exposure -> brightness
  const brightness = 100 + grade.exposure * 20;
  filters.push(`brightness(${brightness}%)`);

  // Contrast
  filters.push(`contrast(${grade.contrast}%)`);

  // Saturation
  const saturation = 100 + grade.saturation;
  filters.push(`saturate(${saturation}%)`);

  // Hue rotation (approximation from temperature)
  if (grade.temperature !== 0) {
    filters.push(`hue-rotate(${grade.temperature * 0.5}deg)`);
  }

  return filters.join(' ');
};

/**
 * Generate WebGL shader code for color grading
 * Returns fragment shader source code
 */
export const generateWebGLShader = (grade: ColorGrade): string => {
  return `
    precision mediump float;
    uniform sampler2D u_texture;
    varying vec2 v_texCoord;

    void main() {
      vec4 color = texture2D(u_texture, v_texCoord);

      // Apply exposure
      color.rgb *= pow(2.0, ${grade.exposure.toFixed(2)});

      // Apply contrast
      color.rgb = (color.rgb - 0.5) * ${(grade.contrast / 100).toFixed(2)} + 0.5;

      // Apply saturation
      float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
      color.rgb = mix(vec3(gray), color.rgb, ${((grade.saturation + 100) / 100).toFixed(2)});

      // Clamp
      color.rgb = clamp(color.rgb, 0.0, 1.0);

      gl_FragColor = color;
    }
  `;
};

/**
 * Apply color grade to a video element using canvas
 */
export const applyColorGradeToVideo = (
  videoElement: HTMLVideoElement,
  outputCanvas: HTMLCanvasElement,
  grade: ColorGrade
): void => {
  const ctx = outputCanvas.getContext('2d', { willReadFrequently: true });
  if (!ctx) return;

  // Match canvas size to video
  outputCanvas.width = videoElement.videoWidth;
  outputCanvas.height = videoElement.videoHeight;

  const processFrame = () => {
    // Draw video frame to canvas
    ctx.drawImage(videoElement, 0, 0, outputCanvas.width, outputCanvas.height);

    // Get image data
    const imageData = ctx.getImageData(0, 0, outputCanvas.width, outputCanvas.height);

    // Apply color grade
    const gradedData = applyColorGradeToImageData(imageData, grade);

    // Put back to canvas
    ctx.putImageData(gradedData, 0, 0);

    // Continue processing if video is playing
    if (!videoElement.paused && !videoElement.ended) {
      requestAnimationFrame(processFrame);
    }
  };

  processFrame();
};

/**
 * Export color grade to JSON string
 */
export const exportColorGrade = (grade: ColorGrade, name?: string): string => {
  return JSON.stringify(
    {
      version: '1.0.0',
      name: name || 'Untitled Grade',
      timestamp: new Date().toISOString(),
      grade,
    },
    null,
    2
  );
};

/**
 * Import color grade from JSON string
 */
export const importColorGrade = (json: string): ColorGrade | null => {
  try {
    const parsed = JSON.parse(json);
    if (parsed.grade) {
      return parsed.grade;
    }
    return parsed;
  } catch (error) {
    console.error('Failed to import color grade:', error);
    return null;
  }
};

/**
 * Interpolate between two color grades
 * Useful for animated transitions
 */
export const interpolateColorGrades = (
  gradeA: ColorGrade,
  gradeB: ColorGrade,
  t: number // 0 to 1
): ColorGrade => {
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

  const lerpRGB = (a: RGBOffset, b: RGBOffset): RGBOffset => ({
    r: lerp(a.r, b.r, t),
    g: lerp(a.g, b.g, t),
    b: lerp(a.b, b.b, t),
  });

  return {
    lift: lerpRGB(gradeA.lift, gradeB.lift),
    gamma: lerpRGB(gradeA.gamma, gradeB.gamma),
    gain: lerpRGB(gradeA.gain, gradeB.gain),
    curves: gradeA.curves, // Curves don't interpolate well, use A
    hsl: gradeA.hsl, // HSL is complex, use A
    exposure: lerp(gradeA.exposure, gradeB.exposure, t),
    contrast: lerp(gradeA.contrast, gradeB.contrast, t),
    highlights: lerp(gradeA.highlights, gradeB.highlights, t),
    shadows: lerp(gradeA.shadows, gradeB.shadows, t),
    whites: lerp(gradeA.whites, gradeB.whites, t),
    blacks: lerp(gradeA.blacks, gradeB.blacks, t),
    temperature: lerp(gradeA.temperature, gradeB.temperature, t),
    tint: lerp(gradeA.tint, gradeB.tint, t),
    vibrance: lerp(gradeA.vibrance, gradeB.vibrance, t),
    saturation: lerp(gradeA.saturation, gradeB.saturation, t),
    selectedLUT: t < 0.5 ? gradeA.selectedLUT : gradeB.selectedLUT,
  };
};

export default {
  applyColorGradeToImageData,
  generateCSSFilters,
  generateWebGLShader,
  applyColorGradeToVideo,
  exportColorGrade,
  importColorGrade,
  interpolateColorGrades,
};
