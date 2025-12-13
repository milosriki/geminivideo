export default function MarketIntelPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Market Intelligence</h1>
        <p className="text-zinc-400">
          Real-time market trends, competitor insights, and industry analysis
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Market Trends</h3>
          <p className="text-zinc-400">Track emerging trends in your industry</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Competitive Analysis</h3>
          <p className="text-zinc-400">Monitor competitor strategies and performance</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Industry Insights</h3>
          <p className="text-zinc-400">Get actionable insights from market data</p>
        </div>
      </div>
    </div>
  )
}
