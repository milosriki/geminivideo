import React, { useState } from 'react';
import { ColorGradingPanel } from './ColorGradingPanel';
import './ColorGradingPanel.css';

/**
 * Demo component showing how to use the ColorGradingPanel
 * This demonstrates integration with a video player and real-time preview
 */
export const ColorGradingPanelDemo: React.FC = () => {
  const [currentGrade, setCurrentGrade] = useState<any>(null);

  const handleGradeChange = (grade: any) => {
    // console.log('Color grade updated:', grade);
    setCurrentGrade(grade);

    // Here you would apply the color grade to your video
    // Example: applyColorGradeToVideo(grade);
  };

  return (
    <div className="min-h-screen bg-black p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-white mb-8">
          Pro-Grade Color Grading Panel Demo
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Video Preview */}
          <div className="space-y-4">
            <div className="aspect-video bg-gray-800 rounded-lg flex items-center justify-center border-2 border-gray-700">
              <div className="text-center">
                <div className="text-6xl mb-4">🎬</div>
                <p className="text-gray-400 text-lg">Video Preview</p>
                <p className="text-gray-500 text-sm mt-2">
                  Color grading will be applied here in real-time
                </p>
              </div>
            </div>

            {/* Current Grade Info */}
            {currentGrade && (
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
                <h3 className="text-white font-semibold mb-2">Current Grade Settings</h3>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-gray-400">
                    Exposure: <span className="text-white">{currentGrade.exposure}</span>
                  </div>
                  <div className="text-gray-400">
                    Contrast: <span className="text-white">{currentGrade.contrast}</span>
                  </div>
                  <div className="text-gray-400">
                    Temperature: <span className="text-white">{currentGrade.temperature}</span>
                  </div>
                  <div className="text-gray-400">
                    Saturation: <span className="text-white">{currentGrade.saturation}</span>
                  </div>
                </div>
                {currentGrade.selectedLUT && (
                  <div className="mt-2 pt-2 border-t border-gray-700">
                    <span className="text-gray-400">
                      LUT: <span className="text-blue-400">{currentGrade.selectedLUT}</span>
                    </span>
                  </div>
                )}
              </div>
            )}

            {/* Instructions */}
            <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
              <h3 className="text-blue-300 font-semibold mb-2">How to Use</h3>
              <ul className="text-sm text-blue-200 space-y-1">
                <li>• Drag on color wheels to adjust lift, gamma, and gain</li>
                <li>• Click on RGB curves to add control points</li>
                <li>• Use sliders for precise adjustments</li>
                <li>• Apply LUT presets for instant looks</li>
                <li>• Save your grades as presets</li>
                <li>• Export/import grades as JSON files</li>
              </ul>
            </div>
          </div>

          {/* Color Grading Panel */}
          <div>
            <ColorGradingPanel onGradeChange={handleGradeChange} />
          </div>
        </div>

        {/* Feature Showcase */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
            <div className="text-3xl mb-3">🎨</div>
            <h3 className="text-white font-semibold mb-2">Professional Tools</h3>
            <p className="text-gray-400 text-sm">
              Industry-standard color wheels, curves, and HSL controls for precise grading
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
            <div className="text-3xl mb-3">⚡</div>
            <h3 className="text-white font-semibold mb-2">Real-time Preview</h3>
            <p className="text-gray-400 text-sm">
              See your changes instantly with optimized rendering and smooth updates
            </p>
          </div>

          <div className="bg-gray-900 rounded-lg p-6 border border-gray-700">
            <div className="text-3xl mb-3">💾</div>
            <h3 className="text-white font-semibold mb-2">Save & Share</h3>
            <p className="text-gray-400 text-sm">
              Create presets, export grades, and share your color grading workflows
            </p>
          </div>
        </div>

        {/* Code Example */}
        <div className="mt-12 bg-gray-900 rounded-lg p-6 border border-gray-700">
          <h3 className="text-white font-semibold mb-4">Integration Example</h3>
          <pre className="bg-black p-4 rounded text-sm text-green-400 overflow-x-auto">
            {`import { ColorGradingPanel } from './components/pro/ColorGradingPanel';
import './components/pro/ColorGradingPanel.css';

function VideoEditor() {
  const handleGradeChange = (grade) => {
    // Apply color grade to video
    videoPlayer.applyColorGrade(grade);
  };

  return (
    <ColorGradingPanel
      onGradeChange={handleGradeChange}
      initialGrade={{
        exposure: 0.5,
        contrast: 110,
        saturation: 10
      }}
    />
  );
}`}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default ColorGradingPanelDemo;
