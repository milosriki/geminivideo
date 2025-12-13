export default function AssetManagerPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Asset Manager</h1>
        <p className="text-zinc-400">
          Advanced asset management with AI-powered tagging and organization
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 bg-zinc-900 border border-zinc-800 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Filters</h3>
          <div className="space-y-3">
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Asset Type</label>
              <select className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-white text-sm">
                <option>All Types</option>
                <option>Video</option>
                <option>Image</option>
                <option>Audio</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-zinc-400 mb-1 block">Date Added</label>
              <select className="w-full bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-white text-sm">
                <option>Any Time</option>
                <option>Last 7 Days</option>
                <option>Last 30 Days</option>
                <option>Last Year</option>
              </select>
            </div>
          </div>
        </div>

        <div className="lg:col-span-3">
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
            <h3 className="text-xl font-semibold text-white mb-4">Recent Assets</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="bg-zinc-800 rounded-lg p-3 hover:bg-zinc-700 cursor-pointer transition-colors">
                  <div className="aspect-video bg-zinc-700 rounded mb-2"></div>
                  <p className="text-white text-sm font-medium">Asset {i}</p>
                  <p className="text-zinc-400 text-xs">Modified 2 days ago</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
