export default function BrandKitPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Brand Kit</h1>
        <p className="text-zinc-400">
          Manage your brand assets, colors, fonts, and guidelines
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Brand Colors</h3>
          <div className="grid grid-cols-4 gap-3">
            {['#8B5CF6', '#EC4899', '#10B981', '#F59E0B', '#3B82F6', '#EF4444', '#6366F1', '#14B8A6'].map((color, i) => (
              <div key={i} className="space-y-2">
                <div
                  className="aspect-square rounded-lg border-2 border-zinc-700 cursor-pointer hover:scale-105 transition-transform"
                  style={{ backgroundColor: color }}
                ></div>
                <p className="text-xs text-zinc-400 text-center font-mono">{color}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Logos</h3>
          <div className="grid grid-cols-2 gap-4">
            {['Primary Logo', 'Secondary Logo', 'Logo Mark', 'Wordmark'].map((logo) => (
              <div key={logo} className="bg-zinc-800 rounded-lg p-4 text-center">
                <div className="aspect-square bg-zinc-700 rounded-lg mb-2"></div>
                <p className="text-white text-sm">{logo}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Typography</h3>
          <div className="space-y-4">
            <div>
              <p className="text-zinc-400 text-sm mb-1">Heading Font</p>
              <p className="text-white text-2xl font-bold">Inter Bold</p>
            </div>
            <div>
              <p className="text-zinc-400 text-sm mb-1">Body Font</p>
              <p className="text-white text-lg">Inter Regular</p>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Brand Guidelines</h3>
          <div className="space-y-3">
            <button className="w-full bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-3 rounded-lg text-left transition-colors">
              Logo Usage Guidelines
            </button>
            <button className="w-full bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-3 rounded-lg text-left transition-colors">
              Color Palette Guide
            </button>
            <button className="w-full bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-3 rounded-lg text-left transition-colors">
              Typography Guide
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
