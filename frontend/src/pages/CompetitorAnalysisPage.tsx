export default function CompetitorAnalysisPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Competitor Analysis</h1>
        <p className="text-zinc-400">
          Deep dive into competitor strategies, campaigns, and performance metrics
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Competitor Tracking</h3>
          <p className="text-zinc-400">Monitor up to 50 competitors simultaneously</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Campaign Analysis</h3>
          <p className="text-zinc-400">Analyze competitor ad campaigns and creative strategies</p>
        </div>
      </div>
    </div>
  )
}
