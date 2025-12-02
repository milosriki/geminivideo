# Installation Guide - Color Grading Panel

## Dependencies

Add these dependencies to your `package.json`:

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lucide-react": "^0.294.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.0.0"
  }
}
```

## Installation Steps

### 1. Install Dependencies

```bash
npm install lucide-react
# or
yarn add lucide-react
# or
pnpm add lucide-react
```

### 2. Import the Component

```tsx
import { ColorGradingPanel } from './components/pro/ColorGradingPanel';
import './components/pro/ColorGradingPanel.css';
```

### 3. Basic Usage

```tsx
import React, { useState } from 'react';
import { ColorGradingPanel } from './components/pro';
import type { ColorGrade } from './components/pro';
import './components/pro/ColorGradingPanel.css';

function App() {
  const [colorGrade, setColorGrade] = useState<ColorGrade | null>(null);

  const handleGradeChange = (grade: ColorGrade) => {
    console.log('Color grade updated:', grade);
    setColorGrade(grade);

    // Apply to your video player
    // videoPlayer.applyColorGrade(grade);
  };

  return (
    <div className="app">
      <ColorGradingPanel onGradeChange={handleGradeChange} />
    </div>
  );
}
```

### 4. With Initial Values

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

### 5. Apply to Video (Canvas Method)

```tsx
import { applyColorGradeToVideo } from './components/pro/ColorGradingUtils';

function VideoEditor() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [currentGrade, setCurrentGrade] = useState<ColorGrade>(DEFAULT_COLOR_GRADE);

  useEffect(() => {
    if (videoRef.current && canvasRef.current) {
      applyColorGradeToVideo(videoRef.current, canvasRef.current, currentGrade);
    }
  }, [currentGrade]);

  return (
    <div>
      <video ref={videoRef} src="video.mp4" />
      <canvas ref={canvasRef} style={{ display: 'none' }} />
      <ColorGradingPanel onGradeChange={setCurrentGrade} />
    </div>
  );
}
```

### 6. Apply to Image (ImageData Method)

```tsx
import { applyColorGradeToImageData } from './components/pro/ColorGradingUtils';

function ImageEditor() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const applyGrade = (grade: ColorGrade) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const gradedData = applyColorGradeToImageData(imageData, grade);
    ctx.putImageData(gradedData, 0, 0);
  };

  return (
    <div>
      <canvas ref={canvasRef} />
      <ColorGradingPanel onGradeChange={applyGrade} />
    </div>
  );
}
```

## Tailwind CSS Configuration (Optional)

If you're using Tailwind CSS, add these colors to your config:

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        gray: {
          750: '#2d3748',
          850: '#1a1f2e',
        },
      },
    },
  },
};
```

## Without Tailwind CSS

If you're not using Tailwind CSS, you'll need to add the base styles manually:

```css
/* Add to your global CSS file */
.bg-gray-900 { background-color: #111827; }
.bg-gray-800 { background-color: #1f2937; }
.bg-gray-700 { background-color: #374151; }
.text-white { color: #ffffff; }
.text-gray-300 { color: #d1d5db; }
.text-gray-400 { color: #9ca3af; }
.text-blue-400 { color: #60a5fa; }
.rounded { border-radius: 0.25rem; }
.rounded-lg { border-radius: 0.5rem; }
.p-2 { padding: 0.5rem; }
.p-4 { padding: 1rem; }
.p-6 { padding: 1.5rem; }
/* ... add other utility classes as needed */
```

Or convert the component to use CSS modules or styled-components.

## Testing the Installation

Run the demo component to test:

```tsx
import { ColorGradingPanelDemo } from './components/pro';

function App() {
  return <ColorGradingPanelDemo />;
}
```

## Troubleshooting

### Issue: Icons not showing

**Solution:** Make sure `lucide-react` is installed:
```bash
npm install lucide-react
```

### Issue: Canvas not working

**Solution:** Ensure you're using a modern browser with canvas support. Check browser console for errors.

### Issue: TypeScript errors

**Solution:** Make sure all type files are imported:
```tsx
import type { ColorGrade } from './components/pro/ColorGradingPanel.types';
```

### Issue: Styling not working

**Solution:** Make sure to import the CSS file:
```tsx
import './components/pro/ColorGradingPanel.css';
```

## Performance Tips

1. **Debounce Updates**: Use lodash debounce for real-time video processing
2. **Web Workers**: Process video frames in a worker thread
3. **WebGL**: Use WebGL shaders for better performance
4. **Memoization**: Memoize the component if parent re-renders frequently

```tsx
import { memo } from 'react';
import { debounce } from 'lodash';

const MemoizedPanel = memo(ColorGradingPanel);

const debouncedHandler = debounce((grade) => {
  applyToVideo(grade);
}, 50);
```

## Next Steps

1. Read the full [README.md](./README.md) for feature documentation
2. Check out [ColorGradingPanelDemo.tsx](./ColorGradingPanelDemo.tsx) for examples
3. Review [ColorGradingUtils.ts](./ColorGradingUtils.ts) for processing utilities
4. Explore the type definitions in [ColorGradingPanel.types.ts](./ColorGradingPanel.types.ts)

## Support

For issues or questions:
- Check the README.md file
- Review the demo component
- Check browser console for errors
- Ensure all dependencies are installed

Happy color grading! 🎨
