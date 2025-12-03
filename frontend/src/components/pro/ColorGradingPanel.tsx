import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Palette,
  Copy,
  Clipboard,
  RotateCcw,
  Save,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  Download,
  Upload
} from 'lucide-react';

// ==================== INTERFACES ====================

interface ColorGrade {
  // Color Wheels
  lift: { r: number; g: number; b: number };
  gamma: { r: number; g: number; b: number };
  gain: { r: number; g: number; b: number };

  // RGB Curves
  curves: {
    red: CurvePoint[];
    green: CurvePoint[];
    blue: CurvePoint[];
    master: CurvePoint[];
  };

  // HSL per color
  hsl: {
    red: { h: number; s: number; l: number };
    orange: { h: number; s: number; l: number };
    yellow: { h: number; s: number; l: number };
    green: { h: number; s: number; l: number };
    cyan: { h: number; s: number; l: number };
    blue: { h: number; s: number; l: number };
    purple: { h: number; s: number; l: number };
    magenta: { h: number; s: number; l: number };
  };

  // Basic Adjustments
  exposure: number;
  contrast: number;
  highlights: number;
  shadows: number;
  whites: number;
  blacks: number;

  // Temperature & Tint
  temperature: number;
  tint: number;

  // Vibrance & Saturation
  vibrance: number;
  saturation: number;

  // LUT
  selectedLUT: string | null;
}

interface CurvePoint {
  x: number;
  y: number;
}

interface LUTPreset {
  id: string;
  name: string;
  category: string;
  thumbnail: string;
  description: string;
}

interface ColorGradingPanelProps {
  onGradeChange?: (grade: ColorGrade) => void;
  initialGrade?: Partial<ColorGrade>;
}

// ==================== DEFAULT VALUES ====================

