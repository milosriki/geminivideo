export default function CollaborationPage() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">Collaboration Tools</h1>
        <p className="text-zinc-400">
          Work together with your team in real-time
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Team Members</h3>
          <p className="text-zinc-400 mb-4">12 active members</p>
          <button className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2 rounded-lg transition-colors w-full">
            Invite Members
          </button>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Active Projects</h3>
          <p className="text-zinc-400 mb-4">8 shared projects</p>
          <button className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg transition-colors w-full">
            View All
          </button>
        </div>

        <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
          <h3 className="text-xl font-semibold text-white mb-2">Comments</h3>
          <p className="text-zinc-400 mb-4">23 unread comments</p>
          <button className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg transition-colors w-full">
            View Comments
          </button>
        </div>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {[
            { user: 'Sarah Chen', action: 'commented on', target: 'Summer Campaign Video', time: '2 minutes ago' },
            { user: 'Mike Rodriguez', action: 'approved', target: 'Q4 Creative Brief', time: '15 minutes ago' },
            { user: 'Emily Johnson', action: 'uploaded', target: 'Brand Assets.zip', time: '1 hour ago' },
            { user: 'David Kim', action: 'shared', target: 'Analytics Dashboard', time: '2 hours ago' },
          ].map((activity, i) => (
            <div key={i} className="bg-zinc-800 rounded-lg p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-violet-600 flex items-center justify-center text-white font-medium">
                {activity.user.split(' ').map(n => n[0]).join('')}
              </div>
              <div className="flex-1">
                <p className="text-white text-sm">
                  <span className="font-medium">{activity.user}</span> {activity.action}{' '}
                  <span className="text-violet-400">{activity.target}</span>
                </p>
                <p className="text-zinc-400 text-xs">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
