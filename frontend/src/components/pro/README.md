# Pro-Grade Color Grading Panel

A complete, production-ready React component for professional video color grading with TypeScript support.

## Features

### 🎨 Color Wheels
- **Lift** (Shadows) - Control shadow tones
- **Gamma** (Midtones) - Adjust middle gray values
- **Gain** (Highlights) - Fine-tune highlight values
- Interactive canvas-based drag interface
- Real-time RGB offset visualization

### 📈 RGB Curves
- Separate curves for Red, Green, Blue, and Master
- Bezier curve interpolation for smooth transitions
- Click to add control points (up to 10 per curve)
- Drag to adjust existing points
- Visual grid and reference diagonal
- Per-channel color-coded interface

### 🌈 HSL Per Color
Fine-tune 8 color ranges independently:
- Red
- Orange
- Yellow
- Green
- Cyan
- Blue
- Purple
- Magenta

Each with:
- Hue shift (-180 to +180)
- Saturation adjustment (-100 to +100)
- Luminance adjustment (-100 to +100)

### ⚙️ Basic Adjustments
- **Exposure** (-5 to +5) - Overall brightness
- **Contrast** (0 to 200) - Contrast ratio
- **Highlights** (-100 to +100) - Bright area recovery
- **Shadows** (-100 to +100) - Dark area detail
- **Whites** (-100 to +100) - White point adjustment
- **Blacks** (-100 to +100) - Black point adjustment

### 🌡️ Temperature & Tint
- **Temperature** (-100 to +100) - Cool to warm color cast
- **Tint** (-100 to +100) - Green to magenta shift

### 💫 Vibrance & Saturation
- **Vibrance** (-100 to +100) - Smart saturation (protects skin tones)
- **Saturation** (-100 to +100) - Global color intensity

### 🎬 LUT Presets
Built-in professional looks:
- Cinematic Teal & Orange
- Vintage Film
- Moody Dark
- Bright & Airy
- Cyberpunk
- Bleach Bypass
- Golden Hour
- Film Noir

### 🛠️ Utility Features
- **Copy/Paste** - Transfer grades between clips
- **Reset** - Return to default settings
- **Save Preset** - Create custom presets
- **Export** - Save grades as JSON files
- **Import** - Load grades from JSON files
- **Before/After Toggle** - Preview toggle
- **Collapsible Sections** - Organized workspace

### 📊 Vectorscope (Optional)
- Real-time color distribution visualization
- Professional color space analysis

## Installation

```bash
# Copy files to your project
cp ColorGradingPanel.tsx your-project/components/
cp ColorGradingPanel.css your-project/components/
```

### Dependencies

```bash
npm install lucide-react
# or
yarn add lucide-react
```

## Usage

### Basic Implementation

```tsx
import { ColorGradingPanel } from './components/pro/ColorGradingPanel';
import './components/pro/ColorGradingPanel.css';

function MyVideoEditor() {
  const handleGradeChange = (grade) => {
    console.log('New color grade:', grade);
    // Apply to your video player/renderer
  };

  return (
    <ColorGradingPanel onGradeChange={handleGradeChange} />
  );
}
```

### With Initial Values

```tsx
<ColorGradingPanel
  onGradeChange={handleGradeChange}
  initialGrade={{
    exposure: 0.5,
    contrast: 110,
    saturation: 10,
    temperature: 15,
    selectedLUT: 'cinematic-teal-orange'
  }}
/>
```

### Integration with Video Player

```tsx
import { ColorGradingPanel } from './components/pro/ColorGradingPanel';
import { useVideoPlayer } from './hooks/useVideoPlayer';

function VideoEditorWithGrading() {
  const videoPlayer = useVideoPlayer();

  const handleGradeChange = (grade) => {
    // Apply color corrections to video
    videoPlayer.setColorGrade(grade);
  };

  return (
    <div className="editor-layout">
      <div className="video-preview">
        <VideoPlayer ref={videoPlayer} />
      </div>
      <div className="color-panel">
        <ColorGradingPanel onGradeChange={handleGradeChange} />
      </div>
    </div>
  );
}
```

## API Reference

### Props

#### `ColorGradingPanelProps`

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `onGradeChange` | `(grade: ColorGrade) => void` | No | Callback fired when any grade parameter changes |
| `initialGrade` | `Partial<ColorGrade>` | No | Initial color grade values |