const DEFAULT_GRADE: ColorGrade = {
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

const LUT_PRESETS: LUTPreset[] = [
  {
    id: 'cinematic-teal-orange',
    name: 'Cinematic Teal & Orange',
    category: 'Cinematic',
    thumbnail: '🎬',
    description: 'Classic Hollywood blockbuster look',
  },
  {
    id: 'vintage-film',
    name: 'Vintage Film',
    category: 'Vintage',
    thumbnail: '📹',
    description: 'Warm vintage film aesthetic',
  },
  {
    id: 'moody-dark',
    name: 'Moody Dark',
    category: 'Cinematic',
    thumbnail: '🌙',
    description: 'Dark and moody atmosphere',
  },
  {
    id: 'bright-airy',
    name: 'Bright & Airy',
    category: 'Natural',
    thumbnail: '☀️',
    description: 'Light and airy natural look',
  },
  {
    id: 'cyberpunk',
    name: 'Cyberpunk',
    category: 'Creative',
    thumbnail: '🌆',
    description: 'Neon and high contrast',
  },
  {
    id: 'bleach-bypass',
    name: 'Bleach Bypass',
    category: 'Creative',
    thumbnail: '🎨',
    description: 'Desaturated high contrast',
  },
  {
    id: 'golden-hour',
    name: 'Golden Hour',
    category: 'Natural',
    thumbnail: '🌅',
    description: 'Warm sunset tones',
  },
  {
    id: 'noir',
    name: 'Film Noir',
    category: 'Vintage',
    thumbnail: '🎭',
    description: 'Classic black and white contrast',
  },
];

// ==================== COLOR WHEEL COMPONENT ====================

interface ColorWheelProps {
  value: { r: number; g: number; b: number };
  onChange: (value: { r: number; g: number; b: number }) => void;
  label: string;
  size?: number;
}

const ColorWheel: React.FC<ColorWheelProps> = ({ value, onChange, label, size = 150 }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const drawWheel = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size / 2 - 10;

    // Clear canvas
    ctx.clearRect(0, 0, size, size);

    // Draw color wheel
    for (let angle = 0; angle < 360; angle++) {
      const startAngle = (angle - 90) * Math.PI / 180;
      const endAngle = (angle - 89) * Math.PI / 180;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, endAngle);
      ctx.closePath();

      const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, radius);
      gradient.addColorStop(0, '#ffffff');
      gradient.addColorStop(1, `hsl(${angle}, 100%, 50%)`);

      ctx.fillStyle = gradient;
      ctx.fill();
    }

    // Draw center circle (neutral)
    ctx.beginPath();
    ctx.arc(centerX, centerY, 15, 0, 2 * Math.PI);
    ctx.fillStyle = '#808080';
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw current position indicator
    const { r, g, b } = value;
    const offsetX = (r - g) * radius * 0.7;
    const offsetY = (b - (r + g) / 2) * radius * 0.7;

    ctx.beginPath();
    ctx.arc(centerX + offsetX, centerY + offsetY, 8, 0, 2 * Math.PI);
    ctx.fillStyle = `rgb(${128 + r * 127}, ${128 + g * 127}, ${128 + b * 127})`;
    ctx.fill();
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    ctx.stroke();
  }, [value, size]);

  useEffect(() => {
    drawWheel();
  }, [drawWheel]);

  const handleInteraction = useCallback((clientX: number, clientY: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = clientX - rect.left;
    const y = clientY - rect.top;

    const centerX = size / 2;
    const centerY = size / 2;
    const radius = size / 2 - 10;

    const dx = x - centerX;
    const dy = y - centerY;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance > radius) return;

    const normalizedX = dx / (radius * 0.7);
    const normalizedY = dy / (radius * 0.7);

    // Convert to RGB offsets
    const r = Math.max(-1, Math.min(1, normalizedX));
    const b = Math.max(-1, Math.min(1, normalizedY));
    const g = Math.max(-1, Math.min(1, -normalizedX));

    onChange({ r, g, b });
  }, [onChange, size]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true);
    handleInteraction(e.clientX, e.clientY);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      handleInteraction(e.clientX, e.clientY);
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleReset = () => {
    onChange({ r: 0, g: 0, b: 0 });
  };

  return (
    <div className="color-wheel-container">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gray-300">{label}</label>
        <button
          onClick={handleReset}
          className="text-xs text-blue-400 hover:text-blue-300"
          title="Reset"
        >
          Reset
        </button>
      </div>
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="cursor-crosshair border border-gray-700 rounded"
        style={{ display: 'block', margin: '0 auto' }}
      />
    </div>
  );
};

// ==================== CURVE EDITOR COMPONENT ====================

interface CurveEditorProps {
  points: CurvePoint[];
  onChange: (points: CurvePoint[]) => void;
  color: string;
  label: string;
}

