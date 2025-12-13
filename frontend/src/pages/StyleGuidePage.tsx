export default function StyleGuidePage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Style Guide</h1>
        <p className="text-zinc-400">
          Comprehensive brand style guide for consistent creative output
        </p>
      </div>

      <div className="space-y-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Visual Style</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-zinc-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Tone</h4>
              <p className="text-zinc-400 text-sm">Professional, Modern, Energetic</p>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Imagery</h4>
              <p className="text-zinc-400 text-sm">High-quality, Authentic, Diverse</p>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Composition</h4>
              <p className="text-zinc-400 text-sm">Clean, Minimalist, Balanced</p>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Voice & Messaging</h3>
          <div className="space-y-3">
            <div className="bg-zinc-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Brand Voice</h4>
              <p className="text-zinc-400 text-sm">
                Confident, approachable, and innovative. We speak to our audience as trusted partners
                in their success, using clear and actionable language.
              </p>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Key Messages</h4>
              <ul className="list-disc list-inside text-zinc-400 text-sm space-y-1">
                <li>AI-powered creative automation at scale</li>
                <li>Data-driven insights for better ROI</li>
                <li>Enterprise-grade reliability and security</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Design Patterns</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-zinc-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Layout Grid</h4>
              <div className="grid grid-cols-12 gap-1 mt-2">
                {Array.from({ length: 12 }).map((_, i) => (
                  <div key={i} className="h-12 bg-violet-500/20 rounded"></div>
                ))}
              </div>
            </div>
            <div className="bg-zinc-800 rounded-lg p-4">
              <h4 className="text-white font-medium mb-2">Spacing System</h4>
              <div className="space-y-2 mt-2">
                {[4, 8, 16, 24, 32].map((space) => (
                  <div key={space} className="flex items-center gap-3">
                    <div className="w-16 h-4 bg-violet-500 rounded" style={{ width: `${space}px` }}></div>
                    <span className="text-zinc-400 text-sm">{space}px</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
