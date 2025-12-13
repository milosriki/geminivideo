export default function AdLibraryPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Ad Library</h1>
        <p className="text-zinc-400">
          Browse and analyze millions of ads from across the web
        </p>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 mb-6">
        <h3 className="text-xl font-semibold text-white mb-4">Search & Filter</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            placeholder="Search ads..."
            className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white"
          />
          <select className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white">
            <option>All Platforms</option>
            <option>Facebook</option>
            <option>Instagram</option>
            <option>Google</option>
          </select>
          <select className="bg-zinc-800 border border-zinc-700 rounded-lg px-4 py-2 text-white">
            <option>All Industries</option>
            <option>E-commerce</option>
            <option>SaaS</option>
            <option>Finance</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
            <div className="aspect-video bg-zinc-800 rounded-lg mb-3"></div>
            <h4 className="text-white font-medium mb-1">Sample Ad {i}</h4>
            <p className="text-zinc-400 text-sm">Platform: Facebook | Views: 1.2M</p>
          </div>
        ))}
      </div>
    </div>
  )
}
