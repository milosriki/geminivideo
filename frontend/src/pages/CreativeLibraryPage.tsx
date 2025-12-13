export default function CreativeLibraryPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Creative Library</h1>
        <p className="text-zinc-400">
          Organize and manage all your creative assets in one place
        </p>
      </div>

      <div className="mb-6 flex gap-4">
        <button className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg transition-colors">
          Upload Assets
        </button>
        <button className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg transition-colors">
          Create Folder
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { name: 'Videos', count: 142 },
          { name: 'Images', count: 328 },
          { name: 'Audio', count: 89 },
          { name: 'Templates', count: 56 },
        ].map((folder) => (
          <div key={folder.name} className="bg-zinc-900 border border-zinc-800 rounded-lg p-6 hover:border-violet-500 cursor-pointer transition-colors">
            <div className="text-4xl mb-3">📁</div>
            <h3 className="text-xl font-semibold text-white mb-1">{folder.name}</h3>
            <p className="text-zinc-400">{folder.count} items</p>
          </div>
        ))}
      </div>
    </div>
  )
}
