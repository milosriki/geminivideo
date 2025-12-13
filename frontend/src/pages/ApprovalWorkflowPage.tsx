export default function ApprovalWorkflowPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Approval Workflow</h1>
        <p className="text-zinc-400">
          Manage approval processes and review creative assets
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[
          { status: 'Pending Review', count: 12, color: 'bg-amber-500' },
          { status: 'In Review', count: 5, color: 'bg-blue-500' },
          { status: 'Approved', count: 28, color: 'bg-emerald-500' },
          { status: 'Rejected', count: 3, color: 'bg-red-500' },
        ].map((stat) => (
          <div key={stat.status} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
            <div className={`w-3 h-3 rounded-full ${stat.color} mb-2`}></div>
            <p className="text-2xl font-bold text-white mb-1">{stat.count}</p>
            <p className="text-zinc-400 text-sm">{stat.status}</p>
          </div>
        ))}
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white">Pending Approvals</h3>
          <select className="bg-zinc-800 border border-zinc-700 rounded px-3 py-2 text-white text-sm">
            <option>All Items</option>
            <option>Videos</option>
            <option>Images</option>
            <option>Campaigns</option>
          </select>
        </div>

        <div className="space-y-3">
          {[
            { name: 'Summer Campaign Video - Final Cut', type: 'Video', submitted: '2 hours ago', submitter: 'Sarah Chen' },
            { name: 'Instagram Story Template Set', type: 'Template', submitted: '5 hours ago', submitter: 'Mike Rodriguez' },
            { name: 'Q4 Product Launch Campaign', type: 'Campaign', submitted: '1 day ago', submitter: 'Emily Johnson' },
          ].map((item, i) => (
            <div key={i} className="bg-zinc-800 rounded-lg p-4 flex items-center gap-4">
              <div className="flex-1">
                <h4 className="text-white font-medium mb-1">{item.name}</h4>
                <div className="flex items-center gap-4 text-xs text-zinc-400">
                  <span>{item.type}</span>
                  <span>•</span>
                  <span>Submitted by {item.submitter}</span>
                  <span>•</span>
                  <span>{item.submitted}</span>
                </div>
              </div>
              <div className="flex gap-2">
                <button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                  Approve
                </button>
                <button className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                  Reject
                </button>
                <button className="bg-zinc-700 hover:bg-zinc-600 text-white px-4 py-2 rounded-lg text-sm transition-colors">
                  Review
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