const CurveEditor: React.FC<CurveEditorProps> = ({ points, onChange, color, label }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedPoint, setSelectedPoint] = useState<number | null>(null);
  const size = 200;

  const drawCurve = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, size, size);

    // Draw grid
    ctx.strokeStyle = '#333333';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const pos = (i * size) / 4;
      ctx.beginPath();
      ctx.moveTo(pos, 0);
      ctx.lineTo(pos, size);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, pos);
      ctx.lineTo(size, pos);
      ctx.stroke();
    }

    // Draw diagonal reference line
    ctx.strokeStyle = '#444444';
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    ctx.moveTo(0, size);
    ctx.lineTo(size, 0);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw curve
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.beginPath();

    const sortedPoints = [...points].sort((a, b) => a.x - b.x);

    sortedPoints.forEach((point, index) => {
      const x = point.x * size;
      const y = (1 - point.y) * size;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        const prevPoint = sortedPoints[index - 1];
        const prevX = prevPoint.x * size;
        const prevY = (1 - prevPoint.y) * size;

        // Smooth bezier curve
        const cpX1 = prevX + (x - prevX) / 3;
        const cpY1 = prevY;
        const cpX2 = prevX + (2 * (x - prevX)) / 3;
        const cpY2 = y;

        ctx.bezierCurveTo(cpX1, cpY1, cpX2, cpY2, x, y);
      }
    });

    ctx.stroke();

    // Draw points
    sortedPoints.forEach((point, index) => {
      const x = point.x * size;
      const y = (1 - point.y) * size;

      ctx.beginPath();
      ctx.arc(x, y, selectedPoint === index ? 6 : 4, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }, [points, color, selectedPoint, size]);

  useEffect(() => {
    drawCurve();
  }, [drawCurve]);

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = (e.clientX - rect.left) / size;
    const y = 1 - (e.clientY - rect.top) / size;

    // Check if clicking near existing point
    const pointIndex = points.findIndex((p) => {
      const dx = Math.abs(p.x - x);
      const dy = Math.abs(p.y - y);
      return dx < 0.05 && dy < 0.05;
    });

    if (pointIndex !== -1) {
      setSelectedPoint(pointIndex);
    } else if (points.length < 10) {
      // Add new point
      const newPoints = [...points, { x, y }].sort((a, b) => a.x - b.x);
      onChange(newPoints);
      setSelectedPoint(newPoints.findIndex((p) => p.x === x && p.y === y));
    }
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (selectedPoint === null) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / size));
    const y = Math.max(0, Math.min(1, 1 - (e.clientY - rect.top) / size));

    const newPoints = [...points];

    // Prevent moving first and last points horizontally
    if (selectedPoint === 0) {
      newPoints[selectedPoint] = { x: 0, y };
    } else if (selectedPoint === points.length - 1) {
      newPoints[selectedPoint] = { x: 1, y };
    } else {
      newPoints[selectedPoint] = { x, y };
    }

    onChange(newPoints);
  };

  const handleMouseUp = () => {
    setSelectedPoint(null);
  };

  const handleReset = () => {
    onChange([{ x: 0, y: 0 }, { x: 1, y: 1 }]);
  };

  return (
    <div className="curve-editor-container">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium" style={{ color }}>{label}</label>
        <button
          onClick={handleReset}
          className="text-xs text-blue-400 hover:text-blue-300"
        >
          Reset
        </button>
      </div>
      <canvas
        ref={canvasRef}
        width={size}
        height={size}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        className="cursor-crosshair border border-gray-700 rounded bg-gray-900"
        style={{ display: 'block' }}
      />
    </div>
  );
};

// ==================== MAIN COMPONENT ====================

