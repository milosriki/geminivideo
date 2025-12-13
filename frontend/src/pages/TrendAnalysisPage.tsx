export default function TrendAnalysisPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Trend Analysis</h1>
        <p className="text-zinc-400">
          AI-powered trend detection and forecasting for your market
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Emerging Trends</h3>
          <p className="text-zinc-400">Discover trends before they go mainstream</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Trend Forecasting</h3>
          <p className="text-zinc-400">AI predictions for upcoming market shifts</p>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Sentiment Analysis</h3>
          <p className="text-zinc-400">Track audience sentiment across platforms</p>
        </div>
      </div>
    </div>
  )
}