### ColorGrade Interface

```typescript
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
```

## Applying Color Grades

### WebGL Shader Example

```glsl
// Fragment shader example for applying color grade
precision mediump float;
uniform sampler2D u_texture;
uniform float u_exposure;
uniform float u_contrast;
uniform float u_saturation;
varying vec2 v_texCoord;

void main() {
  vec4 color = texture2D(u_texture, v_texCoord);

  // Apply exposure
  color.rgb *= pow(2.0, u_exposure);

  // Apply contrast
  color.rgb = (color.rgb - 0.5) * (u_contrast / 100.0) + 0.5;

  // Apply saturation
  float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
  color.rgb = mix(vec3(gray), color.rgb, (u_saturation + 100.0) / 100.0);

  gl_FragColor = color;
}
```

### CSS Filter Example (Limited)

```tsx
const applyBasicGrade = (grade: ColorGrade) => {
  const filters = [
    `brightness(${100 + grade.exposure * 20}%)`,
    `contrast(${grade.contrast}%)`,
    `saturate(${100 + grade.saturation}%)`,
  ].join(' ');

  return { filter: filters };
};

<video style={applyBasicGrade(colorGrade)} />
```

### Canvas 2D Example

```typescript
const applyColorGrade = (
  ctx: CanvasRenderingContext2D,
  grade: ColorGrade
) => {
  const imageData = ctx.getImageData(0, 0, width, height);
  const data = imageData.data;

  for (let i = 0; i < data.length; i += 4) {
    let r = data[i];
    let g = data[i + 1];
    let b = data[i + 2];

    // Apply exposure
    r *= Math.pow(2, grade.exposure);
    g *= Math.pow(2, grade.exposure);
    b *= Math.pow(2, grade.exposure);

    // Apply contrast
    r = ((r / 255 - 0.5) * (grade.contrast / 100) + 0.5) * 255;
    g = ((g / 255 - 0.5) * (grade.contrast / 100) + 0.5) * 255;
    b = ((b / 255 - 0.5) * (grade.contrast / 100) + 0.5) * 255;

    // Clamp values
    data[i] = Math.max(0, Math.min(255, r));
    data[i + 1] = Math.max(0, Math.min(255, g));
    data[i + 2] = Math.max(0, Math.min(255, b));
  }

  ctx.putImageData(imageData, 0, 0);
};
```

## Customization

### Custom LUT Presets

```typescript
// Add your own LUT presets
const CUSTOM_LUTS: LUTPreset[] = [
  {
    id: 'my-custom-look',
    name: 'My Custom Look',
    category: 'Custom',
    thumbnail: '🎯',
    description: 'My signature color grade',
  },
];
```

### Styling

Override default styles:

```css
/* Custom panel background */
.color-grading-panel {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

/* Custom slider colors */
input[type='range'].slider::-webkit-slider-thumb {
  background: #ff6b6b;
  border-color: #ff6b6b;
}

/* Custom button styles */
.color-grading-panel button {
  border-radius: 8px;
  font-weight: 600;
}
```

## Performance Optimization

### Debouncing Updates

```typescript
import { debounce } from 'lodash';

const debouncedGradeChange = debounce((grade) => {
  applyColorGradeToVideo(grade);
}, 50);

<ColorGradingPanel onGradeChange={debouncedGradeChange} />
```

### Memoization

```typescript
import { memo } from 'react';

const MemoizedColorGradingPanel = memo(ColorGradingPanel, (prev, next) => {
  return JSON.stringify(prev.initialGrade) === JSON.stringify(next.initialGrade);
});
```

## Browser Compatibility

- Chrome/Edge: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Mobile browsers: ✅ Responsive design

## Keyboard Shortcuts

Future enhancements could include:
- `Ctrl/Cmd + C` - Copy grade
- `Ctrl/Cmd + V` - Paste grade
- `Ctrl/Cmd + R` - Reset grade
- `Ctrl/Cmd + S` - Save preset
- `Space` - Toggle preview

## Examples

See `ColorGradingPanelDemo.tsx` for a complete working example.

## License

MIT License - Free to use in commercial and personal projects.

## Contributing

Contributions welcome! Please submit issues and pull requests.

## Support

For issues or questions, please open a GitHub issue.

---

Built with ❤️ for professional video editors