export const ColorGradingPanel: React.FC<ColorGradingPanelProps> = ({
  onGradeChange,
  initialGrade,
}) => {
  const [colorGrade, setColorGrade] = useState<ColorGrade>({
    ...DEFAULT_GRADE,
    ...initialGrade,
  });

  const [clipboard, setClipboard] = useState<ColorGrade | null>(null);
  const [showPreview, setShowPreview] = useState(true);
  const [activeCurve, setActiveCurve] = useState<'master' | 'red' | 'green' | 'blue'>('master');
  const [savedPresets, setSavedPresets] = useState<{ name: string; grade: ColorGrade }[]>([]);

  // Collapsible sections
  const [expandedSections, setExpandedSections] = useState({
    colorWheels: true,
    curves: false,
    hsl: false,
    basic: true,
    tempTint: true,
    vibrance: true,
    lut: false,
    vectorscope: false,
  });

  const updateGrade = useCallback((updates: Partial<ColorGrade>) => {
    setColorGrade((prev) => {
      const newGrade = { ...prev, ...updates };
      onGradeChange?.(newGrade);
      return newGrade;
    });
  }, [onGradeChange]);

  const handleCopy = () => {
    setClipboard(colorGrade);
    alert('Color grade copied to clipboard!');
  };

  const handlePaste = () => {
    if (clipboard) {
      setColorGrade(clipboard);
      onGradeChange?.(clipboard);
    }
  };

  const handleReset = () => {
    setColorGrade(DEFAULT_GRADE);
    onGradeChange?.(DEFAULT_GRADE);
  };

  const handleSavePreset = () => {
    const name = prompt('Enter preset name:');
    if (name) {
      setSavedPresets((prev) => [...prev, { name, grade: colorGrade }]);
      alert(`Preset "${name}" saved!`);
    }
  };

  const handleLoadPreset = (preset: { name: string; grade: ColorGrade }) => {
    setColorGrade(preset.grade);
    onGradeChange?.(preset.grade);
  };

  const handleExport = () => {
    const dataStr = JSON.stringify(colorGrade, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);
    const exportFileDefaultName = 'color-grade.json';

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          try {
            const imported = JSON.parse(event.target?.result as string);
            setColorGrade(imported);
            onGradeChange?.(imported);
            alert('Color grade imported successfully!');
          } catch (error) {
            alert('Error importing color grade');
          }
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  return (
    <div className="color-grading-panel bg-gray-900 text-white p-6 rounded-lg shadow-xl max-h-[90vh] overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Palette className="w-6 h-6 text-purple-400" />
          <h2 className="text-2xl font-bold">Color Grading</h2>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded"
            title={showPreview ? 'Hide Preview' : 'Show Preview'}
          >
            {showPreview ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button
            onClick={handleCopy}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded"
            title="Copy Grade"
          >
            <Copy className="w-4 h-4" />
          </button>
          <button
            onClick={handlePaste}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded"
            disabled={!clipboard}
            title="Paste Grade"
          >
            <Clipboard className="w-4 h-4" />
          </button>
          <button
            onClick={handleReset}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded"
            title="Reset All"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={handleSavePreset}
            className="p-2 bg-blue-600 hover:bg-blue-500 rounded"
            title="Save Preset"
          >
            <Save className="w-4 h-4" />
          </button>
          <button
            onClick={handleExport}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded"
            title="Export Grade"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={handleImport}
            className="p-2 bg-gray-800 hover:bg-gray-700 rounded"
            title="Import Grade"
          >
            <Upload className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Saved Presets */}
      {savedPresets.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-semibold mb-2 text-gray-400">Saved Presets</h3>
          <div className="flex gap-2 flex-wrap">
            {savedPresets.map((preset, index) => (
              <button
                key={index}
                onClick={() => handleLoadPreset(preset)}
                className="px-3 py-1 bg-purple-600 hover:bg-purple-500 rounded text-sm"
              >
                {preset.name}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Color Wheels */}
      <CollapsibleSection
        title="Color Wheels"
        expanded={expandedSections.colorWheels}
        onToggle={() => toggleSection('colorWheels')}
      >
        <div className="grid grid-cols-3 gap-6">
          <ColorWheel
            label="Lift (Shadows)"
            value={colorGrade.lift}
            onChange={(lift) => updateGrade({ lift })}
          />
          <ColorWheel
            label="Gamma (Midtones)"
            value={colorGrade.gamma}
            onChange={(gamma) => updateGrade({ gamma })}
          />
          <ColorWheel
            label="Gain (Highlights)"
            value={colorGrade.gain}
            onChange={(gain) => updateGrade({ gain })}
          />
        </div>
      </CollapsibleSection>

      {/* RGB Curves */}
      <CollapsibleSection
        title="RGB Curves"
        expanded={expandedSections.curves}
        onToggle={() => toggleSection('curves')}
      >
        <div className="mb-4">
          <div className="flex gap-2 mb-4">
            {(['master', 'red', 'green', 'blue'] as const).map((curve) => (
              <button
                key={curve}
                onClick={() => setActiveCurve(curve)}
                className={`px-4 py-2 rounded ${
                  activeCurve === curve
                    ? 'bg-blue-600'
                    : 'bg-gray-800 hover:bg-gray-700'
                }`}
                style={
                  curve !== 'master'
                    ? {
                        backgroundColor:
                          activeCurve === curve
                            ? curve === 'red'
                              ? '#dc2626'
                              : curve === 'green'
                              ? '#16a34a'
                              : '#2563eb'
                            : undefined,
                      }
                    : undefined
                }
              >
                {curve.charAt(0).toUpperCase() + curve.slice(1)}
              </button>
            ))}
          </div>
          <CurveEditor
            points={colorGrade.curves[activeCurve]}
            onChange={(points) =>
              updateGrade({
                curves: { ...colorGrade.curves, [activeCurve]: points },
              })
            }
            color={
              activeCurve === 'master'
                ? '#ffffff'
                : activeCurve === 'red'
                ? '#ef4444'
                : activeCurve === 'green'
                ? '#22c55e'
                : '#3b82f6'
            }
            label={`${activeCurve.charAt(0).toUpperCase() + activeCurve.slice(1)} Curve`}
          />
        </div>
      </CollapsibleSection>

      {/* HSL Per Color */}
      <CollapsibleSection
        title="HSL (Per Color)"
        expanded={expandedSections.hsl}
        onToggle={() => toggleSection('hsl')}
      >
        <div className="space-y-4">
          {(Object.keys(colorGrade.hsl) as Array<keyof typeof colorGrade.hsl>).map((color) => (
            <div key={color} className="border border-gray-700 rounded p-3">
              <h4 className="text-sm font-semibold mb-2 capitalize">{color}</h4>
              <div className="space-y-2">
                <Slider
                  label="Hue"
                  value={colorGrade.hsl[color].h}
                  onChange={(h) =>
                    updateGrade({
                      hsl: {
                        ...colorGrade.hsl,
                        [color]: { ...colorGrade.hsl[color], h },
                      },
                    })
                  }
                  min={-180}
                  max={180}
                  step={1}
                />
                <Slider
                  label="Saturation"
                  value={colorGrade.hsl[color].s}
                  onChange={(s) =>
                    updateGrade({
                      hsl: {
                        ...colorGrade.hsl,
                        [color]: { ...colorGrade.hsl[color], s },
                      },
                    })
                  }
                  min={-100}
                  max={100}
                  step={1}
                />
                <Slider
                  label="Luminance"
                  value={colorGrade.hsl[color].l}
                  onChange={(l) =>
                    updateGrade({
                      hsl: {
                        ...colorGrade.hsl,
                        [color]: { ...colorGrade.hsl[color], l },
                      },
                    })
                  }
                  min={-100}
                  max={100}
                  step={1}
                />
              </div>
            </div>
          ))}
        </div>
      </CollapsibleSection>

      {/* Basic Adjustments */}
      <CollapsibleSection
        title="Basic Adjustments"
        expanded={expandedSections.basic}
        onToggle={() => toggleSection('basic')}
      >
        <div className="space-y-3">
          <Slider
            label="Exposure"
            value={colorGrade.exposure}
            onChange={(exposure) => updateGrade({ exposure })}
            min={-5}
            max={5}
            step={0.1}
          />
          <Slider
            label="Contrast"
            value={colorGrade.contrast}
            onChange={(contrast) => updateGrade({ contrast })}
            min={0}
            max={200}
            step={1}
          />
          <Slider
            label="Highlights"
            value={colorGrade.highlights}
            onChange={(highlights) => updateGrade({ highlights })}
            min={-100}
            max={100}
            step={1}
          />
          <Slider
            label="Shadows"
            value={colorGrade.shadows}
            onChange={(shadows) => updateGrade({ shadows })}
            min={-100}
            max={100}
            step={1}
          />
          <Slider
            label="Whites"
            value={colorGrade.whites}
            onChange={(whites) => updateGrade({ whites })}
            min={-100}
            max={100}
            step={1}
          />
          <Slider
            label="Blacks"
            value={colorGrade.blacks}
            onChange={(blacks) => updateGrade({ blacks })}
            min={-100}
            max={100}
            step={1}
          />
        </div>
      </CollapsibleSection>

      {/* Temperature & Tint */}
      <CollapsibleSection
        title="Temperature & Tint"
        expanded={expandedSections.tempTint}
        onToggle={() => toggleSection('tempTint')}
      >
        <div className="space-y-3">
          <Slider
            label="Temperature"
            value={colorGrade.temperature}
            onChange={(temperature) => updateGrade({ temperature })}
            min={-100}
            max={100}
            step={1}
          />
          <Slider
            label="Tint"
            value={colorGrade.tint}
            onChange={(tint) => updateGrade({ tint })}
            min={-100}
            max={100}
            step={1}
          />
        </div>
      </CollapsibleSection>

      {/* Vibrance & Saturation */}
      <CollapsibleSection
        title="Vibrance & Saturation"
        expanded={expandedSections.vibrance}
        onToggle={() => toggleSection('vibrance')}
      >
        <div className="space-y-3">
          <Slider
            label="Vibrance"
            value={colorGrade.vibrance}
            onChange={(vibrance) => updateGrade({ vibrance })}
            min={-100}
            max={100}
            step={1}
          />
          <Slider
            label="Saturation"
            value={colorGrade.saturation}
            onChange={(saturation) => updateGrade({ saturation })}
            min={-100}
            max={100}
            step={1}
          />
        </div>
      </CollapsibleSection>

      {/* LUT Browser */}
      <CollapsibleSection
        title="LUT Presets"
        expanded={expandedSections.lut}
        onToggle={() => toggleSection('lut')}
      >
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {LUT_PRESETS.map((lut) => (
            <button
              key={lut.id}
              onClick={() => updateGrade({ selectedLUT: lut.id })}
              className={`p-4 rounded border-2 transition-all ${
                colorGrade.selectedLUT === lut.id
                  ? 'border-blue-500 bg-blue-900/30'
                  : 'border-gray-700 bg-gray-800 hover:border-gray-600'
              }`}
            >
              <div className="text-3xl mb-2">{lut.thumbnail}</div>
              <div className="text-sm font-semibold">{lut.name}</div>
              <div className="text-xs text-gray-400 mt-1">{lut.category}</div>
            </button>
          ))}
        </div>
        {colorGrade.selectedLUT && (
          <div className="mt-4 p-3 bg-gray-800 rounded">
            <div className="flex justify-between items-center">
              <span className="text-sm">
                Active LUT: <strong>{LUT_PRESETS.find((l) => l.id === colorGrade.selectedLUT)?.name}</strong>
              </span>
              <button
                onClick={() => updateGrade({ selectedLUT: null })}
                className="text-xs text-red-400 hover:text-red-300"
              >
                Remove LUT
              </button>
            </div>
          </div>
        )}
      </CollapsibleSection>

      {/* Vectorscope */}
      <CollapsibleSection
        title="Vectorscope (Preview)"
        expanded={expandedSections.vectorscope}
        onToggle={() => toggleSection('vectorscope')}
      >
        <div className="bg-gray-800 rounded p-4 text-center">
          <div className="w-48 h-48 mx-auto bg-gray-900 rounded-full border border-gray-700 flex items-center justify-center">
            <span className="text-gray-500">Vectorscope Visualization</span>
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Real-time color distribution analysis
          </p>
        </div>
      </CollapsibleSection>
    </div>
  );
};

// ==================== HELPER COMPONENTS ====================

interface SliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min: number;
  max: number;
  step: number;
}

const Slider: React.FC<SliderProps> = ({ label, value, onChange, min, max, step }) => {
  return (
    <div className="slider-container">
      <div className="flex justify-between items-center mb-1">
        <label className="text-sm text-gray-300">{label}</label>
        <span className="text-sm font-mono text-gray-400">{value.toFixed(step < 1 ? 1 : 0)}</span>
      </div>
      <input
        type="range"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        min={min}
        max={max}
        step={step}
        className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
      />
    </div>
  );
};

interface CollapsibleSectionProps {
  title: string;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  title,
  expanded,
  onToggle,
  children,
}) => {
  return (
    <div className="mb-6 border border-gray-700 rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex justify-between items-center p-4 bg-gray-800 hover:bg-gray-750 transition-colors"
      >
        <h3 className="text-lg font-semibold">{title}</h3>
        {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
      </button>
      {expanded && <div className="p-4 bg-gray-850">{children}</div>}
    </div>
  );
};

export default ColorGradingPanel;
